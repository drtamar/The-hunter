---
name: opsec-firewall
description: Operational security defaults for the Hunter — user-agent rotation, referer suppression, no-leak request headers, optional proxy, paid-API budget cap. Loaded by hooks and HTTP-touching subagents.
---

# Opsec Firewall Skill

Keeps the investigator’s identity and infrastructure off the target’s logs. Defaults are conservative; tighten via `scope.yaml → opsec`.

## What it does

1. **User-agent rotation.** Every outbound HTTP fetch picks a UA from a pool of 12 common desktop / mobile / curl strings. No predictable pattern.
2. **Referer suppression.** Always `Referer:` empty unless the request would obviously look fake without one (a CDN-hosted asset linked from a page).
3. **No-leak headers.** Strip `X-Forwarded-For`, `Via`, `X-Real-IP` from any wrapped tooling. Disable curl `-v` in production paths.
4. **DNS leak control.** When `scope.opsec.proxy` is set (e.g., `socks5://127.0.0.1:9050` for Tor or a residential proxy), all outbound HTTP and DNS goes via it.
5. **Cookie isolation.** No persistent cookies across a case. Each fetch gets a fresh container.
6. **Active-scan gate.** Refuse `nmap`, `masscan`, `nuclei`, `dirb`, `ffuf`, `sqlmap`, `gobuster`, `wpscan` invocations unless `scope.opsec.allow_active_scanning: true` AND the target is in scope.
7. **Credential-check gate.** Refuse `h8mail`, `holehe`, breach-DB lookups unless `scope.opsec.allow_credential_checks: true`.
8. **Paid-API budget cap.** When `scope.opsec.allow_paid_apis: false`, refuse calls that consume paid credits (Shodan keyed, VirusTotal, IntelX, Whoxy paid, etc.).

## Implementation

The opsec firewall is enforced by `hooks/opsec-gate.sh` (PreToolUse) plus a thin Python wrapper in `hunter_lib/opsec.py` that wraps `requests`/`httpx`. Subagents using Bash for `curl` should source the helper:

```bash
source hooks/_opsec-helpers.sh
opsec_curl "https://target/"   # injects UA + headers + proxy
```

or in Python:

```python
from hunter_lib.opsec import session
r = session().get("https://target/")
```

## UA pool

```
Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36
Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15
Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Safari/537.36
Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1
Mozilla/5.0 (Linux; Android 14; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0.0.0 Mobile Safari/537.36
curl/8.6.0
Wget/1.21.4
... (extend in hunter_lib/opsec.py)
```

## Refusals

If opsec.proxy is configured but unreachable (proxy down), refuse the request. Better to fail than to fall back to your real IP.

## When NOT to use opsec rotation

When explicitly authenticating (e.g., logging into your own VirusTotal API), you must use a stable UA / IP. The wrapper allows `session(stable=True)` to opt out for that specific call.
