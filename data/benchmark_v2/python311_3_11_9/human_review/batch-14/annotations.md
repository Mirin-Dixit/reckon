# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_train_051

```text
In Python 3.11, what quantity does timedelta.total_seconds return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_051",
  "question": "In Python 3.11, what quantity does timedelta.total_seconds return?",
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
  "expected_answer": "Return the total number of seconds contained in the duration. Equivalent to td / timedelta(seconds=1). For interval units other than seconds, use the division form directly (e.g. td / timedelta(microseconds=1)).",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.datetime_s16347_16572",
      "doc_id": "py3119.datetime",
      "start_char": 16347,
      "end_char": 16572,
      "text": "Return the total number of seconds contained in the duration. Equivalent to\n   ``td / timedelta(seconds=1)``. For interval units other than seconds, use the\n   division form directly (e.g. ``td / timedelta(microseconds=1)``)."
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

py3119.datetime_s16347_16572; Unicode [16347, 16572). [Full pinned source](../../sources/datetime.rst); [official reader URL](https://docs.python.org/3.11/library/datetime.html).
```text
Return the total number of seconds contained in the duration. Equivalent to
   ``td / timedelta(seconds=1)``. For interval units other than seconds, use the
   division form directly (e.g. ``td / timedelta(microseconds=1)``).
```

## py311v2_train_053

```text
In Python 3.11, what two values does calendar.monthrange return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_053",
  "question": "In Python 3.11, what two values does calendar.monthrange return?",
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
  "expected_answer": "Returns weekday of first day of the month and number of days in month, for the specified *year* and *month*.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.calendar_s12020_12132",
      "doc_id": "py3119.calendar",
      "start_char": 12020,
      "end_char": 12132,
      "text": "Returns weekday of first day of the month and number of days in month,  for the\n   specified *year* and *month*."
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

