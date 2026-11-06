"""Offline human review packets and lexical alarms; never a runtime gold adapter.

Nothing here authenticates humans, makes semantic judgments, or freezes a dataset.
Submission validation is read-only: proposed edits and reviews are not applied.
"""

import argparse
import hashlib
import html
import itertools
import json
import math
import re
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Literal, Self

from pydantic import Field, field_validator, model_validator

from app.evaluation.benchmark_review import (
    Category,
    Check,
    Digest,
    HumanDecision,
    Identifier,
    ReviewItem,
    SourceRecord,
    StrictRecord,
    acceptance_issues,
    canonical_digest,
)
from app.evaluation.benchmark_v2 import (
    CandidateRecord,
    ExactSpan,
    load_v2_candidates,
    second_review_sample,
    validate_v2_dataset,
)
from app.ingestion.loader import load_documents_from_jsonl

PROTECTED = {
    "schema_version",
    "dataset_version",
    "id",
    "status",
    "verification_status",
    "author_id",
    "corpus_sha256",
    "candidate_revision",
}


def required_checks(q: CandidateRecord) -> list[str]:
    checks = {"source", "split", "answerability", "evidence"}
    checks.add(
        "reference_answer"
        if q.is_answerable
        else "ambiguity"
        if q.expected_decision == "CLARIFY"
        else "negative_absence"
    )
    if q.ambiguity_type:
        checks.add("ambiguity")
    if q.is_compound:
        checks.add("compound")
    return sorted(checks)


def required_reviews(q: CandidateRecord, sample: set[str]) -> int:
    return (
        2
        if (not q.is_answerable or q.is_compound or q.ambiguity_type or q.id in sample)
        else 1
    )


def _tokens(question: str) -> list[str]:
    question = re.sub(
        r"\bpython\s+\d+\.\d+(?:\.\d+)?", "python version", question.casefold()
    )
    stop = {
        "a",
        "an",
        "the",
        "in",
        "of",
        "to",
        "is",
        "and",
        "or",
        "what",
        "which",
        "does",
        "do",
        "how",
        "for",
        "its",
        "it",
        "python",
        "version",
    }
    # Small, explicit lexical equivalences. These do not establish semantic sameness.
    synonyms = {
        "returns": "return",
        "returning": "return",
        "returned": "return",
        "dictionary": "dict",
        "mapping": "dict",
        "mappings": "dict",
        "converts": "convert",
        "conversion": "convert",
        "constructs": "construct",
        "creates": "create",
    }
    return [
        synonyms.get(word, word)
        for word in re.findall(r"\w+", question)
        if word not in stop
    ]


