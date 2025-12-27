#!/bin/bash
# session-benchmark.sh - Generic Coding Session Benchmark
#
# Simulates 30 typical coding tasks across common patterns:
#   - Finding implementations
#   - Locating configs
#   - Understanding flows
#   - Debugging paths
#
# Designed to be comparable across tools - not self-testing.
# Uses langchain repo for realistic scale (2,600+ files).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/assert.sh"

AOA_URL="${AOA_URL:-http://localhost:8080}"
CODEBASE_ROOT="${CODEBASE_ROOT:-/home/corey/aOa/repos/langchain}"
REPO_NAME="${REPO_NAME:-langchain}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
DIM='\033[2m'
NC='\033[0m'

# ============================================================
# GENERIC CODING TASKS (30 total)
# These represent typical developer questions across ANY codebase
# ============================================================

declare -A TASKS
declare -A EXPECTED_PATTERNS  # Patterns that should appear in results
declare -A SEARCH_TERMS

# --- Category: Finding Implementations ---
TASKS[1]="Find the main entry point"
EXPECTED_PATTERNS[1]="main|__main__|entry|app"
SEARCH_TERMS[1]="main"

TASKS[2]="Find authentication logic"
EXPECTED_PATTERNS[2]="auth|login|token|credential"
SEARCH_TERMS[2]="auth"

TASKS[3]="Find API endpoint handlers"
EXPECTED_PATTERNS[3]="route|endpoint|handler|api"
SEARCH_TERMS[3]="handler"

TASKS[4]="Find database connection code"
EXPECTED_PATTERNS[4]="database|db|connection|pool"
SEARCH_TERMS[4]="database"

TASKS[5]="Find error handling"
EXPECTED_PATTERNS[5]="error|exception|catch|handle"
SEARCH_TERMS[5]="error"

# --- Category: Config & Setup ---
TASKS[6]="Find configuration loading"
EXPECTED_PATTERNS[6]="config|settings|env"
SEARCH_TERMS[6]="config"

TASKS[7]="Find environment variables"
EXPECTED_PATTERNS[7]="env|environ|getenv"
SEARCH_TERMS[7]="environ"

TASKS[8]="Find logging setup"
EXPECTED_PATTERNS[8]="log|logger|logging"
SEARCH_TERMS[8]="logger"

TASKS[9]="Find initialization code"
EXPECTED_PATTERNS[9]="init|setup|bootstrap"
SEARCH_TERMS[9]="init"

TASKS[10]="Find dependency injection"
EXPECTED_PATTERNS[10]="inject|provider|container"
SEARCH_TERMS[10]="provider"

# --- Category: Data Flow ---
TASKS[11]="Find data models"
EXPECTED_PATTERNS[11]="model|schema|entity"
SEARCH_TERMS[11]="model"

TASKS[12]="Find serialization code"
EXPECTED_PATTERNS[12]="serialize|json|parse"
SEARCH_TERMS[12]="serialize"

TASKS[13]="Find validation logic"
EXPECTED_PATTERNS[13]="valid|check|verify"
SEARCH_TERMS[13]="validate"

TASKS[14]="Find caching logic"
EXPECTED_PATTERNS[14]="cache|redis|memo"
SEARCH_TERMS[14]="cache"

TASKS[15]="Find queue/async handling"
EXPECTED_PATTERNS[15]="queue|async|worker|task"
SEARCH_TERMS[15]="async"

# --- Category: External Integrations ---
TASKS[16]="Find HTTP client code"
EXPECTED_PATTERNS[16]="http|request|fetch|client"
SEARCH_TERMS[16]="http"

TASKS[17]="Find webhook handlers"
EXPECTED_PATTERNS[17]="webhook|callback|hook"
SEARCH_TERMS[17]="callback"

TASKS[18]="Find file I/O operations"
EXPECTED_PATTERNS[18]="file|read|write|path"
SEARCH_TERMS[18]="file"

TASKS[19]="Find streaming logic"
EXPECTED_PATTERNS[19]="stream|chunk|buffer"
SEARCH_TERMS[19]="stream"

TASKS[20]="Find retry/backoff logic"
EXPECTED_PATTERNS[20]="retry|backoff|attempt"
SEARCH_TERMS[20]="retry"

# --- Category: Testing & Debug ---
TASKS[21]="Find test utilities"
EXPECTED_PATTERNS[21]="test|mock|fixture"
SEARCH_TERMS[21]="test"

