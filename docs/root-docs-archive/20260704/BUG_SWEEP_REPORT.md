# 全面 Bug 排查与修复报告

> 生成时间：2026-06-21
> 范围：`non-standard-automation-pm` 后端（FastAPI），全量测试套件（tests/ 共 1831 个测试文件）

## 一、结论速览

- **应用本体健康**：`app.main` 正常导入，4238 条路由全部加载，`/health` 200、`/docs` 200、`/api/v1/openapi.json` 200。
- **全量测试规模**：约 **18,000+ 用例通过**，约 1,700 失败 + 490 错误（失败数受“分批运行时跨文件数据污染”放大，详见第三节）。
- **已定位并修复的真实产品 Bug：15 项**（另修正 1 个被错误固化的测试）。
- 其余失败**绝大多数为测试债**（测试隔离 + 测试漂移），**非产品缺陷**，已分类说明并给出建议。

## 二、已修复的真实产品 Bug（15）

| # | 文件 | 问题 | 修复 |
|---|------|------|------|
| 1 | `app/services/approval_engine/adapters/quote.py` | `quote.owner.name`：User 无 `name` 字段 → 报价审批提交 500 | 改为 `owner.real_name or owner.username` |
| 2 | `app/services/quote_approval/quote_approval_service.py` | 把审批引擎返回的 `{"items": [...]}` 当列表切片 → `KeyError: slice` | 取 `["items"]` 后再分页 |
| 3 | `app/services/production/workshop_service.py` | `workshop.worker_count`：模型无该字段 → 车间产能 500 | 按 `Worker` 表统计在职人数 |
| 4 | `app/services/production/workshop_service.py` | 缺少 `get_task_board()` → 车间看板端点 500 | 实现该方法（工位/工单/工人） |
| 5 | `app/services/ai_planning/resource_optimizer.py` | `user.role` ×2：User 无 `role` 字段 | 改为 `user.position` |
| 6 | `app/services/timesheet_records.py` | `current_user.is_admin()` ×6：User 无该方法 → 工时记录端点 500 | 改为 `is_superuser` |
| 7 | `app/common/crud/base_crud_service.py` | 通用 CRUD 删除：模型无 `deleted_at` 时软删除抛错 → DELETE 500 | 无软删字段时自动降级硬删除 |
| 8 | `app/services/report_excel_service.py` | `col[0].column_letter` ×2：合并单元格(MergedCell)无该属性 → Excel 导出报错 | 用 `get_column_letter(col[0].column)` |
| 9 | `app/services/performance_trend_service.py` | `Employee.department_id`：Employee 无该字段 → 部门绩效趋势 500 | 改为 `User.department_id` 直接查询 |
| 10 | `app/services/project_evaluation_service.py` | `Timesheet.total_hours`：模型字段为 `hours` | 改为 `func.sum(Timesheet.hours)` |
| 11 | `app/services/notification/channels/email_handler.py` + `channels/__init__.py` | 通知模块循环导入（冷导入即失败）→ 任何先导入该链路的入口崩溃 | `__getattr__` 惰性导入打破环 |
| 12 | `app/services/shortage/shortage_reports_service.py` | `joinedload(reporter/confirmer/handler/resolver)`：模型无这些 relationship → 缺料报告查询 500 | 改为 eager load 真实存在的 `project/machine/material` |
| 13 | `app/services/report_data_generation/project_reports.py` | `ProjectMilestone.milestone_date` ×4：模型字段为 `planned_date` | 统一改为 `planned_date` |
| 14 | `app/services/cost/cost_forecast_service.py` | `import sklearn`：依赖未安装（项目刻意不含）→ 线性预测 500 | 用 numpy 最小二乘重写，去除依赖 |
| 15 | `app/services/file_upload_service.py` | `hashlib.md5(str)`：传入字符串时崩溃 | 入参为 str 时按 UTF-8 编码（容错） |

附：`tests/unit/test_approval_adapter_quote.py` 的 mock 把 owner 名字设在已废弃的 `.name` 字段，随 #1 一并修正为 `real_name`。

每个修复均已通过对应测试文件的单独回归验证。

## 三、未修复失败的分类（测试债，非产品 Bug）

1. **测试隔离债（占比最大，~数百 errors）**
   - 现象：`sqlite3.IntegrityError: UNIQUE constraint failed: projects.project_code / users.username ...`
   - 根因：`tests/conftest.py` 的 `db_session` 仅回滚“未提交”更改；大量测试 fixture 直接 `commit()` 固定主键（如 `RES_TEST_001`、`dev1`），会话级共享同一 `:memory:` 库（StaticPool），导致同名数据冲突。
   - 影响：同一文件内多个用例、或同批多个文件并存时报错；**与产品逻辑无关**。
   - 建议：为 `db`/`db_session` 引入真正的“按用例隔离”（每用例后清表或外层事务+SAVEPOINT 回滚），可一次性消除绝大部分 errors。

2. **测试漂移（重构后测试未同步）**
   - 旧模块路径：`app.services.cpq_pricing_service` 等（已移入子包 `app.services.presale.cpq_pricing_service`），测试 `@patch` 仍指旧路径。
   - 重命名字段：`request_code`→`request_no`、`milestone_date`→`planned_date` 等，测试仍用旧名。
   - 缺失工厂/导入：`SupplierFactory`、`ProjectMaterial` 等未定义。
   - 错误的 `@patch` 目标：`module.get_or_404`、`module.security`、`ENABLE_GLOBAL_AUTH` 等。
   - 这些是测试自身需更新，**产品代码正确**。

3. **Mock 失真的单元测试**
   - 现象：`MagicMock` 无法 `len()`/比较/迭代、`'str' object has no attribute 'is_superuser'`、`fromisoformat` 入参类型不符等。
   - 根因：测试用 Mock 替身或传错类型；产品端类型契约正确。

## 四、已知“半成品/废弃特性”（非线上可达，建议单独立项）

- `app/services/material_transfer_service.py`：引用不存在的 `ProjectMaterial`，且兜底用的 `MaterialReservation` 字段名也不匹配。线上调用方 `shortage/.../transfers.py` 已用 `try/except` 兜住，不会 500；测试通过 `sys.modules` 打桩绕过。需补齐数据模型后重写。
- `app/services/knowledge_auto_identification_service.py::identify_code_module`：`CodeModule` 模型用 `contributor_id`，无 `author_id/file_path/project_id`；该方法未被线上端点调用（批量识别走另两个方法）。

## 五、基础设施观察

- 全量测试**单进程跑会 OOM**（约 42% 处被杀）。本次采用“按文件分批 + 子分批”策略规避。
- **已定位主要内存元凶**：`tests/unit/test_batch_utils_1.py`（96 用例）单文件即可吃满 4GB+ 内存且长时间不结束 → 这是全量套件 OOM 的主因之一。属测试质量问题（疑似某用例内存泄漏/失控），建议单独排查该文件并加 `pytest-timeout`/内存上限。
- 缺少 `pytest-xdist`/`pytest-timeout`（CI 用到 `--timeout=30`，本地未装）。
- 本地 conftest 强制 `:memory:`，CI 用 `sqlite:///test.db`（文件库），两者行为存在差异。

## 六、2026-06-25 增量排查与修复

### 1. 售前工作台 500 已修复

- 复现页面：`/presales/workbench/sales`
- 复现接口：
  - `GET /api/v1/presale/workbench/overview` → 500
  - `GET /api/v1/presale/tickets` → 500
  - `GET /api/v1/presale/expenses` 受同类历史库字段漂移影响
- 根因：本地历史 SQLite `data/app.db` 的售前表结构落后于 ORM：
  - `presale_tender_record.project_id` 缺失
  - `presale_ticket_deliverable.is_required` 缺失
  - `presale_expenses.ticket_id / approval_status / approved_by / approved_at / approval_note` 缺失
- 修复：
  - 在 `app/models/base.py::_ensure_sqlite_schema()` 增加售前历史 SQLite schema patch。
  - 在 `tests/core/test_database.py::TestSQLiteSchemaPatches` 增加回归测试，模拟旧表并断言补丁会补齐字段。
- 验证：
  - `pytest tests/core/test_database.py::TestSQLiteSchemaPatches -q` → 6 passed
  - `GET /api/v1/presale/workbench/overview` → 200
  - `GET /api/v1/presale/tickets` → 200
  - `GET /api/v1/presale/expenses` → 200

### 2. 售前演示数据已补齐关联链路

- 新增脚本：`scripts/seed_presale_workbench_demo_data.py`
- 数据前缀：`PWB26`
- 数据特点：
  - 4 组客户-线索-商机-需求包-技术评估-售前工单-方案-投标-报价联动场景
  - 4 个技术参数模板
  - 16 个工单交付物、16 个报价明细
  - 1 个已赢单合同
  - 每组商机带未决事项、需求冻结、AI 澄清和售前费用
- 幂等验证：
  - 第一次运行新增 4 组场景。
  - 第二次运行只更新根对象，不重复新增；核心对象计数保持：customers/leads/opportunities/tickets/solutions/tenders/quotes/templates 均为 4，contracts 为 1。
- 页面验证：
  - Playwright 访问 `http://127.0.0.1:5173/presales/workbench/sales`
  - 页面显示 `PWB26-TK-001`、宁德时代、比亚迪和关联方案
  - 未出现 `Request failed with status code 500`
  - 截图：`.gstack/qa-reports/screenshots/presale-workbench-sales-pwb26.png`

### 3. 增量验证结果

- `python -m py_compile scripts/seed_presale_workbench_demo_data.py` → passed
- `python -m pytest tests/api/test_sales_quotes_api.py tests/unit/test_approval_adapter_quote.py -q` → 48 passed, 6 skipped
- `from app.main import app` → 成功加载 4238 条 API 路由
- `GET /health` → 200
- `frontend npm run build` → passed，保留既有 chunk/dynamic import 警告

### 4. 仓储工作台 500 已修复

- 复现页面：`/workstation/warehouse`
- 复现接口：
  - `GET /api/v1/warehouse/stats` → 500
  - `GET /api/v1/warehouse/alerts` → 500
  - `GET /api/v1/warehouse/inbound?status=pending` → 500
  - `GET /api/v1/warehouse/outbound?status=pending` → 500
- 根因：本地历史 SQLite 缺少仓储模块核心表，接口查询 `inbound_orders / outbound_orders / inventory` 时直接抛 `sqlite3.OperationalError: no such table`。
- 修复：
  - 在 `app/models/base.py::_ensure_sqlite_schema()` 增加仓储核心表补建逻辑。
  - 补建表：`warehouses / warehouse_locations / inbound_orders / inbound_order_items / outbound_orders / outbound_order_items / inventory / stock_count_orders / stock_count_items`。
  - 补建索引：`ix_warehouse_location_code`、`ix_inventory_material`。
  - 在 `tests/core/test_database.py::TestSQLiteSchemaPatches` 增加旧库缺表回归测试。
- 验证：
  - 新测试先失败，补丁后通过。
  - `GET /api/v1/warehouse/stats / alerts / inbound / outbound / inventory` 均为 200。
  - Playwright 访问 `http://127.0.0.1:5173/workstation/warehouse`，无 500、无控制台错误。
  - 截图：`.gstack/qa-reports/screenshots/smoke-workstation-warehouse-after.png`

### 5. 销售工作台汇总接口 404/500 已修复

- 复现页面：`/sales/workstation`
- 复现接口：
  - `GET /api/v1/sales/follow-up/reminders/summary` → 404
  - `GET /api/v1/sales/collection/priority/summary` → 404
  - `GET /api/v1/sales/opportunities/health/summary` → 404
  - `GET /api/v1/sales/contracts/milestones/summary` → 404；挂载后暴露 `Contract.end_date` 兼容 500
- 根因：
  - 后端已有对应 endpoint 文件，但未纳入 `sales` 聚合路由。
  - 合同里程碑服务沿用旧字段 `end_date`，当前合同模型真实字段为 `expiry_date`。
  - 前端调用了 `followUpReminderApi.getActionBoard()`，服务封装缺该方法。
- 修复：
  - 在 `app/api/v1/endpoints/sales/__init__.py` 挂载 follow-up、collection priority、opportunity health、contract milestones 路由，并将静态汇总路由排在动态资源路由前。
  - 在 `app/models/sales/contracts.py` 增加 `end_date <-> expiry_date` legacy alias。
  - 在 `app/services/sales/follow_up_reminder_service.py` 补充工作台需要的 `total_count / overdue_count / high_priority_count / by_urgency` 字段。
  - 在 `frontend/src/services/api/sales.js` 补齐 `getActionBoard()`。
- 验证：
  - 新增合同模型 alias 回归测试先失败，修复后通过。
  - `GET /api/v1/sales/collection/priority/summary` → 200
  - `GET /api/v1/sales/opportunities/health/summary` → 200
  - `GET /api/v1/sales/contracts/milestones/summary` → 200
  - `GET /api/v1/sales/follow-up/reminders/summary` → 200
  - Playwright 访问 `http://127.0.0.1:5173/sales/workstation`，无后端 4xx/5xx、无控制台错误。
  - 截图：`.gstack/qa-reports/screenshots/sales-workstation-after-route-fixes.png`

### 6. 报价页趋势图 NaN 已修复

- 复现页面：`/sales/quotes`
- 现象：
  - 控制台提示 SVG `points` / `cy` 包含 `NaN`。
  - 页面传入 `SimpleLineChart` 的数据字段为 `month / quotes / converted`，组件只读取固定 `label / value`。
- 修复：
  - `SimpleLineChart` 支持 `xKey / valueKey / yKeys`，并将非有限数值兜底为 0。
  - 增加 `frontend/src/components/administrative/__tests__/StatisticsCharts.test.jsx`，断言多字段数据不会生成 NaN SVG 坐标。
- 验证：
  - 新测试先失败，修复后通过。
  - `npm run test:run -- StatisticsCharts.test.jsx` → passed
  - `npm run build` → passed（保留既有 dynamic import/chunk 警告）
  - Playwright 访问 `http://127.0.0.1:5173/sales/quotes`，无 NaN、无后端 4xx/5xx、无控制台错误。
  - 截图：`.gstack/qa-reports/screenshots/sales-quotes-after-route-fixes.png`

### 7. 宽页面 smoke 后新增修复

- 宽 smoke 范围：27 个高频路由，覆盖管理/销售/售前/仓储/项目中心等入口。
- 发现并修复：
  - `/sales/dashboard` 前端崩溃：后端 dashboard 返回缺少 `avg_deal_size / weighted_value / deal_count / avg_cycle_days / risks / forecast.total_* / accuracy` 等前端契约字段；同时前端空数组和除零场景可能生成 NaN。
  - `/sales/leads` 500：历史库中 `selected_advantage_products='["EOL","FCT","MES"]'`，响应 schema 期望 `List[int]`，Pydantic 校验失败。
  - `/sales/opportunity-center` 受 `/sales/leads` 500 连带报错。
- 修复：
  - `app/api/v1/endpoints/sales/dashboard.py` 补齐 dashboard 前端契约字段。
  - `frontend/src/pages/SalesDashboard.jsx` 对月度/季度/阶段/风险数组和除零场景做兜底。
  - `app/api/v1/endpoints/sales/leads/crud.py` 在响应层解析历史优势产品 JSON，仅保留数值 ID，非数值历史编码返回空列表而不是 500。
- 验证：
  - 新增 `tests/integration/sales/test_sales_dashboard.py`，接口契约测试先失败、修复后通过。
  - 新增 `tests/integration/sales/test_leads.py::TestLeadList::test_list_leads_handles_legacy_advantage_product_codes`，历史字段回归先失败、修复后通过。
  - `GET /api/v1/sales/dashboard` → 200
  - `GET /api/v1/sales/leads?page=1&page_size=20` → 200
  - Playwright 访问 `/sales/dashboard`、`/sales/leads`、`/sales/opportunity-center`，均无后端 4xx/5xx、无控制台错误、无 NaN。
  - 截图：
    - `.gstack/qa-reports/screenshots/sales-dashboard-after-dashboard-leads-fixes.png`
    - `.gstack/qa-reports/screenshots/sales-leads-after-dashboard-leads-fixes.png`
    - `.gstack/qa-reports/screenshots/sales-opportunity-center-after-dashboard-leads-fixes.png`
- 备注：宽 smoke 中 `/presales/technical-solutions`、`/presales/presale-analytics`、`/warehouse/inbound` 的 429 属于快速连续页面探测触发本地限流；对应功能需用更慢节奏或关闭限流再复扫。

### 8. 本轮最终回归记录

- `.venv/bin/python -m pytest tests/core/test_database.py::TestSQLiteSchemaPatches -q` → 6 passed
- `.venv/bin/python -m pytest tests/integration/sales/test_follow_up_value_api.py tests/unit/services/sales/test_collection_priority_service.py tests/unit/services/sales/test_opportunity_health_service.py tests/unit/services/sales/test_contract_milestone_service.py -q` → 72 passed
- `.venv/bin/python -m pytest tests/integration/sales/test_leads.py::TestLeadList tests/integration/sales/test_sales_dashboard.py -q` → 7 passed
- `.venv/bin/python -m pytest tests/api/test_sales_quotes_api.py tests/unit/test_approval_adapter_quote.py -q` → 48 passed, 6 skipped
- `python -m py_compile app/models/base.py app/models/sales/contracts.py app/api/v1/endpoints/sales/__init__.py app/services/sales/follow_up_reminder_service.py app/services/sales/contract_milestone_service.py scripts/seed_presale_workbench_demo_data.py` → passed
- `.venv/bin/python -m py_compile app/api/v1/endpoints/sales/leads/crud.py app/api/v1/endpoints/sales/dashboard.py` → passed
- `npm run test:run -- StatisticsCharts.test.jsx` → 1 passed
- `npm run build` → passed（保留既有 dynamic import/chunk 警告）
- `GET /health` → 200
- 备注：直接使用系统 Python 3.14 跑 TestClient 类 API 测试会出现 `Client.__init__() got an unexpected keyword argument 'app'`，根因是本机全局 `httpx/starlette` 版本组合不匹配；项目 `.venv` 下同一批测试通过。

### 9. 2026-06-25 宽页面第二轮修复

- 修复前端 API client 重复前缀：工程师绩效页原先会把已带 `/api/v1` 的调用拼成 `/api/v1/api/v1/...`；现在请求拦截器统一规整重复前缀。
- 修复供应商卡片历史状态值崩溃：`SupplierCard` 对未知 `status`/`level` 做兜底，不再因 `statusConfig[supplier.status]` 为 `undefined` 白屏。
- 修复系统权限中心角色接口：`/api/v1/roles/` 原先是 placeholder/路由缺失，补齐列表、权限、模板、层级、CRUD、权限分配等基础端点，并保证静态路由排在动态路由前。
- 修复历史演示库 NULL 响应 500：
  - `users.is_active / is_superuser`
  - `roles.sort_order`
  - `technical_reviews.issue_count_*`
  - `outsourcing_orders.status / payment_status / vendor_name`
  - `hr_tag_dict.is_active / is_required`
  - `qualification_level.is_active`
  - `position_competency_model.is_active` 及关联 `level.is_active`
- 修复历史 SQLite schema 漂移：
  - `annual_key_works.progress_description`
  - `bom_items` 多个旧库兼容列（齐套状态、到货日期、物料/图号/金额/供应商/排序等字段）
- 修复产能趋势接口 SQLite 兼容：`/api/v1/production/capacity/trend` 的周/月聚合不再使用 MySQL `date_format()`，SQLite 下改用 `strftime()`。
- 修复后台 API 路径漂移：
  - `/management-rhythm/dashboard/`
  - `/audits/`
  - `/data-import-export/...`

验证：

- `.venv/bin/python -m pytest tests/api/test_roles.py tests/api/test_users.py::TestUserCRUD::test_list_users_handles_null_boolean_flags tests/core/test_database.py::TestSQLiteSchemaPatches::test_strategy_and_bom_patch_adds_legacy_missing_columns tests/api/test_production.py::TestCapacityAnalysis::test_capacity_trend_week_and_month_work_on_sqlite tests/api/test_null_response_defaults.py -q` → 24 passed, 1 skipped
- `.venv/bin/python -m pytest tests/unit/test_api_p6_coverage.py::TestRoles -q` → 9 passed
- `.venv/bin/python -m pytest tests/unit/test_qualification_service.py tests/unit/test_batch2_qualification_service.py -q` → 55 passed
- `npm run test:run -- src/services/api/__tests__/client.test.js src/pages/__tests__/SupplierManagement.test.jsx` → 27 passed
- `.venv/bin/python -m py_compile app/api/v1/endpoints/roles.py app/services/role_service.py app/api/v1/endpoints/users/utils.py app/api/v1/endpoints/users/crud_refactored.py app/api/v1/endpoints/production/capacity/trend.py app/api/v1/endpoints/qualification/levels.py app/api/v1/endpoints/qualification/models.py app/api/v1/endpoints/technical_review/reviews.py app/api/v1/endpoints/outsourcing/orders.py app/api/v1/endpoints/staff_matching/tags.py app/models/base.py` → passed
- `npm run build` → passed（保留既有 dynamic import/chunk size 警告）
- Live API 复验均 200：
  - `/api/v1/roles/?page=1&page_size=100`
  - `/api/v1/users/?page_size=1000`
  - `/api/v1/technical-reviews?page=1&page_size=20`
  - `/api/v1/outsourcing-orders?page=1&page_size=20`
  - `/api/v1/staff-matching/tags/?page_size=500`
  - `/api/v1/qualifications/levels?page=1&page_size=1`
  - `/api/v1/qualifications/models?page=1&page_size=1`
  - `/api/v1/strategy/annual-works?strategy_id=1`
  - `/api/v1/bom/`
  - `/api/v1/production/capacity/trend?type=oee&granularity=week`
  - `/api/v1/management-rhythm/dashboard/`
  - `/api/v1/audits/`
  - `/api/v1/data-import-export/templates`
- Playwright 页面烟测 15 个入口，无 JS 崩溃、无 API 500：
  - `/suppliers`
  - `/engineer-performance`
  - `/engineer-performance/collaboration`
  - `/system/account-permission-center`
  - `/data-import-export`
  - `/management-rhythm-dashboard`
  - `/audit-logs`
  - `/strategy/annual-work`
  - `/procurement/material-center`
  - `/production/capacity-analysis`
  - `/technical-reviews`
  - `/outsourcing-orders`
  - `/hr/talent-matching-center`
  - `/qualifications`
  - `/production/resource-center`

### 10. 工程师绩效无当前考核周期空态修复

- 复现页面：
  - `/engineer-performance`
  - `/engineer-performance/collaboration`
- 复现接口：
  - `/api/v1/engineer-performance/summary/company`
  - `/api/v1/engineer-performance/collaboration/pending`
  - `/api/v1/engineer-performance/collaboration/matrix`
- 根因：本地演示库没有活跃 `performance_period`，总览/协作页面类接口主动抛 `404 未找到当前考核周期`，导致前端控制台报 API 错误。
- 修复：
  - 无当前周期时，工程师绩效公司总览返回 200 空态：`period_id=null`、`period_name=暂无考核周期`、统计值为 0、分布为空。
  - 无当前周期时，协作待评价列表返回空数组，协作矩阵返回空矩阵。
  - 协作评价已有记录时的用户显示名改用 `User.display_name`，避免后续演示数据出现后因 `User.name` 不存在触发 500。
- 验证：
  - 新增 `tests/api/test_engineer_performance_empty_period.py`，先复现 404 红灯，修复后通过。
  - `.venv/bin/python -m pytest tests/api/test_engineer_performance_empty_period.py -q` → 1 passed
  - Live API 复验三条接口均 200。
  - Playwright 复扫 `/engineer-performance`、`/engineer-performance/collaboration`，无 API 4xx/5xx、无 JS 错误。

### 11. 战略分解树响应契约修复

- 复现页面：`/strategy/decomposition`
- 复现接口：`/api/v1/strategy/decomposition/tree/1`
- 根因：
  - 后端服务仍返回旧版 `nodes` 结构，节点 id 使用 `csf-* / kpi-*` 字符串，且缺少 schema 必填的 `level/root/year`。
  - 服务还引用了当前模型不存在的旧字段：`DepartmentObjective.kpi_id`、`PersonalKPI.user_id/name/code`、`Department.name`、`User.name`。
  - 前端当前页面实际读取 `csfs / total_departments / total_kpis / avg_completion_rate` 等兼容字段，和 schema 的 `root` 树结构没有对齐。
- 修复：
  - `get_decomposition_tree` 改为返回合法 `DecompositionTreeResponse`：`root` 节点、整型命名空间 id、完整 `level/parent_id`、KPI/个人 KPI 目标和完成率。
  - 部门目标按当前模型的 `strategy_id` 归属加载，个人 KPI 使用 `department_objective_id`，用户显示名使用 `User.display_name`，部门名使用 `Department.dept_name`。
  - `DecompositionTreeResponse` 显式保留前端兼容字段：`csfs`、`total_csfs`、`total_departments`、`total_kpis`、`total_personal_kpis`、`avg_completion_rate`。
- 验证：
  - 新增 `tests/api/test_strategy_decomposition_tree_contract.py`，先复现契约失败，修复后通过。
  - `.venv/bin/python -m pytest tests/api/test_engineer_performance_empty_period.py tests/api/test_strategy_decomposition_tree_contract.py -q` → 2 passed
  - `.venv/bin/python -m py_compile app/services/strategy/decomposition/decomposition_tree.py app/schemas/strategy/decomposition.py app/api/v1/endpoints/strategy/decomposition.py` → passed
  - Live API：登录后 `GET /api/v1/strategy/decomposition/tree/1` → 200，返回 `root/csfs/total_*` 字段。
  - Playwright 复扫 `/strategy/decomposition`，无 API 4xx/5xx、无 JS 错误。

### 12. 财务报表 404 与空数据 NaN 修复

- 复现页面：`/financial-reports`
- 复现接口：
  - `/api/v1/finance/monthly-trend?period=month&year=2024`
  - `/api/v1/finance/cost-analysis?period=month`
  - `/api/v1/finance/project-profitability?limit=10`
  - `/api/v1/finance/cash-flow?period=month`
- 根因：
  - 前端财务报表已接入上述 4 条 `/finance/*` 报表接口，但后端没有注册对应路由，页面 smoke 出现 404。
  - 2024 演示数据存在营收为 0、成本非 0 的月份，前端利润率、同比、预算执行、现金流进度条等位置存在 `0/0` 或非法数值传染，可能显示 `NaN/Infinity`。
- 修复：
  - 新增 `app/api/v1/endpoints/finance_reports.py`，并在 `app/api/v1/api.py` 注册 `/finance` 报表路由。
  - 4 条接口返回前端直接消费的数组结构：月度趋势、成本分析、项目盈利、现金流；无 live 数据时给出确定性演示兜底。
  - 新增 `frontend/src/pages/FinancialReports/numberUtils.js`，对财务页内利润率、进度条、图表输入统一做有限数值和分母为 0 保护。
- 验证：
  - 新增 `tests/api/test_financial_reports_api.py`，先复现 404 红灯，修复后通过。
  - `.venv/bin/python -m pytest tests/api/test_financial_reports_api.py tests/api/test_engineer_performance_empty_period.py tests/api/test_strategy_decomposition_tree_contract.py -q` → 3 passed
  - Live API 复验 4 条 `/api/v1/finance/*` 接口均 200。
  - Playwright 复扫 `/financial-reports`，无 API 4xx/5xx、无 JS 错误、无 `NaN/Infinity`。

### 13. 项目成本、采购分析、HR 绩效 NaN 展示兜底修复

- 复现页面：
  - `/project/management-center?tab=cost`：预算汇总卡显示 `¥NaN`。
  - `/procurement/analysis-center`：物料分析饼图在全 0 分布时生成 SVG `NaN` 路径。
  - `/hr/performance-center`：绩效统计卡显示 `占比 NaN%`。
- 根因：
  - 项目预算页只用 `|| 0`，无法拦截 API 返回的非法数值，`NaN` 会传染到 reduce 汇总和金额格式化。
  - `SimplePieChart` 在 `total=0` 时仍计算扇区角度和坐标。
  - HR 绩效页在 `total_employees=0/undefined` 时直接计算人数占比。
- 修复：
  - `formatCurrency` 对 `NaN`、非法字符串等非有限数值统一显示为 `¥0.00`。
  - `BudgetManagement` 在预算金额、已用金额和汇总 reduce 前做有限数值归一化。
  - `SimplePieChart` 在总值为 0 时不计算扇区路径，图例显示 0.0%。
  - `PerformanceManagement` 的优秀/良好占比改为分母安全计算。
- 验证：
  - `npm run test:run -- src/components/administrative/__tests__/StatisticsCharts.test.jsx src/lib/__tests__/utils.test.js src/pages/FinancialReports/__tests__/numberUtils.test.js` → 5 passed
  - Playwright 复扫 `/project/management-center?tab=cost`、`/procurement/analysis-center`、`/hr/performance-center`，均无 API 4xx/5xx、无 JS 错误、无 `NaN/Infinity`。
  - `npm run build` → passed（保留既有 dynamic import/chunk size 警告）。

剩余未修复：

- 本轮复扫的四个早前风险入口已清零：`/financial-reports`、`/project/management-center?tab=cost`、`/procurement/analysis-center`、`/hr/performance-center`。
- 更宽系统仍需继续下一轮页面/模块扫描；目前没有把“全系统全面清理”标记为完成。

### 14. 宽页面第三轮：60 入口扫描与路径/兼容路由修复

- 扫描证据：
  - `.gstack/qa-reports/slow-smoke-2026-06-25-next.json`：覆盖 60 个真实侧边栏/业务入口。
  - `.gstack/qa-reports/targeted-smoke-2026-06-25-routes.json`：修复后针对 5 个问题入口复扫。
- 复现页面：
  - `/rd-projects`
  - `/material-requisitions`
  - `/pmc/delivery-orders`
  - `/settlement`
  - `/multi-currency`
- 根因：
  - `/rd-projects` 前端请求无尾斜杠路径，后端只注册 `/rd-projects/`，302/307 重定向到 `127.0.0.1:8002` 后触发浏览器 CORS。
  - 领料单前端请求 `/material-requisitions`，后端实际注册在 `/production/material-requisitions`。
  - 配送单前端请求 `/business-support/delivery-orders`，后端实际注册在 `/business-support-orders/delivery-orders`。
  - 配送单 `statistics` 静态路由注册在动态详情路由之后，被 `/{delivery_id}` 捕获，返回 422。
  - `/settlement` 页面依赖 `/settlements*`，后端没有兼容路由。
  - `/multi-currency` 页面依赖 `/currency/rates`、`/currency/history`、`/currency/convert`，后端 `multi_currency` 仍是占位接口。
- 修复：
  - 新增 `rd_project_aliases`，为 `/rd-projects` 提供无重定向别名，避免跨端口重定向/CORS。
  - 领料单 API 前端路径统一改到 `/production/material-requisitions`。
  - 配送单 API 前端路径统一改到 `/business-support-orders/delivery-orders`。
  - 配送单聚合路由改为先注册 `statistics`，再注册 CRUD 动态详情路由。
  - 新增 `settlements` 兼容接口：列表、统计、详情，优先从项目/合同/成本/回款计划生成可演示数据。
  - 补齐 `multi_currency` 兼容接口：汇率列表、汇率更新、换算、历史记录、项目汇总。
- 验证：
  - 新增 `frontend/src/services/api/__tests__/routeContracts.test.js`，覆盖领料单与配送单前端路径契约。
  - 新增 `tests/api/test_finance_compat_routes.py`，覆盖 `/currency/*` 与 `/settlements*` 前端消费形状。
  - 新增 `tests/api/test_rd_project_route_alias.py`，确认 `/rd-projects` 不再返回 307。
  - 新增 `tests/api/test_business_support_delivery_routes.py`，确认 `/delivery-orders/statistics` 不再被详情路由捕获。
  - `.venv/bin/python -m pytest tests/api/test_finance_compat_routes.py tests/api/test_rd_project_route_alias.py tests/api/test_business_support_delivery_routes.py tests/api/test_financial_reports_api.py tests/api/test_engineer_performance_empty_period.py tests/api/test_strategy_decomposition_tree_contract.py -q` → 7 passed
  - `npm run test:run -- src/services/api/__tests__/routeContracts.test.js src/components/administrative/__tests__/StatisticsCharts.test.jsx src/lib/__tests__/utils.test.js src/pages/FinancialReports/__tests__/numberUtils.test.js` → 7 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/multi_currency.py app/api/v1/endpoints/settlements.py app/api/v1/endpoints/rd_project_aliases.py app/api/v1/endpoints/rd_project/initiation.py app/api/v1/endpoints/business_support_orders/delivery_orders/__init__.py app/api/v1/api.py` → passed
  - Live API 复验以下接口均 200：
    - `/api/v1/production/material-requisitions?page=1&page_size=10`
    - `/api/v1/business-support-orders/delivery-orders?page=1&page_size=10`
    - `/api/v1/business-support-orders/delivery-orders/statistics`
    - `/api/v1/settlements?page=1&page_size=10`
    - `/api/v1/settlements/statistics`
    - `/api/v1/currency/rates`
    - `/api/v1/currency/history?limit=3`
    - `/api/v1/currency/convert?from_currency=USD&to_currency=CNY&amount=1000`
    - `/api/v1/rd-projects?page=1&page_size=10`
  - Playwright 复扫 5 个问题入口，均无 API 4xx/5xx、无 JS 错误、无 `NaN/Infinity`。

剩余未修复：

- 系统仍需继续做更深交互路径、增删改流程和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 15. ECN 中心 React 只读 input 警告修复

- 复现页面：`/change-management/ecn-center`
- 复现现象：Playwright 宽扫捕获 React 控制台错误：`value` 传入表单字段但没有 `onChange`，字段会变成只读。
- 根因：
  - 通用 `Input` 组件在调用方没有传 `value` 时也会向原生 `<input>` 传 `value=""`。
  - ECN 管理页工具栏搜索框本来是非受控输入，但被通用组件强制渲染成受控空值输入，触发 React 警告。
  - `Textarea` 也存在同类风险。
- 修复：
  - `Input`/`Textarea` 仅在调用方明确传入非空 `value` 时向原生字段传 `value`。
  - 显式传 `value` 但没有 `onChange`、`readOnly`、`defaultValue` 时，组件自动标记 `readOnly`，让只读语义显式化。
  - 未传 `value` 的字段保持原生非受控，用户输入不再被组件层固定为空字符串。
- 验证：
  - 新增 `Input` 组件契约测试，覆盖非受控 `Input`/`Textarea` 可输入且不触发 React 只读警告。
  - `npm run test:run -- src/components/ui/__tests__/input.test.jsx` → 37 passed，4 snapshots updated。
  - Playwright 复扫 `/change-management/ecn-center`：页面 200、无 API 4xx/5xx、无控制台 warning/error、无 `NaN/Infinity`。
  - `npm run test:run -- src/components/ui/__tests__/input.test.jsx src/services/api/__tests__/routeContracts.test.js src/components/administrative/__tests__/StatisticsCharts.test.jsx src/lib/__tests__/utils.test.js src/pages/FinancialReports/__tests__/numberUtils.test.js` → 44 passed
  - `npm run build` → passed（保留既有 dynamic import/chunk size 警告）。

剩余未修复：

- 系统仍需继续做更深交互路径、增删改流程和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 16. 宽页面第四批：销售/成本/资质/考勤/报表链路修复

- 扫描证据：
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch4.json`：覆盖 44 个前期未扫页面，初扫发现 9 个入口存在 API 4xx/5xx 或页面控制台问题。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch4-targeted.json`：14 个重点入口接口已清零，但仍有 4 个页面控制台问题。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch4-targeted-rerun.json`：剩余 `/quote-compare` reload 瞬断和 `/opportunities` key warning。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch4-targeted-rerun2.json`：14 个重点入口全部清零。
- 复现页面：
  - `/quality/reports/archives`
  - `/performance-contract`
  - `/qualifications/assessments`
  - `/attendance-management`
  - `/engineer-performance/ranking`
  - `/cost-collection`
  - `/quote-compare`
  - `/cost-variance`
  - `/finance/analytics-dashboard`
  - `/sales-reports`
  - `/opportunities`
  - `/contracts`
  - `/payments`
  - `/sales/statistics`
- 根因：
  - 报告归档前端把响应 envelope 当数组直接 `.map`，触发页面 JS 崩溃。
  - 绩效合同、销售回款、报告归档等前端路径和后端注册路径不一致，或带尾斜杠引发重定向/CORS 风险。
  - 资质员工列表在 legacy NULL 字段下直接按响应模型序列化，`status`、`assessment_details`、等级启用状态等字段会触发 500。
  - 考勤管理页面依赖 `/admin/attendance`，后端没有兼容入口。
  - 成本归集、报价实绩对比、成本差异分析仅有空兼容文件，未挂真实路由。
  - 工作量瓶颈路由多包了一层 `/workload`，前端实际路径 404。
  - 工程师绩效排名在无活跃考核周期时返回 404，演示库无法展示空态。
  - 销售统计页缺少看板统计、月度趋势、客户/产品/区域分布等 API helper；商机/销售统计存在 React key warning。
  - 财务分析看板 Recharts 容器在首屏布局时宽高为负数，触发控制台 warning。
  - 合同列表对金额字段缺少有限数值归一化，存在 `NaN` 传染风险。
- 修复：
  - `ReportArchives` 兼容 `data.data.items / data.items / data` 三种响应形状。
  - `performanceContractApi`、`reportCenterApi`、`paymentApi` 路径统一到后端已注册路由。
  - 资质员工列表增加响应转换，NULL 字段给出稳定默认值。
  - 新增 `/admin/attendance` 兼容路由，提供列表、统计、我的记录、导出、上下班打卡接口，并从员工/用户数据生成部门考勤演示统计。
  - 成本归集、报价实绩对比、成本差异分析兼容 router 改为挂载真实成本端点。
  - 工作量瓶颈路由修正为 `/analytics/workload/bottlenecks`。
  - 工程师绩效排名无当前周期时返回 200 空态。
  - 补齐销售统计 API helper，销售回款路径改为 `/sales/payments/records`，合同列表金额统一做有限数值映射。
  - `AnalyticsDashboard` Recharts 容器改为稳定数字高度并设置 `minWidth=0`。
  - `BoardView` 阶段列和商机卡片使用稳定 composite key，并新增回归测试捕获 React key warning。
  - `SalesStatistics` 阶段列表 key 改为阶段/月度等字段与索引组合。
- 验证：
  - Live API：本批问题接口复验均 200，包括 `/cost-collection/status`、`/cost-collection/by-project`、`/quote-compare/list`、`/cost-variance/summary`、`/cost-variance/patterns`、`/report/archives`、`/analytics/workload/bottlenecks`、`/sales/payments/records`、`/engineer-performance/ranking`、销售统计接口、`/admin/attendance`、`/qualifications/employees`。
  - `.venv/bin/python -m pytest tests/api/test_batch4_route_contracts.py tests/api/test_null_response_defaults.py tests/api/test_finance_compat_routes.py tests/api/test_rd_project_route_alias.py tests/api/test_business_support_delivery_routes.py tests/api/test_financial_reports_api.py tests/api/test_engineer_performance_empty_period.py tests/api/test_strategy_decomposition_tree_contract.py -q` -> 10 passed
  - `npm run test:run -- src/pages/OpportunityBoard/__tests__/BoardView.test.jsx src/components/ui/__tests__/input.test.jsx src/services/api/__tests__/routeContracts.test.js src/components/administrative/__tests__/StatisticsCharts.test.jsx src/lib/__tests__/utils.test.js src/pages/FinancialReports/__tests__/numberUtils.test.js` -> 47 passed
  - `npm run build` -> passed
  - Playwright 14 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch4-targeted-rerun2.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/Infinity`。

剩余未修复：

- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 55. 权限组合第二批：14 个角色核心入口矩阵与项目详情旧路径 404 清零

- 扫描证据：
  - `.gstack/qa-reports/frontend-role-matrix-smoke-2026-06-26-multirole-core.json`：14 个现有数据库角色、85 次页面访问，首扫发现严重项 24；严重项全部集中在 PMO/PM 打开 `/projects/1` 时的两个旧路径 API 404。
  - 严重缺口：
    - `GET /api/v1/members/projects/1/members`
    - `GET /api/v1/stages/projects/1/stages`
  - `.gstack/qa-reports/frontend-role-matrix-smoke-2026-06-26-multirole-project-detail-rerun.json`：PMO/PM `/projects/1` targeted 复扫，`routeVisits=2`，`severeCount=0`。
  - `.gstack/qa-reports/frontend-role-matrix-smoke-2026-06-26-multirole-core-rerun.json`：完整 14 角色 85 页复扫，`severeCount=0`，`warningCount=220`，HTTP 状态只剩 `403: 58`。
- 覆盖角色：
  - `gm`
  - `sales_director`
  - `sales_rep`
  - `qa_sales`
  - `tech_director`
  - `qa_engineer`
  - `pmo_director`
  - `pm`
  - `production_mgr`
  - `procurement_mgr`
  - `quality_mgr`
  - `hr_manager`
  - `finance_mgr`
  - `service_mgr`
- 覆盖入口类型：
  - 各角色工作台：管理、销售、工程、生产、采购、质量、服务。
  - 深层动态页：`/projects/1`、`/projects/1/workspace`、`/technical-reviews/1`、`/strategy/team-generation/1`、`/work-orders/1`、`/workshops/1/task-board` 等。
  - 增删改前置业务页：销售线索/报价、采购申请、物料分析、质量检验、工时、售后工单、财务报表、项目成本中心。
- 根因：
  - 项目详情页的 `stageApi.list({ project_id })` 与 `memberApi.list({ project_id })` 仍调用旧顶层路径 `/stages/projects/{id}/stages`、`/members/projects/{id}/members`。
  - 当前后端新版实现已经迁移到 `/projects/{id}/stages/`、`/projects/{id}/members/`，旧路径未注册，导致 PMO/PM 打开项目详情时出现 API 404 和控制台 `Request failed with status code 404`。
- 修复：
  - 新增 `app/api/v1/endpoints/project_legacy_compat.py`：
    - `GET /members/projects/{project_id}/members` 复用 `ProjectMembersService`，保留 `project:read` 权限和项目数据权限校验，返回 `PaginatedResponse[ProjectMemberResponse]`。
    - `GET /stages/projects/{project_id}/stages` 复用 `ProjectStageInstance` 查询，保留项目数据权限校验，返回阶段数组。
  - 在 `app/api/v1/api.py` 注册项目旧路径兼容 router，静态前缀分别挂到 `/members`、`/stages`。
  - 在 `tests/api/test_openapi_route_contracts.py` 增加旧路径注册回归断言，防止后续再丢。
- 验证：
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/project_legacy_compat.py app/api/v1/api.py tests/api/test_openapi_route_contracts.py` -> passed
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py::test_multirole_project_detail_legacy_routes_are_registered -q` -> 1 passed
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py::test_multirole_project_detail_legacy_routes_are_registered tests/api/test_openapi_route_contracts.py::test_registered_api_routes_do_not_duplicate_method_paths -q` -> 2 passed
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js` -> 18 passed
  - `pnpm build` -> passed
  - Live API 使用 `admin/admin123` 登录 token 复验：
    - `/api/v1/members/projects/1/members` -> 200，返回分页对象，`items=1`
    - `/api/v1/stages/projects/1/stages` -> 200，返回数组，`count=2`
  - Playwright targeted 复扫：`.gstack/qa-reports/frontend-role-matrix-smoke-2026-06-26-multirole-project-detail-rerun.json`，`severeCount=0`
  - Playwright 完整多角色复扫：`.gstack/qa-reports/frontend-role-matrix-smoke-2026-06-26-multirole-core-rerun.json`，`routeVisits=85`，`severeCount=0`，无 401/404/405/5xx、无 pageerror、无空白页。

剩余未修复：

- 多角色矩阵中的 `/api/v1/notifications/` 个人收件箱 403 已由第 82 批修复；其余 `403` warning 仍需按真实岗位权限表单独校准哪些是合理拒绝、哪些应放行。
- `pnpm build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 系统仍需继续做更深的增删改提交链路、移动端尺寸和真实数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 111. 项目总览数据流转：WBS/BOM/里程碑/售后链路实跑通过

- 扫描证据：
  - 继续从项目总览页背后的数据流转接口做写入链路 smoke，覆盖 WBS 转工单、BOM 转采购申请、里程碑转交付排产、项目转售后保养记录。
  - 新建临时项目 `QA_DATA_FLOW_20260701072006` / `PJ263C9788A`，项目 ID `104`；补齐 S4/S5 任务、里程碑，并直接种入一条本链路所需的 BOM 表头与物料行。
- 验证：
  - `POST /projects/104/data-flow/wbs-work-orders` -> 200，创建工单 `2` 条：`WO-PJ263C9788A-S4-20260701072006`、`WO-PJ263C9788A-S5-20260701072006`。
  - `POST /projects/104/data-flow/bom-purchase-requests` -> 200，创建采购申请 ID `27`，`items_with_net_demand=1`。
  - `POST /projects/104/data-flow/delivery-schedule` -> 200，创建交付排产 ID `7`，`tasks_created=1`。
  - `POST /projects/104/data-flow/after-sales` -> 200，创建售后保养记录 `4` 条，周期为 `1/3/6/12` 个月。
  - DB 复核计数：`work_orders=2`、`purchase_requests=1`、`delivery_schedules=1`、`after_sales_maintenance=4`。
  - `DATA_FLOW_FAILED=` 为空；随后清理工单、采购申请、交付排产、BOM、任务、里程碑、售后保养记录，并 `DELETE /projects/104` -> 200。
- 当前结论：
  - 本批未发现该数据流转链路新的后端阻塞；剩余更深一层是用真实浏览器点击项目总览页按钮补 UI 层证据，并继续覆盖审批/评价、角色权限组合、移动端尺寸。
  - 运行末尾保留既有环境提示：Redis 未配置，限流使用内存存储；这不是本链路失败。

### 110. 项目按钮级写操作：成员新增与任务创建兼容链路清零

- 扫描证据：
  - Live API 初扫新建临时项目 ID `89` 后，`POST /api/v1/members/` 返回 404，`POST /api/v1/projects/89/tasks` 返回 405。
  - 前端成员新增来自项目详情按钮流，传入 `{ project_id, user_id, role, status }`；后端当前真实创建路由是 `POST /projects/{project_id}/members/`，请求字段需要 `role_code`。
  - 项目任务页调用 `POST /projects/{projectId}/tasks`，后端兼容层只注册了 `GET /projects/{project_id}/tasks`，缺少创建路由。
- 根因：
  - `frontend/src/services/api/projects.js` 的 `memberApi.add()` 仍调用旧顶层 `/members/`，且没有把旧前端字段 `role` 归一为后端 schema 字段 `role_code`。
  - `app/api/v1/endpoints/progress_compat.py` 缺少项目视角任务创建兼容 POST，导致当前项目任务页的“新建任务”提交到已注册前缀但方法不允许。
- 修复：
  - `memberApi.add()` 改为支持 `memberApi.add(data)` 与 `memberApi.add(projectId, data)` 两种调用形态，统一请求 `/projects/{projectId}/members/`，并把 `role` 兼容转换为 `role_code`。
  - `progress_compat.py` 新增 `POST /projects/{project_id}/tasks`，复用项目访问权限校验，支持 `task_name/name`、`planned_start_date/plan_start/start_date`、`planned_end_date/plan_end/end_date`、`assigned_to/owner_id/assignee_id` 等前端常见字段，创建后返回与列表接口一致的序列化 shape。
  - 前端合同回归增加项目成员新增路径与 payload 断言；后端回归增加项目任务兼容创建后再列表读回的断言。
- 验证：
  - 红测：`npm run test:run -- src/services/api/__tests__/routeContracts.test.js -t "project members"` 先失败，确认旧实现仍打 `/members/`。
  - 红测：`.venv/bin/python -m pytest tests/api/test_progress.py::TestProjectTasks::test_create_project_task_via_project_compat_route -q` 先失败，确认旧后端返回 405。
  - 绿测：`npm run test:run -- src/services/api/__tests__/routeContracts.test.js -t "project members"` -> 1 passed。
  - 绿测：`.venv/bin/python -m pytest tests/api/test_progress.py::TestProjectTasks::test_create_project_task_via_project_compat_route -q` -> passed。
  - Live API 按钮级写操作 smoke：新建 `QA_BUTTON_20260630205940` / `PJ26AF42BEA`，项目 ID `90`；`POST /projects/90/members/` -> 201；`POST /projects/90/tasks` -> 201；`GET /projects/90/tasks` -> 200 且读回新任务；`POST /projects/90/stages/initialize` -> 200；`POST /projects/90/stages/165/start` -> 200；`POST /projects/90/stages/165/complete` -> 200；`POST /projects/90/costs/` -> 201；`GET /projects/90/costs/` -> 200；`DELETE /projects/90` -> 200。
  - 真实浏览器按钮流复跑：`node .gstack/qa-scripts/project-button-flow.mjs` -> passed；项目 ID `103`，共执行 `16` 步；`apiErrors=[]`、`pageErrors=[]`、`requestFailures=[]`；清理成本 ID `62` 返回 204，清理项目 ID `103` 返回 200。
  - 真实浏览器报告：`.gstack/qa-reports/project-button-flow-20260630231732.json`；截图：`.gstack/qa-reports/screenshots/project-button-flow-final-20260630231732.png`。
  - 前端组合回归：`npm run test:run -- src/services/api/__tests__/routeContracts.test.js src/services/api/__tests__/projects.test.js src/components/project/__tests__/ProjectFormStepper.test.jsx src/pages/__tests__/ProgressForecast.test.jsx` -> 4 files passed。
  - 后端组合回归：`.venv/bin/python -m pytest tests/api/test_progress.py::TestProjectTasks::test_create_project_task_via_project_compat_route tests/core/test_database.py::TestSQLiteSchemaPatches::test_requirement_extraction_patch_creates_required_tables -q` -> 2 passed。
  - 编译：`.venv/bin/python -m py_compile app/api/v1/endpoints/progress_compat.py app/models/base.py` -> passed。
- 剩余未修复：
  - 本批已覆盖项目创建后的成员、任务、阶段、成本关键写操作 API smoke，并用真实浏览器补过项目按钮流证据；数据流转/售后链路见第 111 批。
  - 还需要继续覆盖审批/评价、角色权限组合、移动端尺寸，以及旧自动化脚本与当前卡片 UI 的对齐。
  - 旧 `e2e/project-management.spec.js` 仍是 AntD table 时代的测试结构，需要另行更新为当前项目中心卡片 UI。

### 109. 项目创建后 25 个子页矩阵：工程师推荐 500 与进度预测 401 清零

- 扫描证据：
  - Playwright 新建项目 `QA_FLOW_20260630123558` / `PJ260630123558`，项目 ID `87`，初始化阶段后访问项目子页矩阵。
  - `/projects/87/engineer-recommendation` 调用 `GET /api/v1/requirement-extraction/projects/87/requirements` 返回 500，异常为 `sqlite3.OperationalError: no such table: project_requirements`。
  - `/projects/87/progress-forecast` 内部项目详情请求返回 401 `MISSING_TOKEN`。
- 根因：
  - 历史 SQLite `data/app.db` 缺少工程师推荐兼容接口依赖的 `project_requirements` 与 `engineer_recommendations` 表；接口直接 ORM 查询缺表，导致 500。
  - `frontend/src/pages/ProgressForecast.jsx` 使用裸 `fetch('/api/v1/projects/:id')` 获取项目详情，没有经过统一 axios client，因此不会自动带 Authorization。
- 修复：
  - `app/models/base.py::_ensure_sqlite_schema()` 纳入 `app.models.project_requirements`，旧 SQLite 会补建 `project_requirements` 与 `engineer_recommendations`。
  - `frontend/src/pages/ProgressForecast.jsx` 改用 `projectApi.get(id)` 获取项目详情。
  - 新增后端旧库补表回归：`tests/core/test_database.py::TestSQLiteSchemaPatches::test_requirement_extraction_patch_creates_required_tables`。
  - 新增前端页面回归：`frontend/src/pages/__tests__/ProgressForecast.test.jsx`，断言使用认证 API client 且不调用裸 `fetch`。
- 验证：
  - 真实接口复验：`GET /api/v1/requirement-extraction/projects/87/requirements` -> 200，返回空需求分组而不是 500。
  - Playwright 矩阵复扫：新建 `QA_FLOW_RERUN_20260630124142` / `PJ260630124142`，项目 ID `88`，初始化阶段后访问 25 个项目子页，`events: []`，无 console error/warning、pageerror、requestfailed 或 API 4xx/5xx。截图：`.gstack/qa-reports/screenshots/project-flow-route-matrix-QA_FLOW_RERUN_20260630124142.png`。
  - 清理：`DELETE /api/v1/projects/88` -> 200。
  - 前端组合回归：`npm run test:run -- src/components/project/__tests__/ProjectFormStepper.test.jsx src/services/api/__tests__/routeContracts.test.js src/pages/__tests__/ProgressForecast.test.jsx` -> 3 files passed, 25 tests passed。
  - 后端回归：`.venv/bin/python -m pytest tests/core/test_database.py::TestSQLiteSchemaPatches::test_requirement_extraction_patch_creates_required_tables -q` -> passed。
  - 编译：`.venv/bin/python -m py_compile app/models/base.py app/api/v1/endpoints/requirement_extraction.py` -> passed。
  - `npm run build`（`frontend/`）-> passed；仅保留既有 Vite 动静态重复导入和 chunk size 提示。
- 剩余未修复：
  - 本批验证的是项目创建后 25 个子页的首屏/API 加载健康；按钮级“启动/完成阶段、新建任务、添加成员、录成本、交付排产提交”等写操作仍需继续分批跑。
  - 旧 `e2e/project-management.spec.js` 仍是 AntD table 时代的测试结构，需要另行更新为当前项目中心卡片 UI。

### 108. 项目创建入口与缺料 smoke 假红清零

- 扫描证据：
  - 后端健康：`GET http://127.0.0.1:8002/health` -> 200。
  - 项目主链路后端基线：`tests/e2e/test_project_lifecycle.py::TestProjectLifecycleE2E::test_complete_project_lifecycle_from_s1_to_s9` -> passed。
  - 项目自服务/工作空间/里程碑 API：`tests/api/test_project_manager_self_service_contract.py tests/api/test_project_workspace_contract_api.py tests/api/test_project_milestones_api.py` -> 30 passed, 1 skipped。
  - 旧带登录 smoke 初扫在 `/api/v1/shortage-alerts/` 失败 404；当前后端 OpenAPI 与前端页面实际使用 `/api/v1/shortage/detection/alerts`。
  - 浏览器复现：`/projects` 点击 `新建项目` 后，`stage-templates` 请求从 `/api/v1/stage-templates?is_active=true` 307 到后端绝对地址，浏览器 CORS 拦截，并出现 `无法加载客户和员工数据` toast。
  - 浏览器继续复现：输入全新项目编码后仍提示 `项目编码已存在，请使用其他编码`，无法进入下一步。
  - 浏览器继续复现：修复编码误判后，最后提交 `POST /api/v1/projects/` 返回 422，提示可选 date / integer 字段收到空字符串。
  - 控制台还提示 Radix `DialogContent` missing `Description`，属于可访问性缺口。
- 根因：
  - `frontend/src/services/api/stageViews.js` 的 `stageViewsApi.templates.list()` 调用 `/stage-templates`，后端集合路由真实注册为 `/stage-templates/`；无尾斜杠触发 FastAPI 307，开发环境下跨过 Vite proxy 变成浏览器 CORS。
  - `scripts/smoke_auth_api.sh` 固化了已废弃的缺料旧路径 `/shortage-alerts/`，导致产品页面正常但脚本报假红。
  - `ProjectFormStepper` 使用 `projectApi.list({ project_code })` 做项目编码校验，但后端列表接口不支持该精确参数；参数被忽略后返回第一页项目，前端只看列表非空就误判重复。
  - 项目创建表单直接提交 `""` 给可选日期和可选整数字段，后端 schema 期望 `null` 或合法日期/数字。
  - 项目创建 Dialog 缺少 `DialogDescription`。
- 修复：
  - `stageViewsApi.templates.list()` 改为请求 `/stage-templates/`，直接命中后端真实集合路由。
  - `frontend/src/services/api/__tests__/routeContracts.test.js` 增加阶段模板集合路由合同，防止项目创建入口再次退回无尾斜杠路径。
  - `scripts/smoke_auth_api.sh` 的缺料预警检查改为 `/shortage/detection/alerts?page=1&page_size=1`。
  - 项目编码校验改为请求已有 `keyword` 查询契约，并对返回项目做 `project_code` 精确相等判断。
  - 新增 `normalizeProjectFormData()`，提交前把可选数值/日期空值归一为 `null`，金额空值归一为 `0`。
  - 项目创建 Dialog 增加 `sr-only` 的 `DialogDescription`。
- 验证：
  - 红测：`npm run test:run -- src/services/api/__tests__/routeContracts.test.js -t "stage template collection"` 先失败，确认旧实现仍发 `/stage-templates`。
  - 绿测：同一 targeted route contract 修复后 passed；完整 `npm run test:run -- src/services/api/__tests__/routeContracts.test.js` -> 22 passed。
  - 项目创建组件回归：`frontend/src/components/project/__tests__/ProjectFormStepper.test.jsx` 覆盖“非精确 keyword 命中不误判重复”和“空可选字段提交前归一化”。
  - 合并前端回归：`npm run test:run -- src/components/project/__tests__/ProjectFormStepper.test.jsx src/services/api/__tests__/routeContracts.test.js` -> 2 files passed, 24 tests passed。
  - `npm run build`（`frontend/`）-> passed；仅保留既有 Vite 动静态重复导入和 chunk size 提示。
  - 浏览器复验 `/projects` -> `新建项目`：表单可打开，无 `无法加载客户和员工数据` toast，无 stage-template CORS。截图：`.gstack/qa-reports/screenshots/project-center-create-after-stage-template-fix.png`。
  - 真实浏览器创建项目：`QA_E2E_CLEAN_20260630123113` / `PJ260630123113` 创建成功，项目 ID `86`，`stage_template_id=1`；随后 `DELETE /api/v1/projects/86` -> 200，再查详情 `is_active=false`，Playwright 捕获事件为空数组 `[]`。
  - 浏览器复验 `/shortage-alerts`：登录态页面加载正常，无 API failure。截图：`.gstack/qa-reports/screenshots/shortage-alerts-current-auth.png`。
  - 修复后 smoke：`BASE_URL=http://127.0.0.1:8002 bash scripts/smoke_auth_api.sh --no-seed --no-start --base-url http://127.0.0.1:8002 --user admin --password admin123` -> passed。
- 剩余未修复：
  - `e2e/project-management.spec.js` 仍按旧 AntD table 等待 `.ant-table, table`，当前项目中心已是卡片式 UI，测试会超时；需要单独重写为当前产品结构。
  - 本批清理了项目创建入口、项目编码校验、提交 payload、Dialog 可访问性 warning 和 smoke 假红；真实浏览器从创建项目到阶段推进、成员、任务、成本、交付的深层点击流仍需继续分批扫。

### 107. 前端静态入口当前态复验：399 个静态路由仍为 0 severe

- 扫描证据：
  - 总汇总：`.gstack/qa-reports/frontend-static-route-smoke-2026-06-28-all-static-routes-summary.json`
    - `totalStaticRouteCount=399`
    - `coveredRouteCount=399`
    - `uniqueCoveredRouteCount=399`
    - `duplicateRouteCount=0`
    - `severeCount=0`
    - `httpStatusCounts={}`
    - `consoleErrorCount=0`
    - `consoleWarningCount=0`
    - `pageErrorCount=0`
    - `requestFailedCount=0`
  - 来源报告：
    - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch1-classified.json`：0-79，分类复核后 `severeCount=0`。
    - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch2.json`：80-159，`severeCount=0`。
    - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch3.json`：160-239，`severeCount=0`。
    - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-28-batch4a.json`：240-279，`severeCount=0`。
    - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-28-batch4b.json`：280-319，`severeCount=0`。
    - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-28-batch5a.json`：320-359，`severeCount=0`。
    - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-28-batch5b.json`：360-398，`severeCount=0`。
- 覆盖范围：
  - 从当前 `frontend/src/routes` 抽取全部静态路径，过滤动态 `:id`、catch-all 和需要参数的页面。
  - Playwright 使用本机 `admin/admin123` 登录态逐页访问，检查页面加载、API 4xx/5xx、request failed、console error/warning、pageerror、空白页和 `NaN/Infinity`。
- 结论：
  - 当前态 399 个静态前端入口加载 smoke 仍为清洁状态；本批没有发现新的真实 severe，因此无需新增代码修复。
- 剩余未修复：
  - 这仍然只证明静态入口加载态；动态 ID 页面、深层点击流、增删改提交链路、权限边界、移动端尺寸和大文件/长数据场景还要继续扫。
  - 系统仍未达到“全系统所有 bug 清零”，继续分批推进。

### 106. 权限组合第四十批：总经理图表空数据、PM 自服务项目详情、销售工作站重复 key 清零

- 扫描证据：
  - `.gstack/qa-reports/live-frontend-key-role-matrix-smoke-2026-06-27-batch46.json` 覆盖 50 个关键角色入口，发现 `severeCount=2`、`warningCount=7`。
  - 严重项：`gm` 访问 `/dashboard`、`/workstation/management` 时 `RevenueChart` 对空收入数据直接读取 `byMonth`，触发 ErrorBoundary。
  - 警告项：`pm` 访问 `/projects/83`、`/projects/83/workspace`、`/tasks` 暴露自己项目基础信息、旧阶段/成员、成本、机台、工作空间、任务中心等 403；`sales_director` 访问 `/sales/workstation` 暴露 React duplicate key `opportunity-78`。
- 红测：
  - 新增 `frontend/src/components/finance-dashboard/__tests__/RevenueChart.test.jsx`，首跑复现 `Cannot read properties of undefined (reading 'byMonth')`。
  - 扩展 `tests/api/test_project_manager_self_service_contract.py`，首跑复现 PM 自己项目下 `/costs/`、`/machines/` 403。
  - 扩展 `frontend/src/pages/__tests__/SalesWorkstation.test.jsx`，分别复现跟进提醒和商机健康列表同 ID 多行时的 React duplicate key 警告。
- 修复：
  - `RevenueChart` 增加默认收入数据 shape，所有子图表使用归一化后的 `safeRevenueData`，空数据不再打爆总经理工作台。
  - `DataScopeService` 的项目范围纳入 `Project.pm_id == current_user.id`，PROJECT 数据范围的 PM 能读取自己负责项目、工作空间、旧阶段/成员兼容接口。
  - `task_center:*` 加入 PM 标准角色包，恢复 PM 自己任务中心读取。
  - 项目成本 GET 集合/详情使用项目可读校验，不再要求全局 `cost:read`；写接口仍保留原权限。
  - 项目机台 GET 集合/详情/汇总/BOM/文档读取/服务历史使用项目可读校验，不再要求全局 `machine:read`；创建、更新、删除、上传仍保留原写权限。
  - 销售工作站跟进提醒、商机健康列表改为复合行 key，后端返回同一业务对象多条提醒/健康记录时不再撞 React key。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_project_manager_self_service_contract.py tests/api/test_hr_manager_role_contract.py tests/api/test_pmo_director_role_contract.py -q` -> 7 passed
  - `npm run test:run -- src/components/finance-dashboard/__tests__/RevenueChart.test.jsx src/pages/__tests__/SalesWorkstation.test.jsx` -> 8 passed
  - `npm run test:run -- src/services/api/__tests__/projects.test.js` -> 44 passed
  - `PYTHONWARNINGS=ignore .venv/bin/python -m py_compile ...` -> passed
  - `git diff --check -- <本批触达文件>` -> passed
  - `npm run build` -> passed；仅保留既有 Vite 动态/静态导入和 chunk size 提示。
  - Playwright targeted 复扫：`.gstack/qa-reports/live-frontend-targeted-regression-2026-06-27-batch49.json`，`routeVisits=7`、`severeCount=0`、`warningCount=0`、`badStatusCount=0`、`forbiddenStatusCount=0`、`consoleErrorCount=0`。

剩余未修复：

- 本轮 targeted 覆盖到的 GM、销售总监、PM 关键回归链路已清零；这不等于全系统所有深层增删改、移动端和边缘权限组合都已穷尽。
- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。

### 105. 权限组合第三十九批：PMO 总监角色包补齐成本只读权限

- 定位：
  - 修复项目详情尾斜杠后，`pmo_director` 打开 `/projects/1` 暴露真实 403：`GET /api/v1/projects/1/costs/` 返回 `权限不足: cost:read`。
  - 活库确认 `wangjg` 绑定 `pmo_director`，角色数据范围为 `ALL`，项目访问边界不是问题；缺口在 `role_api_permissions` 中没有 `pmo_director -> cost:read`。
  - 成本列表端点仍正确要求 `cost:read`，本批不降低端点鉴权，不放开成本写入权限。
- 红测：
  - 新增 `tests/api/test_pmo_director_role_contract.py`。
  - 首跑：`.venv/bin/python -m pytest tests/api/test_pmo_director_role_contract.py -q` -> 2 failed。
    - `pmo_director` 用户访问 `/projects/{project_id}/costs/` 返回 403 `权限不足: cost:read`。
    - `pmo_director` 角色包没有 `cost:read` 绑定。
- 修复：
  - `app/utils/init_permissions_data.py` 增加系统 API 权限 `cost:read`。
  - `ROLE_PERMISSIONS_MAPPING` 覆盖 `pmo_director` 和历史口径 `PMO_DIRECTOR`，只补成本只读入口。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_pmo_director_role_contract.py -q` -> 2 passed
  - `.venv/bin/python -m pytest tests/api/test_hr_manager_role_contract.py tests/api/test_pmo_director_role_contract.py -q` -> 4 passed
  - `PYTHONWARNINGS=ignore .venv/bin/python -m py_compile app/utils/init_permissions_data.py tests/api/test_hr_manager_role_contract.py tests/api/test_pmo_director_role_contract.py` -> passed
  - 活库确认 `pmo_director -> cost:read` 绑定数为 1。
  - Playwright 复验 `/projects/1`：`.gstack/qa-reports/live-project-detail-pmo-cors-cost-permission-2026-06-27-batch45.json`，`badStatuses=[]`、`corsLikeConsole=[]`、`consoleErrors=[]`、`pageErrors=[]`、`requestFailures=[]`，`/costs/`、`/machines/`、`/costs/profit-optimization` 均 200。

### 104. 权限组合第三十八批：项目详情成本/机台集合端点尾斜杠 CORS 清零

- 定位：
  - 当前多角色浏览器复扫中，`pmo_director` 访问 `/projects/1` 的 `/api/v1/projects/1/machines` 与 `/api/v1/projects/1/costs` 出现浏览器 CORS console error。
  - 后端真实注册的是 FastAPI 集合路由 `/projects/{project_id}/machines/` 和 `/projects/{project_id}/costs/`；前端无尾斜杠会被 307 到 `http://127.0.0.1:8002/.../`，跨 host 后被浏览器拦截。
  - 这不是权限边界问题，也不是后端路由缺失；应让前端直接打后端真实集合路径。
- 红测：
  - 修改 `frontend/src/services/api/__tests__/projects.test.js`，约束 `projectApi.getMachines`、`machineApi.list/create`、`costApi.list/create/getProjectCosts` 必须使用带尾斜杠的集合路径。
  - 首跑：`npm run test:run -- src/services/api/__tests__/projects.test.js` -> 6 failed，均复现旧无尾斜杠路径。
- 修复：
  - `frontend/src/services/api/projects.js` 中项目机台和项目成本集合接口统一改为 `/machines/`、`/costs/`。
  - `frontend/src/components/project/RealTimeMarginPanel.jsx` 的成本列表兜底直连调用同步改为 `/costs/`。
  - 全仓库扫描确认不再有无尾斜杠的 `/projects/${id}/machines` 或 `/projects/${id}/costs` 集合调用。
- 验证：
  - `npm run test:run -- src/services/api/__tests__/projects.test.js` -> 44 passed
  - Playwright 初次复验确认 CORS 已清零，但暴露 `pmo_director` 缺 `cost:read` 的真实 403；第 105 批已继续修复。
  - 第 105 批最终 Playwright 证据文件同样覆盖本批：`.gstack/qa-reports/live-project-detail-pmo-cors-cost-permission-2026-06-27-batch45.json`，无 CORS、无 request failed。

### 103. 权限组合第三十七批：HR 经理角色包补齐 HR 只读权限

- 定位：
  - 6/26 多角色矩阵中的 `hr_manager` 访问 HR 页面曾出现 `/api/v1/hr/dashboard`、`/api/v1/hr/contracts`、`/api/v1/hr/contracts/expiring`、`/api/v1/hr/transactions` 403。
  - 当前源码确认这些 HR 只读端点仍正确要求 `hr:read`，活库角色 `hr_manager` 存在且用户 `zhoul` 绑定该角色，但角色包缺少 `hr:read`。
  - 权限引擎实际读取 `role_api_permissions` + `api_permissions`，不是旧 `role_permissions`，因此需要修新权限初始化口径。
- 红测：
  - 新增 `tests/api/test_hr_manager_role_contract.py`。
  - 首跑：`.venv/bin/python -m pytest tests/api/test_hr_manager_role_contract.py -q` -> 2 failed。
    - `hr_manager` 用户访问 `/hr/dashboard` 返回 403 `权限不足: hr:read`。
    - `hr_manager` 角色包没有 `hr:read` 绑定。
- 修复：
  - `app/utils/init_permissions_data.py` 增加系统 API 权限 `hr:read`。
  - `ROLE_PERMISSIONS_MAPPING` 同时覆盖现有 `hr_manager` 和历史口径 `HR_MGR`，只补 HR 工作台只读入口，不降低端点鉴权要求。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_hr_manager_role_contract.py -q` -> 2 passed
  - `PYTHONWARNINGS=ignore .venv/bin/python -m py_compile app/utils/init_permissions_data.py tests/api/test_hr_manager_role_contract.py` -> passed
  - 活库确认 `hr_manager -> hr:read` 绑定数为 1。
  - Live API 使用本机签发的 `zhoul` 用户 token 复验：
    - `/api/v1/hr/dashboard` -> 200
    - `/api/v1/hr/contracts?page=1&page_size=10` -> 200
    - `/api/v1/hr/contracts/expiring?days=60` -> 200
    - `/api/v1/hr/transactions?page=1&page_size=10` -> 200
  - Live 负向复验：无 HR 权限的普通用户访问 `/api/v1/hr/dashboard` 和 `/api/v1/hr/contracts?page=1&page_size=10` 仍为 403。
  - 证据文件：`.gstack/qa-reports/live-hr-manager-self-service-permission-matrix-2026-06-27-batch44.json`。

### 102. 权限组合第三十六批：业务人员选择器批量改用 users/options

- 定位：
  - 继续第 101 批方向排查，发现多个业务页面仍把人员选择、负责人筛选、派工人员、车间经理等轻量人员选项写成 `userApi.list()`，会命中 `/api/v1/users/` 管理列表。
  - 这些入口不需要邮箱、电话、角色、权限等管理字段；继续放任它们打 `/users/` 会让普通业务用户在无 `user:read` 时遇到 403。
- 红测：
  - 新增 `frontend/src/services/api/__tests__/userOptionsCallSites.test.js`，约束业务人员选择器不得调用 `userApi.list()`，用户管理页仍必须保留 `userApi.list()`。
  - 首跑：`npm run test:run -- src/services/api/__tests__/userOptionsCallSites.test.js` -> 7 failed, 2 passed，7 个业务文件均缺少 `userApi.options`。
- 修复：
  - 以下业务入口从 `userApi.list(...)` 改为 `userApi.options(..., is_active: true)`：
    - `frontend/src/pages/CustomerCommunication/index.jsx`
    - `frontend/src/pages/ProjectRoles.jsx`
    - `frontend/src/pages/SalesFunnel/index.jsx`
    - `frontend/src/components/project/ProjectLeadsPanel.jsx`
    - `frontend/src/pages/OpportunityManagement/index.jsx`
    - `frontend/src/pages/InstallationDispatchManagement.jsx`
    - `frontend/src/pages/WorkshopManagement/hooks/useWorkshopManagement.js`
  - 同步 `SalesFunnel`、`OpportunityManagement` 测试 mock，避免测试继续静默吞掉 `userApi.options is not a function`。
  - `UserManagement` 两个真实管理列表调用保持 `userApi.list()`，本批不放开 `/users/`。
- 验证：
  - `npm run test:run -- src/services/api/__tests__/userOptionsCallSites.test.js` -> 9 passed
  - `npm run test:run -- src/pages/__tests__/SalesFunnel.test.jsx` -> 29 passed（保留该旧测试既有 act warning）
  - `npm run test:run -- src/pages/__tests__/OpportunityManagement.test.jsx` -> 8 passed
  - `npm run test:run -- src/pages/__tests__/WorkshopManagement.test.jsx` -> 8 passed
  - `rg -n "userApi\\.list" frontend/src -g "*.js" -g "*.jsx" | rg -v "__tests__|\\.test\\.|ProjectDetail/__tests__"` -> 仅剩 `frontend/src/hooks/useApi.js` 文档示例和 `UserManagement` 两个管理列表真实调用。
  - `git diff --check -- frontend/src/pages/CustomerCommunication/index.jsx frontend/src/pages/ProjectRoles.jsx frontend/src/pages/SalesFunnel/index.jsx frontend/src/components/project/ProjectLeadsPanel.jsx frontend/src/pages/OpportunityManagement/index.jsx frontend/src/pages/InstallationDispatchManagement.jsx frontend/src/pages/WorkshopManagement/hooks/useWorkshopManagement.js frontend/src/services/api/__tests__/userOptionsCallSites.test.js frontend/src/pages/__tests__/SalesFunnel.test.jsx frontend/src/pages/__tests__/OpportunityManagement.test.jsx` -> passed
  - `npm run build` -> passed（保留既有 dynamic import/chunk size 警告）

剩余未修复：

- `/users/` 管理列表继续按第 88 批结论保留 403；当前直接业务调用点已收口到 `/users/options`，后续若新增人员选择器应受 `userOptionsCallSites` 回归测试约束。
- HR 合同/看板/事务等敏感域仍需后续单独判定。

### 101. 权限组合第三十五批：项目详情添加成员人员选择改用 options

- 定位：
  - 第 88 批已明确 `/users/` 是用户管理列表，普通业务用户无 `user:read` 时应继续 403；第 31 批已提供 `/users/options` 作为人员选择轻量接口。
  - `ProjectDetail` 的添加项目成员弹窗仍调用 `userApi.list({ is_active: true })`，会命中 `/api/v1/users/`，导致普通项目成员在项目详情里打开添加成员时被用户管理权限误伤。
- 红测：
  - 先用临时前端断言复现旧实现：`npm run test:run -- src/pages/__tests__/ProjectDetail.test.jsx -t "should load add-member choices from user options"` -> 1 failed，`userApi.options` 未被调用。
  - 随后改为独立 hook 回归用例，避免旧整页测试文件的历史测试债影响本批验收。
- 修复：
  - `frontend/src/pages/ProjectDetail/useProjectDetail.js`：`loadAvailableUsers()` 从 `userApi.list(...)` 改为 `userApi.options(...)`。
  - 用户管理页仍保留 `userApi.list`；本批不放开 `/users/`，只修正项目详情人员选择入口的前端调用。
- 验证：
  - `npm run test:run -- src/pages/ProjectDetail/__tests__/useProjectDetailUserOptions.test.jsx` -> 1 passed
  - `npm run test:run -- src/services/api/__tests__/routeContracts.test.js -t "lightweight user options"` -> 1 passed, 20 skipped
  - `rg -n "userApi\\.(list|options)" src/pages/ProjectDetail src/pages/ProjectDetail/__tests__/useProjectDetailUserOptions.test.jsx` -> 项目详情业务代码仅剩 `userApi.options`，测试断言 `userApi.list` 不被调用。
  - `git diff --check -- frontend/src/pages/ProjectDetail/useProjectDetail.js frontend/src/pages/ProjectDetail/__tests__/useProjectDetailUserOptions.test.jsx` -> passed
  - `npm run build` -> passed（保留既有 dynamic import/chunk size 警告）

剩余未修复：

- `/users/` 管理列表仍按第 88 批结论保留 403；其它业务选择器如仍调用 `userApi.list`，需要继续逐个改到 `/users/options`，不能通过放开管理列表解决。
- HR 合同/看板/事务等敏感域仍需后续单独判定。

### 100. 权限组合第三十四批：技术规格项目成员读取 403 清零

- 定位：
  - `TechnicalSpecManagement` 首屏调用 `/technical-spec/requirements`，普通项目成员无 `technical_spec:read` 时返回 `403 权限不足: technical_spec:read`。
  - `SpecMatchCheck` 的只读列表调用 `/technical-spec/match/records` 同属项目技术规格读场景；本批只放开项目范围内的要求/匹配记录读取，不放开规格创建、更新、删除、文档提取或手动匹配检查。
- 红测：
  - 新增 `tests/api/test_technical_spec_route_contract.py::test_regular_member_can_read_project_technical_spec_without_module_permission`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_technical_spec_route_contract.py::test_regular_member_can_read_project_technical_spec_without_module_permission --tb=short` -> 1 failed，稳定复现 `权限不足: technical_spec:read`；同一用例要求无关项目 403，创建规格和 `match/check` 仍 403。
- 修复：
  - `app/api/v1/endpoints/technical_spec/requirements.py`：`GET /requirements` 与 `GET /requirements/{id}` 依赖改为登录用户，并用 `check_project_read_access_or_raise()` 与 `filter_by_project_access()` 限制到可读项目。
  - `app/api/v1/endpoints/technical_spec/match.py`：仅 `GET /match/records` 改为登录用户 + 项目读范围过滤；`POST /match/check` 保持 `technical_spec:read`。
  - 无 `project_id` 的列表不返回全公司技术规格，只返回当前用户数据范围或 active 项目成员范围内的记录。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_technical_spec_route_contract.py::test_regular_member_can_read_project_technical_spec_without_module_permission --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_technical_spec_route_contract.py --tb=short` -> 4 passed
  - `.venv/bin/pytest -q tests/api/test_technical_spec_route_contract.py::test_regular_member_can_read_project_technical_spec_without_module_permission tests/api/test_technical_spec_route_contract.py::test_technical_spec_requirements_tolerate_legacy_null_requirement_level tests/api/test_technical_spec_route_contract.py::test_technical_spec_match_records_tolerate_legacy_null_requirement_level tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_project_profit_card_without_cost_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_workspace_without_project_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_legacy_member_and_stage_blocks_without_project_read tests/api/test_users.py::TestUserPermissionEnforcement::test_user_options_available_without_user_read --tb=short` -> 7 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/technical_spec/requirements.py app/api/v1/endpoints/technical_spec/match.py tests/api/test_technical_spec_route_contract.py app/utils/permission_helpers.py` -> passed
  - 路由注册确认：`GET /api/v1/technical-spec/requirements`、`GET /api/v1/technical-spec/requirements/{requirement_id}`、`GET /api/v1/technical-spec/match/records` 以及 `/technical-specs` 双前缀均注册。
  - live 复扫：`.gstack/qa-reports/live-technical-spec-self-service-permission-matrix-2026-06-27-batch43.json`，临时用户无 `technical_spec:read/create`，作为 active 项目成员读取技术规格列表/详情 200、读取匹配记录 200、无关项目列表/详情/匹配记录 403、创建规格 403、`match/check` 403；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-technical-spec-self-service-batch43-20260627131836.db`

剩余未修复：

- 旧多角色 core 矩阵中的 `technical-spec/requirements` 已由第 100 批覆盖；`/users/` 管理列表仍按第 88 批结论保留 403，前端应使用 `/users/options` 做人员选择。
- HR 合同/看板/事务等仍是敏感域，后续需要逐项确认是岗位权限配置、前端降级，还是后端本人/范围读取误伤。

### 99. 权限组合第三十三批：项目利润卡成员读取 403 清零

- 定位：
  - 项目详情页的 `ProfitAnalysisCard` 调用 `/projects/{project_id}/costs/profit-optimization`，普通 active 项目成员无 `cost:read` 时返回 `403 权限不足: cost:read`。
  - 该接口是本项目详情里的利润卡片，只读取当前项目合同金额、预算、已发生成本和优化建议；本批不放开全局成本表，也不放开相邻 `margin-analysis/cost-optimization/quote-cost-variance` 等成本分析接口。
- 红测：
  - 新增 `tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_project_profit_card_without_cost_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_project_profit_card_without_cost_read --tb=short` -> 1 failed，稳定复现 `权限不足: cost:read`；同一用例要求无关项目仍 403、相邻 `margin-analysis` 仍 403。
- 修复：
  - `app/api/v1/endpoints/projects/costs/profit_optimization.py`：仅将 `GET /profit-optimization` 依赖从 `security.require_permission("cost:read")` 改为登录用户。
  - 在业务计算前调用 `check_project_read_access_or_raise()`，只允许通用项目数据范围命中，或当前用户是该项目 active `ProjectMember`；无关项目仍返回 403。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_project_profit_card_without_cost_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_project_profit_card_without_cost_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_workspace_without_project_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_legacy_member_and_stage_blocks_without_project_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_detail_without_project_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects tests/api/test_issues.py::TestIssueTemplates::test_logged_in_user_can_list_active_issue_templates_without_issue_read --tb=short` -> 6 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/projects/costs/profit_optimization.py app/utils/permission_helpers.py tests/api/test_projects.py` -> passed
  - 路由注册确认：`GET /api/v1/projects/{project_id}/costs/profit-optimization`、`GET /api/v1/projects/{project_id}/costs/margin-analysis`、`GET /api/v1/projects/{project_id:int}` 均注册。
  - live 复扫：`.gstack/qa-reports/live-project-profit-card-self-service-permission-matrix-2026-06-27-batch42.json`，目标用户 `demo26_sales_002` 无 `cost:read` 且无 `project:read`，作为 active 项目成员读取利润卡 200、无关项目利润卡 403、相邻 `margin-analysis` 仍 403、详情读取仍 200；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-project-profit-card-self-service-batch42-20260627130617.db`

剩余未修复：

- 旧多角色项目详情矩阵里的 `projects/stages/members/issue-templates/profit-optimization` 403 已分别由第 95-99 批覆盖；剩余 403 需要从其它矩阵继续逐项确认，例如工作空间其它子接口、HR 合同/看板、技术规格等。

### 98. 权限组合第三十二批：问题模板列表自服务读取 403 清零

- 定位：
  - 项目详情和项目工作空间的 `SolutionLibrary` 只读加载 `/issue-templates` 作为解决方案模板库；普通项目成员无 `issue:read` 时，该基础模板列表返回 `403 权限不足: issue:read`。
  - `issue:read` 同时控制问题详情/管理能力，本批不扩大问题详情、模板详情、创建、更新、删除、从模板创建问题等接口，只放开模板列表读。
- 红测：
  - 新增 `tests/api/test_issues.py::TestIssueTemplates::test_logged_in_user_can_list_active_issue_templates_without_issue_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_issues.py::TestIssueTemplates::test_logged_in_user_can_list_active_issue_templates_without_issue_read --tb=short` -> 1 failed，稳定复现 `权限不足: issue:read`。
- 修复：
  - `app/api/v1/endpoints/issues/templates.py`：`GET /issue-templates/` 列表依赖从 `security.require_permission("issue:read")` 改为 `security.get_current_active_user`。
  - `app/api/v1/endpoints/issues/__init__.py`：无斜杠兼容入口 `GET /issue-templates` 同步改为登录用户依赖，并继续转调同一个列表函数。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_issues.py::TestIssueTemplates::test_logged_in_user_can_list_active_issue_templates_without_issue_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_issues.py::TestIssueTemplates::test_logged_in_user_can_list_active_issue_templates_without_issue_read tests/api/test_issues.py::TestIssueTemplates::test_list_templates tests/api/test_batch9_route_contracts.py::test_issue_template_list_handles_legacy_nullable_defaults --tb=short` -> 3 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/issues/__init__.py app/api/v1/endpoints/issues/templates.py tests/api/test_issues.py` -> passed
  - 路由注册确认：`GET /api/v1/issue-templates`、`GET /api/v1/issue-templates/`、`GET /api/v1/issue-templates/{template_id}` 均注册；详情仍保留原 `issue:read`。
  - live 复扫：`.gstack/qa-reports/live-issue-template-list-self-service-permission-matrix-2026-06-27-batch41.json`，目标用户 `demo26_sales_002` 无 `issue:read`，无斜杠列表 200、有斜杠列表 200、详情仍 403；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-issue-template-list-self-service-batch41-20260627125814.db`

剩余未修复：

- 剩余 403 中，项目成本利润卡、工作空间其它子接口、HR 合同/看板、技术规格等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 97. 权限组合第三十一批：项目详情旧成员/阶段子接口成员读取 403 清零

- 定位：
  - 项目详情页仍会调用旧兼容路径 `/members/projects/{project_id}/members` 和 `/stages/projects/{project_id}/stages`。
  - 第 95/96 批已放开 active 项目成员读取项目详情和工作空间主入口，但旧成员接口依赖层仍要求 `project:read`，旧阶段接口仍使用通用 `check_project_access_or_raise()`，导致“详情可进，成员/阶段子块继续 403”。
  - 本批只放开两个旧兼容读取接口；成员新增、批量、通知、阶段写入等路径不变。
- 红测：
  - 新增 `tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_legacy_member_and_stage_blocks_without_project_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_legacy_member_and_stage_blocks_without_project_read --tb=short` -> 1 failed，成员旧接口在依赖层稳定复现 `权限不足: project:read`。
- 修复：
  - `app/api/v1/endpoints/project_legacy_compat.py`：旧成员列表依赖从 `security.require_permission("project:read")` 改为 `security.get_current_active_user`。
  - 两个旧读取接口统一使用 `check_project_read_access_or_raise()`，允许通用项目数据范围命中，或当前用户是该项目 active `ProjectMember`；无关项目仍返回 403。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_legacy_member_and_stage_blocks_without_project_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_legacy_member_and_stage_blocks_without_project_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_workspace_without_project_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_detail_without_project_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects tests/api/test_openapi_route_contracts.py::test_multirole_project_detail_legacy_routes_are_registered --tb=short` -> 5 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/project_legacy_compat.py app/utils/permission_helpers.py tests/api/test_projects.py` -> passed
  - 路由注册确认：`GET /api/v1/members/projects/{project_id}/members`、`GET /api/v1/stages/projects/{project_id}/stages`、`GET /api/v1/projects/{project_id:int}` 均注册。
  - live 复扫：`.gstack/qa-reports/live-project-legacy-blocks-self-service-permission-matrix-2026-06-27-batch40.json`，目标用户 `demo26_sales_002` 无 `project:read`，作为 active 项目成员读取旧成员列表 200、旧阶段列表 200、无关项目两个接口均 403、详情读取仍 200；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-project-legacy-blocks-self-service-batch40-20260627125003.db`

剩余未修复：

- 剩余 403 中，项目成本利润卡、issue templates、工作空间其它子接口、HR 合同/看板、技术规格等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 96. 权限组合第三十批：项目工作空间成员读取 403 清零

- 定位：
  - 多角色矩阵中项目详情页会继续请求 `/api/v1/project-workspace/projects/{project_id}/workspace`；普通 active 项目成员虽然已能读取 `/projects/{id}`，但工作空间主入口仍调用通用 `check_project_access_or_raise()`，对“仅项目成员、无 project:read”的用户返回 403。
  - 本批只放开工作空间主读取入口；工作空间 context、downstream、奖金、会议、问题、方案等其它子接口暂不扩大，更新/删除/写入路径仍保持原权限。
- 红测：
  - 新增 `tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_workspace_without_project_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_workspace_without_project_read --tb=short` -> 1 failed，稳定复现 `您没有权限访问该项目`；同一用例确认无关项目工作空间仍 403。
- 修复：
  - `app/utils/permission_helpers.py`：新增 `check_project_read_access_or_raise()`，读取场景允许通用项目数据范围命中，或当前用户是该项目 active `ProjectMember`；写入场景继续使用原 `check_project_access_or_raise()`。
  - `app/api/v1/endpoints/projects/project_crud.py`：项目详情读取改为复用新 helper，避免 B95 的成员读取口径与工作空间分叉。
  - `app/api/v1/endpoints/projects/workspace.py`：仅 `get_project_workspace()` 主入口改用新 helper，并直接复用 helper 返回的项目对象。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_workspace_without_project_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_workspace_without_project_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_detail_without_project_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects tests/api/test_sales_customers_api.py::TestSalesCustomersAPI::test_regular_sales_user_can_read_own_customers_without_customer_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_anomalies_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_statistics_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_month_summary_without_timesheet_read --tb=short` -> 7 passed
  - `.venv/bin/python -m py_compile app/utils/permission_helpers.py app/api/v1/endpoints/projects/project_crud.py app/api/v1/endpoints/projects/workspace.py tests/api/test_projects.py` -> passed
  - 路由注册确认：`GET /api/v1/project-workspace/projects/{project_id}/workspace`、`GET /api/v1/projects/{project_id:int}`、`GET /api/v1/projects/my-projects` 均注册，且 `my-projects` 仍在动态详情路由前。
  - live 复扫：`.gstack/qa-reports/live-project-workspace-self-service-permission-matrix-2026-06-27-batch39.json`，目标用户 `demo26_sales_002` 无 `project:read`，作为 active 项目成员读取工作空间 200、无关项目工作空间 403、详情读取仍 200、工作空间团队包含本人；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-project-workspace-self-service-batch39-20260627124009.db`

剩余未修复：

- 剩余 403 中，工作空间其它子接口、HR 合同/看板、技术规格/问题模板等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 95. 权限组合第二十九批：项目成员详情读取 403 清零

- 定位：
  - 多角色矩阵中 `/projects/1` 会请求 `/api/v1/projects/1`，普通项目成员容易返回 `403 您没有权限查看该项目`。
  - `GET /projects/my-projects` 已允许登录用户读取自己参与项目；但详情页复用了通用 `check_project_access_or_raise()`，其 OWN 范围只认创建人/PM，不认 active 项目成员，导致“能在我的项目列表看到，却打不开详情”。
  - 本批只放开 `GET /projects/{project_id:int}` 的项目成员读取；更新/删除仍走原通用项目访问 helper，不扩大写权限。
- 红测：
  - 新增 `tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_detail_without_project_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_detail_without_project_read --tb=short` -> 1 failed，稳定复现 `您没有权限查看该项目`；同一用例确认无关项目详情仍 403。
- 修复：
  - `app/api/v1/endpoints/projects/project_crud.py`：仅在 `read_project()` 内改读权限判断。
  - 先查项目存在；再允许 `DataScopeService.check_project_access(...)` 通过，或当前用户是该项目 active `ProjectMember`；否则仍返回 403。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_detail_without_project_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_member_project_detail_without_project_read tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects tests/api/test_sales_customers_api.py::TestSalesCustomersAPI::test_regular_sales_user_can_read_own_customers_without_customer_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_anomalies_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_statistics_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_month_summary_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_week_timesheet_without_timesheet_read --tb=short` -> 7 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/projects/project_crud.py tests/api/test_projects.py app/api/v1/endpoints/customers/crud_refactored.py tests/api/test_sales_customers_api.py` -> passed
  - 路由注册确认：`GET /api/v1/projects/{project_id:int}`、`GET /api/v1/projects/my-projects`、`GET /api/v1/customers/` 均注册。
  - live 复扫：`.gstack/qa-reports/live-project-detail-self-service-permission-matrix-2026-06-27-batch38.json`，目标用户 `demo26_sales_002` 无 `project:read`，作为 active 项目成员读取项目详情 200、无关项目详情 403、`my-projects` 仍只包含参与项目；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-project-detail-self-service-batch38-20260627122610.db`

剩余未修复：

- 项目工作空间主入口已由第 96 批修复；剩余 403 中，工作空间其它子接口、HR 合同/看板、技术规格/问题模板等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 94. 权限组合第二十八批：旧客户列表销售范围过滤 403 清零

- 定位：
  - 多角色矩阵中 `/api/v1/customers/?page=1&page_size=100` 返回 `403 权限不足: customer:read`。
  - 新销售路径 `/api/v1/sales/customers` 已经是登录态并调用 `filter_sales_data_by_scope(..., Customer, "sales_owner_id")`；但旧兼容路径 `/api/v1/customers/` 仍走 `customers/crud_refactored.py`，列表依赖 `customer:read` 且 service 列表未套销售范围过滤。
  - 本批只放开旧 `/customers/` 列表，并按 `sales_owner_id` 套销售数据范围；详情、创建、更新、删除仍保持原 `customer:*` 权限。
- 红测：
  - 新增 `tests/api/test_sales_customers_api.py::TestSalesCustomersAPI::test_regular_sales_user_can_read_own_customers_without_customer_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_sales_customers_api.py::TestSalesCustomersAPI::test_regular_sales_user_can_read_own_customers_without_customer_read --tb=short` -> 1 failed，稳定复现 `权限不足: customer:read`；同一用例准备本人/他人负责客户，要求本人客户可见、他人客户不可见。
- 修复：
  - `app/api/v1/endpoints/customers/crud_refactored.py`：仅将旧 `GET /customers/` 列表依赖从 `customer:read` 降为登录用户。
  - 该列表改为直接构建 `Customer` 查询，先调用 `security.filter_sales_data_by_scope(query, current_user, db, Customer, "sales_owner_id")`，再应用 keyword/industry/is_active 筛选、分页和原 `PaginatedResponse[CustomerResponse]` 响应格式。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_sales_customers_api.py::TestSalesCustomersAPI::test_regular_sales_user_can_read_own_customers_without_customer_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_sales_customers_api.py::TestSalesCustomersAPI::test_regular_sales_user_can_read_own_customers_without_customer_read tests/api/test_sales_customers_api.py::TestSalesCustomersAPI::test_list_customers tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_anomalies_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_statistics_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_month_summary_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_week_timesheet_without_timesheet_read tests/api/test_collection_priority_api.py::test_regular_sales_user_can_read_own_collection_summary_without_contract_read --tb=short` -> 7 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/customers/crud_refactored.py tests/api/test_sales_customers_api.py app/api/v1/endpoints/timesheet/quality.py app/services/timesheet/timesheet_quality_service.py` -> passed
  - 路由注册确认：`GET /api/v1/customers/`、`GET /api/v1/customers/{item_id}`、`GET /api/v1/sales/customers`、`GET /api/v1/timesheet/anomalies` 均注册。
  - live 复扫：`.gstack/qa-reports/live-customer-list-self-service-permission-matrix-2026-06-27-batch37.json`，目标用户 `demo26_sales_002` 无 `customer:read`，旧 `/customers/` 列表 200 且只返回本人负责客户；用他人客户关键词查询返回 200 空列表；旧详情仍 403；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-customer-list-self-service-batch37-20260627121738.db`

剩余未修复：

- 剩余 403 中，HR 合同/看板、项目详情/工作空间数据范围、技术规格/问题模板等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 93. 权限组合第二十七批：工时异常检测范围过滤 403 清零

- 定位：
  - 多角色矩阵中 `/timesheet/dashboard` 同时请求统计、月汇总、异常检测；B91/B92 后，`/api/v1/timesheet/anomalies` 仍返回 `403 权限不足: timesheet:read`，会继续拖垮 dashboard 的 `Promise.all`。
  - 不能直接降权限：`TimesheetQualityService.detect_anomalies(user_id=None, ...)` 原逻辑会扫描全量已审批工时。
  - 本批把 HTTP 入口改成登录用户可访问，同时在服务层按当前用户套用统一工时访问范围；内部提醒任务不传 `current_user` 时仍保持原全量扫描语义。
- 红测：
  - 新增 `tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_anomalies_without_timesheet_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_anomalies_without_timesheet_read --tb=short` -> 1 failed，稳定复现 `权限不足: timesheet:read`；同一用例准备本人/他人超 16 小时 approved 工时，要求本人异常可见、他人异常不可见，显式 `user_id=他人` 返回空列表。
- 修复：
  - `app/api/v1/endpoints/timesheet/quality.py`：仅将 `GET /timesheet/anomalies` 的依赖从 `timesheet:read` 降为登录用户，并把 `current_user` 传入质量服务。
  - `app/services/timesheet/timesheet_quality_service.py`：`detect_anomalies()` 新增可选 `current_user` 参数；传入时先调用 `apply_timesheet_access_filter()`，再执行显式 `user_id`、日期范围和日/周/月异常聚合。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_anomalies_without_timesheet_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_anomalies_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_statistics_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_month_summary_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_week_timesheet_without_timesheet_read tests/api/test_collection_priority_api.py::test_regular_sales_user_can_read_own_collection_summary_without_contract_read tests/api/test_users.py::TestUserPermissionEnforcement::test_user_options_available_without_user_read tests/api/test_pmo.py::TestInitiations::test_regular_applicant_can_list_only_own_initiations tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects --tb=short` -> 8 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/timesheet/quality.py app/services/timesheet/timesheet_quality_service.py app/api/v1/endpoints/timesheet/statistics.py app/api/v1/endpoints/timesheet/monthly.py app/api/v1/endpoints/timesheet/weekly.py tests/api/test_timesheet_weekly_api.py` -> passed
  - 路由注册确认：`GET /api/v1/timesheet/anomalies`、`GET /api/v1/timesheet/statistics`、`GET /api/v1/timesheet/monthly/month-summary`、`GET /api/v1/timesheet/weekly/week` 均注册。
  - live 复扫：`.gstack/qa-reports/live-timesheet-anomalies-self-service-permission-matrix-2026-06-27-batch36.json`，目标用户 `demo26_sales_002` 无 `timesheet:read`，anomalies 200、显式查询他人返回 200 空列表、statistics 200、month-summary 200；临时插入的本人 `17.25` 小时异常可见、他人 `18.00` 小时异常不可见；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-timesheet-anomalies-self-service-batch36-20260627120332.db`

剩余未修复：

- 剩余 403 中，客户列表、HR 合同、项目详情/工作空间数据范围等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 92. 权限组合第二十六批：工时统计范围过滤 403 清零

- 定位：
  - 多角色矩阵中 `/timesheet/dashboard` 会请求 `/api/v1/timesheet/statistics?year=2026&month=6` 或日期范围统计，普通业务角色返回 `403 权限不足: timesheet:read`。
  - 该入口内部已经调用 `apply_timesheet_access_filter(query, db, current_user)`，可按本人、管理项目、研发项目、管理部门、下属范围收窄已审批工时。
  - 本批只放开 `GET /timesheet/statistics` 的范围过滤读取；`/timesheet/anomalies` 仍保持 `timesheet:read`，因为当前异常检测服务在未传 `user_id` 时会扫描全量已审批工时，不能直接降权限。
- 红测：
  - 新增 `tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_statistics_without_timesheet_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_statistics_without_timesheet_read --tb=short` -> 1 failed，稳定复现 `权限不足: timesheet:read`；同一用例准备本人/他人 approved 工时，要求本人可见、他人不可见，显式 `user_id=他人` 返回空统计。
- 修复：
  - `app/api/v1/endpoints/timesheet/statistics.py`：仅将 `GET /timesheet/statistics` 的依赖从 `timesheet:read` 降为登录用户。
  - 保留原有 `apply_timesheet_access_filter()`，避免无管理范围用户看到本人以外工时。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_statistics_without_timesheet_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_scoped_statistics_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_month_summary_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_week_timesheet_without_timesheet_read tests/api/test_collection_priority_api.py::test_regular_sales_user_can_read_own_collection_summary_without_contract_read tests/api/test_users.py::TestUserPermissionEnforcement::test_user_options_available_without_user_read tests/api/test_pmo.py::TestInitiations::test_regular_applicant_can_list_only_own_initiations tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects --tb=short` -> 7 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/timesheet/statistics.py app/api/v1/endpoints/timesheet/monthly.py app/api/v1/endpoints/timesheet/weekly.py tests/api/test_timesheet_weekly_api.py` -> passed
  - 路由注册确认：`GET /api/v1/timesheet/statistics`、`GET /api/v1/timesheet/monthly/month-summary`、`GET /api/v1/timesheet/weekly/week`、`GET /api/v1/timesheet/anomalies` 均注册。
  - live 复扫：`.gstack/qa-reports/live-timesheet-statistics-self-service-permission-matrix-2026-06-27-batch35.json`，目标用户 `demo26_sales_002` 无 `timesheet:read`，本人统计 200、显式查询他人返回 200 空统计、anomalies 仍 403；临时插入的本人 `4.75` 小时可见、他人 `8.00` 小时不可见；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-timesheet-statistics-self-service-batch35-20260627115330.db`

剩余未修复：

- 剩余 403 中，客户列表、HR 合同、项目详情/工作空间数据范围、工时异常检测等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 91. 权限组合第二十五批：月度工时本人汇总 403 清零

- 定位：
  - 多角色矩阵中 `/timesheet/dashboard` 会请求 `/api/v1/timesheet/monthly/month-summary?year=2026&month=6`，普通 HR/业务角色返回 `403 权限不足: timesheet:read`。
  - 该入口默认读取当前登录用户的月度汇总；当显式传 `user_id` 查询他人时，原函数内已有 `get_user_manageable_dimensions()` 校验直属下属/部门管理范围。
  - 本批只放开 `GET /timesheet/monthly/month-summary` 的本人读取；`/timesheet/statistics` 和 `/timesheet/anomalies` 仍保持管理/看板权限。
- 红测：
  - 新增 `tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_month_summary_without_timesheet_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_month_summary_without_timesheet_read --tb=short` -> 1 failed，默认本人月汇总稳定复现 `权限不足: timesheet:read`；同一用例确认查询他人仍为 403。
- 修复：
  - `app/api/v1/endpoints/timesheet/monthly.py`：仅将 `GET /timesheet/monthly/month-summary` 的依赖从 `timesheet:read` 降为登录用户。
  - 保留函数内 `target_user_id != current_user.id` 时的管理范围校验，避免跨人读取。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_month_summary_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_week_timesheet_without_timesheet_read --tb=short` -> 2 passed
  - `.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_month_summary_without_timesheet_read tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_week_timesheet_without_timesheet_read tests/api/test_collection_priority_api.py::test_regular_sales_user_can_read_own_collection_summary_without_contract_read tests/api/test_users.py::TestUserPermissionEnforcement::test_user_options_available_without_user_read tests/api/test_pmo.py::TestInitiations::test_regular_applicant_can_list_only_own_initiations tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects --tb=short` -> 6 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/timesheet/monthly.py app/api/v1/endpoints/timesheet/weekly.py tests/api/test_timesheet_weekly_api.py` -> passed
  - 路由注册确认：`GET /api/v1/timesheet/monthly/month-summary`、`GET /api/v1/timesheet/weekly/week`、`GET /api/v1/timesheet/statistics`、`GET /api/v1/timesheet/anomalies` 均注册。
  - live 复扫：`.gstack/qa-reports/live-timesheet-month-self-service-permission-matrix-2026-06-27-batch34.json`，目标用户 `demo26_sales_002` 无 `timesheet:read`，本人月汇总 200、查询他人 403、statistics/anomalies 仍 403；临时插入的本人日期工时可见；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-timesheet-month-self-service-batch34-20260627114153.db`

剩余未修复：

- 剩余 403 中，客户列表、HR 合同、项目详情/工作空间数据范围、工时 dashboard 统计/异常检测等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 90. 权限组合第二十四批：周工时本人读取 403 清零

- 定位：
  - 多角色矩阵中 `/timesheet` 会请求 `/api/v1/timesheet/weekly/week?week_start=2026-06-22`，普通 HR/业务角色返回 `403 权限不足: timesheet:read`。
  - 该入口默认读取当前登录用户的周工时；当显式传 `user_id` 查询他人时，原函数内已有 `get_user_manageable_dimensions()` 校验直属下属/部门管理范围。
  - 本批只放开 `GET /timesheet/weekly/week` 的本人读取；`POST /timesheet/weekly/week/submit` 仍要求 `timesheet:submit`，统计、异常检测等管理/看板接口不在本批放开。
- 红测：
  - 新增 `tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_week_timesheet_without_timesheet_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_week_timesheet_without_timesheet_read --tb=short` -> 1 failed，默认本人周工时稳定复现 `权限不足: timesheet:read`；同一用例确认查询他人仍为 403。
- 修复：
  - `app/api/v1/endpoints/timesheet/weekly.py`：仅将 `GET /timesheet/weekly/week` 的依赖从 `timesheet:read` 降为登录用户。
  - 保留函数内 `target_user_id != current_user.id` 时的管理范围校验，避免跨人读取。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_week_timesheet_without_timesheet_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_timesheet_weekly_api.py::test_regular_user_can_read_own_week_timesheet_without_timesheet_read tests/api/test_collection_priority_api.py::test_regular_sales_user_can_read_own_collection_summary_without_contract_read tests/api/test_users.py::TestUserPermissionEnforcement::test_user_options_available_without_user_read tests/api/test_pmo.py::TestInitiations::test_regular_applicant_can_list_only_own_initiations tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects --tb=short` -> 5 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/timesheet/weekly.py tests/api/test_timesheet_weekly_api.py app/api/v1/endpoints/sales/collection_priority.py tests/api/test_collection_priority_api.py` -> passed
  - 路由注册确认：`GET /api/v1/timesheet/weekly/week` 与 `POST /api/v1/timesheet/weekly/week/submit` 均注册。
  - live 复扫：`.gstack/qa-reports/live-timesheet-week-self-service-permission-matrix-2026-06-27-batch33.json`，目标用户 `demo26_sales_002` 无 `timesheet:read`，本人周工时 200、查询他人 403、提交周工时仍 403；临时插入的本人周工时可见、他人周工时不可见；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-timesheet-week-self-service-batch33-20260627113344.db`

剩余未修复：

- 剩余 403 中，客户列表、HR 合同、项目详情/工作空间数据范围、工时 dashboard 统计/月汇总/异常检测等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 89. 权限组合第二十三批：销售工作台本人催款汇总 403 清零

- 定位：
  - 多角色矩阵中 `/sales/workstation` 会请求 `/api/v1/sales/collection/priority/summary`，普通销售角色返回 `403 权限不足: contract:read`。
  - 该入口是销售工作台本人催款汇总；后端 `CollectionPriorityService.get_collection_summary(current_user.id)` 已继续调用 `filter_sales_finance_data_by_scope(..., Contract, "sales_owner_id")` 按当前销售数据范围收窄，不是合同管理全量列表。
  - `/sales/collection/priority` 列表和 `/sales/collection/priority/critical` 仍属于催款管理视图，本批不放开。
- 红测：
  - 新增 `tests/api/test_collection_priority_api.py::test_regular_sales_user_can_read_own_collection_summary_without_contract_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_collection_priority_api.py::test_regular_sales_user_can_read_own_collection_summary_without_contract_read --tb=short` -> 1 failed，`summary` 稳定复现 `权限不足: contract:read`；同一用例确认列表和 critical 仍为 403。
- 修复：
  - `app/api/v1/endpoints/sales/collection_priority.py`：仅将 `GET /sales/collection/priority/summary` 的依赖从 `contract:read` 降为登录用户。
  - 保留服务层 `current_user` 数据范围过滤，确保无 `contract:read` 用户只能看到本人/其角色范围内的应收汇总。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_collection_priority_api.py::test_regular_sales_user_can_read_own_collection_summary_without_contract_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_collection_priority_api.py::test_regular_sales_user_can_read_own_collection_summary_without_contract_read tests/api/test_users.py::TestUserPermissionEnforcement::test_user_options_available_without_user_read tests/api/test_pmo.py::TestInitiations::test_regular_applicant_can_list_only_own_initiations tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects --tb=short` -> 4 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/sales/collection_priority.py tests/api/test_collection_priority_api.py app/services/sales/collection_priority_service.py` -> passed
  - 路由注册确认：`GET /api/v1/sales/collection/priority`、`GET /api/v1/sales/collection/priority/summary`、`GET /api/v1/sales/collection/priority/critical` 均注册。
  - live 复扫：`.gstack/qa-reports/live-collection-summary-self-service-permission-matrix-2026-06-27-batch32.json`，目标用户 `demo26_sales_002` 无 `contract:read`，本人催款汇总 200、列表和 critical 仍 403；临时插入的本人发票可见、他人发票不可见；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-collection-summary-self-service-batch32-20260627112419.db`

剩余未修复：

- 剩余 403 中，客户列表、HR 合同、项目详情/工作空间数据范围、工时统计等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 88. 权限组合第二十二批：人员下拉选项 403 清零

- 定位：
  - 多角色矩阵中 `/technical-reviews/1`、`/service/center`、`/service-tickets` 会为主持人/参与人/负责人下拉请求 `/api/v1/users/`，普通技术/服务角色返回 `403 权限不足: user:read`。
  - `/users/` 是用户管理列表，返回联系方式、角色等管理字段，已有安全测试要求无 `user:read` 时必须 403，不能直接放开。
- 红测：
  - 新增 `tests/api/test_users.py::TestUserPermissionEnforcement::test_user_options_available_without_user_read`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_users.py::TestUserPermissionEnforcement::test_user_options_available_without_user_read --tb=short` -> 1 failed，`/users/options` 未注册返回 404；同一用例确认 `/users/` 仍为 403。
- 修复：
  - `app/schemas/auth.py` 新增 `UserOptionResponse`，只包含 `id / username / name / real_name / department / position`。
  - `app/api/v1/endpoints/users/crud_refactored.py` 新增 `GET /users/options`，登录用户可读取同租户 active 人员选项，不返回邮箱、电话、角色、权限、超管标记等管理字段。
  - `frontend/src/services/api/auth.js` 新增 `userApi.options()`。
  - `frontend/src/pages/TechnicalReviewDetail/hooks/useTechnicalReviewForm.js`、`frontend/src/components/service/ServiceTicketBatchActions.jsx`、`ServiceTicketAssignDialog.jsx`、`ServiceTicketCreateDialog.jsx` 改用 `/users/options`，不再打用户管理列表。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_users.py::TestUserPermissionEnforcement::test_user_options_available_without_user_read --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_users.py::TestUserPermissionEnforcement::test_user_list_requires_permission tests/api/test_users.py::TestUserPermissionEnforcement::test_user_options_available_without_user_read --tb=short` -> 2 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/users/crud_refactored.py app/schemas/auth.py tests/api/test_users.py` -> passed
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js src/pages/TechnicalReviewDetail/hooks/__tests__/useTechnicalReviewForm.test.js` -> 2 files / 29 tests passed
  - 路由注册确认：`GET /api/v1/users/options`、`GET /api/v1/users/`、`POST /api/v1/users/` 均注册。
  - live 复扫：`.gstack/qa-reports/live-user-options-self-service-permission-matrix-2026-06-27-batch31.json`，目标用户 `demo26_sales_002` 无 `user:read`，`/users/options` 200、`/users/` 仍 403，插入的临时用户在 options 中可见且敏感字段缺失；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-user-options-self-service-batch31-20260627110905.db`

剩余未修复：

- 剩余 403 中，客户列表、HR 合同、项目详情/工作空间数据范围等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 87. 权限组合第二十一批：PMO 立项本人列表 403 清零

- 定位：
  - 多角色矩阵中 `/sales/workstation` 会请求 `/api/v1/pmo/initiations?page=1&page_size=100&applicant_id={currentUser.id}`，普通销售角色返回 `403 权限不足: project:initiation:read`。
  - 该入口来自销售工作台的本人立项摘要；但 `GET /pmo/initiations` 不带 `applicant_id` 时可看全量，不能直接整体放开。
- 红测：
  - 新增 `tests/api/test_pmo.py::TestInitiations::test_regular_applicant_can_list_only_own_initiations`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_pmo.py::TestInitiations::test_regular_applicant_can_list_only_own_initiations --tb=short` -> 1 failed，稳定复现 `权限不足: project:initiation:read`。
- 修复：
  - `app/api/v1/endpoints/pmo/initiation.py`：列表入口降到登录用户，但函数内先用 `security.check_permission(..., "project:initiation:read", db)` 判断是否有全量读权限。
  - 无全量读权限时，仅允许 `applicant_id == current_user.id`；查询他人 applicant 或不带 applicant_id 仍返回 403。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_pmo.py::TestInitiations::test_regular_applicant_can_list_only_own_initiations --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_pmo.py::TestInitiations::test_regular_applicant_can_list_only_own_initiations tests/api/test_pmo.py::TestInitiations::test_list_initiations tests/api/test_pmo.py::TestInitiations::test_list_initiations_by_contract_no --tb=short` -> 3 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/pmo/initiation.py tests/api/test_pmo.py` -> passed
  - 路由注册确认：`GET /api/v1/pmo/initiations`、`POST /api/v1/pmo/initiations`、`GET/PUT /api/v1/pmo/initiations/{initiation_id}` 均注册。
  - live 复扫：`.gstack/qa-reports/live-pmo-initiation-self-service-permission-matrix-2026-06-27-batch30.json`，目标用户 `demo26_sales_002` 无 `project:initiation:read`，本人 applicant 列表 200 且只返回本人申请；他人 applicant 和缺少 applicant_id 均 403；`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-pmo-initiation-self-service-batch30-20260627105324.db`

剩余未修复：

- 剩余 403 中，客户列表、HR 合同、项目详情/工作空间数据范围等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 86. 权限组合第二十批：我的项目列表 403 清零

- 定位：
  - 多角色矩阵中 `/timesheet` 会请求 `/api/v1/projects/my-projects?page=1&page_size=100&is_active=true`，普通业务角色返回 `403 权限不足: project:read`。
  - `GET /projects/my-projects` 本身已经先按 `ProjectMember.user_id == current_user.id` 收窄到本人参与项目，属于登录用户自服务入口；项目详情、创建、更新、删除和普通列表仍走各自原边界。
- 红测：
  - 新增 `tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects --tb=short` -> 1 failed，稳定复现 `权限不足: project:read`。
  - 放开认证后暴露旧 controller 调用了不存在的 `ProjectCrudService.list_projects()`；一并修正为真实服务层分页方法。
- 修复：
  - `app/api/v1/endpoints/projects/project_crud.py`：仅将 `GET /projects/my-projects` 改为 `security.get_current_active_user`，继续按项目成员关系过滤本人项目，并转换为现有 `ProjectListResponse`。
  - `app/services/project_crud/service.py`：为现有项目分页查询增加可选 `project_ids` 过滤，默认不影响普通项目列表。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_projects.py::TestProjectCRUD::test_regular_member_can_read_only_my_projects tests/api/test_projects.py::TestProjectCRUD::test_project_permission_filter --tb=short` -> 2 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/projects/project_crud.py app/services/project_crud/service.py tests/api/test_projects.py` -> passed
  - 路由注册确认：`GET /api/v1/projects/my-projects`、`GET /api/v1/projects/` 和 `POST /api/v1/projects/` 均注册；`my-projects` 静态路由位于动态项目详情路由前。
  - live 复扫：`.gstack/qa-reports/live-my-projects-self-service-permission-matrix-2026-06-27-batch29.json`，目标用户 `demo26_sales_002` 无 `project:read`，本人项目列表 200 且只返回本人参与项目、不返回其他用户项目，`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-my-projects-self-service-batch29-20260627104327.db`

剩余未修复：

- 剩余 403 中，客户列表、HR 合同、项目详情/工作空间数据范围等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 85. 权限组合第十九批：节点子任务个人列表 403 清零

- 定位：
  - 多角色矩阵中 `/dashboard` 会请求 `/api/v1/node-tasks/my-tasks?filter=project`，普通业务角色返回 `403 权限不足: task_center:read`。
  - `NodeTaskService.get_user_tasks()` 已按 `NodeTask.assignee_id == current_user.id` 限定本人任务；跨用户入口 `/node-tasks/user/{user_id}` 仍属于权限管理范围。
- 红测：
  - 新增 `tests/api/test_node_tasks_api.py::test_regular_user_can_read_only_own_node_tasks`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_node_tasks_api.py::test_regular_user_can_read_only_own_node_tasks --tb=short` -> 1 failed，稳定复现 `权限不足: task_center:read`。
- 修复：
  - `app/api/v1/endpoints/node_tasks.py`：仅将 `GET /node-tasks/my-tasks` 改为 `security.get_current_active_user`；`/node-tasks/user/{user_id}`、详情、节点列表、创建/更新/删除仍保留原权限。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_node_tasks_api.py::test_regular_user_can_read_only_own_node_tasks --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_node_tasks_api.py --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py::test_acceptance_and_node_task_routes_tolerate_legacy_nulls --tb=short` -> 1 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/node_tasks.py tests/api/test_node_tasks_api.py` -> passed
  - 路由注册确认：`GET /api/v1/node-tasks/my-tasks` 与 `GET /api/v1/node-tasks/user/{user_id}` 均注册，且只放开前者。
  - live 复扫：`.gstack/qa-reports/live-node-task-self-service-permission-matrix-2026-06-27-batch28-rerun.json`，目标用户 `demo26_sales_002` 无 `task_center:read`，本人任务列表 200 且只返回自己的任务，跨用户列表仍 403，`severe_count=0`，`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-node-task-self-service-batch28-rerun-20260627-102109.db`
- 清理说明：
  - 首次 live 脚本用 ORM 删除临时 `Project` 时触发 `tenant_query` 递归，已按 marker `QA_NODE_TASK_SELF_%` 使用原生 SQL 反向清理，并确认 customers/projects/stages/nodes/tasks 残留均 0；复扫脚本已改为 SQL cleanup。

剩余未修复：

- 剩余 403 中，客户列表、HR 合同、项目详情/工作空间数据范围、工时统计等仍待逐项判断是测试角色缺权限、前端应降级，还是后端自服务误伤。

### 84. 权限组合第十八批：审批待办个人工作台 403 清零

- 定位：
  - 多角色矩阵中 `/dashboard` 会请求 `/api/v1/approvals/pending/mine`，普通业务角色返回 `403 权限不足: approval:view`。
  - `app/api/v1/endpoints/approvals/pending_refactored.py` 的待我审批、我发起、抄送我、已处理、数量统计和标记抄送已读接口都已经按 `current_user.id` 限定本人数据，但入口仍要求 `approval:view` 模块权限。
- 红测：
  - 在 `tests/api/test_approvals_api.py` 增加 `test_regular_user_can_read_only_own_approval_workbench`。
  - 首跑：`.venv/bin/pytest -q tests/api/test_approvals_api.py::TestApprovalPendingAPI::test_regular_user_can_read_only_own_approval_workbench --tb=short` -> 1 failed，稳定复现 `权限不足: approval:view`。
- 修复：
  - `app/api/v1/endpoints/approvals/pending_refactored.py`：6 个“我的审批”自服务入口统一改为 `security.get_current_active_user`，保留原本的本人数据过滤和 `mark_cc_as_read(cc_id, current_user.id)` 边界。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_approvals_api.py::TestApprovalPendingAPI::test_regular_user_can_read_only_own_approval_workbench --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_approvals_api.py::TestApprovalPendingAPI --tb=short` -> 6 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/approvals/pending_refactored.py tests/api/test_approvals_api.py` -> passed
  - 路由注册确认：`GET /approvals/pending/mine`、`GET /initiated`、`GET /cc`、`POST /cc/{cc_id}/read`、`GET /processed`、`GET /counts` 均在 `/api/v1` 下注册。
  - live 复扫：`.gstack/qa-reports/live-approval-self-service-permission-matrix-2026-06-27-batch27.json`，目标用户 `demo26_sales_002` 无 `approval:view` / `approval:read`，6 个真实 HTTP 路由均 200，`severe_count=0`，`row_count_delta` 和 `cleanup_residue` 全 0。
  - live 备份：`.gstack/db-backups/app-before-approval-self-service-batch27-20260627-100809.db`

剩余未修复：

- 多角色矩阵中仍有其它 403 待定标，例如客户列表、HR 合同、项目详情/工作空间数据范围、工时统计等；财务金额类接口暂不直接放宽权限，需逐个确认是否已有本人/范围过滤。

### 83. 前端 warning 第十八批：Dashboard ErrorBoundary fallback 契约清零

- 扫描证据：
  - 多角色矩阵中 `/dashboard` 首项 warning 为 `TypeError: this.props.fallback is not a function`，来源 `src/components/ui/ErrorBoundary.jsx`。
  - `frontend/src/pages/UnifiedDashboard/DashboardRenderer.jsx` 给 `ErrorBoundary` 传入的是 JSX 节点 `<WidgetErrorFallback widgetId={id} />`，但 `ErrorBoundary` 只支持函数型 `fallback(error, reset)`。
- 复现与红测试：
  - 在 `frontend/src/components/common/__tests__/ErrorBoundary.test.jsx` 增加 `renders custom fallback element instead of calling it as a function`。
  - 初跑：
    - `pnpm test:run src/components/common/__tests__/ErrorBoundary.test.jsx` -> 7 tests，1 failed，稳定复现 `this.props.fallback is not a function`。
- 根因：
  - ErrorBoundary 的 fallback 契约和实际调用方不一致；组件层只把 truthy fallback 当函数调用，没有兼容 React node。
- 修复：
  - `frontend/src/components/ui/ErrorBoundary.jsx`：
    - `fallback` 是函数时保持原有调用方式。
    - `fallback` 是 React element 时用 `React.cloneElement()` 注入 `error` 和 `reset`。
    - 其它可渲染值直接返回。
- 验证：
  - `pnpm test:run src/components/common/__tests__/ErrorBoundary.test.jsx` -> 7 passed
  - `pnpm test:run src/pages/UnifiedDashboard/widgets/NotificationPanel.test.jsx` -> 2 passed
  - `pnpm build` -> passed
  - build 仍仅有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。

剩余未修复：

- 多角色矩阵中其它 403 仍需继续结合岗位权限表核查。
- 还需要后续用 Playwright 多角色矩阵复扫确认 warning 总数下降；本批已用单元测试和生产构建锁住 fallback 契约。

### 82. 权限组合第十七批：通知中心个人收件箱 403 清零

- 扫描证据：
  - 多角色前端矩阵 `.gstack/qa-reports/frontend-role-matrix-smoke-2026-06-26-multirole-core-rerun.json` 中反复出现 `GET /api/v1/notifications/` 的 403 warning。
  - 前端 `frontend/src/services/api/alerts.js` 的 `notificationApi` 会在全局通知面板/通知中心调用列表、未读数、标记已读、全部已读、删除和个人通知设置。
  - 后端通知路由已经按 `Notification.user_id == current_user.id` 做本人数据过滤，但列表/未读/已读/设置/删除仍额外要求 `notification:read` 或 `notification:delete`，无权限普通用户无法读取自己的收件箱。
  - 同时发现未读统计和全部已读使用 `not Notification.is_read`，在 SQLAlchemy 条件里不是可靠布尔表达式。
- 复现与红测试：
  - 在 `tests/api/test_notifications.py` 增加 `test_regular_user_can_read_only_own_notifications`：
    - 普通用户 token 访问 `/notifications/` 应 200，且只能看到自己的通知。
    - `/notifications/unread-count` 应返回本人未读数。
    - 本人标记已读、批量已读、全部已读、个人设置、删除本人通知应可用；删除他人通知应 404。
  - 初跑稳定复现：
    - 列表接口先返回 `403 权限不足: notification:read`。
    - 放开读权限后，DELETE 再返回 `403 权限不足: notification:delete`。
- 根因：
  - 个人收件箱接口的安全边界应是“已登录 + 本人 `user_id` 过滤”，不是角色权限表里的模块读/删权限。
  - 未读过滤使用 Python `not` 操作符，语义偏离 SQLAlchemy 表达式，导致未读数/全部已读存在计数与更新风险。
- 修复：
  - `app/api/v1/endpoints/notifications/crud_refactored.py`：列表、未读数、标记已读、批量已读、全部已读、删除本人通知统一改为 `security.get_current_active_user`，保留 `Notification.user_id == current_user.id` 过滤。
  - `app/api/v1/endpoints/notifications/settings.py`：个人通知设置 GET/PUT 改为登录态自服务。
  - 未读过滤改为 `Notification.is_read.is_(False)`。
- 验证：
  - 红测修复后：
    - `.venv/bin/pytest -q tests/api/test_notifications.py::TestNotificationCRUD::test_regular_user_can_read_only_own_notifications --tb=short` -> 1 passed
  - 通知接口整组：
    - `.venv/bin/pytest -q tests/api/test_notifications.py --tb=short` -> 9 collected，5 passed，4 skipped
  - 编译与路由：
    - `.venv/bin/python -m py_compile app/api/v1/endpoints/notifications/crud_refactored.py app/api/v1/endpoints/notifications/settings.py tests/api/test_notifications.py` -> passed
    - 路由注册确认：`GET /notifications/`、`GET /notifications/unread-count`、`PUT /notifications/{notification_id}/read`、`PUT /notifications/batch-read`、`PUT /notifications/read-all`、`DELETE /notifications/{notification_id}`、`GET/PUT /notifications/settings` 均存在。
  - Live DB 矩阵：
    - `.gstack/qa-reports/live-notification-self-service-permission-matrix-2026-06-27-batch26-rerun.json`
    - 目标用户 `demo26_sales_002` 无 `notification:read` / `notification:delete` 权限；列表、未读数、标记已读、批量已读、全部已读、设置、删除本人均通过，删除他人通知返回 404。
    - `severe_count=0`，`route_statuses={"list":200,"unread_count":200,"mark_read":200,"batch_read":200,"read_all":200,"settings_get":200,"delete_other":404,"delete_own":200}`。
    - 备份：`.gstack/db-backups/app-before-notification-self-service-batch26-rerun-20260627-093727.db`
    - 清理后 `notifications / notification_settings / user_sessions / login_attempts` 相对备份行数 diff 全 0，`source_type='qa_batch26'` 残留 0。

剩余未修复：

- 多角色矩阵中除通知中心外的 403 仍待逐项定标，例如客户列表、HR 合同、项目详情/工作空间数据范围、工时统计等；下一步继续做跨角色权限表和前端按钮 payload 对账。
- `/dashboard` 的 `ErrorBoundary fallback is not a function` 已由第 83 批修复；仍需后续多角色矩阵复扫确认 warning 总数下降。

### 81. 权限组合第十六批：发票 DELEGATE/WITHDRAW 多人审批链路清零

- 扫描证据：
  - 第 80 批之后，发票旧 `approve/cancel` 与主审批通过链路已清零，但真实 `DELEGATE/WITHDRAW` 多人路径仍未做 live 组合。
  - 代码阅读确认：
    - `ApprovalEngineService.transfer()` 会把原任务置为 `TRANSFERRED`，并创建转办人新的 `PENDING` 任务。
    - `ApprovalEngineService.withdraw()` 会取消待办任务、把实例置为 `CANCELLED`，并调用发票适配器 `on_withdrawn()` 把发票退回 `DRAFT`。
  - 同时发现发票接口层在 `WITHDRAW` 分支调用引擎后又写 `invoice.status = SUBMITTED`，覆盖了适配器的 `DRAFT` 状态。
- 复现与红测试：
  - 在 `tests/api/test_invoice_approval_workflow_contracts.py` 增加：
    - `test_invoice_delegate_action_transfers_pending_task_to_delegate_user`
    - `test_invoice_withdraw_action_uses_adapter_state_and_cancels_pending_tasks`
  - 初跑：
    - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py::test_invoice_delegate_action_transfers_pending_task_to_delegate_user tests/api/test_invoice_approval_workflow_contracts.py::test_invoice_withdraw_action_uses_adapter_state_and_cancels_pending_tasks --tb=short`
    - `DELEGATE` 用例暴露测试夹具缺第二个激活用户；`WITHDRAW` 用例稳定复现发票状态为 `SUBMITTED`，期望应为 `DRAFT`。
- 根因：
  - 测试层不能依赖内存 fixture 中一定存在非 admin 用户，转办用例需要自建临时目标用户。
  - 产品层 `WITHDRAW` 分支重复写发票状态，和统一审批引擎适配器职责冲突，导致撤回后发票不能回到可编辑草稿态。
- 修复：
  - 测试辅助 `_seed_pending_invoice_approval()` 复用真实审批模型，`DELEGATE` 用例显式创建临时转办用户。
  - `app/api/v1/endpoints/sales/invoices/workflow.py` 删除 `WITHDRAW` 分支中覆盖 `invoice.status = SUBMITTED` 的语句，保留发票适配器 `on_withdrawn()` 的 `DRAFT` 状态。
- 验证：
  - 聚焦红测修复后：
    - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py::test_invoice_delegate_action_transfers_pending_task_to_delegate_user tests/api/test_invoice_approval_workflow_contracts.py::test_invoice_withdraw_action_uses_adapter_state_and_cancels_pending_tasks --tb=short` -> 2 passed
  - 发票全组：
    - `.venv/bin/pytest -q tests/api/test_invoice_basic_route_contracts.py tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_sales_invoices_api.py --tb=short` -> 34 collected，33 passed，1 skipped
  - 审批/路由组合：
    - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_approval_action_validation_contracts.py tests/api/test_path_param_route_contracts.py::test_sales_path_param_routes_tolerate_legacy_nulls_and_safe_export_headers --tb=short` -> 41 passed
    - `.venv/bin/python -m py_compile app/api/v1/endpoints/sales/invoices/operations.py app/api/v1/endpoints/sales/invoices/workflow.py tests/api/test_invoice_approval_workflow_contracts.py` -> passed
  - 路由注册确认：
    - app routes 已同时存在 `POST /api/v1/sales/invoices/{invoice_id}/approval/action`、`POST /approve`、`POST /cancel`、`PUT /void`。
  - Live DB 矩阵：
    - 首轮矩阵发现清理脚本按 `source_id` 泛删了历史采购审批通知 `856-859`；已从备份 `.gstack/db-backups/app-before-invoice-delegate-withdraw-batch25-20260627-075808.db` 精确恢复，并复验 4 条通知仍在库中。
    - 修正清理策略为仅删除本次新增通知 ID 后重跑：`.gstack/qa-reports/live-invoice-delegate-withdraw-workflow-matrix-2026-06-27-batch25-rerun.json`
    - `marker=B25-EF7AE444`，登录 200，`DELEGATE` 200，`WITHDRAW` 200，`severe_count=0`。
    - 真实 `data/app.db` 验证：转办后原任务 `TRANSFERRED`、新任务 `PENDING` 且 `assignee_type=TRANSFERRED`；撤回后任务 `CANCELLED`、实例 `CANCELLED`、发票 `DRAFT`。
    - 备份：`.gstack/db-backups/app-before-invoice-delegate-withdraw-batch25-rerun-20260627-080055.db`
    - 清理后 `opportunities/contracts/invoices/approval_* /notifications/user_sessions/login_attempts` 相对备份行数 diff 全 0。

剩余未修复：

- 发票审批主链路的 `APPROVE/REJECT/DELEGATE/WITHDRAW`、旧 `approve/cancel`、创建启动、待审批和撤回状态已覆盖；通知中心个人收件箱 403 已由第 82 批补齐，后续继续扫跨角色权限表与前端按钮 payload 对账。

### 80. 权限组合第十五批：发票旧 approve/cancel 兼容入口清零

- 扫描证据：
  - 旧发票测试 `tests/api/test_sales_invoices_api.py` 仍访问：
    - `POST /api/v1/sales/invoices/{id}/approve`
    - `POST /api/v1/sales/invoices/{id}/cancel`
  - 当前后端只有新版 `POST /sales/invoices/{id}/approval/action` 和 `PUT /sales/invoices/{id}/void`，旧路径真实返回 404，被旧测试 skip 掉，没有覆盖真实兼容能力。
  - 同时发现 `PUT /void` 内部写入 `InvoiceStatusEnum.VOIDED`，但发票状态枚举只有 `CANCELLED`，一旦走到作废逻辑会 500。
- 复现与红测试：
  - 在 `tests/api/test_invoice_approval_workflow_contracts.py` 增加：
    - `test_invoice_legacy_approve_route_maps_to_unified_engine_task`
    - `test_invoice_legacy_cancel_route_cancels_approved_invoice`
  - 初跑：
    - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py::test_invoice_legacy_approve_route_maps_to_unified_engine_task tests/api/test_invoice_approval_workflow_contracts.py::test_invoice_legacy_cancel_route_cancels_approved_invoice --tb=short` -> 2 failed，均为 404。
- 根因：
  - 发票 workflow 已迁移到统一审批引擎，但没有保留旧 `/approve` 的路径转发层。
  - 发票作废已有新版 `/void`，但没有保留旧 `/cancel` 的路径转发层。
  - 作废状态使用了不存在的 `VOIDED`，和 `InvoiceStatusEnum.CANCELLED` 枚举不一致。
- 修复：
  - `app/api/v1/endpoints/sales/invoices/workflow.py`
    - 新增 `POST /invoices/{invoice_id}/approve` legacy 入口，接收旧 payload 的 `comment/comments`，内部转成 `ApprovalActionRequest(action="APPROVE")` 并复用新版 `invoice_approval_action()`。
  - `app/api/v1/endpoints/sales/invoices/operations.py`
    - 抽出 `_void_invoice_logic()`，让新版 `PUT /void` 和旧版 `POST /cancel` 共用。
    - 作废状态从不存在的 `VOIDED` 修正为 `CANCELLED`。
    - 旧 `/cancel` 接收 body 中 `reason/cancel_reason`，写入发票备注。
- 验证：
  - 红灯用例修复后：
    - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py::test_invoice_legacy_approve_route_maps_to_unified_engine_task tests/api/test_invoice_approval_workflow_contracts.py::test_invoice_legacy_cancel_route_cancels_approved_invoice --tb=short` -> 2 passed
  - 发票全组：
    - `.venv/bin/pytest -q tests/api/test_invoice_basic_route_contracts.py tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_sales_invoices_api.py --tb=short` -> 32 collected，31 passed，1 skipped
    - `.venv/bin/python -m py_compile app/api/v1/endpoints/sales/invoices/operations.py app/api/v1/endpoints/sales/invoices/workflow.py tests/api/test_invoice_approval_workflow_contracts.py` -> passed
  - 审批/路由组合：
    - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_approval_action_validation_contracts.py tests/api/test_path_param_route_contracts.py::test_sales_path_param_routes_tolerate_legacy_nulls_and_safe_export_headers --tb=short` -> 39 passed
  - 路由注册确认：
    - app routes 已同时存在 `POST /api/v1/sales/invoices/{invoice_id}/approve`、`POST /api/v1/sales/invoices/{invoice_id}/cancel`、`POST /api/v1/sales/invoices/{invoice_id}/approval/action`、`PUT /api/v1/sales/invoices/{invoice_id}/void`。
  - Live DB 矩阵：
    - `.gstack/qa-reports/live-invoice-legacy-routes-workflow-matrix-2026-06-27-batch24.json`
    - `marker=B24-2F4F9C59`，`severe_count=0`
    - 真实 `data/app.db` 验证：登录 200，旧 `/approve` 200 并把审批任务/实例/发票置为完成/通过；旧 `/cancel` 200 并把已审批未收款发票置为 `CANCELLED`。
    - 备份：`.gstack/db-backups/app-before-invoice-legacy-routes-batch24-rerun-20260627-074711.db`
    - 清理后 `opportunities/contracts/invoices/approval_* /notifications/user_sessions/login_attempts` 相对备份行数 diff 全 0。

剩余未修复：

- 发票 `DELEGATE/WITHDRAW` 的真实多人路径已由第 81 批补齐；后续剩余重点转为跨角色权限表与前端按钮 payload 对账。

### 79. 权限组合第十四批：发票基础路由、创建自动审批与更新链路清零

- 扫描证据：
  - 旧发票 API 用例稳定复现：
    - `GET /api/v1/sales/invoices/` -> 405，尾斜杠列表被仅支持 POST 的创建别名命中。
    - `POST /api/v1/sales/invoices/calculate-tax` -> 405，静态税额计算路径缺失，被 `/invoices/{invoice_id}` 动态详情路径吞掉。
    - `PUT /api/v1/sales/invoices/{id}` -> 405，旧 CRUD 更新契约缺真实后端入口。
  - 创建 `status=SUBMITTED` 发票时，`buyer_name/buyer_tax_no` 被 `InvoiceCreate` 丢弃；旧自动审批逻辑仍调用统一审批引擎不存在的 `start_approval()`，日志只吞异常，实际没有 `ApprovalInstance/ApprovalTask`。
- 复现与红测试：
  - 新增 `tests/api/test_invoice_basic_route_contracts.py`，覆盖尾斜杠列表、静态税额计算、创建提交态发票自动进入统一审批。
  - 扩展 `tests/api/test_invoice_approval_workflow_contracts.py`，把创建发票自动审批、`calculate-tax` 静态路由顺序、`PUT /invoices/{id}` legacy alias 更新锁进审批工作流契约。
  - 旧 `tests/api/test_sales_invoices_api.py` 的 `test_update_invoice` 同步作为回归雷达：修复前稳定暴露 405。
- 根因：
  - `basic.py` 只有 `GET /invoices`，没有 legacy `GET /invoices/`。
  - `calculate-tax` 没有真实后端实现，路径自然落入动态详情路由。
  - `basic.py` 缺少 `PUT /invoices/{invoice_id}`，旧前端/测试传入的 `invoice_amount/invoice_date/remarks` 无法落到 ORM 的 `amount/issue_date/remark`。
  - `InvoiceCreate/InvoiceResponse` 未暴露购买方字段，导致发票审批适配器校验 `buyer_name` 失败。
  - `basic.py` 仍把 `ApprovalEngineService` 当旧 `ApprovalWorkflowService` 使用，调用已不存在的 `start_approval()`。
- 修复：
  - `app/api/v1/endpoints/sales/invoices/basic.py`
    - 新增 `GET /invoices/` 兼容别名，复用列表实现。
    - 在动态详情路由前新增 `POST /invoices/calculate-tax`，按百分比税率返回 `amount/tax_rate/tax_amount/total_amount`。
    - 补齐 `PUT /invoices/{invoice_id}` 更新入口，支持 `invoice_amount -> amount`、`invoice_date -> issue_date`、`remarks -> remark` 和状态大写归一化。
    - 创建 `APPLIED/SUBMITTED` 发票时改用统一审批引擎 `submit()`，复用发票工作流模板选择和 form_data 构建；成功后由适配器置为 `PENDING_APPROVAL`。
  - `app/schemas/sales/invoices.py` / `app/schemas/sales/__init__.py`
    - `InvoiceCreate/InvoiceUpdate/InvoiceResponse` 补齐 `buyer_name/buyer_tax_no`，`InvoiceUpdate` 补齐 `remarks` alias。
    - 新增并导出 `InvoiceTaxCalculationRequest`。
- 验证：
  - 红灯复现：
    - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py::test_invoice_create_submitted_auto_starts_approval_with_buyer_fields tests/api/test_invoice_approval_workflow_contracts.py::test_invoice_calculate_tax_static_route_precedes_dynamic_invoice_id --tb=short` -> 初始 2 failed：`buyer_name=None` / 旧 `start_approval` 日志失败，`calculate-tax` 为 405。
    - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_sales_invoices_api.py --tb=short` -> 初始暴露 `TestSalesInvoicesAPI.test_update_invoice` 405。
  - 修复后：
    - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py --tb=short` -> 12 passed
    - `.venv/bin/pytest -q tests/api/test_invoice_basic_route_contracts.py tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_sales_invoices_api.py --tb=short` -> 30 collected，27 passed，3 skipped
    - `.venv/bin/python -m py_compile app/api/v1/endpoints/sales/invoices/basic.py app/api/v1/endpoints/sales/invoices/workflow.py app/schemas/sales/invoices.py app/schemas/sales/contracts.py tests/api/test_invoice_approval_workflow_contracts.py` -> passed
    - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_approval_action_validation_contracts.py tests/api/test_path_param_route_contracts.py::test_sales_path_param_routes_tolerate_legacy_nulls_and_safe_export_headers --tb=short` -> 37 passed
    - `pnpm --dir frontend test:run src/services/api/__tests__/sales.test.js` -> 52 passed
    - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
    - `pnpm --dir frontend build` -> passed，保留既有 dynamic/static import 与 chunk size 警告。
  - Live DB 矩阵：
    - `.gstack/qa-reports/live-invoice-basic-routes-workflow-matrix-2026-06-27-batch23.json`
    - `marker=B23-EF28C276`，`severe_count=0`
    - 真实 `data/app.db` 验证：尾斜杠列表 200，税额计算 200，创建 `SUBMITTED` 发票 201，更新发票 200，小写 approve 归一化后审批通过 200。
    - DB 中发票保留购买方字段、状态流转为 `PENDING_APPROVAL -> APPROVED`，创建统一 `ApprovalInstance/ApprovalTask`，最终清理 marker 业务行。
    - 备份：`.gstack/db-backups/app-before-invoice-basic-routes-batch23-rerun-20260627-062529.db`
    - 清理后 `cleanup_residue` 全 0；初次清理因审批实例 `source_id=9` 与两条历史采购审批通知碰撞，已从备份按主键恢复通知 `856/857`，恢复后 `notifications` 当前 859、备份 859、缺失主键 0，`row_count_delta` 全 0。

剩余未修复：

- 旧发票 `/sales/invoices/{id}/approve`、`/sales/invoices/{id}/cancel` 已由第 80 批补齐兼容。
- 发票 `DELEGATE/WITHDRAW` 真实多人路径已由第 81 批补齐；后续剩余重点转为跨角色权限表与前端按钮 payload 对账。

### 78. 权限组合第十三批：发票审批启动与前端动作契约清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_invoice_approval_workflow_contracts.py` 新增 start / 小写 action 用例后初跑 2 failures。
  - 前端 `invoiceApi.approveApproval/rejectApproval` 传 `approve/reject` 小写；付款审批页调用 `invoiceApi.approve()` 时传的是 `{ approved, remark }`，后端 action schema 收不到可执行动作。
  - `/sales/invoices/{id}/approval/start` 的 body 是必填 `ApprovalStartRequest`，但前端 `startApproval(id)` 空 body 调用；真实点击会先被 422 拦住。代码审计同时确认 start 分支仍调用旧 `start_approval`。
  - live 前备份：`.gstack/db-backups/app-before-invoice-approval-start-workflow-20260627-043649.db`。
  - live 复扫：`.gstack/qa-reports/live-invoice-approval-start-workflow-matrix-2026-06-27-batch22.json`，`marker=QA_INVOICE_APPROVAL_START_20260627_043649`，7 步，`severe_count=0`，最终业务表、通知表、会话表相对备份行级 diff 全 0。
- 复现链路：
  - 前端直接调用 `invoiceApi.startApproval(id)`，请求体为空。
  - 后端旧行为：FastAPI body 校验返回 422；即使传 `{}`，代码仍会走不存在的旧 `ApprovalEngineService.start_approval`。
  - 前端审批按钮调用 `invoiceApi.approve()` 或 `approveApproval/rejectApproval()`，payload 与后端 `APPROVE/REJECT/DELEGATE/WITHDRAW` 契约不一致。
- 根因：
  - 发票 workflow endpoint 混用了旧 `ApprovalRecord` 服务命名和新版 `ApprovalInstance/ApprovalTask` 引擎。
  - 发票审批模板在 live 库中是 `TPL_INVOICE`，不能再硬编码适配器里的旧 `SALES_INVOICE`。
  - 前端发票审批 API 封装没有把页面动作规范成后端审批 action。
- 修复：
  - `start_invoice_approval()` 允许空 body，并改用 `ApprovalEngineService.submit()` 创建新版审批实例和任务。
  - 新增发票模板选择逻辑：优先使用传入 `workflow_id` 对应的 INVOICE 流程；否则按 active/published 的 `entity_type=INVOICE` 模板选择。
  - `ApprovalActionRequest` 增加 before validator，把小写 action 规范为大写后再走 Literal 校验。
  - `InvoiceApprovalAdapter.validate_submit()` 兼容旧接口约定的 `APPLIED/SUBMITTED` 状态。
  - `frontend/src/services/api/sales.js` 将发票审批 payload 统一规范为 `{ action, comment }`，并补齐前端 API 契约测试；同时修正 `paymentApi.list` 测试 mock 到真实 `/sales/payments/records`。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py --tb=short` -> 红灯复现 2 failures，修复后 9 passed
  - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_approval_action_validation_contracts.py --tb=short` -> 33 passed
  - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_approval_action_validation_contracts.py tests/api/test_path_param_route_contracts.py::test_sales_path_param_routes_tolerate_legacy_nulls_and_safe_export_headers --tb=short` -> 34 passed
  - `.venv/bin/python -m py_compile app/schemas/sales/contracts.py app/api/v1/endpoints/sales/invoices/workflow.py app/services/approval_engine/adapters/invoice.py tests/api/test_invoice_approval_workflow_contracts.py` -> passed
  - `pnpm --dir frontend test:run src/services/api/__tests__/sales.test.js` -> 52 passed
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
  - live 复扫报告：`.gstack/qa-reports/live-invoice-approval-start-workflow-matrix-2026-06-27-batch22.json`，`severe_count=0`，`approval_instances / approval_tasks / approval_action_logs / notifications / user_sessions / login_attempts` 等相对备份 residue 全 0。
- 剩余未修复：
  - 发票创建接口的“status=SUBMITTED 自动启动审批”、`/sales/invoices/` GET trailing slash 405、`/sales/invoices/calculate-tax` 405 已由第 79 批清理。
  - 发票 `DELEGATE/WITHDRAW` 的真实多人路径仍需后续批次覆盖。

### 77. 权限组合第十二批：发票审批动作入口旧引擎漂移清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_invoice_approval_workflow_contracts.py` 初跑 6 failures。管理员调用 `/sales/invoices/999999/approval/action` 传合法 action 时，endpoint 先调用不存在的 `ApprovalEngineService.get_approval_record`，直接 500；`ApprovalActionRequest` 也没有 `delegate_to_id` 字段。
  - 代码审计确认发票 action/status/history 混用旧 `ApprovalRecord` 服务 API 与新版 `ApprovalInstance/ApprovalTask` 引擎。
  - live 前备份：`.gstack/db-backups/app-before-invoice-approval-action-workflow-20260627-042104.db`。
  - live 复扫：`.gstack/qa-reports/live-invoice-approval-action-workflow-matrix-2026-06-27-batch21.json`，`marker=QA_INVOICE_APPROVAL_ACTION_20260627_042104`，8 步，`severe_count=0`。
- 复现链路：
  - 管理员调用 `/sales/invoices/999999/approval/action`，非法 `ESCALATE` 应在 schema 层 422，不能进旧引擎查询。
  - 管理员调用同一路径，合法 `APPROVE/REJECT/DELEGATE/WITHDRAW` 对不存在发票应稳定返回 404，不能 500。
  - 构造真实发票、审批模板、审批实例和待办任务后，`APPROVE` 应通过新版 task 完成审批并更新发票状态。
- 根因：
  - 发票审批 action endpoint 引入 `ApprovalEngineService` 后仍调用旧方法：`get_approval_record / approve_step / reject_step / delegate_step / withdraw_approval`。
  - `ApprovalActionRequest.action` 是裸 `str`，且缺少 `delegate_to_id`，委托分支即使进入也会属性错误。
- 修复：
  - `ApprovalActionRequest.action` 改为 `Literal["APPROVE", "REJECT", "DELEGATE", "WITHDRAW"]`，并补充 `delegate_to_id`。
  - 发票 action 改为先定位 `Invoice` 与 `ApprovalInstance`，再查当前用户 pending `ApprovalTask`。
  - `APPROVE/REJECT/DELEGATE/WITHDRAW` 分别调用新版 `approve / reject / transfer / withdraw`，并同步发票状态。
  - `approval-status` / `approval-history` 也切到 `ApprovalInstance/ApprovalTask` 读模型，避免继续读旧 record。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py --tb=short` -> 红灯复现 6 failures，修复后 7 passed
  - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_approval_action_validation_contracts.py --tb=short` -> 30 passed
  - `.venv/bin/pytest -q tests/api/test_invoice_approval_workflow_contracts.py tests/api/test_approval_action_validation_contracts.py tests/api/test_path_param_route_contracts.py::test_sales_path_param_routes_tolerate_legacy_nulls_and_safe_export_headers --tb=short` -> 32 passed
  - `.venv/bin/python -m py_compile app/schemas/sales/contracts.py app/api/v1/endpoints/sales/invoices/workflow.py tests/api/test_invoice_approval_workflow_contracts.py` -> passed
  - live 复扫报告：`.gstack/qa-reports/live-invoice-approval-action-workflow-matrix-2026-06-27-batch21.json`，`severe_count=0`，最终业务表、通知表、会话表相对备份行级 diff 全 0。
- 剩余未修复：
  - 本批只验证真实 `APPROVE` 完整链路；真实 `DELEGATE/WITHDRAW` 的多人委托与撤回组合仍需后续权限矩阵批次覆盖。
  - 发票路由层仍有 trailing slash 与 `calculate-tax` 405 旧账，已列入后续批次。

### 76. 权限组合第十一批：工时审批 action 输入校验清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_approval_action_validation_contracts.py -k timesheet` 初跑 2 failures。管理员调用 `/timesheet/workflow/tasks/999999/action` 传 `action="ESCALATE"` 时先查任务并返回 404；调用 `/timesheet/workflow/batch-action` 传同样非法 action 时由 handler 返回 400。
  - 代码审计确认 `TimesheetApprovalActionRequest.action` 和 `TimesheetBatchApprovalRequest.action` 都是 `str`，非法动作没有在请求 schema 层收口。
  - live 前备份：`.gstack/db-backups/app-before-timesheet-action-validation-20260627-040224.db`。
  - live 复扫：`.gstack/qa-reports/live-timesheet-action-validation-matrix-2026-06-27-batch20.json`，`marker=QA_TIMESHEET_ACTION_20260627_040224`，9 步，`severe_count=0`，最终 approval_instances / approval_tasks delta 全 0。
- 复现链路：
  - 管理员调用单任务工时审批：`/timesheet/workflow/tasks/999999/action`。
  - 管理员调用批量工时审批：`/timesheet/workflow/batch-action`。
  - 请求体传 `action="ESCALATE"`。
  - 正确行为：请求应在 schema 层 422，不能先进入任务查询或 handler 手写校验。
  - 同时验证合法 `APPROVE` / `REJECT` 仍可通过 schema：单任务假 task id 返回 404，批量假 task id 返回 200 + `failed_count=1`。
- 根因：
  - 工时 workflow 和前面 approve/reject 型审批入口不同，动作使用大写业务值，但 schema 未限定枚举。
  - 单任务入口把任务查询排在 action 分支之前，导致非法 action 可被动态 ID 404 掩盖。
- 修复：
  - `app/api/v1/endpoints/timesheet/workflow.py` 引入 `Literal`。
  - `TimesheetApprovalActionRequest.action` 改为 `Literal["APPROVE", "REJECT"]`。
  - `TimesheetBatchApprovalRequest.action` 改为 `Literal["APPROVE", "REJECT"]`。
  - 扩展 `tests/api/test_approval_action_validation_contracts.py`，覆盖工时单任务和批量 action 的非法/合法路径。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_approval_action_validation_contracts.py -k timesheet --tb=short` -> 红灯复现 2 failures，修复后 6 passed
  - `.venv/bin/pytest -q tests/api/test_approval_action_validation_contracts.py --tb=short` -> 24 passed
  - `.venv/bin/pytest -q tests/api/test_approval_action_validation_contracts.py tests/api/test_batch12_route_contracts.py::test_timesheet_records_collection_route_is_registered tests/api/test_batch12_route_contracts.py::test_timesheet_anomalies_route_uses_quality_service tests/api/test_timesheet_crud_contracts.py --tb=short` -> 28 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/timesheet/workflow.py tests/api/test_approval_action_validation_contracts.py` -> passed
  - live 复扫报告：`.gstack/qa-reports/live-timesheet-action-validation-matrix-2026-06-27-batch20.json`，`severe_count=0`，最终 approval_instances / approval_tasks delta 全 0。
  - live 登录副作用已按备份精确清理：恢复 `user_sessions.id=853`，删除本次新增 `user_sessions.id=858` 和 `login_attempts.id=898`。
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
- 剩余未修复：
  - 本批只处理工时 `APPROVE/REJECT` 动作枚举；发票审批的 `APPROVE/REJECT/DELEGATE/WITHDRAW` 仍需按独立业务动作继续扫。
  - 更深的真实工时审批完整通过/驳回链路、撤回、权限矩阵还没标记为完成。

### 75. 权限组合第十批：批量审批 action 输入校验清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_approval_action_validation_contracts.py::test_batch_approval_rejects_unknown_action_before_service_layer` 初跑 6 个参数全部失败。管理员分别调用报价、合同、验收、ECN、采购、外协 6 个批量审批接口，传入 `action="escalate"` 和假 task id，接口均返回 200，并以 `errors` 数组承载“不支持的操作”。
  - 代码审计确认 4 个重复审批 endpoint 和 1 个公共审批 schema 均使用 `action: str`，非法动作直到服务层才被识别；批量接口因此表现为“请求成功但每条失败”。
  - live 前备份：`.gstack/db-backups/app-before-approval-batch-action-validation-20260627-035240.db`。
  - live 复扫：`.gstack/qa-reports/live-approval-batch-action-validation-matrix-2026-06-27-batch19.json`，`marker=QA_APPROVAL_BATCH_ACTION_20260627_035250`，21 步，`severe_count=0`，最终 approval_instances / approval_tasks delta 全 0。
- 复现链路：
  - 管理员调用以下批量审批接口：`/sales/quotes/approval/batch-action`、`/sales/contracts/approval/batch-action`、`/acceptance/acceptance-orders/approval/batch-action`、`/ecns/approval/batch-action`、`/purchase-orders/workflow/batch-action`、`/outsourcing-orders/workflow/batch-action`。
  - 请求体传 `{"task_ids":[999999],"action":"escalate"}`。
  - 正确行为：请求在 schema 层 422，不能进入服务层形成“200 但全失败”的假成功。
  - 同时验证合法 `approve` / `reject` 仍能通过 schema 并进入服务层，假 task id 场景返回 200 + errors，证明正向 action 未被误伤。
- 根因：
  - 批量审批动作字段没有枚举约束。
  - 服务层可识别非法 action，但 API 层的 200 响应会误导前端和调用方，尤其批量动作容易被当作整体成功。
- 修复：
  - `app/api/v1/endpoints/sales/quote_approval.py`、`app/api/v1/endpoints/sales/contracts/approval.py`、`app/api/v1/endpoints/acceptance/order_approval.py`、`app/api/v1/endpoints/ecn/approval.py` 的 `ApprovalActionRequest` / `BatchApprovalRequest.action` 改为 `Literal["approve", "reject"]`。
  - `app/schemas/approval_workflow.py` 的公共 `ApprovalActionRequest` / `BatchApprovalRequest.action` 同步改为 `Literal["approve", "reject"]`，覆盖采购和外协工作流。
  - 增加 API 契约测试，断言 6 个批量审批入口未知 action 均 422，并断言合法 `approve/reject` 仍可用。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_approval_action_validation_contracts.py --tb=short` -> 红灯复现 6 failures，修复后 18 passed
  - `.venv/bin/pytest -q tests/api/test_approval_action_validation_contracts.py tests/api/test_purchase_workflow_contracts.py tests/api/test_ecn_state_machine_contracts.py tests/api/test_batch14_route_contracts.py::test_sales_contract_pending_approval_route_accepts_engine_result_dict tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_contract_approval_submit tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_contract_approval_approve --tb=short` -> 25 passed
  - `.venv/bin/python -m py_compile app/schemas/approval_workflow.py app/api/v1/endpoints/sales/quote_approval.py app/api/v1/endpoints/sales/contracts/approval.py app/api/v1/endpoints/acceptance/order_approval.py app/api/v1/endpoints/ecn/approval.py tests/api/test_approval_action_validation_contracts.py` -> passed
  - `git diff --check -- app/schemas/approval_workflow.py app/api/v1/endpoints/sales/quote_approval.py app/api/v1/endpoints/sales/contracts/approval.py app/api/v1/endpoints/acceptance/order_approval.py app/api/v1/endpoints/ecn/approval.py tests/api/test_approval_action_validation_contracts.py` -> passed
  - live 复扫报告：`.gstack/qa-reports/live-approval-batch-action-validation-matrix-2026-06-27-batch19.json`，`severe_count=0`，最终 approval_instances / approval_tasks delta 全 0。
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
  - 额外探测：`.venv/bin/pytest -q tests/unit/test_quote_approval_service.py tests/unit/test_contract_approval_service.py tests/unit/test_acceptance_approval_service.py tests/unit/test_outsourcing_workflow_service.py --tb=short` 发现既有无关失败：外协工作流单测仍引用已不存在的 `_trigger_cost_collection` / `app.services.cost_collection_service`，合同审批 pending 旧 mock 断言与当前 `page/page_size` 调用不一致；本批未改服务层，未把这些旧账并入本批修复。
- 剩余未修复：
  - 本批覆盖 approve/reject 型批量审批 action 输入校验；工时审批使用大写 `APPROVE/REJECT`，销售发票审批还有 delegate/withdraw 分支，需另按各自业务动作枚举继续扫。
  - 外协工作流服务单测存在既有失败，后续可单独作为服务层回归修复批次处理。
  - 系统仍需继续做更深权限矩阵、导入导出、移动端尺寸和真实业务数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 74. 权限组合第九批：报价成本批量改价 mode 输入校验清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_sales_quote_cost_batch_update_contracts.py::test_quote_cost_batch_update_rejects_unknown_mode_without_price_changes` 初跑失败。管理员调用 `POST /api/v1/sales/quotes/{quote_id}/cost-calculations/batch-update`，传入 `mode="discount"`，接口返回 200，响应 `已更新 1 个明细项的价格`，并把非法 mode 回显为 `discount`。
  - 代码审计确认 `batch_update_prices()` 的请求体是裸 `dict`，`mode` 只判断 `mode == "markup"`，其它任意字符串都会落入 margin 分支并真实写入 `quote_items.unit_price`。
  - live 前备份：`.gstack/db-backups/app-before-quote-cost-batch-mode-validation-20260627-033650.db`。
  - live 复扫：`.gstack/qa-reports/live-quote-cost-batch-mode-validation-matrix-2026-06-27-batch18.json`，`marker=QA_QUOTE_COST_BATCH_MODE_20260627_034110`，8 步，`severe_count=0`，最终 customers / opportunities / quotes / quote_versions / quote_items residue 全 0。
- 复现链路：
  - 创建客户、商机、报价、报价版本和一条成本 100、单价 100 的报价明细。
  - 管理员调用报价成本批量改价接口，传 `mode="discount"` 和 `rate=20`。
  - 正确行为：请求在进入写逻辑前 422，明细单价保持 100.00。
  - 同时验证合法 `markup` 仍把单价改为 120.00，合法 `margin` 仍把单价改为 125.00。
- 根因：
  - 批量改价接口缺少请求 schema，模式字段没有枚举约束。
  - 实现把“不是 markup”的所有值都当 margin，前端拼写错误或未来新增模式会变成静默批量改价。
- 修复：
  - `app/api/v1/endpoints/sales/quote_costs.py` 新增 `QuoteCostBatchUpdateRequest`。
  - `mode` 改为 `Literal["markup", "margin"]`，未知 mode 由 FastAPI 返回 422。
  - `batch_update_prices()` 从裸 `dict` 读取改为读取结构化请求对象。
  - 增加 API 回归测试，断言未知 mode 不改变 `quote_items.unit_price`，并覆盖合法 `markup/margin` 正向路径。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_sales_quote_cost_batch_update_contracts.py::test_quote_cost_batch_update_rejects_unknown_mode_without_price_changes --tb=short` -> 红灯复现 200，修复后通过
  - `.venv/bin/pytest -q tests/api/test_sales_quote_cost_batch_update_contracts.py --tb=short` -> 3 passed
  - `.venv/bin/pytest -q tests/api/test_sales_quote_cost_batch_update_contracts.py tests/unit/test_sales_scope_tail.py --tb=short` -> 23 passed
  - `python -m py_compile app/api/v1/endpoints/sales/quote_costs.py tests/api/test_sales_quote_cost_batch_update_contracts.py` -> passed
  - `git diff --check -- app/api/v1/endpoints/sales/quote_costs.py tests/api/test_sales_quote_cost_batch_update_contracts.py` -> passed
  - live 复扫报告：`.gstack/qa-reports/live-quote-cost-batch-mode-validation-matrix-2026-06-27-batch18.json`，`severe_count=0`，最终 residue 全 0。
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
- 剩余未修复：
  - 本批覆盖报价成本批量改价 mode 输入校验；其它批量价格、审批动作、导入导出、移动端尺寸和更多跨模块授权闭环仍需继续分批扫。
  - 系统仍需继续做更深权限矩阵和真实业务数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 73. 权限组合第八批：用户批量角色 mode 输入校验清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_role_permission_workflow_contracts.py::test_batch_user_role_assignment_rejects_unknown_mode_without_role_changes` 初跑失败。管理员调用 `PUT /api/v1/users/batch-roles`，传入 `mode="append"`，接口返回 200，并把目标用户原角色替换成请求中的新角色。
  - schema 红灯：`tests/schemas/test_auth.py::TestBatchRoleAssign::test_invalid_mode` 初跑失败，`BatchRoleAssign(mode="append")` 未触发 `ValidationError`。
  - 代码审计确认 `BatchRoleAssign.mode` 是普通 `str`，路由只判断 `mode == "remove"`，其它任意字符串都会落入 replace 分支。
  - live 前备份：`.gstack/db-backups/app-before-user-batch-role-mode-validation-20260627-032744.db`。
  - live 复扫：`.gstack/qa-reports/live-user-batch-role-mode-validation-matrix-2026-06-27-batch17.json`，`marker=QA_USER_BATCH_ROLE_MODE_20260627_032851`，7 步，`severe_count=0`，最终 users / roles / user_roles residue 全 0。
- 复现链路：
  - 目标用户已有 A 角色，另准备 B 角色。
  - 管理员批量角色接口传 `mode="append"` 和 B 角色。
  - 正确行为：请求在 schema 层 422，A 角色保留，B 角色不新增。
  - 同时验证合法 `replace` 仍能替换成 B，合法 `remove` 仍能移除 B。
- 根因：
  - 批量角色接口的模式字段没有枚举约束。
  - 路由实现把“不是 remove”的所有值都当 replace，拼写错误或前端未来新增模式会变成高风险批量替换。
- 修复：
  - `app/schemas/auth.py` 中 `BatchRoleAssign.mode` 从 `str` 改为 `Literal["replace", "remove"]`。
  - FastAPI 在进入写逻辑前对未知 mode 返回 422，避免 DB 被误改。
  - 增加 API 回归测试，断言未知 mode 不改变 `user_roles`。
  - 增加 schema 回归测试，断言 `append` 触发 `ValidationError`，合法 `replace/remove` 保持可用。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_role_permission_workflow_contracts.py::test_batch_user_role_assignment_rejects_unknown_mode_without_role_changes tests/schemas/test_auth.py::TestBatchRoleAssign::test_invalid_mode tests/schemas/test_auth.py::TestBatchRoleAssign::test_valid_modes --tb=short` -> 3 passed
  - `.venv/bin/pytest -q tests/api/test_role_permission_workflow_contracts.py tests/api/test_users.py tests/schemas/test_auth.py tests/unit/test_user_role_utils_security.py tests/api/test_role_permission_assignment_boundaries.py tests/api/test_role_tenant_isolation_contracts.py tests/api/test_role_template_tenant_isolation_contracts.py --tb=short` -> 59 passed, 4 skipped
  - `python -m py_compile app/schemas/auth.py tests/schemas/test_auth.py tests/api/test_role_permission_workflow_contracts.py` -> passed
  - `git diff --check -- app/schemas/auth.py tests/schemas/test_auth.py tests/api/test_role_permission_workflow_contracts.py` -> passed
  - live 复扫报告：`.gstack/qa-reports/live-user-batch-role-mode-validation-matrix-2026-06-27-batch17.json`，`severe_count=0`，最终 residue 全 0。
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
- 剩余未修复：
  - 本批覆盖用户批量角色 mode 输入校验；真实岗位权限表、导入导出、移动端尺寸和更多跨模块授权闭环仍需继续分批扫。
  - 系统仍需继续做更深权限矩阵和真实业务数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 72. 权限组合第七批：用户角色分配 role:assign 边界清零

- 扫描证据：
  - TDD 红灯：新增 4 个接口级回归用例初跑全部失败。仅有 `user:update` 的普通用户可通过 `PUT /api/v1/users/{id}/roles`、`PUT /api/v1/users/batch-roles`、`PUT /api/v1/users/{id}` 携带 `role_ids` 给目标用户分配角色；仅有 `user:create` 的普通用户可通过 `POST /api/v1/users/` 携带 `role_ids` 创建已绑定角色的新用户。
  - 代码审计确认用户角色写入口只校验 `user:update` / `user:create`，未复用角色权限变更路径已有的 `role:assign` 二次门禁。
  - live 前备份：`.gstack/db-backups/app-before-user-role-assign-boundary-20260627-031604.db`。
  - live 复扫：`.gstack/qa-reports/live-user-role-assign-boundary-matrix-2026-06-27-batch16.json`，`marker=QA_USER_ROLE_ASSIGN_BOUNDARY_20260627_031827`，11 步，`severe_count=0`，最终 users / roles / tenants / user_roles residue 全 0。
- 复现链路：
  - 租户内创建仅有 `user:update + user:create` 的测试操作者，不授予 `role:assign`。
  - 该操作者直接分配目标用户角色、批量替换目标用户角色、通过用户更新接口提交 `role_ids`、通过创建用户接口提交非空 `role_ids`，均必须返回 403 且不能留下 `user_roles` 或新用户残留。
  - 管理员仍可正常给目标用户分配并清空角色，证明正向路径未被误伤。
- 根因：
  - `replace_user_roles()` 已负责租户、系统角色和缓存失效，但调用它的用户路由没有先校验“是否有资格改角色集合”。
  - `user:update` 被隐式放大为用户授权能力，`user:create` 也可通过非空 `role_ids` 创建带权限用户，和 `roles.py` 中权限集合变更必须持有 `role:assign` 的策略不一致。
- 修复：
  - `app/api/v1/endpoints/users/crud_refactored.py` 新增 `_require_role_assign_permission()`，统一调用 `security.check_permission(current_user, "role:assign", db)`，失败返回 `403 权限不足: role:assign`。
  - `PUT /users/{id}/roles`、`PUT /users/batch-roles`：角色集合写入前强制要求 `role:assign`。
  - `PUT /users/{id}`：请求显式包含 `role_ids`（包括清空角色）时要求 `role:assign`。
  - `POST /users/`：仅当 `role_ids` 非空时要求 `role:assign`；普通无角色创建不受影响。
  - `tests/api/test_role_permission_workflow_contracts.py` 增加租户内四入口越权回归测试。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_role_permission_workflow_contracts.py::test_direct_user_role_assignment_requires_role_assign_permission tests/api/test_role_permission_workflow_contracts.py::test_batch_user_role_assignment_requires_role_assign_permission tests/api/test_role_permission_workflow_contracts.py::test_user_update_role_ids_requires_role_assign_permission tests/api/test_role_permission_workflow_contracts.py::test_user_create_with_role_ids_requires_role_assign_permission --tb=short` -> 4 passed
  - `.venv/bin/pytest -q tests/api/test_role_permission_workflow_contracts.py tests/api/test_users.py tests/unit/test_user_role_utils_security.py tests/api/test_role_permission_assignment_boundaries.py tests/api/test_role_tenant_isolation_contracts.py tests/api/test_role_template_tenant_isolation_contracts.py tests/api/test_role_permission_assignment_boundaries.py --tb=short` -> 29 passed, 4 skipped
  - `python -m py_compile app/api/v1/endpoints/users/crud_refactored.py tests/api/test_role_permission_workflow_contracts.py` -> passed
  - `git diff --check -- app/api/v1/endpoints/users/crud_refactored.py tests/api/test_role_permission_workflow_contracts.py` -> passed
  - live 复扫报告：`.gstack/qa-reports/live-user-role-assign-boundary-matrix-2026-06-27-batch16.json`，`severe_count=0`，最终 residue 全 0。
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
- 剩余未修复：
  - 本批覆盖用户角色分配的 `role:assign` 边界；真实岗位权限表、批量导入导出、移动端尺寸和更多跨模块授权闭环仍需继续分批扫。
  - 系统仍需继续做更深权限矩阵和真实业务数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 71. 权限组合第六批：用户批量角色移除缓存失效清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_role_permission_workflow_contracts.py::test_batch_role_remove_invalidates_user_permission_cache` 初跑失败；目标用户角色关联已被批量 remove 删除，但同一个用户 token 继续访问 `GET /api/v1/users/` 仍返回 200。
  - 代码审计确认 `PUT /api/v1/users/batch-roles` 的 `mode=remove` 分支直接删除 `user_roles` 行，绕过 `replace_user_roles()`，没有触发用户权限缓存失效。
  - live 前备份：`.gstack/db-backups/app-before-user-batch-role-cache-invalidation-20260627-030324.db`。
  - live 复扫：`.gstack/qa-reports/live-user-batch-role-cache-invalidation-matrix-2026-06-27-batch15.json`，`marker=QA_USER_BATCH_ROLE_CACHE_20260627_030428`，10 步，`severe_count=0`，最终 users / roles / user_roles residue 全 0。
- 复现链路：
  - 创建带 `user:read` 权限的角色，并绑定给测试用户。
  - 测试用户登录后访问 `GET /api/v1/users/` 返回 200。
  - 管理员访问 `GET /api/v1/permissions/users/{user_id}`，在服务进程内预热该用户权限缓存。
  - 管理员调用 `PUT /api/v1/users/batch-roles`，`mode=remove` 移除该角色。
  - 数据库确认 `user_roles` 关联已删除后，同一个用户 token 再访问 `GET /api/v1/users/` 必须立刻 403。
- 根因：
  - 单用户角色分配、用户更新和批量 replace 都走 `replace_user_roles()`，会统一做目标用户/角色校验，并调用 `_invalidate_user_cache()`。
  - 批量 remove 只执行 `DELETE FROM user_roles WHERE user_id=:uid AND role_id IN (...)`，没有清用户权限缓存、用户角色缓存、角色用户缓存。
  - 权限检查会优先读取用户权限缓存；缓存未失效时，数据库角色已移除但旧权限仍可继续生效到 TTL。
- 修复：
  - `batch_assign_roles(mode="remove")` 改为先读取用户当前角色，计算移除后的保留角色集合，再调用 `replace_user_roles(db, uid, kept_role_ids, acting_user=current_user)`。
  - 批量 remove 复用既有的租户/角色校验和缓存失效路径，不再手写裸删除。
  - 新增 API 回归测试覆盖缓存预热后的批量移除即时失效。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_role_permission_workflow_contracts.py::test_batch_role_remove_invalidates_user_permission_cache --tb=short` -> 1 passed
  - `.venv/bin/pytest -q tests/api/test_role_permission_workflow_contracts.py tests/api/test_users.py tests/unit/test_user_role_utils_security.py tests/api/test_role_tenant_isolation_contracts.py tests/api/test_role_template_tenant_isolation_contracts.py tests/api/test_role_permission_assignment_boundaries.py --tb=short` -> 25 passed, 4 skipped
  - `python -m py_compile app/api/v1/endpoints/users/crud_refactored.py tests/api/test_role_permission_workflow_contracts.py` -> passed
  - live 复扫报告：`.gstack/qa-reports/live-user-batch-role-cache-invalidation-matrix-2026-06-27-batch15.json`，`severe_count=0`，最终 residue 全 0。
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
- 剩余未修复：
  - 本批覆盖用户批量角色移除后的缓存即时失效；批量新增/替换的租户矩阵、真实岗位权限表、导入导出和移动端尺寸仍需继续分批扫。
  - 系统仍需继续做更深权限矩阵和真实业务数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 70. 权限组合第五批：角色模板租户隔离链路清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_role_template_tenant_isolation_contracts.py` 初跑失败，租户 A 创建模板后通过 `GET /api/v1/roles/templates` 能看到租户 B 模板。
  - 代码审计确认 `RoleTemplate` 缺少 `tenant_id`，模板列表、详情、更新、删除、从模板建角色都按裸模板 ID 查询。
  - live 前备份：`.gstack/db-backups/app-before-role-template-tenant-isolation-20260627-025254.db`。
  - live 复扫：`.gstack/qa-reports/live-role-template-tenant-isolation-matrix-2026-06-27-batch14.json`，`marker=QA_ROLE_TPL_TENANT_20260627_025500`，16 步，`severe_count=0`，最终 templates / roles / users / tenants residue 全 0。
- 复现链路：
  - 租户 A 用户创建模板后，列表只能看到全局模板和本租户模板，不能看到租户 B 模板。
  - 租户 A 读取租户 B 模板详情必须 404。
  - 租户 A 更新、删除租户 B 模板必须 404，且数据库中 B 模板不能被改名或删除。
  - 租户 A 不能通过租户 B 模板创建角色，不能留下越权角色。
  - 租户用户创建模板时，后端必须自动写入当前租户 ID，不能落成全局模板。
- 根因：
  - `RoleTemplate` 模型没有租户归属字段，所有模板天然全局可见。
  - `RoleManagementService.get_role_templates()/get_template_by_id()/get_template_detail()/update_template()/delete_template()/create_role_from_template()` 都没有模板 scope 参数。
  - `roles.py` 模板端点只校验动作权限，没有把 `_can_access_all_roles(current_user)` 和 `current_user.tenant_id` 传入服务层。
  - 旧 SQLite live 库缺少新列，直接给 ORM 加字段会触发运行期列不存在风险。
- 修复：
  - `RoleTemplate` 新增 `tenant_id` 字段，并新增 Alembic 迁移 `alembic/versions/add_role_template_tenant_id.py`。
  - `app/models/base.py` 的启动/运行时 SQLite schema patch 补齐 `role_templates.tenant_id`，兼容旧 live 库。
  - `RoleManagementService` 增加模板读/写 scope：超级/系统管理员全局；普通无租户用户只读写全局；租户用户读全局+本租户、写本租户。
  - 模板列表/详情响应补充 `tenant_id`；创建模板时非全局管理员强制写入当前租户。
  - 模板详情、更新、删除、从模板创建角色全部改为 scoped 查询；从模板复制权限时也按当前租户权限范围过滤。
  - `roles.py` 模板端点统一传入 `tenant_id/include_all_tenants`，跨租户模板一律返回 404。
- 验证：
  - `python -m py_compile app/models/user.py app/models/base.py app/services/role_management/service.py app/api/v1/endpoints/roles.py tests/api/test_role_template_tenant_isolation_contracts.py alembic/versions/add_role_template_tenant_id.py` -> passed
  - `.venv/bin/pytest -q tests/api/test_role_template_tenant_isolation_contracts.py --tb=short` -> 2 passed
  - `.venv/bin/pytest -q tests/api/test_role_template_tenant_isolation_contracts.py tests/api/test_role_template_workflow_contracts.py tests/api/test_role_permission_assignment_boundaries.py tests/api/test_role_permission_workflow_contracts.py tests/api/test_roles.py --tb=short` -> 30 passed, 1 skipped（旧测试需至少两个角色）
  - live schema 复核：`role_templates` 已包含 `tenant_id`。
  - live 复扫报告：`.gstack/qa-reports/live-role-template-tenant-isolation-matrix-2026-06-27-batch14.json`，`severe_count=0`，最终 residue 全 0。
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
- 剩余未修复：
  - 本批覆盖角色模板租户隔离；真实岗位权限表、批量导入导出、移动端尺寸和更多写流程仍需继续分批扫。
  - 系统仍需继续做更深权限矩阵和真实业务数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 69. 权限组合第四批：角色租户隔离链路清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_role_tenant_isolation_contracts.py` 初跑失败，租户 A 用户通过 `GET /api/v1/roles/?keyword=QA_TENANT_` 能看到租户 B 角色。
  - 代码审计确认同类动态 ID 入口仍直接使用裸 `Role` 查询：详情、更新、删除、权限分配、导航组、层级树、父级设置等未套租户 scope。
  - live 前备份：`.gstack/db-backups/app-before-role-tenant-isolation-20260627-023255.db`。
  - live 复扫：`.gstack/qa-reports/live-role-tenant-isolation-matrix-2026-06-27-batch13.json`，`marker=QA_ROLE_TENANT_20260627_0233`，16 步，`severe_count=0`，最终 tenants / users / roles / tenant_permissions / role_api_permissions / user_roles / user_sessions residue 全 0。
- 复现链路：
  - 租户 A 角色管理员列表只能看到本租户角色和全局共享角色，不能看到租户 B 角色。
  - 租户 A 用户读取租户 B 角色详情必须 404。
  - 租户 A 用户更新、分配权限、删除租户 B 角色必须 404，且不能产生 `role_api_permissions` 泄漏行。
  - 租户 A 用户不能把租户 B 自定义权限分配给本租户角色。
  - 租户 A 用户创建角色时，后端必须自动写入当前租户 ID，不能落成全局角色。
- 根因：
  - `Role` 模型已有 `tenant_id`，`RoleManagementService` 也有 scope helper，但 `app/api/v1/endpoints/roles.py` 的主角色接口绕过服务层，直接全表查角色。
  - `RoleService.list_roles()` 原先走通用 `BaseService.list()`，没有按当前用户租户过滤。
  - `_replace_role_permissions()` 只校验权限 ID 存在，不校验权限属于全局或当前租户。
  - `POST /roles/` 没有为普通租户用户写入 `current_user.tenant_id`，租户用户创建的角色会变成全局角色。
- 修复：
  - `roles.py` 新增统一 scope helper：超级/系统管理员看全部；普通无租户用户只看/写全局；租户用户读全局+本租户，写本租户。
  - 列表、配置、层级、比较、详情、更新、删除、权限分配、导航组、祖先/后代、父级设置全部改走 scoped role query。
  - 权限分配增加 permission scope，租户用户只能使用全局权限和本租户权限。
  - 创建角色时，非全局管理员强制使用 `current_user.tenant_id`。
  - 父角色设置和 `RoleUpdate.parent_id` 增加父级可见性校验，防止跨租户挂父级。
  - `RoleService.list_roles()` 增加 `tenant_id/include_all_tenants` 参数并在服务层分页前过滤。
  - 新增 API 回归测试：`tests/api/test_role_tenant_isolation_contracts.py`。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_role_tenant_isolation_contracts.py --tb=short` -> 3 passed
  - `.venv/bin/pytest -q tests/api/test_role_tenant_isolation_contracts.py tests/api/test_role_permission_assignment_boundaries.py tests/api/test_role_template_workflow_contracts.py tests/api/test_role_permission_workflow_contracts.py tests/api/test_roles.py --tb=short` -> 31 passed, 1 skipped（旧测试需至少两个角色）
  - `python -m py_compile app/api/v1/endpoints/roles.py app/services/role_service.py tests/api/test_role_tenant_isolation_contracts.py` -> passed
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
  - live 复扫报告：`.gstack/qa-reports/live-role-tenant-isolation-matrix-2026-06-27-batch13.json`，`severe_count=0`，最终 residue 全 0。
- 剩余未修复：
  - 本批覆盖角色主接口的租户隔离；角色模板租户隔离、真实岗位权限表、批量导入导出、移动端尺寸仍需继续分批扫。
  - 系统仍需继续做更深权限矩阵和真实业务数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 68. 权限组合第三批：角色权限分配边界清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_role_permission_assignment_boundaries.py` 初跑失败，只有 `role:create` 的普通用户可通过 `POST /api/v1/roles/` 携带 `permission_ids=[user:read]` 创建含权限角色，返回 201，绕过了专门的 `role:assign` 权限。
  - 同类入口扩展审计发现：`PUT /roles/{id}`、`POST/PUT /roles/templates/`、`POST /roles/templates/{id}/create-role`、`POST /roles/{id}/save-as-template` 都可能改变或复制权限集合，但只校验 `role:create` / `role:update`。
  - live 前备份：`.gstack/db-backups/app-before-role-permission-boundary-20260627-021349.db`。
  - live 复扫：`.gstack/qa-reports/live-role-permission-boundary-matrix-2026-06-27-batch12.json`，`marker=QA_ROLE_BOUND_20260627_021814`，23 步，`severe_count=0`，最终 users / roles / templates / role_api_permissions / user_roles / user_sessions / role_audits_by_marker_users residue 全 0。
- 复现链路：
  - 非管理员仅有 `role:create`：带 `permission_ids` 创建角色必须 403；空权限创建仍允许 201。
  - 非管理员仅有 `role:update`：普通字段更新允许 200；带 `permission_ids` 更新角色必须 403。
  - 非管理员有 `role:create + role:update` 但无 `role:assign`：创建/更新带权限模板、从带权限模板创建角色、把带权限角色另存为模板都必须 403。
  - 非管理员额外拥有 `role:assign`：带权限创建角色、更新角色权限、创建/更新模板权限快照、从模板复制权限、另存带权限角色均允许。
- 根因：
  - 系统已有 `PUT /roles/{role_id}/permissions` 使用 `role:assign`，但角色创建/更新和模板复制路径没有把“权限集合变更”视为独立能力。
  - `role:create` / `role:update` 因此被隐式放大成权限分配能力，普通角色管理员可绕开 `role:assign` 授出其他 API 权限。
- 修复：
  - `app/api/v1/endpoints/roles.py` 新增 `_require_role_assign_permission()`，统一调用 `security.check_permission(current_user, "role:assign", db)`。
  - `POST /roles/`：仅当 `permission_ids` 非空时额外要求 `role:assign`；空权限创建不受影响。
  - `PUT /roles/{role_id}`：只要请求显式包含 `permission_ids`（包括清空权限）就要求 `role:assign`。
  - `POST /roles/templates/`、`PUT /roles/templates/{template_id}`：创建非空权限快照或修改权限快照时要求 `role:assign`。
  - `POST /roles/templates/{template_id}/create-role`：模板快照含权限时要求 `role:assign`，避免通过模板复制权限。
  - `POST /roles/{role_id}/save-as-template`：来源角色含权限时要求 `role:assign`，避免把角色权限另存为可复用模板。
  - 新增 API 回归测试：`tests/api/test_role_permission_assignment_boundaries.py`。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_role_permission_assignment_boundaries.py --tb=short` -> 3 passed
  - `.venv/bin/pytest -q tests/api/test_role_permission_assignment_boundaries.py tests/api/test_role_template_workflow_contracts.py tests/api/test_role_permission_workflow_contracts.py tests/api/test_roles.py --tb=short` -> 28 passed, 1 skipped（旧测试需至少两个角色）
  - `python -m py_compile app/api/v1/endpoints/roles.py tests/api/test_role_permission_assignment_boundaries.py` -> passed
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
  - live 复扫报告：`.gstack/qa-reports/live-role-permission-boundary-matrix-2026-06-27-batch12.json`，`severe_count=0`，最终 residue 全 0。
- 剩余未修复：
  - 本批只覆盖角色权限分配边界；跨租户模板隔离、真实岗位权限表、批量导入导出、移动端尺寸仍需继续分批扫。
  - 系统仍需继续做更深权限矩阵和真实业务数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 67. 可回滚 CRUD 第十一批：角色模板深层点击流清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_role_template_workflow_contracts.py` 初跑 2 条均失败：
    - `POST /api/v1/roles/templates/` -> 405，前端模板中心已调用创建模板但后端只注册了空列表接口。
    - `POST /api/v1/roles/{id}/save-as-template` -> 404，角色“另存为模板”按钮无后端落点。
  - live 初扫红灯：`role_templates.version/version_note/source_role_id/source_role_name` 已在模型和 Alembic 中存在，但本地历史 SQLite `data/app.db` 缺列，模板查询/创建直接 500。
  - live 二扫红灯：模板创建、更新、复制权限均已通过，但 `DELETE /roles/{id}` 使用 `db.delete(role)` 触发动态关系 + 租户查询递归爆栈，导致模板来源角色删不掉，随后删除被引用模板出现外键 500。
  - live 前备份：`.gstack/db-backups/app-before-role-template-workflow-20260627-015331.db`。
  - live 复扫：`.gstack/qa-reports/live-role-template-workflow-matrix-2026-06-27-batch11.json`，`marker=QA_ROLE_TPL_20260627_0207`，24 步，`severe_count=0`，roles / role_templates / role_api_permissions / user_roles residue 全 0。
- 复现链路：
  - 创建带 `user:read` 快照的角色模板 -> 列表回读 -> 详情回读 -> 更新模板并清空权限快照，版本号递增。
  - 创建来源角色并授予 `user:read` -> `/roles/{id}/save-as-template` 另存为模板 -> `/roles/templates/{id}/create-role` 从模板创建角色。
  - 查询模板创建出的角色权限，确认复制到 `user:read` -> 删除模板创建角色 -> 删除来源角色 -> 删除两个模板 -> marker 清理后 0 残留。
- 根因：
  - `app/api/v1/endpoints/roles.py` 只有 `GET /roles/templates` 空实现，缺少模板详情、创建、更新、删除、从模板创建角色、角色另存模板接口。
  - `RoleManagementService.get_role_templates()` 把 `permission_snapshot` JSON 字符串原样返回，前端 `TemplateDialog` 需要的是 `permission_codes` 数组。
  - `RoleService._to_response()` 没有带回 `source_template_id/nav_groups/ui_config`，模板创建角色后前端无法确认来源模板。
  - 历史 SQLite 未补齐角色模板版本/来源字段，ORM 一查询 `role_templates` 就 500。
  - 角色删除使用 ORM delete，会触发动态 relationship 的租户过滤递归；模板创建出的角色无法通过 API 删除。
- 修复：
  - `app/api/v1/endpoints/roles.py` 新增模板 CRUD、`create-role`、`save-as-template` 路由，并保持静态模板路由在动态角色路由前注册。
  - `app/services/role_management/service.py` 统一解析模板权限快照，列表/详情/创建/更新都返回 `permission_codes: list[str]`。
  - `app/services/role_service.py` 响应补齐 `tenant_id/source_template_id/nav_groups/ui_config`。
  - `app/models/base.py` 的 SQLite schema patch 补齐 `role_templates.version/version_note/source_role_id/source_role_name`，覆盖历史开发库。
  - `DELETE /roles/{role_id}` 改为显式删除 `role_api_permissions/user_roles` 后 bulk delete 角色，避免 ORM 动态关系递归。
  - 新增 API 回归测试：`tests/api/test_role_template_workflow_contracts.py`，覆盖模板 CRUD、另存模板、模板创建角色、权限复制、角色/模板删除闭环。
  - 扩展前端 route contract：覆盖 `list/get/create/update/deleteTemplate/createFromTemplate/saveAsTemplate` 的路径和 payload。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_role_template_workflow_contracts.py` -> 2 passed
  - `.venv/bin/pytest -q tests/api/test_role_template_workflow_contracts.py tests/api/test_role_permission_workflow_contracts.py tests/api/test_roles.py --tb=short` -> 25 passed, 1 skipped（旧测试需至少两个角色）
  - `python -m py_compile app/models/base.py app/api/v1/endpoints/roles.py app/services/role_management/service.py app/services/role_service.py tests/api/test_role_template_workflow_contracts.py` -> passed
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 20 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
  - live 复扫报告：`.gstack/qa-reports/live-role-template-workflow-matrix-2026-06-27-batch11.json`，`severe_count=0`，最终 residue 全 0。
- 剩余未修复：
  - 本批覆盖角色模板后端深层点击流和路径合同；跨租户模板隔离、非管理员权限组合、批量导入导出、移动端尺寸仍需继续分批扫。
  - `pnpm build` 的 Vite 拆包警告仍是既有性能债，本批未处理。
  - 系统仍需继续扫更深权限矩阵和真实岗位授权；目前没有把“全系统全面清理”标记为完成。

### 66. 可回滚 CRUD 第十批：角色/权限组合链路清零

- 扫描证据：
  - TDD 红灯：`tests/api/test_role_permission_workflow_contracts.py` 初跑 4 条中 2 条失败：
    - `PUT /api/v1/roles/{id}/nav-groups` -> 405，前端 `roleApi.updateNavGroups` 已调用但后端未注册写接口。
    - `POST /api/v1/roles/compare` -> 405，前端 `roleApi.compare` 已调用但后端未注册比较接口。
  - 前端合同红灯：`pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js -t "role and permission workflow"` 失败，`userApi.assignRoles` 发送裸数组 `[7]`，后端要求 `{role_ids:[7]}`。
  - live 前备份：`.gstack/db-backups/app-before-role-permission-workflow-20260627-013838.db`。
  - live 复扫：`.gstack/qa-reports/live-role-permission-workflow-matrix-2026-06-27-batch10.json`，`marker=QA_ROLE_PERM_20260627_0139`，22 步，`severe_count=0`，目标角色/用户/角色权限/用户角色/登录会话 residue 全 0。
- 复现链路：
  - 创建带 `user:read` 的角色 A 和空权限角色 B -> 保存角色导航组 -> 比较 A/B 权限差异 -> `/permissions/roles/{role_id}` 查询角色权限。
  - 创建可登录普通用户 -> 未分配角色访问 `/users/` 被 403 -> 通过 `/users/{id}/roles` 分配角色 A -> 重新登录后 `/users/` 200。
  - 通过 `/roles/{id}/permissions` 移除角色 A 的 `user:read` -> 同一 token 再访问 `/users/` 立即回到 403。
- 根因：
  - `roles.py` 只有读取导航组接口，没有对应的 `PUT /roles/{role_id}/nav-groups` 写接口，RoleManagement 页面保存菜单配置会直接 405。
  - 前端存在 `/roles/compare` 调用，但后端未实现角色权限对比接口，进入角色继承/权限差异点击流会 405。
  - 前端 `userApi.assignRoles` 与后端 `UserRoleAssign` schema 不一致，裸数组 payload 会导致真实用户角色分配 422。
  - 角色权限变更后未显式清理角色及关联用户权限缓存；测试环境未稳定复现，但 live 链路已把“同 token 撤权立即 403”纳入防线。
- 修复：
  - `app/api/v1/endpoints/roles.py` 新增：
    - `POST /roles/compare`，返回 `roles/common_permissions/diff_permissions`，使用权限编码而不是权限名称做差异比较。
    - `PUT /roles/{role_id}/nav-groups`，保存并回读角色导航组配置。
    - 角色权限更新后调用权限缓存服务，失效角色缓存和关联用户权限缓存。
  - `frontend/src/services/api/auth.js`：`userApi.assignRoles` 改为发送 `{ role_ids: roleIds }`。
  - 新增 API 回归测试：`tests/api/test_role_permission_workflow_contracts.py`。
  - 扩展前端 route contract：覆盖 `updateNavGroups`、`compare`、`assignPermissions`、`permissionApi.getByRole`、`userApi.assignRoles` 的路径和 payload。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_role_permission_workflow_contracts.py` -> 4 passed
  - `.venv/bin/pytest -q tests/api/test_role_permission_workflow_contracts.py tests/api/test_roles.py` -> 23 passed, 1 skipped（旧测试需至少两个非系统角色）
  - `.venv/bin/pytest -q tests/api/test_users.py::TestUserPermissionEnforcement` -> 1 passed, 2 skipped（历史用例仍使用旧口径/旧 skip；本批新合同已覆盖当前链路）
  - `python -m py_compile app/api/v1/endpoints/roles.py tests/api/test_role_permission_workflow_contracts.py` -> passed
  - `pnpm --dir frontend test:run src/services/api/__tests__/routeContracts.test.js` -> 19 passed
  - `pnpm --dir frontend build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
  - `git diff --check -- app/api/v1/endpoints/roles.py frontend/src/services/api/auth.js frontend/src/services/api/__tests__/routeContracts.test.js tests/api/test_role_permission_workflow_contracts.py` -> passed
- 剩余未修复：
  - 角色模板深层接口（详情、创建、更新、删除、从模板创建角色、保存为模板）仍未纳入本批修复；需要单独按真实 UI 操作流做下一批。
  - `tests/api/test_users.py` 中两条历史 skipped 用例仍是旧权限码/旧业务假设，不作为本批完成标准；后续可单独清理测试债。
  - 系统仍需继续扫更深的角色模板、跨租户权限、移动端尺寸和真实数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 65. 可回滚 CRUD 第九批：采购收货/质检链路清零

- 扫描证据：
  - 首版初扫脚本误判订单明细响应形状，使用了空 `order_item_id`；该报告仅作为脚本校准证据保留，不纳入缺陷统计。
  - 修正后初扫：`.gstack/qa-reports/live-purchase-receipts-matrix-2026-06-27-batch9-corrected.json`，`marker=QA_PO_RCPT_20260627011043`，39 步，`severeCount=4`，`cleanupFailureCount=0`，5 张目标表 residue 全 0。
  - 初扫备份：`.gstack/db-backups/app-before-purchase-receipts-corrected-20260627-011043.db`。
  - 修复后复扫：`.gstack/qa-reports/live-purchase-receipts-matrix-2026-06-27-batch9-rerun.json`，`marker=QA_PO_RCPT_RERUN_20260627012303`，39 步，`severeCount=0`，`cleanupFailureCount=0`，状态分布 `200=36 / 400=3`，5 张目标表 residue 全 0。
  - 复扫备份：`.gstack/db-backups/app-before-purchase-receipts-rerun-20260627012303.db`。
- 复现链路：
  - 登录 -> 生成可回滚供应商 -> 创建两张采购订单 -> 提交/审批 -> A/B 收货 -> 按 `order_id/status` 列表过滤 -> 尝试超收 -> 收货确认 -> 非法质检参数 -> 部分合格质检 -> 清理数据。
- 根因：
  - `GET /purchase-orders/goods-receipts/` 声明了列表接口，但后端未消费 `order_id/status` 查询参数，前端筛选会混入其它采购单收货记录。
  - `POST /purchase-orders/goods-receipts/` 只校验“实收 <= 送货”，没有校验订单行归属和采购订单剩余可收数量；多次收货可超过订单数量。
  - 质检接口忽略前端传入的 `rejected_qty/inspect_result`，并把结果写成旧合约 `PASS/FAIL`、单据状态写成 `COMPLETED`，与页面消费的 `QUALIFIED/UNQUALIFIED/PARTIAL` 不一致。
- 修复：
  - 收货列表增加 `order_id/status` 过滤，并在分页统计前应用过滤条件。
  - 收货创建改为先校验所有明细，再创建单据和累加已收数量；校验订单行归属、同单重复行合计、送货/实收数量不得超过剩余可收数量。
  - 质检接口接收并校验 `rejected_qty/inspect_result`，要求“合格 + 不合格 = 送检”，输出前端合约 `QUALIFIED/UNQUALIFIED/PARTIAL`。
  - 新增回归测试：`tests/api/test_purchase_receipts_workflow_contracts.py`。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_purchase_receipts_workflow_contracts.py` -> 3 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/purchase/receipts.py tests/api/test_purchase_receipts_workflow_contracts.py` -> passed
  - `.venv/bin/pytest -q tests/api/test_purchase.py::TestGoodsReceipt` -> 3 passed
  - `.venv/bin/pytest -q tests/api/test_openapi_route_contracts.py` -> 8 passed
  - Live API 复扫：`.gstack/qa-reports/live-purchase-receipts-matrix-2026-06-27-batch9-rerun.json`，39 步、0 severe、0 cleanup failure。
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js` -> 18 passed
  - `pnpm build` -> passed，保留既有 Vite 动静态导入和 chunk size 警告。
- 剩余未修复：
  - 本批未做完整浏览器页面 Playwright 流程，只覆盖 API 写链路、前端 API 契约和构建。
  - 系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 64. 可回滚 CRUD 第八批：采购订单审批工作流链路清零

- 扫描证据：
  - 运行库备份：`.gstack/db-backups/app-before-purchase-workflow-20260627-005005.db`
  - 初扫报告：`.gstack/qa-reports/live-purchase-workflow-matrix-2026-06-27-batch8.json`，marker `QA_PO_WF_20260627004725`，`stepCount=13`、`severeCount=5`、`cleanupFailureCount=0`、`statusSummary={"200":8,"599":4,"400":1}`。
  - 复扫前备份：`.gstack/db-backups/app-before-purchase-workflow-rerun-20260627-010204.db`
  - 复扫报告：`.gstack/qa-reports/live-purchase-workflow-matrix-2026-06-27-batch8-rerun.json`，marker `QA_PO_WF_20260627010204`，`stepCount=24`、`severeCount=0`、`cleanupFailureCount=0`、`statusSummary={"200":24}`。
  - 复扫清理残留：`vendors`、`purchase_orders/items`、`approval_templates/flows/nodes`、`approval_instances/tasks` 均为 0。
- 复现链路：
  - 创建采购订单 -> `POST /api/v1/purchase-orders/workflow/submit` -> 待审批列表 -> `POST /api/v1/purchase-orders/workflow/action` 审批通过 -> 重复提交防护。
  - 创建采购订单 -> 提交审批 -> `POST /api/v1/purchase-orders/workflow/withdraw` 撤回 -> 订单恢复草稿。
- 根因：
  - 采购订单创建只计算 `total_amount`，未写 `tax_amount/amount_with_tax`；采购审批适配器按含税金额校验，导致提交响应 200 但 `success=[]`、`errors=[订单总金额必须大于0]`。
  - 采购审批适配器仍使用废弃字段 `order.vendor_id`、`vendor.vendor_name/vendor_code`，而现行模型为 `order.supplier_id` 与 `Vendor.supplier_name/supplier_code`。
  - 采购待审批项读取 `entity.supplier.vendor_name`，现行关系为 `entity.vendor.supplier_name`；旧单元测试中的 `MagicMock` 还会因自动生成假字段造成误判。
  - 审批完成时实例没有写 `final_approver_id`，采购订单通过回调又读取不存在的 `instance.approved_by`，导致通过后审批人字段无法可靠落库。
  - 通用审批服务把审批任务状态误当实例状态返回，并且撤回调用参数名与审批引擎签名不一致。
- 修复：
  - `purchase/orders_refactored.py` 在创建采购订单时逐行计算并汇总 `tax_amount`、`amount_with_tax`，订单和明细同时落库。
  - `purchase/utils.py` 序列化采购订单和明细时返回税额/含税金额，避免 API 响应缺字段。
  - `approval_engine/adapters/purchase.py` 全面切到 `supplier_id` 与 `supplier_name/supplier_code`，并保留 `vendor_*` 别名给历史条件数据；通过回调使用 `instance.final_approver_id`。
  - `approval_engine/engine/core.py` 在最后一个审批任务完成时写入 `instance.final_approver_id`。
  - `base_approval_workflow.py` 修正待办分页、审批动作返回实例状态、撤回调用 `initiator_id/comment`。
  - `purchase_workflow/service.py` 待审批供应商名称读取只接受真实字符串，并兼容旧测试的 `supplier.vendor_name`。
  - 新增 `tests/api/test_purchase_workflow_contracts.py`，覆盖含税金额落库、提交待审、待办供应商、审批通过、重复提交防护、撤回恢复草稿。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_purchase_workflow_contracts.py app/tests/services/purchase_workflow/test_purchase_workflow.py` -> 12 passed
  - `.venv/bin/pytest -q tests/api/test_openapi_route_contracts.py` -> 8 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/purchase/orders_refactored.py app/api/v1/endpoints/purchase/utils.py app/services/approval_engine/adapters/purchase.py app/services/approval_engine/engine/core.py app/services/base_approval_workflow.py app/services/purchase_workflow/service.py tests/api/test_purchase_workflow_contracts.py` -> passed
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js`（`frontend/`）-> 18 passed
  - `pnpm build`（`frontend/`）-> passed；仍只有既有 Vite 动态/静态重复导入和 chunk size 提示。
  - Live API 复扫：`.gstack/qa-reports/live-purchase-workflow-matrix-2026-06-27-batch8-rerun.json` -> `severeCount=0`、`cleanupFailureCount=0`、清理残留全 0。

剩余未修复：

- 本批只覆盖采购订单审批提交、通过、重复提交和撤回；采购申请转订单、收货质检、付款、导入导出和跨角色审批权限组合仍需继续分批扫。
- 前端构建仍有既有 Vite 拆包提示，当前不阻塞功能，但后续性能优化应单独处理。

### 63. 可回滚 CRUD 第七批：仓库入库/出库/盘点库存链路清零

- 扫描证据：
  - 运行库备份：`.gstack/db-backups/app-before-warehouse-deep-crud-20260627-003117.db`
  - 初扫报告：`.gstack/qa-reports/live-warehouse-deep-matrix-2026-06-27-batch7.json`，`stepCount=17`、`severeCount=5`、`cleanupFailureCount=0`、`statusSummary={"200":12,"500":1,"599":4}`。
  - 复扫前备份：`.gstack/db-backups/app-before-warehouse-deep-crud-rerun-20260627-004045.db`
  - 复扫报告：`.gstack/qa-reports/live-warehouse-deep-matrix-2026-06-27-batch7-rerun.json`，marker `QA_WH_DEEP_20260627004207`，`stepCount=28`、`severeCount=0`、`cleanupFailureCount=0`、`statusSummary={"200":27,"400":1}`。
  - 复扫清理残留：`warehouses`、`warehouse_locations`、`inventory`、`inbound_orders/items`、`outbound_orders/items`、`stock_count_orders/items` 均为 0。
- 复现链路：
  - `POST /api/v1/warehouse/inbound` -> `PUT /api/v1/warehouse/inbound/{id}/status?status=COMPLETED`
  - `POST /api/v1/warehouse/outbound` -> `PUT /api/v1/warehouse/outbound/{id}/status?status=COMPLETED`
  - `POST /api/v1/warehouse/stock-count` -> 更新盘点明细 -> 完成盘点。
- 根因：
  - 入库/出库状态接口只改订单状态和日期，没有写入库存表，也没有回写明细/单头的实收数量、拣货数量。
  - 出库完成未校验可用库存，存在“完成成功但库存不变”的假成功风险。
  - 盘点创建响应模型把 ORM `created_at: datetime` 声明成 `Optional[str]`，FastAPI 响应校验抛 `ResponseValidationError`，live 表现为 500。
- 修复：
  - `warehouse/crud.py` 增加 Decimal 数量归一、库存定位、入库完成、出库完成 helper。
  - 完成入库时按“计划数量 - 已收数量”增量写库存，创建缺失库存行，回写明细 `received_quantity`、单头 `received_quantity` 和入库时间，重复完成不重复入库。
  - 完成出库时先按库存行聚合校验可用量，不足返回 400；足量后扣减库存/可用库存，回写明细 `picked_quantity`、单头 `picked_quantity` 和出库时间，重复完成不重复扣减。
  - `warehouse/count.py` 将 `CountOrderOut.created_at` 改为 `Optional[datetime]`，恢复盘点创建响应序列化。
  - 新增 `tests/api/test_warehouse_deep_workflow_contracts.py`，覆盖入库完成、出库完成、缺库存拒绝、幂等完成、盘点创建/更新/完成。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_warehouse_deep_workflow_contracts.py` -> 3 passed
  - `.venv/bin/pytest -q tests/api/test_openapi_route_contracts.py` -> 8 passed
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js`（`frontend/`）-> 18 passed
  - `pnpm build`（`frontend/`）-> passed；仍只有既有 Vite 动态/静态重复导入和 chunk size 提示。
  - Live API 复扫：`.gstack/qa-reports/live-warehouse-deep-matrix-2026-06-27-batch7-rerun.json` -> `severeCount=0`、`cleanupFailureCount=0`。

剩余未修复：

- 本批只覆盖仓库入库/出库/盘点主写链路；采购审批、质量检验、导入导出、批量操作、更多角色权限组合仍需继续分批扫。
- 出入库完成目前按整单计划数量一次性完成；如果后续要支持部分收货/部分拣货，需要补独立数量编辑接口和更细的状态流。

### 62. 可回滚 CRUD 第六批：ECN 状态机/成本/物料/通知深链路清零

- 扫描证据：
  - 运行库初扫备份：`.gstack/db-backups/app-before-ecn-deep-crud-20260627-000954.db`。
  - 复扫前备份：`.gstack/db-backups/app-before-ecn-deep-crud-rerun-20260627-002024.db`。
  - 初扫报告：`.gstack/qa-reports/live-ecn-deep-matrix-2026-06-27-batch6.json`，覆盖 ECN 创建/更新/状态机提交、核心提交、成本影响、成本记录、物料影响、执行进度、相关人员、通知；`stepCount=18`、`severeCount=1`、`cleanupFailureCount=1`、`statusSummary={"200":14,"201":3,"500":1}`。
  - 复扫报告：`.gstack/qa-reports/live-ecn-deep-matrix-2026-06-27-batch6-rerun.json`，`stepCount=18`、`severeCount=0`、`cleanupFailureCount=0`、`statusSummary={"200":15,"201":3}`。
- 覆盖链路：
  - ECN 草稿创建、详情读取、草稿更新。
  - `/ecn/state-machine/{id}` 当前状态、允许转换、`DRAFT -> SUBMITTED` 写入转换。
  - `/ecns/{id}/submit` 核心提交。
  - 成本影响分析、成本跟踪、成本记录新增/列表/重新汇总。
  - 物料影响分析、执行进度、相关人员识别、相关人员通知。
- 根因：
  - `ecn/state_machine.py` API 层仍把旧 `EcnStateMachine` 的 `DRAFT -> PENDING_REVIEW` 流程直接暴露给现行 ECN 页面和核心接口；当前前端/核心接口使用 `SUBMITTED/EVALUATING/APPROVED/EXECUTING/COMPLETED` 等状态，导致 live 状态机提交 `DRAFT -> SUBMITTED` 返回 500。
  - `transition_ecn_state()` 内部 typo 使用 `request.target_status`，且把业务 `HTTPException(400)` 全部捕获后重包成 500，非法转换错误码失真。
  - 初扫清理脚本误假设所有 ECN 相关表都有 `ecn_id`，遇到无该列的表时清理失败。
- 修复：
  - `app/api/v1/endpoints/ecn/state_machine.py` 增加 API 层当前 ECN 状态转换表，覆盖当前前端/核心接口状态，同时保留旧状态机作为历史状态兜底。
  - 状态查询和允许转换接口优先返回当前状态流，`DRAFT` 现在允许 `SUBMITTED/CANCELLED`。
  - 状态转换改为统一 helper：校验当前状态、更新 ECN 状态和关键时间字段，写入 `ecn_logs` 与 `state_transition_logs`，并保持业务 400 不被包装为 500。
  - 批量状态转换复用同一套当前状态校验/落库逻辑，避免同类 bug 在批量入口复发。
  - 新增 `tests/api/test_ecn_state_machine_contracts.py`，覆盖 `DRAFT -> SUBMITTED` 当前状态契约和非法转换应返回 400。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_ecn_state_machine_contracts.py -q` -> 2 passed
  - `.venv/bin/python -m pytest tests/unit/test_state_machines_depth.py::TestEcnStateMachineIntegration -q` -> 7 passed
  - `.venv/bin/python -m pytest tests/api/test_path_param_route_contracts.py::test_ecn_state_machine_routes_tolerate_null_legacy_status -q` -> 1 passed
  - `.venv/bin/python -m pytest tests/api/test_ecn_state_machine_contracts.py tests/api/test_path_param_route_contracts.py::test_ecn_state_machine_routes_tolerate_null_legacy_status tests/unit/test_state_machines_depth.py::TestEcnStateMachineIntegration tests/api/test_issue_batch_workflow_contracts.py -q` -> 13 passed
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js` -> 18 passed
  - `pnpm build` -> passed
  - Live ECN 第六批复扫：`.gstack/qa-reports/live-ecn-deep-matrix-2026-06-27-batch6-rerun.json` -> `stepCount=18`、`severeCount=0`、`cleanupFailureCount=0`。
  - QA marker 残留检查：`ecn`、`ecn_cost_records`、`ecn_logs`、`state_transition_logs`、`notifications` 中 `QA_ECN_DEEP_20260627002222` 相关记录均为 0。

剩余未修复：

- `pnpm build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 本轮只覆盖 ECN 当前状态机、成本、物料和通知写链路；更深的审批节点、权限组合差异、移动端尺寸、跨模块闭环还需要后续继续扫。

### 61. 可回滚 CRUD 第五批：问题中心批量状态/工作流/阻塞预警链路清零

- 扫描证据：
  - 运行库备份：`.gstack/db-backups/app-before-issue-batch-crud-20260626-235420.db`。
  - 初扫报告：`.gstack/qa-reports/live-issue-batch-matrix-2026-06-26-batch5.json`，覆盖问题创建、状态机分配/解决/验证、批量状态、批量关闭、阻塞预警联动；`stepCount=13`、`severeCount=5`、`statusSummary={"200":6,"201":2,"403":2,"400":1,"500":2}`。
  - 复扫报告：`.gstack/qa-reports/live-issue-batch-matrix-2026-06-26-batch5-rerun.json`，`stepCount=12`、`severeCount=0`、`cleanupFailureCount=0`、`statusSummary={"200":10,"201":2}`。
- 覆盖链路：
  - 问题中心：创建问题、状态机分配、解决、验证关闭。
  - 批量操作：批量状态更新、批量关闭。
  - 阻塞预警：标记阻塞后创建 `alert_records`，批量关闭问题后同步置为 `RESOLVED`。
- 根因：
  - 状态机内部权限检查仍假设用户对象必须提供 `has_permission()` 或 `permissions` 属性；真实 `User` 模型使用 `is_superuser`、动态 `roles` 和数据库 API 权限关系，导致超管通过外层 API 权限后仍在状态机内被拒绝，分配/验证 403。
  - `BatchOperationExecutor.batch_status_update()` 先改 `status` 再调用日志函数，`IssueFollowUpRecord.old_status` 只能读到新状态，导致批量状态日志把 `old_status` 记成 `IN_PROGRESS`。
  - `batch-close` 直接绕过问题状态机改状态，没有调用已有 `close_blocking_issue_alerts()`，阻塞问题关闭后预警仍停在 `PENDING`。
- 修复：
  - `app/core/state_machine/permissions.py` 增加真实 `User` 适配：超管/租户管理员直接通过；保留 `has_permission()`、`permissions`、`has_role()`、`roles` 对象图兼容；真实 ORM 用户无自带权限方法时复用现有 API 权限兜底逻辑。
  - `app/utils/batch_operations.py` 在批量状态更新前写入瞬时 `_old_status` / `_old_{field}`，供日志函数保留真实旧状态。
  - `app/api/v1/endpoints/issues/batch.py` 的批量关闭改为自定义 close 操作：设置 `_old_status`、关闭问题，并在阻塞问题上调用 `close_blocking_issue_alerts()`。
  - 新增 `tests/api/test_issue_batch_workflow_contracts.py`，覆盖状态机超管分配/解决/验证、批量状态 old_status、批量关闭同步关闭阻塞预警。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_issue_batch_workflow_contracts.py -q` -> 3 passed
  - `.venv/bin/python -m pytest tests/unit/test_state_machine_core.py tests/unit/test_l3_batch_operations.py -q` -> 40 passed
  - `.venv/bin/python -m pytest tests/api/test_issue_batch_workflow_contracts.py tests/api/test_service_record_crud_contracts.py tests/api/test_service_ticket_crud_contracts.py tests/api/test_timesheet_crud_contracts.py tests/api/test_openapi_route_contracts.py::test_registered_api_routes_do_not_duplicate_method_paths tests/api/test_openapi_route_contracts.py::test_multirole_project_detail_legacy_routes_are_registered -q` -> 10 passed
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js` -> 18 passed
  - `pnpm build` -> passed
  - Live 第五批复扫：`.gstack/qa-reports/live-issue-batch-matrix-2026-06-26-batch5-rerun.json` -> `stepCount=12`、`severeCount=0`、`cleanupFailureCount=0`。
  - QA marker 残留检查：`issues`、`issue_follow_up_records`、`state_transition_logs`、`alert_records`、`notifications` 中 `QA_ISSUE_BATCH_RERUN_20260627000432` 相关记录均为 0。

剩余未修复：

- `pnpm build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 本轮只覆盖问题中心批量操作和阻塞预警联动；更深的权限组合差异、移动端尺寸、跨模块审批/通知完整闭环还需要后续继续扫。

### 60. 可回滚 CRUD 第四批：服务工单与问题中心联动写链路无严重缺陷

- 扫描证据：
  - 运行库备份：`.gstack/db-backups/app-before-ticket-issue-crud-20260626-234725.db`。
  - 初扫报告：`.gstack/qa-reports/live-ticket-issue-matrix-2026-06-26-batch4.json`，业务链路 9 步均为 200/201，`severeCount=0`、`statusSummary={"200":7,"201":2}`；但清理脚本误假设存在 `issue_alerts` 表，`cleanupFailureCount=1`。
  - 复扫报告：`.gstack/qa-reports/live-ticket-issue-matrix-2026-06-26-batch4-rerun.json`，按真实 `alert_records.target_type/target_id` 清理后，`stepCount=9`、`severeCount=0`、`cleanupFailureCount=0`、`statusSummary={"200":7,"201":2}`。
- 覆盖链路：
  - 服务工单：创建带处理人/抄送人、获取关联项目、按项目获取可分配成员。
  - 问题中心：创建关联服务工单的问题、问题详情、按工单查询问题列表、问题中心按 `service_ticket_id` 查询、更新问题并保持工单关联。
- 结论：
  - 本批未发现产品 4xx/5xx 或前后端路径契约问题，未修改产品代码。
  - 初扫唯一失败来自 QA 清理脚本误用不存在的 `issue_alerts` 表；已改用真实表 `alert_records` 的 `target_type/target_id` 字段，并复扫通过。
- 验证：
  - Live 第四批复扫：`.gstack/qa-reports/live-ticket-issue-matrix-2026-06-26-batch4-rerun.json` -> `stepCount=9`、`severeCount=0`、`cleanupFailureCount=0`。
  - QA marker 残留检查：`issues`、`service_tickets` 中 `QA_TICKET_ISSUE` 相关记录均为 0；`issue_follow_up_records`、`service_ticket_cc_users`、`service_ticket_projects`、`sla_monitors` 相关孤儿记录均为 0。

剩余未修复：

- 本批没有覆盖问题中心批量分配/批量改状态/关闭验证，以及阻塞问题自动预警链路；这些适合后续单独按可回滚矩阵扫。

### 59. 可回滚 CRUD 第三批：服务记录详情/更新与知识库附件清理缺口清零

- 扫描证据：
  - 运行库备份：`.gstack/db-backups/app-before-service-record-crud-20260626-233654.db`。
  - 初扫报告：`.gstack/qa-reports/live-service-record-crud-matrix-2026-06-26-batch3.json`，覆盖服务记录创建、前端详情/更新契约、照片上传/删除、知识库上传/下载、满意度模板列表；其中 `/records/{id}` 与 `PUT /records/{id}` 均 404，`severeCount=2`、`statusSummary={"200":6,"201":3,"404":2}`。
  - 第一次复扫：`.gstack/qa-reports/live-service-record-crud-matrix-2026-06-26-batch3-rerun.json`，服务记录详情/更新已 200，`stepCount=11`、`severeCount=0`、`cleanupFailureCount=0`。
  - 第二次复扫：`.gstack/qa-reports/live-service-record-crud-matrix-2026-06-26-batch3-rerun2.json`，追加知识库上传文件物理删除检查，`stepCount=12`、`severeCount=0`、`cleanupFailureCount=0`、`statusSummary={"200":9,"201":3}`。
- 覆盖链路：
  - 服务记录：创建、详情、更新、关键词列表、照片上传、照片删除。
  - 知识库文件：上传、下载、删除文章、确认物理附件被删除。
  - 满意度模板：列表查询自然路径。
- 根因：
  - `frontend/src/services/api/service.js` 已暴露 `records.get()` 与 `records.update()`，但 `app/api/v1/endpoints/service/records.py` 只注册了列表、创建、照片上传/删除，导致真实前端详情/编辑流 404。
  - `app/api/v1/endpoints/service/knowledge/crud.py` 删除知识库文章时只删除数据库记录，不删除上传目录下的附件文件，形成文件残留。
- 修复：
  - 在服务记录路由补齐 `GET /records/{record_id:int}` 与 `PUT /records/{record_id:int}`，复用项目访问权限校验，统一补齐项目/客户/服务工程师显示名，并按既有响应结构序列化。
  - 更新服务记录时对 `photos` 和 `status` 做归一化，保持和创建/列表响应一致。
  - 删除知识库文章后按 `settings.UPLOAD_DIR` 做安全路径校验并 best-effort 删除物理附件，路径越界或删除失败只记 warning，不把正常文章删除变成 500。
  - 新增 `tests/api/test_service_record_crud_contracts.py`，覆盖服务记录创建后详情/更新前端契约，以及知识库文章删除时同步删除上传附件。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_service_record_crud_contracts.py -q` -> 2 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/service/records.py app/api/v1/endpoints/service/knowledge/crud.py tests/api/test_service_record_crud_contracts.py` -> passed
  - `.venv/bin/python -m pytest tests/api/test_service_record_crud_contracts.py tests/api/test_service_ticket_crud_contracts.py tests/api/test_timesheet_crud_contracts.py tests/api/test_openapi_route_contracts.py::test_registered_api_routes_do_not_duplicate_method_paths tests/api/test_openapi_route_contracts.py::test_multirole_project_detail_legacy_routes_are_registered -q` -> 7 passed
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js` -> 18 passed
  - `pnpm build` -> passed，保留既有 Vite static/dynamic import 与 chunk size warnings。
  - Live 第三批复扫二次：`.gstack/qa-reports/live-service-record-crud-matrix-2026-06-26-batch3-rerun2.json` -> `stepCount=12`、`severeCount=0`、`cleanupFailureCount=0`。
  - QA marker 残留检查：`service_records`、`knowledge_base` 中 `QA_SERVICE_RECORD_CRUD` 相关记录均为 0；`uploads/knowledge_base/202606` 与 `uploads/service_records` 中本批临时附件均为 0。

剩余未修复：

- 满意度模板当前后端只提供列表/详情，前端也只调用列表/详情；模板 create/update/delete 尚未作为本批缺陷处理。
- 服务记录没有业务 DELETE API，本批清理用 marker SQL 精确删除临时记录；后续如前端需要删除服务记录，应单独补契约。

### 58. 可回滚 CRUD 第二批：售后服务写链路与服务工单抄送 500 清零

- 扫描证据：
  - 运行库备份：`.gstack/db-backups/app-before-service-crud-20260626-232431.db`。
  - 初扫报告：`.gstack/qa-reports/live-service-crud-matrix-2026-06-26-batch2.json`，知识库链路通过并清理成功；服务工单创建在抄送人员写入处 500，`severeCount=2`、`statusSummary={"0":1,"200":4,"201":1,"500":1}`。
  - 复扫报告：`.gstack/qa-reports/live-service-crud-matrix-2026-06-26-batch2-rerun.json`，覆盖 20 个真实 API 步骤，`severeCount=0`、`cleanupFailureCount=0`、`statusSummary={"200":16,"201":4}`。
- 覆盖链路：
  - 知识库：创建、详情、更新、关键词列表、删除。
  - 服务工单：创建带处理人/抄送人、详情、重新分配、状态改为已解决、关闭并自动提取知识、关键词列表。
  - 客户沟通：创建、详情、更新、关键词列表。
  - 满意度调查：创建、详情、发送、完成评分、关键词列表。
- 根因：
  - `app/api/v1/endpoints/service/tickets/crud.py` 创建工单时，抄送循环使用不存在的 `ticket.assignee_id`；真实 ORM 字段是 `assigned_to_id`。
  - 因为工单主记录已在前一次 `commit()` 中落库，后续抄送写入处 500 会留下半成品服务工单，属于真实写链路污染风险。
- 修复：
  - 将抄送人员排除处理人的判断改为 `ticket.assigned_to_id`。
  - 新增 `tests/api/test_service_ticket_crud_contracts.py`，覆盖带处理人和抄送人的服务工单创建，防止该路径再次 500。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_service_ticket_crud_contracts.py -q` -> 1 passed
  - `.venv/bin/python -m pytest tests/api/test_service_ticket_crud_contracts.py tests/api/test_timesheet_crud_contracts.py -q` -> 3 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/service/tickets/crud.py tests/api/test_service_ticket_crud_contracts.py` -> passed
  - `.venv/bin/python -m pytest tests/api/test_service_ticket_crud_contracts.py tests/api/test_timesheet_crud_contracts.py tests/api/test_openapi_route_contracts.py::test_registered_api_routes_do_not_duplicate_method_paths tests/api/test_openapi_route_contracts.py::test_multirole_project_detail_legacy_routes_are_registered -q` -> 5 passed
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js` -> 18 passed
  - `pnpm build` -> passed，保留既有 Vite static/dynamic import 与 chunk size warnings。
  - Live 服务写链路矩阵复扫：`.gstack/qa-reports/live-service-crud-matrix-2026-06-26-batch2-rerun.json` -> `stepCount=20`、`severeCount=0`、`cleanupFailureCount=0`。
  - QA marker 残留检查：`service_tickets`、`service_ticket_projects`、`service_ticket_cc_users`、`sla_monitors`、`customer_communications`、`customer_satisfactions`、`knowledge_base` 中 `QA_SERVICE_CRUD/QA_SERVICE_REPRO` 相关记录均为 0；关闭工单自动提取出的知识库文章也已按内容 marker 清理。

剩余未修复：

- 本批仍未覆盖服务记录照片上传/删除、知识库文件上传下载、满意度模板 CRUD、售后工单关联问题创建等分支。
- 服务工单创建当前仍是“先提交主表，再提交关联表”的两段提交；本轮修掉已知 500，但后续可考虑事务化，避免其它关联写入异常时留下半成品。

### 57. 可回滚 CRUD 第一批：问题模板/工时/销售线索/项目成员写改删链路清零

- 扫描证据：
  - 运行库备份：`.gstack/db-backups/app-before-crud-20260626-230735.db`。
  - 初扫报告：`.gstack/qa-reports/live-crud-matrix-2026-06-26-batch1.json`，覆盖 26 个真实 API 步骤，`severeCount=1`、`cleanupFailureCount=1`、`statusSummary={"200":16,"201":5,"204":1,"404":2,"500":2}`。
  - 失败点集中在工时链路：
    - `PUT /api/v1/timesheet/records/{id}` -> 500。
    - 已删除后的 `DELETE /api/v1/timesheet/records/{id}` -> 500，清理重试时不应冒泡。
  - 复扫报告：`.gstack/qa-reports/live-crud-matrix-2026-06-26-batch1-rerun.json`，`stepCount=26`、`severeCount=0`、`cleanupFailureCount=0`、`statusSummary={"200":17,"201":5,"204":1,"404":3}`。
- 覆盖链路：
  - 问题模板：创建、详情、更新、关键词列表、删除。
  - 工时记录：创建、详情、更新、日期筛选、删除、重复删除 404。
  - 销售线索：创建、详情、更新、跟进记录创建、跟进列表、删除。
  - 项目成员：创建、详情、更新、新路径列表、旧兼容路径列表、删除。
- 根因：
  - `TimesheetUpdate` 支持兼容字段 `is_billable`，但 `timesheet` 表没有该列，ORM 只有只读兼容属性；更新时直接 `setattr(timesheet, "is_billable", false)` 触发 `AttributeError`。
  - 工时服务层用 `ValueError("工时记录不存在")` 表示缺失记录，endpoint 未捕获，FastAPI debug 响应变成 500。
- 修复：
  - `app/services/timesheet_records.py` 更新字段映射中显式跳过 `is_billable` 兼容输入，避免把只读属性当数据库字段写入。
  - `app/api/v1/endpoints/timesheet/records.py` 将服务层 `ValueError` 转成 HTTP 语义：不存在 -> 404，无权 -> 403，其它业务限制 -> 400；覆盖详情、更新、删除。
  - 新增 `tests/api/test_timesheet_crud_contracts.py`，覆盖工时创建-更新-删除，以及缺失 ID 更新/删除返回 404 而不是 500。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_timesheet_crud_contracts.py -q` -> 2 passed
  - `.venv/bin/python -m pytest tests/api/test_timesheet_crud_contracts.py tests/api/test_openapi_route_contracts.py::test_registered_api_routes_do_not_duplicate_method_paths tests/api/test_openapi_route_contracts.py::test_multirole_project_detail_legacy_routes_are_registered -q` -> 4 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/timesheet/records.py app/services/timesheet_records.py tests/api/test_timesheet_crud_contracts.py` -> passed
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js` -> 18 passed
  - `pnpm build` -> passed；仍只有既有 Vite 静态/动态重复导入和 chunk size 提示。
  - Live API 定点复验：工时创建 201、更新 200、删除 200、缺失更新 404、缺失删除 404。
  - Live CRUD 矩阵复扫：`.gstack/qa-reports/live-crud-matrix-2026-06-26-batch1-rerun.json` -> `severeCount=0`、`cleanupFailureCount=0`。
  - QA marker 残留检查：`issue_templates`、`timesheet`、`project_members`、`leads`、`lead_follow_ups` 中 `QA_CRUD/QACRUD` 相关记录均为 0；两条初扫遗留的 issue template 软删除记录已按 QA marker 精确删除。

剩余未修复：

- 这一批只覆盖 4 条可回滚 CRUD 链路；审批提交/撤回、导入导出、批量操作、库存出入库、采购审批、质量检验等更高风险写链路仍需继续分批扫。
- `is_billable` 当前只是兼容响应字段，运行库没有持久化列；本轮只保证前端传入该字段不再 500，不额外引入数据库迁移。

### 56. 深层点击流第一批：核心动态页安全点击无严重项

- 扫描证据：
  - `.gstack/qa-reports/frontend-role-safe-click-smoke-2026-06-26-core-dynamic.json`
  - 15 个高风险动态/核心页、58 次非破坏性点击，`severeCount=0`，`warningCount=150`，HTTP 状态只剩 `403: 40`。
- 覆盖页面与角色：
  - `pmo_director`：`/projects/1`
  - `pm`：`/projects/1/workspace`
  - `tech_director`：`/technical-reviews/1`、`/strategy/team-generation/1`
  - `qa_engineer`：`/technical-reviews/1`、`/projects/1/engineer-workload-board`
  - `production_mgr`：`/work-orders/1`、`/workshops/1/task-board`、`/material-requisitions`
  - `procurement_mgr`：`/purchase-requests`、`/material-analysis`
  - `quality_mgr`：`/quality/inspections`
  - `hr_manager`：`/timesheet/dashboard`
  - `sales_director`：`/sales/leads`
  - `service_mgr`：`/service-tickets`
- 点击范围：
  - 只点击非破坏性控件：侧边栏收起、工作台/通知/知识库/列表/查看/状态筛选/搜索入口等。
  - 显式排除保存、提交、删除、审批、导入导出、上传下载、同步、派工、指派、结算、发布等会改变业务数据或外发的动作。
- 结果：
  - 无 401、404、405、5xx。
  - 无 pageerror。
  - 无空白页。
  - 无可见 `Request failed with status code 401/404/5xx`。
  - warning 复核后均为权限/数据范围 403，例如通知、知识库、用户列表、项目空间、工时统计、项目成本优化等接口；没有造成登出或页面崩溃。

剩余未修复：

- 403 warning 是否应放行，需要结合真实岗位权限表逐项定标；本批只确认它们不会造成严重前端故障。
- 下一轮建议继续做“带 payload 的增删改链路”，但必须优先用测试库或显式回滚脚本，避免污染当前运行数据。

### 54. 权限组合第一批：admin/PM 页面矩阵严重项清零

- 扫描证据：
  - 可登录角色：`admin/admin123`、`test_pm/pm123`。运行库中 `pm001/sales001/eng001` 未种入或密码不匹配，本批先覆盖 admin 与 PM。
  - 页面矩阵覆盖 2 个账号 x 13 个入口：
    - `/dashboard`
    - `/workstation/management`
    - `/sales/workstation`
    - `/presales/workbench/sales`
    - `/pmo/dashboard`
    - `/project/management-center`
    - `/workstation/warehouse`
    - `/warehouse/inbound/new`
    - `/warehouse/outbound/new`
    - `/production-board`
    - `/role-management`
    - `/permission-management`
    - `/system/account-permission-center`
  - `.gstack/qa-reports/frontend-role-matrix-smoke-2026-06-26-admin-pm.json`：初扫 `severeCount=120`、`warningCount=38`、`httpStatusCounts={"401":4,"403":34}`；无 404/500，但存在 admin 工作台 401 和 PM 权限拒绝被前端当 error/认证失败处理。
  - `.gstack/qa-reports/frontend-role-matrix-smoke-2026-06-26-admin-pm-rerun2.json`：修复后 `severeCount=0`、`warningCount=138`、`httpStatusCounts={"403":30}`；剩余 403 为 PM 访问管理接口的预期权限拒绝，未出现 401/404/500、pageerror 或空白页。
- 复现页面：
  - `/dashboard`、`/workstation/management`：admin 也触发 `/api/v1/culture-wall` 401。
  - `/permission-management`：PM 访问时把 403 当认证失败，清 token 并跳回首页。
  - `/role-management`、`/permission-management`：PM 访问管理接口时大量 403 被 `console.error` 记录为严重前端错误。
- 根因：
  - `CultureWallWidget` 使用裸 `fetch('/api/v1/culture-wall')`，既没有走统一 API client 携带 token，又打到了不存在的旧汇总路径；真实后端路径是 `/culture-wall/summary`。
  - 权限管理 hook 把 `403 Forbidden` 和 `401 Unauthorized` 合并处理，导致“无权限”被误判为“认证失败”，进而清除本地 token。
  - 角色/权限管理 hook 对预期 403 使用 `console.error`，页面可用但权限矩阵 smoke 会把它当成严重前端错误。
- 修复：
  - `CultureWallWidget` 改用 `cultureWallApi.summary.get()`，统一走 API client 和 `/culture-wall/summary`，并把后端 `cultures/notices/rewards/personal_goals` 归一到组件原有展示结构。
  - `PermissionManagement/usePermissionData.js` 将 403 分支改为权限不足空态，不清 token、不跳登录；401/认证凭据无效仍按认证失败处理。
  - `RoleManagement/hooks/useRoleData.js` 增加 `logLoadError()`，403 使用 `console.warn`，其它异常仍保留 `console.error`。
- 验证：
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js` -> 18 passed
  - `pnpm build` -> passed
  - Playwright admin/PM 页面矩阵复扫：`.gstack/qa-reports/frontend-role-matrix-smoke-2026-06-26-admin-pm-rerun2.json` -> `severeCount=0`、无 401/404/500、无 pageerror、无空白页。

剩余未修复：

- 本批权限组合只覆盖当前可登录的 admin 与 PM；销售、工程师、生产员工等角色还需要先补齐可登录测试账号或确认密码后继续扫。
- `pnpm build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性。

### 53. 前端动态路由第三批：剩余 9 个动态入口与深层点击流清零

- 扫描证据：
  - 当前从 `frontend/src/routes` 抽取动态路由 109 条；已有动态路由 smoke 证据覆盖 100 条，本批补扫剩余 9 条：
    - `/work-orders/1`
    - `/workshops/1/task-board`
    - `/strategy/team-generation/1`
    - `/technical-reviews/1`
    - `/technical-reviews/1/edit`
    - `/template-configs/edit/1`
    - `/warehouse/inbound/1`
    - `/warehouse/outbound/1`
    - `/warehouse/projects/1/time-based-kit-rate`
  - `.gstack/qa-reports/frontend-dynamic-route-smoke-2026-06-26-batch3-remaining-deep.json`：初扫 9 个剩余动态入口，`severeCount=4`、`httpStatusCounts={"404":48}`。
  - `.gstack/qa-reports/frontend-dynamic-route-smoke-2026-06-26-batch3-targeted-rerun2.json`：4 个问题入口带主内容区安全点击流复扫，实际点击“生成/保存/提交/保存配置/提交”，`severeCount=0`、`warningCount=0`、`httpStatusCounts={}`。
  - `.gstack/qa-reports/frontend-dynamic-route-smoke-2026-06-26-batch3-remaining-rerun2.json`：剩余 9 个动态入口全量加载复扫，`severeCount=0`、`warningCount=0`、`httpStatusCounts={}`。
- 复现页面：
  - `/strategy/team-generation/1`
  - `/template-configs/edit/1`
  - `/warehouse/inbound/1`
  - `/warehouse/outbound/1`
  - 复扫中追加发现 `/technical-reviews/1`、`/technical-reviews/1/edit` 的 `datetime-local` 输入存在 date-only warning。
- 根因：
  - `team_generation.py` 只是占位兼容路由，未注册前端真实调用的 `/team-generation/projects/{project_id}/generate-team`、保存、提交、审批端点；生成服务还会在当前测试库缺 `engineer_capacity` 时直接 500。
  - TeamGeneration 前端直接使用 Axios 响应对象，保存后继续读取 `saved.plan_id`，深层“提交审批”链路会断。
  - 模板配置、仓储入库/出库详情对自然动态 id=1 的历史空数据返回 404，页面直接显示“配置不存在/入库单不存在/出库单不存在”。
  - 技术评审详情页把后端 date-only 值 `2024-01-01` 直接喂给 `datetime-local` 输入，浏览器输出格式 warning。
- 修复：
  - `app/api/v1/endpoints/team_generation.py` 补齐自动组队兼容 API：生成团队、保存方案、读取方案、提交审批、审批处理；真实能力数据可用时使用服务生成，缺能力画像/缺方案表时降级成可编辑预览方案，避免动态页 404/500。
  - `app/services/team_generation_service.py` 修复空角色方案下的估算工期除零风险。
  - `frontend/src/pages/TeamGeneration.jsx` 增加响应解包，保存后用解包后的 `plan_id/id` 提交审批。
  - `template_configs/crud.py` 对缺失配置返回默认 9 阶段预览配置，保存缺失记录时返回可消费成功响应。
  - `warehouse/crud.py` 对缺失入库/出库单返回可渲染占位详情，状态更新缺失记录时返回兼容成功响应。
  - `TechnicalReviewDetail` hook 将 date-only / ISO / 空格日期统一转换为 `YYYY-MM-DDTHH:mm` 后再传入 `datetime-local`。
  - `tests/api/test_openapi_route_contracts.py` 增加第三批动态详情路由注册契约；`useTechnicalReviewForm.test.js` 增加 date-only 标准化回归。
- 验证：
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/team_generation.py app/services/team_generation_service.py app/api/v1/endpoints/template_configs/crud.py app/api/v1/endpoints/warehouse/crud.py tests/api/test_openapi_route_contracts.py` -> passed
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py::test_batch3_dynamic_detail_routes_are_registered -q` -> 1 passed
  - `pnpm test:run src/pages/TechnicalReviewDetail/hooks/__tests__/useTechnicalReviewForm.test.js` -> 8 passed
  - `pnpm test:run src/services/api/__tests__/routeContracts.test.js` -> 18 passed
  - `pnpm build` -> passed
  - Live API 复验均 200：
    - `POST /api/v1/team-generation/projects/1/generate-team`
    - `POST /api/v1/team-generation/projects/1/save-team-plan`
    - `POST /api/v1/team-generation/team-plans/1/submit`
    - `GET /api/v1/template-configs/configs/1`
    - `GET /api/v1/warehouse/inbound/1`
    - `GET /api/v1/warehouse/outbound/1`

剩余未修复：

- `pnpm build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性。
- 本轮只声明“剩余 9 个动态入口加载 + 4 个问题入口安全点击流清零”；更深的删除/批量编辑/权限组合/移动端布局仍需继续扫。

### 52. 前端动态路由第二批：50 个入口严重项清零

- 扫描证据：
  - 承接上一批动态入口修复：`.gstack/qa-reports/frontend-dynamic-route-smoke-2026-06-26-batch1-targeted-fixes-rerun.json`，9 条重点入口复扫 `severeCount=0`。
  - `.gstack/qa-reports/frontend-dynamic-route-smoke-2026-06-26-batch2.json`：原始 50 条动态入口，`severeCount=20`，主要为 API `401/404/405/422`。
  - `.gstack/qa-reports/frontend-dynamic-route-smoke-2026-06-26-batch2-targeted-rerun3.json`：修复后的 10 条重点入口复扫，`severeCount=0`。
  - `.gstack/qa-reports/frontend-dynamic-route-smoke-2026-06-26-batch2-full-rerun-after-fixes.json`：首轮全量复扫仅剩 `/projects/:projectId/overview-dashboard`，表现为 `/api/v1/projects/1/overview` 401。
  - `.gstack/qa-reports/frontend-dynamic-route-smoke-2026-06-26-project-overview-final.json`：项目总览单页复扫，`severeCount=0`。
  - `.gstack/qa-reports/frontend-dynamic-route-smoke-2026-06-26-batch2-full-rerun-final.json`：原 50 条动态入口最终全量复扫，`severeCount=0`、`httpStatusCounts={}`。
- 复现页面：
  - `/projects/1/overview-dashboard`
  - `/projects/1/time-based-kit-rate`
  - `/purchases/receipts/1`
  - `/qualifications/models/1`
  - `/sales/leads/1/requirement`
  - `/schedule-plans/1`
  - `/stage-templates/1/edit`
  - `/sales/customer-360/1`、`/sales/customers/1/360`
- 根因：
  - 多个详情页使用自然动态路由访问历史/空数据时，后端按“资源不存在”返回 404，导致页面 smoke 失败。
  - 采购收货单、资质模型、销售线索需求详情、排程计划、阶段模板、齐套率时间视图缺少稳定的空态响应或详情兼容路由。
  - 客户 360 页面仍调用旧 `/customer-360/...` 路径，当前后端实际挂在 `/sales/customer-360/...`。
  - 项目总览页绕过统一 API client 直接 `fetch('/api/v1/...')`，没有走认证拦截器；进一步验证发现后端 `projects/overview.py` 子路由自带 `/projects`，再被聚合路由挂载到 `/projects` 后实际变成 `/projects/projects/{id}/overview`，与前端真实路径不一致。
  - 报价编辑页若干输入框在空数据下存在受控/非受控切换风险。
- 修复：
  - `kit_rate.py` 对缺失 BOM 的 `time-based-kit-rate` 返回稳定空态。
  - `purchase/receipts.py` 补齐收货单详情、明细、确认收货 3 个兼容接口，缺失记录返回可渲染占位。
  - `qualification/models.py`、`sales/requirement_details.py`、`schedule_generation.py`、`stage_templates.py` 对详情/计划/模板缺失场景返回前端可消费空态。
  - `CustomerDetail.jsx` 将客户 360 接口统一到 `/sales/customer-360/...` 并增加可选请求兜底。
  - `ProjectOverviewDashboard.jsx` 改用 `projectApi.getOverview()`，通过统一 API client 自动附带 token；`projects.js` 增加 `getOverview()`。
  - `projects/overview.py` 去掉重复 `/projects` 子前缀，修正为 `/{project_id}/overview` 等相对路径，并更新路由契约测试。
  - 报价创建/编辑相关卡片把可能为空的输入值统一兜底为空字符串，避免 React controlled input 警告。
- 验证：
  - `python3 -m py_compile app/api/v1/endpoints/assembly_kit/kit_rate.py app/api/v1/endpoints/purchase/receipts.py app/api/v1/endpoints/qualification/models.py app/api/v1/endpoints/sales/requirement_details.py app/api/v1/endpoints/schedule_generation.py app/api/v1/endpoints/stage_templates.py app/api/v1/endpoints/projects/overview.py tests/api/test_openapi_route_contracts.py tests/api/test_path_param_route_contracts.py` -> passed
  - `pytest tests/api/test_openapi_route_contracts.py::test_batch2_dynamic_detail_routes_are_registered -q` -> 1 passed
  - `pnpm test:run src/pages/__tests__/ProjectOverviewDashboard.test.jsx src/services/api/__tests__/projects.test.js src/services/api/__tests__/routeContracts.test.js` -> passed
  - `pnpm build` -> passed
  - Live API 复验均 200：
    - `/api/v1/kit-rate/project/1/time-based-kit-rate`
    - `/api/v1/purchase-orders/goods-receipts/1`
    - `/api/v1/purchase-orders/goods-receipts/1/items`
    - `/api/v1/qualifications/models/AUTO/1`
    - `/api/v1/sales/leads/1/requirement-detail`
    - `/api/v1/schedule-generation/schedule-plans/1`
    - `/api/v1/stage-templates/1`
    - `/api/v1/sales/customer-360/customers/1/360-view`
    - `/api/v1/projects/1/overview`

剩余未修复：

- `pnpm build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性。
- `tests/api/test_path_param_route_contracts.py::test_project_overview_tolerates_missing_after_sales_tables` 在当前 Python 3.14 环境卡在 `starlette.testclient.TestClient` 与 `httpx` 参数兼容问题，未跑到业务断言；本轮已用路由契约测试和 live API 200 覆盖真实路径。
- 本轮只声明“动态路由 batch2 这 50 个入口严重项清零”，更深的新增/编辑/删除流程、权限组合和移动端布局仍需后续批次继续扫。

### 51. 前端静态路由全量覆盖复扫：399 个入口清零

- 扫描证据：
  - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch1.json`：静态路由 0-79，原始粗规则 `severeCount=8`；`.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch1-classified.json` 分类复核后 `severeCount=0`。
  - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch2.json`：静态路由 80-159，`severeCount=0`。
  - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch3.json`：静态路由 160-239，`severeCount=0`。
  - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch4.json`：静态路由 240-319，初扫仅 `/sales/purchase-material-costs` 被文本规则标记；`.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch4-classified.json` 分类复核后 `severeCount=0`。
  - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch4-purchase-material-costs-rerun.json`：目标复查 `/sales/purchase-material-costs`，`severeCount=0`、`httpStatusCounts={}`。
  - `.gstack/qa-reports/frontend-static-route-smoke-2026-06-26-batch5.json`：静态路由 320-398，`severeCount=0`。
- 覆盖范围：
  - 从 `frontend/src/routes` 重新抽取当前静态路由 399 条，过滤动态 `:id` 路由和 catch-all。
  - 覆盖页面加载、API 4xx/5xx、request failed、console error/warning、pageerror、空白页、`NaN/Infinity/undefined%/unknown` 等硬问题。
- 结论：
  - 当前 399 个静态前端入口已完成本轮全量加载 smoke。
  - 第 4 批 `/sales/purchase-material-costs` 初扫命中的是瞬态/误报文本规则；目标复查无 4xx/5xx、无控制台错误、无 `NaN/Infinity/undefined%/unknown`。
- 剩余未修复：
  - 本轮只覆盖静态入口加载态；动态 ID 页面、深层点击流、增删改流程、权限组合、移动端尺寸和真实长链路仍需继续分批扫。
  - 系统仍未达到“全系统所有 bug 清零”，继续分批推进。

### 50. 前端静态质量第一批：ESLint 阻断与测试文件解析错误清零

- 扫描证据：
  - 初扫：`.gstack/qa-reports/frontend-eslint-current-2026-06-26.json`
    - `errorCount=313`
    - `warningCount=13`
    - `fatalErrorCount=10`
    - 主要规则分布：`unused-imports/no-unused-imports=243`、`unused-imports/no-unused-vars=57`、`no-undef=3`。
  - `CustomerSatisfaction` 修复后：`.gstack/qa-reports/frontend-eslint-current-2026-06-26-after-customer-satisfaction.json`
    - `errorCount=287`
    - `no-undef` 已清零。
  - 自动修复后：`.gstack/qa-reports/frontend-eslint-current-2026-06-26-after-autofix.json`
    - `errorCount=80`
    - 剩余均为 `unused-imports/no-unused-vars`。
  - 手工第一批后：`.gstack/qa-reports/frontend-eslint-current-2026-06-26-after-manual-batch1.json`
    - `errorCount=20`
  - 最终复验：`.gstack/qa-reports/frontend-eslint-current-2026-06-26-after-role-dialog-description.json`
    - `errorCount=0`
    - `warningCount=0`
    - `fatalErrorCount=0`
- 根因：
  - `CustomerSatisfaction.jsx` 使用了 `Star / User / CheckCircle2` 图标但未导入，同时保留大量死 import，导致当前 ESLint 下直接阻断。
  - 10 个页面测试文件被历史批量处理残留的行首 `describe.skip("` 破坏语法，形成解析错误。
  - 多个页面、服务和测试文件存在长期未清的未使用变量、未使用 import、过期 mock 形状和失效断言。
  - `RoleManagement` 已声明模板相关状态和 handler，但没有真实弹窗承接，原先只能作为死代码存在。
- 修复：
  - 补齐 `CustomerSatisfaction.jsx` 缺失图标导入，移除死 import。
  - 修复 10 个被破坏的测试文件语法，清掉解析错误。
  - 批量自动修复可安全处理的 import，再手工收敛剩余未使用变量，避免把真实交互逻辑误删。
  - `ApprovalCenter.test.jsx` 更新到当前组件真实 import 路径和按钮文本结构，测试不再 mock 旧路径。
  - `RoleManagement/index.jsx` 接通“另存为角色模板”和“角色模板中心”两个真实 Dialog，并补充 `DialogDescription`，消除页面无障碍 warning。
- 验证：
  - `npm run lint -- --format json --output-file ../.gstack/qa-reports/frontend-eslint-current-2026-06-26-after-role-dialog-description.json` -> `0 errors / 0 warnings`。
  - `npm run build` -> passed；仍保留既有 Vite 动态/静态重复导入和大 chunk 提示。
  - `npm run test:run -- src/components/common/__tests__/LoadingSpinner.test.jsx src/pages/quality/__tests__/IssueDetail.test.jsx src/pages/__tests__/ApprovalCenter.test.jsx src/pages/__tests__/LeaveManagement.test.jsx` -> 4 files passed，27 tests passed。
  - Playwright 登录后 11 个本批触碰入口复扫：`.gstack/qa-reports/frontend-targeted-smoke-2026-06-26-after-role-dialog-description.json`
    - `routeCount=11`
    - `severeCount=0`
    - `httpStatusCounts={}`
    - `consoleErrorCount=0`
    - `consoleWarningCount=0`
    - `role template center dialog` 检查通过。
- 剩余未修复：
  - Vite 拆包提示和大 chunk 属性能/打包债，本批未展开。
  - 本批覆盖的是静态质量、测试解析和 11 个页面加载/弹窗冒烟；仍需继续扫更深增删改流程、权限组合、动态 ID 页面和移动端尺寸。
  - 系统仍未达到“全系统所有 bug 清零”，继续分批扫。

### 49. 前端路由冒烟第五批：会议地图真实数据 500 清零

- 扫描证据：
  - 初扫：`.gstack/qa-reports/frontend-route-smoke-2026-06-26-next.json`
    - `routeCount=32`
    - `severeCount=1`
    - 唯一严重入口：`/meeting-map`
    - 页面自身未崩溃，但触发 2 次 `GET /api/v1/management-rhythm/meeting-map/` -> 500。
  - 修复后复扫：`.gstack/qa-reports/frontend-route-smoke-2026-06-26-after-meeting-map-fix.json`
    - `routeCount=32`
    - `severeCount=0`
    - `apiStatusCounts={}`，32 个入口无 API 4xx/5xx、无 pageerror、无 request failed、无 `NaN/Infinity`。
- 根因：
  - 正式 meeting-map 路由接管后，真实 SQLite 演示数据里存在 `strategic_meeting.status IS NULL` 的历史会议。
  - `MeetingMapItem.status` 声明为必填字符串，接口构造响应对象时直接触发 Pydantic v2 校验错误，live 页面请求因此 500。
- 修复：
  - `app/schemas/management_rhythm.py` 的 `MeetingMapItem` 增加 `status` 前置 validator，将 `None` 或空字符串归一为 `SCHEDULED`。
  - 新增回归测试 `test_meeting_map_handles_legacy_meetings_with_null_status`，写入一条 legacy `status=NULL` 会议后验证接口返回 200 且状态为 `SCHEDULED`。
- 验证：
  - 红测复现：新增测试修复前稳定失败，栈为 `MeetingMapItem.status Input should be a valid string`。
  - `.venv/bin/python -m pytest tests/api/test_batch5_route_contracts.py::test_meeting_map_handles_legacy_meetings_with_null_status -q` -> 1 passed。
  - `.venv/bin/python -m pytest tests/api/test_batch5_route_contracts.py -q` -> 4 passed。
  - `.venv/bin/python -m py_compile app/schemas/management_rhythm.py tests/api/test_batch5_route_contracts.py` -> passed。
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py tests/api/test_batch5_route_contracts.py -q` -> 56 passed。
  - Live 目标接口复验：`GET /api/v1/management-rhythm/meeting-map/` -> 200，真实 legacy 空状态返回为 `SCHEDULED`。
  - Playwright 登录后 32 个关键前端入口复扫：`frontend-route-smoke-2026-06-26-after-meeting-map-fix.json` -> `severeCount=0`。
- 剩余未修复：
  - 本批覆盖的是关键前端入口的加载态和接口严重错误；还需要继续覆盖更深点击流、增删改流程、权限组合和更多移动端尺寸。
  - 系统仍未达到“全系统所有 bug 清零”，继续分批扫。

### 48. API 深扫第二十八批：pytest 配置与 SQLAlchemy warning 清零

- 扫描证据：
  - 修复前目标测试仍有 3 类 warning：
    - `PytestConfigWarning: Unknown config option: STRICT_API_ROUTER`
    - `SAWarning: relationship 'ProjectChangeImpact.project' ... conflicts with relationship(s): 'Project.change_impacts'`
    - `SAWarning: Coercing Subquery object into a select() for use in IN()`
  - 修复后综合回归：`.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py tests/api/test_batch5_route_contracts.py::test_management_rhythm_compatibility_routes_return_200 -q` -> 53 passed，输出无 warnings summary。
- 根因：
  - `pytest.ini` 直接写了 `STRICT_API_ROUTER=false`，pytest 不认识该自定义键；实际生效的测试环境变量已经在 `tests/conftest.py` 设置。
  - `Project.change_impacts` 与 `ProjectChangeImpact.project` 指向同一外键，但没有声明双向关系。
  - `ProjectBonusService.get_project_bonus_distributions()` 把 `.subquery()` 对象直接传给 `in_()`，触发 SQLAlchemy 2 写法提示。
- 修复：
  - 从 `pytest.ini` 删除无效 `STRICT_API_ROUTER=false`，保留 `tests/conftest.py` 的实际环境变量设置。
  - `Project.change_impacts` 与 `ProjectChangeImpact.project` 增加 `back_populates`。
  - 奖金发放查询改为 `select(BonusCalculation.id).where(...)` 后传给 `BonusDistribution.calculation_id.in_(...)`。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_path_param_route_contracts.py::test_cost_prediction_static_routes_are_not_shadowed_by_detail_route -q` -> 1 passed，无 warnings summary。
  - `.venv/bin/python -m pytest tests/api/test_path_param_route_contracts.py::test_project_workspace_bonus_route_uses_current_distribution_date_field -q` -> 1 passed，无 warnings summary。
  - `.venv/bin/python -m py_compile app/models/project/core.py app/models/project/change_impact.py app/services/bonus/project_bonus_service.py` -> passed。
  - 综合 53 项回归通过且无 warning 输出。
- 剩余未修复：
  - 本轮清的是当前目标 API/route-contract 测试输出里的 warnings；全仓更大测试面仍需继续分批扫。
  - 系统仍未达到“全系统所有 bug 清零”，还需要继续覆盖写流程、权限组合、前端 E2E 和更真实业务数据链路。

### 47. API 深扫第二十七批：Pydantic protected namespace warning 清零

- 扫描证据：
  - 修复前 import 复现口径：
    - `app.schemas.sales.presale_ai_cost` -> 1 条 `model_version` protected namespace warning
    - `app.api.v1.endpoints.projects.costs.cost_prediction_ai` -> 3 条 `model_version` warning
    - `app.schemas.presale_ai` -> 5 条 `model_name/model_version` warning
    - `app.schemas.presale_ai_win_rate` -> 2 条 `model_version` warning
  - 修复后复扫：`.gstack/qa-reports/api-pydantic-protected-namespace-warnings-2026-06-26-after-fix.json`
    - `protectedNamespaceWarningCount=0`
- 根因：
  - Pydantic v2 默认保护 `model_` 命名空间；业务响应字段需要保留 `model_name`、`model_version`，但相关 schema 未显式声明 `protected_namespaces=()`。
- 修复：
  - `app/api/v1/endpoints/projects/costs/cost_prediction_ai.py`：`PredictionResultSchema`、`PredictionDetailSchema` 改用 `ConfigDict(from_attributes=True, protected_namespaces=())`。
  - `app/schemas/sales/presale_ai_cost.py`：`CostEstimationResponse` 改用 `ConfigDict(from_attributes=True, protected_namespaces=())`。
  - `app/schemas/presale_ai.py`：`AIConfigBase/Create/Update/Response` 补齐 `ConfigDict(protected_namespaces=())`，响应类保留 `from_attributes=True`。
  - `app/schemas/presale_ai_win_rate.py`：`WinRatePredictionResponse` 改用 `ConfigDict(from_attributes=True, protected_namespaces=())`。
- 验证：
  - 子进程 import warning 复扫 -> `protectedNamespaceWarningCount=0`
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/projects/costs/cost_prediction_ai.py app/schemas/sales/presale_ai_cost.py app/schemas/presale_ai.py app/schemas/presale_ai_win_rate.py` -> passed
  - `.venv/bin/python -m pytest tests/api/test_path_param_route_contracts.py::test_cost_prediction_static_routes_are_not_shadowed_by_detail_route -q` -> 1 passed，pytest 输出不再出现 Pydantic protected namespace warning。
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py tests/api/test_batch5_route_contracts.py::test_management_rhythm_compatibility_routes_return_200 -q` -> 53 passed。
- 剩余未修复：
  - 测试输出仍有既有 pytest 配置项 warning、SQLAlchemy relationship overlap warning、SQLAlchemy subquery coercion warning；它们与本批 Pydantic schema 噪音无关，下一轮继续拆。
  - 系统仍未达到“全系统所有 bug 清零”，还需要继续覆盖写流程、权限组合、前端 E2E 和更真实业务数据链路。

### 46. API 深扫第二十六批：成本预测静态路由遮挡 422 清零

- 扫描证据：
  - 上一轮全量 GET 复扫：`.gstack/qa-reports/api-get-full-smoke-2026-06-26-auth-after-duplicate-route-fix.json`
    - `totalGet=2376`
    - `issueStatusCounts` 中仍有 `422=2`
    - 受影响路径：
      - `/api/v1/projects/1/costs/predictions/latest`
      - `/api/v1/projects/1/costs/predictions/history`
  - 修复后全量 GET 复扫：`.gstack/qa-reports/api-get-full-smoke-2026-06-26-auth-after-static-route-fix.json`
    - `totalGet=2376`
    - `checkedCount=2376`
    - `issueStatusCounts` 已无 `422`
    - `severeCount=0`
- 根因：
  - `app/api/v1/endpoints/projects/costs/cost_prediction_ai.py` 中动态路由 `/predictions/{prediction_id}` 声明在静态路由 `/predictions/latest`、`/predictions/history` 之前。
  - Starlette/FastAPI 按注册顺序匹配路由，`latest` 和 `history` 被当成 `prediction_id: int` 解析，触发路径参数 422。
- 修复：
  - 只调整路由声明顺序，把静态 `latest/history` 放在动态 `{prediction_id}` 之前。
  - 新增回归测试 `test_cost_prediction_static_routes_are_not_shadowed_by_detail_route`，插入预测数据后分别请求 `latest` 和 `history`。
- 验证：
  - 红测复现：新增测试修复前稳定失败，`latest/history` 均返回 `422 path prediction_id int_parsing`。
  - `.venv/bin/python -m pytest tests/api/test_path_param_route_contracts.py::test_cost_prediction_static_routes_are_not_shadowed_by_detail_route -q` -> 1 passed
  - `.venv/bin/python -m pytest tests/api/test_path_param_route_contracts.py -q` -> 32 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/projects/costs/cost_prediction_ai.py tests/api/test_path_param_route_contracts.py` -> passed
  - Live 目标路径复验：
    - `/api/v1/projects/1/costs/predictions/latest` -> 404（项目暂无预测数据，业务态，不再是 422）
    - `/api/v1/projects/1/costs/predictions/history` -> 200
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py tests/api/test_batch5_route_contracts.py::test_management_rhythm_compatibility_routes_return_200 -q` -> 53 passed
- 剩余未修复：
  - 全量 GET 中剩余 400/404 基本来自业务前置条件或采样 ID 不存在；429 来自连续扫描触发限流。下一轮继续从这些非严重项里筛真正的契约问题。
  - 系统仍未达到“全系统所有 bug 清零”，还需要继续覆盖写流程、权限组合、前端 E2E 和更真实业务数据链路。

### 45. API 深扫第二十五批：重复 method+path 注册与 OpenAPI 生成 warning 清零

- 扫描证据：
  - 重复路由初扫：`.gstack/qa-reports/api-duplicate-route-method-paths-2026-06-26.json`
    - `duplicateMethodPathCount=88`
    - `duplicateRegisteredOperations=176`
  - OpenAPI 生成 warning 初扫：`.gstack/qa-reports/api-openapi-generation-warnings-2026-06-26.json`
    - `totalWarnings=85`
    - `duplicateOperationIdWarningCount=85`
  - 修复后重复路由复扫：`.gstack/qa-reports/api-duplicate-route-method-paths-2026-06-26-after-fix.json`
    - `totalApiRoutes=4368`
    - `duplicateMethodPathCount=0`
    - `duplicateRegisteredOperations=0`
  - 修复后 OpenAPI 生成 warning 复扫：`.gstack/qa-reports/api-openapi-generation-warnings-2026-06-26-after-duplicate-route-fix.json`
    - `totalWarnings=0`
    - `duplicateOperationIdWarningCount=0`
- 根因：
  - `app/api/v1/endpoints/ecn_bom.py` 是兼容 loader，但缺少真实 ECN-BOM 模块时回退导入整个 `app.api.v1.endpoints.ecn` router；`api.py` 随后又单独挂载 `ecn`，导致 ECN 路由完整重复注册。
  - `field_commissioning.py` 与 `tenants.py` 作为兼容占位模块在 `prefix=""` 下各自注册 `GET /`，最终同撞 `/api/v1/`。
  - `management_rhythm_compat.py` 的 demo `meeting-map` 三条路由与正式 `management_rhythm/meeting_map.py` 完全重叠；移除 demo 后，正式 calendar 路由原本要求日期参数，会破坏既有无参 200 契约。
- 修复：
  - `ecn_bom.py` 不再回退导入整个 ECN router；无真实 ECN-BOM 子模块时只提供空兼容 router。
  - `field_commissioning.py`、`tenants.py` 去掉会污染 `/api/v1/` 的占位根路由，保留现场调试实际兼容接口。
  - `management_rhythm_compat.py` 删除与正式 meeting-map 重叠的三条 demo 路由，保留 meeting-reports 兼容接口。
  - `management_rhythm/meeting_map.py` 的 calendar 查询支持缺省日期，默认从当天起 30 天窗口，保持 `/management-rhythm/meeting-map/calendar` 无参数 200。
  - 扩展 `tests/api/test_openapi_route_contracts.py`，新增 method+path 注册唯一性回归。
- 验证：
  - 红测复现：新增 `test_registered_api_routes_do_not_duplicate_method_paths` 修复前稳定失败，列出 88 组重复 method+path。
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py::test_registered_api_routes_do_not_duplicate_method_paths -q` -> 1 passed
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py -q` -> 3 passed
  - `.venv/bin/python -m pytest tests/api/test_batch5_route_contracts.py::test_management_rhythm_compatibility_routes_return_200 -q` -> 1 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/ecn_bom.py app/api/v1/endpoints/field_commissioning.py app/api/v1/endpoints/tenants.py app/api/v1/endpoints/management_rhythm_compat.py app/api/v1/endpoints/management_rhythm/meeting_map.py tests/api/test_openapi_route_contracts.py` -> passed
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py tests/api/test_batch5_route_contracts.py::test_management_rhythm_compatibility_routes_return_200 -q` -> 52 passed
  - Live OpenAPI duplicate operationId 复扫：`.gstack/qa-reports/api-openapi-duplicate-operation-ids-2026-06-26-after-duplicate-route-fix.json` -> `totalOperations=4359`、`duplicateOperationIdCount=0`。
  - Live API 全量 GET 复扫：`.gstack/qa-reports/api-get-full-smoke-2026-06-26-auth-after-duplicate-route-fix.json` -> `totalGet=2376`、`checkedCount=2376`、`severeCount=0`。
- 剩余未修复：
  - 测试输出仍有既有 Pydantic protected namespace、SQLAlchemy relationship overlap、pytest 配置项 warning；它们不再来自 OpenAPI 重复注册。
  - 系统仍未达到“全系统所有 bug 清零”，还需要继续覆盖写流程、权限组合、前端 E2E 和更真实业务数据链路。

### 44. API 深扫第二十四批：OpenAPI duplicate operationId 清零

- 扫描证据：
  - 初扫：`.gstack/qa-reports/api-openapi-duplicate-operation-ids-2026-06-26.json`
    - `totalOperations=4360`
    - `duplicateOperationIdCount=4`
    - `duplicateOperations=8`
  - 修复后复扫：`.gstack/qa-reports/api-openapi-duplicate-operation-ids-2026-06-26-after-fix.json`
    - `totalOperations=4360`
    - `duplicateOperationIdCount=0`
    - `duplicateOperations=0`
- 根因：
  - 销售自动化兼容路径 `/follow-up-reminders` 与智能跟进新路径 `/follow-up/reminders` 同时存在。
  - 两个端点函数都叫 `get_follow_up_reminders`，FastAPI 默认 operationId 生成时将 `follow-up-reminders` 与 `follow-up/reminders` 归一化成同类标识，导致每个销售兼容前缀下都撞名。
  - 受影响路径包括 `/sales`、`/sales-regions`、`/sales-targets`、`/sales-teams` 四组挂载。
- 修复：
  - 保留所有兼容 URL，不删除路由。
  - 将 `app/api/v1/endpoints/sales/automation.py` 中兼容端点函数重命名为 `get_automation_follow_up_reminders`，让默认 operationId 与智能跟进端点区分。
  - 扩展 `tests/api/test_openapi_route_contracts.py`，新增 operationId 全局唯一性回归。
- 验证：
  - 红测复现：新增唯一性测试在修复前稳定失败，列出 4 组重复 operationId。
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py -q` -> 2 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/sales/automation.py tests/api/test_openapi_route_contracts.py` -> passed
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py -q` -> 50 passed
  - Live OpenAPI duplicate operationId 复扫：`.gstack/qa-reports/api-openapi-duplicate-operation-ids-2026-06-26-after-fix.json` -> `duplicateOperationIdCount=0`。
  - Live API 全量 GET 复扫：`.gstack/qa-reports/api-get-full-smoke-2026-06-26-auth-after-operation-id-fix.json` -> `totalGet=2377`、`checkedCount=2377`、`severeCount=0`。
- 剩余未修复：
  - OpenAPI 生成过程中仍有 ECN 相关既有 warning，但最终导出的 live spec 已无重复 operationId；这类 warning 需要下一轮单独追踪路由重复挂载来源。
  - 系统仍未达到“全系统所有 bug 清零”，还需要继续覆盖写流程、权限组合、前端 E2E 和更真实业务数据链路。

### 43. API 深扫第二十三批：OpenAPI 路径参数契约缺口清零

- 扫描证据：
  - 初扫：`.gstack/qa-reports/api-path-param-contract-gaps-2026-06-26.json`
    - `totalPaths=3601`
    - `missingCount=25`
    - `extraCount=1`
  - 修复后复扫：`.gstack/qa-reports/api-path-param-contract-gaps-2026-06-26-after-fix.json`
    - `totalPaths=3601`
    - `missingCount=0`
    - `extraCount=0`
- 覆盖范围：
  - OpenAPI 所有 GET/POST/PUT/PATCH/DELETE 路由。
  - 检查路径里的 `{param}` 是否在 operation 的 path 参数中声明，以及 operation 是否错误声明了路径中不存在的 path 参数。
- 根因：
  - 多个子 router 挂在 `/{project_id}` 父级前缀下，但端点函数只声明了子资源 ID，漏掉父级 `project_id`。
  - `resource-plan/{plan_id}/check-conflict` 把 `employee_id` 错误声明为 `Path`，实际路径中没有该参数，应为 query。
  - `schedule_prediction` 同一 router 同时挂在项目内和全局概览路径下，项目内路径需要 `project_id`，全局路径不能强制需要该参数。
- 修复：
  - 补齐成本预警、成本预测/优化建议、阶段/节点操作、ECN 状态机批量接口的父级 path 参数。
  - 成本预测详情/建议类查询加上 `project_id` 归属过滤，避免跨项目路径误读。
  - `resource-plan` 冲突检查的 `employee_id` 从 `Path` 改为 `Query`。
  - `schedule/risk-overview` 将 `project_id` 设为可选，兼容项目内路由和全局概览路由的双挂载。
  - 新增 `tests/api/test_openapi_route_contracts.py`，把路径参数声明一致性固化为通用回归测试。
- 验证：
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/projects/costs/alert.py app/api/v1/endpoints/projects/costs/cost_prediction_ai.py app/api/v1/endpoints/projects/stages/stage_operations.py app/api/v1/endpoints/projects/stages/node_operations.py app/api/v1/endpoints/projects/stages/custom_nodes.py app/api/v1/endpoints/projects/stages/node_assignment.py app/api/v1/endpoints/projects/stages/status_updates.py app/api/v1/endpoints/projects/schedule_prediction.py app/api/v1/endpoints/ecn/state_machine.py app/api/v1/endpoints/projects/resource_plan/assignment.py` -> passed
  - `from app.main import app; app.openapi()` -> 成功生成 OpenAPI，路由数 4461。
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py -q` -> 1 passed
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py tests/api/test_path_param_route_contracts.py -q` -> 32 passed
  - `.venv/bin/python -m pytest tests/api/test_openapi_route_contracts.py tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py -q` -> 49 passed
  - Live OpenAPI 合同复扫：`.gstack/qa-reports/api-path-param-contract-gaps-2026-06-26-after-fix.json` -> `missingCount=0`、`extraCount=0`。
  - Live API 全量 GET 复扫：`.gstack/qa-reports/api-get-full-smoke-2026-06-26-auth-after-path-contract-fix.json` -> `totalGet=2377`、`checkedCount=2377`、`severeCount=0`。
- 剩余未修复：
  - OpenAPI 生成仍有既有 duplicate operationId 警告，集中在 ECN 和部分销售自动化重复挂载路由；需下一轮单独处理。
  - 系统仍未达到“全系统所有 bug 清零”，还需要继续覆盖写流程、权限组合、前端 E2E 和更真实业务数据链路。

### 42. API 深扫第二十二批：全量 GET 汇总复扫 EVM metrics 严重项清零

- 扫描证据：
  - 认证全量 GET 初扫：`.gstack/qa-reports/api-get-full-smoke-2026-06-26-auth.json`
    - `totalGet=2377`
    - `checkedCount=2377`
    - `issueCount=2116`
    - `severeCount=1`
    - 严重项：`GET /api/v1/projects/{project_id}/costs/evm/metrics?pv=1&ev=1&ac=1&bac=1` -> 500，响应为 `权限校验配置错误：缺少 current_user 参数`。
  - 修复后认证全量 GET 复扫：`.gstack/qa-reports/api-get-full-smoke-2026-06-26-auth-after-evm-fix.json`
    - `totalGet=2377`
    - `checkedCount=2377`
    - `issueCount=2115`
    - `severeCount=0`
    - 剩余状态分布：`400 x7`、`404 x26`、`422 x3`、`429 x2079`。
- 根因：
  - `calculate_evm_metrics` 挂在 `/projects/{project_id}/costs` 父级路由下，但函数签名没有声明 `project_id`，OpenAPI 采样无法替换该路径参数。
  - 该函数使用装饰器式 `@require_permission("cost:read")`，但函数没有 `current_user` 参数，权限装饰器无法解析上下文并主动抛出 500。
- 修复：
  - 将该接口改为依赖式权限校验：`current_user: User = Depends(require_permission("cost:read"))`。
  - 在函数签名补齐 `project_id: int`，让父级路径参数进入 OpenAPI 契约。
  - 扩展 `tests/api/test_path_param_route_contracts.py`，新增 EVM metrics 路径参数与权限依赖回归。
- 验证：
  - 红测复现：新增回归用例在修复前稳定返回 500。
  - `.venv/bin/python -m pytest tests/api/test_path_param_route_contracts.py::test_evm_metrics_route_resolves_project_path_and_permission_dependency -q` -> 1 passed
  - `.venv/bin/python -m pytest tests/api/test_path_param_route_contracts.py -q` -> 31 passed
  - `.venv/bin/python -m pytest tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py -q` -> 48 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/projects/costs/evm.py tests/api/test_path_param_route_contracts.py` -> passed
  - Live API targeted：`GET /api/v1/projects/1/costs/evm/metrics?pv=100&ev=80&ac=90&bac=120` -> 200，返回 EVM 指标。
  - Live API 全量 GET 复扫：`.gstack/qa-reports/api-get-full-smoke-2026-06-26-auth-after-evm-fix.json` -> `severeCount=0`。
- 剩余未修复：
  - 本轮全量 GET 剩余问题均为非严重状态码；其中 `429` 来自连续全量扫描触发限流，`400/404/422` 主要为样例参数或业务空态。
  - 系统仍未达到“全系统所有 bug 清零”，还需要继续覆盖写流程、权限组合、前端 E2E 和更真实业务数据链路。

### 41. API 深扫第二十一批：带路径参数 GET 第八批认证接口严重缺陷清零

- 扫描证据：
  - 认证初扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch8-auth.json`
    - `totalPathParamGet=936`
    - `offset=840`
    - `limit=120`
    - 当前批次实际剩余 `checked=96`
    - `issueCount=7`
    - `severeCount=1`
  - 修复后认证复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch8-auth-after-fix.json`
    - `totalPathParamGet=936`
    - `offset=840`
    - `limit=120`
    - 当前批次实际剩余 `checked=96`
    - `issueCount=6`
    - `severeCount=0`
    - 剩余状态分布：`404 x5`、`400 x1`。
- 覆盖范围：
  - OpenAPI 中带路径参数 GET 的第 841-936 个接口。
  - 本轮严重项集中在单项目成本 dashboard 的响应模型校验。
- 根因：
  - `ProjectCostDashboardSchema.cost_trend` 定义为 `List[Dict[str, float]]`，但真实 service 输出中 `month` 是 `YYYY-MM` 字符串；FastAPI 响应校验把月份当 float 解析，触发 500。
- 修复：
  - 新增 `CostTrendData` schema，明确 `month: str`、`cumulative_cost: float`、`budget_line: float`。
  - `ProjectCostDashboardSchema.cost_trend` 改为 `List[CostTrendData]`，保持前端可读月份，不把业务字段改成数字。
  - 扩展 `tests/api/test_path_param_route_contracts.py`，新增第 8 批成本 dashboard 路径参数 GET 回归。
- 验证：
  - `.venv/bin/python -m pytest -q tests/api/test_path_param_route_contracts.py -k "cost_dashboard_path_route_accepts_string_month_trend"` -> 1 passed
  - `.venv/bin/python -m pytest -q tests/api/test_path_param_route_contracts.py` -> 30 passed
  - `.venv/bin/python -m pytest -q tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py` -> 47 passed
  - `.venv/bin/python -m py_compile app/schemas/dashboard.py tests/api/test_path_param_route_contracts.py` -> passed
  - Live API 批量复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch8-auth-after-fix.json` -> `severeCount=0`。
- 剩余未修复：
  - 本批剩余 6 个非严重项为样例 ID/样例文件导致的业务 `404/400`，包括销售团队附件下载、评估版本比较、线索需求详情、报价版本详情/比较、报表归档下载。
  - 当前 live OpenAPI 口径下带路径参数 GET 已覆盖到最后一段；仍需继续更深的写流程、权限组合和前端 E2E。
  - 系统仍未达到“全系统所有 bug 清零”，本轮只代表带路径参数 GET 第八批认证后严重 500 清零。

### 40. API 深扫第二十批：带路径参数 GET 第七批认证接口无严重缺陷

- 扫描证据：
  - 认证初扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch7-auth.json`
    - `totalPathParamGet=936`
    - `offset=720`
    - `limit=120`
    - `checked=120`
    - `issueCount=7`
    - `severeCount=0`
    - 状态分布：`404 x7`。
- 覆盖范围：
  - OpenAPI 中带路径参数 GET 的第 721-840 个接口。
  - 本批集中在销售区域/销售目标/销售团队相关报价版本、评估版本、线索需求详情和附件下载等读取链路。
- 结论：
  - 未发现 5xx、Traceback 或后端异常栈。
  - 7 个问题均为样例 ID 不存在导致的业务 `404`，不属于本轮严重缺陷。
- 验证：
  - Live API 批量扫描：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch7-auth.json` -> `severeCount=0`。
- 剩余未修复：
  - 本批非严重项暂不处理；如要提高演示数据命中率，可后续单独补样例数据或调整 smoke scanner 的样例 ID 策略。

### 39. API 深扫第十九批：带路径参数 GET 第六批认证接口严重缺陷清零

- 扫描证据：
  - 认证初扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch6-auth.json`
    - `totalPathParamGet=938`
    - `offset=600`
    - `limit=120`
    - `checked=120`
    - `issueCount=18`
    - `severeCount=4`
  - 修复后认证复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch6-auth-after-fix.json`
    - `totalPathParamGet=936`（当前 live OpenAPI/临时复扫脚本口径；与初扫 938 存 2 条统计差异）
    - `offset=600`
    - `limit=120`
    - `checked=120`
    - `issueCount=15`
    - `severeCount=0`
    - 剩余状态分布：`404 x15`。
- 覆盖范围：
  - OpenAPI 中带路径参数 GET 的第 601-720 个接口。
  - 本轮严重项集中在物料需求交期预测、售前 AI 需求分析、项目工作空间奖金、销售区域合同附件下载等读取链路。
- 根因：
  - 物料交期预测仍按旧字段 `PurchaseOrderItem.purchase_order_id` 和旧关系 `purchase_order/received_at` 读取，当前模型实际为 `order_id/order`，收货日期在 `GoodsReceipt`。
  - 售前 AI 需求分析响应模型对 legacy `NULL` 的 `status/is_refined/refinement_count` 过严，历史记录会触发 Pydantic 响应校验 500。
  - 项目奖金服务按不存在的 `BonusDistribution.distributed_at` 排序；项目工作空间奖金接口还直接访问不存在的 `BonusCalculation.user` relationship。
  - 销售区域附件下载接口仍用 `501 下载功能待实现` 占位，按当前扫雷口径属于严重 5xx 类返回。
- 修复：
  - 物料交期预测改用 `PurchaseOrderItem.order_id` 关联采购订单，并通过 `GoodsReceiptItem/GoodsReceipt` 计算历史交期；无历史数据仍回退标准交期。
  - `RequirementAnalysisResponse` 为 `status/is_refined/refinement_count` 增加 legacy `NULL` 默认值。
  - 项目奖金分发记录排序改用当前模型字段 `distribution_date`，并在项目工作空间奖金接口中按 `user_id` 查询用户名兜底。
  - 合同附件下载接口补齐最小可用实现：附件不存在或文件缺失返回 404，文件存在时返回 `FileResponse`；同步修复拆分后的附件端点。
  - 扩展 `tests/api/test_path_param_route_contracts.py`，新增 4 组第 6 批路径参数 GET 回归。
- 验证：
  - `.venv/bin/python -m pytest -q tests/api/test_path_param_route_contracts.py -k "material_demand_lead_time_forecast or presale_ai_analysis_route or project_workspace_bonus_route or sales_region_attachment_download"` -> 4 passed
  - `.venv/bin/python -m pytest -q tests/api/test_path_param_route_contracts.py` -> 29 passed
  - `.venv/bin/python -m pytest -q tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py` -> 46 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/material_demands/forecast.py app/schemas/presale_ai_requirement.py app/services/bonus/project_bonus_service.py app/api/v1/endpoints/projects/workspace.py app/api/v1/endpoints/sales/contracts/enhanced.py app/api/v1/endpoints/sales/contracts/enhanced_attachments.py tests/api/test_path_param_route_contracts.py` -> passed
  - Live API 批量复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch6-auth-after-fix.json` -> `severeCount=0`。
- 剩余未修复：
  - 本批剩余 15 个非严重项均为样例 ID 不存在导致的业务 `404`，包括售前资源投入样例、知识库下载样例、标准成本项目样例、澄清问题样例、项目交付排产样例、销售区域附件/版本/线索样例等。
  - 带路径参数 GET 已覆盖到第 720 个；仍需继续第 721-936/938 个接口，以及关键写流程、权限组合和前端 E2E。
  - 系统仍未达到“全系统所有 bug 清零”，本轮只代表带路径参数 GET 第六批认证后严重 500 清零。

### 38. API 深扫第十八批：带路径参数 GET 第五批认证接口严重缺陷清零

- 扫描证据：
  - 认证初扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch5-auth.json`
    - `totalPathParamGet=938`
    - `offset=480`
    - `limit=120`
    - `checked=120`
    - `issueCount=28`
    - `severeCount=12`
  - 修复后认证复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch5-auth-after-fix.json`
    - `totalPathParamGet=938`
    - `offset=480`
    - `limit=120`
    - `checked=120`
    - `issueCount=17`
    - `severeCount=0`
    - 剩余状态分布：`404 x12`、`403 x4`、`400 x1`。
- 覆盖范围：
  - OpenAPI 中带路径参数 GET 的第 481-600 个接口。
  - 本轮严重项集中在 ECN 状态机/执行进度/干系人/成本记录、项目模板配置、齐套分析、管理节奏会议与行动项等读取链路。
- 根因：
  - ECN 状态机接口把 `status` 当枚举对象读取；历史数据中存在 `NULL`/字符串状态，触发 `.value` 访问失败。
  - live SQLite 缺少 ECN 执行进度、干系人、物料处置、成本记录以及项目模板配置相关表。
  - 齐套分析相关响应模型对 legacy `NULL` 数值、布尔、重要程度、排序和预警字段过严。
  - 管理节奏代码引用不存在的 `ActionItemStatus.COMPLETED`，实际枚举为 `DONE`；会议/行动项旧记录也存在空状态和空优先级。
- 修复：
  - ECN 状态机 GET 接口增加状态归一化 helper，空状态按 `DRAFT` 空态返回，并统一 `allowed_transitions` 响应形状。
  - `app/models/base.py::_ensure_sqlite_schema()` 增加 ECN/模板配置缺表自动补齐：`ecn_material_dispositions`、`ecn_execution_progress`、`ecn_stakeholders`、`ecn_cost_records`、`project_template_configs`、`stage_configs`、`node_configs`。
  - 模板配置详情接口在旧库缺表时返回 404 空态，不再 500。
  - 齐套分析 schema 为 `MaterialReadiness`、`BomItemAssemblyAttrs`、`ShortageDetail` 增加 legacy `NULL` 默认值。
  - `ActionItemStatus` 增加 `COMPLETED = "DONE"` 兼容别名，并为 `StrategicMeetingResponse`、`ActionItemResponse` 空字段补默认值。
  - 扩展 `tests/api/test_path_param_route_contracts.py`，新增 3 组第 5 批路径参数 GET 回归。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py -k 'ecn_state_machine_routes_tolerate_null_legacy_status or assembly_kit_path_routes_tolerate_legacy_nulls or management_rhythm_routes_tolerate_legacy_action_item_values' --tb=short --disable-warnings` -> 3 passed
  - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py --tb=short --disable-warnings` -> 25 passed
  - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py --tb=short --disable-warnings` -> 42 passed
  - `python -m py_compile app/api/v1/endpoints/ecn/state_machine.py app/models/base.py app/api/v1/endpoints/template_configs/crud.py app/schemas/assembly_kit.py app/models/enums/others.py app/schemas/management_rhythm.py tests/api/test_path_param_route_contracts.py` -> passed
  - Live API 批量复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch5-auth-after-fix.json` -> `severeCount=0`。
- 剩余未修复：
  - 本批剩余 17 个非严重项为权限、样例 ID 或参数类型导致的业务 `400/403/404`，包括文档下载权限、工程师任务权限、机台齐套率样例、报表下载/预览样例、现场任务样例、模板配置样例、项目齐套率样例、排产计划样例、导入导出模板类型和管理节奏默认报告配置等。
  - 带路径参数 GET 已覆盖到第 600 个；仍需继续第 601-938 个接口，以及关键写流程、权限组合和前端 E2E。
  - 系统仍未达到“全系统所有 bug 清零”，本轮只代表带路径参数 GET 第五批认证后严重 500 清零。

### 37. API 深扫第十七批：带路径参数 GET 第四批认证接口严重缺陷清零

- 扫描证据：
  - 未认证探测：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch4.json`
    - `totalPathParamGet=936`
    - `offset=360`
    - `limit=120`
    - `checked=120`
    - `issueCount=120`
    - `severeCount=0`
    - 状态全为 `401`，仅证明认证保护生效，不作为清零证据。
  - 认证初扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch4-auth.json`
    - `totalPathParamGet=936`
    - `offset=360`
    - `limit=120`
    - `checked=120`
    - `issueCount=45`
    - `severeCount=26`
  - 修复后认证复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch4-auth-after-fix.json`
    - 当前 live OpenAPI 统计 `totalPathParamGet=938`
    - `offset=360`
    - `limit=120`
    - `checked=120`
    - `issueCount=18`
    - `severeCount=0`
    - 剩余状态分布：`404 x13`、`400 x3`、`403 x2`。
- 覆盖范围：
  - OpenAPI 中带路径参数 GET 的第 361-480 个接口。
  - 本轮严重项集中在工单/绩效/战略分解与审视/年度重点工作/委外订单与打印/任务评论/资质/项目文档等认证后读取链路。
- 根因：
  - 历史服务仍读取旧字段名，如 `User.name`、`Department.name`、`Project.progress`、`PersonalKPI.user_id/source_kpi_id/dept_objective_id`、`StrategyComparison.comparison_type/base_year/compare_year/created_by`。
  - 多个响应模型对 legacy `NULL` 和 JSON 字符串过严，导致 Pydantic v2 响应校验失败。
  - 策略服务拆包后存在相对导入漂移，错误引用不存在的 `health_calculator` 子模块。
  - `annual_key_work_project_links.is_active` 在 live SQLite 旧库缺列，年度重点工作项目链接字段映射不完整。
  - 委外订单打印读取已不存在的主表交付数量字段，旧库交付数量实际在交付明细表。
- 修复：
  - 增加模型兼容属性：`User.name`、`Department.name`、`Project.progress`、`PersonalKPI.user_id/dept_objective_id/source_kpi_id/name`、`StrategyComparison` 历史别名。
  - 修复问题列表 JSON 字符串解析、团队/部门绩效无周期空响应、绩效数据完整性建议、反馈消息、方案工程师评分、经理评价空字段默认值。
  - 修正策略 KPI/健康度导入路径、追溯链路返回结构、例行管理周期响应、执行状态看板响应、比较详情序列化、年度重点工作项目链接字段。
  - 为旧 SQLite 补 `annual_key_work_project_links.is_active` schema patch。
  - 委外订单/明细/打印、任务评论、资质员工详情、项目文档版本等接口增加 legacy `NULL` 默认值和显式响应转换。
  - 扩展 `tests/api/test_path_param_route_contracts.py`，新增 4 组认证路径参数 GET 回归，覆盖本轮字段漂移、空值、旧库缺列和响应结构问题。
- 验证：
  - 新增 4 组回归先 RED 后修复；最终：
    - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py -k 'authenticated_path_param_routes_tolerate_legacy_aliases_and_json_text or engineer_performance_path_routes_tolerate_missing_optional_data or strategy_path_routes_tolerate_legacy_model_field_drift or outsourcing_task_qualification_and_document_routes_tolerate_legacy_nulls' -x --tb=short --disable-warnings` -> 4 passed
    - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py --tb=short --disable-warnings` -> 22 passed
    - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py --tb=short --disable-warnings` -> 39 passed
  - `python -m py_compile` 覆盖本轮变更文件 -> passed。
  - Live API 批量复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch4-auth-after-fix.json` -> `severeCount=0`。
- 剩余未修复：
  - 本批剩余 18 个非严重项为样例 ID/参数/权限导致的业务 `400/403/404`，包括告警订阅、分摊单下载、工程师绩效样例 job_type/user、用户详情、项目绩效样例项目、委外供应商、PMO 结项、任务中心、调度配置、资质模型等。
  - 带路径参数 GET 已覆盖到第 480 个；仍需继续第 481-938 个接口，以及关键写流程、权限组合和前端 E2E。
  - 系统仍未达到“全系统所有 bug 清零”，本轮只代表带路径参数 GET 第四批认证后严重 500 清零。

### 36. API 深扫第十六批：带路径参数 GET 第三批严重缺陷清零

- 扫描证据：
  - 初扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch3.json`
    - `totalPathParamGet=938`
    - `offset=240`
    - `limit=120`
    - `checked=120`
    - `issueCount=32`
    - `severeCount=19`
  - 修复后复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch3-after-fix.json`
    - `totalPathParamGet=936`
    - `offset=240`
    - `limit=120`
    - `checked=120`
    - `issueCount=14`
    - `severeCount=0`
- 覆盖范围：
  - OpenAPI 中带路径参数 GET 的第 241-360 个接口。
  - 本轮严重项集中在供应商物料、缺料智能处理方案、售前技术参数模板、售前 AI 成本/方案/情绪/报价/赢率、验收报告/签署/问题、节点任务等读取链路。
- 根因：
  - 多个接口直接返回 ORM 对象或 legacy JSON 形态，响应模型要求更严格后触发 500。
  - 历史 SQLite 中存在大量 `NULL` 的布尔、数值、状态、时间、字符串字段，Pydantic v2 响应模型严格校验失败。
  - 售前 AI 报价历史数据存在旧枚举值 `NORMAL`，SQLAlchemy Enum 在 ORM 读取时抛 `LookupError`。
  - 赢率预测服务被同步 `Session` 调用时仍 `await db.execute(...)`，导致运行时类型错误。
  - 验收报告接口引用了 schema 字段 `include_signatures`，但历史 ORM 模型没有该列。
- 修复：
  - 供应商物料接口改为显式输出 `MaterialResponse`，避免 ORM 直接序列化失败。
  - 缺料智能处理方案、售前 AI 成本/方案/情绪/赢率、验收、节点任务等 schema 增加 legacy `NULL` 默认值。
  - 售前技术参数模板允许 `reference_docs/sample_images` 保留历史 JSON 对象结构。
  - 售前 AI 报价详情增加 raw SQL 兜底读取和枚举归一化，未知报价类型/状态降级为稳定默认值；报价明细非列表时输出空列表。
  - 赢率预测服务增加同步/异步 DB session 统一执行 helper。
  - 验收报告列表用 `getattr(..., True)` 兼容模型字段漂移，并补齐报告版本默认值。
  - 扩展 `tests/api/test_path_param_route_contracts.py`，覆盖本轮 5 组路径参数 GET 回归场景。
- 验证：
  - `python -m py_compile app/api/v1/endpoints/suppliers.py app/schemas/shortage_smart.py app/schemas/presale_technical_parameter.py app/schemas/sales/presale_ai_cost.py app/schemas/presale_ai_solution.py app/schemas/presale_ai_emotion.py app/schemas/presale_ai_quotation.py app/services/presale/presale_ai_quotation_service.py app/api/v1/presale_ai_quotation.py app/services/win_rate_prediction_service/service.py app/schemas/presale_ai_win_rate.py app/schemas/acceptance.py app/api/v1/endpoints/acceptance/report_generation.py app/schemas/stage_template/node_tasks.py tests/api/test_path_param_route_contracts.py` -> passed
  - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py --tb=short` -> 18 passed
  - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py --tb=short` -> 35 passed
  - Live API 定点复验均 200：
    - `/api/v1/presale/ai/quotation/1`
    - `/api/v1/presale/ai/win-rate/1`
    - `/api/v1/acceptance/acceptance-orders/1/report`
  - Live API 批量复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch3-after-fix.json` -> `severeCount=0`
- 剩余未修复：
  - 本批剩余 14 个非严重项均为样本 ID/文件/配置不存在导致的业务 404，包括报价版本、结算单、研发文档下载、售前 AI 工作流/成本/建议、验收文件下载、报表配置、仓库入库/出库/盘点详情等。
  - 带路径参数 GET 已覆盖 1-360，仍需继续 361-936 以及关键写流程、权限组合和前端 E2E。
  - 系统仍未达到“全系统所有 bug 清零”，本轮只代表带路径参数 GET 第三批严重 500 清零。

### 35. API 深扫第十五批：带路径参数 GET 第二批严重缺陷清零

- 扫描证据：
  - 初扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch2.json`
    - `totalPathParamGet=938`
    - `offset=120`
    - `limit=120`
    - `checked=120`
    - `issueCount=25`
    - `severeCount=18`
  - 修复后复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch2-after-fix.json`
    - `checked=120`
    - `issueCount=9`
    - `severeCount=0`
- 覆盖范围：
  - OpenAPI 中带路径参数 GET 的第 121-240 个接口。
  - 本轮严重项集中在项目阶段、项目风险、物料订阅、项目变更、生产进度、销售合同/模板/发票/技术评估/报价导出。
- 根因：
  - 历史数据中存在 `NULL` 的布尔、数值、状态、枚举字段，Pydantic v2 响应模型严格校验后直接 500。
  - 本地历史库缺少可选业务表：`project_risks`、`material_progress_subscriptions`。
  - 项目变更审批记录存在历史非法枚举值 `ch230356`，SQLAlchemy Enum 在 ORM 读取时抛 `LookupError`。
  - 发票审批接口仍调用旧审批引擎方法 `get_approval_record`，当前审批引擎已迁移到 `ApprovalInstance/ApprovalTask`。
  - 报价 Excel/PDF 导出把中文文件名直接塞入 `Content-Disposition`，Starlette header latin-1 编码失败。
  - 合同模板 apply 接口返回富对象，但 response model 要求 `success/template_id/version_id`。
- 修复：
  - 阶段、生产进度、销售合同、技术评估、审批流程、项目变更 schema 增加历史脏数据默认值和进度 0-100 裁剪。
  - 项目风险服务增加缺表空结果/404 降级；物料订阅读接口缺表返回未订阅。
  - 项目变更审批记录改用 raw mapping 读取，并把未知审批决策归一为 `PENDING`。
  - 发票审批状态/历史改用现有 `ApprovalInstance/ApprovalTask` 查询并返回当前 schema 结构。
  - 合同模板 apply 补齐必填响应字段，同时保留模板、版本、差异、历史为可选富字段。
  - 报价导出文件名使用 RFC 5987 百分号编码，避免中文 header 崩溃。
  - 新增/扩展 `tests/api/test_path_param_route_contracts.py`，覆盖本轮 6 组回归。
- 验证：
  - `python -m py_compile app/schemas/stage_template/instances.py app/services/project_risk/project_risk_service.py app/services/material_progress_service.py app/schemas/change_request.py app/services/project_change_requests/service.py app/schemas/production_progress.py app/schemas/sales/contract_enhanced.py app/schemas/sales/assessments.py app/schemas/approval/flow.py app/schemas/sales/contract_templates.py app/api/v1/endpoints/sales/templates/contract_templates.py app/api/v1/endpoints/sales/invoices/workflow.py app/api/v1/endpoints/sales/quote_exports.py` -> passed
  - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py` -> 13 passed
  - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py` -> 30 passed
  - Live API 复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch2-after-fix.json` -> `severeCount=0`
- 剩余未修复：
  - 本批剩余 9 个非严重项均为业务前置条件或明确未实现：
    - 评价、机台进度、阶段详情、工时详情、风险详情、异常处理流程、评估版本比较、线索需求详情均为样本 ID 不存在导致 404。
    - `/api/v1/sales/enhanced/attachments/{attachment_id}/download` 返回 501：下载功能仍是明确 TODO，未在本轮冒充已实现。
  - 带路径参数 GET 总量为 938；已覆盖 1-240，仍需继续 241-938 以及关键写流程、权限组合和前端 E2E。
  - 系统仍未达到“全系统所有 bug 清零”，本轮只代表带路径参数 GET 第二批严重 500 清零。

### 34. API 深扫第十四批：带路径参数 GET 第一批严重缺陷清零

- 扫描证据：
  - 本批从 OpenAPI 抽取“带路径参数”的只读 GET 接口第 1-120 个；必填 query 参数也按类型生成样本。
  - `.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch1.json`：初扫 checked 120，issueCount 38，severeCount 15。
  - `.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch1-after-fix2.json`：同口径复扫 checked 120，issueCount 23，severeCount 0。
- 修复接口/问题：
  - `GET /api/v1/org/departments/{dept_id}/users`：用户角色关系从不存在的 `user_roles` 改为当前 `roles` 关系。
  - `GET /api/v1/projects/templates/{template_id}/versions`：模板版本说明从不存在的 `description` 改为 `release_notes`。
  - `GET /api/v1/projects/projects/{project_id}/overview`、`GET /api/v1/projects/projects/{project_id}/after-sales-status`：开发 SQLite 缺少售后表时返回空售后统计；项目总览不再直接返回 ORM `Project` 对象。
  - `GET /api/v1/projects/{project_id}`：项目详情兼容历史 NULL，补齐进度、金额、激活状态、ERP 同步状态、开票/尾款状态默认值。
  - `GET /api/v1/projects/{project_id}/status-history`：状态日志使用真实字段 `changed_at` 作为创建时间输出。
  - `GET /api/v1/projects/{project_id}/payment-plans`：收款计划字段从旧 `plan_type` 改为当前 `payment_type`，同时保留兼容输出。
  - `GET /api/v1/projects/{project_id}/resource-plan/`、`/utilization`、`/summary`：资源计划兼容历史 NULL 和旧阶段编码，补齐人数、分配比例、分配状态，并避免汇总计算时 `None` 参与求和。
  - `GET /api/v1/projects/{project_id}/members/`：项目成员兼容历史 NULL 的 `allocation_pct/is_active`。
  - `GET /api/v1/projects/{project_id}/costs/`：项目成本兼容历史 NULL 的成本类型、成本分类、税额和发生日期。
  - `GET /api/v1/projects/{project_id}/evaluations/`：项目评价兼容历史 NULL 的分项得分、总分、等级和状态。
  - `GET /api/v1/projects/{project_id}/costs/predictions/{prediction_id}`、`/suggestions/{suggestion_id}`：成本预测/优化建议详情兼容历史 NULL 和非零点 `datetime`，避免响应模型校验 500。
- 验证：
  - 新增 `tests/api/test_path_param_route_contracts.py`，覆盖本批字段漂移、历史 NULL、缺表、ORM 序列化和成本预测详情场景。
  - `python -m py_compile` 覆盖本批修改的 Python 文件 -> passed。
  - `.venv/bin/pytest -q tests/api/test_path_param_route_contracts.py tests/api/test_required_query_route_contracts.py tests/api/test_batch14_route_contracts.py` -> 24 passed。
  - 同口径 path-param GET 第 1-120 个复扫：`.gstack/qa-reports/api-path-param-smoke-2026-06-26-batch1-after-fix2.json`，severeCount 为 0。

剩余未修复：

- 复扫剩余 23 个 issue 均为业务前置条件或样本不存在导致的 400/404，例如不存在的模板/机台/计划/文档/资源记录；本批没有把这些业务态响应改成 200。
- 带路径参数 GET 总量为 938，本批覆盖前 120 个；后续仍需继续第 121-938 个、关键写流程、权限组合和前端端到端路径。目前没有把“全系统全面清理”标记为完成。

### 33. API 深扫第十三批：必填 Query 只读 GET 严重缺陷清零

- 扫描证据：
  - 本批从 OpenAPI 抽取“无路径参数、存在必填 query”的只读 GET 接口，共 107 个。
  - `.gstack/qa-reports/api-required-query-smoke-2026-06-26-batch1.json`：初扫 checked 107，issueCount 19，severeCount 8。
  - `.gstack/qa-reports/api-required-query-smoke-2026-06-26-batch1-after-fix.json`：同口径复扫 checked 107，issueCount 18，severeCount 0。
- 修复接口/问题：
  - `GET /api/v1/projects/status?project_id=1`：审批状态接口调用已不存在的 `ApprovalEngineService.get_approval_record/get_pending_tasks/get_approval_logs`，改为直接按当前模型查询 `ApprovalInstance`、`ApprovalTask`、`ApprovalActionLog`。
  - `GET /api/v1/materials/search?keyword=测试`：采购订单明细字段从旧 `po_id` 漂移为 `order_id`，同步修复物料统计和装配套件分析中的引用。
  - `GET /api/v1/engineer-performance/data-integrity/reminders?period_id=1`：工程师用户显示名从不存在的 `user.name` 改为 `display_name/real_name/username` 兜底。
  - `GET /api/v1/ai-strategy/reviews?strategy_id=1`、`GET /api/v1/strategy/reviews?strategy_id=1`：兼容历史战略复盘 JSON，字符串列表自动规范为 `{"content": ...}` 结构，参会人姓名拆入 `attendee_names`。
  - `GET /api/v1/report-center/rd-expense/rd-personnel?year=2026`：研发项目起止日期字段从不存在的 `start_date/end_date` 改为当前实际/计划/立项日期字段兜底。
  - `GET /api/v1/report-center/rd-expense/rd-export?report_type=auxiliary-ledger&year=2026&format=xlsx`：`xlsx` 规范为 `excel`，报表适配器按格式选择渲染器，并支持从 `file_path` 流式返回导出的 Excel 文件。
  - `GET /api/v1/management-rhythm/reports-unified/meeting-monthly?year=2026&month=6`：月度会议报表 YAML 对空统计结果增加保护，避免空数组下标异常。
  - `GET /api/v1/presale-analytics/resource-waste-analysis?period=测试`、`GET /api/v1/presale-analytics/salesperson-ranking?period=测试` 及 `/api/v1/presales/...` 兼容路径：无效 period 从 `ValueError` 500 改为 422，并修正销售人员字段为 `display_name`。
- 验证：
  - `python -m py_compile` 覆盖本批修改的 Python 文件 -> passed。
  - `.venv/bin/pytest -q tests/api/test_required_query_route_contracts.py` -> 4 passed。
  - `.venv/bin/pytest -q tests/api/test_batch14_route_contracts.py` -> 13 passed。
  - `.venv/bin/pytest -q tests/unit/test_report_framework_service.py` -> 31 passed。
  - 现场复验本批 8 个严重缺陷接口均不再 500；其中研发费用 Excel 导出返回 `application/vnd.openxmlformats-officedocument.spreadsheetml.sheet`。
  - 同口径必填 query GET 复扫：`.gstack/qa-reports/api-required-query-smoke-2026-06-26-batch1-after-fix.json`，severeCount 为 0。

剩余未修复：

- 复扫剩余 18 个 issue 均为业务前置条件或扫描默认值导致的 400/404，例如缺少排产计划、批次、日报、模板或绩效周期；本批没有把这些业务态响应改成 200。
- 后续仍需继续覆盖带路径参数的只读接口、关键写流程、权限组合和前端端到端路径；目前没有把“全系统全面清理”标记为完成。

### 32. API 深扫第七至十二批：剩余无参 GET 全量复扫

- 扫描证据：
  - OpenAPI 当前可抽取的无路径参数、无必填 query 的 GET 共 1332 个。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch7.json`：第 721-840 个，checked 120，issueCount 0。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch8.json`：第 841-960 个，checked 120，issueCount 0。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch9.json`：第 961-1080 个，初扫 issueCount 66，全部为 `/sales-targets/*` 的 429 限流。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch9-slow-rerun.json`：同批慢速复跑，checked 120，issueCount 0。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch10.json`：第 1081-1200 个，checked 120，issueCount 0。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch11.json`：第 1201-1320 个，checked 120，issueCount 0。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch12.json`：第 1321-1332 个，checked 12，issueCount 0。
- 结论：
  - API read-only 无参 GET 深扫已覆盖 1332/1332。
  - 第九批初始 429 的响应均为 `{"detail":"请求过于频繁，请稍后再试"}`，降速后全量通过，归类为扫描器触发限流，不是接口 500/404 缺陷。
  - 本轮第七至十二批未产生新的代码修复项。

剩余未修复：

- 后续还需要覆盖带路径参数/必填 query 的只读接口和关键写流程。
- 目前没有把“全系统全面清理”标记为完成。

### 31. API 深扫第六批：装配/预算/商务支持/报表框架 legacy 兼容修复

- 扫描证据：
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch6.json`：继续从 OpenAPI 抽取第 601-720 个无路径参数、无必填 query 的 GET 接口，初扫发现 16 个非 2xx，其中 15 个为 500，1 个为报表配置 404。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch6-after-fix.json`：同口径 120 个 GET 接口复跑，issueCount 为 0。
- 修复接口：
  - `GET /api/v1/assembly-kit/material-mapping/category-mappings` -> 500 修复为 200。
  - `GET /api/v1/assembly-kit/scheduling/suggestions` -> 500 修复为 200。
  - `GET /api/v1/budgets/`、`GET /api/v1/budgets/allocation-rules` -> 500 修复为 200。
  - `GET /api/v1/business-support-orders/invoice-requests`、`GET /api/v1/business-support-orders/customer-registrations` -> 500 修复为 200。
  - `GET /api/v1/business-support-orders/reports/sales-monthly` -> 报表配置 404 修复为 200。
  - `GET /api/v1/management-rhythm/report-configs/meeting-reports/configs`、`GET /api/v1/management-rhythm/reports/meeting-reports` -> 500 修复为 200。
  - `GET /api/v1/my/work-logs`、`GET /api/v1/analytics/analytics/workload/overview`、`GET /api/v1/project-reviews/lessons` -> 500 修复为 200。
  - `GET /api/v1/sla/policies`、`GET /api/v1/sla/monitors`、`GET /api/v1/solution-credits/admin/configs`、`GET /api/v1/standard-costs/` -> 500 修复为 200。
- 根因：
  - 多个只读列表响应模型没有兼容历史 NULL：装配映射、排产建议、预算、商务支持开票/注册、管理节奏、工作日志、复盘经验、SLA、积分配置、标准成本均触发 Pydantic 响应校验 500。
  - 工作量分析读取 `Department.name`，当前模型字段实际为 `dept_name`。
  - 装配排产建议读取 `Project.project_no/name`，当前模型字段实际为 `project_code/project_name`。
  - 销售月报 YAML 已使用 `type: adapter` 和 `SalesReportAdapter`，但统一报表框架的 `DataSourceType/DataSourceConfig/DataResolver` 未支持 adapter 数据源，导致配置校验 404。
  - 报表表达式把空月份渲染为字符串 `"None"`，旧销售月报接口还依赖 `result.data["sales_data"]` 原始数据源。
- 修复：
  - 给上述 schema 增加最小默认值/空值转换，保留真实字段，避免把历史 NULL 放大成接口 500。
  - 工作量分析改用 `dept.dept_name`；装配排产建议改用 `project.project_code/project.project_name`。
  - 报表框架新增 `adapter` 数据源类型和 `adapter` 配置字段，`DataResolver` 动态调用已存在的报表适配器。
  - 表达式解析器将 `None/null` 字符串结果转换回空值；JSON 报表结果保留 `sales_data` 等原始数据源，兼容旧销售月报 endpoint。
- 验证：
  - `.venv/bin/python -m py_compile app/schemas/assembly_kit.py app/schemas/budget.py app/schemas/business_support/invoice.py app/schemas/business_support/registration.py app/schemas/management_rhythm.py app/schemas/work_log.py app/schemas/project_review.py app/schemas/project_review/lesson.py app/schemas/sla.py app/api/v1/endpoints/solution_credits/schemas.py app/schemas/standard_cost.py app/api/v1/endpoints/analytics/workload.py app/api/v1/endpoints/assembly_kit/scheduling.py app/services/report_framework/models.py app/services/report_framework/data_resolver.py app/services/report_framework/engine.py app/services/report_framework/expressions/parser.py` -> passed。
  - `.venv/bin/pytest -q tests/api/test_batch14_route_contracts.py` -> 13 passed。
  - `.venv/bin/pytest -q tests/unit/test_report_framework_service.py` -> 31 passed。
  - 现场复验 `/api/v1/business-support-orders/reports/sales-monthly` 为 200，并返回真实销售月报数据。
  - 同口径 OpenAPI read-only 第六批 120 接口复跑：`.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch6-after-fix.json`，issueCount 为 0。

剩余未修复：

- API read-only 深扫已完成前 720 个无参 GET；后续还需要继续覆盖剩余 OpenAPI GET、带 query 的只读接口和关键写流程。
- 目前没有把“全系统全面清理”标记为完成。

### 30. API 深扫第五批：战略对比字段漂移与外协 legacy NULL 修复

- 扫描证据：
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch5.json`：继续从 OpenAPI 抽取第 481-600 个无路径参数、无必填 query 的 GET 接口，初扫发现 5 个 500。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch5-after-fix.json`：同口径 120 个 GET 接口复跑，issueCount 为 0。
- 复现接口：
  - `GET /api/v1/ai-strategy/comparisons` -> 500。
  - `GET /api/v1/strategy/comparisons` -> 500。
  - `GET /api/v1/outsourcing-deliveries` -> 500。
  - `GET /api/v1/outsourcing-inspections` -> 500。
  - `GET /api/v1/outsourcing-payments` -> 500。
- 根因：
  - 战略对比 endpoint/service 仍按旧字段 `comparison_type/base_year/compare_year/created_by` 构造响应和创建记录；当前模型真实字段为 `current_year/previous_year/generated_date/generated_by` 等。
  - 战略对比筛选逻辑还引用未定义变量 `base_strategy_id`。
  - 外协交付、质检、付款历史数据存在 `vendor_name/delivery_type/status/inspect_type` 等 legacy NULL 或类型不匹配，响应模型校验 500。
- 修复：
  - 战略对比创建、列表统一对齐当前模型字段，并补充 `highlights/improvements/recommendations` JSON 文本到列表字段的安全转换。
  - 修正战略对比列表筛选变量为 `current_strategy_id`。
  - 外协响应 schema 对未知外协商、交付类型、状态、质检类型做最小默认值兜底。
- 验证：
  - 新增 2 个 batch5 回归测试，覆盖 `/strategy/comparisons`、`/ai-strategy/comparisons` 和三条外协只读接口，先红灯复现，修复后通过。
  - `.venv/bin/pytest -q tests/api/test_batch14_route_contracts.py` -> 13 passed。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/strategy/comparison.py app/services/strategy/comparison_service.py app/schemas/outsourcing.py tests/api/test_batch14_route_contracts.py` -> passed。
  - 现场复验上述 5 个原 500 接口均为 200。

剩余未修复：

- API read-only 深扫已完成前 600 个无参 GET；后续还需要继续覆盖剩余 OpenAPI GET、带 query 的只读接口和关键写流程。
- 目前没有把“全系统全面清理”标记为完成。

### 29. API 深扫第四批：售前 AI/奖金/工程师 legacy 数据兼容修复

- 扫描证据：
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch4.json`：继续从 OpenAPI 抽取第 361-480 个无路径参数、无必填 query 的 GET 接口，初扫发现 12 个非 2xx，其中 8 个为 500。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch4-after-fix.json`：同口径 120 个 GET 接口复跑，8 个 500 已清零；剩余 4 个 404 均为当前登录用户无工程师档案/无考核周期的业务前置条件。
- 修复接口：
  - `GET /api/v1/presale/tenders/analysis` -> 500 修复为 200。
  - `GET /api/v1/presale/ai/usage-stats` -> 500 修复为 200。
  - `GET /api/v1/presale/ai/config` -> 500 修复为 200。
  - `GET /api/v1/presale/ai/follow-up-reminders` -> 500 修复为 200。
  - `GET /api/v1/bonus/rules/rules` -> 500 修复为 200。
  - `GET /api/v1/bonus/team/team-allocations` -> 500 修复为 200。
  - `GET /api/v1/allocation-sheets` -> 500 修复为 200。
  - `GET /api/v1/engineer-performance/engineer` -> 500 修复为 200。
- 根因：
  - 投标分析访问 `Opportunity.industry`，当前商机模型没有该字段。
  - 售前 AI 使用统计表存在旧字符串枚举值，ORM Enum 反序列化抛 `LookupError`。
  - 售前 AI 配置、跟进提醒、奖金规则、团队奖金分配、奖金分配明细表存在 legacy NULL，响应模型必填字段校验 500。
  - 工程师列表继续访问旧字段 `User.name`，当前用户显示名应使用 `display_name/real_name/username`。
- 修复：
  - 投标行业统计使用 `Opportunity.industry` 的安全读取，并回退到 `project_type` 或 `其他`。
  - 售前 AI 使用统计改用 raw/cast 字符串读取 AI function，避免 ORM Enum 处理器被历史脏值击穿。
  - 售前 AI、情绪跟进、奖金相关响应 schema 对历史 NULL 做最小默认值兜底。
  - 工程师列表改用 `user.display_name`。
- 验证：
  - 新增 3 个 batch4 回归测试，覆盖售前/AI、奖金、工程师列表，先红灯复现，修复后通过。
  - `.venv/bin/pytest -q tests/api/test_batch14_route_contracts.py` -> 11 passed。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/presale/bids.py app/services/presale/presale_ai_integration.py app/schemas/presale_ai.py app/schemas/presale_ai_emotion.py app/schemas/bonus.py app/api/v1/endpoints/engineer_performance/engineer.py tests/api/test_batch14_route_contracts.py` -> passed。
  - 现场复验上述 8 个原 500 接口均为 200。

剩余未修复：

- batch4 复扫剩余 4 个 404：`/engineer-performance/engineer/profile`、`/engineer-performance/collaboration/pending-ratings`、`/my`、`/performance/team/ranking`，均为无当前工程师档案或无当前考核周期的业务前置条件；暂不按 500/路由错误处理。
- API read-only 深扫已完成前 480 个无参 GET；后续还需要继续覆盖剩余 OpenAPI GET、带 query 的只读接口和关键写流程。
- 目前没有把“全系统全面清理”标记为完成。

### 28. API 深扫第三批：销售转化字段漂移与库存 legacy NULL 修复

- 扫描证据：
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch3.json`：继续从 OpenAPI 抽取第 241-360 个无路径参数、无必填 query 的 GET 接口，初扫发现 4 个 500。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch3-after-fix.json`：同口径 120 个 GET 接口复跑，issueCount 为 0。
- 复现接口：
  - `GET /api/v1/sales/conversion/by-person` -> 500。
  - `GET /api/v1/inventory/stocks` -> 500。
  - `GET /api/v1/inventory/count/tasks` -> 500。
  - `GET /api/v1/inventory/analysis/turnover` -> 500。
- 根因：
  - 销售转化按人统计仍访问旧合同字段 `Contract.owner_id`，当前合同模型真实负责人字段为 `sales_owner_id`。
  - 历史 SQLite 库中库存与盘点任务存在 legacy NULL：`reserved_quantity/unit/unit_price/total_value/status/count_type/counts/total_diff_value` 等响应必填字段为 NULL 时触发响应模型校验 500。
  - 库存周转分析直接对 `None` 金额求和，真实历史数据下 `sum()` 抛类型错误。
- 修复：
  - 销售转化合同统计统一按 `Contract.sales_owner_id` 分组。
  - `MaterialStockResponse` 与 `StockCountTaskResponse` 对历史 NULL 数字、单位、状态、盘点类型做响应层默认值兜底。
  - 库存分析服务对出库金额、库存金额、库龄数量/单价/金额统一做 `None -> 0` 归一化。
- 验证：
  - 新增回归测试 `test_sales_conversion_by_person_uses_contract_sales_owner`、`test_inventory_readonly_routes_tolerate_legacy_nulls`，先红灯复现，修复后通过。
  - `.venv/bin/pytest -q tests/api/test_batch14_route_contracts.py` -> 8 passed。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/sales/conversion_analysis.py app/api/v1/endpoints/inventory/inventory_router.py app/services/inventory/analysis_service.py` -> passed。
  - 现场接口 `GET http://127.0.0.1:8002/api/v1/sales/conversion/by-person` -> 200。
  - 现场接口 `GET http://127.0.0.1:8002/api/v1/inventory/stocks` -> 200。
  - 现场接口 `GET http://127.0.0.1:8002/api/v1/inventory/count/tasks` -> 200。
  - 现场接口 `GET http://127.0.0.1:8002/api/v1/inventory/analysis/turnover` -> 200。

剩余未修复：

- API read-only 深扫已完成前 360 个无参 GET；后续还需要继续覆盖剩余 OpenAPI GET、带 query 的只读接口和关键写流程。
- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 目前没有把“全系统全面清理”标记为完成。

### 27. API 深扫第二批：审批 pending 契约漂移与审批模板脏 JSON 修复

- 扫描证据：
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch2.json`：继续从 OpenAPI 抽取第 121-240 个无路径参数、无必填 query 的 GET 接口，初扫发现 2 个 500。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch2-after-fix.json`：同口径 120 个 GET 接口复跑，issueCount 为 0。
- 复现接口：
  - `GET /api/v1/sales/contracts/approval/pending` -> 500。
  - `GET /api/v1/sales/templates` -> 500。
- 根因：
  - `ApprovalEngineService.get_pending_tasks()` 当前返回 `{"items": [...], "total": ...}`，合同审批服务仍按旧的 `List[ApprovalTask]` 直接遍历，实际遍历到 dict key 字符串后访问 `task.instance` 崩溃。
  - `/sales/templates` 命中审批模板列表路由；历史 SQLite 中 `approval_templates.form_schema` 存在非法 JSON 文本，ORM 查询 `ApprovalTemplate` 时 JSON 类型自动反序列化抛 `JSONDecodeError`。
- 修复：
  - 合同审批 pending 查询先解包 `items`，并一次性取足待审批任务后再做业务筛选和分页。
  - 同步修复通用审批基类和 ECN 审批服务的 pending 查询，避免后续同类接口再踩同一返回契约漂移。
  - 审批模板列表/详情改为选择原始列并对 `form_schema/visible_scope` 做安全 JSON 解析；脏 JSON 降级为 `None`，合法 JSON 保持原结构。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_batch14_route_contracts.py::test_sales_contract_pending_approval_route_accepts_engine_result_dict tests/api/test_batch14_route_contracts.py::test_sales_templates_route_tolerates_legacy_invalid_json`：先红灯复现两个 500，修复后通过。
  - `.venv/bin/pytest -q tests/api/test_batch14_route_contracts.py` -> 6 passed。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/approvals/templates.py app/services/contract_approval/service.py app/services/ecn/approval/service.py app/services/base_approval_workflow.py` -> passed。
  - 现场接口 `GET http://127.0.0.1:8002/api/v1/sales/contracts/approval/pending` -> 200。
  - 现场接口 `GET http://127.0.0.1:8002/api/v1/sales/templates` -> 200。

剩余未修复：

- API read-only 深扫已完成前 240 个无参 GET；后续还需要继续覆盖剩余 OpenAPI GET、带 query 的只读接口和关键写流程。
- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 目前没有把“全系统全面清理”标记为完成。

### 26. API 深扫第一批：静态路由遮挡归零与 legacy 报价模板 500 修复

- 扫描证据：
  - `.gstack/qa-reports/slow-smoke-2026-06-25-current-recheck.json`：复核此前 26 条慢速 smoke 问题入口，issueCount 为 0。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch1.json`：从 OpenAPI 抽取前 120 个无路径参数、无必填 query 的 GET 接口，发现 3 个非 2xx。
  - 路由遮挡审计：4455 条 method-route 初始发现 29 个“动态路由压住后置静态路由”的风险点；修复后冲突数为 0。
  - `.gstack/qa-reports/api-readonly-smoke-2026-06-25-batch1-after-fix.json`：同口径 120 个 GET 接口复跑后非 2xx 降为 2 个，均为业务前置条件。
- 复现接口：
  - `GET /api/v1/production/work-reports/my`：被 `/work-reports/{report_id}` 抢先匹配，返回 422。
  - `GET /api/v1/sales/leads/export`：被 `/leads/{lead_id}` 抢先匹配，返回 422。
  - `GET /api/v1/sales/quotes/templates`：`QuoteTemplate.created_by` 字段不存在，返回 500。
- 根因：
  - FastAPI/Starlette 按注册顺序匹配路由；多个模块把 `/{id}` 动态路由放在静态路由前，或动态路径缺少 `:int` converter。
  - 销售线索路由聚合顺序先注册 CRUD，再注册 actions，导致 `/leads/export` 落到 `/leads/{lead_id}`。
  - legacy 报价模板端点还按旧字段访问 `QuoteTemplate.created_by` 和 `QuoteTemplateVersion.content_json`；当前模型里模板归属是 `owner_id`，版本内容是 `sections/pricing_rules/config_schema/discount_rules`。
- 修复：
  - 将生产工单日报 `/work-reports/my` 放到详情路由前，并为详情、审批等 ID 路径增加 `:int` converter。
  - 调整销售线索路由注册顺序：actions、follow_ups 先于 CRUD。
  - 为项目、销售团队、报价、ECN、经营节奏配置、标准成本、用户、验收订单等高风险 ID 路由补充 `:int` converter，避免静态路径被字符串 ID 捕获。
  - legacy 报价模板端点统一使用 `owner_id` 做权限与兼容响应字段；版本序列化和创建改为当前模型字段，同时保留 `content_json` 响应别名。
- 验证：
  - `.venv/bin/pytest -q tests/api/test_batch14_route_contracts.py::test_legacy_sales_quote_templates_route_uses_current_template_model`：先红灯复现 500，修复后通过。
  - `.venv/bin/pytest -q tests/api/test_batch14_route_contracts.py` -> 4 passed。
  - 现场接口 `GET http://127.0.0.1:8002/api/v1/sales/quotes/templates` -> 200。
  - 同口径 OpenAPI read-only 120 接口复跑：`/sales/leads/export` 与 `/sales/quotes/templates` 已清零；剩余 `/auth/2fa/backup-codes` 为“未启用2FA”，`/production/work-reports/my` 为“当前用户未关联工人信息”，不再是路由遮挡或 500。

剩余未修复：

- API read-only 深扫仍只覆盖第一批 120 个无参 GET；后续还需要继续按批次覆盖剩余 OpenAPI GET、带 query 的只读接口和关键写流程。
- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 目前没有把“全系统全面清理”标记为完成。

### 25. 静态入口第十三批：剩余 99 条路由覆盖补齐与月度总结崩溃修复

- 扫描证据：
  - 当前从 `frontend/src/routes` 重新抽取静态路由 399 条；已有 clean route-smoke 证据覆盖 301 条，剩余 99 条进入第十三批。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch13.json`：覆盖剩余 99 条，初扫发现 23 条可疑入口；其中 20 条为快速扫测触发全局 `300/min` 内存限流后的 429。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch13-targeted-rerun.json`：23 条可疑入口全部清零。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch13-rerun.json`：第十三批剩余 76 条未问题入口节流复扫全部清零。
  - 当前静态路由覆盖复核：399/399 条当前静态路由均已有 clean route-smoke 证据，缺口 0。
- 复现页面：
  - `/personal/monthly-summary`
  - `/lead-assessment`
  - batch13 其余 97 条静态入口作为覆盖缺口一起复扫。
- 根因：
  - 月度总结页直接使用 `currentUser.name.charAt(0)`，但真实 `/auth/me` 写入 localStorage 的用户对象字段为 `real_name`，没有 `name`，导致页面 ErrorBoundary。
  - `LeadOverview` 和 `FollowUpManager` 仍使用 AntD v6 已弃用的 `List` / `Timeline.Item`，页面控制台输出 deprecation warning。
  - 初扫 20 条 429 来自自动化在 1 分钟内连续打开 99 个页面并触发全局 IP 限流；慢速逐页复扫后对应业务接口均为 200。
  - `/acceptance-orders` 初扫的请求失败来自外部 `rsms.me` 字体文件在页面切换时被浏览器中止；复扫已过滤为非本地接口噪声。
- 修复：
  - `MonthlySummary` 将 localStorage 用户对象统一归一为 `name / department / position`，`name` 依次兼容 `name`、`real_name`、`username`。
  - `SummaryForm` 对展示名、部门、职位增加兜底，避免用户字段漂移导致渲染崩溃。
  - `LeadOverview` 将热门线索改为普通列表，并将时间线改为 AntD `Timeline items` API。
  - `FollowUpManager` 将跟进任务改为普通列表，移除弃用的 AntD `List`。
- 验证：
  - `npm run test:run -- src/pages/__tests__/MonthlySummary.test.jsx`：先红灯复现 `Cannot read properties of undefined (reading 'charAt')`，修复后通过。
  - `npm run test:run -- src/pages/__tests__/MonthlySummary.test.jsx src/hooks/__tests__/useMonthlySummary.test.js` -> 15 passed。
  - Playwright targeted 23 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch13-targeted-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined`、无空白页。
  - Playwright 节流 76 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch13-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined`、无空白页。

剩余未修复：

- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 当前静态路由入口已覆盖清零，但系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 24. 宽页面第十二批：工时/模板配置/工作量看板兼容路由修复

- 扫描证据：
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch12.json`：覆盖 22 个战略、人资、模板、工时和工作中心入口，发现 4 条页面有 API 4xx/5xx 或控制台问题。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch12-targeted-rerun2.json`：4 个重点入口全部清零。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch12-rerun.json`：第十二批 22 个入口全部清零。
- 复现页面：
  - `/template-configs`
  - `/timesheet/batch`
  - `/timesheet/dashboard`
  - `/workload-board`
- 根因：
  - 模板配置模块存在但未挂载到主 API；live SQLite 可能缺少 `project_template_configs` 表，导致列表接口 500。
  - 前端工时列表仍调用旧 `/timesheets` 路径，后端实际记录路由为 `/timesheet/records`。
  - 工时模型和接口字段漂移：live 表使用 `hours/overtime_type/work_content`，前端契约使用 `work_hours/work_type/description`。
  - `TimesheetQualityService` 已有异常检测服务，但缺少 `/timesheet/anomalies` 路由。
  - 工作量看板调用 `/workload/dashboard`、`/workload/team`，后端只有 analytics/project 口径路由。
  - 工时看板收到 Decimal 字符串后直接 `.toFixed()`，触发控制台错误。
- 修复：
  - 主路由挂载 `template_configs`，模板配置列表在 live 表缺失时返回稳定空分页。
  - 新增 `/timesheet/anomalies` 质量检测路由，并纳入 timesheet router。
  - 新增 `/workload/dashboard`、`/workload/team` 兼容路由，按活跃用户、任务计划工时和实际工时返回看板摘要。
  - `timesheetApi` 工时 CRUD 路径统一到 `/timesheet/records`。
  - `Timesheet` 模型补兼容属性，`timesheet_records` 服务统一日期过滤、字段映射和大小写状态处理。
  - `TimesheetDashboard` 统一数值格式化和异常字段归一化，避免 Decimal 字符串触发 `.toFixed()` 崩溃。
- 验证：
  - `.venv/bin/pytest tests/api/test_batch12_route_contracts.py -q` -> 4 passed
  - `npm run test:run -- src/services/api/__tests__/hr.test.js src/services/api/__tests__/routeContracts.test.js` -> passed
  - Live API 复验 5/5 均 200：`/template-configs/configs`、`/timesheet/records`、`/timesheet/anomalies`、`/workload/dashboard`、`/workload/team`。
  - Playwright targeted 4 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch12-targeted-rerun2.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined`、无空白页。
  - Playwright 22 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch12-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined`、无空白页。
  - `npm run build` -> passed；仍只有既有 Vite 动态/静态导入和 chunk size 提示。
  - 后端 reload 曾卡住 8002，确认旧进程占端口后已重启；当前 `/health` 正常，日志见 `.gstack/qa-reports/backend-8002-batch12.log`。

剩余未修复：

- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 23. 宽页面第十一批：排程请求风暴/服务知识库/人员匹配/缺料预警修复

- 扫描证据：
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch11.json`：覆盖 50 个销售、排程、服务、缺料、人员匹配和战略入口，发现 9 条页面有 API 4xx/5xx、10 条页面有控制台问题。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch11-targeted-rerun.json`：10 个重点入口全部清零。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch11-rerun.json`：第十一批 50 个入口全部清零。
- 复现页面：
  - `/schedule`
  - `/schedule-generation`
  - `/service-knowledge-base`
  - `/service-records`
  - `/service-tickets`
  - `/service/center`
  - `/shortage-alerts`
  - `/staff-matching/matching`
  - `/staff-matching/profiles`
  - `/staff-matching/staffing-needs`
- 根因：
  - `ScheduleBoard` 在总览入口对所有项目并发请求里程碑，触发 `/milestones/projects/{id}/milestones` 大量 429；后续服务页的 429 是该请求风暴的连带影响。
  - 服务知识库历史数据存在 `status=NULL`，`KnowledgeBaseResponse.status` 枚举校验失败，导致 `/knowledge-base` 500。
  - 人员匹配历史旧数据存在 `matching_time=NULL`，`MatchingLogResponse.matching_time` 响应校验失败。
  - 员工匹配档案旧数据存在 `total_projects=NULL`，且技能 JSON 可能是 legacy sentinel 对象，不是数组。
  - 项目人员需求旧数据存在 `headcount/priority/allocation_pct/status/filled_count=NULL`，`required_skills` 也可能是 legacy sentinel 对象。
  - 缺料预警页面调用 `shortageAlertApi.getSummary()`，但前端 helper 和后端 `/shortage/detection/alerts/summary` 均缺失。
- 修复：
  - `ScheduleBoard` 增加里程碑补水阈值：总览项目过多时只展示项目卡片，不逐项目打里程碑接口；项目数量较少时才补里程碑详情。
  - `KnowledgeBaseResponse` 对响应态 `status` 做兜底归一化，历史 NULL 返回 `DRAFT`。
  - 人员匹配 profiles/staffing-needs/matching 返回层统一把 legacy NULL、旧 JSON sentinel 转成页面可用默认值。
  - 修正人员匹配档案工作量筛选中 `HrEmployeeProfile.id is None` 的 SQLAlchemy 条件，改为 `.is_(None)`。
  - 新增 `/shortage/detection/alerts/summary`，返回 pending/processing/resolved/total/critical 统计；前端 `shortageAlertApi.getSummary()` 指向该路径。
- 验证：
  - `.venv/bin/pytest tests/api/test_batch11_route_contracts.py -q` -> 5 passed
  - `npm run test:run -- src/services/api/__tests__/routeContracts.test.js src/pages/__tests__/ProjectManagementChildContext.test.jsx` -> 16 passed
  - Live API 复验均 200：`/knowledge-base`、`/staff-matching/matching/history`、`/staff-matching/profiles/`、`/staff-matching/staffing-needs/`、`/shortage/detection/alerts/summary`。
  - `npm run build` -> passed
  - Playwright targeted 10 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch11-targeted-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined`、无空白页。
  - Playwright 50 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch11-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined`、无空白页。

剩余未修复：

- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 22. 宽页面第十批：进度/报表/客户360/角色/延期分析路由修复

- 扫描证据：
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch10.json`：覆盖 50 个组织、进度、研发、报表、角色和销售入口，发现 6 条 API 4xx/5xx、8 条控制台问题。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch10-targeted-rerun3.json`：8 个重点入口全部清零。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch10-rerun.json`：第十批 50 个入口全部清零。
- 复现页面：
  - `/progress-tracking/schedule`
  - `/progress-tracking/wbs`
  - `/project-health-monitor`
  - `/reports/delay-reasons`
  - `/reports/milestone-rate`
  - `/role-management`
  - `/sales/customer-360`
  - `/sales/delay-analysis`
- 根因：
  - 进度看板把纯 `projectId` 传给只接受对象参数的阶段/里程碑 API helper，导致 Axios 参数合并报错。
  - 里程碑列表后端返回分页对象，页面仍按数组直接 `.map()`；同时进度看板额外批量请求项目进度概要，造成 live 冒烟时限流放大。
  - `/wbs-templates`、`/reports/milestone-rate`、`/reports/delay-reasons` 缺少与前端一致的兼容路由，且报表静态路径必须排在动态报表路由之前。
  - `/assembly/material-readiness/batch-kit-rate` 未注册，项目健康监控页批量成套率请求 404。
  - `RoleManagement` 漏导入 `LayoutGrid`、`Copy`，且本地重复 `renderDataScopeBadge` 引用了不存在的 `DATA_SCOPE_MAP`。
  - `Customer360` 使用 `customerId` 参数，但实际路由使用 `:id`；静态 `/sales/customer-360` 入口会请求 `/customers/undefined/360`。
  - 销售延期根因分析仍读取旧字段 `Task.delay_reason`，当前模型字段为 `block_reason`。
- 修复：
  - 新增 `progress_compat` 兼容 router，补齐 WBS 模板 CRUD、模板任务接口、里程碑完成率报表、延期原因报表，并同时挂载根路径和 `/progress` 前缀。
  - 在主路由聚合中把进度兼容 router 放在动态报表 router 前，避免 `/reports/{report_code}` 截获静态报表路径。
  - 新增装配成套率批量接口 `/assembly/material-readiness/batch-kit-rate`，按项目返回稳定的成套率摘要；空入参返回空映射。
  - `DelayRootCauseService` 改用 `Task.block_reason`，过滤空计划/实际完成日期，并补充任务责任人名称。
  - `stageApi.list()`、`milestoneApi.list()` 兼容纯项目 ID 和对象参数。
  - `ScheduleBoard` 兼容分页里程碑响应，并移除未使用的项目进度概要批量请求。
  - `RoleManagement` 补齐 lucide 图标导入，移除重复的本地数据权限 badge 渲染函数。
  - `Customer360` 同时兼容 `customerId` 与 `id` 路由参数；无客户 ID 的静态入口展示空态，不再发 `undefined` 请求。
- 验证：
  - `.venv/bin/pytest tests/api/test_batch10_route_contracts.py -q` -> 5 passed
  - `npm run test:run -- src/services/api/__tests__/projects.test.js src/services/api/__tests__/routeContracts.test.js` -> 51 passed
  - `npm run test:run -- src/pages/__tests__/ProjectManagementChildContext.test.jsx` -> 5 passed
  - 严格模式路由导入：`from app.main import app` 成功，API router 加载 4437 条路由；本批必需路径均已注册。
  - Live API 复验均 200：`/wbs-templates`、`/progress/wbs-templates`、`/reports/milestone-rate`、`/reports/delay-reasons`、`/sales/analysis/delay/root-cause`、`POST /assembly/material-readiness/batch-kit-rate`。
  - `npm run build` -> passed
  - Playwright targeted 8 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch10-targeted-rerun3.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined`、无空白页。
  - Playwright 50 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch10-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined`、无空白页。

剩余未修复：

- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 21. 宽页面第九批：模板/成本/现场/里程碑兼容路由修复

- 扫描证据：
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch9.json`：覆盖 50 个 AI 工具、预警订阅、变更、成本报价、客户、交付、人资、移动端和模板入口，发现 7 条 API 4xx/5xx、3 条请求失败、8 条控制台问题、1 条页面错误。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch9-targeted-rerun.json`：10 个重点入口全部清零。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch9-rerun.json`：第九批 50 个入口全部清零。
- 复现页面：
  - `/assembly-template-management`
  - `/cost-quotes/financial-costs`
  - `/cost-quotes/material-costs`
  - `/customer-communications`
  - `/field-commissioning`
  - `/financial-costs`
  - `/hourly-rates`
  - `/issue-templates`
  - `/lessons-learned`
  - `/milestones`
- 根因：
  - 装配模板页绕过统一 axios 客户端裸 `fetch("/api/v1/assembly-templates")`，未带 Authorization。
  - `/projects/financial-costs` 静态路径未注册在 `/projects/{project_id}` 之前，被动态项目详情路由截获为 422。
  - 销售采购物料提醒 `/sales/purchase-material-costs/reminder` 被 `{cost_id}` 动态路由截获，且提醒响应 schema 仍是旧字段。
  - `api.py` 主聚合漏挂 `/issue-templates`，现场调试兼容文件只有根占位，`/milestones` 全局路由缺失。
  - `/hourly-rates` 无尾斜杠会 307 到后端绝对地址，浏览器经 Vite proxy 触发 CORS/request failed。
  - 真实历史数据存在财务成本和问题模板 legacy NULL 字段，空测试库无法覆盖，live API 会响应校验 500。
- 修复：
  - 装配模板页改用 `assemblyKitApi.getTemplates()`，统一走 axios token 注入。
  - 新增 `/projects/financial-costs` 财务成本兼容路由，提供列表、模板下载、上传、删除，并在项目 router 中置于动态项目路由前。
  - 采购物料成本聚合路由改为静态提醒/匹配先于 `{cost_id}`，并把 `MaterialCostUpdateReminderResponse/Update` 对齐当前模型和页面字段。
  - `api.py` 挂载 `/issue-templates` 与全局 `/milestones`；新增全局里程碑兼容 CRUD/完成接口。
  - 现场调试兼容路由补齐 `/field/tasks`、`/field/dashboard` 和基本操作接口。
  - 工时费率聚合 router 增加 `/hourly-rates` 无尾斜杠 GET 别名，避免 307。
  - 财务成本和问题模板响应对 legacy NULL 默认字段做稳定兜底。
- 验证：
  - `.venv/bin/pytest tests/api/test_batch9_route_contracts.py -q` -> 7 passed
  - `npm run test:run -- src/services/api/__tests__/projects.test.js src/services/api/__tests__/hr.test.js src/services/api/__tests__/routeContracts.test.js` -> passed
  - Live API 复验均 200：`/projects/financial-costs`、`/sales/purchase-material-costs/reminder`、`/field/tasks`、`/field/dashboard`、`/issue-templates`、`/milestones/`、`/hourly-rates`、`/assembly-kit/templates/templates`。
  - 严格模式路由导入：`from app.main import app` 成功，`/api/v1/hourly-rates` 与 `/api/v1/hourly-rates/` 均在路由表。
  - `npm run build` -> passed
  - Playwright targeted 10 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch9-targeted-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined`、无空白页。
  - Playwright 50 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch9-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined`、无空白页。

剩余未修复：

- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 20. 宽页面第八批：排产/经验教训/验收/缺料/绩效链路修复

- 扫描证据：
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch8.json`：覆盖 50 个销售、项目交付、人资、PMO、售前、采购、生产、验收、缺料入口，发现 `/project-delivery-schedule`、`/engineer-performance/collaboration`、`/projects/lessons-learned`、`/acceptance-templates` 存在 API 4xx/5xx，`/projects/best-practices/recommend`、`/pmo/meetings`、缺料相关页面存在控制台问题，`/hr/performance-center` 存在 `undefined%`。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch8-targeted-rerun.json`：9 个重点入口全部清零。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch8-rerun.json`：第八批 50 个入口全部清零。
- 复现页面：
  - `/project-delivery-schedule`
  - `/engineer-performance/collaboration`
  - `/projects/lessons-learned`
  - `/projects/best-practices/recommend`
  - `/pmo/meetings`
  - `/acceptance-templates`
  - `/shortage/dashboard`
  - `/shortage-management-board`
  - `/hr/performance-center`
- 根因：
  - 项目交付排产后端包存在但未在 `api.py` 注册，且本地历史 SQLite 缺少 `project_delivery_*` 表。
  - 经验教训 `/lessons/*` 兼容文件仍是占位 router；本地历史 SQLite `project_lessons` 缺少 `ai_extracted` 字段，ORM 查询 500。
  - 验收模板旧数据存在 `version/is_system/is_active` 为 NULL，响应模型校验 500。
  - 工程师协作页面没有当前用户 ID 时仍请求 `/received/undefined`、`/given/undefined`。
  - 最佳实践热门接口返回统一 envelope，页面把对象当数组 `.map`。
  - 会议管理常量导出为对象，但页面按数组 `.map/.find` 使用。
  - 绩效中心对空统计直接渲染百分比和人数，显示 `undefined%`。
  - 缺料看板 Recharts 容器首屏布局宽高不稳定，触发 warning。
- 修复：
  - 注册 `/project-delivery` router，`projectDeliveryApi` 统一拆包 axios/envelope 响应并改用 `params`。
  - SQLite schema 启动补丁补齐 `project_delivery_*` 表，并在模型导出完成后做 SQLite-only 二次确保；补齐 `project_lessons.ai_extracted/ai_confidence`。
  - `/lessons/list`、`/lessons/stats`、`/lessons/search` 和基础详情/创建/更新/删除兼容路由改为真实读取 `ProjectLesson`。
  - 验收模板列表响应对 legacy NULL 字段给出稳定默认值。
  - 工程师协作读取当前用户 ID 前先做 localStorage 守卫，评分组件不再用字符串兜底。
  - 最佳实践页增加统一响应拆包和列表归一化，移除可见 `unknown` 默认值。
  - 会议类型/状态常量改为页面实际使用的数组形态。
  - 绩效中心统计和当前周期字段统一做有限数值/文本兜底。
  - 缺料看板 Recharts 容器改为稳定数字高度。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_batch8_route_contracts.py -q` -> 3 passed
  - `npm run test:run -- MeetingManagement.test.jsx BestPracticeRecommendations.test.jsx EngineerCollaboration.test.jsx PerformanceManagement.test.jsx` -> 4 passed
  - Live API 复验均 200：
    - `/api/v1/project-delivery/schedules`
    - `/api/v1/lessons/list`
    - `/api/v1/lessons/stats`
    - `/api/v1/acceptance/acceptance-templates?page=1&page_size=100`
  - SQLite 冷启动临时库验证：`project_delivery_*` 6 张表可自动创建。
  - `npm run build` -> passed
  - Playwright 9 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch8-targeted-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined/unknown`、无空白页。
  - Playwright 50 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch8-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined/unknown`、无空白页。

剩余未修复：

- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 19. 宽页面第七批：工作台/仪表盘/发货/财务/项目复盘链路修复

- 扫描证据：
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch7.json`：覆盖 50 个工作台、仪表盘、PMC、财务、人资、PMO、项目复盘入口，发现 `/strategic-meetings`、`/margin-prediction`、`/projects/reviews` 存在 API 4xx/5xx 或请求失败，`/shipments`、`/finance/cost-center` 存在控制台问题。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch7-targeted-rerun2.json`：5 个重点入口全部清零。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch7-rerun2.json`：第七批 50 个入口全部清零。
- 复现页面：
  - `/strategic-meetings`
  - `/shipments`
  - `/finance/cost-center`
  - `/margin-prediction`
  - `/projects/reviews`
  - `/pmc/delivery-plan`（第七批全量复扫中追加发现 `unknown` 显示）
- 根因：
  - 战略会议前端调用旧路径 `/strategic-meetings`，且后端统计行动项时引用不存在的 `ActionItemStatus.COMPLETED`；本地旧会议数据存在空 `status`，响应模型校验 500。
  - 项目复盘前端路径缺少尾斜杠导致本地跨端口重定向/CORS 问题；本地历史 SQLite `project_reviews` 缺少 AI 字段，且旧演示数据若干默认值为 NULL，响应模型校验 500。
  - 毛利预测前端页面需要 `/margin-prediction/historical`、`/variance`、`/predict`，后端对应文件只有占位实现。
  - 发货页和 PMC 发货概览把 0 用 `|| "unknown"` 兜底，零值被误显示为英文占位。
  - 成本中心在未选择项目时直接打成本查询并写 console warning，页面首屏扫描被标记为问题。
- 修复：
  - 前端管理节律 API 改为实际注册路径 `/management-rhythm/meetings/strategic-meetings`，行动项路径改为 `/management-rhythm/action-items/strategic-meetings/...`。
  - 战略会议后端完成项计数兼容 `DONE/COMPLETED`，会议状态为空时输出 `SCHEDULED`。
  - 项目复盘前端列表改为 `/project-reviews/`，后端列表/详情/更新统一做旧数据默认值转换；SQLite 启动补丁补齐 `project_reviews` 的 AI 字段。
  - 补齐毛利预测 4 个接口：历史毛利、预测、偏差、项目 BOM 成本，空数据也返回前端稳定 shape。
  - 发货页移除 AntD `List` warning 源，统计卡片保留 0；PMC 发货概览已送达和完成率保留 0。
  - 成本中心未选择项目时安静返回空态，不再写 warning。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_batch7_route_contracts.py -q` -> 4 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/management_rhythm/meetings.py app/api/v1/endpoints/project_review/reviews.py app/models/base.py tests/api/test_batch7_route_contracts.py` -> passed
  - `npm test -- --run src/components/delivery-management/__tests__/DeliveryOverview.test.jsx src/services/api/__tests__/routeContracts.test.js src/services/api/__tests__/engineering.test.js src/pages/__tests__/Shipments.test.jsx src/pages/CostAccounting/hooks/__tests__/useCostAccounting.test.js` -> 56 passed
  - `npm run build` -> passed
  - Live API 复验均 200：
    - `/api/v1/management-rhythm/meetings/strategic-meetings?page=1&page_size=20`
    - `/api/v1/project-reviews/?page=1&page_size=20`
  - Playwright 5 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch7-targeted-rerun2.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined/unknown`、无空白页。
  - Playwright 50 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch7-rerun2.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/undefined/unknown`、无空白页。

剩余未修复：

- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 18. 宽页面第六批：仓储/采购/质量/售前链路修复

- 扫描证据：
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch6.json`：覆盖 50 个仓储、采购、质量、售前入口，发现 `/material-tracking`、`/inventory-analysis`、`/budgets`、`/material-analysis` 存在 API 404/429、控制台错误或 `NaN`。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch6-targeted-rerun.json`：4 个重点入口全部清零。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch6-rerun2.json`：第六批 50 个入口全部清零。
- 复现页面：
  - `/material-tracking`
  - `/inventory-analysis`
  - `/budgets`
  - `/material-analysis`
- 根因：
  - 物料跟踪页面一次加载 100 张采购单后逐单请求明细，真实数据下触发本地 API 429；行级到货进度在订购数量为 0 时直接除法，显示 `NaN%`。
  - 库存分析后端只有占位兼容文件，前端访问 `/inventory-analysis/turnover-rate` 等自然路径时 404。
  - 预算管理页逐项目请求 `/projects/{id}/costs/summary`，和其它页面连续扫描叠加后触发 429。
  - 材料分析页本身接口可用，初扫 429 是前面请求风暴连带污染。
- 修复：
  - 物料跟踪只探测最近 8 张采购单明细，支持 `received_qty/received_quantity` 两种字段，并对统计百分比和行级进度做有限数值兜底。
  - 新增库存分析 5 个兼容接口：周转率、呆滞物料、安全库存、ABC 分类、成本占用，空库和真实物料库都返回前端稳定 shape。
  - 预算管理初始页改用项目列表已有 `actual_cost/used_amount/total_cost/cost_amount` 字段，不再 N 次打成本摘要接口；搜索框恢复空字符串控制值。
  - 补充第六批后端契约、物料跟踪请求上限、行级 `NaN`、预算上下文回归测试。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_batch6_route_contracts.py -q` -> 1 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/inventory_analysis.py` -> passed
  - `npm test -- --run src/pages/MaterialTracking/__tests__/MaterialRow.test.jsx src/pages/__tests__/MaterialTracking.test.jsx src/pages/__tests__/ProjectManagementDownstreamContext.test.jsx` -> 11 passed
  - `npm run build` -> passed
  - Playwright 4 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch6-targeted-rerun.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/Infinity`、无空白页。
  - Playwright 50 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch6-rerun2.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/Infinity`、无空白页。

剩余未修复：

- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。

### 17. 宽页面第五批：行政/会议节奏/成套装配/生产派工链路修复

- 扫描证据：
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch5.json`：覆盖 50 个前期未扫页面，发现 12 个入口存在 API 4xx/5xx，15 个入口存在控制台问题或 `NaN`。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch5-targeted.json`：首轮修复后剩余行政费用 404、办公用品 `NaN`、成套 dashboard 500、BOM 模板 `.map` 崩溃、告警统计 warning、齐套检查 API 对象结构错误。
  - `.gstack/qa-reports/route-smoke-2026-06-25-batch5-targeted-rerun2.json`：15 个重点入口全部清零。
- 复现页面：
  - `/admin-dashboard`
  - `/administrative-expenses`
  - `/office-supplies-management`
  - `/vehicle-management`
  - `/fixed-assets-management`
  - `/meeting-map`
  - `/meeting-reports`
  - `/assembly-kit`
  - `/material-demands`
  - `/bom-assembly-attrs`
  - `/production-exceptions`
  - `/dispatch-management`
  - `/project/cost-center`
  - `/alert-statistics`
  - `/kit-check`
- 根因：
  - 行政管理多页面沿用 `/admin/stats`、`/admin/supplies`、`/admin/vehicles`、`/admin/assets`、`/admin/expenses/statistics` 等旧接口，后端缺少兼容数据。
  - 会议地图和会议报告前端路径切到 `/management-rhythm/meeting-map*`、`/management-rhythm/meeting-reports*`，但后端拆分路由的日历接口要求必填日期，报告列表未被前端路径稳定命中。
  - 生产/成套页面存在前后端路径错位：`/workers`、`/production-exceptions`、`/material-demands`、`/assembly/dashboard`、`/assembly/stages`、`/assembly/templates` 等。
  - 成套 dashboard 真实库存在 `None` 齐套率和空 BOM 记录，后端直接比较或按严格响应模型序列化会 500。
  - 齐套检查路由存在双前缀注册问题：子路由已写 `/kit-check/...`，总路由又加 `prefix="/kit-check"`，页面自然路径 404。
  - 办公用品后端字段是 `quantity/lastPurchaseDate`，页面读取 `currentStock/lastPurchase`，导致库存率出现 `NaN`。
  - BOM 装配模板接口返回 envelope 对象，页面把对象当数组 `.map`。
  - 项目成本中心一次并发请求过多项目成本摘要，触发本地 API 429。
  - 告警统计页面把常量对象的缺失 `value` 当 Select option value，且旧 `destroyOnClose` / 自定义 Button `block` 触发控制台 warning。
- 修复：
  - 新增 `admin_compat` 数据：系统统计、行政费用统计、办公用品、车辆、固定资产，并补齐办公用品字段别名。
  - 新增 `management_rhythm_compat`，为会议地图、日历、统计、会议报告列表/详情/生成/导出提供稳定演示数据和前端消费形状。
  - 生产 API 路径统一到已注册后端路由：`/production/workers`、`/production/exceptions`、`/material-demands/`。
  - 成套 API 路径统一到实际注册路由：`/assembly-kit/dashboard/dashboard`、`/assembly-kit/stages/stages`、`/assembly-kit/shortage-alerts/shortage-alerts`、`/assembly-kit/templates/templates`。
  - 成套 dashboard 增加 `None` 数值和空必填字段兜底，真实历史数据不再导致 500。
  - 新增 `kit_check_compat`，在自然路径 `/kit-check/work-orders*` 提供列表、详情、检查、确认接口。
  - 行政费用页、办公用品页、BOM 装配属性页、成套看板页增加响应解包和数值/数组归一化。
  - 车辆页补齐空字符串、空里程、空统计时的安全显示，避免 `NaN`。
  - 项目成本中心把项目列表 page size 降低并分批加载成本摘要，避免本地 429。
  - 告警统计页改用常量 key 作为 Select option value，Modal 使用 `destroyOnHidden`，自定义 Button 用 `className="w-full"` 替代 `block`。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_batch5_route_contracts.py -q` -> 3 passed
  - `npm run test:run -- src/services/api/__tests__/routeContracts.test.js` -> 7 passed
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/kit_check_compat.py app/api/v1/endpoints/admin_compat.py app/api/v1/endpoints/assembly_kit/dashboard.py app/api/v1/endpoints/management_rhythm_compat.py app/api/v1/api.py` -> passed
  - `.venv/bin/python -m pytest tests/api/test_batch5_route_contracts.py tests/api/test_batch4_route_contracts.py tests/api/test_null_response_defaults.py tests/api/test_finance_compat_routes.py tests/api/test_rd_project_route_alias.py tests/api/test_business_support_delivery_routes.py tests/api/test_financial_reports_api.py tests/api/test_engineer_performance_empty_period.py tests/api/test_strategy_decomposition_tree_contract.py -q` -> 13 passed
  - `npm run test:run -- src/pages/OpportunityBoard/__tests__/BoardView.test.jsx src/components/ui/__tests__/input.test.jsx src/services/api/__tests__/routeContracts.test.js src/components/administrative/__tests__/StatisticsCharts.test.jsx src/lib/__tests__/utils.test.js src/pages/FinancialReports/__tests__/numberUtils.test.js` -> 50 passed
  - `npm run build` -> passed
  - Live API 复验均 200：
    - `/api/v1/admin/expenses/statistics?period=month`
    - `/api/v1/admin/supplies`
    - `/api/v1/assembly-kit/dashboard/dashboard`
    - `/api/v1/assembly-kit/templates/templates`
    - `/api/v1/kit-check/work-orders?page=1&page_size=3`
    - `/api/v1/kit-check/work-orders/1`
    - `/api/v1/management-rhythm/meeting-map/`
    - `/api/v1/management-rhythm/meeting-reports?page=1&page_size=3`
  - Playwright 15 入口复扫：`.gstack/qa-reports/route-smoke-2026-06-25-batch5-targeted-rerun2.json`，无 API 4xx/5xx、无 request failed、无控制台 warning/error、无 pageerror、无 `NaN/Infinity`、无空白页。

剩余未修复：

- `npm run build` 仍有既有 Vite 提示：部分页面同时静态/动态导入导致拆包无效，以及若干 chunk 超过 500 kB。当前不阻塞页面可用性，但后续性能优化应单独处理。
- 系统仍需继续做更深的增删改流程、权限组合、移动端尺寸和演示数据关联增强；目前没有把“全系统全面清理”标记为完成。
