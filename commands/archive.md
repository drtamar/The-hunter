---
description: Chain-of-custody capture for one URL — Wayback + archive.today + SHA-256 + screenshot — returns an EV-ID.
argument-hint: <url>
allowed-tools: Read, Write, Bash, Task
---

The user wants to archive `$ARGUMENTS` with full chain-of-custody.

## Preflight

- Read `scope/scope.yaml` (warn but don’t hard-block if missing — archiving is a defensive op; users may want to seal a hostile URL before opening a formal case).
- If scope present, verify the URL’s host is in `scope.targets.domains` or in the `notes`/justification of an existing case. If not, ask: “This URL’s host isn’t in your declared scope. Add it, or proceed as a one-off seal?”

## Execute

Use the Task tool to invoke `evidence-officer` with:
```
{
  case_id: <current or NEW-ONESHOT>,
  artifact_kind: "url",
  source: "$ARGUMENTS",
  source_grade: "A",       # captured-at-source = grade A
  collected_by: "user-via-/archive",
  notes: "manual-capture"
}
```

## Return

Show the user:
- The issued EV-ID.
- Wayback URL.
- archive.today URL.
- Local snapshot path: `case/<CASE-ID>/raw/<EV-ID>.html`.
- Screenshot path (if captured).
- SHA-256 of the raw content.

If any archive target failed, say so explicitly. Do not silently produce a partial seal.
