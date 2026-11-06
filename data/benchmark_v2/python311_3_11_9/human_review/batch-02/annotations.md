# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_train_067

```text
In Python 3.13, in what order does itertools.chain consume its input iterables?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_067",
  "question": "In Python 3.13, in what order does itertools.chain consume its input iterables?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.itertools"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_014"
  ],
  "is_answerable": false,
  "category": "temporal_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"Python 3.13\": [], \"itertools.chain\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
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

## py311v2_train_068

```text
In Python 3.13, what caching behavior does functools.lru_cache provide?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_068",
  "question": "In Python 3.13, what caching behavior does functools.lru_cache provide?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.functools"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_021"
  ],
  "is_answerable": false,
  "category": "temporal_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"Python 3.13\": [], \"functools.lru_cache\": [\"collections\", \"fnmatch\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
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

## py311v2_test_028

```text
In Python 3.13, what components does urllib.parse.urlparse return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_028",
  "question": "In Python 3.13, what components does urllib.parse.urlparse return?",
  "split": "test",
  "cluster_id": "networking",
  "source_document_ids": [
    "py3119.urllib.parse"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_007"
  ],
  "is_answerable": false,
  "category": "temporal_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"Python 3.13\": [], \"urllib.parse.urlparse\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.urllib.parse_s1460_1997",
      "doc_id": "py3119.urllib.parse",
      "start_char": 1460,
      "end_char": 1997,
      "text": "Parse a URL into six components, returning a 6-item :term:`named tuple`.  This\n   corresponds to the general structure of a URL:\n   ``scheme://netloc/path;parameters?query#fragment``.\n   Each tuple item is a string, possibly empty. The components are not broken up\n   into smaller parts (for example, the network location is a single string), and %\n   escapes are not expanded. The delimiters as shown above are not part of the\n   result, except for a leading slash in the *path* component, which is retained if\n   present.  For example:"
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

py3119.urllib.parse_s1460_1997; Unicode [1460, 1997). [Full pinned source](../../sources/urllib.parse.rst); [official reader URL](https://docs.python.org/3.11/library/urllib.parse.html).
```text
Parse a URL into six components, returning a 6-item :term:`named tuple`.  This
   corresponds to the general structure of a URL:
   ``scheme://netloc/path;parameters?query#fragment``.
   Each tuple item is a string, possibly empty. The components are not broken up
   into smaller parts (for example, the network location is a single string), and %
   escapes are not expanded. The delimiters as shown above are not part of the
   result, except for a leading slash in the *path* component, which is retained if
   present.  For example:
```

## py311v2_dev_016

```text
In Python 3.13, what boolean result does math.isclose return for close versus non-close values?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_016",
  "question": "In Python 3.13, what boolean result does math.isclose return for close versus non-close values?",
  "split": "dev",
  "cluster_id": "numeric",
  "source_document_ids": [
    "py3119.math"
  ],
  "near_miss_parent_ids": [
    "py311v2_dev_001"
  ],
  "is_answerable": false,
  "category": "temporal_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"Python 3.13\": [], \"math.isclose\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.math_s5298_5391",
      "doc_id": "py3119.math",
      "start_char": 5298,
      "end_char": 5391,
      "text": "Return ``True`` if the values *a* and *b* are close to each other and\n   ``False`` otherwise."
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

