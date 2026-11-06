"""Loopback-only benchmark curation UI, separate from the inference application.

Run from the repository root: python -m app.evaluation.review_app --reviewer ID
Drafts and validated receipts never enter the benchmark ledger automatically.
"""

import argparse
import hashlib
import json
import os
import re
import secrets
import tempfile
from collections.abc import Iterator
from contextlib import contextmanager
from datetime import UTC, datetime
from pathlib import Path
from threading import RLock
from typing import Literal, Self
from urllib.parse import urlsplit

from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse, Response
from pydantic import Field, ValidationError, model_validator

from app.evaluation.benchmark_queue import (
    ReviewEvidence,
    Submission,
    _template,
    required_checks,
    validate_submission,
)
from app.evaluation.benchmark_review import Category, Check, StrictRecord
from app.evaluation.benchmark_v2 import load_v2_candidates, validate_v2_dataset
from app.evaluation.pilot30 import (
    PILOT_ID,
    PILOT_ROOT,
    validate_pilot,
    validate_pilot_submission,
)
from app.ingestion.loader import load_documents_from_jsonl

DATASET = Path("data/benchmark_v2/python311_3_11_9")
DRAFTS = Path(".ragbench-cache/human-review/browser")
ASSETS = Path(__file__).with_name("review_ui")
DESIGN_TOKENS = Path(__file__).resolve().parents[3] / "frontend/app/tokens.css"
FIRST_FIELDS = (
    "first_pass_decision",
    "first_pass_category",
    "first_pass_findings",
    "corpus_search_notes",
)


class Revision(StrictRecord):
    revision: int = Field(ge=0)


class FirstPass(Revision):
    first_pass_decision: Literal["ANSWER", "ABSTAIN", "CLARIFY"]
    first_pass_category: Category
    first_pass_findings: str = Field(min_length=1, max_length=16000)
    corpus_search_notes: str = Field(min_length=1, max_length=16000)
    basis: Literal["independent", "assisted"]
    evidence_records: list[ReviewEvidence] = Field(max_length=100)

    @model_validator(mode="after")
    def meaningful(self) -> Self:
        if not self.first_pass_findings.strip() or not self.corpus_search_notes.strip():
            raise ValueError("Record your findings and source searches first")
        expected = (
            "ANSWER"
            if self.first_pass_category == "answerable"
            else "CLARIFY"
            if self.first_pass_category == "ambiguous_question"
            else "ABSTAIN"
        )
        if self.first_pass_decision != expected:
            raise ValueError("Decision and category do not match")
        return self


class AnnotationReview(Revision):
    action: Literal["accept", "revise", "reject", "reclassify"]
    checks: list[Check] = Field(max_length=8)
    rationale: str = Field(min_length=1, max_length=16000)
    evidence_records: list[ReviewEvidence] = Field(max_length=100)
    proposed_changes: dict[str, object] | None


class Passage(StrictRecord):
    doc_id: str = Field(max_length=200)
    start_char: int = Field(ge=0)
    end_char: int = Field(gt=0)
    finding: str = Field(min_length=1, max_length=8000)


class ImportedNotes(Revision):
    records: list[dict] = Field(min_length=1, max_length=10)


def _issues(error: ValidationError) -> list[str]:
    return [
        ".".join(map(str, e["loc"])) + ": " + e["msg"]
        for e in error.errors(include_input=False, include_context=False)
    ]


