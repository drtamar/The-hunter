---
name: chain-of-custody
description: The legal-grade evidence-handling discipline. Defines how artifacts are sealed, identified (EV-IDs), and tracked across supersession and contradiction. Required reading for evidence-officer and any subagent producing artifacts.
---

# Chain of Custody Skill

Fusion of `drtamar/huntkit` (capture-evidence + EV-IDs) and `drtamar/UAP_OSINT-v0.1` (primary-source schema with Superseded/Contradicted markers). This is the protocol the Evidence Officer enforces.

## Core invariants

1. **Append-only ledger.** `case/<CASE-ID>/evidence.jsonl` is never edited or rewritten. Status changes are added as new rows that reference the original.
2. **Every artifact has an EV-ID.** Sequential, prefix `EV-`, zero-padded to 4. Issued by `hunter_lib.evidence_log.next_id()`.
3. **Triple-archive.** Wayback + archive.today + local snapshot + SHA-256. See `web-archiving` skill.
4. **Source-graded.** A–F, per huntkit. Default conservative — downgrade on any failure.
5. **Verifiable.** `python -m hunter_lib.cli evidence verify --case <ID>` rehashes everything and reports drift. Final reports must include the verify result.

## Ledger row schema (JSONL)

```json
{
  "ev_id": "EV-0042",
  "case_id": "CASE-2026-0001",
  "kind": "url",
  "source": "https://scammer.example.com/promo",
  "collected_by": "infra-attribution",
  "collected_at": "2026-05-01T14:32:11Z",
  "sha256": {
    "raw": "<hex>",
    "screenshot": "<hex>",
    "canonical": "<hex>"
  },
  "archives": {
    "wayback": "https://web.archive.org/web/2026…/...",
    "archive_today": "https://archive.ph/abcde"
  },
  "source_grade": "A",
  "status": "sealed",
  "superseded_by": null,
  "contradicted_by": [],
  "notes": ""
}
```

### Supersession (page changed, account deleted, edited tweet)
```json
{"ev_id":"EV-0050","supersedes":"EV-0042","reason":"page edited", … normal fields…}
```

### Contradiction (later evidence disputes earlier finding)
```json
{"ev_id":"EV-0051","contradicts":["EV-0042"],"reason":"different registrant on RDAP refresh", … normal fields…}
```

The `report-synthesizer` reads `supersedes` / `contradicts` markers when computing hypothesis confidence.

## What gets an EV-ID

- Every external URL fetched (full HTML + screenshot + hashes).
- Every API JSON response (saved as `<EV-ID>.json`).
- Every screenshot pasted/uploaded by the user.
- Every chat-log export (Telegram dump, Discord log).
- Every document the user provides (PDF receipt, email .eml, .msg).
- Every wallet snapshot (block-explorer page state at a given block height).

## What does NOT get an EV-ID

- The investigator’s own research notes (those go in case notes, not the evidence ledger).
- Inferences and conclusions — those are *findings*, not evidence. They live in `findings.jsonl`, citing EV-IDs.
- Raw search engine result lists — only the actual artifacts each result points to (after fetch + archive).

## Verification protocol

```bash
python -m hunter_lib.cli evidence verify --case CASE-2026-0001
```
For each row:
- Recompute SHA-256 of `case/<ID>/raw/<EV-ID>.html` and compare to `sha256.raw`.
- Recompute SHA-256 of `case/<ID>/raw/<EV-ID>.png` and compare to `sha256.screenshot`.
- Hit the Wayback URL and confirm 200 OK.
- Hit the archive.today URL and confirm 200 OK.

Result written to `case/<CASE-ID>/audit.jsonl`. Final reports must include the verify summary.

## Refusals (Evidence Officer enforces)

- Refuse to seal artifacts from `out_of_scope` domains.
- Refuse to seal artifacts containing `victim_pii` matches before redaction. (Run `pii-redaction` skill first.)
- Refuse to seal artifacts the user produced themselves about themselves — you don’t investigate yourself.
