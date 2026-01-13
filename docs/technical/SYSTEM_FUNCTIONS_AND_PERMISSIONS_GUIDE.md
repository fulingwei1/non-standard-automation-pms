# 系统功能与权限对应关系完整指南

> 更新日期：2026-01-XX

## 一、系统功能汇总

### 1.1 API端点汇总位置

**主要汇总文件**：`app/api/v1/api.py`

这是系统中所有API端点的注册中心，所有功能模块的路由都在这里注册。

**当前系统包含的功能模块**（共60+个模块）：

1. **项目管理**：projects, milestones, members, stages, project_workspace, project_contributions
2. **客户管理**：customers
3. **供应商管理**：suppliers
4. **设备管理**：machines
5. **物料管理**：materials, bom, material_demands
6. **采购管理**：purchase
7. **销售管理**：sales, presale, business_support, business_support_orders
8. **生产管理**：production, assembly_kit, kit_rate, kit_check
9. **外协管理**：outsourcing
10. **验收管理**：acceptance
11. **ECN管理**：ecn
12. **问题管理**：issues
13. **预警管理**：alerts, shortage_alerts, shortage
14. **进度管理**：progress
15. **任务管理**：task_center
16. **工时管理**：timesheet, work_log
17. **绩效管理**：performance, bonus, project_evaluation
18. **任职资格**：qualification
19. **PMO管理**：pmo, management_rhythm
20. **报表中心**：report_center
21. **数据导入导出**：data_import_export
22. **系统管理**：users, roles, audits
23. **组织管理**：organization
24. **文档管理**：documents
25. **成本管理**：costs, budget
26. **技术规格**：technical_spec, technical_review
27. **工程师管理**：engineers
28. **研发项目**：rd_project
29. **服务管理**：service, installation_dispatch
30. **通知管理**：notifications
31. **工作负荷**：workload
32. **时薪配置**：hourly_rate
33. **调度器**：scheduler
34. **人员匹配**：staff_matching
35. **项目角色**：project_roles
36. **文化墙**：culture_wall, culture_wall_config

### 1.2 API端点统计

- **总模块数**：60+
- **总API端点数**：1400+（通过 `@router.get/post/put/delete` 统计）

### 1.3 查看所有API端点

**方法1：通过FastAPI自动文档**
```
访问：http://localhost:8000/docs
```

**方法2：查看代码**
```bash
# 查看所有路由注册
cat app/api/v1/api.py

# 统计API端点数量
grep -r "@router\.\(get\|post\|put\|delete\)" app/api/v1/endpoints | wc -l
```

---

## 二、权限表结构

### 2.1 数据库表结构

#### permissions 表

```sql
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY,
    permission_code VARCHAR(100) UNIQUE NOT NULL,  -- 权限编码（如 'project:read'）
    permission_name VARCHAR(200) NOT NULL,         -- 权限名称（如 '项目查看权限'）
    module VARCHAR(50),                             -- 所属模块（如 'project'）
    resource VARCHAR(50),                           -- 资源类型（如 'project'）
    action VARCHAR(20),                             -- 操作类型（如 'read', 'write', 'delete'）
    description TEXT,                               -- 权限描述
    is_active BOOLEAN DEFAULT TRUE,                 -- 是否启用
    created_at DATETIME,
    updated_at DATETIME
);
```

#### roles 表

```sql
CREATE TABLE roles (
    id INTEGER PRIMARY KEY,
    role_code VARCHAR(50) UNIQUE NOT NULL,          -- 角色编码（如 'pm'）
    role_name VARCHAR(100) NOT NULL,                -- 角色名称（如 '项目经理'）
    data_scope VARCHAR(20) DEFAULT 'OWN',           -- 数据权限范围（ALL/DEPT/PROJECT/OWN）
    is_system BOOLEAN DEFAULT FALSE,                -- 是否系统预置
    nav_groups JSON,                                -- 导航菜单配置
    ui_config JSON,                                 -- UI配置
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME
);
```

#### role_permissions 表（关联表）

```sql
CREATE TABLE role_permissions (
    id INTEGER PRIMARY KEY,
    role_id INTEGER NOT NULL,                       -- 角色ID
    permission_id INTEGER NOT NULL,                  -- 权限ID
    FOREIGN KEY (role_id) REFERENCES roles(id),
    FOREIGN KEY (permission_id) REFERENCES permissions(id)
);
```

#### user_roles 表（关联表）

```sql
CREATE TABLE user_roles (
    id INTEGER PRIMARY KEY,
    user_id INTEGER NOT NULL,                        -- 用户ID
    role_id INTEGER NOT NULL,                        -- 角色ID
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (role_id) REFERENCES roles(id)
);
```

### 2.2 权限数据来源

权限数据通过**数据库迁移脚本**创建：

