# 权限系统完整指南

> 更新日期：2026-01-XX

## 一、权限系统架构概览

本系统采用 **RBAC（基于角色的访问控制）** 模型，结合 **数据权限范围** 和 **功能权限** 双重控制机制。

### 1.1 核心组件

```
用户 (User)
  ↓ (多对多)
角色 (Role)
  ↓ (多对多)
权限 (Permission)
```

### 1.2 数据库模型

#### 核心表结构

1. **users** - 用户表
   - `id`: 主键
   - `username`: 用户名（唯一）
   - `employee_id`: 关联员工ID
   - `is_superuser`: 是否超级管理员
   - `is_active`: 是否启用

2. **roles** - 角色表
   - `id`: 主键
   - `role_code`: 角色编码（唯一，如 'pm', 'sales_director'）
   - `role_name`: 角色名称（如 '项目经理', '销售总监'）
   - `data_scope`: 数据权限范围（ALL/DEPT/PROJECT/OWN/CUSTOMER）
   - `nav_groups`: 导航菜单配置（JSON数组）
   - `ui_config`: UI配置（JSON对象）
   - `is_system`: 是否系统预置角色

3. **permissions** - 权限表
   - `id`: 主键
   - `permission_code`: 权限编码（唯一，如 'project:read', 'material:write'）
   - `permission_name`: 权限名称
   - `module`: 所属模块（如 'project', 'material'）
   - `resource`: 资源类型（如 'project', 'material'）
   - `action`: 操作类型（如 'read', 'write', 'delete'）

4. **user_roles** - 用户角色关联表
   - `user_id`: 用户ID
   - `role_id`: 角色ID

5. **role_permissions** - 角色权限关联表
   - `role_id`: 角色ID
   - `permission_id`: 权限ID

6. **permission_audits** - 权限审计表
   - 记录所有权限相关操作的审计日志

### 1.3 数据权限范围（Data Scope）

| 范围 | 说明 | 优先级 | 适用场景 |
|------|------|:------:|----------|
| **ALL** | 全部可见 | 最高 | 管理员、总经理、董事长 |
| **DEPT** | 同部门可见 | 中 | 部门经理、部门成员 |
| **PROJECT** | 参与项目可见 | 中 | 项目经理、项目成员 |
| **OWN** | 自己创建/负责的可见 | 低 | 普通员工、工程师 |
| **CUSTOMER** | 客户门户仅看自身项目 | 特殊 | 客户用户 |

**权限优先级**：用户有多个角色时，取最宽松的权限范围。

---

## 二、后端权限控制

### 2.1 认证机制

#### JWT Token 认证

```python
# 登录流程
POST /api/v1/auth/login
  → 返回 access_token (JWT)

# 后续请求
Authorization: Bearer <access_token>
```

#### Token 管理

- **Token 生成**：`app/core/security.py::create_access_token()`
- **Token 验证**：`app/core/security.py::get_current_user()`
- **Token 撤销**：支持 Redis 黑名单和内存黑名单（降级方案）

### 2.2 权限检查函数

#### 通用权限检查

```python
from app.core.security import check_permission, require_permission

# 检查用户是否有指定权限
has_permission = check_permission(user, "project:read")

# 在API端点中使用权限依赖
@router.get("/projects")
async def list_projects(
    current_user: User = Depends(require_permission("project:read"))
):
    ...
```

#### 模块级权限检查

系统为不同模块提供了专门的权限检查函数：

| 函数 | 说明 | 位置 |
|------|------|------|
| `has_procurement_access()` | 采购和物料管理模块 | `app/core/security.py:267` |
| `has_finance_access()` | 财务管理模块 | `app/core/security.py:355` |
| `has_production_access()` | 生产管理模块 | `app/core/security.py:407` |
| `has_sales_assessment_access()` | 技术评估权限 | `app/core/security.py:499` |
| `has_hr_access()` | 人力资源管理模块 | `app/core/security.py:539` |
| `has_rd_project_access()` | 研发项目访问权限 | `app/core/security.py:598` |
| `check_project_access()` | 项目访问权限（数据权限） | `app/core/security.py:454` |

#### 使用示例

```python
from app.core.security import require_procurement_access

@router.get("/purchases")
async def list_purchases(
    current_user: User = Depends(require_procurement_access())
):
    # 只有有采购权限的用户才能访问
    ...
```

### 2.3 数据权限过滤

#### 数据权限服务

`app/services/data_scope_service.py` 提供数据权限过滤功能：

