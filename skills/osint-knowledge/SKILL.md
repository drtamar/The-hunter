---
name: osint-knowledge
description: Comprehensive OSINT methodology and reference index. Routing skill that points investigators to the right technique for the target type. Synthesizes the 204 KB Claude-OSINT corpus into operational checklists.
---

# OSINT Knowledge Routing Skill

This skill is the index. It routes you to the right technique by target type. For depth, follow the cross-references to the dedicated skills.

## Decision tree by target type

### Domain or website
1. **WHOIS / RDAP** — registrar, registrant (often privacy-protected, but check), creation/expiration, name servers, abuse contact. Tool: `whois`, RDAP via `https://rdap.org/domain/<d>`.
2. **DNS records** — A, AAAA, MX, TXT, NS, CAA, SOA. Capture SPF / DKIM / DMARC. Each record is a pivot.
3. **Certificate transparency** — `https://crt.sh/?q=<d>&output=json`. Every SAN on the cert is a sibling domain.
4. **Wayback** — `https://web.archive.org/cdx/search/cdx?url=<d>&output=json` for the timeline.
5. **HTTP fingerprint** — favicon-MMH3 hash (Shodan pivot), Server / X-Powered-By headers, Set-Cookie patterns, framework hints, `<title>`.
6. **Subdomain enum** — passive only (subfinder, amass passive, crt.sh) unless `opsec.allow_active_scanning`.
7. **Threat-intel** — URLhaus, PhishTank, OpenPhish, VirusTotal, OTX, ThreatFox.

→ Subagents: `infra-attribution`, `threat-intel`. Skill: `dorking`.

### IP address
1. **Geo / ASN / ISP** — Shodan host, ipinfo.io, ipapi.co.
2. **Open ports / banners** — Shodan (passive). Active nmap only with explicit scope authorization.
3. **Reverse DNS** — every PTR is a pivot.
4. **Co-hosted domains** — Shodan `hostname:` queries.
5. **Reputation** — GreyNoise, AbuseIPDB, Spamhaus DROP, URLhaus.
6. **Honeypot detection** — Shodan honeypot-score (avoid wasting cycles on canaries).

→ Subagents: `infra-attribution`, `threat-intel`.

### Email
1. **Account binding** — holehe (passive, no-login).
2. **Breach exposure** — h8mail, HIBP. Never echo passwords; record dataset name + exposed fields only.
3. **Naming convention discovery** — theHarvester on the email’s domain to find peers; cluster by pattern.
4. **Reverse-WHOIS** — Whoxy / SecurityTrails (paid) — every domain registered with this email.
5. **Gravatar** — `https://www.gravatar.com/avatar/<md5(lower(email))>?d=404` reveals if a Gravatar exists.
6. **Local-part as username** — if `local@x` is unique, run sherlock/maigret on `local`.

→ Subagents: `identity-correlator`. Skill: `attribution-pivots`.

### Phone
1. **Carrier / region / line type** — phoneinfoga.
2. **Search the number on social platforms** that allow phone-based contact discovery (Telegram, WhatsApp — manual interactive).
3. **Reverse-phone DBs** — country-specific (TrueCaller-like services, only where legal).

→ Subagents: `identity-correlator`, `social-intel`.

### Username / handle
1. **Cross-platform discovery** — sherlock, maigret, blackbird (different coverage; run all three).
2. **Per-platform pull** — see `social-media-intel` skill for per-platform playbook.
3. **Account age** — first activity vs. account creation; suspicious gaps imply purchased account.

→ Subagents: `social-intel`, `identity-correlator`. Skill: `social-media-intel`.

### Wallet / payment ref
→ Subagent: `financial-tracer`. Skill: `crypto-tracing`.

### Image (face or photo)
1. **Reverse image search** — TinEye, Yandex, Google Lens (interactive).
2. **Face match** — FaceCheck.id, PimEyes (interactive, paid). Emit a manual-action note.
3. **EXIF** — `exiftool` on the file. Often stripped, but check.
4. **Stock-photo detection** — reverse-image hits to Shutterstock/iStock are red flags.

→ Subagent: `identity-correlator` (with manual-action notes).

## Source grading reference (huntkit / military OSINT)

- **A** Reliable — primary, technically authenticated.
- **B** Usually reliable — third-party with track record.
- **C** Fairly reliable — community-curated, multi-source.
- **D** Not usually reliable — single, unverified.
- **E** Unreliable.
- **F** Cannot be judged.

Report rules: A claims may be stated as fact. B as likely. C as uncorroborated. D–F flagged or omitted.

## Hypothesis discipline (Heuer ACH)

Every actionable claim is `Confirmed | Indeterminate | Refuted`. Confirmed requires ≥ 2 grade-A independent supports and 0 unrebutted grade-A contradictions. Otherwise default to Indeterminate.
