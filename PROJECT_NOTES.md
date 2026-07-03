# PROJECT_NOTES

## 2026-07-03

- 根据桌面审计报告先做一轮小切口止血，未改 ROADMAP：
  - HR 员工与人事档案接口加权限：员工/档案读走 `hr:read`，员工创建/档案导入走 `hr:create`，员工/档案更新走 `hr:update`。
  - `init_api_permissions_data` 补 `hr:create/hr:update/hr:read_sensitive` 与 `bonus:read/bonus:distribute/bonus:pay/bonus:manage`，并给 `hr_manager/HR_MGR`、`FINANCE/FINANCE_MANAGER` 角色包补对应映射。
  - 奖金发放接口加权限：列表/详情走 `bonus:read`，创建发放走 `bonus:distribute`，确认付款走 `bonus:pay`；普通 `bonus:read` 用户只能看到自己的发放记录，跨用户详情返回 404。
  - 合同/验收/报价/ECN 撤回统一把 `engine.withdraw(... user_id=...)` 改为 `initiator_id=...`，并传 `comment=reason`，修复撤回 TypeError。
  - stub 定时任务从 `status="stub"` 改为 `status="not_implemented"`；调度器识别 `stub/not_implemented/error/failed` 返回为失败并记录 `record_job_failure`；所有仍落在 `stub_tasks` 的 enabled 调度项默认禁用，避免监控假成功。
- 新增/调整回归：
  - `tests/api/test_hr_bonus_permission_contracts.py`
  - `tests/unit/test_scheduler_utils.py::TestWrapJobCallable::test_not_implemented_result_records_failure`
  - 同步更新撤回和 stub 旧单测断言，避免继续固定错误行为。
- 本轮验证：
  - `.venv/bin/python -m pytest tests/api/test_hr_bonus_permission_contracts.py -q` -> 3 passed。
  - `.venv/bin/python -m pytest tests/audit_p0/test_p0_17_contract_withdraw_typeerror.py ... -q` -> 8 passed。
  - `.venv/bin/python -m pytest tests/audit_p0/test_p0_10_stub_tasks.py tests/unit/test_scheduled_stub_tasks.py tests/unit/test_j3_scheduled_tasks.py::TestStubTasks tests/unit/test_scheduler_utils.py::TestWrapJobCallable -q` -> 50 passed。
  - `.venv/bin/python -m pytest tests/api/test_hr_manager_role_contract.py -q` -> 2 passed。
  - `py_compile` 本轮触达 Python 文件 -> passed。
  - `ruff check` 本轮触达 Python/测试文件 -> passed。
  - enabled stub-backed scheduler scan -> `[]`。

## 2026-07-01

- 完成单独一轮“全前端路由页面巡检”：
  - 当前 route inventory 复核为 530 个路由，基准报告：`.gstack/qa-reports/all-frontend-route-sweep-20260701142722.json`。
  - 使用真实 Chromium（`QA_HEADLESS=0`）逐段打开页面并点击可见安全按钮，危险/破坏性/下载导出类动作继续跳过。
  - 最终覆盖审计：27 份干净报告覆盖 `originalPath -> route` 530/530，缺口 0，额外路由 0；累计安全点击 1293 次，跳过 164 次；`hardErrorCount/apiErrors/rateLimitErrors/pageErrors/requestFailures/hardConsoleErrors/click/load/errorBoundary/authFailure` 均为 0。
  - 收尾复跑补齐：
    - `/timesheet/dashboard` “同步数据”旧报告 404 已验证为当前代码已注册并可用；live API `POST /api/v1/timesheet/sync?year=2026&month=7&sync_target=all` 带 admin token 返回 200；单页报告 `.gstack/qa-reports/all-frontend-route-sweep-20260701141300.json` 干净。
    - `480-530` 最后一段完成：`.gstack/qa-reports/all-frontend-route-sweep-20260701141536.json`、`20260701141840.json`、`20260701142059.json`、`20260701142524.json` 全部硬错误 0。
    - 旧 `260-280` rate-limit 噪声已用 `.gstack/qa-reports/all-frontend-route-sweep-20260701142736.json` 复跑清零。
    - 旧 `400-420` rate-limit 噪声拆段复跑：`.gstack/qa-reports/all-frontend-route-sweep-20260701144151.json`、`20260701143510.json`、`20260701143601.json`、`20260701143822.json` 全部硬错误 0。
  - 本轮验证命令：
    - `python -m py_compile app/api/v1/endpoints/timesheet/sync.py app/api/v1/endpoints/timesheet/__init__.py app/services/timesheet/timesheet_sync_service.py` -> passed。
    - `.venv/bin/python -m pytest -q tests/api/test_batch12_route_contracts.py::test_timesheet_sync_route_is_registered_for_dashboard` -> passed。
    - `npm --prefix frontend run test:run -- src/services/api/__tests__/routeContracts.test.js --reporter=dot` -> 1 file passed，24 tests passed；保留既有未登录 token 警告和 Node `DEP0205` warning。
    - `node --check .gstack/qa-scripts/all-frontend-route-sweep.mjs` -> passed。
  - 工具侧小修：`.gstack/qa-scripts/all-frontend-route-sweep.mjs` 的弹层清理在页面已关闭时直接返回，避免巡检工具在页面/上下文关闭后中断；业务问题仍按报告中的 page/api/console/click 错误计数暴露。

- 继续交付验收中心 / 验收管理真实浏览器写入链路：
  - 新增真实浏览器脚本：`.gstack/qa-scripts/acceptance-management-sweep.mjs`。
  - 脚本通过 `admin/admin123` 登录，临时创建客户、项目、设备、SAT 模板和前置 FAT 完成单，然后从 `/delivery/acceptance-center?tab=acceptance` 真实 UI 创建 SAT 验收单。
  - 覆盖链路：SAT 验收单新建、开始验收、进入执行页、填写 2 个检查项、上报 1 个非阻断问题、完成验收、DB 复核、临时数据清理。
- 本轮真实浏览器发现并修复：
  - 新建验收记录缺少设备和检查模板选择，FAT/SAT 单据无法可靠带出项目设备和模板检查项。已补项目设备下拉、验收模板下拉、FINAL 类型、必填校验和可访问名称。
  - 项目设备接口遇到历史 NULL 数据 500：`MachineResponse` 对 `stage/status/health/progress_pct/machine_no` 增加旧数据默认值归一化。
  - 验收管理页 toast 调用方式错误，创建成功后会抛 `toast is not a function`，按钮卡在“创建中...”。已改为当前 UI toast API，并用 `finally` 收口提交态。
  - 验收记录列表缺少可见的“开始验收 / 执行验收”动作。已按状态补齐按钮，并接入开始接口与执行页跳转。
  - 执行页打开待检查项时默认仍为 `PENDING`，现场人员填了实际值也可能保存成待检查。已改为待检查项默认 `PASSED`，已保存的失败/不适用结果保持原值。
  - 执行页上报问题、完成验收、检查结果弹窗缺少 `DialogDescription`，真实浏览器 console 有 Radix warning。已补 `sr-only` 描述。
- 最终真实浏览器结果：
  - `.gstack/qa-reports/acceptance-management-sweep-20260701080500.json`
  - 9 steps 全部 passed；DB 状态复核为 `COMPLETED|PASSED|100|2|1`；`console=0`、`pageErrors=[]`、`requestFailures=[]`。
  - 清理复核：`customers/projects/machines/acceptance_orders` 中 `QA_ACCEPT_%` 残留均为 0。
- 本轮验证：
  - `npm --prefix frontend run test:run -- --reporter=dot pages/AcceptanceExecution/hooks/__tests__/useAcceptanceExecutionPage.test.js pages/AcceptanceManagement/__tests__/acceptance-management.test.jsx` -> 2 files passed，6 tests passed。
  - `pytest tests/schemas/test_project_machine.py -q` -> 1 passed；保留环境 warning。
  - `node --check .gstack/qa-scripts/acceptance-management-sweep.mjs` -> passed。
  - `python -m py_compile app/schemas/project/machine.py` -> passed。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入、chunk size 和 Node `DEP0205` warning。
  - `git diff --check -- <本轮相关文件>` -> passed。

- 继续生产管理模块真实浏览器写入链路验收：
  - 新增真实浏览器写入脚本：`.gstack/qa-scripts/production-full-crud-sweep.mjs`。
  - 通过登录页真实表单登录 `admin/admin123`，创建生产载体项目后，从生产管理模块完整跑车间、工人、生产计划、工单、移动端报工、报工审批和生产异常。
  - 覆盖写入链路：车间创建/编辑、工人创建/编辑、生产计划创建/提交审批/审批通过/发布、工单创建/派工、移动端开工/进度上报/完工报工、报工审批、生产异常上报/处理/关闭。
  - 覆盖只读入口：`/production/execution-center`、`/workshops/:id/task-board`、`/work-orders/:id`、`/production-board`、`/production/capacity-analysis`、`/production-dashboard`。
- 本轮真实浏览器发现并修复：
  - 生产计划页面只有“发布”按钮，缺少可见的“提交审批 / 审批通过 / 审批驳回”入口；后端实际已有 `submit/approve/publish` 三段状态流。已补齐列表和详情页状态动作，并新增 hook 回归测试覆盖提交审批和审批通过/驳回。
  - 车间、工人、工单、生产异常、报工等多个 Dialog 缺少 `DialogDescription`，真实浏览器 console 出现 Radix warning。已补齐对应描述。
  - 生产计划/工单筛选，以及移动端开工/任务筛选存在空值显示或传递 `unknown` 的问题。已改为空值显示正常、选择“全部”时清空筛选。
- 最终真实浏览器结果：
  - `.gstack/qa-reports/production-full-crud-sweep-20260701063533.json`
  - 12 steps / 0 failedSteps / 0 apiErrors / 0 pageErrors / 0 requestFailures / 0 consoleItems / 0 cleanupFailures。
  - 业务状态复核：生产计划 `PUBLISHED`，工单 `COMPLETED`，3 条报工 `APPROVED`，生产异常 `CLOSED`。
  - 清理确认：project 105、workshop 5、worker 6、production plan 81、work order 52、work reports 4/5/6、production exception 28 均已删除；SQLite 复核本轮 `QA_PROD_20260701063533%` 在 `projects`、`workshop`、`worker`、`production_plan`、`work_order`、`production_exception` 残留均为 0。
- 本轮验证：
  - `node --check .gstack/qa-scripts/production-full-crud-sweep.mjs` -> passed。
  - `npm --prefix frontend run test:run -- --reporter=dot ProductionPlanList/hooks/__tests__/useProductionPlanList.test.js WorkOrderManagement.test.jsx WorkshopManagement.test.jsx ProductionModuleSmoke.test.jsx` -> 4 files passed，22 tests passed；保留 mocked API 测试里的预期错误日志和 Node `DEP0205` warning。
  - `QA_HEADLESS=0 QA_ROOT=http://127.0.0.1:5173 node .gstack/qa-scripts/production-full-crud-sweep.mjs` -> passed。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入、chunk size 和 Node `DEP0205` warning。

- 复跑真实浏览器项目按钮流：
  - `node .gstack/qa-scripts/project-button-flow.mjs` -> passed。
  - QA 报告：`.gstack/qa-reports/project-button-flow-20260630231732.json`。
  - 截图：`.gstack/qa-reports/screenshots/project-button-flow-final-20260630231732.png`。
  - 报告要点：项目 ID `103`，脚本执行 `16` 步；成员、任务、成本、阶段启动/完成、交付排产均通过真实 UI/接口组合提交；`apiErrors/pageErrors/requestFailures` 均为空；成本 ID `62` 删除返回 204，临时项目删除返回 200。
- 继续做项目总览数据流转 API smoke：
  - 临时项目：`QA_DATA_FLOW_20260701072006` / `PJ263C9788A`，项目 ID `104`。
  - 补齐 S4/S5 任务、里程碑，并种入本链路所需 BOM 表头与物料行后，依次实跑：
    - `POST /projects/104/data-flow/wbs-work-orders` -> 200，创建工单 `2` 条。
    - `POST /projects/104/data-flow/bom-purchase-requests` -> 200，创建采购申请 ID `27`。
    - `POST /projects/104/data-flow/delivery-schedule` -> 200，创建交付排产 ID `7`。
    - `POST /projects/104/data-flow/after-sales` -> 200，创建 `1/3/6/12` 个月售后保养记录 `4` 条。
  - DB 复核：`work_orders=2`、`purchase_requests=1`、`delivery_schedules=1`、`after_sales_maintenance=4`；`DATA_FLOW_FAILED=` 为空。
  - 已清理工单、采购申请、交付排产、BOM、任务、里程碑、售后保养记录，并 `DELETE /projects/104` -> 200。
