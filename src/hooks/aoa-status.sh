#!/bin/bash
# =============================================================================
# aOa Status Line - Reads from ~/.aoa/status.json
# =============================================================================
#
# Usage in Claude Code settings:
#   "statusLine": "bash /path/to/aoa-status.sh"
#
# =============================================================================

STATUS_FILE="${AOA_STATUS_FILE:-$HOME/.aoa/status.json}"

if [ ! -f "$STATUS_FILE" ]; then
    echo "⚡ aOa │ learning..."
    exit 0
fi

# Read status file
INTENTS=$(jq -r '.intents // 0' "$STATUS_FILE" 2>/dev/null)
TAGS_COUNT=$(jq -r '.tags | length // 0' "$STATUS_FILE" 2>/dev/null)
RECENT=$(jq -r '.recent[:3] | map(gsub("#"; "")) | join(" ")' "$STATUS_FILE" 2>/dev/null)
LAST_TOOL=$(jq -r '.last_tool // ""' "$STATUS_FILE" 2>/dev/null)

if [ "$INTENTS" = "0" ] || [ -z "$INTENTS" ]; then
    echo "⚡ aOa │ learning..."
else
    echo "⚡ aOa │ ${INTENTS} │ ${TAGS_COUNT} tags │ ${RECENT}"
fi
