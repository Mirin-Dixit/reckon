# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_train_009

```text
In Python 3.11, for which operations was collections.OrderedDict designed?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_009",
  "question": "In Python 3.11, for which operations was collections.OrderedDict designed?",
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
  "expected_answer": "Return an instance of a dict subclass that has methods specialized for rearranging dictionary order.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.collections_s43586_43699",
      "doc_id": "py3119.collections",
      "start_char": 43586,
      "end_char": 43699,
      "text": "Return an instance of a :class:`dict` subclass that has methods\n    specialized for rearranging dictionary order."
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

py3119.collections_s43586_43699; Unicode [43586, 43699). [Full pinned source](../../sources/collections.rst); [official reader URL](https://docs.python.org/3.11/library/collections.html).
```text
Return an instance of a :class:`dict` subclass that has methods
    specialized for rearranging dictionary order.
```

## py311v2_train_032

```text
In Python 3.11, how do IntEnum members relate to integers?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_032",
  "question": "In Python 3.11, how do IntEnum members relate to integers?",
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
  "expected_answer": "*IntEnum* is the same as *Enum*, but its members are also integers and can be used anywhere that an integer can be used. If any integer operation is performed with an *IntEnum* member, the resulting value loses its enumeration status.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.enum_s13905_14146",
      "doc_id": "py3119.enum",
      "start_char": 13905,
      "end_char": 14146,
      "text": "*IntEnum* is the same as *Enum*, but its members are also integers and can be\n   used anywhere that an integer can be used.  If any integer operation is performed\n   with an *IntEnum* member, the resulting value loses its enumeration status."
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

