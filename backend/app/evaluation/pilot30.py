"""Versioned pilot selection and offline release gate. No inference or gold adapter.

The full benchmark contracts, ledger and release gates are never modified here.
Review attestations cannot authenticate humans or prove their factual judgments.
"""

import argparse
import hashlib
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Literal

from pydantic import ValidationError, field_validator

from app.evaluation.benchmark_queue import (
    Submission,
    _historical,
    _template,
    leakage_report,
    validate_submission,
)
from app.evaluation.benchmark_review import (
    Digest,
    Identifier,
    ReviewItem,
    SourceRecord,
    StrictRecord,
    acceptance_issues,
    canonical_digest,
)
from app.evaluation.benchmark_v2 import (
    CandidateRecord,
    load_v2_candidates,
    validate_v2_dataset,
)
from app.ingestion.loader import load_documents_from_jsonl

PILOT_ID = "python311-pilot30.v1"
PILOT_ROOT = Path("data/pilot30/python311_3_11_9_v1")
PARENT_ROOT = Path("data/benchmark_v2/python311_3_11_9")
SEED = "ragbench-pilot30-v1"
EXPOSED_IDS = (
    "py311v2_test_027",
    "py311v2_train_064",
    "py311v2_train_065",
)
STRATA = (
    "off_topic",
    "temporal_near_miss",
    "entity_near_miss",
    "attribute_near_miss",
    "false_premise",
    "ambiguous_question",
)
RELEASE_CHECKS = (
    "source_and_reference_semantics",
    "corpus_wide_negative_checks",
    "split_and_historical_overlap",
    "duplicate_pair_review",
    "licensing",
    "held_out_protocol_and_exposure_log",
)


def _read(path: Path) -> object:
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Pilot file exceeds 16 MiB")
    return json.loads(path.read_text(encoding="utf-8"))


def _rank(q: CandidateRecord) -> tuple[str, str]:
    return hashlib.sha256((SEED + ":" + q.id).encode("utf-8")).hexdigest(), q.id


def select_candidates(candidates: list[CandidateRecord]) -> tuple[list, list[str]]:
    """Pure deterministic selection from frozen IDs, never from model outputs."""
    by_id = {q.id: q for q in candidates}
    excluded = set(EXPOSED_IDS)
    if not excluded <= set(by_id):
        raise ValueError("Known exposure IDs are missing from parent benchmark")
    while True:
        previous = set(excluded)
        for q in candidates:
            family = {q.id, *q.near_miss_parent_ids}
            if family & excluded:
                excluded.update(family)
        if excluded == previous:
            break
    selected = []
    for split in ("dev", "test"):
        eligible = [q for q in candidates if q.split == split and q.id not in excluded]
        group = []
        for category in STRATA:
            choices = [q for q in eligible if q.category == category]
            if not choices:
                raise ValueError("Pilot stratum has no eligible candidate")
            group.append(min(choices, key=_rank))
        anchors = {pid: by_id[pid] for q in group for pid in q.near_miss_parent_ids}
        if any(q.split != split or not q.is_answerable for q in anchors.values()):
            raise ValueError("Pilot anchor crosses splits or is not answerable")
        for cluster in sorted({q.cluster_id for q in eligible}):
            if not any(q.cluster_id == cluster for q in anchors.values()):
                choices = [
                    q for q in eligible if q.is_answerable and q.cluster_id == cluster
                ]
                if not choices:
                    raise ValueError("Pilot topic has no eligible answerable candidate")
                q = min(choices, key=_rank)
                anchors[q.id] = q
        if len(anchors) > 9 or set(anchors) & excluded:
            raise ValueError("Pilot anchor/topic requirements exceed positive quota")
        remaining = sorted(
            (q for q in eligible if q.is_answerable and q.id not in anchors), key=_rank
        )
        for q in remaining[: 9 - len(anchors)]:
            anchors[q.id] = q
        group.extend(anchors.values())
        if len(group) != 15:
            raise ValueError("Pilot split quota cannot be met")
        selected.extend(group)
    # Blind review packet order does not sort by labels, topic or evaluation role.
    selected.sort(
        key=lambda q: (
            hashlib.sha256((SEED + ":review:" + q.id).encode()).hexdigest(),
            q.id,
        )
    )
    return selected, sorted(excluded)


