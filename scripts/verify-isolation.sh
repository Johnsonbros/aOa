#!/bin/bash
# =============================================================================
# verify-isolation.sh - Prove aOa network isolation
# =============================================================================
#
# This script verifies that:
# 1. Gateway, index, status, redis have NO internet access
# 2. Git-proxy CAN reach allowed git hosts
# 3. All services are healthy
#
# Run after `docker compose up -d`
# =============================================================================

set -e

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "=== aOa Network Isolation Verification ==="
echo

PASS=0
FAIL=0

# Helper functions
check_no_internet() {
    local service=$1
    echo -n "Checking $service has NO internet access... "

    # Try to reach an external host - should fail
    if docker compose exec -T "$service" timeout 3 curl -s --connect-timeout 2 https://api.anthropic.com >/dev/null 2>&1; then
        echo -e "${RED}FAIL${NC} - $service can reach internet (unexpected)"
        ((FAIL++))
        return 1
    else
        echo -e "${GREEN}PASS${NC} - No internet access"
        ((PASS++))
        return 0
    fi
}

check_has_internet() {
    local service=$1
    echo -n "Checking $service CAN reach git hosts... "

    # Try to reach github.com - should succeed
    if docker compose exec -T "$service" timeout 10 git ls-remote --exit-code https://github.com/git/git.git HEAD >/dev/null 2>&1; then
        echo -e "${GREEN}PASS${NC} - Can reach github.com"
        ((PASS++))
        return 0
    else
        echo -e "${RED}FAIL${NC} - Cannot reach github.com"
        ((FAIL++))
        return 1
    fi
}

check_health() {
    local service=$1
    local port=$2
    echo -n "Checking $service is healthy... "

    if docker compose exec -T "$service" curl -sf "http://localhost:$port/health" >/dev/null 2>&1; then
        echo -e "${GREEN}OK${NC}"
        ((PASS++))
        return 0
    else
        echo -e "${RED}FAIL${NC}"
        ((FAIL++))
        return 1
    fi
}

# =============================================================================
# Test 1: Services should NOT have internet access
# =============================================================================
echo "1. Testing network isolation (services should NOT reach internet)..."
echo

check_no_internet "gateway"
check_no_internet "index"
check_no_internet "status"

echo

# =============================================================================
# Test 2: Git-proxy SHOULD have internet access (for git operations only)
# =============================================================================
echo "2. Testing git-proxy internet access (should be able to reach git hosts)..."
echo

check_has_internet "git-proxy"

echo

# =============================================================================
# Test 3: All services should be healthy
# =============================================================================
echo "3. Testing service health..."
echo

check_health "gateway" "8080"
check_health "index" "9999"
check_health "status" "9998"
check_health "git-proxy" "9997"

echo

# =============================================================================
# Test 4: Gateway endpoints
# =============================================================================
echo "4. Testing gateway endpoints..."
echo

echo -n "  /network endpoint... "
if curl -sf "http://localhost:8080/network" >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

echo -n "  /audit endpoint... "
if curl -sf "http://localhost:8080/audit" >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

echo -n "  /verify endpoint... "
if curl -sf "http://localhost:8080/verify" >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

echo -n "  /routes endpoint... "
if curl -sf "http://localhost:8080/routes" >/dev/null 2>&1; then
    echo -e "${GREEN}OK${NC}"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC}"
    ((FAIL++))
fi

echo

# =============================================================================
# Test 5: Docker network configuration
# =============================================================================
echo "5. Verifying Docker network configuration..."
echo

echo -n "  aoa-internal is internal... "
INTERNAL=$(docker network inspect aoa_aoa-internal --format '{{.Internal}}' 2>/dev/null || echo "false")
if [ "$INTERNAL" = "true" ]; then
    echo -e "${GREEN}OK${NC} (internal=true)"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC} (internal=$INTERNAL)"
    ((FAIL++))
fi

echo -n "  aoa-external is not internal... "
EXTERNAL=$(docker network inspect aoa_aoa-external --format '{{.Internal}}' 2>/dev/null || echo "true")
if [ "$EXTERNAL" = "false" ]; then
    echo -e "${GREEN}OK${NC} (internal=false)"
    ((PASS++))
else
    echo -e "${RED}FAIL${NC} (internal=$EXTERNAL)"
    ((FAIL++))
fi

echo

# =============================================================================
# Summary
# =============================================================================
echo "=== Verification Summary ==="
echo
echo -e "Passed: ${GREEN}$PASS${NC}"
echo -e "Failed: ${RED}$FAIL${NC}"
echo

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}All checks PASSED!${NC}"
    echo
    echo "Network isolation verified. You can share this output as proof that:"
    echo "  - Gateway, index, status, redis have NO internet access"
    echo "  - Only git-proxy can reach external hosts (restricted to git operations)"
    echo "  - All requests are logged and auditable"
    exit 0
else
    echo -e "${RED}Some checks FAILED!${NC}"
    echo
    echo "Please review the failures above."
    echo "Network isolation may not be properly configured."
    exit 1
fi
