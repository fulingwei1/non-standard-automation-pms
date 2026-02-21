#!/bin/bash
# 运行 Models 和 Schemas 测试并生成覆盖率报告

set -e

cd "$(dirname "$0")/.."

echo "🧪 开始运行 Models 和 Schemas 测试..."
echo ""

# 设置环境变量
export DATABASE_URL="sqlite:///:memory:"
export SECRET_KEY="test-secret-key-for-ci-with-32-chars-minimum!"
export REDIS_URL=""
export ENABLE_SCHEDULER="false"

# 运行 Models 测试
echo "📦 运行 Models 测试..."
python3 -m pytest tests/unit/models/ \
    -v \
    --tb=short \
    --maxfail=5 \
    -x \
    2>&1 | tee logs/models_test_output.txt || true

echo ""
echo "📋 运行 Schemas 测试..."
python3 -m pytest tests/unit/schemas/ \
    -v \
    --tb=short \
    --maxfail=5 \
    -x \
    2>&1 | tee logs/schemas_test_output.txt || true

echo ""
echo "📊 生成覆盖率报告..."
python3 -m pytest tests/unit/models/ tests/unit/schemas/ \
    --cov=app/models \
    --cov=app/schemas \
    --cov-report=term \
    --cov-report=html:htmlcov \
    --cov-report=json:coverage.json \
    -v \
    2>&1 | tee logs/coverage_report.txt || true

echo ""
echo "✅ 测试完成！"
echo ""
echo "📈 测试统计："
echo "  - Models 测试文件: $(find tests/unit/models -name 'test_*.py' | wc -l | tr -d ' ')"
echo "  - Schemas 测试文件: $(find tests/unit/schemas -name 'test_*.py' | wc -l | tr -d ' ')"
echo "  - 总计: $(find tests/unit/{models,schemas} -name 'test_*.py' | wc -l | tr -d ' ')"
echo ""
echo "📁 报告位置："
echo "  - HTML 覆盖率报告: htmlcov/index.html"
echo "  - JSON 覆盖率数据: coverage.json"
echo "  - 测试日志: logs/"
