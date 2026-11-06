# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_dev_002

```text
In Python 3.11, what integer does math.isqrt return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_002",
  "question": "In Python 3.11, what integer does math.isqrt return?",
  "split": "dev",
  "cluster_id": "numeric",
  "source_document_ids": [
    "py3119.math"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return the integer square root of the nonnegative integer *n*. This is the floor of the exact square root of *n*, or equivalently the greatest integer *a* such that *a*\\ ² |nbsp| ≤ |nbsp| *n*.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.math_s6931_7129",
      "doc_id": "py3119.math",
      "start_char": 6931,
      "end_char": 7129,
      "text": "Return the integer square root of the nonnegative integer *n*. This is the\n   floor of the exact square root of *n*, or equivalently the greatest integer\n   *a* such that *a*\\ ² |nbsp| ≤ |nbsp| *n*."
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

py3119.math_s6931_7129; Unicode [6931, 7129). [Full pinned source](../../sources/math.rst); [official reader URL](https://docs.python.org/3.11/library/math.html).
```text
Return the integer square root of the nonnegative integer *n*. This is the
   floor of the exact square root of *n*, or equivalently the greatest integer
   *a* such that *a*\ ² |nbsp| ≤ |nbsp| *n*.
```

## py311v2_dev_003

```text
In Python 3.11, what does math.fsum compute while tracking partial sums?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_003",
  "question": "In Python 3.11, what does math.fsum compute while tracking partial sums?",
  "split": "dev",
  "cluster_id": "numeric",
  "source_document_ids": [
    "py3119.math"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return an accurate floating point sum of values in the iterable. Avoids loss of precision by tracking multiple intermediate partial sums.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.math_s3899_4041",
      "doc_id": "py3119.math",
      "start_char": 3899,
      "end_char": 4041,
      "text": "Return an accurate floating point sum of values in the iterable.  Avoids\n   loss of precision by tracking multiple intermediate partial sums::"
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

py3119.math_s3899_4041; Unicode [3899, 4041). [Full pinned source](../../sources/math.rst); [official reader URL](https://docs.python.org/3.11/library/math.html).
```text
Return an accurate floating point sum of values in the iterable.  Avoids
   loss of precision by tracking multiple intermediate partial sums::
```

## py311v2_dev_004

```text
In Python 3.11, which input types does Decimal.from_float accept?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_004",
  "question": "In Python 3.11, which input types does Decimal.from_float accept?",
  "split": "dev",
  "cluster_id": "numeric",
  "source_document_ids": [
    "py3119.decimal"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Alternative constructor that only accepts instances of float or int.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.decimal_s22462_22554",
      "doc_id": "py3119.decimal",
      "start_char": 22462,
      "end_char": 22554,
      "text": "Alternative constructor that only accepts instances of :class:`float` or\n      :class:`int`."
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

py3119.decimal_s22462_22554; Unicode [22462, 22554). [Full pinned source](../../sources/decimal.rst); [official reader URL](https://docs.python.org/3.11/library/decimal.html).
```text
Alternative constructor that only accepts instances of :class:`float` or
      :class:`int`.
```

## py311v2_dev_005

```text
In Python 3.11, how does Fraction.limit_denominator approximate its input?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_005",
  "question": "In Python 3.11, how does Fraction.limit_denominator approximate its input?",
  "split": "dev",
  "cluster_id": "numeric",
  "source_document_ids": [
    "py3119.fractions"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Finds and returns the closest Fraction to self that has denominator at most max_denominator. This method is useful for finding rational approximations to a given floating-point number:",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.fractions_s5093_5303",
      "doc_id": "py3119.fractions",
      "start_char": 5093,
      "end_char": 5303,
      "text": "Finds and returns the closest :class:`Fraction` to ``self`` that has\n      denominator at most max_denominator.  This method is useful for finding\n      rational approximations to a given floating-point number:"
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

py3119.fractions_s5093_5303; Unicode [5093, 5303). [Full pinned source](../../sources/fractions.rst); [official reader URL](https://docs.python.org/3.11/library/fractions.html).
```text
Finds and returns the closest :class:`Fraction` to ``self`` that has
      denominator at most max_denominator.  This method is useful for finding
      rational approximations to a given floating-point number:
```

## py311v2_test_020

```text
In Python 3.11, what does subprocess.Popen execute?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_020",
  "question": "In Python 3.11, what does subprocess.Popen execute?",
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
  "expected_answer": "Execute a child program in a new process. On POSIX, the class uses os.execvpe-like behavior to execute the child program. On Windows, the class uses the Windows CreateProcess() function. The arguments to Popen are as follows.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.subprocess_s14449_14707",
      "doc_id": "py3119.subprocess",
      "start_char": 14449,
      "end_char": 14707,
      "text": "Execute a child program in a new process.  On POSIX, the class uses\n   :meth:`os.execvpe`-like behavior to execute the child program.  On Windows,\n   the class uses the Windows ``CreateProcess()`` function.  The arguments to\n   :class:`Popen` are as follows."
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

py3119.subprocess_s14449_14707; Unicode [14449, 14707). [Full pinned source](../../sources/subprocess.rst); [official reader URL](https://docs.python.org/3.11/library/subprocess.html).
```text
Execute a child program in a new process.  On POSIX, the class uses
   :meth:`os.execvpe`-like behavior to execute the child program.  On Windows,
   the class uses the Windows ``CreateProcess()`` function.  The arguments to
   :class:`Popen` are as follows.
```

## py311v2_test_022

```text
In Python 3.11, what does subprocess.check_output return, and what happens on nonzero exit?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_022",
  "question": "In Python 3.11, what does subprocess.check_output return, and what happens on nonzero exit?",
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
  "expected_answer": "Run command with arguments and return its output. If the return code was non-zero it raises a CalledProcessError. The CalledProcessError object will have the return code in the CalledProcessError.returncode attribute and any output in the CalledProcessError.output attribute.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.subprocess_s49226_49546",
      "doc_id": "py3119.subprocess",
      "start_char": 49226,
      "end_char": 49546,
      "text": "Run command with arguments and return its output.\n\n   If the return code was non-zero it raises a :exc:`CalledProcessError`. The\n   :exc:`CalledProcessError` object will have the return code in the\n   :attr:`~CalledProcessError.returncode` attribute and any output in the\n   :attr:`~CalledProcessError.output` attribute."
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

py3119.subprocess_s49226_49546; Unicode [49226, 49546). [Full pinned source](../../sources/subprocess.rst); [official reader URL](https://docs.python.org/3.11/library/subprocess.html).
```text
Run command with arguments and return its output.

   If the return code was non-zero it raises a :exc:`CalledProcessError`. The
   :exc:`CalledProcessError` object will have the return code in the
   :attr:`~CalledProcessError.returncode` attribute and any output in the
   :attr:`~CalledProcessError.output` attribute.
```

## py311v2_dev_011

```text
In Python 3.11, where does json.dump write a serialized object?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_011",
  "question": "In Python 3.11, where does json.dump write a serialized object?",
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
  "expected_answer": "Serialize *obj* as a JSON formatted stream to *fp* (a .write()-supporting file-like object) using this conversion table .",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.json_s4291_4455",
      "doc_id": "py3119.json",
      "start_char": 4291,
      "end_char": 4455,
      "text": "Serialize *obj* as a JSON formatted stream to *fp* (a ``.write()``-supporting\n   :term:`file-like object`) using this :ref:`conversion table\n   <py-to-json-table>`."
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

py3119.json_s4291_4455; Unicode [4291, 4455). [Full pinned source](../../sources/json.rst); [official reader URL](https://docs.python.org/3.11/library/json.html).
```text
Serialize *obj* as a JSON formatted stream to *fp* (a ``.write()``-supporting
   :term:`file-like object`) using this :ref:`conversion table
   <py-to-json-table>`.
```

## py311v2_dev_012

```text
In Python 3.11, what does csv.reader return for iteration over CSV input?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_012",
  "question": "In Python 3.11, what does csv.reader return for iteration over CSV input?",
  "split": "dev",
  "cluster_id": "serialization",
  "source_document_ids": [
    "py3119.csv"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return a reader object that will process lines from the given *csvfile*. A csvfile must be an iterable of strings, each in the reader's defined csv format. A csvfile is most commonly a file-like object or list. If *csvfile* is a file object, it should be opened with newline=''. [1]_ An optional *dialect* parameter can be given which is used to define a set of parameters specific to a particular CSV dialect. It may be an instance of a subclass of the Dialect class or one of the strings returned by the list_dialects function. The other optional *fmtparams* keyword arguments can be given to override individual formatting parameters in the current dialect. For full details about the dialect and formatting parameters, see section csv-fmt-params.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.csv_s2072_2915",
      "doc_id": "py3119.csv",
      "start_char": 2072,
      "end_char": 2915,
      "text": "Return a :ref:`reader object <reader-objects>` that will process\n   lines from the given *csvfile*.  A csvfile must be an iterable of\n   strings, each in the reader's defined csv format.\n   A csvfile is most commonly a file-like object or list.\n   If *csvfile* is a file object,\n   it should be opened with ``newline=''``. [1]_  An optional\n   *dialect* parameter can be given which is used to define a set of parameters\n   specific to a particular CSV dialect.  It may be an instance of a subclass of\n   the :class:`Dialect` class or one of the strings returned by the\n   :func:`list_dialects` function.  The other optional *fmtparams* keyword arguments\n   can be given to override individual formatting parameters in the current\n   dialect.  For full details about the dialect and formatting parameters, see\n   section :ref:`csv-fmt-params`."
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

py3119.csv_s2072_2915; Unicode [2072, 2915). [Full pinned source](../../sources/csv.rst); [official reader URL](https://docs.python.org/3.11/library/csv.html).
```text
Return a :ref:`reader object <reader-objects>` that will process
   lines from the given *csvfile*.  A csvfile must be an iterable of
   strings, each in the reader's defined csv format.
   A csvfile is most commonly a file-like object or list.
   If *csvfile* is a file object,
   it should be opened with ``newline=''``. [1]_  An optional
   *dialect* parameter can be given which is used to define a set of parameters
   specific to a particular CSV dialect.  It may be an instance of a subclass of
   the :class:`Dialect` class or one of the strings returned by the
   :func:`list_dialects` function.  The other optional *fmtparams* keyword arguments
   can be given to override individual formatting parameters in the current
   dialect.  For full details about the dialect and formatting parameters, see
   section :ref:`csv-fmt-params`.
```

## py311v2_dev_013

```text
In Python 3.11, what does csv.writer return and what output interface does it require?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_013",
  "question": "In Python 3.11, what does csv.writer return and what output interface does it require?",
  "split": "dev",
  "cluster_id": "serialization",
  "source_document_ids": [
    "py3119.csv"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return a writer object responsible for converting the user's data into delimited strings on the given file-like object. *csvfile* can be any object with a io.TextIOBase.write method. If *csvfile* is a file object, it should be opened with newline='' [1]_. An optional *dialect* parameter can be given which is used to define a set of parameters specific to a particular CSV dialect. It may be an instance of a subclass of the Dialect class or one of the strings returned by the list_dialects function. The other optional *fmtparams* keyword arguments can be given to override individual formatting parameters in the current dialect. For full details about dialects and formatting parameters, see the csv-fmt-params section. To make it as easy as possible to interface with modules which implement the DB API, the value None is written as the empty string. While this isn't a reversible transformation, it makes it easier to dump SQL NULL data values to CSV files without preprocessing the data returned from a cursor.fetch* call. All other non-string data are stringified with str before being written.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.csv_s3574_4786",
      "doc_id": "py3119.csv",
      "start_char": 3574,
      "end_char": 4786,
      "text": "Return a writer object responsible for converting the user's data into delimited\n   strings on the given file-like object.  *csvfile* can be any object with a\n   :meth:`~io.TextIOBase.write` method.  If *csvfile* is a file object, it should be opened with\n   ``newline=''`` [1]_.  An optional *dialect*\n   parameter can be given which is used to define a set of parameters specific to a\n   particular CSV dialect.  It may be an instance of a subclass of the\n   :class:`Dialect` class or one of the strings returned by the\n   :func:`list_dialects` function.  The other optional *fmtparams* keyword arguments\n   can be given to override individual formatting parameters in the current\n   dialect.  For full details about dialects and formatting parameters, see\n   the :ref:`csv-fmt-params` section. To make it\n   as easy as possible to interface with modules which implement the DB API, the\n   value :const:`None` is written as the empty string.  While this isn't a\n   reversible transformation, it makes it easier to dump SQL NULL data values to\n   CSV files without preprocessing the data returned from a ``cursor.fetch*`` call.\n   All other non-string data are stringified with :func:`str` before being written."
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

py3119.csv_s3574_4786; Unicode [3574, 4786). [Full pinned source](../../sources/csv.rst); [official reader URL](https://docs.python.org/3.11/library/csv.html).
```text
Return a writer object responsible for converting the user's data into delimited
   strings on the given file-like object.  *csvfile* can be any object with a
   :meth:`~io.TextIOBase.write` method.  If *csvfile* is a file object, it should be opened with
   ``newline=''`` [1]_.  An optional *dialect*
   parameter can be given which is used to define a set of parameters specific to a
   particular CSV dialect.  It may be an instance of a subclass of the
   :class:`Dialect` class or one of the strings returned by the
   :func:`list_dialects` function.  The other optional *fmtparams* keyword arguments
   can be given to override individual formatting parameters in the current
   dialect.  For full details about dialects and formatting parameters, see
   the :ref:`csv-fmt-params` section. To make it
   as easy as possible to interface with modules which implement the DB API, the
   value :const:`None` is written as the empty string.  While this isn't a
   reversible transformation, it makes it easier to dump SQL NULL data values to
   CSV files without preprocessing the data returned from a ``cursor.fetch*`` call.
   All other non-string data are stringified with :func:`str` before being written.
```

## py311v2_dev_014

```text
In Python 3.11, how does csv.DictReader map row information to field names?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_014",
  "question": "In Python 3.11, how does csv.DictReader map row information to field names?",
  "split": "dev",
  "cluster_id": "serialization",
  "source_document_ids": [
    "py3119.csv"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Create an object that operates like a regular reader but maps the information in each row to a dict whose keys are given by the optional *fieldnames* parameter.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.csv_s6414_6589",
      "doc_id": "py3119.csv",
      "start_char": 6414,
      "end_char": 6589,
      "text": "Create an object that operates like a regular reader but maps the\n   information in each row to a :class:`dict` whose keys are given by the\n   optional *fieldnames* parameter."
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

py3119.csv_s6414_6589; Unicode [6414, 6589). [Full pinned source](../../sources/csv.rst); [official reader URL](https://docs.python.org/3.11/library/csv.html).
```text
Create an object that operates like a regular reader but maps the
   information in each row to a :class:`dict` whose keys are given by the
   optional *fieldnames* parameter.
```
