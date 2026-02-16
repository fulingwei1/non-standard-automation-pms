#!/bin/bash

echo "=== 🧪 全面API测试套件 ==="
echo ""

# 获取token
echo "🔐 登录测试..."
LOGIN_RESPONSE=$(curl -s -X POST http://127.0.0.1:8001/api/v1/auth/login \
  -d "username=admin&password=admin123")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; d=json.load(sys.stdin); print(d.get('access_token', 'ERROR'))" 2>/dev/null)

if [ "$TOKEN" = "ERROR" ] || [ -z "$TOKEN" ]; then
  echo "❌ 登录失败"
  exit 1
fi

echo "✅ 登录成功"
echo ""

# 核心API测试
echo "📊 核心业务API测试:"
echo ""

test_api() {
  local name=$1
  local url=$2
  local response=$(curl -s -H "Authorization: Bearer $TOKEN" "$url")
  
  if echo "$response" | python3 -c "import sys, json; json.load(sys.stdin); sys.exit(0)" 2>/dev/null; then
    local count=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('total', '?'))" 2>/dev/null)
    echo "  ✅ $name - 返回: $count 条记录"
    return 0
  else
    echo "  ❌ $name - 错误"
    echo "$response" | head -3
    return 1
  fi
}

# 测试各个端点
test_api "当前用户" "http://127.0.0.1:8001/api/v1/auth/me"
test_api "项目列表" "http://127.0.0.1:8001/api/v1/projects/?page=1&page_size=3"
test_api "生产工单" "http://127.0.0.1:8001/api/v1/production/work-orders?page=1&page_size=3"
test_api "销售合同" "http://127.0.0.1:8001/api/v1/sales/contracts?page=1&page_size=3"
test_api "客户列表" "http://127.0.0.1:8001/api/v1/customers/?page=1&page_size=3"
test_api "物料列表" "http://127.0.0.1:8001/api/v1/materials/?page=1&page_size=3"

echo ""
echo "=== 测试完成 ==="