class ReviewStore:
    """One configured reviewer per process; atomic, versioned local draft writes."""

    def __init__(
        self,
        root: Path,
        drafts: Path,
        reviewer: str,
        *,
        pilot: Path | None = None,
    ) -> None:
        if not reviewer or len(reviewer) > 120 or any(c.isspace() for c in reviewer):
            raise ValueError("Use your real stable reviewer ID, without spaces")
        if reviewer == "codex":
            raise ValueError("The candidate author cannot act as a human reviewer")
        self.root = root.resolve()
        base = drafts.resolve()
        # Never permit draft writes into benchmark inputs, even by CLI accident.
        data_dir = self.root.parent.parent
        if base.is_relative_to(data_dir) or data_dir.is_relative_to(base):
            raise ValueError("Draft storage must be separate from benchmark data")
        self.reviewer = reviewer
        self.pilot = pilot.resolve() if pilot is not None else None
        self.profile_sha256 = None
        if self.pilot is not None:
            result = validate_pilot(self.pilot, parent=self.root)
            self.profile_sha256 = result["selection_sha256"]
            # Keep Windows paths short; the complete digest remains bound in state.
            base = base / PILOT_ID / self.profile_sha256[:16]
        self.base = base
        self.directory = base / hashlib.sha256(reviewer.encode()).hexdigest()
        self.fingerprint = validate_v2_dataset(self.root)["corpus_sha256"]
        self.questions = {q.id: q for q in load_v2_candidates(self.root)}
        self.documents = {
            d.id: d for d in load_documents_from_jsonl(self.root / "documents.jsonl")
        }
        manifest = json.loads((self.root / "sources_manifest.json").read_text("utf-8"))
        self.sources = {s["document_id"]: s for s in manifest["sources"]}
        queue_path = self.root / "human_review/queue.json"
        packet_hashes = json.loads(
            (self.root / "human_review/packet_hashes.json").read_text("utf-8")
        )["files"]
        if (
            hashlib.sha256(queue_path.read_bytes()).hexdigest()
            != packet_hashes["queue.json"]
        ):
            raise ValueError("Review queue fingerprint mismatch")
        queue = json.loads(queue_path.read_text("utf-8"))["queue"]
        self.batches: dict[int, list[str]] = {}
        for row in queue:
            number = int(row["packet"].removeprefix("batch-"))
            self.batches.setdefault(number, []).append(row["candidate_id"])
        ids = [qid for group in self.batches.values() for qid in group]
        if (
            set(ids) != set(self.questions)
            or len(ids) != len(self.questions)
            or set(self.batches) != set(range(1, 17))
            or any(len(group) != 10 for group in self.batches.values())
        ):
            raise ValueError("Review queue membership mismatch")
        self.blind_questions = {}
        for number, members in self.batches.items():
            relative = f"batch-{number:02}/blind.md"
            blind = self.root / "human_review" / relative
            if (
                hashlib.sha256(blind.read_bytes()).hexdigest()
                != packet_hashes[relative]
            ):
                raise ValueError("Blind packet fingerprint mismatch")
            parsed = {
                qid: question
                for qid, _, question in re.findall(
                    r"## (\S+)\n\n(`{3,})text\n(.*?)\n\2\n",
                    blind.read_text("utf-8"),
                    re.DOTALL,
                )
            }
            if list(parsed) != members or any(
                parsed[qid] != self.questions[qid].question for qid in members
            ):
                raise ValueError("Blind questions differ from candidate records")
            self.blind_questions.update(parsed)
        if self.pilot is not None:
            selection = json.loads((self.pilot / "selection.json").read_text("utf-8"))
            self.batches = {}
            for item in selection["records"]:
                self.batches.setdefault(item["packet"], []).append(item["candidate_id"])
            selected_ids = {qid for group in self.batches.values() for qid in group}
            self.questions = {qid: self.questions[qid] for qid in selected_ids}
        self.lock = RLock()

    def path(self, batch: int) -> Path:
        if batch not in self.batches:
            raise HTTPException(404, "Unknown packet")
        path = self.directory / f"batch-{batch:02}.json"
        if (
            self.directory.resolve() != self.base / self.directory.name
            or path.resolve() != self.directory / path.name
        ):
            raise HTTPException(409, "Draft paths must not be symbolic links")
        return path

    @contextmanager
    def transaction(self) -> Iterator[None]:
        """Refuse concurrent writers, including another local server process."""
        with self.lock:
            self.path(1)
            self.directory.mkdir(parents=True, exist_ok=True)
            lock_path = self.directory / ".write-lock"
            try:
                fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            except FileExistsError:
                raise HTTPException(409, "Workspace busy in another service; retry")
            try:
                os.close(fd)
                yield
            finally:
                lock_path.unlink()

    def load(self, batch: int) -> dict:
        path = self.path(batch)
        if path.exists():
            try:
                if path.stat().st_size > 16 * 1024 * 1024:
                    raise ValueError("Oversized workspace")
                state = json.loads(path.read_text("utf-8"))
                if (
                    state["schema_version"] != "ragbench.review-workspace.v1"
                    or state["reviewer_id"] != self.reviewer
                    or state["corpus_sha256"] != self.fingerprint
                    or state.get("profile_sha256") != self.profile_sha256
                    or list(state["records"]) != self.batches[batch]
                    or type(state["revision"]) is not int
                    or state["revision"] < 0
                    or type(state["revealed"]) is not bool
                ):
                    raise ValueError("Invalid workspace header")
                for qid, record in state["records"].items():
                    submission = record["submission"]
                    template = _template(self.questions[qid])
                    if (
                        set(submission) != set(template)
                        or submission["reviewer_id"] != self.reviewer
                        or any(
                            submission[key] != template[key]
                            for key in (
                                "schema_version",
                                "candidate_id",
                                "candidate_sha256",
                                "corpus_sha256",
                            )
                        )
                        or any(
                            type(record[key]) is not bool
                            for key in ("first_pass_saved", "assisted", "final_saved")
                        )
                        or record["final_saved"]
                        and not state["revealed"]
                        or record["validation"] is not None
                        and not isinstance(record["validation"], dict)
                    ):
                        raise ValueError("Invalid workspace entry")
                    if record["first_pass_saved"]:
                        FirstPass.model_validate(
                            dict(
                                revision=state["revision"],
                                basis="assisted"
                                if record["assisted"]
                                else "independent",
                                evidence_records=submission["evidence_records"],
                                **{k: submission[k] for k in FIRST_FIELDS},
                            )
                        )
                        if submission["independent_first_pass"] is not (
                            None if record["assisted"] else True
                        ):
                            raise ValueError("Invalid independence attestation")
                    elif any(submission[k] for k in FIRST_FIELDS):
                        raise ValueError("Unmarked first-pass entry")
                if state["revealed"] and not all(
                    r["first_pass_saved"] for r in state["records"].values()
                ):
                    raise ValueError("Premature annotation reveal")
                return state
            except (ValueError, KeyError, TypeError, AttributeError):
                raise HTTPException(
                    409, "Draft is invalid or stale; it was not changed"
                )
        return dict(
            schema_version="ragbench.review-workspace.v1",
            reviewer_id=self.reviewer,
            corpus_sha256=self.fingerprint,
            profile_sha256=self.profile_sha256,
            revision=0,
            revealed=False,
            records={
                qid: dict(
                    submission={
                        **_template(self.questions[qid]),
                        "reviewer_id": self.reviewer,
                    },
                    first_pass_saved=False,
                    assisted=False,
                    final_saved=False,
                    validation=None,
                )
                for qid in self.batches[batch]
            },
        )

    def check_revision(self, state: dict, revision: int) -> None:
        if state["revision"] != revision:
            raise HTTPException(409, "Another tab saved changes. Reload before editing")
        try:
            validate_v2_dataset(self.root)
            if self.pilot is not None:
                result = validate_pilot(self.pilot, parent=self.root)
                if result["selection_sha256"] != self.profile_sha256:
                    raise ValueError("Pilot profile changed")
        except (ValueError, OSError):
            raise HTTPException(409, "Benchmark inputs changed; saving is blocked")

    def save(self, batch: int, state: dict) -> dict:
        self.directory.mkdir(parents=True, exist_ok=True)
        state["revision"] += 1
        fd, name = tempfile.mkstemp(dir=self.directory, suffix=".tmp")
        try:
            with os.fdopen(fd, "w", encoding="utf-8", newline="\n") as stream:
                json.dump(state, stream, ensure_ascii=False, indent=2, allow_nan=False)
                stream.write("\n")
                stream.flush()
                os.fsync(stream.fileno())
            os.replace(name, self.path(batch))
        finally:
            if os.path.exists(name):
                os.unlink(name)
        return self.view(state)

    def view(self, state: dict) -> dict:
        # Only this reviewer's draft; no ledger verdicts or other reviewer data.
        rows = []
        for qid, row in state["records"].items():
            public = {**row, "question": self.blind_questions[qid]}
            if state["revealed"]:
                public["annotation"] = self.questions[qid].model_dump(mode="json")
                public["required_checks"] = required_checks(self.questions[qid])
            rows.append(public)
        return dict(
            revision=state["revision"],
            revealed=state["revealed"],
            records=rows,
            first_pass_saved=sum(r["first_pass_saved"] for r in rows),
            final_saved=sum(r["final_saved"] for r in rows),
            validated_not_imported=sum(
                (r["validation"] or {}).get("status") == "validated_not_imported"
                for r in rows
            ),
        )

    def evidence(self, spans: list[ReviewEvidence]) -> None:
        for span in spans:
            doc = self.documents.get(span.doc_id)
            if (
                not doc
                or doc.text[span.start_char : span.end_char] != span.text
                or not span.finding.strip()
            ):
                raise HTTPException(422, "Evidence must be exact and have a finding")

    def validate(self, submission: dict) -> dict:
        if submission["independent_first_pass"] is not True:
            return dict(
                status="assisted_not_eligible",
                issues=[
                    "Assisted notes cannot satisfy the independent human-review gate"
                ],
            )
        try:
            parsed = Submission.model_validate_json(json.dumps(submission))
            if self.pilot is not None:
                return validate_pilot_submission(self.pilot, parsed, parent=self.root)
            return validate_submission(self.root, parsed)
        except ValidationError as error:
            return dict(status="incomplete", issues=_issues(error))
        except ValueError as error:
            return dict(status="incomplete", issues=[str(error)])