```python
from app.utils.permission_helpers import filter_projects_by_scope

@router.get("/projects")
def list_projects(
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    query = db.query(Project)
    # 自动根据用户的数据权限范围过滤
    query = filter_projects_by_scope(db, query, current_user)
    return query.all()
```

#### 项目访问权限检查

```python
from app.utils.permission_helpers import check_project_access_or_raise

@router.get("/projects/{project_id}")
def get_project(
    project_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db),
):
    # 检查项目访问权限（如果无权限会自动抛出403异常）
    check_project_access_or_raise(db, current_user, project_id)
    ...
```

### 2.4 权限审计

所有权限相关操作都会记录审计日志：

- 用户创建/更新/角色分配
- 角色创建/更新/权限分配
- 导航菜单配置更新

审计日志存储在 `permission_audits` 表中，可通过 `/api/v1/audits` 查询。

---

## 三、前端权限控制

### 3.1 用户信息获取

#### 登录流程

```javascript
// 1. 用户登录
POST /api/v1/auth/login
  → 返回 { access_token, user }

// 2. 存储到 localStorage
localStorage.setItem('token', access_token)
localStorage.setItem('user', JSON.stringify(user))

// 3. 获取当前用户信息
GET /api/v1/auth/me
  → 返回用户详细信息（包含角色和权限）
```

#### 用户数据结构

```javascript
{
  id: 1,
  username: "zhangsan",
  real_name: "张三",
  role: "pm",  // 主要角色（兼容字段）
  roles: ["项目经理", "PM"],  // 所有角色名称数组
  permissions: ["project:read", "project:write"],  // 权限编码数组
  is_superuser: false,
  department: "项目部",
  ...
}
```

### 3.2 路由保护

#### ProtectedRoute 组件

`frontend/src/components/common/ProtectedRoute.jsx` 提供路由级别的权限控制：

```javascript
import { ProtectedRoute } from '../components/common/ProtectedRoute'
import { hasProcurementAccess } from '../lib/roleConfig'

function ProcurementPage() {
  return (
    <ProtectedRoute
      checkPermission={(role) => hasProcurementAccess(role, isSuperuser)}
      permissionName="采购和物料管理模块"
    >
      {/* 页面内容 */}
    </ProtectedRoute>
  )
}
```

#### 专用保护组件

系统提供了几个专用的保护组件：

- `ProcurementProtectedRoute` - 采购模块保护
- `FinanceProtectedRoute` - 财务模块保护
- `ProductionProtectedRoute` - 生产模块保护
- `ProjectReviewProtectedRoute` - 项目复盘保护

### 3.3 权限检查函数

`frontend/src/lib/roleConfig.js` 提供权限检查函数：

| 函数 | 说明 |
|------|------|
| `hasProcurementAccess(role, isSuperuser)` | 检查采购模块访问权限 |
| `hasFinanceAccess(role, isSuperuser)` | 检查财务模块访问权限 |
| `hasProductionAccess(role, isSuperuser)` | 检查生产模块访问权限 |
| `hasProjectReviewAccess(role, isSuperuser)` | 检查项目复盘权限 |
| `isEngineerRole(role)` | 检查是否是工程师角色 |
| `isManagerRole(role)` | 检查是否是管理层角色 |

#### 权限检查逻辑

```javascript
export function hasProcurementAccess(role, isSuperuser = false) {
  if (isSuperuser) return true;
  
  const allowedRoles = [
    'admin', 'super_admin', 'chairman', 'gm',
    'procurement_manager', 'procurement_engineer', 'procurement', 'buyer',
    'pmc', 'pm', 'project_dept_manager',
    'production_manager', 'manufacturing_director',
    '采购部经理', '采购工程师', '采购专员', '采购员',
    '项目经理', '生产部经理', '制造总监',
  ];
  
  return allowedRoles.includes(role);
}
```

**⚠️ 重要提示**：前端和后端的权限检查逻辑需要保持同步！

### 3.4 导航菜单控制

#### 菜单获取流程

```javascript
// 1. 优先从后端获取动态菜单
GET /api/v1/roles/my/nav-groups
  → 返回 { nav_groups: [...] }

// 2. 如果后端没有配置，使用前端硬编码菜单
// frontend/src/lib/roleConfig.js::getNavForRole(role)
```

#### 菜单配置优先级

1. **后端动态菜单**（`Role.nav_groups`）
   - 存储在数据库 `roles` 表的 `nav_groups` 字段（JSON）
   - 可通过角色管理页面配置
   - 支持多角色菜单合并