TASKS[22]="Find debug helpers"
EXPECTED_PATTERNS[22]="debug|trace|inspect"
SEARCH_TERMS[22]="debug"

TASKS[23]="Find benchmark code"
EXPECTED_PATTERNS[23]="bench|perf|timing"
SEARCH_TERMS[23]="benchmark"

# --- Category: Core Utilities ---
TASKS[24]="Find string utilities"
EXPECTED_PATTERNS[24]="string|text|format"
SEARCH_TERMS[24]="string"

TASKS[25]="Find date/time handling"
EXPECTED_PATTERNS[25]="date|time|timestamp"
SEARCH_TERMS[25]="timestamp"

TASKS[26]="Find ID generation"
EXPECTED_PATTERNS[26]="id|uuid|generate"
SEARCH_TERMS[26]="uuid"

TASKS[27]="Find encryption/hashing"
EXPECTED_PATTERNS[27]="hash|encrypt|crypto"
SEARCH_TERMS[27]="hash"

TASKS[28]="Find rate limiting"
EXPECTED_PATTERNS[28]="rate|limit|throttle"
SEARCH_TERMS[28]="limit"

TASKS[29]="Find pagination logic"
EXPECTED_PATTERNS[29]="page|offset|cursor"
SEARCH_TERMS[29]="pagination"

TASKS[30]="Find middleware/interceptors"
EXPECTED_PATTERNS[30]="middleware|intercept|filter"
SEARCH_TERMS[30]="middleware"

# ============================================================
# BENCHMARK FUNCTIONS
# ============================================================

# Simulate grep→read workflow (traditional approach)
simulate_grep() {
    local term="$1"
    local pattern="$2"
    local calls=0
    local tokens=0
    local found=false

    # grep for term
    calls=$((calls + 1))
    tokens=$((tokens + 200))

    local files
    files=$(grep -rl --include="*.py" "$term" "$CODEBASE_ROOT/src" 2>/dev/null | head -10)

    # Read files until we find one matching expected pattern
    local position=0
    while IFS= read -r file; do
        [[ -z "$file" ]] && continue
        position=$((position + 1))
        calls=$((calls + 1))

        local lines
        lines=$(wc -l < "$file" 2>/dev/null || echo "100")
        tokens=$((tokens + lines * 5))

        # Check if file matches expected pattern
        if echo "$file" | grep -qiE "$pattern"; then
            found=true
            break
        fi

        # Also check file content for pattern
        if grep -qiE "$pattern" "$file" 2>/dev/null; then
            found=true
            break
        fi

        # Stop after 5 files
        [[ $position -ge 5 ]] && break
    done <<< "$files"

    echo "$calls $tokens $found $position"
}

# Use aOa symbol search (repo-specific for langchain)
simulate_aoa() {
    local term="$1"
    local pattern="$2"
    local calls=0
    local tokens=0
    local found=false
    local position=0

    # aOa search against the repo
    calls=$((calls + 1))
    local result
    result=$(curl -s "$AOA_URL/repo/$REPO_NAME/symbol?q=$term" 2>/dev/null)
    tokens=$((tokens + 300))

    # Check results
    local rank=0
    for file in $(echo "$result" | jq -r '.results[].file' 2>/dev/null | sort -u | head -5); do
        rank=$((rank + 1))

        # Check if file matches expected pattern
        if echo "$file" | grep -qiE "$pattern"; then
            found=true
            position=$rank
            calls=$((calls + 1))
            local lines
            lines=$(wc -l < "$CODEBASE_ROOT/$file" 2>/dev/null || echo "100")
            tokens=$((tokens + lines * 5))
            break
        fi
    done

    if [[ "$found" != "true" ]]; then
        calls=$((calls + 3))
        tokens=$((tokens + 1500))
    fi

    echo "$calls $tokens $found $position"
}

# ============================================================
# MAIN BENCHMARK
# ============================================================

