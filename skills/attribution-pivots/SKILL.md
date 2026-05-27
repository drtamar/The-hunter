---
name: attribution-pivots
description: The pivot heuristics catalog — every value type (email, domain, IP, wallet, handle, favicon-hash, TLS-fingerprint, registrant-email) with its high-yield pivot edges. Read this to plan multi-hop attribution traversal.
---

# Attribution Pivots Skill

Every scam-attribution case is a graph traversal. Each finding is a node; each pivot edge is an attempt to attribute by association. Tighter the edge, higher the confidence.

## Pivot map (value kind → edges)

### email
- **Reverse-WHOIS** — Whoxy / SecurityTrails (paid) → every domain registered with this email. **Highest-yield single edge for scam-attribution.**
- **Gravatar** — `md5(lowercase(email))` → sometimes resolves to a profile photo or display name.
- **Breach-coupling** — h8mail / HIBP → leaked records often pair email with username + name + IP.
- **Local-part as username** — if local-part is unique, treat as a handle pivot (sherlock/maigret).
- **Same-domain peers** — theHarvester on email’s domain reveals corporate naming conventions; cluster.

### domain
- **TLS SAN** — every alt-name on the cert → sibling domain.
- **Cert reissue history** — crt.sh history reveals operator continuity over time.
- **Registrant email (when not redacted)** — reverse-WHOIS pivot.
- **Favicon-MMH3 hash** — Shodan `http.favicon.hash:<n>` → every host serving the same favicon. **Single most under-used pivot for clone-shop networks.**
- **HTML hash** — Shodan `http.html_hash:<n>` → exact body-clone detection.
- **Same registrar + creation-day cluster** — phishing kits register N domains on one day; nearby creation timestamps + same registrar = same operator.
- **Co-hosted on same IP** — Shodan reverse-DNS.
- **Wayback siblings** — historical state may reveal deleted siblings.

### IP
- **Co-hosted domains** — every PTR / Shodan `hostname:` record.
- **ASN siblings** — other IPs in the same /24 may share operator (especially for bulletproof hosters).
- **Banner fingerprint similarity** — `http.html_hash` + `ssl.cert.serial` matching across the AS.

### wallet
- **Top counterparties** (by volume) → hop forward.
- **Common-input cluster (BTC)** → wallets sharing inputs in one tx are usually one entity.
- **Same withdrawal-pattern from exchange** → timing+amount fingerprint.
- **Exchange deposit** → attribution choke point.
- **Tornado / Wasabi / Whirlpool input** → trail broken; mark and stop.

### handle (username)
- **Cross-platform username match** — sherlock / maigret / blackbird; same username on N platforms is suggestive (not conclusive).
- **Bio links** — every URL in the profile bio is a fresh node.
- **Profile photo reverse-image** — stock = false persona; reused across platforms = persona link.
- **Top interlocutors** — N most-replied accounts may be the actor’s network.

### favicon-MMH3 hash
- **Shodan host enumeration** — `http.favicon.hash:<n>` is a population query: returns the universe of hosts using that exact icon. Ten new domains in one query is normal for phishing kits.

### TLS-cert fingerprint (sha256)
- **Censys / Shodan host enumeration** — `ssl.cert.fingerprint:<…>`. Same cert across hosts → same operator (or shared CDN).

### registrant-email
- **Whoxy reverse-WHOIS** — every domain registered to that email. The single most valuable pivot for scam-attribution — phishing operators routinely register dozens of domains under one email before privacy-protection kicks in.

## Confidence multipliers

When multiple distinct pivot types corroborate (registrant-email + favicon-hash + TLS-cert all link domain A to domain B), confidence multiplies. The hypothesis tracker treats convergent independent grade-A pivots as Confirmed-tier evidence.

## Depth and budget

Respect `scope.opsec.max_pivot_depth` (default 3). Past depth 3, signal-to-noise collapses. The orchestrator caps depth even when subagents propose deeper chains.

## Don’t pivot from

- Grade D / E / F findings — you amplify noise.
- Findings already marked `superseded` or `contradicted`.
- Targets in `out_of_scope`.