- 收尾复验：
  - 触达文件行尾空白扫描无命中；代码差异 `git diff --check` 通过。
  - `npm run test:run -- src/services/api/__tests__/routeContracts.test.js src/services/api/__tests__/projects.test.js src/components/project/__tests__/ProjectFormStepper.test.jsx src/pages/__tests__/ProgressForecast.test.jsx` -> passed。
  - `.venv/bin/python -m pytest tests/api/test_progress.py::TestProjectTasks::test_create_project_task_via_project_compat_route tests/core/test_database.py::TestSQLiteSchemaPatches::test_requirement_extraction_patch_creates_required_tables -q` -> 2 passed。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/progress_compat.py app/models/base.py` -> passed。
  - `npm run build` -> passed；保留既有 Vite 动静态重复导入、chunk size 和 Node `DEP0205` warning。
- 当前剩余：
  - 项目总览页数据流转按钮还可继续补真实浏览器点击证据；审批/评价、角色权限组合、移动端尺寸仍待扫。
  - 不能宣称全系统无 bug；当前只是项目主链路和关键数据流转链路的阶段性清零。

## 2026-06-30

- 当前运行态：后端 `127.0.0.1:8002` 健康检查 200，前端 Vite dev `127.0.0.1:5173` 可访问。前面一次超时 Playwright 留下的 `127.0.0.1:4173` preview 已清理。
- 本轮先按项目主链路做基线验证：
  - `.venv/bin/python -m pytest -q tests/e2e/test_project_lifecycle.py::TestProjectLifecycleE2E::test_complete_project_lifecycle_from_s1_to_s9 -q` -> passed
  - `.venv/bin/python -m pytest -q tests/api/test_project_manager_self_service_contract.py tests/api/test_project_workspace_contract_api.py tests/api/test_project_milestones_api.py -q` -> 30 passed, 1 skipped
- 发现并修复前端项目创建弹窗加载基础选项失败：
  - 复现：`/projects` 点击 `新建项目` 后提示 `无法加载客户和员工数据`，浏览器报 `stage-templates` 307 redirect 后 CORS。
  - 根因：`stageViewsApi.templates.list()` 调用 `/stage-templates`，后端集合路由真实注册为 `/stage-templates/`，无尾斜杠会被 FastAPI 307 到后端绝对地址，绕开 Vite proxy。
  - 修复：`frontend/src/services/api/stageViews.js` 改为 `/stage-templates/`。
  - 回归：`frontend/src/services/api/__tests__/routeContracts.test.js` 增加 `uses non-redirecting stage template collection route for project creation`。
  - 验证：红测先失败，修复后 targeted test passed；完整 `npm run test:run -- src/services/api/__tests__/routeContracts.test.js` -> 22 passed；`npm run build` -> passed。
  - 浏览器复验：`/projects` 点击 `新建项目` 后表单可打开，无 `无法加载客户和员工数据` toast，无 stage-template CORS。截图：`.gstack/qa-reports/screenshots/project-center-create-after-stage-template-fix.png`。
- 修复 `scripts/smoke_auth_api.sh` 的缺料预警假红：
  - 旧脚本请求废弃路径 `/api/v1/shortage-alerts/`，当前产品页和后端注册路径为 `/api/v1/shortage/detection/alerts`。
  - 修复后运行 `BASE_URL=http://127.0.0.1:8002 bash scripts/smoke_auth_api.sh --no-seed --no-start --base-url http://127.0.0.1:8002 --user admin --password admin123` -> passed。
- 继续深挖项目创建弹窗，修复两处提交阻塞：
  - 复现：输入全新项目编码后仍提示 `项目编码已存在，请使用其他编码`。
  - 根因：前端调用 `projectApi.list({ project_code })`，但后端列表接口不支持 `project_code` 精确过滤；参数被忽略后返回第一页任意项目，前端只看列表非空就误判重复。
  - 修复：改为使用后端已有 `keyword` 查询，再在前端按 `project_code` 做精确相等判断。
  - 复现：进入最后一步提交后，`POST /api/v1/projects/` 返回 422，提示空字符串不是合法 date / integer。
  - 根因：表单把可选日期和可选整数字段的空值按 `""` 提交，后端 schema 期望 `null` 或合法值。
  - 修复：新增 `normalizeProjectFormData()`，提交前把可选数值/日期归一为 `null`，金额空值归一为 `0`。
  - 同步补齐 `DialogDescription` 的 `sr-only` 可访问性描述，清掉 Radix `DialogContent` warning。
  - 回归：`frontend/src/components/project/__tests__/ProjectFormStepper.test.jsx` 覆盖“非精确 keyword 命中不误判重复”和“空可选字段提交前归一化”。
- 额外确认：
  - `/shortage-alerts` 页面登录态访问正常，无 API failure。截图：`.gstack/qa-reports/screenshots/shortage-alerts-current-auth.png`。
  - 真实浏览器创建项目干净跑通：`QA_E2E_CLEAN_20260630123113` / `PJ260630123113` 创建成功，项目 ID `86`，`stage_template_id=1`；随后 `DELETE /api/v1/projects/86` 返回 200，再查详情 `is_active=false`。本次 Playwright 捕获事件为空数组 `[]`，无 console error/warning、pageerror、requestfailed 或 API 4xx/5xx。
  - `npm run test:run -- src/components/project/__tests__/ProjectFormStepper.test.jsx src/services/api/__tests__/routeContracts.test.js` -> 2 files passed, 24 tests passed。
  - `npm run build` -> passed，仅保留既有 Vite 动静态重复导入和 chunk size 提示。
  - 旧 `e2e/project-management.spec.js` 仍按 AntD table 旧页面结构等待 `.ant-table, table`，当前项目中心已改为卡片 UI，测试会超时；这是测试漂移，不作为本轮产品缺陷结论。
- 继续跑“项目创建后子页矩阵”，修复两处深层问题：
  - 复现：新建项目 ID `87` 后访问 `/projects/87/engineer-recommendation`，`GET /api/v1/requirement-extraction/projects/87/requirements` 返回 500；完整异常为 `sqlite3.OperationalError: no such table: project_requirements`。
  - 修复：`app/models/base.py::_ensure_sqlite_schema()` 把 `app.models.project_requirements` 纳入可选历史表补建，旧 SQLite 会自动创建 `project_requirements` 与 `engineer_recommendations`。
  - 回归：`tests/core/test_database.py::TestSQLiteSchemaPatches::test_requirement_extraction_patch_creates_required_tables` 覆盖缺表旧库补建。
  - 复现：`/projects/87/progress-forecast` 中项目详情请求用裸 `fetch('/api/v1/projects/:id')`，不带 Authorization，受保护页面内出现 401 `MISSING_TOKEN`。
  - 修复：`frontend/src/pages/ProgressForecast.jsx` 改用已有 `projectApi.get(id)`，走统一认证 API client。
  - 回归：`frontend/src/pages/__tests__/ProgressForecast.test.jsx` 断言使用 `projectApi.get()` 且不调用 `global.fetch`。
- 深层矩阵复验：
  - 新建项目 `QA_FLOW_RERUN_20260630124142` / `PJ260630124142`，项目 ID `88`，初始化阶段后依次打开 25 个项目子页：详情 tabs、workspace、tasks、timeline、milestones、progress-report、progress-board、progress-forecast、dependency-check、milestone-rate、delay-reasons、material-progress、schedule-generation、schedule-optimization、engineer-recommendation、engineer-workload-board、overview-dashboard、delivery、roles、contributions。
  - 结果：`events: []`，无 console error/warning、pageerror、requestfailed 或 API 4xx/5xx；截图：`.gstack/qa-reports/screenshots/project-flow-route-matrix-QA_FLOW_RERUN_20260630124142.png`。
  - 清理：`DELETE /api/v1/projects/88` -> 200。
  - 组合回归：`npm run test:run -- src/components/project/__tests__/ProjectFormStepper.test.jsx src/services/api/__tests__/routeContracts.test.js src/pages/__tests__/ProgressForecast.test.jsx` -> 3 files passed, 25 tests passed。
  - 后端回归：`.venv/bin/python -m pytest tests/core/test_database.py::TestSQLiteSchemaPatches::test_requirement_extraction_patch_creates_required_tables -q` -> passed；`.venv/bin/python -m py_compile app/models/base.py app/api/v1/endpoints/requirement_extraction.py` -> passed。
  - `npm run build` -> passed，仅保留既有 Vite 动静态重复导入和 chunk size 提示。
- 继续做“项目创建后按钮级写操作” smoke，修复成员/任务两条阻塞：
  - 初扫新建临时项目 ID `89` 后，`POST /api/v1/members/` -> 404，`POST /api/v1/projects/89/tasks` -> 405。
  - 根因 1：`memberApi.add()` 仍打旧顶层 `/members/`，并发送旧字段 `role`；当前后端真实路由是 `/projects/{project_id}/members/`，字段为 `role_code`。
  - 根因 2：`progress_compat.py` 只提供项目任务列表 GET，缺少项目任务页实际调用的 `POST /projects/{project_id}/tasks`。
  - 修复：`frontend/src/services/api/projects.js` 的 `memberApi.add()` 改为项目内路由并兼容 `role -> role_code`；`app/api/v1/endpoints/progress_compat.py` 新增项目任务创建兼容 POST。
  - 回归：`frontend/src/services/api/__tests__/routeContracts.test.js`、`frontend/src/services/api/__tests__/projects.test.js` 覆盖成员新增路径/payload；`tests/api/test_progress.py::TestProjectTasks::test_create_project_task_via_project_compat_route` 覆盖创建任务后列表读回。
  - Live API smoke：新建 `QA_BUTTON_20260630205940` / `PJ26AF42BEA`，项目 ID `90`，完成新增成员、创建任务、任务列表读回、阶段初始化/启动/完成、成本创建/查询；`SMOKE_FAILED=` 为空；最后 `DELETE /api/v1/projects/90` -> 200 清理。
  - 组合验证：前端 4 个测试文件 passed；后端 2 个目标测试 passed；`py_compile app/api/v1/endpoints/progress_compat.py app/models/base.py` passed。
- 剩余待扫：
  - 继续做交付排产、项目数据流转、售后转交、审批/评价等业务写入链路，以及用真实浏览器点击表单补 UI 层证据。
  - 系统还不能宣称全量无 bug。

## 2026-06-30 继续：项目按钮级流程

- 已补齐真实浏览器按钮流脚本：`.gstack/qa-scripts/project-button-flow.mjs`。
  - 登录后写入真实 token 到 localStorage，走 UI 创建项目、选择阶段模板、选择客户、填写金额/周期并提交。
  - 创建后通过项目详情按钮添加成员，通过任务页按钮新建任务，通过成本核算页按钮录入成本，通过项目阶段时间轴按钮启动并完成阶段，通过交付页按钮创建排产计划。
  - 阶段操作不再只看旧 DOM：点击 `开始` / `完成` 时等待对应 `/projects/{id}/stages/{stage_id}/start|complete` 接口响应，并用 `/projects/{id}/stages/views/timeline?include_nodes=true` 断言 `PENDING -> IN_PROGRESS -> COMPLETED`。
- 发现并修复后端创建项目时的真实缺口：
  - 复现：带 `stage_template_id` 创建项目后，旧状态阶段会初始化，但当前时间轴使用的 `ProjectStageInstance` 未初始化，导致项目阶段视图没有可推进阶段。
  - 修复：`app/services/project_crud/service.py` 在创建项目并执行旧 `init_project_stages()` 后，如果存在 `stage_template_id`，调用 `StageInstanceService.initialize_project_stages(project.id, template_id, planned_start_date)` 并刷新项目。
  - 回归：`tests/api/test_projects.py::TestProjectCRUD::test_create_project_with_stage_template_initializes_stage_instances` 覆盖带模板创建后能查到阶段实例，且数据库持久化计数正确。
- 发现并修复成本核算页真实缺口：
  - 复现：`/costs?project_id={id}` 点击 `录入成本` 后，空项目没有项目选项；即使打开弹窗，`保存` 也只是关闭弹窗，不会调用 `/projects/{id}/costs/`。
  - 修复：`frontend/src/pages/CostAccounting.jsx` 增加当前项目选项、受控成本表单、保存校验和 `costApi.create(projectId, payload)`；`frontend/src/pages/CostAccounting/hooks/useCostAccounting.js` 改为直接从 `services/api/projects.js` 导入 `costApi`，避免总入口未导出导致带项目筛选时失败。
  - 回归：新增 `frontend/src/pages/__tests__/CostAccounting.test.jsx` 覆盖当前项目上下文录入成本；同步更新 `frontend/src/pages/CostAccounting/hooks/__tests__/useCostAccounting.test.js` mock 路径。
- 本轮验证：
  - `node .gstack/qa-scripts/project-button-flow.mjs` -> passed。
  - QA 报告：`.gstack/qa-reports/project-button-flow-20260630133626.json`。
  - 截图：`.gstack/qa-reports/screenshots/project-button-flow-final-20260630133626.png`。
  - 报告要点：项目 `QA_BTN_20260630133626` / ID `102`，阶段实例数 `22`，成本 ID `62` 通过 UI 创建并在清理时删除，阶段 `S01 市场开拓` 已通过 UI `开始` 并 `完成`；成员、任务、成本、交付排产均提交成功；`apiErrors/pageErrors/requestFailures` 均为空；成本记录删除返回 204，临时项目删除返回 200。
  - `npm run test:run -- src/pages/__tests__/CostAccounting.test.jsx src/pages/CostAccounting/hooks/__tests__/useCostAccounting.test.js` -> 2 files passed, 3 tests passed。
  - `.venv/bin/python -m pytest tests/api/test_projects.py::TestProjectCRUD::test_create_project_with_stage_template_initializes_stage_instances tests/api/test_projects.py::TestProjectCRUD::test_create_project_success tests/api/test_projects.py::TestProjectCRUD::test_create_project_auto_init_stage -q` -> 3 passed；保留既有 pytest warning：`test_create_project_success` 返回了 dict。
  - `npm run build` -> passed；保留既有 Vite 动静态重复导入和 chunk size 提示。
- 当前结论：本轮指定的“创建项目 -> 推进阶段启动/完成 -> 新建任务/成员/成本/交付操作提交”按钮级路径已跑通。系统仍不能宣称全量无 bug，但这条主流程已有脚本化复验。

## 2026-06-30 继续：project_costs 业务单据归集

