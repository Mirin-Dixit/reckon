# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_test_019

```text
In Python 3.11, when does subprocess.run return and what result object does it provide?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_019",
  "question": "In Python 3.11, when does subprocess.run return and what result object does it provide?",
  "split": "test",
  "cluster_id": "process-control",
  "source_document_ids": [
    "py3119.subprocess"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Run the command described by *args*. Wait for command to complete, then return a CompletedProcess instance.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.subprocess_s1409_1529",
      "doc_id": "py3119.subprocess",
      "start_char": 1409,
      "end_char": 1529,
      "text": "Run the command described by *args*.  Wait for command to complete, then\n   return a :class:`CompletedProcess` instance."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 1,
  "required_checks": [
    "answerability",
    "evidence",
    "reference_answer",
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

## py311v2_dev_010

```text
In Python 3.11, what input types can json.loads deserialize?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_010",
  "question": "In Python 3.11, what input types can json.loads deserialize?",
  "split": "dev",
  "cluster_id": "serialization",
  "source_document_ids": [
    "py3119.json"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Deserialize *s* (a str, bytes or bytearray instance containing a JSON document) to a Python object using this conversion table .",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.json_s11192_11378",
      "doc_id": "py3119.json",
      "start_char": 11192,
      "end_char": 11378,
      "text": "Deserialize *s* (a :class:`str`, :class:`bytes` or :class:`bytearray`\n   instance containing a JSON document) to a Python object using this\n   :ref:`conversion table <json-to-py-table>`."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 1,
  "required_checks": [
    "answerability",
    "evidence",
    "reference_answer",
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

## py311v2_test_002

```text
In Python 3.11, what operations does asyncio.TaskGroup combine?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_002",
  "question": "In Python 3.11, what operations does asyncio.TaskGroup combine?",
  "split": "test",
  "cluster_id": "concurrency",
  "source_document_ids": [
    "py3119.asyncio-task"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "An asynchronous context manager holding a group of tasks. Tasks can be added to the group using create_task. All tasks are awaited when the context manager exits.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.asyncio-task_s8936_9147",
      "doc_id": "py3119.asyncio-task",
      "start_char": 8936,
      "end_char": 9147,
      "text": "An :ref:`asynchronous context manager <async-context-managers>`\n   holding a group of tasks.\n   Tasks can be added to the group using :meth:`create_task`.\n   All tasks are awaited when the context manager exits."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 1,
  "required_checks": [
    "answerability",
    "evidence",
    "reference_answer",
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

## py311v2_test_003

```text
In Python 3.11, how does asyncio.gather run its awaitables?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_003",
  "question": "In Python 3.11, how does asyncio.gather run its awaitables?",
  "split": "test",
  "cluster_id": "concurrency",
  "source_document_ids": [
    "py3119.asyncio-task"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Run awaitable objects in the *aws* sequence *concurrently*.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.asyncio-task_s12812_12902",
      "doc_id": "py3119.asyncio-task",
      "start_char": 12812,
      "end_char": 12902,
      "text": "Run :ref:`awaitable objects <asyncio-awaitables>` in the *aws*\n   sequence *concurrently*."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 1,
  "required_checks": [
    "answerability",
    "evidence",
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.asyncio-task_s12812_12902; Unicode [12812, 12902). [Full pinned source](../../sources/asyncio-task.rst); [official reader URL](https://docs.python.org/3.11/library/asyncio-task.html).
```text
Run :ref:`awaitable objects <asyncio-awaitables>` in the *aws*
   sequence *concurrently*.
```

## py311v2_test_004

```text
In Python 3.11, what does Executor.submit schedule and return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_004",
  "question": "In Python 3.11, what does Executor.submit schedule and return?",
  "split": "test",
  "cluster_id": "concurrency",
  "source_document_ids": [
    "py3119.concurrent.futures"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Schedules the callable, *fn*, to be executed as fn(*args, **kwargs) and returns a Future object representing the execution of the callable. .",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.concurrent.futures_s1027_1194",
      "doc_id": "py3119.concurrent.futures",
      "start_char": 1027,
      "end_char": 1194,
      "text": "Schedules the callable, *fn*, to be executed as ``fn(*args, **kwargs)``\n      and returns a :class:`Future` object representing the execution of the\n      callable. ::"
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 1,
  "required_checks": [
    "answerability",
    "evidence",
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.concurrent.futures_s1027_1194; Unicode [1027, 1194). [Full pinned source](../../sources/concurrent.futures.rst); [official reader URL](https://docs.python.org/3.11/library/concurrent.futures.html).
```text
Schedules the callable, *fn*, to be executed as ``fn(*args, **kwargs)``
      and returns a :class:`Future` object representing the execution of the
      callable. ::
```

## py311v2_test_005

```text
In Python 3.11, what does Thread.start arrange for the thread object?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_005",
  "question": "In Python 3.11, what does Thread.start arrange for the thread object?",
  "split": "test",
  "cluster_id": "concurrency",
  "source_document_ids": [
    "py3119.threading"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Start the thread's activity. It must be called at most once per thread object. It arranges for the object's Thread.run method to be invoked in a separate thread of control.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.threading_s12961_13162",
      "doc_id": "py3119.threading",
      "start_char": 12961,
      "end_char": 13162,
      "text": "Start the thread's activity.\n\n      It must be called at most once per thread object.  It arranges for the\n      object's :meth:`~Thread.run` method to be invoked in a separate thread\n      of control."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 1,
  "required_checks": [
    "answerability",
    "evidence",
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.threading_s12961_13162; Unicode [12961, 13162). [Full pinned source](../../sources/threading.rst); [official reader URL](https://docs.python.org/3.11/library/threading.html).
```text
Start the thread's activity.

      It must be called at most once per thread object.  It arranges for the
      object's :meth:`~Thread.run` method to be invoked in a separate thread
      of control.
```

## py311v2_test_006

```text
In Python 3.11, what does Queue.task_done signal to the queue?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_006",
  "question": "In Python 3.11, what does Queue.task_done signal to the queue?",
  "split": "test",
  "cluster_id": "concurrency",
  "source_document_ids": [
    "py3119.queue"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Indicate that a formerly enqueued task is complete. Used by queue consumer threads. For each get used to fetch a task, a subsequent call to task_done tells the queue that the processing on the task is complete.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.queue_s6356_6590",
      "doc_id": "py3119.queue",
      "start_char": 6356,
      "end_char": 6590,
      "text": "Indicate that a formerly enqueued task is complete.  Used by queue consumer\n   threads.  For each :meth:`get` used to fetch a task, a subsequent call to\n   :meth:`task_done` tells the queue that the processing on the task is complete."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 1,
  "required_checks": [
    "answerability",
    "evidence",
    "reference_answer",
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

## py311v2_train_001

```text
In Python 3.11, what view does collections.ChainMap provide when combining mappings?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_001",
  "question": "In Python 3.11, what view does collections.ChainMap provide when combining mappings?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "A ChainMap groups multiple dicts or other mappings together to create a single, updateable view. If no *maps* are specified, a single empty dictionary is provided so that a new chain always has at least one mapping.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s1979_2212",
      "doc_id": "py3119.collections",
      "start_char": 1979,
      "end_char": 2212,
      "text": "A :class:`ChainMap` groups multiple dicts or other mappings together to\n    create a single, updateable view.  If no *maps* are specified, a single empty\n    dictionary is provided so that a new chain always has at least one mapping."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 1,
  "required_checks": [
    "answerability",
    "evidence",
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.collections_s1979_2212; Unicode [1979, 2212). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
A :class:`ChainMap` groups multiple dicts or other mappings together to
    create a single, updateable view.  If no *maps* are specified, a single empty
    dictionary is provided so that a new chain always has at least one mapping.
```

## py311v2_train_004

```text
In Python 3.11, how does collections.defaultdict differ from the built-in dict class?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_004",
  "question": "In Python 3.11, how does collections.defaultdict differ from the built-in dict class?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return a new dictionary-like object. defaultdict is a subclass of the built-in dict class. It overrides one method and adds one writable instance variable. The remaining functionality is the same as for the dict class and is not documented here.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s27713_28000",
      "doc_id": "py3119.collections",
      "start_char": 27713,
      "end_char": 28000,
      "text": "Return a new dictionary-like object.  :class:`defaultdict` is a subclass of the\n    built-in :class:`dict` class.  It overrides one method and adds one writable\n    instance variable.  The remaining functionality is the same as for the\n    :class:`dict` class and is not documented here."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 1,
  "required_checks": [
    "answerability",
    "evidence",
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.collections_s27713_28000; Unicode [27713, 28000). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Return a new dictionary-like object.  :class:`defaultdict` is a subclass of the
    built-in :class:`dict` class.  It overrides one method and adds one writable
    instance variable.  The remaining functionality is the same as for the
    :class:`dict` class and is not documented here.
```

## py311v2_train_006

```text
In Python 3.11, what does a named tuple's _make method construct from its argument?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_006",
  "question": "In Python 3.11, what does a named tuple's _make method construct from its argument?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Class method that makes a new instance from an existing sequence or iterable.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s36845_36922",
      "doc_id": "py3119.collections",
      "start_char": 36845,
      "end_char": 36922,
      "text": "Class method that makes a new instance from an existing sequence or iterable."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 1,
  "required_checks": [
    "answerability",
    "evidence",
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.collections_s36845_36922; Unicode [36845, 36922). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Class method that makes a new instance from an existing sequence or iterable.
```
