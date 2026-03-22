# ARCHITECTURE.md — 系统架构概览

## 高层架构

```
┌─────────────────────────────────────────────────────┐
│                    客户端                             │
│   React 19 + Ant Design 6 + Tailwind + shadcn/ui    │
│   (Vite 7 构建 · pnpm 管理)                          │
└──────────────────────┬──────────────────────────────┘
                       │ HTTPS / REST API
┌──────────────────────▼──────────────────────────────┐
│                  Nginx 反向代理                       │
│         (TLS 终端 · 静态文件 · 负载均衡)              │
└──────────────────────┬──────────────────────────────┘
                       │
┌──────────────────────▼──────────────────────────────┐
│              FastAPI 应用服务器                       │
│  ┌─────────────────────────────────────────────┐    │
│  │           中间件栈 (7 层 LIFO)               │    │
│  │  SecurityHeaders → CORS → CSRF → Audit      │    │
│  │  → TenantContext → RateLimit → GlobalAuth    │    │
│  └──────────────────┬──────────────────────────┘    │
│  ┌──────────────────▼──────────────────────────┐    │
│  │         API 路由层 (app/api/v1/)             │    │
│  │  130+ 端点 · 动态路由注册 · 权限守卫          │    │
│  └──────────────────┬──────────────────────────┘    │
│  ┌──────────────────▼──────────────────────────┐    │
│  │         服务层 (app/services/)               │    │
│  │  755 服务文件 · 业务逻辑 · AI/ML 推理         │    │
│  └──────────────────┬──────────────────────────┘    │
│  ┌──────────────────▼──────────────────────────┐    │
│  │         模型层 (app/models/)                 │    │
│  │  91 SQLAlchemy 模型 · TimestampMixin         │    │
│  │  · TenantQuery 自动过滤                      │    │
│  └──────────────────┬──────────────────────────┘    │
└──────────────────────┼──────────────────────────────┘
           ┌───────────┼───────────┐
           ▼                       ▼
┌──────────────────┐    ┌──────────────────┐
│   MySQL 8.0      │    │   Redis 7        │
│  (SQLite 开发)   │    │  (缓存 · 令牌    │
│  91 表 · 多租户   │    │   黑名单 · 限流)  │
└──────────────────┘    └──────────────────┘
```

## 后端分层架构

```
请求 → 中间件 → 端点 (Endpoint) → 服务 (Service) → 模型 (Model) → 数据库
                    │                    │                │
                    │ Pydantic Schema    │ 业务逻辑        │ SQLAlchemy ORM
                    │ 入参校验            │ 权限检查        │ TenantQuery
                    │ 响应序列化          │ AI/ML 推理      │ 事务管理
```

**核心原则：**
- 端点层只做参数校验和响应序列化，不含业务逻辑
- 服务层封装所有业务规则，通过依赖注入获取 db session
- 模型层定义数据结构和关系，TenantQuery 自动注入租户过滤

## 前端架构

```
App.jsx (暗色主题 · 路由)
├── routes/modules/         # 路由按功能域分模块
│   ├── DashboardRoutes
│   ├── ProjectRoutes
│   ├── SalesRoutes
│   ├── ProcurementRoutes
│   ├── ProductionRoutes
│   ├── FinanceRoutes
│   ├── HRRoutes
│   ├── PresalesRoutes
│   ├── WarehouseRoutes
│   └── SystemRoutes
│
├── pages/                  # 页面组件
│   └── Feature/
│       ├── index.jsx       # 页面入口
│       ├── hooks/          # 业务逻辑 hooks
│       ├── components/     # 页面私有组件
│       └── constants.js    # 页面常量
│
├── core/components/        # 共享核心组件
│   ├── Dashboard.tsx       # 仪表盘布局
│   ├── DataTable.tsx       # 数据表格
│   ├── FilterPanel.tsx     # 筛选面板
│   └── Form.tsx            # 表单组件
│
├── services/               # API 通信层
│   ├── apiClient.js        # Axios 实例 (拦截器 · token 刷新)
│   └── api.js              # 端点方法集合
│
└── context/                # 全局状态
    ├── AuthContext.jsx      # 认证 (登录/登出/token)
    └── PermissionContext.jsx # 权限 (RBAC 前端守卫)
```

**数据流：** 页面 → hook (业务逻辑) → TanStack Query (服务端状态) → apiClient (HTTP) → 后端 API

## 多租户数据隔离

采用**单数据库逻辑隔离**模式：所有租户共享同一数据库，通过 `tenant_id` 字段实现数据隔离。

### 三层隔离机制

```
第 1 层：数据库约束
  └── tenant_id NOT NULL + FOREIGN KEY + 复合索引

第 2 层：ORM 自动过滤
  └── TenantQuery 类在 SQL 执行前自动注入 WHERE tenant_id = ?

第 3 层：业务逻辑校验
  └── require_tenant_access() 防御性编程
```