def leakage_report(
    candidates: list[CandidateRecord], historical: list[dict[str, str]]
) -> dict:
    """Deterministic review alarms, including prior development exposure.

    Fixed thresholds select review candidates, not model or decision thresholds.
    No model, embedding, inference, or external corpus is used.
    """
    rows = [
        dict(id=q.id, split=q.split, question=q.question, dataset="v2")
        for q in candidates
    ] + historical
    tokens = [_tokens(row["question"]) for row in rows]
    frequency = Counter(word for words in tokens for word in set(words))
    vectors = [
        {
            word: count * (1 + math.log((1 + len(rows)) / (1 + frequency[word])))
            for word, count in Counter(words).items()
        }
        for words in tokens
    ]
    norms = [
        math.sqrt(sum(value * value for value in vector.values())) for vector in vectors
    ]
    by_id = {q.id: q for q in candidates}
    flags = []
    for i, j in itertools.combinations(range(len(rows)), 2):
        a, b = rows[i], rows[j]
        if a["dataset"] != "v2" and b["dataset"] != "v2":
            continue
        cosine = (
            (
                sum(
                    value * vectors[j].get(word, 0)
                    for word, value in vectors[i].items()
                )
                / (norms[i] * norms[j])
            )
            if norms[i] and norms[j]
            else 0.0
        )
        sa, sb = set(tokens[i]), set(tokens[j])
        jaccard = len(sa & sb) / len(sa | sb) if sa | sb else 0.0
        exact = (
            re.sub(r"\W+", " ", a["question"].casefold()).strip()
            == re.sub(r"\W+", " ", b["question"].casefold()).strip()
        )
        neutral_equal = tokens[i] == tokens[j]
        qa, qb = by_id.get(a["id"]), by_id.get(b["id"])
        shared_support = (
            sorted(
                {s.id for s in qa.evidence_spans} & {s.id for s in qb.evidence_spans}
            )
            if qa and qb and qa.is_answerable and qb.is_answerable
            else []
        )
        if not (
            exact
            or neutral_equal
            or cosine >= 0.72
            or jaccard >= 0.65
            or shared_support
        ):
            continue
        known_pair = (
            a["id"] in by_id
            and b["id"] in by_id
            and (
                a["id"] in by_id[b["id"]].near_miss_parent_ids
                or b["id"] in by_id[a["id"]].near_miss_parent_ids
            )
        )
        kind = (
            "historical_exposure"
            if a["dataset"] != b["dataset"]
            else "cross_split_possible_paraphrase"
            if a["split"] != b["split"]
            else "declared_related_pair"
            if known_pair
            else "within_split_possible_duplicate"
        )
        flags.append(
            dict(
                left=a,
                right=b,
                kind=kind,
                exact_normalized=exact,
                version_neutral_equal=neutral_equal,
                tfidf_cosine=round(cosine, 6),
                token_jaccard=round(jaccard, 6),
                shared_answer_evidence_ids=shared_support,
                status="pending_human_pair_review",
            )
        )
    return dict(
        schema_version="ragbench.leakage-screen.v1",
        status="screen_only_not_semantic_verification",
        method=(
            "version-neutral TF-IDF cosine/token Jaccard, lexical equivalences "
            "and exact answer-support reuse"
        ),
        thresholds=dict(tfidf_cosine=0.72, token_jaccard=0.65),
        counts=dict(Counter(flag["kind"] for flag in flags)),
        pairs=flags,
        limitation=(
            "Can miss paraphrases and flag different facts. No pair is "
            "automatically accepted, rejected or reassigned."
        ),
    )


def _fence(value: str) -> str:
    longest = max((len(m[0]) for m in re.finditer(r"`+", value)), default=0)
    fence = "`" * max(3, longest + 1)
    return fence + "text\n" + value + "\n" + fence + "\n"


