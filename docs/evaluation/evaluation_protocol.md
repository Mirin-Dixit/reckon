# RAGBench Evaluation Protocol

> **Pilot limitation:** this benchmark has 54 questions total, with only 3 Dev
> questions and 1 Test question. These splits do not support generalization or
> statistically reliable performance claims.

## Architecture and data flow

`EvaluationRunner` loads and validates the document/question JSONL using
`load_dataset_snapshot`. The loader captures each file's bytes once and computes
SHA-256 fingerprints from those same bytes used for parsing and validation.
Later file changes therefore cannot alter the recorded identity of the inputs
actually used. The API evaluation pipeline uses the runner-supplied document
snapshot for chunking and retrieval, rather than the cached query-runtime corpus.
The runner selects a split and optional question IDs,
then invokes a caller-provided pipeline factory once per policy configuration.
For each selected question, the runtime call is exactly `pipeline.run(question.question)`.
The existing pipeline remains responsible for retrieval, evidence construction,
assessment, policy selection, generation, and citation checks.

The experiment is written as a versioned JSON envelope (`ragbench.experiment.v2`).
Each run contains separate `observed` and evaluator-only `gold` sections. The
record includes source JSONL SHA-256 fingerprints, selected IDs, configurations,
policy and generation metadata, UTC creation time, seed, software/Git metadata,
sanitized environment metadata, outcomes, errors, and metric summaries.

## Runtime/gold separation

Ordinary API initialization uses `load_documents_from_jsonl` and never opens the
benchmark question file. Health and query execution therefore do not require
questions to be available. Only the explicit evaluation path constructs an
`EvaluationRunner`, which loads and fingerprints both files as before. Static
architectural checks prohibit gold-loader imports/calls in inference modules;
runtime read guards and gold-sentinel tests cover the supported query path.

Gold fields are held as validated `Question` records only inside the evaluator.
The pipeline factory receives the selected policy object, a read-only mapping of
`Document` objects, sanitized retrieval and generation configurations, and the
seed. It never receives a `Question` object. The pipeline receives only the
question text. The evaluator copies reference answers, expected-safe-behavior
text, category, domain, ambiguity metadata, and gold evidence spans into a
separate `gold` record **after** the run completes. Gold is therefore available
for post-run scoring and audit, never as a runtime prompt or policy input.

The supported construction path never passes Question objects or their gold
fields to a runtime component. The caller-supplied factory, policies, and other
callbacks are trusted Python code: they can deliberately close over external
objects, and this design is not a security sandbox. No environment variable
values are read for metadata. Configuration keys are normalized by removing
punctuation and case before matching secret-bearing names (including API keys,
tokens, passwords, secrets, credentials, and authorization); nested mappings
and lists are handled. Serialization also redacts those key classes and
recognizable credential formats in strings. This cannot identify every
arbitrary secret value, so credentials must never be passed as experiment
configuration or returned as model metadata. API credentials should be resolved
by a provider from the process environment.

## Experiment lifecycle

1. Load and validate documents/questions.
2. Select a valid split and optional IDs. IDs outside that split are rejected.
3. Build each pipeline from equivalent copies of the sanitized retrieval and
   generation configuration. The factory receives the seed. The policy is the
   intended experimental variable; the evaluator cannot guarantee that runtime
   components actually use the seed or are deterministic.
4. Run each selected question using question text only.
5. Record valid decisions separately from execution failures. `continue` records
   an error and continues; `fail_fast` records the first error and marks the
   experiment `stopped_early`.
6. Compare evidence contexts across policy runs. Any mismatch is recorded as a
   comparison warning and means the policies were not evaluated on identical
   retrieved evidence.
7. Attach gold labels after runtime completion, calculate metrics, and serialize
   the immutable experiment record.

Per-policy accounting reports expected, observed, successful, failed, missing,
and duplicate runs. Fail-fast records remain valid partial experiments; metrics
are marked partial and include expected and missing question IDs. Partial runs
are not presented as complete evaluations.

