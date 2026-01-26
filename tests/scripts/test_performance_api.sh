#!/bin/bash

# 新绩效系统 API 测试脚本
# 创建时间: 2026-01-07

BASE_URL="http://localhost:8000/api/v1"
echo "=========================================="
echo "新绩效系统 API 测试"
echo "=========================================="
echo ""

# 测试健康检查
echo "1. 测试健康检查..."
curl -s http://localhost:8000/health | jq '.' 2>/dev/null || curl -s http://localhost:8000/health
echo -e "\n"

# 测试权重配置端点（不需要认证的测试）
echo "2. 测试 API 端点可访问性..."
echo "   - 检查 /docs 文档页面..."
curl -s -o /dev/null -w "   HTTP Status: %{http_code}\n" http://localhost:8000/docs

echo "   - 检查 /api/v1/performance/weight-config (需要认证)..."
curl -s -o /dev/null -w "   HTTP Status: %{http_code}\n" ${BASE_URL}/performance/weight-config

echo "   - 检查 /api/v1/performance/my-performance (需要认证)..."
curl -s -o /dev/null -w "   HTTP Status: %{http_code}\n" ${BASE_URL}/performance/my-performance

echo "   - 检查 /api/v1/performance/evaluation-tasks (需要认证)..."
curl -s -o /dev/null -w "   HTTP Status: %{http_code}\n" ${BASE_URL}/performance/evaluation-tasks
echo ""

# 检查数据库表
echo "3. 检查数据库表..."
sqlite3 data/app.db "SELECT COUNT(*) as count FROM sqlite_master WHERE type='table' AND name IN ('monthly_work_summary', 'performance_evaluation_record', 'evaluation_weight_config');" 2>/dev/null
echo "   预期: 3 (三张新表)"
echo ""

# 检查默认权重配置
echo "4. 检查默认权重配置..."
sqlite3 data/app.db "SELECT dept_manager_weight, project_manager_weight, effective_date FROM evaluation_weight_config LIMIT 1;" 2>/dev/null
echo ""

echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "📌 重要提示:"
echo "   - API 端点返回 401 是正常的（需要认证）"
echo "   - API 端点返回 403 是正常的（需要权限）"
echo "   - 完整测试需要先通过 /auth/login 获取 Token"
echo ""
echo "📚 API 文档: http://localhost:8000/docs"
echo "🔍 测试工具: Swagger UI 或 Postman"
echo ""
