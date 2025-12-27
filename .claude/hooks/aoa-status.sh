#!/bin/bash
# =============================================================================
# aOa Status Line - Branded with Accuracy First
# =============================================================================
#
# Usage in Claude Code settings:
#   "statusLine": "bash /path/to/aoa-status.sh"
#
# NEW Format (accuracy is first-class):
#   ⚡ aOa 87% │ 25 intents │ editing hooks python
#        ^^^^
#        Bright, visible, LEFT side
#
# =============================================================================

AOA_URL="${AOA_URL:-http://localhost:8080}"
STATUS_FILE="${AOA_STATUS_FILE:-$HOME/.aoa/status.json}"

# ANSI colors - bright variants
CYAN='\033[96m'
GREEN='\033[92m'
YELLOW='\033[93m'
RED='\033[91m'
BOLD='\033[1m'
DIM='\033[2m'
RESET='\033[0m'

# Get accuracy from metrics API (fast, <10ms)
get_accuracy() {
    local metrics
    metrics=$(curl -s --max-time 0.5 "${AOA_URL}/metrics" 2>/dev/null)
    if [ -z "$metrics" ]; then
        echo "---"
        return
    fi

    local evaluated hit_pct
    evaluated=$(echo "$metrics" | jq -r '.rolling.evaluated // 0' 2>/dev/null)
    hit_pct=$(echo "$metrics" | jq -r '.rolling.hit_at_5_pct // 0' 2>/dev/null)

    if [ "$evaluated" -lt 3 ] 2>/dev/null; then
        echo "---"
    else
        printf "%.0f" "$hit_pct"
    fi
}

# Color accuracy based on value
color_accuracy() {
    local acc="$1"
    if [ "$acc" = "---" ]; then
        echo -e "${DIM}---%${RESET}"
    elif [ "$acc" -ge 80 ] 2>/dev/null; then
        echo -e "${GREEN}${BOLD}${acc}%${RESET}"
    elif [ "$acc" -ge 50 ] 2>/dev/null; then
        echo -e "${YELLOW}${BOLD}${acc}%${RESET}"
    else
        echo -e "${RED}${BOLD}${acc}%${RESET}"
    fi
}

# Main
if [ ! -f "$STATUS_FILE" ]; then
    echo -e "${CYAN}${BOLD}⚡ aOa${RESET} ${DIM}│${RESET} learning..."
    exit 0
fi

# Read status file
INTENTS=$(jq -r '.intents // 0' "$STATUS_FILE" 2>/dev/null)
RECENT=$(jq -r '.recent[:5] | map(gsub("#"; "")) | join(" ")' "$STATUS_FILE" 2>/dev/null)

if [ "$INTENTS" = "0" ] || [ -z "$INTENTS" ]; then
    echo -e "${CYAN}${BOLD}⚡ aOa${RESET} ${DIM}│${RESET} learning..."
    exit 0
fi

# Get and format accuracy
ACC=$(get_accuracy)
ACC_COLORED=$(color_accuracy "$ACC")

# Build branded output - ACCURACY FIRST
echo -e "${CYAN}${BOLD}⚡ aOa${RESET} ${ACC_COLORED} ${DIM}│${RESET} ${INTENTS} intents ${DIM}│${RESET} ${YELLOW}${RECENT}${RESET}"
