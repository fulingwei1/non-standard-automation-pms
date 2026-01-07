#!/bin/bash
# -*- coding: utf-8 -*-
# 用户认证与权限 API 测试脚本
# 使用方法: bash test_auth_apis.sh

BASE_URL="http://127.0.0.1:8000/api/v1"
TOKEN_FILE="/tmp/auth_token.txt"

echo "=========================================="
echo "用户认证与权限 API 测试脚本"
echo "=========================================="
echo ""

# 颜色定义
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# 检查服务器是否运行
echo "1. 检查服务器状态..."
HEALTH_RESPONSE=$(curl -s http://127.0.0.1:8000/health)
if [ $? -ne 0 ]; then
    echo -e "${RED}❌ 服务器未运行！请先启动服务器：${NC}"
    echo "   cd 非标自动化项目管理系统"
    echo "   uvicorn app.main:app --reload"
    exit 1
fi
echo -e "${GREEN}✅ 服务器运行正常${NC}"
echo "   响应: $HEALTH_RESPONSE"
echo ""

# 保存token的函数
save_token() {
    echo "$1" > $TOKEN_FILE
}

# 读取token的函数
get_token() {
    if [ -f $TOKEN_FILE ]; then
        cat $TOKEN_FILE
    else
        echo ""
    fi
}

# 测试函数
test_api() {
    local method=$1
    local endpoint=$2
    local data=$3
    local description=$4
    local need_auth=${5:-true}
    
    echo "----------------------------------------"
    echo "测试: $description"
    echo "请求: $method $endpoint"
    
    TOKEN=$(get_token)
    if [ "$need_auth" = "true" ] && [ -z "$TOKEN" ]; then
        echo -e "${YELLOW}⚠️  需要先登录获取Token${NC}"
        return 1
    fi
    
    if [ "$method" = "GET" ]; then
        if [ -n "$TOKEN" ] && [ "$need_auth" = "true" ]; then
            RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
                -H "Authorization: Bearer $TOKEN" \
                "$BASE_URL$endpoint")
        else
            RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
                "$BASE_URL$endpoint")
        fi
    elif [ "$method" = "POST" ] || [ "$method" = "PUT" ]; then
        if [ -n "$TOKEN" ] && [ "$need_auth" = "true" ]; then
            RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
                -X $method \
                -H "Content-Type: application/json" \
                -H "Authorization: Bearer $TOKEN" \
                -d "$data" \
                "$BASE_URL$endpoint")
        else
            RESPONSE=$(curl -s -w "\nHTTP_CODE:%{http_code}" \
                -X $method \
                -H "Content-Type: application/json" \
                -d "$data" \
                "$BASE_URL$endpoint")
        fi
    fi
    
    HTTP_CODE=$(echo "$RESPONSE" | grep "HTTP_CODE" | cut -d: -f2)
    BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')
    
    if [ "$HTTP_CODE" -ge 200 ] && [ "$HTTP_CODE" -lt 300 ]; then
        echo -e "${GREEN}✅ 成功 (HTTP $HTTP_CODE)${NC}"
        echo "响应: $BODY" | python3 -m json.tool 2>/dev/null || echo "响应: $BODY"
    else
        echo -e "${RED}❌ 失败 (HTTP $HTTP_CODE)${NC}"
        echo "响应: $BODY"
    fi
    echo ""
}

# ==========================================
# 2. 认证相关 API 测试
# ==========================================
echo "=========================================="
echo "2. 认证相关 API 测试"
echo "=========================================="

# 2.1 用户登录
echo "请输入测试用户名（默认: admin）:"
read -r TEST_USERNAME
TEST_USERNAME=${TEST_USERNAME:-admin}

echo "请输入测试密码（默认: admin123）:"
read -s TEST_PASSWORD
TEST_PASSWORD=${TEST_PASSWORD:-admin123}
echo ""

LOGIN_DATA="{\"username\": \"$TEST_USERNAME\", \"password\": \"$TEST_PASSWORD\"}"
LOGIN_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$TEST_USERNAME&password=$TEST_PASSWORD" \
    "$BASE_URL/auth/login")

ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)

if [ -n "$ACCESS_TOKEN" ]; then
    echo -e "${GREEN}✅ 登录成功${NC}"
    save_token "$ACCESS_TOKEN"
    echo "Token已保存"
    echo ""
else
    echo -e "${RED}❌ 登录失败${NC}"
    echo "响应: $LOGIN_RESPONSE"
    echo ""
    echo "提示: 如果数据库中没有用户，请先运行:"
    echo "  python3 init_db.py"
    exit 1
fi

# 2.2 获取当前用户信息
test_api "GET" "/auth/me" "" "获取当前用户信息"

# 2.3 刷新Token
test_api "POST" "/auth/refresh" "" "刷新访问令牌"

# 2.4 修改密码
PASSWORD_DATA='{"old_password": "admin123", "new_password": "admin123"}'
test_api "PUT" "/auth/password" "$PASSWORD_DATA" "修改密码"

# 2.5 用户登出
test_api "POST" "/auth/logout" "" "用户登出"

