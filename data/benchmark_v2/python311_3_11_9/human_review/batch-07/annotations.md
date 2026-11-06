# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_dev_019

```text
For orjson.dumps rather than json.dumps, which return type and non-string-key option are documented?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_019",
  "question": "For orjson.dumps rather than json.dumps, which return type and non-string-key option are documented?",
  "split": "dev",
  "cluster_id": "serialization",
  "source_document_ids": [
    "py3119.json"
  ],
  "near_miss_parent_ids": [
    "py311v2_dev_009"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"json.dumps\": [\"json\"], \"orjson.dumps\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
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

## py311v2_dev_021

```text
What minimum rows-per-second throughput does csv.reader guarantee for UTF-8 files?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_021",
  "question": "What minimum rows-per-second throughput does csv.reader guarantee for UTF-8 files?",
  "split": "dev",
  "cluster_id": "serialization",
  "source_document_ids": [
    "py3119.csv"
  ],
  "near_miss_parent_ids": [
    "py311v2_dev_012"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"csv.reader\": [\"collections\", \"csv\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.csv_s2072_2915",
      "doc_id": "py3119.csv",
      "start_char": 2072,
      "end_char": 2915,
      "text": "Return a :ref:`reader object <reader-objects>` that will process\n   lines from the given *csvfile*.  A csvfile must be an iterable of\n   strings, each in the reader's defined csv format.\n   A csvfile is most commonly a file-like object or list.\n   If *csvfile* is a file object,\n   it should be opened with ``newline=''``. [1]_  An optional\n   *dialect* parameter can be given which is used to define a set of parameters\n   specific to a particular CSV dialect.  It may be an instance of a subclass of\n   the :class:`Dialect` class or one of the strings returned by the\n   :func:`list_dialects` function.  The other optional *fmtparams* keyword arguments\n   can be given to override individual formatting parameters in the current\n   dialect.  For full details about the dialect and formatting parameters, see\n   section :ref:`csv-fmt-params`."
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

## py311v2_dev_022

```text
Since json.dumps automatically signs JSON using a secret key, where is that key stored and which signature algorithm is selected?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_022",
  "question": "Since json.dumps automatically signs JSON using a secret key, where is that key stored and which signature algorithm is selected?",
  "split": "dev",
  "cluster_id": "serialization",
  "source_document_ids": [
    "py3119.json"
  ],
  "near_miss_parent_ids": [
    "py311v2_dev_009"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"json.dumps\": [\"json\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
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

## py311v2_dev_024

```text
Use the JSON serialization destination I intended. Should you return text or write a stream?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_dev_024",
  "question": "Use the JSON serialization destination I intended. Should you return text or write a stream?",
  "split": "dev",
  "cluster_id": "serialization",
  "source_document_ids": [
    "py3119.json"
  ],
  "near_miss_parent_ids": [
    "py311v2_dev_009",
    "py311v2_dev_011"
  ],
  "is_answerable": false,
  "category": "ambiguous_question",
  "expected_decision": "CLARIFY",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "clarification_required",
  "ambiguity_interpretations": [
    "Return a str with dumps",
    "Write to a file-like stream with dump"
  ],
  "expected_answer": null,
  "expected_safe_behavior": "Ask which of the documented interpretations the requester intends. Do not select one arbitrarily or present either as confirmed intent.",
  "absence_note": "Both documented operations are plausible; the request omits the intended operation/output. Clarification resolves intent, whereas listing both does not authorize choosing one. Independent ambiguity review pending.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.json_s7671_7837",
      "doc_id": "py3119.json",
      "start_char": 7671,
      "end_char": 7837,
      "text": "Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion\n   table <py-to-json-table>`.  The arguments have the same meaning as in\n   :func:`dump`."
    },
    {
      "id": "py3119.json_s4291_4455",
      "doc_id": "py3119.json",
      "start_char": 4291,
      "end_char": 4455,
      "text": "Serialize *obj* as a JSON formatted stream to *fp* (a ``.write()``-supporting\n   :term:`file-like object`) using this :ref:`conversion table\n   <py-to-json-table>`."
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

py3119.json_s7671_7837; Unicode [7671, 7837). [Full pinned source](../../sources/json.rst); [official reader URL](https://docs.python.org/3.11/library/json.html).
```text
Serialize *obj* to a JSON formatted :class:`str` using this :ref:`conversion
   table <py-to-json-table>`.  The arguments have the same meaning as in
   :func:`dump`.
```

py3119.json_s4291_4455; Unicode [4291, 4455). [Full pinned source](../../sources/json.rst); [official reader URL](https://docs.python.org/3.11/library/json.html).
```text
Serialize *obj* as a JSON formatted stream to *fp* (a ``.write()``-supporting
   :term:`file-like object`) using this :ref:`conversion table
   <py-to-json-table>`.
```

## py311v2_train_008

```text
How do namedtuple._asdict and namedtuple._replace differ in what they return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_008",
  "question": "How do namedtuple._asdict and namedtuple._replace differ in what they return?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "compound",
  "is_compound": true,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Return a new dict which maps field names to their corresponding values: Return a new instance of the named tuple replacing specified fields with new values.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s37063_37147",
      "doc_id": "py3119.collections",
      "start_char": 37063,
      "end_char": 37147,
      "text": "Return a new :class:`dict` which maps field names to their corresponding\n    values:"
    },
    {
      "id": "py3119.collections_s37769_37858",
      "doc_id": "py3119.collections",
      "start_char": 37769,
      "end_char": 37858,
      "text": "Return a new instance of the named tuple replacing specified fields with new\n    values::"
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [
    "py3119.collections_s37063_37147",
    "py3119.collections_s37769_37858"
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

py3119.collections_s37063_37147; Unicode [37063, 37147). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Return a new :class:`dict` which maps field names to their corresponding
    values:
```

py3119.collections_s37769_37858; Unicode [37769, 37858). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Return a new instance of the named tuple replacing specified fields with new
    values::
```

## py311v2_train_012

```text
In the collections module, how does a user wrapper hold its contents?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_012",
  "question": "In the collections module, how does a user wrapper hold its contents?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "qualified_answer",
  "ambiguity_interpretations": [
    "UserDict dictionary wrapper",
    "UserList list wrapper"
  ],
  "expected_answer": "UserDict dictionary wrapper: Class that simulates a dictionary. The instance's contents are kept in a regular dictionary, which is accessible via the data attribute of UserDict instances. If *initialdata* is provided, data is initialized with its contents; note that a reference to *initialdata* will not be kept, allowing it to be used for other purposes.; UserList list wrapper: Class that simulates a list. The instance's contents are kept in a regular list, which is accessible via the data attribute of UserList instances. The instance's contents are initially set to a copy of *list*, defaulting to the empty list []. *list* can be any iterable, for example a real Python list or a UserList object.",
  "expected_safe_behavior": "Give a qualified answer for both documented interpretations, clearly naming each. Do not claim either is the confirmed intended meaning.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s49739_50109",
      "doc_id": "py3119.collections",
      "start_char": 49739,
      "end_char": 50109,
      "text": "Class that simulates a dictionary.  The instance's contents are kept in a\n    regular dictionary, which is accessible via the :attr:`data` attribute of\n    :class:`UserDict` instances.  If *initialdata* is provided, :attr:`data` is\n    initialized with its contents; note that a reference to *initialdata* will not\n    be kept, allowing it to be used for other purposes."
    },
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

py3119.collections_s49739_50109; Unicode [49739, 50109). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Class that simulates a dictionary.  The instance's contents are kept in a
    regular dictionary, which is accessible via the :attr:`data` attribute of
    :class:`UserDict` instances.  If *initialdata* is provided, :attr:`data` is
    initialized with its contents; note that a reference to *initialdata* will not
    be kept, allowing it to be used for other purposes.
```

py3119.collections_s50905_51277; Unicode [50905, 51277). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Class that simulates a list.  The instance's contents are kept in a regular
    list, which is accessible via the :attr:`data` attribute of :class:`UserList`
    instances.  The instance's contents are initially set to a copy of *list*,
    defaulting to the empty list ``[]``.  *list* can be any iterable, for
    example a real Python list or a :class:`UserList` object.
```

## py311v2_train_026

```text
Compare the conversions performed by dataclasses.asdict and dataclasses.astuple.
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_026",
  "question": "Compare the conversions performed by dataclasses.asdict and dataclasses.astuple.",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.dataclasses"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "compound",
  "is_compound": true,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Converts the dataclass obj to a dict (by using the factory function dict_factory). Each dataclass is converted to a dict of its fields, as name: value pairs. dataclasses, dicts, lists, and tuples are recursed into. Other objects are copied with copy.deepcopy. Converts the dataclass obj to a tuple (by using the factory function tuple_factory). Each dataclass is converted to a tuple of its field values. dataclasses, dicts, lists, and tuples are recursed into. Other objects are copied with copy.deepcopy.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.dataclasses_s14907_15201",
      "doc_id": "py3119.dataclasses",
      "start_char": 14907,
      "end_char": 15201,
      "text": "Converts the dataclass ``obj`` to a dict (by using the\n   factory function ``dict_factory``).  Each dataclass is converted\n   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,\n   lists, and tuples are recursed into.  Other objects are copied with\n   :func:`copy.deepcopy`."
    },
    {
      "id": "py3119.dataclasses_s15865_16141",
      "doc_id": "py3119.dataclasses",
      "start_char": 15865,
      "end_char": 16141,
      "text": "Converts the dataclass ``obj`` to a tuple (by using the\n   factory function ``tuple_factory``).  Each dataclass is converted\n   to a tuple of its field values.  dataclasses, dicts, lists, and\n   tuples are recursed into. Other objects are copied with\n   :func:`copy.deepcopy`."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [
    "py3119.dataclasses_s14907_15201",
    "py3119.dataclasses_s15865_16141"
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

py3119.dataclasses_s14907_15201; Unicode [14907, 15201). [Full pinned source](../../sources/dataclasses.rst); [official reader URL](https://docs.python.org/3.11/library/dataclasses.html).
```text
Converts the dataclass ``obj`` to a dict (by using the
   factory function ``dict_factory``).  Each dataclass is converted
   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,
   lists, and tuples are recursed into.  Other objects are copied with
   :func:`copy.deepcopy`.
```

py3119.dataclasses_s15865_16141; Unicode [15865, 16141). [Full pinned source](../../sources/dataclasses.rst); [official reader URL](https://docs.python.org/3.11/library/dataclasses.html).
```text
Converts the dataclass ``obj`` to a tuple (by using the
   factory function ``tuple_factory``).  Each dataclass is converted
   to a tuple of its field values.  dataclasses, dicts, lists, and
   tuples are recursed into. Other objects are copied with
   :func:`copy.deepcopy`.
```

## py311v2_train_036

```text
For an object, what does copying return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_036",
  "question": "For an object, what does copying return?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.copy"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "qualified_answer",
  "ambiguity_interpretations": [
    "Shallow copy with copy.copy",
    "Deep copy with copy.deepcopy"
  ],
  "expected_answer": "Shallow copy with copy.copy: Return a shallow copy of *x*.; Deep copy with copy.deepcopy: Return a deep copy of *x*.",
  "expected_safe_behavior": "Give a qualified answer for both documented interpretations, clearly naming each. Do not claim either is the confirmed intended meaning.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.copy_s597_626",
      "doc_id": "py3119.copy",
      "start_char": 597,
      "end_char": 626,
      "text": "Return a shallow copy of *x*."
    },
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

py3119.copy_s597_626; Unicode [597, 626). [Full pinned source](../../sources/copy.rst); [official reader URL](https://docs.python.org/3.11/library/copy.html).
```text
Return a shallow copy of *x*.
```

py3119.copy_s667_693; Unicode [667, 693). [Full pinned source](../../sources/copy.rst); [official reader URL](https://docs.python.org/3.11/library/copy.html).
```text
Return a deep copy of *x*.
```

## py311v2_train_042

```text
What does shutil.copyfile copy, and what extra preservation does copy2 attempt compared with copy?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_042",
  "question": "What does shutil.copyfile copy, and what extra preservation does copy2 attempt compared with copy?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.shutil"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "compound",
  "is_compound": true,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": "Copy the contents (no metadata) of the file named *src* to a file named *dst* and return *dst* in the most efficient way possible. *src* and *dst* are path-like objects or path names given as strings. Identical to shutil.copy except that copy2 also attempts to preserve file metadata.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.shutil_s1824_2057",
      "doc_id": "py3119.shutil",
      "start_char": 1824,
      "end_char": 2057,
      "text": "Copy the contents (no metadata) of the file named *src* to a file named\n   *dst* and return *dst* in the most efficient way possible.\n   *src* and *dst* are :term:`path-like objects <path-like object>` or path names given as strings."
    },
    {
      "id": "py3119.shutil_s7624_7727",
      "doc_id": "py3119.shutil",
      "start_char": 7624,
      "end_char": 7727,
      "text": "Identical to :func:`~shutil.copy` except that :func:`copy2`\n   also attempts to preserve file metadata."
    }
  ],
  "diagnostic_spans": [],
  "compound_required_spans": [
    "py3119.shutil_s1824_2057",
    "py3119.shutil_s7624_7727"
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

py3119.shutil_s1824_2057; Unicode [1824, 2057). [Full pinned source](../../sources/shutil.rst); [official reader URL](https://docs.python.org/3.11/library/shutil.html).
```text
Copy the contents (no metadata) of the file named *src* to a file named
   *dst* and return *dst* in the most efficient way possible.
   *src* and *dst* are :term:`path-like objects <path-like object>` or path names given as strings.
```

py3119.shutil_s7624_7727; Unicode [7624, 7727). [Full pinned source](../../sources/shutil.rst); [official reader URL](https://docs.python.org/3.11/library/shutil.html).
```text
Identical to :func:`~shutil.copy` except that :func:`copy2`
   also attempts to preserve file metadata.
```

## py311v2_test_011

```text
What does parsing a URL return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_011",
  "question": "What does parsing a URL return?",
  "split": "test",
  "cluster_id": "networking",
  "source_document_ids": [
    "py3119.urllib.parse"
  ],
  "near_miss_parent_ids": [],
  "is_answerable": true,
  "category": "answerable",
  "expected_decision": "ANSWER",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "qualified_answer",
  "ambiguity_interpretations": [
    "urllib.parse.urlparse with separate params",
    "urllib.parse.urlsplit without separate params"
  ],
  "expected_answer": "urllib.parse.urlparse with separate params: Parse a URL into six components, returning a 6-item named tuple. This corresponds to the general structure of a URL: scheme://netloc/path;parameters?query#fragment. Each tuple item is a string, possibly empty. The components are not broken up into smaller parts (for example, the network location is a single string), and % escapes are not expanded. The delimiters as shown above are not part of the result, except for a leading slash in the *path* component, which is retained if present. For example:; urllib.parse.urlsplit without separate params: This is similar to urlparse, but does not split the params from the URL. This should generally be used instead of urlparse if the more recent URL syntax allowing parameters to be applied to each segment of the *path* portion of the URL (see 2396) is wanted. A separate function is needed to separate the path segments and parameters. This function returns a 5-item named tuple.",
  "expected_safe_behavior": "Give a qualified answer for both documented interpretations, clearly naming each. Do not claim either is the confirmed intended meaning.",
  "absence_note": null,
  "evidence_spans": [
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
