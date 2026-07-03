# PROJECT_NOTES

## 2026-07-03 继续：功能审计 SALES-06/07 修复（销售预测接线真算法 + 前端去假）

- 修复项：`SALES-06`（全局 P0#15，预测接口整文件硬编码，SalesForecastService 500 行真实现是死代码）+ `SALES-07`（ForecastDashboard 假数据兜底、AI 预测卡纯常量）。
- 后端：
  - 真服务修模型漂移：`Contract.status` 大写→现行小写词表（兼容历史大写）、`Opportunity.estimated_amount`→`est_amount`、去掉不存在的 `outcome` 列、漏斗只统计 STAGE_WIN_RATES 的 5 个非终态阶段。
  - `company-overview` 端点接线真服务（已签合同 + 漏斗 est_amount×阶段赢单率 + 季节因子）。
  - 其余 8 个端点（团队/个人分解、准确性、驾驶舱、增强预测族）整段硬编码且前端零调用，统一 501 下架（同 MISC-01 止损口径），detail 指引用 company-overview。
  - `tests/audit_p0/test_p0_15_forecast_hardcoded.py` 驾驶舱用例更新口径：501 止损或 200 无常量皆合格。
- 前端 ForecastDashboard：
  - AI 预测卡改调真接口 `/sales/forecast/forecast/company-overview`，失败显式"预测服务暂不可用"；漏斗改真实枚举键（STAGE_LABELS）。
  - 假兜底全清：目标汇总（5000万/2850万常量）、团队（华南/华东/华北演示区）、个人（张三李四）→ 空态；"驾驶舱"tab 整段编造数字（新客户 106.7%/客单价 158 万/红绿灯）下架。
- 验证：`tests/unit/test_sales_forecast_wiring.py` 3 项红转绿（真数据计算/端点接线/8 端点 501）；P0-15 复现 2 项过；`import app.main` 通过；`npm run build` + eslint 通过。
- 残留：SALES-08（目标 actual_value 自动回填）待修——SalesTeamService 已有目标实际值计算逻辑（SALES-15 补的），可复用；团队/个人预测分解做实排期在 ROADMAP F6。

## 2026-07-03 继续：功能审计 PROJ-21 修复（项目变更通知）

- 修复项：`PROJ-21`，`ProjectChangeRequestsService` 中变更提交后的团队通知、审批结果通知都是 TODO/pass，业务状态已变但无真实站内通知。
- 改动：
  - `create_change_request()`：`notify_team=True` 时，向项目 PM 发送 `PROJECT_CHANGE_SUBMITTED` 站内通知。
  - `approve_change_request()`：审批通过/拒绝/退回后，向提交人发送 `PROJECT_CHANGE_{decision}` 站内通知。
  - 新增 `_send_change_notification()`，统一走 `NotificationRequest` + `channels=["system"]` + `force_send=True`；只在真实 SQLAlchemy Session 下发送，避免旧 mock 单测多出 commit。
  - 新增 `tests/unit/test_project_change_notifications_proj21.py`，用真实测试 DB 查询 `notifications` 表。
- 验证：
  - 红灯：`pytest tests/unit/test_project_change_notifications_proj21.py -q` -> 2 failed，无 `notifications` 记录。
  - 绿灯：同命令 -> 2 passed。
  - 相邻回归：`tests/unit/test_project_change_notifications_proj21.py` + 原有创建/审批 mock 用例 -> 6 passed。
  - 项目变更 service 回归（排除既有 `test_get_approval_records_success` raw SQL/mock 测试债）：46 passed。
  - API 旧数据兼容契约：`tests/api/test_path_param_route_contracts.py::test_project_change_routes_tolerate_legacy_nulls_and_old_decisions` -> passed。
  - 静态检查：`py_compile app/services/project_change_requests/service.py tests/unit/test_project_change_notifications_proj21.py` passed；`ruff check` passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROJ-21` 已改为 `已验证`；F3 扩围列表同步标记 `PROJ-21（已验证）`。

## 2026-07-03 继续：功能审计 APPR-22 小切口（调度禁用/导入失败治理）

- 修复项：`APPR-22` 子项③/⑤。
  - ③：`scheduler_task_configs.is_enabled=false` 的 DB 配置在 `_load_task_config_from_db()` 中被 `SchedulerTaskConfig.is_enabled` 过滤掉，启动时查不到禁用配置，就回落 `scheduler_config.py` 默认 enabled，导致管理员禁用的任务重启后复活。
  - ⑤：调度任务模块/函数导入失败只写日志并跳过，不进入 scheduler failure metrics；`main.py` scheduler 整体导入失败是裸 `except ImportError: pass`。
- 改动：
  - `app/utils/scheduler.py`：DB 配置查询只按 `task_id` 查，不再过滤 `is_enabled`；返回 `{"enabled": False, "cron": ...}` 后由 `init_scheduler()` 原有逻辑跳过注册。
  - `app/utils/scheduler.py`：任务解析/注册失败调用 `record_job_failure(task_id, 0.0, timestamp)`，监控面能看到注册失败。
  - `app/main.py`：scheduler 整体导入失败改为记录 `定时任务调度器导入失败` 错误日志，不再静默吞掉。
  - `tests/unit/test_scheduler_utils.py`：新增 APPR-22 契约，锁定禁用配置必须可加载、且启动时不会调用 `scheduler.add_job()`。
  - `tests/unit/test_scheduler_utils.py`：新增导入失败入 metrics、main 外层 ImportError 不静默的契约。
- 验证：
  - 红灯：`pytest tests/unit/test_scheduler_utils.py::TestSchedulerDbConfig -q` -> 2 failed，禁用配置加载为 `None` 且被重新注册。
  - 绿灯：同命令 -> 2 passed；`tests/unit/test_scheduler_utils.py` -> 18 passed。
  - 红灯：`pytest tests/unit/test_scheduler_utils.py::TestSchedulerDbConfig::test_init_scheduler_records_failure_for_unresolvable_task -q` -> failed，导入失败未调用 `record_job_failure`。
  - 红灯：`pytest tests/unit/test_scheduler_utils.py::TestSchedulerStartup::test_main_scheduler_import_error_is_logged -q` -> failed，`main.py` 没有错误日志文本。
  - 绿灯：`tests/unit/test_scheduler_utils.py` -> 20 passed；`import app.main` 路由加载成功。
  - 相邻回归：`tests/audit_p0/test_p0_10_stub_tasks.py tests/unit/test_j3_scheduled_tasks.py::TestStubTasks tests/unit/test_scheduler_utils.py` -> 47 passed。
  - 静态检查：`py_compile app/utils/scheduler.py app/main.py tests/unit/test_scheduler_utils.py` passed；`ruff check` passed。
- 台账：`APPR-22` 从 `待修` 改为 `修复中`；子项①/③/⑤已标已回归，②备份自动执行、④第二调度器监控仍待做。

## 2026-07-03 继续：功能审计 PRE-21 验收收口（AI job 恢复）

- 收口项：`PRE-21` 之前代码已补 startup 恢复和轮询惰性超时，但 `FUNCTIONAL_AUDIT_TRACKER.md` 仍是 `已修待验`。
- 本轮复核：
  - `pytest tests/unit/test_ai_job_recovery.py -q` -> 4 passed。
  - `import app.main` -> 路由加载成功（3004 routes），startup 接线源码包含 `recover_stale_jobs`。
- 台账：`PRE-21` 已从 `已修待验` 改为 `已验证`；F3 扩围列表同步标记 `PRE-21（已验证，含 APPR-22①）`。

## 2026-07-03 继续：功能审计 AS-23 收口（after_sales 写端通知）

- 修复项：补齐 `AS-23` 剩余旧 `app/api/v1/endpoints/after_sales.py` 项目售后写端；原反馈、保养、support ticket、质保、备件、现场服务、满意度、知识库、support ticket 升级均只写业务表，不产生真实站内通知。
- 改动：
  - `after_sales.py` 新增 `_send_after_sales_notification()`，统一发 `AFTER_SALES_*` 站内通知，强制 `channels=["system"]`、`force_send=True`。
  - 项目上下文写端默认通知项目 PM；知识库这类无项目上下文写端通知创建人。
  - `create_maintenance()` / `create_field_service()` 的日期参数改为 `date`，与 SQLAlchemy `Date` 字段和 FastAPI 参数解析一致。
  - 所有写端在业务 `commit + refresh` 后发通知；通知异常只记日志，不阻断主业务提交。
- 验证：
  - 红灯：`pytest tests/unit/test_service_ticket_notifications_as23.py -q` -> 3 failed，命中 after_sales 写端没有 `notifications` 记录。
  - 绿灯：同命令 -> 7 passed，覆盖服务工单 lifecycle + after_sales 项目售后写端 + 知识库创建。
  - 相邻回归：`tests/unit/test_service_ticket_notifications_as23.py tests/unit/test_service_tickets_service.py tests/unit/test_service_tickets_service_coverage.py tests/unit/test_status_update_service.py` -> 62 passed。
  - 合并回归：`tests/unit/test_sla_service_coverage.py tests/unit/test_batch2_sla_service.py tests/unit/test_sla_as06.py tests/unit/test_service_ticket_notifications_as23.py tests/unit/test_service_tickets_service.py tests/unit/test_service_tickets_service_coverage.py tests/unit/test_status_update_service.py` -> passed。
  - 静态检查：相关文件 `py_compile` passed；`ruff check` passed；`git diff --check` passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-23` 已更新为 `已验证`；F3 扩围列表同步标记 `AS-23（已验证）`。

## 2026-07-03 继续：功能审计 AS-23 小切口（服务工单事件通知）

- 修复项：`AS-23` 的服务工单 lifecycle 部分；原创建/派工端点会写业务状态和 CC 记录，但没有真实通知，且 `ServiceTicketCcUser.notified_at` 在未发送通知时直接置当前时间，属于假成功。
- 改动：
  - 新增 `app/services/service/service_ticket_notifications.py`，统一发送服务工单站内通知，强制 `channels=["system"]`，返回实际成功用户 ID。
  - `create_service_ticket()`：创建时通知处理人、报告人、CC；CC 的 `notified_at` 仅在对应用户通知成功后写。
  - `assign_service_ticket()`：派工时通知新处理人、报告人、CC；CC 的 `notified_at` 同样改为发送成功后写。
  - `update_service_ticket_status()` / `close_service_ticket()`：状态变更和关闭后通知处理人、报告人、CC。
  - 新增 `app/services/unified_notification_service.py` 兼容 re-export，恢复旧测试/旧调用 patch 路径。
- 验证：
  - 红灯：`pytest tests/unit/test_service_ticket_notifications_as23.py -q` -> 2 failed，创建/派工都没有 `notifications` 记录。
  - 绿灯：扩展后同命令 -> 4 passed，覆盖创建/派工/状态变更/关闭。
  - 相邻回归：`tests/unit/test_service_tickets_service.py tests/unit/test_service_tickets_service_coverage.py tests/unit/test_status_update_service.py tests/unit/test_service_ticket_notifications_as23.py` -> passed。
  - 静态检查：相关文件 `py_compile` passed；`ruff check` passed。
- 残留：旧 `app/api/v1/endpoints/after_sales.py` 项目售后写端已在后续 AS-23 收口小切口补齐，`AS-23` 台账已改为 `已验证`。

## 2026-07-03 继续：功能审计 SALES-16 修复（AI 助手降级标注 + 流失清单口径）

- 修复项：`SALES-16`，AI 销售助手 5 个方法（话术/方案/竞品/谈判/流失）AI 不可用时静默返回罐头文本冒充 AI 输出；流失清单 20 客户全走规则分但无任何标注。
- 代码面：
  - `sales_ai_assistant_service` 新增 `_mark_ai`/`_mark_degraded`：真 AI 输出标 `ai_generated=true`；降级统一标 `ai_generated=false + degraded=true + degraded_reason`。
  - 流失清单定口径：批量扫描用规则（20 客户逐个调 LLM 不现实），显式标 `scoring_method=rule_scan` + 每项 `analysis_source=rule` + note 指引单客户深评走 predict_churn_risk（真 AI）。
  - 前端 `SalesAI/index.jsx` 新增 `DegradedNotice` 横幅，话术/方案/竞品/流失四张卡片接入——降级内容对用户可见地标黄。
- 验证：红灯 4 项 → 绿灯 `tests/unit/test_sales_ai_degradation_marking.py` 4 passed；既有 `test_sales_ai_assistant_service.py` 4 passed；`npm run build` 通过。`test_sales_ai_assistant_deep.py` 2 项失败经 HEAD worktree 证实为既有测试债（调用签名过时）。
- 至此审计"AI mock 降级无标记静默污染真数据"共性根因在 AI 线全部收口（方案入库/纪要解析/BOM 成本/销售助手/流失清单）。

## 2026-07-03 继续：功能审计 AS-06 修复（SLA 历史策略激活 + 定时预警）

- 修复项：`AS-06`，SLA 服务本体有计时逻辑，但历史 `sla_policies.is_active` 全为 `NULL` 时策略匹配/预警查询被裸布尔过滤排除；同时调度配置没有 SLA 扫描任务，超时/预警链路不会自动运行。
- 改动：
  - `sla_service` 增加历史兼容过滤：`is_active=True OR is_active IS NULL`，覆盖精确/兜底策略匹配和 warning 查询。
  - `sync_ticket_to_sla_monitor()` 支持传入 `current_time`，调度扫描和测试能用同一时点更新状态。
  - 新增 `check_sla_warnings_task`：每小时扫描未关闭服务工单，同步/创建 SLA monitor，筛出 WARNING monitor，生成去重 `AlertRecord`，调用现有通知入口，并标记 response/resolve warning sent。
  - `scheduler_config/alerting.py` 注册 `check_sla_warnings`，统一导出到 `app.utils.scheduled_tasks`。