2. **前端硬编码菜单**（`roleConfig.js`）
   - 根据角色代码返回预设菜单
   - 作为后备方案

#### Sidebar 组件逻辑

`frontend/src/components/layout/Sidebar.jsx` 的菜单显示逻辑：

```javascript
// 1. 从 localStorage 获取用户信息
const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
const role = currentUser?.role || 'admin'

// 2. 尝试从后端获取动态菜单
useEffect(() => {
  roleApi.getMyNavGroups()
    .then(response => {
      if (response.data.nav_groups?.length > 0) {
        setDynamicNavGroups(response.data.nav_groups)
      }
    })
}, [])

// 3. 确定最终使用的菜单
const navGroups = useMemo(() => {
  // 优先使用后端动态菜单
  if (dynamicNavGroups) {
    return dynamicNavGroups
  }
  
  // 否则使用前端硬编码菜单
  return getNavForRole(role)
}, [dynamicNavGroups, role])
```

#### 菜单项权限过滤

某些菜单项可以配置 `roles` 属性，只对特定角色显示：

```javascript
{
  label: '财务管理',
  items: [
    { name: '财务成本上传', path: '/financial-costs', icon: 'DollarSign' },
  ],
  roles: ['finance', 'accounting', '财务', '会计', 'admin', 'super_admin'],
}
```

---

## 四、前后端权限匹配机制

### 4.1 角色识别

#### 后端角色存储

- 数据库：`users` 表通过 `user_roles` 关联 `roles` 表
- 用户可以有多个角色
- 角色有 `role_code`（英文编码）和 `role_name`（中文名称）

#### 前端角色识别

- 从 `localStorage.getItem('user')` 获取用户信息
- 主要使用 `user.role` 字段（单个角色，兼容字段）
- 或从 `user.roles` 数组获取所有角色

#### 角色映射问题

**问题**：前端和后端可能使用不同的角色标识符

- 后端：`role_code`（如 'pm', 'sales_director'）
- 前端：`role_name`（如 '项目经理', '销售总监'）

**解决方案**：

1. **登录时角色映射**（`frontend/src/pages/Login.jsx`）
   ```javascript
   const roleMap = {
     '系统管理员': 'admin',
     '项目经理': 'pm',
     '销售总监': 'sales_director',
     ...
   }
   ```

2. **前端角色配置**（`frontend/src/lib/roleConfig.js`）
   - 支持中英文角色名称映射
   - `getRoleInfo()` 函数处理角色名称转换

### 4.2 权限检查同步

#### 后端权限检查

```python
# app/core/security.py
def has_procurement_access(user: User) -> bool:
    if user.is_superuser:
        return True
    
    procurement_roles = [
        'procurement_engineer',
        'procurement_manager',
        'procurement',
        'buyer',
        'pmc',
        ...
    ]
    
    for user_role in user.roles:
        role_code = user_role.role.role_code.lower()
        if role_code in procurement_roles:
            return True
    
    return False
```

#### 前端权限检查

```javascript
// frontend/src/lib/roleConfig.js
export function hasProcurementAccess(role, isSuperuser = false) {
  if (isSuperuser) return true;
  
  const allowedRoles = [
    'admin', 'super_admin', 'chairman', 'gm',
    'procurement_manager', 'procurement_engineer', 'procurement', 'buyer',
    'pmc', 'pm', 'project_dept_manager',
    ...
  ];
  
  return allowedRoles.includes(role);
}
```

**⚠️ 同步要求**：

1. 当修改后端权限检查函数时，必须同步更新前端对应函数
2. 当添加新角色时，需要同时更新前后端的角色列表
3. 建议在代码注释中标注同步关系

### 4.3 菜单配置同步

#### 后端菜单配置

- 存储在数据库 `roles.nav_groups` 字段
- 可通过 API 更新：`PUT /api/v1/roles/{role_id}/nav-groups`
- 格式：JSON 数组

#### 前端菜单配置

- 硬编码在 `frontend/src/lib/roleConfig.js::getNavForRole()`
- 格式：JavaScript 对象数组

#### 同步策略

1. **优先使用后端菜单**：如果后端配置了菜单，前端使用后端菜单
2. **前端作为后备**：如果后端没有配置，使用前端硬编码菜单
3. **迁移建议**：逐步将前端硬编码菜单迁移到后端数据库

---

## 五、常见角色和权限配置

### 5.1 系统预置角色