def _historical(root: Path) -> list[dict[str, str]]:
    rows = []
    for dataset in ("benchmark", "sample"):
        for line in (
            (root / "data" / dataset / "questions.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        ):
            q = json.loads(line)
            rows.append(
                dict(
                    id=q["id"],
                    question=q["question"],
                    split=q.get("split", "unspecified"),
                    dataset=dataset,
                )
            )
    return rows


def _ledger(root: Path) -> dict[str, ReviewItem]:
    return {
        r.candidate_id: r
        for r in (
            ReviewItem.model_validate_json(line)
            for line in (root / "review_ledger.jsonl")
            .read_text(encoding="utf-8")
            .splitlines()
        )
    }


def review_status(
    candidates: list[CandidateRecord], ledger: dict[str, ReviewItem]
) -> dict:
    sample = set(second_review_sample(candidates))
    accepted = disagreements = review_count = 0
    remaining = 0
    for q in candidates:
        item = ledger[q.id]
        review_count += len(item.reviews)
        distinct = {r.reviewer_id for r in item.reviews}
        remaining += max(0, required_reviews(q, sample) - len(distinct))
        issues = acceptance_issues(
            item, candidate=q.model_dump(mode="json"), corpus_sha256=q.corpus_sha256
        )
        if len(distinct) < required_reviews(q, sample):
            issues += ("required second review incomplete",)
        accepted += not issues
        # Verdict disagreement is not an answerability-agreement score.
        disagreements += len({r.verdict for r in item.reviews}) > 1 and (
            item.adjudication is None
        )
    return dict(
        candidates=len(candidates),
        human_reviews=review_count,
        accepted_candidates=accepted,
        unresolved_verdict_disagreements=disagreements,
        required_review_records=sum(required_reviews(q, sample) for q in candidates),
        missing_review_records=remaining,
        agreement=None,
        agreement_status="not_computed_from_verdicts",
        freeze_status="blocked_pending_human_and_release_gates",
    )


def _template(q: CandidateRecord) -> dict:
    return dict(
        schema_version="ragbench.review-submission.v1",
        candidate_id=q.id,
        candidate_sha256=canonical_digest(q.model_dump(mode="json")),
        corpus_sha256=q.corpus_sha256,
        reviewer_id=None,
        reviewed_at_utc=None,
        independent_first_pass=None,
        first_pass_decision=None,
        first_pass_category=None,
        first_pass_findings="",
        action=None,
        checks=[],
        rationale="",
        corpus_search_notes="",
        evidence_records=[],
        proposed_changes=None,
    )


def build_queue(root: Path, output: Path, *, repository: Path) -> dict:
    """Create a new packet directory; never overwrite filled human forms."""
    validate_v2_dataset(root)
    if output.exists():
        raise ValueError(
            "Review output already exists; human work will not be overwritten"
        )
    candidates = load_v2_candidates(root)
    ledger = _ledger(root)
    sources = json.loads((root / "sources_manifest.json").read_text(encoding="utf-8"))
    source_map = {s["document_id"]: s for s in sources["sources"]}
    screen = leakage_report(candidates, _historical(repository))
    sample = set(second_review_sample(candidates))
    alarms = {row[side]["id"] for row in screen["pairs"] for side in ("left", "right")}
    ordered = sorted(
        candidates,
        key=lambda q: (
            0
            if not q.is_answerable
            else 1
            if q.is_compound or q.ambiguity_type
            else 2
            if q.id in sample
            else 3,
            q.id not in alarms,
            q.cluster_id,
            q.id,
        ),
    )
    files = {}
    queue = []
    for start in range(0, len(ordered), 10):
        group = ordered[start : start + 10]
        name = f"batch-{start // 10 + 1:02}"
        blind = [
            "# Independent first pass\n\nRead this before "
            "annotations.md. Derive your judgment from the full "
            "corpus; save your first-pass findings before opening "
            "proposed labels. Do not view another reviewer's completed "
            "forms.\n"
        ]
        annotated = [
            "# Proposed annotations and exact passages\n\nOpen only "
            "after recording your independent first-pass findings. "
            "Quotes below are source text; labels are machine-authored "
            "candidates, not verified truth.\n"
        ]
        forms = {"A": [], "B": []}
        for q in group:
            item = ledger[q.id]
            minimum = required_reviews(q, sample)
            blind += [
                "\n## " + html.escape(q.id) + "\n\n" + _fence(q.question),
                "Full corpus inventory: [source "
                "manifest](../../sources_manifest.json). "
                "Use all 34 documents for absence checks, not just "
                "selected passages.\n",
            ]
            annotated += [
                "\n## " + html.escape(q.id) + "\n\n" + _fence(q.question),
                _fence(
                    json.dumps(
                        {
                            **q.model_dump(mode="json"),
                            "required_human_reviews": minimum,
                            "required_checks": required_checks(q),
                        },
                        indent=2,
                        ensure_ascii=False,
                    )
                ),
                "### Exact source passages\n",
            ]
            for span in q.evidence_spans + q.diagnostic_spans:
                source = source_map[span.doc_id]
                filename = Path(source["snapshot_path"]).name
                annotated += [
                    f"\n{html.escape(span.id)}; "
                    f"Unicode [{span.start_char}, {span.end_char}). "
                    f"[Full pinned source](../../sources/{filename}); "
                    f"[official reader URL]({source['source_url']}).\n",
                    _fence(span.text),
                ]
            forms["A"].append(_template(q))
            if minimum == 2:
                forms["B"].append(_template(q))
            queue.append(
                dict(
                    candidate_id=q.id,
                    candidate_sha256=item.candidate_sha256,
                    corpus_sha256=item.corpus_sha256,
                    packet=name,
                    required_reviews=minimum,
                    ordinary_sample=q.id in sample,
                    leakage_alarm=q.id in alarms,
                    existing_reviews=len(item.reviews),
                )
            )
        files[f"{name}/blind.md"] = "".join(blind)
        files[f"{name}/annotations.md"] = "".join(annotated)
        for slot, rows in forms.items():
            if rows:
                files[f"{name}/reviewer-{slot}.json"] = (
                    json.dumps(rows, indent=2) + "\n"
                )
    status = review_status(candidates, ledger)
    summary = dict(
        schema_version="ragbench.review-queue.v1",
        **status,
        corpus_sha256=canonical_digest(sources),
        ledger_sha256=hashlib.sha256(
            (root / "review_ledger.jsonl").read_bytes()
        ).hexdigest(),
        leakage_counts=screen["counts"],
        queue=queue,
    )
    files["queue.json"] = json.dumps(summary, indent=2) + "\n"
    files["leakage_report.json"] = (
        json.dumps(screen, indent=2, ensure_ascii=False) + "\n"
    )
    files["pair_adjudication_templates.json"] = (
        json.dumps(
            [
                dict(
                    pair_sha256=canonical_digest(pair),
                    left=pair["left"],
                    right=pair["right"],
                    corpus_sha256=summary["corpus_sha256"],
                    reviewer_id=None,
                    reviewed_at_utc=None,
                    disposition=None,
                    evidence_records=[],
                    rationale="",
                )
                for pair in screen["pairs"]
            ],
            indent=2,
            ensure_ascii=False,
        )
        + "\n"
    )
    files["submission_schema.json"] = (
        json.dumps(Submission.model_json_schema(), indent=2) + "\n"
    )
    files["README.md"] = (
        "# Human review queue — pending\n\n"
        "160 candidates; 90 need independent dual review and 70 "
        "need one review (250 minimum reviews). "
        "A/B denote blank assignment slots, not reviewer identities.\n\n"
        "Work in packet order, ten candidates per packet: "
        "negatives/clarifications, then hard answerable "
        "cases, then the agreed ordinary second-review sample, then remaining answers. "
        "Each reviewer keeps a separate copy. Read blind.md and "
        "derive findings from the pinned corpus "
        "before opening annotations.md. Never view the other "
        "reviewer's completed form.\n\n"
        "Fill actual identity, UTC date, independent-first-pass "
        "attestation, initial decision/category, "
        "findings, checks, rationale, searches and exact evidence "
        "in reviewer-A/B.json. Null/blank forms "
        "are deliberately invalid submissions and do not count as reviews.\n\n"
        "Actions: accept, revise, reject or reclassify. "
        "Reclassification maps to the existing revise "
        "verdict and must include proposed_changes with a "
        "different category and consistent labels. "
        "Revise requires proposed changes too. No proposal is "
        "applied automatically. All edits require "
        "a new candidate revision/hash and renewed review.\n\n"
        "Validate filled forms from the repository root with PYTHONPATH=backend:\n\n"
        "```powershell\n.\\.venv\\Scripts\\python.exe -m "
        "app.evaluation.benchmark_queue check-submission "
        "data/benchmark_v2/python311_3_11_9 PATH_TO_FILLED_FORM.json\n```\n\n"
        "The command is read-only. It returns validated "
        "ledger-review/proposal receipts for curation, "
        "does not append reviews or change integrity hashes, and "
        "cannot authenticate humans. "
        "Preserve originals; actual receipt import and candidate "
        "changes require a reviewed curation step.\n\n"
        "leakage_report.json contains lexical alarms, not semantic "
        "judgments. Inspect every flagged "
        "pair, including historical pilot/sample exposure and "
        "expected version-near-miss pairs. "
        "Record pair disposition/evidence/rationale separately for "
        "adjudication; no alarm is cleared "
        "automatically. Inspect unflagged paraphrases too.\n\n"
        "No agreement score can be reported yet. After reviews, "
        "compute pre-adjudication agreement "
        "from independent annotation judgments, not accept/reject "
        "verdicts. Require the documented "
        "kappa gate, resolve all pair/licensing issues and obtain "
        "explicit Test-freeze approval. "
        "This directory's fingerprints identify review inputs; "
        "they are not a benchmark freeze.\n"
    )
    files["packet_hashes.json"] = (
        json.dumps(
            dict(
                schema_version="ragbench.review-packets.v1",
                files={
                    name: hashlib.sha256(value.encode("utf-8")).hexdigest()
                    for name, value in files.items()
                },
            ),
            indent=2,
        )
        + "\n"
    )
    output.mkdir(parents=True, exist_ok=False)
    for name, value in files.items():
        target = output / name
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(value, encoding="utf-8", newline="\n")
    return summary


class ReviewEvidence(ExactSpan):
    finding: str = Field(min_length=1)


class Submission(StrictRecord):
    schema_version: Literal["ragbench.review-submission.v1"]
    candidate_id: Identifier
    candidate_sha256: Digest
    corpus_sha256: Digest
    reviewer_id: Identifier
    reviewed_at_utc: datetime
    independent_first_pass: Literal[True]
    first_pass_decision: Literal["ANSWER", "ABSTAIN", "CLARIFY"]
    first_pass_category: Category
    first_pass_findings: str = Field(min_length=1)
    action: Literal["accept", "revise", "reject", "reclassify"]
    checks: list[Check]
    rationale: str = Field(min_length=1)
    corpus_search_notes: str
    evidence_records: list[ReviewEvidence]
    proposed_changes: dict[str, object] | None

    _utc = field_validator("reviewed_at_utc")(SourceRecord.utc.__func__)
    _independent = field_validator("independent_first_pass", mode="before")(
        HumanDecision.explicit_boolean.__func__
    )

    @model_validator(mode="after")
    def meaningful(self) -> Self:
        if any(
            not value.strip() for value in (self.first_pass_findings, self.rationale)
        ):
            raise ValueError("Human findings and rationale must be nonblank")
        expected = (
            "ANSWER"
            if self.first_pass_category == "answerable"
            else "CLARIFY"
            if self.first_pass_category == "ambiguous_question"
            else "ABSTAIN"
        )
        if self.first_pass_decision != expected:
            raise ValueError("Independent first-pass category/decision mismatch")
        return self


def validate_submission(root: Path, submission: Submission) -> dict:
    """Read-only intake validation; no review is manufactured or applied."""
    validate_v2_dataset(root)
    candidates = {q.id: q for q in load_v2_candidates(root)}
    q = candidates.get(submission.candidate_id)
    if (
        q is None
        or submission.candidate_sha256 != canonical_digest(q.model_dump(mode="json"))
        or submission.corpus_sha256 != q.corpus_sha256
    ):
        raise ValueError("Submission is bound to a stale or unknown candidate/corpus")
    existing = _ledger(root)[q.id]
    if submission.reviewer_id in {
        q.author_id,
        *(r.reviewer_id for r in existing.reviews),
    }:
        raise ValueError("Author self-review or duplicate reviewer")
    if not set(required_checks(q)) <= set(submission.checks):
        raise ValueError("Review checklist incomplete")
    documents = {d.id: d for d in load_documents_from_jsonl(root / "documents.jsonl")}
    if not submission.evidence_records:
        raise ValueError("Review requires recorded exact source evidence")
    for span in submission.evidence_records:
        if (
            span.doc_id not in documents
            or documents[span.doc_id].text[span.start_char : span.end_char] != span.text
            or not span.finding.strip()
        ):
            raise ValueError(
                "Review evidence is not an exact, explained source passage"
            )
    if not q.is_answerable and not submission.corpus_search_notes.strip():
        raise ValueError("Negative/clarification review requires corpus search notes")
    if submission.action == "accept":
        if (submission.first_pass_decision, submission.first_pass_category) != (
            q.expected_decision,
            q.category,
        ):
            raise ValueError(
                "Divergent first-pass labels require revision or adjudication"
            )
        required_spans = {s.id for s in q.evidence_spans + q.diagnostic_spans}
        if not required_spans <= {s.id for s in submission.evidence_records}:
            raise ValueError(
                "Accept requires explicit verification of proposed source spans"
            )
    proposal = None
    if submission.action in {"revise", "reclassify"}:
        patch = submission.proposed_changes
        if not patch or PROTECTED & set(patch):
            raise ValueError(
                "Revision requires annotation changes, not protected identity edits"
            )
        proposal = CandidateRecord.model_validate(
            {**q.model_dump(), **patch, "candidate_revision": q.candidate_revision + 1}
        )
        if submission.action == "reclassify" and proposal.category == q.category:
            raise ValueError("Reclassify requires a different proposed category")
    elif submission.proposed_changes is not None:
        raise ValueError("Accept/reject cannot apply hidden proposed changes")
    rationale = json.dumps(
        dict(
            rationale=submission.rationale,
            first_pass_decision=submission.first_pass_decision,
            first_pass_category=submission.first_pass_category,
            first_pass_findings=submission.first_pass_findings,
            corpus_search_notes=submission.corpus_search_notes,
            evidence_records=[s.model_dump() for s in submission.evidence_records],
        ),
        ensure_ascii=False,
        sort_keys=True,
    )
    review = HumanDecision(
        reviewer_id=submission.reviewer_id,
        actor_kind="human",
        candidate_sha256=submission.candidate_sha256,
        corpus_sha256=submission.corpus_sha256,
        reviewed_at_utc=submission.reviewed_at_utc,
        verdict="revise" if submission.action == "reclassify" else submission.action,
        checks=submission.checks,
        rationale=rationale,
        independent_first_pass=submission.independent_first_pass,
    )
    return dict(
        status="validated_not_imported",
        action=submission.action,
        candidate_id=q.id,
        ledger_review=review.model_dump(mode="json"),
        proposed_candidate=proposal.model_dump(mode="json") if proposal else None,
    )


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    build = sub.add_parser("build")
    build.add_argument("root", type=Path)
    build.add_argument("output", type=Path)
    build.add_argument("--repository", type=Path, default=Path("."))
    check = sub.add_parser("check-submission")
    check.add_argument("root", type=Path)
    check.add_argument("form", type=Path)
    args = parser.parse_args()
    if args.command == "build":
        result = build_queue(args.root, args.output, repository=args.repository)
        print(
            json.dumps(
                {k: v for k, v in result.items() if k != "queue"}, sort_keys=True
            )
        )
    else:
        if args.form.stat().st_size > 16 * 1024 * 1024:
            raise ValueError("Submission file exceeds 16 MiB bound")
        payload = json.loads(args.form.read_text(encoding="utf-8"))
        rows = payload if isinstance(payload, list) else [payload]
        print(
            json.dumps(
                [
                    validate_submission(
                        args.root, Submission.model_validate_json(json.dumps(row))
                    )
                    for row in rows
                ],
                ensure_ascii=False,
            )
        )


if __name__ == "__main__":
    main()
