# 多租户架构总览

> 非标自动化测试设备项目管理系统 — 多租户架构设计文档  
> 版本: 1.0 | 更新时间: 2026-02-17 | 负责团队: Multi-Tenant Architecture Group

---

## 目录

1. [架构概述](#1-架构概述)
2. [数据隔离策略](#2-数据隔离策略)
3. [租户识别方式](#3-租户识别方式)
4. [超级管理员](#4-超级管理员)
5. [租户初始化流程](#5-租户初始化流程)
6. [核心组件说明](#6-核心组件说明)
7. [技术栈](#7-技术栈)

---

## 1. 架构概述

### 1.1 为什么需要多租户

非标自动化测试设备项目管理系统服务于**多家工厂/子公司**，不同客户的项目数据、人员、权限需要严格隔离。具体场景包括：

| 场景 | 说明 |
|------|------|
| 集团下属工厂 | A工厂不能看到B工厂的项目进度和报价数据 |
| 独立子公司 | 各子公司拥有独立的管理员和角色权限体系 |
| SaaS 服务 | 同一套部署，服务多个付费客户，数据物理共享、逻辑隔离 |

### 1.2 多租户模型选择

系统采用 **共享数据库 + 行级数据隔离（Shared Database, Separate Rows）** 模型：

```
┌─────────────────────────────────────────────────────────────┐
│                      同一个数据库实例                         │
│                                                             │
│  ┌──────────────────┐   ┌──────────────────┐               │
│  │  tenant_id = 1   │   │  tenant_id = 2   │               │
│  │  上海工厂         │   │  苏州工厂         │               │
│  │  users, projects │   │  users, projects │               │
│  └──────────────────┘   └──────────────────┘               │
│                                                             │
│  ┌──────────────────┐   ┌──────────────────┐               │
│  │  tenant_id = 3   │   │  tenant_id = NULL│               │
│  │  北京研发中心      │   │  超级管理员专区    │               │
│  └──────────────────┘   └──────────────────┘               │
└─────────────────────────────────────────────────────────────┘
```

**优势：**
- 部署简单，单一数据库实例
- 成本低，资源共享
- 易于维护和升级
- 适合当前业务规模

### 1.3 整体架构分层

```
┌─────────────────────────────────────────────────────────┐
│                    API Endpoint Layer                   │
│  @require_tenant_isolation / @allow_cross_tenant        │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│              Middleware Layer（租户上下文）               │
│  GlobalAuthMiddleware → TenantContextMiddleware         │
│  解析 JWT → 提取 tenant_id → 存入 ContextVar            │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│               Database Query Layer                      │
│  TenantQuery（继承 SQLAlchemy Query）                   │
│  自动拦截查询 → WHERE tenant_id = ?                     │
└────────────────────┬────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────┐
│            Permission Check Layer                       │
│  check_tenant_access() → 验证跨租户资源访问              │
└─────────────────────────────────────────────────────────┘
```

---

## 2. 数据隔离策略

### 2.1 行级租户过滤

每张业务表都包含 `tenant_id` 字段，作为数据归属标记：

```sql
-- 示例：项目表结构
CREATE TABLE projects (
    id          INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id   INT NOT NULL,           -- 租户标识
    name        VARCHAR(200) NOT NULL,
    status      VARCHAR(20),
    created_at  DATETIME,
    -- ... 其他业务字段
    INDEX idx_tenant_id (tenant_id),    -- 必须建索引
    FOREIGN KEY (tenant_id) REFERENCES tenants(id)
);
```

### 2.2 自动过滤机制（TenantQuery）

系统使用自定义 `TenantQuery` 类（继承 SQLAlchemy `Query`），在查询执行前自动添加 `tenant_id` 过滤：

```python
# app/core/database/tenant_query.py

class TenantQuery(Query):
    """自动添加租户过滤的 Query 类"""

    def __iter__(self):
        """在查询执行前自动注入租户条件"""
        if getattr(self, '_skip_tenant_filter', False):
            return super().__iter__()
        return self._apply_tenant_filter().__iter__()

    def _apply_tenant_filter(self):
        tenant_id = get_current_tenant_id()
        model = self.column_descriptions[0].get('type')

        # 模型没有 tenant_id 字段（系统级表），不过滤
        if not hasattr(model, 'tenant_id'):
            return self

        # 超级管理员（tenant_id=None + is_superuser=True），不过滤
        if tenant_id is None:
            return self

        # 普通租户用户，自动添加过滤
        return self.filter(model.tenant_id == tenant_id)
```

**效果：** 开发者写 `db.query(Project).all()`，实际执行的 SQL 是：
```sql
SELECT * FROM projects WHERE tenant_id = 1;
```

### 2.3 涉及的数据表范围

全系统共 **473 张业务表** 均包含 `tenant_id` 字段，涵盖：

- 项目管理（projects, tasks, milestones）
- 人员管理（users, roles, permissions）
- 销售售前（quotations, contracts, presale_solutions）
- 生产管理（production_orders, work_orders）
- 采购库存（purchase_orders, inventory）
- 财务成本（cost_items, budgets）
- 质量管理（quality_inspections, defect_records）

---

## 3. 租户识别方式

### 3.1 JWT Token 携带租户信息

用户登录后，系统签发包含 `tenant_id` 的 JWT Token：

```python
# app/core/auth.py - 生成 Token
def create_access_token(user: User) -> str:
    payload = {
        "sub": str(user.id),           # 用户ID
        "tenant_id": user.tenant_id,   # 租户ID（超级管理员为 null）
        "is_superuser": user.is_superuser,
        "exp": datetime.utcnow() + timedelta(hours=8),
        "jti": secrets.token_hex(16),  # Token 唯一标识（用于吊销）
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm="HS256")
```

### 3.2 中间件提取租户上下文

```python
# app/core/middleware/tenant_middleware.py

class TenantContextMiddleware(BaseHTTPMiddleware):
    """从已认证用户提取 tenant_id，存入请求上下文"""

    async def dispatch(self, request: Request, call_next):
        try:
            user = getattr(request.state, "user", None)
            if user:
                tenant_id = getattr(user, "tenant_id", None)
                request.state.tenant_id = tenant_id
                set_current_tenant_id(tenant_id)  # 存入 ContextVar
            response = await call_next(request)
            return response
        finally:
            set_current_tenant_id(None)  # 清理上下文，防止泄露
```

### 3.3 请求全生命周期的租户上下文

```
HTTP Request
    │
    ▼ GlobalAuthMiddleware
    │  解析 Authorization: Bearer <token>
    │  → request.state.user = User(id=42, tenant_id=1)
    │
    ▼ TenantContextMiddleware
    │  → ContextVar[tenant_id] = 1
    │
    ▼ API Handler
    │  current_user.tenant_id == 1
    │
    ▼ db.query(Project).all()
    │  TenantQuery 自动添加 WHERE tenant_id = 1
    │
    ▼ Response（仅返回 tenant_id=1 的数据）
```

### 3.4 上下文变量实现（线程安全）

```python
# 使用 Python contextvars 模块，天然支持 asyncio 并发
_current_tenant_id: ContextVar[Optional[int]] = ContextVar(
    "current_tenant_id", default=None
)

def get_current_tenant_id() -> Optional[int]:
    return _current_tenant_id.get()

def set_current_tenant_id(tenant_id: Optional[int]) -> None:
    _current_tenant_id.set(tenant_id)
```

---

## 4. 超级管理员

### 4.1 超级管理员定义

超级管理员必须**同时满足**以下两个条件：

```python
# app/core/auth.py
def is_superuser(user: User) -> bool:
    """
    超级管理员判断标准：
    1. is_superuser = True
    2. tenant_id IS NULL（不属于任何租户）
    """
    return bool(user.is_superuser and user.tenant_id is None)
```

| 用户类型 | is_superuser | tenant_id | 说明 |
|---------|-------------|-----------|------|
| 超级管理员 | TRUE | NULL | ✅ 合法 |
| 租户普通用户 | FALSE | 非NULL | ✅ 合法 |
| ❌ 非法状态 | TRUE | 非NULL | 超级管理员不能属于租户 |
| ❌ 非法状态 | FALSE | NULL | 普通用户必须属于租户 |

### 4.2 超级管理员的数据权限

```python
# 超级管理员可以访问所有租户数据
# TenantQuery._apply_tenant_filter() 中的处理：

if tenant_id is None:
    user = self._get_current_user_from_context()
    if user and not user.is_superuser:
        # 非法状态：tenant_id=None 但不是超级管理员
        raise ValueError("Invalid user: tenant_id=None but is_superuser=False")
    # 超级管理员：不添加过滤，可访问所有数据
    return self
```

### 4.3 数据库约束保障

```sql
-- 数据库层面防止非法用户状态
ALTER TABLE users
ADD CONSTRAINT chk_superuser_tenant
    CHECK (
        (is_superuser = TRUE  AND tenant_id IS NULL)
        OR
        (is_superuser = FALSE AND tenant_id IS NOT NULL)
    );
```

---

## 5. 租户初始化流程

### 5.1 完整流程图

```
超级管理员操作
    │
    ▼
POST /api/v1/tenants/                 创建租户记录
    │  tenant_code, tenant_name, plan_type
    │
    ▼
POST /api/v1/tenants/{id}/init        初始化租户数据
    │  admin_username, admin_password, admin_email
    │
    ├── 创建默认角色（管理员、项目经理、工程师等）
    ├── 创建租户管理员账号
    ├── 分配管理员角色权限
    └── 初始化基础配置数据
    │
    ▼
租户管理员登录系统
    │
    ▼
正常使用（所有数据自动归属该租户）
```

### 5.2 创建租户 API

```bash
# 创建租户（需要超级管理员 Token）
curl -X POST http://localhost:8000/api/v1/tenants/ \
  -H "Authorization: Bearer <superadmin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "tenant_name": "上海精密制造有限公司",
    "tenant_code": "SH-FACTORY-001",
    "plan_type": "STANDARD",
    "contact_name": "张三",
    "contact_email": "zhangsan@example.com",
    "max_users": 50,
    "expired_at": "2027-12-31T00:00:00"
  }'
```

### 5.3 初始化租户数据 API

```bash
# 初始化租户（创建默认角色和管理员账号）
curl -X POST http://localhost:8000/api/v1/tenants/1/init \
  -H "Authorization: Bearer <superadmin_token>" \
  -H "Content-Type: application/json" \
  -d '{
    "admin_username": "sh_admin",
    "admin_password": "Secure@Password123",
    "admin_email": "admin@sh-factory.com",
    "admin_real_name": "张三",
    "copy_role_templates": true
  }'
```

### 5.4 租户套餐说明

| 套餐 | 用户上限 | 角色上限 | 存储空间 |
|------|---------|---------|---------|
| FREE | 5 | 5 | 1 GB |
| STANDARD | 50 | 20 | 10 GB |
| ENTERPRISE | 无限制 | 无限制 | 100 GB |

---

## 6. 核心组件说明

| 文件路径 | 作用 |
|---------|------|
| `app/models/tenant.py` | 租户数据模型（Tenant, TenantStatus, TenantPlan） |
| `app/core/middleware/tenant_middleware.py` | 租户上下文中间件（TenantContextMiddleware） |
| `app/core/database/tenant_query.py` | 自动过滤 Query 类（TenantQuery） |
| `app/core/decorators/tenant_isolation.py` | API 装饰器（@require_tenant_isolation） |
| `app/core/permissions/tenant_access.py` | 租户权限检查工具函数 |
| `app/core/auth.py` | 认证逻辑（is_superuser 判断、JWT 生成） |
| `app/api/v1/endpoints/tenants.py` | 租户管理 API 端点 |
| `app/services/tenant_service.py` | 租户业务逻辑服务层 |
| `app/schemas/tenant.py` | 租户相关 Pydantic Schema |

---

## 7. 技术栈

| 技术 | 版本 | 用途 |
|------|------|------|
| FastAPI | ≥ 0.100 | Web 框架 |
| SQLAlchemy | ≥ 2.0 | ORM（TenantQuery 继承其 Query 类） |
| python-jose | ≥ 3.3 | JWT Token 生成与解析 |
| Python contextvars | 内置 | 异步安全的租户上下文存储 |
| MySQL / SQLite | — | 数据库（生产 MySQL，测试 SQLite） |

---

## 相关文档

- [DEPLOYMENT.md](./DEPLOYMENT.md) — 生产部署指南
- [ADMIN_GUIDE.md](./ADMIN_GUIDE.md) — 系统管理员操作手册
- [DEVELOPER_GUIDE.md](./DEVELOPER_GUIDE.md) — 开发者指南
- [../租户过滤实现原理.md](../租户过滤实现原理.md) — 详细技术实现
- [../租户隔离测试指南.md](../租户隔离测试指南.md) — 测试用例说明
- [../超级管理员设计规范.md](../超级管理员设计规范.md) — 超级管理员规范
