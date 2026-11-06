# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_train_075

```text
For boltons.queueutils.PriorityQueue rather than collections.deque, what is its documented tie-breaking rule?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_075",
  "question": "For boltons.queueutils.PriorityQueue rather than collections.deque, what is its documented tie-breaking rule?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_003"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"boltons.queueutils.PriorityQueue\": [], \"collections.deque\": [\"itertools\", \"typing\", \"queue\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.collections_s18929_19092",
      "doc_id": "py3119.collections",
      "start_char": 18929,
      "end_char": 19092,
      "text": "Returns a new deque object initialized left-to-right (using :meth:`append`) with\n    data from *iterable*.  If *iterable* is not specified, the new deque is empty."
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

py3119.collections_s18929_19092; Unicode [18929, 19092). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Returns a new deque object initialized left-to-right (using :meth:`append`) with
    data from *iterable*.  If *iterable* is not specified, the new deque is empty.
```

## py311v2_train_081

```text
What exact peak memory in bytes does Counter require to count one million distinct strings?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_081",
  "question": "What exact peak memory in bytes does Counter require to count one million distinct strings?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_002"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.collections_s10099_10473",
      "doc_id": "py3119.collections",
      "start_char": 10099,
      "end_char": 10473,
      "text": "A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.\n    It is a collection where elements are stored as dictionary keys\n    and their counts are stored as dictionary values.  Counts are allowed to be\n    any integer value including zero or negative counts.  The :class:`Counter`\n    class is similar to bags or multisets in other languages."
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

py3119.collections_s10099_10473; Unicode [10099, 10473). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
    It is a collection where elements are stored as dictionary keys
    and their counts are stored as dictionary values.  Counts are allowed to be
    any integer value including zero or negative counts.  The :class:`Counter`
    class is similar to bags or multisets in other languages.
```

## py311v2_train_091

```text
Since Counter synchronizes its counts to a database automatically, which transaction isolation level does it select?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_091",
  "question": "Since Counter synchronizes its counts to a database automatically, which transaction isolation level does it select?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_002"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.collections_s10099_10473",
      "doc_id": "py3119.collections",
      "start_char": 10099,
      "end_char": 10473,
      "text": "A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.\n    It is a collection where elements are stored as dictionary keys\n    and their counts are stored as dictionary values.  Counts are allowed to be\n    any integer value including zero or negative counts.  The :class:`Counter`\n    class is similar to bags or multisets in other languages."
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

py3119.collections_s10099_10473; Unicode [10099, 10473). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
A :class:`Counter` is a :class:`dict` subclass for counting :term:`hashable` objects.
    It is a collection where elements are stored as dictionary keys
    and their counts are stored as dictionary values.  Counts are allowed to be
    any integer value including zero or negative counts.  The :class:`Counter`
    class is similar to bags or multisets in other languages.
```

## py311v2_train_093

```text
Please configure the wrapper we discussed. Which one did I mean?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_093",
  "question": "Please configure the wrapper we discussed. Which one did I mean?",
  "split": "train",
  "cluster_id": "containers",
  "source_document_ids": [
    "py3119.collections"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_010",
    "py311v2_train_011"
  ],
  "is_answerable": false,
  "category": "ambiguous_question",
  "expected_decision": "CLARIFY",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "clarification_required",
  "ambiguity_interpretations": [
    "A UserDict wrapper around a dictionary",
    "A UserList wrapper around a list"
  ],
  "expected_answer": null,
  "expected_safe_behavior": "Ask which of the documented interpretations the requester intends. Do not select one arbitrarily or present either as confirmed intent.",
  "absence_note": "Both documented operations are plausible; the request omits the intended operation/output. Clarification resolves intent, whereas listing both does not authorize choosing one. Independent ambiguity review pending.",
  "evidence_spans": [],
  "diagnostic_spans": [
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

## py311v2_train_061

```text
How does the TypeScript compiler emit metadata for class decorators in TypeScript 5.4?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_061",
  "question": "How does the TypeScript compiler emit metadata for class decorators in TypeScript 5.4?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.dataclasses"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_025"
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
      "id": "py3119.dataclasses_s14907_15201",
      "doc_id": "py3119.dataclasses",
      "start_char": 14907,
      "end_char": 15201,
      "text": "Converts the dataclass ``obj`` to a dict (by using the\n   factory function ``dict_factory``).  Each dataclass is converted\n   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,\n   lists, and tuples are recursed into.  Other objects are copied with\n   :func:`copy.deepcopy`."
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

