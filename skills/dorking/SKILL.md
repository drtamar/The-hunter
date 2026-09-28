---
name: dorking
description: Search-engine and surface-database dorking patterns for Google, Bing, DuckDuckGo, GitHub Code Search, Shodan, and Censys. Use to enumerate scammer infrastructure, leaked content, and exposed assets without active scanning.
---

# Dorking Skill

Query patterns to extract attribution-grade signal from public surfaces. Imported from `drtamar/dorking-skill` and tightened for scam-attribution.

## Google / Bing / DuckDuckGo

### Find a target’s footprint
```
site:<domain>                        # everything indexed
site:<domain> -www                   # subdomains the search engine has indexed
site:<domain> ext:pdf|doc|xls        # leaked office docs
site:<domain> intext:"@"             # email addresses on pages
site:<domain> inurl:admin|login|wp-admin
site:pastebin.com "<domain>" OR "<email>"   # paste leaks
site:github.com "<domain>" OR "<email>"
site:linkedin.com/in "<domain or company>"
site:facebook.com|t.me|x.com|reddit.com "<handle>"
```

### Find scam patterns
```
"<scammer-handle>" ("scam"|"fraud"|"stolen"|"refund")
"<wallet-address>" site:reddit.com|x.com|t.me|telegra.ph|chainabuse.com
"<domain>" "reported"|"complaint"|"trustpilot"
intitle:"index of" "<keyword>"        # exposed dirs
```

### Find leaked credentials (passive only — do NOT use the creds)
```
"<email>" pastebin.com|ghostbin.com|telegra.ph|justpaste.it
"<email>" filetype:txt|csv|sql
site:github.com "<email>" extension:env|json|yml
```

### Geo / OSINT pivots
```
intext:"<phone>" OR "<phone reformatted>"
"<image-filename>"                    # find re-uploads
```

## GitHub Code Search

```
<email> path:.env
<api-key-prefix> language:json
<domain> extension:env|yml|json
org:<org-name> <secret-pattern>
"<wallet-address>" extension:json|md
```

Always feed hits to `evidence-officer` for archival — GitHub will scrub and rotate keys, but the leak is still attributable.

## Shodan

```
http.favicon.hash:<MMH3>              # find every host serving the same favicon (powerful pivot)
ssl.cert.subject.cn:"<domain>"        # cert SAN-based pivots
ssl.cert.serial:<n>                   # exact-cert sibling-host pivot
http.title:"<unique-string>"          # find clones
hostname:<domain>
org:"<asn-org>"
http.html_hash:<n>                    # exact HTML body match — phishing-kit detection gold
http.html:"<unique-string-from-page>"
country:<cc> port:<n> product:"<svc>"
asn:AS<n> port:443 ssl:"<keyword>"
```

Favicon-MMH3 and html_hash are the two most under-used Shodan keys; for scam-attribution, they routinely surface entire networks of clone shops sharing one operator.

## Censys

```
services.tls.certificates.leaf_data.subject_dn:"<domain>"
same_service.tls.certificates.leaf_data.fingerprint_sha256:"<…>"
services.http.response.body_hash:"sha1:<…>"
autonomous_system.asn:<n>
```

## crt.sh

```
https://crt.sh/?q=<domain>&output=json                 # SAN siblings
https://crt.sh/?q=<email>&output=json                  # certs registered with this email (rare, valuable)
https://crt.sh/?q=%25<word>%25&output=json             # wildcard — every SAN containing <word>
```

## Wayback

```
https://web.archive.org/cdx/search/cdx?url=<domain>&output=json&limit=1000
https://web.archive.org/cdx/search/cdx?url=*.example.com&matchType=domain&fl=original,timestamp&output=json
```

The second pattern enumerates every subdomain Wayback ever crawled — historical SAN siblings.

## Telegram

- `t.me/s/<channel>` — last-N public messages without auth.
- `tgstat.com/<channel>` — channel stats.
- Cross-channel mentions — search across multiple known scam channels for the target string.

## Operational rules

- Every notable hit → `evidence-officer` — search results disappear or change daily.
- Never click through to obviously malicious URLs without containerized browsing.
- Stack queries: a single dork rarely solves attribution; chain 5–10.
- When a query returns >50 results, narrow before archiving — quality > quantity in the ledger.
