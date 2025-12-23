#!/bin/bash
# assert.sh - Lightweight assertion library for aOa benchmarks
# Usage: source this file, then use assert_* functions

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Counters
ASSERT_PASSED=0
ASSERT_FAILED=0

# assert_equals "expected" "actual" "message"
assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="${3:-Values should be equal}"

    if [[ "$expected" == "$actual" ]]; then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        echo -e "  Expected: ${GREEN}$expected${NC}" >&2
        echo -e "  Actual:   ${RED}$actual${NC}" >&2
        return 1
    fi
}

# assert_not_equals "not_expected" "actual" "message"
assert_not_equals() {
    local not_expected="$1"
    local actual="$2"
    local message="${3:-Values should not be equal}"

    if [[ "$not_expected" != "$actual" ]]; then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        echo -e "  Should not be: ${RED}$not_expected${NC}" >&2
        return 1
    fi
}

# assert_contains "haystack" "needle" "message"
assert_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-String should contain pattern}"

    if echo "$haystack" | grep -qE "$needle"; then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        echo -e "  Looking for: ${GREEN}$needle${NC}" >&2
        echo -e "  In: ${RED}$haystack${NC}" >&2
        return 1
    fi
}

# assert_not_contains "haystack" "needle" "message"
assert_not_contains() {
    local haystack="$1"
    local needle="$2"
    local message="${3:-String should not contain pattern}"

    if ! echo "$haystack" | grep -qE "$needle"; then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        echo -e "  Should not contain: ${RED}$needle${NC}" >&2
        return 1
    fi
}

# assert_lt "actual" "max" "message" (actual < max)
assert_lt() {
    local actual="$1"
    local max="$2"
    local message="${3:-Value should be less than maximum}"

    if (( $(echo "$actual < $max" | bc -l) )); then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        echo -e "  Actual: ${RED}$actual${NC} >= Max: ${GREEN}$max${NC}" >&2
        return 1
    fi
}

# assert_gt "actual" "min" "message" (actual > min)
assert_gt() {
    local actual="$1"
    local min="$2"
    local message="${3:-Value should be greater than minimum}"

    if (( $(echo "$actual > $min" | bc -l) )); then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        echo -e "  Actual: ${RED}$actual${NC} <= Min: ${GREEN}$min${NC}" >&2
        return 1
    fi
}

# assert_gte "actual" "min" "message" (actual >= min)
assert_gte() {
    local actual="$1"
    local min="$2"
    local message="${3:-Value should be greater than or equal to minimum}"

    if (( $(echo "$actual >= $min" | bc -l) )); then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        echo -e "  Actual: ${RED}$actual${NC} < Min: ${GREEN}$min${NC}" >&2
        return 1
    fi
}

# assert_empty "value" "message"
assert_empty() {
    local value="$1"
    local message="${3:-Value should be empty}"

    if [[ -z "$value" ]]; then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        echo -e "  Got: ${RED}$value${NC}" >&2
        return 1
    fi
}

# assert_not_empty "value" "message"
assert_not_empty() {
    local value="$1"
    local message="${2:-Value should not be empty}"

    if [[ -n "$value" ]]; then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        return 1
    fi
}

# assert_http_ok "url" "message" - check HTTP 200
assert_http_ok() {
    local url="$1"
    local message="${2:-HTTP request should succeed}"

    local status
    status=$(curl -s -o /dev/null -w "%{http_code}" "$url" 2>/dev/null)

    if [[ "$status" == "200" ]]; then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        echo -e "  HTTP Status: ${RED}$status${NC} (expected 200)" >&2
        return 1
    fi
}

# assert_json_field "json" "field" "expected" "message"
assert_json_field() {
    local json="$1"
    local field="$2"
    local expected="$3"
    local message="${4:-JSON field should match expected value}"

    local actual
    actual=$(echo "$json" | jq -r "$field" 2>/dev/null)

    if [[ "$actual" == "$expected" ]]; then
        ((ASSERT_PASSED++))
        return 0
    else
        ((ASSERT_FAILED++))
        echo -e "${RED}ASSERTION FAILED${NC}: $message" >&2
        echo -e "  Field: $field" >&2
        echo -e "  Expected: ${GREEN}$expected${NC}" >&2
        echo -e "  Actual: ${RED}$actual${NC}" >&2
        return 1
    fi
}

# Print summary
assert_summary() {
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "Assertions: ${GREEN}$ASSERT_PASSED passed${NC}, ${RED}$ASSERT_FAILED failed${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"

    if [[ $ASSERT_FAILED -gt 0 ]]; then
        return 1
    fi
    return 0
}

# Reset counters (useful between test files)
assert_reset() {
    ASSERT_PASSED=0
    ASSERT_FAILED=0
}
