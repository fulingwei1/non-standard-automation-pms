#!/bin/bash

# 快速验证 CI/CD 和测试配置

set -e

echo "=== 验证 CI/CD 和测试配置 ==="
echo

# 1. 检查 Python 环境
echo "1. 检查 Python 环境..."
python3 --version
pip list | grep -E "(pytest|coverage|ruff|mypy|bandit)" || echo "⚠️  部分工具未安装"

echo
# 2. 检查测试配置
echo "2. 检查测试配置..."
if [ -f "pytest.ini" ]; then
    echo "✅ pytest.ini 存在"
    cat pytest.ini
else
    echo "❌ pytest.ini 不存在"
fi

echo
# 3. 检查 CI/CD 配置
echo "3. 检查 CI/CD 配置..."
if [ -f ".github/workflows/ci.yml" ]; then
    echo "✅ GitHub Actions 工作流配置存在"
else
    echo "❌ GitHub Actions 工作流配置不存在"
fi

echo
# 4. 检查 Docker 配置
echo "4. 检查 Docker 配置..."
if [ -f "Dockerfile" ]; then
    echo "✅ Dockerfile 存在"
else
    echo "❌ Dockerfile 不存在"
fi

if [ -f "docker-compose.yml" ]; then
    echo "✅ docker-compose.yml 存在"
else
    echo "❌ docker-compose.yml 不存在"
fi

echo
# 5. 检查测试文件
echo "5. 检查测试文件..."
TEST_COUNT=$(find tests/ -name "test_*.py" | wc -l | tr -d ' ')
echo "找到 $TEST_COUNT 个测试文件"

NEW_TESTS=(
    "test_health_calculator.py"
    "test_permission_system.py"
    "test_stage_transition.py"
    "test_cache_system.py"
    "test_notification_service.py"
)

for test_file in "${NEW_TESTS[@]}"; do
    if [ -f "tests/unit/$test_file" ]; then
        echo "✅ $test_file 存在"
    else
        echo "⚠️  $test_file 不存在"
    fi
done

echo
# 6. 检查代码质量工具
echo "6. 检查代码质量工具..."
if [ -f ".pre-commit-config.yaml" ]; then
    echo "✅ pre-commit 配置存在"
else
    echo "❌ pre-commit 配置不存在"
fi

echo
# 7. 收集测试统计
echo "7. 收集测试统计..."
if command -v pytest &> /dev/null; then
    echo "收集测试用例..."
    TOTAL=$(python3 -m pytest tests/ --collect-only -q 2>/dev/null | grep "collected" || echo "0")
    echo "$TOTAL"
else
    echo "⚠️  pytest 未安装，无法收集测试"
fi

echo
# 8. 检查监控配置
echo "8. 检查监控配置..."
if [ -f "monitoring/prometheus.yml" ]; then
    echo "✅ Prometheus 配置存在"
fi

if [ -f "monitoring/alerts/pms.yml" ]; then
    echo "✅ 告警规则配置存在"
fi

echo
# 9. 运行代码检查
echo "9. 运行代码检查（快速）..."
if command -v ruff &> /dev/null; then
    echo "运行 Ruff 检查..."
    ruff check app/ --output-format=concise --select=E,F --count || true
else
    echo "⚠️  ruff 未安装"
fi

echo
# 10. 生成验证报告
echo "10. 生成验证报告..."
REPORT_FILE="validation_report_$(date +%Y%m%d_%H%M%S).txt"

cat > "$REPORT_FILE" <<EOF
CI/CD 配置验证报告
==================
时间: $(date)

环境:
- Python: $(python3 --version)
- OS: $(uname -s)

配置文件:
- pytest.ini: $([ -f pytest.ini ] && echo "✅" || echo "❌")
- .github/workflows/ci.yml: $([ -f .github/workflows/ci.yml ] && echo "✅" || echo "❌")
- Dockerfile: $([ -f Dockerfile ] && echo "✅" || echo "❌")
- docker-compose.yml: $([ -f docker-compose.yml ] && echo "✅" || echo "❌")
- .pre-commit-config.yaml: $([ -f .pre-commit-config.yaml ] && echo "✅" || echo "❌")
- monitoring/prometheus.yml: $([ -f monitoring/prometheus.yml ] && echo "✅" || echo "❌")

测试文件:
- 总数: $TEST_COUNT
- 新增单元测试: 5

下一步:
1. 安装依赖: pip install -r requirements.txt
2. 安装测试工具: pip install pytest pytest-cov pytest-benchmark
3. 运行测试: pytest tests/ -v
4. 运行性能测试: pytest tests/performance/ --benchmark-only
5. 部署到 Docker: docker-compose up -d

完整文档: docs/TEST_AND_CI_CD_OPTIMIZATION.md
性能优化: docs/PERFORMANCE_OPTIMIZATION.md
EOF

echo "✅ 验证报告已生成: $REPORT_FILE"
cat "$REPORT_FILE"

echo
echo "=== 验证完成 ==="
echo
echo "建议的后续步骤:"
echo "1. 运行完整测试: pytest tests/ -v --cov=app"
echo "2. 安装 pre-commit: pre-commit install"
echo "3. 运行性能分析: ./scripts/analyze_performance.sh"
echo "4. 启动 Docker 环境: docker-compose up -d"
