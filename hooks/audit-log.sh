#!/usr/bin/env bash
# hooks/audit-log.sh — PostToolUse hook
#
# Append every tool call (and its return summary) to case/<CASE-ID>/audit.jsonl.
# Runs on every tool use AFTER the call completes. Cheap, append-only.

set -euo pipefail

PAYLOAD="$(cat)"
NOW="$(date -u +%Y-%m-%dT%H:%M:%SZ)"
CASE_ID="${HUNTER_CASE_ID:-no-case}"
DIR="case/${CASE_ID}"
mkdir -p "$DIR"

TOOL="$(echo "$PAYLOAD" | jq -r '.tool_name // "unknown"')"
INPUT="$(echo "$PAYLOAD" | jq -c '.tool_input // {}')"
RESULT="$(echo "$PAYLOAD" | jq -c '.tool_response // {}' | head -c 4096)"

ROW=$(jq -n -c \
  --arg ts "$NOW" \
  --arg case "$CASE_ID" \
  --arg tool "$TOOL" \
  --argjson input "$INPUT" \
  --argjson result "$(echo "$RESULT" | jq -c .)" \
  '{ts:$ts, case:$case, tool:$tool, input:$input, result_summary:$result}')

echo "$ROW" >> "$DIR/audit.jsonl"
echo "{}"
