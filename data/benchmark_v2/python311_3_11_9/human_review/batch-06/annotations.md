# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_test_032

```text
For urllib3.PoolManager.request rather than urllib.request.urlopen, what connection-pool blocking defaults are documented?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_032",
  "question": "For urllib3.PoolManager.request rather than urllib.request.urlopen, what connection-pool blocking defaults are documented?",
  "split": "test",
  "cluster_id": "networking",
  "source_document_ids": [
    "py3119.urllib.request"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_010"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"urllib.request.urlopen\": [\"functools\", \"concurrent.futures\", \"urllib.parse\", \"urllib.request\"], \"urllib3.PoolManager.request\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.urllib.request_s1318_1433",
      "doc_id": "py3119.urllib.request",
      "start_char": 1318,
      "end_char": 1433,
      "text": "Open *url*, which can be either a string containing a valid, properly\n   encoded URL, or a :class:`Request` object."
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

py3119.urllib.request_s1318_1433; Unicode [1318, 1433). [Full pinned source](../../sources/urllib.request.rst); [official reader URL](https://docs.python.org/3.11/library/urllib.request.html).
```text
Open *url*, which can be either a string containing a valid, properly
   encoded URL, or a :class:`Request` object.
```

## py311v2_test_039

```text
Use the URL parser I meant. Should the params component be separate?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_039",
  "question": "Use the URL parser I meant. Should the params component be separate?",
  "split": "test",
  "cluster_id": "networking",
  "source_document_ids": [
    "py3119.urllib.parse"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_007",
    "py311v2_test_008"
  ],
  "is_answerable": false,
  "category": "ambiguous_question",
  "expected_decision": "CLARIFY",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "clarification_required",
  "ambiguity_interpretations": [
    "urlparse separates params",
    "urlsplit retains params in the path"
  ],
  "expected_answer": null,
  "expected_safe_behavior": "Ask which of the documented interpretations the requester intends. Do not select one arbitrarily or present either as confirmed intent.",
  "absence_note": "Both documented operations are plausible; the request omits the intended operation/output. Clarification resolves intent, whereas listing both does not authorize choosing one. Independent ambiguity review pending.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.urllib.parse_s1460_1997",
      "doc_id": "py3119.urllib.parse",
      "start_char": 1460,
      "end_char": 1997,
      "text": "Parse a URL into six components, returning a 6-item :term:`named tuple`.  This\n   corresponds to the general structure of a URL:\n   ``scheme://netloc/path;parameters?query#fragment``.\n   Each tuple item is a string, possibly empty. The components are not broken up\n   into smaller parts (for example, the network location is a single string), and %\n   escapes are not expanded. The delimiters as shown above are not part of the\n   result, except for a leading slash in the *path* component, which is retained if\n   present.  For example:"
    },
    {
      "id": "py3119.urllib.parse_s13045_13471",
      "doc_id": "py3119.urllib.parse",
      "start_char": 13045,
      "end_char": 13471,
      "text": "This is similar to :func:`urlparse`, but does not split the params from the URL.\n   This should generally be used instead of :func:`urlparse` if the more recent URL\n   syntax allowing parameters to be applied to each segment of the *path* portion\n   of the URL (see :rfc:`2396`) is wanted.  A separate function is needed to\n   separate the path segments and parameters.  This function returns a 5-item\n   :term:`named tuple`::"
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

py3119.urllib.parse_s13045_13471; Unicode [13045, 13471). [Full pinned source](../../sources/urllib.parse.rst); [official reader URL](https://docs.python.org/3.11/library/urllib.parse.html).
```text
This is similar to :func:`urlparse`, but does not split the params from the URL.
   This should generally be used instead of :func:`urlparse` if the more recent URL
   syntax allowing parameters to be applied to each segment of the *path* portion
   of the URL (see :rfc:`2396`) is wanted.  A separate function is needed to
   separate the path segments and parameters.  This function returns a 5-item
   :term:`named tuple`::
```

## py311v2_dev_018

```text
For numpy.mean rather than statistics.mean, what accumulation dtype is selected for float32 input?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_018",
  "question": "For numpy.mean rather than statistics.mean, what accumulation dtype is selected for float32 input?",
  "split": "dev",
  "cluster_id": "numeric",
  "source_document_ids": [
    "py3119.statistics"
  ],
  "near_miss_parent_ids": [
    "py311v2_dev_006"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"numpy.mean\": [], \"statistics.mean\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.statistics_s4874_4954",
      "doc_id": "py3119.statistics",
      "start_char": 4874,
      "end_char": 4954,
      "text": "Return the sample arithmetic mean of *data* which can be a sequence or iterable."
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

py3119.statistics_s4874_4954; Unicode [4874, 4954). [Full pinned source](../../sources/statistics.rst); [official reader URL](https://docs.python.org/3.11/library/statistics.html).
```text
Return the sample arithmetic mean of *data* which can be a sequence or iterable.
```

## py311v2_dev_020

```text
What exact maximum memory allocation in bytes does Decimal.from_float guarantee for any finite float?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_020",
  "question": "What exact maximum memory allocation in bytes does Decimal.from_float guarantee for any finite float?",
  "split": "dev",
  "cluster_id": "numeric",
  "source_document_ids": [
    "py3119.decimal"
  ],
  "near_miss_parent_ids": [
    "py311v2_dev_004"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"Decimal.from_float\": [\"decimal\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.decimal_s22462_22554",
      "doc_id": "py3119.decimal",
      "start_char": 22462,
      "end_char": 22554,
      "text": "Alternative constructor that only accepts instances of :class:`float` or\n      :class:`int`."
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

py3119.decimal_s22462_22554; Unicode [22462, 22554). [Full pinned source](../../sources/decimal.rst); [official reader URL](https://docs.python.org/3.11/library/decimal.html).
```text
Alternative constructor that only accepts instances of :class:`float` or
      :class:`int`.
```

## py311v2_dev_023

```text
Use the median function I intended for an even-length sample. Which one should you call?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_023",
  "question": "Use the median function I intended for an even-length sample. Which one should you call?",
  "split": "dev",
  "cluster_id": "numeric",
  "source_document_ids": [
    "py3119.statistics"
  ],
  "near_miss_parent_ids": [
    "py311v2_dev_007",
    "py311v2_dev_008"
  ],
  "is_answerable": false,
  "category": "ambiguous_question",
  "expected_decision": "CLARIFY",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "clarification_required",
  "ambiguity_interpretations": [
    "median_low selects the low median",
    "median_high selects the high median"
  ],
  "expected_answer": null,
  "expected_safe_behavior": "Ask which of the documented interpretations the requester intends. Do not select one arbitrarily or present either as confirmed intent.",
  "absence_note": "Both documented operations are plausible; the request omits the intended operation/output. Clarification resolves intent, whereas listing both does not authorize choosing one. Independent ambiguity review pending.",
  "evidence_spans": [],
  "diagnostic_spans": [
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

## py311v2_test_026

```text
How do I configure GitHub Actions billing limits for hosted macOS runners?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_026",
  "question": "How do I configure GitHub Actions billing limits for hosted macOS runners?",
  "split": "test",
  "cluster_id": "process-control",
  "source_document_ids": [
    "py3119.subprocess"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_019"
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

## py311v2_test_036

```text
What maximum process startup latency in microseconds does subprocess.Popen guarantee on Windows?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_036",
  "question": "What maximum process startup latency in microseconds does subprocess.Popen guarantee on Windows?",
  "split": "test",
  "cluster_id": "process-control",
  "source_document_ids": [
    "py3119.subprocess"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_020"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"subprocess.Popen\": [\"os\", \"subprocess\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.subprocess_s14449_14707",
      "doc_id": "py3119.subprocess",
      "start_char": 14449,
      "end_char": 14707,
      "text": "Execute a child program in a new process.  On POSIX, the class uses\n   :meth:`os.execvpe`-like behavior to execute the child program.  On Windows,\n   the class uses the Windows ``CreateProcess()`` function.  The arguments to\n   :class:`Popen` are as follows."
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

py3119.subprocess_s14449_14707; Unicode [14449, 14707). [Full pinned source](../../sources/subprocess.rst); [official reader URL](https://docs.python.org/3.11/library/subprocess.html).
```text
Execute a child program in a new process.  On POSIX, the class uses
   :meth:`os.execvpe`-like behavior to execute the child program.  On Windows,
   the class uses the Windows ``CreateProcess()`` function.  The arguments to
   :class:`Popen` are as follows.
```

## py311v2_test_038

```text
Since subprocess.check_call automatically retries nonzero exits, what backoff interval and maximum retry count does it use?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_038",
  "question": "Since subprocess.check_call automatically retries nonzero exits, what backoff interval and maximum retry count does it use?",
  "split": "test",
  "cluster_id": "process-control",
  "source_document_ids": [
    "py3119.subprocess"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_021"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"subprocess.check_call\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.subprocess_s47514_47894",
      "doc_id": "py3119.subprocess",
      "start_char": 47514,
      "end_char": 47894,
      "text": "Run command with arguments.  Wait for command to complete. If the return\n   code was zero then return, otherwise raise :exc:`CalledProcessError`. The\n   :exc:`CalledProcessError` object will have the return code in the\n   :attr:`~CalledProcessError.returncode` attribute.\n   If :func:`check_call` was unable to start the process it will propagate the exception\n   that was raised."
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

py3119.subprocess_s47514_47894; Unicode [47514, 47894). [Full pinned source](../../sources/subprocess.rst); [official reader URL](https://docs.python.org/3.11/library/subprocess.html).
```text
Run command with arguments.  Wait for command to complete. If the return
   code was zero then return, otherwise raise :exc:`CalledProcessError`. The
   :exc:`CalledProcessError` object will have the return code in the
   :attr:`~CalledProcessError.returncode` attribute.
   If :func:`check_call` was unable to start the process it will propagate the exception
   that was raised.
```

## py311v2_test_040

```text
Check whether the child is finished using the behavior I intended. Should the call wait?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_040",
  "question": "Check whether the child is finished using the behavior I intended. Should the call wait?",
  "split": "test",
  "cluster_id": "process-control",
  "source_document_ids": [
    "py3119.subprocess"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_023",
    "py311v2_test_024"
  ],
  "is_answerable": false,
  "category": "ambiguous_question",
  "expected_decision": "CLARIFY",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "clarification_required",
  "ambiguity_interpretations": [
    "poll checks without waiting for termination",
    "wait waits for termination"
  ],
  "expected_answer": null,
  "expected_safe_behavior": "Ask which of the documented interpretations the requester intends. Do not select one arbitrarily or present either as confirmed intent.",
  "absence_note": "Both documented operations are plausible; the request omits the intended operation/output. Clarification resolves intent, whereas listing both does not authorize choosing one. Independent ambiguity review pending.",
  "evidence_spans": [],
  "diagnostic_spans": [
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

## py311v2_dev_015

```text
Which JavaScript JSON.stringify replacer configuration serializes BigInt values in Node.js 22?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_015",
  "question": "Which JavaScript JSON.stringify replacer configuration serializes BigInt values in Node.js 22?",
  "split": "dev",
  "cluster_id": "serialization",
  "source_document_ids": [
    "py3119.json"
  ],
  "near_miss_parent_ids": [
    "py311v2_dev_009"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"JSON.stringify\": [], \"Node.js\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.json_s7671_7837",
      "doc_id": "py3119.json",
      "start_char": 7671,
      "end_char": 7837,
      "text": "Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion\n   table <py-to-json-table>`.  The arguments have the same meaning as in\n   :func:`dump`."
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

py3119.json_s7671_7837; Unicode [7671, 7837). [Full pinned source](../../sources/json.rst); [official reader URL](https://docs.python.org/3.11/library/json.html).
```text
Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion
   table <py-to-json-table>`.  The arguments have the same meaning as in
   :func:`dump`.
```
