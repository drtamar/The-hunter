---
description: Manage the continuous-monitoring watchlist — add, list, poll, alerts. Watches survive across sessions.
argument-hint: add <kind> <value> [interval] | list | poll | alerts [--since=<n>d]
allowed-tools: Read, Write, Bash, Task
---

The user ran `/monitor $ARGUMENTS`. Parse the first token as the subcommand.

## `add`

Args: `add <kind> <value> [interval_minutes]`. Valid kinds match the table in `agents/continuous-monitor.md`.

Delegate to `continuous-monitor` subagent with `op: add`, `kind`, `value`, `poll_interval_minutes` (default 60).

Return confirmation: watch ID, polling interval, alert channels.

## `list`

Delegate to `continuous-monitor` with `op: list`. Pretty-print the result as a markdown table.

## `poll`

Force a polling cycle now (rather than waiting for the scheduled interval). Delegate to `continuous-monitor` with `op: poll`. Return the count of watches polled, hits, and any alerts emitted.

Use this when the user wants an immediate sweep without waiting for the cron / loop.

## `alerts`

Args: `alerts [--since=Nd]` (default 7d).

Read `case/*/alerts.jsonl`, filter by recency, pretty-print.

## `remove`

Args: `remove <watch_id>`. Mark a watch inactive (do not delete; we keep history).

## Refusals

Do not add a watch on a domain or handle that isn’t in any case’s scope. Tell the user to add it to scope first via `/scope set`.