- 验证：
  - 红灯：`pytest tests/unit/test_sla_as06.py -q` -> 4 failed，命中历史 `NULL is_active` 匹配不到、warning 查不出、调度任务不存在、task callable 缺失。
  - 绿灯：同命令 -> passed；`tests/unit/test_sla_service_coverage.py tests/unit/test_batch2_sla_service.py tests/unit/test_sla_as06.py` -> passed。
  - 相邻回归：`tests/unit/test_scheduled_alert_tasks.py tests/unit/test_j3_scheduled_tasks.py::TestSendAlertNotifications tests/unit/test_scheduled_tasks_h2.py::TestAlertTasksExtended::test_send_alert_notifications_no_pending_alerts` -> passed。
  - 静态检查：`py_compile` passed；`ruff check` passed；`git diff --check` passed；调度元数据解析 `check_sla_warnings -> app.utils.scheduled_tasks.check_sla_warnings_task` 成功。
- 残留：本项不直接修改生产/本地 `data/app.db` 的历史策略行；代码已兼容 NULL，后续若要数据清洗可单独迁移为 `is_active=1`。AS-23 的售后业务事件通知产生端已在后续小切口处理。

## 2026-07-03 继续：功能审计 AS-25 修复（预警订阅接收人与 Webhook 兼容）

- 修复项：`AS-25`，预警订阅默认接收人为空、旧 `notification_utils` resolver 无人时硬塞 user_id=1、Webhook 通道只认 `WECHAT_WEBHOOK_URL`；顺带发现顶层旧入口 `app.services.notification_service` 已不存在，旧通知调用面和测试会直接导入失败。
- 改动：
  - `AlertSubscriptionService.get_notification_recipients()` 无订阅/无规则指定用户时，默认取预警处理人、确认人、创建/更新人、项目 PM/项目负责人，不再直接返回空。
  - `notification_utils.resolve_recipients()` 对齐同一默认收件人口径；无人可通知时返回 `{}`，不再虚构 admin/user_id=1。
  - 新增兼容入口 `app/services/notification_utils.py` 与 `app/services/notification_service.py`，恢复旧 import path；旧 `NotificationService` facade 内部转 `NotificationRequest` 调统一通知服务。
  - `WebhookChannelHandler` 支持通用 `WEBHOOK_URL`，并保留 `WECHAT_WEBHOOK_URL` 兼容；`config.py` 增加 `WEBHOOK_URL`。
- 验证：
  - 红灯：`pytest tests/unit/test_alert_subscription_service_coverage.py tests/unit/test_notification_utils_as25.py tests/unit/test_webhook_handler_coverage.py -q` -> 4 failed，分别命中默认收件人空、旧工具路径不可导入、Webhook 通用 URL 不生效。
  - 绿灯：同命令 -> passed；旧通知 facade 全套 `tests/unit/test_notification_service_n3.py` -> passed。
  - 相邻回归：`tests/unit/test_i6_core_services.py::TestNotificationService tests/unit/test_notification_service_deep.py tests/unit/test_views_and_others_auto.py::TestNotificationService tests/unit/test_notification_utils_service.py tests/unit/test_notification_utils.py tests/unit/test_webhook_handler_coverage.py tests/unit/test_alert_subscription_service_coverage.py tests/unit/test_notification_utils_as25.py` -> passed。
  - 静态检查：`py_compile` passed；`ruff check` passed；`git diff --check` passed。
- 残留：本项不解决“哪些业务端点必须产生售后事件通知”的 AS-23；该项后续已补齐。SLA 策略激活/调度已由后续 AS-06 单独处理。

## 2026-07-03 继续：功能审计 PRE 详#10/#7 修复（mock 方案禁入库 + BOM 真实询价）

- 修复项：审计详#10（generate_solution 不检测 mock，AI 故障时"自动上料机"演示方案以 0.8 置信度入库；BOM 单价写死 10000 元/"推荐供应商A"/交期 30 天）+ 详#7（纪要解析后台任务 mock 也标 SUCCESS）。
- 代码面：
  - `ai_client_service` 新增共享守卫 `is_mock_response()`（模型名 -mock 后缀判定），业务写库前必须过闸。
  - `generate_solution`：mock 响应直接 ValueError 拒绝入库（走 ai_job 时任务标 FAILED，错误信息指向 AI 配置）。
  - `_handle_parse_meeting_minutes`：mock 同样 raise，job 不再假 SUCCESS。
  - `_generate_bom_item` 接真实数据源：物料库 `materials`（最近采购价优先，其次标准价）→ AI 模块库 `ai_standard_modules.ref_cost`；查无价 `unit_price=null` 标"待询价"；供应商/交期无真实数据源，置 null 宁缺毋假。
- 验证：红灯 4 项 → 绿灯 `tests/unit/test_presale_ai_mock_guard.py` 4 passed + bridge 套件 7 passed；相邻回归 10 passed；`import app.main` 通过。
- 备注：方案生成 mock 检测后，AI 密钥配错时工作台会显式报"AI 服务不可用"而非静默出演示方案——这是预期行为变化。

## 2026-07-03 继续：功能审计 APPR-16 修复（ECN 超期检查调度路径）

- 修复项：`APPR-16`，`check_ecn_overdue` enabled 调度任务配置到不存在的 `app.services.ecn_scheduler`，APScheduler 初始化时导入失败并跳过注册，ECN 超期检查实际不运行。
- 改动：
  - `app/utils/scheduler_config/other.py`：模块路径改为真实实现 `app.services.ecn.ecn_scheduler`，callable 仍为 `run_ecn_scheduler`。
  - `tests/unit/test_scheduler_utils.py` 新增配置契约，锁定 `check_ecn_overdue` 必须能经 `_resolve_callable()` 解析到真实 `run_ecn_scheduler`。
- 验证：
  - 红灯：`pytest tests/unit/test_scheduler_utils.py::TestResolveCallable::test_registered_ecn_overdue_job_resolves_real_callable -q` -> failed，`ModuleNotFoundError: No module named 'app.services.ecn_scheduler'`。
  - 绿灯：同命令 -> 1 passed；`pytest tests/unit/test_scheduler_utils.py::TestResolveCallable -q` -> 4 passed。
- 残留：本项只修 ECN job 注册路径；`APPR-22` 里导入失败可见化已在后续小切口处理，备份自动执行和第二调度器监控仍单独保留。

## 2026-07-03 继续：功能审计 MISC-03 修复（预警超时升级扫描）

- 修复项：`MISC-03`，`check_alert_timeout_escalation()` 用 `not AlertRecord.is_escalated` 构造 SQLAlchemy 查询，实际会把列对象变成 Python `False`，导致过滤条件短路，升级扫描永远查不到待升级预警。
- 改动：
  - `app/utils/alert_escalation_task.py` 改为 SQL 表达式：`AlertRecord.is_escalated.is_(False)` 或历史 NULL。
  - 扫描状态纳入 `OPEN/PENDING/ACKNOWLEDGED/PROCESSING`，和 APPR-17 的 `PENDING→OPEN` 状态流转对齐。
  - `tests/unit/test_utils_missing.py` 增加查询契约，锁定不能出现裸 `False` 条件、必须扫描 `OPEN`；旧升级用例改为验证超时 INFO 预警会升级到 WARNING 并发送升级通知。
- 验证：
  - 红灯：`pytest tests/unit/test_utils_missing.py::TestAlertEscalationTask::test_check_alert_timeout_escalation_query_targets_open_unescalated_alerts tests/unit/test_utils_missing.py::TestAlertEscalationTask::test_check_alert_timeout_escalation -q` -> 1 failed，捕获到过滤条件 `[status IN (...), False]`。
  - 绿灯：同命令 -> 2 passed；`pytest tests/unit/test_utils_missing.py::TestAlertEscalationTask -q` -> 6 passed。
- 残留：本项只修升级任务自身查询和状态覆盖；订阅默认接收人与 webhook 渠道问题仍归 `AS-25`，备份/调度监控残项仍归 `APPR-22`。

## 2026-07-03 继续：售前 AI 前端闭环重建（requirement_analysis_id 全链贯通）

- 背景：旧售前 AI 方案栈前端在去重重构中下线，方案生成连后端 HTTP 端点都没有；`presaleAIService.js` 不存在但测试文件还在（孤儿测试债）。PRE-10 后端贯通后前端无处可接。
- 后端：
  - `ai_job_service` 注册 `presale_solution_generation` handler（复用后台任务基建，单次重 AI 调用不占同步请求）；
  - 新增 `POST /presale/ai/generate-solution`（提交返回 job_id，轮询 /ai-jobs/{id}）；
  - `app/models/__init__.py` 补注册 ai_feedback/ai_job 模型（隔离测试库 create_all 此前漏建表，靠测试文件自身 import 碰巧过）。
- 前端：
  - 重建精简版 `services/presaleAIService.js`：analyze/getAnalysis/confirm/generate-solution/three-tier/getJob 六个方法；孤儿测试同路径替换为对齐新服务面的活测试（5 用例）。
  - 新页 `pages/PresaleAIWorkbench.jsx`（路由 `/presales/ai-workbench`，菜单"AI需求工作台"挂售前技术组）：需求只录一次——分析 → 确认回填商机（显示补齐字段）→ 生成方案/三档报价均自动带 `requirement_analysis_id`，后台任务轮询展示。
- 验证：后端 bridge 套件 11 passed（含 handler 注册+端点挂载契约）；前端 42 passed（服务 5 + 页面 4 + 路由回归）；`npm run build` 通过；TestClient 验证 generate-solution 端点 401 权限门。
- 边界：方案生成默认 generate_architecture/generate_bom=false（BOM 成本假数据是 PRE 详#10 待修项，不放大）；PRE 详#10 mock 方案可入库仍待修。

## 2026-07-03 继续：功能审计 APPR-17 修复（预警通知状态流转）

- 修复项：`APPR-17`，`send_alert_notifications()` 每轮只取最新 50 条 `AlertRecord.status='PENDING'`，且通知创建/发送尝试后不流转 `AlertRecord` 状态，导致老预警永久留在 PENDING 窗口外。
- 根因：
  - `app/utils/scheduled_tasks/alert_tasks.py` 对 `AlertRecord` 使用 `triggered_at.desc()`，只优先处理最新预警。
  - 预警通知生成/发送后只更新 `AlertNotification`，没有把 `AlertRecord` 从“等待通知生成”的 `PENDING` 推到真正业务待处理态。
- 改动：
  - `send_alert_notifications()` 改为 `triggered_at.asc().nulls_last()`，优先处理最老 PENDING，避免积压饿死。
  - 每个 pending alert 完成通知生成/发送尝试后，若仍为 `PENDING`，推进为 `OPEN`，不冒充用户确认；返回值与日志新增 `opened_alerts`。
  - `tests/audit_p0/test_p0_11_notification_fake_success.py` 新增两个契约：通知尝试后 alert 必须离开 PENDING；积压扫描必须最老优先。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_11_notification_fake_success.py -q` -> 2 failed，缺 `opened_alerts` 且 order_by 为 `triggered_at DESC`。
  - 绿灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_11_notification_fake_success.py -q` -> 7 passed。
  - 相邻回归：`.venv/bin/python -m pytest tests/unit/test_scheduled_alert_tasks.py tests/unit/test_j3_scheduled_tasks.py::TestSendAlertNotifications tests/unit/test_scheduled_tasks_h2.py::TestAlertTasksExtended::test_send_alert_notifications_no_pending_alerts -q` -> 16 passed。
  - 静态检查：`py_compile app/utils/scheduled_tasks/alert_tasks.py tests/audit_p0/test_p0_11_notification_fake_success.py` passed；`ruff check app/utils/scheduled_tasks/alert_tasks.py tests/audit_p0/test_p0_11_notification_fake_success.py tests/unit/test_scheduled_alert_tasks.py` passed；`git diff --check` passed。
- 残留：未直接改写 `data/app.db` 里的历史 841 条；修复后调度会按最老优先逐批把 PENDING 推到 OPEN，一次性生产清理仍应走运维窗口。

## 2026-07-03 继续：AI 效果看板（持续优化环节的人工消费入口）

- 新增 `pages/AIEffectiveness.jsx`（路由 `/ai/effectiveness`，菜单"AI效果看板"挂客户关系层 AI 组）：
  - 采纳率统计表：GET /ai-feedback/stats，feature_key 中文名映射，采纳/驳回/部分/采纳率；
  - 报价对账：GET /ai-feedback/quote-calibration，三档平均偏差卡片 + 逐单明细（成交金额 vs 三档、最贴近档）。
- 验证：页面测试 3 passed（含空态）；路由回归 salesCompetitorAnalysisStopgap 2 passed；`npm run build` 通过。
- 至此闭环六环节全部有人机接口：需求识别/判断分析（存量）→ 执行动作（确认回填+G2 门）→ 结果反馈（反馈按钮+处置留痕）→ 持续优化（效果看板）。

## 2026-07-03 继续：AI 闭环前端接入（反馈按钮 + 评审处置入口）

- 背景：反馈闭环/G2 风险门后端已通，但对人不可用——前端无反馈入口、评审卡片无处置动作。
- 代码面：
  - 新增 `components/ai/AiFeedbackButtons.jsx`：通用采纳/驳回按钮（驳回强制写原因），打 `POST /ai-feedback`；任何 AI 卡片挂上即接入闭环。
  - 新增 `components/opportunity/SolutionReviewCard.jsx`：方案评审卡片抽组件，HIGH 风险显示 G2 拦截提示 + "已消除风险/带险推进"处置按钮（强制写理由），调 `POST /sales/opportunities/{id}/solution-review/resolution`。
  - `OpportunityDetail.jsx`：评审卡片换用新组件；推进建议/报价估算/验收标准三张 AI 卡片挂反馈按钮（feature_key：opportunity_next_action / opportunity_quote_estimate / opportunity_acceptance_criteria）。
- 验证：红灯（组件不存在收集失败）→ 绿灯组件测试 7 passed；连同 OpportunityManagement 回归 16 passed；`npm run build` 通过（仅既有 chunk 警告）。
- 备注：售前方案生成/三档报价前端页已在早前去重重构中下线，`requirement_analysis_id` 前端传参待售前 AI 页重建时接（后端已兼容）。

## 2026-07-03 继续：AI 报价对账（持续优化环节数据地基第一块）

