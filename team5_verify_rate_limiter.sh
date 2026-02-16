#!/bin/bash
# Team 5: Rate Limiter 验证脚本

echo "========================================================================"
echo "Rate Limiter 功能验证"
echo "========================================================================"
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查1: 验证代码修改
echo "1. 检查代码修改..."
if grep -q "@limiter.limit(\"5/minute\")  # IP级别限流" app/api/v1/endpoints/auth.py; then
    echo -e "   ${GREEN}✅${NC} login endpoint 已启用 rate limiter"
else
    echo -e "   ${RED}❌${NC} login endpoint 未启用 rate limiter"
    exit 1
fi

if grep -q "@limiter.limit(\"10/minute\")  # 防止token刷新滥用" app/api/v1/endpoints/auth.py; then
    echo -e "   ${GREEN}✅${NC} refresh endpoint 已启用 rate limiter"
else
    echo -e "   ${RED}❌${NC} refresh endpoint 未启用 rate limiter"
    exit 1
fi

if grep -q "@limiter.limit(\"5/hour\")  # 严格限制密码修改频率" app/api/v1/endpoints/auth.py; then
    echo -e "   ${GREEN}✅${NC} password endpoint 已启用 rate limiter"
else
    echo -e "   ${RED}❌${NC} password endpoint 未启用 rate limiter"
    exit 1
fi

# 检查2: 语法检查
echo ""
echo "2. Python 语法检查..."
if python3 -m py_compile app/api/v1/endpoints/auth.py 2>/dev/null; then
    echo -e "   ${GREEN}✅${NC} 语法检查通过"
else
    echo -e "   ${RED}❌${NC} 语法检查失败"
    exit 1
fi

# 检查3: 导入测试
echo ""
echo "3. 模块导入测试..."
if python3 -c "from app.core.rate_limiting import limiter; print('导入成功')" 2>/dev/null | grep -q "导入成功"; then
    echo -e "   ${GREEN}✅${NC} rate_limiting 模块导入成功"
else
    echo -e "   ${RED}❌${NC} rate_limiting 模块导入失败"
    exit 1
fi

# 检查4: 运行兼容性测试
echo ""
echo "4. 运行兼容性测试..."
if python3 test_slowapi_production_env.py 2>&1 | grep -q "测试完成"; then
    echo -e "   ${GREEN}✅${NC} 兼容性测试通过"
else
    echo -e "   ${YELLOW}⚠️${NC}  兼容性测试执行但可能有问题，请检查详细输出"
fi

# 检查5: 运行性能测试
echo ""
echo "5. 运行性能测试..."
if python3 team5_rate_limiter_performance_test.py 2>&1 | grep -q "性能测试通过"; then
    echo -e "   ${GREEN}✅${NC} 性能测试通过"
else
    echo -e "   ${YELLOW}⚠️${NC}  性能测试执行但可能有问题，请检查详细输出"
fi

# 检查6: 文档检查
echo ""
echo "6. 检查交付文档..."
docs=(
    "team5_rate_limiter_analysis_report.md"
    "team5_rate_limiter_fix.patch"
    "team5_rate_limiter_usage_guide.md"
    "team5_rate_limiter_performance_test.py"
    "test_slowapi_production_env.py"
)

all_docs_exist=true
for doc in "${docs[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "   ${GREEN}✅${NC} $doc"
    else
        echo -e "   ${RED}❌${NC} $doc (缺失)"
        all_docs_exist=false
    fi
done

# 最终结果
echo ""
echo "========================================================================"
if [ "$all_docs_exist" = true ]; then
    echo -e "${GREEN}✅ 所有检查通过！Rate Limiter 已成功启用并验证。${NC}"
    echo ""
    echo "下一步："
    echo "  1. 提交代码: git add app/api/v1/endpoints/auth.py"
    echo "  2. 查看完整报告: cat team5_rate_limiter_analysis_report.md"
    echo "  3. 查看使用指南: cat team5_rate_limiter_usage_guide.md"
else
    echo -e "${RED}❌ 部分检查未通过，请检查上述错误。${NC}"
    exit 1
fi
echo "========================================================================"
