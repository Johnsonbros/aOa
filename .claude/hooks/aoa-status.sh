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
# Returns: evaluated count and hit percentage
get_accuracy() {
    local metrics
    metrics=$(curl -s --max-time 0.5 "${AOA_URL}/metrics" 2>/dev/null)
    if [ -z "$metrics" ]; then
        echo "0 0"
        return
    fi

    local evaluated hit_pct
    evaluated=$(echo "$metrics" | jq -r '.rolling.evaluated // 0' 2>/dev/null)
    hit_pct=$(echo "$metrics" | jq -r '.rolling.hit_at_5_pct // 0' 2>/dev/null)
    echo "$evaluated $hit_pct"
}

# Format with traffic lights
format_accuracy() {
    local evaluated="$1"
    local hit_pct="$2"

    # Learning mode - traffic light only
    if [ "$evaluated" -lt 2 ] 2>/dev/null; then
        # Grey = learning (neutral, not broken)
        echo -e "${DIM}⚪${RESET}"
    elif [ "$evaluated" -lt 3 ] 2>/dev/null; then
        # Yellow = calibrating
        echo -e "${YELLOW}🟡${RESET}"
    else
        # Ready - show traffic light + percentage
        local pct_int
        pct_int=$(printf "%.0f" "$hit_pct")
        if [ "$pct_int" -ge 80 ] 2>/dev/null; then
            echo -e "${GREEN}🟢 ${BOLD}${pct_int}%${RESET}"
        else
            # Yellow for anything below 80%
            echo -e "${YELLOW}🟡 ${BOLD}${pct_int}%${RESET}"
        fi
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

# Get and format accuracy with traffic lights
read -r EVAL HIT_PCT <<< "$(get_accuracy)"
ACC_DISPLAY=$(format_accuracy "$EVAL" "$HIT_PCT")

# Build branded output - TRAFFIC LIGHT FIRST
echo -e "${CYAN}${BOLD}⚡ aOa${RESET} ${ACC_DISPLAY} ${DIM}│${RESET} ${INTENTS} intents ${DIM}│${RESET} ${YELLOW}${RECENT}${RESET}"
