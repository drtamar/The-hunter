#!/usr/bin/env bash
# hooks/evidence-capture.sh — PostToolUse hook
#
# When a web-fetching tool runs (WebFetch, mcp__*__http_get, or Bash curl/wget),
# auto-archive the URL through evidence-officer protocol and assign an EV-ID.
# This makes chain-of-custody happen by default, not by remembering.

set -euo pipefail

PAYLOAD="$(cat)"
TOOL="$(echo "$PAYLOAD" | jq -r '.tool_name // empty')"
CASE_ID="${HUNTER_CASE_ID:-no-case}"

is_web_tool() {
  case "$1" in
    WebFetch) return 0 ;;
    Bash)
      CMD="$(echo "$PAYLOAD" | jq -r '.tool_input.command // empty')"
      echo "$CMD" | grep -Eq '^[[:space:]]*(curl|wget)\b' && return 0
      return 1
      ;;
    *) return 1 ;;
  esac
}

extract_url() {
  case "$TOOL" in
    WebFetch) echo "$PAYLOAD" | jq -r '.tool_input.url // empty' ;;
    Bash)     echo "$PAYLOAD" | jq -r '.tool_input.command // empty' \
                | grep -oE 'https?://[^[:space:]"'\'']+' | head -1 ;;
  esac
}

if ! is_web_tool "$TOOL"; then
  echo "{}"
  exit 0
 fi

URL="$(extract_url)"
if [ -z "$URL" ] || [ "$CASE_ID" = "no-case" ]; then
  echo "{}"
  exit 0
fi

# Best-effort archival; never block the parent flow.
(
  python -c "
import sys
try:
    from hunter_lib.archiver import auto_capture
    auto_capture(case_id='$CASE_ID', url='$URL', collected_by='evidence-capture-hook')
except Exception as e:
    sys.stderr.write(f'evidence-capture: {e}\n')
" >/dev/null 2>&1 &
)

echo "{}"
