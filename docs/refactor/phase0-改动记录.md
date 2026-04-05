# Phase 0 改动记录（持续更新）

## 已完成（第一批）

- `app/api/v1/endpoints/stub_endpoints.py`
  - 默认返回 `501 Not Implemented`，不再返回 200 假成功
  - 新增开关：`ALLOW_STUB_SUCCESS=true` 才启用兼容模式
  - `auth/*` 落入 stub 时固定返回 404

- `app/api/v1/api.py`
  - 新增开关：`STRICT_API_ROUTER`（默认 true）
  - 新增开关：`ENABLE_STUB_ENDPOINTS`（默认 false）
  - 去掉 `create_api_router()` 失败后空路由 fallback
  - ITR / auth 关键模块在严格模式下 fail-fast

- `app/main.py`
  - app 级 auth 路由注册失败在严格模式下直接抛错（默认）

- `app/api/v1/endpoints/itr.py`
  - 修复错误导入：`from app.models.customer import Customer` -> `from app.models import Customer, Project, ServiceTicket, User`

- `app/services/two_factor_service.py`
  - `qrcode` 改为可选导入，缺失时抛出明确错误

- `app/api/v1/endpoints/two_factor.py`
  - 2FA setup 捕获依赖缺失并返回 `503 Service Unavailable`

- `.env.example`
  - 增加 `STRICT_API_ROUTER` / `ENABLE_STUB_ENDPOINTS` / `ALLOW_STUB_SUCCESS`

## 已完成（第二批）

`app/api/v1/api.py` 在严格模式下新增 fail-fast 的关键域：

- users/org
- projects
- production
- sales
- timesheet
- approvals
- customers/suppliers
- materials/purchase/bom
- shortage
- presale
- acceptance
- warehouse
- notifications
- issues
- scheduler
- dashboard
- report-center
- report

## 已完成（第三批）

`app/api/v1/api.py` 在严格模式下新增 fail-fast 的关键域：

- performance-contract
- hr-management
- task-center
- service
- project-workspace
- resource-scheduling
- sales-regions
- sales-targets
- sales-teams
- timesheet-reminders

## 已完成（第四批）

`app/api/v1/api.py` 在严格模式下新增 fail-fast 的关键域：

- inventory
- bonus
- engineer-performance
- performance
- pmo
- documents
- procurement-analysis
- installation-dispatch
- stage-templates
- budget
- departments
- material-demands
- project-reviews
- standard-costs
- inventory-analysis
- tenants

## 已完成（第五批）

`app/api/v1/api.py` 在严格模式下新增 fail-fast 的关键域：

- roles
- permissions
- rd-projects
- shortage-smart-alerts
- reports-unified
- node-tasks
- dashboard-stats
- dashboard-unified
- alerts
- qualifications
- engineers
- hourly-rates
- admin-stats
- strategy
- sla
- technical-specs
- audits
- change-impact

## 已完成（第六批）

`app/api/v1/api.py` 在严格模式下新增 fail-fast 的关键域：

- kit-rates
- supplier-price
- ecn-bom
- field-commissioning
- multi-currency
- ecn
- advantage-products
- assembly-kit
- ai-modules
- business-support
- business-support-orders
- culture-wall
- data-import-export
- kit-check
- management-rhythm
- my
- presale-ai
- ai-strategy
- outsourcing
- staff-matching
- technical-reviews
- analytics
- pitfalls
- presale-analytics
- solution-credits
- account-unlock
- backup
- culture-wall-config
- pm-involvement
- presale-ai-requirement
- presale-mobile
- project-contributions
- quality-risk
- lessons

## 已完成（第七批）

- `app/api/v1/api.py`
  - 增加路由加载失败汇总输出：启动末尾统一打印失败条目列表
  - 通过函数内 `print` 包装自动收集所有 `✗` 模块加载失败日志
  - 新增 fail-fast 关键域：
    - presale-ai
    - ai-strategy
    - outsourcing
    - staff-matching
    - technical-reviews
    - analytics
    - pitfalls
    - presale-analytics
    - solution-credits
    - account-unlock
    - backup
    - culture-wall-config
    - pm-involvement
    - presale-ai-requirement
    - presale-mobile
    - project-contributions
    - quality-risk
    - lessons

- 新增 CI 防回退守卫：
  - `scripts/ci_guard_stub_defaults.py`
  - `.github/workflows/guard-stub-defaults.yml`
  - 防止 `.env.example` 或 `api.py` 将 stub 默认值改回不安全状态

## 已完成（第八批）

- 新增启动回归脚本：`scripts/startup_regression_check.py`
  - 支持 strict / non-strict 两种模式下的启动验证
  - 自动输出 `api_router.routes` 与 `app.routes` 统计
- 新增 CI 启动回归工作流：`.github/workflows/startup-regression.yml`
  - PR 上对路由改动执行启动烟雾回归（strict + non-strict）

## 已完成（第九批）

- 新增 stub 行为回归测试：`tests/test_stub_endpoint_behavior.py`
  - 校验默认 501
  - 校验 `auth/*` 落入 stub 时 404
  - 校验兼容模式 `ALLOW_STUB_SUCCESS=true` 时可返回 200
- 新增路由失败分层助手：`scripts/classify_router_failures.py`
  - 从启动日志提取 `关键模块加载失败[xxx]`
  - 自动给出“必须修复 / 可临时降级 / 待人工判断”分类建议

## 已完成（第十批）

- 新增 CI 严格策略守卫：
  - `scripts/ci_guard_router_strict.py`
  - `.github/workflows/guard-router-strict.yml`
- 作用：防止 `app/api/v1/api.py` 出现“except 只打印不处理”的回退，要求 except 块必须包含：
  - `if STRICT_API_ROUTER:` 分支，或
  - 直接 `raise RuntimeError(...)`

## 下一步（待做）

- 对 `STRICT_API_ROUTER=true` 的回归失败项做分层处置：关键域保留 fail-fast，低优先级域降级为 warning
- 根据启动回归结果补充“关键域/可降级域”最终分层清单
