#!/bin/bash
# 快速测试脚本 - 测试登录和获取用户信息

BASE_URL="http://127.0.0.1:8000/api/v1"

echo "=========================================="
echo "快速API测试"
echo "=========================================="
echo ""

# 检查服务器
echo "1. 检查服务器..."
if ! curl -s http://127.0.0.1:8000/health > /dev/null; then
    echo "❌ 服务器未运行！请先启动："
    echo "   cd 非标自动化项目管理系统"
    echo "   uvicorn app.main:app --reload"
    exit 1
fi
echo "✅ 服务器运行正常"
echo ""

# 登录
echo "2. 用户登录..."
echo "请输入用户名（默认: admin）:"
read -r USERNAME
USERNAME=${USERNAME:-admin}

echo "请输入密码（默认: admin123）:"
read -s PASSWORD
PASSWORD=${PASSWORD:-admin123}
echo ""

LOGIN_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$USERNAME&password=$PASSWORD" \
    "$BASE_URL/auth/login")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    echo "响应: $LOGIN_RESPONSE"
    exit 1
fi

echo "✅ 登录成功"
echo "Token: ${TOKEN:0:50}..."
echo ""

# 获取当前用户
echo "3. 获取当前用户信息..."
USER_INFO=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/auth/me")

echo "$USER_INFO" | python3 -m json.tool 2>/dev/null || echo "$USER_INFO"
echo ""

# 获取用户列表
echo "4. 获取用户列表..."
USER_LIST=$(curl -s -X GET \
    -H "Authorization: Bearer $TOKEN" \
    "$BASE_URL/users?page=1&page_size=5")

echo "$USER_LIST" | python3 -m json.tool 2>/dev/null || echo "$USER_LIST"
echo ""

echo "✅ 测试完成！"
echo ""
echo "提示: 可以访问 http://127.0.0.1:8000/docs 查看完整API文档"



