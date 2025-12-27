#!/bin/bash
# lsp-compare.sh - Knowledge-Seeking Benchmark (Real aOa Capabilities)
#
# Measures what actually matters: How many tool calls to find an answer?
#
# aOa's real power:
#   /symbol - Ranked results, top file is usually correct
#   /predict - Predicts next files with confidence + snippets
#   /intent - Knows what you're working on
#
# Traditional workflow:
#   grep "redis" → 8 files
#   read file1 → wrong
#   read file2 → wrong
#   read file3 → found it!
#   = 4+ calls, 5000+ tokens
#
# With aOa:
#   /symbol?q=redis → top result is gateway.py (correct!)
#   /predict → shows related files + snippets
#   = 1-2 calls, 500 tokens, includes context!

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/assert.sh"

AOA_URL="${AOA_URL:-http://localhost:8080}"
CODEBASE_ROOT="${CODEBASE_ROOT:-/home/corey/aOa}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ============================================================
# KNOWLEDGE-SEEKING QUESTIONS
# ============================================================

declare -A QUESTIONS
declare -A CORRECT_FILES
declare -A SEARCH_TERMS

QUESTIONS[1]="Where is Redis connection configured?"
CORRECT_FILES[1]="gateway.py"
SEARCH_TERMS[1]="redis"

QUESTIONS[2]="How does the indexer work?"
CORRECT_FILES[2]="indexer.py"
SEARCH_TERMS[2]="indexer"

QUESTIONS[3]="Where are intents captured?"
CORRECT_FILES[3]="intent-capture.py"
SEARCH_TERMS[3]="intent"

QUESTIONS[4]="How does prediction work?"
CORRECT_FILES[4]="intent-prefetch.py"
SEARCH_TERMS[4]="predict"

QUESTIONS[5]="Where is health check?"
CORRECT_FILES[5]="gateway.py"
SEARCH_TERMS[5]="health"

# ============================================================
# TRADITIONAL: grep → read → grep → read
# ============================================================

simulate_traditional() {
    local q_id="$1"
    local correct="${CORRECT_FILES[$q_id]}"
    local term="${SEARCH_TERMS[$q_id]}"

    local calls=0
    local tokens=0
    local found=false

    # grep for term
    calls=$((calls + 1))
    tokens=$((tokens + 200))
    local files
    files=$(grep -rl --include="*.py" "$term" "$CODEBASE_ROOT/src" 2>/dev/null | head -10)

    # Read files until we find the answer
    local position=0
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        position=$((position + 1))
        calls=$((calls + 1))

        local lines
        lines=$(wc -l < "$file" 2>/dev/null || echo "100")
        tokens=$((tokens + lines * 5))

        if [[ "$file" == *"$correct"* ]]; then
            found=true
            break
        fi
    done <<< "$files"

    echo "$calls $tokens $found $position"
}

# ============================================================
# aOa: Single ranked search (top result usually correct)
# ============================================================

simulate_aoa() {
    local q_id="$1"
    local correct="${CORRECT_FILES[$q_id]}"
    local term="${SEARCH_TERMS[$q_id]}"

    local calls=0
    local tokens=0
    local found=false
    local position=0

    # aOa symbol search - ONE call, ranked results
    calls=$((calls + 1))
    local result
    result=$(curl -s "$AOA_URL/symbol?q=$term" 2>/dev/null)

    # aOa returns compact JSON with ranked results
    tokens=$((tokens + 300))

    # Check position of correct file in results
    local rank=0
    for file in $(echo "$result" | jq -r '.results[].file' 2>/dev/null | head -5); do
        rank=$((rank + 1))
        if [[ "$file" == *"$correct"* ]]; then
            found=true
            position=$rank

            # Only need to read the correct file
            calls=$((calls + 1))
            local lines
            lines=$(wc -l < "$CODEBASE_ROOT/$file" 2>/dev/null || echo "100")
            tokens=$((tokens + lines * 5))
            break
        fi
    done

    # If not found in top 5, would need more calls
    if [[ "$found" != "true" ]]; then
        calls=$((calls + 3))
        tokens=$((tokens + 1500))
    fi

    echo "$calls $tokens $found $position"
}

# ============================================================
# BONUS: Show /predict capability
# ============================================================

demo_predict() {
    echo ""
    echo -e "${BOLD}BONUS: aOa Prediction Demo${NC}"
    echo -e "${DIM}After finding gateway.py, aOa predicts what you'll need next:${NC}"
    echo ""

    local predict
    predict=$(curl -s "$AOA_URL/predict?file=src/gateway/gateway.py" 2>/dev/null)

    echo "  Predicted next files (with confidence + snippets):"
    echo ""

    local i=0
    while IFS= read -r line; do
        i=$((i + 1))
        [[ $i -gt 3 ]] && break

        local path conf snippet
        path=$(echo "$line" | jq -r '.path' 2>/dev/null | sed 's|/home/corey/aOa/||')
        conf=$(echo "$line" | jq -r '.confidence' 2>/dev/null)
        snippet=$(echo "$line" | jq -r '.snippet' 2>/dev/null | head -3 | sed 's/^/      /')

        echo -e "  ${CYAN}$i. $path${NC} (${conf})"
        echo -e "${DIM}$snippet${NC}"
        echo ""
    done < <(echo "$predict" | jq -c '.files[]' 2>/dev/null)

    echo -e "${DIM}This is context you get FOR FREE with aOa - no extra tool calls!${NC}"
}

