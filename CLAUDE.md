# 非标自动化项目管理系统 (Non-standard Automation PM)

## 项目概述

非标自动化项目管理系统，覆盖销售、项目管理、采购、生产、库存、质量、工时、财务等完整业务链。
后端基于 FastAPI + SQLAlchemy，前端基于 React + Ant Design + shadcn/ui + Tailwind CSS。

## 模块索引

### 后端 (`app/`)

| 目录 | 职责 |
|------|------|
| `app/api/v1/endpoints/` | API 路由层，按业务域拆分文件 |
| `app/services/` | 业务逻辑层 |
| `app/models/` | SQLAlchemy ORM 模型 |
| `app/schemas/` | Pydantic 请求/响应模型 |
| `app/core/` | 框架核心：配置、认证、中间件、安全 |
| `app/middleware/` | 自定义中间件（审计等） |
| `app/utils/` | 工具函数 |
| `app/common/` | 公共模块（上下文等） |

### 前端 (`frontend/src/`)

| 目录 | 职责 |
|------|------|
| `pages/` | 页面组件，按业务域拆分 |
| `core/components/` | 通用核心组件（Dashboard, DataTable, FilterPanel, Form） |
| `core/hooks/` | 通用 hooks（useForm, usePaginatedData, useTable, useDataLoader） |
| `components/` | 共享 UI 组件 |
| `context/` | React Context（AuthContext, PermissionContext） |
| `services/` | API 调用层 |
| `routes/` | 路由配置 |
| `lib/` | 常量和工具库 |

### 文档 (`docs/`)

业务模块和技术文档按主题分布在 `docs/` 子目录中，包括 `architecture/`、`development/`、`security/` 等。

## 编码约定

### 后端

- **框架**: FastAPI，路由通过 `_safe_include()` 动态注册到 `api_router`
- **ORM**: SQLAlchemy 2.0，声明式模型继承自 `app.models.base.Base`
- **配置**: `pydantic-settings` 驱动，`app.core.config.Settings` 类
- **认证**: JWT (HS256, PyJWT) + 可选 2FA (pyotp) + API Key
- **密码**: bcrypt 哈希
- **权限**: 数据库驱动，使用 `require_permission("module:action")`
- **多租户**: 单数据库共享 + `tenant_id` 逻辑隔离，通过 `TenantContextMiddleware` 自动注入
- **格式化**: black (line-length=100) + isort + ruff
- **Python**: 目标版本 3.9+

### 前端

- **框架**: React 19 + Vite 7
- **UI**: Ant Design 6 + shadcn/ui (Radix) + Tailwind CSS 4
- **状态**: Zustand + React Query (TanStack Query)
- **表单**: react-hook-form + zod 验证
- **路由**: react-router-dom v7
- **主题**: 深色主题，主色 `#8b5cf6`（紫色）
- **测试**: Vitest + Testing Library + Playwright (E2E)

## 常用命令

```bash
# 后端
pip install -r requirements-dev.txt       # 安装依赖
uvicorn app.main:app --reload             # 启动开发服务器
pytest                                     # 运行测试（含覆盖率）
pytest -m unit                             # 仅单元测试
pytest -m integration                      # 仅集成测试

# 前端
cd frontend && npm install                 # 安装依赖
npm run dev                                # 启动开发服务器
npm run build                              # 构建生产包
npm test                                   # 运行测试
```

## 环境变量

关键环境变量在 `app/core/config.py` 的 `Settings` 类中定义，通过 `.env` / `.env.local` 加载：

- `SECRET_KEY` — JWT 签名密钥（生产环境必填，最少 32 字符）
- `DATABASE_URL` / `SQLITE_DB_PATH` — 数据库连接
- `REDIS_URL` — Redis 连接（可选，用于缓存和速率限制存储）
- `DEBUG` — 调试模式（控制 OpenAPI 文档暴露）
- `CORS_ORIGINS` — 允许的跨域来源
- `KIMI_API_KEY` / `GLM_API_KEY` — AI 服务密钥（可选）

## 实战积累的规则

<!-- 由纠错即建规（Self-Evolution）自动追加 -->