- 实现统一成本归集服务：`app/services/cost/cost_collection_service.py` 新增 `collect_project_costs()`，批量扫描并 upsert 到 `project_costs`：
  - 采购订单：`PurchaseOrder`，状态 `RECEIVED/COMPLETED/SHIPPED`，来源 `PURCHASE / PURCHASE_ORDER`，材料采购成本。
  - 已发布 BOM：`BomHeader/BomItem`，状态 `RELEASED`，来源 `BOM / BOM_COST`，按 BOM 明细金额汇总，表头总额大于 0 时优先用表头总额。
  - 生产工单：`WorkOrder`，状态 `COMPLETED/IN_PROGRESS`，来源 `PRODUCTION / WORK_ORDER`，按实际工时优先、标准工时兜底，默认 `200 元/小时` 估算人工/加工成本。
  - 已审批工时：`Timesheet`，状态 `APPROVED`，来源 `TIMESHEET / LABOR_COST`，按项目+人员汇总，时薪走 `HourlyRateService`。
- 同步改造 `/api/v1/cost-collection/collect`：从 raw SQL 直接插表改为调用统一服务；`/status` 和 `/by-project` 同步识别采购、BOM、工单、工时四类来源。
- 增加旧路径兼容：`app/services/cost_collection_service.py` 作为 `app.services.cost.cost_collection_service` 的模块别名，兼容旧单测和老导入。
- 新增回归：
  - `tests/services/test_cost_collection_business_docs.py` 覆盖采购 + BOM + 工单 + 工时采集、金额、来源口径和重复采集不重复插入。
  - `tests/api/test_cost_collection_collect_api.py` 覆盖真实 `/cost-collection/collect` 路由能落 `project_costs`。
- 本轮验证：
  - `.venv/bin/python -m pytest tests/services/test_cost_collection_business_docs.py tests/api/test_cost_collection_collect_api.py tests/api/test_batch4_route_contracts.py::test_finance_cost_analysis_routes_are_registered tests/unit/test_cost_collection_service_coverage.py tests/unit/test_cost_collection_n3.py -q` -> 44 passed。
  - `.venv/bin/python -m ruff format app/services/cost/cost_collection_service.py app/services/cost_collection_service.py app/api/v1/endpoints/cost_endpoints/collection.py tests/services/test_cost_collection_business_docs.py tests/api/test_cost_collection_collect_api.py` -> formatted。
  - `.venv/bin/python -m ruff check app/services/cost/cost_collection_service.py app/services/cost_collection_service.py app/api/v1/endpoints/cost_endpoints/collection.py tests/services/test_cost_collection_business_docs.py tests/api/test_cost_collection_collect_api.py` -> passed。
  - `.venv/bin/python -m py_compile app/services/cost/cost_collection_service.py app/services/cost_collection_service.py app/api/v1/endpoints/cost_endpoints/collection.py tests/services/test_cost_collection_business_docs.py tests/api/test_cost_collection_collect_api.py` -> passed。

## 2026-06-30 继续：project_costs 计划/实际成本口径

- 修复成本归集后的双算风险：
  - `project_costs` 新增 `cost_basis`，默认 `ACTUAL`；`BOM / BOM_COST` 写入 `PLAN`，采购、外协、ECN、生产工单、工时人工写入 `ACTUAL`。
  - `Project.actual_cost` 统一只按 `ACTUAL` 成本重算；BOM 作为计划/估算成本保留在 `project_costs`，但不进入项目实际成本、预算执行、利润分析、成本 dashboard 的实际成本汇总。
  - 旧 SQLite 补丁会给 `project_costs` 补 `cost_basis` 列，并把历史 `source_type=BOM_COST` 或 `source_module=BOM` 的记录标记为 `PLAN`。
  - `/cost-collection/by-project` 返回 `actual_cost/plan_cost`，其中旧字段 `total_cost` 保持实际成本口径，避免前端利润/预算继续把 BOM 计划成本当发生额。
  - 继续补齐 `BudgetAnalysisService`、财务报表 `/finance/*`、结算兼容页、成本复盘和项目复盘 AI 里的实际成本汇总，避免它们直接全量相加 `ProjectCost.amount`。
  - 顺手修复财务报表旧双算：`_project_cost_total()` 不再把 `Project.actual_cost` 和同项目 `project.costs` 再叠加一次；有 `Project.actual_cost` 时优先视为项目实际成本汇总，`FinancialProjectCost` 另计。
- 新增/调整回归：
  - `tests/services/test_cost_collection_business_docs.py` 覆盖采购 1000 + BOM 500 + 工单 500 + 工时 300 的混合采集：`total_amount=2300`，但项目 `actual_cost=1800`；同时验证删除 BOM 计划成本不影响实际成本。
  - 同一真实 DB 用例同步断言 `CostService`、`BudgetAnalysisService`、`finance_reports._project_cost_total()`、`settlements._project_cost_totals()` 都只汇总 1800 的实际成本。
  - 旧 mock 分支测试改为验证触发实际成本重算，而不是继续断言直接加减 `Project.actual_cost`。
  - `BudgetAnalysisService` 补回实例式兼容入口：`BudgetAnalysisService(db).get_budget_execution_analysis(project_id)` 与原来的 `BudgetAnalysisService.get_budget_execution_analysis(db, project_id)` 均可用。
- 本轮验证：
  - `.venv/bin/python -m ruff check ...` 成本口径相关 26 个 Python 文件 -> passed。
  - `.venv/bin/python -m py_compile ...` 成本口径相关 26 个 Python 文件 -> passed。
  - `.venv/bin/python -m pytest tests/services/test_cost_collection_business_docs.py tests/unit/test_cost_collection_service_coverage.py tests/unit/test_cost_collection_n3.py tests/api/test_cost_collection_collect_api.py tests/api/test_batch4_route_contracts.py::test_finance_cost_analysis_routes_are_registered tests/unit/test_cost_forecast_branches.py::TestCostCollectionOutsourcingOrder tests/unit/test_cost_forecast_branches.py::TestCostCollectionECN tests/unit/test_cost_forecast_branches.py::TestCostCollectionBOM tests/unit/test_cost_forecast_branches.py::TestCostCollectionRemove -q` -> 58 passed。
  - `.venv/bin/python -m pytest tests/unit/test_budget_analysis_service.py tests/unit/test_budget_analysis_service_coverage.py tests/unit/test_budget_analysis_deep.py -q` -> 17 passed。
  - `.venv/bin/python -m pytest tests/api/test_financial_reports_api.py tests/api/test_finance_compat_routes.py -q` -> 3 passed。
  - `.venv/bin/python -m pytest tests/unit/test_review_report_generator.py::TestProjectReviewReportGenerator::test_extract_project_data_with_costs tests/unit/test_cost_review_service_coverage.py -q` -> 2 passed。

## 2026-07-01 继续：销售模块真实浏览器按钮验收

- 新增真实浏览器按钮巡检脚本：`.gstack/qa-scripts/sales-button-sweep.mjs`。
  - 通过登录页真实表单登录 `admin/admin123`，使用 Chromium 逐页访问销售相关页面。
  - 只点击主内容区 `main button`，并跳过删除、提交、审批、保存、立项、导入导出、收款等会写业务数据或外发文件的危险动作。
  - 将 API 4xx/5xx、pageerror、requestfailed、React ErrorBoundary/console hard error、点击失败分别计入报告；429 限流单独统计，避免和真实崩溃混淆。
- 本轮真实浏览器发现并修复：
  - 客户列表点击“记录沟通”进入客户 360 时，`/api/v1/sales/customer-360/customers/{id}/360-view` 500；根因是 `Opportunity` 字段误用 `name/win_rate`，实际为 `opp_name/probability`。修复：`app/api/v1/endpoints/customer_360.py`。
  - 智能报价“历史价格”请求 404；根因是旧 API client 仍打 `/intelligent-quote/historical-prices`。修复：`frontend/src/services/api/intelligentQuote.js` 改为 `/sales/quotes/historical-prices`，参数改为 `product_category`。
  - 智能报价接口修复后出现 React ErrorBoundary：页面未解包 axios/unified response，直接读取 `price_range.min`。修复：`frontend/src/pages/SalesAI/IntelligentQuote.jsx` 增加响应解包和字段兜底。
  - 支付管理概览页出现 React ErrorBoundary：账龄/催收图表把 key 当天数字段再传给 `getAgingPeriod()`，且催收配置无 `color`。修复：`frontend/src/components/payment-management/PaymentStatsOverview.jsx` 增加安全图表颜色和账龄 key 反查。
  - 销售团队弹窗触发 React key warning。修复：`frontend/src/pages/SalesTeam/CreateTeamDialog.jsx` 负责人选项使用复合 key 并跳过缺 id 成员。
- 真实浏览器最终去重汇总：
  - 覆盖 50 个销售相关页面，主内容区安全按钮点击 250 次，危险/禁用/不可见动作跳过 74 次。
  - 去重后的最终结果：`hard=0`，`rate=0`，无 API 硬错误、无页面异常、无点击失败、无 console hard error。
  - 最终证据报告：
    - `.gstack/qa-reports/sales-button-sweep-20260701014412.json`（0-4 段；其中工作台/漏斗连续扫触发过限流，已单独干净复跑）
    - `.gstack/qa-reports/sales-button-sweep-20260701015536.json`（销售工作台单页复跑）
    - `.gstack/qa-reports/sales-button-sweep-20260701015626.json`（销售漏斗单页复跑）
    - `.gstack/qa-reports/sales-button-sweep-20260701014710.json`（5-9 段）
    - `.gstack/qa-reports/sales-button-sweep-20260701014930.json`（10-19 段）
    - `.gstack/qa-reports/sales-button-sweep-20260701012937.json`（20-29 段）
    - `.gstack/qa-reports/sales-button-sweep-20260701015257.json`（30-39 段）
    - `.gstack/qa-reports/sales-button-sweep-20260701013453.json`（40-49 段）
- 本轮验证：
  - `python -m py_compile app/api/v1/endpoints/customer_360.py` -> passed。
  - `node --check .gstack/qa-scripts/sales-button-sweep.mjs` -> passed。
  - `npm --prefix frontend run test:run -- IntelligentQuoteSidebar.test.jsx` -> passed。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入和 chunk size 提示。
  - Live API：`GET /api/v1/sales/customer-360/customers/108/360-view` -> 200，返回 active opportunity。
  - Live browser：`/sales/customers`、`/sales/quotes`、`/sales/intelligent-quote`、`/payments`、`/sales/team` 修复后单页复跑均为 0 硬错误。

## 2026-07-01 继续：售前技术支持模块真实浏览器按钮验收

- 新增真实浏览器按钮巡检脚本：`.gstack/qa-scripts/presales-button-sweep.mjs`。
  - 覆盖售前统一工作台、执行/经理工作台、统一售前技术支持中心、需求调研、投标、知识库、模板、技术参数、票板，以及销售/项目侧旧入口重定向。
  - 通过登录页真实表单登录 `admin/admin123`，使用 Chromium 逐页访问；只点击主内容区 `main button`，跳过删除、提交、审批、保存、立项、导入导出、投标结果、转项目等危险动作。
  - 将 API 4xx/5xx、pageerror、requestfailed、console hard error、点击失败和登录失败分别落入报告；429 限流单独统计。
- 本轮真实浏览器发现并修复：
  - `/knowledge-base` 点击“创建文档/上传文档”等按钮时，浏览器 console 出现 Ant Design warning：`useForm` 未连接到 Form，以及 `message` 静态方法无法消费主题上下文。
  - 修复：`frontend/src/pages/KnowledgeBase.jsx` 改用 `message.useMessage()` + `messageContextHolder`，创建/编辑文档弹窗改为 `forceRender`，避免隐藏 Modal 中的 form 实例未挂载时被调用。
- 真实浏览器最终去重汇总：
  - 覆盖 31 个售前相关入口，主内容区安全按钮点击 190 次，危险/不可见动作跳过 6 次。
  - 去重后的最终结果：`hard=0`，`rate=0`，无 API 硬错误、无页面异常、无点击失败、无 requestfailed、无 console hard error。
  - 最终证据报告：
    - `.gstack/qa-reports/presales-button-sweep-20260701023407.json`（0-3 段）
    - `.gstack/qa-reports/presales-button-sweep-20260701023444.json`（4-13 段）
    - `.gstack/qa-reports/presales-button-sweep-20260701023757.json`（14-20 段；原 `/knowledge-base` warning 已由后续修复复跑覆盖）
    - `.gstack/qa-reports/presales-button-sweep-20260701024221.json`（21-30 段）
    - `.gstack/qa-reports/presales-button-sweep-20260701024552.json`（`/knowledge-base` 修复后单页复跑，0 console）
- 本轮验证：
  - `node --check .gstack/qa-scripts/presales-button-sweep.mjs` -> passed。
  - `QA_HEADLESS=0 QA_ROUTE_FILTER=knowledge-base QA_BUTTON_LIMIT=8 ... node .gstack/qa-scripts/presales-button-sweep.mjs` -> passed，4 clicks / 4 skipped / 0 hard errors / 0 console。
  - `npm --prefix frontend run test:run -- presalesRoutes.test.jsx salesPresaleWorkbenchRoutes.test.jsx projectPresalesTaskRoutes.test.jsx` -> 3 files passed，19 tests passed；保留既有 Node `module.register()` deprecation warning。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入和 chunk size 提示。

## 2026-07-01 继续：销售模块真实浏览器写入链路验收

