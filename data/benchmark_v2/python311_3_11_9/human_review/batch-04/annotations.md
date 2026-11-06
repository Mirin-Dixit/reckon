# Proposed annotations and exact passages

Open only after recording your independent first-pass findings. Quotes below are source text; labels are machine-authored candidates, not verified truth.

## py311v2_test_033

```text
For aiosqlite.Cursor.fetchone rather than sqlite3.Cursor.fetchone, how is the result awaited and scheduled?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_033",
  "question": "For aiosqlite.Cursor.fetchone rather than sqlite3.Cursor.fetchone, how is the result awaited and scheduled?",
  "split": "test",
  "cluster_id": "database",
  "source_document_ids": [
    "py3119.sqlite3"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_017"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"aiosqlite.Cursor.fetchone\": [], \"sqlite3.Cursor.fetchone\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.sqlite3_s48523_48744",
      "doc_id": "py3119.sqlite3",
      "start_char": 48523,
      "end_char": 48744,
      "text": "If :attr:`~Cursor.row_factory` is ``None``,\n      return the next row query result set as a :class:`tuple`.\n      Else, pass it to the row factory and return its result.\n      Return ``None`` if no more data is available."
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

py3119.sqlite3_s48523_48744; Unicode [48523, 48744). [Full pinned source](../../sources/sqlite3.rst); [official reader URL](https://docs.python.org/3.11/library/sqlite3.html).
```text
If :attr:`~Cursor.row_factory` is ``None``,
      return the next row query result set as a :class:`tuple`.
      Else, pass it to the row factory and return its result.
      Return ``None`` if no more data is available.
