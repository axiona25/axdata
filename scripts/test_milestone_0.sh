#!/bin/bash
# Test script for Milestone 0 - Bootstrap & Infrastruttura

set -e

echo "🧪 Testing Milestone 0: Bootstrap & Infrastruttura"
echo "=================================================="

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Test counters
TESTS_PASSED=0
TESTS_FAILED=0

# Function to run test
run_test() {
    local test_name=$1
    local test_command=$2
    
    echo -n "Testing: $test_name... "
    if eval "$test_command" > /dev/null 2>&1; then
        echo -e "${GREEN}✓ PASSED${NC}"
        ((TESTS_PASSED++))
        return 0
    else
        echo -e "${RED}✗ FAILED${NC}"
        ((TESTS_FAILED++))
        return 1
    fi
}

# 1. Check Docker services are running
echo ""
echo "1. Checking Docker services..."
run_test "PostgreSQL container running" "docker ps | grep dataset_portal_postgres | grep Up"
run_test "Redis container running" "docker ps | grep dataset_portal_redis | grep Up"
run_test "MinIO container running" "docker ps | grep dataset_portal_minio | grep Up"

# 2. Check PostgreSQL connection
echo ""
echo "2. Testing PostgreSQL connection..."
run_test "PostgreSQL accessible" "docker exec dataset_portal_postgres pg_isready -U dataset_user"

# 3. Check Redis connection
echo ""
echo "3. Testing Redis connection..."
run_test "Redis accessible" "docker exec dataset_portal_redis redis-cli ping | grep PONG"

# 4. Check MinIO connection
echo ""
echo "4. Testing MinIO connection..."
run_test "MinIO API accessible" "curl -s -o /dev/null -w '%{http_code}' http://localhost:9000/minio/health/live | grep -q 200"

# 5. Check Backend health endpoints
echo ""
echo "5. Testing Backend health endpoints..."
run_test "Backend /health endpoint" "curl -s http://localhost:8000/health | grep -q 'healthy'"
run_test "Backend /api/v1/health endpoint" "curl -s http://localhost:8000/api/v1/health | grep -q 'healthy'"

# 6. Check Collector health endpoint
echo ""
echo "6. Testing Collector health endpoint..."
run_test "Collector /health endpoint" "curl -s http://localhost:8001/health | grep -q 'healthy'"

# 7. Check Python dependencies
echo ""
echo "7. Checking Python dependencies..."
if [ -d "apps/backend" ]; then
    run_test "Backend requirements.txt exists" "test -f apps/backend/requirements.txt"
fi
if [ -d "apps/collector" ]; then
    run_test "Collector requirements.txt exists" "test -f apps/collector/requirements.txt"
fi

# 8. Check configuration files
echo ""
echo "8. Checking configuration files..."
run_test "Backend .env exists" "test -f apps/backend/.env"
run_test "Collector .env exists" "test -f apps/collector/.env"
run_test "Docker Compose exists" "test -f infra/docker-compose.yml"

# Summary
echo ""
echo "=================================================="
echo "Test Summary:"
echo -e "${GREEN}Passed: $TESTS_PASSED${NC}"
if [ $TESTS_FAILED -gt 0 ]; then
    echo -e "${RED}Failed: $TESTS_FAILED${NC}"
    exit 1
else
    echo -e "${GREEN}All tests passed!${NC}"
    exit 0
fi