- 新增真实浏览器写入脚本：`.gstack/qa-scripts/sales-full-crud-sweep.mjs`。
  - 通过登录页真实表单登录 `admin/admin123`，从销售开始完整跑：客户创建/删除、客户主流程创建、线索创建/编辑/跟进/转商机、报价创建、合同创建、发票草稿创建/删除、发票创建/开票/收款。
  - 每轮自动追踪创建的 customer/lead/opportunity/quote/contract/invoice，并按逆序清理；已开票/已收款发票先清回款、转草稿，再删除，避免留下 QA 数据。
- 本轮真实浏览器发现并修复：
  - 客户列表行操作菜单“删除”未真正接入删除回调，且行点击会抢掉菜单点击。修复客户列表删除回调和 action 单元格事件阻止冒泡。
  - 线索跟进发送空 `next_action_at` 导致 422。修复为空时不提交该字段。
  - 线索快速转商机被 G1 校验硬拦。修复为先提示“快速转商机会跳过完整 G1 模板”，确认后带 `skip_validation=true` 转换。
  - 线索/商机页客户下拉只加载 100 条，新建 QA 客户选不到。修复为加载 1000 条。
  - 发票创建/编辑/开票弹窗 prop 命名与页面传参不一致，真实页面无法提交/更新表单。修复弹窗同时兼容 `onFormChange/onSubmit` 与旧命名。
  - 发票“删除”用更新 `VOID` 冒充删除；后端已有 draft DELETE。新增 `invoiceApi.delete()`，页面删除改用真正 DELETE。
  - 合同页进入后对全部合同并发加载应收汇总/收款计划，触发 429，导致合同创建下拉被打空。修复为只对首屏 10 条合同补履约状态。
  - AntD `message` 静态调用在合同创建后产生主题上下文 warning。根组件增加 AntD `App` provider，合同编辑器改用 `App.useApp()` 的 message 实例。
- 最终真实浏览器结果：
  - `.gstack/qa-reports/sales-full-crud-sweep-20260701033959.json`
  - 11 steps / 0 failedSteps / 0 apiErrors / 0 pageErrors / 0 requestFailures / 0 consoleItems / 0 cleanupFailures。
  - 清理确认：invoice 100 reset-and-deleted，contract 117 deleted，quote 276 deleted，opportunity 251 deleted，lead 195 deleted，customer 111 deleted。
- 本轮验证：
  - `node --check .gstack/qa-scripts/sales-full-crud-sweep.mjs` -> passed。
  - `npm --prefix frontend run test:run -- ContractManagement.test.jsx InvoiceManagement.test.jsx sales.test.js` -> 4 files passed，77 tests passed（Vitest 还匹配到 presales API 测试）。
  - `npm --prefix frontend run test:run -- ContractManagement.test.jsx` -> 9 tests passed。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入和 chunk size 提示。

## 2026-07-01 继续：售前技术支持模块真实浏览器写入链路验收

- 新增真实浏览器写入脚本：`.gstack/qa-scripts/presales-full-crud-sweep.mjs`。
  - 通过登录页真实表单登录 `admin/admin123`，使用 Chromium 从售前技术支持开始跑创建、编辑、审批/完成、评分和清理链路。
  - 覆盖工作台角色/资产入口导航、需求调研创建、售前工单创建、工单接单/交付物/审批/进度/完成/评分、方案创建并提交评审、技术参数模板创建/编辑/估算/删除、投标创建并进入成本支持、知识模板预览/应用/评分。
  - 测试数据统一使用 `QA_PRESALE_20260701035838` 前缀，脚本在 `finally` 中按依赖顺序清理 `presale_solution_cost`、`presale_solution`、`presale_tender_record`、`presale_ticket_progress`、`presale_ticket_deliverable`、`presale_support_ticket`、`technical_parameter_templates`、`presale_solution_template`。
- 本轮真实浏览器发现：
  - 最终业务链路未发现新的产品阻断 bug。
  - 前几轮失败来自脚本定位/测试边界：方案子 tab locator、技术参数模板分页上限、知识模板搜索/评分定位；均已修正到脚本中。
  - 单测因 `KnowledgeBase.jsx` 已改为 `message.useMessage()`，测试 mock 缺少该方法而失败；修复：`frontend/src/pages/__tests__/KnowledgeBase.test.jsx` 补 `useMessage` mock 和 `messageContextHolder`。
- 最终真实浏览器结果：
  - `.gstack/qa-reports/presales-full-crud-sweep-20260701035838.json`
  - 9 steps / 0 failed / 0 apiErrors / 0 pageErrors / 0 requestFailures / 0 consoleItems / 0 cleanup failures。
  - 清理确认：solution 10 deleted，tender 8 deleted，ticket 12/13 deleted，technical template 8 deleted，solution template 4 deleted。
  - SQLite 复核：`presale_support_ticket`、`presale_solution`、`presale_tender_record`、`technical_parameter_templates`、`presale_solution_template` 中本轮 `QA_PRESALE_20260701035838%` 残留均为 0。
- 本轮验证：
  - `QA_HEADLESS=0 node .gstack/qa-scripts/presales-full-crud-sweep.mjs` -> passed。
  - `node --check .gstack/qa-scripts/presales-full-crud-sweep.mjs` -> passed。
  - `npm --prefix frontend run test:run -- --reporter=dot PresalesTasks.test.jsx RequirementSurvey.test.jsx PresaleProposals.test.jsx TechnicalParameterManagement.test.jsx BiddingCenter.test.jsx KnowledgeBase.test.jsx presales.test.js presaleWorkbench.test.js presalesRoutes.test.jsx salesPresaleWorkbenchRoutes.test.jsx` -> 11 files passed，108 tests passed。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入和 chunk size 提示。

## 2026-07-01 继续：项目管理环节真实浏览器写入链路验收

- 新增真实浏览器写入脚本：`.gstack/qa-scripts/project-full-crud-sweep.mjs`。
  - 通过登录页真实表单登录 `admin/admin123`，从项目管理中心开始完整跑项目创建、9 个页签导航、项目任务创建/详情、里程碑创建/详情/完成、项目成本录入、下游 API 复核和 SQLite 清理。
  - 覆盖入口：`/project/management-center?tab=board&view=card`、`/projects/:id/tasks`、`/projects/:id/milestones`、`/costs?project_id=:id`。
  - 清理逻辑按本轮创建的 project/task/milestone/cost id 精确删除，并动态检查引用 `projects` 的外键表，避免留下 QA 数据。
- 本轮真实浏览器发现并修复：
  - 任务新建/详情弹窗、里程碑新建/详情弹窗缺少 Radix `DialogDescription`，真实浏览器 console warning。修复：`frontend/src/pages/ProjectTaskList/index.jsx` 和 `frontend/src/pages/MilestoneManagement.jsx` 增加屏幕阅读器可见描述。
  - 脚本自身修正：里程碑详情弹窗存在两个“关闭”按钮导致 strict locator 冲突；里程碑完成动作需要点击自定义确认弹窗“确认”。均已修到脚本中。
  - 修复后项目管理写入链路未发现新的产品阻断 bug。
- 最终真实浏览器结果：
  - `.gstack/qa-reports/project-full-crud-sweep-20260701041913.json`
  - 6 steps / 0 failedSteps / 0 apiErrors / 0 pageErrors / 0 requestFailures / 0 consoleItems / 0 cleanupFailures。
  - 清理确认：project 105 deleted，task 132 deleted，milestone 201 deleted，cost 62 deleted。
  - SQLite 复核：`projects`、`tasks`、`project_milestones`、`project_costs` 中本轮 `QA_PROJECT_20260701041913%` 残留均为 0。
- 本轮验证：
  - `node --check .gstack/qa-scripts/project-full-crud-sweep.mjs` -> passed。
  - `QA_HEADLESS=0 node .gstack/qa-scripts/project-full-crud-sweep.mjs` -> passed。
  - `npm --prefix frontend run test:run -- --reporter=dot ProjectManagementCenter.test.jsx ProjectManagementChildContext.test.jsx ProjectManagementDownstreamContext.test.jsx ProjectFormStepper.test.jsx projectManagementCenterRoutes.test.jsx projects.test.js` -> 6 files passed，66 tests passed；保留 mocked API 测试里的预期错误日志。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入和 chunk size 提示。

## 2026-07-01 继续：工程技术模块真实浏览器写入链路验收

- 新增真实浏览器写入脚本：`.gstack/qa-scripts/engineering-full-crud-sweep.mjs`。
  - 通过登录页真实表单登录 `admin/admin123`，创建工程技术载体项目后，从工程技术模块跑 ECN 中心和技术评审。
  - 覆盖入口：`/change-management/ecn-center?tab=management`、`/change-management/ecn-center?tab=types`、`/change-management/ecn-center?tab=statistics`、`/technical-reviews?project_id=:id`、`/technical-reviews/:reviewId`。
  - 覆盖写入链路：ECN 创建、影响分析弹窗、ECN 类型创建/删除、统计页导航、技术评审创建、参与人/材料/检查项/问题新增、下游 API 复核、SQLite 精确清理。
- 本轮真实浏览器发现并修复：
  - ECN 影响分析弹窗按旧 `impact_summary` 结构读取，当前后端返回 `ResponseModel` 且可能无影响，导致弹窗崩。修复：统一 normalize 当前/旧响应结构。
  - ECN 新建和 ECN 类型弹窗缺少 Radix `DialogDescription`，真实浏览器 console warning。修复：补充描述。
  - 技术评审新建表单把 `project_id/host_id/presenter_id/recorder_id` 以字符串提交，后端校验 422。修复：保存前转数值，空可选设备转 `null`，空必填值不误转 `0`。
  - ECN 类型和技术评审筛选输入空值时显示 `unknown`。修复为空字符串。
  - 项目复盘经验教训 API 单测 mock 仍指旧路径。修复为 `/project-reviews/lessons`。
  - 脚本自身修正：技术评审详情页自定义 Tabs 实际是 button；材料弹窗版本号不能用 `input.last()`，避免点到复选框。
- 最终真实浏览器结果：
  - `.gstack/qa-reports/engineering-full-crud-sweep-20260701045322.json`
  - 8 steps / 0 failedSteps / 0 apiErrors / 0 pageErrors / 0 requestFailures / 0 consoleItems / 0 cleanupFailures。
  - 清理确认：project 105 deleted，ECN 4 deleted，ECN type 4 UI deleted，technical review 4 deleted，participant/material/checklist/issue deleted。
  - SQLite 复核：`projects`、`ecn`、`ecn_types`、`technical_reviews`、`review_participants`、`review_materials`、`review_checklist_records`、`review_issues`、`issues` 中本轮 `QA_ENGINEERING_20260701045322%` 残留均为 0。
- 本轮验证：
  - `node --check .gstack/qa-scripts/engineering-full-crud-sweep.mjs` -> passed。
  - `QA_HEADLESS=0 node .gstack/qa-scripts/engineering-full-crud-sweep.mjs` -> passed。
  - `npm --prefix frontend run test:run -- --reporter=dot TechnicalReviewList.test.jsx TechnicalReviewDetail.test.jsx useTechnicalReviewForm.test.js engineering.test.js` -> 4 files passed，57 tests passed。
  - `npm --prefix frontend run test:run -- --reporter=dot ecnBom.test.js routeContracts.test.js ProjectWorkspaceNextActionContext.test.jsx TechnicalReviewList.test.jsx TechnicalReviewDetail.test.jsx useTechnicalReviewForm.test.js engineering.test.js` -> passed。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入和 chunk size 提示。

## 2026-07-01 继续：研发管理模块真实浏览器写入链路验收

- 新增真实浏览器写入脚本：`.gstack/qa-scripts/rd-full-crud-sweep.mjs`。
  - 通过登录页真实表单登录 `admin/admin123`，从研发管理菜单开始跑研发项目、研发成本、工作日志、研发文档、成本汇总和研发报表。
  - 覆盖入口：`/rd-projects`、`/rd-cost`、`/rd-projects/:id`、`/rd-projects/:id/cost-entry`、`/rd-projects/:id/worklogs`、`/rd-projects/:id/documents`、`/rd-projects/:id/reports?type=...`。
  - 每轮自动追踪创建的 `rd_project`、`rd_cost`、`timesheet`、`project_documents` 和上传文件，并在 `finally` 中精确清理。
- 本轮真实浏览器发现并修复：
  - 研发项目创建接口前端打 `/rd-projects`，后端只注册 POST `/rd-projects/`，导致 405。修复：`rdProjectApi.create()` 改为 `/rd-projects/`，并同步单测 mock。
  - 研发项目表单把未选分类等可选整数以空字符串提交，导致 FastAPI 422。修复：`category_id/project_manager_id/linked_project_id` 提交前统一转数值或 `null`，并把校验错误提示从 `[object Object]` 改为可读文本。
  - 详情页“录入费用/费用汇总”和报表按钮指向未注册旧路由 `/costs/...`、`/reports/...`。修复为当前已注册的 `/cost-entry`、`/cost-summary`、`/reports?type=...`。
  - `/rd-cost` 菜单入口在无项目 id 时一直 loading。修复为空入口显示“请选择研发项目查看研发费用汇总”。
  - 研发费用类型前端按 `cost_type_code/cost_type_name` 读取，后端实际返回兼容字段 `type_code/type_name`。修复显示和人工费用判断的字段兼容。
  - 研发文档“全部类型”筛选把值设为 `all`，导致列表被筛空。修复为空筛选值；并补齐研发项目、费用、工时、文档弹窗的 `DialogDescription`，消除浏览器 console warning。
  - 新建研发项目不关联非标项目时，文档上传会写入 `project_documents.project_id = null`，但本地 SQLite 表约束为 NOT NULL。修复：`ProjectDocument.project_id` 模型改为 nullable；本地 `data/app.db` 已备份到 `data/app.db.backup-rd-doc-project-null-20260701130907` 后重建 `project_documents` 表并保留原 60 条数据。
