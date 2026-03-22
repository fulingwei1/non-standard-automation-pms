# CLAUDE.md — 非标自动化项目管理系统

> 本文件是 AI 辅助开发的入口文档。遵循分形规范：先读本文件获取全局规则和模块索引，再按需加载目标模块的 SPEC。

## 项目概述

**名称：** 非标自动化项目管理系统 (Non-Standard Automation PM)
**定位：** 面向非标自动化设备制造企业的全生命周期项目管理 SaaS 平台
**规模：** 130+ API 端点 · 91 数据模型 · 150+ 前端页面 · 多租户架构

## 技术栈

| 层级 | 技术 |
|------|------|
| 后端框架 | FastAPI 0.115 + Uvicorn |
| 数据库 | SQLAlchemy 2.0 · SQLite(开发) / MySQL 8.0(生产) |
| 缓存 | Redis 7 (in-memory fallback) |
| 前端框架 | React 19 + TypeScript + Vite 7 |
| UI 组件 | Ant Design 6 (暗色主题) + shadcn/ui (Radix) + Tailwind CSS 4 |
| 状态管理 | Zustand 5 · TanStack Query 5 · React Context |
| 表单 | React Hook Form 7 + Zod 4 |
| 图表 | Recharts 3 + Ant Design Plots 2 |
| 测试 | pytest(后端) · Vitest + Playwright(前端) |
| 部署 | Docker Compose · Nginx · Prometheus + Grafana |

## 快速命令

```bash
# 后端启动
python3 -m uvicorn app.main:app --reload

# 前端启动
cd frontend && pnpm dev

# 后端测试
pytest tests/ -v

# 前端测试
cd frontend && pnpm test

# 前端 E2E
cd frontend && pnpm e2e

# 前端 lint
cd frontend && pnpm lint

# 数据库初始化
python3 scripts/init_db.py
```

## 模块索引

### 后端 `app/`

```
app/
├── main.py                    # FastAPI 入口，中间件栈注册
├── core/                      # 核心基础设施
│   ├── config.py              # Pydantic Settings 配置
│   ├── auth.py                # JWT + bcrypt 认证
│   ├── security.py            # 安全工具
│   ├── permission_codes.py    # 125 个 API 权限码
│   ├── csrf.py                # CSRF 防护
│   ├── rate_limiting.py       # IP 级限流
│   ├── secret_manager.py      # 密钥管理
│   ├── encryption.py          # 加密工具
│   └── middleware/            # 中间件层
│       ├── auth_middleware.py     # 全局认证 (默认拒绝)
│       ├── tenant_middleware.py   # 多租户上下文 (ContextVar)
│       └── rate_limiting.py      # 限流中间件
├── api/v1/                    # API 路由层
│   ├── api.py                 # 路由注册中心
│   └── endpoints/             # 各领域端点
├── models/                    # SQLAlchemy 模型 (91 个)
│   └── base.py                # Base + TimestampMixin
├── services/                  # 业务逻辑层 (755 文件)
└── schemas/                   # Pydantic 请求/响应模型
```

### 前端 `frontend/src/`

```
frontend/src/
├── App.jsx                    # 应用入口 (Ant Design 暗色主题)
├── pages/                     # 页面组件 (150+)
├── routes/                    # 路由配置
│   └── modules/               # 按功能域分模块
├── core/                      # 核心组件和 hooks
│   ├── components/            # Dashboard, DataTable, FilterPanel, Form
│   └── hooks/                 # useForm, usePaginatedData 等
├── components/                # 可复用组件
│   └── ui/                    # shadcn/ui 组件
├── services/                  # API 服务层
│   ├── api.js                 # API 方法集合
│   └── apiClient.js           # Axios 实例 (自动 token 刷新)
├── context/                   # React Context
│   ├── AuthContext.jsx        # 认证状态
│   └── PermissionContext.jsx  # 权限状态
├── lib/                       # 工具库和常量
└── types/                     # TypeScript 类型定义
```

### 文档 `docs/`

- `docs/architecture/多租户架构设计.md` — 多租户数据隔离架构
- `docs/development/多租户开发指南.md` — 多租户 API 开发规范
- `docs/design/MULTI_TENANT_GUIDE.md` — 数据隔离分类指南

## 编码约定

### 后端 (Python/FastAPI)

- **分层架构：** `endpoint → service → model → database`，端点不含业务逻辑
- **多租户：** 所有业务表必须有 `tenant_id` 字段；使用 TenantQuery 自动过滤；创建时从 `current_user.tenant_id` 取值，**严禁从客户端接收**
- **认证：** 使用 `Depends(get_current_active_user)` 注入当前用户
- **超级用户：** `is_superuser=True AND tenant_id IS NULL`
- **权限：** RBAC 125 权限码 + 471 角色映射，通过 `permission_codes.py` 管理
- **密码：** bcrypt 哈希（72 字符限制），PyJWT HS256 令牌
- **配置：** 通过 Pydantic Settings + 环境变量，不硬编码

### 前端 (React/TypeScript)

- **主题：** Ant Design 暗色主题，主色 `#8b5cf6` (紫色)
- **状态：** 服务端状态用 TanStack Query，客户端状态用 Zustand
- **表单：** React Hook Form + Zod schema 校验
- **API 调用：** 通过 `services/apiClient.js` 的 Axios 实例
- **组件：** 优先使用 `core/components/` 中的共享组件 (Dashboard, DataTable, FilterPanel, Form)
- **Hooks：** 业务逻辑封装在 `pages/*/hooks/` 中的自定义 hooks

### 通用

- **不可变性：** 始终创建新对象，禁止原地修改
- **文件大小：** 200-400 行为宜，不超过 800 行
- **注释：** 业务逻辑必须有简体中文注释，说明 Why 而非 How
- **错误处理：** 所有外部调用必须 try/catch，用户友好的错误信息

## 中间件执行顺序 (LIFO)

1. `GlobalAuthMiddleware` — 默认拒绝策略
2. `InMemoryRateLimitMiddleware` — IP 限流
3. `TenantContextMiddleware` — 租户上下文注入
4. `AuditMiddleware` — 审计日志
5. `CSRFMiddleware` — CSRF 防护
6. `CORSMiddleware` — 跨域
7. `SecurityHeadersMiddleware` — 安全头

## 测试组织

```
tests/
├── unit/          # 单元测试 (函数/方法级)
├── integration/   # 集成测试 (API 端点)
├── e2e/           # 端到端 (Playwright)
├── security/      # 安全测试
├── performance/   # 性能测试
├── conftest.py    # 共享 fixtures
└── helpers/       # 测试工具
```

## 实战积累的规则

> 此部分由 AI 纠错驱动自进化机制自动维护，格式：`- [YYYY-MM-DD] 规则内容（触发原因）`

<!-- 尚无条目，随开发迭代自动积累 -->
