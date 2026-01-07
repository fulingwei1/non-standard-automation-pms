#!/bin/bash
# 前端诊断脚本

echo "=========================================="
echo "前端服务诊断"
echo "=========================================="

echo ""
echo "1. 检查前端服务..."
if curl -s http://localhost:5173 > /dev/null 2>&1; then
    echo "✓ 前端服务运行正常 (http://localhost:5173)"
else
    echo "✗ 前端服务无法访问"
fi

echo ""
echo "2. 检查后端 API..."
if curl -s http://127.0.0.1:8000/health > /dev/null 2>&1; then
    echo "✓ 后端 API 运行正常 (http://127.0.0.1:8000)"
    HEALTH=$(curl -s http://127.0.0.1:8000/health)
    echo "  响应: $HEALTH"
else
    echo "✗ 后端 API 无法访问"
fi

echo ""
echo "3. 检查 API 代理配置..."
if grep -q "target: 'http://127.0.0.1:8000'" frontend/vite.config.js 2>/dev/null; then
    echo "✓ Vite 代理配置正确"
else
    echo "⚠ 请检查 vite.config.js 中的代理配置"
fi

echo ""
echo "4. 检查端口占用..."
if lsof -ti:5173 > /dev/null 2>&1; then
    PID=$(lsof -ti:5173 | head -1)
    echo "✓ 端口 5173 被进程 $PID 占用（正常）"
else
    echo "✗ 端口 5173 未被占用（前端服务可能未启动）"
fi

if lsof -ti:8000 > /dev/null 2>&1; then
    PID=$(lsof -ti:8000 | head -1)
    echo "✓ 端口 8000 被进程 $PID 占用（正常）"
else
    echo "✗ 端口 8000 未被占用（后端服务可能未启动）"
fi

echo ""
echo "5. 测试 API 连接..."
API_TEST=$(curl -s http://127.0.0.1:8000/api/v1/openapi.json 2>&1 | head -1)
if [[ $API_TEST == *"openapi"* ]] || [[ $API_TEST == *"swagger"* ]] || [[ $API_TEST == "{"* ]]; then
    echo "✓ API 端点可访问"
else
    echo "✗ API 端点无法访问"
    echo "  响应: $API_TEST"
fi

echo ""
echo "=========================================="
echo "诊断完成"
echo "=========================================="
echo ""
echo "访问地址:"
echo "  前端: http://localhost:5173"
echo "  后端 API: http://127.0.0.1:8000"
echo "  API 文档: http://127.0.0.1:8000/docs"
echo ""
echo "如果前端页面显示异常，请："
echo "1. 打开浏览器开发者工具 (F12)"
echo "2. 查看 Console 标签页的错误信息"
echo "3. 查看 Network 标签页的请求状态"
echo "4. 检查是否有 CORS 错误"