### 上下文传播

```
HTTP 请求
  → GlobalAuthMiddleware (验证 JWT)
  → TenantContextMiddleware (从 user 提取 tenant_id → ContextVar)
  → 端点函数 (自动继承上下文)
  → 服务层 (自动继承上下文)
  → TenantQuery (从 ContextVar 读取 tenant_id，注入 WHERE 条件)
```

### 超级用户

- 定义：`is_superuser=True AND tenant_id IS NULL`
- 数据库约束确保两者互斥
- 可通过 `skip_tenant_filter()` 跨租户操作
- 必须使用 `Depends(get_current_active_superuser)` 显式声明

详见：`docs/architecture/多租户架构设计.md`、`docs/development/多租户开发指南.md`

## 认证与授权

### 认证流程

```
登录请求 (用户名 + 密码)
  → bcrypt 验证 (72 字符限制)
  → 检查账户锁定状态
  → [可选] 2FA TOTP 验证
  → 签发 JWT access_token (HS256, 24h 有效期)
  → 签发 refresh_token
  → 返回 token pair
```

### 授权模型

- **RBAC：** 125 个 API 权限码 + 471 角色到权限的映射
- **权限缓存：** Redis 缓存权限查询结果，22 倍性能提升 (61ms → 3ms)
- **API Key：** 支持 API Key 认证（机器间调用）
- **数据级控制：** 部门/项目级数据范围过滤

### 令牌管理

- JWT 包含可选 JTI (JWT ID) 用于会话管理
- 令牌黑名单（Redis 优先，内存兜底）
- 支持密钥轮换（旧密钥宽限期）

## AI/ML 子系统

```
app/services/
├── ai_service.py                  # 通用 AI 工具
├── cost_forecast_service.py       # 成本预测 (3 种算法)
├── sales_forecast_service.py      # 销售漏斗预测
├── ai_emotion_service.py          # 客户情感分析
├── ai_cost_estimation_service.py  # AI 成本估算
├── demand_forecast_engine.py      # 缺料需求预测
├── forecast_dashboard_service.py  # 预测仪表盘聚合
└── win_rate_prediction_service/   # 赢单率预测
```

**核心能力：**
- 成本预测：3 种算法（均值/线性回归/趋势），准确率 >85%
- 工时预测：6 维度分析（趋势/负荷/效率/加班/部门对比），准确率 >90%
- 销售预测：漏斗优化、赢单率预测、客户账龄分析
- 售前 AI：情感分析、需求提取、方案推荐、成本估算

## 部署拓扑

```
┌─────────────────────────────────────────┐
│            Docker Compose               │
│                                         │
│  ┌─────────┐  ┌───────┐  ┌──────────┐  │
│  │  app    │  │ mysql │  │  redis   │  │
│  │ :8000   │  │ :3306 │  │  :6379   │  │
│  └────┬────┘  └───────┘  └──────────┘  │
│       │                                 │
│  ┌────▼────┐  ┌────────────┐  ┌──────┐ │
│  │  nginx  │  │ prometheus │  │grafana│ │
│  │ :80/443 │  │   :9090    │  │:3000 │ │
│  └─────────┘  └────────────┘  └──────┘ │
└─────────────────────────────────────────┘
```

| 服务 | 镜像 | 用途 |
|------|------|------|
| app | 自定义 Dockerfile | FastAPI 后端 |
| mysql | mysql:8.0 | 主数据库 |
| redis | redis:7-alpine | 缓存/令牌黑名单/限流 |
| nginx | nginx:alpine | 反向代理/TLS/静态文件 |
| prometheus | prom/prometheus | 监控指标采集 |
| grafana | grafana/grafana | 监控仪表盘 |

配置文件：`docker/docker-compose.yml` (开发)、`docker/docker-compose.production.yml` (生产)

## 关键设计决策

| 决策 | 选择 | 理由 |
|------|------|------|
| 多租户模式 | 单库逻辑隔离 | 运维简单，适合中小规模 SaaS |
| 认证方案 | JWT + bcrypt + 可选 2FA | 无状态 + 安全性平衡 |
| 缓存策略 | Redis + in-memory fallback | 高可用，开发环境零依赖 |
| 前端 UI | Ant Design + shadcn/ui | 企业级组件 + 灵活定制 |
| 状态管理 | TanStack Query + Zustand | 服务端/客户端状态分离 |
| 权限模型 | RBAC 125 码 + 缓存 | 细粒度 + 高性能 |
| 数据库 ORM | SQLAlchemy 2.0 | 成熟 + async 就绪 |
| 暗色主题 | 默认暗色 (#8b5cf6 主色) | 工业制造场景长时间使用 |