- 背景：AI 三档报价与实际成交从无勾稽，报价规则无从校准（backlog 中"报价→实际闭环校准"一直未做）。
- 代码面：
  - 新增 `app/services/ai_quote_calibration_service.py`：链路 AI 报价(售前工单)→工单商机→已签合同（signed/executing/completed），逐工单报各档偏差+最贴近档位，汇总按档平均绝对偏差与最贴近档分布；同工单同档多次生成取最新；未成交计 unmatched 不进偏差。
  - 新增端点 `GET /ai-feedback/quote-calibration`。
  - 边界：实际成本对账待成本归集口径修复（MISC-09/PROJ-11）后扩展，本轮只对成交金额。
- 验证：红灯 4 项（模块不存在/种子 created_by 缺）→ 绿灯 `tests/unit/test_ai_quote_calibration_contracts.py` 4 passed + AI 反馈/闸门套件 12 passed；TestClient 动态验证端点 401 权限门；`import app.main` 通过。

## 2026-07-03 继续：AI 方案评审嵌入 G2 闸门（决策流改造第一处）

- 背景：ai-solution-review（PRE-19 正面确认项）结果不落库、看完即丢，AI 初判无法进决策流。本次把"未处置的 HIGH 风险"变成 G2（商机→报价）硬约束——AI 出风险清单（初步判断），人处置留痕（关键判断+责任承担），闸门消费处置状态（决策流硬约束）。
- 代码面：
  - 新增 `sales/utils/solution_review.py`：`persist_solution_review`（评审结果存 opportunity_requirements.extra_json，覆盖旧评审并重置处置态）、`resolve_solution_review`（RESOLVED/ACCEPT_RISK 双动作，强制写理由，留人/时间痕，落 AI 反馈）、`unresolved_high_risk`（G2 消费口）。
  - `validate_g2_opportunity_to_quote` 增加可选 db 参数：有未处置 HIGH 风险即拦截；**未做过评审不新增拦截**（评审暂不强制，不破坏存量流程）；闸门提交端点传 db。
  - `ai-solution-review` 端点评审后自动落库；新增 `POST /opportunities/{id}/solution-review/resolution` 处置端点。
- 验证：
  - 红灯：`tests/unit/test_ai_review_gate_contracts.py` 4 项（持久化/拦截/处置放行+反馈/处置校验）。
  - 绿灯：4 passed；相邻回归 `test_api_p6_coverage + integration/sales/test_opportunities + ai_feedback + requirement_bridge` 134 passed；`import app.main` 通过。
- 后续：前端商机页评审卡片需加"处置"入口（调 resolution 端点）；G2 拦截文案已给操作指引；评审是否转强制（无评审不能过 G2）待业务拍板后一行切换。

## 2026-07-03 继续：AI 反馈闭环第一步（采纳/驳回记录 + 采纳率统计）

- 背景：AI 融入业务流程闭环愿景（需求识别→信息收集→判断分析→执行动作→结果反馈→持续优化）中"结果反馈"环节此前为 0——所有 AI 建议看完即走，无采纳记录、无采纳率、无从校准。
- 代码面：
  - 新增 `app/models/ai_feedback.py`：`ai_output_feedbacks` 表（feature_key/ref_type/ref_id/verdict/reason/detail/created_by），append-only。
  - 新增 `app/services/ai_feedback_service.py`：`record()`（verdict 只认 ADOPTED/REJECTED/PARTIAL）+ `stats()`（同一产出多次反馈按最新去重，按 feature_key 出采纳率）。
  - 新增端点 `POST /ai-feedback`（记录）+ `GET /ai-feedback/stats`（采纳率统计）；挂载在 ai_jobs 之后。
  - 第一处业务接线：PRE-10 确认端点 `confirm_and_backfill` 自动落一条 ADOPTED 反馈（确认即采纳，随同事务提交）。
  - 迁移 `migrations/20260703_ai_output_feedback_sqlite.sql` 已应用到 data/app.db。
- 验证：
  - 红灯：`tests/unit/test_ai_feedback_contracts.py` 收集失败（模块不存在）。
  - 绿灯：4 passed + 桥接套件回归 5 passed。
  - 动态：TestClient 起真实 app，`GET /ai-feedback/stats`、`POST /ai-feedback` 未认证 401（路由真实挂载 + 权限门生效），路由加载失败 0 项。
- 后续接线点（前端加"采纳/驳回"按钮即可）：三档报价、谈判建议、流失预测、经营简报行动项、方案评审；经营侧月度复盘用 stats 出各 AI 功能真实采纳率。

## 2026-07-03 继续：功能审计 PRE-10 修复（AI 需求分析下游贯通）

- 修复项：`PRE-10`，AI 需求分析结果数据孤岛：方案生成只存 requirement_analysis_id 不读内容（需求靠前端重贴）、三档报价只认手填 base_requirements、分析结果永不回填商机，与商机域 ai-enrich-requirement 两套抽取互不相通。
- 代码面：
  - 新增 `app/services/presale/requirement_analysis_bridge.py`：`build_requirements_payload`（方案生成结构化输入）、`compose_requirements_text`（报价文本输入）、`confirm_and_backfill`（确认+回填）。
  - `presale_ai_service.generate_solution` 增加 `_resolve_requirements`：requirement_analysis_id 自动带出分析内容打底，显式 requirements 字段覆盖，两者皆空 ValueError；`SolutionGenerationRequest.requirements` 转可选。
  - `presale_ai_quotation_service` 新增 `resolve_base_requirements` 并接入三档报价入口；`ThreeTierQuotationRequest` 增加 `requirement_analysis_id`，`base_requirements` 转可选。
  - 新增端点 `POST /presale/ai/analysis/{id}/confirm`：人工确认（状态 approved）后增量回填商机 `opportunity_requirements`——只补空缺字段、人工值不覆盖，完整分析内容带确认人/时间挂 `extra_json` 溯源。
- 验证：
  - 红灯：`tests/unit/test_presale_requirement_bridge.py` 5 项先失败（schema 必填/方法不存在/桥接模块不存在）。
  - 绿灯：同套件 5 passed。
  - 相邻回归：presale_ai_service/quotation/schemas 套件 82 passed / 16 skipped；`tests/unit/test_presale_ai_service.py` 32 项失败为既有测试债（patch 兼容壳旧路径），已用 HEAD 临时 worktree 证实与本次改动无关。
  - `py_compile` 全部触达文件 + `import app.main` 通过。
- 残留：前端方案生成/三档报价页面尚未传 requirement_analysis_id（后端已兼容旧调用方式）；确认回填目前只写 opportunity_requirements，不动商机主表字段（商机主表回填走已有 ai-enrich-requirement）。

## 2026-07-03 继续：功能审计 PRE-21 修复（AI 后台任务重启恢复与超时）

- 修复项：`PRE-21`（含 APPR-22① 并入），进程内线程池不跨重启，DB 里遗留 PENDING/RUNNING 任务永久卡死，轮询无超时判定。
- 代码面：
  - `ai_job_service.recover_stale_jobs()`：启动时把遗留 PENDING/RUNNING 统一标 FAILED（"进程重启导致任务中断，请重新提交"）；会话工厂运行时解析（支持测试注入 db）。
  - `get()` 轮询惰性超时：超过 `AI_JOB_MAX_RUNTIME_SECONDS`（默认 1800s，env 可配）仍未完成即标 FAILED。
  - `main.py` startup 接线 recover_stale_jobs（异常不阻断启动）。
- 验证：红灯 3 项（恢复/超时/startup 接线）→ 绿灯 `tests/unit/test_ai_job_recovery.py` 4 passed；`import app.main` 通过。

## 2026-07-03 继续：功能审计 AS-03 修复（Redis 通知队列默认同步止血）

- 修复项：`AS-03`，通知队列“有生产者无消费者”：Redis 可用时会把通知标记为 `QUEUED`，但默认没有 worker 进程消费；同时 `scripts/notification_worker.py` 仍导入已不存在的旧模块路径。
- 止血策略：
  - `app/core/config.py`：新增 `NOTIFICATION_QUEUE_ENABLED=False`，生产默认不启用异步通知队列。
  - `app/services/notification/notification_queue.py`：未显式启用队列时，`enqueue_notification()` 返回 `False`，上层自动同步 `dispatch`，避免“配置 Redis 即通知黑洞”；`dequeue_notification()` 同样受开关约束。
  - `scripts/notification_worker.py`：修正为当前模块路径 `app.services.notification.notification_queue` / `notification_dispatcher`，确保后续显式启用队列时 worker 可导入。
  - `tests/audit_p0/test_p0_11_notification_fake_success.py`：新增 Redis 存在时默认同步发送、worker 脚本导入当前模块的审计契约。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_11_notification_fake_success.py -q` -> 2 failed，Redis 存在时仍 queued，worker 导入旧路径失败。
  - 绿灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_11_notification_fake_success.py tests/unit/test_notification_queue_service_standalone.py tests/unit/test_scheduled_base_tasks.py::TestEnqueueOrDispatchNotification -q` -> 17 passed。
  - 通知整包：`.venv/bin/python -m pytest tests/audit_p0/test_p0_11_notification_fake_success.py app/tests/services/notification/test_email_handler.py app/tests/services/notification/test_sms_handler.py tests/unit/test_notification_channels_email.py tests/unit/test_notification_channels_sms.py tests/unit/test_notification_sender_coverage.py tests/unit/test_notification_queue_service_standalone.py tests/unit/test_scheduled_base_tasks.py::TestEnqueueOrDispatchNotification -q` -> 48 passed。
  - 静态检查：`py_compile` passed；`ruff check` 本轮通知触达/队列文件 passed；`git diff --check` passed。
- 残留：`APPR-17` 预警 PENDING 积压、发送后 AlertRecord 状态不流转、历史 841 条积压清理仍未修。

## 2026-07-03 继续：功能审计 AS-02/AS-15 修复（通知触达假成功止血）

- 修复项：`AS-02` + `AS-15`，邮件/短信统一通知通道在没有真实 SMTP/短信网关发送的情况下只写日志就返回 `success=True`；工时提醒邮件发送器还读取旧 `SMTP_*` 配置，与现行 `EMAIL_*` 配置错位。
- 根因：
  - `EmailChannelHandler.send()` 找到用户邮箱后直接 logger.info 并返回成功，没有 SMTP 调用。
  - `SMSChannelHandler.send()` 找到手机号后直接 logger.info 并返回成功，阿里云短信发送函数不在统一通道链路里。
  - `timesheet/reminder/notification_sender.py` 使用 `SMTP_HOST/SMTP_USER`，但配置层定义的是 `EMAIL_SMTP_SERVER/EMAIL_USERNAME`。
- 改动：
  - `app/services/notification/channels/email_handler.py`：补 SMTP 配置校验和真实 `smtplib.SMTP.send_message()`；缺配置、认证配置不完整或 SMTP 异常时返回失败，不再假报送达。
  - `app/services/notification/channels/sms_handler.py`：补短信网关配置校验，接入阿里云 `SendSms` 调用；缺配置、SDK 缺失或网关异常时返回失败。
  - `app/services/timesheet/reminder/notification_sender.py`：邮件发送优先读取现行 `EMAIL_*` 配置，同时兼容旧 `SMTP_*`。
  - 更新通知通道单测，成功路径必须 mock 到真实 SMTP/短信网关调用；新增缺配置失败契约。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_11_notification_fake_success.py -q` -> 2 failed，email/SMS 均 logger.info 后返回 `success=True`。
  - 红灯：`.venv/bin/python -m pytest tests/unit/test_notification_sender_coverage.py -q` -> failed，有 `EMAIL_SMTP_SERVER` 但 sender 仍报“邮件服务未配置”。
  - 绿灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_11_notification_fake_success.py app/tests/services/notification/test_email_handler.py app/tests/services/notification/test_sms_handler.py tests/unit/test_notification_channels_email.py tests/unit/test_notification_channels_sms.py tests/unit/test_notification_sender_coverage.py -q` -> 34 passed。
  - 静态检查：`py_compile` passed；`ruff check` 本轮通知触达文件 passed；`git diff --check` passed。
- 残留：`AS-03` 已在本轮后续修复；`APPR-17` 预警 PENDING 积压/状态不流转仍未修，继续留在 F3。

## 2026-07-03 继续：功能审计 MISC-01 止血（竞品分析假数据下架）

