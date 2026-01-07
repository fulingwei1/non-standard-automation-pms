# 用户认证与权限 API 测试指南

本文档提供了完整的API测试方法，包括使用curl命令和Postman两种方式。

## 前置条件

1. **启动服务器**
```bash
cd 非标自动化项目管理系统
uvicorn app.main:app --reload --host 127.0.0.1 --port 8000
```

2. **初始化数据库（如果还没有用户）**
```bash
python3 init_db.py
```

3. **检查服务器状态**
```bash
curl http://127.0.0.1:8000/health
```

## 快速测试脚本

运行自动化测试脚本：
```bash
bash test_auth_apis.sh
```

## 手动测试（curl命令）

### 1. 认证相关 API

#### 1.1 用户登录
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123"
```

**响应示例：**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 86400
}
```

**保存Token：**
```bash
TOKEN=$(curl -s -X POST "http://127.0.0.1:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=admin&password=admin123" | \
  python3 -c "import sys, json; print(json.load(sys.stdin)['access_token'])")

echo $TOKEN
```

#### 1.2 获取当前用户信息
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/auth/me" \
  -H "Authorization: Bearer $TOKEN"
```

#### 1.3 刷新Token
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/refresh" \
  -H "Authorization: Bearer $TOKEN"
```

#### 1.4 修改密码
```bash
curl -X PUT "http://127.0.0.1:8000/api/v1/auth/password" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "old_password": "admin123",
    "new_password": "newpassword123"
  }'
```

#### 1.5 用户登出
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/auth/logout" \
  -H "Authorization: Bearer $TOKEN"
```

### 2. 用户管理 API

#### 2.1 获取用户列表（分页）
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/users?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.2 搜索用户（关键词）
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/users?keyword=admin&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.3 筛选用户（部门）
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/users?department=技术部&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.4 筛选用户（启用状态）
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/users?is_active=true&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.5 创建用户
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/users" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "password": "test123456",
    "email": "test@example.com",
    "real_name": "测试用户",
    "employee_no": "EMP001",
    "department": "测试部门",
    "position": "测试职位",
    "role_ids": []
  }'
```

#### 2.6 获取用户详情
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/users/1" \
  -H "Authorization: Bearer $TOKEN"
```

#### 2.7 更新用户
```bash
curl -X PUT "http://127.0.0.1:8000/api/v1/users/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "real_name": "更新后的姓名",
    "department": "新部门",
    "is_active": true
  }'
```

#### 2.8 分配用户角色
```bash
curl -X PUT "http://127.0.0.1:8000/api/v1/users/1/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[1, 2]'
```

### 3. 角色管理 API

#### 3.1 获取角色列表（分页）
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/roles?page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

#### 3.2 搜索角色（关键词）
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/roles?keyword=admin&page=1&page_size=10" \
  -H "Authorization: Bearer $TOKEN"
```

#### 3.3 获取权限列表
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/roles/permissions" \
  -H "Authorization: Bearer $TOKEN"
```

#### 3.4 创建角色
```bash
curl -X POST "http://127.0.0.1:8000/api/v1/roles" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role_code": "TEST_ROLE",
    "role_name": "测试角色",
    "description": "这是一个测试角色",
    "data_scope": "OWN",
    "permission_ids": []
  }'
```

#### 3.5 获取角色详情
```bash
curl -X GET "http://127.0.0.1:8000/api/v1/roles/1" \
  -H "Authorization: Bearer $TOKEN"
```

#### 3.6 更新角色
```bash
curl -X PUT "http://127.0.0.1:8000/api/v1/roles/1" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "role_name": "更新后的角色名",
    "description": "更新后的描述"
  }'
```

#### 3.7 分配角色权限
```bash
curl -X PUT "http://127.0.0.1:8000/api/v1/roles/1/permissions" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '[1, 2, 3]'
```

## Postman 测试

### 导入环境变量

1. 创建新的Environment，设置以下变量：
   - `base_url`: `http://127.0.0.1:8000/api/v1`
   - `token`: (登录后自动设置)

2. 创建Pre-request Script（用于自动设置Token）：
```javascript
// 如果token存在，自动添加到请求头
if (pm.environment.get("token")) {
    pm.request.headers.add({
        key: "Authorization",
        value: "Bearer " + pm.environment.get("token")
    });
}
```

### 测试集合结构

#### 1. 认证 (Auth)
- **登录** - POST `{{base_url}}/auth/login`
  - Body (x-www-form-urlencoded):
    - username: admin
    - password: admin123
  - Tests (保存Token):
    ```javascript
    var jsonData = pm.response.json();
    pm.environment.set("token", jsonData.access_token);
    ```

- **获取当前用户** - GET `{{base_url}}/auth/me`
- **刷新Token** - POST `{{base_url}}/auth/refresh`
- **修改密码** - PUT `{{base_url}}/auth/password`
- **登出** - POST `{{base_url}}/auth/logout`

#### 2. 用户管理 (Users)
- **用户列表** - GET `{{base_url}}/users?page=1&page_size=10`
- **搜索用户** - GET `{{base_url}}/users?keyword=admin`
- **创建用户** - POST `{{base_url}}/users`
- **用户详情** - GET `{{base_url}}/users/{id}`
- **更新用户** - PUT `{{base_url}}/users/{id}`
- **分配角色** - PUT `{{base_url}}/users/{id}/roles`

#### 3. 角色管理 (Roles)
- **角色列表** - GET `{{base_url}}/roles?page=1&page_size=10`
- **权限列表** - GET `{{base_url}}/roles/permissions`
- **创建角色** - POST `{{base_url}}/roles`
- **角色详情** - GET `{{base_url}}/roles/{id}`
- **更新角色** - PUT `{{base_url}}/roles/{id}`
- **分配权限** - PUT `{{base_url}}/roles/{id}/permissions`

## 预期响应格式

### 成功响应
```json
{
  "code": 200,
  "message": "success",
  "data": { ... }
}
```

### 分页响应
```json
{
  "items": [...],
  "total": 100,
  "page": 1,
  "page_size": 20,
  "pages": 5
}
```

### 错误响应
```json
{
  "detail": "错误信息"
}
```

## 常见问题

### 1. 401 Unauthorized
- 检查Token是否过期
- 检查Token是否正确设置
- 重新登录获取新Token

### 2. 403 Forbidden
- 检查用户是否有相应权限
- 确认用户角色已正确分配

### 3. 404 Not Found
- 检查URL路径是否正确
- 检查资源ID是否存在

### 4. 422 Validation Error
- 检查请求体格式是否正确
- 检查必填字段是否提供
- 检查字段类型和格式

## API文档

访问以下地址查看完整的API文档：
- Swagger UI: http://127.0.0.1:8000/docs
- ReDoc: http://127.0.0.1:8000/redoc



