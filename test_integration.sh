#!/bin/bash

# 绩效管理系统 - 集成验证脚本
# 用于快速验证前后端集成是否正常

echo "=========================================="
echo "  绩效管理系统 - 集成验证"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 测试计数
TOTAL_TESTS=0
PASSED_TESTS=0
FAILED_TESTS=0

# 测试函数
test_endpoint() {
    local name=$1
    local url=$2
    local expected_code=$3

    TOTAL_TESTS=$((TOTAL_TESTS + 1))

    echo -n "测试 $TOTAL_TESTS: $name ... "

    response_code=$(curl -s -o /dev/null -w "%{http_code}" "$url")

    if [ "$response_code" -eq "$expected_code" ]; then
        echo -e "${GREEN}✓ 通过${NC} (HTTP $response_code)"
        PASSED_TESTS=$((PASSED_TESTS + 1))
    else
        echo -e "${RED}✗ 失败${NC} (期望 $expected_code, 实际 $response_code)"
        FAILED_TESTS=$((FAILED_TESTS + 1))
    fi
}

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第一部分: 后端服务检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查后端是否运行
echo -n "检查后端服务状态 ... "
if lsof -ti:8000 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 运行中${NC}"
    BACKEND_RUNNING=1
else
    echo -e "${RED}✗ 未运行${NC}"
    echo ""
    echo -e "${YELLOW}提示: 请先启动后端服务${NC}"
    echo "命令: python3 -m app.main"
    BACKEND_RUNNING=0
fi

echo ""

# 如果后端运行,测试API端点
if [ $BACKEND_RUNNING -eq 1 ]; then
    echo "测试后端API端点:"
    echo ""

    # 测试健康检查
    test_endpoint "健康检查" "http://localhost:8000/health" 200

    # 测试API文档
    test_endpoint "API文档" "http://localhost:8000/docs" 200

    # 测试性能管理API (需要认证,预期401)
    test_endpoint "获取权重配置(未认证)" "http://localhost:8000/api/v1/performance/weight-config" 401

    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第二部分: 前端服务检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查前端是否运行
echo -n "检查前端服务状态 ... "
if lsof -ti:5173 > /dev/null 2>&1; then
    echo -e "${GREEN}✓ 运行中${NC}"
    FRONTEND_RUNNING=1
else
    echo -e "${RED}✗ 未运行${NC}"
    echo ""
    echo -e "${YELLOW}提示: 请先启动前端服务${NC}"
    echo "命令: cd frontend && npm run dev"
    FRONTEND_RUNNING=0
fi

echo ""

# 如果前端运行,测试页面
if [ $FRONTEND_RUNNING -eq 1 ]; then
    echo "测试前端页面:"
    echo ""

    # 测试主页
    test_endpoint "前端主页" "http://localhost:5173" 200

    echo ""
fi

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第三部分: 数据库检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# 检查数据库文件
echo -n "检查SQLite数据库 ... "
if [ -f "data/app.db" ]; then
    echo -e "${GREEN}✓ 存在${NC}"

    # 检查表是否存在
    echo ""
    echo "检查绩效管理相关表:"

    tables=(
        "monthly_work_summary"
        "performance_evaluation_record"
        "performance_final_score"
        "performance_weight_config"
    )

    for table in "${tables[@]}"; do
        echo -n "  - $table ... "
        if sqlite3 data/app.db "SELECT name FROM sqlite_master WHERE type='table' AND name='$table';" | grep -q "$table"; then
            echo -e "${GREEN}✓ 存在${NC}"
        else
            echo -e "${RED}✗ 不存在${NC}"
        fi
    done
else
    echo -e "${RED}✗ 不存在${NC}"
    echo ""
    echo -e "${YELLOW}提示: 请先初始化数据库${NC}"
    echo "命令: python3 init_db.py"
fi

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "第四部分: 文件完整性检查"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

