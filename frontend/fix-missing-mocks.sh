#!/bin/bash
# Find all test files with missing mock methods

cd /Users/fulingwei/.openclaw/workspace/non-standard-automation-pms/frontend

echo "=== Finding missing mock methods ==="
echo

# Run tests and capture errors
npm test 2>&1 | grep -B 3 "Cannot read properties of undefined (reading 'mockResolvedValue')" | \
grep "❯" | \
sed 's/.*❯ //' | \
sort -u

echo
echo "=== Files with errors ==="
npm test 2>&1 | grep "Cannot read properties of undefined" | \
grep -o "src/pages/__tests__/[^:]*" | \
sort -u
