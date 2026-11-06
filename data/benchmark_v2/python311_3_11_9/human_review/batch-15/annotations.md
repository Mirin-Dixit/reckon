# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_train_048

```text
In Python 3.11, what representation does os.fspath return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_048",
  "question": "In Python 3.11, what representation does os.fspath return?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.os"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return the file system representation of the path.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.os_s10414_10464",
      "doc_id": "py3119.os",
      "start_char": 10414,
      "end_char": 10464,
      "text": "Return the file system representation of the path."
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

py3119.os_s10414_10464; Unicode [10414, 10464). [Full pinned source](../../sources/os.rst); [official reader URL](https://docs.python.org/3.11/library/os.html).
```text
Return the file system representation of the path.
```

## py311v2_train_015

```text
In Python 3.11, how does itertools.compress select elements, and when does it stop?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_015",
  "question": "In Python 3.11, how does itertools.compress select elements, and when does it stop?",
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
  "expected_answer": "Make an iterator that filters elements from *data* returning only those that have a corresponding element in *selectors* that evaluates to True. Stops when either the *data* or *selectors* iterables has been exhausted. Roughly equivalent to.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.itertools_s14485_14740",
      "doc_id": "py3119.itertools",
      "start_char": 14485,
      "end_char": 14740,
      "text": "Make an iterator that filters elements from *data* returning only those that\n   have a corresponding element in *selectors* that evaluates to ``True``.\n   Stops when either the *data* or *selectors* iterables has been exhausted.\n   Roughly equivalent to::"
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

