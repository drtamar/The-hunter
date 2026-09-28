---
description: Auto-pivot from one finding to its graph neighbors — follows email→reverse-WHOIS→new-domains, wallet→counterparty→exchange, handle→cross-platform, etc.
argument-hint: from-finding <EV-ID>  [--depth=N]
allowed-tools: Read, Write, Bash, Task
---

The user ran `/pivot $ARGUMENTS`. Format: `from-finding <EV-ID> [--depth=N]` (default depth=1, capped at scope.opsec.max_pivot_depth).

## Plan

1. Look up the EV-ID in the case’s `findings.jsonl` and `evidence.jsonl`. Identify the artifact kind and value.
2. Build the **pivot map** from the value:

| Value kind     | Pivot edges to follow |
| ---            | --- |
| email          | reverse-WHOIS (Whoxy/SecurityTrails), Gravatar, breach lookups, cross-platform username (sherlock if local-part used as handle) |
| domain         | shared-cert SANs, shared registrar+registrant via reverse-WHOIS, shared favicon-MMH3 (Shodan), Wayback siblings |
| ip             | co-hosted domains (Shodan reverse-DNS), ASN siblings, banner-similarity matches |
| wallet         | top counterparties → their tags / exchange tags; common-input cluster (BTC); same-deposit-pattern (any chain) |
| handle         | username on other platforms (sherlock/maigret), connected accounts (bio links, follower-graph) |
| favicon-mmh3   | Shodan `http.favicon.hash:<n>` — every co-using host |
| tls-fingerprint| Censys / Shodan `ssl.cert.fingerprint:<…>` — every co-using host |
| registrant-email| reverse-WHOIS → every other domain registered to that email |

3. Spawn the matching subagent for each pivot edge, with `depth = original_depth + 1` (cap at `scope.opsec.max_pivot_depth`).

## Output

Return:
- The new findings (each with their own EV-IDs).
- The updated alias / infrastructure graph delta.
- Recommended next pivots (so the user can chain `/pivot` calls).

## Refusals

If the original EV-ID is graded `D`, `E`, or `F`, warn before pivoting — you risk amplifying noise. Ask the user to confirm.