| 角色代码 | 角色名称 | 数据权限 | 主要功能 |
|---------|---------|---------|---------|
| `super_admin` | 超级管理员 | ALL | 系统所有功能 |
| `admin` | 系统管理员 | ALL | 系统管理功能 |
| `chairman` | 董事长 | ALL | 战略决策、全面监控 |
| `gm` | 总经理 | ALL | 经营管理、审批监控 |
| `sales_director` | 销售总监 | DEPT | 销售管理、客户管理 |
| `pm` | 项目经理 | PROJECT | 项目管理、进度跟踪 |
| `pmc` | 项目经理(PMC) | PROJECT | 生产计划、采购跟踪 |
| `procurement_manager` | 采购部经理 | DEPT | 采购管理、供应商管理 |
| `production_manager` | 生产部经理 | DEPT | 生产管理、装配管理 |
| `finance_manager` | 财务经理 | ALL | 财务管理、成本管理 |
| `hr_manager` | 人事经理 | ALL | 人员管理、绩效管理 |

### 5.2 模块权限矩阵

| 模块 | 允许的角色 | 后端检查函数 | 前端检查函数 |
|------|-----------|------------|------------|
| **采购物料** | procurement_*, buyer, pmc, pm, production_* | `has_procurement_access()` | `hasProcurementAccess()` |
| **财务管理** | finance_*, sales_*, business_support, pmc, pm | `has_finance_access()` | `hasFinanceAccess()` |
| **生产管理** | production_*, manufacturing_*, pmc, pm, assembler_* | `has_production_access()` | `hasProductionAccess()` |
| **项目复盘** | project_dept_manager, pmc, pm, tech_dev_manager, *_dept_manager | `has_project_review_access()` | `hasProjectReviewAccess()` |
| **技术评估** | sales_*, presales_*, te, technical_engineer | `has_sales_assessment_access()` | - |
| **人力资源** | hr_manager, gm, chairman, admin | `has_hr_access()` | - |
| **研发项目** | admin, tech_dev_manager, rd_engineer, me_engineer, ee_engineer, ... | `has_rd_project_access()` | - |

### 5.3 数据权限示例

#### 项目列表查询

```python
# 用户A：role_code='pm', data_scope='PROJECT'
# → 只能看到自己参与的项目

# 用户B：role_code='project_dept_manager', data_scope='DEPT'
# → 可以看到同部门的所有项目

# 用户C：role_code='gm', data_scope='ALL'
# → 可以看到所有项目
```

---

## 六、权限系统使用指南

### 6.1 添加新权限

#### 步骤1：在数据库中添加权限记录

```sql
INSERT INTO permissions (permission_code, permission_name, module, resource, action)
VALUES ('new_module:read', '新模块查看权限', 'new_module', 'resource', 'read');
```

#### 步骤2：在角色中分配权限

```python
# 通过 API 或管理界面
PUT /api/v1/roles/{role_id}/permissions
{
  "permission_ids": [1, 2, 3, ...]
}
```

#### 步骤3：在API端点中使用权限检查

```python
from app.core.security import require_permission

@router.get("/new-module/items")
async def list_items(
    current_user: User = Depends(require_permission("new_module:read"))
):
    ...
```

### 6.2 添加新角色

#### 步骤1：创建角色

```python
POST /api/v1/roles/
{
  "role_code": "new_role",
  "role_name": "新角色",
  "data_scope": "OWN",
  "description": "角色描述"
}
```

#### 步骤2：配置导航菜单

```python
PUT /api/v1/roles/{role_id}/nav-groups
[
  {
    "label": "我的工作",
    "items": [
      {"name": "工作台", "path": "/workstation", "icon": "LayoutDashboard"}
    ]
  }
]
```

#### 步骤3：分配权限

```python
PUT /api/v1/roles/{role_id}/permissions
{
  "permission_ids": [1, 2, 3, ...]
}
```

#### 步骤4：更新前端配置（如需要）

```javascript
// frontend/src/lib/roleConfig.js
export const ROLE_INFO = {
  new_role: { name: '新角色', dataScope: 'OWN', level: 5 },
  ...
}

export function getNavForRole(role) {
  const navConfigs = {
    new_role: [
      {
        label: '我的工作',
        items: [
          { name: '工作台', path: '/workstation', icon: 'LayoutDashboard' },
        ],
      },
    ],
    ...
  }
  return navConfigs[role] || navConfigs.dept_manager
}
```

### 6.3 配置角色菜单

#### 通过管理界面