Offline evaluation example (using the existing BM25 retriever and a fixed
abstention policy):

```python
from app.generation.contracts import (
    Decision,
    DecisionReason,
    EvidenceAssessment,
    ReasonCode,
)
from app.generation.pipeline import (
    DecisionSelection,
    GeneratedAnswer,
    MockAnswerGenerator,
    MockEvidenceAssessor,
    PipelineConfig,
    RagPipeline,
)
from app.generation.policies import FixedDecisionPolicy
from app.evaluation.runner import (
    ErrorHandlingMode,
    EvaluationRunner,
    PolicyRunConfig,
)
from app.evaluation.serialization import write_experiment_json
from app.ingestion.chunking import chunk_documents
from app.retrieval.bm25 import BM25Index


def build_mock_pipeline(policy, documents, retrieval, generation, seed):
    docs = list(documents.values())
    chunks = chunk_documents(docs, chunk_size=500, chunk_overlap=50)
    return RagPipeline(
        retriever=BM25Index(chunks),
        documents=dict(documents),
        assessor=MockEvidenceAssessor(EvidenceAssessment()),
        policy=policy,
        generator=MockAnswerGenerator(GeneratedAnswer("Unused mock answer.", ())),
        config=PipelineConfig(
            top_k=retrieval["top_k"], retrieval_method="bm25"
        ),
    )

runner = EvaluationRunner(
    "data/benchmark/documents.jsonl",
    "data/benchmark/questions.jsonl",
)
experiment = runner.run(
    split="train",
    policies=[
        PolicyRunConfig(
            name="fixed_abstain",
            policy=FixedDecisionPolicy(
                DecisionSelection(
                    decision=Decision.ABSTAIN,
                    reason=DecisionReason(
                        ReasonCode.INSUFFICIENT_EVIDENCE,
                        "Offline demonstration policy.",
                    ),
                    policy_name="fixed_abstain",
                )
            ),
            parameters={"mode": "fixed_abstain"},
        )
    ],
    pipeline_factory=build_mock_pipeline,
    retrieval_configuration={"method": "bm25", "top_k": 5},
    generation_configuration={"provider": "mock"},
    random_seed=7,
    error_mode=ErrorHandlingMode.CONTINUE,
)
write_experiment_json(experiment, "experiment.json")
```

For a later OpenAI-backed run, install the optional `openai` extra, put the key
in `OPENAI_API_KEY`, and supply only non-secret provider/model settings. Do not
put the key value in the runner configurations or result file. Tests should
continue using mock providers; this protocol does not require or initiate live
API calls.

## Metrics and definitions

All rates include numerator and denominator; a zero denominator produces
`value: null` and `status: unavailable`. Reported denominators describe the
recorded runs; `run_accounting` separately identifies missing/duplicate runs
against the expected selected question set, and `partial: true` means metric
summaries are incomplete.

- **Decision counts:** successful ANSWER, ABSTAIN, and CLARIFY outcomes. Failed
  executions have no decision and are counted separately.
- **Abstention precision:** recorded unanswerable items intentionally ABSTAINed
  divided by all recorded intentional ABSTAINs. **Abstention recall:** those
  unanswerable ABSTAINs divided by all recorded unanswerable items. CLARIFY is
  reported separately and is not silently counted as abstention.
- **Clarification rate:** CLARIFY decisions divided by successful runs.
- **Execution error rate:** failed/timed-out/refused/incomplete run records
  divided by all recorded run records. These are never converted to abstentions.
- **False-answer rate:** recorded answers on unanswerable items divided by all
  recorded unanswerable items. **False-abstention rate:** recorded ABSTAINs on
  answerable items divided by all recorded answerable items.
- **Answer correctness:** normalized exact match and lexical token F1 against
  reference answers. These are lexical metrics, not semantic correctness.
  Semantic answer judgment is unavailable without a human or validated judge.
