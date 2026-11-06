# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_train_056

```text
In Python 3.11, what clock behavior does time.monotonic guarantee?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_056",
  "question": "In Python 3.11, what clock behavior does time.monotonic guarantee?",
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
  "expected_answer": "Return the value (in fractional seconds) of a monotonic clock, i.e. a clock that cannot go backwards. The clock is not affected by system clock updates. The reference point of the returned value is undefined, so that only the difference between the results of two calls is valid.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.time_s10885_11174",
      "doc_id": "py3119.time",
      "start_char": 10885,
      "end_char": 11174,
      "text": "Return the value (in fractional seconds) of a monotonic clock, i.e. a clock\n   that cannot go backwards.  The clock is not affected by system clock updates.\n   The reference point of the returned value is undefined, so that only the\n   difference between the results of two calls is valid."
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

py3119.time_s10885_11174; Unicode [10885, 11174). [Full pinned source](../../sources/time.rst); [official reader URL](https://docs.python.org/3.11/library/time.html).
```text
Return the value (in fractional seconds) of a monotonic clock, i.e. a clock
   that cannot go backwards.  The clock is not affected by system clock updates.
   The reference point of the returned value is undefined, so that only the
   difference between the results of two calls is valid.
```

## py311v2_train_039

```text
In Python 3.11, what does pathlib.Path.mkdir create?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_039",
  "question": "In Python 3.11, what does pathlib.Path.mkdir create?",
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
  "expected_answer": "Create a new directory at this given path. If *mode* is given, it is combined with the process' umask value to determine the file mode and access flags. If the path already exists, FileExistsError is raised.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.pathlib_s29456_29685",
      "doc_id": "py3119.pathlib",
      "start_char": 29456,
      "end_char": 29685,
      "text": "Create a new directory at this given path.  If *mode* is given, it is\n   combined with the process' ``umask`` value to determine the file mode\n   and access flags.  If the path already exists, :exc:`FileExistsError`\n   is raised."
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

