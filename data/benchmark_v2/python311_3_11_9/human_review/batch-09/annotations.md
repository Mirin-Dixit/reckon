# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_train_054

```text
In Python 3.11, what does calendar.isleap determine?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_054",
  "question": "In Python 3.11, what does calendar.isleap determine?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.calendar"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Returns True if *year* is a leap year, otherwise False.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.calendar_s11375_11448",
      "doc_id": "py3119.calendar",
      "start_char": 11375,
      "end_char": 11448,
      "text": "Returns :const:`True` if *year* is a leap year, otherwise :const:`False`."
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

py3119.calendar_s11375_11448; Unicode [11375, 11448). [Full pinned source](../../sources/calendar.rst); [official reader URL](https://docs.python.org/3.11/library/calendar.html).
```text
Returns :const:`True` if *year* is a leap year, otherwise :const:`False`.
```

## py311v2_train_055

```text
In Python 3.11, what weekday numbering does calendar.weekday use?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_055",
  "question": "In Python 3.11, what weekday numbering does calendar.weekday use?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.calendar"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Returns the day of the week (0 is Monday) for *year* (1970--...), *month* (1--12), *day* (1--31).",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.calendar_s11705_11829",
      "doc_id": "py3119.calendar",
      "start_char": 11705,
      "end_char": 11829,
      "text": "Returns the day of the week (``0`` is Monday) for *year* (``1970``--...),\n   *month* (``1``--``12``), *day* (``1``--``31``)."
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