def selection_inputs(parent: Path = PARENT_ROOT) -> tuple[dict, dict, list]:
    """Reconstruct the approved protocol and complete hash-bound reference list."""
    full = validate_v2_dataset(parent)
    selected, excluded = select_candidates(load_v2_candidates(parent))
    history = _historical(parent.resolve().parents[2])
    screen = leakage_report(selected, history)
    protocol = dict(
        schema_version="ragbench.pilot-protocol.v1",
        pilot_id=PILOT_ID,
        status="unaccepted",
        selection_seed=SEED,
        parent_dataset_version="python311-3.11.9-candidates.1",
        parent_corpus_sha256=full["corpus_sha256"],
        parent_integrity_sha256=hashlib.sha256(
            (parent / "integrity.json").read_bytes()
        ).hexdigest(),
        historical_questions_sha256=canonical_digest(history),
        exposure_seed_ids=list(EXPOSED_IDS),
        excluded_family_ids=excluded,
        selection_rules=[
            "Preserve original Dev/Test roles; no Train candidates",
            "Lowest SHA-256(seed:ID), then ID, in each non-answerable stratum",
            "Include all selected anchor IDs and one positive per topic cluster",
            "Fill nine positives per split by the same hash rank",
            "Order three blind packets by SHA-256(seed:review:ID), then ID",
            "No model-performance inputs or automatic replacements",
        ],
        split_composition={
            s: {"answerable": 9, **{c: 1 for c in STRATA}} for s in ("dev", "test")
        },
        required_reviews=60,
        reviewers_per_question=2,
        reviewer_policy="Same two independent humans each review all 30",
        answerability_kappa_minimum=0.70,
        release_checks=list(RELEASE_CHECKS),
        fixture_infrastructure_requires_human_acceptance=False,
        empirical_evaluation_requires_pilot_release=True,
        full_benchmark_gate_satisfied=False,
    )
    selection = dict(
        schema_version="ragbench.pilot-selection.v1",
        pilot_id=PILOT_ID,
        protocol_sha256=canonical_digest(protocol),
        records=[
            dict(
                candidate_id=q.id,
                candidate_sha256=canonical_digest(q.model_dump(mode="json")),
                split=q.split,
                packet=index // 10 + 1,
            )
            for index, q in enumerate(selected)
        ],
        leakage_screen=screen,
    )
    return protocol, selection, selected


def create_pilot(output: Path = PILOT_ROOT, *, parent: Path = PARENT_ROOT) -> dict:
    """Create references and empty review items once; never regenerate parent data."""
    if output.exists():
        raise ValueError("Pilot output already exists; it will not be overwritten")
    if output.resolve().is_relative_to(parent.resolve()):
        raise ValueError("Pilot output must be separate from the full benchmark")
    protocol, selection, selected = selection_inputs(parent)
    original = {
        r.candidate_id: r
        for r in (
            ReviewItem.model_validate_json(line)
            for line in (parent / "review_ledger.jsonl").read_text("utf-8").splitlines()
        )
    }
    output.mkdir(parents=True, exist_ok=False)
    for name, payload in (("protocol.json", protocol), ("selection.json", selection)):
        (output / name).write_text(
            json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
            newline="\n",
        )
    with (output / "review_ledger.jsonl").open(
        "w", encoding="utf-8", newline="\n"
    ) as stream:
        for q in selected:
            # Never carry over author/AI/other-track verdicts as pilot reviews.
            item = original[q.id].model_copy(
                update={"reviews": [], "adjudication": None}
            )
            stream.write(item.model_dump_json() + "\n")
    (output / ".gitattributes").write_text(
        "*.json text eol=lf\n*.jsonl text eol=lf\n", encoding="utf-8", newline="\n"
    )
    return validate_pilot(output, parent=parent)


def pilot_ledger(root: Path) -> dict[str, ReviewItem]:
    path = root / "review_ledger.jsonl"
    if path.stat().st_size > 16 * 1024 * 1024:
        raise ValueError("Pilot review ledger exceeds 16 MiB")
    records = [
        ReviewItem.model_validate_json(s)
        for s in path.read_text("utf-8").splitlines()
        if s.strip()
    ]
    if len({r.candidate_id for r in records}) != len(records):
        raise ValueError("Duplicate pilot review item")
    return {r.candidate_id: r for r in records}


def agreement(left: list, right: list) -> dict:
    """Pre-adjudication nominal agreement; an undefined kappa stays null."""
    if not left or len(left) != len(right):
        return dict(n=0, raw_agreement=None, kappa=None)
    n = len(left)
    observed = sum(a == b for a, b in zip(left, right, strict=True)) / n
    a, b = Counter(left), Counter(right)
    expected = sum(a[k] * b[k] for k in a.keys() | b.keys()) / (n * n)
    kappa = (observed - expected) / (1 - expected) if expected < 1 else None
    return dict(n=n, raw_agreement=observed, kappa=kappa)


