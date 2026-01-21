# API集成测试运行脚本
#
# 使用方法：
#   python3 tests/run_api_integration_tests.sh
# 或者直接运行：
#   ./tests/run_api_integration_tests.sh

#!/bin/bash

set -e

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$PROJECT_ROOT"

echo ""
echo "========================================"
echo "  API集成测试运行脚本"
echo "========================================"
echo ""
echo "项目根目录: $PROJECT_ROOT"
echo ""

# 检查依赖
echo "检查依赖..."
if ! command -v pytest &> /dev/null; then
    echo -e "${RED}✗ pytest未安装，请运行: pip install pytest${NC}"
    exit 1
fi
echo -e "${GREEN}✓ pytest已安装${NC}"
echo ""

# 激活虚拟环境（如果存在）
if [ -d "venv" ]; then
    echo "激活虚拟环境..."
    source venv/bin/activate
    echo -e "${GREEN}✓ 虚拟环境已激活${NC}"
    echo ""
fi

# 运行测试函数
run_tests() {
    local test_file=$1
    local description=$2

    echo ""
    echo "========================================"
    echo "  $description"
    echo "========================================"

    if [ -f "tests/$test_file" ]; then
        pytest "tests/$test_file" -v --tb=short
        if [ $? -eq 0 ]; then
            echo -e "${GREEN}✓ $description 测试通过${NC}"
        else
            echo -e "${RED}✗ $description 测试失败${NC}"
            return 1
        fi
    else
        echo -e "${YELLOW}⚠ 测试文件不存在: tests/$test_file${NC}"
    fi
}

# 运行所有测试
run_all_tests() {
    echo ""
    echo -e "${BLUE}运行所有API集成测试...${NC}"
    echo ""

    local failed=0

    # 认证模块
    run_tests "integration/test_auth_api.py" "认证模块测试" || failed=$((failed + 1))

    # 项目管理模块
    run_tests "integration/test_projects_api_ai.py" "项目管理模块测试" || failed=$((failed + 1))

    # 物料管理模块
    run_tests "integration/test_materials_api_ai.py" "物料管理模块测试" || failed=$((failed + 1))

    # 采购管理模块
    run_tests "integration/test_purchase_api_ai.py" "采购管理模块测试" || failed=$((failed + 1))

    # 验收管理模块
    run_tests "integration/test_acceptance_api_ai.py" "验收管理模块测试" || failed=$((failed + 1))

    # ECN变更管理模块
    run_tests "integration/test_ecn_api_ai.py" "ECN变更管理模块测试" || failed=$((failed + 1))

    # 预警管理模块
    run_tests "integration/test_alerts_api_ai.py" "预警管理模块测试" || failed=$((failed + 1))

    # 销售管理模块
    run_tests "integration/test_sales_api_ai.py" "销售管理模块测试" || failed=$((failed + 1))

    # 生产管理模块
    run_tests "integration/test_production_api_ai.py" "生产管理模块测试" || failed=$((failed + 1))

    # 外协管理模块
    run_tests "integration/test_outsourcing_api_ai.py" "外协管理模块测试" || failed=$((failed + 1))

    # 成本管理模块
    run_tests "integration/test_costs_api_ai.py" "成本管理模块测试" || failed=$((failed + 1))

    # 进度管理模块
    run_tests "integration/test_progress_api_ai.py" "进度管理模块测试" || failed=$((failed + 1))

    # 任务中心模块
    run_tests "integration/test_task_center_api_ai.py" "任务中心模块测试" || failed=$((failed + 1))

    # 工时管理模块
    run_tests "integration/test_timesheet_api_ai.py" "工时管理模块测试" || failed=$((failed + 1))

    # PMO管理模块
    run_tests "integration/test_pmo_api_ai.py" "PMO管理模块测试" || failed=$((failed + 1))

    # 文档管理模块
    run_tests "integration/test_documents_api_ai.py" "文档管理模块测试" || failed=$((failed + 1))

    # 客户管理模块
    run_tests "integration/test_customers_api_ai.py" "客户管理模块测试" || failed=$((failed + 1))

    # 供应商管理模块
    run_tests "integration/test_suppliers_api_ai.py" "供应商管理模块测试" || failed=$((failed + 1))

    # 机台管理模块
    run_tests "integration/test_machines_api_ai.py" "机台管理模块测试" || failed=$((failed + 1))

    # 用户管理模块
    run_tests "integration/test_users_api_ai.py" "用户管理模块测试" || failed=$((failed + 1))

    # 现有其他集成测试
    run_tests "integration/test_critical_apis.py" "关键API测试" || failed=$((failed + 1))
    run_tests "integration/test_project_workflow.py" "项目工作流测试" || failed=$((failed + 1))

    echo ""
    echo "========================================"
    echo "  测试汇总"
    echo "========================================"

    if [ $failed -eq 0 ]; then
        echo -e "${GREEN}✓ 所有测试通过！${NC}"
        return 0
    else
        echo -e "${RED}✗ 有 $failed 个模块测试失败${NC}"
        return 1
    fi
}

