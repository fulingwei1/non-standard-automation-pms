# 系统功能与权限完整对应关系

> 更新日期：2026-01-XX

## 一、系统功能汇总位置

### 1.1 API端点注册中心

**文件位置**：`app/api/v1/api.py`

这是系统中**所有API端点的注册中心**，所有功能模块的路由都在这里统一注册。

**当前系统包含的功能模块**（共60+个模块）：

```python
# 主要模块列表
- projects          # 项目管理
- customers         # 客户管理
- suppliers         # 供应商管理
- machines          # 设备管理
- materials         # 物料管理
- bom               # BOM管理
- purchase          # 采购管理
- sales             # 销售管理
- production        # 生产管理
- ecn               # 工程变更
- acceptance        # 验收管理
- outsourcing       # 外协管理
- issues            # 问题管理
- alerts            # 预警管理
- performance       # 绩效管理
- bonus             # 奖金管理
- users             # 用户管理
- roles             # 角色管理
- audits            # 审计管理
... (共60+个模块)
```

### 1.2 API端点统计

- **总模块数**：60+
- **总API端点数**：1400+（通过 `@router.get/post/put/delete` 统计）

### 1.3 查看所有API端点的方法

#### 方法1：FastAPI自动文档（推荐）

```
访问：http://localhost:8000/docs
```

这是最直观的方式，可以看到：
- 所有API端点
- 请求参数
- 响应格式
- 权限要求（如果有）

#### 方法2：查看代码

```bash
# 查看所有路由注册
cat app/api/v1/api.py

# 统计API端点数量
grep -r "@router\.\(get\|post\|put\|delete\)" app/api/v1/endpoints | wc -l
```

#### 方法3：生成功能权限映射报告

```bash
# 运行脚本
python scripts/generate_function_permission_mapping.py

# 查看报告
cat docs/FUNCTION_PERMISSION_MAPPING.md
```

---

## 二、权限数据库统计

### 2.1 权限表结构

**表名**：`permissions`

**字段说明**：

| 字段名 | 类型 | 说明 | 备注 |
|--------|------|------|------|
| `id` | INTEGER | 主键ID | 自增 |
| `permission_code` | VARCHAR(100) | 权限编码 | 唯一，如 'project:read' |
| `permission_name` | VARCHAR(200) | 权限名称 | 如 '项目查看权限' |
| `module` | VARCHAR(50) | 所属模块 | 如 'project' |
| `resource` | VARCHAR(50) | 资源类型 | 如 'project' |
| `action` | VARCHAR(20) | 操作类型 | 如 'read', 'write', 'delete' |
| `description` | TEXT | 权限描述 | 可选 |
| `is_active` | BOOLEAN | 是否启用 | 默认 TRUE |
| `created_at` | DATETIME | 创建时间 | |
| `updated_at` | DATETIME | 更新时间 | |

**⚠️ 注意**：部分旧迁移脚本使用 `perm_code` 和 `perm_name`，但模型定义使用 `permission_code` 和 `permission_name`。实际数据库字段名可能因迁移脚本版本而异。

### 2.2 权限数据来源

权限数据通过**数据库迁移脚本**创建：

**主要迁移文件**：
- `migrations/20250712_permissions_seed_sqlite.sql` - SQLite权限种子数据
- `migrations/20250712_permissions_seed_mysql.sql` - MySQL权限种子数据
- `migrations/20260115_ecn_permissions_sqlite.sql` - ECN模块权限
- `migrations/20260115_ecn_permissions_mysql.sql` - ECN模块权限（MySQL）

**权限创建示例**：
```sql
INSERT INTO permissions (permission_code, permission_name, module, resource, action)
VALUES 
    ('project:read', '项目查看权限', 'project', 'project', 'read'),
    ('project:write', '项目编辑权限', 'project', 'project', 'write'),
    ('ecn:ecn:create', 'ECN创建权限', 'ecn', 'ecn', 'create'),
    ...
```

### 2.3 查询权限数据

#### 通过SQL查询

