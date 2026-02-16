#!/bin/bash

TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | grep -o '"access_token":"[^"]*"' | cut -d'"' -f4)

test_route() {
    path=$1
    name=$2
    http_code=$(curl -s -o /dev/null -w "%{http_code}" \
        -H "Authorization: Bearer $TOKEN" \
        "http://127.0.0.1:8000${path}")
    
    if [ "$http_code" == "404" ]; then
        echo "❌ $name - 404"
        # 尝试不同的路径变体
        alt_path=$(echo "$path" | sed 's/\/$//')  # 去掉末尾斜杠
        if [ "$alt_path" != "$path" ]; then
            alt_code=$(curl -s -o /dev/null -w "%{http_code}" \
                -H "Authorization: Bearer $TOKEN" \
                "http://127.0.0.1:8000${alt_path}")
            if [ "$alt_code" != "404" ]; then
                echo "   💡 尝试 $alt_path - $alt_code"
            fi
        fi
    elif [ "$http_code" == "422" ]; then
        echo "✅ $name - 422 (路由存在，参数错误)"
    else
        echo "✅ $name - $http_code"
    fi
}

echo "测试路由（带末尾斜杠）"
test_route "/api/v1/roles/" "角色列表"
test_route "/api/v1/permissions/" "权限列表"
test_route "/api/v1/inventory/" "库存列表"
test_route "/api/v1/rd-projects/" "研发项目"
test_route "/api/v1/approvals/" "审批列表"
test_route "/api/v1/presale/tickets/" "预售工单"

echo ""
echo "测试路由（不带末尾斜杠）"
test_route "/api/v1/roles" "角色列表"
test_route "/api/v1/permissions" "权限列表"
test_route "/api/v1/inventory" "库存列表"
test_route "/api/v1/rd-projects" "研发项目"
test_route "/api/v1/approvals" "审批列表"
test_route "/api/v1/presale/tickets" "预售工单"