def create_review_app(
    *,
    reviewer: str,
    root: Path = DATASET,
    drafts: Path = DRAFTS,
    pilot: Path | None = None,
) -> FastAPI:
    """Build the independent local curation app without importing inference code."""
    store = ReviewStore(root, drafts, reviewer, pilot=pilot)
    app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
    token = secrets.token_urlsafe(32)

    @app.middleware("http")
    async def local_boundary(request: Request, call_next):
        try:
            address = urlsplit("http://" + request.headers.get("host", ""))
            host = address.hostname
            if (
                address.username is not None
                or address.password is not None
                or address.path
                or address.query
                or address.fragment
            ):
                raise ValueError("Invalid Host header")
            address.port  # Validate the port, if one is present.
        except ValueError:
            return JSONResponse({"detail": "Invalid local host"}, 403)
        origin = request.headers.get("origin")
        if (
            host not in {"127.0.0.1", "localhost", "::1"}
            or not request.client
            or request.client.host not in {"127.0.0.1", "::1"}
            or request.headers.get("sec-fetch-site") == "cross-site"
            or (origin and origin != str(request.base_url).rstrip("/"))
        ):
            return JSONResponse({"detail": "Local same-origin access only"}, 403)
        if request.method not in {"GET", "HEAD"}:
            if not secrets.compare_digest(
                request.headers.get("x-review-token", "").encode(), token.encode()
            ):
                return JSONResponse({"detail": "Reload the review page"}, 403)
            if request.headers.get("content-type", "").split(";")[0] != (
                "application/json"
            ):
                return JSONResponse({"detail": "JSON body required"}, 415)
            body = bytearray()
            async for chunk in request.stream():
                body.extend(chunk)
                if len(body) > 512 * 1024:
                    return JSONResponse({"detail": "Request exceeds 512 KiB"}, 413)
            request._body = bytes(body)
        response = await call_next(request)
        response.headers.update(
            {
                "Cache-Control": "no-store",
                "X-Content-Type-Options": "nosniff",
                "Referrer-Policy": "no-referrer",
                "Content-Security-Policy": "default-src 'self'; script-src 'self'; "
                "style-src 'self'; connect-src 'self'; object-src 'none'; "
                "base-uri 'none'; frame-ancestors 'none'; form-action 'self'",
            }
        )
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid(request: Request, error: RequestValidationError):
        return JSONResponse(
            {
                "detail": [
                    ".".join(map(str, e["loc"])) + ": " + e["msg"]
                    for e in error.errors()
                ]
            },
            422,
        )

    @app.exception_handler(OSError)
    async def storage_failure(request: Request, error: OSError):
        return JSONResponse(
            {
                "detail": (
                    "Local storage could not be read or saved. Keep your unsaved text, "
                    "check disk space and permissions, then retry. "
                    "No save was confirmed."
                )
            },
            503,
        )

    @app.get("/")
    def index():
        return FileResponse(ASSETS / "index.html")

    @app.get("/assets/{name}")
    def asset(name: str):
        if name == "tokens.css":
            return FileResponse(DESIGN_TOKENS)
        if name not in {"review.js", "review.css"}:
            raise HTTPException(404)
        return FileResponse(ASSETS / name)

    @app.get("/api/session")
    def session():
        return dict(
            reviewer_id=reviewer,
            token=token,
            packets=list(store.batches),
            profile=PILOT_ID if store.pilot is not None else "full-160",
            schema=Submission.model_json_schema(),
            sources=[
                dict(
                    id=doc.id,
                    title=doc.title,
                    version=doc.version,
                    filename=Path(store.sources[doc.id]["snapshot_path"]).name,
                )
                for doc in store.documents.values()
            ],
        )

    @app.get("/api/packets/{batch}")
    def packet(batch: int):
        with store.lock:
            return store.view(store.load(batch))

    @app.put("/api/packets/{batch}/first-pass/{qid}")
    def first_pass(batch: int, qid: str, body: FirstPass):
        with store.transaction():
            state = store.load(batch)
            store.check_revision(state, body.revision)
            if state["revealed"]:
                raise HTTPException(409, "First-pass entries are locked after reveal")
            if qid not in state["records"]:
                raise HTTPException(404, "Question is not in this packet")
            store.evidence(body.evidence_records)
            row = state["records"][qid]
            if row["assisted"] and body.basis == "independent":
                raise HTTPException(409, "Assisted notes cannot become independent")
            row["submission"].update({k: getattr(body, k) for k in FIRST_FIELDS})
            row["submission"]["evidence_records"] = [
                s.model_dump() for s in body.evidence_records
            ]
            row["assisted"] = body.basis == "assisted"
            row["submission"]["independent_first_pass"] = (
                None if row["assisted"] else True
            )
            row["first_pass_saved"] = True
            row["first_pass_saved_at_utc"] = datetime.now(UTC).isoformat()
            return store.save(batch, state)

    @app.post("/api/packets/{batch}/reveal")
    def reveal(batch: int, body: Revision):
        with store.transaction():
            state = store.load(batch)
            store.check_revision(state, body.revision)
            if not all(r["first_pass_saved"] for r in state["records"].values()):
                raise HTTPException(409, "Save all ten first-pass entries first")
            state["revealed"] = True
            return store.save(batch, state)

    @app.put("/api/packets/{batch}/annotation/{qid}")
    def annotation(batch: int, qid: str, body: AnnotationReview):
        with store.transaction():
            state = store.load(batch)
            store.check_revision(state, body.revision)
            if not state["revealed"]:
                raise HTTPException(409, "Complete the independent first pass first")
            if qid not in state["records"]:
                raise HTTPException(404)
            try:
                json.dumps(body.model_dump(), allow_nan=False)
            except ValueError:
                raise HTTPException(422, "Proposed changes must use finite JSON values")
            store.evidence(body.evidence_records)
            row = state["records"][qid]
            row["submission"].update(body.model_dump(exclude={"revision"}))
            row["submission"]["reviewed_at_utc"] = datetime.now(UTC).isoformat()
            row["final_saved"] = True
            row["validation"] = store.validate(row["submission"])
            return store.save(batch, state)

    @app.post("/api/packets/{batch}/import-notes")
    def import_notes(batch: int, body: ImportedNotes):
        with store.transaction():
            state = store.load(batch)
            store.check_revision(state, body.revision)
            if state["revealed"] or any(
                r["first_pass_saved"] for r in state["records"].values()
            ):
                raise HTTPException(409, "Import only into an empty blind packet")
            seen = set()
            for item in body.records:
                qid = item.get("candidate_id")
                if (
                    not isinstance(qid, str)
                    or qid not in state["records"]
                    or qid in seen
                ):
                    raise HTTPException(422, "Unknown or duplicate imported candidate")
                seen.add(qid)
                row = state["records"][qid]
                for key in ("candidate_sha256", "corpus_sha256"):
                    if item.get(key) != row["submission"][key]:
                        raise HTTPException(422, "Imported notes have stale hashes")
                if not any(item.get(k) for k in FIRST_FIELDS):
                    continue
                values = {k: item.get(k) for k in FIRST_FIELDS}
                try:
                    parsed = FirstPass(
                        revision=body.revision,
                        basis="assisted",
                        evidence_records=[],
                        **values,
                    )
                except ValidationError:
                    raise HTTPException(422, "Import requires four complete fields")
                row["submission"].update({k: getattr(parsed, k) for k in FIRST_FIELDS})
                row.update(first_pass_saved=True, assisted=True)
            return store.save(batch, state)

    @app.post("/api/packets/{batch}/validate")
    def validate(batch: int, body: Revision):
        with store.lock:
            state = store.load(batch)
            store.check_revision(state, body.revision)
            results = [
                {
                    "candidate_id": qid,
                    **(
                        store.validate(r["submission"])
                        if r["final_saved"]
                        else dict(
                            status="incomplete",
                            issues=["Annotation review is not saved"],
                        )
                    ),
                }
                for qid, r in state["records"].items()
            ]
            return dict(
                status="validated_not_imported"
                if all(r["status"] == "validated_not_imported" for r in results)
                else "incomplete_or_assisted",
                results=results,
            )

    @app.get("/api/packets/{batch}/export")
    def export(batch: int):
        with store.lock:
            rows = [r["submission"] for r in store.load(batch)["records"].values()]
            return Response(
                json.dumps(rows, ensure_ascii=False, indent=2) + "\n",
                media_type="application/json",
                headers={
                    "Content-Disposition": (
                        f'attachment; filename="batch-{batch:02}-review.json"'
                    )
                },
            )

    @app.get("/api/sources/{doc_id}")
    def source(doc_id: str):
        doc = store.documents.get(doc_id)
        if not doc:
            raise HTTPException(404)
        return dict(
            id=doc.id,
            text=doc.text,
            version=doc.version,
            sha256=store.sources[doc_id]["text_sha256"],
        )

    @app.get("/api/search")
    def search(q: str = ""):
        if not q.strip() or len(q) > 200:
            raise HTTPException(422, "Enter 1–200 characters to search")
        matches = []
        for doc in store.documents.values():
            for number, line in enumerate(doc.text.splitlines(), 1):
                if q.casefold() in line.casefold():
                    matches.append(dict(doc_id=doc.id, line=number, text=line))
        return dict(
            documents_searched=len(store.documents),
            total=len(matches),
            matches=matches[:200],
            truncated=len(matches) > 200,
        )

    @app.post("/api/evidence")
    def evidence(body: Passage):
        doc = store.documents.get(body.doc_id)
        if not doc or not (0 <= body.start_char < body.end_char <= len(doc.text)):
            raise HTTPException(422, "Select a nonempty passage inside the source")
        span = ReviewEvidence(
            id=f"{doc.id}_s{body.start_char}_{body.end_char}",
            doc_id=doc.id,
            start_char=body.start_char,
            end_char=body.end_char,
            text=doc.text[body.start_char : body.end_char],
            finding=body.finding,
        )
        store.evidence([span])
        return span.model_dump()

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--reviewer", required=True)
    parser.add_argument("--port", type=int, default=8010)
    parser.add_argument("--pilot", nargs="?", type=Path, const=PILOT_ROOT)
    args = parser.parse_args()
    if not 1024 <= args.port <= 65535:
        parser.error("Choose a port between 1024 and 65535")
    import uvicorn

    uvicorn.run(
        create_review_app(reviewer=args.reviewer, pilot=args.pilot),
        host="127.0.0.1",
        port=args.port,
        access_log=False,
        proxy_headers=False,
    )


if __name__ == "__main__":
    main()