py3119.itertools_s14485_14740; Unicode [14485, 14740). [Full pinned source](../../sources/itertools.rst); [official reader URL](https://docs.python.org/3.11/library/itertools.html).
```text
Make an iterator that filters elements from *data* returning only those that
   have a corresponding element in *selectors* that evaluates to ``True``.
   Stops when either the *data* or *selectors* iterables has been exhausted.
   Roughly equivalent to::
```

## py311v2_train_017

```text
In Python 3.11, which input elements does itertools.filterfalse yield?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_017",
  "question": "In Python 3.11, which input elements does itertools.filterfalse yield?",
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
  "expected_answer": "Make an iterator that filters elements from iterable returning only those for which the predicate is false. If *predicate* is None, return the items that are false. Roughly equivalent to.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.itertools_s17058_17256",
      "doc_id": "py3119.itertools",
      "start_char": 17058,
      "end_char": 17256,
      "text": "Make an iterator that filters elements from iterable returning only those for\n   which the predicate is false. If *predicate* is ``None``, return the items\n   that are false. Roughly equivalent to::"
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

py3119.itertools_s17058_17256; Unicode [17058, 17256). [Full pinned source](../../sources/itertools.rst); [official reader URL](https://docs.python.org/3.11/library/itertools.html).
```text
Make an iterator that filters elements from iterable returning only those for
   which the predicate is false. If *predicate* is ``None``, return the items
   that are false. Roughly equivalent to::
```

## py311v2_train_019

```text
In Python 3.11, when does itertools.takewhile stop yielding elements?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_019",
  "question": "In Python 3.11, when does itertools.takewhile stop yielding elements?",
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
  "expected_answer": "Make an iterator that returns elements from the iterable as long as the predicate is true. Roughly equivalent to.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.itertools_s27590_27708",
      "doc_id": "py3119.itertools",
      "start_char": 27590,
      "end_char": 27708,
      "text": "Make an iterator that returns elements from the iterable as long as the\n   predicate is true.  Roughly equivalent to::"
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

py3119.itertools_s27590_27708; Unicode [27590, 27708). [Full pinned source](../../sources/itertools.rst); [official reader URL](https://docs.python.org/3.11/library/itertools.html).
```text
Make an iterator that returns elements from the iterable as long as the
   predicate is true.  Roughly equivalent to::
```

## py311v2_train_020

```text
In Python 3.11, what caching wrapper does functools.cache provide?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_020",
  "question": "In Python 3.11, what caching wrapper does functools.cache provide?",
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
  "expected_answer": "Simple lightweight unbounded function cache. Sometimes called \"memoize\".",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.functools_s1013_1136",
      "doc_id": "py3119.functools",
      "start_char": 1013,
      "end_char": 1136,
      "text": "Simple lightweight unbounded function cache.  Sometimes called\n   `\"memoize\" <https://en.wikipedia.org/wiki/Memoization>`_."
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

py3119.functools_s1013_1136; Unicode [1013, 1136). [Full pinned source](../../sources/functools.rst); [official reader URL](https://docs.python.org/3.11/library/functools.html).
```text
Simple lightweight unbounded function cache.  Sometimes called
   `"memoize" <https://en.wikipedia.org/wiki/Memoization>`_.
```

## py311v2_train_022

```text
In Python 3.11, how does functools.partial combine bound and later arguments?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_022",
  "question": "In Python 3.11, how does functools.partial combine bound and later arguments?",
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
  "expected_answer": "Return a new partial object which when called will behave like *func* called with the positional arguments *args* and keyword arguments *keywords*. If more arguments are supplied to the call, they are appended to *args*. If additional keyword arguments are supplied, they extend and override *keywords*. Roughly equivalent to.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.functools_s12999_13365",
      "doc_id": "py3119.functools",
      "start_char": 12999,
      "end_char": 13365,
      "text": "Return a new :ref:`partial object<partial-objects>` which when called\n   will behave like *func* called with the positional arguments *args*\n   and keyword arguments *keywords*. If more arguments are supplied to the\n   call, they are appended to *args*. If additional keyword arguments are\n   supplied, they extend and override *keywords*.\n   Roughly equivalent to::"
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

py3119.functools_s12999_13365; Unicode [12999, 13365). [Full pinned source](../../sources/functools.rst); [official reader URL](https://docs.python.org/3.11/library/functools.html).
```text
Return a new :ref:`partial object<partial-objects>` which when called
   will behave like *func* called with the positional arguments *args*
   and keyword arguments *keywords*. If more arguments are supplied to the
   call, they are appended to *args*. If additional keyword arguments are
   supplied, they extend and override *keywords*.
   Roughly equivalent to::
```

## py311v2_train_023

```text
In Python 3.11, how does functools.reduce combine elements of an iterable?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_023",
  "question": "In Python 3.11, how does functools.reduce combine elements of an iterable?",
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
  "expected_answer": "Apply *function* of two arguments cumulatively to the items of *iterable*, from left to right, so as to reduce the iterable to a single value. For example, reduce(lambda x, y: x+y, [1, 2, 3, 4, 5]) calculates ((((1+2)+3)+4)+5). The left argument, *x*, is the accumulated value and the right argument, *y*, is the update value from the *iterable*. If the optional *initializer* is present, it is placed before the items of the iterable in the calculation, and serves as a default when the iterable is empty. If *initializer* is not given and *iterable* contains only one item, the first item is returned.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.functools_s15884_16519",
      "doc_id": "py3119.functools",
      "start_char": 15884,
      "end_char": 16519,
      "text": "Apply *function* of two arguments cumulatively to the items of *iterable*, from\n   left to right, so as to reduce the iterable to a single value.  For example,\n   ``reduce(lambda x, y: x+y, [1, 2, 3, 4, 5])`` calculates ``((((1+2)+3)+4)+5)``.\n   The left argument, *x*, is the accumulated value and the right argument, *y*, is\n   the update value from the *iterable*.  If the optional *initializer* is present,\n   it is placed before the items of the iterable in the calculation, and serves as\n   a default when the iterable is empty.  If *initializer* is not given and\n   *iterable* contains only one item, the first item is returned."
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

py3119.functools_s15884_16519; Unicode [15884, 16519). [Full pinned source](../../sources/functools.rst); [official reader URL](https://docs.python.org/3.11/library/functools.html).
```text
Apply *function* of two arguments cumulatively to the items of *iterable*, from
   left to right, so as to reduce the iterable to a single value.  For example,
   ``reduce(lambda x, y: x+y, [1, 2, 3, 4, 5])`` calculates ``((((1+2)+3)+4)+5)``.
   The left argument, *x*, is the accumulated value and the right argument, *y*, is
   the update value from the *iterable*.  If the optional *initializer* is present,
   it is placed before the items of the iterable in the calculation, and serves as
   a default when the iterable is empty.  If *initializer* is not given and
   *iterable* contains only one item, the first item is returned.
```

## py311v2_test_009

```text
In Python 3.11, what does urllib.parse.urlencode convert to a query string?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_009",
  "question": "In Python 3.11, what does urllib.parse.urlencode convert to a query string?",
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
  "expected_answer": "Convert a mapping object or a sequence of two-element tuples, which may contain str or bytes objects, to a percent-encoded ASCII text string. If the resultant string is to be used as a *data* for POST operation with the urllib.request.urlopen function, then it should be encoded to bytes, otherwise it would result in a TypeError.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.urllib.parse_s30379_30759",
      "doc_id": "py3119.urllib.parse",
      "start_char": 30379,
      "end_char": 30759,
      "text": "Convert a mapping object or a sequence of two-element tuples, which may\n   contain :class:`str` or :class:`bytes` objects, to a percent-encoded ASCII\n   text string.  If the resultant string is to be used as a *data* for POST\n   operation with the :func:`~urllib.request.urlopen` function, then\n   it should be encoded to bytes, otherwise it would result in a\n   :exc:`TypeError`."
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

py3119.urllib.parse_s30379_30759; Unicode [30379, 30759). [Full pinned source](../../sources/urllib.parse.rst); [official reader URL](https://docs.python.org/3.11/library/urllib.parse.html).
```text
Convert a mapping object or a sequence of two-element tuples, which may
   contain :class:`str` or :class:`bytes` objects, to a percent-encoded ASCII
   text string.  If the resultant string is to be used as a *data* for POST
   operation with the :func:`~urllib.request.urlopen` function, then
   it should be encoded to bytes, otherwise it would result in a
   :exc:`TypeError`.
```

## py311v2_test_010

```text
In Python 3.11, what kinds of arguments can urllib.request.urlopen open?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_010",
  "question": "In Python 3.11, what kinds of arguments can urllib.request.urlopen open?",
  "split": "test",
  "cluster_id": "networking",
  "source_document_ids": [
    "py3119.urllib.request"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Open *url*, which can be either a string containing a valid, properly encoded URL, or a Request object.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.urllib.request_s1318_1433",
      "doc_id": "py3119.urllib.request",
      "start_char": 1318,
      "end_char": 1433,
      "text": "Open *url*, which can be either a string containing a valid, properly\n   encoded URL, or a :class:`Request` object."
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

py3119.urllib.request_s1318_1433; Unicode [1318, 1433). [Full pinned source](../../sources/urllib.request.rst); [official reader URL](https://docs.python.org/3.11/library/urllib.request.html).
```text
Open *url*, which can be either a string containing a valid, properly
   encoded URL, or a :class:`Request` object.
```

## py311v2_test_012

```text
In Python 3.11, what does an http.client.HTTPConnection instance represent?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_012",
  "question": "In Python 3.11, what does an http.client.HTTPConnection instance represent?",
  "split": "test",
  "cluster_id": "networking",
  "source_document_ids": [
    "py3119.http.client"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "factoid",
  "is_compound": false,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "An HTTPConnection instance represents one transaction with an HTTP server. It should be instantiated by passing it a host and optional port number. If no port number is passed, the port is extracted from the host string if it has the form host:port, else the default HTTP port (80) is used. If the optional *timeout* parameter is given, blocking operations (like connection attempts) will timeout after that many seconds (if it is not given, the global default timeout setting is used). The optional *source_address* parameter may be a tuple of a (host, port) to use as the source address the HTTP connection is made from. The optional *blocksize* parameter sets the buffer size in bytes for sending a file-like message body.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.http.client_s1062_1833",
      "doc_id": "py3119.http.client",
      "start_char": 1062,
      "end_char": 1833,
      "text": "An :class:`HTTPConnection` instance represents one transaction with an HTTP\n   server.  It should be instantiated by passing it a host and optional port\n   number.  If no port number is passed, the port is extracted from the host\n   string if it has the form ``host:port``, else the default HTTP port (80) is\n   used.  If the optional *timeout* parameter is given, blocking\n   operations (like connection attempts) will timeout after that many seconds\n   (if it is not given, the global default timeout setting is used).\n   The optional *source_address* parameter may be a tuple of a (host, port)\n   to use as the source address the HTTP connection is made from.\n   The optional *blocksize* parameter sets the buffer size in bytes for\n   sending a file-like message body."
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

py3119.http.client_s1062_1833; Unicode [1062, 1833). [Full pinned source](../../sources/http.client.rst); [official reader URL](https://docs.python.org/3.11/library/http.client.html).
```text
An :class:`HTTPConnection` instance represents one transaction with an HTTP
   server.  It should be instantiated by passing it a host and optional port
   number.  If no port number is passed, the port is extracted from the host
   string if it has the form ``host:port``, else the default HTTP port (80) is
   used.  If the optional *timeout* parameter is given, blocking
   operations (like connection attempts) will timeout after that many seconds
   (if it is not given, the global default timeout setting is used).
   The optional *source_address* parameter may be a tuple of a (host, port)
   to use as the source address the HTTP connection is made from.
   The optional *blocksize* parameter sets the buffer size in bytes for
   sending a file-like message body.
```
