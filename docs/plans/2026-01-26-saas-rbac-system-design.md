# SaaS 多租户角色权限系统设计文档

> 创建日期：2026-01-26
> 状态：已确认，待实现

## 一、设计目标

将现有的单租户 RBAC 系统升级为完整的多租户 SaaS 架构：

1. **多租户支持** - 每个租户有独立的用户、角色、权限体系
2. **数据隔离** - 共享数据库 + tenant_id 字段实现数据隔离
3. **角色模板** - 新租户创建时自动复制默认角色，可自行修改
4. **统一编码** - 角色编码统一使用大写格式（如 `PM`、`SALES_DIR`）
5. **修复现有问题** - 补充缺失的 API 端点，移除废弃代码

## 二、数据模型设计

### 2.1 新增表

#### tenants（租户表）

```sql
CREATE TABLE tenants (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tenant_code VARCHAR(50) UNIQUE NOT NULL,     -- 租户编码（唯一标识）
    tenant_name VARCHAR(200) NOT NULL,           -- 租户名称
    status VARCHAR(20) DEFAULT 'ACTIVE',         -- 状态：ACTIVE/SUSPENDED/DELETED
    plan_type VARCHAR(20) DEFAULT 'FREE',        -- 套餐：FREE/STANDARD/ENTERPRISE
    max_users INTEGER DEFAULT 5,                 -- 最大用户数
    max_roles INTEGER DEFAULT 5,                 -- 最大角色数
    settings JSON,                               -- 租户配置（JSON）
    contact_name VARCHAR(100),                   -- 联系人
    contact_email VARCHAR(200),                  -- 联系邮箱
    contact_phone VARCHAR(50),                   -- 联系电话
    expired_at DATETIME,                         -- 过期时间
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

#### role_templates（角色模板表）

```sql
CREATE TABLE role_templates (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    role_code VARCHAR(50) NOT NULL,              -- 角色编码
    role_name VARCHAR(100) NOT NULL,             -- 角色名称
    description TEXT,                            -- 描述
    data_scope VARCHAR(20) DEFAULT 'OWN',        -- 数据权限范围
    nav_groups JSON,                             -- 导航配置
    ui_config JSON,                              -- UI配置
    permission_codes JSON,                       -- 权限编码列表
    sort_order INTEGER DEFAULT 0,                -- 排序
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);
```

### 2.2 修改现有表

#### users 表添加字段

```sql
ALTER TABLE users ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
ALTER TABLE users ADD COLUMN is_tenant_admin BOOLEAN DEFAULT FALSE;
```

#### roles 表添加字段

```sql
ALTER TABLE roles ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
ALTER TABLE roles ADD COLUMN is_template BOOLEAN DEFAULT FALSE;
ALTER TABLE roles ADD COLUMN source_template_id INTEGER REFERENCES role_templates(id);
```

#### permissions 表添加字段（可选，用于租户自定义权限）

```sql
ALTER TABLE permissions ADD COLUMN tenant_id INTEGER REFERENCES tenants(id);
ALTER TABLE permissions ADD COLUMN is_system BOOLEAN DEFAULT TRUE;
```

### 2.3 数据模型关系图

```
┌─────────────────────────────────────────────────────────────┐
│                      tenants                                 │
│  id, tenant_code, tenant_name, status, plan_type, ...       │
└─────────────────────────────────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│    users      │    │    roles      │    │  permissions  │
│ +tenant_id    │    │ +tenant_id    │    │ +tenant_id    │
│ +is_tenant_   │    │ +is_template  │    │ +is_system    │
│   admin       │    │ +source_id    │    │               │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │
        └──────────┬──────────┘
                   ▼
          ┌───────────────┐
          │  user_roles   │
          │ user_id       │
          │ role_id       │
          └───────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   role_templates                             │