- 最终真实浏览器结果：
  - `.gstack/qa-reports/rd-full-crud-sweep-20260701051404.json`
  - 7 steps / 0 failedSteps / 0 apiErrors / 0 pageErrors / 0 requestFailures / 0 consoleItems / 0 cleanupFailures。
  - 清理确认：rd project 4 deleted，rd cost 4 deleted，worklog 429 deleted，document 61 deleted，上传文件已删除。
  - SQLite 复核：`rd_project`、`rd_cost`、`timesheet`、`project_documents` 中本轮 `QA_RD_20260701051404%` 残留均为 0。
- 本轮验证：
  - `node --check .gstack/qa-scripts/rd-full-crud-sweep.mjs` -> passed。
  - `QA_HEADLESS=0 node .gstack/qa-scripts/rd-full-crud-sweep.mjs` -> passed。
  - `npm --prefix frontend run test:run -- --reporter=dot engineering.test.js` -> 1 file passed，43 tests passed。
  - `npm --prefix frontend run test:run -- --reporter=dot routeContracts.test.js` -> 1 file passed，23 tests passed。
  - `python -m compileall app/models/project/document.py app/api/v1/endpoints/rd_project/documents.py` -> passed。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入和 chunk size 提示。

## 2026-07-01 继续：采购管理模块真实浏览器写入链路验收

- 新增真实浏览器写入脚本：`.gstack/qa-scripts/procurement-full-crud-sweep.mjs`。
  - 通过登录页真实表单登录 `admin/admin123`，从采购管理模块完整跑供应商、采购申请、采购订单、收货、质检和采购中心页。
  - 覆盖入口：`/suppliers`、`/purchase-requests/new`、`/purchase-requests`、`/purchases`、`/purchases/receipts/new?order_id=:id`、`/purchases/receipts/:id`、`/procurement/execution-center`、`/procurement/material-center`、`/procurement/analysis-center`。
  - 每轮自动追踪创建的供应商、采购申请、采购订单、订单明细、收货单和收货明细，并在 `finally` 中精确清理。
- 本轮真实浏览器发现并修复：
  - 采购订单 API 前端封装缺少删除、提交审批、审批、收货等入口；订单/申请审批参数位置与后端不一致。修复：`frontend/src/services/api/procurement.js` 统一补齐接口并改为 query params。
  - 采购订单状态常量缺少 `SUBMITTED/APPROVED/RECEIVED/REJECTED`，导致按钮状态和展示不准确。修复：`frontend/src/lib/constants/procurement.js` 补齐状态、动作判断和金额/明细兼容。
  - 采购订单卡片、详情、新建编辑弹窗仍按旧字段读取订单号、供应商、项目、审批人和明细，且新建订单不能录入明细。修复：订单字段映射兼容后端 snake_case，并补齐采购明细编辑。
  - 供应商列表按旧字段显示，新建后不刷新；部分筛选框和搜索框出现 `unknown`。修复：供应商字段 normalize、创建后刷新，并清理 `unknown` fallback。
  - 收货新建页 `getItems` 返回统一对象时被当数组 `.filter()`，导致页面崩溃；创建成功后也可能跳到 `/purchases/receipts/undefined`。修复：统一 unwrap 响应、列表兜底，并从多种响应结构提取收货单 id。
  - 多个采购相关弹窗缺少 Radix `DialogDescription`，真实浏览器 console warning。修复：补齐供应商、采购订单、采购申请、物料选择、收货和质检相关弹窗描述。
  - 脚本自身修正：收货页添加物料时需要精确点击物料行 `cursor-pointer` 容器，避免点到外层空区域。
- 最终真实浏览器结果：
  - `.gstack/qa-reports/procurement-full-crud-sweep-20260701054459.json`
  - 11 steps / 0 failedSteps / 0 apiErrors / 0 pageErrors / 0 requestFailures / 0 consoleItems / 0 cleanupFailures。
  - 清理确认：supplier 50 deleted，purchase request 27 deleted，purchase order 133 deleted，goods receipt 26 deleted，receipt item 9 deleted。
  - SQLite 复核：`vendors`、`purchase_requests`、`purchase_orders`、`goods_receipts` 中本轮 `QA_PROC_20260701054459%` 残留均为 0。
- 本轮验证：
  - `node --check .gstack/qa-scripts/procurement-full-crud-sweep.mjs` -> passed。
  - `QA_HEADLESS=0 node .gstack/qa-scripts/procurement-full-crud-sweep.mjs` -> passed。
  - `npm --prefix frontend run test:run -- --reporter=dot procurement.test.js` -> 1 file passed，38 tests passed；保留 mocked API 测试里的预期错误日志。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入和 chunk size 提示。
- 2026-07-01 追修采购订单审批入口：
  - 已补齐采购订单 `SUBMITTED` 状态下的“审批通过 / 审批驳回”可见按钮，点击后打开“审批采购订单”弹窗，可填写审批意见，再调用后端审批接口。
  - 新增回归测试：`frontend/src/components/purchase/orders/__tests__/OrderCard.approval.test.jsx`，覆盖待审批订单同时展示通过/驳回动作并传出审批结果。
  - 真实浏览器脚本已改为 UI 审批，不再用 API 快捷推进订单状态；提交后会断言“审批通过”和“审批驳回”都可见。
  - 最新真实浏览器结果：`.gstack/qa-reports/procurement-full-crud-sweep-20260701055521.json`
  - 11 steps / 0 failedSteps / 0 apiErrors / 0 pageErrors / 0 requestFailures / 0 consoleItems / 0 cleanupFailures。
  - SQLite 复核：`vendors`、`purchase_requests`、`purchase_orders`、`goods_receipts` 中本轮 `QA_PROC_20260701055521%` 残留均为 0。
- 2026-07-01 追修采购订单审批分权：
  - 后端 `purchase-orders/{id}/approve` 已增加分权校验：管理员/超管/租户管理员/管理员角色可审批；普通用户只能审批采购订单创建人的直属下级关系（`created_by` 用户的 `reporting_to == 当前用户.id`）。
  - 普通用户自审、无关同事审批均返回 403；直属上级审批返回 200。
  - 本地 `admin` 账号存在 `is_superuser=True` 且 `tenant_id=1` 的特殊数据，采购审批按业务管理员口径放行，避免管理员自审被误挡。
  - 顺手修复采购收货端点中 Python 3.9 不兼容的 `| None` 注解，否则测试环境会导致整个采购路由包导入失败。
  - 验证：
    - `python -m pytest tests/api/test_purchase.py::TestPurchaseOrderApproval::test_approve_order tests/api/test_purchase.py::TestPurchaseOrderApproval::test_non_admin_order_requires_direct_manager_approval tests/api/test_purchase.py::TestPurchaseOrderApproval::test_superuser_with_tenant_can_approve_own_purchase_order tests/api/test_purchase.py::TestPurchaseOrderApproval::test_reject_order -q` -> 4 passed。
    - `python -m compileall app/api/v1/endpoints/purchase/orders_refactored.py app/api/v1/endpoints/purchase/receipts.py tests/api/test_purchase.py` -> passed。
    - `QA_HEADLESS=0 QA_ROOT=http://127.0.0.1:5173 node .gstack/qa-scripts/procurement-full-crud-sweep.mjs` -> passed，报告 `.gstack/qa-reports/procurement-full-crud-sweep-20260701062037.json`。
    - 报告摘要：11 steps / 0 failedSteps / 0 apiErrors / 0 pageErrors / 0 requestFailures / 0 consoleItems / 0 cleanupFailures；SQLite 复核本轮 `QA_PROC_20260701062037%` 在 `vendors`、`purchase_requests`、`purchase_orders`、`goods_receipts` 残留均为 0。

## 2026-07-01 继续：发货计划项目来源和计划/实际发货日期口径

- 发货管理已按业务口径调整为“发货计划”：
  - 全局发货列表不再提供独立新建入口；发货计划从项目交付页发起，路径保留 `project_id` 上下文。
  - 后端创建发货计划时校验销售订单必须关联项目； standalone 销售订单不能直接生成发货计划。
  - 创建/编辑表单改为“生成/编辑发货计划”；编辑页只读显示来源销售订单，不再展示空订单警告。
  - `delivery_date` 明确为“计划发货日期”，`ship_date` 明确为“实际发货日期”，实际发货日期由发货动作写入。
  - 真实浏览器 toast API 兼容已修复，避免运行态 `toast is not a function`。
- 验证：
  - `npm --prefix frontend run test:run -- --reporter=dot DeliveryManagement/__tests__/notify.test.js DeliveryManagement/__tests__/PageHeader.test.jsx DeliveryManagement/__tests__/DeliveryForm.test.jsx DeliveryManagement/__tests__/useDeliveryManagement.test.js DeliveryManagement/__tests__/DeliveryDetail.test.jsx pages/__tests__/ExecutionTailContext.test.jsx components/delivery-management/__tests__/DeliveryOverview.test.jsx` -> 7 files passed，18 tests passed。
  - `.venv/bin/python -m pytest tests/api/test_business_support_delivery_routes.py -q` -> 3 passed。
  - `node --check .gstack/qa-scripts/delivery-full-crud-sweep.mjs` -> passed。
  - `/opt/homebrew/Cellar/python@3.13/3.13.11_1/bin/python3.13 -m compileall app/api/v1/endpoints/business_support_orders/delivery_orders/crud.py app/schemas/business_support/delivery.py tests/api/test_business_support_delivery_routes.py` -> passed。
  - `QA_ROOT=http://127.0.0.1:5173 QA_DB_PATH=data/app.db node .gstack/qa-scripts/delivery-full-crud-sweep.mjs` -> passed，报告 `.gstack/qa-reports/delivery-full-crud-sweep-20260701071428.json`。
  - 报告摘要：12 steps / 0 failedSteps / 0 apiErrors / 0 pageErrors / 0 requestFailures / 0 consoleErrors；计划发货日期 `2026-07-18`，实际发货日期由确认发货写入 `shipDate`；SQLite 清理复核本轮 `QA_DELIVERY_20260701071428%` 在 `delivery_orders`、`sales_orders`、`sales_order_items`、`projects`、`customers` 残留均为 0。

## 2026-07-01 继续：客服验收 / 安装调试 / 售后外出日志

- 售后外出人员工作日志已按“少填、自动带出”实现：
  - 新增 `/my/work-logs/field-service-context`，按当前登录人员和日期自动读取其安装调试派工，带出派工单、项目、设备、任务类型、进度和派工说明。
  - 新增 `/my/work-logs/from-dispatch`，从所选派工自动生成/提交当天工作日志；复用现有 `work_logs` 和 `work_log_mentions`，自动写入 `PROJECT`、`MACHINE` 关联。
  - 约束为同一人员同一天一条日志；草稿可更新提交，已提交则禁止重复提交。
  - 前端安装调试页新增“今日外出日志”入口，外勤只需填工时、今日进展、现场问题、下一步，项目/设备/工作内容由系统自动挂钩。
- 同步修复安装调试派工页面真实接口问题：
  - 后端派工返回 `machine_no` 类型与 schema 不一致导致 500，已改为整数并补 `machine_name`。
  - 前端派工列表/详情/统计统一兼容后端 snake_case 字段和大写状态；修复指派人员下拉为空、`search` 参数错传、`ASSIGNED` 状态缺少“开始执行”按钮等问题。
- 验证：
  - `pytest tests/unit/test_field_service_work_log_service.py -q` -> 2 passed。
  - `python -m py_compile app/services/field_service_work_log_service.py app/api/v1/endpoints/my/__init__.py app/schemas/work_log.py` -> passed。
  - `python -m py_compile app/schemas/installation_dispatch.py app/api/v1/endpoints/installation_dispatch/orders.py` -> passed。
  - `npm --prefix frontend run test:run -- --reporter=dot components/installation-dispatch/__tests__/dispatch-components.test.jsx` -> 5 passed。
  - `npm --prefix frontend run build` -> passed；保留既有 Vite 动静态重复导入和 chunk size 提示。
  - 真实浏览器脚本 `.gstack/qa-scripts/field-service-work-log-sweep.mjs` -> passed，报告 `.gstack/qa-reports/field-service-work-log-sweep-20260701153850.json`。
  - 真实浏览器验证内容：登录后进入交付验收中心安装调试页，打开“今日外出日志”，选择日期 `2035-01-31`，自动带出 `QA售后日志项目 / QA售后日志设备`，提交后 SQLite 复核日志内容和 `PROJECT:105,MACHINE:4` 关联均写入成功。
- 注意：
  - `tests/api/test_work_log.py` 已补充外出日志 API 用例，但当前 API TestClient 受 Starlette/httpx 版本兼容问题阻塞，错误为 `Client.__init__() got an unexpected keyword argument 'app'`；本轮业务链路已通过服务层单测、前端单测、构建和真实浏览器端到端验证。
  - 浏览器报告里仅有外部字体 `InterVariable.woff2` abort，非业务阻断。

## 2026-07-01 继续：全前端路由真实浏览器逐页巡检

- 回应“为什么不像之前一个个页面打开测试”：本轮已恢复为 `QA_HEADLESS=0` 真实可见浏览器逐页打开，自动脚本仅用于顺序打开、点击安全按钮、记录 console/API/page error，不用纯后台结果替代页面确认。
- 本轮修复：
  - `/timesheet/dashboard` 点击“同步数据”时调用 `POST /api/v1/timesheet/sync`，但后端没有注册该路由，真实浏览器报 404 和 console error。
  - 新增 `app/api/v1/endpoints/timesheet/sync.py`，注册到工时模块；支持 `year/month/project_id/sync_target=all|finance|rd|project|hr`，无已审批工时时返回 200 摘要，有数据时调用现有 `TimesheetSyncService` 同步到财务/研发/项目/HR。
  - 新增契约测试 `tests/api/test_batch12_route_contracts.py::test_timesheet_sync_route_is_registered_for_dashboard`，先复现 404，再验证 200。
