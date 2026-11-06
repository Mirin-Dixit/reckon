# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_dev_008

```text
For numeric data, what does taking the low or high median return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_008",
  "question": "For numeric data, what does taking the low or high median return?",
  "split": "dev",
  "cluster_id": "numeric",
  "source_document_ids": [
    "py3119.statistics"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "qualified_answer",
  "ambiguity_interpretations": [
    "statistics.median_low",
    "statistics.median_high"
  ],
  "expected_answer": "statistics.median_low: Return the low median of numeric data. If *data* is empty, StatisticsError is raised. *data* can be a sequence or iterable.; statistics.median_high: Return the high median of data. If *data* is empty, StatisticsError is raised. *data* can be a sequence or iterable.",
  "expected_safe_behavior": "Give a qualified answer for both documented interpretations, clearly naming each. Do not claim either is the confirmed intended meaning.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.statistics_s10422_10557",
      "doc_id": "py3119.statistics",
      "start_char": 10422,
      "end_char": 10557,
      "text": "Return the low median of numeric data.  If *data* is empty,\n   :exc:`StatisticsError` is raised.  *data* can be a sequence or iterable."
    },
    {
      "id": "py3119.statistics_s11029_11157",
      "doc_id": "py3119.statistics",
      "start_char": 11029,
      "end_char": 11157,
      "text": "Return the high median of data.  If *data* is empty, :exc:`StatisticsError`\n   is raised.  *data* can be a sequence or iterable."
    }
  ],
  "diagnostic_spans": [],
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
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.statistics_s10422_10557; Unicode [10422, 10557). [Full pinned source](../../sources/statistics.rst); [official reader URL](https://docs.python.org/3.11/library/statistics.html).
```text
Return the low median of numeric data.  If *data* is empty,
   :exc:`StatisticsError` is raised.  *data* can be a sequence or iterable.
```

py3119.statistics_s11029_11157; Unicode [11029, 11157). [Full pinned source](../../sources/statistics.rst); [official reader URL](https://docs.python.org/3.11/library/statistics.html).
```text
Return the high median of data.  If *data* is empty, :exc:`StatisticsError`
   is raised.  *data* can be a sequence or iterable.