run_benchmark() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║           Generic Coding Session Benchmark (30 Tasks)                    ║"
    echo "╠══════════════════════════════════════════════════════════════════════════╣"
    echo "║  Simulates typical developer questions across any codebase               ║"
    echo "║  Measures: Tool calls, tokens consumed, success rate                     ║"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"
    echo ""

    local total_grep_calls=0
    local total_aoa_calls=0
    local total_grep_tokens=0
    local total_aoa_tokens=0
    local grep_found=0
    local aoa_found=0
    local aoa_top3=0

    echo -e "${BOLD}Running 30 coding tasks...${NC}"
    echo ""

    for i in $(seq 1 30); do
        local task="${TASKS[$i]}"
        local pattern="${EXPECTED_PATTERNS[$i]}"
        local term="${SEARCH_TERMS[$i]}"

        printf "  [%2d/30] %-35s " "$i" "$task"

        # Run both approaches
        local grep_result aoa_result
        grep_result=$(simulate_grep "$term" "$pattern")
        aoa_result=$(simulate_aoa "$term" "$pattern")

        local g_calls=$(echo "$grep_result" | cut -d' ' -f1)
        local g_tokens=$(echo "$grep_result" | cut -d' ' -f2)
        local g_found=$(echo "$grep_result" | cut -d' ' -f3)

        local a_calls=$(echo "$aoa_result" | cut -d' ' -f1)
        local a_tokens=$(echo "$aoa_result" | cut -d' ' -f2)
        local a_found=$(echo "$aoa_result" | cut -d' ' -f3)
        local a_pos=$(echo "$aoa_result" | cut -d' ' -f4)

        total_grep_calls=$((total_grep_calls + g_calls))
        total_aoa_calls=$((total_aoa_calls + a_calls))
        total_grep_tokens=$((total_grep_tokens + g_tokens))
        total_aoa_tokens=$((total_aoa_tokens + a_tokens))

        [[ "$g_found" == "true" ]] && grep_found=$((grep_found + 1))
        [[ "$a_found" == "true" ]] && aoa_found=$((aoa_found + 1))
        [[ "$a_pos" -le 3 ]] 2>/dev/null && [[ "$a_pos" -gt 0 ]] && aoa_top3=$((aoa_top3 + 1))

        # Show result
        if [[ "$a_found" == "true" ]]; then
            echo -e "${GREEN}✓${NC} (aOa: ${a_calls} calls, grep: ${g_calls} calls)"
        else
            echo -e "${YELLOW}○${NC} (aOa: ${a_calls} calls, grep: ${g_calls} calls)"
        fi
    done

    # Summary
    echo ""
    echo "╔══════════════════════════════════════════════════════════════════════════╗"
    echo "║                              RESULTS                                     ║"
    echo "╠══════════════════════════════════════════════════════════════════════════╣"
    echo "║                        │ grep→read        │ aOa              │ Savings   ║"
    echo "╠════════════════════════╪══════════════════╪══════════════════╪═══════════╣"

    local call_save=$((100 - (total_aoa_calls * 100 / (total_grep_calls + 1))))
    local token_save=$((100 - (total_aoa_tokens * 100 / (total_grep_tokens + 1))))

    printf "║  Tool calls            │ %14d   │ %14d   │ %6d%%   ║\n" "$total_grep_calls" "$total_aoa_calls" "$call_save"
    printf "║  Tokens consumed       │ %14d   │ %14d   │ %6d%%   ║\n" "$total_grep_tokens" "$total_aoa_tokens" "$token_save"
    printf "║  Tasks completed       │ %14d/30 │ %14d/30 │           ║\n" "$grep_found" "$aoa_found"
    printf "║  Top-3 accuracy        │            N/A   │ %14d/30 │           ║\n" "$aoa_top3"
    echo "╚══════════════════════════════════════════════════════════════════════════╝"

    # Save results
    local results_dir="$SCRIPT_DIR/../results"
    mkdir -p "$results_dir"
    local today=$(date +%Y-%m-%d)

    cat > "$results_dir/${today}-session-benchmark.json" << EOF
{
    "benchmark": "session-benchmark-v1",
    "date": "$today",
    "tasks": 30,
    "traditional": { "calls": $total_grep_calls, "tokens": $total_grep_tokens, "found": $grep_found },
    "aoa": { "calls": $total_aoa_calls, "tokens": $total_aoa_tokens, "found": $aoa_found, "top3": $aoa_top3 },
    "savings": { "calls_pct": $call_save, "tokens_pct": $token_save }
}
EOF

    echo ""
    echo "Results: $results_dir/${today}-session-benchmark.json"
}

main() {
    if ! curl -s --max-time 2 "$AOA_URL/health" > /dev/null 2>&1; then
        echo -e "${RED}aOa not available${NC}"
        exit 1
    fi
    run_benchmark
}

main "$@"
