#!/bin/bash

echo "=================================="
echo "🧪 API测试开始"
echo "=================================="

echo ""
echo "1️⃣ 测试根路径..."
curl -s http://127.0.0.1:8001/

echo ""
echo ""
echo "2️⃣ 测试健康检查..."
curl -s http://127.0.0.1:8001/health 2>/dev/null || echo "No /health endpoint"

echo ""
echo ""
echo "3️⃣ 检查API文档..."
curl -s -I http://127.0.0.1:8001/docs | grep -i "HTTP\|content-type"

echo ""
echo "4️⃣ 检查路由统计..."
curl -s http://127.0.0.1:8001/openapi.json | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    paths = data.get('paths', {})
    print(f'总路由数: {len(paths)}')
    print(f'前5个路由:')
    for i, path in enumerate(list(paths.keys())[:5], 1):
        methods = ', '.join(paths[path].keys())
        print(f'  {i}. {path} ({methods})')
except: pass
"

echo ""
echo ""
echo "5️⃣ 测试用户模块（需要认证，预期401）..."
curl -s http://127.0.0.1:8001/users/ | python3 -c "
import sys, json
try:
    data = json.load(sys.stdin)
    print(f'状态码判断: {\"detail\" in data}')
    print(f'响应: {data}')
except Exception as e:
    print(f'解析失败: {e}')
    print(sys.stdin.read())
"

echo ""
echo ""
echo "=================================="
echo "✅ API测试完成"
echo "=================================="