```sql
-- 查询所有权限
SELECT 
    id,
    permission_code,
    permission_name,
    module,
    resource,
    action,
    is_active
FROM permissions
ORDER BY module, permission_code;

-- 统计权限数量
SELECT 
    module,
    COUNT(*) as permission_count
FROM permissions
GROUP BY module
ORDER BY permission_count DESC;

-- 查询某个模块的所有权限
SELECT * FROM permissions WHERE module = 'project';
```

#### 通过API查询

```python
# 获取所有权限列表
GET /api/v1/roles/permissions

# 获取当前用户权限
GET /api/v1/auth/me
# 返回：{ ..., "permissions": ["project:read", "project:write", ...] }

# 获取角色权限
GET /api/v1/roles/{role_id}
# 返回：{ ..., "permissions": ["project:read", ...] }
```

#### 通过权限管理页面

访问：`/permission-management`

可以：
- 查看所有权限列表
- 按模块筛选
- 查看权限详情
- 查看拥有该权限的角色

---

## 三、功能与权限对应逻辑

### 3.1 完整流程

```
┌─────────────────────────────────────────────────────────────┐
│              功能与权限对应完整流程                            │
└─────────────────────────────────────────────────────────────┘

1. 功能定义（API端点）
   ├─ 在 app/api/v1/endpoints/*.py 中定义
   ├─ 在 app/api/v1/api.py 中注册
   └─ 通过 @router.get/post/put/delete 装饰器定义

2. 权限定义（数据库）
   ├─ 在 migrations/*_permissions*.sql 中创建
   ├─ 插入到 permissions 表
   └─ 权限编码格式：{module}:{resource}:{action}

3. 权限分配（角色）
   ├─ 通过 role_permissions 表关联
   ├─ 一个角色可以有多个权限
   └─ 通过角色管理页面或API分配

4. 角色分配（用户）
   ├─ 通过 user_roles 表关联
   ├─ 一个用户可以有多个角色
   └─ 通过用户管理页面或API分配

5. 权限检查（运行时）
   ├─ API端点使用 require_permission() 检查
   ├─ 系统自动检查用户是否有权限
   └─ 无权限返回 403 Forbidden
```

### 3.2 权限编码规范

**格式**：`{module}:{resource}:{action}`

**示例**：
- `project:read` - 项目查看权限
- `project:write` - 项目编辑权限
- `project:delete` - 项目删除权限
- `material:bom:read` - BOM查看权限
- `ecn:ecn:create` - ECN创建权限
- `system:user:manage` - 用户管理权限

**模块划分**：
- `project` - 项目管理
- `material` - 物料管理
- `purchase` - 采购管理
- `sales` - 销售管理
- `production` - 生产管理
- `ecn` - 工程变更
- `system` - 系统管理
- `performance` - 绩效管理
- ...

### 3.3 API端点与权限的对应方式

#### 方式1：显式权限检查（推荐）

```python
# app/api/v1/endpoints/projects.py
@router.get("/projects")
async def list_projects(
    current_user: User = Depends(require_permission("project:read"))
):
    """
    获取项目列表
    
    权限要求：project:read
    - 如果用户有该权限 → 允许访问
    - 如果用户没有该权限 → 返回403 Forbidden
    """
    ...
```

#### 方式2：模块级权限检查

```python
# app/api/v1/endpoints/purchases.py
@router.get("/purchase-orders")
async def list_purchases(
    current_user: User = Depends(require_procurement_access())
):
    """
    获取采购订单列表
    
    权限要求：采购模块访问权限
    - 检查用户角色是否在采购角色列表中
    """
    ...
```

#### 方式3：无权限检查（公开API）

```python
# app/api/v1/endpoints/auth.py
@router.post("/auth/login")
async def login(...):
    """
    登录接口
    
    无需权限检查（公开API）
    """
    ...
```

---

## 四、权限统计查询

### 4.1 数据库查询

#### 查询所有权限

```sql
SELECT 
    id,
    permission_code,
    permission_name,
    module,
    resource,
    action,
    is_active,
    created_at
FROM permissions
WHERE is_active = TRUE
ORDER BY module, permission_code;
```

#### 按模块统计权限