py3119.calendar_s11705_11829; Unicode [11705, 11829). [Full pinned source](../../sources/calendar.rst); [official reader URL](https://docs.python.org/3.11/library/calendar.html).
```text
Returns the day of the week (``0`` is Monday) for *year* (``1970``--...),
   *month* (``1``--``12``), *day* (``1``--``31``).
```

## py311v2_train_040

```text
In Python 3.11, what representation does PurePath.as_posix return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_040",
  "question": "In Python 3.11, what representation does PurePath.as_posix return?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.pathlib"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return a string representation of the path with forward slashes (/).",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.pathlib_s12974_13047",
      "doc_id": "py3119.pathlib",
      "start_char": 12974,
      "end_char": 13047,
      "text": "Return a string representation of the path with forward slashes (``/``)::"
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

py3119.pathlib_s12974_13047; Unicode [12974, 13047). [Full pinned source](../../sources/pathlib.rst); [official reader URL](https://docs.python.org/3.11/library/pathlib.html).
```text
Return a string representation of the path with forward slashes (``/``)::
```

## py311v2_train_046

```text
In Python 3.11, what paths does glob.glob return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_046",
  "question": "In Python 3.11, what paths does glob.glob return?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.glob"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return a possibly empty list of path names that match *pathname*, which must be a string containing a path specification. *pathname* can be either absolute (like /usr/src/Python-1.5/Makefile) or relative (like ../../Tools/\\*/\\*.gif), and can contain shell-style wildcards. Broken symlinks are included in the results (as in the shell). Whether or not the results are sorted depends on the file system. If a file that satisfies conditions is removed or added during the call of this function, whether a path name for that file be included is unspecified.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.glob_s1621_2212",
      "doc_id": "py3119.glob",
      "start_char": 1621,
      "end_char": 2212,
      "text": "Return a possibly empty list of path names that match *pathname*, which must be\n   a string containing a path specification. *pathname* can be either absolute\n   (like :file:`/usr/src/Python-1.5/Makefile`) or relative (like\n   :file:`../../Tools/\\*/\\*.gif`), and can contain shell-style wildcards. Broken\n   symlinks are included in the results (as in the shell). Whether or not the\n   results are sorted depends on the file system.  If a file that satisfies\n   conditions is removed or added during the call of this function, whether\n   a path name for that file be included is unspecified."
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

py3119.glob_s1621_2212; Unicode [1621, 2212). [Full pinned source](../../sources/glob.rst); [official reader URL](https://docs.python.org/3.11/library/glob.html).
```text
Return a possibly empty list of path names that match *pathname*, which must be
   a string containing a path specification. *pathname* can be either absolute
   (like :file:`/usr/src/Python-1.5/Makefile`) or relative (like
   :file:`../../Tools/\*/\*.gif`), and can contain shell-style wildcards. Broken
   symlinks are included in the results (as in the shell). Whether or not the
   results are sorted depends on the file system.  If a file that satisfies
   conditions is removed or added during the call of this function, whether
   a path name for that file be included is unspecified.
```

## py311v2_train_016

```text
In Python 3.11, how does itertools.dropwhile use its predicate to start yielding elements?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_016",
  "question": "In Python 3.11, how does itertools.dropwhile use its predicate to start yielding elements?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.itertools"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Make an iterator that drops elements from the iterable as long as the predicate is true; afterwards, returns every element. Note, the iterator does not produce *any* output until the predicate first becomes false, so it may have a lengthy start-up time. Roughly equivalent to.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.itertools_s16413_16701",
      "doc_id": "py3119.itertools",
      "start_char": 16413,
      "end_char": 16701,
      "text": "Make an iterator that drops elements from the iterable as long as the predicate\n   is true; afterwards, returns every element.  Note, the iterator does not produce\n   *any* output until the predicate first becomes false, so it may have a lengthy\n   start-up time.  Roughly equivalent to::"
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

py3119.itertools_s16413_16701; Unicode [16413, 16701). [Full pinned source](../../sources/itertools.rst); [official reader URL](https://docs.python.org/3.11/library/itertools.html).
```text
Make an iterator that drops elements from the iterable as long as the predicate
   is true; afterwards, returns every element.  Note, the iterator does not produce
   *any* output until the predicate first becomes false, so it may have a lengthy
   start-up time.  Roughly equivalent to::
```

## py311v2_train_018

```text
In Python 3.11, what does itertools.repeat produce when times is omitted?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_018",
  "question": "In Python 3.11, what does itertools.repeat produce when times is omitted?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.itertools"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Make an iterator that returns *object* over and over again. Runs indefinitely unless the *times* argument is specified.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.itertools_s26316_26438",
      "doc_id": "py3119.itertools",
      "start_char": 26316,
      "end_char": 26438,
      "text": "Make an iterator that returns *object* over and over again. Runs indefinitely\n   unless the *times* argument is specified."
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

py3119.itertools_s26316_26438; Unicode [26316, 26438). [Full pinned source](../../sources/itertools.rst); [official reader URL](https://docs.python.org/3.11/library/itertools.html).
```text
Make an iterator that returns *object* over and over again. Runs indefinitely
   unless the *times* argument is specified.
```

## py311v2_train_024

```text
In Python 3.11, what does operator.itemgetter construct?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_024",
  "question": "In Python 3.11, what does operator.itemgetter construct?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.operator"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return a callable object that fetches *item* from its operand using the operand's object.__getitem__ method. If multiple items are specified, returns a tuple of lookup values. For example:",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.operator_s7588_7793",
      "doc_id": "py3119.operator",
      "start_char": 7588,
      "end_char": 7793,
      "text": "Return a callable object that fetches *item* from its operand using the\n   operand's :meth:`~object.__getitem__` method.  If multiple items are specified,\n   returns a tuple of lookup values.  For example:"
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

py3119.operator_s7588_7793; Unicode [7588, 7793). [Full pinned source](../../sources/operator.rst); [official reader URL](https://docs.python.org/3.11/library/operator.html).
```text
Return a callable object that fetches *item* from its operand using the
   operand's :meth:`~object.__getitem__` method.  If multiple items are specified,
   returns a tuple of lookup values.  For example:
```

## py311v2_dev_006

```text
In Python 3.11, what arithmetic statistic does statistics.mean return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_006",
  "question": "In Python 3.11, what arithmetic statistic does statistics.mean return?",
  "split": "dev",
  "cluster_id": "numeric",
  "source_document_ids": [
    "py3119.statistics"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return the sample arithmetic mean of *data* which can be a sequence or iterable.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.statistics_s4874_4954",
      "doc_id": "py3119.statistics",
      "start_char": 4874,
      "end_char": 4954,
      "text": "Return the sample arithmetic mean of *data* which can be a sequence or iterable."
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

py3119.statistics_s4874_4954; Unicode [4874, 4954). [Full pinned source](../../sources/statistics.rst); [official reader URL](https://docs.python.org/3.11/library/statistics.html).
```text
Return the sample arithmetic mean of *data* which can be a sequence or iterable.
```

## py311v2_test_021

```text
In Python 3.11, how does subprocess.check_call handle a successful command or a nonzero exit?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_021",
  "question": "In Python 3.11, how does subprocess.check_call handle a successful command or a nonzero exit?",
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
  "expected_answer": "Run command with arguments. Wait for command to complete. If the return code was zero then return, otherwise raise CalledProcessError. The CalledProcessError object will have the return code in the CalledProcessError.returncode attribute. If check_call was unable to start the process it will propagate the exception that was raised.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.subprocess_s47514_47894",
      "doc_id": "py3119.subprocess",
      "start_char": 47514,
      "end_char": 47894,
      "text": "Run command with arguments.  Wait for command to complete. If the return\n   code was zero then return, otherwise raise :exc:`CalledProcessError`. The\n   :exc:`CalledProcessError` object will have the return code in the\n   :attr:`~CalledProcessError.returncode` attribute.\n   If :func:`check_call` was unable to start the process it will propagate the exception\n   that was raised."
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

py3119.subprocess_s47514_47894; Unicode [47514, 47894). [Full pinned source](../../sources/subprocess.rst); [official reader URL](https://docs.python.org/3.11/library/subprocess.html).
```text
Run command with arguments.  Wait for command to complete. If the return
   code was zero then return, otherwise raise :exc:`CalledProcessError`. The
   :exc:`CalledProcessError` object will have the return code in the
   :attr:`~CalledProcessError.returncode` attribute.
   If :func:`check_call` was unable to start the process it will propagate the exception
   that was raised.
```

## py311v2_dev_009

```text
In Python 3.11, what output type does json.dumps return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_009",
  "question": "In Python 3.11, what output type does json.dumps return?",
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
  "expected_answer": "Serialize *obj* to a JSON formatted str using this conversion table . The arguments have the same meaning as in dump.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.json_s7671_7837",
      "doc_id": "py3119.json",
      "start_char": 7671,
      "end_char": 7837,
      "text": "Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion\n   table <py-to-json-table>`.  The arguments have the same meaning as in\n   :func:`dump`."
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

py3119.json_s7671_7837; Unicode [7671, 7837). [Full pinned source](../../sources/json.rst); [official reader URL](https://docs.python.org/3.11/library/json.html).
```text
Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion
   table <py-to-json-table>`.  The arguments have the same meaning as in
   :func:`dump`.
```
