---
description: Full investigation — the orchestrator delegates to all relevant subagents in parallel and produces an interim dossier.
argument-hint: <target>  (domain | ip | email | phone | handle | wallet | image-path)
allowed-tools: Read, Write, Bash, Task, mcp__github__*, mcp__shodan__*, mcp__pentest-osint__*, mcp__world-intel__*
---

You are running the **Hunter** root flow. The user has run `/hunt $ARGUMENTS`.

## Required preflight

1. Read `scope/scope.yaml`. If missing, abort and tell the user to run `/scope set` first.
2. Validate `$ARGUMENTS` against `scope.targets.*`. Refuse with a clear message if not in scope.
3. Open a case via `python -c "from hunter_lib.case_db import open_case; print(open_case(target='$ARGUMENTS'))"`. Capture the returned `CASE-ID`.
4. Compute `scope_hash = sha256(scope/scope.yaml content)` and record in the case meta.

## Plan

Enumerate which subagents apply to the target kind:

| Target kind  | Subagents to spawn (in parallel) |
| ---          | --- |
| domain / ip  | infra-attribution, threat-intel, evidence-officer (preflight archive) |
| email        | identity-correlator, threat-intel |
| phone        | identity-correlator, social-intel |
| handle       | social-intel, identity-correlator |
| wallet       | financial-tracer, threat-intel |
| image        | identity-correlator (for face/reverse-image hints), evidence-officer (hash + archive) |

Always add `evidence-officer` to the chain so every external fetch yields an EV-ID.

## Execute

Use the Task tool to spawn the chosen subagents IN PARALLEL (single message, multiple tool_use blocks). Pass each `{case_id, scope_path: scope/scope.yaml, target: $ARGUMENTS, depth: 0}`.

As findings stream back, append each to `case/<CASE-ID>/findings.jsonl`.

## Pivot loop

After the first wave returns, scan findings for `pivot_candidates`. For each candidate:
- Check it isn't already covered
- Check `depth + 1 ≤ scope.opsec.max_pivot_depth`
- Check it isn't in `out_of_scope`
- Spawn the appropriate subagent with `depth = depth + 1`

Keep pivoting until no new candidates or depth limit reached.

## Synthesize

When all subagents quiesce, call `report-synthesizer` with `mode: "interim"` and `output_format: ["markdown"]`. Write the report to `case/<CASE-ID>/reports/`.

## Wrap up

Output to the user:
- Case ID and report path
- One-paragraph summary (Confirmed / Indeterminate / Refuted counts)
- Top 3 actionable next steps (e.g., "Subpoena Binance for tx-hash X", "Run `/monitor add registrant-email scammer@y.com`")
- Offer: “Want to add this target to continuous monitoring? Run `/monitor add ...`”

## Refusals

If any subagent reports a scope violation or a refused operation, stop the entire flow, log the violation to `case/<CASE-ID>/audit.jsonl`, and return an error to the user. Never “route around” a scope refusal.