- 后端验证：
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_batch12_route_contracts.py::test_timesheet_sync_route_is_registered_for_dashboard -q` -> passed。
  - `PYTHONPATH=. .venv/bin/pytest tests/api/test_batch12_route_contracts.py::test_timesheet_records_collection_route_is_registered tests/api/test_batch12_route_contracts.py::test_timesheet_anomalies_route_uses_quality_service tests/api/test_batch12_route_contracts.py::test_timesheet_sync_route_is_registered_for_dashboard -q` -> 3 passed。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/timesheet/sync.py app/api/v1/endpoints/timesheet/__init__.py` -> passed。
  - 真实服务 `POST http://127.0.0.1:8002/api/v1/timesheet/sync?year=2026&month=7&sync_target=all` -> HTTP 200，返回“没有已审批工时需要同步”。
- 真实浏览器回归：
  - `/timesheet/dashboard` 单页回归报告 `.gstack/qa-reports/all-frontend-route-sweep-20260701140935.json`：1 route / clicked 2 / hard errors 0 / console errors 0。
  - 480-490 报告 `.gstack/qa-reports/all-frontend-route-sweep-20260701141536.json`：10 routes / clicked 29 / hard errors 0。
  - 490-500 报告 `.gstack/qa-reports/all-frontend-route-sweep-20260701141840.json`：10 routes / clicked 21 / hard errors 0。
  - 500-520 报告 `.gstack/qa-reports/all-frontend-route-sweep-20260701142059.json`：20 routes / clicked 43 / hard errors 0。
  - 520-530 报告 `.gstack/qa-reports/all-frontend-route-sweep-20260701142524.json`：10 routes / clicked 8 / hard errors 0。
  - 补扫当前清单缺口 260-280 报告 `.gstack/qa-reports/all-frontend-route-sweep-20260701142736.json`：20 routes / clicked 60 / hard errors 0。
- 覆盖核算：
  - 使用当前最新 route inventory `.gstack/qa-reports/all-frontend-route-sweep-20260701142736.json` 对照所有完整干净报告。
  - 当前清单 530 个路由，干净报告覆盖 530 个，missing 0。

## 2026-07-03 继续：AI 功能线遗留——"评估通过→approve→建项"补充演练 + 立项关卡修复

- 补验 E2E 报告遗留的立项完整落地链（脚本 approve_drill.py，16/16 通过）：
  - 商机→申请售前支持(工单)→技术评估申请→售前方案(挂工单+商机)→立项(挂 technical_solution_id)→评估执行 COMPLETED→submit 放行→approve(指定 PM)→真实创建项目。
  - 建项验证：pmo_project_initiation 回填 project_id；项目 PJ260703016 客户/PM/合同金额正确带出；售前工单反绑 project_id；建项自动生成 9 阶段+状态流水。
- 演练暴露并修复缺陷：
  - **立项关卡漏洞**：`submit_initiation` 只检查"存在技术评估记录"，评估仅申请（status=PENDING、未执行评估）时提交即放行，违背"完成技术初评后再提交"的关卡语义。
  - 修复：`app/services/pmo_initiation/service.py` submit 关卡增加评估状态校验——current assessment status ≠ COMPLETED 时报 400"售前技术评估尚未完成（当前状态：…）"。评估 decision（RECOMMEND/NOT_RECOMMEND）不硬拦截，留给 PMO 评审人工裁量。
- 验证：
  - 实测：PENDING 时 submit → HTTP400 拦截；评估执行后 → HTTP200 SUBMITTED；approve → 项目真实创建。
  - `PYTHONPATH=. .venv/bin/pytest tests/unit/test_pmo_initiation_service.py -q` → 35 passed（原 success 用例适配新关卡语义 + 新增拦截 PENDING/缺失 2 例）。
  - 测试数据按外键图递归清理（51 行），残留 0；admin 密码演练后已还原（临时密码登录 401 复核）。

## 2026-07-03 继续：AI 表单填充嵌入新建对话框

- 可复用 `AutofillBar` 组件 + `mergeAutofill` 合并策略（只填空位/不覆盖用户已填/嵌套递归/忽略多余键/数字转字符串适配受控 Input）。
- 嵌入新建商机、新建客户对话框；后端 `/ai-copilot/autofill` schema 扩充对齐表单全字段并加"不编造"约束。
- 验证：
  - `npm run test:run -- src/components/ai/__tests__/AutofillBar.test.jsx` -> 6 passed。
  - `npm run build` -> passed（既有 chunk 提示不变）。
  - 真实 AI 实测：商机线索→金额/节拍/交付窗口/验收标准带出；客户线索→不编造电话。
  - 真实浏览器 `.gstack/qa-scripts/ai-autofill-sweep.mjs` -> 5/5 passed，0 console/page/api error，报告+截图在 .gstack/qa-reports。
- 注意：`tests/pages/__tests__/CustomerList.test.jsx` 的 15 个失败为既有测试债（customerApi mock 形状漂移，测试对象是 CustomerManagement 页，与本次改动无关，已用 stash 对照确认）。
- 遗留（AI 功能线）：命令栏执行动作、语义搜索接向量检索(ROADMAP F4)、多模型配置页切换、表单填充扩到更多新建入口。

## 2026-07-03 继续：命令栏执行动作 + 多模型/多厂商配置页切换

- 命令栏执行动作：
  - 后端 `/ai-copilot/command` 意图扩为 navigate|search|answer|action，action 白名单 create_opportunity/create_customer，AI 同时提取去指令词的业务线索 hint；未知动作回落 search。
  - 前端 CommandBar 对 action 意图跳转 `path?ai_hint=...`；商机/客户列表页监听 ai_hint 参数→自动开新建对话框→AutofillBar 以 defaultHint 自动预填（同一线索只跑一次，关对话框清线索，URL 参数即刻 replace 清除）。
  - 安全边界：动作只打开预填好的对话框，创建仍由用户点击确认。
- 多模型/多厂商切换：
  - `AI_DEFAULT_MODEL` 设置（ai_settings 可存，空值=回落原逻辑）；AIClientService.default_model 优先读它，模型前缀路由厂商，缺 Key 自动回退 qwen。
  - /admin/ai-config FIELDS 分组(通用/阿里百炼/其他厂商)+新增 ZHIPU/OPENAI/KIMI Key；/test 支持 model 参数且不再强依赖 qwen Key。
  - 配置页按组渲染、默认模型预设快捷按钮、测试连接可选模型。
- 验证：
  - `npm run test:run -- src/components/ai/__tests__/AutofillBar.test.jsx` -> 7 passed；`npm run build` -> passed；py_compile passed。
  - 后端实测：三条自然语言指令正确分类(两动作一导航，hint 提取干净)；切 glm-5 即时生效且无 Key 回退 qwen 连通；指定模型测试 1.0s；复位正常。
  - 真实浏览器 `.gstack/qa-scripts/ai-command-action-sweep.mjs` -> 6/6 passed（Cmd+K→动作→自动开框→AI 预填→导航回归），0 console/page/api error。
  - admin 密码临时切换后已还原（401 复核）。
- AI 功能线遗留仅剩：语义搜索接向量检索（ROADMAP F4，大项建议单独立项）。

## 2026-07-03 继续：AI 需求解读与技术方案深化（第一批 A+B+C+D）

- **A 需求澄清助手**（治"需求不清晰"根因）：新端点 `POST /sales/opportunities/{id}/ai-requirement-gaps`——按非标十要素（对象/节拍/精度/接口/现场/验收/安全/预算/交期/数量扩展性）逐项评 filled/partial/missing + 置信度 + 证据原文摘录 + 追问话术；成熟度改为 rubric 确定性计分（filled=10/partial=5/missing=0，总分0-100→HIGH≥75/MEDIUM≥45/LOW），不再由 AI 拍脑袋。缺口分析 JSON 存 `opportunity_requirements.extra_json.gap_analysis`。前端商机详情页新增"🧭 需求缺口追问"按钮+面板（十要素红绿灯+追问清单可一键复制）。
- **B 方案落库闭环 + D 历史教训注入**：`/ai-eng/config-design` 增加 `persist` 参数——方案落库 `presale_solution`（编号 SOL-yymmdd-xxx，同商机 AI 方案版本链 V1→V2 挂 parent_id），模块明细/定制项/复用率存 technical_spec；生成时自动注入 project_lessons + lessons_learned 历史教训，输出 risk_reminders（历史坑提醒）。前端配置设计按钮改为落库并显示方案号/版本/坑提醒。
- **C 需求-方案符合性矩阵**：新端点 `POST /ai-eng/requirement-coverage`——综合结构化需求+客户沟通原文拆 5-12 条可核对条目，逐条判断方案覆盖（满足/部分/未覆盖+差距说明），矩阵并入方案 technical_spec.coverage_matrix 沉淀；前端配置设计后自动核对并渲染矩阵。
- **修复演练暴露的存量缺陷（成熟度口径 split-brain）**：模型/Schema/存量数据/编辑框均为 1-5 整数，但 A1 enrich 和经营简报 SQL 用 HIGH/MEDIUM/LOW 字符串——AI 写入后商机详情 GET 直接 500。统一为整数口径：新增 MATURITY_LEVELS 映射（HIGH=4/MEDIUM=3/LOW=2），enrich/gaps 写数字，简报 SQL 改 `<=2`。存量无脏数据（分布 None/4/5）。
- 验证：
  - API 实测 13/13（scratchpad/deepen_drill.py）：十要素齐全、已知项识别（节拍filled/接口partial 符合 rubric）、8条追问、6项证据、rubric 回写、写后详情 200、方案落库 V1→V2 版本链、2条历史坑提醒、矩阵 8 条覆盖率 75% 正确识别 2 项未覆盖、矩阵沉淀。
  - 真实浏览器 5/5（`.gstack/qa-scripts/ai-deepen-sweep.mjs`，报告 ai-deepen-sweep-20260703004546.json）：0 api/console/page error。
  - `npm run build` passed；py_compile passed；测试数据清理 0 残留。
- 第二批候选（未做）：证据链字段级溯源、需求文档/图纸多模态输入、三档方案对比、可行性红线计算。

## 2026-07-03 继续：商机页一步式"需求文档上传"入口（PDF/Word→需求抽取链）

- 新端点 `POST /sales/opportunities/{id}/requirement-document`（multipart）：
  - 提取文本：.docx（正文+**表格**，python-docx）/.pdf（**PyMuPDF 主提取**+PyPDF2 兜底+乱码率检测，解决中文 CID 字体 UniGB-UCS2-H 提取乱码）/.txt/.md；旧 .doc 明确拒绝提示另存 docx；扫描件 PDF 明确报错建议走图纸照片识别。
  - 一步式链路：文本落 `customer_communications`（type=DOCUMENT，进入需求链统一数据源）→ 原文件存档 `uploads/requirement_docs/` 并登记 `opportunity_requirements.attachments`（JSON 列表，此前空置字段启用）→ 直接复用 `ai_enrich_requirement` 抽取回填（AI 失败不吞上传结果）。
  - 会议纪要文件上传同步获益（同一提取函数，纪要页现也支持 PDF）。
- 前端商机详情页新增"📄 传需求文档"按钮：上传→显示提取字数/活动号/附件数/回填摘要→**自动触发需求缺口分析**。
- 验证：
  - API 实测 11/11（scratchpad/reqdoc_drill.py）：Word 表格参数（节拍15s/GRR/CPK）与正文（对象/MES接口）均抽到；PDF 补充需求正确融合（CE认证/安全光栅进安全要求）；附件累计 2 份且文件落盘；两份文档叠加完备度 0→95/100 HIGH；写后详情 200；.doc 拒绝 400。
  - 真实浏览器 5/5（`.gstack/qa-scripts/ai-reqdoc-sweep.mjs`）：上传→抽取面板→自动缺口分析 80/100，0 错误。
  - PyMuPDF==1.28.0 已装并写入 requirements-dev.txt。测试数据/存档文件清理 0 残留。
- 后续增量（未做）：三维 CAD 文件（STEP/STL）几何解析+多角度渲染截图喂视觉模型；扫描件 PDF OCR。

## 2026-07-03 继续：功能审计 PRE-16 止血（知识库 qwen live AI 判断）

- 修复项：`PRE-16`，售前知识库 `_has_live_ai()` 漏判阿里百炼/通义千问配置，导致已有 qwen key 时仍按无真实 AI 能力降级为规则模板。
- 改动：
  - `app/services/presale/presale_ai_knowledge_service.py`：`_has_live_ai()` 纳入 `ai_client.qwen_api_key`。
  - `tests/unit/test_presale_ai_knowledge_service_coverage.py`：新增 qwen-only live AI 回归用例，并修正该测试文件既有 fixture 类名拼写，保证整文件可跑。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`PRE-16` 标为 `已验证`，Quick-win 视图同步。
- 验证：
  - 红灯：新增用例先失败，`_has_live_ai()` 返回 False。
  - 绿灯：`.venv/bin/python -m pytest tests/unit/test_presale_ai_knowledge_service_coverage.py -q` -> 22 passed。
  - `.venv/bin/python -m py_compile app/services/presale/presale_ai_knowledge_service.py tests/unit/test_presale_ai_knowledge_service_coverage.py` -> passed。
  - `.venv/bin/python -m ruff check app/services/presale/presale_ai_knowledge_service.py tests/unit/test_presale_ai_knowledge_service_coverage.py` -> All checks passed。