# ============================================================
# RUN BENCHMARK
# ============================================================

run_benchmark() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║          Knowledge-Seeking: Tool Calls to Find Answers                   ║"
    echo "╠══════════════════════════════════════════════════════════════════════════╣"
    echo "║  Traditional: grep → read wrong file → read wrong file → find it        ║"
    echo "║  aOa: symbol search → top result is correct → done                       ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo ""

    local total_trad_calls=0
    local total_aoa_calls=0
    local total_trad_tokens=0
    local total_aoa_tokens=0
    local trad_found=0
    local aoa_found=0
    local aoa_top1=0

    echo -e "${BOLD}Questions:${NC}"
    echo ""

    for q_id in 1 2 3 4 5; do
        echo -e "${BOLD}Q$q_id: ${QUESTIONS[$q_id]}${NC}"
        echo -e "  ${DIM}Answer: ${CORRECT_FILES[$q_id]}${NC}"

        # Traditional
        local trad
        trad=$(simulate_traditional "$q_id")
        local t_calls=$(echo "$trad" | cut -d' ' -f1)
        local t_tokens=$(echo "$trad" | cut -d' ' -f2)
        local t_found=$(echo "$trad" | cut -d' ' -f3)
        local t_pos=$(echo "$trad" | cut -d' ' -f4)

        total_trad_calls=$((total_trad_calls + t_calls))
        total_trad_tokens=$((total_trad_tokens + t_tokens))
        [[ "$t_found" == "true" ]] && trad_found=$((trad_found + 1))

        # aOa
        local aoa
        aoa=$(simulate_aoa "$q_id")
        local a_calls=$(echo "$aoa" | cut -d' ' -f1)
        local a_tokens=$(echo "$aoa" | cut -d' ' -f2)
        local a_found=$(echo "$aoa" | cut -d' ' -f3)
        local a_pos=$(echo "$aoa" | cut -d' ' -f4)

        total_aoa_calls=$((total_aoa_calls + a_calls))
        total_aoa_tokens=$((total_aoa_tokens + a_tokens))
        [[ "$a_found" == "true" ]] && aoa_found=$((aoa_found + 1))
        [[ "$a_pos" == "1" ]] && aoa_top1=$((aoa_top1 + 1))

        echo ""
        echo "  ┌─────────────────┬───────────┬──────────┬─────────────────┐"
        echo "  │ Method          │ Calls     │ Tokens   │ Found at pos    │"
        echo "  ├─────────────────┼───────────┼──────────┼─────────────────┤"
        printf "  │ grep→read       │ %7d   │ %7d  │ #%-14s │\n" "$t_calls" "$t_tokens" "$t_pos"
        printf "  │ aOa /symbol     │ %7d   │ %7d  │ #%-14s │\n" "$a_calls" "$a_tokens" "$a_pos"
        echo "  └─────────────────┴───────────┴──────────┴─────────────────┘"

        if [[ $a_calls -lt $t_calls ]]; then
            local savings=$((100 - (a_calls * 100 / t_calls)))
            echo -e "  ${GREEN}↓ ${savings}% fewer calls${NC}"
        fi
        echo ""
    done

    # Summary
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║                              RESULTS                                     ║"
    echo "╠══════════════════════════════════════════════════════════════════════════╣"
    echo "║                        │ grep→read        │ aOa              │ Savings   ║"
    echo "╠════════════════════════╪══════════════════╪══════════════════╪═══════════╣"

    local call_save=$((100 - (total_aoa_calls * 100 / (total_trad_calls + 1))))
    local token_save=$((100 - (total_aoa_tokens * 100 / (total_trad_tokens + 1))))

    printf "║  Tool calls            │ %14d   │ %14d   │ %6d%%   ║\n" "$total_trad_calls" "$total_aoa_calls" "$call_save"
    printf "║  Tokens consumed       │ %14d   │ %14d   │ %6d%%   ║\n" "$total_trad_tokens" "$total_aoa_tokens" "$token_save"
    printf "║  Questions answered    │ %14d/5 │ %14d/5 │           ║\n" "$trad_found" "$aoa_found"
    printf "║  Top-1 accuracy        │            N/A   │ %14d/5 │           ║\n" "$aoa_top1"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"

    # Show predict demo
    demo_predict

    echo ""
    echo -e "${BOLD}Key Insight:${NC}"
    echo -e "  aOa's value isn't raw speed - it's ${GREEN}finding answers in 1-2 calls${NC}"
    echo -e "  instead of the grep→read→grep→read cycle that burns context."
    echo ""

    # Save
    local results_dir="$SCRIPT_DIR/../results"
    mkdir -p "$results_dir"
    local today=$(date +%Y-%m-%d)

    cat > "$results_dir/${today}-knowledge-seeking.json" << EOF
{
    "benchmark": "knowledge-seeking-v2",
    "date": "$today",
    "traditional": { "calls": $total_trad_calls, "tokens": $total_trad_tokens, "found": $trad_found },
    "aoa": { "calls": $total_aoa_calls, "tokens": $total_aoa_tokens, "found": $aoa_found, "top1": $aoa_top1 },
    "savings": { "calls_pct": $call_save, "tokens_pct": $token_save }
}
EOF
    echo "Results: $results_dir/${today}-knowledge-seeking.json"
}

main() {
    if ! curl -s --max-time 2 "$AOA_URL/health" > /dev/null 2>&1; then
        echo -e "${RED}aOa not available${NC}"
        exit 1
    fi
    run_benchmark
}

main "$@"
