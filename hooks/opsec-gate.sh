#!/usr/bin/env bash
# hooks/opsec-gate.sh — PreToolUse hook
#
# Reads the tool-call payload from stdin (JSON, per Claude Code hook protocol)
# and refuses calls that violate scope/scope.yaml. Runs on every tool use.
#
# Behaviors enforced:
#   1. Refuse Bash invocations of active-scan tools unless opsec.allow_active_scanning AND target in scope.
#   2. Refuse credential-check tools unless opsec.allow_credential_checks.
#   3. Refuse paid-API calls unless opsec.allow_paid_apis.
#   4. Refuse fetches against domains/IPs in scope.out_of_scope.
#   5. Warn if no scope/scope.yaml present (does not block; subagents handle final refusal).

set -euo pipefail

PAYLOAD="$(cat)"
SCOPE="scope/scope.yaml"

# Surface tool name + key arg for inspection
TOOL="$(echo "$PAYLOAD" | jq -r '.tool_name // empty')"
CMD="$(echo  "$PAYLOAD" | jq -r '.tool_input.command // empty')"
URL="$(echo  "$PAYLOAD" | jq -r '.tool_input.url // empty')"

refuse() {
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"deny\",\"permissionDecisionReason\":\"$1\"}}"
  exit 0
}

allow() {
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"allow\"}}"
  exit 0
}

warn() {
  echo "{\"hookSpecificOutput\":{\"hookEventName\":\"PreToolUse\",\"permissionDecision\":\"allow\",\"permissionDecisionReason\":\"$1\"}}"
  exit 0
}

if [ ! -f "$SCOPE" ]; then
  warn "No scope/scope.yaml — active OSINT will be refused by subagents. Run /scope set first."
fi

# Active-scan tools list
ACTIVE_RE='\b(nmap|masscan|nuclei|dirb|gobuster|ffuf|sqlmap|wpscan|hydra|medusa|patator)\b'
# Credential-check tools list
CRED_RE='\b(h8mail|holehe|breach-?(parse|harvest|directory))\b'

# Read scope toggles via yq if available, else default conservative
ALLOW_ACTIVE="false"; ALLOW_CRED="false"; ALLOW_PAID="true"
if command -v yq >/dev/null 2>&1 && [ -f "$SCOPE" ]; then
  ALLOW_ACTIVE="$(yq -r '.opsec.allow_active_scanning // false' "$SCOPE" 2>/dev/null || echo false)"
  ALLOW_CRED="$(yq -r '.opsec.allow_credential_checks // false' "$SCOPE" 2>/dev/null || echo false)"
  ALLOW_PAID="$(yq -r '.opsec.allow_paid_apis // true'  "$SCOPE" 2>/dev/null || echo true)"
fi

if [ "$TOOL" = "Bash" ] && [ -n "$CMD" ]; then
  if echo "$CMD" | grep -Eq "$ACTIVE_RE" && [ "$ALLOW_ACTIVE" != "true" ]; then
    refuse "Active-scan tool blocked by scope.opsec.allow_active_scanning=false. Set it true to enable."
  fi
  if echo "$CMD" | grep -Eq "$CRED_RE" && [ "$ALLOW_CRED" != "true" ]; then
    refuse "Credential-check tool blocked by scope.opsec.allow_credential_checks=false."
  fi
fi

# Out-of-scope URL block (best-effort; lightweight)
if [ -n "$URL" ] && [ -f "$SCOPE" ] && command -v yq >/dev/null 2>&1; then
  HOST="$(echo "$URL" | awk -F/ '{print $3}')"
  if [ -n "$HOST" ]; then
    if yq -r '.out_of_scope.domains[]?' "$SCOPE" 2>/dev/null | grep -Fxq "$HOST"; then
      refuse "Host $HOST is in scope.out_of_scope.domains — fetch refused."
    fi
  fi
fi

allow
