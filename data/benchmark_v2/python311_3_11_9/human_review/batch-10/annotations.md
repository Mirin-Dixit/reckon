# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_test_001

```text
In Python 3.11, what does asyncio.create_task schedule and return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_001",
  "question": "In Python 3.11, what does asyncio.create_task schedule and return?",
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
  "expected_answer": "Wrap the *coro* coroutine into a Task and schedule its execution. Return the Task object.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.asyncio-task_s5968_6089",
      "doc_id": "py3119.asyncio-task",
      "start_char": 5968,
      "end_char": 6089,
      "text": "Wrap the *coro* :ref:`coroutine <coroutine>` into a :class:`Task`\n   and schedule its execution.  Return the Task object."
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

py3119.asyncio-task_s5968_6089; Unicode [5968, 6089). [Full pinned source](../../sources/asyncio-task.rst); [official reader URL](https://docs.python.org/3.11/library/asyncio-task.html).
```text
Wrap the *coro* :ref:`coroutine <coroutine>` into a :class:`Task`
   and schedule its execution.  Return the Task object.
```

## py311v2_train_003

```text
In Python 3.11, how is a collections.deque initialized from an iterable?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_003",
  "question": "In Python 3.11, how is a collections.deque initialized from an iterable?",
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
  "expected_answer": "Returns a new deque object initialized left-to-right (using append) with data from *iterable*. If *iterable* is not specified, the new deque is empty.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s18929_19092",
      "doc_id": "py3119.collections",
      "start_char": 18929,
      "end_char": 19092,
      "text": "Returns a new deque object initialized left-to-right (using :meth:`append`) with\n    data from *iterable*.  If *iterable* is not specified, the new deque is empty."
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

py3119.collections_s18929_19092; Unicode [18929, 19092). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Returns a new deque object initialized left-to-right (using :meth:`append`) with
    data from *iterable*.  If *iterable* is not specified, the new deque is empty.
```

## py311v2_train_007

```text
In Python 3.11, what mapping does a named tuple's _asdict method return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_007",
  "question": "In Python 3.11, what mapping does a named tuple's _asdict method return?",
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
  "expected_answer": "Return a new dict which maps field names to their corresponding values:",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s37063_37147",
      "doc_id": "py3119.collections",
      "start_char": 37063,
      "end_char": 37147,
      "text": "Return a new :class:`dict` which maps field names to their corresponding\n    values:"
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

py3119.collections_s37063_37147; Unicode [37063, 37147). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Return a new :class:`dict` which maps field names to their corresponding
    values:
```

## py311v2_train_010

```text
In Python 3.11, what is the purpose of collections.UserDict?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_010",
  "question": "In Python 3.11, what is the purpose of collections.UserDict?",
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
  "expected_answer": "Class that simulates a dictionary. The instance's contents are kept in a regular dictionary, which is accessible via the data attribute of UserDict instances. If *initialdata* is provided, data is initialized with its contents; note that a reference to *initialdata* will not be kept, allowing it to be used for other purposes.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s49739_50109",
      "doc_id": "py3119.collections",
      "start_char": 49739,
      "end_char": 50109,
      "text": "Class that simulates a dictionary.  The instance's contents are kept in a\n    regular dictionary, which is accessible via the :attr:`data` attribute of\n    :class:`UserDict` instances.  If *initialdata* is provided, :attr:`data` is\n    initialized with its contents; note that a reference to *initialdata* will not\n    be kept, allowing it to be used for other purposes."
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

py3119.collections_s49739_50109; Unicode [49739, 50109). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Class that simulates a dictionary.  The instance's contents are kept in a
    regular dictionary, which is accessible via the :attr:`data` attribute of
    :class:`UserDict` instances.  If *initialdata* is provided, :attr:`data` is
    initialized with its contents; note that a reference to *initialdata* will not
    be kept, allowing it to be used for other purposes.
```

## py311v2_train_011

```text
In Python 3.11, what is the purpose of collections.UserList?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_011",
  "question": "In Python 3.11, what is the purpose of collections.UserList?",
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
  "expected_answer": "Class that simulates a list. The instance's contents are kept in a regular list, which is accessible via the data attribute of UserList instances. The instance's contents are initially set to a copy of *list*, defaulting to the empty list []. *list* can be any iterable, for example a real Python list or a UserList object.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s50905_51277",
      "doc_id": "py3119.collections",
      "start_char": 50905,
      "end_char": 51277,
      "text": "Class that simulates a list.  The instance's contents are kept in a regular\n    list, which is accessible via the :attr:`data` attribute of :class:`UserList`\n    instances.  The instance's contents are initially set to a copy of *list*,\n    defaulting to the empty list ``[]``.  *list* can be any iterable, for\n    example a real Python list or a :class:`UserList` object."
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

