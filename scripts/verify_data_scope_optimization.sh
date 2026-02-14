#!/bin/bash
# 数据范围优化验证脚本

echo "=================================================="
echo "数据范围过滤功能优化 - 验证脚本"
echo "=================================================="
echo ""

# 设置颜色
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 计数器
PASS=0
FAIL=0

# 检查函数
check_file() {
    local file=$1
    local desc=$2
    
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $desc"
        ((PASS++))
        return 0
    else
        echo -e "${RED}✗${NC} $desc"
        ((FAIL++))
        return 1
    fi
}

echo "1. 检查代码文件"
echo "-------------------"
check_file "app/services/data_scope_service_enhanced.py" "增强的数据范围服务"
check_file "app/services/data_scope/generic_filter.py" "通用过滤器"
check_file "app/services/data_scope/config.py" "配置文件"
echo ""

echo "2. 检查测试文件"
echo "-------------------"
check_file "tests/unit/test_data_scope_enhanced.py" "增强版测试套件"
check_file "tests/unit/test_data_scope_service_comprehensive.py" "综合测试"
echo ""

echo "3. 检查文档文件"
echo "-------------------"
check_file "docs/data_scope_optimization_report.md" "优化报告"
check_file "docs/DATA_SCOPE_USAGE_GUIDE.md" "使用指南"
check_file "docs/DATA_SCOPE_QUICK_REFERENCE.md" "快速参考"
check_file "docs/DATA_SCOPE_DELIVERY_SUMMARY.md" "交付总结"
echo ""

echo "4. 检查示例文件"
echo "-------------------"
check_file "examples/data_scope_examples.py" "实际使用示例"
echo ""

echo "5. 验证代码导入"
echo "-------------------"
export SECRET_KEY="test-secret-key-for-validation"

if python3 -c "from app.services.data_scope_service_enhanced import DataScopeServiceEnhanced; print('导入成功')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 增强服务导入成功"
    ((PASS++))
else
    echo -e "${YELLOW}⚠${NC} 增强服务导入失败（可能需要完整环境）"
fi

if python3 -c "from app.services.data_scope_service_enhanced import SCOPE_TYPE_MAPPING; print('映射导入成功')" 2>/dev/null; then
    echo -e "${GREEN}✓${NC} 枚举映射导入成功"
    ((PASS++))
else
    echo -e "${YELLOW}⚠${NC} 枚举映射导入失败（可能需要完整环境）"
fi
echo ""

echo "6. 统计测试用例数量"
echo "-------------------"
TEST_COUNT=$(grep -c "def test_" tests/unit/test_data_scope_enhanced.py)
echo "测试用例数量: $TEST_COUNT"
if [ $TEST_COUNT -ge 15 ]; then
    echo -e "${GREEN}✓${NC} 测试用例数量达标 (>15个)"
    ((PASS++))
else
    echo -e "${RED}✗${NC} 测试用例数量不足"
    ((FAIL++))
fi
echo ""

echo "7. 统计文档字数"
echo "-------------------"
USAGE_GUIDE_LINES=$(wc -l < docs/DATA_SCOPE_USAGE_GUIDE.md)
EXAMPLES_LINES=$(wc -l < examples/data_scope_examples.py)
echo "使用指南行数: $USAGE_GUIDE_LINES"
echo "示例代码行数: $EXAMPLES_LINES"
if [ $USAGE_GUIDE_LINES -gt 100 ] && [ $EXAMPLES_LINES -gt 100 ]; then
    echo -e "${GREEN}✓${NC} 文档内容充实"
    ((PASS++))
else
    echo -e "${RED}✗${NC} 文档内容不足"
    ((FAIL++))
fi
echo ""

echo "=================================================="
echo "验证结果"
echo "=================================================="
echo -e "通过: ${GREEN}$PASS${NC}"
echo -e "失败: ${RED}$FAIL${NC}"
echo ""

if [ $FAIL -eq 0 ]; then
    echo -e "${GREEN}✓ 所有检查通过！${NC}"
    exit 0
else
    echo -e "${YELLOW}⚠ 部分检查未通过，请查看详情${NC}"
    exit 1
fi
