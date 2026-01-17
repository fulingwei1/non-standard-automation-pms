# SaaS 多租户改造方案

> 文档版本：v1.0
> 创建日期：2026-01-17
> 状态：待实施

## 1. 概述

### 1.1 目标

将现有的非标自动化项目管理系统改造为 SaaS 多租户架构，支持：
- 多家公司独立使用
- 按用户数 + 开户费灵活计费
- 数据完全隔离

### 1.2 核心决策

| 决策项 | 选择 | 理由 |
|--------|------|------|
| 数据隔离 | 共享数据库 + tenant_id | 336个模型，分库成本过高 |
| 租户识别 | 子域名 | 专业感强，行业惯例 |
| 计费模式 | 灵活可配置 | 支持多种定价策略 |
| MVP范围 | 用户权限 + 项目 + 销售 | 最小可用，快速验证 |

---

## 2. 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        负载均衡 (Nginx)                       │
│            *.pm.yourdomain.com → 提取 subdomain              │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      FastAPI 应用层                          │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 租户中间件   │→│  认证中间件  │→│  业务路由    │         │
│  │ 解析subdomain│  │ JWT+tenant  │  │ API endpoints│         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                      Service 层                              │
│         所有查询自动注入 tenant_id 过滤条件                    │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    MySQL 共享数据库                          │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐       │
│  │ tenants  │ │  users   │ │ projects │ │  sales   │ ...   │
│  │          │ │+tenant_id│ │+tenant_id│ │+tenant_id│       │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘       │
└─────────────────────────────────────────────────────────────┘
```

### 2.1 核心设计原则

1. **请求入口统一**：Nginx 解析子域名，传递给应用层
2. **租户上下文贯穿**：从中间件到 Service 层，tenant_id 自动传递
3. **数据自动隔离**：Service 基类自动添加 `WHERE tenant_id = ?`
4. **零信任原则**：即使前端传了其他租户 ID，后端也只用 token 中的

---

## 3. 数据模型设计

### 3.1 新增租户相关表

```sql
-- 租户表（公司）
CREATE TABLE tenants (
    id INT PRIMARY KEY AUTO_INCREMENT,
    code VARCHAR(50) UNIQUE NOT NULL,      -- 子域名标识，如 'huace'
    name VARCHAR(200) NOT NULL,            -- 公司名称，如 '华测自动化'
    status ENUM('trial','active','suspended','cancelled') DEFAULT 'trial',
    plan_id INT,                           -- 关联套餐
    trial_ends_at DATETIME,                -- 试用到期时间
    created_at DATETIME DEFAULT NOW(),
    settings JSON                          -- 租户个性化配置
);

-- 套餐计划表
CREATE TABLE plans (
    id INT PRIMARY KEY AUTO_INCREMENT,
    name VARCHAR(100) NOT NULL,            -- '基础版/专业版/企业版'
    max_users INT,                         -- 最大用户数，NULL=不限
    price_yearly DECIMAL(10,2),            -- 年费
    price_per_user DECIMAL(10,2),          -- 每用户单价
    features JSON,                         -- 功能开关
    is_active BOOLEAN DEFAULT TRUE
);

-- 订阅记录表
CREATE TABLE subscriptions (
    id INT PRIMARY KEY AUTO_INCREMENT,
    tenant_id INT NOT NULL,
    plan_id INT NOT NULL,
    status ENUM('active','expired','cancelled'),
    current_period_start DATE,
    current_period_end DATE,
    user_quota INT,                        -- 购买的用户数
    amount DECIMAL(10,2),                  -- 订阅金额
    paid_at DATETIME
);
```

### 3.2 现有表改造

```sql
-- 批量给现有表加字段的模式
ALTER TABLE users ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE users ADD INDEX idx_tenant_id (tenant_id);

ALTER TABLE projects ADD COLUMN tenant_id INT NOT NULL AFTER id;
ALTER TABLE projects ADD INDEX idx_tenant_id (tenant_id);

-- ... 其他业务表同理
```

### 3.3 不加 tenant_id 的表（全局共享）

- `plans` - 套餐定义，平台级
- `permissions` - 权限定义，平台级
- `system_configs` - 系统配置

---

## 4. 代码层改造

### 4.1 租户中间件

```python
# app/core/tenant.py
from fastapi import Request, HTTPException
from contextvars import ContextVar

# 使用 ContextVar 存储当前请求的租户，线程安全
current_tenant: ContextVar[int] = ContextVar('current_tenant', default=None)

class TenantMiddleware:
    async def __call__(self, request: Request, call_next):
        # 从子域名提取租户标识
        host = request.headers.get("host", "")
        subdomain = host.split(".")[0]  # huace.pm.domain.com → huace

        # 查询租户（带缓存）
        tenant = await get_tenant_by_code(subdomain)
        if not tenant:
            raise HTTPException(404, "租户不存在")
        if tenant.status == "suspended":
            raise HTTPException(403, "账户已停用，请联系管理员")

        # 设置到上下文
        current_tenant.set(tenant.id)
        request.state.tenant_id = tenant.id
        request.state.tenant = tenant

        return await call_next(request)