py3119.collections_s50905_51277; Unicode [50905, 51277). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Class that simulates a list.  The instance's contents are kept in a regular
    list, which is accessible via the :attr:`data` attribute of :class:`UserList`
    instances.  The instance's contents are initially set to a copy of *list*,
    defaulting to the empty list ``[]``.  *list* can be any iterable, for
    example a real Python list or a :class:`UserList` object.
```

## py311v2_train_025

```text
In Python 3.11, what conversion does dataclasses.asdict perform on a dataclass instance?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_025",
  "question": "In Python 3.11, what conversion does dataclasses.asdict perform on a dataclass instance?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.dataclasses"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Converts the dataclass obj to a dict (by using the factory function dict_factory). Each dataclass is converted to a dict of its fields, as name: value pairs. dataclasses, dicts, lists, and tuples are recursed into. Other objects are copied with copy.deepcopy.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.dataclasses_s14907_15201",
      "doc_id": "py3119.dataclasses",
      "start_char": 14907,
      "end_char": 15201,
      "text": "Converts the dataclass ``obj`` to a dict (by using the\n   factory function ``dict_factory``).  Each dataclass is converted\n   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,\n   lists, and tuples are recursed into.  Other objects are copied with\n   :func:`copy.deepcopy`."
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

py3119.dataclasses_s14907_15201; Unicode [14907, 15201). [Full pinned source](../../sources/dataclasses.rst); [official reader URL](https://docs.python.org/3.11/library/dataclasses.html).
```text
Converts the dataclass ``obj`` to a dict (by using the
   factory function ``dict_factory``).  Each dataclass is converted
   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,
   lists, and tuples are recursed into.  Other objects are copied with
   :func:`copy.deepcopy`.
```

## py311v2_train_027

```text
In Python 3.11, how does dataclasses.replace create its result?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_027",
  "question": "In Python 3.11, how does dataclasses.replace create its result?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.dataclasses"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Creates a new object of the same type as obj, replacing fields with values from changes. If obj is not a Data Class, raises TypeError. If values in changes do not specify fields, raises TypeError.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.dataclasses_s18041_18278",
      "doc_id": "py3119.dataclasses",
      "start_char": 18041,
      "end_char": 18278,
      "text": "Creates a new object of the same type as ``obj``, replacing\n   fields with values from ``changes``.  If ``obj`` is not a Data\n   Class, raises :exc:`TypeError`.  If values in ``changes`` do not\n   specify fields, raises :exc:`TypeError`."
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

py3119.dataclasses_s18041_18278; Unicode [18041, 18278). [Full pinned source](../../sources/dataclasses.rst); [official reader URL](https://docs.python.org/3.11/library/dataclasses.html).
```text
Creates a new object of the same type as ``obj``, replacing
   fields with values from ``changes``.  If ``obj`` is not a Data
   Class, raises :exc:`TypeError`.  If values in ``changes`` do not
   specify fields, raises :exc:`TypeError`.
```

## py311v2_train_029

```text
In Python 3.11, what kind of copy does copy.copy return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_029",
  "question": "In Python 3.11, what kind of copy does copy.copy return?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.copy"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return a shallow copy of *x*.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.copy_s597_626",
      "doc_id": "py3119.copy",
      "start_char": 597,
      "end_char": 626,
      "text": "Return a shallow copy of *x*."
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

py3119.copy_s597_626; Unicode [597, 626). [Full pinned source](../../sources/copy.rst); [official reader URL](https://docs.python.org/3.11/library/copy.html).
```text
Return a shallow copy of *x*.
```

## py311v2_train_030

```text
In Python 3.11, what kind of copy does copy.deepcopy return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_030",
  "question": "In Python 3.11, what kind of copy does copy.deepcopy return?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.copy"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return a deep copy of *x*.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.copy_s667_693",
      "doc_id": "py3119.copy",
      "start_char": 667,
      "end_char": 693,
      "text": "Return a deep copy of *x*."
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

py3119.copy_s667_693; Unicode [667, 693). [Full pinned source](../../sources/copy.rst); [official reader URL](https://docs.python.org/3.11/library/copy.html).
```text
Return a deep copy of *x*.
```

## py311v2_test_013

```text
In Python 3.11, what operation does sqlite3.connect perform?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_013",
  "question": "In Python 3.11, what operation does sqlite3.connect perform?",
  "split": "test",
  "cluster_id": "database",
  "source_document_ids": [
    "py3119.sqlite3"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Open a connection to an SQLite database.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.sqlite3_s8959_8999",
      "doc_id": "py3119.sqlite3",
      "start_char": 8959,
      "end_char": 8999,
      "text": "Open a connection to an SQLite database."
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

py3119.sqlite3_s8959_8999; Unicode [8959, 8999). [Full pinned source](../../sources/sqlite3.rst); [official reader URL](https://docs.python.org/3.11/library/sqlite3.html).
```text
Open a connection to an SQLite database.
```
