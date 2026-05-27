---
name: web-archiving
description: How to seal a URL with full chain-of-custody — Wayback + archive.today + local snapshot + SHA-256 + screenshot. Used by every web-fetch-touching subagent.
---

# Web Archiving Skill

The sealing protocol. Every external URL the Hunter touches must be archived through this skill (executed via `evidence-officer`).

## Why three archive layers

1. **Wayback Machine** — widely accepted in courts and journalism. Public, neutral.
2. **archive.today** — captures pages that Wayback can’t (JS-heavy, cookie-walled). Different operator, jurisdictionally distinct.
3. **Local snapshot + SHA-256** — you control the chain. If both public archives later go dark, you still have the sealed copy + a hash that proves it didn’t change.

More layers = more defensible.

## Procedure (per URL)

```bash
URL="$1"
EV_ID="$(python -c 'from hunter_lib.evidence_log import next_id; print(next_id())')"
CASE_DIR="case/${CASE_ID}"
mkdir -p "${CASE_DIR}/raw"

# 1. Wayback save — capture the X-Cache-Key/Content-Location
WAYBACK_URL=$(curl -sI "https://web.archive.org/save/${URL}" | awk -F': ' '/^Content-Location:/ {print $2}' | tr -d '\r')

# 2. archive.today save — follow the redirect chain
ARCHIVE_TODAY_URL=$(curl -sIL --data-urlencode "url=${URL}" "https://archive.ph/?run=1" | awk -F': ' '/^Refresh:|^Location:/ {print $2}' | tail -1 | tr -d '\r')

# 3. Local snapshot
wget --no-check-certificate -q -O "${CASE_DIR}/raw/${EV_ID}.html" "${URL}"

# 4. WARC capture (optional, set in scope.evidence.warc_capture)
if [ "${WARC_CAPTURE:-false}" = "true" ]; then
  wget --warc-file="${CASE_DIR}/raw/${EV_ID}" --warc-cdx -q -O /dev/null "${URL}"
fi

# 5. Screenshot (best-effort)
if command -v chromium >/dev/null 2>&1; then
  chromium --headless --disable-gpu --screenshot="${CASE_DIR}/raw/${EV_ID}.png" --window-size=1280,1800 "${URL}" 2>/dev/null
fi

# 6. Hash everything
RAW_SHA=$(sha256sum "${CASE_DIR}/raw/${EV_ID}.html" | awk '{print $1}')
SCREEN_SHA=$([ -f "${CASE_DIR}/raw/${EV_ID}.png" ] && sha256sum "${CASE_DIR}/raw/${EV_ID}.png" | awk '{print $1}' || echo "")

# 7. Append to ledger
python -c "from hunter_lib.evidence_log import seal; seal(case='${CASE_ID}', ev_id='${EV_ID}', kind='url', source='${URL}', sha256={'raw':'${RAW_SHA}','screenshot':'${SCREEN_SHA}'}, archives={'wayback':'${WAYBACK_URL}','archive_today':'${ARCHIVE_TODAY_URL}'}, source_grade='A')"

echo "${EV_ID}"
```

## Failure modes

- Wayback returns 0-byte / 5xx → retry once with 30s back-off; if still fails, downgrade source_grade by one and note in ledger.
- archive.today refused (rate-limit or captcha) — fall through; continue Wayback + local.
- `wget` fails (TLS issue) — try `curl -sLk -o ...`. If both fail, mark `kind=url` with `status=failed-fetch` and grade F.
- Screenshot tool absent — omit; never block.

## Verification (chain-of-custody check)

```bash
python -m hunter_lib.cli evidence verify --case ${CASE_ID}
```
Rehashes every raw file and screenshot and compares to the ledger. Mismatch = chain-of-custody breach — critical for legal handover.