1. 登录系统管理员账号
2. 进入「系统管理」→「角色管理」
3. 选择要配置的角色
4. 编辑「导航菜单配置」
5. 保存

#### 通过 API

```javascript
// 前端调用
await roleApi.updateNavGroups(roleId, [
  {
    label: "概览",
    items: [
      { name: "工作台", path: "/workstation", icon: "LayoutDashboard" },
      { name: "项目看板", path: "/board", icon: "Kanban" },
    ],
  },
])
```

---

## 七、权限系统最佳实践

### 7.1 权限检查原则

1. **后端为主，前端为辅**
   - 所有关键权限检查必须在后端进行
   - 前端权限检查仅用于UI显示控制，不能作为安全依据

2. **最小权限原则**
   - 默认拒绝，明确允许
   - 只授予必要的权限

3. **权限粒度**
   - 模块级权限：控制整个模块的访问
   - 功能级权限：控制具体功能的访问
   - 数据级权限：控制数据的可见范围

### 7.2 前后端同步

1. **角色列表同步**
   - 修改角色时，同时更新前后端配置
   - 在代码注释中标注同步关系

2. **权限检查函数同步**
   - 后端：`app/core/security.py`
   - 前端：`frontend/src/lib/roleConfig.js`
   - 修改时保持逻辑一致

3. **菜单配置迁移**
   - 逐步将前端硬编码菜单迁移到后端数据库
   - 使用后端动态菜单作为主要来源

### 7.3 调试和排查

#### 权限问题排查步骤

1. **检查用户角色**
   ```javascript
   // 前端
   console.log('User roles:', JSON.parse(localStorage.getItem('user')))
   
   // 后端
   GET /api/v1/auth/me
   ```

2. **检查角色权限**
   ```python
   # 后端
   role = db.query(Role).filter(Role.role_code == 'pm').first()
   for rp in role.permissions:
       print(rp.permission.permission_code)
   ```

3. **检查菜单配置**
   ```javascript
   // 前端
   GET /api/v1/roles/my/nav-groups
   ```

4. **查看审计日志**
   ```python
   # 后端
   GET /api/v1/audits?target_type=user&target_id=1
   ```

#### 调试工具

- **前端调试页面**：`/permission-debug`（如果存在）
- **后端日志**：查看 `app/core/security.py` 中的日志输出

---

## 八、常见问题

### Q1: 为什么前端和后端的权限检查逻辑不一致？

**A**: 这是历史遗留问题。建议：
1. 逐步统一前后端权限检查逻辑
2. 在代码注释中标注同步关系
3. 考虑将权限检查逻辑提取到共享配置

### Q2: 如何添加新的模块权限？

**A**: 参考「六、权限系统使用指南」中的「添加新权限」部分。

### Q3: 用户有多个角色时，权限如何合并？

**A**: 
- **功能权限**：取并集（有任一角色有权限即可）
- **数据权限**：取最宽松的范围（ALL > DEPT > PROJECT > OWN）
- **导航菜单**：合并所有角色的菜单项

### Q4: 如何迁移前端硬编码菜单到后端？

**A**: 
1. 通过角色管理界面或API，将菜单配置保存到数据库
2. 前端优先使用后端菜单（已实现）
3. 逐步移除前端硬编码菜单

### Q5: 超级管理员是否绕过所有权限检查？

**A**: 是的。`is_superuser=True` 的用户会绕过所有权限检查，包括：
- 功能权限检查
- 数据权限过滤
- 模块访问限制

---

## 九、相关文档

- [权限功能实现总结](./PERMISSION_IMPLEMENTATION_SUMMARY.md)
- [数据权限和审计实现](./DATA_SCOPE_AND_AUDIT_IMPLEMENTATION.md)
- [采购权限实现](./PROCUREMENT_PERMISSION_IMPLEMENTATION.md)
- [角色配置迁移指南](./ROLE_CONFIG_MIGRATION_GUIDE.md)

---

## 十、总结

本系统的权限控制体系包括：

1. **数据库层**：用户-角色-权限的RBAC模型
2. **后端层**：JWT认证 + 权限检查 + 数据权限过滤
3. **前端层**：路由保护 + 菜单控制 + 权限检查

**关键点**：
- 后端权限检查是安全的基础
- 前端权限检查仅用于UI控制
- 前后端权限逻辑需要保持同步
- 菜单配置优先使用后端动态配置

**改进方向**：
- 统一前后端权限检查逻辑
- 将前端硬编码菜单迁移到后端
- 完善权限审计和日志记录
