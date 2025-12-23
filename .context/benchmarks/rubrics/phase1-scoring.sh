#!/bin/bash
# phase1-scoring.sh - Phase 1 Redis Scoring Engine Rubrics
#
# These tests verify the scoring system works correctly.
# Before Phase 1 implementation: All tests FAIL (no /rank endpoint)
# After Phase 1 implementation: All tests PASS
#
# Usage: ./phase1-scoring.sh

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/../lib/assert.sh"

# Configuration
AOA_URL="${AOA_URL:-http://localhost:8080}"
# Default to docker exec since Redis runs in container
REDIS_CLI="${REDIS_CLI:-docker exec aoa-redis-1 redis-cli}"

# Test database (use DB 15 to avoid polluting production data)
TEST_DB=15

# Colors
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ============================================================
# SETUP / TEARDOWN
# ============================================================

setup() {
    # Switch to test database and clear it
    $REDIS_CLI SELECT $TEST_DB > /dev/null 2>&1
    $REDIS_CLI FLUSHDB > /dev/null 2>&1
}

teardown() {
    $REDIS_CLI SELECT $TEST_DB > /dev/null 2>&1
    $REDIS_CLI FLUSHDB > /dev/null 2>&1
}

# Check if services are available
preflight_check() {
    echo -e "${CYAN}Preflight Check${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    # Check Redis
    if ! $REDIS_CLI PING > /dev/null 2>&1; then
        echo -e "  Redis: ${RED}NOT AVAILABLE${NC}"
        echo ""
        echo "Start Redis with: docker-compose up -d redis"
        exit 1
    fi
    echo -e "  Redis: ${GREEN}OK${NC}"

    # Check aOa API (may not have /rank yet - that's expected)
    if curl -s --max-time 2 "$AOA_URL/health" > /dev/null 2>&1; then
        echo -e "  aOa API: ${GREEN}OK${NC}"
    else
        echo -e "  aOa API: ${YELLOW}NOT AVAILABLE${NC} (some tests will fail)"
    fi

    echo ""
}

# ============================================================
# RUBRIC 1: Recency Dominance
# A file accessed 1 second ago should rank higher than 1 hour ago
# ============================================================
test_recency_dominance() {
    local test_name="Recency Dominance"
    echo -e "${BOLD}TEST: $test_name${NC}"
    echo "  A recently accessed file should rank higher than an old one"

    setup

    local now
    now=$(date +%s)

    # Old access (1 hour ago)
    $REDIS_CLI SELECT $TEST_DB > /dev/null
    $REDIS_CLI ZADD "aoa:recency" $((now - 3600)) "/src/old_file.py" > /dev/null

    # Recent access (now)
    $REDIS_CLI ZADD "aoa:recency" "$now" "/src/recent_file.py" > /dev/null

    # Query the rank endpoint
    local result
    result=$(curl -s "$AOA_URL/rank?db=$TEST_DB&limit=2" 2>/dev/null) || {
        echo -e "  ${RED}FAIL${NC}: /rank endpoint not available"
        teardown
        return 1
    }

    local first
    first=$(echo "$result" | jq -r '.files[0]' 2>/dev/null)

    if assert_equals "/src/recent_file.py" "$first" "Recent file should rank first"; then
        echo -e "  ${GREEN}PASS${NC}"
        teardown
        return 0
    else
        teardown
        return 1
    fi
}

# ============================================================
# RUBRIC 2: Frequency Dominance
# A file accessed 10 times should rank higher than accessed once
# ============================================================
test_frequency_dominance() {
    local test_name="Frequency Dominance"
    echo -e "${BOLD}TEST: $test_name${NC}"
    echo "  A frequently accessed file should rank higher than a rare one"

    setup

    $REDIS_CLI SELECT $TEST_DB > /dev/null

    # Low frequency (1 access)
    $REDIS_CLI ZADD "aoa:frequency" 1 "/src/rare_file.py" > /dev/null

    # High frequency (10 accesses)
    $REDIS_CLI ZADD "aoa:frequency" 10 "/src/common_file.py" > /dev/null

    local result
    result=$(curl -s "$AOA_URL/rank?db=$TEST_DB&limit=2" 2>/dev/null) || {
        echo -e "  ${RED}FAIL${NC}: /rank endpoint not available"
        teardown
        return 1
    }

    local first
    first=$(echo "$result" | jq -r '.files[0]' 2>/dev/null)

    if assert_equals "/src/common_file.py" "$first" "Frequent file should rank first"; then
        echo -e "  ${GREEN}PASS${NC}"
        teardown
        return 0
    else
        teardown
        return 1
    fi
}

