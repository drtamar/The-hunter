---
description: Targeted single-vector trace — wallet | domain | email | handle | phone | ip | image. Faster than /hunt; runs only the relevant subagent.
argument-hint: <kind> <value>
allowed-tools: Read, Write, Bash, Task
---

You are running a **targeted trace**. Args: `$ARGUMENTS` (expected: `<kind> <value>`).

## Parse

Split `$ARGUMENTS` into `<kind>` and `<value>`. Valid kinds: `wallet`, `domain`, `email`, `handle`, `phone`, `ip`, `image`.

## Preflight

- Read `scope/scope.yaml`; require it exist.
- Verify `<value>` is in scope (allow `<kind>` lookup against the matching scope list).
- Open or attach to an existing case (the user may run `/trace` inside an open case context; otherwise create a single-target case).

## Dispatch

| kind     | subagent               |
| ---      | ---                    |
| wallet   | financial-tracer       |
| domain   | infra-attribution      |
| ip       | infra-attribution      |
| email    | identity-correlator    |
| phone    | identity-correlator + social-intel |
| handle   | social-intel + identity-correlator |
| image    | identity-correlator (with note for manual reverse-image) + evidence-officer |

Spawn the chosen subagent(s) with the Task tool, in parallel where multiple apply.

## Output

Return the subagent’s findings inline (don’t call `report-synthesizer` for a single-vector trace unless the user asks). Append findings to `case/<CASE-ID>/findings.jsonl`. Tell the user how to convert this trace into a full hunt: `/hunt <value>` or how to add the value to monitoring.
