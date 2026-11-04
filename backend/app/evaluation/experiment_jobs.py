"""One bounded durable worker. Empirical profiles are intentionally unavailable."""

from __future__ import annotations

import logging
import threading
import time
from pathlib import Path

from app.api.experiment_models import ExperimentRequest
from app.db.experiments import ExperimentStore
from app.evaluation.runner import ErrorHandlingMode, EvaluationRunner
from app.evaluation.serialization import to_primitive
from app.evaluation.synthetic_runtime import (
    FIXTURES,
    GENERATION,
    pipeline_factory,
    policy_configs,
    source_fingerprint,
)

logger = logging.getLogger(__name__)


class ExperimentJobs:
    """SQLite owns pending work. Never automatically replay interrupted jobs."""

    def __init__(
        self, path: Path, *, capacity: int = 5, start_worker: bool = True
    ) -> None:
        self.store = ExperimentStore(path, capacity)
        self.stop = threading.Event()
        self.wake = threading.Event()
        self.unavailable = False
        self.worker = threading.Thread(target=self._work, daemon=True)
        if start_worker:
            self.worker.start()

    def submit(self, request: ExperimentRequest) -> dict:
        if self.unavailable or self.stop.is_set():
            raise OSError("Experiment worker unavailable")
        runner = EvaluationRunner(
            FIXTURES / "documents.jsonl", FIXTURES / "questions.jsonl"
        )
        split_ids = {q.id for q in runner._questions if q.split == request.split}
        selected = (
            split_ids if request.question_ids is None else (set(request.question_ids))
        )
        if not selected or not selected <= split_ids:
            raise ValueError("Question IDs must belong to the selected fixture split")
        # Persist effective IDs in dataset order, not an unbound future selection.
        config = request.model_dump()
        config["question_ids"] = [q.id for q in runner._questions if q.id in selected]
        config["retrieval"].update(chunk_size=500, chunk_overlap=50, k1=1.5, b=0.75)
        if request.retrieval.method == "hybrid":
            config["retrieval"].update(
                rank_lists=2,
                rrf_k=request.retrieval.rrf_k or 60,
                candidate_k=request.retrieval.candidate_k or 50,
            )
        job = self.store.submit(
            config,
            runner._dataset_fingerprint,
            len(selected) * len(request.policies),
            source_fingerprint(),
        )
        self.wake.set()
        return job

    def _execute(self, job: dict) -> None:
        config = job["configuration"]
        # Request schema rejects internal effective retrieval fields.
        supplied = dict(config)
        supplied["retrieval"] = {
            k: v
            for k, v in config["retrieval"].items()
            if k not in ("chunk_size", "chunk_overlap", "k1", "b", "rank_lists")
        }
        request = ExperimentRequest.model_validate(supplied)
        runner = EvaluationRunner(
            FIXTURES / "documents.jsonl", FIXTURES / "questions.jsonl"
        )
        if runner._dataset_fingerprint != job["dataset_fingerprint"]:
            raise ValueError("Fixture changed after submission")
        if source_fingerprint() != job["runtime_source_sha256"]:
            raise ValueError("Runtime changed after submission")
        deadline = time.monotonic() + 60
        record = runner.run(
            split=request.split,
            question_ids=request.question_ids,
            policies=policy_configs(request),
            pipeline_factory=pipeline_factory,
            retrieval_configuration=config["retrieval"],
            generation_configuration={
                **GENERATION,
                "source_sha256": job["runtime_source_sha256"],
            },
            random_seed=request.random_seed,
            error_mode=(
                ErrorHandlingMode.FAIL_FAST
                if request.fail_fast
                else ErrorHandlingMode.CONTINUE
            ),
            experiment_id=job["id"],
            on_observation=lambda run: self.store.observe(job["id"], to_primitive(run)),
            should_stop=lambda: self.stop.is_set() or time.monotonic() > deadline,
        )
        error = "execution_interrupted" if record.stopped_early else None
        self.store.finish(job["id"], record.to_dict(), error)

    def _work(self) -> None:
        try:
            while not self.stop.is_set():
                job = self.store.claim()
                if job is None:
                    self.wake.wait(0.25)
                    self.wake.clear()
                    continue
                try:
                    self._execute(job)
                except Exception as error:
                    # Sanitized code only; never expose raw exception details.
                    logger.error("Synthetic job failed (%s)", type(error).__name__)
                    self.store.finish(job["id"], None, "execution_failure")
        except Exception as error:
            # If storage is unavailable, do not invent a terminal persisted state.
            self.unavailable = True
            logger.error("Experiment worker stopped (%s)", type(error).__name__)

    def close(self) -> None:
        self.stop.set()
        self.wake.set()
        if self.worker.is_alive():
            self.worker.join(timeout=5)
        if self.worker.is_alive():
            self.unavailable = True
            # Retain ownership while thread is alive; restart recovery is safe.
            return
        self.store.close()
