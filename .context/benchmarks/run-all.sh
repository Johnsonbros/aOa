#!/bin/bash
# run-all.sh - Master benchmark runner for aOa
#
# Usage:
#   ./run-all.sh              # Run all phases
#   ./run-all.sh phase1       # Run Phase 1 only
#   ./run-all.sh phase1 phase2  # Run specific phases
#   ./run-all.sh --ir-metrics # Run IR metrics evaluation
#
# Environment Variables:
#   AOA_URL       - aOa API URL (default: http://localhost:8080)
#   REDIS_CLI     - Redis CLI command (default: redis-cli)

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# Configuration
AOA_URL="${AOA_URL:-http://localhost:8080}"
# Default to docker exec since Redis runs in container
REDIS_CLI="${REDIS_CLI:-docker exec aoa-redis-1 redis-cli}"

export AOA_URL REDIS_CLI

# ============================================================
# UTILITY FUNCTIONS
# ============================================================

print_header() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                    aOa Benchmark Suite                       ║"
    echo "║                                                              ║"
    echo "║  Measuring the benefit of predictive file ranking            ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "  ${CYAN}API:${NC}   $AOA_URL"
    echo -e "  ${CYAN}Redis:${NC} $REDIS_CLI"
    echo -e "  ${CYAN}Date:${NC}  $(date '+%Y-%m-%d %H:%M:%S')"
    echo ""
}

check_dependencies() {
    local missing=()

    command -v curl >/dev/null 2>&1 || missing+=("curl")
    command -v jq >/dev/null 2>&1 || missing+=("jq")
    command -v bc >/dev/null 2>&1 || missing+=("bc")

    if [[ ${#missing[@]} -gt 0 ]]; then
        echo -e "${RED}Missing dependencies:${NC} ${missing[*]}"
        echo "Install with: sudo apt-get install ${missing[*]}"
        exit 1
    fi
}

run_phase() {
    local phase="$1"
    local script="$SCRIPT_DIR/rubrics/${phase}-scoring.sh"

    if [[ ! -f "$script" ]]; then
        echo -e "${YELLOW}Skipping ${phase}:${NC} No rubric file found"
        return 0
    fi

    echo -e "${BOLD}Running $phase rubrics...${NC}"
    echo ""

    chmod +x "$script"
    if "$script"; then
        return 0
    else
        return 1
    fi
}

run_ir_metrics() {
    local metrics_script="$SCRIPT_DIR/metrics/ir-metrics.py"
    local fixtures="$SCRIPT_DIR/fixtures/synthetic-sessions.jsonl"

    if [[ ! -f "$metrics_script" ]]; then
        echo -e "${YELLOW}Skipping IR metrics:${NC} Script not found"
        return 0
    fi

    if [[ ! -f "$fixtures" ]]; then
        echo -e "${YELLOW}Skipping IR metrics:${NC} No fixtures found"
        return 0
    fi

    echo -e "${BOLD}Running IR Metrics Evaluation...${NC}"
    echo ""

    python3 "$metrics_script" --fixtures "$fixtures" --url "$AOA_URL"
}

print_summary() {
    local passed=$1
    local failed=$2

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                      FINAL SUMMARY                           ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""
    echo -e "  Phases passed: ${GREEN}$passed${NC}"
    echo -e "  Phases failed: ${RED}$failed${NC}"
    echo ""

    if [[ $failed -gt 0 ]]; then
        echo -e "${YELLOW}Some benchmarks failed. This is expected before implementation.${NC}"
        echo ""
        echo "Next steps:"
        echo "  1. Implement the /rank endpoint in aOa"
        echo "  2. Re-run: ./run-all.sh"
        echo "  3. Watch the tests go green!"
        exit 1
    else
        echo -e "${GREEN}All benchmarks passed!${NC}"
        exit 0
    fi
}

# ============================================================
# MAIN
# ============================================================

main() {
    print_header
    check_dependencies

    local phases=()
    local run_metrics=false

    # Parse arguments
    if [[ $# -eq 0 ]]; then
        # Default: run all phases
        phases=("phase1")  # Add more as we create them
    else
        for arg in "$@"; do
            case "$arg" in
                --ir-metrics)
                    run_metrics=true
                    ;;
                phase*)
                    phases+=("$arg")
                    ;;
                *)
                    echo -e "${RED}Unknown argument:${NC} $arg"
                    echo "Usage: $0 [phase1] [phase2] [--ir-metrics]"
                    exit 1
                    ;;
            esac
        done
    fi

    local passed=0
    local failed=0

    # Run phase rubrics
    for phase in "${phases[@]}"; do
        if run_phase "$phase"; then
            passed=$((passed + 1))
        else
            failed=$((failed + 1))
        fi
    done

    # Run IR metrics if requested
    if [[ "$run_metrics" == true ]]; then
        run_ir_metrics
    fi

    print_summary $passed $failed
}

main "$@"
