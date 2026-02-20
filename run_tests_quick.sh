#!/bin/bash
# 快速运行测试并收集失败信息
cd /Users/fulingwei/.openclaw/workspace/non-standard-automation-pms

# 运行测试，只显示失败的
python3 -m pytest tests/unit/ -v --tb=no --maxfail=100 2>&1 | grep -E "(FAILED|ERROR)" | tee test_failures.txt

echo ""
echo "=== 失败测试统计 ==="
wc -l test_failures.txt