- 修复项：`MISC-01`，竞品分析菜单页前后端双假：后端 `/sales/competitor/competitor/*` 3 个端点硬编码竞品、客户、金额与赢单率；前端 `/sales/competitor-analysis` 页面本地硬编码，不调 API。
- 止血策略：
  - `app/api/v1/endpoints/competitor_analysis.py`：3 个竞品分析端点统一返回 HTTP 501，明确“硬编码演示数据，未接真实数据源”，避免直链继续吐假数据。
  - `frontend/src/components/layout/sidebarConfig/default.js`：移除“对手分析”菜单项。
  - `frontend/src/routes/modules/salesRoutes.jsx`：移除 `/sales/competitor-analysis` 路由。
  - `tests/api/test_competitor_analysis_stopgap_contracts.py`：新增后端契约，锁定 501 且响应中不能包含“竞品 A/宁德时代”等演示数据。
  - `frontend/src/routes/modules/__tests__/salesCompetitorAnalysisStopgap.test.jsx`：新增前端契约，锁定菜单和销售路由不再暴露假页。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/api/test_competitor_analysis_stopgap_contracts.py -q` -> failed，接口仍 200 返回硬编码“竞品 A”等假数据。
  - 红灯：`npm test -- --run src/routes/modules/__tests__/salesCompetitorAnalysisStopgap.test.jsx` -> 2 failed，菜单和路由仍暴露。
  - 绿灯：`.venv/bin/python -m pytest tests/api/test_competitor_analysis_stopgap_contracts.py -q` -> 1 passed。
  - 绿灯：`npm test -- --run src/routes/modules/__tests__/salesCompetitorAnalysisStopgap.test.jsx` -> 2 passed。
  - 相邻回归：`npm test -- --run src/routes/modules/__tests__/salesCompetitorAnalysisStopgap.test.jsx src/routes/modules/__tests__/salesPresaleWorkbenchRoutes.test.jsx` -> 8 passed。
  - 静态检查：`py_compile app/api/v1/endpoints/competitor_analysis.py` passed；`git diff --check` 本轮触达文件 passed。
- 残留：旧前端组件文件仍保留但已无菜单/销售路由入口；后续若要做真竞品分析，应新建真实数据源与页面，而不是复用硬编码页。

## 2026-07-03 继续：功能审计 PROD-14 修复（物料调拨真实库存变动）

- 修复项：`PROD-14`，物料调拨执行端点只把调拨单置为 `EXECUTED`，不扣源库库存、不增目标库库存、不写交易流水；旧 `MaterialTransferService` 还引用不存在的 `ProjectMaterial`，一调用就 `NameError`。
- 根因：
  - `shortage/handling/transfers.py` 的 `/execute` 只改 `material_transfers` 状态，注释里仍写着“需要与库存管理系统集成”。
  - 库存域已有 `TransferService.transfer_stock()`，但调拨执行端点没有接入。
  - `material_transfer_service.py` 遗留项目物料表模型不存在，测试靠打桩绕过，真实调用不可靠。
- 改动：
  - `app/api/v1/endpoints/shortage/handling/transfers.py`：执行调拨时要求调出/调入库位，校验实际数量，调用 `TransferService.transfer_stock(..., commit=False)`；库存失败时 rollback，不再假成功。
  - `app/services/inventory/transfer_service.py`：补 `tenant_id=1` 默认值、`commit=False` 事务控制和关联单据信息写入。
  - `app/services/material_transfer_service.py`：补兼容构造器和 `ProjectMaterial` 缺失兼容层，真实环境安全降级，不再 NameError。
  - `tests/api/test_shortage_transfers.py`：新增调拨执行 API 契约，覆盖源库扣减、目标库增加、物料总库存净额不变、ISSUE/TRANSFER_IN 流水。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/api/test_shortage_transfers.py::test_transfer_approval_and_execution_flow -q` -> failed（执行后目标库位无库存行）。
  - 绿灯：同命令 -> 1 passed。
  - 相邻回归：`.venv/bin/python -m pytest tests/api/test_shortage_transfers.py tests/unit/test_transfer_service_coverage.py tests/unit/test_material_transfer_service.py tests/services/test_material_transfer_svc.py tests/unit/test_material_transfer_service_coverage.py tests/unit/test_zero_coverage_batch9_auto.py -q` -> 48 passed, 3 skipped。
  - 静态检查：`py_compile` passed；`ruff check app/api/v1/endpoints/shortage/handling/transfers.py app/services/inventory/transfer_service.py app/services/material_transfer_service.py tests/api/test_shortage_transfers.py` -> All checks passed；`git diff --check` passed。
- 已知测试边界：
  - `tests/unit/test_inventory_management_service.py` 仍有 4 个既有失败：旧测试调用 facade 上不存在的私有 `_calculate_stock_status`；与本次调拨链路无关。
- 残留：
  - `PROD-05` 仍待修：齐套算法“在途是否算已齐套/双算/跨项目预留”仍需独立修。
  - 历史已执行但未动库存的调拨单需要后续数据清洗/补偿，代码不会自动回放旧单据。

## 2026-07-03 继续：功能审计 PROD-12 修复（生产领料扣库存）

- 修复项：`PROD-12`，生产领料兼容接口只有列表/详情/审批/发料，缺创建入口；发料只把领料单状态置为 `ISSUED`，不扣库存、不写库存流水。
- 根因：
  - `production/material_requisitions.py` 未提供 `POST /production/material-requisitions`，前端创建领料单没有可用入口。
  - `/issue` 端点未调用 `OutboundService.issue_material()`，导致 `MaterialStock`、`MaterialTransaction`、`Material.current_stock` 全不变。
  - `OutboundService.issue_material()` 原先内部直接 `commit()`，不适合被领料单多明细事务复用。
- 改动：
  - `app/api/v1/endpoints/production/material_requisitions.py`：新增创建领料单端点，写入主表和明细；审批时补齐批准数量；发料时校验状态/数量并调用出库服务。
  - `app/services/inventory/outbound_service.py`：补 `tenant_id=1` 默认值，并增加 `commit=False` 选项，支持领料单统一事务提交/回滚。
  - `tests/api/test_production_compat_endpoints.py`：新增 API 契约，覆盖创建领料单→审批→发料→库存扣减→ISSUE 流水。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/api/test_production_compat_endpoints.py::TestProductionCompatibilityEndpoints::test_material_requisition_create_issue_deducts_inventory -q` -> failed（POST 405 Method Not Allowed）。
  - 绿灯：同命令 -> 1 passed。
  - 相邻回归：`.venv/bin/python -m pytest tests/api/test_production_compat_endpoints.py -q` -> 8 passed；`.venv/bin/python -m pytest tests/unit/test_outbound_service_coverage.py -q` -> 1 passed；`.venv/bin/python -m pytest tests/api/test_production.py::TestMaterialRequisition -q` -> 1 passed。
  - 静态检查：`py_compile` passed；`ruff check app/api/v1/endpoints/production/material_requisitions.py app/services/inventory/outbound_service.py tests/api/test_production_compat_endpoints.py` -> All checks passed；`git diff --check` passed。
- 已知测试边界：
  - `tests/test_inventory_management.py` 当前因既有 fixture `test_tenant` 缺失，17 个用例在 setup 阶段报错，不能作为本轮回归包；本次未修改该测试基础设施。
- 残留：
  - `PROD-05` 仍待修：齐套算法“在途是否算已齐套/双算/跨项目预留”仍需独立修。

## 2026-07-03 继续：功能审计 PROD-04 修复（采购在途读侧口径）

- 修复项：`PROD-04`，齐套/缺料/物料需求等读侧按 `PurchaseOrderItem.status in (APPROVED, ORDERED, PARTIAL_RECEIVED)` 计算在途，但审批后的 POI 仍是 `PENDING`，导致已审批未收货订单在途恒漏算。
- 根因：
  - PO 主状态表示订单是否已审批/收货进度，POI 行状态更多表示行收货进度。
  - 读侧只看 POI 状态，没有结合 PO 主状态与订单行剩余数量。
  - 多个模块各写一套状态字典，`CONFIRMED/IN_TRANSIT`、小写 `approved/partial_received`、POI `ORDERED` 混用。
- 改动：
  - `app/services/purchase/in_transit.py`：新增共享在途 helper，统一口径为“PO 主状态在 APPROVED/ORDERED/PARTIAL_RECEIVED 等生效状态 + 订单行剩余数量 > 0”。
  - 接入 `KitRateService`、kit-rate 工具、kit-check、定时齐套快照、物料需求列表/生成、智能缺料扫描、装配齐套基础/增强分析。
  - `app/api/v1/endpoints/assembly_kit/kit_analysis/utils.py`：同步修掉采购订单不存在的 `expected_date` 读法，改用承诺交期/要求交期。
  - `tests/api/test_purchase_receipts_workflow_contracts.py`：新增 API 契约，覆盖审批后未收货=全量在途、部分收货=剩余在途、全部收货=0。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/api/test_purchase_receipts_workflow_contracts.py::test_approved_purchase_order_counts_remaining_quantity_as_in_transit -q` -> failed（在途为 0）。
  - 绿灯：同命令 -> 1 passed。
  - 相邻回归：`.venv/bin/python -m pytest tests/api/test_purchase_receipts_workflow_contracts.py tests/api/test_purchase_workflow_contracts.py tests/audit_p0/test_p0_06_receipt_no_stock.py tests/audit_p0/test_p0_07_shortage_scan_500.py tests/unit/test_kit_rate_service.py tests/unit/test_kit_rate_service_coverage.py tests/unit/test_smart_alert_engine.py tests/unit/test_smart_alert_engine_coverage.py -q` -> 83 passed, 11 skipped。
  - 静态检查：`py_compile` passed；`ruff check` 本轮触达 Python/测试文件 -> All checks passed；`git diff --check` passed。
- 残留：
  - `PROD-05` 仍待修：齐套算法“在途是否算已齐套/双算/跨项目预留”仍需独立修，不因在途数据能读到而自动正确。
  - `PROD-14` 已在后续补齐：调拨执行 now 源库扣减、目标库增加并写库存流水；`PROD-12` 已补齐领料扣库。
  - 存量数据仍需清洗：历史 PO/POI 空状态、历史收货明细金额空值不会自动回填。

## 2026-07-03 继续：功能审计 PROD-11/22 修复（收货状态与金额流转）

- 修复项：`PROD-11` + `PROD-22`，创建采购收货单后只累加 `PurchaseOrderItem.received_qty`，不刷新 PO/POI 状态，也不计算收货明细金额和订单已收金额。
- 根因：
  - `purchase/receipts.py` 创建 `GoodsReceiptItem` 时没有写 `amount`。
  - 收货后没有任何写入点把 PO/POI 状态推进到 `PARTIAL_RECEIVED` / `RECEIVED`。
  - `PurchaseOrder.received_amount` 未随收货累计，后续对账缺基础。