│  系统预置角色模板，新租户创建时复制                          │
└─────────────────────────────────────────────────────────────┘
```

## 三、API 端点设计

### 3.1 租户管理 API（平台管理员专用）

| 方法 | 路径 | 说明 |
|------|------|------|
| POST | `/api/v1/tenants/` | 创建租户 |
| GET | `/api/v1/tenants/` | 租户列表 |
| GET | `/api/v1/tenants/{tenant_id}` | 租户详情 |
| PUT | `/api/v1/tenants/{tenant_id}` | 更新租户 |
| DELETE | `/api/v1/tenants/{tenant_id}` | 禁用租户 |
| POST | `/api/v1/tenants/{tenant_id}/init` | 初始化租户数据 |
| GET | `/api/v1/tenants/{tenant_id}/stats` | 租户统计信息 |

### 3.2 角色管理 API（租户管理员）

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/roles/` | 角色列表（自动过滤当前租户） |
| POST | `/api/v1/roles/` | 创建角色 |
| GET | `/api/v1/roles/{role_id}` | 角色详情 |
| PUT | `/api/v1/roles/{role_id}` | 更新角色 |
| DELETE | `/api/v1/roles/{role_id}` | 删除角色 |
| PUT | `/api/v1/roles/{role_id}/permissions` | 分配权限 |
| GET | `/api/v1/roles/{role_id}/nav-groups` | 获取导航配置 |
| PUT | `/api/v1/roles/{role_id}/nav-groups` | 更新导航配置 |
| GET | `/api/v1/roles/templates` | 获取角色模板列表 |
| GET | `/api/v1/roles/config/all` | 获取所有配置 |
| GET | `/api/v1/roles/my/nav-groups` | 获取当前用户导航 |

### 3.3 权限管理 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/permissions/` | 权限列表 |
| GET | `/api/v1/permissions/matrix` | 权限矩阵 |
| GET | `/api/v1/permissions/by-role/{role_id}` | 角色权限列表 |
| GET | `/api/v1/permissions/dependencies` | 权限依赖关系 |

### 3.4 用户管理 API

| 方法 | 路径 | 说明 |
|------|------|------|
| GET | `/api/v1/users/` | 用户列表（自动过滤当前租户） |
| POST | `/api/v1/users/` | 创建用户 |
| PUT | `/api/v1/users/{user_id}/roles` | 分配角色 |
| GET | `/api/v1/auth/me` | 当前用户信息（含权限、租户） |

## 四、租户生命周期

### 4.1 租户创建流程

```
1. 创建租户记录
   └─ POST /api/v1/tenants/
   └─ 生成唯一 tenant_code
   └─ 设置套餐类型、用户上限

2. 初始化租户数据
   └─ POST /api/v1/tenants/{id}/init
   └─ 从 role_templates 复制角色到 roles（设置 tenant_id）
   └─ 创建租户管理员账号（is_tenant_admin=True）
   └─ 分配 TENANT_ADMIN 角色

3. 租户管理员登录
   └─ 获取 JWT Token（含 tenant_id）
   └─ 配置角色、创建用户、管理业务数据
```

### 4.2 套餐限制

| 套餐 | 用户数 | 角色数 | 存储空间 | 功能 |
|------|--------|--------|----------|------|
| FREE | 5 | 5 | 1GB | 基础功能 |
| STANDARD | 50 | 20 | 10GB | 全部功能 |
| ENTERPRISE | 无限 | 无限 | 100GB | 全部功能 + 定制 |

## 五、权限模型

### 5.1 权限编码规范

```
格式: {module}:{resource}:{action}

示例:
- project:list:view      # 查看项目列表
- project:detail:edit    # 编辑项目详情
- role:manage:create     # 创建角色
- user:manage:delete     # 删除用户
- tenant:settings:edit   # 编辑租户设置
```

### 5.2 权限层级

```
┌─────────────────────────────────────────────────────────────┐
│                    平台级权限 (Platform)                     │
│  SUPER_ADMIN 专用：租户管理、平台配置、系统监控              │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    租户级权限 (Tenant)                       │
│  TENANT_ADMIN 专用：用户管理、角色管理、租户设置             │
└─────────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────────┐
│                    业务级权限 (Business)                     │
│  普通用户：项目管理、采购管理、生产管理等业务功能            │
└─────────────────────────────────────────────────────────────┘
```