py3119.enum_s13905_14146; Unicode [13905, 14146). [Full pinned source](../../sources/enum.rst); [official reader URL](https://docs.python.org/3.11/library/enum.html).
```text
*IntEnum* is the same as *Enum*, but its members are also integers and can be
   used anywhere that an integer can be used.  If any integer operation is performed
   with an *IntEnum* member, the resulting value loses its enumeration status.
```

## py311v2_train_033

```text
In Python 3.11, what does typing.NewType provide to type checkers?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_033",
  "question": "In Python 3.11, what does typing.NewType provide to type checkers?",
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
  "expected_answer": "Helper class to create low-overhead distinct types .",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.typing_s63014_63083",
      "doc_id": "py3119.typing",
      "start_char": 63014,
      "end_char": 63083,
      "text": "Helper class to create low-overhead :ref:`distinct types <distinct>`."
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

py3119.typing_s63014_63083; Unicode [63014, 63083). [Full pinned source](../../sources/typing.rst); [official reader URL](https://docs.python.org/3.11/library/typing.html).
```text
Helper class to create low-overhead :ref:`distinct types <distinct>`.
```

## py311v2_train_035

```text
In Python 3.11, what information does typing.get_type_hints return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_035",
  "question": "In Python 3.11, what information does typing.get_type_hints return?",
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
  "expected_answer": "Return a dictionary containing type hints for a function, method, module or class object.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.typing_s88178_88270",
      "doc_id": "py3119.typing",
      "start_char": 88178,
      "end_char": 88270,
      "text": "Return a dictionary containing type hints for a function, method, module\n   or class object."
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

py3119.typing_s88178_88270; Unicode [88178, 88270). [Full pinned source](../../sources/typing.rst); [official reader URL](https://docs.python.org/3.11/library/typing.html).
```text
Return a dictionary containing type hints for a function, method, module
   or class object.
```

## py311v2_test_014

```text
In Python 3.11, what does sqlite3.complete_statement check about its input?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_014",
  "question": "In Python 3.11, what does sqlite3.complete_statement check about its input?",
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
  "expected_answer": "Return True if the string *statement* appears to contain one or more complete SQL statements. No syntactic verification or parsing of any kind is performed, other than checking that there are no unclosed string literals and the statement is terminated by a semicolon.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.sqlite3_s12390_12673",
      "doc_id": "py3119.sqlite3",
      "start_char": 12390,
      "end_char": 12673,
      "text": "Return ``True`` if the string *statement* appears to contain\n   one or more complete SQL statements.\n   No syntactic verification or parsing of any kind is performed,\n   other than checking that there are no unclosed string literals\n   and the statement is terminated by a semicolon."
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

py3119.sqlite3_s12390_12673; Unicode [12390, 12673). [Full pinned source](../../sources/sqlite3.rst); [official reader URL](https://docs.python.org/3.11/library/sqlite3.html).
```text
Return ``True`` if the string *statement* appears to contain
   one or more complete SQL statements.
   No syntactic verification or parsing of any kind is performed,
   other than checking that there are no unclosed string literals
   and the statement is terminated by a semicolon.
```

## py311v2_test_016

```text
In Python 3.11, how does sqlite3.Connection.execute use a cursor?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_016",
  "question": "In Python 3.11, how does sqlite3.Connection.execute use a cursor?",
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
  "expected_answer": "Create a new Cursor object and call Cursor.execute on it with the given *sql* and *parameters*. Return the new cursor object.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.sqlite3_s22552_22707",
      "doc_id": "py3119.sqlite3",
      "start_char": 22552,
      "end_char": 22707,
      "text": "Create a new :class:`Cursor` object and call\n      :meth:`~Cursor.execute` on it with the given *sql* and *parameters*.\n      Return the new cursor object."
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

py3119.sqlite3_s22552_22707; Unicode [22552, 22707). [Full pinned source](../../sources/sqlite3.rst); [official reader URL](https://docs.python.org/3.11/library/sqlite3.html).
```text
Create a new :class:`Cursor` object and call
      :meth:`~Cursor.execute` on it with the given *sql* and *parameters*.
      Return the new cursor object.
```

## py311v2_test_017

```text
In Python 3.11, what does sqlite3.Cursor.fetchone return when no rows remain?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_017",
  "question": "In Python 3.11, what does sqlite3.Cursor.fetchone return when no rows remain?",
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
  "expected_answer": "If Cursor.row_factory is None, return the next row query result set as a tuple. Else, pass it to the row factory and return its result. Return None if no more data is available.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.sqlite3_s48523_48744",
      "doc_id": "py3119.sqlite3",
      "start_char": 48523,
      "end_char": 48744,
      "text": "If :attr:`~Cursor.row_factory` is ``None``,\n      return the next row query result set as a :class:`tuple`.\n      Else, pass it to the row factory and return its result.\n      Return ``None`` if no more data is available."
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

py3119.sqlite3_s48523_48744; Unicode [48523, 48744). [Full pinned source](../../sources/sqlite3.rst); [official reader URL](https://docs.python.org/3.11/library/sqlite3.html).
```text
If :attr:`~Cursor.row_factory` is ``None``,
      return the next row query result set as a :class:`tuple`.
      Else, pass it to the row factory and return its result.
      Return ``None`` if no more data is available.
```

## py311v2_test_018

```text
In Python 3.11, what rows does sqlite3.Cursor.fetchall return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_018",
  "question": "In Python 3.11, what rows does sqlite3.Cursor.fetchall return?",
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
  "expected_answer": "Return all (remaining) rows of a query result as a list. Return an empty list if no rows are available. Note that the arraysize attribute can affect the performance of this operation.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.sqlite3_s49543_49761",
      "doc_id": "py3119.sqlite3",
      "start_char": 49543,
      "end_char": 49761,
      "text": "Return all (remaining) rows of a query result as a :class:`list`.\n      Return an empty list if no rows are available.\n      Note that the :attr:`arraysize` attribute can affect the performance of\n      this operation."
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

py3119.sqlite3_s49543_49761; Unicode [49543, 49761). [Full pinned source](../../sources/sqlite3.rst); [official reader URL](https://docs.python.org/3.11/library/sqlite3.html).
```text
Return all (remaining) rows of a query result as a :class:`list`.
      Return an empty list if no rows are available.
      Note that the :attr:`arraysize` attribute can affect the performance of
      this operation.
```

## py311v2_train_049

```text
In Python 3.11, what string format does date.isoformat return?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_049",
  "question": "In Python 3.11, what string format does date.isoformat return?",
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
  "expected_answer": "Return a string representing the date in ISO 8601 format, YYYY-MM-DD.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.datetime_s26343_26417",
      "doc_id": "py3119.datetime",
      "start_char": 26343,
      "end_char": 26417,
      "text": "Return a string representing the date in ISO 8601 format, ``YYYY-MM-DD``::"
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

py3119.datetime_s26343_26417; Unicode [26343, 26417). [Full pinned source](../../sources/datetime.rst); [official reader URL](https://docs.python.org/3.11/library/datetime.html).
```text
Return a string representing the date in ISO 8601 format, ``YYYY-MM-DD``::
```

## py311v2_train_050

```text
In Python 3.11, what timezone information does datetime.utcnow attach to its result?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_050",
  "question": "In Python 3.11, what timezone information does datetime.utcnow attach to its result?",
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
  "expected_answer": "Return the current UTC date and time, with .tzinfo None.",
  "expected_safe_behavior": "Answer only from the cited Python 3.11.9 passages; preserve qualifications and cite exact support.",
  "absence_note": null,
  "evidence_spans": [
    {
      "id": "py3119.datetime_s31697_31765",
      "doc_id": "py3119.datetime",
      "start_char": 31697,
      "end_char": 31765,
      "text": "Return the current UTC date and time, with :attr:`.tzinfo` ``None``."
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

py3119.datetime_s31697_31765; Unicode [31697, 31765). [Full pinned source](../../sources/datetime.rst); [official reader URL](https://docs.python.org/3.11/library/datetime.html).
```text
Return the current UTC date and time, with :attr:`.tzinfo` ``None``.
```