# ============================================================
# RUBRIC 3: Tag Affinity
# Querying for #api should return api-tagged files first
# ============================================================
test_tag_affinity() {
    local test_name="Tag Affinity"
    echo -e "${BOLD}TEST: $test_name${NC}"
    echo "  Files with matching tags should rank higher"

    setup

    $REDIS_CLI SELECT $TEST_DB > /dev/null

    # File associated with #api tag
    $REDIS_CLI ZADD "aoa:tag:api" 5 "/src/api/routes.py" > /dev/null

    # File associated with #testing tag (not #api)
    $REDIS_CLI ZADD "aoa:tag:testing" 5 "/tests/test_routes.py" > /dev/null

    # Also add both to frequency so they're in the pool
    $REDIS_CLI ZADD "aoa:frequency" 1 "/src/api/routes.py" > /dev/null
    $REDIS_CLI ZADD "aoa:frequency" 1 "/tests/test_routes.py" > /dev/null

    local result
    result=$(curl -s "$AOA_URL/rank?db=$TEST_DB&tag=api&limit=2" 2>/dev/null) || {
        echo -e "  ${RED}FAIL${NC}: /rank endpoint not available"
        teardown
        return 1
    }

    local first
    first=$(echo "$result" | jq -r '.files[0]' 2>/dev/null)

    if assert_equals "/src/api/routes.py" "$first" "API-tagged file should rank first when querying #api"; then
        echo -e "  ${GREEN}PASS${NC}"
        teardown
        return 0
    else
        teardown
        return 1
    fi
}

# ============================================================
# RUBRIC 4: Composite Scoring
# Combined recency + frequency + tag should produce expected order
# ============================================================
test_composite_scoring() {
    local test_name="Composite Scoring"
    echo -e "${BOLD}TEST: $test_name${NC}"
    echo "  All three signals should combine to produce correct ranking"

    setup

    local now
    now=$(date +%s)

    $REDIS_CLI SELECT $TEST_DB > /dev/null

    # File A: recent, low frequency, no tag
    $REDIS_CLI ZADD "aoa:recency" "$now" "/src/fileA.py" > /dev/null
    $REDIS_CLI ZADD "aoa:frequency" 1 "/src/fileA.py" > /dev/null

    # File B: old, high frequency, has tag
    $REDIS_CLI ZADD "aoa:recency" $((now - 3600)) "/src/fileB.py" > /dev/null
    $REDIS_CLI ZADD "aoa:frequency" 20 "/src/fileB.py" > /dev/null
    $REDIS_CLI ZADD "aoa:tag:api" 10 "/src/fileB.py" > /dev/null

    # File C: medium recency, medium frequency, has tag
    $REDIS_CLI ZADD "aoa:recency" $((now - 600)) "/src/fileC.py" > /dev/null
    $REDIS_CLI ZADD "aoa:frequency" 8 "/src/fileC.py" > /dev/null
    $REDIS_CLI ZADD "aoa:tag:api" 10 "/src/fileC.py" > /dev/null

    local result
    result=$(curl -s "$AOA_URL/rank?db=$TEST_DB&tag=api&limit=3" 2>/dev/null) || {
        echo -e "  ${RED}FAIL${NC}: /rank endpoint not available"
        teardown
        return 1
    }

    local first
    first=$(echo "$result" | jq -r '.files[0]' 2>/dev/null)

    # With #api tag query, B or C should be first (they have tag match + other signals)
    # A should NOT be first (no tag match)
    if assert_contains "$first" "fileB|fileC" "Composite scoring should favor tag-matched files"; then
        echo -e "  ${GREEN}PASS${NC}"
        teardown
        return 0
    else
        teardown
        return 1
    fi
}

# ============================================================
# RUBRIC 5: Cold Start
# Empty Redis should return empty results, not error
# ============================================================
test_cold_start() {
    local test_name="Cold Start"
    echo -e "${BOLD}TEST: $test_name${NC}"
    echo "  Empty database should return empty results gracefully"

    setup

    local result
    local http_code

    # Get both response and HTTP code
    http_code=$(curl -s -o /tmp/aoa_cold_start.json -w "%{http_code}" "$AOA_URL/rank?db=$TEST_DB&tag=api&limit=5" 2>/dev/null) || {
        echo -e "  ${RED}FAIL${NC}: /rank endpoint not available"
        teardown
        return 1
    }

    result=$(cat /tmp/aoa_cold_start.json 2>/dev/null)

    # Should not error
    if ! assert_equals "200" "$http_code" "API should return 200 on cold start"; then
        teardown
        return 1
    fi

    # Should return empty or zero-length files array
    local file_count
    file_count=$(echo "$result" | jq -r '.files | length' 2>/dev/null)

    if assert_equals "0" "$file_count" "Should return empty list on cold start"; then
        echo -e "  ${GREEN}PASS${NC}"
        teardown
        return 0
    else
        teardown
        return 1
    fi
}