# 重新登录（登出后需要重新登录）
echo "重新登录..."
LOGIN_RESPONSE=$(curl -s -X POST \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=$TEST_USERNAME&password=$TEST_PASSWORD" \
    "$BASE_URL/auth/login")
ACCESS_TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('access_token', ''))" 2>/dev/null)
if [ -n "$ACCESS_TOKEN" ]; then
    save_token "$ACCESS_TOKEN"
    echo -e "${GREEN}✅ 重新登录成功${NC}"
    echo ""
fi

# ==========================================
# 3. 用户管理 API 测试
# ==========================================
echo "=========================================="
echo "3. 用户管理 API 测试"
echo "=========================================="

# 3.1 用户列表（分页）
test_api "GET" "/users?page=1&page_size=10" "" "获取用户列表（分页）"

# 3.2 用户列表（关键词搜索）
test_api "GET" "/users?keyword=admin&page=1&page_size=10" "" "搜索用户（关键词）"

# 3.3 用户列表（筛选）
test_api "GET" "/users?is_active=true&page=1&page_size=10" "" "筛选用户（启用状态）"

# 3.4 创建用户
CREATE_USER_DATA='{
    "username": "test_user_'$(date +%s)'",
    "password": "test123456",
    "email": "test@example.com",
    "real_name": "测试用户",
    "employee_no": "EMP001",
    "department": "测试部门",
    "position": "测试职位"
}'
CREATE_RESPONSE=$(test_api "POST" "/users" "$CREATE_USER_DATA" "创建新用户")
NEW_USER_ID=$(echo "$CREATE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('id', ''))" 2>/dev/null)

# 3.5 获取用户详情
if [ -n "$NEW_USER_ID" ]; then
    test_api "GET" "/users/$NEW_USER_ID" "" "获取用户详情"
fi

# 3.6 更新用户
UPDATE_USER_DATA='{
    "real_name": "更新后的测试用户",
    "department": "更新后的部门"
}'
if [ -n "$NEW_USER_ID" ]; then
    test_api "PUT" "/users/$NEW_USER_ID" "$UPDATE_USER_DATA" "更新用户信息"
fi

# 3.7 用户角色分配（需要先有角色）
test_api "GET" "/roles?page=1&page_size=5" "" "获取角色列表（用于分配）"

# ==========================================
# 4. 角色管理 API 测试
# ==========================================
echo "=========================================="
echo "4. 角色管理 API 测试"
echo "=========================================="

# 4.1 角色列表（分页）
test_api "GET" "/roles?page=1&page_size=10" "" "获取角色列表（分页）"

# 4.2 角色列表（关键词搜索）
test_api "GET" "/roles?keyword=admin&page=1&page_size=10" "" "搜索角色（关键词）"

# 4.3 获取权限列表
test_api "GET" "/roles/permissions" "" "获取所有权限列表"

# 4.4 创建角色
CREATE_ROLE_DATA='{
    "role_code": "TEST_ROLE_'$(date +%s)'",
    "role_name": "测试角色",
    "description": "这是一个测试角色",
    "data_scope": "OWN"
}'
CREATE_ROLE_RESPONSE=$(test_api "POST" "/roles" "$CREATE_ROLE_DATA" "创建新角色")
NEW_ROLE_ID=$(echo "$CREATE_ROLE_RESPONSE" | python3 -c "import sys, json; print(json.load(sys.stdin).get('data', {}).get('id', ''))" 2>/dev/null)

# 4.5 获取角色详情
if [ -n "$NEW_ROLE_ID" ]; then
    test_api "GET" "/roles/$NEW_ROLE_ID" "" "获取角色详情"
fi

# 4.6 更新角色
UPDATE_ROLE_DATA='{
    "role_name": "更新后的测试角色",
    "description": "更新后的描述"
}'
if [ -n "$NEW_ROLE_ID" ]; then
    test_api "PUT" "/roles/$NEW_ROLE_ID" "$UPDATE_ROLE_DATA" "更新角色信息"
fi

# 4.7 角色权限分配（需要先有权限）
PERMISSIONS_RESPONSE=$(curl -s -H "Authorization: Bearer $(get_token)" "$BASE_URL/roles/permissions")
FIRST_PERMISSION_ID=$(echo "$PERMISSIONS_RESPONSE" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data[0]['id'] if data else '')" 2>/dev/null)

if [ -n "$NEW_ROLE_ID" ] && [ -n "$FIRST_PERMISSION_ID" ]; then
    ASSIGN_PERMISSIONS_DATA="[$FIRST_PERMISSION_ID]"
    test_api "PUT" "/roles/$NEW_ROLE_ID/permissions" "$ASSIGN_PERMISSIONS_DATA" "分配角色权限"
fi

# ==========================================
# 测试完成
# ==========================================
echo "=========================================="
echo "测试完成！"
echo "=========================================="
echo ""
echo "提示:"
echo "1. 所有需要认证的API都使用了Bearer Token"
echo "2. Token保存在: $TOKEN_FILE"
echo "3. 可以访问 http://127.0.0.1:8000/docs 查看API文档"
echo "4. 可以访问 http://127.0.0.1:8000/redoc 查看ReDoc文档"
echo ""



