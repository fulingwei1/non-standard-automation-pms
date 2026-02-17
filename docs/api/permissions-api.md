# 权限管理 API 文档

## 概述

权限管理 API 提供完整的权限 CRUD 操作、角色权限关联和用户权限查询功能，支持多租户数据隔离。

## 基础信息

- **基础路径**: `/api/v1/permissions/`
- **认证方式**: Bearer Token
- **权限要求**: 需要相应的 `permission:*` 或 `role:*` 或 `user:*` 权限

## API 端点列表

### 1. 权限 CRUD

#### 1.1 获取权限列表
```http
GET /permissions/
```

**查询参数**:
- `page` (int, 可选): 页码，默认 1
- `page_size` (int, 可选): 每页条数，默认 20
- `module` (string, 可选): 按模块筛选
- `action` (string, 可选): 按操作类型筛选
- `keyword` (string, 可选): 关键词搜索
- `is_active` (bool, 可选): 是否启用

**权限要求**: `permission:read`

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "items": [
      {
        "id": 1,
        "permission_code": "project:create",
        "permission_name": "创建项目",
        "module": "project",
        "action": "CREATE",
        "description": "项目创建权限",
        "is_active": true,
        "is_system": false,
        "tenant_id": 1
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20,
    "pages": 3
  }
}
```

#### 1.2 获取模块列表
```http
GET /permissions/modules
```

**权限要求**: `permission:read`

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": ["project", "user", "role", "system"]
}
```

#### 1.3 获取权限详情
```http
GET /permissions/{permission_id}
```

**权限要求**: `permission:read`

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "id": 1,
    "permission_code": "project:create",
    "permission_name": "创建项目",
    "module": "project",
    "action": "CREATE",
    "description": "项目创建权限",
    "is_active": true,
    "is_system": false,
    "tenant_id": 1,
    "created_at": "2026-01-01T00:00:00",
    "updated_at": "2026-01-01T00:00:00"
  }
}
```

#### 1.4 创建权限
```http
POST /permissions/
```

**查询参数**:
- `perm_code` (string, 必填): 权限编码
- `perm_name` (string, 必填): 权限名称
- `module` (string, 可选): 所属模块
- `page_code` (string, 可选): 所属页面
- `action` (string, 可选): 操作类型
- `description` (string, 可选): 权限描述
- `permission_type` (string, 可选): 权限类型，默认 "API"

**权限要求**: `permission:create`

**响应示例**:
```json
{
  "code": 201,
  "message": "创建成功",
  "data": {
    "id": 1,
    "permission_code": "project:create",
    "permission_name": "创建项目",
    "module": "project"
  }
}
```

#### 1.5 更新权限
```http
PUT /permissions/{permission_id}
```

**查询参数**:
- `perm_name` (string, 可选): 权限名称
- `module` (string, 可选): 所属模块
- `page_code` (string, 可选): 所属页面
- `action` (string, 可选): 操作类型
- `description` (string, 可选): 权限描述
- `is_active` (bool, 可选): 是否启用

**权限要求**: `permission:update`

**注意**: 系统预置权限不允许修改

#### 1.6 删除权限
```http
DELETE /permissions/{permission_id}
```

**权限要求**: `permission:delete`

**注意**: 
- 系统预置权限不允许删除
- 被角色使用的权限不允许删除

### 2. 角色权限关联

#### 2.1 获取角色权限
```http
GET /permissions/roles/{role_id}
```

**权限要求**: `role:read`

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "role_id": 1,
    "role_code": "PROJECT_MANAGER",
    "role_name": "项目经理",
    "permissions": [
      {
        "id": 1,
        "permission_code": "project:create",
        "permission_name": "创建项目",
        "module": "project",
        "action": "CREATE"
      }
    ]
  }
}
```

#### 2.2 分配角色权限
```http
POST /permissions/roles/{role_id}
```

**查询参数**:
- `permission_ids` (array[int], 必填): 权限ID列表

**权限要求**: `role:update`

**功能**: 覆盖式更新角色权限（删除旧的，添加新的）

**响应示例**:
```json
{
  "code": 200,
  "message": "权限分配成功，共分配 5 个权限",
  "data": {
    "role_id": 1,
    "assigned_count": 5
  }
}
```

### 3. 用户权限查询

#### 3.1 获取用户权限
```http
GET /permissions/users/{user_id}
```

**权限要求**: `user:read`

**功能**: 获取用户通过角色继承的所有权限

**响应示例**:
```json
{
  "code": 200,
  "message": "获取成功",
  "data": {
    "user_id": 1,
    "username": "zhangsan",
    "real_name": "张三",
    "permissions": [
      {
        "id": 1,
        "permission_code": "project:create",
        "permission_name": "创建项目",
        "module": "project",
        "action": "CREATE"
      }
    ],
    "permission_count": 10
  }
}
```

#### 3.2 检查用户权限
```http
GET /permissions/users/{user_id}/check
```

**查询参数**:
- `permission_code` (string, 必填): 权限编码

**权限要求**: `user:read`

**响应示例**:
```json
{
  "code": 200,
  "message": "检查完成",
  "data": {
    "user_id": 1,
    "permission_code": "project:create",
    "has_permission": true
  }
}
```

## 多租户隔离

### 权限可见性规则

1. **系统级权限** (`tenant_id = NULL`):
   - 所有租户可见
   - 只能由超级管理员创建
   - 不允许修改和删除

2. **租户级权限** (`tenant_id = N`):
   - 仅该租户可见
   - 租户管理员可以创建
   - 可以修改和删除（如果未被使用）

### 数据隔离

- 权限列表查询自动过滤：只返回系统级 + 当前租户级权限
- 权限详情查询：只能查看可访问的权限
- 权限删除：只能删除自己租户的权限

## 错误码

| HTTP 状态码 | 错误说明 |
|------------|---------|
| 400 | 请求参数错误、权限编码重复、系统权限受保护、权限被使用 |
| 401 | 未授权（需要登录） |
| 403 | 权限不足、跨租户访问被拒绝 |
| 404 | 权限不存在、角色不存在、用户不存在 |

## 使用示例

### 创建自定义权限

```bash
curl -X POST "http://localhost:8000/api/v1/permissions/" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "perm_code=custom:export" \
  -d "perm_name=导出数据" \
  -d "module=custom" \
  -d "action=EXPORT" \
  -d "description=自定义导出权限"
```

### 为角色分配权限

```bash
curl -X POST "http://localhost:8000/api/v1/permissions/roles/1" \
  -H "Authorization: Bearer YOUR_TOKEN" \
  -d "permission_ids=1" \
  -d "permission_ids=2" \
  -d "permission_ids=3"
```

### 检查用户权限

```bash
curl "http://localhost:8000/api/v1/permissions/users/1/check?permission_code=project:create" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

## 性能优化

### 缓存机制

- 用户权限查询使用 Redis 缓存（TTL: 10分钟）
- 角色权限更新时自动清除相关缓存
- 支持分布式缓存失效

### 最佳实践

1. **批量权限检查**: 使用 `get_user_permissions` 一次获取所有权限，前端缓存
2. **权限预加载**: 登录时加载用户权限，避免频繁查询
3. **角色继承**: 充分利用角色继承机制，减少重复分配

## 相关文档

- [角色管理 API](./roles-api.md)
- [用户管理 API](./users-api.md)
- [权限设计文档](../design/permission-design.md)