echo "检查关键文件:"
echo ""

# 后端文件
files=(
    "app/services/performance_service.py:后端业务逻辑"
    "app/api/v1/endpoints/performance.py:后端API端点"
    "app/models/performance.py:数据模型"
    "app/schemas/performance.py:数据验证"
)

for item in "${files[@]}"; do
    IFS=: read -r file desc <<< "$item"
    echo -n "  - $desc ... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ 存在${NC}"
    else
        echo -e "${RED}✗ 缺失${NC}"
    fi
done

echo ""

# 前端文件
frontend_pages=(
    "frontend/src/pages/MonthlySummary.jsx:月度总结页"
    "frontend/src/pages/MyPerformance.jsx:我的绩效页"
    "frontend/src/pages/EvaluationTaskList.jsx:评价任务页"
    "frontend/src/pages/EvaluationScoring.jsx:评价打分页"
    "frontend/src/pages/EvaluationWeightConfig.jsx:权重配置页"
)

for item in "${frontend_pages[@]}"; do
    IFS=: read -r file desc <<< "$item"
    echo -n "  - $desc ... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ 存在${NC}"
    else
        echo -e "${RED}✗ 缺失${NC}"
    fi
done

echo ""

# 文档文件
docs=(
    "PERFORMANCE_SYSTEM_COMPLETE.md:完整实现报告"
    "QUICK_VERIFICATION_GUIDE.md:快速验证指南"
    "FINAL_INTEGRATION_REPORT.md:最终集成报告"
)

for item in "${docs[@]}"; do
    IFS=: read -r file desc <<< "$item"
    echo -n "  - $desc ... "
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓ 存在${NC}"
    else
        echo -e "${RED}✗ 缺失${NC}"
    fi
done

echo ""

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "测试结果汇总"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

if [ $TOTAL_TESTS -gt 0 ]; then
    success_rate=$((PASSED_TESTS * 100 / TOTAL_TESTS))

    echo "API测试统计:"
    echo "  总测试数: $TOTAL_TESTS"
    echo -e "  通过: ${GREEN}$PASSED_TESTS${NC}"
    echo -e "  失败: ${RED}$FAILED_TESTS${NC}"
    echo "  成功率: $success_rate%"
    echo ""
fi

echo "系统状态:"
if [ $BACKEND_RUNNING -eq 1 ]; then
    echo -e "  后端: ${GREEN}✓ 运行中${NC}"
else
    echo -e "  后端: ${RED}✗ 未运行${NC}"
fi

if [ $FRONTEND_RUNNING -eq 1 ]; then
    echo -e "  前端: ${GREEN}✓ 运行中${NC}"
else
    echo -e "  前端: ${RED}✗ 未运行${NC}"
fi

echo ""

# 给出建议
if [ $BACKEND_RUNNING -eq 1 ] && [ $FRONTEND_RUNNING -eq 1 ]; then
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${GREEN}✓ 系统运行正常!${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "访问地址:"
    echo "  前端: http://localhost:5173"
    echo "  后端: http://localhost:8000"
    echo "  API文档: http://localhost:8000/docs"
    echo ""
    echo "下一步:"
    echo "  1. 访问前端页面进行功能测试"
    echo "  2. 查看 QUICK_VERIFICATION_GUIDE.md 进行详细验证"
    echo "  3. 查看 PERFORMANCE_SYSTEM_COMPLETE.md 了解完整功能"
else
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo -e "${YELLOW}⚠ 系统未完全启动${NC}"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "请执行以下命令启动服务:"
    echo ""

    if [ $BACKEND_RUNNING -eq 0 ]; then
        echo "启动后端:"
        echo "  python3 -m app.main"
        echo ""
    fi

    if [ $FRONTEND_RUNNING -eq 0 ]; then
        echo "启动前端:"
        echo "  cd frontend && npm run dev"
        echo ""
    fi
fi

echo "=========================================="
echo ""
