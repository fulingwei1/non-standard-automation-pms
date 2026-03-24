# CLAUDE.md — 非标自动化项目管理系统

> AI 辅助开发的项目级指南。修改代码前先读此文件。

## 项目概述

非标自动化设备制造企业的智能项目管理系统（SaaS），覆盖签单→设计→生产→验收→售后全生命周期。

- **后端**: FastAPI + SQLAlchemy 2.0 + Pydantic 2.x，数据库 SQLite（开发）/ MySQL（生产）
- **前端**: React 19 + Vite 7 + Tailwind CSS 4 + shadcn/ui + Zustand + React Query
- **AI**: scikit-learn 成本预测，Moonshot/智谱 AI 集成

## 快速命令

```bash
# 后端
pip install -r requirements-dev.txt
uvicorn app.main:app --reload --port 8002

# 前端
cd frontend && pnpm install && pnpm dev

# 测试
pytest tests/                          # 后端全量（2454 tests）
pytest tests/ -m unit                  # 仅单元测试
pytest tests/ -m api                   # 仅 API 测试
cd frontend && pnpm test:run           # 前端单次运行
cd frontend && pnpm e2e                # Playwright E2E
```

## 项目结构

```
app/
├── main.py                  # FastAPI 入口，中间件栈
├── api/v1/
│   ├── api.py               # 路由聚合（_safe_include 安全加载）
│   └── endpoints/           # 71 个端点模块目录
├── core/                    # 配置、安全、中间件、数据库
├── models/                  # SQLAlchemy 模型（18 个领域分组）
├── services/                # 业务逻辑层（93 个服务模块）
├── schemas/                 # Pydantic 校验器
└── utils/                   # 工具函数
frontend/src/
├── pages/                   # 页面组件
├── components/              # 可复用组件
├── hooks/                   # 自定义 React Hooks
├── services/                # API 客户端
└── lib/                     # 工具库
tests/                       # pytest 后端测试
docs/                        # 项目文档（见 docs/INDEX.md）
scripts/                     # 运维/数据脚本（214+）
migrations/                  # Alembic 数据库迁移
```

## 核心模块索引

| 模块 | 后端路径 | 说明 |
|------|----------|------|
| 认证 | `endpoints/auth.py`, `core/security.py` | JWT + API Key + 2FA |
| 项目管理 | `endpoints/projects/`, `services/project_*` | 全生命周期 + 风险管理 |
| 成本管理 | `services/cost/`, `services/project_cost_prediction/` | EVM + AI 预测 |
| 工时管理 | `endpoints/timesheet/`, `services/timesheet_*` | 自动提醒 + 异常检测 |
| 审批引擎 | `services/approval_engine/`, `endpoints/approvals/` | 11 种业务类型适配器 |
| 销售管理 | `endpoints/sales/`, `services/sales/` | 线索→回款全流程 |
| 生产调度 | `endpoints/production/`, `services/production_*` | 排程 + 产能分析 |
| 多租户 | `core/middleware/tenant_middleware.py` | 框架级数据隔离 |
| 权限 | `services/permission_management/`, `services/role_management/` | RBAC 125 权限 |
| AI 售前 | `endpoints/presale/`, `services/presale_ai/` | 成本估算 + 胜率预测 |

## 开发约定

### 后端
- Python 代码用 Black 格式化，行宽 100
- import 排序用 isort（black profile）
- 所有 API 端点通过 `_safe_include()` 注册，失败不阻塞启动
- 业务逻辑放 `services/`，路由层 `endpoints/` 只做参数校验和调用
- 多租户：所有查询自动注入 `tenant_id` 过滤

### 前端
- ESLint 检查，Tailwind CSS 样式
- 状态管理用 Zustand，服务端状态用 React Query
- 表单用 React Hook Form + Zod 校验

### 测试
- pytest markers: `unit`, `api`, `integration`, `slow`, `security`, `e2e`
- 前端 E2E: `pnpm e2e:auth`, `pnpm e2e:project`, `pnpm e2e:sales` 等

## 环境变量

关键变量（详见 `.env.example`）:
- `SECRET_KEY` — JWT 签名密钥（生产必填）
- `DATABASE_URL` — 数据库连接串
- `REDIS_URL` — Redis 缓存（可选）
- `KIMI_API_KEY` / `GLM_API_KEY` — AI 服务密钥
- `DEBUG` — 调试模式（控制 OpenAPI 文档可见性）

## 详细文档

- [文档索引](docs/INDEX.md) — 全部文档入口
- [数据字典](docs/technical/数据字典.md)
- [API 快速参考](docs/api/API_QUICK_REFERENCE.md)
- [多租户开发指南](docs/development/多租户开发指南.md)
- [安全指南](docs/SECURITY.md)

## 实战积累的规则

<!-- 由 AI 纠错机制自动追加，格式：- [YYYY-MM-DD] 规则内容（触发原因：...） -->
