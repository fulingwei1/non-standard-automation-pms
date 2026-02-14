#!/bin/bash
# 测试权限管理功能

BASE_URL="http://127.0.0.1:8000"

echo "=========================================="
echo "权限管理功能测试"
echo "=========================================="
echo

# 1. 登录获取Token
echo "📝 步骤1: 管理员登录"
echo "----------------------------------------"
LOGIN_RESPONSE=$(curl -s -X POST "$BASE_URL/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123")

TOKEN=$(echo "$LOGIN_RESPONSE" | python3 -c "import json, sys; d=json.load(sys.stdin); print(d.get('access_token', ''))")

if [ -z "$TOKEN" ]; then
    echo "❌ 登录失败"
    echo "$LOGIN_RESPONSE" | python3 -m json.tool
    exit 1
fi

echo "✅ 登录成功, Token: ${TOKEN:0:30}..."
echo

# 2. 测试查询角色列表
echo "📝 步骤2: 查询角色列表"
echo "----------------------------------------"
ROLES_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/api/v1/roles")

echo "$ROLES_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'data' in data and 'items' in data['data']:
        roles = data['data']['items']
        print(f'✅ 获取到 {len(roles)} 个角色')
        for role in roles[:5]:
            print(f\"  - {role.get('role_code')}: {role.get('role_name')}\")
    elif 'code' in data:
        print(f\"⚠️  响应码: {data.get('code')}, 消息: {data.get('message')}\")
        if data.get('code') == 403:
            print('  原因: 管理员无权限访问角色列表（权限数据未初始化）')
    else:
        print('⚠️  响应格式异常')
        print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f'❌ 解析失败: {e}')
" 2>&1
echo

# 3. 测试查询权限列表
echo "📝 步骤3: 查询权限列表"
echo "----------------------------------------"
PERMS_RESPONSE=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/api/v1/roles/permissions")

echo "$PERMS_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'data' in data and isinstance(data['data'], list):
        perms = data['data']
        print(f'✅ 获取到 {len(perms)} 个权限')
        for perm in perms[:5]:
            print(f\"  - {perm.get('perm_code')}: {perm.get('perm_name')}\")
    elif 'code' in data:
        print(f\"⚠️  响应码: {data.get('code')}, 消息: {data.get('message')}\")
    else:
        print('⚠️  响应格式异常')
        print(json.dumps(data, indent=2, ensure_ascii=False))
except Exception as e:
    print(f'❌ 解析失败: {e}')
" 2>&1
echo

# 4. 测试修改用户角色（给pm001添加新角色）
echo "📝 步骤4: 测试修改用户角色"
echo "----------------------------------------"
echo "操作: 给pm001用户分配角色"

# 先获取pm001的用户ID
PM_USER=$(curl -s -H "Authorization: Bearer $TOKEN" \
  "$BASE_URL/api/v1/users?keyword=pm001" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if 'data' in data and 'items' in data['data']:
        users = data['data']['items']
        if users:
            print(users[0].get('id', ''))
except: pass
")

if [ -z "$PM_USER" ]; then
    echo "⚠️  无法获取pm001用户信息（可能无权限）"
else
    echo "  用户ID: $PM_USER"
    
    # 分配角色（角色ID 26 = PM）
    ASSIGN_RESPONSE=$(curl -s -X PUT \
      -H "Authorization: Bearer $TOKEN" \
      -H "Content-Type: application/json" \
      "$BASE_URL/api/v1/users/$PM_USER/roles" \
      -d '{"role_ids": [26]}')
    
    echo "$ASSIGN_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('code') == 200:
        print('✅ 用户角色分配成功')
    else:
        print(f\"⚠️  响应: {data.get('message')}\")
except Exception as e:
    print(f'❌ 解析失败: {e}')
" 2>&1
fi
echo

# 5. 测试修改角色权限
echo "📝 步骤5: 测试修改角色权限"
echo "----------------------------------------"
echo "操作: 更新PM角色的权限"

UPDATE_PERM_RESPONSE=$(curl -s -X PUT \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  "$BASE_URL/api/v1/roles/26/permissions" \
  -d '[1, 2, 3]')  # 权限ID 1,2,3

echo "$UPDATE_PERM_RESPONSE" | python3 -c "
import json, sys
try:
    data = json.load(sys.stdin)
    if data.get('code') == 200:
        print('✅ 角色权限更新成功')
    elif data.get('code') == 403:
        print('⚠️  无权限更新角色权限')
        print(f\"  消息: {data.get('message')}\")
    else:
        print(f\"⚠️  响应: {data.get('code')} - {data.get('message')}\")
except Exception as e:
    print(f'❌ 解析失败: {e}')
" 2>&1
echo

echo "=========================================="
echo "测试总结"
echo "=========================================="
echo "功能1: 修改用户角色 - PUT /api/v1/users/{id}/roles"
echo "功能2: 修改角色权限 - PUT /api/v1/roles/{id}/permissions"
echo
echo "✅ = 功能正常"
echo "⚠️  = 功能存在但可能缺少权限"
echo "❌ = 功能异常"
echo