- 改动：
  - `app/api/v1/endpoints/purchase/receipts.py`：新增 `_refresh_order_receipt_progress()`，按所有订单行 `received_qty / quantity` 刷新 PO/POI 状态，并累计 `received_amount`。
  - 创建收货明细时写入 `amount = received_qty * unit_price`。
  - `tests/api/test_purchase_receipts_workflow_contracts.py`：新增 API 契约，覆盖部分收货变 `PARTIAL_RECEIVED`、补齐后变 `RECEIVED`、收货明细金额和订单已收金额同步。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/api/test_purchase_receipts_workflow_contracts.py::test_goods_receipt_updates_order_item_status_and_amounts -q` -> failed（`GoodsReceiptItem.amount == 0.00`）。
  - 绿灯：同命令 -> 1 passed。
  - 相邻回归：`.venv/bin/python -m pytest tests/audit_p0/test_p0_06_receipt_no_stock.py tests/api/test_purchase_workflow_contracts.py tests/api/test_purchase_receipts_workflow_contracts.py tests/unit/test_inbound_service_coverage.py -q` -> 10 passed。
  - 静态检查：`py_compile` passed；`ruff check app/api/v1/endpoints/purchase/receipts.py tests/api/test_purchase_receipts_workflow_contracts.py` -> All checks passed；`git diff --check` passed。
- 残留：
  - `PROD-04` 已在后续补齐：齐套/缺料/物料需求等读侧统一按 PO 主状态 + 订单行剩余数量计算在途。
  - `PROD-14` 已在后续补齐：调拨执行 now 源库扣减、目标库增加并写库存流水；`PROD-12` 已补齐领料扣库。
  - 存量数据仍需清洗：已有 PO/POI 空状态、历史收货金额空值不会被本次代码自动回填。

## 2026-07-03 继续：功能审计 PROD-03 修复（采购收货入库断链）

- 修复项：`PROD-03`，采购收货只回写 `PurchaseOrderItem.received_qty`，不写库存台账、库存交易或 `Material.current_stock`。
- 根因：
  - `purchase/receipts.py` 创建收货单/质检时没有调用 `InboundService`。
  - `InboundService.purchase_in()` 只在库存 facade 内部可达，收货流没有业务调用方。
  - 库存更新服务只维护 `material_stock`，没有同步旧读侧常用的 `materials.current_stock`。
- 改动：
  - `app/api/v1/endpoints/purchase/receipts.py`：质检确认时按“合格数量 - 已入库数量”增量调用 `InboundService.purchase_in()`；写回 `warehoused_qty`、默认库位、入库时间/人员，避免重复质检重复入库。
  - `app/services/inventory/stock_update_service.py`：库存增减同步维护 `Material.current_stock`。
  - `app/services/inventory/inbound_service.py`：保留 `tenant_id=1` 默认值，兼容旧调用/测试。
  - `tests/api/test_purchase_receipts_workflow_contracts.py`：新增 API 契约，覆盖收货质检合格后写 `MaterialStock`、`MaterialTransaction(PURCHASE_IN)`、`Material.current_stock`。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_06_receipt_no_stock.py -q` -> 2 failed；新增 API 契约 -> failed（`MaterialStock` 不存在）。
  - 绿灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_06_receipt_no_stock.py tests/api/test_purchase_receipts_workflow_contracts.py tests/unit/test_inbound_service_coverage.py -q` -> 7 passed。
  - 相邻回归：`.venv/bin/python -m pytest tests/api/test_purchase_workflow_contracts.py tests/api/test_purchase_receipts_workflow_contracts.py tests/audit_p0/test_p0_06_receipt_no_stock.py -q` -> 8 passed。
  - 静态检查：`py_compile` passed；`ruff check` 本轮触达 Python/测试文件 -> All checks passed；`git diff --check` passed。
- 残留：
  - `PROD-11/22` 已在后续补齐：收货后 PO/POI 状态、收货明细金额和订单已收金额已回归。
  - `PROD-04` 已在后续补齐：在途读侧状态字典/剩余数量口径已回归。
  - `PROD-14` 已在后续补齐：调拨执行 now 源库扣减、目标库增加并写库存流水；`PROD-12` 已补齐领料扣库。
  - `tests/test_inventory_management.py` 当前因既有 fixture `test_tenant` 缺失无法作为回归包运行，未计入本轮验证。

## 2026-07-03 继续：功能审计 PROD-02 修复（智能缺料扫描字段错配 500）

- 修复项：`PROD-02`，智能缺料预警扫描引用不存在字段，`POST /shortage/smart-alerts/scan` 返回 500。
- 根因：
  - `WorkOrder` 模型只有 `plan_start_date`，服务引用了不存在的 `planned_start_date`。
  - `WorkOrder` 模型没有 `is_critical_path`，服务把它放进查询列并读取。
  - `MaterialStock` 模型字段是 `available_quantity`，服务引用了不存在的 `available_qty`。
- 改动：
  - `app/services/shortage/smart_alert_engine.py`：需求扫描改用 `WorkOrder.plan_start_date`，并排除无计划开始日期的工单；库存汇总改用 `MaterialStock.available_quantity`；工单缺少关键路径来源时先以 `False` 进入预警等级计算。
  - `FUNCTIONAL_AUDIT_TRACKER.md`、`P0_REPRO_REPORT.md`、`tests/audit_p0/README.md`：`PROD-02/P0-7` 标为已动态复现并回归。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_07_shortage_scan_500.py -q` -> failed（HTTP 500）。
  - 绿灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_07_shortage_scan_500.py -q` -> 1 passed。
  - 相邻回归：`.venv/bin/python -m pytest tests/unit/test_smart_alert_engine.py tests/unit/test_smart_alert_engine_coverage.py tests/audit_p0/test_p0_07_shortage_scan_500.py -q` -> 50 passed, 11 skipped。
  - 静态检查：`py_compile app/services/shortage/smart_alert_engine.py` passed；`ruff check app/services/shortage/smart_alert_engine.py tests/audit_p0/test_p0_07_shortage_scan_500.py` -> All checks passed；`git diff --check` passed。
- 残留：
  - 该修复只解决扫描入口字段错配 500；库存/在途基础后续已由 `PROD-03/PROD-11/PROD-04` 接上，预警/齐套算法口径仍归 `PROD-05`。
  - 深覆盖相邻包 `tests/unit/test_smart_alert_n2.py` 仍有 2 个既有失败：测试 helper 把 `Decimal("0")` 当默认值覆盖、以及成本影响为 0 时评分期望与现行实现不一致；未并入本次字段修复。

## 2026-07-03 继续：功能审计 APPR-03 修复（会签/或签驳回汇总与终态防复活）

- 修复项：`APPR-03`，会签/或签驳回语义破坏，`REJECTED` 审批实例可被剩余待办继续 `approve` 翻回 `APPROVED`。
- 根因：
  - `engine.reject()` 调了 `executor.process_approval()` 但忽略 `can_proceed/final_result`，导致 OR_SIGN/AND_SIGN 一票拒就直接置 `REJECTED`。
  - `engine.approve()` 只校验任务 `PENDING`，不校验实例是否已是 `APPROVED/REJECTED/CANCELLED/TERMINATED` 终态。
  - 会签最终汇总为 `FAILED` 时，approve 路径仍直接 `_advance_to_next_node()`，可把失败汇总推进成通过。
- 改动：
  - `app/services/approval_engine/engine/core.py`：新增终态实例守卫、会签汇总结果读取、实例驳回终态清理待办 helper；`_get_and_validate_task()` 禁止终态实例继续处理待办。
  - `app/services/approval_engine/engine/approve.py`：approve 路径识别会签 `FAILED` 并置 `REJECTED`；reject 路径对 OR_SIGN/AND_SIGN 尊重 `can_proceed`，未完成汇总时不提前终止，汇总通过时继续流转，汇总失败时驳回到发起人。
  - `tests/audit_p0/test_p0_05_cosign_reject_flip.py`：从 skip 占位改为 3 个稳定动态用例，覆盖 AND_SIGN 汇总失败、OR_SIGN 等待其他审批人、终态 REJECTED 防复活。
  - `FUNCTIONAL_AUDIT_TRACKER.md`、`P0_REPRO_REPORT.md`、`tests/audit_p0/README.md`：APPR-03 标为已动态复现并回归。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_05_cosign_reject_flip.py -q` -> 3 failed（会签/或签一票拒立即 REJECTED；终态 REJECTED 未拦截并被翻 APPROVED）。
  - 绿灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_05_cosign_reject_flip.py -q` -> 3 passed。
  - 邻近回归：`.venv/bin/python -m pytest tests/unit/test_approval_engine_approve.py tests/services/test_approval_approve.py tests/unit/test_approval_executor.py -q` -> 88 passed。
  - APPR 回归包：`.venv/bin/python -m pytest tests/audit_p0/test_p0_01_approval_template_mismatch.py tests/audit_p0/test_p0_02_approval_template_no_seed.py tests/audit_p0/test_p0_05_cosign_reject_flip.py tests/audit_p0/test_p0_17_contract_withdraw_typeerror.py tests/api/test_approval_submit_error_contracts.py -q` -> 17 passed。
  - 静态检查：`py_compile` passed；`ruff check app/services/approval_engine/engine/approve.py app/services/approval_engine/engine/core.py tests/audit_p0/test_p0_05_cosign_reject_flip.py` -> All checks passed。
- 已知测试边界：
  - 更大组合 `tests/unit/test_approval_engine_core.py tests/services/test_approval_workflow_engine.py tests/integration/test_approval_integration.py` 仍有 6 个既有失败：旧 mock 假设 `_generate_instance_no().scalar()`、workflow_engine 旧断言、integration 测试给 `ApprovalTask` 传已不存在的 `is_active`。与 APPR-03 改动不在同一根因，后续单独收口。

## 2026-07-03 继续：功能审计 APPR-02 修复（统一审批新库种子）

- 修复项：`APPR-02`，全新初始化数据库没有统一审批模板、默认流程、节点和路由规则，导致 F1/ECN/采购/外协/验收/立项等审批链在新部署环境全部不可用。
- 根因：
  - `scripts/init_db.py` 只建表、跑迁移、建默认账号，没有统一审批种子入口；旧迁移里的审批模板 code 也与当前业务代码漂移。
  - `python scripts/init_db.py` 时 `sys.path[0]` 为 `scripts/`，直接执行脚本会先因找不到 `app` 失败。
- 改动：
  - `scripts/init_db.py`：补项目根目录到 `sys.path`；默认账号后调用统一审批种子初始化。
  - `app/utils/init_approval_data.py`：统一维护 10 个审批模板、13 条 flow、30 个审批节点、3 条 routing rule，采用 upsert 幂等写法。
  - `app/utils/init_data.py`：应用启动基础数据初始化时也调用统一审批种子，避免只修脚本不修运行态。
  - `tests/audit_p0/test_p0_02_approval_template_no_seed.py`：从只查模板数量升级为校验关键 code、默认 flow、active 节点、flow/node/rule 数量。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`APPR-02` 标为 `已验证`；`SALES-10` 同步标为 `已验证`。
- 验证：
  - 红灯 1：`.venv/bin/python -m pytest tests/audit_p0/test_p0_02_approval_template_no_seed.py -q` -> failed（`ModuleNotFoundError: No module named 'app'`）。
  - 红灯 2：修复脚本入口后同命令 -> failed（`approval_templates=0`，10 个关键 code 全缺）。
  - 绿灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_02_approval_template_no_seed.py -q` -> 1 passed。
  - 回归：`.venv/bin/python -m pytest tests/audit_p0/test_p0_01_approval_template_mismatch.py tests/audit_p0/test_p0_02_approval_template_no_seed.py tests/api/test_approval_submit_error_contracts.py tests/unit/test_acceptance_approval_service.py tests/api/test_purchase_workflow_contracts.py tests/unit/test_api_p7_coverage.py app/tests/services/purchase_workflow/test_purchase_workflow.py -q` -> 71 passed。
  - 合同专项：`.venv/bin/python -m pytest tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_contract_approval_submit -q` -> 1 passed。
  - 幂等实测：全新库 `init_db.py` 后再次连续调用两次 `init_approval_workflow_seeds()`，数量保持 `templates=10/flows=13/nodes=30/rules=3`。
  - 静态检查：`py_compile` passed；`ruff check app/utils/init_approval_data.py scripts/init_db.py app/utils/init_data.py tests/audit_p0/test_p0_02_approval_template_no_seed.py` -> All checks passed；`git diff --check` passed。
- 残留：
  - 会签/或签驳回语义已随 `APPR-03` 修复；项目审批路由 404 仍需后续另项收口。

## 2026-07-03 继续：功能审计 APPR-01 修复（审批链模板 code 与 200 掩盖）

- 修复项：`APPR-01`，采购/外协/验收/立项 4 条审批链引用的 `template_code` 与库里 `approval_templates` 错位；提交失败时部分接口仍返回 HTTP 200，前端和调用方会误判成功。同步消除 `SALES-10` 的同型 200 掩盖问题，种子缺口仍留给 `APPR-02`。
- 根因：
  - 业务代码仍引用 `PURCHASE_ORDER_APPROVAL`、`OUTSOURCING_ORDER_APPROVAL`、`ACCEPTANCE_ORDER_APPROVAL`、`PROJECT_TEMPLATE` 等旧别名，当前初始化数据实际是 `TPL_PURCHASE/TPL_OUTSOURCING/TPL_ACCEPTANCE/TPL_PROJECT`。
  - 采购/外协/验收/合同提交端点在 `success=[]` 且 `errors!=[]` 时仍继续 commit 并包装 200。
- 改动：
  - `app/services/purchase_workflow/service.py`、`app/services/outsourcing_workflow/outsourcing_workflow_service.py`、`app/services/acceptance_approval/service.py`、`app/api/v1/endpoints/projects/approvals/submit_new.py`：统一改用现有 `TPL_*` 模板 code，并显式暴露验收/立项模板常量给测试锁定。
  - 新增 `app/api/v1/endpoints/approval_submit_guard.py`：提交批次如果 0 成功且存在错误，先 `rollback()`，再返回 HTTP 400。
  - `purchase/workflow.py`、`outsourcing/workflow.py`、`acceptance/order_approval.py`、`sales/contracts/approval.py`：提交端点接入全失败 guard。
  - 更新旧测试契约：采购 contract duplicate guard 改为 400；验收/采购/项目相关测试种子和断言改为 `TPL_*`。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`APPR-01` 标为 `已验证`；`SALES-10` 标为 `修复中`（200 掩盖已消除，种子待 `APPR-02`）。
- 验证：
  - 红灯：旧 `tests/audit_p0/test_p0_01_approval_template_mismatch.py -q` -> 4 failed（4 个业务模板 code 不在 DB）。
  - 红灯：新增 `tests/api/test_approval_submit_error_contracts.py -q` -> 4 failed（全失败提交未抛 HTTPException，仍会 200）。
  - 绿灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_01_approval_template_mismatch.py tests/api/test_approval_submit_error_contracts.py -q` -> 8 passed。
  - 回归：`.venv/bin/python -m pytest tests/audit_p0/test_p0_01_approval_template_mismatch.py tests/api/test_approval_submit_error_contracts.py tests/unit/test_acceptance_approval_service.py tests/api/test_purchase_workflow_contracts.py tests/unit/test_api_p7_coverage.py app/tests/services/purchase_workflow/test_purchase_workflow.py -q` -> 70 passed。
  - 静态检查：`py_compile` passed；`ruff check` 本轮触达 Python/测试文件 -> All checks passed。
- 残留：
  - `tests/integration/test_project_approval_smoke.py` 当前提交路径仍 404，归入后续项目审批路由收口，不计入 `APPR-01` 已修范围。
  - `tests/unit/test_outsourcing_workflow_service.py` 当前有 9 个旧失败，集中在成本归集私有方法/撤回参数/Mock 结构，不是本轮模板码或 200 掩盖改动引入；后续另项处理。
  - `tests/unit/test_contract_approval_service.py` 当前有 1 个旧断言失败，服务实际调用已带 `page/page_size`。

## 2026-07-03 继续：功能审计 APPR-15 修复（发货款回款计划触发器）

- 修复项：`APPR-15`，发货款（默认 40%）回款计划生成后没有任何业务触发器，设备已发货也不会进入开票申请流程，财务只能人工盯。
- 根因：
  - `PaymentPlanService` 只负责生成 `DELIVERY` 类型收款计划，不负责触发。
  - `business_support_orders/delivery_orders/crud.py::ship_delivery_order` 发货确认只更新发货单状态和 `ship_date`，没有联动 `ProjectPaymentPlan` 或 `InvoiceRequest`。
- 改动：
  - `app/services/sales/payment_plan_service.py`：新增 `trigger_delivery_payment_plan()`，按发货单 `project_id/contract_id` 查找 `DELIVERY` 收款计划；发货日早于计划日时将计划日期推进到实际发货日；若未存在待审/已批开票申请，则自动创建发货款 `InvoiceRequest`。
  - `app/api/v1/endpoints/business_support_orders/delivery_orders/crud.py`：确认发货时调用上述服务，与发货状态在同一事务提交。
  - `tests/api/test_delivery_payment_plan_trigger_contracts.py`：新增合约测试，覆盖“已审批发货单确认发货后自动创建发货款开票申请”。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`APPR-15` 标为 `已验证`，P0-0 资金正确性急救包同步。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/api/test_delivery_payment_plan_trigger_contracts.py -q` -> failed（无 `InvoiceRequest`）。
  - 绿灯：`.venv/bin/python -m pytest tests/api/test_delivery_payment_plan_trigger_contracts.py -q` -> 1 passed。
  - 回归：`.venv/bin/python -m pytest tests/api/test_delivery_payment_plan_trigger_contracts.py tests/unit/test_delivery_order_project_filter.py tests/services/test_payment_plan_service.py tests/api/test_sales_invoice_gate_contracts.py tests/audit_p0/test_p0_16_invoice_gate.py -q` -> 26 passed。
  - 静态检查：`py_compile` passed；`ruff check app/services/sales/payment_plan_service.py app/api/v1/endpoints/business_support_orders/delivery_orders/crud.py tests/api/test_delivery_payment_plan_trigger_contracts.py` -> All checks passed。

## 2026-07-03 继续：功能审计 APPR-10/APPR-11/SALES-09/PEER-05 修复（发票开票与 update 门禁）

- 修复项：`APPR-10`、`APPR-11`、`SALES-09`、`PEER-05`，集中处理发票未审批可开票、通用 update 绕状态/金额门禁、作废后可重开票、写操作挂 `finance:read` 和未签合同可建发票的问题。
- 根因：
  - `/sales/invoices/{id}/issue` 仍查旧 `ApprovalRecord` 轨道；统一审批实例不存在时会放行。
  - `Invoice` ORM 未映射库里已有的 `approval_instance_id/approval_status`，审批 adapter 写入字段但不可靠。
  - `update_invoice` 对传入字段直接 `setattr`，可改 `status`，也可把金额改到超过合同累计开票上限。
  - 发票创建/更新/删除/开票/作废等写入口使用 `finance:read`，且发票创建没有合同签署状态前置校验。
