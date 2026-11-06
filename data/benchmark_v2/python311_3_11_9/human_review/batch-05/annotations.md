# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_train_080

```text
For fsspec.open rather than pathlib.Path.read_text, which compression formats are automatically inferred?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_080",
  "question": "For fsspec.open rather than pathlib.Path.read_text, which compression formats are automatically inferred?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.pathlib"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_037"
  ],
  "is_answerable": false,
  "category": "entity_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"fsspec.open\": [], \"pathlib.Path.read_text\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.pathlib_s31204_31268",
      "doc_id": "py3119.pathlib",
      "start_char": 31204,
      "end_char": 31268,
      "text": "Return the decoded contents of the pointed-to file as a string::"
    }
  ],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "evidence",
    "negative_absence",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.pathlib_s31204_31268; Unicode [31204, 31268). [Full pinned source](../../sources/pathlib.rst); [official reader URL](https://docs.python.org/3.11/library/pathlib.html).
```text
Return the decoded contents of the pointed-to file as a string::
```

## py311v2_train_085

```text
What minimum disk transfer speed does shutil.copyfile guarantee on an SSD?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_085",
  "question": "What minimum disk transfer speed does shutil.copyfile guarantee on an SSD?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.shutil"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_041"
  ],
  "is_answerable": false,
  "category": "attribute_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"shutil.copyfile\": [\"shutil\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.shutil_s1824_2057",
      "doc_id": "py3119.shutil",
      "start_char": 1824,
      "end_char": 2057,
      "text": "Copy the contents (no metadata) of the file named *src* to a file named\n   *dst* and return *dst* in the most efficient way possible.\n   *src* and *dst* are :term:`path-like objects <path-like object>` or path names given as strings."
    }
  ],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "evidence",
    "negative_absence",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.shutil_s1824_2057; Unicode [1824, 2057). [Full pinned source](../../sources/shutil.rst); [official reader URL](https://docs.python.org/3.11/library/shutil.html).
```text
Copy the contents (no metadata) of the file named *src* to a file named
   *dst* and return *dst* in the most efficient way possible.
   *src* and *dst* are :term:`path-like objects <path-like object>` or path names given as strings.
```

## py311v2_train_090

```text
Since TemporaryDirectory archives deleted contents for recovery, where is its archive and how long is it retained?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_090",
  "question": "Since TemporaryDirectory archives deleted contents for recovery, where is its archive and how long is it retained?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.tempfile"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_044"
  ],
  "is_answerable": false,
  "category": "false_premise",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.tempfile_s6070_6438",
      "doc_id": "py3119.tempfile",
      "start_char": 6070,
      "end_char": 6438,
      "text": "This class securely creates a temporary directory using the same rules as :func:`mkdtemp`.\n   The resulting object can be used as a :term:`context manager` (see\n   :ref:`tempfile-examples`).  On completion of the context or destruction\n   of the temporary directory object, the newly created temporary directory\n   and all its contents are removed from the filesystem."
    }
  ],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "evidence",
    "negative_absence",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.tempfile_s6070_6438; Unicode [6070, 6438). [Full pinned source](../../sources/tempfile.rst); [official reader URL](https://docs.python.org/3.11/library/tempfile.html).
```text
This class securely creates a temporary directory using the same rules as :func:`mkdtemp`.
   The resulting object can be used as a :term:`context manager` (see
   :ref:`tempfile-examples`).  On completion of the context or destruction
   of the temporary directory object, the newly created temporary directory
   and all its contents are removed from the filesystem.
```

## py311v2_train_060

```text
How do I configure backpressure in a Java Reactor Flux.concat pipeline?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_060",
  "question": "How do I configure backpressure in a Java Reactor Flux.concat pipeline?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.itertools"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_014"
  ],
  "is_answerable": false,
  "category": "off_topic",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"Flux.concat\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.itertools_s9897_10156",
      "doc_id": "py3119.itertools",
      "start_char": 9897,
      "end_char": 10156,
      "text": "Make an iterator that returns elements from the first iterable until it is\n   exhausted, then proceeds to the next iterable, until all of the iterables are\n   exhausted.  Used for treating consecutive sequences as a single sequence.\n   Roughly equivalent to::"
    }
  ],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "evidence",
    "negative_absence",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.itertools_s9897_10156; Unicode [9897, 10156). [Full pinned source](../../sources/itertools.rst); [official reader URL](https://docs.python.org/3.11/library/itertools.html).
```text
Make an iterator that returns elements from the first iterable until it is
   exhausted, then proceeds to the next iterable, until all of the iterables are
   exhausted.  Used for treating consecutive sequences as a single sequence.
   Roughly equivalent to::
```

## py311v2_train_076

```text
For toolz.itertoolz.interleave rather than itertools.chain, how are unequal-length inputs exhausted?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_076",
  "question": "For toolz.itertoolz.interleave rather than itertools.chain, how are unequal-length inputs exhausted?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.itertools"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_014"
  ],
  "is_answerable": false,
  "category": "entity_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"itertools.chain\": [], \"toolz.itertoolz.interleave\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.itertools_s9897_10156",
      "doc_id": "py3119.itertools",
      "start_char": 9897,
      "end_char": 10156,
      "text": "Make an iterator that returns elements from the first iterable until it is\n   exhausted, then proceeds to the next iterable, until all of the iterables are\n   exhausted.  Used for treating consecutive sequences as a single sequence.\n   Roughly equivalent to::"
    }
  ],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "evidence",
    "negative_absence",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.itertools_s9897_10156; Unicode [9897, 10156). [Full pinned source](../../sources/itertools.rst); [official reader URL](https://docs.python.org/3.11/library/itertools.html).
```text
Make an iterator that returns elements from the first iterable until it is
   exhausted, then proceeds to the next iterable, until all of the iterables are
   exhausted.  Used for treating consecutive sequences as a single sequence.
   Roughly equivalent to::
```

## py311v2_train_077

```text
For cachetools.TTLCache rather than functools.lru_cache, when are expired items physically removed?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_077",
  "question": "For cachetools.TTLCache rather than functools.lru_cache, when are expired items physically removed?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.functools"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_021"
  ],
  "is_answerable": false,
  "category": "entity_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"cachetools.TTLCache\": [], \"functools.lru_cache\": [\"collections\", \"fnmatch\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.functools_s5481_5697",
      "doc_id": "py3119.functools",
      "start_char": 5481,
      "end_char": 5697,
      "text": "Decorator to wrap a function with a memoizing callable that saves up to the\n   *maxsize* most recent calls.  It can save time when an expensive or I/O bound\n   function is periodically called with the same arguments."
    }
  ],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "evidence",
    "negative_absence",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.functools_s5481_5697; Unicode [5481, 5697). [Full pinned source](../../sources/functools.rst); [official reader URL](https://docs.python.org/3.11/library/functools.html).
```text
Decorator to wrap a function with a memoizing callable that saves up to the
   *maxsize* most recent calls.  It can save time when an expensive or I/O bound
   function is periodically called with the same arguments.
```

## py311v2_train_082

```text
What minimum throughput in elements per second does itertools.compress guarantee on a four-core CPU?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_082",
  "question": "What minimum throughput in elements per second does itertools.compress guarantee on a four-core CPU?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.itertools"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_015"
  ],
  "is_answerable": false,
  "category": "attribute_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"itertools.compress\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.itertools_s14485_14740",
      "doc_id": "py3119.itertools",
      "start_char": 14485,
      "end_char": 14740,
      "text": "Make an iterator that filters elements from *data* returning only those that\n   have a corresponding element in *selectors* that evaluates to ``True``.\n   Stops when either the *data* or *selectors* iterables has been exhausted.\n   Roughly equivalent to::"
    }
  ],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "evidence",
    "negative_absence",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.itertools_s14485_14740; Unicode [14485, 14740). [Full pinned source](../../sources/itertools.rst); [official reader URL](https://docs.python.org/3.11/library/itertools.html).
```text
Make an iterator that filters elements from *data* returning only those that
   have a corresponding element in *selectors* that evaluates to ``True``.
   Stops when either the *data* or *selectors* iterables has been exhausted.
   Roughly equivalent to::
```

## py311v2_train_083

```text
What caching wrapper does functools.cache provide, and what maximum wall-clock lookup latency does it guarantee under contention?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_083",
  "question": "What caching wrapper does functools.cache provide, and what maximum wall-clock lookup latency does it guarantee under contention?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.functools"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_020"
  ],
  "is_answerable": false,
  "category": "attribute_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "compound",
  "is_compound": true,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"functools.cache\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.functools_s1013_1136",
      "doc_id": "py3119.functools",
      "start_char": 1013,
      "end_char": 1136,
      "text": "Simple lightweight unbounded function cache.  Sometimes called\n   `\"memoize\" <https://en.wikipedia.org/wiki/Memoization>`_."
    }
  ],
  "compound_required_spans": [],
  "compound_missing_premises": [
    "The requested numerical performance guarantee is not supplied by the captured documentation."
  ],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "compound",
    "evidence",
    "negative_absence",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.functools_s1013_1136; Unicode [1013, 1136). [Full pinned source](../../sources/functools.rst); [official reader URL](https://docs.python.org/3.11/library/functools.html).
```text
Simple lightweight unbounded function cache.  Sometimes called
   `"memoize" <https://en.wikipedia.org/wiki/Memoization>`_.
```

## py311v2_train_088

```text
Since lru_cache automatically persists cached return values across interpreter restarts, which on-disk directory and retention period does it use?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_088",
  "question": "Since lru_cache automatically persists cached return values across interpreter restarts, which on-disk directory and retention period does it use?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.functools"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_021"
  ],
  "is_answerable": false,
  "category": "false_premise",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.functools_s5481_5697",
      "doc_id": "py3119.functools",
      "start_char": 5481,
      "end_char": 5697,
      "text": "Decorator to wrap a function with a memoizing callable that saves up to the\n   *maxsize* most recent calls.  It can save time when an expensive or I/O bound\n   function is periodically called with the same arguments."
    }
  ],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "evidence",
    "negative_absence",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.functools_s5481_5697; Unicode [5481, 5697). [Full pinned source](../../sources/functools.rst); [official reader URL](https://docs.python.org/3.11/library/functools.html).
```text
Decorator to wrap a function with a memoizing callable that saves up to the
   *maxsize* most recent calls.  It can save time when an expensive or I/O bound
   function is periodically called with the same arguments.
```

## py311v2_train_094

```text
Apply the cache decorator I meant. Which decorator should you select?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_094",
  "question": "Apply the cache decorator I meant. Which decorator should you select?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.functools"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_020",
    "py311v2_train_021"
  ],
  "is_answerable": false,
  "category": "ambiguous_question",
  "expected_decision": "CLARIFY",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "clarification_required",
  "ambiguity_interpretations": [
    "Unbounded functools.cache",
    "Bounded functools.lru_cache"
  ],
  "expected_answer": null,
  "expected_safe_behavior": "Ask which of the documented interpretations the requester intends. Do not select one arbitrarily or present either as confirmed intent.",
  "absence_note": "Both documented operations are plausible; the request omits the intended operation/output. Clarification resolves intent, whereas listing both does not authorize choosing one. Independent ambiguity review pending.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.functools_s1013_1136",
      "doc_id": "py3119.functools",
      "start_char": 1013,
      "end_char": 1136,
      "text": "Simple lightweight unbounded function cache.  Sometimes called\n   `\"memoize\" <https://en.wikipedia.org/wiki/Memoization>`_."
    },
    {
      "id": "py3119.functools_s5481_5697",
      "doc_id": "py3119.functools",
      "start_char": 5481,
      "end_char": 5697,
      "text": "Decorator to wrap a function with a memoizing callable that saves up to the\n   *maxsize* most recent calls.  It can save time when an expensive or I/O bound\n   function is periodically called with the same arguments."
    }
  ],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "ambiguity",
    "answerability",
    "evidence",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.functools_s1013_1136; Unicode [1013, 1136). [Full pinned source](../../sources/functools.rst); [official reader URL](https://docs.python.org/3.11/library/functools.html).
```text
Simple lightweight unbounded function cache.  Sometimes called
   `"memoize" <https://en.wikipedia.org/wiki/Memoization>`_.
```

py3119.functools_s5481_5697; Unicode [5481, 5697). [Full pinned source](../../sources/functools.rst); [official reader URL](https://docs.python.org/3.11/library/functools.html).
```text
Decorator to wrap a function with a memoizing callable that saves up to the
   *maxsize* most recent calls.  It can save time when an expensive or I/O bound
   function is periodically called with the same arguments.
```
