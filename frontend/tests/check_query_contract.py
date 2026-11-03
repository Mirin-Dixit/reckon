"""Offline contract drift check. Run from repository root; no runtime initialization."""

import json
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "backend"))
from app.api.models import QueryRequest, QueryResponse  # noqa: E402

snapshot = json.loads((root / "frontend/lib/query-schema.json").read_text())
assert snapshot == {
    "request": QueryRequest.model_json_schema(),
    "response": QueryResponse.model_json_schema(),
}, "Query schema drift: inspect and update frontend contracts before accepting changes"
for method, family in (
    ("bm25", "bm25"),
    ("dense", "dense_cosine"),
    ("hybrid", "hybrid_rrf"),
):
    for policy in ("always_answer", "threshold", "prompt_abstention"):
        payload = {
            "question": "A corpus question",
            "retrieval": {"method": method, "top_k": 3},
            "policy": {"name": policy},
        }
        if method == "hybrid":
            payload["retrieval"]["rrf_k"] = 60
        if policy == "threshold":
            payload["policy"].update(
                score_type=family,
                threshold=0,
                direction="at_least",
                missing_score_decision="ABSTAIN",
            )
        QueryRequest.model_validate(payload)
print("PASS: exact query request/response schema snapshots and 9 request combinations")