```sql
SELECT 
    module,
    COUNT(*) as permission_count,
    GROUP_CONCAT(permission_code) as permissions
FROM permissions
WHERE is_active = TRUE
GROUP BY module
ORDER BY permission_count DESC;
```

#### 查询权限使用情况

```sql
-- 查看哪些角色拥有某个权限
SELECT 
    r.role_code,
    r.role_name,
    p.permission_code,
    p.permission_name
FROM roles r
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE p.permission_code = 'project:read'
ORDER BY r.role_code;
```

#### 查询用户的所有权限

```sql
-- 查看某个用户的所有权限
SELECT DISTINCT
    p.permission_code,
    p.permission_name,
    p.module,
    r.role_code,
    r.role_name
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.id = 1
  AND r.is_active = TRUE
  AND p.is_active = TRUE
ORDER BY p.module, p.permission_code;
```

### 4.2 通过API查询

#### 获取所有权限列表

```python
GET /api/v1/roles/permissions
# 返回所有可用权限列表

# 支持模块筛选
GET /api/v1/roles/permissions?module=project
```

#### 获取当前用户权限

```python
GET /api/v1/auth/me
# 返回：
{
  "id": 1,
  "username": "zhangsan",
  "roles": ["项目经理", "PM"],
  "permissions": ["project:read", "project:write", ...],
  ...
}
```

#### 获取角色权限

```python
GET /api/v1/roles/{role_id}
# 返回：
{
  "id": 1,
  "role_code": "pm",
  "role_name": "项目经理",
  "permissions": ["project:read", "project:write", ...],
  ...
}
```

### 4.3 生成功能权限映射报告

系统提供了脚本来自动生成功能与权限的映射关系：

```bash
# 运行脚本
python scripts/generate_function_permission_mapping.py

# 生成报告
docs/FUNCTION_PERMISSION_MAPPING.md
```

**报告内容包括**：
1. **统计概览**：API模块数、端点总数、权限总数等
2. **API端点列表**：模块、方法、路径、权限要求
3. **数据库权限列表**：权限编码、名称、模块、资源、操作
4. **权限使用情况**：哪些API使用了哪些权限
5. **未使用的权限**：数据库中定义但未使用的权限
6. **未定义的权限**：代码中使用但数据库未定义的权限

---

## 五、新增功能的权限配置流程

### 5.1 完整流程

**步骤1：创建API端点**

```python
# app/api/v1/endpoints/new_module.py
from app.core.security import require_permission

@router.get("/new-module/items")
async def list_items(
    current_user: User = Depends(require_permission("new_module:read"))
):
    """获取新模块列表 - 需要 new_module:read 权限"""
    ...
```

**步骤2：注册路由**

```python
# app/api/v1/api.py
from app.api.v1.endpoints import new_module

api_router.include_router(new_module.router, prefix="/new-module", tags=["new-module"])
```

**步骤3：创建数据库迁移脚本**

```sql
-- migrations/YYYYMMDD_new_module_permissions_sqlite.sql
BEGIN;

-- 创建权限
INSERT INTO permissions (permission_code, permission_name, module, resource, action, description)
VALUES 
    ('new_module:read', '新模块查看权限', 'new_module', 'item', 'read', '可以查看新模块列表'),
    ('new_module:write', '新模块编辑权限', 'new_module', 'item', 'write', '可以编辑新模块数据'),
    ('new_module:delete', '新模块删除权限', 'new_module', 'item', 'delete', '可以删除新模块数据');

COMMIT;
```

**步骤4：执行迁移脚本**

```bash
# SQLite
sqlite3 data/app.db < migrations/YYYYMMDD_new_module_permissions_sqlite.sql

# MySQL
mysql -u user -p database < migrations/YYYYMMDD_new_module_permissions_mysql.sql
```

**步骤5：分配权限给角色**

```python
# 通过角色管理页面或API
PUT /api/v1/roles/{role_id}/permissions
{
  "permission_ids": [1, 2, 3, ...]  # 包含新模块的权限ID
}
```

**步骤6：测试权限控制**

