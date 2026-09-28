---
description: Manage the engagement scope file (targets, redactions, opsec). Subcommands set|show|lock|hash.
argument-hint: set|show|lock|hash
allowed-tools: Read, Write, Bash
---

You are operating the scope-management surface. The user ran `/scope $ARGUMENTS`.

## Subcommand: `set`

1. Check if `scope/scope.yaml` already exists. If yes, ask the user whether to overwrite or open for edit.
2. If no, copy `scope/scope.template.yaml` → `scope/scope.yaml`.
3. Walk the user through filling in the required fields interactively, in this order:
   - case_title, investigator, authorization (this is the legal basis — require something concrete, e.g. “Victim of fraud, scope is the alleged scammer’s infrastructure”).
   - targets (collect what they have: domains, handles, wallets, emails, phones).
   - victim_pii (their own name, emails, phones, address, bank, wallets — to redact from outputs).
   - opsec.allow_active_scanning (default false; warn before enabling).
   - opsec.allow_credential_checks (default false; warn).
   - notifications channels (optional).
4. Save and show a diff of what changed.
5. Compute and display `sha256(scope/scope.yaml)` and tell the user this is the scope_hash that will appear in every report.

## Subcommand: `show`

Read and pretty-print `scope/scope.yaml`. Redact `victim_pii.bank_accounts` and `victim_pii.wallets` partial values (last-4 only).

Also show:
- Current scope hash (sha256).
- Active case count (rows in `case/` directory).
- Active watches.

## Subcommand: `lock`

Makes the scope file read-only:
- Compute the hash.
- Append to `scope/scope.lock.jsonl`: `{"locked_at":"…Z","hash":"…","locked_by":"<investigator>"}`.
- `chmod 0444 scope/scope.yaml`.
- Tell the user: any later modification will require explicit unlock and will be logged in `scope.lock.jsonl`.

## Subcommand: `hash`

Print only `sha256(scope/scope.yaml)`. Used by reports and CI checks.

## Refusals

Refuse to add targets that are obviously third-party / bystander accounts (e.g., a domain the user explicitly says they have no relationship to and no evidence of malicious activity from). Push back — “can you describe the harm tying this target to your case?” — before adding.