**主要迁移文件**：
- `migrations/20250712_permissions_seed_sqlite.sql` - SQLite权限种子数据
- `migrations/20250712_permissions_seed_mysql.sql` - MySQL权限种子数据
- `migrations/20260115_ecn_permissions_sqlite.sql` - ECN模块权限
- `migrations/20260115_ecn_permissions_mysql.sql` - ECN模块权限（MySQL）

**权限创建方式**：
```sql
INSERT INTO permissions (permission_code, permission_name, module, resource, action)
VALUES 
    ('project:read', '项目查看权限', 'project', 'project', 'read'),
    ('project:write', '项目编辑权限', 'project', 'project', 'write'),
    ...
```

---

## 三、功能与权限对应逻辑

### 3.1 完整流程

```
1. 定义功能（API端点）
   ↓
2. 创建权限（数据库迁移脚本）
   ↓
3. 分配权限给角色（role_permissions表）
   ↓
4. 分配角色给用户（user_roles表）
   ↓
5. API端点使用权限检查（require_permission）
   ↓
6. 用户请求 → 检查权限 → 允许/拒绝
```

### 3.2 权限编码规范

**格式**：`{module}:{resource}:{action}`

**示例**：
- `project:read` - 项目查看权限
- `project:write` - 项目编辑权限
- `project:delete` - 项目删除权限
- `material:bom:read` - BOM查看权限
- `ecn:ecn:create` - ECN创建权限

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

### 3.3 API端点与权限的对应

#### 方式1：显式权限检查

```python
# app/api/v1/endpoints/projects.py
@router.get("/projects")
async def list_projects(
    current_user: User = Depends(require_permission("project:read"))
):
    """获取项目列表 - 需要 project:read 权限"""
    ...
```

#### 方式2：模块级权限检查

```python
# app/api/v1/endpoints/purchases.py
@router.get("/purchase-orders")
async def list_purchases(
    current_user: User = Depends(require_procurement_access())
):
    """获取采购订单列表 - 需要采购模块访问权限"""
    ...
```

#### 方式3：无权限检查（公开API）

```python
# app/api/v1/endpoints/auth.py
@router.post("/auth/login")
async def login(...):
    """登录接口 - 无需权限检查"""
    ...
```

---

## 四、权限统计和查询

### 4.1 数据库查询权限

**查询所有权限**：
```sql
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
```

**查询权限使用情况**：
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
WHERE p.permission_code = 'project:read';
```

**查询用户的所有权限**：
```sql
-- 查看某个用户的所有权限
SELECT DISTINCT
    p.permission_code,
    p.permission_name,
    p.module
FROM users u
JOIN user_roles ur ON u.id = ur.user_id
JOIN roles r ON ur.role_id = r.id
JOIN role_permissions rp ON r.id = rp.role_id
JOIN permissions p ON rp.permission_id = p.id
WHERE u.id = 1
ORDER BY p.module, p.permission_code;
```

### 4.2 通过API查询权限

**获取所有权限列表**：
```python
GET /api/v1/roles/permissions
# 返回所有可用权限列表
```

**获取当前用户权限**：
```python
GET /api/v1/auth/me
# 返回用户信息，包含 roles 和 permissions 字段
```

**获取角色权限**：
```python
GET /api/v1/roles/{role_id}
# 返回角色信息，包含 permissions 字段
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
1. API端点列表（模块、方法、路径、权限要求）
2. 数据库权限列表（权限编码、名称、模块、资源、操作）
3. 权限使用情况（哪些API使用了哪些权限）
4. 未使用的权限（数据库中定义但未使用）
5. 未定义的权限（代码中使用但数据库未定义）

---

## 五、新增功能的权限配置流程

### 5.1 完整流程

**步骤1：创建API端点**
```python
# app/api/v1/endpoints/new_module.py
@router.get("/new-module/items")
async def list_items(
    current_user: User = Depends(require_permission("new_module:read"))
):
    """获取新模块列表"""
    ...
```

**步骤2：创建数据库迁移脚本**
```sql
-- migrations/YYYYMMDD_new_module_permissions_sqlite.sql
INSERT INTO permissions (permission_code, permission_name, module, resource, action)
VALUES 
    ('new_module:read', '新模块查看权限', 'new_module', 'item', 'read'),
    ('new_module:write', '新模块编辑权限', 'new_module', 'item', 'write'),
    ('new_module:delete', '新模块删除权限', 'new_module', 'item', 'delete');
```

**步骤3：执行迁移脚本**
```bash
# SQLite
sqlite3 data/app.db < migrations/YYYYMMDD_new_module_permissions_sqlite.sql

# MySQL
mysql -u user -p database < migrations/YYYYMMDD_new_module_permissions_mysql.sql
```

**步骤4：分配权限给角色**
```python
# 通过角色管理页面或API
PUT /api/v1/roles/{role_id}/permissions
{
  "permission_ids": [1, 2, 3, ...]  # 包含新模块的权限ID
}
```

**步骤5：测试权限控制**
- 使用有权限的用户测试 → 应该能访问
- 使用无权限的用户测试 → 应该返回403

---

## 六、权限管理最佳实践

