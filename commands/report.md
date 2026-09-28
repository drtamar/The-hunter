---
description: Generate an investigation dossier — interim or final. Runs hypothesis tracker + A–F grading + PII redaction.
argument-hint: interim | final  [--case=<CASE-ID>]  [--format=markdown,pdf]
allowed-tools: Read, Write, Bash, Task
---

The user ran `/report $ARGUMENTS`.

## Parse

- Subcommand: first token — `interim` or `final`.
- Optional `--case=CASE-ID` (default: current/most-recent).
- Optional `--format=markdown,pdf` (default: markdown).

## Execute

Delegate to `report-synthesizer` subagent with:
```
{
  case_id: <resolved>,
  mode: "interim"|"final",
  scope_path: "scope/scope.yaml",
  output_format: <list>
}
```

## Final-mode checks

If `mode == final`, before writing:
- Confirm there is at least one `Confirmed` finding OR a clear authorization for an empty-result final report.
- Compute and embed the scope hash.
- Refuse to publish if `victim_pii` is empty (likely the user forgot to declare it; don’t leak them).

## Return

Report path(s) and SHA-256 of each output file. Also tell the user the manifest entry that was appended to `case/<CASE-ID>/reports/manifest.jsonl`.
