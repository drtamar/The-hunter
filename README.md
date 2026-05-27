# The Hunter — OSINT Cybersecurity Super-Agent

This directory adds **The Hunter** as a Claude Code plugin overlay on top of the existing `AI-OSINT-Framework` repo. It does not modify the existing `core/`, `modules/`, `ai_tools/` Python package — those continue to live unchanged. The Hunter sits above them as a Claude Code plugin + Python helper library.

## What is this?

A single, unified OSINT super-agent synthesized from the best capabilities of 50+ OSINT/pentest repos in this organization. Designed for **legitimate scam-attribution** and **authorized investigations**: scope-driven, evidence-first, legally-defensible.

## Capability synthesis

| Capability | Source |
| --- | --- |
| Plugin shell + MCP config | `claude-osint-plugin` |
| Root persona + ATT&CK skill index | `Anthropic-Cybersecurity-Skills` |
| OSINT knowledge corpus | `Claude-OSINT/skills/offensive-osint/SKILL.md` (chunked) |
| Social / archiving / verification skills | `claude-skills-journalism` |
| Dorking | `dorking-skill` |
| Chain-of-custody commands | `Claude-Legal-Investigative-Plugin` |
| Crypto tracing + scam-domain check | `cti-expert` |
| Case lifecycle + evidence (Wayback + archive.today + SHA-256 + EV-IDs + Heuer ACH) | `huntkit` |
| Identity correlation engine | `ghost` |
| Primary-source schema (Superseded/Contradicted markers) | `UAP_OSINT-v0.1` |
| Findings DB + multi-channel notifier | `claudeos` |
| Always-on poller + tiered sources + dedup + scoring | `strike-monitor` |
| Alias graph + data-archivist | `newsroom-extension` |
| Hypothesis tracker (Confirmed/Indeterminate/Refuted) | `intellyweave` |
| World-intel MCP (Qdrant + circuit-breaker + 110 tools) | `world-intel-mcp` |
| Shodan MCP (production Pydantic) | `shodan-mcp` |
| Pentest-OSINT MCP + chat-key-vault | `pentest-osint-mcp-server` |

## Quick start

```bash
# 1. Sibling-checkout the MCP backends (one-time)
cd ..
git clone https://github.com/drtamar/world-intel-mcp
git clone https://github.com/drtamar/shodan-mcp
git clone https://github.com/drtamar/pentest-osint-mcp-server
cd AI-OSINT-Framework

# 2. Set API keys in your shell or .env
export SHODAN_API_KEY=...
export VIRUSTOTAL_API_KEY=...
# (others optional — see .mcp.json)

# 3. Declare an investigation scope
cp scope/scope.template.yaml scope/scope.yaml
# edit scope.yaml — fill in targets, victim PII to redact, opsec settings

# 4. In Claude Code, install this plugin (already wired via .claude-plugin/plugin.json)
# Then hunt:
/hunt scammer-domain.com
/trace wallet 0xabc123...
/monitor add domain newscamdomain.com
/report final
```

## Slash command reference

| Command | Purpose |
| --- | --- |
| `/scope set` / `/scope show` / `/scope lock` | declare and freeze the engagement scope |
| `/hunt <target>` | full investigation — orchestrator delegates to all relevant subagents |
| `/trace wallet\|domain\|email\|handle <value>` | targeted single-vector trace |
| `/archive <url>` | chain-of-custody capture (Wayback + archive.today + SHA-256) |
| `/monitor add\|list\|alerts` | manage continuous watchlist |
| `/report interim\|final` | generate hypothesis-tracked dossier |
| `/ev log\|list\|verify` | evidence ledger operations |
| `/pivot from-finding <EV-ID>` | auto-pivot from one finding to its neighbors |

## Subagents

Live in `agents/`. The orchestrator (`hunter`) delegates to:
- `infra-attribution` — domain, IP, SSL, registrar, ASN, hosting
- `identity-correlator` — email, phone, handle, breach correlation
- `financial-tracer` — crypto wallets, payment processors, sanctions
- `social-intel` — Telegram/X/IG/FB/TikTok/Discord/Reddit/LinkedIn
- `evidence-officer` — chain-of-custody capture and EV-ID issuance
- `threat-intel` — IOC enrichment, scam-domain DBs, CTI feeds
- `continuous-monitor` — watchlist + alerting + re-emergence detection
- `report-synthesizer` — hypothesis tracking and final dossier

## Hooks (default-on)

- `hooks/opsec-gate.sh` — PreToolUse — refuses out-of-scope lookups, redacts victim PII
- `hooks/audit-log.sh` — PostToolUse — append-only `case/<CASE-ID>/audit.jsonl`
- `hooks/evidence-capture.sh` — PostToolUse on web fetches — auto-archive + hash + EV-ID

## Built for legitimate use

The Hunter is designed for: scam victims pursuing attribution, authorized pentest engagements, CTF competitions, journalism source-protection investigations, threat intelligence work, and academic OSINT research. The scope-file mechanism (`scope/scope.yaml`) is the entry barrier: no scope file → no active OSINT.

## License

Apache-2.0 (matches parent `AI-OSINT-Framework`).
