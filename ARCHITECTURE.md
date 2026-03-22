# 系统架构概览 (Architecture Overview)

## 技术栈

| 层 | 技术 | 版本（来源：requirements-dev.txt / package.json） |
|----|------|------|
| 后端框架 | FastAPI | 0.115.0 |
| ORM | SQLAlchemy | 2.0.36 |
| 数据验证 | Pydantic + pydantic-settings | 2.9.2 / 2.5.2 |
| 认证 | PyJWT (HS256) + bcrypt + pyotp (2FA) | 2.10.1 / ≥4.3.0 / 2.9.0 |
| 速率限制 | slowapi + 自研内存限流中间件 | 0.1.9 |
| 前端框架 | React + Vite | 19.2.4 / 7.3.1 |
| UI 组件 | Ant Design + Radix UI (shadcn/ui) | 6.3.1 |
| 样式 | Tailwind CSS | 4.1.18 |
| 状态管理 | Zustand + TanStack React Query | 5.0.9 / 5.90.21 |
| 数据库 | SQLite（开发）/ PostgreSQL（生产） | — |
| 缓存 | Redis（可选，不可用时降级到内存） | — |
| 部署 | Docker + Vercel | — |
| 监控 | Prometheus + Grafana | — |

## 后端分层架构

```
请求 → 中间件栈 → 路由层 → 服务层 → 模型层 → 数据库
```

### 中间件执行顺序

中间件在 `app/main.py` 中注册，FastAPI 采用 LIFO（后进先出）顺序执行。
以下是注册顺序（最后注册的最先执行）：

1. `InMemoryRateLimitMiddleware` — IP 级速率限制（可通过 `RATE_LIMIT_ENABLED=false` 禁用）
2. `GlobalAuthMiddleware` — 全局认证，默认拒绝策略
3. `TenantContextMiddleware` — 从认证用户提取 `tenant_id`，写入 `request.state` 和 `ContextVar`
4. `AuditMiddleware` — 审计日志
5. `CSRFMiddleware` — CSRF 防护
6. Security Headers — HTTP 安全响应头
7. `CORSMiddleware` — 跨域资源共享

### 路由注册

`app/api/v1/api.py` 通过 `_safe_include()` 动态导入并注册各业务模块路由。
导入失败时记录警告但不阻塞应用启动，保证部分模块异常不影响整体可用性。

### 分层职责

| 层 | 目录 | 职责 |
|----|------|------|
| 路由层 | `app/api/v1/endpoints/` | 参数解析、权限检查、调用服务层 |
| 服务层 | `app/services/` | 业务逻辑、事务协调 |
| 模型层 | `app/models/` | SQLAlchemy ORM 定义、数据库表结构 |
| Schema 层 | `app/schemas/` | Pydantic 请求/响应模型 |

## 前端架构

```
页面 (pages/) → 核心组件 (core/components/) → hooks (core/hooks/)
                                              → 服务层 (services/)
                                              → Context (context/)
```

### 核心组件

`frontend/src/core/components/` 提供 4 个通用组件：
- **Dashboard** — 仪表盘布局
- **DataTable** — 数据表格
- **FilterPanel** — 筛选面板
- **Form** — 表单

### 状态与数据流

- **AuthContext** — 认证状态（登录/登出/Token 管理）
- **PermissionContext** — 权限状态（前端权限控制）
- **Zustand** — 局部业务状态
- **React Query** — 服务端数据缓存和同步

### 主题

深色主题为主，Ant Design 通过 `darkAlgorithm` 配置，主色调紫色 `#8b5cf6`。

## 多租户数据隔离

采用**单数据库多租户**模式（详见 `docs/architecture/多租户架构设计.md`）：

- 所有业务表包含 `tenant_id` 字段
- `TenantContextMiddleware` 从认证用户自动提取 `tenant_id`，存入 `ContextVar`
- 查询层自动注入租户过滤条件，开发者无需手动处理
- 超级管理员可跨租户操作

## 认证与授权

### 认证方式

1. **JWT** — 主认证方式，HS256 签名，24 小时有效期（`ACCESS_TOKEN_EXPIRE_MINUTES` 配置）
2. **Refresh Token** — Token 刷新机制
3. **2FA** — 可选 TOTP 双因素认证（pyotp），支持备用码
4. **API Key** — 程序化访问

### 密钥管理

- `SECRET_KEY` 支持环境变量和 Docker Secrets 文件加载
- 支持密钥轮转：`OLD_SECRET_KEYS` 保留旧密钥（最多 3 个，30 天有效期）
- 开发环境自动生成临时密钥，生产环境强制要求配置

### 权限模型

- 数据库驱动的权限系统，使用 `require_permission("module:action")` 装饰器
- Token 黑名单优先使用 Redis，不可用时降级到内存 `set()`
- 销售模块有独立的数据范围权限控制（`sales_permissions.py`）

## AI/ML 子系统

系统集成两个可选的 AI 服务：

- **Kimi (Moonshot)** — 模型 `moonshot-v1-8k`，通过 `KIMI_API_KEY` 启用
- **GLM (智谱 AI)** — 模型 `glm-4`，通过 `GLM_API_KEY` 启用

AI 功能分布在多个服务中（`ai_service.py`、`ai_client_service.py`、`ai_assessment_service.py` 等），
用于需求分析、方案评估、情感分析等辅助决策场景。

## 部署拓扑

### Vercel（前端 + Serverless API）

`vercel.json` 定义了部署配置：
- 前端通过 Vite 构建，输出到 `frontend/dist`
- 后端作为 Python 3.9 Serverless Function（`api/index.py`），60s 超时，1024MB 内存
- API 路由通过 rewrites 转发到 Serverless Function

### Docker（自托管）

`docker/` 目录提供：
- `Dockerfile` — 后端镜像
- `Dockerfile.fullstack` — 全栈镜像
- `Dockerfile.nginx` — Nginx 反向代理
- `docker-compose.yml` — 基础编排
- `docker-compose.production.yml` — 生产环境编排
- `docker-compose.secrets.yml` — 密钥管理
- `docker-compose.waf.yml` — WAF 配置

### 监控

`monitoring/` 目录包含 Prometheus 配置（`prometheus.yml`）和 Grafana 仪表盘及告警规则。

## 定时任务

通过 APScheduler (`apscheduler==3.10.4`) 实现，可通过 `ENABLE_SCHEDULER` 环境变量控制开关。
包括进度跟踪调度器和通用任务调度器，在应用启动时初始化，关闭时清理。