# ============================================================
# RUBRIC 6: Latency
# /rank endpoint should respond in <50ms
# ============================================================
test_latency() {
    local test_name="Latency"
    echo -e "${BOLD}TEST: $test_name${NC}"
    echo "  /rank should respond in <50ms even with 1000 files"

    setup

    $REDIS_CLI SELECT $TEST_DB > /dev/null

    # Populate with 1000 files
    echo -n "  Populating 1000 files..."
    for i in $(seq 1 1000); do
        $REDIS_CLI ZADD "aoa:frequency" "$i" "/src/file$i.py" > /dev/null
    done
    echo " done"

    # Measure latency (average of 10 requests)
    local total_ms=0
    local runs=10

    for _ in $(seq 1 $runs); do
        local start end elapsed_ms
        start=$(date +%s%N)
        curl -s "$AOA_URL/rank?db=$TEST_DB&limit=10" > /dev/null 2>&1 || {
            echo -e "  ${RED}FAIL${NC}: /rank endpoint not available"
            teardown
            return 1
        }
        end=$(date +%s%N)
        elapsed_ms=$(( (end - start) / 1000000 ))
        total_ms=$((total_ms + elapsed_ms))
    done

    local avg_ms=$((total_ms / runs))
    echo "  Average latency: ${avg_ms}ms"

    if assert_lt "$avg_ms" 50 "Mean latency should be <50ms"; then
        echo -e "  ${GREEN}PASS${NC}"
        teardown
        return 0
    else
        teardown
        return 1
    fi
}

# ============================================================
# MAIN: Run All Tests
# ============================================================
main() {
    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║          aOa Phase 1 Benchmark: Redis Scoring Engine         ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    preflight_check

    local tests=(
        "test_recency_dominance"
        "test_frequency_dominance"
        "test_tag_affinity"
        "test_composite_scoring"
        "test_cold_start"
        "test_latency"
    )

    local passed=0
    local failed=0
    local results=()

    for test in "${tests[@]}"; do
        echo ""
        if $test; then
            passed=$((passed + 1))
            results+=("${GREEN}✓${NC} $test")
        else
            failed=$((failed + 1))
            results+=("${RED}✗${NC} $test")
        fi
    done

    echo ""
    echo "╔══════════════════════════════════════════════════════════════╗"
    echo "║                         RESULTS                              ║"
    echo "╚══════════════════════════════════════════════════════════════╝"
    echo ""

    for result in "${results[@]}"; do
        echo -e "  $result"
    done

    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "  Total: ${GREEN}$passed passed${NC}, ${RED}$failed failed${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""

    # Write results to file
    local results_dir="$SCRIPT_DIR/../results"
    local today
    today=$(date +%Y-%m-%d)
    local results_file="$results_dir/${today}-phase1.json"

    mkdir -p "$results_dir"

    cat > "$results_file" << EOF
{
    "phase": 1,
    "date": "$today",
    "timestamp": "$(date -Iseconds)",
    "rubrics": {
        "passed": $passed,
        "failed": $failed,
        "total": ${#tests[@]}
    },
    "tests": {
        "recency_dominance": $([ "$passed" -gt 0 ] && echo "true" || echo "false"),
        "frequency_dominance": $([ "$passed" -gt 1 ] && echo "true" || echo "false"),
        "tag_affinity": $([ "$passed" -gt 2 ] && echo "true" || echo "false"),
        "composite_scoring": $([ "$passed" -gt 3 ] && echo "true" || echo "false"),
        "cold_start": $([ "$passed" -gt 4 ] && echo "true" || echo "false"),
        "latency": $([ "$passed" -gt 5 ] && echo "true" || echo "false")
    }
}
EOF

    echo "Results saved to: $results_file"
    echo ""

    if [[ $failed -gt 0 ]]; then
        echo -e "${YELLOW}Phase 1 not yet complete. Implement /rank endpoint to pass tests.${NC}"
        exit 1
    fi

    echo -e "${GREEN}All Phase 1 rubrics passed!${NC}"
    exit 0
}

main "$@"