py3119.math_s5298_5391; Unicode [5298, 5391). [Full pinned source](../../sources/math.rst); [official reader URL](https://docs.python.org/3.11/library/math.html).
```text
Return ``True`` if the values *a* and *b* are close to each other and
   ``False`` otherwise.
```

## py311v2_test_030

```text
In Python 3.13, when does subprocess.run return and what result object does it provide?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_030",
  "question": "In Python 3.13, when does subprocess.run return and what result object does it provide?",
  "split": "test",
  "cluster_id": "process-control",
  "source_document_ids": [
    "py3119.subprocess"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_019"
  ],
  "is_answerable": false,
  "category": "temporal_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"Python 3.13\": [], \"subprocess.run\": [\"os\", \"subprocess\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.subprocess_s1409_1529",
      "doc_id": "py3119.subprocess",
      "start_char": 1409,
      "end_char": 1529,
      "text": "Run the command described by *args*.  Wait for command to complete, then\n   return a :class:`CompletedProcess` instance."
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

py3119.subprocess_s1409_1529; Unicode [1409, 1529). [Full pinned source](../../sources/subprocess.rst); [official reader URL](https://docs.python.org/3.11/library/subprocess.html).
```text
Run the command described by *args*.  Wait for command to complete, then
   return a :class:`CompletedProcess` instance.
```

## py311v2_dev_017

```text
In Python 3.13, what input types can json.loads deserialize?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_017",
  "question": "In Python 3.13, what input types can json.loads deserialize?",
  "split": "dev",
  "cluster_id": "serialization",
  "source_document_ids": [
    "py3119.json"
  ],
  "near_miss_parent_ids": [
    "py311v2_dev_010"
  ],
  "is_answerable": false,
  "category": "temporal_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"Python 3.13\": [], \"json.loads\": [\"json\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.json_s11192_11378",
      "doc_id": "py3119.json",
      "start_char": 11192,
      "end_char": 11378,
      "text": "Deserialize *s* (a :class:`str`, :class:`bytes` or :class:`bytearray`\n   instance containing a JSON document) to a Python object using this\n   :ref:`conversion table <json-to-py-table>`."
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

py3119.json_s11192_11378; Unicode [11192, 11378). [Full pinned source](../../sources/json.rst); [official reader URL](https://docs.python.org/3.11/library/json.html).
```text
Deserialize *s* (a :class:`str`, :class:`bytes` or :class:`bytearray`
   instance containing a JSON document) to a Python object using this
   :ref:`conversion table <json-to-py-table>`.
```

## py311v2_test_031

```text
For anyio.create_task_group rather than asyncio.TaskGroup, how are cancellation scopes inherited?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_031",
  "question": "For anyio.create_task_group rather than asyncio.TaskGroup, how are cancellation scopes inherited?",
  "split": "test",
  "cluster_id": "concurrency",
  "source_document_ids": [
    "py3119.asyncio-task"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_002"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"anyio.create_task_group\": [], \"asyncio.TaskGroup\": [\"asyncio-task\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.asyncio-task_s8936_9147",
      "doc_id": "py3119.asyncio-task",
      "start_char": 8936,
      "end_char": 9147,
      "text": "An :ref:`asynchronous context manager <async-context-managers>`\n   holding a group of tasks.\n   Tasks can be added to the group using :meth:`create_task`.\n   All tasks are awaited when the context manager exits."
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

py3119.asyncio-task_s8936_9147; Unicode [8936, 9147). [Full pinned source](../../sources/asyncio-task.rst); [official reader URL](https://docs.python.org/3.11/library/asyncio-task.html).
```text
An :ref:`asynchronous context manager <async-context-managers>`
   holding a group of tasks.
   Tasks can be added to the group using :meth:`create_task`.
   All tasks are awaited when the context manager exits.
```

## py311v2_test_034

```text
What maximum scheduling delay in milliseconds does Queue.join guarantee after the final task_done call?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_034",
  "question": "What maximum scheduling delay in milliseconds does Queue.join guarantee after the final task_done call?",
  "split": "test",
  "cluster_id": "concurrency",
  "source_document_ids": [
    "py3119.queue"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_006"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"Queue.join\": [\"queue\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.queue_s6356_6590",
      "doc_id": "py3119.queue",
      "start_char": 6356,
      "end_char": 6590,
      "text": "Indicate that a formerly enqueued task is complete.  Used by queue consumer\n   threads.  For each :meth:`get` used to fetch a task, a subsequent call to\n   :meth:`task_done` tells the queue that the processing on the task is complete."
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

py3119.queue_s6356_6590; Unicode [6356, 6590). [Full pinned source](../../sources/queue.rst); [official reader URL](https://docs.python.org/3.11/library/queue.html).
```text
Indicate that a formerly enqueued task is complete.  Used by queue consumer
   threads.  For each :meth:`get` used to fetch a task, a subsequent call to
   :meth:`task_done` tells the queue that the processing on the task is complete.
```

## py311v2_train_059

```text
In Java 21, which Guava Multiset implementation should I use to count concurrently updated inventory?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_059",
  "question": "In Java 21, which Guava Multiset implementation should I use to count concurrently updated inventory?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_002"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.collections_s10099_10473",
      "doc_id": "py3119.collections",
      "start_char": 10099,
      "end_char": 10473,
      "text": "A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.\n    It is a collection where elements are stored as dictionary keys\n    and their counts are stored as dictionary values.  Counts are allowed to be\n    any integer value including zero or negative counts.  The :class:`Counter`\n    class is similar to bags or multisets in other languages."
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

py3119.collections_s10099_10473; Unicode [10099, 10473). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
    It is a collection where elements are stored as dictionary keys
    and their counts are stored as dictionary values.  Counts are allowed to be
    any integer value including zero or negative counts.  The :class:`Counter`
    class is similar to bags or multisets in other languages.
```

## py311v2_train_074

```text
For the third-party multiset.Multiset class rather than collections.Counter, how are negative multiplicities handled?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_074",
  "question": "For the third-party multiset.Multiset class rather than collections.Counter, how are negative multiplicities handled?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_002"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"collections.Counter\": [\"typing\"], \"multiset.Multiset\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.collections_s10099_10473",
      "doc_id": "py3119.collections",
      "start_char": 10099,
      "end_char": 10473,
      "text": "A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.\n    It is a collection where elements are stored as dictionary keys\n    and their counts are stored as dictionary values.  Counts are allowed to be\n    any integer value including zero or negative counts.  The :class:`Counter`\n    class is similar to bags or multisets in other languages."
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

py3119.collections_s10099_10473; Unicode [10099, 10473). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
    It is a collection where elements are stored as dictionary keys
    and their counts are stored as dictionary values.  Counts are allowed to be
    any integer value including zero or negative counts.  The :class:`Counter`
    class is similar to bags or multisets in other languages.
```