- 改动：
  - `app/models/sales/invoices.py`：补 `approval_instance_id`、`approval_status` 映射。
  - `app/services/approval_engine/adapters/invoice.py`：提交/通过/驳回/撤回时同步回写统一审批实例 ID 与审批状态。
  - `app/api/v1/endpoints/sales/invoices/operations.py`：开票前要求发票当前状态为 `APPROVED`，且统一 `approval_instances` 最新实例为 `APPROVED`；作废/取消等写操作权限改为 `finance:update`。
  - `app/api/v1/endpoints/sales/invoices/basic.py`：创建发票要求合同为 `SIGNED/ACTIVE/COMPLETED`；发票金额新增与更新均重跑合同累计开票上限；通用 PUT 禁止变更 `status`；写权限改为 `finance:create/update/delete`。
  - `tests/api/test_sales_invoice_gate_contracts.py`：新增发票门禁合约测试，覆盖统一审批实例、作废重开票、通用状态变更、金额上限、未签合同。
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`APPR-10/APPR-11/SALES-09/PEER-05` 标为 `已验证`，P0-0 资金正确性急救包同步。
- 验证：
  - 红灯：`.venv/bin/python -m pytest tests/audit_p0/test_p0_16_invoice_gate.py -q` -> 2 failed；`.venv/bin/python -m pytest tests/api/test_sales_invoice_gate_contracts.py -q` -> 5 failed。
  - 绿灯：`.venv/bin/python -m pytest tests/api/test_sales_invoice_gate_contracts.py -q` -> 7 passed；`.venv/bin/python -m pytest tests/audit_p0/test_p0_16_invoice_gate.py -q` -> 2 passed。
  - 回归：`.venv/bin/python -m pytest tests/api/test_invoice_basic_route_contracts.py tests/api/test_invoice_approval_workflow_contracts.py -q` -> 19 passed。
  - 专项包：`.venv/bin/python -m pytest tests/api/test_sales_invoice_gate_contracts.py tests/api/test_invoice_basic_route_contracts.py tests/api/test_invoice_approval_workflow_contracts.py tests/audit_p0/test_p0_16_invoice_gate.py tests/api/test_sales_invoices_api.py tests/api/test_sales.py::TestInvoiceManagement -q` -> 44 passed, 1 skipped。
  - 资金相邻 P0：`.venv/bin/python -m pytest tests/audit_p0/test_p0_03_quote_fund_trio.py tests/audit_p0/test_p0_04_payment_no_reconciliation.py tests/audit_p0/test_p0_16_invoice_gate.py -q` -> 7 passed。
  - 静态检查：`py_compile` passed；`ruff check` 本轮触达 Python/测试文件 -> All checks passed。

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

## 2026-07-03 继续：项目管理域去重排查与清理