### 6.1 权限命名规范

1. **统一格式**：`{module}:{resource}:{action}`
2. **模块名**：使用小写，单词间用下划线（如 `project`, `material_bom`）
3. **资源名**：使用单数形式（如 `project`, `material`）
4. **操作名**：使用标准操作（`read`, `write`, `create`, `update`, `delete`, `approve`, `submit`）

### 6.2 权限粒度

**建议粒度**：
- **粗粒度**：模块级权限（如 `project:read` 控制整个项目模块）
- **细粒度**：功能级权限（如 `project:milestone:read` 控制里程碑查看）

**当前系统主要使用粗粒度权限**，部分模块使用细粒度权限。

### 6.3 权限文档化

**建议**：
1. 在数据库迁移脚本中创建权限时，添加清晰的注释
2. 在API端点中添加权限要求的文档字符串
3. 定期生成功能权限映射报告
4. 在权限管理页面显示权限的使用情况

---

## 七、权限系统完整逻辑图

```
┌─────────────────────────────────────────────────────────────┐
│                     权限系统完整流程                          │
└─────────────────────────────────────────────────────────────┘

1. 功能定义层
   ├─ API端点定义（app/api/v1/endpoints/*.py）
   ├─ 路由注册（app/api/v1/api.py）
   └─ 权限检查（require_permission / 模块级权限检查）

2. 权限定义层
   ├─ 数据库迁移脚本（migrations/*_permissions*.sql）
   ├─ 权限表（permissions）
   └─ 权限编码规范（module:resource:action）

3. 角色配置层
   ├─ 角色定义（roles表）
   ├─ 权限分配（role_permissions表）
   └─ 数据权限范围（data_scope字段）

4. 用户配置层
   ├─ 用户定义（users表）
   ├─ 角色分配（user_roles表）
   └─ 超级管理员标志（is_superuser）

5. 权限检查层
   ├─ 认证检查（get_current_active_user）
   ├─ 功能权限检查（check_permission）
   └─ 数据权限过滤（filter_projects_by_scope）

6. 数据访问层
   ├─ 功能权限：控制能否访问API
   └─ 数据权限：控制可以看到哪些数据
```

---

## 八、常见问题

### Q1: 如何查看系统有哪些功能？

**A**: 
1. 查看 `app/api/v1/api.py` - 所有路由注册
2. 访问 `/docs` - FastAPI自动文档
3. 运行统计脚本：`python scripts/generate_function_permission_mapping.py`

### Q2: 如何查看系统有哪些权限？

**A**: 
1. 查询数据库：`SELECT * FROM permissions`
2. 通过API：`GET /api/v1/roles/permissions`
3. 查看权限管理页面：`/permission-management`
4. 查看迁移脚本：`migrations/*_permissions*.sql`

### Q3: 如何知道某个功能需要什么权限？

**A**: 
1. 查看API端点代码中的 `require_permission()` 调用
2. 查看API文档（`/docs`）中的权限要求
3. 查看功能权限映射报告

### Q4: 如何知道某个权限被哪些功能使用？

**A**: 
1. 在代码中搜索权限编码：`grep -r "permission_code" app/api/v1/endpoints`
2. 查看功能权限映射报告
3. 查询数据库关联表

### Q5: 新增功能时如何配置权限？

**A**: 参考「五、新增功能的权限配置流程」

---

## 九、相关文档

- [权限系统完整指南](./PERMISSION_SYSTEM_COMPLETE_GUIDE.md)
- [权限机制说明](./PERMISSION_MECHANISM_EXPLANATION.md)
- [数据权限控制指南](./DATA_PERMISSION_CONTROL_GUIDE.md)
- [API快速参考](../API_QUICK_REFERENCE.md)

---

## 十、总结

### 系统功能汇总位置

1. ✅ **API端点注册**：`app/api/v1/api.py` - 所有路由的注册中心
2. ✅ **API文档**：`http://localhost:8000/docs` - FastAPI自动生成的交互式文档
3. ✅ **功能统计脚本**：`scripts/generate_function_permission_mapping.py` - 自动生成功能权限映射报告

### 权限数据来源

1. ✅ **数据库表**：`permissions` 表存储所有权限定义
2. ✅ **迁移脚本**：`migrations/*_permissions*.sql` - 权限的创建脚本
3. ✅ **权限管理页面**：`/permission-management` - 可视化查看和管理权限

### 功能与权限对应逻辑

1. ✅ **API端点** → 通过 `require_permission()` 指定需要的权限
2. ✅ **权限定义** → 在数据库迁移脚本中创建
3. ✅ **权限分配** → 通过 `role_permissions` 表分配给角色
4. ✅ **用户继承** → 通过 `user_roles` 表分配角色给用户
5. ✅ **权限检查** → 在API端点中自动检查用户权限

### 整个逻辑流程

```
功能定义（API） → 权限定义（数据库） → 权限分配（角色） → 角色分配（用户） → 权限检查（运行时）
```