## 2026-07-03 继续：功能审计 RPT-16 验证（负荷瓶颈部门名）

- 修复项：`RPT-16`，审计指出负荷瓶颈接口访问 `dept.name`，而部门模型只有 `dept_name`，超载部门分支会 500。
- 当前状态：
  - 当前工作树里的 `app/models/organization.py` 已有 `Department.name` 兼容属性，返回 `dept_name`。
  - 本轮未改业务代码，只新增 API 合约测试覆盖真实超载部门分支，避免空数据 200 掩盖问题。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_batch4_route_contracts.py::test_workload_bottlenecks_serializes_department_dept_name -q` -> passed。
  - `.venv/bin/python -m pytest tests/api/test_batch4_route_contracts.py -q` -> 3 passed。
  - `FUNCTIONAL_AUDIT_TRACKER.md` 已将 `RPT-16` 标为 `已验证`。

## 2026-07-03 继续：功能审计 PROJ-10 修复（里程碑完成门禁）

- 修复项：`PROJ-10`，里程碑完成门禁在 `_ensure_can_complete()` 中自己抛 `HTTPException(400)` 后被 `except Exception` 吞掉；同时全局兼容端点 `/milestones/{id}/complete` 直接写 `status=COMPLETED`，绕开状态机。
- 改动：
  - `app/core/state_machine/milestone.py`：在宽泛异常前显式 `except HTTPException: raise`，不再吞掉业务门禁 400。
  - `app/api/v1/endpoints/milestones.py`：全局兼容 complete 端点改走 `MilestoneStateMachine.transition_to("COMPLETED")`，统一权限、完成条件检查、自动开票触发和异常映射；失败时 rollback。
  - 新增 `tests/unit/test_milestone_state_machine_completion.py`：覆盖交付物未审批时 `_ensure_can_complete()` 必须抛 400。
  - 新增 `tests/api/test_milestone_completion_gate_contracts.py`：覆盖全局 complete 端点不得完成交付物未审批的 DELIVERY 里程碑。
  - `tests/api/test_milestones.py`：适配全局里程碑列表分页响应，避免旧测试把 `"items"` 字符串当里程碑遍历。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`PROJ-10` 标为 `已验证`，Quick-win 视图同步。
- 验证：
  - 红灯1：状态机用例先失败，`HTTPException` 未抛出，仅记录日志。
  - 红灯2：API 用例先失败，兼容端点返回 200 且状态变为 `COMPLETED`。
  - 绿灯：`.venv/bin/python -m pytest tests/unit/test_milestone_state_machine_completion.py tests/api/test_milestone_completion_gate_contracts.py -q` -> 2 passed。
  - 回归：`.venv/bin/python -m pytest tests/unit/test_progress_integration_service.py::TestCheckMilestoneCompletionRequirements tests/unit/test_milestone_state_machine_completion.py tests/api/test_milestone_completion_gate_contracts.py tests/unit/test_milestone_service.py -q` -> 10 passed。
  - 相关旧 API：`.venv/bin/python -m pytest tests/api/test_milestones.py -k complete_milestone -q` -> 1 skipped（当前无可用里程碑）；`.venv/bin/python -m pytest tests/api/test_project_milestones_api.py -k complete_project_milestone -q` -> 1 skipped（门禁/状态校验返回 400）。
  - `py_compile` passed；`ruff check` -> All checks passed。

## 2026-07-03 继续：功能审计 PRE-23 修复（立项关卡异常不静默放行）

- 修复项：`PRE-23`，立项提交时 `build_presale_handover_context()` 若异常，旧代码会 `missing=[]` 并继续提交，导致售前技术评估关卡失效。
- 改动：
  - `app/services/pmo_initiation/service.py`：售前交接/技术评估上下文构建异常 now raises `ValueError`，阻断提交，不再默认放行。
  - `tests/unit/test_pmo_initiation_service.py`：新增红绿回归用例，确认异常时状态保持 `DRAFT` 且不会 `add/commit`。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`PRE-23` 标为 `已验证`，Quick-win 视图同步。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/unit/test_pmo_initiation_service.py::TestPmoInitiationServiceSubmit::test_submit_initiation_blocks_when_handover_context_fails -q` -> failed（ValueError not raised）。
  - 绿灯：`.venv/bin/python -m pytest tests/unit/test_pmo_initiation_service.py::TestPmoInitiationServiceSubmit -q` -> 6 passed。
  - 回归：`.venv/bin/python -m pytest tests/unit/test_pmo_initiation_service.py -q` -> 36 passed。
  - `py_compile` passed；`ruff check app/services/pmo_initiation/service.py tests/unit/test_pmo_initiation_service.py` -> All checks passed；`git diff --check` passed。

## 2026-07-03 继续：功能审计 PROJ-06 修复（结项 readiness 强制门禁）

- 修复项：`PROJ-06`，`POST /pmo/projects/{project_id}/closure` 创建结项只查项目/查重，不调用现成 `ClosureReadinessService`，未验收/未达准备度的项目仍可落 `DRAFT` 结项。
- 改动：
  - `app/api/v1/endpoints/pmo/closure.py`：创建结项前调用 `ClosureReadinessService(db).check_readiness(project_id)`；`ready=False` 时返回 400，detail 带准备度分数和缺项。
  - `tests/api/test_pmo.py`：新增未达 readiness 不得创建结项的 API 合约测试；旧 `_ensure_closure` helper 显式模拟 ready=True，并修正读结项接口 `200 null` 被误当已有记录的问题。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`PROJ-06` 标为 `已验证`；全局 P0#8 标清 `PROJ-20` 仍待修，避免把变更审批回基线一起误判完成。
- 验证：
  - 红灯1：`.venv/bin/python -m pytest tests/audit_p0/test_p0_08_closure_gate_and_change_baseline.py::test_closure_blocked_when_not_ready -q` -> failed，未达 readiness 项目仍 HTTP 201。
  - 红灯2：`.venv/bin/python -m pytest tests/api/test_pmo.py::TestProjectClosures::test_create_closure_blocks_when_readiness_not_ready -q` -> failed，返回 201。
  - 绿灯：`.venv/bin/python -m pytest tests/api/test_pmo.py::TestProjectClosures -q` -> 3 passed。
  - 原始 P0 回归：`.venv/bin/python -m pytest tests/audit_p0/test_p0_08_closure_gate_and_change_baseline.py::test_closure_blocked_when_not_ready -q` -> passed。
  - 服务回归：`.venv/bin/python -m pytest tests/services/test_closure_readiness_service.py -q` -> 7 passed。
  - `py_compile` passed；`ruff check app/api/v1/endpoints/pmo/closure.py tests/api/test_pmo.py` -> All checks passed；`git diff --check` passed。

## 2026-07-03 继续：功能审计 AS-19 修复（客服关单 payload 与质保列表）

- 修复项：`AS-19`，客服工作台关闭工单时前端发 `{ resolution: "resolved" }`，后端 `ServiceTicketClose` 要求 `solution`，导致 422；同时“解决”按钮从子组件传 record、父组件按 id 用，可能拼出 `/tickets/[object Object]/close`；质保页签只读 dashboard 的 `warranty_projects`，当前统计接口不返回该字段，页面恒空。
- 改动：
  - `app/schemas/service.py`：`ServiceTicketClose.solution` 兼容历史 `resolution` alias，避免旧客户端直接 422。
  - `frontend/src/pages/CustomerServiceDashboard/utils.js`：新增纯工具，统一工单归一化、关单 payload、record/id 兼容、质保项目归一化与质保工单兜底。
  - `frontend/src/pages/CustomerServiceDashboard.jsx`：关闭工单 now sends `{ solution: ... }`，状态本地更新为 `CLOSED`；质保页签优先用 dashboard 明细，缺失时从真实质保类服务工单生成列表。
  - 新增/更新测试：`tests/schemas/test_service.py`、`tests/api/test_service_ticket_crud_contracts.py`、`frontend/src/pages/CustomerServiceDashboard/__tests__/dashboardContracts.test.js`。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`AS-19` 标为 `已验证`；备注注明 `AS-09` 售后质保表缺失仍待修。
- 验证：
  - 红灯1：`.venv/bin/python -m pytest tests/schemas/test_service.py::TestServiceTicketClose::test_accepts_legacy_resolution_alias -q` -> failed，`solution` required。
  - 红灯2：`npm run test:run -- src/pages/CustomerServiceDashboard/__tests__/dashboardContracts.test.js` -> failed，`../utils` 尚不存在。
  - 绿灯：`.venv/bin/python -m pytest tests/schemas/test_service.py::TestServiceTicketClose -q` -> 5 passed。
  - API 回归：`.venv/bin/python -m pytest tests/api/test_service_ticket_crud_contracts.py -q` -> 2 passed（含 resolution payload 关闭工单）。
  - 前端回归：`npm run test:run -- src/pages/CustomerServiceDashboard/__tests__/dashboardContracts.test.js` -> 2 passed；`npm run build` -> passed（仅既有 chunk/dynamic import warning）。
  - `py_compile` passed；`ruff check app/schemas/service.py tests/schemas/test_service.py tests/api/test_service_ticket_crud_contracts.py` -> All checks passed；targeted `eslint` passed；`git diff --check` passed。

## 2026-07-03 继续：功能审计 AS-16 修复（Header 通知铃铛）

- 修复项：`AS-16`，Header 铃铛原本无点击动作、红点无条件显示，侧栏通知中心 badge 写死 `5`。
- 改动：
  - `frontend/src/components/layout/Header.jsx`：挂接 `notificationApi.getUnreadCount()`，按未读数显示角标（0 不显示，99+ 封顶），点击跳转 `/notifications`。
  - `frontend/src/components/layout/sidebarConfig/default.js`：移除通知中心写死 badge。
  - `frontend/src/components/layout/__tests__/Header.test.jsx`：新增未读数加载、无未读不显示角标、点击跳转通知中心回归用例。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`AS-16` 标为 `已验证`，Quick-win 视图同步。
- 验证：
  - 红灯：`npm run test:run -- src/components/layout/__tests__/Header.test.jsx` -> failed（无未读数、未调用 getUnreadCount）。
  - 绿灯：`npm run test:run -- src/components/layout/__tests__/Header.test.jsx` -> 16 passed。
  - `npx eslint src/components/layout/Header.jsx src/components/layout/sidebarConfig/default.js src/components/layout/__tests__/Header.test.jsx` -> passed。
  - `npm run build` -> passed（仅既有 chunk/dynamic import warning 与 chunk size warning）。

## 2026-07-03 继续：功能审计 PROD-13 修复（完工报工审批后回写）