- 排查结论（项目域路径 584 个）：
  - **确认重复并已清理**：progress_compat 同一 router 挂两处（裸挂 + /progress，21端点×2）——6月抢修时有意做的双别名（batch10 测试曾断言两处都通）。前端消费方集中在 services/api/progress.js 一个文件，已全部迁到 /progress 前缀（18处），裸挂载下线（顶层不再被 /tasks、/wbs-templates、/reports/* 污染）。前端孤儿页 ProjectGantt.jsx 删除（无路由无引用；/gantt API 保留，BlockingChain 组件在用）。
  - **有意的兼容层，保留**：/milestones/projects/{id}/milestones、/members/projects/…、/stages/projects/…（operationId 带 legacy/compat，前端 projects.js 在用）；rd_project_aliases（自述"Redirect-free aliases"）。
  - **记录不动（表级/分散）**：tasks(131行) 与 task_unified(91行) 双任务表并存+task-center/node-tasks/ecn-tasks 多任务面——ROADMAP 级重构；kit-rate(看板/分析) 与 kit-rates(统一口径/对比) 两前缀各有消费方属分散；/projects/{id}/{template_id} 类粗糙嵌套参数路径存在但不冲突。
  - **顺带发现的断链**（记录）：progress.js taskApi 的 update/delete/updateProgress/updateAssignee/complete 调的 PUT/DELETE /tasks/* 后端从来不存在（仅 GET），迁移后仍 404——真正任务 CRUD 在 /task-center；后续如需页面内改任务应切 task-center。
- 测试同步：test_batch10（裸别名断言改为 404 验证）、test_progress（compat 路由测试改 /progress 路径）、test_project_team_collaboration（任务创建改 /progress 路径）；test_milestones 两例适配 /milestones/ 分页化响应（items 包裹，系另一会话的里程碑改造，测试未跟上）。
- 验证：openapi 裸别名清零、/progress/* 16 条完好；pytest -k 'progress/wbs/milestone/gantt' 全绿；batch10 5/5；实机冒烟 /progress 两口 200、裸口 404；前端 build 通过。integration/test_project_team_collaboration 整文件失败经 stash 对照确认为既有债（fixture 层）。

## 2026-07-03 继续：生产域去重清理

- 排查（生产域路径 399 个），确认三处双挂载 + 一处假实现占位 + 前端断链：
  - **kit-check 假实现换真**：kit_check 包内路由自带 /kit-check 前缀，挂载又加 prefix → 真实现（真DB查询+齐套率计算）全部落在 /kit-check/kit-check/* 不可达，自然路径被 batch5 造的**硬编码演示数据 compat** 占用（功能审计"末梢假"实锤之一）。已挂载去前缀让真实现上位、compat 下线；/kit-check/history 顺带首次可达。响应契约两者一致（code/data{work_orders,summary,pagination}），页面无感。
  - **workers 双挂载**：顶层 /workers 与 /production/workers 同 router 两挂（api.py+api_lazy 都有），前端只用后者；顶层摘除。
  - **production exceptions 双挂载**：顶层 /production-exceptions 与 /production/exceptions 同 router 两挂——启动日志 Duplicate Operation ID 的根源；顶层摘除后警告清零。
  - **前端断链清理**：services/api/kit.js（kitApi 全指向不存在的 /kit-checks 复数路径）删除；production.js kitCheckApi 的 6 个 /kit-checks 死方法删除（保留 workOrders 活方法）；pages/KitCheck/ 目录（hooks+constants，无人引用且与 KitCheck.jsx 同名解析歧义）删除。备份均在 scratchpad/deleted_presale。
- 测试同步：test_production_write_smoke / test_production_compat_endpoints 路径迁到 /production/*；batch5 kit-check 断言直接过（真实现同 200）。
- 验证：openapi 双挂载清零、kit-check 5 条自然路径；实机 /kit-check/work-orders 真数据 200（空列表=演示库无未来7天工单，比假数据诚实）、history 200；Duplicate Operation 警告 0；两测试文件全绿；-k sweep 中 2 例失败为跨文件隔离债（单跑/同文件跑均绿）；前端 build 通过。
- 遗留（下一刀）：**assembly-kit 双段路径**——8 个子路由 /dashboard/dashboard、/stages/stages、/templates/templates、/alert-rules/alert-rules、/shortage-alerts/shortage-alerts 等同病根，batch5 当时让前端将就了双段路径；修复涉及包内前缀+前端 assemblyKit.js+batch5/6 测试，面较大单独做。kit-rate/kit-rates 分散、tasks/task_unified 双表维持记录。

## 2026-07-03 继续：assembly-kit 双段路径修复（生产域去重第二刀）

- 病根：各子文件先 `router = APIRouter()` 又重新赋值带前缀的 router（死代码残迹），且装饰器路径重复自身前缀段——/assembly-kit/dashboard/dashboard、/stages/stages、/templates/templates、/alert-rules/alert-rules、/shortage-alerts/shortage-alerts；kit_analysis 挂载前缀 kit-analysis 与内部 /analysis 冗余。batch5 当时让前端将就了双段路径。
- 修复：5 个子文件装饰器去重复段（"" 或 /{param}）；kit_analysis 挂载前缀改 /assembly-kit（新路径 /assembly-kit/analysis*、/assembly-kit/projects/{id}/assembly-readiness）。
- 同步：前端 assemblyKit.js TEMPLATE_BASE + production.js 8 处调用改单段；tests/api/test_batch5、test_path_param（kit-analysis 路径）、frontend routeContracts.test.js 更新。
- 顺带清断链：production.js assemblyKitApi 的 listKits(/assembly/projects/readiness)、analyzeKit(/assembly/analysis) 指向从不存在的路径且无消费方，移除。
- 验证：openapi 双段/冗余清零（assembly 28 条全部单段）；实机 5 个自然路径 200、旧双段 404；batch5+path_param 36 绿；前端 routeContracts 24 绿；build 通过。

## 2026-07-03 继续：采购域去重清理

- 排查（采购域路径 122 个）：
  - **procurement 包"活两个死四个"**：包聚合 router（suppliers+price-analysis+kitting-analysis）从未挂载于活动注册表；其中 suppliers.py(531行,端点已标deprecated) 与顶层活跃的 /suppliers 重复，price_analysis/kitting_analysis/kitting_optimization 无任何消费方——四个死模块删除，__init__ 重写为纯包声明。活的 analysis(/procurement-analysis) 与 supplier_price_trend(/supplier-price) 保留并由 api.py 直连挂载。
  - **shim 收敛**：procurement_analysis.py、supplier_price_trend.py 两个 9 行转发壳删除（api.py 改直连包内模块）。
  - **purchase_intelligence.py 删除**：荒诞的"四层 try-import 兜底空 router"占位文件，挂载在 api.py/api_medium 均被注释——连注释一并清掉。服务层 purchase_intelligence(有单测)保留。
  - **补删售前遗漏**：tests/unit/services/sales/test_solution_version_service.py（子目录真测试）、test_presale_ai_export_service_coverage.py 两个引用已删服务的测试（此前造成 2 个收集错误）。
- 记录不动：
  - **endpoints/material/ 包**（tracking/sync/procurement_optimization/project_fusion 四模块）只被备用注册表 api_lazy 挂载，活动注册表(api.py)不挂——生产环境全部不可达；MaterialTracking 前端页实际走 /materials + /purchase-orders。与 ROADMAP F1 库存台账相关，留待该项决策。
  - 既有测试债（stash 对照确认与本次无关）：test_procurement_analysis_service 期望的 price_analyzer 等服务模块名从来不存在（实际为 cost_trend 等）；test_kitting_optimization_deep、test_best_practice_deep 同类。
- 验证：启动 0 加载失败；/procurement-analysis/overview、/supplier-price 实机 200（直连挂载生效）；tests/api 采购面 88 通过；收集错误清零。

## 2026-07-03 继续：售后域去重清理（全链最后一域）

- **acceptance 双挂载收敛**：acceptance 包原被挂两次（/acceptance 前缀 + 裸挂 legacy），产生 32 对双生路径（/acceptance/acceptance-orders 与 /acceptance-orders 同函数）。前端只用裸路径；已去前缀挂载（api.py+api_lazy），32 对双生清零、裸 32 条保留。测试 3 个文件 8 处路径迁移，71 过。
- 排查无恙：installation-dispatch(9)/after-sales(10)/field(7) 均单挂载；售后域前端无孤儿页。
- **记录（命名空间设计问题，非重复）**：客服 service 包裸挂顶层，喷出 /tickets、/records、/communications、/surveys、/statistics 等通用命名空间（前端 service.js 在调），极易与其他域撞车——建议后续统一迁 /service/* 前缀（涉及 service.js 全量调用点，独立一刀）。

## 2026-07-03 继续：客服 service 包命名空间迁移 /service/*

- 客服包原裸挂顶层，喷出 /tickets、/records、/communications、/surveys、/survey-templates、/knowledge-base、/knowledge-features、/statistics 八个通用命名空间——api_lazy 备用注册表早就用 prefix="/service"，活动注册表漏了；本轮对齐设计意图。
- 迁移面：api.py 挂载加前缀；前端 service.js(44处)+customerCommunication.js(6处)；后端 5 个测试文件 22 处。前端 /knowledge-base 的页面路由（浏览器 URL）不受影响。
- 验证：openapi /service/* 38 条、八个裸命名空间清零；后端 27 测试过；前端 API 测试 17/18 文件过（debug.test.js 为 stash 对照确认的既有失败）；build 通过；实机 /service/tickets/statistics 等 200、旧裸路径 404。

## 2026-07-03 继续：双任务表整合 P1 完成（A路线：task_unified 收编 tasks）

- 设计文档 TASK_UNIFICATION_DESIGN.md（目标模型/字段映射/ID策略/四期计划/回滚方案）。
- P1 落地：
  - TaskUnified 模型扩 5 列（project_stage/machine_id/milestone_id/weight/block_reason）+ 迁移 SQL（migrations/20260703_task_unification_p1_sqlite.sql，含 task_id_map 映射表）。
  - 迁移脚本 scripts/migrate_tasks_to_unified.py（原生 sqlite3，幂等可复跑）：131 行全量迁入（task_type=PROJECT，确定性 new_id=10000+old_id 零区间重叠）；owner 空 10 行按 项目PM→admin 兜底；status TODO→PENDING/DONE→COMPLETED 映射；priority 补 MEDIUM（任务中心按优先级分组，NULL 会 500——实测踩到后回填）。
  - **5 张引用表 FK 重建**（SQLite 不支持 ALTER FK，DDL 重建把 REFERENCES tasks 改指 task_unified）+ 56 行引用重接 + PRAGMA foreign_key_check 兜底。
  - 坑：库里既有坏视图 v_bom_ready_rate（引用不存在的 bi.ready_status）会挡 RENAME，需 PRAGMA legacy_alter_table=ON；**真实 DB 是 data/app.db，根目录 app.db 是空壳**。
- 对账全绿：行数 131=131、每项目一致、状态分布一致、6 列引用完整性全过；幂等复跑 0 新增全跳过。
- 即刻生效的价值：任务中心总览/我的任务首次出现 PROJECT 类型任务（实测 by_type PROJECT:7）。
- 现状与下一步：tasks 表保留只读双读校验（写路径仍写 tasks，P2 切换；期间可重跑迁移脚本追平增量）。P2=写路径切换（WBS/模板/售前遗留同步/导入），P3=34 个读消费方+前端断链修复，P4=下线旧表。
- 回归：tests/api task/progress/task_center 面 43 过；后端启动 0 失败；数据库迁移前备份在 scratchpad（data-app.db.pre-task-unification.bak）。

## 2026-07-03 继续：PROD-05 齐套率口径修复

- 修复目标：齐套率当前/预计口径拆分，解决审计 PROD-05 的三类问题：在途计入已齐套、`received_qty` 与库存双算、主齐套服务不考虑预留可用量。
- 代码面：
  - `app/services/kit_rate/kit_rate_service.py`：当前齐套只按现有可用库存判断；新增 `MaterialStock.available_quantity` 优先口径，无库存跟踪记录时才回退 `Material.current_stock`。
  - `app/api/v1/endpoints/kit_rate/utils.py`、`app/utils/scheduled_tasks/kit_rate_tasks.py`、`app/api/v1/endpoints/kit_check/utils.py`、`app/api/v1/endpoints/kit_check/work_orders.py`、`app/api/v1/endpoints/assembly_kit/kit_analysis/utils.py`、`app/services/assembly_kit_service.py`、`app/services/project_workspace_service.py`：移除 `received_qty + current_stock` 双算和 `current + in_transit` 判当前齐套；在途继续保留为单独字段/预计到货依据。
  - `kit_check/work_orders.py` 详情在途读取改接 `app.services.purchase.in_transit.get_purchase_in_transit_qty`，不再用旧 POI.status 小字典。
- 验证：
  - `.venv/bin/python -m pytest tests/unit/test_kit_rate_service.py tests/unit/test_kit_rate_utils.py tests/unit/test_scheduled_kit_rate_tasks.py tests/unit/test_kit_check_utils.py tests/unit/test_assembly_kit_analysis_utils.py tests/unit/test_assembly_kit_service.py tests/services/test_assembly_kit_service.py tests/unit/test_project_workspace_service.py -q` 通过。
  - focused 组合 45 个用例通过；源码搜索未再发现齐套域 `received_qty + stock_qty`、`available_qty + in_transit_qty`、`PurchaseOrderItem.status.in_(["APPROVED","ORDERED","PARTIAL_RECEIVED"])` 残留。

## 2026-07-03 继续：PROD-15 现场缺料应急处理闭环

- 修复目标：现场缺料处理选择采购时不能只写处理状态；紧急采购不能停在 `DRAFT`；增强缺料预警不能只返回紧急采购，替代/调拨方案不再空转。
- 代码面：
  - `app/api/v1/endpoints/shortage/handling/reports.py`：`solution_type=PURCHASE` now 创建并提交来源 `SHORTAGE` 的紧急采购申请，失败时返回 400 提示检查供应商配置。
  - `app/services/urgent_purchase_from_shortage_service.py`：AlertRecord 自动触发和现场 ShortageReport 触发均生成 `SUBMITTED` 采购申请，写 `submitted_at/requested_by/requested_at`，并按 source 去重。
  - `app/services/shortage/smart_alert_engine.py`：替代方案查询 `material_alternatives`，调拨方案查询 `MaterialStock.available_quantity`；同一事务内方案号递增，避免多方案撞号。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_shortage_handling.py tests/unit/test_urgent_purchase_service_coverage.py tests/unit/test_smart_alert_n2.py tests/unit/test_smart_alert_engine.py -q` 通过（11 个既有 skip 保持原状）。
  - `.venv/bin/python -m compileall -q app/services/urgent_purchase_from_shortage_service.py app/services/shortage/smart_alert_engine.py app/api/v1/endpoints/shortage/handling/reports.py` 通过；`git diff --check` 通过。

## 2026-07-03 继续：PROD-10 采购申请转订单闸门

- 修复目标：采购申请转订单必须走完审批，不能对未审批申请直接生成订单；同一申请不能重复生成订单；转单后要回写申请明细 `ordered_qty`，否则后续仍会认为未采购。
- 代码面：
  - `app/services/purchase/purchase_service.py`：`generate_orders_from_request()` now 要求申请状态 `APPROVED`，已有任何 `source_request_id` 订单即拒绝重复生成；成功转单后回写 `PurchaseRequestItem.ordered_qty` 与 `PurchaseRequest.auto_po_created/auto_po_created_at`。
  - 同文件顺带修正两个真实模型字段名错配：`PurchaseRequestItem.amount` 替代不存在的 `total_amount`，`GoodsReceiptItem.received_qty/qualified_qty` 替代不存在的 `received_quantity/qualified_quantity`。
- 验证：
  - `.venv/bin/python -m pytest tests/unit/test_purchase_service_generate_orders.py app/tests/services/purchase/test_purchase_service.py tests/api/test_purchase.py::TestPurchaseRequest -q` 通过（25 个用例）。
  - `.venv/bin/python -m compileall -q app/services/purchase/purchase_service.py app/api/v1/endpoints/purchase/requests_refactored.py` 通过；`git diff --check` 通过。

## 2026-07-03 继续：PROD-09 ECN 通用状态机审批绕过

- 修复目标：ECN 通用状态机不能把 `SUBMITTED` 等待评估/待审批状态直接写成 `APPROVED/REJECTED`；状态写入口不能只要登录态。
- 红测：
  - `tests/api/test_ecn_state_machine_contracts.py::test_ecn_state_machine_rejects_submitted_to_approved_bypass` 先失败，证明 `SUBMITTED` 的 allowed 列表暴露 `APPROVED/REJECTED`。
  - `tests/api/test_ecn_state_machine_contracts.py::test_ecn_state_machine_transition_requires_update_permission` 先失败，证明普通登录用户可 POST `/ecn/state-machine/{id}/transition` 写状态。
- 代码面：
  - `app/api/v1/endpoints/ecn/state_machine.py`：`CURRENT_ECN_TRANSITIONS` 移除通用路径中的 `APPROVED/REJECTED` 目标；`_reject_approval_result_target()` 兜底禁止任何通用 transition/batch-transition 写审批结果状态。
  - `transition_ecn_state()` 与 `batch_transition_ecns()` 改为 `Depends(require_permission("ecn:update"))`；审批通过/驳回继续走 `/ecns/approval/action` 和审批适配器回调。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_ecn_state_machine_contracts.py -q` 通过。
  - `.venv/bin/python -m pytest tests/api/test_ecn_state_machine_contracts.py tests/api/test_path_param_route_contracts.py::test_ecn_state_machine_routes_tolerate_null_legacy_status tests/unit/test_state_machines_depth.py::TestEcnStateMachineIntegration tests/unit/test_ecn_adapter.py tests/unit/test_ecn_approval_adapter_n3.py -q` 通过（75 个用例）。

## 2026-07-03 继续：kit-rate 双前缀归一 + 齐套率产品口径宣言

- 现状澄清：/kit-rate 命名空间实为两个包共享——assembly_kit/kit_rate.py（AssemblyKitService，装配阶段/时间预警/增强分析）与 endpoints/kit_rate 包（KitRateService，看板/机台/项目/统一）。而"统一口径层"其实早已有人建好：kit_rate/unified.py 聚合三种算法（数量金额比例 quantity_based / 物料计数 kit_check / 装配阶段 stage_based）并给出对比——只是埋在 /kit-rates 复数前缀下无人知晓。
- 归一动作：/kit-rates/unified/{id} → **/kit-rate/unified/{id}**、/kit-rates/comparison → **/kit-rate/comparison**（与 assembly_kit 的 /kit-rate/* 无路径冲突，实测共存）；前端 procurement.js 与其测试同步；复数前缀清零。
- **产品口径宣言（记录为约定）**：跨模块展示齐套率一律以 `/kit-rate/unified/{project_id}`（KitRateService 聚合层）为权威查询口径——它同时返回三种算法结果与差异，天然可解释；各专用端点（time-based 预警、enhanced 分析、dashboard 快照）作为专业场景保留，但都归于 /kit-rate 单一命名空间。后续新页面接齐套率一律走 unified。
- 验证：/kit-rate/unified/66 实测返回真实聚合（DEMO26 项目 15 项物料三算法对比）、comparison 200、旧复数路径 404；前端 procurement 测试 38 绿；build 通过；后端 kit 面 4 过。

## 2026-07-03 继续：SALES-05 商机赢/输单状态守卫

- 修复目标：商机 LOST/WON 终态不能被通用更新或旧阶段接口随意翻转，尤其禁止 LOST→WON。
- 红测：
  - `tests/api/test_sales.py::TestOpportunityManagement::test_update_opportunity_rejects_lost_to_won_transition` 先失败，通用 PUT 返回 200。
  - `tests/api/test_sales.py::TestOpportunityManagement::test_stage_endpoint_rejects_lost_to_won_transition` 先失败，旧 `/stage` 返回 200。
  - `tests/api/test_sales.py::TestOpportunityManagement::test_legacy_win_endpoint_rejects_lost_opportunity` 先失败，旧 PUT `/win` 返回 200。
- 代码面：
  - `app/api/v1/endpoints/sales/utils/stage_guard.py` 新增统一商机阶段守卫。
  - `app/api/v1/endpoints/sales/opportunity_crud.py` 通用更新 `stage` 走守卫。
  - `app/api/v1/endpoints/sales/opportunity_workflow.py` 旧 `/stage`、PUT `/win`、PUT `/lose` 走守卫/终态保护。
  - `app/api/v1/endpoints/sales/opportunity_batch.py` 批量阶段更新复用守卫，且修正终态字符串/Enum 混比。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_sales.py::TestOpportunityManagement::test_update_opportunity_rejects_lost_to_won_transition tests/api/test_sales.py::TestOpportunityManagement::test_stage_endpoint_rejects_lost_to_won_transition tests/api/test_sales.py::TestOpportunityManagement::test_legacy_win_endpoint_rejects_lost_opportunity -q` 通过。
  - `.venv/bin/python -m pytest tests/api/test_sales.py::TestOpportunityManagement tests/api/test_sales.py::TestContractManagement::test_create_contract_success tests/api/test_sales.py::TestSalesFunnelWorkflow::test_g2_quote_can_continue_to_g3_contract tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_create_contract tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_create_contract_accepts_legacy_quote_payload_and_infers_context -q` 通过（11 个用例）。
  - `.venv/bin/python -m compileall app/api/v1/endpoints/sales/opportunity_crud.py app/api/v1/endpoints/sales/opportunity_workflow.py app/api/v1/endpoints/sales/opportunity_batch.py app/api/v1/endpoints/sales/utils/stage_guard.py app/api/v1/endpoints/sales/utils/__init__.py tests/api/test_sales.py` 通过。

## 2026-07-03 继续：SALES-21 商机阶段词表统一

- 修复目标：消除商机阶段 `ON_HOLD/QUALIFIED/REVIEW` 等旧前端词表与后端 `OpportunityStageEnum` 的分裂；`PUT /stage`、`advance`、统计桶、前端下拉/展示都走 `DISCOVERY/QUALIFICATION/PROPOSAL/NEGOTIATION/CLOSING/WON/LOST`。
- 红测：
  - `tests/api/test_sales.py::TestOpportunityManagement::test_stage_endpoint_rejects_legacy_on_hold_stage` 先失败，旧 `/stage` 接受 `ON_HOLD` 并返回 200。
  - `tests/api/test_sales.py::TestOpportunityManagement::test_opportunity_stage_statistics_use_canonical_closing_bucket` 先失败，统计接口没有 `CLOSING` 桶且仍产出 `ON_HOLD`。
  - `frontend/src/pages/__tests__/OpportunityManagement.test.jsx` 新增常量测试，先失败，显示前端仍为 `QUALIFIED/REVIEW/ON_HOLD`。
- 代码面：
  - `sales/utils/stage_guard.py` 的有效阶段收敛到 `OpportunityStageEnum`。
  - `sales/statistics_core.py` 阶段统计桶改由枚举生成；`statistics_reports.py` pipeline 金额只认非终态枚举阶段。
  - `opportunity_batch.py` 同步修正终态字符串/Enum 混比，并复用阶段守卫。
  - `frontend/src/pages/OpportunityManagement/constants.js`、`OpportunityManagement/index.jsx`、`OpportunityDetail.jsx`、`WinRateAnalysisCard.jsx`、`SalesStatistics.jsx`、`lib/constants/opportunityBoard.js` 统一前端阶段词表。
  - `migrations/20260703_sales_opportunity_stage_vocab_sqlite.sql` 清洗旧阶段值：`QUALIFIED/QUALIFYING -> QUALIFICATION`，`PROPOSING -> PROPOSAL`，`NEGOTIATING/ON_HOLD -> NEGOTIATION`。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_sales.py::TestOpportunityManagement tests/api/test_sales.py::TestSalesFunnelWorkflow::test_g2_quote_can_continue_to_g3_contract tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_create_contract tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_create_contract_accepts_legacy_quote_payload_and_infers_context -q` 通过（12 个用例）。
  - `npm test -- --run src/pages/__tests__/OpportunityManagement.test.jsx src/pages/SalesStatistics.test.jsx src/pages/SalesFunnel.test.jsx` 通过（24 个用例；SalesFunnel 测试仍有既有 mock 方法缺失/React key warning）。
  - `npm run build` 通过（保留既有动态/静态混合导入与 chunk size warning）。
  - `sqlite3 data/app.db` 事务 dry-run 执行清洗迁移后，阶段分布归一为 `QUALIFICATION/PROPOSAL/NEGOTIATION/DISCOVERY/WON/LOST/<NULL>`，无旧阶段值。

## 2026-07-03 继续：SALES-20 报价数量/单价正数校验

- 修复目标：报价首版创建、报价新版本创建、报价明细新增/更新都不能写入数量或单价为 0/负数的明细；前端报价明细输入也给出正数约束。
- 红测：
  - `tests/api/test_sales.py::TestQuoteManagement::test_create_quote_rejects_non_positive_item_qty_and_unit_price` 先失败，首版创建对 `qty=0/-1`、`unit_price=0/-100` 返回 201。
  - `tests/api/test_sales.py::TestQuoteManagement::test_create_quote_version_rejects_zero_quantity_without_defaulting_to_one` 先失败，新版本接口把 `qty=0` 静默默认成 1。
  - `tests/api/test_sales.py::TestQuoteManagement::test_quote_item_create_and_update_reject_non_positive_unit_price` 先失败，明细创建 `unit_price=0` 返回 200。
  - `frontend/src/pages/__tests__/QuoteCreateEdit.test.jsx` 正数输入约束测试先失败，数量/单价 number input 没有 `min/step`。
- 代码面：
  - `app/api/v1/endpoints/sales/utils/quote_item_validation.py` 新增统一校验：数量、单价必须是有限 Decimal 且大于 0。
  - `quotes.py`、`quote_versions.py` 在落库前预校验明细，保留旧客户端缺省数量按 1 处理，但明确传 0/负数直接 400。
  - `quote_items.py` 在直接新增/更新明细时校验 `qty/unit_price`。
  - `app/schemas/sales/quotes.py` 将 QuoteItem schema 的单价和更新数量/单价约束对齐为 `gt=0`。
  - `frontend/src/pages/QuoteCreateEdit/QuoteItemsTable.jsx` 给数量/单价输入加 `min="0.01"`、`step="0.01"`。
- 数据现状：
  - `sqlite3 data/app.db` 查到 8 条历史 `quote_items` 空数量/空单价、无负数；这些行的明细名称也为空，无法从版本总额无损推回单价，本次不自动改历史价格。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_sales.py::TestQuoteManagement -q` 通过（12 个用例）。
  - `.venv/bin/python -m pytest tests/api/test_sales.py::TestQuoteManagement tests/api/test_sales.py::TestSalesFunnelWorkflow::test_g2_quote_can_continue_to_g3_contract tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_create_contract tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_create_contract_accepts_legacy_quote_payload_and_infers_context -q` 通过（15 个用例）。
  - `npm test -- --run src/pages/__tests__/QuoteCreateEdit.test.jsx` 通过（2 个用例，仍有 Node `module.register()` deprecation warning）。
  - `npm run build` 通过（保留既有动态/静态混合导入、chunk size 与 Node `module.register()` warning）。
  - `.venv/bin/python -m compileall app/api/v1/endpoints/sales/quotes.py app/api/v1/endpoints/sales/quote_versions.py app/api/v1/endpoints/sales/quote_items.py app/api/v1/endpoints/sales/utils/quote_item_validation.py app/schemas/sales/quotes.py` 通过。
  - `git diff --check` 通过。

## 2026-07-03 继续：双任务表整合 P2+P3 原子切换（门面方案）

- 方案升级：不逐个改 34 个消费文件，而是把 models/progress.Task 改造为 **task_unified 的门面模型**，P2 写路径与 P3 读路径一次原子切换：
  - 列名映射（task_name→title、stage→project_stage、owner_id→assignee_id、plan_start→plan_start_date、progress_percent→progress），54 处 query(Task) 零改动；
  - **状态词汇双向翻译**：自定义 hybrid Comparator——Python 侧沿用 TODO/DONE/BLOCKED，存储侧 PENDING/COMPLETED/PAUSED，查询字面量（==、in_）自动翻译，全库 ~60 处状态字面量零清洗；
  - **全局 PROJECT 过滤**：Session do_orm_execute + with_loader_criteria 注入 task_type='PROJECT'（任务中心 TaskUnified 不受影响）；
  - **写入默认值**：before_insert 兜底 task_type/source/priority/task_code/负责人(项目PM→created_by→admin)/项目冗余列。
- 裸 SQL 4 文件手改：gantt_dependency、ai_report_tasks(日报数据源)、template_projects(WBS INSERT，顺带修历史小写'pending'脏值)、activity_minutes(纪要派生任务)。
- 聚合词汇修正 2 处：member_view 分组结果翻译回旧口径；project_dashboard_service 历史上就按 COMPLETED/PENDING 键读旧表（永远拿 0 的潜在 bug），门面切换后首次正确，BLOCKED 键改 PAUSED。
- 前端断链修复：progress.js updateProgress/complete 接任务中心真实端点；update/delete/updateAssignee（后端从不存在、零消费方）移除。
- 验证：任务域 sweep（progress/task/workload/milestone/gantt）100 过；实测门面读（旧契约输出+状态翻译）、门面写（新任务落 task_unified）、**旧 tasks 表冻结 131 行**；大面 sweep 的其余失败经逐类甄别为另一会话在改的销售/报价面在途状态与既有债（404/422 路由类、405、mock 路径类、schema 缺字段类——与 Task/状态面零交集）。
- ⚠️ 运维教训：并行会话下**禁止 git stash 对照**（对方 mid-edit 会被卷进 stash、pop 冲突）——本轮已用"从 stash 精准 checkout 我的文件"恢复，改用 HEAD worktree 做对照（但 worktree 缺测试库数据时结论也不可靠，最终以失败签名与改动面的交集判断）。stash@{0} 保留未 drop（内含对方过程态快照，勿动）。

## 2026-07-03 继续：SALES-22 销售记录级权限函数去重

- 修复目标：`app/core/sales_permissions.py` 中 `check_sales_data_permission` 只能有一个定义，避免后置同名函数覆盖前置实现；`FINANCE_ONLY` 不应通过普通销售记录的单条访问检查。
- 红测：
  - `tests/unit/test_sales_scope_expansion.py::test_sales_permissions_defines_single_check_sales_data_permission` 先失败，AST 数到两个同名函数，`__all__` 中也重复导出。
  - `tests/unit/test_sales_scope_expansion.py::TestCheckSalesDataPermission::test_finance_only_blocks` 先失败，当前覆盖版在 `owner_id == user.id` 时对 `FINANCE_ONLY` 返回 True。
- 代码面：
  - 删除后置重复的 `check_sales_data_permission` 定义，保留单一记录级权限入口。
  - 清理 `__all__` 中重复的 `check_sales_data_permission`。
  - 将合同 PDF 导出 scope 测试调整为检查 endpoint 委托与 helper 内真实权限校验，避免薄代理函数被源码字符串断言误判。
- 验证：
  - `.venv/bin/python -m pytest tests/unit/test_sales_scope_expansion.py::test_sales_permissions_defines_single_check_sales_data_permission tests/unit/test_sales_scope_expansion.py::TestCheckSalesDataPermission::test_finance_only_blocks -q` 先红后绿。
  - `.venv/bin/python -m pytest tests/unit/test_sales_scope_expansion.py tests/unit/test_sales_scope_tail.py tests/integration/test_sales_scope_integration.py -q` 通过（59 个用例；integration 仍有既有 SQLAlchemy sorted_tables cycle warnings）。
  - `.venv/bin/python -m pytest tests/unit/test_sales_permissions.py -q` 通过（既有权限重构 skip 保持原状）。
  - `.venv/bin/python -m compileall app/core/sales_permissions.py tests/unit/test_sales_scope_expansion.py` 通过。

## 2026-07-03 继续：SALES-18 报价当前版本口径统一

- 修复目标：报价成本分析不能把最新创建的版本当作当前版本；必须优先使用 `Quote.current_version_id`，与报价详情、统计和下游合同链路口径一致。
- 红测：
  - `tests/api/test_sales_quote_costs_quantity_contracts.py::TestQuoteCostQuantityContracts::test_cost_analysis_uses_quote_current_version_not_latest_created_version` 先失败：V1 仍是 `current_version_id`，但后创建的 V2-DRAFT 被成本分析返回为 `current_version`。
- 代码面：
  - `app/api/v1/endpoints/sales/quote_costs.py` 新增 `_select_current_quote_version()`，优先按 `quote.current_version_id` 选择版本。
  - 无 `current_version_id` 或指向缺失时，才显式回退到最新创建版本，保留老数据兼容。
  - 成本分析版本趋势排序补 `id` 作为同时间戳稳定排序。
- 验证：
  - `.venv/bin/python -m pytest tests/api/test_sales_quote_costs_quantity_contracts.py -q` 通过（3 个用例）。
  - `.venv/bin/python -m pytest tests/api/test_sales_quote_costs_quantity_contracts.py tests/api/test_sales_quote_cost_batch_update_contracts.py tests/api/test_sales_quote_item_contracts.py -q` 通过（9 个用例）。
  - `.venv/bin/python -m pytest tests/api/test_sales.py::TestQuoteManagement tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_create_contract tests/api/test_sales_contracts_api.py::TestSalesContractsAPI::test_create_contract_accepts_legacy_quote_payload_and_infers_context -q` 通过（14 个用例）。
  - `rg -n "versions\\[-1\\]|order_by\\(QuoteVersion\\.created_at\\)" app/api/v1/endpoints/sales/quote_costs.py app/api/v1/endpoints/sales/quote_quotes_crud.py app/api/v1/endpoints/sales/quotes.py` 无命中。
  - `.venv/bin/python -m compileall app/api/v1/endpoints/sales/quote_costs.py tests/api/test_sales_quote_costs_quantity_contracts.py` 通过。

## 2026-07-03 继续：双任务表整合 P4 收官

- 旧 tasks 物理表改名 **tasks_deprecated**（131 行冻结保留一个版本周期后删；task_id_map 保留作 ID 追溯）；改名经 PRAGMA legacy_alter_table 绕过既有坏视图。
- 前置扫尾确认：测试/alembic/DB 视图触发器零引用（唯一命中为历史迁移 SQL，按惯例不动）。
- scripts/migrate_tasks_to_unified.py 支持 P4 后优雅退化：迁移判定"生命周期结束"，--check 自动对账 tasks_deprecated（仍全绿）。
- 验证：后端重启 0 加载失败；项目任务列表/任务中心总览/项目进度汇总实测 200；任务域回归 **100 passed / 0 failed**。
- 至此双任务表整合 P1-P4 全部完成：单一事实源 task_unified，旧表仅剩改名后的备份躯壳。

## 2026-07-03 继续：SALES-14 付款审批前端接口断链

- 修复目标：`paymentApprovalApi` 不能再调用后端不存在的 `/sales/payments/approvals`；付款审批 hook 不能把 `unifiedApprovalApi` 当成带 `list/approve/reject` 的付款审批 API 使用。
- 红测：
  - `frontend/src/services/api/__tests__/paymentApproval.test.js` 先失败，请求仍打 `/sales/payments/approvals` 并被 axios mock 返回 404。
  - `frontend/src/pages/PaymentApproval/hooks/__tests__/usePaymentApproval.test.js` 从 skip 恢复后先失败，`paymentApprovalApi.list` 未被调用，暴露生产 hook 仍导入 `unifiedApprovalApi`。
- 代码面：
  - `frontend/src/services/api/paymentApproval.js` 改走统一审批真实路由：待办 `/approvals/pending/mine`，已处理 `/approvals/pending/processed`，审批动作 `/approvals/tasks/{id}/approve|reject`。
  - `tab` 仅用于前端选择端点，不再透传给后端；审批/驳回 payload 对齐 `ApproveRequest`/`RejectRequest` 的 `comment/attachments/eval_data/reject_to` 字段。
  - `usePaymentApproval.js` 改为直接导入 `paymentApprovalApi`。
- 验证：
  - `npm test -- --run src/services/api/__tests__/paymentApproval.test.js src/pages/PaymentApproval/hooks/__tests__/usePaymentApproval.test.js` 先红后绿（4 个用例）。
  - `npm test -- --run src/services/api/__tests__/approval.test.js src/services/api/__tests__/paymentApproval.test.js src/pages/PaymentApproval/hooks/__tests__/usePaymentApproval.test.js` 通过（38 个用例）。
  - `rg -n "/sales/payments/approvals|unifiedApprovalApi as paymentApprovalApi|describe\\.skip\\('usePaymentApproval" frontend/src app -S` 无命中。
  - `npm run build` 通过（保留既有 Vite 动静态混合导入、chunk size 与 Node deprecation warning）。
  - `git diff --check -- frontend/src/services/api/paymentApproval.js frontend/src/services/api/__tests__/paymentApproval.test.js frontend/src/pages/PaymentApproval/hooks/usePaymentApproval.js frontend/src/pages/PaymentApproval/hooks/__tests__/usePaymentApproval.test.js` 通过。

## 2026-07-03 继续：SALES-15 销售团队统计/排名恒 0 桩

- 修复目标：`SalesTeamService` 的个人目标、最近跟进、客户分布、跟进统计、线索质量、商机统计不能再返回 `{uid: 0/空}`；`/sales/team` 和 `/sales/team/ranking` 要消费真实销售数据。
- 红测：
  - `tests/services/test_sales_team_aggregation_contracts.py::test_sales_team_maps_aggregate_real_sales_activity` 先失败：`SalesTeamService(db)` 不支持，原方法无法查库。
  - `tests/services/test_sales_team_aggregation_contracts.py::test_sales_ranking_uses_real_opportunity_statistics` 先失败：有真实商机时排名 `opportunity_count` 仍为 0。
- 代码面：
  - `SalesTeamService` 新增 `db` 实例上下文，保留原静态团队 CRUD。
  - 补齐 `parse_period_value()` 和目标实际值计算：LEAD_COUNT、OPPORTUNITY_COUNT、CONTRACT_AMOUNT、COLLECTION_AMOUNT。
  - 6 个桩方法改为真实聚合：客户按 `sales_owner_id`，线索/商机按 `owner_id`，跟进按 `LeadFollowUp.created_by`，并统一日期范围过滤。
  - `/sales/team` 聚合工具与 `SalesRankingService` 均改为 `SalesTeamService(db)`，避免重新变成无 Session 桩。
  - 同步修正旧单测夹具和 `test_sales_team_deep.py` 的伪接口测试，让它们覆盖当前真实服务契约。
- 验证：
  - `.venv/bin/python -m pytest tests/services/test_sales_team_aggregation_contracts.py -q` 先红后绿（2 个用例）。
  - `.venv/bin/python -m pytest tests/services/test_sales_ranking_service.py -q` 通过（19 个用例）。
  - `.venv/bin/python -m pytest tests/unit/test_sales_team_service.py -q` 通过（36 个用例）。
  - `.venv/bin/python -m pytest tests/services/test_sales_team_aggregation_contracts.py tests/services/test_sales_ranking_service.py tests/unit/test_sales_team_service.py tests/unit/test_sales_team_service_coverage.py tests/unit/test_sales_team_deep.py -q` 通过（62 个用例）。
  - `.venv/bin/python -m compileall app/services/sales_team_service.py app/services/sales_ranking_service.py app/api/v1/endpoints/sales/team/utils.py tests/services/test_sales_team_aggregation_contracts.py tests/unit/test_sales_team_service.py tests/unit/test_sales_team_deep.py` 通过。
  - `git diff --check -- app/services/sales_team_service.py app/services/sales_ranking_service.py app/api/v1/endpoints/sales/team/utils.py tests/services/test_sales_team_aggregation_contracts.py tests/unit/test_sales_team_service.py tests/unit/test_sales_team_deep.py` 通过。