```

### 4.2 数据库查询自动过滤

```python
# app/models/base.py
class TenantMixin:
    """所有需要租户隔离的模型继承此类"""
    tenant_id = Column(Integer, nullable=False, index=True)

class TenantQuery(Query):
    """自动注入 tenant_id 过滤的 Query 类"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        tenant_id = current_tenant.get()
        if tenant_id and hasattr(self._entity_from_pre_ent_zero(), 'tenant_id'):
            self._where_criteria = (
                self._entity_from_pre_ent_zero().tenant_id == tenant_id
            )
```

### 4.3 依赖注入改造

```python
# app/api/deps.py
def get_current_tenant(request: Request) -> Tenant:
    """获取当前租户"""
    return request.state.tenant

def get_db_with_tenant(
    db: Session = Depends(get_db),
    tenant: Tenant = Depends(get_current_tenant)
) -> Session:
    """返回带租户上下文的数据库会话"""
    return db
```

### 4.4 Service 基类改造

```python
# app/services/base.py
class TenantService:
    """所有业务 Service 的基类"""

    def __init__(self, db: Session, tenant_id: int):
        self.db = db
        self.tenant_id = tenant_id

    def query(self, model):
        """自动带租户过滤的查询"""
        return self.db.query(model).filter(model.tenant_id == self.tenant_id)

    def create(self, model, **data):
        """创建时自动设置 tenant_id"""
        obj = model(tenant_id=self.tenant_id, **data)
        self.db.add(obj)
        return obj
```

---

## 5. 认证流程改造

### 5.1 登录流程

```
用户 → 访问 huace.pm.domain.com
     → 中间件识别租户
     → 租户专属登录页（可配置 Logo/背景）
     → 输入账号密码
     → 校验用户属于该租户
     → JWT Token（含 tenant_id）
     → 进入系统
```

### 5.2 JWT Token 结构

```python
# 改造后
{
    "sub": "user_id",
    "tenant_id": 123,           # 新增：租户ID
    "tenant_code": "huace",     # 新增：租户标识
    "exp": "过期时间"
}
```

### 5.3 安全设计要点

- 用户只能登录其所属租户
- Token 中的 tenant_id 后端生成，不信任前端
- 超级管理员可跨租户（平台运营用）
- 租户停用后，该租户所有 Token 立即失效

---

## 6. 平台运营后台

### 6.1 访问入口

```
admin.pm.yourdomain.com（平台管理员专用）
```

### 6.2 功能模块

```
平台运营后台
├── 租户管理
│   ├── 租户列表（搜索/筛选/状态）
│   ├── 新建租户（公司名/子域名/管理员账号）
│   ├── 租户详情（基本信息/使用统计/操作日志）
│   ├── 状态管理（启用/停用/删除）
│   └── 配置管理（Logo/主题色/功能开关）
│
├── 订阅与计费
│   ├── 套餐管理（创建/编辑/上下架）
│   ├── 订阅记录（租户订阅历史）
│   ├── 账单管理（生成账单/标记已付）
│   └── 用量统计（各租户用户数/存储/API调用）
│
├── 数据统计
│   ├── 总览仪表盘（租户数/用户数/收入）
│   ├── 增长趋势（新增租户/流失租户）
│   └── 活跃度分析（日活/月活/功能使用）
│
└── 系统设置
    ├── 平台管理员管理
    ├── 全局配置（默认套餐/试用期天数）
    └── 公告管理（发布给所有租户）
```

### 6.3 租户开通流程

```
1. 客户注册/销售录入 → 创建租户记录
2. 系统自动：
   - 生成子域名 huace.pm.domain.com
   - 创建租户管理员账号
   - 初始化默认角色和权限
   - 发送开通邮件（含登录地址和临时密码）
3. 客户登录 → 修改密码 → 开始使用
```

---

## 7. 实施计划

### 7.1 总体时间线：6-8 周

```
Week 1-2: 基础设施层
Week 3-4: 核心业务改造
Week 5-6: 运营后台开发
Week 7-8: 测试与上线准备
```

### 7.2 Phase 1: 基础设施层（Week 1-2）

| 任务 | 工作量 | 产出 |
|------|--------|------|
| 租户数据模型设计 | 2天 | tenants/plans/subscriptions 表 |
| 租户中间件开发 | 2天 | 子域名解析 + 上下文注入 |
| 认证改造 | 2天 | JWT 加入 tenant_id |
| TenantMixin 基类 | 1天 | 模型基类 + 自动过滤 |
| TenantService 基类 | 1天 | Service 基类改造 |
| 数据库迁移脚本 | 2天 | 批量添加 tenant_id 字段 |

**里程碑 1**：租户隔离框架可用，单租户可正常运行

### 7.3 Phase 2: 核心业务改造（Week 3-4）

| 模块 | 涉及表数 | 工作量 | 说明 |
|------|---------|--------|------|
| 用户与权限 | ~8张 | 3天 | users/roles/permissions/departments |
| 组织架构 | ~5张 | 2天 | organization_units/positions |
| 项目管理 | ~15张 | 4天 | projects/machines/stages/milestones |
| 销售管理 | ~12张 | 3天 | leads/opportunities/quotes/contracts |

**每个模块改造步骤：**
```
1. Model 添加 tenant_id 字段
2. Service 继承 TenantService
3. API 依赖注入改造
4. 单元测试验证隔离
```

**里程碑 2**：MVP 功能多租户可用

### 7.4 Phase 3: 运营后台开发（Week 5-6）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 后台框架搭建 | 2天 | 独立前端项目或复用现有 |
| 租户 CRUD | 2天 | 列表/详情/创建/编辑 |
| 套餐管理 | 1天 | 套餐配置 |
| 订阅管理 | 2天 | 订阅记录/账单 |
| 数据统计仪表盘 | 2天 | 核心指标展示 |
| 租户开通自动化 | 1天 | 初始化脚本 |

**里程碑 3**：可以通过后台开通和管理租户

### 7.5 Phase 4: 测试与上线（Week 7-8）

| 任务 | 工作量 | 说明 |
|------|--------|------|
| 多租户隔离测试 | 2天 | 确保数据不串租户 |
| 性能测试 | 2天 | 多租户场景压测 |
| 安全审计 | 1天 | 权限/数据泄露检查 |
| 部署方案 | 2天 | Nginx 配置/泛域名证书 |
| 文档编写 | 1天 | 运营手册/API 文档 |
| 灰度上线 | 2天 | 先上 1-2 个试点客户 |

**里程碑 4**：正式上线，开始商业化

---

## 8. 风险与应对

### 8.1 技术风险

| 风险 | 影响 | 应对措施 |
|------|------|----------|
| 数据隔离遗漏 | 严重：数据泄露 | 代码审查 + 自动化测试覆盖 |
| 性能下降 | 中等：查询变慢 | tenant_id 加索引 + 查询优化 |
| 迁移出错 | 严重：数据丢失 | 迁移前完整备份 + 分批执行 |
| 缓存污染 | 中等：数据错乱 | 缓存 key 加 tenant 前缀 |

### 8.2 改造红线（必须遵守）

1. 所有业务表必须加 tenant_id，无例外
2. 所有查询必须经过 TenantService，禁止裸写 SQL
3. 缓存 key 格式：`tenant:{tenant_id}:{业务key}`
4. 日志必须包含 tenant_id，便于问题排查
5. 禁止前端传 tenant_id，只信任 Token

### 8.3 现有数据处理

```
方案：创建一个默认租户（tenant_id=1）
1. 现有数据全部归属默认租户
2. 默认租户即公司自用
3. 新客户开通新租户（tenant_id=2,3,4...）
```

### 8.4 回滚方案

```
如果上线后发现严重问题：
1. Nginx 切换到旧版本（不解析子域名）
2. 代码回滚到改造前分支
3. 数据库 tenant_id 字段保留但不影响旧逻辑
```

---

## 9. 后续扩展（未来规划）

### 9.1 Phase 5+: 剩余模块改造

- 采购管理
- 客服工单
- ECN 变更
- 外协管理
- 工时管理
- 奖金绩效

### 9.2 高级特性

- 租户自定义域名绑定
- 数据导入导出（租户迁移）
- API 调用量计费
- 大客户独立部署选项

---

## 附录

### A. MVP 涉及的数据表清单

**用户与权限模块（~8张）**
- users
- roles
- permissions
- user_roles
- role_permissions
- departments
- positions
- organization_units

**项目管理模块（~15张）**
- projects
- machines
- project_stages
- project_milestones
- project_members
- project_costs
- project_documents
- project_risks
- project_issues
- ...

**销售管理模块（~12张）**
- leads
- opportunities
- quotes
- quote_items
- contracts
- customers
- contacts
- ...

### B. 缓存 Key 规范

```
# 格式：tenant:{tenant_id}:{module}:{resource}:{id}

# 示例
tenant:1:user:123              # 租户1的用户123
tenant:1:project:list:page1    # 租户1的项目列表第1页
tenant:1:config:settings       # 租户1的配置
```

### C. 日志格式规范

```json
{
    "timestamp": "2026-01-17T10:00:00Z",
    "level": "INFO",
    "tenant_id": 1,
    "tenant_code": "huace",
    "user_id": 123,
    "action": "project.create",
    "message": "Created project PJ260117001"
}
```
