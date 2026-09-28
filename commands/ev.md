---
description: Evidence ledger ops — log a manual artifact, list ledger, verify integrity.
argument-hint: log <kind> <source> | list [--case=ID] | verify [--case=ID]
allowed-tools: Read, Write, Bash, Task
---

The user ran `/ev $ARGUMENTS`.

## `log`

Args: `log <kind> <source>` where kind ∈ {url, file, text, image}. For inline text/files, the user may provide a path or paste content.

Delegate to `evidence-officer` with the corresponding artifact_kind and source. Return the EV-ID.

## `list`

Args: `list [--case=CASE-ID]` (default: current).

Read `case/<CASE-ID>/evidence.jsonl`, render as a table:
```
EV-ID  | Kind  | Source             | Grade | Status   | Collected by         | At
```

For `superseded` and `contradicted` rows, indent and link to the superseder/contradictor EV-ID.

## `verify`

Args: `verify [--case=CASE-ID]`.

Rehash every raw file and screenshot in `case/<CASE-ID>/raw/`, compare to the recorded SHA-256 in the ledger. Report any mismatch as a chain-of-custody breach — this is critical for the legal-handover section.

Run `python -m hunter_lib.cli evidence verify --case <CASE-ID>` if available.

Return:
- Total artifacts checked
- Matches
- Mismatches (with EV-IDs)
- Missing-files (raw file deleted; ledger entry orphaned)
- A summary line suitable for inclusion in a final report