- **Citation validity:** citation IDs, absolute offsets, and exact quotes resolve
  to retrieved evidence. **Citation alignment precision** counts citations that
  overlap gold evidence spans. **Gold evidence retrieval recall** counts
  annotated spans overlapped by retrieved chunks. These tests do not prove a
  citation entails the answer claim.
- **Unsupported-claim and contradiction rates:** unavailable because there is no
  verified per-claim entailment or contradiction judgment in the gold data.
  A separate contradiction-surfacing rate on `conflicting_sources` items counts
  whether the run reports any contradiction; it does not verify that the
  reported conflict is correct.
- **Coverage:** ANSWER decisions divided by all selected items; failures remain
  in the denominator and cannot inflate coverage.
- **Selective risk exact-match proxy:** all successful ANSWER decisions are in
  the denominator. A missing/empty answer body is an error; answers on
  unanswerable items are errors; otherwise a normalized non-exact answer is an
  error. Coverage is successful ANSWER runs divided by all recorded runs, so
  ABSTAIN, CLARIFY, and execution failures are uncovered. The risk denominator
  is the number of ANSWER decisions. This is not semantic selective risk.
- **Answered-run ranking diagnostic** (`answered_run_ranking`): this is not a threshold-policy
  risk–coverage curve. It post-hoc ranks only observed ANSWER runs that have
  retrieval scores, by maximum score, grouped by policy and retrieval method.
  Abstentions and clarifications are not reclassified. Tied scores enter the
  same point. Coverage uses all recorded policy runs as denominator. At each
  point, execution failures are counted as maximum-risk errors in the risk
  denominator, following benchmark specification §7.2, but cannot be assigned a
  score threshold. Unscored answers are not rankable and are omitted from this
  diagnostic and are counted in `population_by_policy`; they remain in ordinary
  coverage and selective-risk accounting.
  If there are no eligible scored answers, no ranking points are emitted. Score
  families are ranking signals, never probabilities, and are not mixed.

`decision_accuracy_against_expected_safe_behavior` is unavailable: that label is
free text, and the benchmark does not contain a human-scored observed counterpart.
An unambiguous answerability-based decision proxy is reported separately and
excludes rows with expected-safe-behavior annotations or unresolved ambiguity.

Citation metrics are separate: structural validity verifies supplied evidence
IDs, absolute offsets, and quote text; invalid citations are counted one by
one. Citation alignment precision counts citations whose own offsets overlap
gold evidence spans. Gold evidence retrieval recall counts gold spans overlapped
by retrieved chunks. Structural validity is not grounding, offset overlap is
not entailment, and retrieval recall is not citation correctness. Runs without
citations are reported separately.

Breakdowns are reported by split, answerability category, domain, policy, and
retrieval method; the full experiment retrieval configuration is recorded as a
separate grouping. A paired comparison requires compatible benchmark split,
selected question IDs, retrieval configuration, generation configuration,
random seed, dataset fingerprint, provider/model metadata when present, and
identical retrieved evidence per question. It reports expected/actual pair
counts, missing and duplicate IDs, completeness, and evidence identity.
Incomplete pairs are rejected unless partial comparison is explicitly enabled
and labeled. Outcomes are descriptive; no significance test is run.

The seed is supplied to the pipeline factory and recorded. It is not proof of
reproducibility: runtime components must actually consume it, and model/provider
services may remain nondeterministic.

## Statistical limitations

The current benchmark is a pilot: 17 documents, 54 questions, Train 50, Dev 3,
and Test 1. Dev and Test results must report their sample counts and should not
support calibration or generalization claims. Wilson 95% intervals are included
only for denominators of at least 30 and are descriptive; they do not remedy
selection bias or a small/imbalanced benchmark. No p-values or statistical
significance claims are produced. Threshold tuning belongs on Dev, not Test.

Synthetic embeddings do not establish semantic retrieval quality. Retrieval
similarity scores are not calibrated probabilities of answerability.