### 5.3 预置角色模板

| 角色编码 | 角色名称 | 数据权限 | 说明 |
|----------|----------|----------|------|
| TENANT_ADMIN | 租户管理员 | ALL | 租户内最高权限 |
| GM | 总经理 | ALL | 经营管理 |
| PM | 项目经理 | PROJECT | 项目管理 |
| PMC | 计划管理 | PROJECT | 生产计划 |
| SALES_DIR | 销售总监 | DEPARTMENT | 销售管理 |
| SA | 销售专员 | OWN | 销售执行 |
| PU_MGR | 采购主管 | DEPARTMENT | 采购管理 |
| PU | 采购专员 | OWN | 采购执行 |
| ME | 机械工程师 | OWN | 机械设计 |
| EE | 电气工程师 | OWN | 电气设计 |
| QA | 质量工程师 | OWN | 质量管理 |

## 六、实现计划

### Phase 1: 数据模型（优先级：高）

1. 创建 `app/models/tenant.py` - 租户模型
2. 修改 `app/models/user.py` - 添加 tenant_id、is_tenant_admin
3. 修改 `app/models/permission.py` - 添加 tenant_id、is_template
4. 创建数据库迁移脚本

### Phase 2: 后端 API（优先级：高）

1. 创建 `app/api/v1/endpoints/tenants.py` - 租户管理 API
2. 创建 `app/api/v1/endpoints/roles.py` - 角色管理 API（修复缺失端点）
3. 修改 `app/api/v1/api.py` - 注册新路由
4. 创建 `app/services/tenant_service.py` - 租户业务逻辑
5. 创建 `app/schemas/tenant.py` - 租户 Schema

### Phase 3: 中间件（优先级：高）

1. 创建 `app/middleware/tenant.py` - 租户隔离中间件
2. 修改现有查询添加租户过滤

### Phase 4: 修复现有问题（优先级：中）

1. 移除废弃的 `project_roles` 路由注册
2. 注册 `permissions` 模块到主路由
3. 清理重复的角色定义

### Phase 5: 前端适配（优先级：中）

1. 创建 `src/context/TenantContext.jsx` - 租户上下文
2. 修改 `src/lib/roleConfig/` - 统一角色编码格式
3. 修改 `src/config/roleDashboardMap.js` - 清理重复定义
4. 创建租户管理页面

## 七、数据迁移策略

### 7.1 现有数据迁移

1. 创建默认租户（tenant_code='DEFAULT'）
2. 将所有现有用户、角色关联到默认租户
3. 将现有角色复制到 role_templates 作为模板

### 7.2 迁移脚本

```python
def migrate_to_multi_tenant():
    # 1. 创建默认租户
    default_tenant = Tenant(
        tenant_code='DEFAULT',
        tenant_name='默认租户',
        status='ACTIVE',
        plan_type='ENTERPRISE'
    )

    # 2. 更新所有用户
    db.execute("UPDATE users SET tenant_id = :tid", {"tid": default_tenant.id})

    # 3. 更新所有角色
    db.execute("UPDATE roles SET tenant_id = :tid", {"tid": default_tenant.id})

    # 4. 复制角色到模板
    for role in db.query(Role).all():
        template = RoleTemplate(
            role_code=role.role_code,
            role_name=role.role_name,
            ...
        )
        db.add(template)
```

## 八、安全考虑

1. **租户隔离** - 所有查询必须包含 tenant_id 过滤
2. **跨租户访问** - 仅平台管理员可跨租户操作
3. **数据泄露防护** - API 响应不包含其他租户数据
4. **审计日志** - 记录所有敏感操作

## 九、相关文档

- [权限系统完整指南](../technical/PERMISSION_SYSTEM_COMPLETE_GUIDE.md)
- [角色管理UI设计](./2026-01-21-role-management-ui-design.md)
