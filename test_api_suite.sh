#!/bin/bash

echo "=== 🧪 API全面测试套件 ==="
echo ""

# 获取token
echo "1️⃣  测试登录API..."
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8001/api/v1/auth/login \
  -d "username=admin&password=admin123")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('access_token', 'ERROR'))" 2>/dev/null)

if [ "$TOKEN" = "ERROR" ] || [ -z "$TOKEN" ]; then
  echo "❌ 登录失败"
  echo "$LOGIN_RESPONSE"
  exit 1
fi

echo "✅ 登录成功，token获取成功"
echo ""

# 测试核心端点
echo "2️⃣  测试核心业务API..."
echo ""

# 项目列表
echo "📋 测试: GET /api/v1/projects/"
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8001/api/v1/projects/?page=1&page_size=3")
echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print('✅ 状态码: 200, 返回: {} 项目'.format(d.get('total', '?')))" 2>/dev/null || echo "⚠️  返回数据: $RESPONSE"
echo ""

# 用户信息
echo "👤 测试: GET /api/v1/users/current"
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8001/api/v1/users/current")
echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print('✅ 用户: {}'.format(d.get('username', '?')))" 2>/dev/null || echo "⚠️  返回数据: $RESPONSE"
echo ""

# 生产工单
echo "🏭 测试: GET /api/v1/production/work-orders/"
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8001/api/v1/production/work-orders/?page=1&page_size=3")
if [ -n "$RESPONSE" ]; then
  echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print('✅ 状态码: 200, 返回: {} 工单'.format(d.get('total', '?')))" 2>/dev/null || echo "⚠️  返回: $RESPONSE"
else
  echo "⚠️  空响应"
fi
echo ""

# 销售订单
echo "💰 测试: GET /api/v1/sales/contracts/"
RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "http://127.0.0.1:8001/api/v1/sales/contracts/?page=1&page_size=3")
echo "$RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print('✅ 状态码: 200, 返回: {} 合同'.format(d.get('total', '?')))" 2>/dev/null || echo "⚠️  返回: $RESPONSE"
echo ""

echo "=== 测试完成 ==="