class ReleaseAttestation(StrictRecord):
    schema_version: Literal["ragbench.pilot-release.v1"]
    pilot_id: Literal["python311-pilot30.v1"]
    actor_kind: Literal["human"]
    reviewer_id: Identifier
    approved_at_utc: datetime
    approval: Literal["explicit_pilot_freeze_approval"]
    protocol_sha256: Digest
    selection_sha256: Digest
    review_ledger_sha256: Digest
    checks: list[str]
    rationale: str

    _utc = field_validator("approved_at_utc")(SourceRecord.utc.__func__)


def validate_pilot(
    root: Path = PILOT_ROOT,
    *,
    parent: Path = PARENT_ROOT,
    require_acceptance: bool = False,
) -> dict:
    """Check pilot-only eligibility; never change either release or review ledger."""
    protocol, selection, selected = selection_inputs(parent)
    if _read(root / "protocol.json") != protocol:
        raise ValueError("Pilot protocol differs from approved v1 selection contract")
    if _read(root / "selection.json") != selection:
        raise ValueError("Pilot selection, hashes or leakage screen changed")
    ledger = pilot_ledger(root)
    if set(ledger) != {q.id for q in selected}:
        raise ValueError("Pilot ledger membership mismatch")
    documents = {d.id: d for d in load_documents_from_jsonl(parent / "documents.jsonl")}
    blockers = []
    judges: dict[str, dict] = {}
    pair = None
    review_count = 0
    for q in selected:
        item = ledger[q.id]
        candidate = q.model_dump(mode="json")
        if any(
            getattr(item, key) != value
            for key, value in {
                "candidate_sha256": canonical_digest(candidate),
                "corpus_sha256": q.corpus_sha256,
                "author_id": q.author_id,
                "category": q.category,
                "expected_decision": q.expected_decision,
                "is_compound": q.is_compound,
                "ambiguity_type": q.ambiguity_type,
            }.items()
        ):
            raise ValueError("Pilot ledger is not bound to the current candidate")
        blockers.extend(
            f"{q.id}: {issue}"
            for issue in acceptance_issues(
                item, candidate=candidate, corpus_sha256=q.corpus_sha256
            )
        )
        review_count += len(item.reviews)
        ids = {r.reviewer_id for r in item.reviews}
        if len(item.reviews) != 2 or len(ids) != 2:
            blockers.append(q.id + ": two distinct first-pass reviewers required")
        elif pair is None:
            pair = ids
        elif pair != ids:
            blockers.append(q.id + ": same two raters must review all 30")
        for review in item.reviews:
            try:
                notes = json.loads(review.rationale)
                parsed = Submission.model_validate_json(
                    json.dumps(
                        {
                            **_template(q),
                            **review.model_dump(
                                mode="json",
                                exclude={"actor_kind", "verdict", "rationale"},
                            ),
                            "action": review.verdict,
                            "rationale": notes["rationale"],
                            **{
                                k: notes[k]
                                for k in (
                                    "first_pass_decision",
                                    "first_pass_category",
                                    "first_pass_findings",
                                    "corpus_search_notes",
                                    "evidence_records",
                                )
                            },
                        }
                    )
                )
                if (
                    not parsed.evidence_records
                    or not parsed.corpus_search_notes.strip()
                ):
                    raise ValueError("Evidence and actual search notes required")
                for span in parsed.evidence_records:
                    if (
                        span.doc_id not in documents
                        or not span.finding.strip()
                        or documents[span.doc_id].text[span.start_char : span.end_char]
                        != span.text
                    ):
                        raise ValueError("Nonexact pilot review evidence")
                if review.verdict == "accept":
                    if (parsed.first_pass_decision, parsed.first_pass_category) != (
                        q.expected_decision,
                        q.category,
                    ):
                        raise ValueError("Divergent first pass cannot silently accept")
                    if not {s.id for s in q.evidence_spans + q.diagnostic_spans} <= {
                        s.id for s in parsed.evidence_records
                    }:
                        raise ValueError("Proposed spans have not all been verified")
                judges.setdefault(review.reviewer_id, {})[q.id] = parsed
            except (ValueError, KeyError, TypeError, ValidationError):
                blockers.append(
                    q.id + ": invalid independent annotation/evidence record"
                )
    stats = None
    if (
        pair
        and len(pair) == 2
        and all(len(judges.get(reviewer, {})) == 30 for reviewer in pair)
    ):
        a, b = sorted(pair)
        records = [[judges[r][q.id] for q in selected] for r in (a, b)]
        stats = {
            "answerability": agreement(
                *[
                    [r.first_pass_category == "answerable" for r in rows]
                    for rows in records
                ]
            ),
            "decision": agreement(
                *[[r.first_pass_decision for r in rows] for rows in records]
            ),
            "category": agreement(
                *[[r.first_pass_category for r in rows] for rows in records]
            ),
        }
    if (
        stats is None
        or stats["answerability"]["kappa"] is None
        or stats["answerability"]["kappa"] < 0.70
    ):
        blockers.append(
            "Pre-adjudication answerability kappa >= 0.70 is not established"
        )
    approval_path = root / "release_approval.json"
    if not approval_path.exists():
        blockers.append(
            "Source/overlap/license checks and explicit pilot freeze approval missing"
        )
    else:
        try:
            approval = ReleaseAttestation.model_validate_json(
                approval_path.read_text("utf-8")
            )
            if (
                approval.reviewer_id == "codex"
                or not approval.rationale.strip()
                or set(approval.checks) != set(RELEASE_CHECKS)
                or len(approval.checks) != len(RELEASE_CHECKS)
                or approval.protocol_sha256 != canonical_digest(protocol)
                or approval.selection_sha256 != canonical_digest(selection)
                or approval.review_ledger_sha256
                != hashlib.sha256(
                    (root / "review_ledger.jsonl").read_bytes()
                ).hexdigest()
            ):
                raise ValueError("Stale or incomplete pilot release attestation")
            review_times = [
                r.reviewed_at_utc
                for item in ledger.values()
                for r in [
                    *item.reviews,
                    *([item.adjudication] if item.adjudication else []),
                ]
            ]
            if review_times and approval.approved_at_utc < max(review_times):
                raise ValueError("Pilot approval predates the reviews it authorizes")
        except (ValueError, TypeError):
            blockers.append("Pilot freeze approval is invalid, stale or incomplete")
    if require_acceptance and blockers:
        raise ValueError("Pilot not accepted: " + "; ".join(blockers))
    return dict(
        pilot_id=PILOT_ID,
        status="pilot_unaccepted" if blockers else "pilot_release_eligible",
        candidates=30,
        splits=dict(Counter(q.split for q in selected)),
        classes=dict(Counter(q.category for q in selected)),
        required_reviews=60,
        human_reviews=review_count,
        agreement=stats,
        blockers=blockers,
        empirical_evaluation_allowed=not blockers,
        synthetic_infrastructure_allowed=True,
        full_benchmark_accepted=False,
        protocol_sha256=canonical_digest(protocol),
        selection_sha256=canonical_digest(selection),
    )


