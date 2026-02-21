#!/bin/bash

echo "=========================================="
echo "审批引擎核心类测试验证"
echo "=========================================="
echo ""

echo "1. 运行测试..."
python3 -m pytest tests/unit/test_core_engine_rewrite.py -v --tb=no

echo ""
echo "2. 生成覆盖率报告..."
python3 -m coverage erase
python3 -m coverage run -m pytest tests/unit/test_core_engine_rewrite.py -q
python3 -m coverage json

echo ""
echo "3. 提取覆盖率数据..."
python3 -c "
import json
with open('coverage.json') as f:
    data = json.load(f)
    info = data['files']['app/services/approval_engine/engine/core.py']
    print('=' * 50)
    print('覆盖率报告')
    print('=' * 50)
    print(f'文件: app/services/approval_engine/engine/core.py')
    print(f'覆盖率: {info[\"summary\"][\"percent_covered\"]:.1f}%')
    print(f'总行数: {info[\"summary\"][\"num_statements\"]}')
    print(f'已覆盖: {info[\"summary\"][\"covered_lines\"]}')
    print(f'未覆盖: {info[\"summary\"][\"missing_lines\"]}')
    print(f'分支总数: {info[\"summary\"][\"num_branches\"]}')
    print(f'分支覆盖: {info[\"summary\"][\"covered_branches\"]}')
    print('=' * 50)
    
    coverage_pct = info['summary']['percent_covered']
    if coverage_pct >= 70:
        print(f'✅ 成功！覆盖率 {coverage_pct:.1f}% >= 70%')
    else:
        print(f'❌ 失败！覆盖率 {coverage_pct:.1f}% < 70%')
"

echo ""
echo "4. 详细覆盖率报告..."
python3 -m coverage report --include="app/services/approval_engine/engine/core.py"

