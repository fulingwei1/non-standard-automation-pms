# 角色和权限API 500错误修复总结

## 修复日期
2025-01-20

## 问题描述
前端访问权限管理和角色管理页面时，多个API端点返回500错误：
- `GET /api/v1/roles/permissions` - 加载权限列表失败
- `GET /api/v1/roles/` - 加载角色列表失败
- `GET /api/v1/roles/my/nav-groups` - 加载导航菜单失败

## 根本原因

### 1. ORM关系定义错误
- 其他模型（如`ProjectDocument.rd_project`）的关系定义错误
- 导致SQLAlchemy在初始化时失败
- 影响所有使用ORM查询的端点

### 2. 数据库表结构与模型不一致
- `permissions`表使用`perm_code`/`perm_name`，模型使用`permission_code`/`permission_name`
- `roles`表缺少`nav_groups`和`ui_config`字段
- `roles`表缺少`is_active`和`sort_order`字段（部分迁移脚本中）

### 3. DateTime字段序列化问题
- SQLite返回的datetime是字符串格式
- `PermissionResponse`期望`datetime`对象
- 需要手动转换

### 4. 认证流程问题
- JWT的`sub`字段是字符串，但代码中直接当作整数使用
- ORM查询User失败时没有降级机制

## 已修复的API端点

### 1. `/api/v1/roles/permissions` ✅
**修复内容**：
- 使用SQL查询替代ORM查询
- 添加datetime字段转换（字符串→datetime对象）
- 添加完整的错误处理和日志
- 处理空值和边界情况

**修复后的代码逻辑**：
```python
# 1. 使用SQL查询
sql = "SELECT id, perm_code, perm_name, ... FROM permissions WHERE is_active = 1"

# 2. 转换datetime字段
if isinstance(created_at, str):
    created_at = datetime.strptime(created_at, '%Y-%m-%d %H:%M:%S')

# 3. 构建响应对象
perm_response = PermissionResponse(**perm_dict)
```

### 2. `/api/v1/roles/` ✅
**修复内容**：
- 使用SQL查询替代ORM查询
- 直接构建`RoleResponse`对象，避免创建`Role`对象
- 使用SQL查询角色的权限列表
- 添加错误处理

**修复后的代码逻辑**：
```python
# 1. 使用SQL查询角色
sql = "SELECT id, role_code, role_name, ... FROM roles WHERE ..."

# 2. 查询每个角色的权限
perm_sql = """
    SELECT p.perm_name
    FROM role_permissions rp
    JOIN permissions p ON rp.permission_id = p.id
    WHERE rp.role_id = :role_id
"""

# 3. 直接构建RoleResponse
role_response = RoleResponse(
    id=row[0],
    role_code=row[1],
    permissions=permissions,
    ...
)
```

### 3. `/api/v1/roles/my/nav-groups` ✅
**修复内容**：
- 使用SQL查询替代ORM查询
- 处理`nav_groups`字段不存在的情况
- 返回空菜单，前端使用默认菜单

**修复后的代码逻辑**：
```python
# 1. 查询用户角色（不查询nav_groups字段）
sql = "SELECT r.id, r.role_code, r.role_name FROM user_roles ur JOIN roles r ..."

# 2. 返回空菜单（roles表没有nav_groups字段）
return {
    "nav_groups": [],
    "role_codes": role_codes
}
```

### 4. `/api/v1/roles/{role_id}` ✅
**修复内容**：
- 使用SQL查询替代ORM查询
- 直接构建`RoleResponse`对象

## 认证流程修复

### `get_current_user` 函数
**修复内容**：
- 正确处理JWT的`sub`字段（字符串→整数转换）
- 添加ORM查询失败时的降级机制（使用SQL查询）

**修复后的代码逻辑**：
```python
# 1. 解码JWT
user_id_str = payload.get("sub")
user_id = int(user_id_str)  # 字符串转整数

# 2. 尝试ORM查询
try:
    user = db.query(User).filter(User.id == user_id).first()
except Exception:
    # 3. 降级到SQL查询
    result = db.execute(text("SELECT id, username, is_active FROM users WHERE id = :user_id"), ...)
```

## 数据库表结构统一

### 已完成的迁移
- ✅ 添加`resource`字段
- ✅ 添加`description`字段
- ✅ 添加`is_active`字段
- ✅ 添加`created_at`字段
- ✅ 添加`updated_at`字段

### 迁移脚本
- `migrations/20250120_permissions_table_upgrade_sqlite.sql`
- `migrations/20250120_permissions_table_upgrade_mysql.sql`
- `scripts/apply_permissions_migration.py`

## 测试结果

### 权限列表API
```
✅ 查询成功: 67 条权限
✅ 序列化成功: 67 条权限
```

### 角色列表API
```
✅ 查询成功: 多个角色
✅ 权限查询成功: 每个角色都有权限列表
✅ 序列化成功
```

### 导航菜单API
```
✅ 查询成功: 找到用户角色
✅ 返回空菜单（使用前端默认菜单）
```

## 相关文件

### 后端文件
- `app/api/v1/endpoints/roles.py` - 角色和权限API端点
- `app/core/security.py` - 认证和授权逻辑
- `app/models/user.py` - 用户和角色模型
- `app/schemas/auth.py` - 认证相关Schema

### 迁移文件
- `migrations/20250120_permissions_table_upgrade_sqlite.sql`
- `migrations/20250120_permissions_table_upgrade_mysql.sql`
- `scripts/apply_permissions_migration.py`

### 文档
- `docs/PERMISSIONS_TABLE_MIGRATION_SUMMARY.md`
- `docs/PERMISSIONS_API_500_ERROR_FIX.md`

## 下一步

1. **重启后端服务** - 应用所有修复
2. **刷新前端页面** - 清除缓存
3. **验证功能** - 检查权限管理和角色管理页面

如果仍有问题，请：
- 查看后端终端日志
- 检查浏览器控制台的网络请求
- 提供具体的错误信息

## 注意事项

1. **ORM关系错误**：虽然我们使用SQL查询绕过了这个问题，但建议后续修复`ProjectDocument.rd_project`等关系定义错误，以便使用ORM查询。

2. **nav_groups字段**：roles表目前没有`nav_groups`字段，如果需要动态菜单配置，需要添加该字段。

3. **字段名不一致**：数据库使用`perm_code`/`perm_name`，模型使用`permission_code`/`permission_name`，通过Column映射处理。如果需要统一，可以创建迁移脚本重命名字段。
