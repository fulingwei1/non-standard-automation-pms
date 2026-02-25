#!/bin/bash
# Run tests in batches and combine coverage
cd /Users/fulingwei/.openclaw/workspace/non-standard-automation-pms
export SECRET_KEY="test-secret-key-for-ci-with-32-chars-minimum!"
export DATABASE_URL="sqlite:///:memory:"
export REDIS_URL=""

# Clean old coverage data
python3 -m coverage erase

# Get list of test files (exclude broken ones)
find tests/unit -maxdepth 1 -name "test_*.py" | sort > /tmp/test_files.txt
TOTAL=$(wc -l < /tmp/test_files.txt)
echo "Total test files: $TOTAL"

PASSED=0
FAILED=0
ERRORS=0
BATCH_SIZE=10
BATCH=0

while IFS= read -r file; do
    BATCH=$((BATCH + 1))
    
    # Run with coverage append
    python3 -m coverage run --append --source=app -m pytest "$file" -o "addopts=" -q --tb=no --no-header --no-cov -x 2>/dev/null
    RC=$?
    
    if [ $RC -eq 0 ]; then
        PASSED=$((PASSED + 1))
    elif [ $RC -eq 1 ]; then
        FAILED=$((FAILED + 1))
    else
        ERRORS=$((ERRORS + 1))
    fi
    
    if [ $((BATCH % 50)) -eq 0 ]; then
        echo "Progress: $BATCH/$TOTAL (passed=$PASSED, failed=$FAILED, errors=$ERRORS)"
    fi
done < /tmp/test_files.txt

echo ""
echo "=== DONE ==="
echo "Total: $TOTAL, Passed: $PASSED, Failed: $FAILED, Errors: $ERRORS"
echo ""

# Also run subdirectory tests
for dir in tests/unit/core tests/unit/schemas; do
    if [ -d "$dir" ]; then
        echo "Running $dir..."
        python3 -m coverage run --append --source=app -m pytest "$dir" -o "addopts=" -q --tb=no --no-header --no-cov --ignore=tests/unit/models --ignore=tests/unit/test_alert_rule_engine 2>/dev/null
    fi
done

# Generate report
echo ""
echo "=== Coverage Report ==="
python3 -m coverage report --sort=cover | head -60
python3 -m coverage html
python3 -m coverage report --sort=cover > /tmp/coverage_report.txt
echo "Full report saved to /tmp/coverage_report.txt"