- 修复项：`PROD-13`，完工报工创建时立即回写工单产量/工时/完成状态，审批通过或驳回都只改报工状态，审批链变成装饰。
- 改动：
  - `app/api/v1/endpoints/production/work_reports.py`：完工报工提交阶段只创建 `PENDING` 报工，不再改工单产量、工时、进度、完成状态或释放工位。
  - 审批通过分支新增 `_apply_complete_report_to_work_order()`，统一把完工报工数量、合格数、不良数、工时、100% 进度和完成状态回写到工单；审批驳回不回写。
  - `tests/api/test_production_write_smoke.py`：把生产写入 smoke 改成“提交后待审批、审批后回写”，并新增“驳回完工报工不更新工单产量”API 回归。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`PROD-13` 标为 `已验证`，Quick-win 视图同步。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/api/test_production_write_smoke.py::TestProductionWriteSmoke::test_production_write_flow_smoke tests/api/test_production_write_smoke.py::TestProductionWriteSmoke::test_rejected_complete_report_does_not_update_work_order_output -q` -> 2 failed（提交即 `COMPLETED`）。
  - 绿灯：同一命令 -> 2 passed。
  - 回归：`.venv/bin/python -m pytest tests/api/test_production_write_smoke.py -q` -> 2 passed；`.venv/bin/python -m pytest tests/api/test_production.py::TestWorkReports -q` -> 1 passed；`.venv/bin/python -m pytest tests/api/test_production_compat_endpoints.py -k "work_report or report" -q` -> 3 passed；`.venv/bin/python -m pytest tests/unit/test_api_p6_coverage.py::TestWorkReports -q` -> 7 passed。
  - `py_compile` passed；`ruff check app/api/v1/endpoints/production/work_reports.py tests/api/test_production_write_smoke.py` -> All checks passed。

## 2026-07-03 继续：功能审计 SALES-03 修复（报价成本汇总乘数量）

- 修复项：`SALES-03`，报价成本拆解 `total_cost/subtotal_cost/gross_margin` 漏乘明细数量，导致售价按 `qty*unit_price`、成本只按单件 `cost`，毛利率虚高。
- 改动：
  - `app/api/v1/endpoints/sales/quote_costs.py`：新增统一行成本口径，`unit_cost = item.cost/tech-meta 单件成本`，`line_cost = qty * unit_cost`；`cost-breakdown` 的总成本、分类小计、成本结构按行成本汇总；`recalculate` 持久化 `QuoteVersion.cost_total/gross_margin/margin_warning` 时按 `qty*unit_cost`。
  - `tests/api/test_sales_quote_costs_quantity_contracts.py`：新增 API 合约测试，覆盖成本拆解展示和重算持久化两个入口。
  - `data/app.db` 存量修复：先备份 `data/app.db.sales03-backup-20260703100245`；只更新有明细的版本，43 条 `quote_versions.cost_total` 按 `Σ(qty*cost)` 重算，`gross_margin/margin_warning` 按原 `total_price` 同步重算；57 条无明细但有总成本的历史版本未动，避免误清零。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`SALES-03` 标为 `已验证`，P0-0 资金正确性急救包同步。
- 验证：
  - 红灯1：`.venv/bin/python -m pytest tests/audit_p0/test_p0_03_quote_fund_trio.py::test_cost_breakdown_multiplies_by_quantity -q` -> failed，接口返回 `6773243.39`，应为 `19040825.62`。
  - 红灯2：`.venv/bin/python -m pytest tests/api/test_sales_quote_costs_quantity_contracts.py -q` -> 2 failed，展示和重算均返回 `total_cost=100`，应为 `300`。
  - 绿灯：`.venv/bin/python -m pytest tests/api/test_sales_quote_costs_quantity_contracts.py -q` -> 2 passed；`.venv/bin/python -m pytest tests/audit_p0/test_p0_03_quote_fund_trio.py::test_cost_breakdown_multiplies_by_quantity -q` -> passed。
  - 回归：`.venv/bin/python -m pytest tests/unit/test_sales_scope_tail.py::TestQuoteCostBreakdownScope -q` -> 4 passed。
  - 静态检查：`py_compile` passed；`ruff check app/api/v1/endpoints/sales/quote_costs.py tests/api/test_sales_quote_costs_quantity_contracts.py` -> All checks passed。
  - 存量复核：`data/app.db` 有明细版本成本偏差从 `43 / 903046776.53` 降为 `0`。

## 2026-07-03 继续：功能审计 SALES-01 修复（报价状态直改禁止审批结果）

- 修复项：`SALES-01`，通用报价状态端点 `/sales/quotes/{id}/status` 允许 `PENDING_APPROVAL -> APPROVED`，任意登录用户可绕过报价审批工作流自助批准。
- 根因：`app/api/v1/endpoints/sales/quote_status.py` 的 `STATUS_TRANSITIONS` 把 `PENDING_APPROVAL/IN_REVIEW -> APPROVED/REJECTED` 放进通用状态机；正式审批入口在 `quote_per_id_approval.py`，但状态端点没有审批任务/权限门禁。
- 改动：
  - `app/api/v1/endpoints/sales/quote_status.py`：从通用状态迁移表移除 `PENDING_APPROVAL/IN_REVIEW -> APPROVED/REJECTED`；审批结论只能走报价审批流程；保留 `DRAFT -> PENDING_APPROVAL` 与批准后的发送/接受等后续流转。
  - `tests/api/test_sales_quote_status_contracts.py`：新增 API 合约测试，覆盖待审批报价不能经状态端点直接批准，且前端状态查询不再暴露 `APPROVED/REJECTED` 为待审批可选迁移。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`SALES-01` 标为 `已验证`，P0-0 资金正确性急救包同步。
- 验证：
  - 红灯1：`.venv/bin/python -m pytest tests/audit_p0/test_p0_03_quote_fund_trio.py::test_quote_status_endpoint_must_not_self_approve -q` -> failed，接口返回 HTTP 200 自助批准。
  - 红灯2：`.venv/bin/python -m pytest tests/api/test_sales_quote_status_contracts.py -q` -> failed，直接批准返回 HTTP 200。
  - 绿灯：`.venv/bin/python -m pytest tests/api/test_sales_quote_status_contracts.py -q` -> passed；`.venv/bin/python -m pytest tests/audit_p0/test_p0_03_quote_fund_trio.py::test_quote_status_endpoint_must_not_self_approve -q` -> passed。
  - 回归：`.venv/bin/python -m pytest tests/api/test_sales_quotes_api.py::TestSalesQuotesAPI::test_approve_does_not_bypass_approval_workflow -q` -> passed。
  - 静态检查：`py_compile` passed；`ruff check app/api/v1/endpoints/sales/quote_status.py tests/api/test_sales_quote_status_contracts.py` -> All checks passed。

## 2026-07-03 继续：功能审计 SALES-02 修复（已审批报价明细冻结与金额重算）

- 修复项：`SALES-02`，已审批报价版本仍可通过 `/sales/quotes/{version_id}/items`、`/sales/quotes/items/{item_id}` 增删改明细，且草稿明细变更后 `QuoteVersion.total_price/cost_total/gross_margin` 不重算。
- 根因：
  - `app/api/v1/endpoints/sales/quote_items.py` 只校验版本存在和销售数据权限，没有检查报价主状态或版本状态。
  - create/update/delete 明细后直接 commit，不按明细行重新汇总版本金额。
  - `quote_versions` 表已有 `status/approval_status/approval_instance_id`，但 `QuoteVersion` ORM 未映射，导致版本级冻结状态无法可靠读取。
- 改动：
  - `app/models/sales/quotes.py`：补齐 `QuoteVersion.quote_code/status/approval_instance_id/approval_status` 映射，并声明 `idx_qv_status`。
  - `app/api/v1/endpoints/sales/quote_items.py`：三类写操作统一调用冻结门禁；父报价或版本处于 `SUBMITTED/PENDING_APPROVAL/IN_REVIEW/APPROVED/SENT/ACCEPTED/CONVERTED/EXPIRED/CANCELLED` 时拒绝改明细。
  - `app/api/v1/endpoints/sales/quote_items.py`：可编辑版本写入后统一重算 `total_price=Σ(qty*unit_price)`、`cost_total=Σ(qty*cost)`、`gross_margin` 与 `margin_warning`。
  - `tests/api/test_sales_quote_item_contracts.py`：新增 API 合约测试，覆盖已审批报价 create/update/delete 全拒绝、版本自身 `APPROVED` 时也冻结、草稿更新明细后版本金额重算。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`SALES-02` 标为 `已验证`，P0-0 资金正确性急救包同步。
- 验证：
  - 红灯1：`.venv/bin/python -m pytest tests/audit_p0/test_p0_03_quote_fund_trio.py::test_items_of_approved_quote_must_be_locked -q` -> failed，已 APPROVED 版本明细 PUT 返回 HTTP 200。
  - 红灯2：`.venv/bin/python -m pytest tests/api/test_sales_quote_item_contracts.py -q` -> 2 failed，已审批报价仍可增删改，草稿明细更新后版本总价仍为 100 而非 150。
  - 绿灯：`.venv/bin/python -m pytest tests/api/test_sales_quote_item_contracts.py -q` -> 3 passed；`.venv/bin/python -m pytest tests/audit_p0/test_p0_03_quote_fund_trio.py::test_items_of_approved_quote_must_be_locked -q` -> passed。
  - 回归：`.venv/bin/python -m pytest tests/audit_p0/test_p0_03_quote_fund_trio.py -q` -> 3 passed；`.venv/bin/python -m pytest tests/api/test_sales.py::TestQuoteManagement::test_create_quote_version tests/api/test_sales.py::TestQuoteManagement::test_create_quote_version_inherits_presale_solution_cost_baseline -q` -> 2 passed；`.venv/bin/python -m pytest tests/api/test_sales_quotes_api.py::TestSalesQuotesAPI::test_quote_items_management -q` -> skipped（既有 smoke 对 `/quotes/1/items` 无数据时跳过）。
  - 静态检查：`py_compile` passed；`ruff check app/models/sales/quotes.py app/api/v1/endpoints/sales/quote_items.py tests/api/test_sales_quote_item_contracts.py` -> All checks passed。

## 2026-07-03 继续：功能审计 SALES-04 修复（回款登记勾稽上限与错配门禁）

- 修复项：`SALES-04`，`/sales/payments/records` 以发票字段承载回款记录，但登记/更新回款无金额上限，且核销接口忽略路径上的 `payment_id`，可拿 A 记录核销 B 发票；写入口也未按合同负责人做权限过滤。
- 根因：
  - `create_payment_record()` 按合同取第一张 `ISSUED` 发票后直接 `new_paid = current_paid + amount`，没有校验 `amount <= unpaid`。
  - `update_payment_record()` 可把发票 `paid_amount` 直接设置到超过发票总额。
  - `match_payment_to_invoice()` 完全忽略路径 `payment_id`，只按 query `invoice_id` 改目标发票。
  - 列表端原来按 `Invoice.owner_id` 过滤，但发票模型没有该字段；写入口没有复用财务数据权限过滤。
- 改动：
  - `app/api/v1/endpoints/sales/payments/payment_records.py`：新增 `_apply_invoice_scope()`，发票/回款统一按 `Contract.sales_owner_id` 走销售财务数据权限过滤。
  - 登记回款时只选择仍有未收金额的已开票发票；`amount` 超过该发票未收金额时拒绝，避免 `unpaid_amount` 为负。
  - 更新回款时拒绝把 `paid_amount` 设置到超过发票总额。
  - 核销接口要求路径 `payment_id` 与 query `invoice_id` 一致，并保留 `match_amount <= unpaid` 校验。
  - `tests/api/test_sales_payment_record_contracts.py`：新增 API 合约测试，覆盖登记超额、合法全额收清、更新超额、核销错配。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`SALES-04` 标为 `已验证`，P0-0 资金正确性急救包同步。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/api/test_sales_payment_record_contracts.py -q` -> 3 failed，登记超额/更新超额/核销错配均返回 HTTP 200。
  - 绿灯：`.venv/bin/python -m pytest tests/api/test_sales_payment_record_contracts.py -q` -> 4 passed；`.venv/bin/python -m pytest tests/audit_p0/test_p0_04_payment_no_reconciliation.py -q` -> 2 passed。
  - 回归：`.venv/bin/python -m pytest tests/api/test_sales_payments_api.py -q` -> 9 passed, 6 skipped（既有未实现/无数据 skip）；`.venv/bin/python -m pytest tests/api/test_collection_priority_api.py -q` -> 1 passed。
  - 静态检查：`py_compile` passed；`ruff check app/api/v1/endpoints/sales/payments/payment_records.py tests/api/test_sales_payment_record_contracts.py` -> All checks passed。

## 2026-07-03 继续：售前技术支持模块去重清理

- 排查结论：后端三代文件并存（api/presale_ai_* → api/v1/presale_ai_* → endpoints/presale包），存在双前缀重复挂载、方案/赢率两套栈、模板三套表、前端3个孤儿页。
- 本轮清理（presale 路径 143 → 119）：
  - **双前缀**：presale_analytics 原挂 /presale-analytics + /presales 两处；保留前端与契约测试在用的 /presales，删无消费方的 /presale-analytics。
  - **老AI方案栈下线**：app/api/presale_ai_routes.py（generate-solution/solution/{id}/template*/match-templates，写 presale_ai_solution 表）——前端唯一消费方是孤儿页；方案统一走 /presale/proposals/solutions。
  - **异步赢率栈下线**：app/api/v1/presale_ai_win_rate.py（AsyncSession 与同步栈不符）及 api.py/api_lazy.py/api_medium.py 三处挂载；赢率统一走 /presales/predict-win-rate。win_rate_prediction_service 服务层与其单测保留（77 用例仍绿）。
  - **shim 收敛**：删 endpoints/presale_ai_requirement.py、endpoints/presale_mobile.py 两个9行转发壳，api.py 改为直接从 presale 包挂载（路径不变，实测 presale-mobile 9 路径完好）。
  - **前端孤儿页**：删 pages/PresaleAI/(AIWorkbench/AIDashboard)、components/PresaleAI/、services/presaleAIService.js、pages/PresaleBids.jsx（备份在 scratchpad/deleted_presale）。
- 契约测试同步更新：test_presales_contract_api（摘除已下线路由，方案契约改指 /presale/proposals）、test_path_param_route_contracts（去 solution/win-rate 腿）、test_required_query_route_contracts（去 /presale-analytics 前缀腿）。
- 附带修复既有测试债：test_pmo.py 两个立项测试从未建技术评估、被售前评估关卡拦截 400——按业务规则补 COMPLETED 评估后通过。
- 验证：pytest tests/api -k presale 全绿 + test_pmo.py/test_pmo_initiation_service 全绿 + win_rate 服务单测 77 绿；前端 build 通过；实机冒烟：保留路由 200/403(权限)、下线路由 404、启动日志无 presale 加载失败。
- 未动（后续可评估）：presale_ai_solution/presale_solution_templates 两张表及模型（PresaleAiSolution 仍被 solution_version_service/export_service 引用）；presale/statistics 与 presale/analytics 与 presales 三个分析面属"分散"非"重复"。

## 2026-07-03 继续：售前去重收尾——死服务/未挂载路由下线

- 顺着 presale_ai_solution/presale_solution_templates 评估，确认并下线 4 个死文件（备份 scratchpad/deleted_presale）：
  - `app/api/v1/solution_versions.py`——路由从未在任何注册表挂载（方案版本唯一活路径是 /presale/proposals/solutions/{id}/versions）。
  - `app/services/sales/solution_version_service.py`——仅被上述死路由引用。
  - `app/services/presale/presale_ai_export_service.py`——导出 TODO 桩（ROADMAP F10 提过），API 面已随老栈下线，零消费方。
  - `app/services/presale/presale_ai_template_service.py`——复数模板表唯一用户，零消费方。
  - 连带删 2 个 10 行 import 覆盖桩测试。
- 表和模型保留（presale_ai_solution/presale_solution_templates 数据在库，模型导出链未动，仅代码面无人再写）。
- 验证：后端重启 0 加载失败；tests/api -k 'presale or solution' 80 全绿；auto 覆盖测试对已删模块正确 skip（try/except ImportError）；test_ppt_generator_auto 的 2 个失败经 stash 对照确认为既有债（构造器签名，与本次无关）；test_services_p5_coverage 的模板服务用例引用本就不存在的顶层路径，属既有失败。
