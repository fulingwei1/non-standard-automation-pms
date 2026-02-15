#!/bin/bash

echo "=========================================="
echo "Team 5 租户隔离测试 - 交付物验证"
echo "=========================================="
echo ""

# 检查文件是否存在
FILES=(
    "tests/fixtures/__init__.py"
    "tests/fixtures/tenant_fixtures.py"
    "tests/security/test_tenant_isolation.py"
    "tests/security/test_tenant_cud.py"
    "tests/security/test_multi_model_isolation.py"
    "tests/security/test_tenant_performance.py"
    "docs/租户隔离测试指南.md"
    "Agent_Team_5_租户隔离测试_交付报告.md"
)

echo "检查文件是否存在..."
echo ""

missing=0
for file in "${FILES[@]}"; do
    if [ -f "$file" ]; then
        size=$(wc -l < "$file" | tr -d ' ')
        echo "✅ $file ($size 行)"
    else
        echo "❌ $file - 缺失"
        missing=$((missing + 1))
    fi
done

echo ""
echo "=========================================="

# 统计代码行数
echo ""
echo "代码行数统计:"
echo ""
wc -l tests/fixtures/tenant_fixtures.py tests/security/test_tenant_*.py docs/租户隔离测试指南.md | tail -1

# 统计测试用例数量
echo ""
echo "测试用例统计:"
echo ""
echo "基础隔离测试:"
grep -c "def test_" tests/security/test_tenant_isolation.py
echo "CUD操作测试:"
grep -c "def test_" tests/security/test_tenant_cud.py
echo "多模型测试:"
grep -c "def test_" tests/security/test_multi_model_isolation.py
echo "性能测试:"
grep -c "def test_" tests/security/test_tenant_performance.py
echo ""
total=$(grep -h "def test_" tests/security/test_tenant_*.py | wc -l | tr -d ' ')
echo "总计: $total 个测试用例"

echo ""
echo "=========================================="

if [ $missing -eq 0 ]; then
    echo "✅ 所有交付物验证通过！"
    exit 0
else
    echo "❌ 有 $missing 个文件缺失"
    exit 1
fi