```

## py311v2_test_035

```text
What operation does sqlite3.connect perform, and what exact maximum number of database writes per second does it guarantee?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_035",
  "question": "What operation does sqlite3.connect perform, and what exact maximum number of database writes per second does it guarantee?",
  "split": "test",
  "cluster_id": "database",
  "source_document_ids": [
    "py3119.sqlite3"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_013"
  ],
  "is_answerable": false,
  "category": "attribute_near_miss",
  "expected_decision": "ABSTAIN",
  "question_type": "compound",
  "is_compound": true,
  "ambiguity_type": null,
  "ambiguity_interpretations": [],
  "expected_answer": null,
  "expected_safe_behavior": "Do not invent the requested facts. Explain the evidence limitation, correct any unsupported premise, and offer relevant Python 3.11.9 information with appropriate qualification.",
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"sqlite3.connect\": [\"collections\", \"sqlite3\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
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
  "compound_missing_premises": [
    "The requested numerical performance guarantee is not supplied by the captured documentation."
  ],
  "notes": "Machine-authored candidate checked against captured text; no human acceptance or semantic verification is claimed.",
  "author_id": "codex",
  "candidate_revision": 1,
  "corpus_sha256": "688627f9ce959fd3ca00dbc9b63f577244c88a91a5633318992857f992b8756c",
  "required_human_reviews": 2,
  "required_checks": [
    "answerability",
    "compound",
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

## py311v2_test_037

```text
Since sqlite3.connect automatically backs up every transaction to cloud storage, which bucket and encryption key does it choose?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_test_037",
  "question": "Since sqlite3.connect automatically backs up every transaction to cloud storage, which bucket and encryption key does it choose?",
  "split": "test",
  "cluster_id": "database",
  "source_document_ids": [
    "py3119.sqlite3"
  ],
  "near_miss_parent_ids": [
    "py311v2_test_013"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"sqlite3.connect\": [\"collections\", \"sqlite3\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
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

## py311v2_train_063

```text
What SQL expression converts a timestamp to a civil date in BigQuery?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_063",
  "question": "What SQL expression converts a timestamp to a civil date in BigQuery?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.datetime"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_049"
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
      "id": "py3119.datetime_s26343_26417",
      "doc_id": "py3119.datetime",
      "start_char": 26343,
      "end_char": 26417,
      "text": "Return a string representing the date in ISO 8601 format, ``YYYY-MM-DD``::"
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

py3119.datetime_s26343_26417; Unicode [26343, 26417). [Full pinned source](../../sources/datetime.rst); [official reader URL](https://docs.python.org/3.11/library/datetime.html).
```text
Return a string representing the date in ISO 8601 format, ``YYYY-MM-DD``::
```

## py311v2_train_079

```text
For arrow.utcnow rather than datetime.utcnow, what timezone object is attached to the result?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_079",
  "question": "For arrow.utcnow rather than datetime.utcnow, what timezone object is attached to the result?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.datetime"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_050"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"arrow.utcnow\": [], \"datetime.utcnow\": [\"datetime\"]}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.datetime_s31697_31765",
      "doc_id": "py3119.datetime",
      "start_char": 31697,
      "end_char": 31765,
      "text": "Return the current UTC date and time, with :attr:`.tzinfo` ``None``."
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

py3119.datetime_s31697_31765; Unicode [31697, 31765). [Full pinned source](../../sources/datetime.rst); [official reader URL](https://docs.python.org/3.11/library/datetime.html).
```text
Return the current UTC date and time, with :attr:`.tzinfo` ``None``.
```

## py311v2_train_086

```text
How many nanoseconds does calendar.monthrange take on an AMD Ryzen CPU?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_086",
  "question": "How many nanoseconds does calendar.monthrange take on an AMD Ryzen CPU?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.calendar"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_053"
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
  "absence_note": "Candidate corpus-wide absence judgment pending independent human review; diagnostic spans supply related facts, not evidence for the requested answer. Corpus lexical checks (not semantic proof): {\"calendar.monthrange\": []}. Independent reviewers must inspect alternative wording, examples and all 34 documents; reclassify if a complete grounded answer exists.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.calendar_s12020_12132",
      "doc_id": "py3119.calendar",
      "start_char": 12020,
      "end_char": 12132,
      "text": "Returns weekday of first day of the month and number of days in month,  for the\n   specified *year* and *month*."
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

py3119.calendar_s12020_12132; Unicode [12020, 12132). [Full pinned source](../../sources/calendar.rst); [official reader URL](https://docs.python.org/3.11/library/calendar.html).
```text
Returns weekday of first day of the month and number of days in month,  for the
   specified *year* and *month*.
```

## py311v2_train_087

```text
What maximum number of bytes per cached ZoneInfo instance is guaranteed?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_087",
  "question": "What maximum number of bytes per cached ZoneInfo instance is guaranteed?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.zoneinfo"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_058"
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
      "id": "py3119.zoneinfo_s6430_6793",
      "doc_id": "py3119.zoneinfo",
      "start_char": 6430,
      "end_char": 6793,
      "text": "A concrete :class:`datetime.tzinfo` subclass that represents an IANA time\n    zone specified by the string ``key``. Calls to the primary constructor will\n    always return objects that compare identically; put another way, barring\n    cache invalidation via :meth:`ZoneInfo.clear_cache`, for all values of\n    ``key``, the following assertion will always be true:"
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

py3119.zoneinfo_s6430_6793; Unicode [6430, 6793). [Full pinned source](../../sources/zoneinfo.rst); [official reader URL](https://docs.python.org/3.11/library/zoneinfo.html).
```text
A concrete :class:`datetime.tzinfo` subclass that represents an IANA time
    zone specified by the string ``key``. Calls to the primary constructor will
    always return objects that compare identically; put another way, barring
    cache invalidation via :meth:`ZoneInfo.clear_cache`, for all values of
    ``key``, the following assertion will always be true:
```

## py311v2_train_092

```text
Since monotonic returns a UTC timestamp, which epoch and leap-second conversion rule should I use to decode it?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_092",
  "question": "Since monotonic returns a UTC timestamp, which epoch and leap-second conversion rule should I use to decode it?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.time"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_056"
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
      "id": "py3119.time_s10885_11174",
      "doc_id": "py3119.time",
      "start_char": 10885,
      "end_char": 11174,
      "text": "Return the value (in fractional seconds) of a monotonic clock, i.e. a clock\n   that cannot go backwards.  The clock is not affected by system clock updates.\n   The reference point of the returned value is undefined, so that only the\n   difference between the results of two calls is valid."
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

py3119.time_s10885_11174; Unicode [10885, 11174). [Full pinned source](../../sources/time.rst); [official reader URL](https://docs.python.org/3.11/library/time.html).
```text
Return the value (in fractional seconds) of a monotonic clock, i.e. a clock
   that cannot go backwards.  The clock is not affected by system clock updates.
   The reference point of the returned value is undefined, so that only the
   difference between the results of two calls is valid.
```

## py311v2_train_096

```text
Read the timing clock I meant. Which clock should you call?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_096",
  "question": "Read the timing clock I meant. Which clock should you call?",
  "split": "train",
  "cluster_id": "dates-time",
  "source_document_ids": [
    "py3119.time"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_056",
    "py311v2_train_057"
  ],
  "is_answerable": false,
  "category": "ambiguous_question",
  "expected_decision": "CLARIFY",
  "question_type": "ambiguous",
  "is_compound": false,
  "ambiguity_type": "clarification_required",
  "ambiguity_interpretations": [
    "A monotonic clock",
    "A high-resolution performance counter"
  ],
  "expected_answer": null,
  "expected_safe_behavior": "Ask which of the documented interpretations the requester intends. Do not select one arbitrarily or present either as confirmed intent.",
  "absence_note": "Both documented operations are plausible; the request omits the intended operation/output. Clarification resolves intent, whereas listing both does not authorize choosing one. Independent ambiguity review pending.",
  "evidence_spans": [],
  "diagnostic_spans": [
    {
      "id": "py3119.time_s10885_11174",
      "doc_id": "py3119.time",
      "start_char": 10885,
      "end_char": 11174,
      "text": "Return the value (in fractional seconds) of a monotonic clock, i.e. a clock\n   that cannot go backwards.  The clock is not affected by system clock updates.\n   The reference point of the returned value is undefined, so that only the\n   difference between the results of two calls is valid."
    },
    {
      "id": "py3119.time_s11684_12033",
      "doc_id": "py3119.time",
      "start_char": 11684,
      "end_char": 12033,
      "text": "Return the value (in fractional seconds) of a performance counter, i.e. a\n   clock with the highest available resolution to measure a short duration.  It\n   does include time elapsed during sleep and is system-wide.  The reference\n   point of the returned value is undefined, so that only the difference between\n   the results of two calls is valid."
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

py3119.time_s10885_11174; Unicode [10885, 11174). [Full pinned source](../../sources/time.rst); [official reader URL](https://docs.python.org/3.11/library/time.html).
```text
Return the value (in fractional seconds) of a monotonic clock, i.e. a clock
   that cannot go backwards.  The clock is not affected by system clock updates.
   The reference point of the returned value is undefined, so that only the
   difference between the results of two calls is valid.
```

py3119.time_s11684_12033; Unicode [11684, 12033). [Full pinned source](../../sources/time.rst); [official reader URL](https://docs.python.org/3.11/library/time.html).
```text
Return the value (in fractional seconds) of a performance counter, i.e. a
   clock with the highest available resolution to measure a short duration.  It
   does include time elapsed during sleep and is system-wide.  The reference
   point of the returned value is undefined, so that only the difference between
   the results of two calls is valid.
```

## py311v2_train_062

```text
Which Kubernetes RBAC permissions let a pod create a persistent volume claim?
```
```text
{
  "schema_version": "ragbench.question.v2",
  "dataset_version": "python311-3.11.9-candidates.1",
  "status": "candidate",
  "verification_status": "machine_checked_human_pending",
  "id": "py311v2_train_062",
  "question": "Which Kubernetes RBAC permissions let a pod create a persistent volume claim?",
  "split": "train",
  "cluster_id": "filesystem",
  "source_document_ids": [
    "py3119.pathlib"
  ],
  "near_miss_parent_ids": [
    "py311v2_train_039"
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
      "id": "py3119.pathlib_s29456_29685",
      "doc_id": "py3119.pathlib",
      "start_char": 29456,
      "end_char": 29685,
      "text": "Create a new directory at this given path.  If *mode* is given, it is\n   combined with the process' ``umask`` value to determine the file mode\n   and access flags.  If the path already exists, :exc:`FileExistsError`\n   is raised."
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

py3119.pathlib_s29456_29685; Unicode [29456, 29685). [Full pinned source](../../sources/pathlib.rst); [official reader URL](https://docs.python.org/3.11/library/pathlib.html).
```text
Create a new directory at this given path.  If *mode* is given, it is
   combined with the process' ``umask`` value to determine the file mode
   and access flags.  If the path already exists, :exc:`FileExistsError`
   is raised.
```