def validate_pilot_submission(
    root: Path,
    submission: Submission,
    *,
    parent: Path = PARENT_ROOT,
) -> dict:
    """Validate a receipt against the pilot ledger without importing it."""
    validate_pilot(root, parent=parent)
    ledger = pilot_ledger(root)
    item = ledger.get(submission.candidate_id)
    if item is None:
        raise ValueError("Candidate is outside this pilot")
    if submission.reviewer_id in {r.reviewer_id for r in item.reviews}:
        raise ValueError("Duplicate pilot reviewer")
    if len(item.reviews) >= 2:
        raise ValueError(
            "Pilot first-pass pair is complete; use adjudication for disagreements"
        )
    return {**validate_submission(parent, submission), "pilot_id": PILOT_ID}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    create = sub.add_parser("create")
    create.add_argument("root", nargs="?", type=Path, default=PILOT_ROOT)
    check = sub.add_parser("validate")
    check.add_argument("root", nargs="?", type=Path, default=PILOT_ROOT)
    check.add_argument("--require-acceptance", action="store_true")
    submission = sub.add_parser("check-submission")
    submission.add_argument("root", type=Path)
    submission.add_argument("form", type=Path)
    args = parser.parse_args()
    if args.command == "create":
        result = create_pilot(args.root)
    elif args.command == "validate":
        result = validate_pilot(args.root, require_acceptance=args.require_acceptance)
    else:
        payload = _read(args.form)
        rows = payload if isinstance(payload, list) else [payload]
        result = [
            validate_pilot_submission(
                args.root, Submission.model_validate_json(json.dumps(row))
            )
            for row in rows
        ]
    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