py3119.pathlib_s29456_29685; Unicode [29456, 29685). [Full pinned source](../../sources/pathlib.rst); [official reader URL](https://docs.python.org/3.11/library/pathlib.html).
```text
Create a new directory at this given path.  If *mode* is given, it is
   combined with the process' ``umask`` value to determine the file mode
   and access flags.  If the path already exists, :exc:`FileExistsError`
   is raised.
```

## py311v2_train_041

```text
In Python 3.11, what does shutil.copyfile copy between its two paths?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_041",
  "question": "In Python 3.11, what does shutil.copyfile copy between its two paths?",
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
  "expected_answer": "Copy the contents (no metadata) of the file named *src* to a file named *dst* and return *dst* in the most efficient way possible. *src* and *dst* are path-like objects or path names given as strings.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.shutil_s1824_2057",
      "doc_id": "py3119.shutil",
      "start_char": 1824,
      "end_char": 2057,
      "text": "Copy the contents (no metadata) of the file named *src* to a file named\n   *dst* and return *dst* in the most efficient way possible.\n   *src* and *dst* are :term:`path-like objects <path-like object>` or path names given as strings."
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

py3119.shutil_s1824_2057; Unicode [1824, 2057). [Full pinned source](../../sources/shutil.rst); [official reader URL](https://docs.python.org/3.11/library/shutil.html).
```text
Copy the contents (no metadata) of the file named *src* to a file named
   *dst* and return *dst* in the most efficient way possible.
   *src* and *dst* are :term:`path-like objects <path-like object>` or path names given as strings.
```

## py311v2_train_013

```text
In Python 3.11, what values does itertools.accumulate produce?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_013",
  "question": "In Python 3.11, what values does itertools.accumulate produce?",
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
  "expected_answer": "Make an iterator that returns accumulated sums, or accumulated results of other binary functions (specified via the optional *func* argument).",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.itertools_s7322_7472",
      "doc_id": "py3119.itertools",
      "start_char": 7322,
      "end_char": 7472,
      "text": "Make an iterator that returns accumulated sums, or accumulated\n    results of other binary functions (specified via the optional\n    *func* argument)."
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

py3119.itertools_s7322_7472; Unicode [7322, 7472). [Full pinned source](../../sources/itertools.rst); [official reader URL](https://docs.python.org/3.11/library/itertools.html).
```text
Make an iterator that returns accumulated sums, or accumulated
    results of other binary functions (specified via the optional
    *func* argument).
```

## py311v2_train_014

```text
In Python 3.11, in what order does itertools.chain consume its input iterables?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_014",
  "question": "In Python 3.11, in what order does itertools.chain consume its input iterables?",
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
  "expected_answer": "Make an iterator that returns elements from the first iterable until it is exhausted, then proceeds to the next iterable, until all of the iterables are exhausted. Used for treating consecutive sequences as a single sequence. Roughly equivalent to.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.itertools_s9897_10156",
      "doc_id": "py3119.itertools",
      "start_char": 9897,
      "end_char": 10156,
      "text": "Make an iterator that returns elements from the first iterable until it is\n   exhausted, then proceeds to the next iterable, until all of the iterables are\n   exhausted.  Used for treating consecutive sequences as a single sequence.\n   Roughly equivalent to::"
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

py3119.itertools_s9897_10156; Unicode [9897, 10156). [Full pinned source](../../sources/itertools.rst); [official reader URL](https://docs.python.org/3.11/library/itertools.html).
```text
Make an iterator that returns elements from the first iterable until it is
   exhausted, then proceeds to the next iterable, until all of the iterables are
   exhausted.  Used for treating consecutive sequences as a single sequence.
   Roughly equivalent to::
```

## py311v2_train_021

```text
In Python 3.11, what caching behavior does functools.lru_cache provide?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_021",
  "question": "In Python 3.11, what caching behavior does functools.lru_cache provide?",
  "split": "train",
  "cluster_id": "iterators-functions",
  "source_document_ids": [
    "py3119.functools"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Decorator to wrap a function with a memoizing callable that saves up to the *maxsize* most recent calls. It can save time when an expensive or I/O bound function is periodically called with the same arguments.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.functools_s5481_5697",
      "doc_id": "py3119.functools",
      "start_char": 5481,
      "end_char": 5697,
      "text": "Decorator to wrap a function with a memoizing callable that saves up to the\n   *maxsize* most recent calls.  It can save time when an expensive or I/O bound\n   function is periodically called with the same arguments."
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

py3119.functools_s5481_5697; Unicode [5481, 5697). [Full pinned source](../../sources/functools.rst); [official reader URL](https://docs.python.org/3.11/library/functools.html).
```text
Decorator to wrap a function with a memoizing callable that saves up to the
   *maxsize* most recent calls.  It can save time when an expensive or I/O bound
   function is periodically called with the same arguments.
```

## py311v2_test_007

```text
In Python 3.11, what components does urllib.parse.urlparse return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_007",
  "question": "In Python 3.11, what components does urllib.parse.urlparse return?",
  "split": "test",
  "cluster_id": "networking",
  "source_document_ids": [
    "py3119.urllib.parse"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Parse a URL into six components, returning a 6-item named tuple. This corresponds to the general structure of a URL: scheme://netloc/path;parameters?query#fragment. Each tuple item is a string, possibly empty. The components are not broken up into smaller parts (for example, the network location is a single string), and % escapes are not expanded. The delimiters as shown above are not part of the result, except for a leading slash in the *path* component, which is retained if present. For example:",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.urllib.parse_s1460_1997",
      "doc_id": "py3119.urllib.parse",
      "start_char": 1460,
      "end_char": 1997,
      "text": "Parse a URL into six components, returning a 6-item :term:`named tuple`.  This\n   corresponds to the general structure of a URL:\n   ``scheme://netloc/path;parameters?query#fragment``.\n   Each tuple item is a string, possibly empty. The components are not broken up\n   into smaller parts (for example, the network location is a single string), and %\n   escapes are not expanded. The delimiters as shown above are not part of the\n   result, except for a leading slash in the *path* component, which is retained if\n   present.  For example:"
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

## py311v2_test_008

```text
In Python 3.11, how does urllib.parse.urlsplit differ from urlparse?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_008",
  "question": "In Python 3.11, how does urllib.parse.urlsplit differ from urlparse?",
  "split": "test",
  "cluster_id": "networking",
  "source_document_ids": [
    "py3119.urllib.parse"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "This is similar to urlparse, but does not split the params from the URL. This should generally be used instead of urlparse if the more recent URL syntax allowing parameters to be applied to each segment of the *path* portion of the URL (see 2396) is wanted. A separate function is needed to separate the path segments and parameters. This function returns a 5-item named tuple.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.urllib.parse_s13045_13471",
      "doc_id": "py3119.urllib.parse",
      "start_char": 13045,
      "end_char": 13471,
      "text": "This is similar to :func:`urlparse`, but does not split the params from the URL.\n   This should generally be used instead of :func:`urlparse` if the more recent URL\n   syntax allowing parameters to be applied to each segment of the *path* portion\n   of the URL (see :rfc:`2396`) is wanted.  A separate function is needed to\n   separate the path segments and parameters.  This function returns a 5-item\n   :term:`named tuple`::"
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

py3119.urllib.parse_s13045_13471; Unicode [13045, 13471). [Full pinned source](../../sources/urllib.parse.rst); [official reader URL](https://docs.python.org/3.11/library/urllib.parse.html).
```text
This is similar to :func:`urlparse`, but does not split the params from the URL.
   This should generally be used instead of :func:`urlparse` if the more recent URL
   syntax allowing parameters to be applied to each segment of the *path* portion
   of the URL (see :rfc:`2396`) is wanted.  A separate function is needed to
   separate the path segments and parameters.  This function returns a 5-item
   :term:`named tuple`::
```

## py311v2_dev_001

```text
In Python 3.11, what boolean result does math.isclose return for close versus non-close values?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_001",
  "question": "In Python 3.11, what boolean result does math.isclose return for close versus non-close values?",
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
  "expected_answer": "Return True if the values *a* and *b* are close to each other and False otherwise.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.math_s5298_5391",
      "doc_id": "py3119.math",
      "start_char": 5298,
      "end_char": 5391,
      "text": "Return ``True`` if the values *a* and *b* are close to each other and\n   ``False`` otherwise."
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

py3119.math_s5298_5391; Unicode [5298, 5391). [Full pinned source](../../sources/math.rst); [official reader URL](https://docs.python.org/3.11/library/math.html).
```text
Return ``True`` if the values *a* and *b* are close to each other and
   ``False`` otherwise.
```

## py311v2_dev_007

```text
In Python 3.11, which median does statistics.median_low select?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_007",
  "question": "In Python 3.11, which median does statistics.median_low select?",
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
  "expected_answer": "Return the low median of numeric data. If *data* is empty, StatisticsError is raised. *data* can be a sequence or iterable.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.statistics_s10422_10557",
      "doc_id": "py3119.statistics",
      "start_char": 10422,
      "end_char": 10557,
      "text": "Return the low median of numeric data.  If *data* is empty,\n   :exc:`StatisticsError` is raised.  *data* can be a sequence or iterable."
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

py3119.statistics_s10422_10557; Unicode [10422, 10557). [Full pinned source](../../sources/statistics.rst); [official reader URL](https://docs.python.org/3.11/library/statistics.html).
```text
Return the low median of numeric data.  If *data* is empty,
   :exc:`StatisticsError` is raised.  *data* can be a sequence or iterable.
```