py3119.calendar_s12020_12132; Unicode [12020, 12132). [Full pinned source](../../sources/calendar.rst); [official reader URL](https://docs.python.org/3.11/library/calendar.html).
```text
Returns weekday of first day of the month and number of days in month,  for the
   specified *year* and *month*.
```

## py311v2_train_057

```text
In Python 3.11, what is time.perf_counter intended to measure?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_057",
  "question": "In Python 3.11, what is time.perf_counter intended to measure?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.time"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return the value (in fractional seconds) of a performance counter, i.e. a clock with the highest available resolution to measure a short duration. It does include time elapsed during sleep and is system-wide. The reference point of the returned value is undefined, so that only the difference between the results of two calls is valid.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.time_s11684_12033",
      "doc_id": "py3119.time",
      "start_char": 11684,
      "end_char": 12033,
      "text": "Return the value (in fractional seconds) of a performance counter, i.e. a\n   clock with the highest available resolution to measure a short duration.  It\n   does include time elapsed during sleep and is system-wide.  The reference\n   point of the returned value is undefined, so that only the difference between\n   the results of two calls is valid."
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

py3119.time_s11684_12033; Unicode [11684, 12033). [Full pinned source](../../sources/time.rst); [official reader URL](https://docs.python.org/3.11/library/time.html).
```text
Return the value (in fractional seconds) of a performance counter, i.e. a
   clock with the highest available resolution to measure a short duration.  It
   does include time elapsed during sleep and is system-wide.  The reference
   point of the returned value is undefined, so that only the difference between
   the results of two calls is valid.
```

## py311v2_train_058

```text
In Python 3.11, what type of timezone does zoneinfo.ZoneInfo construct?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_058",
  "question": "In Python 3.11, what type of timezone does zoneinfo.ZoneInfo construct?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.zoneinfo"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "A concrete datetime.tzinfo subclass that represents an IANA time zone specified by the string key. Calls to the primary constructor will always return objects that compare identically; put another way, barring cache invalidation via ZoneInfo.clear_cache, for all values of key, the following assertion will always be true:",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.zoneinfo_s6430_6793",
      "doc_id": "py3119.zoneinfo",
      "start_char": 6430,
      "end_char": 6793,
      "text": "A concrete :class:`datetime.tzinfo` subclass that represents an IANA time\n    zone specified by the string ``key``. Calls to the primary constructor will\n    always return objects that compare identically; put another way, barring\n    cache invalidation via :meth:`ZoneInfo.clear_cache`, for all values of\n    ``key``, the following assertion will always be true:"
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

py3119.zoneinfo_s6430_6793; Unicode [6430, 6793). [Full pinned source](../../sources/zoneinfo.rst); [official reader URL](https://docs.python.org/3.11/library/zoneinfo.html).
```text
A concrete :class:`datetime.tzinfo` subclass that represents an IANA time
    zone specified by the string ``key``. Calls to the primary constructor will
    always return objects that compare identically; put another way, barring
    cache invalidation via :meth:`ZoneInfo.clear_cache`, for all values of
    ``key``, the following assertion will always be true:
```

## py311v2_train_037

```text
In Python 3.11, what does pathlib.Path.read_text return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_037",
  "question": "In Python 3.11, what does pathlib.Path.read_text return?",
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
  "expected_answer": "Return the decoded contents of the pointed-to file as a string.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.pathlib_s31204_31268",
      "doc_id": "py3119.pathlib",
      "start_char": 31204,
      "end_char": 31268,
      "text": "Return the decoded contents of the pointed-to file as a string::"
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

py3119.pathlib_s31204_31268; Unicode [31204, 31268). [Full pinned source](../../sources/pathlib.rst); [official reader URL](https://docs.python.org/3.11/library/pathlib.html).
```text
Return the decoded contents of the pointed-to file as a string::
```

## py311v2_train_038

```text
In Python 3.11, what does pathlib.Path.iterdir yield for a directory?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_038",
  "question": "In Python 3.11, what does pathlib.Path.iterdir yield for a directory?",
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
  "expected_answer": "When the path points to a directory, yield path objects of the directory contents.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.pathlib_s28386_28472",
      "doc_id": "py3119.pathlib",
      "start_char": 28386,
      "end_char": 28472,
      "text": "When the path points to a directory, yield path objects of the directory\n   contents::"
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

py3119.pathlib_s28386_28472; Unicode [28386, 28472). [Full pinned source](../../sources/pathlib.rst); [official reader URL](https://docs.python.org/3.11/library/pathlib.html).
```text
When the path points to a directory, yield path objects of the directory
   contents::
```

## py311v2_train_043

```text
In Python 3.11, what does shutil.rmtree delete?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_043",
  "question": "In Python 3.11, what does shutil.rmtree delete?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.shutil"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Delete an entire directory tree; *path* must point to a directory (but not a symbolic link to a directory). If *ignore_errors* is true, errors resulting from failed removals will be ignored; if false or omitted, such errors are handled by calling a handler specified by *onerror* or, if that is omitted, they raise an exception.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.shutil_s12612_12953",
      "doc_id": "py3119.shutil",
      "start_char": 12612,
      "end_char": 12953,
      "text": "Delete an entire directory tree; *path* must point to a directory (but not a\n   symbolic link to a directory).  If *ignore_errors* is true, errors resulting\n   from failed removals will be ignored; if false or omitted, such errors are\n   handled by calling a handler specified by *onerror* or, if that is omitted,\n   they raise an exception."
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

py3119.shutil_s12612_12953; Unicode [12612, 12953). [Full pinned source](../../sources/shutil.rst); [official reader URL](https://docs.python.org/3.11/library/shutil.html).
```text
Delete an entire directory tree; *path* must point to a directory (but not a
   symbolic link to a directory).  If *ignore_errors* is true, errors resulting
   from failed removals will be ignored; if false or omitted, such errors are
   handled by calling a handler specified by *onerror* or, if that is omitted,
   they raise an exception.
```

## py311v2_train_044

```text
In Python 3.11, what resource does tempfile.TemporaryDirectory create?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_044",
  "question": "In Python 3.11, what resource does tempfile.TemporaryDirectory create?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.tempfile"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "This class securely creates a temporary directory using the same rules as mkdtemp. The resulting object can be used as a context manager (see tempfile-examples). On completion of the context or destruction of the temporary directory object, the newly created temporary directory and all its contents are removed from the filesystem.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.tempfile_s6070_6438",
      "doc_id": "py3119.tempfile",
      "start_char": 6070,
      "end_char": 6438,
      "text": "This class securely creates a temporary directory using the same rules as :func:`mkdtemp`.\n   The resulting object can be used as a :term:`context manager` (see\n   :ref:`tempfile-examples`).  On completion of the context or destruction\n   of the temporary directory object, the newly created temporary directory\n   and all its contents are removed from the filesystem."
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

py3119.tempfile_s6070_6438; Unicode [6070, 6438). [Full pinned source](../../sources/tempfile.rst); [official reader URL](https://docs.python.org/3.11/library/tempfile.html).
```text
This class securely creates a temporary directory using the same rules as :func:`mkdtemp`.
   The resulting object can be used as a :term:`context manager` (see
   :ref:`tempfile-examples`).  On completion of the context or destruction
   of the temporary directory object, the newly created temporary directory
   and all its contents are removed from the filesystem.
```

## py311v2_train_045

```text
In Python 3.11, how does NamedTemporaryFile differ from TemporaryFile in filesystem visibility?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_045",
  "question": "In Python 3.11, how does NamedTemporaryFile differ from TemporaryFile in filesystem visibility?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.tempfile"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "This function operates exactly as TemporaryFile does, except that the file is guaranteed to have a visible name in the file system (on Unix, the directory entry is not unlinked). That name can be retrieved from the name attribute of the returned file-like object. Whether the name can be used to open the file a second time, while the named temporary file is still open, varies across platforms (it can be so used on Unix; it cannot on Windows). If *delete* is true (the default), the file is deleted as soon as it is closed. The returned object is always a file-like object whose !file attribute is the underlying true file object. This file-like object can be used in a with statement, just like a normal file.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.tempfile_s3498_4281",
      "doc_id": "py3119.tempfile",
      "start_char": 3498,
      "end_char": 4281,
      "text": "This function operates exactly as :func:`TemporaryFile` does, except that\n   the file is guaranteed to have a visible name in the file system (on\n   Unix, the directory entry is not unlinked).  That name can be retrieved\n   from the :attr:`name` attribute of the returned\n   file-like object.  Whether the name can be\n   used to open the file a second time, while the named temporary file is\n   still open, varies across platforms (it can be so used on Unix; it cannot\n   on Windows).  If *delete* is true (the default), the file is\n   deleted as soon as it is closed.\n   The returned object is always a file-like object whose :attr:`!file`\n   attribute is the underlying true file object. This file-like object can\n   be used in a :keyword:`with` statement, just like a normal file."
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

py3119.tempfile_s3498_4281; Unicode [3498, 4281). [Full pinned source](../../sources/tempfile.rst); [official reader URL](https://docs.python.org/3.11/library/tempfile.html).
```text
This function operates exactly as :func:`TemporaryFile` does, except that
   the file is guaranteed to have a visible name in the file system (on
   Unix, the directory entry is not unlinked).  That name can be retrieved
   from the :attr:`name` attribute of the returned
   file-like object.  Whether the name can be
   used to open the file a second time, while the named temporary file is
   still open, varies across platforms (it can be so used on Unix; it cannot
   on Windows).  If *delete* is true (the default), the file is
   deleted as soon as it is closed.
   The returned object is always a file-like object whose :attr:`!file`
   attribute is the underlying true file object. This file-like object can
   be used in a :keyword:`with` statement, just like a normal file.
```

## py311v2_train_047

```text
In Python 3.11, what matching and case behavior does fnmatch.fnmatchcase use?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_047",
  "question": "In Python 3.11, what matching and case behavior does fnmatch.fnmatchcase use?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.fnmatch"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Test whether the filename string *name* matches the pattern string *pat*, returning True or False; the comparison is case-sensitive and does not apply os.path.normcase.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.fnmatch_s2695_2885",
      "doc_id": "py3119.fnmatch",
      "start_char": 2695,
      "end_char": 2885,
      "text": "Test whether the filename string *name* matches the pattern string *pat*,\n   returning ``True`` or ``False``;\n   the comparison is case-sensitive and does not apply :func:`os.path.normcase`."
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

py3119.fnmatch_s2695_2885; Unicode [2695, 2885). [Full pinned source](../../sources/fnmatch.rst); [official reader URL](https://docs.python.org/3.11/library/fnmatch.html).
```text
Test whether the filename string *name* matches the pattern string *pat*,
   returning ``True`` or ``False``;
   the comparison is case-sensitive and does not apply :func:`os.path.normcase`.
```
