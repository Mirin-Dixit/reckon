# RAGBench Studio

**An experimental workbench for evaluating retrieval strategies in retrieval-augmented generation.**

RAGBench Studio is a project focused on a practical question in RAG systems: *when a question is asked, how much does the retrieval strategy influence the evidence available to answer it?*

The goal is to build a controlled environment for comparing retrieval configurations, inspecting retrieved passages, and measuring retrieval quality against a defined evaluation dataset. Rather than treating a generated answer as the only measure of success, the project separates retrieval quality from answer generation so that individual components can be examined and compared.

> **Project status:** Initial development. The repository structure is being established; retrieval pipelines, evaluation metrics, and the web interface are not yet implemented.

## Problem

A RAG pipeline can produce a fluent answer while retrieving incomplete, irrelevant, or poorly ranked evidence. Looking only at the final response makes it difficult to determine where the failure occurred.

RAGBench Studio is being developed to make that process inspectable. The intended workflow is to run the same evaluation questions against different retrieval configurations, examine the resulting passages, and compare measured performance under consistent conditions.

## Scope

The initial implementation is intended to cover:

- **Document ingestion:** loading and preparing a defined collection of source documents.
- **Retrieval experiments:** comparing lexical, dense-vector, and hybrid retrieval approaches.
- **Ranking and inspection:** examining the passages returned for a query and their relative ordering.
- **Evaluation:** measuring retrieval performance against labelled queries and relevant-document judgments.
- **Experiment reproducibility:** recording configurations, datasets, and results so comparisons can be repeated.
- **Interface:** providing a web-based way to run experiments and inspect their outputs.

These are development objectives, not claims of completed functionality. Supported methods, metrics, and datasets will be documented as they are implemented and tested.

## Engineering Approach

The project is organized to keep the main stages of a RAG workflow separate:

| Component | Responsibility |
|---|---|
| Ingestion | Document loading, parsing, and chunk preparation |
| Retrieval | Candidate selection and ranking |
| Generation | Producing responses from retrieved context |
| Evaluation | Computing metrics and comparing runs |
| API | Exposing application operations to the interface |
| Frontend | Configuring experiments and inspecting results |

This separation is intended to make it possible to change one component without rewriting the entire application. It also makes failures easier to isolate: a poor answer can be investigated by inspecting the retrieved evidence before changing the generation stage.

## Repository Layout

```text
ragbench/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   ├── core/
│   │   ├── db/
│   │   ├── evaluation/
│   │   ├── generation/
│   │   ├── ingestion/
│   │   └── retrieval/
│   └── tests/
├── data/
│   └── sample/
├── docs/
│   ├── decisions/
│   ├── reference/
│   └── results/
├── frontend/
├── scripts/
├── .env.example
├── .gitignore
├── AGENTS.md
├── pyproject.toml
└── README.md
```

The layout reflects the intended separation of responsibilities. Modules and files will be added as implementation requires them.

## Technology

The project is being set up around the following tools:

- **Python** for the backend and evaluation logic.
- **Next.js and TypeScript** for the web interface.
- **Git** for version control and traceable development.
- **pytest and Ruff** for automated testing and Python code quality.

Additional libraries, storage systems, and model providers will be selected and documented when their roles in the implementation are defined.

## Evaluation Principles

The evaluation layer is intended to make comparisons meaningful rather than merely produce scores.

1. Use a defined set of evaluation queries.
2. Record which documents or passages are relevant to each query.
3. Apply the same evaluation data when comparing retrieval configurations.
4. Keep retrieval metrics distinct from answer-generation quality.
5. Preserve the configuration and results needed to reproduce an experiment.

Metrics and experimental findings will be reported only after their implementations and outputs have been validated.

## Development

The project is currently at the initial setup stage. The first milestones cover repository configuration, backend foundations, document ingestion, and retrieval. Evaluation and the frontend will be developed incrementally on top of those foundations.

Setup instructions and runnable examples will be added once the corresponding components are available. Until then, the repository should be treated as a work in progress rather than a ready-to-use application.

## Design Decisions and Results

Architecture decisions, implementation notes, and experiment outputs are intended to live alongside the code:

- `docs/decisions/` — significant design choices and their rationale.
- `docs/results/` — measured experiment outputs and comparisons.
- `backend/tests/` — automated checks for implemented behaviour.

The aim is to keep the reasoning behind technical choices visible, not just the final implementation.

---

*This repository is under active development. Features and evaluation results will be documented as they become available.*