#!/bin/bash

# 获取token
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}' | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

echo "Token: ${TOKEN:0:20}..."
echo ""

# 测试路由
test_route() {
    local path=$1
    local name=$2
    
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "http://127.0.0.1:8000${path}")
    
    if [ "$http_code" == "404" ]; then
        echo "❌ $name - 404 (路由不存在)"
    elif [ "$http_code" == "200" ]; then
        echo "✅ $name - 200 (正常)"
    elif [ "$http_code" == "422" ]; then
        echo "⚠️  $name - 422 (参数错误，但路由存在)"
    else
        echo "⚡ $name - $http_code"
    fi
}

echo "=== 核心模块 ==="
test_route "/api/v1/users/" "用户列表"
test_route "/api/v1/roles/" "角色列表"
test_route "/api/v1/permissions/" "权限列表"

echo ""
echo "=== 业务模块 ==="
test_route "/api/v1/projects/" "项目列表"
test_route "/api/v1/production/work-orders" "生产工单"
test_route "/api/v1/sales/opportunities" "销售机会"

echo ""
echo "=== 采购库存 ==="
test_route "/api/v1/suppliers/" "供应商列表"
test_route "/api/v1/purchase-orders/" "采购订单"
test_route "/api/v1/inventory/" "库存列表"
test_route "/api/v1/shortage/alerts" "缺料预警"

echo ""
echo "=== 工时预售 ==="
test_route "/api/v1/timesheet/records" "工时记录"
test_route "/api/v1/presale/tickets" "预售工单"
