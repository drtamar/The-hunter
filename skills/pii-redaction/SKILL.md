---
name: pii-redaction
description: Scrub investigator PII (names, emails, phones, addresses, IPs, bank/wallet) from any text before saving or sharing. Protects the user from leaking themselves into artifacts that may be subpoenaed, leaked, or publicly archived.
---

# PII Redaction Skill

The Hunter is built for victims and authorized investigators. Their PII must never appear in:
- The final dossier
- Any archived artifact (we save sanitized HTML; Wayback gets the original target page, not your annotations)
- Audit logs
- Notification messages
- Any file pushed to a remote (incl. repository commits)

## Source of truth

`scope/scope.yaml → victim_pii`. The redactor reads from this list. Any string match (case-insensitive for names; exact-with-normalization for emails / phones / wallets) is replaced with `[REDACTED-PII]`.

## Patterns

- **Names** — word-boundary match, case-insensitive. Multi-token names match all permutations ("John Q Public", "John Public", "Public, John", "J. Public").
- **Emails** — exact match plus aliases (`name+tag@x.com` matches `name@x.com`).
- **Phones** — normalize to E.164 before match; match against all common formats.
- **Addresses** — fuzzy: street + number + zip; OK to overshoot redact.
- **Bank accounts** — match last-4 *and* full numbers; show `[REDACTED-BANK-***1234]`.
- **Wallets** — case-insensitive exact-match; show `[REDACTED-WALLET-0xab…]` (preserve first-2 last-4 for context).
- **IP addresses** (your own) — exact-match only; preserve `0.0.0.0/0` etc. for technical clarity.
- **Case-ID aliases** — your external case numbers (e.g., FBI IC3 ref) shouldn’t leak.

## Procedure

```python
from hunter_lib.pii_redactor import redact_text

clean, hits = redact_text(text, scope_yaml_path="scope/scope.yaml")
# clean → the scrubbed text
# hits  → list of (kind, original, replacement, position) for the sidecar redactions.json
```

Write `clean` to the report; write `hits` (in case dir, never published) to `case/<CASE-ID>/reports/redactions-<timestamp>.json` so you can audit your own redactions later.

## Two-pass before publishing

1. First pass at write-time of every subagent’s findings.
2. Second pass at report compilation in `report-synthesizer`. Both passes are mandatory.

## What the redactor does NOT do

- Does not scrub the *target's* identifiers — those are the investigation’s subject and must remain.
- Does not silently fail. If the redactor cannot read `scope.yaml`, it raises and blocks the publish step.
- Does not redact in evidence-ledger rows for sealed artifacts — those preserve raw state by design (chain of custody). Redaction happens only on report compilation and on shared/notified content.

## Edge cases

- Investigator's name appearing inside a quote of the scammer (e.g., scammer addressed the victim by name) — redact in the quote: `"Dear [REDACTED-PII], please send…"`.
- Investigator-controlled domain that appears in scammer’s phishing kit (e.g., a redirect to your site) — redact the domain in the report.
- Multiple investigators on one case — redact all listed `victim_pii` consistently.