```

## py311v2_test_024

```text
How do Popen.poll and Popen.wait differ when a child process is still running?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_024",
  "question": "How do Popen.poll and Popen.wait differ when a child process is still running?",
  "split": "test",
  "cluster_id": "process-control",
  "source_document_ids": [
    "py3119.subprocess"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "compound",
  "is_compound": true,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Check if child process has terminated. Set and return Popen.returncode attribute. Otherwise, returns None. Wait for child process to terminate. Set and return Popen.returncode attribute.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.subprocess_s32713_32836",
      "doc_id": "py3119.subprocess",
      "start_char": 32713,
      "end_char": 32836,
      "text": "Check if child process has terminated.  Set and return\n   :attr:`~Popen.returncode` attribute. Otherwise, returns ``None``."
    },
    {
      "id": "py3119.subprocess_s32880_32972",
      "doc_id": "py3119.subprocess",
      "start_char": 32880,
      "end_char": 32972,
      "text": "Wait for child process to terminate.  Set and return\n   :attr:`~Popen.returncode` attribute."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [
    "py3119.subprocess_s32713_32836",
    "py3119.subprocess_s32880_32972"
  ],
  "compound_missing_premises": [],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "compound",
    "evidence",
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.subprocess_s32713_32836; Unicode [32713, 32836). [Full pinned source](../../sources/subprocess.rst); [official reader URL](https://docs.python.org/3.11/library/subprocess.html).
```text
Check if child process has terminated.  Set and return
   :attr:`~Popen.returncode` attribute. Otherwise, returns ``None``.
```

py3119.subprocess_s32880_32972; Unicode [32880, 32972). [Full pinned source](../../sources/subprocess.rst); [official reader URL](https://docs.python.org/3.11/library/subprocess.html).
```text
Wait for child process to terminate.  Set and return
   :attr:`~Popen.returncode` attribute.
```

## py311v2_train_002

```text
In Python 3.11, how does collections.Counter represent objects and their counts?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_002",
  "question": "In Python 3.11, how does collections.Counter represent objects and their counts?",
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
  "expected_answer": "A Counter is a dict subclass for counting hashable objects. It is a collection where elements are stored as dictionary keys and their counts are stored as dictionary values. Counts are allowed to be any integer value including zero or negative counts. The Counter class is similar to bags or multisets in other languages.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s10099_10473",
      "doc_id": "py3119.collections",
      "start_char": 10099,
      "end_char": 10473,
      "text": "A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.\n    It is a collection where elements are stored as dictionary keys\n    and their counts are stored as dictionary values.  Counts are allowed to be\n    any integer value including zero or negative counts.  The :class:`Counter`\n    class is similar to bags or multisets in other languages."
    }
  ],
  "diagnostic_spans": [],
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
    "reference_answer",
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

## py311v2_train_034

```text
In Python 3.11, what value does typing.cast return, and does it check types at runtime?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_034",
  "question": "In Python 3.11, what value does typing.cast return, and does it check types at runtime?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.typing"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "This returns the value unchanged. To the type checker this signals that the return value has the designated type, but at runtime we intentionally don't check anything (we want this to be as fast as possible).",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.typing_s74585_74803",
      "doc_id": "py3119.typing",
      "start_char": 74585,
      "end_char": 74803,
      "text": "This returns the value unchanged.  To the type checker this\n   signals that the return value has the designated type, but at\n   runtime we intentionally don't check anything (we want this\n   to be as fast as possible)."
    }
  ],
  "diagnostic_spans": [],
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
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.typing_s74585_74803; Unicode [74585, 74803). [Full pinned source](../../sources/typing.rst); [official reader URL](https://docs.python.org/3.11/library/typing.html).
```text
This returns the value unchanged.  To the type checker this
   signals that the return value has the designated type, but at
   runtime we intentionally don't check anything (we want this
   to be as fast as possible).
```

## py311v2_train_052

```text
In Python 3.11, what result type does datetime.fromisoformat construct from a date string?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_052",
  "question": "In Python 3.11, what result type does datetime.fromisoformat construct from a date string?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.datetime"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return a .datetime corresponding to a *date_string* in any valid ISO 8601 format, with the following exceptions:",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.datetime_s36638_36762",
      "doc_id": "py3119.datetime",
      "start_char": 36638,
      "end_char": 36762,
      "text": "Return a :class:`.datetime` corresponding to a *date_string* in any valid\n   ISO 8601 format, with the following exceptions:"
    }
  ],
  "diagnostic_spans": [],
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
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.datetime_s36638_36762; Unicode [36638, 36762). [Full pinned source](../../sources/datetime.rst); [official reader URL](https://docs.python.org/3.11/library/datetime.html).
```text
Return a :class:`.datetime` corresponding to a *date_string* in any valid
   ISO 8601 format, with the following exceptions:
```

## py311v2_test_023

```text
In Python 3.11, what does subprocess.Popen.poll check and return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_023",
  "question": "In Python 3.11, what does subprocess.Popen.poll check and return?",
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
  "expected_answer": "Check if child process has terminated. Set and return Popen.returncode attribute. Otherwise, returns None.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.subprocess_s32713_32836",
      "doc_id": "py3119.subprocess",
      "start_char": 32713,
      "end_char": 32836,
      "text": "Check if child process has terminated.  Set and return\n   :attr:`~Popen.returncode` attribute. Otherwise, returns ``None``."
    }
  ],
  "diagnostic_spans": [],
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
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.subprocess_s32713_32836; Unicode [32713, 32836). [Full pinned source](../../sources/subprocess.rst); [official reader URL](https://docs.python.org/3.11/library/subprocess.html).
```text
Check if child process has terminated.  Set and return
   :attr:`~Popen.returncode` attribute. Otherwise, returns ``None``.
```

## py311v2_train_005

```text
In Python 3.11, what kind of class does collections.namedtuple create?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_005",
  "question": "In Python 3.11, what kind of class does collections.namedtuple create?",
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
  "expected_answer": "Returns a new tuple subclass named *typename*. The new subclass is used to create tuple-like objects that have fields accessible by attribute lookup as well as being indexable and iterable. Instances of the subclass also have a helpful docstring (with typename and field_names) and a helpful __repr__ method which lists the tuple contents in a name=value format.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s32914_33306",
      "doc_id": "py3119.collections",
      "start_char": 32914,
      "end_char": 33306,
      "text": "Returns a new tuple subclass named *typename*.  The new subclass is used to\n    create tuple-like objects that have fields accessible by attribute lookup as\n    well as being indexable and iterable.  Instances of the subclass also have a\n    helpful docstring (with typename and field_names) and a helpful :meth:`__repr__`\n    method which lists the tuple contents in a ``name=value`` format."
    }
  ],
  "diagnostic_spans": [],
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
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.collections_s32914_33306; Unicode [32914, 33306). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Returns a new tuple subclass named *typename*.  The new subclass is used to
    create tuple-like objects that have fields accessible by attribute lookup as
    well as being indexable and iterable.  Instances of the subclass also have a
    helpful docstring (with typename and field_names) and a helpful :meth:`__repr__`
    method which lists the tuple contents in a ``name=value`` format.
```

## py311v2_train_028

```text
In Python 3.11, which objects make dataclasses.is_dataclass return true?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_028",
  "question": "In Python 3.11, which objects make dataclasses.is_dataclass return true?",
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
  "expected_answer": "Return True if its parameter is a dataclass or an instance of one, otherwise return False.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.dataclasses_s19357_19458",
      "doc_id": "py3119.dataclasses",
      "start_char": 19357,
      "end_char": 19458,
      "text": "Return ``True`` if its parameter is a dataclass or an instance of one,\n   otherwise return ``False``."
    }
  ],
  "diagnostic_spans": [],
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
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.dataclasses_s19357_19458; Unicode [19357, 19458). [Full pinned source](../../sources/dataclasses.rst); [official reader URL](https://docs.python.org/3.11/library/dataclasses.html).
```text
Return ``True`` if its parameter is a dataclass or an instance of one,
   otherwise return ``False``.
```

## py311v2_train_031

```text
In Python 3.11, what does the enum.unique class decorator enforce?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_031",
  "question": "In Python 3.11, what does the enum.unique class decorator enforce?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.enum"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "A class decorator specifically for enumerations. It searches an enumeration's EnumType.__members__, gathering any aliases it finds; if any are found ValueError is raised with the details.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.enum_s27536_27758",
      "doc_id": "py3119.enum",
      "start_char": 27536,
      "end_char": 27758,
      "text": "A :keyword:`class` decorator specifically for enumerations.  It searches an\n   enumeration's :attr:`~EnumType.__members__`, gathering any aliases it finds; if any are\n   found :exc:`ValueError` is raised with the details::"
    }
  ],
  "diagnostic_spans": [],
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
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.enum_s27536_27758; Unicode [27536, 27758). [Full pinned source](../../sources/enum.rst); [official reader URL](https://docs.python.org/3.11/library/enum.html).
```text
A :keyword:`class` decorator specifically for enumerations.  It searches an
   enumeration's :attr:`~EnumType.__members__`, gathering any aliases it finds; if any are
   found :exc:`ValueError` is raised with the details::
```

## py311v2_test_015

```text
In Python 3.11, what does sqlite3.Connection.cursor create?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_015",
  "question": "In Python 3.11, what does sqlite3.Connection.cursor create?",
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
  "expected_answer": "Create and return a Cursor object. The cursor method accepts a single optional parameter *factory*. If supplied, this must be a callable returning an instance of Cursor or its subclasses.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.sqlite3_s20751_20982",
      "doc_id": "py3119.sqlite3",
      "start_char": 20751,
      "end_char": 20982,
      "text": "Create and return a :class:`Cursor` object.\n      The cursor method accepts a single optional parameter *factory*. If\n      supplied, this must be a :term:`callable` returning\n      an instance of :class:`Cursor` or its subclasses."
    }
  ],
  "diagnostic_spans": [],
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
    "reference_answer",
    "source",
    "split"
  ]
}
```
### Exact source passages

py3119.sqlite3_s20751_20982; Unicode [20751, 20982). [Full pinned source](../../sources/sqlite3.rst); [official reader URL](https://docs.python.org/3.11/library/sqlite3.html).
```text
Create and return a :class:`Cursor` object.
      The cursor method accepts a single optional parameter *factory*. If
      supplied, this must be a :term:`callable` returning
      an instance of :class:`Cursor` or its subclasses.
```