py3119.dataclasses_s14907_15201; Unicode [14907, 15201). [Full pinned source](../../sources/dataclasses.rst); [official reader URL](https://docs.python.org/3.11/library/dataclasses.html).
```text
Converts the dataclass ``obj`` to a dict (by using the
   factory function ``dict_factory``).  Each dataclass is converted
   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,
   lists, and tuples are recursed into.  Other objects are copied with
   :func:`copy.deepcopy`.
```

## py311v2_train_078

```text
For attrs.asdict rather than dataclasses.asdict, what does recurse=False retain?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_078",
  "question": "For attrs.asdict rather than dataclasses.asdict, what does recurse=False retain?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.dataclasses"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_025"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"attrs.asdict\": [], \"dataclasses.asdict\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.dataclasses_s14907_15201",
      "doc_id": "py3119.dataclasses",
      "start_char": 14907,
      "end_char": 15201,
      "text": "Converts the dataclass ``obj`` to a dict (by using the\n   factory function ``dict_factory``).  Each dataclass is converted\n   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,\n   lists, and tuples are recursed into.  Other objects are copied with\n   :func:`copy.deepcopy`."
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

py3119.dataclasses_s14907_15201; Unicode [14907, 15201). [Full pinned source](../../sources/dataclasses.rst); [official reader URL](https://docs.python.org/3.11/library/dataclasses.html).
```text
Converts the dataclass ``obj`` to a dict (by using the
   factory function ``dict_factory``).  Each dataclass is converted
   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,
   lists, and tuples are recursed into.  Other objects are copied with
   :func:`copy.deepcopy`.
```

## py311v2_train_084

```text
What exact recursion-depth-independent memory bound in bytes does dataclasses.asdict guarantee?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_084",
  "question": "What exact recursion-depth-independent memory bound in bytes does dataclasses.asdict guarantee?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.dataclasses"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_025"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"dataclasses.asdict\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.dataclasses_s14907_15201",
      "doc_id": "py3119.dataclasses",
      "start_char": 14907,
      "end_char": 15201,
      "text": "Converts the dataclass ``obj`` to a dict (by using the\n   factory function ``dict_factory``).  Each dataclass is converted\n   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,\n   lists, and tuples are recursed into.  Other objects are copied with\n   :func:`copy.deepcopy`."
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

py3119.dataclasses_s14907_15201; Unicode [14907, 15201). [Full pinned source](../../sources/dataclasses.rst); [official reader URL](https://docs.python.org/3.11/library/dataclasses.html).
```text
Converts the dataclass ``obj`` to a dict (by using the
   factory function ``dict_factory``).  Each dataclass is converted
   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,
   lists, and tuples are recursed into.  Other objects are copied with
   :func:`copy.deepcopy`.
```

## py311v2_train_089

```text
Since asdict automatically encrypts private dataclass fields, which cipher and key-rotation schedule does it use?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_089",
  "question": "Since asdict automatically encrypts private dataclass fields, which cipher and key-rotation schedule does it use?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.dataclasses"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_025"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.dataclasses_s14907_15201",
      "doc_id": "py3119.dataclasses",
      "start_char": 14907,
      "end_char": 15201,
      "text": "Converts the dataclass ``obj`` to a dict (by using the\n   factory function ``dict_factory``).  Each dataclass is converted\n   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,\n   lists, and tuples are recursed into.  Other objects are copied with\n   :func:`copy.deepcopy`."
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

py3119.dataclasses_s14907_15201; Unicode [14907, 15201). [Full pinned source](../../sources/dataclasses.rst); [official reader URL](https://docs.python.org/3.11/library/dataclasses.html).
```text
Converts the dataclass ``obj`` to a dict (by using the
   factory function ``dict_factory``).  Each dataclass is converted
   to a dict of its fields, as ``name: value`` pairs.  dataclasses, dicts,
   lists, and tuples are recursed into.  Other objects are copied with
   :func:`copy.deepcopy`.
```

## py311v2_train_095

```text
Perform the dataclass conversion I meant. Which output form should you choose?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_095",
  "question": "Perform the dataclass conversion I meant. Which output form should you choose?",
  "split": "train",
  "cluster_id": "data-model",
  "source_document_ids": [
    "py3119.dataclasses"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_025",
    "py311v2_train_026"
  ],
  "is_answerable": false,
  "category": "ambiguous_question",
  "expected_decision": "CLARIFY",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "clarification_required",
  "ambiguity_interpretations": [
    "Dictionary conversion with asdict",
    "Tuple conversion with astuple"
  ],
  "expected_answer": null,
  "expected_safe_behavior": "Ask which of the documented interpretations the requester intends. Do not select one arbitrarily or present either as confirmed intent.",
  "absence_note": "Both documented operations are plausible; the request omits the intended operation/output. Clarification resolves intent, whereas listing both does not authorize choosing one. Independent ambiguity review pending.",
  "evidence_spans": [],
  "diagnostic_spans": [
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

## py311v2_test_025

```text
Which PostgreSQL 16 replication settings guarantee synchronous commits to two remote replicas?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_025",
  "question": "Which PostgreSQL 16 replication settings guarantee synchronous commits to two remote replicas?",
  "split": "test",
  "cluster_id": "database",
  "source_document_ids": [
    "py3119.sqlite3"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_013"
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
      "id": "py3119.sqlite3_s8959_8999",
      "doc_id": "py3119.sqlite3",
      "start_char": 8959,
      "end_char": 8999,
      "text": "Open a connection to an SQLite database."
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

py3119.sqlite3_s8959_8999; Unicode [8959, 8999). [Full pinned source](../../sources/sqlite3.rst); [official reader URL](https://docs.python.org/3.11/library/sqlite3.html).
```text
Open a connection to an SQLite database.
```