# 生成测试覆盖率报告
generate_coverage_report() {
    echo ""
    echo -e "${BLUE}生成测试覆盖率报告...${NC}"
    echo ""

    pytest tests/integration/ \
        --cov=app \
        --cov-report=html:htmlcov/integration \
        --cov-report=term-missing \
        --cov-report=xml:coverage/integration.xml \
        -v \
        --tb=short

    echo ""
    echo -e "${GREEN}✓ 覆盖率报告已生成${NC}"
    echo "  - HTML报告: htmlcov/integration/index.html"
    echo "  - XML报告: coverage/integration.xml"
}

# 主函数
main() {
    case "${1:-all}" in
        auth)
            run_tests "integration/test_auth_api.py" "认证模块测试"
            ;;
        projects)
            run_tests "integration/test_projects_api_ai.py" "项目管理模块测试"
            ;;
        materials)
            run_tests "integration/test_materials_api_ai.py" "物料管理模块测试"
            ;;
        purchase)
            run_tests "integration/test_purchase_api_ai.py" "采购管理模块测试"
            ;;
        acceptance)
            run_tests "integration/test_acceptance_api_ai.py" "验收管理模块测试"
            ;;
        ecn)
            run_tests "integration/test_ecn_api_ai.py" "ECN变更管理模块测试"
            ;;
        alerts)
            run_tests "integration/test_alerts_api_ai.py" "预警管理模块测试"
            ;;
        sales)
            run_tests "integration/test_sales_api_ai.py" "销售管理模块测试"
            ;;
        production)
            run_tests "integration/test_production_api_ai.py" "生产管理模块测试"
            ;;
        outsourcing)
            run_tests "integration/test_outsourcing_api_ai.py" "外协管理模块测试"
            ;;
        critical)
            run_tests "integration/test_critical_apis.py" "关键API测试"
            ;;
        workflow)
            run_tests "integration/test_project_workflow.py" "项目工作流测试"
            ;;
        documents)
            run_tests "integration/test_documents_api_ai.py" "文档管理模块测试"
            ;;
        customers)
            run_tests "integration/test_customers_api_ai.py" "客户管理模块测试"
            ;;
        suppliers)
            run_tests "integration/test_suppliers_api_ai.py" "供应商管理模块测试"
            ;;
        machines)
            run_tests "integration/test_machines_api_ai.py" "机台管理模块测试"
            ;;
        users)
            run_tests "integration/test_users_api_ai.py" "用户管理模块测试"
            ;;
        coverage)
            generate_coverage_report
            ;;
        all)
            run_all_tests
            # 可选：生成覆盖率报告
            # generate_coverage_report
            ;;
        clean)
            echo "清理测试缓存和覆盖率文件..."
            rm -rf htmlcov/
            rm -rf coverage/
            rm -rf .pytest_cache/
            rm -rf __pycache__/
            rm -rf .coverage
            rm -rf tests/__pycache__/
            rm -rf tests/integration/__pycache__/
            echo -e "${GREEN}✓ 清理完成${NC}"
            ;;
        *)
            echo "使用方法: $0 [选项]"
            echo ""
            echo "选项："
            echo "  all        - 运行所有测试（默认）"
            echo "  auth       - 运行认证模块测试"
            echo "  projects   - 运行项目管理模块测试"
             echo "  materials  - 运行物料管理模块测试"
            echo "  purchase   - 运行采购管理模块测试"
            echo "  acceptance - 运行验收管理模块测试"
            echo "  ecn        - 运行ECN变更管理模块测试"
            echo "  alerts     - 运行预警管理模块测试"
            echo "  sales      - 运行销售管理模块测试"
            echo "  production - 运行生产管理模块测试"
            echo "  outsourcing - 运行外协管理模块测试"
            echo "  costs      - 运行成本管理模块测试"
            echo "  progress   - 运行进度管理模块测试"
            echo "  tasks      - 运行任务中心模块测试"
            echo "  timesheet  - 运行工时管理模块测试"
            echo "  pmo        - 运行PMO管理模块测试"
            echo "  documents  - 运行文档管理模块测试"
            echo "  customers  - 运行客户管理模块测试"
            echo "  suppliers  - 运行供应商管理模块测试"
            echo "  machines   - 运行机台管理模块测试"
            echo "  users      - 运行用户管理模块测试"
            echo "  critical   - 运行关键API测试"
            echo "  workflow   - 运行项目工作流测试"
            echo "  coverage   - 生成测试覆盖率报告"
            echo "  clean      - 清理测试缓存"
            echo ""
            echo "示例："
            echo "  $0              # 运行所有测试"
            echo "  $0 auth         # 只运行认证测试"
            echo "  $0 coverage     # 生成覆盖率报告"
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"

# 退出码
exit_code=$?

echo ""
echo "========================================"
if [ $exit_code -eq 0 ]; then
    echo -e "${GREEN}✓ 测试完成，所有测试通过${NC}"
else
    echo -e "${RED}✗ 测试完成，存在失败${NC}"
fi
echo "========================================"

exit $exit_code