- 使用有权限的用户测试 → 应该能访问
- 使用无权限的用户测试 → 应该返回403

---

## 六、权限管理最佳实践

### 6.1 权限命名规范

1. **统一格式**：`{module}:{resource}:{action}`
2. **模块名**：使用小写，单词间用下划线（如 `project`, `material_bom`）
3. **资源名**：使用单数形式（如 `project`, `material`）
4. **操作名**：使用标准操作
   - `read` - 查看
   - `write` / `update` - 编辑
   - `create` - 创建
   - `delete` - 删除
   - `approve` - 审批
   - `submit` - 提交

### 6.2 权限粒度

**当前系统主要使用**：
- **粗粒度权限**：模块级权限（如 `project:read` 控制整个项目模块）
- **细粒度权限**：功能级权限（如 `ecn:ecn:create` 控制ECN创建）

**建议**：
- 对于核心功能，使用细粒度权限
- 对于辅助功能，可以使用粗粒度权限

### 6.3 权限文档化

**建议**：
1. 在数据库迁移脚本中创建权限时，添加清晰的注释
2. 在API端点中添加权限要求的文档字符串
3. 定期生成功能权限映射报告
4. 在权限管理页面显示权限的使用情况

---

## 七、整个逻辑总结

### 7.1 功能汇总位置

1. ✅ **API端点注册**：`app/api/v1/api.py` - 所有路由的注册中心
2. ✅ **API文档**：`http://localhost:8000/docs` - FastAPI自动生成的交互式文档
3. ✅ **功能统计脚本**：`scripts/generate_function_permission_mapping.py` - 自动生成功能权限映射报告

### 7.2 权限数据来源

1. ✅ **数据库表**：`permissions` 表存储所有权限定义
2. ✅ **迁移脚本**：`migrations/*_permissions*.sql` - 权限的创建脚本
3. ✅ **权限管理页面**：`/permission-management` - 可视化查看和管理权限

### 7.3 功能与权限对应逻辑

```
功能定义（API端点）
  ↓
权限定义（数据库迁移脚本）
  ↓
权限分配（role_permissions表）
  ↓
角色分配（user_roles表）
  ↓
权限检查（API端点中的require_permission）
  ↓
用户请求 → 检查权限 → 允许/拒绝
```

### 7.4 数据权限控制

```
角色配置（data_scope字段）
  ↓
用户继承（通过user_roles表）
  ↓
数据权限计算（取最宽松的范围）
  ↓
数据过滤（filter_projects_by_scope）
  ↓
返回过滤后的数据
```

---

## 八、相关文档

- [权限系统完整指南](./PERMISSION_SYSTEM_COMPLETE_GUIDE.md)
- [权限机制说明](./PERMISSION_MECHANISM_EXPLANATION.md)
- [数据权限控制指南](./DATA_PERMISSION_CONTROL_GUIDE.md)
- [功能权限映射报告](./FUNCTION_PERMISSION_MAPPING.md)（运行脚本生成）

---

## 九、总结

### 系统功能汇总

- ✅ **API端点注册中心**：`app/api/v1/api.py`（60+模块，1400+端点）
- ✅ **API文档**：`/docs`（FastAPI自动生成）
- ✅ **功能统计脚本**：自动生成功能权限映射报告

### 权限数据库统计

- ✅ **权限表**：`permissions`（存储所有权限定义）
- ✅ **迁移脚本**：`migrations/*_permissions*.sql`（权限创建脚本）
- ✅ **权限管理页面**：`/permission-management`（可视化查看）

### 功能与权限对应

- ✅ **API端点** → 通过 `require_permission()` 指定需要的权限
- ✅ **权限定义** → 在数据库迁移脚本中创建
- ✅ **权限分配** → 通过 `role_permissions` 表分配给角色
- ✅ **用户继承** → 通过 `user_roles` 表分配角色给用户
- ✅ **权限检查** → 在API端点中自动检查用户权限

### 整个逻辑

```
功能（API） → 权限（数据库） → 角色（分配） → 用户（继承） → 检查（运行时）
```

**数据权限**：通过角色的 `data_scope` 字段控制数据可见范围。
