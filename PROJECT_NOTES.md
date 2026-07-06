# PROJECT_NOTES

## 2026-07-05 继续：审批动作日志与业务状态历史边界收口

- 用户选择第 4 条后，收口“审批动作历史只进 `approval_action_logs`；业务状态历史进 `state_transition_logs` 或领域日志”的工程边界。
- TDD：在 `tests/unit/test_approval_engine_consolidation_guard.py` 新增架构守护，先红灯抓到 `app/services/project_change_requests/service.py` 在审批引擎外直接构造 `ApprovalActionLog`；同时禁止把 `STATUS_CHANGE/STATE_CHANGE/UPDATE_STATUS/TRANSITION` 这类业务状态动作写成审批动作。
- 代码面：`ApprovalEngineCore` 新增公共 `record_action_log()`，支持 `tenant_id`、指定 `action_at`、附件、详情、审批前后状态；项目变更服务改为调用 `ApprovalEngineService.record_action_log()`，不再直接插 `approval_action_logs`。
- 验证：审批整合守护、审批核心日志测试、项目变更统一日志测试合计 14 条通过；`rg "ApprovalActionLog\\(" app` 复核运行代码里只有审批引擎内部构造日志，模型定义除外。

## 2026-07-05 继续：PERM-11 进度兼容/行政兼容权限收口

- 用户继续后，沿 PERM-11 Top risk 继续处理业务 AUTH_ONLY 删除点；`progress_compat.py::delete_wbs_template` 背后是 20 个旧进度兼容端点整簇只校验登录态，`admin_compat.py::delete_asset` 背后是 21 个行政管理兼容端点整簇只校验登录态。
- TDD：在 `tests/test_api_permission_scan.py` 新增进度兼容权限守护与行政兼容权限守护，均先红灯确认当前为 AUTH_ONLY，再补权限转绿；另补 `test_directory_size_treats_permission_denied_as_zero`，复现 `/admin/stats` 扫到不可读目录时 500。
- 代码面：`progress_compat.py` 任务/WBS/报表读取挂 `task:read`，任务/WBS 创建挂 `task:create`，自动处理/依赖修复/WBS 更新挂 `task:update`，WBS 模板删除挂 `task:delete`。`admin_compat.py` 行政后台读取挂 `user:read`，申领/用车申请/资产创建挂 `user:create`，审批/驳回/资产更新挂 `user:update`，资产删除挂 `user:delete`；不新增权限码。`admin_stats._directory_size()` 对不可读目录/文件返回 0，避免 `/var/backups/pms` 权限拒绝打崩 `/admin/stats`；同轮补 `contract_approval/service.py` 的 `from __future__ import annotations`，恢复 Python 3.9 下 `app.main` 严格路由加载。
- 验证：进度兼容/行政兼容权限守护及相关 API/路由回归合并跑 32 条中 25 passed/7 skipped（既有 skip）；`python scripts/audit_permission_coverage.py --json-only` 后 PERM 指标为 3022 端点、PERMISSION=1175（38.9%）、AUTH_ONLY=1771、NONE=76；`python scripts/ci_guard_permission_coverage.py` 通过；相关文件 `ruff check`、`py_compile`、`git diff --check` 通过；`from app.main import app` 成功，路由加载失败 0 项，最终路由数 2993，进度/行政目标路由均已挂载。
- 边界：`service/surveys.py::submit_customer_satisfaction` 仍是最高 NONE，但属于外部客户提交；`auth.logout/change_password` 仍是本人操作；下一批 Top risk 已转向 `report.py`、`culture_wall_config.py`、`bom/bom_items.py` 和销售删除类 AUTH_ONLY。

## 2026-07-05 继续：PERM-11 工程师排产路由权限收口

- 用户继续后，沿 PERM-11 Top risk 继续处理第一个语义明确的业务 AUTH_ONLY 删除点；发现 `engineer_scheduling.py` 不是单点问题，而是 15 个工程师排产/负载/能力/预警端点整簇只校验登录态。
- TDD：在 `tests/test_api_permission_scan.py` 新增工程师排产权限守护，先红灯确认 `POST /assignments` 等端点仍为 AUTH_ONLY，再补权限转绿。
- 代码面：排产读侧看板、可用性、能力模型、负载分析、冲突检测、排产报告、AI/核心能力评估统一挂 `task:read`；创建分配挂 `task:create`；更新分配、生成预警、能力/AI/核心能力重算挂 `task:update`；取消分配挂 `task:delete`。本轮采用种子角色里稳定存在的 `task:*`，不新增权限码。
- 验证：工程师排产权限守护 1 passed；`tests/unit/test_engineer_scheduling_as17.py` 2 passed；`python scripts/audit_permission_coverage.py --json-only` 后 PERM 指标为 3022 端点、PERMISSION=1134（37.5%）、AUTH_ONLY=1812、NONE=76；`python scripts/ci_guard_permission_coverage.py` 通过；相关文件 `ruff check`、`py_compile`、`git diff --check` 通过；`from app.main import app` 成功，路由加载失败 0 项，最终路由数 2993，工程师排产目标路由均已挂载。
- 边界：`service/surveys.py::submit_customer_satisfaction` 仍是最高 NONE，但属于外部客户提交；`auth.logout/change_password` 仍是本人操作；下一批可继续收剩余业务删除类 AUTH_ONLY。

## 2026-07-05 继续：PERM-11 里程碑/经验教训兼容路由权限收口

- 用户继续后，沿 PERM-11 Top risk 继续分流；本轮没有改外部客户满意度提交、本人 logout/password 等语义敏感入口，转而收口已在线且权限语义明确的全局里程碑与经验教训兼容路由。
- TDD：在 `tests/test_api_permission_scan.py` 新增里程碑权限守护与经验教训兼容路由权限守护，先红灯确认这两组端点仍是 AUTH_ONLY，再补权限转绿。
- 代码面：`milestones.py` 列表/项目列表/详情挂 `milestone:read`，创建挂 `milestone:create`，更新/完成挂 `milestone:update`，删除挂 `milestone:delete`；`lessons_learned.py` 列表/统计/搜索/详情挂 `project_evaluation:read`，创建挂 `project_evaluation:create`，更新/删除挂 `project_evaluation:update`。
- 验证：里程碑与经验教训权限守护 2 passed；`tests/api/test_batch8_route_contracts.py::test_lessons_compat_routes_return_empty_list_and_stats` 通过；里程碑 API 回归 10 条中 3 passed/7 skipped（既有 skip）；`python scripts/audit_permission_coverage.py --json-only` 后 PERM 指标为 3022 端点、PERMISSION=1119（37.0%）、AUTH_ONLY=1827、NONE=76；`python scripts/ci_guard_permission_coverage.py` 通过；相关文件 `ruff check`、`py_compile`、`git diff --check` 通过；`from app.main import app` 成功，路由加载失败 0 项，最终路由数 2993，里程碑/经验教训目标路由均已挂载。
- 边界：当前 Top risk 仍是 `service/surveys.py::submit_customer_satisfaction` 外部提交、`auth.logout/change_password` 本人会话/密码操作，以及若干剩余 AUTH_ONLY 删除类端点，后续需要按业务语义逐个收口。

## 2026-07-05 继续：PERM-11 严格路由审计分流与甘特依赖权限收口

- 用户继续后，沿 PERM-11 Top risk 继续分流；先确认 `base_crud_router.py` 是未挂载的异步 CRUD route factory，当前主应用实际使用的是 `base_crud_router_sync.py` 生成的 customers/suppliers/materials 路由；`material/tracking.py` 与 `material/project_fusion.py` 也未挂当前严格主路由，不能按在线裸端点处理。
- TDD：在 `tests/test_api_permission_scan.py` 新增两条审计口径守护，先红灯确认上述未挂载 helper/lazy 文件会被错误扫入；再在 `scripts/audit_permission_coverage.py` 加窄范围排除清单，只排这些未挂严格主路由的文件。
- 同轮处理真实在线的 `app/api/v1/endpoints/gantt_dependency.py`：前端 `ganttDependencyApi` 调用 `/gantt/{projectId}`、新增依赖、删除依赖、关键路径接口；新增/删除会改 `task_dependencies` 和级联排期，不能只要求登录。读接口改 `project:read`，新增/删除依赖改 `project:update`。
- 验证：审计分流守护 2 passed；甘特权限守护 1 passed；`tests/unit/test_gantt_dependency_proj09.py` 3 passed；`python scripts/audit_permission_coverage.py --json-only` 后 PERM 指标为 3022 端点、PERMISSION=1105（36.6%）、AUTH_ONLY=1841、NONE=76；`python scripts/ci_guard_permission_coverage.py` 通过；相关文件 `ruff check`、`py_compile`、`git diff --check` 通过；`from app.main import app` 成功，路由加载失败 0 项，最终路由数 2993，甘特目标路由均已挂载。
- 边界：`service/surveys.py::submit_customer_satisfaction` 仍为 Top risk，但语义是外部客户提交，不能粗暴加员工权限；`auth.logout/change_password` 是本人会话/密码操作，也不应改成管理权限。

## 2026-07-05 维护：未启用报价成本历史表退役

- 清理目标：处理台账里剩余待确认的 `quote_cost_histories`。该表模型注释已标“未启用 - 报价成本历史”，运行代码没有真实读写；当前报价成本修改、重算、匹配建议、批量调价的审计已统一写入 `sales_operation_logs`。
- 执行结果：
  - 真实库 `data/app.db` 删除后业务表数为 553。
  - `quote_cost_histories` 3 行已归档到 `data/retired_unused_tables_archive_20260705_162243.db`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_162243.db`。
  - 3 行旧数据的 `total_price/total_cost/gross_margin/cost_breakdown/change_type/change_reason/changed_by` 均为空，判定为生成残留。
- 代码面：
  - 删除未启用 `QuoteCostHistory` ORM 和 `QuoteVersion.cost_histories` 关系，避免 `create_all` 复活旧表。
  - `app.models.sales`、`app.models`、`app.models.exports.complete` 不再导出 `QuoteCostHistory`。
  - `scripts/retire_unused_tables_20260705.py` 与 `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` 纳入 `quote_cost_histories` 防回潮删除；`scripts/ghost_tables_baseline.json` 移除旧 ghost 项。
- 验证：新增守护测试先红后绿；真实库复核 `quote_cost_histories` 不存在，归档库保留 3 行；ORM metadata 和所有 FK 均不再引用该表；`PRAGMA foreign_key_check` 未新增问题。

## 2026-07-05 继续：PERM-11 产能计算/组织部门/员工导入权限与审计口径收口

- 用户继续后，沿 PERM-11 剩余高风险裸端点推进；优先处理已挂主路由且会写业务数据的 `production/capacity/calculation.py`、组织部门主 CRUD 的 `departments_refactored.py`、以及批量新增/更新员工档案的 `employee_import.py`。`service/surveys.py::submit_customer_satisfaction` 虽在 Top risk 中，但源码语义是外部客户满意度提交，本轮不粗暴改成员工登录；后续应按一次性/签名 survey token 设计。
- TDD：在 `tests/test_api_permission_scan.py` 新增产能计算权限守护、APIRouter router-level 权限识别守护、组织部门权限守护、员工导入权限守护，均先红灯确认当前 `production:manage` 缺失、router 级 `hr:read` 未被审计脚本识别、组织部门端点仍是 AUTH_ONLY/NONE、员工导入端点仍只有登录态。
- 代码面：`calculate_oee`、`calculate_worker_efficiency` 统一挂 `production:manage`，并补回文件实际使用但缺失的 `get_or_404` import；`scripts/audit_permission_coverage.py` 现在识别 `APIRouter(dependencies=[Depends(require_permission(...))])` 并让函数级权限覆盖 router 级权限；`departments_refactored.py` 部门列表/树/统计/详情/人员列表挂 `hr:read`，创建挂 `hr:create`，更新/删除挂 `hr:update`；`employee_import.py` 批量导入挂 `hr:create`，导入模板说明挂 `hr:read`。
- 验证：新增权限守护 4 passed；组织部门/员工导入相关 API 回归 9 passed；`python scripts/audit_permission_coverage.py --json-only` 后 PERM 指标为 3033 端点、PERMISSION=1101（36.3%）、AUTH_ONLY=1845、NONE=87；`python scripts/ci_guard_permission_coverage.py` 通过；相关文件 `ruff check`、`py_compile`、`git diff --check` 通过；`from app.main import app` 成功，路由加载失败 0 项，最终路由数 2993，组织部门与员工导入目标路由均已挂载。

## 2026-07-05 继续：PERM-11 项目风险/排程优化/齐套排产权限收口

- 用户继续后，沿 PERM-11 裸端点继续收口；`app/api/v1/endpoints/projects/risks.py` 8 个风险 CRUD/矩阵/汇总/自动扫描端点使用自定义 `require_risk_permission("risk:*")`，审计脚本无法识别且 `risk:*` 不在当前权限种子主链，扫描结果表现为 NONE。
- 同轮继续处理 `app/api/v1/endpoints/schedule_optimization.py` fallback 路由：虽然是占位兼容文件，但已挂到主 API，前端 `scheduleOptimizationApi` 会调用分析/自动生成 BOM/自动创建采购三个接口，不能裸露。
- 同轮继续处理 `app/api/v1/endpoints/assembly_kit/scheduling.py`：生成排产建议是裸 POST，建议列表是裸 GET，接受/拒绝建议虽然有依赖但只挂 `assembly_kit:read`，实际会修改建议状态。
- TDD：在 `tests/test_api_permission_scan.py` 新增项目风险、排程优化 fallback、齐套排产建议三条权限守护，先红灯确认 `POST /{project_id}/risks`、`/schedule-optimization/projects/{project_id}/auto-*`、`/assembly-kit/scheduling/suggestions/generate` 等端点被扫描为 NONE/弱权限；再改代码转绿。
- 代码面：删除风险模块自定义权限依赖，统一复用已初始化的项目权限码：创建/自动扫描用 `project:create`，列表/详情/矩阵/汇总用 `project:read`，更新用 `project:update`，删除用 `project:delete`；同步清理无用 import。
- 排程优化 fallback：根/分析接口挂 `project:read`，自动生成 BOM 挂 `material:update`，自动创建采购挂 `purchase:create`；保持原空态返回结构，避免影响前端兼容。
- 齐套排产建议：生成建议挂 `assembly_kit:create`，建议列表挂 `assembly_kit:read`，接受/拒绝建议改挂 `assembly_kit:update`。
- 验证：项目风险/排程优化/齐套排产权限守护 3 passed；`tests/api/test_project_risks.py` 17 passed；`tests/unit/test_scheduling_suggestion_service.py` 15 passed；`python scripts/audit_permission_coverage.py --json-only` 后 PERM 指标为 3033 端点、PERMISSION=1087（35.8%）、AUTH_ONLY=1853、NONE=93；`python scripts/ci_guard_permission_coverage.py` 通过；相关文件 `ruff check`、`py_compile`、`git diff --check` 通过；`from app.main import app` 成功，路由加载失败 0 项，最终路由数 2993，排程优化与齐套排产目标路由均已挂载。

## 2026-07-05 维护：生产资源冲突表改名隔离

- 清理目标：收口 `resource_conflicts` / `resource_conflict` 这组业务域撞名。两表不是同一业务，不能合并：`resource_conflicts` 是项目阶段资源计划冲突，`resource_conflict` 是生产排程资源冲突。
- 执行结果：
  - 正式保留项目资源冲突主表 `resource_conflicts`。
  - 生产排程冲突表从 `resource_conflict` 改名为 `production_resource_conflicts`，保留原 3 行数据。
  - 真实库业务表数仍为 554；这是 rename，不是 drop。
  - 改名前整库备份：`data/app.before_production_resource_conflict_rename_20260705_140025.db`。
- 代码面：
  - `ProductionResourceConflict.__tablename__` 改为 `production_resource_conflicts`，索引名同步改为 `idx_production_conflict_*`。
  - 新增迁移 `migrations/20260705_z_rename_production_resource_conflict_sqlite.sql`，老库升级时把旧表改为清晰表名。
  - 守护测试把 `resource_conflict` 纳入退役表名集合，并要求 `production_resource_conflicts` 注册在 ORM metadata。
- 验证：红测先失败于 `resource_conflict` 仍在 `Base.metadata.tables`；改名后转绿。真实库复核：`resource_conflict` 不存在，`production_resource_conflicts=3`、`resource_conflicts=3`。迁移前后 `PRAGMA foreign_key_check` 输出一致，未新增 FK 脏数据。

## 2026-07-05 继续：PERM-11 售前 AI 知识库/情绪接口权限收口

- 用户继续后，沿 PERM-11 裸端点收口继续推进；最新 `PERMISSION_COVERAGE_AUDIT.json` 显示售前 AI 知识库与情绪分析两个已挂主路由簇仍为 NONE，且包含案例读写、问答反馈、情绪分析、跟进提醒生成/忽略等真实业务动作。
- TDD：在 `tests/test_api_permission_scan.py` 新增两条守护，先红灯确认 `app/api/v1/presale_ai_knowledge.py` 与 `app/api/presale_ai_emotion.py` 所有端点均被扫描为 NONE。
- 代码面：知识库读/搜索/问答/标签接口挂 `knowledge:read`，案例提取/新增/更新/问答反馈挂 `knowledge:write`；情绪分析/流失预测/跟进建议/提醒/趋势/批量分析统一先挂 `presale:manage`。同步校正 `tests/api/test_presales_contract_api.py` 的旧路由契约：`/presale/ai/generate-solution` 现在是 PRE-10 异步 job 桥接入口，应保留，旧 `solution/{id}/template*` 方案栈才是下线对象。
- 验证：新增权限守护 2 passed；`python scripts/audit_permission_coverage.py --json-only` 后 PERM 指标为 3033 端点、NONE=107、PERMISSION=1073（35.4%）；`python scripts/ci_guard_permission_coverage.py` 通过；`tests/test_ai_emotion_api.py` 4 passed；售前 AI 路由契约与 PRE-10 生成方案挂载契约 2 passed；相关文件 `ruff check`、`py_compile` 通过；`from app.main import app` 成功，路由加载失败 0 项，最终路由数 2993。

## 2026-07-05 维护：售前 AI 报价草稿并入正式报价链路

- 清理目标：收口 `quotes/quote_versions/quote_items` 与 `presale_ai_quotation/quotation_versions` 的报价双轨，避免同一报价金额在销售正式链和售前 AI 链各自成为事实源。
- 业务口径：正式报价唯一事实源为 `quotes`、`quote_versions`、`quote_items`；合同、审批、销售报表继续只认正式报价链。`presale_ai_quotation` 保留为 AI 草稿/三档比选工作台，`quotation_versions` 保留为 AI 草稿版本快照。
- 代码面：
  - `AIQuotationGeneratorService.promote_to_sales_quote()` 新增 AI 草稿采纳能力：解析售前工单/客户商机，复制报价头、版本、明细到正式报价链，设置 `Quote.current_version_id`，并把 AI 草稿标记为 `ACCEPTED`，备注写入 `promoted_quote_id`。
  - 新增 `/presale/ai/quotation/{quotation_id}/promote-to-sales-quote`，作为后续前端“采纳该档报价”的唯一入口；缺商机/客户时拒绝，避免生成孤儿正式报价。
  - `approve_quotation()` 保持不写旧 `quotation_approvals`，符合统一审批引擎收口方向。
- 验证：新增守护测试先红后绿；`python -m pytest tests/unit/test_presale_ai_quotation_to_sales_quote.py -q` 通过（3 passed）。真实库当前仍为 554 张业务表；`quotes=275`、`quote_versions=275`、`quote_items=697`、`presale_ai_quotation=9`、`quotation_versions=9`。
- 边界：本轮未删除 `presale_ai_quotation` / `quotation_versions`，也未自动把真实库 AI 草稿转正式报价；真实转化需要业务先选择采纳哪一档。

## 2026-07-05 继续：CI 质量门禁恢复绿灯

- 用户继续后，优先处理当前红色 CI 门禁：`ci_guard_permission_coverage` 因 NONE 端点 148、权限覆盖率 34.0% 低于基线失败；`ci_guard_ghost_tables` 因 `CompanyProfile(company_profile)`、`Competitor(competitors)` 被误报为新增幽灵表失败；`ci_guard_ai_mock` 原本通过。
- TDD：补 `tests/test_api_permission_scan.py`，覆盖 `deps.require_super_admin` 应计入 PERMISSION、备份接口必须有超管级保护、公司资质证书接口必须有权限保护；新增 `tests/unit/test_ci_guard_ghost_tables.py`，确认主数据导入脚本可作为 `company_profile` / `competitors` 写入证据。
- 代码面：`scripts/audit_permission_coverage.py` 将 `require_super_admin` 纳入权限模式；`app/api/v1/endpoints/backup.py` 所有备份/恢复/清理/统计接口加 `deps.require_super_admin`；`app/api/v1/company_certifications.py` 所有资质证书接口加 `security.require_permission("presale:manage")`；`scripts/ci_guard_ghost_tables.py` 将 `scripts/import_*.py`、`scripts/enrich_*.py` 纳入生产主数据写入证据，并识别 `INSERT OR REPLACE INTO`。
- 验证：`python scripts/ci_guard_permission_coverage.py` 通过（3032 端点，NONE=125，权限覆盖率 34.8%，基线 NONE<=143/覆盖率>=34.4）；`python scripts/ci_guard_ghost_tables.py` 通过（当前 94，基线 98，仅提示可收紧已消除项）；`python scripts/ci_guard_ai_mock.py` 通过。
- 额外验收：目标权限红测 3 passed；幽灵表守护 2 passed；`ruff check`、`py_compile`、`git diff --check` 针对本轮文件通过；`from app.main import app` 成功，路由加载失败 0 项，最终应用路由数 2992。

## 2026-07-05 继续：PERM-22 旧系统直链权限补漏

- 用户继续后，沿 `SYSTEM_IMPROVEMENT_PLAN` 的 `PERM-22` 前端路由/菜单权限守卫继续补漏：此前新中心页已有 `ModuleProtectedRoute` 守卫，但旧系统直链 `/debug/permissions`、`/customer-management`、`/supplier-management-data`、`/projects/:id/roles` 仍可绕过权限直接进入页面。
- TDD：扩展 `frontend/src/routes/modules/__tests__/permissionProtectedRoutes.test.jsx`，先证明无权限用户能看到“权限调试页面”；再补候选菜单库 `allMenuGroups` 的权限字段守护，红灯落在 `/user-management` 缺 `permission` 元数据。
- 代码面：`systemRoutes.jsx` 对旧直链补页面级守卫：权限调试复用账号权限中心 `USER_VIEW/ROLE_VIEW`，客户/供应商主数据分别用 `customer:read`、`supplier:read`，项目角色页面用后端同口径 `project_role:read`；`allMenuItems.js` 给系统/主数据候选菜单补 `permission/permissionAny/permissionLabel`。
- 验证：`npm --prefix frontend test -- --run src/routes/modules/__tests__/permissionProtectedRoutes.test.jsx --silent` 通过（6 passed）；`npm exec eslint -- src/routes/modules/systemRoutes.jsx src/lib/allMenuItems.js src/routes/modules/__tests__/permissionProtectedRoutes.test.jsx`（cwd=`frontend`）通过；`npm --prefix frontend run build` 通过（仅保留既有动态/静态重复导入与大 chunk warning）。

## 2026-07-05 继续：Python 3.9 销售路由 import 兼容

- 用户要求继续下一个高价值任务后，优先处理上一批暴露出的全局验收 blocker：默认 `python` 实际是 3.9.6，销售聚合路由 import 会在 `X | None` 注解求值处崩溃，导致无法做真实 router 级验收。
- TDD：新增 `tests/unit/test_sales_router_import_contract.py`，要求 `from app.api.v1.endpoints.sales import router` 成功，并确认 `/contracts/{contract_id}/amendments` 仍在销售路由中；红测先失败于 `app/models/service/enums.py:152` 的 `str | None`，继续暴露 `operation_log_service.py`、通知 webhook、scheduler metrics 和发票 legacy endpoint 参数注解的同类 Python 3.9 兼容问题。
- 代码面：将 `validate_service_ticket_transition()` 返回注解改回 `Optional[str]`；为仍使用 PEP604 注解的 app 文件补 `from __future__ import annotations`，避免普通 import 时运行期求值；FastAPI/Pydantic 会解析 endpoint 参数和模型字段，不能仅靠 future，因此将发票 workflow/legacy `Body` 参数、角色导航参数、审批 legacy payload、AI job 请求、公司认证字段、多币种/排产 query、管理节奏 query、服务工单 escalation 模型等改为 `Optional[...]`；Webhook `_webhook_url()` 和工程师绩效 scope union 也改回 Python 3.9 可求值写法。
- 验证：`python -m pytest -q tests/unit/test_sales_router_import_contract.py` 通过；直接执行 `python - <<'PY' ... from app.api.v1.endpoints.sales import router ...` 返回 `True` 和 409 条路由，确认合同变更路径可见；继续执行 `python - <<'PY' import app.main; print(len(app.main.app.routes)) PY` 成功，API 路由加载失败汇总 0 项，最终应用路由数 2992。

## 2026-07-05 继续：第三批只读历史表外部归档删除

- 用户继续要求清理没有用的表后，进一步处理 app 运行代码零引用的只读历史表：`legacy_approval_archives`、`tasks_deprecated`、`task_id_map`。这些表已完成主链切换，留在主库只会干扰表口径；历史数据转入外部归档库和整库备份。
- TDD：先给 `tests/unit/test_unused_table_retirement.py` 补红测 `test_retire_unused_tables_archives_history_only_tables`，要求脚本归档并删除三张只读历史表；旧清单未覆盖，红测失败。
- 代码面：将 `legacy_approval_archives`、`tasks_deprecated`、`task_id_map` 加入 `scripts/retire_unused_tables_20260705.py` 的退役表清单；同步更新 `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` 防回潮。
- 真实库执行：
  - dry-run：`.venv/bin/python scripts/retire_unused_tables_20260705.py data/app.db --archive-path /tmp/retired_unused_tables_history_dry_run_20260705.db`，命中 `legacy_approval_archives=125`、`tasks_deprecated=131`、`task_id_map=131`。
  - 正式执行：`.venv/bin/python scripts/retire_unused_tables_20260705.py data/app.db --drop-tables`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_120303.db`；外部归档库：`data/retired_unused_tables_archive_20260705_120303.db`。
  - 已删除表：`legacy_approval_archives`、`tasks_deprecated`、`task_id_map`；真实库业务表数从 570 降到 567。
- 验证：
  - 真实库中三张目标表查询为空，归档库 manifest/表行数分别为 125、131、131。
  - 删除前备份与删除后库的 `PRAGMA foreign_key_check` 输出完全一致；本轮未新增 FK 脏数据。
  - 删除后后端代码零引用表为 0；剩余 12 张无模型表均有 app 运行代码直接读写，不能继续按“无模型/无引用”粗删。

## 2026-07-05 继续：第二批旧 RBAC 残留表删除

- 用户要求继续清理表格后，重新扫描删表后的真实库：572 张业务表，17 张无 SQLAlchemy 模型表；真正低风险的新候选只剩旧 RBAC 残留 `role_exclusions`、`user_role_assignments`，以及只依赖后者的视图 `v_user_active_roles`。
- 业务判断：当前权限主链仍是 `user_roles`、`role_api_permissions`、`permission_audits`，大量运行代码直接使用 `UserRole(user_roles)`；本轮不动主链。`role_exclusions` / `user_role_assignments` 无 app/frontend 运行引用，仅旧脚本和旧视图痕迹。
- TDD：先给 `tests/unit/test_unused_table_retirement.py` 补红测 `test_retire_unused_tables_drops_dependent_views_before_tables`，要求归档 `v_user_active_roles` 定义并先删视图再删表；旧脚本无 `dropped_views` 报告，红测失败。
- 代码面：扩展 `scripts/retire_unused_tables_20260705.py`，新增 `RETIRABLE_VIEWS=("v_user_active_roles",)`、视图 manifest 归档、先 drop view 后 drop table；将 `role_exclusions`、`user_role_assignments` 加入退役表清单；同步更新 `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql`。
- 真实库执行：
  - dry-run：`.venv/bin/python scripts/retire_unused_tables_20260705.py data/app.db --archive-path /tmp/retired_unused_tables_rbac_dry_run_20260705.db`，命中 `role_exclusions=6`、`user_role_assignments=6`、`v_user_active_roles`。
  - 正式执行：`.venv/bin/python scripts/retire_unused_tables_20260705.py data/app.db --drop-tables`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_114553.db`；外部归档库：`data/retired_unused_tables_archive_20260705_114553.db`。
  - 已删除表：`role_exclusions`、`user_role_assignments`；已删除视图：`v_user_active_roles`；真实库业务表数从 572 降到 570。
- 验证：
  - 真实库中 `role_exclusions`、`user_role_assignments`、`v_user_active_roles` 查询为空。
  - 归档库 manifest 确认两张表各 6 行，并保存 `v_user_active_roles` 的 source SQL。
  - 删除前备份与删除后库的 `PRAGMA foreign_key_check` 输出完全一致；本轮未新增 FK 脏数据。
  - 删除后无模型表 15 张；剩余多为仍被运行代码直接读写的裸 SQL 表或只读历史表，不适合继续按“无模型”粗暴删除。

## 2026-07-05 继续：第一批未用/生成残留表删除

- 用户确认“好”后，按“备份 -> 外部归档 -> drop -> 验证”执行第一批低风险表清理；目标是真正删掉无用表，不再只停在台账。
- 真实库：`/Users/flw/non-standard-automation-pm/data/app.db`；删除前整库备份：`data/app.before_unused_tables_drop_20260705_113611.db`；外部归档库：`data/retired_unused_tables_archive_20260705_113611.db`。
- 新增归档/删表脚本：`scripts/retire_unused_tables_20260705.py`，默认只归档，只有显式 `--drop-tables` 才删表；新增防回潮迁移：`migrations/20260705_z_drop_unused_residual_tables_sqlite.sql`。
- 已删除 18 张表：`lead_requirement_facility_v2`、`lead_requirement_technical_v2`、`lead_requirement_basic_v2`、`funding_records`、`equity_structures`、`funding_usages`、`funding_rounds`、`investors`、`department_default_roles`、`department_role_admins`、`role_template_permissions`、`role_audits`、`currency_rates`、`currency_history`、`ecn_records`、`shortage_alerts`、`mat_shortage_alert`、`quotation_templates`。
- 代码收口：
  - 删除空的 `LeadRequirement*V2` 模型文件和销售模型导出，保留当前主链 `lead_requirement_details`。
  - 删除未启用的 `QuotationTemplate` ORM/Schema/tenant-scope 配置，保留正式报价模板 `quote_templates`。
  - `app/utils/scheduler_config/shortage.py` 将紧急缺料采购任务依赖从旧 `mat_shortage_alert` 改为真实使用的 `alert_records`。
  - `scripts/ghost_tables_baseline.json` 移除已删除模型对应 ghost 项。
- 验证：
  - TDD 红测先失败于缺少归档脚本和退役模型仍注册；改动后 `.venv/bin/python -m pytest tests/unit/test_unused_table_retirement.py -q` 通过。
  - dry-run：`.venv/bin/python scripts/retire_unused_tables_20260705.py data/app.db --archive-path /tmp/retired_unused_tables_dry_run_20260705.db` 通过，18 张候选表均可归档，无保留表外键阻断。
  - 正式执行：`.venv/bin/python scripts/retire_unused_tables_20260705.py data/app.db --drop-tables` 成功，归档行数和预期一致。
  - 删除后真实库目标表查询为空，业务表数从 590 降至 572；`retired_unused_tables_archive_20260705_113611.db` 的 manifest 保留每张表 row_count。
  - 删除前备份与删除后库的 `PRAGMA foreign_key_check` 输出完全一致；现存 FK 脏数据是本轮前已有的 `work_order -> worker`、`stock_count_detail -> stock_count_task`、`permission_audits -> users`、`presale_expenses -> projects`，本轮未新增。
  - `.venv/bin/python -m pytest tests/unit/test_unused_table_retirement.py tests/unit/test_shortage_alert_task_backfill.py -q` 通过（11 passed）。
  - `git diff --check`、`.venv/bin/ruff check ...`、`.venv/bin/python -m py_compile ...` 针对本轮文件通过。
  - 精确扫描 `app/` 内退役表的 `__tablename__` 与 `FROM/JOIN/INSERT/UPDATE/DELETE` 运行时 SQL，无命中；`Base.metadata.tables` 中退役模型表为空。
- 边界：`scripts/ci_guard_ghost_tables.py` 当前仍失败于工作区已有的 `CompanyProfile(company_profile)`、`Competitor(competitors)` 新 ghost 模型，和本轮删除表无关；本轮未处理该未落地主链。

## 2026-07-05 继续：流程引擎/审批引擎首批整合

- 用户要求“整合一下”后，先做小范围可验证收口：把流程相关对象分成审批引擎、业务状态机、领域 workflow 门面、状态变更 hook、deprecated 旧审批 workflow。
- 新增台账：`docs/database/process-engine-survival-ledger-20260705.md`，列出 `approval_*` 主表、`state_transition_logs`、销售漏斗日志、售前 AI workflow 日志、ECN/工时/变更请求领域审批表的保留/待合并/只读历史建议。
- 运行代码整合：
  - 发票审批模板编码统一到真实库主线 `TPL_INVOICE`，改动 `app/services/approval_workflow_service.py`、`app/services/approval_engine/adapters/invoice.py`、`app/utils/init_approval_data.py`。
  - `app/api/v1/endpoints/sales/invoices/__init__.py` 移除全局 `approvals_router` 二次挂载；通用审批只走 `/approvals`，发票域保留自己的新版 `workflow_router`。
  - `tests/audit_p0/test_p0_02_approval_template_no_seed.py` 的发票期望种子同步为 `TPL_INVOICE`。
- 守护测试：
  - `tests/unit/test_approval_engine_consolidation_guard.py` 新增三条：发票路由不得再挂全局 approvals、发票运行/种子代码不得再用 `SALES_INVOICE`、app 运行代码不得 import deprecated `approval_engine.workflow_engine`。
  - 红测先失败于发票路由双挂和 `SALES_INVOICE` 旧编码；改动后守护转绿。
- 测试夹具：
  - `tests/conftest.py` 不再强制 import 已删除的 `TaskApprovalWorkflow`；该旧任务审批模型缺失时按 `None` 兼容，`mock_important_task` 不再硬写废弃 `task_approval_workflows`。
- 边界：
  - `app/services/approval_engine/workflow_engine.py` 仍保留为 deprecated 测试兼容层，运行主线不引用；删除前需要迁掉大量旧测试。
  - `ecn_approvals` / `ecn_approval_matrix` 仍被 ECN 服务、通知、看板消费，不能直接删；应作为下一批“领域审批表迁入统一审批引擎”的专题。

## 2026-07-05 继续：真实库旧审批表删除与统一引擎收口

- 用户确认“删除了”后，已对真实库 `/Users/flw/non-standard-automation-pm/data/app.db` 执行旧审批表归档删除；删除前备份：`data/app.before_approval_legacy_drop_20260705_105449.db`。
- 归档结果：`legacy_approval_archives` 125 行；旧表已删除 11 张：`approval_history`、`approval_records`、`approval_workflow_steps`、`approval_workflows`、`contract_approvals`、`invoice_approvals`、`quotation_approvals`、`quote_approvals`、`quote_cost_approvals`、`role_assignment_approvals`、`task_approval_workflows`。
- 修复真实库 `projects.approval_record_id` 的残留外键：已从旧 `approval_records.id` 改为统一 `approval_instances.id`；重建前备份：`data/app.before_projects_fk_rebuild_20260705_110742.db`；`projects` 行数重建前后均为 105，`approval_record_id` 非空 0。
- 代码收口：删除旧销售/任务/报价/合同/发票/售前报价专用审批 ORM 表模型和旧 `sales/legacy_approval.py` 兼容残留；任务重要审批、合同审批兼容门面、合同增强服务、报价状态历史、售前 AI 报价审批路径均不再写旧专用审批表。
- 新增最终清理迁移：`migrations/20260705_999_drop_retired_approval_tables_sqlite.sql`，防止旧迁移/兼容路径后续把废弃审批表留在库里。
- 新增守护：`tests/unit/test_approval_engine_consolidation_guard.py` 现在校验旧审批表不再注册进 `Base.metadata.tables`。
- 验证：
  - 真实库旧审批表查询为空；统一审批核心表计数：`legacy_approval_archives=125`、`approval_templates=10`、`approval_instances=9`、`approval_tasks=19`、`approval_action_logs=36`。
  - ORM metadata：11 张旧审批表为空，`legacy_approval_*` metadata 也为空。
  - `projects` 外键清单确认 `approval_record_id -> approval_instances.id`。
  - `.venv/bin/python -m py_compile ...` 通过。
  - `.venv/bin/python -m pytest tests/unit/test_approval_engine_consolidation_guard.py -q` 通过（5 passed）。
  - `.venv/bin/python -m pytest tests/unit/test_approval_workflow_service.py -q` 通过（11 passed）。
  - `.venv/bin/python -m pytest tests/unit/test_approval_adapter_quote.py tests/unit/test_quote_adapter.py tests/unit/test_approval_adapter_invoice.py tests/unit/test_approval_adapter_invoice_batch19.py -q` 通过；旧 `quote_approvals`/`invoice_approvals` 专用同步用例按废弃路径跳过。
- 边界：`PRAGMA foreign_key_check` 仍报告既有非审批历史坏账：`work_order -> worker`、`stock_count_detail -> stock_count_task`、`permission_audits -> users`、`presale_expenses -> projects`；本轮未处理这些非审批数据完整性问题。

## 2026-07-05 复核：数据库表存废台账第一版

- 只读检查对象：`/Users/flw/non-standard-automation-pm/data/app.db` 当前 600 张业务表；69 张空表，243 张非空 1-3 行小表，其中 232 张刚好 3 行，未发现字段结构完全一致的复制表。
- 产出：`docs/database/table-survival-ledger-20260705.md`。
- 结论：当前主要不是“复制表”，而是同业务多套事实源/新旧双轨/生成残留并存。第一批已列任务表、销售目标、正式报价 vs 售前 AI 报价、售前方案模板、资源冲突、缺料预警、线索需求 V1/V2、审批表、权限数据范围残留、融资/币种 demo 残留的存废建议。
- 边界：本轮未做任何删表、迁移或数据修改；台账里的“废弃候选/合并”必须另起迁移任务，先备份、做引用扫描、外键/视图/触发器扫描和回归。

## 2026-07-05 继续：审批双轨收口到统一审批引擎

- 修复目标：统一审批引擎，包括销售域；同一业务多套审批表、新旧双轨和原型残留不能继续补逻辑。
- 主事实源：保留 `approval_templates`、`approval_instances`、`approval_tasks`、`approval_action_logs`；旧审批表进入只读历史/归档删除路线。
- 代码变更：
  - `app/api/v1/endpoints/sales/__init__.py` 移除旧销售审批配置路由 `/sales/approval-workflows`，并删除旧原型路由文件 `app/api/v1/endpoints/sales/workflows.py`；审批办理继续走统一 `/approvals`。
  - `app/services/approval_engine/adapters/quote.py`、`invoice.py`、`contract.py` 删除旧专用审批表回写方法，不再同步 `quote_approvals`、`invoice_approvals`、`contract_approvals`。
  - `app/services/approval_workflow_service.py` 保留旧调用方法名，但内部改为统一审批门面：`start_approval()` 走 `ApprovalEngineService.submit()`，审批/驳回/撤回查 `approval_instances/approval_tasks`，不再读写旧 `approval_records`。
  - `app/services/sales_reminder/sales_flow_reminders.py` 的审批超时提醒改查统一 `approval_tasks`，不再读旧 `approval_workflow_steps`。
  - 新增 `scripts/consolidate_legacy_approval_tables.py`，把 11 张旧审批表归档进 `legacy_approval_archives`，默认只归档，只有显式 `--drop-legacy-tables` 才删源表。
  - 新增 `tests/unit/test_approval_engine_consolidation_guard.py`，防止旧销售工作流路由和旧适配器回写方法回潮。
  - `tests/unit/test_approval_workflow_service.py` 对齐兼容门面新的统一审批实现，不再 patch 旧审批表枚举/模型。
  - `tests/unit/test_sales_operation_audit_perm07.py` 删除旧 `/sales/approval-workflows` 配置路由审计用例；该路由已下线，不再作为 PERM-07 应保留能力。
  - `app/api/v1/endpoints/sales/quote_costs.py` 顺手修复 PERM-07 匹配建议应用入口漏初始化 `updated_items` 的真实 bug。
- 临时库演练：复制 `data/app.db` 到临时目录后执行 `consolidate_legacy_approval_tables(conn, drop_legacy_tables=True)`，结果 `archived_rows=125`，归档表行数 125，删除旧表：`approval_history`、`approval_records`、`approval_workflow_steps`、`approval_workflows`、`contract_approvals`、`invoice_approvals`、`quotation_approvals`、`quote_approvals`、`quote_cost_approvals`、`role_assignment_approvals`、`task_approval_workflows`；临时库剩余旧审批表 0。
- 验证：
  - `.venv/bin/python -m pytest tests/unit/test_approval_engine_consolidation_guard.py -q` 通过（3 个用例）。
  - `.venv/bin/python -m pytest tests/unit/test_approval_adapter_quote.py tests/unit/test_quote_adapter.py tests/unit/test_approval_adapter_invoice.py tests/unit/test_approval_adapter_invoice_batch19.py -q` 通过；旧专用审批表同步测试已按废弃路径跳过。
  - `.venv/bin/python -m pytest tests/unit/test_sales_operation_audit_perm07.py -q` 通过。
  - 旧 service/提醒邻域回归 `.venv/bin/python -m pytest tests/unit/test_approval_workflow_service.py tests/unit/test_approval_workflow_service_coverage.py app/tests/services/approval_workflow/test_approval_workflow_service.py tests/unit/test_batch_services_1.py::test_approval_workflow_start_approval_basic tests/unit/test_batch_services_1.py::test_approval_workflow_select_workflow_by_routing tests/unit/test_batch_services_1.py::test_approval_workflow_approve_step tests/unit/test_batch_services_1.py::test_approval_workflow_reject_step tests/unit/test_batch_services_1.py::test_approval_workflow_withdraw_approval tests/unit/test_sales_flow_reminders.py tests/unit/test_services_p3_coverage.py::TestSalesFlowReminders -q` 通过（3 skipped 为既有复杂 DB 查询跳过）。
  - 组合回归 `.venv/bin/python -m pytest tests/unit/test_approval_engine_consolidation_guard.py tests/unit/test_approval_adapter_quote.py tests/unit/test_quote_adapter.py tests/unit/test_approval_adapter_invoice.py tests/unit/test_approval_adapter_invoice_batch19.py tests/unit/test_sales_operation_audit_perm07.py tests/unit/test_approval_workflow_service.py tests/unit/test_approval_workflow_service_coverage.py app/tests/services/approval_workflow/test_approval_workflow_service.py tests/unit/test_batch_services_1.py::test_approval_workflow_start_approval_basic tests/unit/test_batch_services_1.py::test_approval_workflow_select_workflow_by_routing tests/unit/test_batch_services_1.py::test_approval_workflow_approve_step tests/unit/test_batch_services_1.py::test_approval_workflow_reject_step tests/unit/test_batch_services_1.py::test_approval_workflow_withdraw_approval tests/unit/test_sales_flow_reminders.py tests/unit/test_services_p3_coverage.py::TestSalesFlowReminders -q` 通过；跳过项为旧专用审批表同步测试与既有复杂 DB 查询跳过。
  - `.venv/bin/ruff check ...` 和 `.venv/bin/python -m py_compile ...` 针对本轮代码/测试文件通过。
- 边界：真实 `data/app.db` 未执行归档/删表；执行真实库清理前必须先备份并显式确认。

## 2026-07-05 复核：已修待验/基本完成项归一关闭

- 复核范围：`ADMIN-07`、`ADMIN-17`、`ADMIN-19`、`TEN-03`、`TEN-06`。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_admin_office_real.py tests/unit/test_file_upload_service.py tests/unit/test_documents_upload_content_validation_admin17.py tests/unit/test_document_delete_file_lifecycle_admin19.py tests/unit/test_project_document_orphan_cleanup_admin19.py tests/unit/test_tenant_fail_closed.py tests/unit/test_ten03_core_tables_tenant_scope.py tests/unit/test_tenant_query_scope_ten02.py tests/unit/test_ten03_batch5_tenant_scope.py` 通过（94 个用例）。
  - `import app.main` 路由清单确认 `/api/v1/admin/*`、`/api/v1/documents/*`、`/api/v1/tenants/*` 已注册，路由加载失败汇总 0 项。
  - `.venv/bin/python -m ruff check ...` 与 `.venv/bin/python -m py_compile ...` 针对相关实现/测试文件通过。
- 台账：`docs/root-docs-archive/20260704/FUNCTIONAL_AUDIT_TRACKER.md` 已将上述 5 项统一改为 `已验证`。
- 边界：`ADMIN-19` 的真实 orphan 文件清理仍未执行 `--delete`，只是功能闭环和 dry-run 扫描能力已验证；清理真实上传目录需要单独确认。

## 2026-07-05 继续：提升方案 P2 小项——PERM-07 业务操作审计日志首批/二批/三批/四批/五批/六批/七批/八批/九批/十批/十一批/十二批/十三批/十四批/十五批/十六批/十七批/十八批/十九批/二十批/二十一批/二十二批/二十三批/二十四批/二十五批/二十六批/二十七批/二十八批/二十九批/三十批/三十一批/三十二批/三十三批/三十四批/三十五批/三十六批/三十七批/三十八批/三十九批/四十批/四十一批/四十二批/四十三批/四十四批/四十五批/四十六批/四十七批/四十八批/四十九批/五十批/五十一批/五十二批/五十三批/五十四批/五十五批/五十六批/五十七批/五十八批/五十九批/六十批/六十一批/六十二批/六十三批/六十四批/六十五批/六十六批/六十七批/六十八批/六十九批/七十批/七十一批/七十二批/七十三批/七十四批/七十五批/七十六批/七十七批/七十八批接线

- 修复项：`PERM-07` 销售业务审计切口：权限/角色/用户已有 `permission_audits`，销售业务侧虽已有 `SalesOperationLog` 模型/服务/查询端点文件，但销售聚合路由未挂 `operation_logs`，报价明细 create/update/delete 写操作也完全不落 `sales_operation_logs`；回款登记/更新/删除/核销、发票创建/更新/删除/开票/作废、合同基础创建/更新/删除、合同从报价生成/签署/归档、合同收款计划创建、客户创建/更新/删除、客户标签新增/批量新增/删除、销售活动 quick 记录/AI 纪要确认/纪要回填商机、客户联系人 CRUD/设主联系人/主联系人自动降级、商机创建/更新/删除、商机阶段/赢单/输单、商机 POST 高频/兼容工作流、商机评分/阶段门、线索创建/更新/删除、线索需求详情创建/更新、线索/商机需求冻结、线索/商机未决事项创建/更新/关闭、线索/商机 AI 澄清创建/答复更新、线索转商机、线索跟进、线索标无效、线索批量状态更新、线索批量转商机、线索批量分配负责人、商机批量操作路由注册、商机批量阶段更新、商机批量负责人更新、商机批量关闭、销售目标创建/更新、销售团队创建/更新/删除、销售团队成员新增/更新/移除/批量新增、销售审批流程配置创建/更新、报价模板创建/更新/删除/版本创建/发布、销售数据审核提交/驳回/撤销、报价交付日期更新、报价主表创建、报价更新/删除、报价版本创建、报价通用状态变更、报价直接审批、报价正式审批提交/通过/驳回/批量通过/批量驳回/撤回也只改业务表，不留业务操作日志。
- TDD：
  - 红测 1：`SalesOperationLogService.log_operation()` 应兼容当前 `User.department` 字符串字段；旧代码按 `operator.department.name` 读取会 AttributeError。
  - 红测 2：销售聚合路由应包含 `/operation-logs/{entity_type}/{entity_id}` 与 `/operation-logs/` 查询入口；旧 `sales/__init__.py` 未 include。
  - 红测 3：报价明细新增/更新/删除应在同一事务内写 3 条 `QUOTE_VERSION` 操作日志；旧写入口只改业务表和重算报价版本金额，日志为空。
  - 红测 4：回款登记/更新/删除应按同一发票写 `INVOICE` 操作日志，分别为 `CREATE/UPDATE/DELETE`，并保留 paid_amount/payment_status 前后值。
  - 红测 5：发票核销应写 `STATUS_CHANGE` 操作日志，记录 `PENDING → PAID` 及核销后的已收款金额。
  - 红测 6：发票创建/更新/删除应按同一发票写 `INVOICE` 操作日志，保留金额、购买方、草稿删除前状态。
  - 红测 7：发票审批后开票、作废应写 `STATUS_CHANGE` 操作日志；已开票作废生成的红冲发票也应有 `CREATE` 日志。
  - 红测 8：合同创建/更新/删除应按同一合同写 `CONTRACT` 操作日志，保留合同名称、金额、付款条款和草稿删除前状态。
  - 红测 9：从报价创建合同应写 `CONTRACT` 的 `CREATE` 操作日志，保留报价版本、金额和付款条款。
  - 红测 10：合同签署、归档应写 `CONTRACT` 的 `STATUS_CHANGE` 操作日志，记录 `APPROVED → SIGNED → COMPLETED` 和签署日期。
  - 红测 11：客户创建/更新/删除应按同一客户写 `CUSTOMER` 操作日志，保留客户名称、状态、付款条件、年成交额和删除前状态。
  - 红测 12：商机创建/更新/删除应按同一商机写 `OPPORTUNITY` 操作日志，保留商机名称、阶段、概率、预算范围和删除前阶段。
  - 红测 13：商机阶段更新、赢单、输单应按对应商机写 `OPPORTUNITY` 的 `STATUS_CHANGE` 操作日志，记录阶段前后值。
  - 红测 14：商机 POST `advance/win/lose/loss` 高频/兼容入口应按对应商机写 `OPPORTUNITY` 的 `STATUS_CHANGE` 操作日志，记录阶段前后值和输单原因。
  - 红测 15：商机评分应写 `OPPORTUNITY` 的 `UPDATE` 操作日志；阶段门提交应写 `OPPORTUNITY` 的 `STATUS_CHANGE` 操作日志，保留评分/风险等级和 gate_status 前后值。
  - 红测 16：线索创建/更新/删除应按同一线索写 `LEAD` 操作日志，保留客户名称、状态、电话、需求摘要和删除前状态。
  - 红测 17：报价主表创建应按同一报价写 `QUOTE` 的 `CREATE` 操作日志，保留报价编号、客户/商机 ID、状态和当前版本金额快照；旧 `create_quote()` 只建报价和版本，日志为空。
  - 红测 18：线索转商机应写线索 `LEAD/CONVERT` 日志和新商机 `OPPORTUNITY/CREATE` 日志，保留线索 `NEW → CONVERTED` 和新商机 lead/customer/stage 快照；旧入口只建商机和改线索状态，日志为空。
  - 红测 19：报价版本创建应写新版本 `QUOTE_VERSION/CREATE` 日志；若设为当前版本，还应写报价主表 `QUOTE/UPDATE` 日志，保留 `current_version_id` 前后值。
  - 红测 20：报价通用状态变更应写 `QUOTE/STATUS_CHANGE` 日志，保留 `DRAFT → PENDING_APPROVAL` 和变更原因；旧入口只调用 `StatusUpdateService` 改状态。
  - 红测 21：报价直接审批通过应写报价 `QUOTE/APPROVE` 与当前版本 `QUOTE_VERSION/APPROVE` 日志，保留报价状态和版本审批人/审批时间前后值。
  - 红测 22：线索跟进应写 `LEAD/COMMENT` 操作日志，保留 `next_action_at` 前后值和跟进内容；旧入口只新增 follow-up 记录，不留线索操作日志。
  - 红测 23：报价正式提交审批服务链应写 `QUOTE/SUBMIT` 操作日志，保留 `DRAFT → PENDING_APPROVAL` 与当前版本 ID；旧 `QuoteApprovalService.submit_quotes_for_approval()` 只调用审批引擎，不留报价操作日志。
  - 红测 24：报价正式审批通过应写 `QUOTE/APPROVE` 操作日志，保留 `PENDING_APPROVAL → APPROVED` 和审批意见。
  - 红测 25：报价正式审批驳回应写 `QUOTE/REJECT` 操作日志，保留 `PENDING_APPROVAL → REJECTED` 和驳回意见。
  - 红测 26：报价基础信息更新应写 `QUOTE/UPDATE` 操作日志，保留 `valid_until` 前后值；旧 `quote_quotes_crud.update_quote()` 只更新报价主表。
  - 红测 27：草稿报价删除应写 `QUOTE/DELETE` 操作日志，保留删除前报价编号、状态和当前版本 ID；旧 `quote_quotes_crud.delete_quote()` 直接 `delete_obj()` 提交，日志为空。
  - 红测 28：报价正式审批批量通过应逐条写 `QUOTE/APPROVE` 操作日志，保留每张报价 `PENDING_APPROVAL → APPROVED` 和批量审批意见。
  - 红测 29：报价正式审批批量驳回应逐条写 `QUOTE/REJECT` 操作日志，保留每张报价 `PENDING_APPROVAL → REJECTED` 和批量驳回意见。
  - 红测 30：报价正式审批撤回应写 `QUOTE/STATUS_CHANGE` 操作日志，保留 `PENDING_APPROVAL → DRAFT` 和撤回原因；旧 `withdraw_approval()` 只调用审批引擎，不留销售业务日志。
  - 红测 31：线索批量状态更新入口应注册到销售线索路由聚合；旧 `leads/__init__.py` 未 include `batch.router`，`/leads/batch/status` 不在活动路由中。
  - 红测 32：线索标无效应写 `LEAD/STATUS_CHANGE` 操作日志，保留 `NEW → INVALID` 和无效原因；旧入口因 `LeadStatusEnum.INVALID` 缺失直接 AttributeError，且不留日志。
  - 红测 33：线索批量状态更新应为每条成功线索写 `LEAD/STATUS_CHANGE` 操作日志，保留 `NEW → INVALID` 和批量原因；旧入口只改状态和 follow-up，日志为空。
  - 红测 34：线索批量转商机应为每条成功线索写 `LEAD/CONVERT`，并为每个新商机写 `OPPORTUNITY/CREATE`；旧入口只建商机和改线索状态，日志为空。
  - 红测 35：线索批量分配负责人应为每条成功线索写 `LEAD/ASSIGN`，保留 `owner_id` 前后值；旧入口只改负责人和 follow-up，日志为空。
  - 红测 36：商机批量操作路由应注册 `/opportunities/batch/stage|owner|close`；旧 `sales/__init__.py` 未 include `opportunity_batch.router`。
  - 红测 37：商机批量阶段更新应为每条成功商机写 `OPPORTUNITY/STATUS_CHANGE`，保留 `DISCOVERY → QUALIFICATION` 和批量原因；旧入口只改阶段/updated_by/updated_at，日志为空。
  - 红测 38：商机批量负责人更新应为每条成功商机写 `OPPORTUNITY/ASSIGN`，保留 `owner_id` 前后值；旧入口只改负责人/updated_by/updated_at，日志为空。
  - 红测 39：商机批量关闭应为每条成功商机写 `OPPORTUNITY/STATUS_CHANGE`，保留 `NEGOTIATION → WON` 和关闭原因；旧入口只改终态/closed_at/close_reason，日志为空。
  - 红测 40：客户联系人创建/更新/删除应按同一联系人写 `CONTACT` 操作日志，保留客户 ID、姓名、职位、手机、主联系人标记等快照；旧入口只改 `contacts` 表，日志为空。
  - 红测 41：设置主要联系人应写 `CONTACT/STATUS_CHANGE` 操作日志，保留 `is_primary: False → True`；旧入口只改布尔值，日志为空。
  - 红测 42：设置主要联系人时，原主要联系人被自动降级也应写 `CONTACT/STATUS_CHANGE` 操作日志；旧入口只记录新主联系人，旧主联系人静默变更。
  - 红测 43：创建新主要联系人时，原主要联系人被自动降级也应写 `CONTACT/STATUS_CHANGE` 操作日志；旧入口使用批量 update，旧主联系人无留痕。
  - 红测 44：更新联系人为主要联系人时，原主要联系人被自动降级也应写 `CONTACT/STATUS_CHANGE` 操作日志；旧入口使用批量 update，旧主联系人无留痕。
  - 补测 45：客户标签单个新增应写 `CUSTOMER/UPDATE` 操作日志，保留 `tags: [] → ["重点客户"]`；当前 worktree 已有接线，作为客户标签切口基线回归。
  - 红测 46：客户标签批量新增应写 `CUSTOMER/UPDATE` 操作日志，保留既有标签到新增多标签后的快照；旧入口只批量插入 `customer_tags`，日志为空。
  - 红测 47：按 `tag_id` 删除客户标签应写 `CUSTOMER/UPDATE` 操作日志，保留删除前后 tags 快照；旧入口走 `delete_obj()` 提前提交，日志为空。
  - 红测 48：按 `tag_name` 删除客户标签应写 `CUSTOMER/UPDATE` 操作日志，保留删除前后 tags 快照；旧入口走 `delete_obj()` 提前提交，日志为空。
  - 红测 49：销售快速活动同时关联客户和商机时，应分别写 `CUSTOMER/COMMENT` 与 `OPPORTUNITY/COMMENT` 操作日志，保留活动 ID、活动编号、类型、主题和跟进任务；旧入口只插入 `customer_communications`，日志为空。
  - 补测 50：销售快速活动只关联线索时，应写 `LEAD/COMMENT` 操作日志，保留活动 ID、类型和跟进任务；该分支复用同一 quick activity 审计 helper。
  - 红测 51：AI 会议纪要确认落库并关联客户/商机时，应分别写 `CUSTOMER/COMMENT` 与 `OPPORTUNITY/COMMENT` 操作日志，保留 communication_id/communication_no、会议主题和后续任务；回填商机需求成熟度/验收依据/预算时，还应写 `OPPORTUNITY/UPDATE` 并保留 requirement_maturity、acceptance_basis、budget_range 前后值；旧入口只插入 `customer_communications` 并 raw SQL 回填商机，日志为空。
  - 红测 52：线索需求详情创建/更新应写 `LEAD/UPDATE` 操作日志，保留 `requirement_detail` 前后快照；旧入口只 `save_obj()` 保存详情，不留业务操作日志，且节拍秒数快照未统一成两位字符串。
  - 红测 53：线索/商机需求冻结应写 `LEAD/STATUS_CHANGE` 与 `OPPORTUNITY/STATUS_CHANGE`，保留 `requirement_detail` 冻结前后值和 `requirement_freeze` 快照；旧 schema 仍要求 `freeze_version` 而真实前端/模型使用 `version_number`，且创建冻结不写销售操作日志。
  - 红测 54：线索/商机未决事项创建、商机未决事项更新和关闭应写 `LEAD/UPDATE`、`OPPORTUNITY/UPDATE` 与 `OPPORTUNITY/STATUS_CHANGE`，保留 `open_item` 前后快照；旧入口还会因线索/商机同日同 ID 生成相同 `item_code` 而唯一键冲突。
  - 红测 55：线索/商机 AI 澄清创建和答案更新应写来源实体 `UPDATE` 操作日志，保留 `ai_clarification` 问题/答案快照；旧入口创建请求 schema 没有 `answers` 字段却直接读取，修复后又失败于日志不存在。
  - 红测 56：报价交付日期更新应写 `QUOTE/UPDATE` 操作日志，保留 `delivery_date` 前后值；旧 `quote_delivery.py` 只更新字段并提交，不留销售操作日志。
  - 红测 57：合同收款计划创建应写 `CONTRACT/UPDATE` 操作日志，保留 `payment_plans` 从空到分期计划的前后快照；旧入口只创建 `ProjectPaymentPlan` 并提交。
  - 红测 58：销售目标创建/更新应写 `TARGET/CREATE` 与 `TARGET/UPDATE` 操作日志，保留 target_scope、target_type、period_value、target_value、status 等快照；旧入口只 `save_obj/db.commit`，日志为空。
  - 红测 59：销售团队创建/更新/软删除应写 `TEAM/CREATE`、`TEAM/UPDATE`、`TEAM/DELETE` 操作日志，保留 team_code、team_name、team_type、sort_order、is_active 等前后快照；旧入口只 `save_obj/db.commit`，日志为空。
  - 红测 60：销售团队成员新增、更新、移除应写同一团队 `TEAM/UPDATE` 操作日志，保留 `team_member` 前后快照；旧入口只改 `sales_team_members` 并提交，日志为空。
  - 红测 61：销售团队成员批量新增应写同一团队 `TEAM/UPDATE` 汇总日志，保留批量前后的 `team_members` 列表；旧入口只批量插入成员并提交，日志为空。
  - 红测 62：销售审批流程配置创建和更新应写 `APPROVAL_WORKFLOW/CREATE` 与 `APPROVAL_WORKFLOW/UPDATE` 操作日志，保留 workflow 基础字段和审批步骤前后快照；旧 `sales/workflows.py` 只改配置表，不留业务操作日志。
  - 红测 63：报价模板创建/更新/删除、模板版本创建和模板发布应写 `QUOTE_TEMPLATE` 与 `QUOTE_TEMPLATE_VERSION` 操作日志，保留模板基础字段、当前版本、版本结构和定价规则快照；旧 `sales/quote_templates.py` 只改模板/版本表，不留销售业务操作日志。
  - 红测 64：销售数据审核提交、驳回、撤销应按来源业务实体写 `SUBMIT/REJECT/STATUS_CHANGE` 操作日志，保留审核请求、原值、新值、变更字段和审核意见；旧 `sales/data_audit.py` 只写 `sales_data_audit_requests`，且 `SalesDataAuditService` 仍把字符串 `User.department` 当对象读取 `.name`。
  - 红测 65：合同模板创建/更新、版本创建和版本发布应写 `CONTRACT_TEMPLATE` 与 `CONTRACT_TEMPLATE_VERSION` 操作日志，保留模板基础字段、当前版本、合同条款结构、条款库、附件、审批流和发布人快照；旧 `contract_templates.py` 还会在创建时读取不存在的 `template_in.owner_id` 并 AttributeError。
  - 红测 66：CPQ 规则集创建/更新应写 `CPQ_RULE_SET/CREATE` 与 `CPQ_RULE_SET/UPDATE` 操作日志，保留规则编码、基准价、配置项、价格矩阵、审批阈值、可见范围和负责角色前后快照；旧 `cpq_rules.py` 还会在创建时读取不存在的 `rule_set_in.status` 并 AttributeError。
  - 红测 67：新版结构化报价模板创建/更新、版本创建和版本发布应写 `QUOTE_TEMPLATE` 与 `QUOTE_TEMPLATE_VERSION` 操作日志，保留模板编码、当前版本、结构、定价规则、配置 schema、折扣规则和发布人快照；旧 `sales/templates/quote_templates.py` 还会在创建时读取不存在的 `template_in.owner_id` 并 AttributeError。
  - 红测 68：报价成本模板创建、更新、删除应写 `QUOTE_COST_TEMPLATE/CREATE/UPDATE/DELETE` 操作日志，保留模板编码、模板类型、成本结构、总成本、启用状态等快照；旧 `sales/cost_templates.py` 只改 `quote_cost_templates`，日志为空。
  - 红测 69：采购物料成本创建、更新、删除应写 `PURCHASE_MATERIAL_COST/CREATE/UPDATE/DELETE` 操作日志，保留物料编码、物料名称、单价、供应商、采购日期、匹配优先级等快照；旧 `sales/purchase_material_costs.py` 只改 `purchase_material_costs`，日志为空。
  - 红测 70：报价成本明细更新入口应写 `QUOTE_VERSION/UPDATE` 操作日志，保留明细项成本、成本分类、成本来源、数量、单价、备注前后快照；旧 `sales/quote_costs.py` 直接改 `QuoteItem` 并提交，日志为空。
  - 红测 71：报价成本重算入口应写 `QUOTE_VERSION/UPDATE` 操作日志，保留 `cost_total/total_price/gross_margin` 前后快照；旧 `sales/quote_costs.py` 重算版本汇总后直接提交，日志为空，且金额乘法中间值可能以 4 位小数进入审计快照。
  - 红测 72：报价成本匹配建议应用入口应写 `QUOTE_VERSION/UPDATE` 操作日志，保留版本汇总和被批量更新的明细项快照；旧 `sales/quote_costs.py` 批量更新明细、重算版本后直接提交，日志为空，且汇总金额可能以 4 位小数进入审计快照。
  - 红测 73：报价成本批量调价入口应写 `QUOTE_VERSION/UPDATE` 操作日志，保留批量更新前后明细项列表、mode/rate/updated_count；旧 `sales/quote_costs.py` 批量更新 `QuoteItem.unit_price` 后直接提交，日志为空。
  - 红测 74：物料成本更新提醒配置更新和确认处理应写 `MATERIAL_COST_REMINDER/UPDATE` 与 `MATERIAL_COST_REMINDER/STATUS_CHANGE` 操作日志，保留提醒间隔、下次提醒日、通知对象、提醒次数等快照；旧 `sales/cost_reminder.py` 只保存提醒配置/确认状态，日志为空。
  - 红测 75：物料成本匹配命中后会更新采购物料成本 `usage_count/last_used_at`，应写 `PURCHASE_MATERIAL_COST/UPDATE` 操作日志；旧 `sales/cost_matching.py` 走 `save_obj()` 静默提交，日志为空。
  - 红测 76：团队 PK 创建、更新、完成应写 `TEAM_PK/CREATE/UPDATE/STATUS_CHANGE` 操作日志，保留参赛团队、目标值、奖励说明、获胜团队和结果汇总快照；旧 `sales/team/pk.py` 只保存 PK 记录，日志为空。
  - 红测 77：回款争议创建应写 `RECEIVABLE_DISPUTE/CREATE` 操作日志，保留关联回款计划、争议金额、原因、状态和期望解决日快照；旧 `sales/disputes.py` 只创建争议记录，日志为空。
  - 红测 78：售前费用化未中标项目批量创建 `PresaleExpense` 时应写 `PRESALE_EXPENSE/CREATE` 操作日志，保留项目、线索/商机、费用类型、金额、工时和创建人快照；旧 `sales/expenses.py` 只批量写费用记录并提交，日志为空。
  - 红测 79：毛利率预警配置更新和软删除应写 `MARGIN_ALERT_CONFIG/UPDATE/DELETE` 操作日志，保留阈值、启用状态和变更字段；旧 `sales/margin_alerts.py` 只改配置并提交，日志为空。
  - 红测 80：评分规则创建和激活应写 `SCORING_RULE/CREATE` 与 `SCORING_RULE/STATUS_CHANGE` 操作日志，保留版本、规则 JSON、启用状态和描述；旧 `sales/assessments/scoring_rules.py` 只改评分规则表，日志为空。
  - 红测 81：激活新评分规则时，旧激活规则被自动停用也应写 `SCORING_RULE/STATUS_CHANGE` 操作日志；旧入口只批量取消其他规则启用状态，不留停用审计。
  - 红测 82：失败案例创建和更新应写 `FAILURE_CASE/CREATE` 与 `FAILURE_CASE/UPDATE` 操作日志，保留案例编号、项目、行业、失败标签、预警信号和复盘结论；旧 `sales/assessments/failure_cases.py` 只 `save_obj()` 静默提交。
  - 红测 83：线索/商机优先级计算后应分别写 `LEAD/UPDATE` 与 `OPPORTUNITY/UPDATE` 操作日志，保留 `priority_score` 和评分结果等级；旧 `sales/priority.py` 只改优先级字段并提交，日志为空。
  - 红测 84：线索/商机申请技术评估后应分别写来源实体 `UPDATE` 操作日志，保留 `assessment_id` 与 `assessment_status=PENDING`；旧 `sales/assessments/assessments.py` 只更新来源对象并提交，日志为空。
  - 红测 85：执行技术评估完成后应分别写来源实体 `UPDATE` 操作日志，保留 `assessment_status=PENDING -> COMPLETED`；旧 `evaluate_assessment` 只调用评估服务完成状态同步并提交，缺第二条完成日志。
  - 红测 86：合同变更记录创建应写 `CONTRACT/UPDATE` 操作日志，保留 `contract_amendments` 从空到新增变更的前后快照；旧 `sales/contracts/deliverables.py` 使用与当前 schema 不一致的字段并直接 `save_obj()`，既会读取不存在的 title，也不留业务操作日志。
  - 红测 87：技术评估模板创建应写 `ASSESSMENT_TEMPLATE/CREATE` 操作日志，保留模板编码、名称、分类、权重和阈值快照；旧 `sales/assessment_templates.py` 只写模板表，日志为空。
  - 红测 88：技术评估模板更新应写 `ASSESSMENT_TEMPLATE/UPDATE` 操作日志，保留名称、阈值等前后值；旧入口只更新模板表，日志为空。
  - 红测 89：技术评估模板设为默认应写 `ASSESSMENT_TEMPLATE/STATUS_CHANGE` 操作日志，保留 `is_default` 前后值；旧入口只改默认标记，日志为空。
  - 红测 90：技术评估项单个新增应写 `ASSESSMENT_ITEM/CREATE` 操作日志，保留模板、编码、维度、权重和评分标准快照；旧入口只写评估项表，日志为空。
  - 红测 91：技术评估项批量新增也应逐项写 `ASSESSMENT_ITEM/CREATE` 操作日志；旧批量入口只批量插入，日志为空。
  - 红测 92：技术评估风险创建和状态更新应写 `ASSESSMENT_RISK/CREATE` 与 `ASSESSMENT_RISK/STATUS_CHANGE` 操作日志，保留风险标题、等级、状态、解决说明等快照；旧入口只改风险表，日志为空。
  - 红测 93：技术评估版本快照创建应写 `ASSESSMENT_VERSION/CREATE` 操作日志，保留评估 ID、版本号、说明、总分和决策快照；旧入口只创建版本记录，日志为空。
  - 红测 94：AI 方案评审结果持久化应写商机 `OPPORTUNITY/UPDATE` 操作日志，保留 `solution_review.high_risk/resolved/reviews` 快照；旧 `sales/utils/solution_review.py` 只写 `opportunity_requirements.extra_json` 并提交，日志为空。
  - 红测 95：AI 方案评审人工处置应写商机 `OPPORTUNITY/STATUS_CHANGE` 操作日志，保留 `solution_review.resolved/resolution` 前后快照；旧入口只写 extra_json 和 AI feedback，销售业务日志为空。
  - 红测 96：发票审批 start 应写 `INVOICE/SUBMIT` 操作日志，保留 `DRAFT -> PENDING_APPROVAL` 与审批实例 ID；旧 `sales/invoices/workflow.py` 只调用统一审批引擎，不留发票业务日志。
  - 红测 97：发票审批通过动作应写 `INVOICE/APPROVE` 操作日志，保留 `PENDING_APPROVAL -> APPROVED` 和审批意见；旧 workflow action 只改审批/发票状态，不留销售操作日志。
  - 红测 98：发票审批驳回动作应写 `INVOICE/REJECT` 操作日志，保留 `PENDING_APPROVAL -> REJECTED` 和驳回意见；旧 workflow action 同样日志为空。
- 代码面：
  - `SalesOperationLogService` 增加轻量实例化兼容和部门字段解析，兼容字符串部门与旧 Department-like 对象。
  - `/sales/operation-logs` 查询路由接入销售聚合路由。
  - `quote_items.py` 在 create/update/delete 三个写入口写 `SalesOperationLog`，old/new value 使用可 JSON 序列化快照，记录 item_id、报价版本、数量、单价、成本等关键字段。
  - 新增 `invoice_operation_audit.py` 统一发票审计快照/变更字段逻辑，金额、日期、枚举都转成 JSON 安全值。
  - `payment_records.py` 在回款登记、回款更新、回款删除、发票核销四个入口写 `SalesOperationLog`，实体统一为 `INVOICE`，与实际承载表一致；日志与业务字段修改同一事务提交。
  - `sales/invoices/basic.py` 在发票创建、更新、删除入口写 `INVOICE` 操作日志；删除入口改为同一事务内 `db.delete + log + commit`，不再走会提前 commit 的 `delete_obj()`。
  - `sales/invoices/operations.py` 在开票写 `APPROVED → ISSUED` 状态日志；作废写原票 `ISSUED/APPROVED → CANCELLED` 状态日志；已开票作废生成的 `RED_CREDIT` 负票同步写创建日志。
  - `sales/invoices/workflow.py` 在发票审批 start/通过/驳回/委托/撤回动作写 `INVOICE` 操作日志，审批引擎继续负责统一审批状态，销售业务日志记录发票 old/new 快照和审批意见。
  - 新增 `contract_operation_audit.py` 统一合同审计快照/变更字段逻辑。
  - `sales/contracts/basic.py` 在合同基础创建、更新、删除入口写 `CONTRACT` 操作日志；删除入口同一事务内 `db.delete + log + commit`。
  - `sales/contracts/basic.py` 在从报价创建合同入口写 `CONTRACT` 创建日志，在归档入口写 `STATUS_CHANGE` 日志。
  - `sales/contracts/sign_project.py` 在合同签署入口写 `STATUS_CHANGE` 日志，日志与签署日期、状态更新同一事务提交。
  - `sales/payments/payment_plans.py` 在合同收款计划创建入口写 `CONTRACT/UPDATE`，把付款计划列表纳入合同审计快照。
  - 新增 `customer_operation_audit.py` 统一客户审计快照/变更字段逻辑。
  - `sales/customers.py` 在客户创建、更新、删除入口写 `CUSTOMER` 操作日志；创建/删除入口不再走会提前提交的 `save_obj/delete_obj`，改为业务变更和日志同一事务提交。
  - `sales/customer_tags.py` 将客户标签变更纳入客户画像审计快照，单个新增、批量新增、按 ID 删除、按名称删除均写 `CUSTOMER/UPDATE`，记录 `tags` 前后值和标签名 remark；删除入口不再走会提前提交的 `delete_obj()`。
  - `sales/activity_minutes.py` 的 `quick_activity()` 和 `confirm_minutes()` 在活动/纪要确认落库后写销售操作日志：按关联对象分别记录 `CUSTOMER/COMMENT`、`OPPORTUNITY/COMMENT`、`LEAD/COMMENT`，快照包含活动 ID、活动编号、类型、主题、内容和跟进任务；`confirm_minutes()` 回填商机需求/预算/成熟度时改用 ORM 快照并写 `OPPORTUNITY/UPDATE`；`quick-ai` 复用 `quick_activity()`，同步获得留痕。
  - 新增 `contact_operation_audit.py` 统一联系人审计快照/变更字段逻辑，`SalesEntityType` 增加 `CONTACT`。
  - `sales/contacts.py` 在联系人创建、更新、删除入口写 `CONTACT` 操作日志，设置主联系人入口写 `CONTACT/STATUS_CHANGE`；创建新主联系人、更新为主联系人、显式设置主联系人时，原主联系人自动降级也逐条写 `CONTACT/STATUS_CHANGE`；创建/删除入口不再走会提前提交的 `save_obj/delete_obj`，改为业务变更和日志同一事务提交。
  - 新增 `opportunity_operation_audit.py` 统一商机审计快照/变更字段逻辑。
  - `sales/opportunity_crud.py` 在商机创建、更新、删除入口写 `OPPORTUNITY` 操作日志；删除入口不再走会提前提交的 `delete_obj()`，改为业务变更和日志同一事务提交。
  - `sales/opportunity_workflow.py` 在 PUT 阶段更新、赢单、输单入口写 `OPPORTUNITY` 的 `STATUS_CHANGE` 操作日志，与阶段字段变更同一事务提交。
  - `sales/opportunity_workflow.py` 在 POST `advance`、POST `win`、POST 兼容 `lose`、POST 新 `loss` 入口写 `OPPORTUNITY` 的 `STATUS_CHANGE` 操作日志；输单原因写入 `remark`。
  - `sales/opportunity_workflow.py` 在商机评分入口写 `UPDATE` 日志，在阶段门提交入口写 `STATUS_CHANGE` 日志。
  - `sales/__init__.py` 注册 `opportunity_batch.router`，并保持在动态 `opportunities.router` 之前，避免静态批量路径被动态详情路由吞掉。
  - `sales/opportunity_batch.py` 在批量阶段更新入口写 `OPPORTUNITY/STATUS_CHANGE` 操作日志，保留阶段变更快照和批量原因。
  - `sales/opportunity_batch.py` 在批量负责人更新入口写 `OPPORTUNITY/ASSIGN` 操作日志，在批量关闭入口写 `OPPORTUNITY/STATUS_CHANGE` 操作日志，保留负责人/终态变更快照和原因。
  - `opportunity_operation_audit.py` 的商机审计快照补入 `close_reason` 与 `closed_at`，让批量关闭日志不只在 remark 里留原因，也在 old/new 快照和 changed_fields 中可追溯。
  - 新增 `lead_operation_audit.py` 统一线索审计快照/变更字段逻辑。
  - `sales/leads/crud.py` 在线索创建、更新、删除入口写 `LEAD` 操作日志；创建/删除入口不再走会提前提交的 `save_obj/delete_obj`，改为业务变更和日志同一事务提交。
  - `sales/requirement_details.py` 在线索需求详情创建/更新入口写 `LEAD/UPDATE` 操作日志，快照包含需求对象、场景、成熟度、SOW/接口/图纸、节拍、验收依据、冻结状态等字段，并将浮点节拍统一为两位字符串。
  - `sales/requirement_freezes.py` 在线索需求冻结入口写 `LEAD/STATUS_CHANGE`，在商机需求冻结入口写 `OPPORTUNITY/STATUS_CHANGE`，冻结记录和业务日志同一事务提交，快照包含冻结点、版本号、ECR 要求和说明。
  - `schemas/sales/requirement_freezes.py` 对齐真实模型和前端字段：使用 `freeze_type/version_number/requires_ecr/description/freeze_time`，不再暴露旧的 `freeze_version/freeze_reason`。
  - `sales/assessments/open_items.py` 为未决事项编号加入来源类型和序号，避免线索/商机同 ID 撞码；创建/更新/关闭未决事项时按来源写 `LEAD/UPDATE`、`OPPORTUNITY/UPDATE` 或 `OPPORTUNITY/STATUS_CHANGE`，快照保留阻塞报价、责任方、关闭证据等字段。
  - `sales/ai_clarifications.py` 创建 AI 澄清时兼容无 `answers` 的真实 schema，请求落库后按来源写 `LEAD/UPDATE` 或 `OPPORTUNITY/UPDATE`；更新答案时保留回答前后快照。
  - `sales/quote_delivery.py` 复用报价审计 helper，在交付日期更新入口写 `QUOTE/UPDATE`，日志与交付日期变更同一事务提交。
  - `SalesEntityType` 增加 `TARGET`；`sales/targets.py` 在销售目标创建/更新入口写 `TARGET/CREATE` 与 `TARGET/UPDATE`，金额、日期和枚举字段统一转 JSON 安全值。
  - `SalesEntityType` 增加 `TEAM`；`sales/team/crud.py` 在销售团队创建、更新、软删除入口写 `TEAM/CREATE`、`TEAM/UPDATE`、`TEAM/DELETE`，创建入口不再走会提前提交的 `save_obj()`。
  - `sales/team/members.py` 在团队成员新增、重新激活、更新、移除入口写 `TEAM/UPDATE`，快照保留成员角色、主团队标记、启用状态和备注；批量新增写一条团队成员列表前后快照汇总日志。
  - `SalesEntityType` 增加 `APPROVAL_WORKFLOW`；`sales/workflows.py` 在销售审批流程配置创建/更新入口写 `APPROVAL_WORKFLOW/CREATE`、`APPROVAL_WORKFLOW/UPDATE`，快照包含流程类型、名称、启用状态、路由规则和审批步骤。
  - `SalesEntityType` 增加 `QUOTE_TEMPLATE` 与 `QUOTE_TEMPLATE_VERSION`；`sales/quote_templates.py` 在报价模板创建、更新、删除、版本创建、发布入口写模板/版本操作日志，快照包含模板基础字段、当前版本、模板结构、定价规则和发布状态。
  - `sales/data_audit.py` 在销售数据审核提交、通过/驳回、撤销入口按来源实体写 `SUBMIT/APPROVE/REJECT/STATUS_CHANGE` 操作日志；`SalesDataAuditService` 的申请人部门读取对齐当前 `User.department` 字符串/对象双形态。
  - `SalesEntityType` 增加 `CONTRACT_TEMPLATE` 与 `CONTRACT_TEMPLATE_VERSION`；`sales/templates/contract_templates.py` 在合同模板创建、更新、版本创建、版本发布入口写模板/版本操作日志，并修复创建请求读取不存在 `owner_id` 的 AttributeError。
  - `SalesEntityType` 增加 `CPQ_RULE_SET`；`sales/templates/cpq_rules.py` 在 CPQ 规则集创建、更新入口写规则集操作日志，并修复创建请求读取不存在 `status` 的 AttributeError。
  - `sales/templates/quote_templates.py` 在新版结构化报价模板创建、更新、版本创建、版本发布入口写 `QUOTE_TEMPLATE` 与 `QUOTE_TEMPLATE_VERSION` 操作日志，并修复创建请求读取不存在 `owner_id` 的 AttributeError。
  - `SalesEntityType` 增加 `QUOTE_COST_TEMPLATE`；`sales/cost_templates.py` 在报价成本模板创建、更新、删除入口写成本模板操作日志，删除入口不再走会提前提交的 `delete_obj()`。
  - `SalesEntityType` 增加 `PURCHASE_MATERIAL_COST`；`sales/purchase_material_costs.py` 在采购物料成本创建、更新、删除入口写采购物料成本操作日志，创建/删除入口不再走会提前提交的 `save_obj/delete_obj()`。
  - `sales/quote_costs.py` 在报价成本明细更新入口写 `QUOTE_VERSION/UPDATE` 操作日志，快照保留成本项字段前后值，日志与明细更新同一事务提交。
  - `sales/quote_costs.py` 在报价成本重算入口写 `QUOTE_VERSION/UPDATE` 操作日志，版本汇总金额持久化前统一量化到 2 位，避免审计快照出现乘法中间精度。
  - `sales/quote_costs.py` 在报价成本匹配建议应用入口写 `QUOTE_VERSION/UPDATE` 操作日志，old/new 快照包含版本汇总和明细列表，版本汇总金额同样量化到 2 位。
  - `sales/quote_costs.py` 在报价成本批量调价入口写 `QUOTE_VERSION/UPDATE` 操作日志，old/new 快照包含明细列表和本次调价参数。
  - `SalesEntityType` 增加 `MATERIAL_COST_REMINDER`；`sales/cost_reminder.py` 在物料成本提醒配置更新和确认入口写提醒实体操作日志。
  - `sales/cost_matching.py` 在采购物料成本匹配命中并更新使用次数时写 `PURCHASE_MATERIAL_COST/UPDATE` 操作日志，保留 `usage_count/last_used_at` 前后快照。
  - `SalesEntityType` 增加 `TEAM_PK`；`sales/team/pk.py` 在团队 PK 创建、更新、完成入口写 PK 操作日志，结果汇总按 JSON 快照入账。
  - `SalesEntityType` 增加 `RECEIVABLE_DISPUTE`；`sales/disputes.py` 在回款争议创建入口写争议操作日志，争议记录和日志同一事务提交。
  - `SalesEntityType` 增加 `PRESALE_EXPENSE`；`sales/expenses.py` 在未中标项目费用化创建售前费用记录时写费用操作日志，费用记录和日志同一事务提交。
  - `SalesEntityType` 增加 `MARGIN_ALERT_CONFIG`；`sales/margin_alerts.py` 在毛利率预警配置更新和软删除入口写配置操作日志，配置变更和日志同一事务提交。
  - `SalesEntityType` 增加 `SCORING_RULE`；`sales/assessments/scoring_rules.py` 在评分规则创建、激活和旧激活规则自动停用入口写评分规则操作日志，`rules_json` 解析后入账，业务变更和日志同一事务提交。
  - `SalesEntityType` 增加 `FAILURE_CASE`；`sales/assessments/failure_cases.py` 在失败案例创建/更新入口写失败案例操作日志，JSON 字符串字段解析成数组入账，业务变更和日志同一事务提交。
  - `sales/priority.py` 在线索/商机优先级计算入口写来源实体 `UPDATE` 操作日志，快照包含持久化的 `priority_score` 和本次评分返回的 key/priority/importance/urgency 等级。
  - `sales/assessments/assessments.py` 在线索/商机技术评估申请与执行完成入口写来源实体 `UPDATE` 操作日志，覆盖 `assessment_id` 与 `assessment_status` 从空到 PENDING、从 PENDING 到 COMPLETED 的关键闭环。
  - `sales/contracts/deliverables.py` 兼容当前 `ContractAmendmentCreate` 字段，在合同变更创建入口写 `CONTRACT/UPDATE` 操作日志，审计快照包含 `contract_amendments` 列表和新增变更的原因、内容、金额、申请日期、状态。
  - `sales/assessment_templates.py` 在技术评估模板创建/更新/设默认、评估项单个/批量新增、评估风险创建/状态更新、评估版本快照创建入口写对应 `ASSESSMENT_*` 操作日志。
  - `sales/utils/solution_review.py` 与真实商机端点接入 AI 方案评审审计：评审落库写 `OPPORTUNITY/UPDATE`，人工处置写 `OPPORTUNITY/STATUS_CHANGE`，旧调用不传 `current_user` 仍兼容。
  - `tests/factories.py` 将旧 `ApprovalWorkflow/ApprovalWorkflowStep` 工厂改为兼容模型存在时才定义；不假造已移除旧模型，只防止全局 conftest 在旧销售审批工作流模型缺失时导入断裂。
  - `sales/leads/actions.py` 在线索转商机入口写 `LEAD` 的 `CONVERT` 日志，并为新建商机同步写 `OPPORTUNITY` 的 `CREATE` 日志，两条日志与商机创建、线索状态变更同一事务提交。
  - `sales/leads/follow_ups.py` 在线索跟进入口写 `LEAD/COMMENT` 操作日志，记录下次行动时间前后值和跟进内容。
  - `sales/leads/actions.py` 在线索标无效入口写 `LEAD/STATUS_CHANGE` 操作日志；`LeadStatusEnum` 补入服务层已消费的 `INVALID` 状态。
  - `sales/leads/batch.py` 批量状态更新入口为每条成功线索写 `LEAD/STATUS_CHANGE` 操作日志；批量转商机入口写 `LEAD/CONVERT` 与新商机 `OPPORTUNITY/CREATE`；批量分配负责人入口写 `LEAD/ASSIGN`，均与业务变更同一事务提交；`sales/leads/__init__.py` 将批量路由纳入聚合并保持静态路由先于动态详情路由。
  - 新增 `quote_operation_audit.py` 统一报价主表审计快照/变更字段逻辑，当前版本金额、税额、毛利等金额字段转为 JSON 安全字符串。
  - `sales/quotes.py` 在报价创建入口写 `QUOTE` 创建日志，日志与报价、当前版本创建同一事务提交。
  - `quote_operation_audit.py` 暴露 `quote_version_audit_value()` 与 `log_quote_version_operation()`，统一报价版本审计快照和日志写入。
  - `sales/quote_versions.py` 在报价版本创建入口写 `QUOTE_VERSION/CREATE`；设为当前版本时同步写 `QUOTE/UPDATE`，与版本创建同一事务提交。
  - `sales/quote_status.py` 在通用状态变更入口写 `QUOTE/STATUS_CHANGE`，记录状态前后值和原因。
  - `sales/quote_per_id_approval.py` 在漏斗报价无待办任务的直接审批兜底入口写 `QUOTE/APPROVE` 与 `QUOTE_VERSION/APPROVE`，记录状态、审批人和审批时间。
  - `quote_approval_service.py` 在正式提交/通过/驳回/撤回审批服务链写 `QUOTE/SUBMIT`、`QUOTE/APPROVE`、`QUOTE/REJECT`、`QUOTE/STATUS_CHANGE` 操作日志；批量通过/驳回复用单条审批动作，逐张报价写入操作日志，记录提交/审批/撤回原因、状态变化和当前版本快照。
  - `quote_quotes_crud.py` 在报价基础信息更新和草稿删除入口写 `QUOTE/UPDATE` 与 `QUOTE/DELETE` 操作日志；删除入口不再走会提前提交的 `delete_obj()`，改为日志与删除同一事务提交。
- 验证：报价撤回红测 `test_quote_withdraw_approval_writes_quote_status_change_log` 先失败于 `sqlalchemy.exc.NoResultFound`；线索标无效红测先失败于 `LeadStatusEnum.INVALID` 缺失；线索批量状态红测先失败于日志为空；线索批量转商机红测先失败于 `len(lead_logs) == 0`；线索批量分配负责人红测先失败于 `len(logs) == 0`；商机批量路由红测先失败于 `/opportunities/batch/stage` 不在活动路由中；商机批量阶段/负责人/关闭日志接线后转绿；关闭快照加严红测先失败于 `KeyError: 'close_reason'`，补入审计快照字段后转绿；客户联系人 CRUD 红测先失败于日志为空，设主联系人目标日志红测先失败于 `NoResultFound`，设置/创建/更新为主联系人时原主联系人自动降级红测先失败于只记录新联系人，补入逐条降级审计后转绿；客户标签批量新增/按 ID 删除/按名称删除红测均先失败于 `sqlalchemy.exc.NoResultFound`，补入同事务标签审计后转绿；销售快速活动客户+商机红测先失败于 `len(logs) == 0`，补入 quick activity 审计后转绿；AI 会议纪要确认 COMMENT 红测先失败于 `len(logs) == 0`，补入 confirm minutes 审计后转绿；会议纪要回填商机 UPDATE 红测先失败于 `sqlalchemy.exc.NoResultFound`，补入 `OPPORTUNITY/UPDATE` 后转绿；线索需求详情审计回归曾失败于 `45.0 != "45.00"`，当前快照格式化后单测转绿；需求冻结红测先失败于 `freeze_version` schema 缺失，schema 对齐后再失败于 `sqlalchemy.exc.NoResultFound`，接入冻结审计后转绿；未决事项红测先失败于 `open_items.item_code` 唯一键冲突，编号修复后再失败于 `sqlalchemy.exc.NoResultFound`，接入 open item 审计后转绿；AI 澄清红测先失败于 `AIClarificationCreate` 缺少 `answers` 属性，创建兼容后再失败于 `sqlalchemy.exc.NoResultFound`，接入来源实体审计后转绿；报价交付日期红测先失败于 `sqlalchemy.exc.NoResultFound`，接入报价审计后转绿；销售目标红测先失败于 `logs == []`，接入 `TARGET` 审计后转绿；销售团队 CRUD 红测先失败于 `logs == []`，接入 `TEAM` 审计后转绿；销售团队成员新增/更新/移除红测先失败于 `logs == []`，批量新增红测先失败于 `logs == []`，接入成员审计后转绿；销售审批流程配置创建/更新红测先失败于 `logs == []`，接入 `APPROVAL_WORKFLOW` 审计后转绿；报价模板生命周期红测先失败于 `sqlalchemy.exc.NoResultFound`（模板/版本日志为空），接入 `QUOTE_TEMPLATE` 与 `QUOTE_TEMPLATE_VERSION` 审计后转绿；销售数据审核红测先失败于 `AttributeError: 'str' object has no attribute 'name'`，修正部门兼容后再失败于 `logs == []`，接入审核动作审计后转绿；合同模板生命周期红测先失败于 `AttributeError: 'ContractTemplateCreate' object has no attribute 'owner_id'`，修复 owner 归属后接入 `CONTRACT_TEMPLATE` 与 `CONTRACT_TEMPLATE_VERSION` 审计并转绿；CPQ 规则集红测先失败于 `AttributeError: 'CpqRuleSetCreate' object has no attribute 'status'`，修复默认状态后接入 `CPQ_RULE_SET` 审计并转绿；结构化报价模板生命周期红测先失败于 `AttributeError: 'QuoteTemplateCreate' object has no attribute 'owner_id'`，修复 owner 归属后接入 `QUOTE_TEMPLATE` 与 `QUOTE_TEMPLATE_VERSION` 审计并转绿；报价成本模板 CRUD 红测先失败于 `logs == []`，接入 `QUOTE_COST_TEMPLATE` 审计并转绿；采购物料成本 CRUD 红测先失败于 `logs == []`，接入 `PURCHASE_MATERIAL_COST` 审计并转绿；报价成本明细更新红测先失败于 `sqlalchemy.exc.NoResultFound`，接入 `QUOTE_VERSION` 审计并转绿；报价成本重算红测先失败于 `sqlalchemy.exc.NoResultFound`，接入 `QUOTE_VERSION` 审计后又暴露 `cost_total` 快照 4 位小数，量化汇总金额后转绿；报价成本匹配建议应用红测先失败于 `sqlalchemy.exc.NoResultFound`，接入 `QUOTE_VERSION` 审计后同样暴露汇总金额 4 位小数和 items 未进 changed_fields，补齐 old items 快照并量化金额后转绿；报价成本批量调价红测先失败于 `sqlalchemy.exc.NoResultFound`，接入 `QUOTE_VERSION` 审计后转绿；物料成本提醒配置/确认红测覆盖旧入口日志为空风险，接入 `MATERIAL_COST_REMINDER` 审计后转绿；物料成本匹配命中红测覆盖旧入口静默更新使用次数风险，接入 `PURCHASE_MATERIAL_COST` 审计后转绿；团队 PK 红测先失败于 `logs == []`，接入 `TEAM_PK` 审计后转绿；回款争议红测先失败于 `sqlalchemy.exc.NoResultFound`，接入 `RECEIVABLE_DISPUTE` 审计后转绿；售前费用化红测先失败于 `sqlalchemy.exc.NoResultFound`，接入 `PRESALE_EXPENSE` 审计后转绿；毛利率预警配置红测先失败于 `logs == []`，接入 `MARGIN_ALERT_CONFIG` 审计后转绿；评分规则创建/激活红测先失败于 `logs == []`，接入 `SCORING_RULE` 审计后转绿；旧激活评分规则停用红测先失败于 `len(logs) == 1`，补入旧规则停用日志后转绿；失败案例创建/更新红测先失败于 `logs == []`，接入 `FAILURE_CASE` 审计后转绿；线索/商机优先级计算红测先失败于 `NoResultFound`，接入来源实体 `UPDATE` 审计后转绿；技术评估申请红测先失败于 `NoResultFound`，接入来源实体申请日志后转绿；技术评估执行红测先失败于 `len(lead_logs) == 1`，接入来源实体完成日志后转绿；合同变更红测先失败于 `ContractAmendmentCreate.title` 缺失，兼容当前 schema 后接入 `CONTRACT/UPDATE` 审计并转绿。
  - 发票审批 workflow 红测先失败于 `sqlalchemy.exc.NoResultFound`（start/approve/reject 日志为空），接入 workflow 审计后 3 条转绿。
  - `tests/unit/test_sales_operation_audit_perm07.py` exit 0（98 passed）。
  - 补充：后续 pytest collect 曾失败于 `tests.factories` 强制导入已移除的旧 `ApprovalWorkflow/ApprovalWorkflowStep`；将旧工作流 factory 改为可选后，`tests/unit/test_sales_operation_audit_perm07.py` 恢复并继续扩展至 98 passed，团队 PK/操作日志相邻回归恢复 24 passed。
  - 销售团队相邻回归 `tests/unit/test_sales_team_deep.py tests/unit/test_sales_target_actuals.py tests/unit/test_sales_operation_audit_perm07.py::test_sales_team_crud_writes_team_operation_logs tests/unit/test_sales_operation_audit_perm07.py::test_sales_team_member_changes_write_team_operation_logs tests/unit/test_sales_operation_audit_perm07.py::test_sales_team_member_batch_add_writes_team_operation_log` exit 0（8 passed）；需求冻结/详情聚焦回归 2 passed；销售活动聚焦回归 4 passed；客户标签聚焦回归 4 passed；联系人聚焦回归 5 passed。
  - 销售审批流程邻域回归 `tests/integration/test_workflow_integration.py::TestApprovalWorkflowIntegration tests/unit/services/sales/test_operation_log_service.py tests/unit/test_operation_log_service_coverage.py tests/unit/test_sales_operation_audit_perm07.py::test_sales_approval_workflow_create_update_writes_operation_logs` exit 0（24 passed）。
  - 报价模板邻域回归 `tests/api/test_batch14_route_contracts.py::test_legacy_sales_quote_templates_route_uses_current_template_model tests/api/test_sales_quotes_api.py::TestSalesQuotesAPI::test_create_quote_from_template_static_route tests/unit/services/sales/test_operation_log_service.py tests/unit/test_operation_log_service_coverage.py` exit 0（21 passed）。
  - 销售数据审核邻域回归 `tests/unit/services/sales/test_data_audit_service.py tests/unit/test_data_audit_service_coverage.py` exit 0（22 passed）。
  - 最终组合回归 `.venv/bin/pytest tests/unit/test_sales_operation_audit_perm07.py tests/unit/services/sales/test_data_audit_service.py tests/unit/test_data_audit_service_coverage.py tests/unit/test_quote_approval_service.py tests/unit/test_quote_approval_service_coverage.py tests/unit/services/sales/test_operation_log_service.py tests/unit/test_operation_log_service_coverage.py tests/unit/test_contract_status_update_guard_peer01_02.py tests/unit/test_contract_project_delivery_date_appr14.py tests/api/test_batch14_route_contracts.py::test_legacy_sales_quote_templates_route_uses_current_template_model tests/api/test_sales_quotes_api.py::TestSalesQuotesAPI::test_create_quote_from_template_static_route tests/api/test_sales.py::TestLeadManagement tests/api/test_sales_customers_api.py tests/api/test_sales_opportunities_api.py tests/api/test_sales_opportunity_unit.py tests/api/test_sales.py::TestOpportunityManagement::test_update_opportunity_rejects_lost_to_won_transition tests/api/test_sales.py::TestOpportunityManagement::test_stage_endpoint_rejects_lost_to_won_transition tests/api/test_sales.py::TestOpportunityManagement::test_legacy_win_endpoint_rejects_lost_opportunity tests/api/test_sales.py::TestQuoteManagement::test_create_quote_success tests/api/test_sales.py::TestQuoteManagement::test_create_quote_version tests/api/test_sales.py::TestQuoteManagement::test_approve_quote tests/api/test_sales_quotes_api.py::TestSalesQuotesAPI::test_create_quote -q -rs` exit 0（7 skipped，跳过项均为既有未实现客户联系人/客户项目/商机 API 分支）。
  - 本轮补充：`pytest -q tests/unit/test_sales_operation_audit_perm07.py::test_invoice_approval_start_writes_invoice_submit_log tests/unit/test_sales_operation_audit_perm07.py::test_invoice_approval_action_writes_invoice_approve_log tests/unit/test_sales_operation_audit_perm07.py::test_invoice_approval_action_writes_invoice_reject_log` 通过；`ruff check app/api/v1/endpoints/sales/invoices/workflow.py tests/unit/test_sales_operation_audit_perm07.py` 通过。尝试跑 `tests/api/test_invoice_approval_workflow_contracts.py` 时卡在测试环境 `starlette.TestClient`/`httpx` 签名不兼容（`Client.__init__() got an unexpected keyword argument 'app'`），未进入业务断言。
  - `ruff check`、`.venv/bin/python -m py_compile` 通过。
- 备注：本轮曾试跑更宽的 `tests/integration/test_workflow_integration.py`，其中两个既有销售 pipeline 用例失败于 `contracts.contract_name` NOT NULL，和销售审批流审计接线无关；有效邻域已改为 `TestApprovalWorkflowIntegration` 子集。
- 补充校验：`git diff --check` 通过。
- 边界：本轮已覆盖报价明细、报价主表创建、报价基础信息更新、报价草稿删除、报价版本创建、报价交付日期更新、报价通用状态变更、报价直接审批兜底、报价正式审批提交/通过/驳回/批量通过/批量驳回/撤回、报价模板创建/更新/删除/版本创建/发布、结构化报价模板创建/更新/版本创建/版本发布、报价成本模板创建/更新/删除、采购物料成本创建/更新/删除、物料成本提醒配置/确认、物料成本匹配命中 usage 更新、报价成本明细更新、报价成本重算、报价成本匹配建议应用、报价成本批量调价、合同模板创建/更新/版本创建/版本发布、CPQ 规则集创建/更新、销售数据审核提交/通过/驳回/撤销、回款/核销、回款争议创建、售前费用化未中标项目、毛利率预警配置更新/软删除、发票 CRUD/开票/作废/审批 start/通过/驳回/委托/撤回 workflow、合同基础 CRUD、合同从报价生成/签署/归档、合同收款计划创建、客户 CRUD、客户标签新增/批量新增/删除、销售活动 quick 记录/AI 纪要确认/纪要回填商机、客户联系人 CRUD/设主联系人/主联系人自动降级、商机 CRUD、商机 PUT 阶段/赢单/输单、商机 POST 高频/兼容工作流、商机评分/阶段门、AI 方案评审落库/人工处置、商机批量路由注册、商机批量阶段/负责人/关闭、销售目标创建/更新、销售团队创建/更新/删除、销售团队成员新增/更新/移除/批量新增、团队 PK 创建/更新/完成、销售审批流程配置创建/更新、线索 CRUD、线索需求详情创建/更新、线索/商机需求冻结、线索/商机未决事项创建/更新/关闭、线索/商机 AI 澄清创建/答复更新、线索转商机、线索跟进、线索标无效、线索批量状态更新、线索批量转商机、线索批量分配负责人、评分规则创建/激活/旧激活规则停用、失败案例创建/更新、线索/商机优先级计算、线索/商机技术评估申请与执行、技术评估模板/评估项/风险/版本管理、合同变更记录创建七十八批高价值写入口；PERM-07 仍可继续扫更多销售写入口，因此台账保持 `修复中`，不标完成。

## 2026-07-05 继续：提升方案 P2 小项——ADMIN-17 文件上传内容校验

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 运维治理里的 `ADMIN-17`：统一文件上传服务存在，但主要只校验扩展名/大小；项目文档上传入口读取文件后直接保存，`.pdf` 可被 EXE/HTML 等内容伪装。
- TDD：
  - 红测 1：`FileUploadService.validate_file_content(b"%PDF-...", "quote.pdf")` 应通过；旧服务没有该方法。
  - 红测 2：`b"MZ..." + "quote.pdf"` 应被拒绝，并提示文件内容与扩展名不匹配；旧服务没有内容校验。
  - 红测 3：`.txt` 上传 HTML/script 内容应被拒绝。
  - 红测 4：`documents/crud_refactored.upload_document_file()` 对伪装 PDF 应在 `save_file()` 前抛 400；旧入口会继续保存。
- 代码面：
  - `FileUploadService.validate_file_content()` 增加内容签名校验：PDF、PNG/JPEG/GIF/BMP/WebP、ZIP/Office、legacy Office、RAR/7z/GZ 等常见格式按魔数匹配。
  - 全局拦截 Windows/Linux 可执行头、shebang 脚本；文本类扩展拒绝 HTML/script 内容。
  - 项目文档上传入口在扩展名和大小校验后、保存前调用内容校验。
  - 兼容旧调用 `FileUploadService(db)`：若第一个参数不是路径则视为 DB，并保留 `self.db`；`check_user_quota()` 可使用实例 DB，修复旧浅覆盖测试里的历史调用方式。
- 验证：`tests/unit/test_file_upload_service.py tests/unit/test_documents_upload_content_validation_admin17.py app/tests/services/file_upload/test_file_upload_service.py tests/unit/test_file_upload_deep.py tests/unit/test_file_upload_service_coverage.py tests/unit/test_zero_coverage_batch10_auto.py::TestFileUploadService` 95 passed；`ruff check`、`.venv/bin/python -m py_compile` 通过。
- 边界：本轮完成内容签名校验和项目文档上传入口接线；真正 AV/杀毒扫描需要外部扫描引擎或队列隔离，后续可在 `FileUploadService` 保存前/后扩展。

## 2026-07-05 继续：提升方案 P1 小项——ADMIN-16 导出水印接线

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 运维治理里的 `ADMIN-16`：`app/services/export/watermark_service.py` 存在但全仓导出链路零调用；同时原 PDF 水印固定用 Helvetica，中文水印容易渲染成黑方块。
- TDD：
  - 红测 1：合同 PDF 导出 `_build_contract_pdf_response()` 应把生成的 PDF bytes 交给 `add_watermark_to_pdf()`，并带上当前用户姓名；旧代码直接 `create_pdf_response(raw_pdf)`。
  - 红测 2：发票 PDF 导出 `export_invoice_pdf()` 同样应调用水印服务；旧代码未调用。
  - 红测 3：中文水印文本应选择 `STSong-Light` CID 字体，英文保留 `Helvetica`；旧 `WatermarkService` 没有字体选择入口。
  - 红测 4：项目依赖实际安装的是 `PyPDF2`，旧水印服务只 import `pypdf`，导致 `PYPDF_AVAILABLE=False`、真实水印合并不可用。
- 代码面：
  - `sales/contracts/export.py` 与 `sales/invoices/export.py` 在 PDF 生成后调用 `add_watermark_to_pdf(..., operator_name=当前用户姓名, custom_text="内部资料")`，再返回 watermarked `BytesIO`。
  - `watermark_service.py` 增加 `get_pdf_font_name()`：非 ASCII 文本注册并使用 `STSong-Light`，避免中文水印黑方块；英文仍用 Helvetica。
  - PDF 合并依赖 now 优先 `pypdf`，没有则 fallback 到项目已有 `PyPDF2==3.0.1`。
- 验证：`tests/unit/test_sales_pdf_watermark_admin16.py tests/unit/test_watermark_service_coverage.py tests/unit/test_sales_scope_expansion.py` 27 passed；`ruff check`、`.venv/bin/python -m py_compile`、`git diff --check` 通过；真实小 PDF 冒烟验证 `raw_len=1408/out_len=5704/changed=True/font=STSong-Light`。
- 边界：本轮先接销售合同/发票 PDF 两条真实导出链路；其它报表/Excel 导出仍可后续复用同一水印服务继续接线。

## 2026-07-05 继续：提升方案 P2 小项——ADMIN-19 文档附件生命周期

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 运维治理里的 `ADMIN-19`：`DELETE /documents/{doc_id}` 只删除 `project_documents` 记录，不删除实际上传文件，历史 `uploads/documents` 下形成大量孤儿附件。
- TDD：
  - 红测 1：临时上传目录内有 `projects/quote.pdf`，`ProjectDocument.file_path="projects/quote.pdf"`；旧 `delete_document()` 返回 200 但文件仍存在。
  - 红测 2：扫描上传目录时，DB 已引用 `project-a/kept.pdf`、目录里另有 `project-a/orphan.pdf`；旧代码没有扫描服务，测试 import 失败。
  - 红测 3：`delete=True` 清理时只删除未引用文件，保留 DB 已引用文件。
- 代码面：
  - `documents/operations.py` 删除文档记录后调用安全文件删除：相对路径按 `DOCUMENT_UPLOAD_DIR` 解析，只允许删除上传目录内文件，越界/不存在不阻断 DB 删除。
  - 新增 `app/services/document_file_lifecycle.py`，提供 `scan_project_document_orphans(db, upload_dir, delete=False)`，默认 dry-run，返回 scanned/referenced/orphan/deleted 计数和路径列表。
  - 新增 `scripts/scan_project_document_orphans.py`，可用 `.venv/bin/python scripts/scan_project_document_orphans.py --upload-dir uploads/documents` dry-run；传 `--delete` 才真实删除。
- 验证：两组红测均红后绿；`tests/unit/test_document_delete_file_lifecycle_admin19.py tests/unit/test_project_document_orphan_cleanup_admin19.py tests/unit/test_documents_upload_misc06.py tests/unit/test_document_management_deep.py` 6 passed / 4 skipped（旧 deep 测试模块缺失原样 skip）；`ruff check`、`.venv/bin/python -m py_compile`、`git diff --check` 通过；脚本临时空目录 dry-run 通过。
- 真实 dry-run：`.venv/bin/python scripts/scan_project_document_orphans.py --upload-dir uploads/documents` 返回 `scanned_count=341`、`referenced_count=0`、`orphan_count=341`、`deleted_count=0`。本轮未执行真实 `--delete`，因为会删除本地文件，需要单独确认。

## 2026-07-05 继续：提升方案 P2 小项——PERM-04 账号锁定死代码清理

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 权限治理里的 `PERM-04`：`app/core/account_lockout.py` 是内存版账号锁定实现，全仓生产代码零调用；真实登录入口早已使用 `app.services.account_lockout_service.AccountLockoutService`，保留 core 版会让后续维护误以为存在第二套有效锁定链路。
- TDD：
  - 红测：新增 `tests/unit/test_account_lockout_entrypoint_perm04.py`，要求 `app/core/account_lockout.py` 不存在，且 `auth.py` 只导入 Service 版锁定入口；旧代码因 core 文件存在失败。
  - 绿测：删除 core 内存版实现后，契约测试通过，并确认登录入口仍导入 `app.services.account_lockout_service`。
- 代码面：
  - 删除 `app/core/account_lockout.py`。
  - 删除两份只覆盖死代码的旧测试：`tests/unit/core/test_account_lockout.py`、`tests/unit/test_core_account_lockout.py`。
  - 从 `tests/unit/test_auth_branches.py` 移除 core 内存版账号锁定分支测试，保留 JWT 与认证中间件分支测试。
- 验证：`tests/unit/test_account_lockout_entrypoint_perm04.py` 红后绿；`tests/services/test_account_lockout_service.py tests/unit/test_account_lockout_service_coverage.py tests/unit/test_account_lockout_entrypoint_perm04.py` 15 passed；`tests/unit/test_auth_branches.py` 29 passed；源码扫描无生产代码引用 `app.core.account_lockout`。
- 边界：`tests/integration/test_auth_lockout_integration.py` 当前因 Starlette `TestClient` 传 `app=` 给本机 httpx 后报 `Client.__init__() got an unexpected keyword argument 'app'`，未能用于本轮验收；这是测试依赖兼容问题，不是 PERM-04 改动路径。

## 2026-07-05 继续：提升方案 P2 小项——ADMIN-22 编码规则统一生成器

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 运维治理里的 `ADMIN-22`：业务支持订单、送货、开票申请、客户入驻、发票、对账编号各自手写“查最大号+1”，同一数据库快照下并发调用会返回重复编号。
- TDD：
  - 红测：固定日期、数据库查询无最新记录时，6 个并发调用 `generate_order_no()`；旧代码全部返回 `SO250115-001`，撞号。
  - 绿测：now 同场景返回 `SO250115-001` 到 `SO250115-006`，且保持既有首号、递增、无效格式兜底、`INV-250520-001` 格式等用例不变。
- 代码面：
  - 新增 `app/utils/business_code_generator.py`：统一生成 `SO250101-001`、`INV-250101-001` 等日期前缀编号。
  - 生成器在当前应用进程内按 `模型/字段/日期前缀` 加锁，并记录已预约的最大序号；并发请求即使看到同一 DB 最大号，也会拿到不同的下一个序号。
  - `BusinessSupportUtilsService` 的 6 个编码方法全部改为调用 `generate_business_code()`，不再各自复制查询和解析逻辑。
- 验证：`test_generate_order_no_reserves_unique_numbers_for_same_snapshot` 红后绿；`tests/unit/test_business_support_utils_service.py` 34 passed；`tests/unit/test_api_p6_coverage.py::TestBSOUtils` 10 passed；`ruff check`、`py_compile` 通过。
- 边界：本轮解决单应用进程内并发撞号；多 worker/多实例部署如果要做到全局强一致，后续应补 DB 序列表或唯一键冲突重试。

## 2026-07-05 继续：提升方案 P2 小项——ADMIN-10 调度器指标持久化与 /metrics 暴露

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 运维治理里的 `ADMIN-10`：调度器指标虽然有内存采集和鉴权后的 `/scheduler/metrics/prometheus`，但重启即清零，且根 `/metrics` 没输出 job 运行结果，Prometheus 默认抓不到任务成功/失败/耗时。
- TDD：
  - 红测 1：`SchedulerMetrics(persistence_path=...)` 记录成功、失败和通知后，新建另一个 `SchedulerMetrics` 应能从同一 JSON 文件恢复；旧代码不支持 `persistence_path` 参数。
  - 红测 2：先 `record_job_success("admin10_job", 42.0, ...)`，再抓根 `/metrics`，应包含 `pms_scheduler_job_success_total` 和 last duration；旧输出只有应用健康、依赖和 scheduler running/job_count。
- 代码面：
  - `app/utils/scheduler_metrics.py` 支持可选 `persistence_path`，记录成功/失败/通知和 reset 时原子写 JSON；初始化时可重载 job 计数、通知计数和 duration history。
  - 全局 `METRICS` 默认持久化到 `data/scheduler_metrics.json`，可通过 `SCHEDULER_METRICS_PATH` 覆盖；运行态文件已加入 `.gitignore`。
  - `app/main.py` 的根 `/metrics` 追加 `pms_scheduler_job_success_total/failure_total/last_duration_ms/duration_avg_ms/duration_p95_ms` 和 `pms_scheduler_notification_*` 指标，沿用 `/metrics` 白名单让 Prometheus 可直接抓。
- 验证：两个红测均先失败后变绿；相邻回归 `tests/unit/test_scheduler_metrics_utils.py tests/unit/test_prometheus_metrics_admin08.py` 共 18 passed；`ruff check`、`py_compile` 通过。
- 边界：当前持久化是本机 JSON 文件，解决单实例重启清零；多实例聚合、Prometheus 长期时序和告警规则仍由 Prometheus/Grafana 侧负责。

## 2026-07-05 继续：提升方案 P2 小项——ADMIN-11 项目缓存内存降级可命中

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 运维治理里的 `ADMIN-11`：项目列表端点每次请求都会新建 `CacheService()`；旧 `CacheService.memory_cache` 是实例字段，Redis 不可用时 A 请求写入、B 请求读取必 miss，所谓内存缓存实际零命中。
- TDD：
  - 红测：在 `REDIS_AVAILABLE=False` 下，实例 A `set_project_list()` 后，实例 B 用相同 page/page_size/is_active 调 `get_project_list()`；旧代码返回 `None`。
  - 绿测：now 实例 B 能读到实例 A 写入的项目列表缓存，且 reader 统计 `hits == 1`。
- 代码面：
  - `app/services/cache_service.py` 把内存降级缓存从每实例 `self.memory_cache = {}` 改为进程级 `_shared_memory_cache`。
  - 每个 `CacheService` 仍保留自己的 `stats`，避免不同调用方的命中/失败统计互相污染。
  - `clear()`、`delete_pattern()`、项目缓存失效方法继续作用于同一共享内存缓存，因此 ADMIN-12 已修的项目缓存清理端点也能清掉内存降级缓存。
- 验证：`test_memory_project_list_cache_survives_new_service_instance` 红后绿；缓存服务和项目缓存清理相邻回归 `tests/unit/test_cache_service.py tests/unit/test_projects_cache_admin12.py` 共 36 passed / 1 skipped（Redis 服务测试原样 skip）；`ruff check`、`py_compile` 通过。
- 边界：这是单进程内存降级缓存修复；多 worker/多机器一致性仍依赖 Redis，不把内存缓存冒充分布式缓存。

## 2026-07-05 继续：提升方案 P2 小项——ADMIN-20 日志文件输出与轮转

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 运维治理里的 `ADMIN-20`：应用日志只有 stdout，`logs/` 为空；服务重启或容器外采集缺失时，故障后几乎没有本机取证材料。
- TDD：
  - 红测：设置临时 `APP_LOG_DIR`、`APP_LOG_FILE`、`APP_LOG_MAX_BYTES`、`APP_LOG_BACKUP_COUNT` 后调用 `setup_logging()`，旧代码 root logger 没有 `RotatingFileHandler`，日志文件不存在。
  - 绿测：now root logger 同时有 stdout 和 `RotatingFileHandler`，写入 warning 后 `app.log` 存在且包含日志内容，轮转大小与保留份数按环境变量生效。
- 代码面：
  - `app/core/logging_config.py` 新增默认日志目录 `logs/`、默认文件 `app.log`、默认 10MB 轮转、默认保留 7 份。
  - 文件 handler 复用现有格式、日志级别、`SensitiveDataFilter` 与 `ProductionSensitiveFilter`，避免文件日志绕过脱敏/生产过滤。
  - 支持 `APP_LOG_DIR`、`APP_LOG_FILE`、`APP_LOG_MAX_BYTES`、`APP_LOG_BACKUP_COUNT` 四个环境变量覆盖。
- 验证：`tests/unit/test_logging_file_rotation_admin20.py` 红后绿 1 passed；稳定相邻日志配置回归 `tests/unit/test_logging_file_rotation_admin20.py app/tests/services/core/test_logging_config.py` 共 14 passed；`ruff check`、`py_compile` 通过；`setup_logging()+get_logger()` 导入写日志验证通过。
- 边界：`tests/unit/test_logger.py` 和 `tests/unit/test_core_modules_deep_auto.py` 文件级回归仍有既有失败（前者测试缩进导致 `NameError`，后者 CRUD 构造签名旧假设），本轮未顺手改无关旧测试。

## 2026-07-05 继续：提升方案 P2 小项——PERM-22 前端路由权限守卫

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 里的 `PERM-22`：system/hr/finance 多个前端页面只有菜单层权限，直接输入路由可绕过前端守卫进入页面；401/mock 回落会进一步掩盖越权体验。
- TDD：
  - 红测 1：无 `system:template:manage` 时访问 `/system/template-center`，旧代码直接渲染模板中心，期望显示路由无权限。
  - 红测 2：无绩效权限时访问 `/hr/performance-center`，旧代码直接渲染绩效中心，期望显示路由无权限。
  - 红测 3：无 `cost:accounting:read` 时访问 `/finance/cost-center`，旧代码直接渲染成本中心，期望显示路由无权限。
- 代码面：
  - `systemRoutes.jsx`、`hrRoutes.jsx`、`financeRoutes.jsx` 接入 `ModuleProtectedRoute`，把管理类页面和既有菜单权限口径对齐。
  - 支持任一权限即可进入的组合路由，例如账号权限中心 `USER_VIEW/ROLE_VIEW`、组织中心 `system:org:manage/system:position:manage`、绩效中心 `performance:manage/evaluation:config:manage`。
  - 保留个人自助页 `/personal/monthly-summary`、`/personal/my-performance`、`/personal/my-bonus` 不挂 HR 管理权限，避免员工自查被误拦。
- 验证：`permissionProtectedRoutes.test.jsx` 红后绿 4 passed；前端权限/布局相邻回归 93 passed；4 个变更文件 ESLint 通过；`npm run build` 通过（仅既有 Vite 分包/大 chunk 提醒、Node `module.register()` 弃用提醒）。
- 边界：本轮是前端直链守卫补齐，不替代后端 `require_permission`；按钮级零散操作仍需随 PERM-11/页面专项继续收口。

## 2026-07-04 继续：提升方案 P2 小项——HR-05 员工部门主链路 ID 化

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 数据治理里的 `HR-05`：`Employee` 只有 `department` 字符串，组织部门端点按部门名统计/拦截/查用户；组织变更后 ID 正确但旧字符串滞后时，会漏拦部门删除、部门用户列表漏人。
- TDD：
  - 红测 1：员工 `department_id=新部门ID`、`department=旧部门名` 且在职时，删除新部门旧代码返回 200 停用，期望 400 拦截“存在在职员工”。
  - 红测 2：用户 `department_id=新部门ID`、`department=旧部门名` 时，`GET /org/departments/{id}/users` 旧代码返回空，期望按 ID 查到该用户。
- 代码面：
  - `Employee` 增加 `department_id` 外键、索引和 `department_ref` 关系；`EmployeeCreate/Update/Response` 增加 `department_id`。
  - 员工创建/更新传入 `department_id` 时校验部门存在，并同步旧 `department` 字符串为当前 `dept_name`，减少新增脏数据。
  - 部门统计、部门删除保护、部门用户列表统一为：优先 `department_id == dept.id`；旧字符串仅在 `department_id IS NULL` 时按 `department == dept_name` 回退。
  - 新增 SQLite 迁移 `migrations/20260704_employee_department_id_sqlite.sql`，精确部门名匹配时回填 `employees.department_id`；启动补丁也会为旧 SQLite 补列。
- 验证：`tests/api/test_org_department_id_hr05.py` 红后绿 2 passed；组织相邻回归 24 passed（2 个既有 skip）；`ruff check`、`py_compile`、`git diff --check` 通过。
- 边界：本轮完成 Employee/User 与组织部门端点的主链路 ID 化；复杂同义词、重复部门名、历史 `Employee.department` 全量人工清洗不在这个小步内自动猜测处理。

## 2026-07-04 继续：提升方案 P1 小项——HR-03 部门数据权限按 ID 随组织变动

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P1 里的 `HR-03`：通用数据权限 DEPT 分支用 `user.department` 部门名字符串反查部门 ID；用户调岗后如果旧字符串没同步，仍会按旧部门过滤，导致看不到新部门数据或继续看到旧部门数据。
- TDD：
  - 红测：当前用户 `department_id=20` 但 `department="旧部门"`，旧部门名反查到部门 ID 99；`dept_field="department_id"` 时旧代码生成 `users.department_id = 99`。
  - 绿测：同场景 now 生成 `users.department_id = 20`，且不会再查询旧部门名。
- 代码面：
  - `GenericFilterService` 新增部门 ID 解析：优先读取 `user.department_id/dept_id/owner_dept_id`，仅在没有 ID 时回退 `Department.dept_name == user.department`。
  - 直接部门字段为 `department_id/dept_id/*_department_id/*_dept_id` 时按 ID 过滤；旧字符串部门字段则可按 ID 反查当前部门名后兼容过滤。
  - 通过项目间接做 DEPT 过滤时也改为用解析后的部门 ID 查 `Project.dept_id`，避免项目域继续被旧部门名带偏。
- 验证：`test_dept_scope_prefers_department_id_over_legacy_name` 红后绿；数据权限核心回归 30 passed；PERM-17 工时/预算财务/采购/BOM/ECN/仓储库存相关回归 31 passed；`ruff check`、`py_compile`、`git diff --check` 通过。
- 边界：本轮只修通用过滤行为和保留旧字段回退；存量 `Employee.department` 等历史字符串字段清洗仍归 HR-05/组织数据治理后续处理。

## 2026-07-04 继续：提升方案 P2 小项——HR-23 资源冲突检测落库

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 多轨收敛里的 `HR-23`：`resource_conflicts` 真表和冲突调解算法存在，但项目级 `/resource-conflicts/check` 只在同一项目内部临时返回冲突，跨项目同人超额分配不会被发现，也不会落库，调解建议长期架在空表上。
- TDD：
  - 红测：同一员工在项目 A 70%、项目 B 60%，日期 2026-07-10~2026-07-20 重叠；调用项目 A 的冲突检查，旧代码返回 `has_conflicts=false` 且 `ResourceConflict` 空表。
- 代码面：
  - `analytics/resource_conflicts.py` 的项目检查 now 扫描目标项目资源计划与全局同员工已分配计划的重叠，计算总分配、超额分配和严重度，并幂等 upsert `resource_conflicts`。
  - 重复调用不会重复插入同一组未解决冲突；已有冲突会更新重叠期/分配比例/严重度。
  - `ConflictMediationService` 补齐 `identify_conflicts/resolve_conflict/escalate_conflict/get_conflict_history` 服务层直调入口；推荐生成增加防御，半成品冲突数据不会拖垮整个建议响应。
- 验证：`tests/unit/test_resource_conflict_persistence_hr23.py` 1 passed；冲突调解/资源冲突/路由契约回归 54 passed；`ruff check`、`py_compile`、`git diff --check` 通过。
- 边界：本轮先打通“检测 -> 落库 -> 调解可读”的主链路；更复杂的多冲突合并、自动派单和 AS-24/MISC-02 双轨收敛后续可继续做。

## 2026-07-04 继续：提升方案 P2 小项——HR-14 月度绩效结果并入正式 PerformanceResult

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 多轨收敛里的 `HR-14`：员工/经理月度绩效体系使用 `MonthlyWorkSummary` + `PerformanceEvaluationRecord` 临时算分，工程师/个人绩效/奖金链路读取 `PerformanceResult`，三套绩效结果互相割裂，谁是正式绩效说不清。
- TDD：
  - 红测：部门经理评分 90、项目经理评分 80，权重 60/40；项目经理提交最后一条评价后，旧代码只把 `MonthlyWorkSummary` 置 `COMPLETED`，不会创建 `MONTHLY-2026-07` 周期，也不会写 `PerformanceResult`。
- 代码面：
  - 新增 `PerformanceService.sync_monthly_summary_result(db, summary)`：月度总结完成后，根据 `calculate_final_score()` 的结果创建/复用 `PerformancePeriod(period_code="MONTHLY-YYYY-MM")`，并 upsert `PerformanceResult`。
  - `ManagerPerformanceService.submit_evaluation()` 在所有评价完成时先 `flush()` 当前评价，再同步正式结果，解决 `SessionLocal(autoflush=False)` 下计算看不到本次评价的问题。
  - 正式结果写入员工姓名、部门、总分、等级和 `indicator_scores`（monthly_final_score / dept_score / project_score / 权重），供个人绩效、排名、奖金等下游统一读取。
- 验证：`tests/unit/test_performance_unification_hr14.py` 1 passed；相邻回归 `test_manager_performance_service.py`、`test_employee_performance_service.py`、`test_performance_service.py` 与 API 路由契约合计 134 passed；`ruff check`、`py_compile`、`git diff --check` 通过。
- 边界：本轮先合上“结果表割裂”这个最大断点；服务层重复代码的深度合并不在本小步内继续扩大战线。

## 2026-07-04 继续：提升方案 P1/P2 小项——HR-11/12 绩效采集器接入算分器

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 多轨收敛里的 `HR-11/12`：工程师五维绩效存在采集器 `PerformanceDataAggregator`，但主算分器没有消费它，导致技术/执行/质量/知识多处靠默认或硬编码，特别是执行分 80、成本质量分 75 对多岗位恒定。
- TDD：
  - 红测：用假的采集器返回机械岗低设计一次通过率、2 个调试问题、任务完成率 40%、准时率 50%、BOM 及时率 50%、标准件率 60%、ECN 责任率 20%、知识贡献 2 条；旧代码仍算出默认技术分 100/执行 80/质量 75/知识 50，测试失败。
- 代码面：
  - `PerformanceCalculator` now 调 `PerformanceDataAggregator.collect_all_data()`；失败或无数据时保留旧兜底，避免空数据把历史结果打穿。
  - 机械岗技术分 now 优先用采集器的 `design_review.first_pass_rate` 与 `debug_issue.mechanical_issues`，知识分优先用 `knowledge_contribution.total_contributions`。
  - 执行分 now 优先按 `task_completion` 计算：`completion_rate*0.6 + on_time_rate*0.4`；机械/测试/电气共用。
  - 成本质量分 now 优先按 `bom_data` 与 `ecn_responsibility` 计算：BOM 及时率、标准件率、复用率（有值才用）和 `100-ECN责任率` 的平均；机械/测试/电气/方案共用。
- 验证：`tests/unit/test_performance_collector_integration_hr11_12.py` 1 passed；相邻绩效计算/HR-10 回归 35 passed；采集器回归 21 passed；`ruff check`、`py_compile`、`git diff --check` 通过；旧的直接硬编码返回 80/75 扫描无命中。
- 边界：本轮接通正式算分器与现有采集器，并保留无数据兜底；HR-14 的“三套绩效服务合一”仍是后续结构收敛项。

## 2026-07-04 继续：提升方案 P2 小项——HR-13 绩效申诉闭环

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 多轨收敛里的 `HR-13`：`PerformanceAppeal` 模型已存在，但绩效申诉没有 API 写入口、没有查询入口，也无法把申诉处理结果写回 `performance_result` 与调整历史。
- TDD：
  - 红测 1：提交本人绩效申诉应落 `performance_appeal`，状态为 `PENDING`，并把对应绩效结果标记为 `APPEALING`；旧代码模块不存在。
  - 红测 2：申诉列表普通员工只能看到自己的申诉，管理员可按绩效结果过滤查看。
  - 红测 3：处理申诉为 `ACCEPTED` 时，应更新处理人/处理时间/调整后分数与等级，并写入 `PerformanceAdjustmentHistory`。
  - 红测 4：`performance` 聚合路由必须注册 `/performance/appeals` 与 `/performance/appeals/{appeal_id}/handle`。
- 代码面：
  - 新增 `app/api/v1/endpoints/performance/appeals.py`：提交、列表、处理三类端点；本人可提交自己的结果申诉，管理员/HR 类角色可处理。
  - 接受申诉时同步更新 `PerformanceResult.total_score/adjusted_total_score/level/is_adjusted/status`，并写调整历史；拒绝/关闭也会回写结果状态。
  - `app/api/v1/endpoints/performance/__init__.py` 注册申诉路由，纳入现有绩效 API 聚合。
- 验证：`tests/unit/test_performance_appeals_hr13.py` 4 passed；相邻回归 `test_engineer_performance_result_persistence_hr10.py`、`test_manager_evaluation_service.py` 合计 20 passed；API 路由契约 36 passed；`ruff check`、`py_compile`、`git diff --check` 通过。
- 边界：本轮先把申诉写入/处理/调整历史闭环做实；若后续要接统一审批引擎，可在当前处理端点前增加审批任务流转，不再需要重建申诉数据模型。

## 2026-07-04 继续：提升方案 P2 小项——HR-20 时薪旁路清理

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 多轨收敛里的 `HR-20`：统一时薪配置服务已存在，但旧模板成本分析、售前资源浪费/投入看板、人工成本 by-engineer、未中标投入分析等入口仍按固定 100/200/300 估算人工成本，且部分入口把未审批工时也计入成本。
- TDD：
  - 红测 1：旧 `template_report` 成本分析对 2h×150 + 3h×80 + 10h SUBMITTED 算成 1500，期望只算已审批配置费率 540。
  - 红测 2：`ResourceWasteAnalysisService.calculate_waste_by_period()` 把未审批工时计入 19h，期望仅已审批 9h、浪费 5h、浪费成本 540。
  - 红测 3：`labor_cost_by_engineer()` 仍按 200 元/小时，期望通过 WorkOrder→Worker→User 走配置费率 175。
  - 红测 4/5：`LossDeepAnalysisService` 与 `LaborCostExpenseService` 缺失用户时仍按 300 兜底，期望统一走 `HourlyRateService` 的可追踪兜底 100。
- 代码面：
  - `report_labor_cost.py` 增加 `TimesheetLaborCostSummary`，统一按 `Timesheet.user_id + work_date` 读取 `HourlyRateService`，并提供加权平均时薪。
  - 旧 `template_report` 成本分析、售前资源投入/浪费 API、售前 dashboard adapter、resource_waste_analysis 服务均改为只读 `APPROVED` 工时并按配置费率逐条计算。
  - `labor_cost_detail.by-engineer` 从 raw SQL 固定 200 改为 WorkOrder→Worker→User 聚合；有绑定用户走 `HourlyRateService`，无绑定用户才使用 worker 自身显式费率或统一兜底。
  - resource_waste_analysis 默认不再持有 300 元/小时；显式传 `hourly_rate` 仍作为兼容覆盖，默认路径走统一配置。
  - `loss_deep_analysis_service` 与 `LaborCostExpenseService` 缺失用户分支不再硬编码 300，改由 `HourlyRateService` 返回来源可追踪的兜底。
- 验证：`tests/unit/test_hourly_rate_consumers_hr20.py` 5 passed；相邻回归（RPT-03、resource_waste、dashboard、loss_deep、labor_cost）91 passed / 2 skipped；`ruff check`、`py_compile`、`git diff --check` 通过；源码扫描未再发现 HR-20 相关的固定时薪 200/300 旁路。

## 2026-07-04 继续：提升方案 P2 小项——HR-19 奖金系数规则化

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P2 多轨收敛里的 `HR-19`：绩效等级系数、售前紧急/满意度系数原先写死在代码里，调整系数必须改代码。
- TDD：
  - 红测 1：`test_performance_bonus_uses_rule_level_coefficients`，规则 JSON 配 `performance_coefficients: {"A": "2.5"}` 时，旧代码仍按 A=1.2 计算 1200。
  - 红测 2：`test_presale_completion_bonus_uses_rule_coefficients`，规则 JSON 配 `VERY_URGENT=2.0`、满意度 5 分=1.5 时，旧代码仍按 1.3*1.2 计算 156。
- 代码面：
  - `BonusCalculatorBase.get_coefficient_by_level(level, bonus_rule)` 支持从 `BonusRule.trigger_condition.performance_coefficients` 读取绩效等级系数；未配置时保留旧默认。
  - `PresaleBonusCalculator` 支持从 `trigger_condition.urgency_coefficients` / `satisfaction_coefficients` 读取售前系数；未配置时保留旧默认。
  - 角色系数原已支持 `trigger_condition.role_coefficients`，本轮补齐绩效等级和售前系数两块。
- 验证：`tests/unit/test_bonus_rule_coefficients_hr19.py` 2 passed；相邻回归 `tests/unit/test_performance_bonus_chain_hr16.py`、`tests/unit/test_presale_bonus.py`、`tests/unit/test_bonus_presale.py` 合计 21 passed；`ruff check` 与 `py_compile` 通过。

## 2026-07-04 继续：提升方案 P1 小项——HR-15 绩效合同裸 sqlite3 改 ORM

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P1 数据治理里的 `HR-15`：`app/api/v1/endpoints/performance/contract.py` 原先 import 期执行 `init_tables()`，并通过裸 `sqlite3.connect(DB_PATH)` 直连业务库；在测试 `:memory:` 下会创建/查询不同连接，实际 CRUD 可 500。
- TDD：
  - 红测 1：`test_performance_contract_module_does_not_open_sqlite_on_import`，旧代码 import 模块即调用 `sqlite3.connect` 建表。
  - 红测 2：`test_create_contract_uses_injected_session`，旧代码忽略注入 `db_session`，新建合约因 `performance_contracts` 不在同一内存库而 500。
  - 回归覆盖：`test_contract_items_submit_and_sign_use_injected_session` 覆盖条目权重、提交、签署主流程。
- 代码面：
  - 新增 `app/models/performance/contract.py`：`PerformanceContract` / `PerformanceContractItem` ORM 模型，并注册到 `app.models.performance` / `app.models`。
  - 重写 `performance/contract.py` 为 SQLAlchemy Session 实现，去掉裸 `sqlite3`、`get_db_connection`、`init_tables`；所有 CRUD/条目/提交/签署/评分都走注入的 `db`。
- 验证：`tests/unit/test_performance_contract_import.py` 4 passed；生产文件 `rg "sqlite3|sqlite3\\.connect|get_db_connection|init_tables"` 无命中；`ruff check`、`py_compile` 通过。

## 2026-07-04 继续：提升方案 P1 小项——SALES-06 预测目标接 sales_targets 真数据

- 修复项：`SYSTEM_IMPROVEMENT_PLAN` P1 数据治理里的 `SALES-06 残项`：`SalesForecastService._get_sales_target` 原先写死年度目标 2 亿，导致销售预测目标不随目标管理页配置变化。
- TDD：
  - 红测 1：`test_sales_target_uses_company_yearly_target_from_sales_targets`，真实 `sales_targets` 年度公司合同额目标为 12,345,678.90 时，旧代码仍返回 200,000,000。
  - 红测 2：`test_sales_target_sums_quarterly_scope_targets_when_company_target_missing`，无公司级目标时，个人/团队同季度有效合同额目标应汇总；旧代码返回默认季度拆分 55,000,000。
- 代码面：`sales_forecast_service.py` 先查 ACTIVE 的 COMPANY/CONTRACT_AMOUNT 周期目标；没有公司级目标时汇总同周期 ACTIVE 的非公司合同额目标；仍无配置才保留原默认值作为兜底。
- 验证：`tests/unit/test_sales_forecast_service.py` 3 passed；相关回归 `tests/unit/test_sales_forecast_wiring.py`、`tests/unit/test_sales_forecast_deep.py`、`tests/unit/test_sales_target_actuals.py`、`tests/services/test_sales_team_aggregation_contracts.py` 合计 11 passed；`ruff check` 与 `py_compile` 通过。
- 备注：`tests/audit_p0/test_p0_15_forecast_hardcoded.py` 在 API fixture 启动/退出阶段仍会 timeout；服务级与目标聚合口径已验证，本项未改 API 路由。

## 2026-07-04 继续：TEN-06 修复（租户 fail-closed 地基）——多租户已拍板启动

- **业务决策**：多租户确定要做，租户管理入口放超级管理员设置（TEN-01 管理 API 已由并行会话补好）。台账最短路径：TEN-06（本条）→ TEN-02 查询层（等 models/base.py 释放）→ TEN-03 按域加列（先 Project 域）。
- 代码面：
  - `tenant_middleware.py` 新增 `evaluate_tenant_access` 决策函数 + `get_enforce_mode`：超管跨租户放行（tenant_id 允许 NULL）、有租户放行、未认证由前置白名单管；无租户的非超管按 `TENANT_ENFORCE_MODE` 处理——默认 `log`（放行+告警，灰度观测），`strict` 即 fail-closed 403（TENANT_REQUIRED，提示联系超管分配租户）。
  - 归户迁移 `20260704_tenant_user_backfill_sqlite.sql`（已应用 data/app.db）：非超管 NULL → 默认 active 租户（id=1 金凯博）；超管保留 NULL。归户后 195 用户仅剩 2 超管 NULL。
- 验证：红灯 7 项 → 绿灯 `tests/unit/test_tenant_fail_closed.py` 7 passed（含 strict 环境变量下复跑）；带认证流回归 14 passed；`import app.main` 通过。
- **切换 strict 的前提清单**：①各环境跑归户迁移；②灰度期观察 no-tenant 告警日志归零；③测试环境 TENANT_ENFORCE_MODE=strict 全量回归。切换后新用户创建必须带 tenant_id（超管租户控制台负责）。
- 后续（多租户 Batch 计划）：TEN-02 with_loader_criteria 全局过滤 → TEN-03 Project 域加列灰度 → 销售/采购/财务域 → TEN-07 配额/生命周期执行。

## 2026-07-04 继续：提升方案 P4 先行——质量门禁三件套进 CI（棘轮机制）

- 背景：SYSTEM_IMPROVEMENT_PLAN（本地文档，*_PLAN.md 被 gitignore）第 1 周动作：把两天来靠自觉的治理纪律变成机器强制。全部纯新增文件+hooks 软提醒，与并行会话在途大扫荡零碰撞。
- 三个守卫（`scripts/ci_guard_*.py`，纯 stdlib，`--update-baseline` 收紧棘轮）：
  - **权限覆盖率棘轮**：复用 audit_permission_coverage 静态扫描；NONE 端点不得超基线、PERMISSION 占比不得回退。当前基线：2997 端点 / NONE 143 / PERMISSION 34.4%。
  - **幽灵表检测**：模型有 `__tablename__` 但全仓无构造/INSERT 写入 → 幽灵；只拦基线外新增。**摸底发现现存 109 张幽灵表**（P1 数据治理的完整靶单，含 ShortageDailyReport/resource_conflicts 等审计已知项）。
  - **AI mock 写库闸**：调 `.generate_solution(` 且 `db.add(` 的文件必须引用 `is_mock_response`；现存 5 处豁免登记在基线（P5 待治理清单）。
- `.github/workflows/guard-quality-gates.yml`：PR + main push 触发三守卫（沿用 guard-stub-defaults 模式，零依赖）。
- `hooks/commit-msg`：新增软提醒（不拦截）——fix 提交未引用审计 ID 时提示补充，配合台账"修复 PR 必引 ID"规则。
- 验证：三守卫本地全绿；hook 两条路径（无 ID 提醒/有 ID 通过）实测正常。
- 基线文件（scripts/*_baseline.json）随修复进展用 --update-baseline 收紧，形成只升不降的棘轮。

## 2026-07-04 继续：功能审计 ADMIN-07 修复（行政管理四件套做实）

- 修复项：`ADMIN-07`，admin_compat 整文件硬编码（A4 复印纸/固定车辆/写死费用统计），前端 adminApi 全部写操作 404。
- 代码面：
  - 新增 `models/admin_office.py` 六张真表：用品/用品申领/车辆/用车申请/资产/费用（已注册 models/__init__）；迁移 `20260704_admin_office_sqlite.sql` 已应用 data/app.db。
  - `admin_compat.py` 重写为真库实现，对齐前端 adminApi 既有调用面：
    - 用品：list/inventory/get + 申领单（PENDING）→ 审批扣库存（不足 400）/驳回不扣；
    - 车辆：list/available/get + 用车申请 → 审批置 IN_USE（可用列表自动排除）；
    - 资产：CRUD（编号自动生成）+ 按状态/分类真实统计；
    - 费用：列表 + 按周期（月/季/年）真实聚合；
    - 响应保留 camelCase 兼容键；/stats 仍委托 collect_admin_stats（ADMIN-05 范围不重复动）。
- 验证：红灯 6 项 → 绿灯 `tests/unit/test_admin_office_real.py` 6 passed；admin_stats 套件回归过；TestClient 动态验证路由挂载 401 权限门；`import app.main` 通过。
- 备注：`test_batch5_route_contracts` 的 /admin/stats 失败来自并行会话未提交的备份代码读 `/var/backups/pms`（HEAD 上通过），归其处理；会议室预定端点前端有封装但历史即缺，另行排期。

## 2026-07-04 继续：功能审计 HR-08 修复（考勤页请假/加班入口止损）

- 修复项：`HR-08`。考勤页展示“请假管理/加班管理”标签，但对应正式请假、加班、补卡域没有接入；页面等于给用户一个看似存在的功能入口。
- 红测：
  - 更新 `frontend/src/pages/__tests__/AttendanceManagement.test.jsx`，先要求页头只描述“员工考勤记录、统计分析”，并且页面不再出现“请假管理/加班管理”两个按钮。旧页面测试失败，证明假入口仍在。
- 代码面：
  - `AttendanceManagement.jsx` 移除未接入的“请假管理/加班管理”Tabs 和空壳内容。
  - 页头描述收敛为“员工考勤记录、统计分析”。
  - 部门统计里的“请假人数”字段保留为考勤统计字段，不再包装成请假管理工作流。
- 验证：
  - `npm --prefix frontend test -- --run src/pages/__tests__/AttendanceManagement.test.jsx` -> 5 passed。
  - `npm exec eslint src/pages/AttendanceManagement.jsx src/pages/__tests__/AttendanceManagement.test.jsx`（workdir=frontend）-> 通过。
  - `git diff --check` 相关文件通过。
- 边界：本轮是前端止损下架入口；完整请假/加班/补卡域仍需后续补模型、审批与排产输入。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `HR-08` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 HR-09 修复（节假日 DB 配置进入消费链）

- 修复项：`HR-09`。系统有 `Holiday/HolidayService` 和 DB 配置，但工作日志规则引擎实际调用 `holiday_utils.get_work_type()` 的硬编码静态日历，DB 中新增/调整的节假日不会进入工时类型判断。
- 红测：
  - 新增 `tests/unit/test_holiday_db_consumption_hr09.py`，在 DB 写入一个硬编码表没有的 `2031-07-04` 公司假期；旧规则引擎返回 `NORMAL`，证明 DB 配置未被消费。
- 代码面：
  - `holiday_utils.is_holiday/get_holiday_name/is_workday_adjustment/get_work_type` 增加可选 `db` 参数；传入 DB 时优先读取 `HolidayService`，无命中再回落静态中国节假日/调休日历。
  - `work_log_ai/rule_engine.py` 在实例有 `self.db` 时把 DB 传给 `get_work_type()`；没有 DB 的纯函数/旧测试路径保持原调用形态。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_holiday_db_consumption_hr09.py tests/unit/test_l3_holiday_utils.py tests/unit/test_holiday_model.py` -> 69 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_rule_engine.py` -> 19 passed。
  - `ruff check`、`py_compile`、`git diff --check` 相关文件通过。
- 边界：本轮打通 DB 配置消费链；静态国家节假日日历仍作为无 DB 场景兜底保留。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `HR-09` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 PROJ-23 修复（SAT 验收通过自动移交售后）

- 修复项：`PROJ-23`（详#18），验收域与售后域零联动——SAT 验收通过后质保、设备档案全靠售后人工重建。前置 AS-10（机台 SN/客户/质保字段）与 PROD-16 已由并行会话修复，本项接线正当其时。
- 代码面：`acceptance_service` 新增 `_handover_to_after_sales`，挂在 `complete_acceptance_order` 的 SAT 分支：
  - 创建 ACTIVE `AfterSalesWarranty`（质保期取 `project.warranty_period_months` 缺省 12 个月，编号 WAR-{project_id}-{日期}，scope 记验收完成人）；
  - 项目质保起止日期/月数回填（只补空不覆盖）；
  - 项目下全部机台回填质保信息与客户归属（只补空）；
  - 幂等：已有 ACTIVE 质保直接返回既有记录。
- 验证：红灯 4 项（建档/幂等/缺省 12 月/接线）→ 绿灯 `tests/unit/test_acceptance_aftersales_handover.py` 4 passed（真 aiosqlite 异步会话）；acceptance 既有套件 12 passed；`import app.main` 通过。
- 备注：ITR 联动（AS-12）不在本项——ITR 工单按需创建而非验收即建，语义不同。

## 2026-07-04 继续：功能审计 HR-06/HR-07 修复（考勤假数据止损）

- 修复项：`HR-06/HR-07`。`/admin/attendance` 原来从员工/用户部门人数合成考勤统计，人数不足时还注入固定部门 fallback；迟到/请假/早退/缺勤由序号取模生成。`my-records` 固定返回当天 08:27/18:04，clock-in/out 不落库但返回成功。
- 红测：
  - 新增 `tests/unit/test_admin_attendance_hr06_07.py`，先证明有真实员工时接口仍返回合成部门统计；“我的考勤”返回硬编码记录；clock-in 假成功。
- 代码面：
  - `/admin/attendance` now 返回 200 显式空态：`items=[]`、`attendance_data_available=false`、`source=attendance-not-configured`、`employee_total`，保留页面入口但不再编造迟到/请假/缺勤/出勤率。
  - `/admin/attendance/statistics` 同步返回零值空态和 `attendance_data_available=false`。
  - `/admin/attendance/my-records` now 返回空态，不再硬编码当天记录。
  - `/admin/attendance/clock-in`、`clock-out`、`/{record_id}` now 返回 501，明确真实考勤域未接入，避免“成功但不落库”的数据丢失假象。
  - `/admin/attendance/export` 仅导出表头，不再导出合成数据。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_admin_attendance_hr06_07.py` -> 2 passed。
  - `.venv/bin/python -m pytest -q tests/api/test_batch4_route_contracts.py::test_batch4_compatibility_routes_return_200` -> 1 passed。
  - `ruff check`、`py_compile`、`git diff --check` 相关文件通过。
- 边界：本轮是止损下架假考勤；完整考勤域（请假/加班/补卡/真实打卡落库/统计）仍属 HR-08 及后续做实范围。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `HR-06/HR-07` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 HR-02 修复（离职审批联动停用登录账号）

- 修复项：`HR-02`。离职事务审批原来只改 `Employee.is_active/employment_status`，不联动绑定的 `User.employee_id`，员工离职后账号仍可登录。
- 红测：
  - 新增 `tests/unit/test_hr_resignation_user_deactivation_hr02.py`，创建员工、绑定用户和待审批 resignation 事务，先证明审批完成后员工已离职但绑定用户仍 `is_active=True`。
- 代码面：
  - `approve_hr_transaction()` 在 resignation 分支查询所有 `User.employee_id == employee.id` 且仍 active 的账号，逐个置 `is_active=False`。
  - 响应增加 `deactivated_user_count`，便于前端/运维确认本次离职处理停用了几个账号。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_hr_resignation_user_deactivation_hr02.py` -> 1 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_hr_resignation_user_deactivation_hr02.py tests/unit/test_hr_management_adapter.py` -> 4 passed。
  - `ruff check`、`py_compile`、`git diff --check` 相关文件通过。
- 已知无关测试债：`.venv/bin/python -m pytest -q tests/unit/test_hr_resignation_user_deactivation_hr02.py tests/unit/test_hr_management_adapter.py tests/unit/test_hr_management_coverage.py` 中 `tests/unit/test_hr_management_coverage.py::TestHrDashboardAdapterInit::test_init` 失败在旧测试只传 `HrDashboardAdapter(Mock())`，缺 `current_user`，与离职事务改动无关。
- 边界：本轮收口“离职后账号不停用”的登录风险；完整交接 workflow 未扩展。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `HR-02` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 HR-21 修复（时薪兜底告警与费率版本化）

- 修复项：`HR-21`。时薪服务原来在用户不存在或 USER/ROLE/DEPT/DEFAULT 全级 miss 时静默返回硬编码 100，查询 API 仍标为“配置”；费率更新原地覆盖、删除物理删，历史月份重算会被今天费率污染。
- 红测：
  - 新增 `tests/unit/test_hourly_rate_hr21.py`，先证明全级 miss 无 warning/API 无兜底来源标记；`PUT /hourly-rates/{id}` 会覆盖原行；`DELETE /hourly-rates/{id}` 会物理删除原行。
- 代码面：
  - `HourlyRateService.get_user_hourly_rate_detail()` 返回 `HourlyRateResolution`，包含 `hourly_rate/source/config_id/is_fallback/fallback_reason`；旧 `get_user_hourly_rate()` 继续返回 `Decimal`，兼容既有成本/报表调用。
  - 全级 miss、用户不存在 now 记录 warning，并标记 `source="系统兜底"`。
  - 查询 API now 返回来源、配置 ID、兜底标记和兜底原因，不再把硬编码 100 伪装成“配置”。
  - 更新费率 now 到期旧版本、创建新版本；历史日期仍按旧费率解析。
  - 删除费率 now 软停用并写入停用备注；历史有效区间仍可查得旧费率。
  - 补 `HourlyRateService(db)` 实例化兼容，满足旧覆盖测试和现有实例化调用。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_hourly_rate_hr21.py` -> 3 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_hourly_rate_hr21.py tests/unit/test_hourly_rate_service.py tests/unit/test_batch2_hourly_rate_service.py tests/unit/test_hourly_rate_service_coverage.py` -> 36 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_analysis_reports_rpt03.py tests/api/test_batch9_route_contracts.py::test_hourly_rates_collection_route_does_not_redirect_without_trailing_slash` -> 3 passed。
  - `ruff check`、`py_compile`、`git diff --check` 相关文件通过。
- 边界：本轮收口 HR-21 的兜底可见性与变更留痕；HR-20 旁路硬编码费率清单仍独立待修。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `HR-21` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 PERM-19 修复（角色删除撤销受影响用户会话）

- 修复项：`PERM-19`。角色删除接口原先直接删除 `role_api_permissions/user_roles/roles`，不收集受影响用户、不 bump 权限缓存修订号、不撤销这些用户已有会话。
- 红测：
  - 新增 `tests/unit/test_role_delete_perm19.py`，创建角色、受影响用户和活跃 `UserSession`，调用 `delete_role()` 后先证明 `UserRole` 被删但 session 仍 active。
- 代码面：
  - `roles.py::delete_role()` 删除前收集 `affected_user_ids` 和 `tenant_id`。
  - 删除提交后复用 PERM-13 的 `_invalidate_role_permission_cache()` bump 权限修订号并删受影响用户缓存。
  - 对受影响用户逐个调用 `SessionService.revoke_all_sessions()`，把活跃 session 标记 inactive 并进入 token 黑名单流程。
  - 响应 data 增加 `affected_user_count/revoked_session_count`，便于前端/运维确认影响范围。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_role_delete_perm19.py` -> 1 passed。
  - `.venv/bin/python -m pytest -q tests/api/test_role_tenant_isolation_contracts.py` -> 3 passed。
  - `.venv/bin/python -m pytest -q tests/api/test_role_permission_workflow_contracts.py -k 'role or permission'` -> 10 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_roles_endpoint.py -k delete_role` -> 2 passed。
  - `.venv/bin/python -m pytest -q tests/test_session_management.py::TestSessionService::test_revoke_all_sessions` -> 1 passed。
  - `ruff check`、`py_compile` 相关文件通过。
- 无关测试债：`tests/test_session_management.py -k 'revoke_all_sessions or revoke_session'` 组合跑会因固定用户名 `test_session_user` 重复插入而撞唯一键；单条 `revoke_all_sessions` 通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PERM-19` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 PERM-08 修复（审计日志查询 API）

- 修复项：`PERM-08`。`app/api/v1/endpoints/audits.py` 是兼容 shim，占位 fallback 只返回 `audits module placeholder`；权限/角色/用户操作有 `permission_audits` 写入，但 API 不可查。
- 红测：
  - 新增 `tests/unit/test_audits_api_perm08.py`，先证明 `read_audits/read_audit` 不存在；随后要求列表能按 operator/target/action/date 过滤，详情能返回 JSON detail，缺失 ID 返回 404。
- 代码面：
  - `audits.py` 替换为真实 `permission_audits` 查询路由：`GET /audits/` 分页列表，`GET /audits/{audit_id}` 详情。
  - 列表支持 `operator_id/target_type/target_id/action/start_date/end_date` 筛选；`detail` 从 JSON 字符串解析成对象，非法 JSON 保留 raw。
  - 读权限沿用管理侧 `role:read`，避免新增未种子的权限码导致查询端不可用。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_audits_api_perm08.py` -> 2 passed。
  - 路由挂载检查：`app.main` route table 包含 `/api/v1/audits/` 与 `/api/v1/audits/{audit_id}`。
  - `ruff check`、`py_compile` 相关文件通过。
- 边界：本轮补“权限审计可查”；业务操作审计覆盖不足仍属 `PERM-07`。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PERM-08` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 PERM-14 修复（read/view 权限别名接入鉴权）

- 修复项：`PERM-14`。系统已有 `permission_codes.py` 把 `*:view`/`*:read` 归一化，但 `auth.check_permission()` 和 `permission_engine.check_*()` 仍做精确串匹配，导致持有旧 `*:view` 权限时无法通过新 `*:read` 鉴权。
- 红测：
  - 新增 `tests/unit/test_permission_alias_perm14.py`，先证明 DB 路径、无 DB 缓存路径、permission engine 路径中 `project:view` 都不能满足 `project:read`。
- 代码面：
  - `auth.check_permission()` 在 DB、缓存、对象图 fallback 三条路径均使用 `canonicalize_permission_code(s)` 比较。
  - `permission_engine.check_permission_for_user/check_any_permission_for_user/check_all_permissions_for_user` 改为 canonicalized 比较。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_permission_alias_perm14.py` -> 3 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_security.py -k 'permission or require_permission'` -> 9 passed。
  - `.venv/bin/python -m pytest -q tests/test_core_modules.py -k permission_codes` -> 2 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_permission_cache_perm13.py` -> 3 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_core_auth.py` -> 24 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_auth_branches.py -k revoke` -> 4 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_permission_service_branches.py -k 'cache or invalidate_role_and_users or role_user_ids'` -> 13 passed。
  - `ruff check`、`py_compile` 相关文件通过。
- 边界：本轮只解决 `read/view` 查看类别名；其他语义别名不扩展，避免把不同动作误归一。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PERM-14` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 PERM-13 修复（权限缓存反查与跨 worker 失效）

- 修复项：`PERM-13`。原先角色权限变更只删角色缓存，受影响用户靠 `role_user_ids` 缓存反查；但 `set_role_user_ids` 基本无写入路径，导致用户权限缓存继续旧值。Redis 缺失时，不同 worker 的内存缓存也互不可见，只能等 TTL。
- 红测：
  - 新增 `tests/unit/test_permission_cache_perm13.py`，先证明 `RoleManagementService._invalidate_permission_cache()` 调 `invalidate_role_and_users()` 时没有传 `user_ids`。
  - 同文件补“修订号变化后不能使用旧缓存”与“`auth.check_permission` 不能绕过权限引擎直接吃旧缓存”两个红测。
- 代码面：
  - `role_management/service.py`、`permission_management_service.py`、`roles.py` 权限变更路径 now 直接查 `user_roles`，把受影响用户传给 `invalidate_role_and_users()`。
  - `permission_engine.py` 新增 `permission_cache_revisions` 修订号表读写；权限/角色关系变更后 bump，`load_permissions()` 用当前 revision 读写用户权限缓存。
  - `permission_cache_service.py` 用户权限缓存 payload 支持 `{permissions, revision}`；revision 不匹配即未命中，强制回 DB。
  - `auth.check_permission()` 有 DB 时统一走 `_load_user_permissions_from_db()`/权限引擎，不再外层直接读无 revision 的缓存。
  - 用户角色替换 `users/utils.py` 也同步 bump 修订号；新增 `migrations/20260704_permission_cache_revisions_sqlite.sql`。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_permission_cache_perm13.py` -> 3 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_permission_cache_service.py` -> 21 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_permission_service_branches.py -k 'cache or invalidate_role_and_users or role_user_ids'` -> 13 passed。
  - `.venv/bin/python -m pytest -q tests/api/test_role_permission_workflow_contracts.py -k 'permission or role'` -> 10 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_security.py -k 'permission or require_permission'` -> 9 passed。
  - `sqlite3 :memory: < migrations/20260704_permission_cache_revisions_sqlite.sql` -> 通过。
  - `ruff check`、`py_compile` 相关文件通过。
- 边界：本轮解决权限缓存即时失效与 Redis 缺失下跨 worker 旧缓存识别；`PERM-11` 裸端点覆盖率和 `PERM-15/16/17` 数据权限挂载仍待独立收口。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PERM-13` 已改为 `已验证`，PERM 小结同步更新。

## 2026-07-04 继续：功能审计 PERM-03 修复（Token 撤销 Redis 缺失持久兜底）

- 修复项：`PERM-03`。原先 Token 撤销优先写 Redis，Redis 未配置/失败时只落本进程 `_token_blacklist`，多 worker 或重启后撤销状态失效。
- 红测：
  - `tests/unit/test_core_auth.py::TestTokenRevocation::test_revoke_token_persists_when_redis_unavailable` 先模拟 `get_redis_client() -> None`，撤销后清空内存黑名单，初始 `is_token_revoked(token)` 返回 `False`。
- 代码面：
  - `app/core/auth.py` 新增 `jwt_token_blacklist` 数据库兜底：Redis 可用仍优先 `setex`；Redis 不可用/失败时按 JTI 写数据库，并保留本进程 token/JTI 内存兼容。
  - 查询撤销状态时 now 先查 Redis，再查数据库兜底表，最后回退内存；过期记录在写入时惰性清理。
  - 新增 `migrations/20260704_jwt_token_blacklist_sqlite.sql`，显式创建 `jwt_token_blacklist` 与过期索引。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_core_auth.py::TestTokenRevocation` -> 7 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_core_auth.py` -> 24 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_auth_branches.py -k revoke` -> 4 passed。
  - `sqlite3 :memory: < migrations/20260704_jwt_token_blacklist_sqlite.sql` -> 通过。
  - `ruff check`、`py_compile` 相关文件通过。
- 边界：本轮只解决 Token 撤销在 Redis 缺失时的跨进程/重启可见性；权限缓存反查与跨 worker 失效已随 `PERM-13` 另项收口。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PERM-03` 已改为 `已验证`，PERM 小结同步收敛根因描述。

## 2026-07-04 继续：功能审计 AS-18 修复（现场服务生成派工单并同步流转）

- 修复项：`AS-18`。售后现场服务原来只是 `after_sales_field_services` 记事本，`is_warranty` 创建时写死 true，没有状态流转，也不生成正式安装调试派工单。
- 红测：
  - 新增 `tests/unit/test_after_sales_field_service_as18.py`，先证明 `create_field_service()` 没有 `engineer_id` 契约、不会生成 `InstallationDispatchOrder`，且没有 `update_field_service_status()` 流转接口。
  - 同一测试证明无质保记录时 `is_warranty` 不应写死 true，并要求现场服务完成时同步派工单 `COMPLETED/progress=100/actual_hours`。
- 代码面：
  - `AfterSalesFieldService` 增加 `dispatch_order_id` 外键和关系，迁移脚本同步加列/索引。
  - `create_field_service()` 增加 `engineer_id/is_warranty/priority`；默认质保标记按项目有效质保期判断，不再硬编码 true。
  - 创建现场服务时同步生成 `InstallationDispatchOrder`：有工程师则派工单状态为 `ASSIGNED`，否则 `PENDING`。
  - 新增 `PUT /projects/{project_id}/field-services/{service_id}/status`，现场服务 `IN_PROGRESS/COMPLETED/CANCELLED/PLANNED` 会同步派工单状态、进度、实际工时和执行说明。
  - AS-07 后续兼容：legacy after-sales support ticket 创建仍发售后通知，升级接口可识别统一 `ServiceTicket`。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_after_sales_field_service_as18.py` -> 2 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_after_sales_field_service_as18.py tests/unit/test_after_sales_spare_parts_as08.py tests/unit/test_after_sales_as07.py tests/unit/test_after_sales_tables_as09.py tests/unit/test_service_ticket_notifications_as23.py tests/unit/test_dispatch_conflict_guard_as04.py tests/audit_p0/test_p0_14_dispatch_conflict.py` -> 29 passed。
  - SQLite 内存执行 `migrations/20260704_after_sales_tables_sqlite.sql` 与 `migrations/20260704_after_sales_field_service_dispatch_sqlite.sql` 通过，确认 `dispatch_order_id` 存在。
  - `ruff check`、`py_compile`、`git diff --check` 相关文件通过。
- 边界：本轮把 after-sales 现场服务接到既有安装调试派工单；未扩展复杂排班/技能推荐，仍沿用派工模块现有能力。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-18` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 AS-08 修复（备件库存联动与数值成本）

- 修复项：`AS-08`。售后备件原来只写 `after_sales_spare_parts.quantity`，不进入库存台账，也没有领用扣减；现场服务 `parts_cost`/备件单价是字符串，无法可靠做成本累计。
- 红测：
  - 新增 `tests/unit/test_after_sales_spare_parts_as08.py`，先证明 `AfterSalesSparePart.unit_price` 和 `AfterSalesFieldService.parts_cost` 仍是 `String`。
  - 同一测试证明 `create_spare_part()` 没有 `part_no/unit_price/min_stock` 契约、不会同步 `Inventory`，且不存在 `issue_spare_part()` 领用扣减闭环。
- 代码面：
  - `AfterSalesSparePart.unit_price`、`AfterSalesFieldService.travel_cost/parts_cost/total_cost` 改为 `Numeric(12, 2)`。
  - `create_spare_part()` 增加 `part_no/min_stock/unit_price`，创建后同步到统一仓储 `inventory`，默认仓为 `AFTER_SALES_SPARES`。
  - 新增 `POST /projects/{project_id}/spare-parts/{part_id}/issue`：校验可用库存，扣减售后备件数量和 `inventory.available_quantity`，可选关联现场服务并按 `unit_price * quantity` 累计 `parts_cost/total_cost`。
  - `get_spare_parts()` 返回 `unit_price/inventory_quantity/inventory_available_quantity`，便于前端识别真实库存状态。
  - `migrations/20260704_after_sales_tables_sqlite.sql` 同步把备件单价和现场服务成本字段改为 `NUMERIC(12, 2)`。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_after_sales_spare_parts_as08.py` -> 3 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_after_sales_spare_parts_as08.py tests/unit/test_after_sales_as07.py tests/unit/test_after_sales_tables_as09.py tests/api/test_openapi_route_contracts.py::test_after_sales_routes_are_registered` -> 17 passed。
  - SQLite 内存执行 `migrations/20260704_after_sales_tables_sqlite.sql` 通过，确认 `unit_price/parts_cost` 建表类型为 `NUMERIC(12, 2)`。
  - `ruff check`、`py_compile`、`git diff --check` 相关文件通过。
- 边界：本轮收口备件数量/库存/成本口径；现场服务派工单已在后续 `AS-18` 收口。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-08` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 AS-07 修复（项目售后中心接统一服务工单）

- 修复项：`AS-07`。项目级售后中心原来只读 `feedback/maintenance/support-tickets` 三组 after-sales 影子数据；支持工单使用 `after_sales_support_tickets`，与真正服务工单 `/service/tickets` 双轨割裂，前端也没有任何状态处理动作。
- 红测：
  - 新增 `tests/unit/test_after_sales_as07.py`，先证明 `get_project_support_tickets()` 读不到统一 `ServiceTicket`，`create_support_ticket()` 也不会写入 `service_tickets`。
  - 新增 `frontend/src/pages/AfterSales/__tests__/AfterSalesCenter.test.jsx`，先证明前端仍调 `/after-sales/projects/{id}/support-tickets`，没有走 `/service/tickets?project_id=...`。
- 代码面：
  - `after_sales.py` 的 legacy support-ticket 列表 now 优先读取统一 `ServiceTicket`，并保留旧 `AfterSalesSupportTicket` 只读兼容；legacy 创建入口 now 调统一 `create_service_ticket()`，新工单进入 `service_tickets`、SLA/通知/状态机同路。
  - `after_sales.py` 补 `PUT /projects/{project_id}/feedback/{feedback_id}` 与 `PUT /projects/{project_id}/maintenance/{maintenance_id}`，让反馈和保养记录至少可流转状态。
  - `AfterSalesCenter.jsx` 支持工单列表改调 `/service/tickets`，并给反馈、保养、工单补最小状态动作：开始处理/标记解决/完成保养/关闭工单。
  - `tests/api/test_service_ticket_crud_contracts.py` 的 resolution alias 测试按 AS-05 状态机先流转到 `RESOLVED` 再关闭。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_after_sales_as07.py` -> 2 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_after_sales_as07.py tests/unit/test_after_sales_tables_as09.py tests/unit/test_service_ticket_state_machine_as05.py tests/api/test_service_ticket_crud_contracts.py tests/api/test_openapi_route_contracts.py::test_after_sales_routes_are_registered` -> 18 passed。
  - `npm --prefix frontend test -- --run src/pages/AfterSales/__tests__/AfterSalesCenter.test.jsx src/pages/CustomerServiceDashboard/__tests__/dashboardContracts.test.js` -> 3 passed。
  - `ruff check`、`py_compile`、前端目标 `eslint`、`git diff --check` 相关文件通过。
- 边界：本轮收口“项目售后中心只读/服务工单双轨”；现场服务派工单已在后续 `AS-18` 收口。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-07` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 ADMIN-08 修复（Prometheus /metrics 与抓取配置）

- 修复项：`ADMIN-08`。`monitoring/prometheus.yml` 配置抓应用 `/metrics`，但主应用根路径没有 `/metrics`，且全局认证会拦截未带 token 的 Prometheus 抓取；配置里还直接抓 `mysql:3306` / `redis:6379`，不是 exporter 端口。
- 红测：
  - 新增 `tests/unit/test_prometheus_metrics_admin08.py`。初始 `TestClient(app).get("/metrics")` 返回 401；配置测试确认 `mysql:3306` 仍在 Prometheus 配置中。
- 代码面：
  - `app/main.py` 新增根 `/metrics`，返回 Prometheus text/plain，指标包括 `pms_app_health`、`pms_dependency_up`、`pms_scheduler_running`、`pms_scheduler_jobs`。
  - `GlobalAuthMiddleware.WHITE_LIST` 加 `/metrics`，Prometheus 无 token 也能抓。
  - `monitoring/prometheus.yml` 移除直接抓 MySQL/Redis 业务端口的 job，注明需部署 `mysqld_exporter` / `redis_exporter` 后再加。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_prometheus_metrics_admin08.py` -> 2 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_prometheus_metrics_admin08.py tests/unit/test_auth_branches.py tests/middleware/test_auth_middleware.py -k 'whitelist or metrics or health'` -> 14 passed。
  - `ruff check`、`py_compile`、`git diff --check` 相关文件通过。
- 边界：本轮只补应用级 Prometheus 抓取与配置止损；MySQL/Redis 深度指标需要后续实际部署 exporter 后再纳入。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `ADMIN-08` 已改为 `已验证`，ADMIN 小结同步移除“无 /metrics”遗留描述。

## 2026-07-04 继续：功能审计 AS-17 修复（工程师调度前端接口与建表职责）

- 修复项：`AS-17`。前端 `engineerScheduling.js` 调 `workload-board`、`availability`、`PUT /assignments/{id}`、`DELETE /assignments/{id}`，后端只具备创建分配/能力/负载/冲突等接口，页面动作会 404；同时分配创建曾在 endpoint 内直接 `__table__.create()`。
- 红测：
  - 新增 `tests/unit/test_engineer_scheduling_as17.py`，先确认前端写死的 4 个路由未注册，初始失败在 `("/workload-board", "GET") not in routes`。
- 代码面：
  - `engineer_scheduling.py` 补 `GET /workload-board`、`GET /engineers/{id}/availability`、`PUT /assignments/{id}`、`DELETE /assignments/{id}`。
  - 分配创建/更新/删除和负载分析统一调用 `EngineerSchedulingService.ensure_task_assignment_table()`；端点不再散落直接建表。
  - 可用性接口复用真实 workload 分析，返回 `available/is_available/availability_pct/booked_hours_per_week`；删除分配按 `CANCELLED` 软删除保留审计记录。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_engineer_scheduling_as17.py` -> 2 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_engineer_scheduling_as17.py tests/unit/test_engineer_scheduling_service_coverage.py tests/unit/test_dispatch_conflict_guard_as04.py tests/audit_p0/test_p0_14_dispatch_conflict.py` -> 24 passed。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js -t "engineer-scheduling"` -> 1 passed, 30 skipped。
  - `ruff check`、`py_compile`、`git diff --check` 相关文件通过。
- 边界：本轮收口“前端接口必 404”和建表职责集中；复杂智能排产策略、技能匹配推荐仍沿用既有 `EngineerSchedulingService` 能力。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-17` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 AS-13 修复（客户 360 页签字段与售后工单接入）

- 修复项：`AS-13`。客户 360 前端页签使用 `orders/payments/satisfactions/services`，后端只返回 `invoices/payment_plans/communications` 等正式字段，导致四个页签恒空；同时服务工单没有进入客户 360。
- 红测：
  - 新增 `tests/unit/test_customer_360_as13.py`，真实 DB 种销售订单、收款计划、服务工单、满意度调查。
  - 初始服务层测试失败：`KeyError: 'orders'`；API 测试失败：`Customer360Response` 过滤掉 `orders`。
- 代码面：
  - `Customer360Service.build_overview()` 增加 `SalesOrder`、`ServiceTicket`、`CustomerSatisfaction` 查询；`payments` 兼容映射现有 `ProjectPaymentPlan`。
  - `/customers/{id}/360` 响应增加前端组件可直接消费的轻量字段：`orders/payments/satisfactions/services`。
  - `Customer360Response` schema 增加这四个数组，避免 FastAPI `response_model` 过滤。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_customer_360_as13.py` -> 2 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_customer_360_service.py tests/unit/test_customer_360_service_coverage.py tests/unit/test_customer_360_as13.py` -> 20 passed。
  - `.venv/bin/python -m pytest -q tests/api/test_customers.py::TestCustomer360::test_get_customer_360` -> 1 passed。
  - `ruff check`、`py_compile`、`git diff --check` 相关文件通过。
- 边界：本轮解决客户 360 字段断链和服务工单入 360；客户 360 组件本身仍是轻量表格展示，不扩展成完整售后工作台。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-13` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 AS-09 修复（售后扩展表缺失 500）

- 修复项：`AS-09`。运行库缺 `after_sales_warranty / spare_parts / field_services / sla / satisfaction / knowledge` 等表时，质保、备件、现场服务、SLA、满意度、知识库端点会直接 `no such table` 500。
- 红测：
  - 新增 `tests/unit/test_after_sales_tables_as09.py`，逐个 drop 售后扩展表后调用真实端点函数。
  - 初始 `.venv/bin/python -m pytest -q tests/unit/test_after_sales_tables_as09.py` -> 读写端点均失败，错误为 `sqlite3.OperationalError: no such table: after_sales_*`。
- 代码面：
  - `app/api/v1/endpoints/after_sales.py` 新增统一 `_ensure_after_sales_tables()`，覆盖反馈、保养、支持工单、质保、备件、现场服务、SLA、满意度、知识库 9 张表；所有售后端点查询/写入前走同一兜底。
  - `app/models/__init__.py` 显式导出 `AfterSales*` 模型，避免 `app.models` 初始化新库时漏注册。
  - 新增 `migrations/20260704_after_sales_tables_sqlite.sql`，用 `CREATE TABLE IF NOT EXISTS`/`CREATE INDEX IF NOT EXISTS` 给真实 SQLite 运行库一次性落表。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_after_sales_tables_as09.py` -> 11 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_service_ticket_notifications_as23.py tests/api/test_path_param_route_contracts.py::test_project_overview_tolerates_missing_after_sales_tables tests/api/test_openapi_route_contracts.py::test_after_sales_routes_are_registered` -> 9 passed。
  - `ruff check` 相关文件通过（保留既有 `app/models/__init__.py:176` invalid noqa warning，非本轮新增）。
  - `py_compile`、`git diff --check` 相关文件通过。
- 边界：本轮只解决“缺表即 500”和新库注册/迁移；现场服务派工单已在后续 `AS-18` 收口。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-09` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 APPR-13 修复（合同中央状态机与大小写状态收口）

- 修复项：`APPR-13`。合同状态从 lowercase/uppercase/ACTIVE/voided 多套混写，收口为 uppercase canonical（`DRAFT/PENDING_APPROVAL/APPROVED/REJECTED/SIGNED/EXECUTING/COMPLETED/CANCELLED`），历史旧值读侧兼容并提供存量清洗脚本。
- 红测：
  - `.venv/bin/python -m pytest -q tests/unit/test_contract_status_machine_appr13.py` 初始 5 failed：新合同默认仍是 `draft`；输单联动不取消小写 `draft` 合同；S3→S4 不认小写 `signed`；到期提醒漏 `EXECUTING`；健康度不把 `voided` 识别为取消。
- 代码面：
  - `status_service.py` 提供 canonical 状态集合、`apply_contract_status()`、`contract_status_query_values()`、`fold_contract_status_counts()`；生产代码扫描确认 `contract.status =` 只剩状态服务写入口。
  - `contracts.py` 合同模型默认状态改为 `DRAFT`；统一审批合同适配器、合同签署/生成项目、商机输单事件监听器都改用状态助手。
  - `data_sync_service.sync_project_to_contract()` now 只允许 `EXECUTING -> COMPLETED`，不再把草稿/审批中合同越级完成。
  - 销售预测、奖金/绩效、商务支持报表、统一工作台、合同执行报表、阶段门、到期提醒、健康度、AI 报价校准等读侧使用 `normalize_contract_status()` / `contract_status_query_values()`，兼容 `ACTIVE/signed/executing/voided/approving` 存量值。
  - 新增 `migrations/20260704_contract_status_normalization_sqlite.sql`，用于把 `contracts.status` 存量旧值归一到 canonical；本轮只验证脚本，未直接写本地真实库。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_contract_status_machine_appr13.py` -> 8 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_contract_status_machine_appr13.py tests/unit/test_status_service_coverage.py tests/services/test_data_sync_service.py tests/unit/test_contract_status_update_guard_peer01_02.py tests/unit/test_contract_approval_adapter_deep.py` -> 43 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_stage_transition_checks.py tests/unit/test_stage_transition_checks_service.py tests/unit/test_stage_transition_service.py tests/unit/test_contract_reminders.py` -> 54 passed, 8 skipped。
  - `.venv/bin/python -m pytest -q tests/unit/test_ai_quote_calibration_contracts.py tests/unit/test_business_support_reports_service.py tests/unit/test_business_support_reports_service_coverage.py tests/unit/test_dashboard_adapter.py tests/unit/test_dashboard_adapter_coverage.py tests/unit/test_dashboard_adapters_compat.py app/tests/services/report_framework/adapters/test_sales.py tests/api/v1/endpoints/test_dashboard.py` -> 69 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_solution_engineer_bonus_service_coverage.py tests/unit/test_presale_bonus.py app/tests/services/engineer_performance/test_performance_calculator.py tests/unit/test_performance_calculator.py tests/unit/test_performance_calculator_coverage.py` -> 73 passed（仅保留既有 PytestCollectionWarning）。
  - `.venv/bin/python -m pytest -q tests/services/test_sales_prediction_service.py tests/unit/test_sales_prediction_service_coverage.py tests/unit/test_sales_prediction_n2.py -k 'not monthly and not accuracy'` -> 41 passed。
  - 迁移脚本内存 SQLite 验证通过：`ACTIVE/draft/executing/voided/approving/review` 归入 `EXECUTING/DRAFT/CANCELLED/PENDING_APPROVAL/APPROVED`。
  - 静态：`ruff check`、`py_compile`、`git diff --check` 相关文件均通过。
- 无关测试债：完整 `pipeline_health_service` 套件当前有缺 `customers` 表、漏导 `MagicMock`、旧签名调用等既有失败；完整销售预测旧测试仍按 `signed_date/contract_amount` mock 当前服务读取的 `signing_date/total_amount`；奖金 auto 套件仍导入不存在旧路径，均未作为 APPR-13 阻塞。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `APPR-13` 保持 `已验证`；F2 审批收口列表清空；数据清洗视图标注迁移脚本待发布/执行。

## 2026-07-04 继续：功能审计 APPR-19 修复（报价大额审批路由）

- 修复项：`APPR-19`，≥50 万报价必须进入含总经理审批的报价流程，旧报价适配器不能再提交到孤儿模板；节点推进时条件分支也不能因为丢 `entity_data` 而失明。
- 红测：
  - `tests/unit/test_approval_quote_routing_appr19.py` 先 3 failed：50 万报价仍走“标准报价审批”；`QuoteApprovalAdapter.submit_for_approval()` 仍用 `SALES_QUOTE` 和报价版本 ID；`_advance_to_next_node()` 的条件分支读不到 `entity.total_price` 而走默认分支。
- 代码面：
  - `init_approval_data.py` 大额报价规则阈值从 100 万修正为 50 万。
  - `QuoteApprovalAdapter.submit_for_approval()` now 使用 `SALES_QUOTE_APPROVAL` 和 `quote_id`，并在 form_data 中补 `total_price/gross_margin` 兼容统一路由字段。
  - `ApprovalEngineCore._build_instance_context()` 为已有实例补 adapter、entity_data、`entity.*` 和 `form_data.entity.*`，`_advance_to_next_node()` / `_return_to_node()` 复用该上下文。
  - `ApprovalSubmitMixin.submit()` 同步补 `entity.*`，新发起审批的规则也可直接写 `entity.total_price`。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_approval_quote_routing_appr19.py` -> 3 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_approval_quote_routing_appr19.py tests/unit/test_quote_adapter.py tests/unit/test_approval_adapter_quote.py tests/services/test_approval_quote_adapter.py tests/unit/test_quote_approval_service.py` -> 128 passed。
  - `.venv/bin/python -m pytest -q tests/unit/test_approval_router_deep.py tests/unit/test_approval_engine_submit.py tests/unit/test_approval_engine_service_combined.py tests/unit/test_approval_engine_approve.py tests/unit/test_approval_engine_approve_deep.py tests/unit/test_approval_timeout_task_appr09.py` -> 82 passed。
  - `.venv/bin/python -m pytest -q tests/api/test_sales_quote_costs_quantity_contracts.py` -> 3 passed。
  - 静态：`ruff check`、`py_compile`、`git diff --check` 相关文件均通过。
- 无关测试债：`tests/api/test_sales_quotes_api.py::TestSalesQuotesAPI::test_quote_items_management` 仍用旧字段 `quantity` 调当前明细接口，接口读取 `qty` 后返回 400“数量必须大于 0”；未作为 APPR-19 失败处理。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `APPR-19` 已改为 `已验证`，F1/F2 汇总残留同步清理。

## 2026-07-04 继续：功能审计 APPR-21 修复（角色审批人按项目上下文解析）

- 修复项：`APPR-21`，角色型审批节点原来只按全局 `Role/UserRole` 查用户；`SINGLE` 节点实际取列表第一个，导致有 `project_id` 的审批仍可能派给与项目无关的全局角色用户。
- 代码面：
  - `ApprovalRouterService._resolve_role_approvers()` now 会先从审批上下文提取 `project_id`（支持顶层、`form_data.project_id`、`entity_data.project_id`、`form_data.entity.project_id`、`entity.type=PROJECT`）。
  - 存在 `project_id` 时优先查 `project_members` 中同项目、同 `role_code`、启用成员，并按 `is_lead` 优先返回；没有项目成员时才回退全局角色。
- 验证：
  - 红灯：`PYTHONPATH=. pytest -q tests/unit/test_approval_role_context_appr21.py` 初始 1 failed，复现返回 `[全局第一人, 项目PM]`。
  - 绿灯：`PYTHONPATH=. pytest -q tests/unit/test_approval_role_context_appr21.py` -> 2 passed。
  - 相邻回归：`PYTHONPATH=. pytest -q tests/services/test_approval_router.py tests/unit/test_approval_engine_branches.py -k 'resolve_approvers_role or resolve_approvers_fixed_user or resolve_approvers_department_head or resolve_approvers_direct_manager or resolve_approvers_form_field or resolve_approvers_initiator'` -> 19 passed。
  - 静态：`ruff check app/services/approval_engine/router.py tests/unit/test_approval_role_context_appr21.py`、`python -m py_compile ...` 均通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `APPR-21` 已改为 `已验证`，F2 审批收口待办列表移除 `APPR-21`。

## 2026-07-04 继续：APPR-20 复核（legacy 审批兼容端点）

- 修复项：`APPR-20`，旧 `/approvals/instances` 兼容创建不能生成无节点、无任务、永久 `PENDING` 的空审批实例。
- 现场确认：工作区已有修复实现和专测；`legacy_compat.py` now 校验审批人、补 `LEGACY_APPROVAL_COMPAT` 模板/默认流/固定审批节点，再调用统一 `ApprovalEngineService.submit()` 创建实例和首节点任务。
- 复跑：`.venv/bin/python -m pytest -q tests/unit/test_approval_legacy_compat_appr20.py` -> 2 passed。
- 相邻回归：`.venv/bin/python -m pytest -q tests/unit/test_approval_legacy_compat_appr20.py tests/unit/test_approval_engine_submit.py tests/unit/test_approval_engine_service_combined.py tests/unit/test_approval_engine_approve.py` -> 50 passed。
- 静态：`.venv/bin/python -m ruff check app/api/v1/endpoints/approvals/legacy_compat.py tests/unit/test_approval_legacy_compat_appr20.py`、`.venv/bin/python -m py_compile ...` 均通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `APPR-20` 已从 `待修` 补正为 `已验证`；历史 `entity_type` 空实例仍属数据清洗。

## 2026-07-04 继续：剩余已修待验项复核（SALES-07/12、PROD-15）

- 复核项：`SALES-07`、`SALES-12`、`PROD-15`。这三项已有修复记录，但总台账仍停在 `已修待验`。
- 前端复跑：
  - `frontend/./node_modules/.bin/vitest run src/pages/QuoteManagement/__tests__/QuoteDetailDialog.fromQuote.test.jsx src/services/api/__tests__/sales.test.js src/routes/modules/__tests__/salesCompetitorAnalysisStopgap.test.jsx` -> 59 passed。
  - `frontend/./node_modules/.bin/eslint src/pages/SalesAI/ForecastDashboard.jsx src/pages/QuoteManagement/QuoteDetailDialog.jsx src/services/api/sales.js src/routes/modules/salesRoutes.jsx src/components/layout/sidebarConfig/default.js` -> passed。
  - `frontend/npm run build` -> passed（仅保留既有大 chunk/动态导入 warning）。
- 后端复跑：`.venv/bin/python -m pytest -q tests/api/test_shortage_handling.py tests/unit/test_urgent_purchase_service_coverage.py tests/unit/test_smart_alert_n2.py tests/unit/test_smart_alert_engine.py` -> 108 passed, 11 skipped（跳过项为测试文件标注的旧字段名/模型债）。
- 结论：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `SALES-07`、`SALES-12`、`PROD-15` 已补正为 `已验证`。

## 2026-07-04 继续：PROD-05 复核（齐套率口径）

- 复核项：`PROD-05`，齐套率口径统一为可用库存口径，在途量单列为预计口径，避免双算和跨项目预留遗漏。
- 复跑：`pytest -q tests/unit/test_kit_rate_service.py tests/unit/test_kit_rate_utils.py tests/unit/test_scheduled_kit_rate_tasks.py tests/unit/test_kit_check_utils.py tests/unit/test_assembly_kit_analysis_utils.py tests/unit/test_assembly_kit_service.py tests/services/test_assembly_kit_service.py tests/unit/test_project_workspace_service.py` -> 83 passed。
- 结论：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROD-05` 已从 `已修待验` 补正为 `已验证`。

## 2026-07-04 继续：F2 已验证项列表清理（SALES-05/PROJ-04/PROJ-07）

- 复核项：`SALES-05`、`PROJ-04`、`PROJ-07` 的明细行已是 `已验证`，但 `FUNCTIONAL_AUDIT_TRACKER.md` 的 F2 审批收口待办列表仍残留这三项。
- 复跑：
  - `.venv/bin/python -m pytest tests/api/test_sales.py::TestOpportunityManagement::test_update_opportunity_rejects_lost_to_won_transition tests/api/test_sales.py::TestOpportunityManagement::test_stage_endpoint_rejects_lost_to_won_transition tests/api/test_sales.py::TestOpportunityManagement::test_legacy_win_endpoint_rejects_lost_opportunity -q` -> 3 passed。
  - `.venv/bin/python -m pytest tests/unit/test_project_status_guard_proj04.py tests/unit/test_stage_advance_service.py tests/unit/test_acceptance_completion_service.py tests/unit/test_acceptance_service.py tests/unit/test_stage_transition_checks.py tests/unit/test_stage_transition_checks_service.py tests/unit/test_stage_transition_service.py -q` -> 99 passed, 8 skipped（按既有测试数据条件跳过）。
- 台账：F2 审批收口待办列表移除 `SALES-05/PROJ-04/PROJ-07`，明细行保持 `已验证`。

## 2026-07-04 继续：功能审计 PROD-09/PROD-10 复核补正

- 复核项：`PROD-09`（ECN 通用状态机审批绕过）和 `PROD-10`（采购申请转订单闸门），两项 7/3 已有红后绿记录，但总台账仍停在 `已修待验`。
- 当前验证：
  - `PROD-09`：`.venv/bin/python -m pytest tests/api/test_ecn_state_machine_contracts.py tests/api/test_path_param_route_contracts.py::test_ecn_state_machine_routes_tolerate_null_legacy_status tests/unit/test_state_machines_depth.py::TestEcnStateMachineIntegration tests/unit/test_ecn_adapter.py tests/unit/test_ecn_approval_adapter_n3.py -q` -> 75 passed。
  - `PROD-10`：`.venv/bin/python -m pytest tests/unit/test_purchase_service_generate_orders.py app/tests/services/purchase/test_purchase_service.py tests/api/test_purchase.py::TestPurchaseRequest -q` -> 25 passed。
  - 静态：`.venv/bin/python -m ruff check app/services/purchase/purchase_service.py app/api/v1/endpoints/ecn/state_machine.py tests/unit/test_purchase_service_generate_orders.py tests/api/test_ecn_state_machine_contracts.py`、`.venv/bin/python -m py_compile ...` 均通过。
- 环境说明：默认系统 Python 3.14 跑 API 用例会卡在 `TestClient` 初始化（`Client.__init__() got an unexpected keyword argument 'app'`）；本轮按项目原 `.venv` 环境复跑通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROD-09/PROD-10` 已改为 `已验证`，F2 审批收口待办列表移除这两项。

## 2026-07-04 继续：已修待验后端项批量复核

- 复核项：`SALES-06`、`SALES-08`、`SALES-11`、`SALES-13`、`SALES-16`、`HR-17`。
- 复跑：`pytest -q tests/unit/test_sales_forecast_wiring.py tests/unit/test_sales_target_actuals.py tests/unit/test_lead_convert_carryover.py tests/unit/test_intelligent_quote_stopgap.py tests/unit/test_sales_ai_degradation_marking.py tests/unit/test_bonus_approval_gate.py` -> 17 passed。
- 结论：以上 6 项已从 `已修待验` 补正为 `已验证`；未复跑的前端项（如 SALES-07/SALES-12）暂不改状态。

## 2026-07-04 继续：功能审计 APPR-15 复核（发货款触发器台账补正）

- 复核项：`APPR-15`，7/3 已修复并在 `PROJECT_NOTES` 记录为已验证，但当前总台账行仍停在 `已修待验`。
- 复跑：`pytest -q tests/api/test_delivery_payment_plan_trigger_contracts.py` -> 1 passed。
- 结论：发货确认同事务调用 `PaymentPlanService.trigger_delivery_payment_plan()` 仍有效；台账 `APPR-15` 已补正为 `已验证`。

## 2026-07-04 继续：功能审计 APPR-09 修复（通用审批超时调度）

- 修复项：`APPR-09`，通用审批节点 `timeout_hours/timeout_action` 原来只在任务上写 `due_at`，但没有任何调度扫描 `approval_tasks.due_at`；`handle_timeout()` 和 `notify_timeout_warning()` 都是死代码，且 AUTO_PASS/AUTO_REJECT 即使被调用也只改任务不推进实例。
- 代码面：
  - `ApprovalNodeExecutor.handle_timeout()` now 对 AUTO_PASS/AUTO_REJECT 复用 `process_approval()`，补齐或签/会签/依次审批的任务流转语义，不再手动只写 `task.status=COMPLETED`。
  - 新增 `ApprovalTimeoutMixin.process_approval_timeouts()`：扫描过期 `ApprovalTask`，执行 REMIND/AUTO_PASS/AUTO_REJECT/ESCALATE；自动通过/驳回会推进实例到下一节点或终态，并写 `ApprovalActionLog(TIMEOUT)`。
  - 新增 `process_approval_timeout_warnings()`：按节点 `timeout_remind_hours` 扫描即将超时任务，调用 `notify_timeout_warning()`，避免预警通知继续无人调用。
  - 新增 `scheduled_tasks/approval_tasks.py` 和 `scheduler_config/approval.py`；调度注册 `process_approval_timeout_warnings`（每小时 30 分）和 `process_approval_timeouts`（整点），并加入任务中心。
  - ESCALATE now 将原任务置 `EXPIRED` 并生成直属上级 `PENDING` 待办；无直属上级时回退为失败并保留原任务待办，避免实例无待办卡死。
- 验证：
  - 红灯：`pytest -q tests/unit/test_approval_timeout_task_appr09.py` 初始 7 failed，复现服务方法/调度函数/配置均不存在。
  - 绿灯：`pytest -q tests/unit/test_approval_timeout_task_appr09.py` -> 7 passed。
  - 相邻回归：`pytest -q tests/unit/test_approval_timeout_task_appr09.py tests/unit/test_approval_executor.py tests/services/test_approval_executor.py tests/unit/test_approval_engine_service_combined.py tests/unit/test_approval_engine_approve.py tests/unit/test_approval_engine_approve_deep.py tests/services/test_approval_approve.py` -> 146 passed。
  - 调度/P0 回归：`pytest -q tests/unit/test_scheduled_stub_tasks.py tests/audit_p0/test_p0_10_stub_tasks.py tests/unit/test_scheduler_utils.py` -> 48 passed。
  - 静态：`python -m py_compile app/services/approval_engine/executor.py app/services/approval_engine/engine/timeout.py app/services/approval_engine/engine/__init__.py app/utils/scheduled_tasks/approval_tasks.py app/utils/scheduled_tasks/__init__.py app/utils/scheduler_config/approval.py app/utils/scheduler_config/__init__.py` 通过。
- 额外观察：全量旧 `tests/unit/test_scheduled_tasks.py` 当前仍有 3 个既有失败，落在 `app.services.notification_queue` 旧 patch 路径和 timesheet 聚合 mock 期望，未作为 APPR-09 阻塞。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `APPR-09` 已改为 `已验证`，并从“审批收口待办”移入 F3 调度可信化已验证列表。

## 2026-07-04 继续：功能审计 APPR-08 修复（前/后加签真实任务流）

- 修复项：`APPR-08`，统一审批加签原来只写附加任务，但流转阶段不会激活加签人任务，导致“前加签”跳过原审批人、“后加签”加签人永远收不到待办。
- 代码面：
  - `ApprovalExecutor.process_approval()` now 识别 `ADDED_BEFORE/ADDED_AFTER` 任务：前加签审批通过后恢复原审批任务为 `PENDING`；后加签在原审批人通过后激活加签任务，等待后加签完成后才推进节点。
  - 审批任务完成后显式 `flush()`，避免 `autoflush=False` 场景下相邻 pending 查询读到旧状态。
  - `_advance_to_next_node()` 对加签任务补 node 兜底，防止任务关系未预载时节点推进拿不到定义。
- 验证：
  - 红灯：`PYTHONPATH=. pytest -q tests/unit/test_approval_add_sign_appr08.py` 初始 2 failed，复现前加签后原审批任务仍 `SKIPPED`、后加签任务仍 `SKIPPED` 且实例被提前 `APPROVED`。
  - 绿灯：`PYTHONPATH=. pytest -q tests/unit/test_approval_add_sign_appr08.py` -> 2 passed。
  - 相邻回归：`PYTHONPATH=. pytest -q tests/unit/test_approval_add_sign_appr08.py tests/unit/test_approval_executor.py tests/unit/test_approval_executor_deep.py tests/audit_p0/test_p0_05_cosign_reject_flip.py` -> 76 passed；`PYTHONPATH=. pytest -q tests/unit/test_approval_engine_approve.py -k 'add_approver or approve or reject'` -> 26 passed；`PYTHONPATH=. pytest -q tests/unit/test_approval_engine_approve_deep.py` -> 12 passed。
  - 静态：`ruff check app/services/approval_engine/executor.py app/services/approval_engine/engine/core.py tests/unit/test_approval_add_sign_appr08.py`、`python -m py_compile ...` 均通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `APPR-08` 已改为 `已验证`，F2 审批收口待办列表移除 `APPR-08`。

## 2026-07-04 继续：功能审计 APPR-12 修复（旧增强合同审批轨道下线）

- 修复项：`APPR-12`，`/sales/contracts/enhanced/{id}/submit|approve|reject` 原来走旧 `contract_approvals` 自维护流程，可绕过统一审批引擎和真实 `ApprovalTask` 自审自过。
- 代码面：
  - 旧增强 `/submit` 保留兼容入口，但内部改调 `app.services.contract_approval.ContractApprovalService.submit_contracts_for_approval()`，使用 `SALES_CONTRACT_APPROVAL` 模板创建统一 `ApprovalInstance/ApprovalTask`，由统一适配器同步合同状态为 `PENDING_APPROVAL`。
  - 旧增强 `/approve`、`/reject` 明确返回 400，提示使用 `/sales/contracts/approval/action`，不再消费旧 `ContractApproval` 记录、也不再直接改 `Contract.status`。
  - 旧 `ContractEnhancedService` 内部审批方法暂保留，避免破坏仍覆盖该兼容 service 的旧单元测试；线上写入口已在路由层切断。
- 验证：
  - 红灯：`PYTHONPATH=. pytest -q tests/unit/test_contract_enhanced_approval_appr12.py` 初始 2 failed，复现旧 submit 不建 `ApprovalInstance`、旧 approve 直接改合同状态。
  - 绿灯：`PYTHONPATH=. pytest -q tests/unit/test_contract_enhanced_approval_appr12.py` -> 2 passed。
  - 相邻回归：`PYTHONPATH=. pytest -q tests/api/test_approval_submit_error_contracts.py tests/unit/test_contract_enhanced_approval_appr12.py` -> 6 passed；`PYTHONPATH=. pytest -q tests/unit/test_contract_enhanced_n2.py -k 'ApproveContract or RejectContract'` -> 7 passed。
  - 旧大套件现状：`tests/unit/test_contract_enhanced_n2.py` 全量仍有早已漂移的 mock 断言/`save_obj` patch 失败；`tests/integration/test_sales_approval_flow.py` 仍有旧 fixture 字段名/adapter 方法名漂移，未作为本轮业务失败。
  - 静态：`ruff check app/api/v1/endpoints/sales/contracts/enhanced.py tests/unit/test_contract_enhanced_approval_appr12.py`、`python -m py_compile ...`、`git diff --check` 均通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `APPR-12` 已改为 `已验证`，F2 审批收口待办列表移除 `APPR-12`。

## 2026-07-04 继续：功能审计 PROD-17 止损（AI 排程/优化拒绝模板假数据）

- 修复项：`PROD-17`，AI 智能排程/优化在没有足够相似历史项目时仍继续输出默认 60 天工期、固定节省天数、复用率和自动化建议，容易把模板数字误当真实 AI 结论。
- 止损口径：
  - `ScheduleGenerationService.generate_schedule()` now 要求至少 3 个同品类/同行业已完成历史项目且有有效起止日期；样本不足返回 `status=unavailable/reason=insufficient_historical_samples`，不返回 `tasks/total_days`。
  - `ScheduleOptimizationService.analyze_optimization_potential()` now 要求至少 3 个相似历史项目；样本不足返回 `status=unavailable/reason=insufficient_similar_projects`，优化分析为空、节省天数为 0、建议为空。
  - 有足够样本时结果显式带 `status=success`、`data_source=historical_projects`、样本数和置信度，避免前端/接口误解数据来源。
  - `schedule_generation` API 对 `unavailable` 返回 422，不再把不可用结果当正常计划继续比较或保存。
- 验证：
  - 红灯：`pytest -q tests/unit/test_ai_schedule_stopgap_prod17.py` 初始 4 failed，复现无样本仍吐模板计划/模板优化建议。
  - 绿灯：`pytest -q tests/unit/test_ai_schedule_stopgap_prod17.py` -> 4 passed。
  - 相邻回归：`pytest -q tests/unit/test_schedule_generation_service.py tests/unit/test_schedule_generation_service_coverage.py` -> 11 passed；`pytest -q tests/unit/test_schedule_optimization_service.py tests/unit/test_schedule_optimization_service_coverage.py` -> 9 passed。
  - 静态：`python -m py_compile ...` 与 `python -m ruff check ...` 均通过。
- 结论：PROD-17 已按止损包验证；完整 AI 排程/优化算法仍是后续做实范围。

## 2026-07-04 继续：功能审计 PROD-16 修复（发货明细 + 齐套/质检门禁 + 项目状态联动）

- 修复项：`PROD-16`，发货单原来只有表头和手填总额，没有明细行；确认发货只改 `DeliveryOrder.delivery_status/ship_date`，不检查项目齐套、出货质检，也不推进项目状态。
- 代码面：
  - `DeliveryOrderItem`/`delivery_order_items` 已新增，发货响应带 `items`；创建发货单时可显式传明细，未传时从 `SalesOrderItem` 复制剩余未发数量，并拦截超发/无明细销售订单。
  - `ship_delivery_order()` 发货前新增三道门禁：发货单必须有正数量明细；项目 `material_status/kitting_rate/shortage_items_count` 达到齐套；项目关联工单或明细物料存在最新 `FQC/OQC` 且结果为 `PASS`。
  - 发货时项目只向前推进到 `S8/ST24`（运输中），签收推进到 `S8/ST25`（SAT 进行中），不会把更后阶段项目倒退。
  - 本地 `data/app.db` 已执行 `migrations/20260704_delivery_order_items_sqlite.sql`，确认存在 `delivery_order_items` 表及 3 个索引。
- 验证：
  - 红灯：`PYTHONPATH=. pytest -q tests/unit/test_delivery_order_detail_gate_prod16.py` 初始 import 失败，复现 `DeliveryOrderItem` 缺失。
  - 绿灯：`PYTHONPATH=. pytest -q tests/unit/test_delivery_order_detail_gate_prod16.py` -> 2 passed。
  - 相邻回归：`PYTHONPATH=. pytest -q tests/api/test_delivery_payment_plan_trigger_contracts.py tests/unit/test_business_support_delivery_approval_misc19.py tests/unit/test_delivery_order_detail_gate_prod16.py tests/unit/test_delivery_order_project_filter.py` -> 7 passed。
  - 路由契约：`PYTHONPATH=. pytest -q tests/api/test_business_support_delivery_routes.py` 仍在本机 `TestClient/httpx` 初始化阶段报 `Client.__init__() got an unexpected keyword argument 'app'`，未进入业务断言；已同步更新该文件测试数据以符合新门禁。
  - 静态：`ruff check ...` 与 `python -m py_compile ...` 均通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROD-16` 已改为 `已验证`；“结构断链”列表清空。

## 2026-07-04 继续：功能审计 AS-14 修复（设备保养提醒 + 终验转售后保养计划）

- 修复项：`AS-14`，设备保养提醒调度仍在 `stub_tasks.py` 返回 not_implemented，生产调度配置依赖不存在的 `equipment_maintenance_plans`；同时已有 `ProjectDataFlowService.transfer_to_after_sales()` 能生成 1/3/6/12 月保养计划，但终验完成流程没有调用。
- 代码面：
  - 新增 `EquipmentMaintenanceService.check_maintenance_reminders()`：扫描启用设备的 `next_maintenance_date`，对窗口内到期/逾期设备生成去重 `EQUIPMENT_MAINTENANCE` AlertRecord；逾期为 CRITICAL，到期/临近为 WARNING，handler 取车间主管。
  - 新增 `scheduled_tasks/equipment_maintenance_tasks.py` 并从任务包导出 `check_equipment_maintenance_reminder`；`stub_tasks.py` 移除旧存根；`scheduler_config/production.py` 解禁每日 8:30 调度，依赖表改为 `equipment/workshop/alert_rules/alert_records`。
  - `AcceptanceCompletionService.trigger_after_sales_maintenance_plan()` 新增终验通过后的售后保养计划联动；`acceptance/order_workflow.py` 在 FINAL/PASSED 完成流中调用它，复用现有 `ProjectDataFlowService.transfer_to_after_sales()` 的保养计划口径。
  - `test_acceptance_outsourcing_branches.py` 中旧质保期测试改为显式模拟阶段门通过，避免和当前 S8→S9 门禁口径互相冲突。
- 验证：
  - 红灯：`pytest -q tests/unit/test_equipment_maintenance_reminder_as14.py` 初始 3 failed，复现设备提醒仍是 not_implemented、stub 仍导出、验收完成服务缺少售后保养联动函数。
  - 绿灯：`pytest -q tests/unit/test_equipment_maintenance_reminder_as14.py` -> 3 passed。
  - 相邻回归：`pytest -q tests/unit/test_scheduled_stub_tasks.py` -> 13 passed；`pytest -q tests/audit_p0/test_p0_10_stub_tasks.py` -> 15 passed；`pytest -q tests/unit/test_acceptance_completion_service.py tests/unit/test_acceptance_outsourcing_branches.py` -> 72 passed；`pytest -q app/tests/services/project_data_flow/test_project_data_flow_service.py` -> 12 passed。
  - 静态：`python -m py_compile ...` 与 `python -m ruff check ...` 均通过。
- 结论：AS-14 已验证；APPR-04 备注里的“维保计划独立留 AS-14”已收口，APPR-04 同步推进为已验证。

## 2026-07-04 继续：功能审计 APPR-04 收口（缺料日报写入 + P0#10 全量回归）

- 修复项：`APPR-04`（全局 P0#10）缺料 3 件套最后一环：`generate_shortage_daily_report` 原来仍由 `stub_tasks.py` 返回 not_implemented，`ShortageDailyReport/mat_shortage_daily_report` 只有模型和查询入口，没有任何写入口。
- 代码面：
  - `ShortageReportsService.generate_daily_report()` 与 `save_shortage_daily_report()` 复用既有统计函数，按日期 upsert `ShortageDailyReport`，覆盖预警、上报、齐套、到货、响应、停工字段。
  - `scheduled_tasks/shortage_tasks.py` 新增真实 `generate_shortage_daily_report(target_date=None)`，success 返回 `report_date/report_id/data`，异常返回 error 哨兵供调度监控计失败。
  - `scheduled_tasks/__init__.py` 改从真实 shortage_tasks 导出日报任务；`stub_tasks.py` 移除该存根和 `__all__` 导出；`scheduler_config/shortage.py` 解禁每日 5:15 日报任务并更新依赖表。
  - `test_scheduled_stub_tasks.py` 移除已回填任务的 stub 断言，避免旧测试把真实任务拉回假实现。
- 验证：
  - 红灯：`pytest -q tests/unit/test_shortage_alert_task_backfill.py` 初始 2 failed，复现日报任务仍返回 not_implemented 且 stub 仍导出。
  - 绿灯：`pytest -q tests/unit/test_shortage_alert_task_backfill.py` -> 9 passed。
  - 相邻回归：`pytest -q tests/services/test_shortage_reports_service.py` -> 17 passed；`pytest -q tests/unit/test_scheduled_stub_tasks.py` -> 14 passed；`pytest -q tests/unit/test_shortage_analytics_service.py -q` -> 20 passed。
  - P0 审计：`pytest -q tests/audit_p0/test_p0_10_stub_tasks.py` -> 15 passed，确认无 enabled scheduler job 继续背靠 stub。
  - 静态：`python -m py_compile ...` 与 `python -m ruff check ...` 均通过。
- 结论：APPR-04 P0 范围后续随 AS-14 一并收口，当前台账已推进为"已验证"。

## 2026-07-04 继续：功能审计 AS-12 修复（售后到质量 Issue/ECN/ITR 闭环）

- 修复项：`AS-12`，售后服务工单无法升级为质量问题或 ECN，`Ecn.source_type/source_id` 虽存在但无售后写入点；`itr.py` 自我导入导致线上只暴露 placeholder，`itr_service.py`/`itr_analytics_service.py` 成为死代码。
- 代码面：
  - `service/tickets/issues.py` 新增 `POST /tickets/{ticket_id}/issues`：服务工单可升级为 `Issue(category=QUALITY)`，自动带 `project_id/machine_id/service_ticket_id` 并写工单 timeline。
  - `service/tickets/issues.py` 新增 `POST /tickets/{ticket_id}/ecn`：服务工单可升级为 ECN 草稿，写 `source_type=SERVICE_TICKET/source_id/source_no`，自动带项目/设备/问题描述并写工单 timeline。
  - `itr.py` 从自我导入占位改为真实路由：`/itr/tickets/{ticket_id}/timeline`、`/itr/issues/{issue_id}/related`、`/itr/dashboard`。
  - `itr_service.get_ticket_timeline()` now 优先按 `Issue.service_ticket_id` 取关联问题，并把 `QUALITY` 问题纳入 ITR timeline/dashboard 统计。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_service_ticket_escalation_as12.py` -> 2 passed。
  - 相邻回归：`PYTHONPATH=. pytest -q tests/unit/test_service_ticket_escalation_as12.py tests/unit/test_device_archive_as10.py tests/unit/test_service_ticket_state_machine_as05.py tests/unit/test_ecn_bom_auto_sync_prod07.py` -> 8 passed。
  - 静态：`ruff check app/api/v1/endpoints/service/tickets/issues.py app/api/v1/endpoints/itr.py app/services/itr_service.py tests/unit/test_service_ticket_escalation_as12.py`、`python -m py_compile ...`、`git diff --check` 均通过。
- 后续更新：`PROJ-23` 已在 2026-07-04 后续主链路补验中标绿；`transfer_to_after_sales()` now 落 ACTIVE 质保档、保养计划，并回填项目/机台质保与客户归属。

## 2026-07-04 继续：功能审计 PROD-07 修复（ECN 审批/执行自动同步 BOM）

- 修复项：`PROD-07`，真正改 BOM 的 `EcnIntegrationService.sync_to_bom()` 原来只有手工端点调用；ECN 审批通过、开始执行、通用状态机进入执行态都只改 ECN 自身状态，导致流程走完但 BOM 仍不变。
- 代码面：
  - `EcnIntegrationService` 新增 `sync_to_bom_if_ready()` 幂等入口：仅 `APPROVED/EXECUTING` 同步，仍只处理 `EcnAffectedMaterial.status == PENDING`，重复调用不会重复改。
  - `EcnApprovalAdapter.sync_from_approval_instance()` 在审批实例变为 `APPROVED` 时自动同步 BOM。
  - `start_ecn_execution()` 在 `APPROVED -> EXECUTING` 时自动同步 BOM，兜底历史/手工置为已批准的 ECN。
  - ECN 通用状态机 `_apply_current_transition()` 在进入 `EXECUTING/IN_PROGRESS/IMPLEMENTED` 时自动同步 BOM，避免只修专用执行端点。
  - 同步后继续写 `EcnBomChange` 审计留痕，并把影响行置为 `PROCESSED`。
- 验证：
  - 红灯：新增 `tests/unit/test_ecn_bom_auto_sync_prod07.py` 初始失败，复现审批通过后 `BomItem.quantity` 仍保持旧值。
  - 绿灯：`PYTHONPATH=. pytest -q tests/unit/test_ecn_bom_auto_sync_prod07.py` -> 2 passed。
  - ECN 相邻状态机：`PYTHONPATH=. pytest -q tests/unit/test_ecn_bom_auto_sync_prod07.py tests/unit/test_state_machines_depth.py -k 'EcnStateMachine or ecn'` -> 9 passed。
  - BOM/工单组合回归：`PYTHONPATH=. pytest -q tests/unit/test_bom_version_management.py tests/unit/test_ecn_bom_auto_sync_prod07.py tests/audit_p0/test_p0_12_bom_workorder_broken.py tests/unit/test_work_order_bom_snapshot.py` -> 8 passed。
  - 静态：`ruff check app/services/ecn/integration/ecn_integration_service.py app/services/approval_engine/adapters/ecn.py app/api/v1/endpoints/ecn/execution.py app/api/v1/endpoints/ecn/state_machine.py tests/unit/test_ecn_bom_auto_sync_prod07.py`、`python -m py_compile ...`、`git diff --check` 均通过。
- 后续更新：`PROD-20` 已在 2026-07-04 后续补齐采购影响传导；`sync_to_purchase()` now 会从受影响物料反查采购订单行并把 `MODIFY` 标记为采购待评审。

## 2026-07-04 继续：功能审计 PROD-06 修复（BOM 多版本修订）

- 修复项：`PROD-06`，`BomHeader.bom_no` 单列唯一导致同一 BOM 永远只有一行，`version/is_latest` 只是装饰；版本列表永远 1 条，发布时“旧版本置非 latest”实际 update 0 行，且缺少从已发布 BOM 创建修订版的入口。
- 代码面：
  - `app/models/material.py` 移除 `bom_no unique=True`，改为 `bom_no + version` 唯一，并增加 `idx_bom_no`。
  - `app/api/v1/endpoints/bom/bom_versions.py` 新增 `POST /{bom_id}/versions`：只能从 `RELEASED` BOM 创建修订版，复制表头和 BOM 明细为新的 `DRAFT` 版本；采购/到货/齐套执行状态不继承，修订版重新从 0 开始。
  - `get_bom_versions()` now 返回真实明细，`release_bom()` 原有 latest 切换 now 因多版本可实际生效；顺手移除 `bom_release.py` 未使用 import。
  - 本地 `data/app.db` 已执行 `migrations/20260703_bom_versioning_sqlite.sql`，`bom_headers` 当前索引为 `uq_bom_no_version`、`idx_bom_no`、`idx_bom_project`、`idx_bom_machine`，不再有单列 `bom_no` 唯一索引。
- 验证：
  - 红灯/现场：`tests/unit/test_bom_version_management.py` 原先通过 `TestClient` 触发本机 `httpx/starlette` 不兼容，未能跑到业务逻辑；改为直接端点函数级契约测试后验证真实逻辑。
  - 绿灯：`PYTHONPATH=. pytest -q tests/unit/test_bom_version_management.py` -> 2 passed。
  - 相邻回归：`PYTHONPATH=. pytest -q tests/unit/test_bom_version_management.py tests/audit_p0/test_p0_12_bom_workorder_broken.py tests/unit/test_work_order_bom_snapshot.py` -> 6 passed。
  - 静态：`ruff check app/models/material.py app/schemas/material.py app/api/v1/endpoints/bom/bom_versions.py app/api/v1/endpoints/bom/bom_release.py tests/unit/test_bom_version_management.py`、`python -m py_compile ...`、`git diff --check` 均通过。

## 2026-07-04 继续：功能审计 AS-05 修复（服务工单状态机矩阵）

- 修复项：`AS-05`，服务工单状态更新入口只校验目标值是否合法，未传 `transition_rules`，导致 `PENDING` 可直接跳 `RESOLVED/CLOSED`；`/close` 只拦重复关闭，未要求先解决；兼容 service 仍写旧状态 `assigned/completed`。
- 代码面：
  - `app/models/service/enums.py` 新增服务工单标准转移矩阵：`PENDING -> IN_PROGRESS -> RESOLVED -> CLOSED`，并提供归一化、规则导出和转移校验 helper。
  - `app/api/v1/endpoints/service/tickets/status.py` 的 `/status` now 先校验状态转移，传入 `StatusUpdateService.transition_rules`；`/close` now 要求当前状态为 `RESOLVED`，不能从待处理/处理中直接关闭。
  - `app/services/service/service_tickets_service.py` 兼容 service 同步接入转移校验；分配/自动分配后新写入 `IN_PROGRESS`，关闭写入 `CLOSED`，读侧继续兼容历史 `assigned/completed` alias。
- 验证：
  - 红灯：新增 `tests/unit/test_service_ticket_state_machine_as05.py` 初始失败，复现 `PENDING -> RESOLVED` 未被拦截。
  - 绿灯：`PYTHONPATH=. pytest -q tests/unit/test_service_ticket_state_machine_as05.py` -> 2 passed。
  - 相邻售后回归：`PYTHONPATH=. pytest -q tests/unit/test_service_ticket_state_machine_as05.py tests/unit/test_service_ticket_notifications_as23.py tests/unit/test_service_tickets_service.py` -> 46 passed。
  - 静态：`ruff check app/models/service/enums.py app/api/v1/endpoints/service/tickets/status.py app/services/service/service_tickets_service.py tests/unit/test_service_ticket_state_machine_as05.py tests/unit/test_service_tickets_service.py`、`python -m py_compile ...`、`git diff --check` 均通过。
- 残留：存量 89 条服务工单中 48 条枚举外脏值仍需迁移清洗；本轮已阻止新写入继续制造 `assigned/completed` 脏状态。

## 2026-07-04 继续：功能审计 AS-10/AS-11 修复（客户侧设备档案与机台级售后溯源）

- 修复项：`AS-10/AS-11`（全局 P0#13，域内 P1；`APPR-06` 合并），`machines` 缺客户侧 SN/客户/质保字段，`service_tickets` 无设备外键，机台“服务历史”靠 `ServiceRecord.machine_no` 文本匹配 `Machine.machine_no` 整数，导致售后无法做设备级溯源。
- 代码面：
  - `Machine` 新增 `customer_id/serial_no/warranty`，`ServiceTicket` 新增 `machine_id`，`ServiceRecord` 新增 `machine_id`；三处 Schema 同步暴露字段。
  - 项目机台创建 now 默认继承项目客户，并拒绝设备客户与项目客户不一致。
  - 服务工单创建 now 校验 `machine_id` 存在且属于同项目/客户，响应返回 `machine_name/machine_serial_no`。
  - 服务记录创建/更新 now 支持 `machine_id` 并同步兼容旧 `machine_no`；机台服务历史 now 优先按 `ServiceRecord.machine_id` 查询，同时兼容旧文本 `machine_no`。
  - 本地 `data/app.db` 已补 `machines.customer_id/serial_no/warranty`、`service_tickets.machine_id`、`service_records.machine_id` 及索引；迁移文件：`migrations/20260704_device_archive_links_sqlite.sql`。
- 验证：
  - 红灯：`PYTHONPATH=. pytest -q tests/audit_p0/test_p0_13_device_archive_missing.py` -> 4 failed；新增 `tests/unit/test_device_archive_as10.py` 初始因 `Machine.customer_id` 不存在失败。
  - 绿灯：`PYTHONPATH=. pytest -q tests/audit_p0/test_p0_13_device_archive_missing.py tests/unit/test_device_archive_as10.py` -> 6 passed。
  - 售后相邻回归：`PYTHONPATH=. pytest -q tests/unit/test_service_ticket_notifications_as23.py tests/unit/test_service_tickets_service.py tests/unit/test_device_archive_as10.py` -> 46 passed；`PYTHONPATH=. pytest -q tests/unit/test_service_records_service.py tests/services/test_service_records_service.py tests/unit/test_service_records_service_coverage.py` -> 9 passed, 1 skipped。
  - 机台 schema 回归：`PYTHONPATH=. pytest -q tests/schemas/test_project_machine.py tests/services/project_crud/test_service.py -k machine` -> 2 passed。
  - 静态：`ruff check ...`、`python -m py_compile ...`、`git diff --check` 均通过。

## 2026-07-04 继续：功能审计 PROD-08 修复（BOM 到生产工单快照）

- 修复项：`PROD-08`（全局 P0#12，域内 P1；`APPR-05` 合并），生产工单不关联 BOM，`WorkOrderBom` 中间表仅有模型/导出引用、无业务读写，导致领料/齐套随机台 BOM 漂移，无法锁定工单时点版本。
- 代码面：
  - `WorkOrder` 新增 `bom_id/bom_no/bom_version`，并与 `BomHeader`、`WorkOrderBom` 建关系；`WorkOrderCreate/Update/Response` 暴露 BOM 字段。
  - `WorkOrderService.create_work_order()` 在传入 `bom_id` 时校验项目/机台归属，保存工单后把 `BomItem` 固化到 `mat_work_order_bom`，`required_qty = bom_qty * plan_qty`。
  - `WorkOrderService.update_work_order()` 支持重新绑定或清空 BOM，并同步刷新/删除工单 BOM 快照，避免更新路径再次断链。
  - 本地 `data/app.db.work_order` 已补 `bom_id/bom_no/bom_version` 和 `idx_work_order_bom`；迁移文件：`migrations/20260703_work_order_bom_snapshot_sqlite.sql`。
- 验证：
  - 红灯：`tests/audit_p0/test_p0_12_bom_workorder_broken.py` 2 failed；`tests/unit/test_work_order_bom_snapshot.py` 1 failed（无 `order.bom_id`）。
  - 绿灯：`PYTHONPATH=. pytest -q tests/audit_p0/test_p0_12_bom_workorder_broken.py tests/unit/test_work_order_bom_snapshot.py` -> 4 passed。
  - 工单服务回归：`PYTHONPATH=. pytest -q tests/unit/test_work_order_service.py tests/services/test_work_order_service.py` -> 33 passed。
  - 静态：`ruff check ...`、`python -m py_compile ...`、`git diff --check` 均通过。

## 2026-07-04 继续：台账对账 + APPR-04 第二个回填（紧急采购自动触发）

- 台账对账：并行会话已修但台账行滞后的 5 项同步为"已修待验"——PROD-05（齐套率口径）、PROD-09（ECN 状态机跳步）、PROD-10（采购转单闸门）、PROD-15（现场缺料断链）、APPR-15（发货款触发器），均引 PROJECT_NOTES 对应验证记录；PROJ-11/14"修复中"状态准确未动。
- APPR-04 第二个回填：PROD-15 做实解锁了前置——`auto_trigger_urgent_purchase_from_shortage_alerts` 移出 stub，接 `auto_trigger_urgent_purchase_for_alerts`（扫 CRITICAL/URGENT 缺料预警、按 related_po_no 去重、建 SUBMITTED 申请**进审批池**——自动化的是提单不是批准，人审仍是闸门）；调度解禁每日 7:30；异常返回 error 哨兵。
- 验证：红灯 3 项 → 绿灯回填套件 7 passed；P0-10 + j3 全套 95 passed（4 项失败为已证实的通知类既有测试债）；`import app.main` 通过。
- 缺料 3 件套至此回填 2/3；剩余：缺料日报（幽灵表需先定义写入口径）、维保计划（随 AS-14）。

## 2026-07-04 继续：功能审计 HR-17 修复（奖金审批主链路加固）

- 修复项：`HR-17`（同 SALES-01 性质），奖金审批端点任意登录用户可批、可批自己的奖金、任意状态可流转；Excel 分配表导入直 APPROVED 无审批人痕迹。
- 代码面：
  - `bonus/sales_calc.py` approve 端点：挂 `bonus:manage` 权限（PERM 小切口已建）；防自审（受益人审批自己的奖金 403）；状态前置（仅 CALCULATED 可流转，防重复审批/终态翻案）。
  - `bonus_distribution_service.create_calculation_from_team_allocation`：保留 APPROVED（发放前有财务/HR/总经理三方线下确认闸，见 validate_sheet_for_distribution），但补审批留痕（approved_by=发放操作人 + 时间 + "线下确认"意见）；调用方传 current_user.id。
- 验证：红灯 4 项 → 绿灯 `tests/unit/test_bonus_approval_gate.py` 4 passed；bonus 相关 6 套件 190 passed（11 项失败经 HEAD worktree 证实为 solution_engineer_bonus/resource_scheduling 既有测试债）；`import app.main` 通过。
- 残留：接统一审批引擎（多级审批链）待排期——当前单级审批+权限门+防自审已闭合审计判定的最大风险。

## 2026-07-04 继续：功能审计 APPR-04 首个回填（缺料预警任务接真引擎）

- 修复项：`APPR-04`（全局 P0#10）剩余的"业务回填"部分，首个回填 `generate_shortage_alerts`——PROD-02 修好的 SmartAlertEngine 一直没有调度消费方。
- 代码面：
  - 新增 `scheduled_tasks/shortage_tasks.py`：真任务调 `SmartAlertEngine.scan_and_alert()` 全量扫描（工单/BOM 需求 vs 库存+在途，CRITICAL/URGENT 自动生成处理方案）；success 返回生成数量，异常返回 error 哨兵（调度监控计失败并按 SLA 重试）。
  - `stub_tasks.py` 移除该任务存根与导出；包 `__init__` 改从真实模块导入（外部导入路径不变）。
  - `scheduler_config/shortage.py` 解禁该任务（每日 7:00）。
  - 测试口径更新：`test_p0_10` 改从任务包解析（回填后任务移出 stub 模块）；`test_j3` 的 stub 断言改为"必须已移出 stub"。
- 验证：红灯 4 项 → 绿灯 `tests/unit/test_shortage_alert_task_backfill.py` 4 passed；P0-10 全套 19 passed；`import app.main` 通过。`test_j3` 4 项通知类失败经 HEAD worktree 证实为并行会话域既有测试债。
- 剩余回填：紧急采购自动触发（依赖 PROD-15 做实）、缺料日报（ShortageDailyReport 幽灵表需先定义写入口径）、维保计划（随 AS-14）。

## 2026-07-04 继续：功能审计 PRE-17/18 修复（中文检索短期方案，详#16）

- 修复项：`PRE-17`（"语义搜索"实为字符哈希/Jaccard）+ `PRE-18`（相似案例 equipment_type 精确匹配、空值互配）。前置勘察：百炼 Coding Plan 端点 `/embeddings` 实测 404——真向量方案需标准百炼密钥，中期再升级（ROADMAP F4）。
- 代码面：
  - 新增 `app/utils/text_similarity.py`：中文字符 bigram + 英文词元的计数向量余弦相似度；`stable_token_hash`（md5 基）替代内建哈希。
  - `presale_ai_service._calculate_similarity` 回退：空格 Jaccard（中文恒 0）→ bigram 余弦。
  - `presale_ai_knowledge_service._generate_embedding` 哈希回退：单字符+内建 hash() → bigram+稳定哈希。**顺带修隐藏 bug**：内建 hash() 进程级随机化，重启后存量向量与新查询必然失配（等于每次重启知识库检索清零）。
  - `similar_cases`：双向 LIKE 粗召回（FCT vs FCT测试 词表分裂容错）+ bigram 相似度精排（WON +0.1 加权，阈值 0.15），空设备类型不再 ''='' 全库互配，返回带 similarity 分。
- 验证：红灯 4 项 → 绿灯 `tests/unit/test_text_similarity_retrieval.py` 4 passed；presale 桥接/mock 守卫回归 11 passed；schemas+技术评估回归 105 passed；`import app.main` 通过。

## 2026-07-04 继续：功能审计 SALES-13 修复（智能报价假实现收口）

- 修复项：`SALES-13`，intelligent_quote.py 整文件硬编码（历史价"宁德时代320万"、竞品、最优价、自动折扣、赢单率全常量）；唯一真实消费方是报价编辑器侧栏的 historical-prices。
- 后端：
  - `historical-prices` 做实：WON 商机 × 已签合同真实成交价（equipment_type/商机名模糊匹配 + 行业/±30% 金额过滤），查无匹配空列表宁缺毋假；响应兼容侧栏旧结构（historical_prices/matched_count/average_price）。
  - 其余 5 端点（竞品录入/对比、最优价、自动折扣、赢单率单个+批量——赢单率原实现所有商机同分）501 下架，detail 指引真实替代（商机页 AI 报价估算/三档报价）。
- 前端：
  - `/sales/intelligent-quote`（整页假）与 `/sales/win-rate-prediction`（整页本地常量、零 API 调用）路由摘除；SalesFunnel 赢单率表的眼睛按钮改跳商机详情（有真实 AI 赢单分析卡）。
  - 旧页面组件文件保留但无路由入口（同 MISC-01 处理惯例）。
- 验证：红灯 3 项 → 绿灯 `tests/unit/test_intelligent_quote_stopgap.py` 3 passed（真数据/空态/501×6）；前端 sidebar+路由回归 35 passed；`npm run build`、`import app.main` 通过。

## 2026-07-04 继续：功能审计 SALES-12 修复（报价转合同前端入口）

- 修复项：`SALES-12`（北极星项），后端 `POST /sales/contracts/from-quote`（自动带出客户/商机/金额/当前版本 + G3 验证）一直齐备，前端零入口——销售建合同要手抄金额和版本 ID。
- 代码面：
  - `services/api/sales.js` contractApi 补 `fromQuote`。
  - `QuoteDetailDialog.jsx`：APPROVED/ACCEPTED 报价显示"转合同"按钮，一键调 from-quote；成功展示合同编码；G3 拦截（400）把缺口信息弹给人（不静默、不自动跳过）。
- 验证：红灯 2 项 → 绿灯组件测试 3 passed（含 G3 拦截展示）；QuoteCreateEdit 回归 2 passed；`npm run build` 通过。
- 至此北极星链路（线索→商机→报价→合同）的两处断链（SALES-11/12）全部接通：每一跳都数据自动带出、闸门默认生效、绕门须人工留痕。

## 2026-07-04 继续：功能审计 SALES-11 修复（线索转商机承接 + G1 默认走门）

- 修复项：`SALES-11`（北极星项），转商机丢字段（LeadRequirementDetail 里已录的对象/节拍/接口/验收/安全全部丢弃）+ 前端 LeadManagement 写死 skip_validation=true 默认绕 G1。
- 后端 `leads/actions.py`：
  - 新增 `_carry_over_lead_detail`：转商机自动承接线索需求详情到 opportunity_requirements（product_object/ct_seconds/interface_desc(通讯协议+接口类型)/acceptance_criteria(依据+方式)/safety_requirement/site_constraints(环境+占地+现场规范)）；显式 requirement_data 优先，承接只补空位；JSON 数组字段拍平为顿号串。
  - 商机侧承接 requirement_maturity/acceptance_basis/delivery_window（期望交付日期）。
- 前端 `LeadManagement.jsx`：默认 skip_validation=false 走 G1；400 时把缺口清单展示给人，由人确认"带缺口转换"（gate_status=PENDING 待补）——绕门从默认行为变成显式人工决策留痕。
- 验证：红灯 2 项（承接/显式优先）→ 绿灯 `tests/unit/test_lead_convert_carryover.py` 2 passed；`tests/api/test_sales.py` 回归仅剩已知签署门禁测试债 2 项；LeadDetail 前端回归 1 passed；eslint + `npm run build` 通过。

## 2026-07-04 继续：功能审计 RPT-07 修复（template_report 三套实现收敛）

- 修复项：`RPT-07`，template_report 同时存在旧根服务 `app/services/template_report_service.py`、新核心 `app/services/template_report/core.py`、统一框架 adapter 三套；adapter 还从 `app.services.template_report import template_report_service` 导入一个不存在的符号，直跑会 ImportError。
- 根因：旧服务早期内置了一套 `_generate_*` 分发，后续新增了 `TemplateReportCore` 和 `TemplateReportDataService`，但 adapter 没切到新核心；`app/services/template_report/` 目录也没有兼容导出。
- 改动：
  - `app/services/report_framework/adapters/template.py`：新增 `template_report_service` facade，实际调用 `TemplateReportCore.generate_from_template()`；移除函数内断链 import。
  - `app/services/template_report_service.py`：改成旧入口兼容 wrapper，不再保留第二套 `_generate_*` 逻辑。
  - `app/services/template_report/__init__.py`：新增懒加载代理，保留旧 `app.services.template_report.template_report_service` 路径。
  - `app/services/template_report/core.py`：补 `__init__(db)` 兼容旧实例化方式，并将 mixin imports 提到模块级。
  - 新增 `tests/unit/test_template_report_rpt07.py`，覆盖 adapter 不再断链、旧根服务只转发到 core。
- 验证：
  - 红灯：`pytest -q tests/unit/test_template_report_rpt07.py` -> 2 failed，adapter ImportError，旧根服务返回自己的空结构。
  - 绿灯：同命令 -> 2 passed。
  - 相邻回归：`pytest -q tests/unit/test_template_report_rpt07.py tests/unit/test_template_report_adapter.py tests/unit/test_template_report_data_service.py tests/unit/test_template_report_core.py tests/unit/test_template_report_service_coverage.py tests/unit/test_template_coverage.py` -> 34 passed。
  - 兼容回归：`PYTHONPATH=. pytest -q app/tests/services/report_framework/adapters/test_template.py` -> 6 passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-07` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 RPT-08 修复（PPT 生成器硬编码孤岛）

- 修复项：`RPT-08`，`app/services/ppt_generator/generator.py` 能真实产出 pptx，但主流程 100% 写死非标自动化营销 deck（15+ 年、1000+ 台、50+ 专利等），且项目内没有 API/服务调用方。
- 根因：PPT 生成器把“模板内容”和“生成引擎”写在同一个类里；无输入参数也会保存一份硬编码演示稿，测试也在保护旧硬编码章节。
- 改动：
  - `PresentationGenerator.generate()` 改为必须显式传入 `deck_spec`，未传直接 `ValueError`，避免无数据也生成演示内容。
  - 主生成流程改为数据驱动：支持 cover、toc、section、content、table；所有标题、正文、表头、行数据都来自 `deck_spec`。
  - 删除旧硬编码营销 deck 生成分支，`rg` 扫描确认生成器内不再残留旧“15+ 年/1000+ 台/50+ 专利/5000 亿美元”等文案。
  - 补齐 `app/services/ppt_generator/builders/*` 兼容导入路径；`BaseSlideBuilder` 支持无参初始化；`PresentationConfig` 增加 `fonts` 映射。
  - 重写 `tests/unit/test_ppt_generator.py` 为新数据驱动契约，并新增 `tests/unit/test_ppt_generator_rpt08.py`。
- 验证：
  - 红灯：`pytest -q tests/unit/test_ppt_generator_rpt08.py` -> 2 failed，无 spec 仍生成 demo，`deck_spec` 参数不存在。
  - 绿灯：同命令 -> 2 passed。
  - PPT 组合回归：`pytest -q tests/unit/test_ppt_generator*.py` -> 25 passed, 8 skipped。
  - 静态扫描：`rg -n "15\\+|1000\\+|50\\+|5000亿美元|黄金时代|智能驱动|精准交付|救火|掌控|非标自动化测试设备全生命周期" app/services/ppt_generator ...` -> no matches。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-08` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 RPT-01 修复（报表中心待实现桩）

- 修复项：`RPT-01`，报表中心配置和角色权限矩阵展示 `RISK_REPORT/COMPANY_MONTHLY/CUSTOM/SALES_FUNNEL/PROCUREMENT_ANALYSIS` 等未实现类型；用户直调生成时旧 router 返回空 `summary/details/charts` + `message=该报表类型待实现`，adapter/API 会当成功报表保存。
- 根因：公开配置、权限矩阵、旧 `ReportRouterMixin` 三处各自维护报表类型；router 的兜底不是 `error`，而 adapter 只会把 `error` 转成异常。
- 改动：
  - `app/services/report_data_generation/core.py`：新增 `IMPLEMENTED_REPORT_TYPE_DEFINITIONS/IMPLEMENTED_REPORT_TYPES`，并将角色权限矩阵收敛到真实可生成的 6 类报表。
  - `app/api/v1/endpoints/report_center/configs.py`：`/configs/types` 改为从真实已实现类型定义生成，不再展示 `RISK_REPORT/COMPANY_MONTHLY/CUSTOM`。
  - `app/services/report_data_generation/router.py`：未实现或未开放报表类型返回 `{"error": ...}`，不再返回空成功桩。
  - 新增 `tests/unit/test_report_center_rpt01.py`，覆盖权限矩阵、类型配置和直调 fail-closed。
- 验证：
  - 红灯：`pytest -q tests/unit/test_report_center_rpt01.py` -> 3 failed，缺少已实现类型中心定义，配置仍展示未实现类型，`RISK_REPORT` 返回空成功桩。
  - 绿灯：同命令 -> 3 passed。
  - 相邻回归：`pytest -q tests/unit/test_report_center_rpt01.py tests/unit/test_services_p5_coverage.py::TestReportRouterMixin tests/unit/test_services_p5_coverage.py::TestReportDataGenerationCore` -> 10 passed。
  - 备注：旧 `app/tests/services/report_framework/adapters/test_report_data_generation.py` 当前自身失败（`mock_db=` 参数错误、patch 不存在的 `ReportRouterMixin` 模块符号），未进入本次业务断言。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-01` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 RPT-14 修复（成本看板图表配置）

- 修复项：`RPT-14`，成本看板 `POST /dashboard/cost/chart-config` 只 echo 请求体，`GET /chart-config/{config_id}` 返回示例配置；同时读取路由排在 `GET /{project_id}` 后，存在被动态路由吞掉的风险。
- 根因：端点没有任何持久化模型；读取接口用硬编码示例配置冒充真实查询；静态路由顺序不符合 FastAPI 路由匹配要求。
- 改动：
  - 新增 `app/models/dashboard_chart_config.py`，保存图表类型、标题、轴字段、数据源、筛选条件、自定义指标和创建用户。
  - `app/schemas/dashboard.py` 的 `ChartConfigSchema` 增加可选 `id`。
  - `app/api/v1/endpoints/dashboard/cost_dashboard.py`：保存配置落库并返回 id；读取按 id 查询，不存在返回 404。
  - 将 `GET /chart-config/{config_id}` 移到 `GET /{project_id}` 之前。
  - 新增 `tests/unit/test_cost_dashboard_chart_config_rpt14.py`，覆盖保存-读取往返、缺失 404、静态路由优先于动态路由。
- 验证：
  - 红灯1：`pytest -q tests/unit/test_cost_dashboard_chart_config_rpt14.py` -> 2 failed，保存返回 dict 无 id，缺失 id 未 404。
  - 红灯2：补持久化后同命令 -> route order failed，`/chart-config/{config_id}` 在 `/{project_id}` 后。
  - 绿灯：同命令 -> 3 passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-14` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 RPT-04 修复（财务报表 demo 兜底）

- 修复项：`RPT-04`，财务报表 `monthly-trend/cost-analysis/project-profitability/cash-flow` 在无真实数据时返回硬编码 demo；`cost-analysis` 预算列用 `amount * 1.08` 编造。
- 根因：`app/api/v1/endpoints/finance_reports.py` 已接真实合同、发票、项目成本和财务成本，但空数据分支继续静默返回演示数据；成本预算没有读取预算表。
- 改动：
  - 删除四个端点的 demo fallback；无真实数据时返回空列表，让前端按空态处理。
  - `cost-analysis` 新增 `_budget_by_cost_category()`，汇总 `ProjectBudgetItem`，只读取 `ProjectBudget.status == APPROVED` 且 active 的预算明细。
  - 成本分析类目 now 取实际成本类目和预算类目的并集，预算-only 类目也返回；`variance = amount - budget`。
  - 新增 `tests/unit/test_finance_reports_rpt04.py`，覆盖空库不返回 demo、预算来自审批预算明细、不计 `PLAN` 成本。
- 验证：
  - 红灯：`pytest -q tests/unit/test_finance_reports_rpt04.py` -> 2 failed，月趋势返回 12 个月 demo，成本预算为 108 且缺人工预算行。
  - 绿灯：同命令 -> 2 passed。
  - 备注：`tests/api/test_financial_reports_api.py` 当前卡在本机 `TestClient`/`httpx` 不兼容：`Client.__init__() got an unexpected keyword argument 'app'`，未进入业务断言。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-04` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 RPT-03 修复（成本分析时薪硬编码）

- 修复项：`RPT-03`，`COST_ANALYSIS` 人工成本按总工时直接乘硬编码 100；同一工程师不同日期时薪变更、不同工程师不同配置都会被抹平。
- 根因：旧 `app/services/report_data_generation/analysis_reports.py` 和新 `app/services/report_framework/generators/analysis.py` 都没有接已有 `HourlyRateService`，而是各自保留 100 元默认口径。
- 改动：
  - 新增 `app/services/report_labor_cost.py`，按每条 `Timesheet.user_id + work_date` 读取 `HourlyRateService.get_user_hourly_rate()` 并汇总人工成本。
  - `report_data_generation` 旧入口和 `report_framework` 新生成器都改用共享 helper。
  - 新增 `tests/unit/test_analysis_reports_rpt03.py`，覆盖同一工程师 1 月 15 日前后不同配置、另一工程师不同配置，以及区间外工时不计入。
- 验证：
  - 红灯：`pytest -q tests/unit/test_analysis_reports_rpt03.py` -> 2 failed，两个入口均返回 600（6 小时 × 100），期望 760。
  - 绿灯：同命令 -> 2 passed。
  - 相邻回归：`pytest -q tests/unit/test_analysis_reports.py tests/unit/test_services_p3_coverage.py::TestAnalysisReportGenerator tests/unit/test_services_p5_coverage.py::TestWorkloadAnalysisAdapter tests/unit/test_services_p5_coverage.py::TestReportDataGenerationAdapter` -> 14 passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-03` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 RPT-02 修复（项目月报成本恒 0）

- 修复项：`RPT-02`，`PROJECT_MONTHLY` 项目月报 `cost.actual_cost/cost_variance/cost_variance_percent` 写死 0，导致有成本记录的项目月报仍显示无实际成本。
- 根因：`app/services/report_data_generation/project_reports.py` 已有项目月报结构，但没有接项目成本数据源；真实成本分散在自动归集 `ProjectCost` 和财务手录 `FinancialProjectCost`。
- 改动：
  - `app/services/report_data_generation/project_reports.py`：新增 `_sum_project_actual_cost()`。
  - 月报成本汇总 now 按报表期间汇总 `ProjectCost` 的 ACTUAL 口径成本与 `FinancialProjectCost` 金额。
  - `cost_variance` 改为 `planned_cost - actual_cost`，`cost_variance_percent` 按预算差额率计算。
  - 新增 `tests/unit/test_project_monthly_report_rpt02.py`，覆盖同项目区间内自动成本 200 + 财务成本 150，区间外成本不计入，月报实际成本应为 350。
- 验证：
  - 红灯：`pytest -q tests/unit/test_project_monthly_report_rpt02.py` -> failed，`actual_cost` 仍为 0。
  - 绿灯：同命令 -> 1 passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-02` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 RPT-13 修复（采购看板节省金额）

- 修复项：`RPT-13`，统一工作台采购统计卡“节省金额”在后端 `dashboard/stats.py` 明确硬编码为 0，前端只显示后端返回值，导致采购看板恒 `¥0`。
- 根因：后端没有把采购申请的预估金额与来源采购订单的实际金额做关联比较；`StatsCard` 的前端默认 `¥0` 只是 API 不可用兜底，不是真实数据源。
- 改动：
  - `app/api/v1/endpoints/dashboard/stats.py`：新增采购节省额聚合，按 `PurchaseRequest.total_amount - 关联 PurchaseOrder 实际金额` 计算正差。
  - 同一采购申请先聚合订单金额，避免拆单重复计算申请金额；订单实际金额优先用 `amount_with_tax`，含税金额为 0 时回退 `total_amount`。
  - 新增 `tests/unit/test_dashboard_procurement_stats_rpt13.py`，用真实 SQLite 测采购申请 1000、关联订单 700 时卡片显示 `¥300`。
- 验证：
  - 红灯：`pytest -q tests/unit/test_dashboard_procurement_stats_rpt13.py` -> failed，节省金额仍返回 `¥0`。
  - 绿灯：同命令 -> 1 passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-13` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 RPT-12 修复（驾驶舱数据集恒空）

- 修复项：`RPT-12`，决策驾驶舱 `costData/salesFunnelData` 使用无 setter 的 `useState([])`，销售漏斗和成本构成恒空；`getHealthDistribution()` 被调用但结果直接丢弃。
- 改动：
  - `frontend/src/pages/executive-dashboard/useExecutiveDashboard.js`：`costData/salesFunnelData` 补 setter。
  - 健康分布接口结果写入 `healthData` 并复用健康指数计算。
  - 成本数据由 executive summary 的 `total_budget/total_actual_cost` 生成“已用预算/剩余预算/超预算”结构。
  - 销售漏斗接 `salesStatisticsApi.funnel()`，归一化为 FunnelChart 需要的 `stage/value`。
  - `frontend/src/pages/executive-dashboard/useExecutiveDashboard.test.js` 新增 RPT-12 契约测试。
- 验证：
  - 红灯：`npm run test:run -- src/pages/executive-dashboard/useExecutiveDashboard.test.js` -> failed，`healthData` 仍为 `{}`。
  - 绿灯：同命令 -> 3 passed。
  - 静态检查：`npx eslint src/pages/executive-dashboard/useExecutiveDashboard.js src/pages/executive-dashboard/useExecutiveDashboard.test.js` passed；相关 diff whitespace check passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-12` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 RPT-10 修复（驾驶舱 KPI 字段绑定）

- 修复项：`RPT-10`，决策驾驶舱 KPI 卡读取后端 executive summary 不存在的 `project_growth/on_time_delivery_rate/delivery_rate_change`，导致活跃项目变化和交付准时率稳定显示假 0。
- 根因：`delivery-rate` 接口已单独请求并返回真实 `on_time_rate/on_time_projects/total_projects`，但前端归一化时丢掉分子/分母，且 `kpiCards` memo 不依赖 `deliveryData`。
- 改动：
  - `frontend/src/pages/executive-dashboard/useExecutiveDashboard.js`：新增交付数据归一化，保留 `rate/on_time_projects/total_projects`。
  - 交付准时率 KPI 优先读 summary 显式字段，否则读最新 `deliveryData`；无环比时显示 `按期/总数`。
  - 活跃项目 KPI 无 `project_growth` 时显示项目总数，不再假写“较上月 0%”。
  - `kpiCards` memo 依赖补 `deliveryData`。
  - `frontend/src/pages/executive-dashboard/useExecutiveDashboard.test.js` 新增 RPT-10 契约测试。
- 验证：
  - 红灯：`npm run test:run -- src/pages/executive-dashboard/useExecutiveDashboard.test.js` -> failed，交付数据只剩 `{ month, rate }`，分子/分母丢失。
  - 绿灯：同命令 -> 2 passed。
  - 静态检查：`npx eslint src/pages/executive-dashboard/useExecutiveDashboard.js src/pages/executive-dashboard/useExecutiveDashboard.test.js` passed；相关 diff whitespace check passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-10` 已改为 `已验证`。

## 2026-07-03 继续：功能审计 RPT-11 修复（驾驶舱 KPI 前端封顶）

- 修复项：`RPT-11`，决策驾驶舱前端把真实营收/利润用 `Math.min(..., 年目标 * 0.3)` 裁成 Q1 口径；合同额超过 4800 万时被截断，同时“合同额-实际成本”被标成“净利润”。
- 改动：
  - `frontend/src/pages/executive-dashboard/useExecutiveDashboard.js`：移除营收/利润 30% 封顶，达成率按真实值计算。
  - 利润卡标题改为“项目毛利”，口径为后端显式 `gross_profit/total_gross_profit/profit`，否则用 `total_contract_amount - total_actual_cost` 兜底。
  - 新增 `frontend/src/pages/executive-dashboard/useExecutiveDashboard.test.js`，覆盖 8000 万合同额不被裁剪、6000 万毛利不误标净利润。
- 验证：
  - 红灯：`npm run test:run -- src/pages/executive-dashboard/useExecutiveDashboard.test.js` -> failed，营收显示 `¥48,000,000.00` 而非 `¥80,000,000.00`。
  - 绿灯：同命令 -> 1 passed。
  - 静态检查：`npx eslint src/pages/executive-dashboard/useExecutiveDashboard.js src/pages/executive-dashboard/useExecutiveDashboard.test.js` passed；相关 diff whitespace check passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-11` 已改为 `已验证`。

## 2026-07-03 继续：功能审计 RPT-09 修复（统一工作台统计卡契约）

- 修复项：`RPT-09`，8 个旧工作台 adapter 用 `DashboardStatCard(label=...)`，但 schema 必填 `title`；统一入口吞掉单模块异常后表现为统计卡恒空。
- 改动：
  - `app/schemas/dashboard.py`：`DashboardStatCard.title` 兼容 `title`/`label` 两种输入，输出字段仍统一为 `title`。
  - 同步保留旧 adapter 已传入的 `icon`/`color` 字段，避免统计卡样式信息被 schema 丢弃。
  - 新增 `tests/unit/test_dashboard_stat_card_rpt09.py`，覆盖直接 `label=` 构造和真实 Presales adapter stats。
- 验证：
  - 红灯：`pytest tests/unit/test_dashboard_stat_card_rpt09.py -q` -> 2 failed，`title Field required`。
  - 绿灯：同命令 -> 2 passed。
  - 相邻回归：`tests/unit/test_dashboard_stat_card_rpt09.py tests/unit/test_dashboard_adapter.py` -> 17 passed。
  - 8 个旧 `label=` adapter 空库 smoke：presales/hr/production/pmo/business_support/shortage/strategy/assembly_kit 均可产出 `title`。
  - 静态检查：相关文件 `py_compile` passed；`ruff check` passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-09` 已改为 `已验证`。

## 2026-07-03 继续：功能审计 RPT-06 修复（报表中心 xlsx 明细导出）

- 修复项：`RPT-06`，旧报表导出分支把 `details` 塞进 table section 的 `source` 字段，而 `ExcelRenderer` 只读取 `data/columns`，导致 xlsx 明细恒写“无数据”。
- 额外发现：同函数 CSV 分支局部 `from datetime import datetime` 让 xlsx 分支更新 `exported_at` 时命中 `UnboundLocalError` 500。
- 改动：
  - `app/api/v1/endpoints/report_center/generate/export.py`：抽出 `_build_legacy_report_sections()` / `_table_section()` / `_table_columns()`，xlsx/pdf 旧导出分支统一生成 `data + columns`。
  - 移除 CSV 分支局部 `datetime` 导入，复用文件顶部导入。
  - 新增 `tests/unit/test_report_center_export_rpt06.py`，用真实 `ExcelRenderer` 生成 xlsx 并用 openpyxl 验证明细表头和数据行。
- 验证：
  - 红灯1：`pytest tests/unit/test_report_center_export_rpt06.py -q` -> 500，`cannot access local variable 'datetime'...`。
  - 红灯2：修复 datetime 后同命令 -> failed，xlsx 中仍有“无数据”。
  - 绿灯：同命令 -> 1 passed。
  - 报表相邻回归：`tests/unit/test_report_center_export_rpt06.py tests/unit/test_excel_renderer_coverage.py tests/unit/test_report_engine_n3.py` -> 49 passed。
  - 静态检查：相关文件 `py_compile` passed；`ruff check` passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `RPT-06` 已改为 `已验证`。

## 2026-07-03 继续：功能审计 HR-01 修复（员工 Excel 导入端点）

- 修复项：`HR-01`，`POST /org/employees/import` 运行时从 `employee_import_service` 导入不存在的 `validate_excel_file`，上传入口会在服务层真正处理前崩溃。
- 改动：
  - `app/services/employee_import_service.py`：新增 `validate_excel_file()`，仅允许 `.xlsx/.xls`，非 Excel 返回 HTTP 400。
  - `app/utils/common.py`：`clean_name("")`/`"/"`/`"NaN"` 恢复清洗为 `None`，避免空姓名行继续进入员工创建逻辑。
  - `tests/unit/test_employee_import_service.py`：新增文件类型校验契约，并恢复员工导入服务整文件通过。
  - `tests/api/test_organization.py`：新增非 Excel 上传 API 合约，确认返回 400 而不是运行时导入崩溃。
- 验证：
  - 红灯：`pytest tests/unit/test_employee_import_service.py -q` -> collection error，`cannot import name 'validate_excel_file'`。
  - 绿灯：`tests/unit/test_employee_import_service.py` -> 24 passed。
  - API 合约：`tests/api/test_organization.py::TestEmployeeCRUD::test_import_employees_rejects_non_excel_file` -> passed。
  - 组合回归：`tests/unit/test_employee_import_service.py tests/api/test_organization.py::TestEmployeeCRUD::test_import_employees_rejects_non_excel_file` -> 25 passed。
  - 静态检查：相关文件 `py_compile` passed；`ruff check` passed。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `HR-01` 已改为 `已验证`。

## 2026-07-03 继续：功能审计 APPR-22 收口（第二调度器监控）

- 修复项：`APPR-22` 子项④，`app/main.py` 启动了第二个 `app.scheduler_progress` 调度器，但监控面只看 `app.utils.scheduler` 主调度器；进度预测 job 执行不写 `scheduler_metrics`，`/scheduler/status` 与 `/scheduler/jobs` 也看不到它。
- 改动：
  - `app/scheduler_progress.py` 注册 `progress_auto_processing_daily` 时包 `_wrap_progress_job_callable()`，成功写 `record_job_success`，异常写 `record_job_failure` 后原样抛出。
  - `app/api/v1/endpoints/scheduler/status.py` 汇总主调度器和 progress 调度器的 `running/job_count/jobs`，jobs 输出增加 `scheduler` 字段标识来源。
  - 新增 `tests/unit/test_scheduler_progress_metrics_appr22.py`，覆盖 success/failure metrics 以及 status/jobs 两个监控接口。
- 验证：
  - 红灯：`pytest tests/unit/test_scheduler_progress_metrics_appr22.py -q` -> 先 2 failed（metrics 不记录），补状态契约后再 2 failed（job_count/jobs 只有主调度器）。
  - 绿灯：同命令 -> 4 passed。
  - 调度相邻回归：`tests/unit/test_scheduler_progress_metrics_appr22.py tests/unit/test_scheduler_utils.py tests/unit/test_scheduler_l4.py tests/unit/test_scheduler.py tests/unit/test_scheduler_unit.py tests/unit/test_scheduler_metrics_utils.py` -> 74 passed。
  - APPR-22 组合回归：`tests/unit/test_ai_job_recovery.py tests/unit/test_backup_scheduler_appr22.py tests/unit/test_scheduler_progress_metrics_appr22.py tests/unit/test_scheduler_utils.py` -> 30 passed。
  - 静态检查：`py_compile` 相关文件 passed；`ruff check` passed。
- 台账：`APPR-22` 子项①/②/③/④/⑤全部已动态回归，主表从 `修复中` 改为 `已验证`。

## 2026-07-03 继续：功能审计 SALES-08 修复（目标 actual_value 实时回填）

- 修复项：`SALES-08`，目标列表接口 `# TODO 实现目标绩效计算逻辑`——`actual_value` 取不存在的模型列恒 0，达成率恒 0；而 `SalesTeamService.calculate_target_performance`（SALES-15 补的）已具备完整口径，又是"算法真接线假"。
- 代码面：`sales/targets.py` 列表接口接线 `calculate_target_performance` 实时计算。口径：LEAD_COUNT/OPPORTUNITY_COUNT 按 owner 计数、CONTRACT_AMOUNT 按合同负责人金额求和、COLLECTION_AMOUNT 按发票实收；达成率 = actual/target*100；团队/部门级目标暂无归集口径返回 0（备注在台账）。
- 验证：红灯（actual 恒 0）→ 绿灯 `tests/unit/test_sales_target_actuals.py` 1 passed；团队服务回归 39 passed + p7 覆盖 23 passed；py_compile 通过。
- 联动：ForecastDashboard（SALES-07 刚修）读的就是该列表的 actual_value——至此目标页"目标-实际-预测"三个数字全部来自真实数据。

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

## 2026-07-03 继续：功能审计 APPR-22 小切口（自动数据库备份）

- 修复项：`APPR-22` 子项②，系统有 `BackupService` 和 shell 脚本，但没有 scheduler 任务自动执行；且默认运行库是 SQLite（`data/app.db`），旧 `backup_database.sh` 是 MySQL/mysqldump 口径，直接接调度也不会产生真实可用备份。
- 改动：
  - `BackupService.create_backup("database")` 在 SQLite URL 下直接用 Python `sqlite3.iterdump()` 生成 `pms_YYYYmmdd_HHMMSS.sql.gz`，并写同名 `.md5`。
  - `sqlite:///:memory:` 测试环境保留旧脚本回退，避免破坏既有脚本包装测试。
  - 新增 `app/utils/scheduled_tasks/backup_tasks.py::daily_database_backup_task()`。
  - `scheduler_config/other.py` 新增 enabled 任务 `daily_database_backup`，每天 2:30 执行。
  - `scheduled_tasks/__init__.py` 导出/注册 `daily_database_backup_task`。
- 验证：
  - 红灯：`pytest tests/unit/test_backup_scheduler_appr22.py -q` -> 2 failed，SQLite 备份走旧脚本失败，调度任务不存在。
  - 绿灯：同命令 -> 2 passed。
  - 备份服务回归：`app/tests/services/backup/test_backup_service.py tests/unit/test_backup_service_deep.py tests/unit/test_backup_scheduler_appr22.py` -> 35 passed。
  - 调度相邻回归：`tests/unit/test_scheduler_utils.py tests/audit_p0/test_p0_10_stub_tasks.py tests/unit/test_j3_scheduled_tasks.py::TestStubTasks tests/unit/test_backup_scheduler_appr22.py` -> 49 passed。
  - 静态检查：相关文件 `py_compile` passed；`ruff check` passed。
- 台账：`APPR-22` 子项②已标已回归；后续子项④“第二调度器不进监控”已在 APPR-22 收口小切口完成。

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
- 台账：`APPR-22` 从 `待修` 改为 `修复中`；子项①/③/⑤已标已回归，②备份自动执行、④第二调度器监控已在后续小切口完成。

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
- 残留：本项只修 ECN job 注册路径；`APPR-22` 里的导入失败可见化、备份自动执行、第二调度器监控已在后续小切口收口。

## 2026-07-03 继续：功能审计 MISC-03 修复（预警超时升级扫描）

- 修复项：`MISC-03`，`check_alert_timeout_escalation()` 用 `not AlertRecord.is_escalated` 构造 SQLAlchemy 查询，实际会把列对象变成 Python `False`，导致过滤条件短路，升级扫描永远查不到待升级预警。
- 改动：
  - `app/utils/alert_escalation_task.py` 改为 SQL 表达式：`AlertRecord.is_escalated.is_(False)` 或历史 NULL。
  - 扫描状态纳入 `OPEN/PENDING/ACKNOWLEDGED/PROCESSING`，和 APPR-17 的 `PENDING→OPEN` 状态流转对齐。
  - `tests/unit/test_utils_missing.py` 增加查询契约，锁定不能出现裸 `False` 条件、必须扫描 `OPEN`；旧升级用例改为验证超时 INFO 预警会升级到 WARNING 并发送升级通知。
- 验证：
  - 红灯：`pytest tests/unit/test_utils_missing.py::TestAlertEscalationTask::test_check_alert_timeout_escalation_query_targets_open_unescalated_alerts tests/unit/test_utils_missing.py::TestAlertEscalationTask::test_check_alert_timeout_escalation -q` -> 1 failed，捕获到过滤条件 `[status IN (...), False]`。
  - 绿灯：同命令 -> 2 passed；`pytest tests/unit/test_utils_missing.py::TestAlertEscalationTask -q` -> 6 passed。
- 残留：本项只修升级任务自身查询和状态覆盖；订阅默认接收人与 webhook 渠道问题仍归 `AS-25`，`APPR-22` 备份/调度监控残项已在后续小切口收口。

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
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`PROJ-06` 标为 `已验证`；当时全局 P0#8 标清 `PROJ-20` 仍待修，避免把变更审批回基线一起误判完成（`PROJ-20` 已在 2026-07-04 后续段落修复）。
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
  - `FUNCTIONAL_AUDIT_TRACKER.md`：`AS-19` 标为 `已验证`；当时备注的 `AS-09` 售后质保表缺失已于 2026-07-04 收口验证，真实库迁移脚本仍待发布/执行。
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

## 2026-07-04 继续：RPT-05 / SALES-17 含税与不含税口径

- 修复目标：报价、合同、财务报表不能再把不含税金额、税额、含税金额混在同一个总额里；报表必须显式输出口径。
- 红测：
  - `tests/unit/test_finance_reports_rpt05.py::test_quote_creation_persists_explicit_tax_breakdown` 先失败：`QuoteVersion` 无 `amount_without_tax`。
  - `tests/unit/test_finance_reports_rpt05.py::test_contract_from_quote_inherits_quote_tax_breakdown` 先失败：`QuoteVersion/Contract` 不接受税口径字段。
  - `tests/unit/test_finance_reports_rpt05.py::test_finance_reports_return_net_tax_and_gross_amounts` 先失败：财务报表无不含税/税额/含税拆分。
- 代码面：
  - `QuoteVersion`、`Contract` 新增 `amount_without_tax/tax_rate/tax_amount/amount_with_tax`。
  - `app/services/sales/tax_basis.py` 统一金额口径推导；报价创建、报价版本创建、报价详情/列表返回均接入。
  - 合同轻量入口支持税字段；从报价生成合同时继承报价版本税口径，旧 `total_price/total_amount` 保持兼容总价。
  - `finance_reports.py` 四个端点改为 net/tax/gross 三元聚合：月趋势、成本分析、项目盈利、现金流都输出不含税、税额、含税字段。
  - 新增迁移脚本 `migrations/versions/20260704_add_sales_tax_basis.py`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_finance_reports_rpt05.py` 通过（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_finance_reports_rpt04.py tests/unit/test_finance_reports_rpt05.py` 通过（5 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_finance_reports_rpt05.py tests/unit/test_finance_reports_rpt04.py tests/unit/test_sales_forecast_wiring.py tests/unit/models/sales/test_contract_model.py` 通过（20 个用例）。
  - `python -m py_compile ...` 覆盖本次改动文件，通过。
  - `ruff check ...` 覆盖本次改动文件，通过。
  - API `TestClient` 类测试当前被本地依赖版本挡住：`Client.__init__() got an unexpected keyword argument 'app'`，不是本次代码路径失败；本轮以直接函数和模型/报表单测完成回归。

## 2026-07-04 继续：ADMIN-18 合同附件任意文件读取

- 修复目标：合同附件下载不能直接信任 DB 中的 `file_path`；绝对路径和路径穿越不能读出上传目录外文件。
- 红测：
  - `tests/unit/test_contract_attachment_security_admin18.py::test_contract_attachment_download_rejects_absolute_path_outside_upload_dir` 先失败：登记 `/tmp/.../secret.txt` 可被 `FileResponse` 返回。
  - `tests/unit/test_contract_attachment_security_admin18.py::test_contract_attachment_download_allows_file_inside_upload_dir` 先失败：合法相对路径未映射到 `UPLOAD_DIR`。
- 代码面：
  - 新增 `app/api/v1/endpoints/sales/contracts/attachment_security.py`，统一解析附件路径：相对路径落到 `settings.UPLOAD_DIR`，绝对路径必须位于上传根目录内。
  - `enhanced_attachments.py` 和老 `enhanced.py` 两个下载入口都走共享 resolver；非法路径返回 403，缺文件返回 404。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_contract_attachment_security_admin18.py` 通过（4 个用例，覆盖新旧两个入口）。
  - `python -m py_compile app/api/v1/endpoints/sales/contracts/attachment_security.py app/api/v1/endpoints/sales/contracts/enhanced_attachments.py app/api/v1/endpoints/sales/contracts/enhanced.py tests/unit/test_contract_attachment_security_admin18.py` 通过。
  - `ruff check app/api/v1/endpoints/sales/contracts/attachment_security.py app/api/v1/endpoints/sales/contracts/enhanced_attachments.py app/api/v1/endpoints/sales/contracts/enhanced.py tests/unit/test_contract_attachment_security_admin18.py` 通过。

## 2026-07-04 继续：ADMIN-01/02/03 备份 API、恢复与 SQLite 脚本

- 修复目标：备份 API 不能再是自 import 占位 router；产品内必须有可调用 restore；数据库备份/校验/恢复脚本必须对齐当前 SQLite 数据库，而不是 MySQL/mysqldump。
- 红测：
  - `tests/unit/test_backup_admin01_03.py::test_backup_router_exposes_real_operations_not_placeholder` 先失败：router 只有 `/` 占位路径。
  - `tests/unit/test_backup_admin01_03.py::test_restore_backup_replaces_sqlite_database_and_keeps_pre_restore_copy` 先失败：`BackupService` 无 `restore_backup`。
  - `tests/unit/test_backup_admin01_03.py::test_database_backup_scripts_use_sqlite_backup_verify_and_restore` 先失败：`backup_database.sh` 要求 `MYSQL_PASSWORD`。
- 代码面：
  - `app/api/v1/endpoints/backup.py` 改为真实 FastAPI router，提供列表、创建、数据库备份、验证、恢复、清理过期备份、统计端点。
  - `BackupService.restore_backup()` 支持 SQLite gzip SQL dump 恢复；恢复必须 `confirm=True`，恢复前自动生成 `before_restore_*.sql.gz`。
  - `backup_database.sh`、`verify_backup.sh`、`restore_database.sh` 改为读取 `DATABASE_URL=sqlite:///...`，用 Python sqlite3 生成/加载 gzip SQL dump，不再依赖 MySQL 客户端。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_backup_admin01_03.py` 先红后绿（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_backup_admin01_03.py tests/unit/test_backup_scheduler_appr22.py tests/unit/test_backup_service.py tests/unit/test_batch2_backup_service.py tests/unit/test_backup_service_coverage.py tests/unit/test_backup_service_deep.py app/tests/services/backup/test_backup_service.py` 通过（95 个用例）。
  - `python -m py_compile app/api/v1/endpoints/backup.py app/services/backup_service.py tests/unit/test_backup_admin01_03.py` 通过。
  - `ruff check app/api/v1/endpoints/backup.py app/services/backup_service.py tests/unit/test_backup_admin01_03.py` 通过。
  - `rg -n "mysql|mysqldump|MYSQL_PASSWORD|DB_HOST|DB_PORT|MySQL" scripts/backup_database.sh scripts/restore_database.sh scripts/verify_backup.sh || true` 无命中。

## 2026-07-04 继续：ADMIN-13/14 数据导入假失败与错误明细

- 修复目标：`/data-import-export/upload` 不能先提交导入数据、再因 `DataImportTask` 字段错配报失败；部分失败时错误行必须落任务表并返回给前端。
- 红测：
  - `tests/unit/test_data_import_upload_admin13_14.py::test_upload_import_persists_real_task_fields_and_returns_failed_rows` 先失败：`DataImportTask(task_code=...)` 抛出 `invalid keyword argument`，且失败发生在导入结果提交之后。
- 代码面：
  - `import_upload.py` 删除导入后提前 `db.commit()`，导入数据和导入任务记录改为同一事务提交。
  - 任务记录改用真实字段：`task_no/import_type/target_table/file_name/file_size/status/total_rows/success_rows/failed_rows/validation_errors/imported_by/started_at/completed_at/error_message`。
  - `ImportUploadResponse` 增加 `imported_count/updated_count/failed_count/failed_rows`，兼容旧的 `task_id/task_code/status/message`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_data_import_upload_admin13_14.py` 先红后绿（1 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_data_import_upload_admin13_14.py tests/unit/test_schemas_p1_coverage.py tests/unit/test_unified_import/test_task_importer.py tests/unit/test_task_importer.py app/tests/services/unified_import/test_task_importer.py` 通过（154 passed，1 skipped）。
  - `python -m py_compile app/api/v1/endpoints/data_import_export/import_upload.py app/schemas/data_import_export.py tests/unit/test_data_import_upload_admin13_14.py` 通过。
  - `ruff check app/api/v1/endpoints/data_import_export/import_upload.py app/schemas/data_import_export.py tests/unit/test_data_import_upload_admin13_14.py` 通过。

## 2026-07-04 继续：ADMIN-09 健康检查依赖探测

- 修复目标：`/health` 与 `/api/health` 不能再只返回常量；至少要反映数据库、调度器、Redis 的当前状态。
- 红测：
  - `tests/unit/test_health_check_admin09.py::test_root_health_reports_degraded_when_database_probe_fails` 先失败：数据库探测被 mock 为 down 时 `/health` 仍返回 `ok` 且没有 `dependencies`。
  - `tests/unit/test_health_check_admin09.py::test_api_health_reports_healthy_when_required_dependencies_are_up` 先失败：`/api/health` 只有 `status/timestamp`，没有依赖详情。
- 代码面：
  - `app/main.py` 新增 `_probe_database()`、`_probe_scheduler()`、`_probe_redis()` 与 `_build_health_payload()`。
  - 数据库使用 `SELECT 1` 探测；调度器返回 running/job_count；Redis 未配置返回 `disabled`，配置后异常返回 `down`。
  - `/health` 保持成功态 `ok`，异常态 `degraded`；`/api/health` 保持成功态 `healthy`，异常态 `degraded`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_health_check_admin09.py` 先红后绿（2 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_health_check_admin09.py tests/unit/test_data_import_upload_admin13_14.py tests/unit/test_backup_admin01_03.py` 通过（6 个用例）。
  - `python -m py_compile app/main.py tests/unit/test_health_check_admin09.py` 通过。
  - `ruff check app/main.py tests/unit/test_health_check_admin09.py` 通过。

## 2026-07-04 继续：ADMIN-05/06 admin_stats 与系统统计

- 修复目标：`admin_stats.py` 不能再是 fallback 占位；`/admin/stats` 不能再返回 99.9% uptime、0 错误率、从未备份等硬编码指标。
- 红测：
  - `tests/unit/test_admin_stats_admin05_06.py::test_admin_stats_router_exposes_stats_route_not_placeholder` 先失败：router 只有 `/` 占位路径。
  - `tests/unit/test_admin_stats_admin05_06.py::test_collect_admin_stats_uses_runtime_counts_and_backup_metadata` 先失败：`admin_stats` 无 `BackupService/collect_admin_stats`。
  - `tests/unit/test_admin_stats_admin05_06.py::test_admin_compat_stats_delegates_to_same_runtime_collector` 先失败：兼容路由未复用共享采集器。
- 代码面：
  - `app/api/v1/endpoints/admin_stats.py` 改为真实 `/stats` 路由，并提供 `collect_admin_stats(db)`。
  - 统计字段保留旧契约，但来源改为运行时采集：用户、角色、权限、用户角色、登录尝试、权限审计、备份元数据、SQLite DB 文件体积、上传/备份目录体积、DB ping 响应耗时。
  - `admin_compat.py` 的 `/admin/stats` 复用同一采集器，避免两个 `/admin/stats` 口径分叉。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_admin_stats_admin05_06.py` 先红后绿（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_admin_stats_admin05_06.py tests/unit/test_health_check_admin09.py` 通过（5 个用例）。
  - `python -m py_compile app/api/v1/endpoints/admin_stats.py app/api/v1/endpoints/admin_compat.py tests/unit/test_admin_stats_admin05_06.py` 通过。
  - `ruff check app/api/v1/endpoints/admin_stats.py app/api/v1/endpoints/admin_compat.py tests/unit/test_admin_stats_admin05_06.py` 通过。

## 2026-07-04 继续：MISC-18 business_support 前端 API 404

- 修复目标：前端 `businessSupportApi` 调用的 `/business-support/...` 不能再因为后端裸挂 `business_support` 子路由而全部 404；dashboard/todos、投标、合同审核、回款催收路径要与前端契约对齐。
- 红测：
  - `tests/unit/test_business_support_prefix_misc18.py::test_business_support_frontend_routes_are_registered_under_expected_prefix` 先失败：`/business-support/dashboard`、`/business-support/bidding`、`/business-support/contract-review`、`/business-support/payment-reminder`、`/business-support/dashboard/todos` 等路径均缺失。
- 代码面：
  - `api.py` 将商务支持主路由统一挂到 `prefix="/business-support"`。
  - `business_support/__init__.py` 增加 `/contract-review` 与 `/payment-reminder` 前端兼容别名，保留旧 `/contracts` 与 `/payment-reminders`。
  - `dashboard.py` 将 active-contracts/active-bidding/performance 收口到 `/dashboard/...`，并新增 `/dashboard/todos`。
  - `contract_review.py` 增加前端需要的列表、详情、创建、更新 CRUD 形态，复用原合同审核创建/更新逻辑。
  - `payment_reminders.py` 增加详情和更新端点，复用现有列表/创建响应转换。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_business_support_prefix_misc18.py` 先红后绿（1 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/api.py app/api/v1/endpoints/business_support/__init__.py app/api/v1/endpoints/business_support/dashboard.py app/api/v1/endpoints/business_support/contract_review.py app/api/v1/endpoints/business_support/payment_reminders.py tests/unit/test_business_support_prefix_misc18.py` 通过。
  - `ruff check app/api/v1/api.py app/api/v1/endpoints/business_support/__init__.py app/api/v1/endpoints/business_support/dashboard.py app/api/v1/endpoints/business_support/contract_review.py app/api/v1/endpoints/business_support/payment_reminders.py tests/unit/test_business_support_prefix_misc18.py` 通过。
  - `git diff --check app/api/v1/api.py app/api/v1/endpoints/business_support/__init__.py app/api/v1/endpoints/business_support/dashboard.py app/api/v1/endpoints/business_support/contract_review.py app/api/v1/endpoints/business_support/payment_reminders.py tests/unit/test_business_support_prefix_misc18.py` 通过。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js` 通过（24 个用例）。
  - 相关扩展回归仍有既存阻塞：`tests/api/test_business_support_delivery_routes.py` 卡在本地 `TestClient` / `httpx` 版本不兼容（`Client.__init__() got an unexpected keyword argument 'app'`）；`tests/unit/test_business_support_auto.py tests/unit/test_business_support_helpers.py` 中 `generate_invoice_no` 旧方法名漂移失败，与本次路由修复无关。

## 2026-07-04 继续：ADMIN-12 项目缓存管理端点

- 修复目标：`/projects/cache/clear` 不能调用不存在的 `clear_all/invalidate_all_project_details/invalidate_user_cache`，也不能为了“清全部”改成会 `flushdb()` 的全库清理；前端传 `pattern` 参数时必须进入项目缓存白名单。
- 红测：
  - `tests/unit/test_projects_cache_admin12.py::test_clear_cache_default_clears_only_project_namespace` 先失败：默认清理走 `clear_all`，触发整库清理保护并返回 500。
  - `tests/unit/test_projects_cache_admin12.py::test_clear_cache_supports_frontend_pattern_param_with_allowlist` 先失败：endpoint 不接受前端 `pattern` 参数。
- 代码面：
  - `clear_cache()` 新增 `pattern` 兼容参数，`cache_type`/`pattern` 统一归一为项目缓存范围。
  - 默认、`project`、`all`、`project:*` 全部只调用 `CacheService.invalidate_all_project_cache()`，限定 `project:*` 命名空间。
  - `project_list/project:list:*`、`project_detail/project:detail:*`、`project_statistics/project:statistics:*` 走明确白名单方法或 pattern；未知范围返回 `code=400`，不执行删除。
  - 删除对不存在方法和全库清理方法的调用，避免误清限流、Token 黑名单等共库数据。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_projects_cache_admin12.py` 先红后绿（2 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_projects_cache_admin12.py tests/unit/test_cache_service.py` 通过（35 passed，1 skipped；Redis 外部依赖测试按原标记跳过）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/projects/cache.py tests/unit/test_projects_cache_admin12.py` 通过。
  - `ruff check app/api/v1/endpoints/projects/cache.py tests/unit/test_projects_cache_admin12.py` 通过。
  - `git diff --check app/api/v1/endpoints/projects/cache.py tests/unit/test_projects_cache_admin12.py` 通过。

## 2026-07-04 继续：MISC-09 成本归集写端点 RBAC

- 修复目标：`POST /cost-collection/collect` 会触发写库归集，不能只要求登录；必须要求成本管理权限，避免任意用户全量触发成本归集。
- 红测：
  - `tests/unit/test_cost_collection_permissions_misc09.py::test_cost_collection_collect_requires_cost_manage_permission` 先失败：`run_cost_collection.current_user` 依赖是 `Depends(deps.get_current_active_user)`。
- 代码面：
  - `app/api/v1/endpoints/cost_endpoints/collection.py` 引入 `security.require_permission`。
  - `run_cost_collection` 的 `current_user` 依赖改为 `Depends(security.require_permission("cost:manage"))`。
  - 只收紧写端点；`GET /status`、`GET /by-project` 仍保持登录可读。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_cost_collection_permissions_misc09.py` 先红后绿（1 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_cost_collection_permissions_misc09.py tests/services/test_cost_collection_business_docs.py` 通过（2 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/cost_endpoints/collection.py tests/unit/test_cost_collection_permissions_misc09.py` 通过。
  - `ruff check app/api/v1/endpoints/cost_endpoints/collection.py tests/unit/test_cost_collection_permissions_misc09.py` 通过。
  - `git diff --check app/api/v1/endpoints/cost_endpoints/collection.py tests/unit/test_cost_collection_permissions_misc09.py` 通过。

## 2026-07-04 继续：MISC-20 预算写接口权限码

- 修复目标：预算相关写操作不能继续使用 `budget:read`；更新、提交、删除、明细维护、分摊规则维护要使用现有 `budget:create/update/delete` 权限。
- 红测：
  - `tests/unit/test_budget_permissions_misc20.py::test_budget_write_endpoints_do_not_use_budget_read_permission` 先失败：`update_budget` 等写函数仍绑定 `budget:read`。
- 代码面：
  - `budgets.py`：预算 `update/submit` 改 `budget:update`，`delete` 改 `budget:delete`；列表、项目预算列表、详情仍为 `budget:read`。
  - `items.py`：预算明细 `create/update/delete` 改 `budget:update`；明细列表仍为 `budget:read`。
  - `allocation_rules.py`：分摊规则 `create/update/delete` 分别改 `budget:create/update/delete`；列表和详情仍为 `budget:read`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_budget_permissions_misc20.py` 先红后绿（1 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_budget_permissions_misc20.py tests/schemas/test_budget.py tests/unit/test_budget_execution_check_service.py tests/unit/test_budget_alert_service.py` 通过（28 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/budget/budgets.py app/api/v1/endpoints/budget/items.py app/api/v1/endpoints/budget/allocation_rules.py tests/unit/test_budget_permissions_misc20.py` 通过。
  - `ruff check app/api/v1/endpoints/budget/budgets.py app/api/v1/endpoints/budget/items.py app/api/v1/endpoints/budget/allocation_rules.py tests/unit/test_budget_permissions_misc20.py` 通过。
  - `git diff --check app/api/v1/endpoints/budget/budgets.py app/api/v1/endpoints/budget/items.py app/api/v1/endpoints/budget/allocation_rules.py tests/unit/test_budget_permissions_misc20.py` 通过。

## 2026-07-04 继续：MISC-11 方案积分退款刷分漏洞

- 修复目标：`POST /solution-credits/internal/refund` 不能只要求登录；该入口可增加积分，必须要求积分管理权限，避免任意用户给自己退款刷分。
- 红测：
  - `tests/unit/test_solution_credits_permissions_misc11.py::test_internal_refund_requires_solution_credit_manage_permission` 先失败：`internal_refund_credits.current_user` 依赖是 `Depends(deps.get_current_user)`。
- 代码面：
  - `app/api/v1/endpoints/solution_credits/internal.py` 引入 `security.require_permission`。
  - `internal_refund_credits` 的 `current_user` 依赖改为 `Depends(security.require_permission("solution_credit:manage"))`。
  - 退款 `amount` Query 增加 `ge=1/le=1000` 边界；用户端查询/检查接口不变。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_solution_credits_permissions_misc11.py` 先红后绿（1 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_solution_credits_permissions_misc11.py tests/unit/test_solution_credit_service.py` 通过（26 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/solution_credits/internal.py tests/unit/test_solution_credits_permissions_misc11.py` 通过。
  - `ruff check app/api/v1/endpoints/solution_credits/internal.py tests/unit/test_solution_credits_permissions_misc11.py` 通过。
  - `git diff --check app/api/v1/endpoints/solution_credits/internal.py tests/unit/test_solution_credits_permissions_misc11.py` 通过。

## 2026-07-04 继续：MISC-14 PM 介入零鉴权与数据源桩

- 修复目标：`/pm-involvement` 6 个端点不能匿名调用；POST 判断/自动判断/通知生成使用 `presale:manage`，GET 相似项目/标准方案/示例至少要求登录。同时，PM 介入判断不能再用相似项目 0、失败数 0、标准方案 False 的固定桩。
- 红测：
  - `tests/unit/test_pm_involvement_misc14.py::test_pm_involvement_post_endpoints_require_presale_manage_permission` 先失败：POST 端点没有 `current_user` 依赖。
  - `tests/unit/test_pm_involvement_misc14.py::test_pm_involvement_read_endpoints_require_authenticated_user` 先失败：GET 端点没有登录依赖。
  - `tests/unit/test_pm_involvement_misc14.py` 中 3 个数据源用例先失败：服务方法不接受 DB，仍返回固定 0/False/模拟工单。
  - `test_presale_ticket_creation_no_longer_hardcodes_zero_history` 先失败：工单创建仍写死 `历史相似项目数/失败项目数` 为 0。
- 代码面：
  - `performance/pm_involvement.py`：POST 判断、auto-judge、通知生成改为 `presale:manage`；GET 相似项目、标准方案、测试示例改为登录用户可读；相似项目/模板/auto-judge 注入 DB。
  - `pm_involvement_service.py`：新增基于 `Project` 的相似项目总数/成功数/失败数/成功率；新增基于启用 `PresaleSolutionTemplate` 的标准方案检查；`auto_judge_from_ticket` 查真实售前工单并结合历史/模板判断。
  - `presale/tickets/crud.py`：创建工单时复用同一历史项目/标准方案查询，不再固定相似项目 0、失败数 0、标准方案 False。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_pm_involvement_misc14.py` 先红后绿（6 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_pm_involvement_misc14.py tests/unit/test_services_p3_coverage.py::TestPMInvolvementService tests/unit/test_services_p4_coverage.py::TestPMInvolvementService` 通过（19 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_presale_ticket_response.py::test_build_ticket_response_exposes_pm_involvement_context` 通过。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/performance/pm_involvement.py app/api/v1/endpoints/presale/tickets/crud.py app/services/pm_involvement_service.py tests/unit/test_pm_involvement_misc14.py` 通过。
  - `ruff check app/api/v1/endpoints/performance/pm_involvement.py app/api/v1/endpoints/presale/tickets/crud.py app/services/pm_involvement_service.py tests/unit/test_pm_involvement_misc14.py` 通过。
  - `git diff --check app/api/v1/endpoints/performance/pm_involvement.py app/api/v1/endpoints/presale/tickets/crud.py app/services/pm_involvement_service.py tests/unit/test_pm_involvement_misc14.py` 通过。
  - 旁路观察：全量 `tests/unit/test_presale_ticket_response.py` 仍有一个既存失败，原因是 deliverables 响应多了 `is_required` 字段，与本次 MISC-14 改动无关。

## 2026-07-04 继续：MISC-04 legacy best_practice 半成品路由

- 修复目标：旧 `app/api/v1/endpoints/best_practice.py` 的 4 个 P0 优化端点不能作为裸写路由残留；同时必须确认它没有被主路由误挂载，避免和已注册的真实 `/projects/best-practices` 混淆。
- 红测：
  - `tests/unit/test_best_practice_legacy_misc04.py::test_legacy_best_practice_write_endpoints_are_permission_guarded` 先失败：`abc_classification` 等函数没有 `current_user` 权限依赖。
  - 同文件确认 `api.py` 没有挂旧 `best_practice` 模块，且 `projects/__init__.py` 继续挂载真实 `ext_best_practices.router`。
- 代码面：
  - `app/api/v1/endpoints/best_practice.py` 引入 `security.require_permission`。
  - ABC 分级和缺料升级潜在写端点要求 `material:update`。
  - 供应商自动升降级要求 `supplier:update`。
  - 项目齐套率目标配置要求 `project:update`。
  - 不把旧模块新增挂载到 `api.py`；真实前端路径继续走 `/projects/best-practices`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_best_practice_legacy_misc04.py` 先红后绿（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_best_practices_service.py` 通过（23 个用例），确认真实 best-practices 服务未受影响。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/best_practice.py tests/unit/test_best_practice_legacy_misc04.py` 通过。
  - `ruff check app/api/v1/endpoints/best_practice.py tests/unit/test_best_practice_legacy_misc04.py` 通过。
  - `git diff --check app/api/v1/endpoints/best_practice.py tests/unit/test_best_practice_legacy_misc04.py` 通过。
  - 旁路观察：`tests/unit/test_best_practice_service_coverage.py` 和 `tests/unit/test_best_practice_deep.py` 仍有既存失败，分别要求不存在的 `get_best_practices()` 和无参 config 调用，与本次 legacy 路由权限补丁无关。

## 2026-07-04 继续：MISC-10 成本偏差权限/404/N+1

- 修复目标：`/cost-variance` 三个端点不能只要求登录；详情缺失项目不能返回 200；summary 成本类型 breakdown 不应按项目逐条查询。
- 红测：
  - `tests/unit/test_cost_variance_misc10.py::test_cost_variance_routes_require_project_read_permission` 先失败：summary/patterns/detail 仍绑定 `deps.get_current_active_user`。
  - `tests/unit/test_cost_variance_misc10.py::test_variance_detail_returns_404_when_project_missing` 先失败：缺失项目没有抛 `HTTPException(404)`。
  - `tests/unit/test_cost_variance_misc10.py::test_variance_summary_loads_cost_breakdowns_in_one_grouped_query` 覆盖 summary 只做项目列表 + grouped breakdown 两次查询。
- 代码面：
  - `cost_endpoints/variance_analysis.py` 引入 `security.require_permission("project:read")`，summary/patterns/detail 三个端点统一收紧为项目读权限。
  - `variance_detail` 在项目不存在时抛 `HTTPException(status_code=404, detail="项目不存在")`。
  - 新增 `_load_cost_breakdowns`，按项目 ID 一次 grouped 查询 `project_costs`，替代原先逐项目 breakdown 查询。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_cost_variance_misc10.py` 先红后绿（3 个用例）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js` 通过（24 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/cost_endpoints/variance_analysis.py tests/unit/test_cost_variance_misc10.py` 通过。
  - `ruff check app/api/v1/endpoints/cost_endpoints/variance_analysis.py tests/unit/test_cost_variance_misc10.py` 通过。
  - `git diff --check app/api/v1/endpoints/cost_endpoints/variance_analysis.py tests/unit/test_cost_variance_misc10.py` 通过。

## 2026-07-04 继续：MISC-15 关系成熟度假数据与 NameError

- 修复目标：`relationship_maturity` 不能继续向用户展示固定客户样例；`POST /relationship/improvement-plan` 不能因为未定义 `gap` 直接 500；前端页面不能继续内置固定客户和组合分析数据。
- 红测：
  - `tests/unit/test_relationship_maturity_misc15.py::test_customer_assessment_uses_scoring_service_and_real_customer` 先失败：客户评估没有调用 `RelationshipScoringService`，仍返回固定“宁德时代”。
  - `test_customer_assessment_raises_404_for_missing_customer` 先失败：不存在客户仍返回假评估。
  - `test_improvement_plan_uses_computed_gap_without_name_error` 先失败：`gap` 未定义导致 NameError。
  - `test_portfolio_analysis_uses_score_records_not_static_demo_customers` 先失败：组合分析固定返回 45 个客户和固定客户名。
  - 前端 route contract 先失败：`relationshipMaturity.js` API 模块不存在。
- 代码面：
  - `relationship_maturity.py`：客户评估查 `Customer`，缺失返回 404；评估结果走 `RelationshipScoringService.calculate_customer_score(save_to_db=False)`；历史趋势取真实评分历史；组合分析读取 `CustomerRelationshipScore` 最新记录并按 L1-L5 汇总。
  - `create_relationship_improvement_plan`：显式计算 `gap`，里程碑用真实差距，行动项改成通用角色/信息补齐动作，移除固定人名。
  - `frontend/src/services/api/relationshipMaturity.js`：新增真实路由包装，保持当前后端挂载路径 `/sales/relationship/relationship/...`。
  - `frontend/src/pages/SalesAI/RelationshipMaturity.jsx`：移除本地 `useState({ ...固定样例... })`，改为接口读取、空态/错误态/刷新。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_relationship_maturity_misc15.py --tb=short` 先红后绿（5 个用例）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js` 通过（25 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/relationship_maturity.py tests/unit/test_relationship_maturity_misc15.py` 通过。
  - `ruff check app/api/v1/endpoints/relationship_maturity.py tests/unit/test_relationship_maturity_misc15.py` 通过。
  - `npm exec eslint src/pages/SalesAI/RelationshipMaturity.jsx src/services/api/relationshipMaturity.js src/services/api/__tests__/routeContracts.test.js`（cwd=`frontend`）通过。
  - `git diff --check app/api/v1/endpoints/relationship_maturity.py tests/unit/test_relationship_maturity_misc15.py frontend/src/pages/SalesAI/RelationshipMaturity.jsx frontend/src/services/api/relationshipMaturity.js frontend/src/services/api.js frontend/src/services/api/__tests__/routeContracts.test.js FUNCTIONAL_AUDIT_TRACKER.md PROJECT_NOTES.md` 通过。
  - 旁路观察：`tests/services/test_relationship_scoring_service.py` 现有两处旧 mock 链用例仍失败（`get_score_history` / `get_latest_score`），失败在测试 patch 链与当前服务查询链不匹配，不是本次 MISC-15 接线失败。

## 2026-07-04 继续：MISC-07 优势产品入口与导入默认安全

- 修复目标：`AdvantageProducts.jsx` 有真实优势产品展示和 133 行历史数据，但前端没有路由/菜单入口；Excel 导入前后端默认 `clear_existing=true`，用户不显式传参时会清空现有数据。
- 红测：
  - `tests/unit/test_advantage_products_misc07.py` 先失败：后端导入默认 `Query(True)`、路由和侧边栏无 `/presales/advantage-products`、搜索框默认显示 `unknown`。
  - `frontend/src/services/api/__tests__/routeContracts.test.js` 中优势产品导入用例先失败：前端 `importFromExcel(file)` 发送 `clear_existing: true`。
  - `frontend/src/routes/modules/__tests__/presalesRoutes.test.jsx` 中优势产品路由用例先失败：没有匹配 `/presales/advantage-products`。
- 代码面：
  - `app/api/v1/endpoints/advantage_products/import_excel.py`：`clear_existing` 默认改为 `False`。
  - `frontend/src/services/api/presales.js`：`advantageProductApi.importFromExcel` 默认 `clearExisting=false`。
  - `frontend/src/routes/modules/presalesRoutes.jsx`：新增 `/presales/advantage-products` 路由。
  - `frontend/src/components/layout/sidebarConfig/default.js`：售前技术菜单新增“优势产品”。
  - `frontend/src/components/sales/AdvantageProducts.jsx`：搜索输入框不再把空值显示成 `unknown`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_advantage_products_misc07.py --tb=short --disable-warnings` 先红后绿（3 个用例）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js --testNamePattern "advantage products"` 先红后绿（1 个用例）。
  - `npm --prefix frontend test -- --run src/routes/modules/__tests__/presalesRoutes.test.jsx --testNamePattern "advantage products"` 先红后绿（1 个用例）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js` 通过（26 个用例）。
  - `npm --prefix frontend test -- --run src/routes/modules/__tests__/presalesRoutes.test.jsx` 通过（13 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/advantage_products/import_excel.py tests/unit/test_advantage_products_misc07.py` 通过。
  - `ruff check app/api/v1/endpoints/advantage_products/import_excel.py tests/unit/test_advantage_products_misc07.py` 通过。
  - `npm exec eslint src/components/sales/AdvantageProducts.jsx src/routes/modules/presalesRoutes.jsx src/components/layout/sidebarConfig/default.js src/services/api/presales.js src/services/api/__tests__/routeContracts.test.js src/routes/modules/__tests__/presalesRoutes.test.jsx`（cwd=`frontend`）通过。
  - `git diff --check app/api/v1/endpoints/advantage_products/import_excel.py tests/unit/test_advantage_products_misc07.py frontend/src/components/sales/AdvantageProducts.jsx frontend/src/routes/modules/presalesRoutes.jsx frontend/src/components/layout/sidebarConfig/default.js frontend/src/services/api/presales.js frontend/src/services/api/__tests__/routeContracts.test.js frontend/src/routes/modules/__tests__/presalesRoutes.test.jsx FUNCTIONAL_AUDIT_TRACKER.md PROJECT_NOTES.md` 通过。

## 2026-07-04 继续：MISC-06 文档中心上传端到端不可用

- 修复目标：`Documents.jsx` 上传 `FormData` 时不能继续 POST 到只收 JSON schema 的 `/documents/`，否则端到端必 422；项目级创建文档不能用 `document:read` 作为写权限；当前默认 `data/app.db` 里 60 行 `project_documents` 均为 `/demo/project_documents/*` 假文件路径，不能继续在列表里冒充真实可下载文件。
- 红测：
  - `tests/unit/test_documents_upload_misc06.py` 先失败：没有 `upload_document_file`；`crud_refactored.py` 没有 `/upload` multipart 端点；`create_project_document` 仍使用 `document:read`。
  - `frontend/src/services/api/__tests__/routeContracts.test.js` 中 FormData 上传用例先失败：`documentApi.create(formData)` 仍 POST `/documents/`。
  - 新增 fake path 过滤红测先失败：列表查询没有过滤 `/demo/%` 文件路径。
- 代码面：
  - `documents/crud_refactored.py`：新增静态路由 `/documents/upload`，接收 `file/project_id/machine_id/doc_type/doc_category/doc_name/doc_no/version/description` 的 multipart 表单，验证项目/机台、扩展名和 50MB 大小限制，保存到 `uploads/documents/{project_id}/{YYYYMM}/...`，并创建 `ProjectDocument`。
  - `create_project_document` 写权限从 `document:read` 改为 `document:create`。
  - 文档列表和项目文档列表通过 `_exclude_demo_file_paths` 过滤 `/demo/%`，不直接删除本地 SQLite 里的历史 demo 行。
  - `frontend/src/services/api/projects.js`：`documentApi.create(FormData)` 自动走 `/documents/upload`，保留 JSON 创建走 `/documents/`；同时新增显式 `documentApi.upload(formData)`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_documents_upload_misc06.py --tb=short --disable-warnings` 先红后绿（3 个用例）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js --testNamePattern "uploads document FormData"` 先红后绿（1 个用例）。
  - `npm --prefix frontend test -- --run src/pages/__tests__/Documents.test.jsx` 通过（5 个用例）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js` 通过（27 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/documents/crud_refactored.py tests/unit/test_documents_upload_misc06.py` 通过。
  - `ruff check app/api/v1/endpoints/documents/crud_refactored.py tests/unit/test_documents_upload_misc06.py` 通过。
  - `npm exec eslint src/services/api/projects.js src/services/api/__tests__/routeContracts.test.js src/pages/__tests__/Documents.test.jsx`（cwd=`frontend`）通过。
  - `git diff --check app/api/v1/endpoints/documents/crud_refactored.py frontend/src/services/api/projects.js tests/unit/test_documents_upload_misc06.py frontend/src/services/api/__tests__/routeContracts.test.js frontend/src/pages/__tests__/Documents.test.jsx FUNCTIONAL_AUDIT_TRACKER.md PROJECT_NOTES.md` 通过。

## 2026-07-04 继续：MISC-05 legacy endpoints/knowledge 下架止血

- 修复目标：`app/api/v1/endpoints/knowledge` 旧自动沉淀聚合包不能继续聚合 `extraction/induction/alerts/search` 四个半成品路由；这些路由依赖默认库不存在的 `knowledge_entries/knowledge_alerts`，误挂后会 500 或暴露硬编码 AI 行为。真实前端知识库继续走 `/knowledge-base` 和 `/service/knowledge-base`。
- 现场确认：
  - `api.py` / `api_lazy.py` 当前没有 include `app.api.v1.endpoints.knowledge`，也没有 legacy `/knowledge` 主挂载。
  - 默认 `data/app.db` 只有 `knowledge_base`，查询 `knowledge_entries` 报 `no such table: knowledge_entries`。
  - `frontend/src/services/api/knowledge.js`、`knowledgeBase.js` 走 `/knowledge-base`；客服知识库走 `/service/knowledge-base`。
- 红测：
  - `tests/unit/test_knowledge_legacy_misc05.py::test_legacy_knowledge_router_no_longer_aggregates_broken_subrouters` 先失败：旧包仍 include `extraction.router` 等四个子路由。
  - `test_legacy_knowledge_endpoint_returns_501_when_accidentally_mounted` 先失败：没有 `legacy_knowledge_disabled` 止血入口。
- 代码面：
  - `endpoints/knowledge/__init__.py` 去掉 `.alerts/.extraction/.induction/.search` 导入和 include_router。
  - 新增 catch-all `legacy_knowledge_disabled`，误挂时对 GET/POST/PUT/PATCH/DELETE/OPTIONS 返回 501，并提示使用 `/knowledge-base` 或 `/service/knowledge-base`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_knowledge_legacy_misc05.py --tb=short --disable-warnings` 先红后绿（3 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/knowledge/__init__.py tests/unit/test_knowledge_legacy_misc05.py` 通过。
  - `ruff check app/api/v1/endpoints/knowledge/__init__.py tests/unit/test_knowledge_legacy_misc05.py` 通过。

## 2026-07-04 继续：MISC-08 change_impact 占位路由下架并挂真实现

- 修复目标：主 `api.py` 不能继续把旧 `/change-impact` shim 当成可用功能上线；真实项目变更影响接口应挂载 `/project-change-impacts/*`，旧占位不能再返回 `change_impact module placeholder`。
- 现场确认：
  - `api.py` 原来 include `app.api.v1.endpoints.change_impact` 到 `/change-impact`，该文件 ImportError 后返回占位 JSON。
  - `api_lazy.py` 已挂 `app.api.v1.endpoints.projects.change_impact`，但主 `api.py` 未挂。
  - `app/api/v1/endpoints/projects/change_impact.py` 有真实 `assess/execute-linkage/detail/by-ecn/by-project` 端点；默认 `data/app.db` 存在 `project_change_impacts` 表。
- 红测：
  - `tests/unit/test_change_impact_misc08.py::test_main_api_mounts_real_project_change_impact_not_legacy_placeholder` 先失败：主 `api.py` 未挂真实 `projects.change_impact`，仍挂 `/change-impact`。
  - `test_legacy_change_impact_router_no_longer_returns_placeholder_payload` 先失败：旧 shim 仍含 `change_impact module placeholder`。
  - `test_legacy_change_impact_endpoint_returns_501_when_accidentally_mounted` 先失败：没有 `legacy_change_impact_disabled`。
- 代码面：
  - `api.py` 的变更影响块改为 include `app.api.v1.endpoints.projects.change_impact`，prefix 为空，暴露真实 `/project-change-impacts/*`。
  - `endpoints/change_impact.py` 改为 disabled legacy shim，误挂时 GET/POST/PUT/PATCH/DELETE/OPTIONS 返回 501，并提示使用 `/project-change-impacts`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_change_impact_misc08.py --tb=short --disable-warnings` 先红后绿（4 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/api.py app/api/v1/endpoints/change_impact.py tests/unit/test_change_impact_misc08.py` 通过。
  - `ruff check app/api/v1/api.py app/api/v1/endpoints/change_impact.py tests/unit/test_change_impact_misc08.py` 通过。

## 2026-07-04 继续：MISC-13 project_contributions 报告页闭环

- 修复目标：`/projects/:id/contributions` 页面不能继续默认按当前月过滤，导致默认库里 period 全是 `pr30222` 时永远空白；已有 `getReport/calculate/rateMember` API 应在页面形成最小闭环。
- 现场确认：
  - 主 `api.py` 和 `api_lazy.py` 均挂 `/project-contributions`，后端 5 个端点存在。
  - `frontend/src/pages/ProjectContributionReport.jsx` 原来只调用 `getReport(id, { period: 当前月 })`，没有周期切换、计算、评分入口。
  - 默认 `data/app.db.project_member_contributions` 为 60 行，period 全是 `pr30222`，因此当前月过滤必空。
- 红测：
  - `tests/unit/test_project_contributions_misc13.py` 先失败：报告行和 top contributor 没有带 `period`，全周期下无法按行评分。
  - `ProjectContributionReport.test.jsx` 先失败：页面默认调用 `getReport("42", { period: "2026-07" })`，且没有 `统计周期` 控件和 `计算贡献` 按钮。
  - 追加评分红测：页面应调用 `rateMember(projectId, userId, { period: row.period, pm_rating })`。
- 代码面：
  - `project_contribution_service.py`：`generate_contribution_report` 的 `contributions/top_contributors` now 带 `period`。
  - `ProjectContributionReport.jsx`：默认 period 改为空，首次读取全周期；新增 month 筛选、全部周期、计算贡献按钮；已有报告刷新时不整页 skeleton；表格新增周期列；PM 评分由静态文本改为可提交下拉框。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_project_contributions_misc13.py --tb=short --disable-warnings` 先红后绿（1 个用例）。
  - `npm --prefix frontend test -- --run src/pages/__tests__/ProjectContributionReport.test.jsx --silent` 先红后绿（3 个用例）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/projects.test.js --testNamePattern "projectContributionApi" --silent` 通过（3 个相关用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/services/project_contribution_service.py tests/unit/test_project_contributions_misc13.py` 通过。
  - `ruff check app/services/project_contribution_service.py tests/unit/test_project_contributions_misc13.py` 通过。
  - `npm exec eslint src/pages/ProjectContributionReport.jsx src/pages/__tests__/ProjectContributionReport.test.jsx`（cwd=`frontend`）通过。

## 2026-07-04 继续：MISC-16 RequirementSurvey 旧死链下架

- 修复目标：不能继续从前端 barrel export `surveyApi`，因为它调用 `/requirement-surveys`，后端无匹配路由/表；同时不能误删当前已经接入售前工单上下文的 `RequirementSurvey` 活页面。
- 现场确认：
  - `frontend/src/pages/RequirementSurvey/index.jsx` 当前通过 `presaleApi.tickets.list/create` 和 `presaleWorkbenchApi.loadContext` 工作，已有 7 个页面测试覆盖上下文、需求包和创建调研工单。
  - `frontend/src/services/api/survey.js` 仍导出旧 `surveyApi`，调用 `/requirement-surveys`；`api.js` 仍 barrel export 该死链。
  - `frontend/src/pages/RequirementSurvey/hooks/useRequirementSurvey.js` 是未使用旧 hook，仅依赖旧 `surveyApi`；其测试为 `describe.skip`。
- 红测：
  - `routeContracts.test.js::does not expose the legacy requirement-surveys API that has no backend` 先失败：`api.js` 仍包含 `./api/survey.js`。
- 代码面：
  - `frontend/src/services/api.js` 删除 `export * from "./api/survey.js"`。
  - 删除旧 `frontend/src/services/api/survey.js`。
  - 删除未使用的 `RequirementSurvey/hooks/useRequirementSurvey.js`、`hooks/index.js`、以及 skipped hook test。
  - 保留当前 `RequirementSurvey` 页面、路由和售前工单实现。
- 验证：
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js --testNamePattern "legacy requirement-surveys" --silent` 先红后绿。
  - `npm --prefix frontend test -- --run src/pages/__tests__/RequirementSurvey.test.jsx --silent` 通过（7 个用例）。
  - `rg -n "surveyApi|requirement-surveys|useRequirementSurvey|RequirementSurvey/hooks" frontend/src --glob '*.js' --glob '*.jsx'` 仅剩本次防回归测试命中。

## 2026-07-04 继续：MISC-17 legacy resource_scheduling 下架止血

- 修复目标：主 `api.py` 不能继续暴露旧 `/resource-scheduling` 占位 shim；真实工程师调度 `/engineer-scheduling` 必须保留，前端现有调用不能误删。
- 现场确认：
  - `api.py` 同时挂了真实 `engineer_scheduling` 到 `/engineer-scheduling`，以及旧 `resource_scheduling` 到 `/resource-scheduling`。
  - `app/api/v1/endpoints/resource_scheduling.py` 是 ImportError 猜模块后返回 `resource_scheduling module placeholder` 的 shim。
  - 前端只调用 `/engineer-scheduling`；没有 `/resource-scheduling` 调用点。
- 红测：
  - `tests/unit/test_resource_scheduling_misc17.py` 先失败：主 `api.py` 仍 import/include `resource_scheduling`，旧 shim 仍有 placeholder，且无 `legacy_resource_scheduling_disabled`。
- 代码面：
  - `api.py` 移除 legacy `/resource-scheduling` 挂载，同块 `resource_overview/margin_prediction/cost_collection` 保持不动。
  - `resource_scheduling.py` 改为 501 stopgap，误挂时提示使用 `/engineer-scheduling`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_resource_scheduling_misc17.py --tb=short --disable-warnings` 先红后绿（3 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/api.py app/api/v1/endpoints/resource_scheduling.py tests/unit/test_resource_scheduling_misc17.py` 通过。
  - `ruff check app/api/v1/api.py app/api/v1/endpoints/resource_scheduling.py tests/unit/test_resource_scheduling_misc17.py` 通过。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js --testNamePattern "engineer-scheduling" --silent` 通过。

## 2026-07-04 继续：MISC-19 发货审批接统一审批引擎

- 修复目标：`business_support_orders` 的发货审批不能继续在模块内直接翻 `approval_status/delivery_status`，必须通过统一审批实例和审批任务落状态；同时现场校正原 tracker 的“开票/对账/入驻/验收僵尸”判断，默认库已有 `invoice_requests/reconciliations` 等真实表和已挂路由，不按全量下架处理。
- 现场确认：
  - `/business-support-orders/delivery-orders/{id}/approve` 原来虽有 `delivery:manage` 权限，但直接修改发货单状态，没有 `ApprovalInstance/ApprovalTask`。
  - `businessSupportApi.deliveryOrders` 只有发货/销售订单 wrapper，发货详情页旧按钮直接调用 approve。
  - `app/utils/init_approval_data.py` 没有发货审批模板，审批引擎 registry 也没有 `DELIVERY_ORDER` 适配器。
- 红测：
  - `test_business_support_delivery_routes.py::test_delivery_order_approval_template_and_adapter_are_registered` 先失败：`TPL_DELIVERY_ORDER` 不存在。
  - `tests/unit/test_business_support_delivery_approval_misc19.py` 锁定：没有统一审批实例时 approve 必须 400；提交统一审批后才可通过待办任务审批并落发货单状态。
- 代码面：
  - 新增 `DeliveryOrderApprovalAdapter` 并注册 `DELIVERY_ORDER`，回调负责 submit/approved/rejected/withdrawn 时同步发货单状态。
  - `init_approval_data.py` 和 `migrations/20260704_delivery_order_approval_sqlite.sql` 补 `TPL_DELIVERY_ORDER` 默认审批模板/流程/节点。
  - `delivery_orders/crud.py` 新增 `submit-approval`；旧 `approve` 变成兼容入口，只查当前活跃统一审批实例和当前用户待办任务，再调用 `ApprovalEngineService.approve/reject`。
  - 前端 `businessSupportApi.deliveryOrders.submitApproval` 补齐；`DeliveryDetail` 的通过/驳回按钮先提交统一审批，再走兼容 approve，用户仍是一键操作。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_business_support_delivery_approval_misc19.py tests/api/test_business_support_delivery_routes.py::test_delivery_order_approval_template_and_adapter_are_registered --tb=short --disable-warnings` 通过（3 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/business_support_orders/delivery_orders/crud.py app/services/approval_engine/adapters/delivery_order.py app/services/approval_engine/adapters/__init__.py app/utils/init_approval_data.py tests/unit/test_business_support_delivery_approval_misc19.py tests/api/test_business_support_delivery_routes.py tests/audit_p0/test_p0_02_approval_template_no_seed.py` 通过。
  - `ruff check app/api/v1/endpoints/business_support_orders/delivery_orders/crud.py app/services/approval_engine/adapters/delivery_order.py app/services/approval_engine/adapters/__init__.py app/utils/init_approval_data.py tests/unit/test_business_support_delivery_approval_misc19.py tests/api/test_business_support_delivery_routes.py tests/audit_p0/test_p0_02_approval_template_no_seed.py` 通过。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js src/pages/DeliveryManagement/__tests__/DeliveryDetail.test.jsx --silent` 通过（29 个用例）。
  - 备注：直接跑 API TestClient 路由测试时命中当前环境的 `Client.__init__() got an unexpected keyword argument 'app'`，属于 Starlette/TestClient 与 httpx 版本兼容问题；本次用直接函数+真实 DB/审批引擎覆盖核心行为。

## 2026-07-04 继续：MISC-22 alert-rules 写接口权限降级止血

- 修复目标：自定义预警规则 CRUD 目前未接生产扫描调度，不能继续让任意登录用户创建/更新/开关/删除规则；本次只做降级止血，不宣称已补完整调度链路。
- 现场确认：
  - `app/api/v1/endpoints/alerts/rules.py` 中模板/规则读、创建、更新、toggle、delete 全部只依赖 `security.get_current_active_user`。
  - `AlertRuleEngine` 位于 `app/services/alert/rule_engine`，`evaluate_rule` 主要由单测覆盖；生产预警仍更多走各域硬编码规则和专用任务。
  - 权限种子中缺 `alert:read/alert:manage`，前端 `usePermission.js` 只有 `ALERT.READ`。
- 红测：
  - `tests/unit/test_alert_rules_misc22.py` 先失败：读接口未要求 `alert:read`，写接口未要求 `alert:manage`，权限种子和前端常量缺失。
- 代码面：
  - 规则模板/规则列表/详情：改为 `security.require_permission("alert:read")`。
  - create/update/toggle/delete：改为 `security.require_permission("alert:manage")`。
  - `init_permissions_data.py` 补 `alert:read`、`alert:manage`；`usePermission.js` 补 `ALERT.MANAGE`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_alert_rules_misc22.py --tb=short --disable-warnings` 先红后绿（4 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile app/api/v1/endpoints/alerts/rules.py app/utils/init_permissions_data.py tests/unit/test_alert_rules_misc22.py` 通过。
  - `ruff check app/api/v1/endpoints/alerts/rules.py app/utils/init_permissions_data.py tests/unit/test_alert_rules_misc22.py` 通过。
  - `npm exec eslint src/hooks/usePermission.js`（cwd=`frontend`）通过。

## 2026-07-04 继续：MISC-24 legacy ai_strategy 下架止血

- 修复目标：不能继续把 `/ai-strategy` 旧别名/占位 shim 当成可用模块挂到主 API；前端不能继续暴露会调用 5 个 `/ai-strategy/*` 死接口的 AI 战略助手入口。真实战略能力继续保留在 `/strategy`。
- 现场确认：
  - `app/api/v1/endpoints/ai_strategy.py` 实际只有兼容导入 fallback，最终返回 `ai_strategy module placeholder`，本地不存在 `app/api/v1/endpoints/ai_strategy/` 子模块。
  - 主 `api.py` 原来把该占位 shim 挂到 `/ai-strategy`。
  - 前端 `aiStrategyApi` 调用 `/ai-strategy/analyze/decompose/annual-plan/dept-objectives/apply`，`/strategy/ai-assistant` 路由和侧边栏入口会把用户带到死链。
  - 历史 API 契约测试还把 `/ai-strategy` 当 `/strategy` 的旧别名覆盖。
- 红测：
  - 新增 `tests/unit/test_ai_strategy_misc24.py`，先失败：主路由仍挂 `/ai-strategy`，shim 仍有 placeholder，前端 barrel/route/sidebar/API 仍存在，历史契约测试仍引用 `/ai-strategy`。
- 代码面：
  - `api.py` 移除 `/ai-strategy` 挂载。
  - `ai_strategy.py` 改为未挂载的 501 legacy shim，误挂时提示使用 `/strategy`。
  - 删除 `frontend/src/services/api/aiStrategy.js` 和 `frontend/src/pages/AIStrategyAssistant/*`，移除 `/strategy/ai-assistant` 路由与侧边栏入口。
  - API 契约测试中的旧 `/ai-strategy` 别名改回真实 `/strategy`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_ai_strategy_misc24.py --tb=short --disable-warnings` 先红后绿（3 个用例）。
  - `rg -n "ai-strategy|aiStrategyApi|aiStrategy.js|AIStrategyAssistant|AI战略助手|strategy/ai-assistant|ai_strategy module placeholder|include_router\\(ai_strategy_router" app frontend/src tests --glob '*.py' --glob '*.js' --glob '*.jsx'` 仅剩 MISC-24 防回归测试自身命中。

## 2026-07-04 继续：MISC-02 资源总览 PMO 页面接真实数据源

- 修复目标：PMO 的 `/pmo/resource-overview` 页面不能继续调用旧 `/resource-overview/` 占位 shim；即使当前库没有资源分配明细，也要展示真实 PMO 汇总和部门资源汇总，而不是吃 placeholder 后看起来恒空白。
- 现场确认：
  - `app/api/v1/endpoints/resource_overview.py` 是兼容 fallback，占位返回 `resource_overview module placeholder`。
  - 主 `api.py` 原来仍挂 legacy `/resource-overview`。
  - 活接口已存在于 `app/api/v1/endpoints/pmo/cockpit.py` 的 `/pmo/resource-overview`，但响应只含 `total_resources/allocated_resources/by_department`，不含页面甘特需要的 `employees`。
  - `ResourceOverview.jsx` 原来通过 `resourceOverviewApi.list()` 调旧 `/resource-overview/`，所以 PMO 可达页无法拿到真实数据。
- 红测：
  - 新增 `tests/unit/test_resource_overview_misc02.py`：锁旧 `/resource-overview` 不再挂主路由、shim 不再 placeholder、PMO schema 必须有 `employees/avg_utilization/conflicts`、前端 service 必须走 `/pmo/resource-overview`。
  - `routeContracts.test.js` 新增 PMO resource overview 路由契约，先失败在旧 `/resource-overview/`。
- 代码面：
  - `api.py` 移除 legacy `/resource-overview` 挂载；`resource_overview.py` 改为未挂载 501 shim，误挂时提示使用 `/pmo/resource-overview`。
  - `ResourceOverviewResponse` 补 `total_employees/employees_with_conflicts/total_conflicts/avg_utilization/employees`。
  - `PmoCockpitService.get_resource_overview()` 从 `pmo_resource_allocation + users + projects` 组装页面 timeline rows，并计算当前负荷和重叠分配冲突。
  - `resourceOverviewApi.list()` 改走 `/pmo/resource-overview`；`ResourceOverview.jsx` 改本地部门/冲突过滤，并在无 allocation 明细时展示真实资源总数和部门汇总。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_resource_overview_misc02.py --tb=short --disable-warnings` 先红后绿（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_pmo_cockpit_service.py -k resource_overview --tb=short --disable-warnings` 通过（2 个用例）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js --testNamePattern "PMO resource overview" --silent` 先红后绿。
  - `npm --prefix frontend test -- --run src/pages/__tests__/ResourceOverview.test.jsx --silent` 通过。
  - 直接调用 `PmoCockpitService(SessionLocal()).get_resource_overview()` 成功返回 `employees` key；当前默认库 `employee_rows=0`，说明页面会显示真实汇总/部门汇总，等待业务表产生 allocation 明细后甘特行自然出现。

## 2026-07-04 继续：MISC-21 项目预算审批接统一审批引擎

- 修复目标：预算不能继续在 `/budgets/{id}/submit` 和 `/budgets/{id}/approve` 内直接翻 `status`；预算总额不能长期与明细合计不一致；前端预算入口不能只停留在项目列表预算字段而完全不碰预算单 API。
- 现场确认：
  - `budgets.py` 原来 `submit_budget` 直接 `SUBMITTED`，`approve_budget` 直接 `APPROVED/REJECTED` 并同步项目预算金额，没有 `ApprovalInstance/ApprovalTask`。
  - 默认 `data/app.db` 中 60 条 `project_budgets` 全部 `total_amount != Σproject_budget_items.budget_amount`。
  - `BudgetManagement.jsx` 原来只读 `projectApi.list`，`budgetApi` 虽存在但页面不使用。
- 红测：
  - 新增 `tests/unit/test_budget_approval_misc21.py`，先失败：缺 `PROJECT_BUDGET` adapter/template，预算路由仍直接翻状态，缺总额重算 helper。
  - 新增 `tests/unit/test_budget_approval_flow_misc21.py`，验证没有统一审批实例时旧 approve 必须 400；submit 后产生 `PROJECT_BUDGET` 审批实例和待办，approve 后预算/项目金额按明细总额落库。
- 代码面：
  - 新增 `ProjectBudgetApprovalAdapter` 并注册 `PROJECT_BUDGET`。
  - `init_approval_data.py`、审计测试和 `migrations/20260704_project_budget_approval_sqlite.sql` 补 `TPL_PROJECT_BUDGET`、默认流程、财务审批节点。
  - 预算创建/提交前按明细合计重算 `total_amount`；迁移同时修历史预算总额。
  - `submit_budget` now 调 `ApprovalEngineService.submit`；`approve_budget` 必须找到活跃统一审批实例和当前用户待办，再调用 `engine.approve/reject`。
  - `BudgetManagement.jsx` 优先读 `budgetApi.list(projectContext)`；无预算单时保留原项目预算使用率 fallback，避免破坏现有项目成本中心入口。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_budget_approval_misc21.py tests/unit/test_budget_approval_flow_misc21.py tests/audit_p0/test_p0_02_approval_template_no_seed.py --tb=short --disable-warnings` 通过（6 个用例）。
  - `/Library/Frameworks/Python.framework/Versions/3.14/bin/python3.14 -m py_compile ...` 通过。
  - `ruff check ...` 通过。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js src/pages/__tests__/ProjectManagementDownstreamContext.test.jsx --silent` 通过（34 个用例）。
  - `npm exec eslint src/pages/BudgetManagement.jsx src/pages/__tests__/ProjectManagementDownstreamContext.test.jsx src/services/api/__tests__/routeContracts.test.js src/services/api/budget.js` 通过。
  - 迁移 SQL 用 `data/app.db` 备份到临时库执行后，`TPL_PROJECT_BUDGET`、默认流程、`PROJECT_BUDGET_FINANCE_REVIEW` 均存在，预算总额 mismatch 数从 60 降到 0。

## 2026-07-04 继续：MISC-23 文化墙 config/goals/content 链路补齐

- 修复目标：文化墙配置不能继续返回 placeholder；前端 goals 不能再打裸 `/personal-goals` 或跳未注册页面；内容管理既然前端暴露 update，就必须有后端 PUT/DELETE。
- 现场确认：
  - `app/api/v1/endpoints/culture_wall_config.py` 原来只是兼容导入 fallback，最终返回 `culture_wall_config module placeholder`。
  - 后端真实 goals 已在 `/culture-wall/personal-goals`，但 `frontend/src/services/api/admin.js` 原来调用 `/personal-goals`。
  - `contents.py` 原来只有 list/create/get，缺 `/culture-wall/contents/{id}` 的 PUT/DELETE。
  - Chairman/GM 工作台点击 GOAL 原来跳 `/personal-goals`，项目里没有该页面路由。
- 红测：
  - 新增 `tests/unit/test_culture_wall_misc23.py`，先失败在 config placeholder、contents 缺 PUT/DELETE、前端缺 `contents.delete` 且 goals 路径错误。
- 代码面：
  - `culture_wall_config.py` 改为真实 CRUD：list/create/get/update/delete，支持默认配置唯一性、配置名唯一性、默认 content/play 配置回填。
  - `contents.py` 补统一响应 helper、PUT 更新、DELETE 删除内容并清理阅读记录。
  - `cultureWallApi.contents` 补 `delete`；`cultureWallApi.goals` 改走 `/culture-wall/personal-goals`。
  - Chairman/GM 工作台点击文化墙任意项统一跳 `/culture-wall?item={id}`，不再跳不存在的 `/personal-goals`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_culture_wall_misc23.py` 先红后绿（5 个用例，含临时 SQLite 落库验证）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js --silent` 通过（31 个用例）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js src/pages/gm-workstation/__tests__/GeneralManagerWorkstation.test.jsx --silent` 通过；其中 GM 工作台测试文件当前 34 个用例为 skip，未作为行为证明。
  - `PYTHONPATH=. python -m py_compile app/api/v1/endpoints/culture_wall/contents.py app/api/v1/endpoints/culture_wall_config.py tests/unit/test_culture_wall_misc23.py` 通过。
  - `PYTHONPATH=. ruff check app/api/v1/endpoints/culture_wall/contents.py app/api/v1/endpoints/culture_wall_config.py tests/unit/test_culture_wall_misc23.py` 通过。
  - `npm exec eslint -- src/services/api/admin.js src/services/api/__tests__/routeContracts.test.js src/pages/ChairmanWorkstation.jsx src/pages/gm-workstation/GeneralManagerWorkstation.jsx src/pages/gm-workstation/__tests__/GeneralManagerWorkstation.test.jsx`（cwd=`frontend`）通过。
  - 残留扫描：`culture_wall_config module placeholder` 只剩防回归测试负断言；裸 `/personal-goals` 不再出现在工作台跳转或 API service 中。

## 2026-07-04 继续：HR-22 文化墙发布审核补齐

- 修复目标：文化墙内容不能由创建/编辑人自勾 `is_published=true` 直接上墙；MISC-23 已修配置 CRUD、前端 405 和 goals 前缀，本项补主问题“无审核”。
- 现场确认：
  - `CultureWallContentCreate/Update` 都带 `is_published`，旧 `contents.py` 直接按入参写发布状态和发布人。
  - 列表响应 `is_read` 原来恒 `False`，实际阅读记录表和详情阅读写入链路已存在。
- 代码面：
  - 新增 `CultureWallContentReview` schema。
  - 创建内容时强制 `is_published=False`，不接受作者自发布。
  - 更新内容时忽略 `is_published` 字段，内容编辑与发布分离。
  - 新增 `POST /culture-wall/contents/{content_id}/review`，审核通过才设置 `is_published/publish_date/published_by/published_by_name`，驳回则取消发布。
  - 内容列表批量查询 `CultureWallReadRecord`，返回当前用户真实 `is_read`。
  - 前端 `cultureWallApi.contents.review()` 接入 `/culture-wall/contents/{id}/review`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_culture_wall_hr22.py tests/unit/test_culture_wall_misc23.py` 通过（8 个用例，含临时 SQLite 自发布拦截、review 发布、is_read 回归）。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js --silent` 通过（31 个用例）。
  - `PYTHONPATH=. python -m py_compile app/api/v1/endpoints/culture_wall/contents.py app/api/v1/endpoints/culture_wall_config.py app/schemas/culture_wall.py tests/unit/test_culture_wall_hr22.py tests/unit/test_culture_wall_misc23.py` 通过。
  - `PYTHONPATH=. ruff check app/api/v1/endpoints/culture_wall/contents.py app/api/v1/endpoints/culture_wall_config.py app/schemas/culture_wall.py tests/unit/test_culture_wall_hr22.py tests/unit/test_culture_wall_misc23.py` 通过。
  - `npm exec eslint -- src/services/api/admin.js src/services/api/__tests__/routeContracts.test.js`（cwd=`frontend`）通过。
  - 残留扫描：旧 `is_published=content_data.is_published` / `published_by=... if content_data.is_published` 不再存在；`review` 路由和前端调用均可搜到。

## 2026-07-04 继续：PRE-07 报价更新后税额/折扣重算

- 修复目标：`update_quotation` 修改明细时，不能只改 `subtotal` 却沿用旧税额/旧折扣绝对值；JSON 字段也不能塞 `Decimal` 导致提交失败。
- 现场确认：
  - `generate_quotation()` 创建分支会把报价项中的 `Decimal` 转 `float`，但 `update_quotation()` 原来直接 `[item.dict()]` 写 JSON。
  - `update_quotation()` 原来只有传 `tax_rate/discount_rate` 时才改税额/折扣；只改明细时 `tax/discount` 不随新小计变化。
- 代码面：
  - 更新前先从旧 `tax/subtotal`、`discount/subtotal` 计算有效税率和折扣率。
  - 明细变更时用旧有效税率/折扣率重算 `tax/discount/total`；显式传新税率/折扣率时优先用新值。
  - 新增 `_serialize_items()` 复用创建分支的 `Decimal -> float` JSON 序列化规则。
- 验证：
  - 新增 `tests/unit/test_presale_ai_quotation_pre07.py`，先红后绿：只改明细时 `100→200` 后税额 `13→26`、折扣 `5→10`、总额 `216`；同时覆盖显式税率/折扣率覆盖场景。
  - `PYTHONPATH=. pytest -q tests/unit/test_presale_ai_quotation_pre07.py tests/unit/test_presale_ai_quotation_service_coverage.py tests/unit/test_presale_requirement_bridge.py` 通过（10 个用例）。
  - `PYTHONPATH=. python -m py_compile app/services/presale/presale_ai_quotation_service.py tests/unit/test_presale_ai_quotation_pre07.py` 通过。
  - `PYTHONPATH=. ruff check app/services/presale/presale_ai_quotation_service.py tests/unit/test_presale_ai_quotation_pre07.py` 通过。

## 2026-07-04 继续：PRE-05/PRE-06 三档报价阶梯与静态兜底修复

- 修复目标：三档报价不能因为 AI 独立生成和折扣叠加出现 `BASIC > STANDARD`；AI 失效时静态兜底也不能继续输出 ERP/进销存/移动端 APP 这种非本业务报价。
- 现场确认：
  - `generate_three_tier_quotations()` 原来逐档生成后直接落库，没有 basic/standard/premium 跨档金额校验。
  - `_generate_standard_items()`、`_generate_premium_items()` 的静态回退仍是 ERP 软件报价；在真实非标自动化场景里领域错配。
- 代码面：
  - 新增 `_ensure_minimum_subtotal()`、`_items_subtotal()`、价格复制/四舍五入 helper。
  - 标准档生成后要求小计不少于基础档 `1.18x`，高级档生成后要求小计不少于标准档 `1.22x`，即使 AI 返回低价明细也按比例抬升明细单价，避免总价阶梯倒挂。
  - 静态兜底替换为非标自动化检测工作站、夹治具与安全防护、视觉检测、数据采集追溯、机器人/自动上下料、现场调试与验收培训、质保驻场支持等明细。
- 验证：
  - 新增 `tests/unit/test_presale_ai_quotation_pre05_06.py`，先红后绿：模拟 AI 把标准/高级报低时，最终报价仍满足 `basic.total < standard.total < premium.total`；强制静态兜底时不含 ERP/进销存/财务/人力资源/移动端 APP。
  - `PYTHONPATH=. pytest -q tests/unit/test_presale_ai_quotation_pre05_06.py tests/unit/test_presale_ai_quotation_pre07.py tests/unit/test_presale_ai_quotation_service_coverage.py tests/unit/test_presale_requirement_bridge.py` 通过（12 个用例）。
  - `PYTHONPATH=. python -m py_compile app/services/presale/presale_ai_quotation_service.py tests/unit/test_presale_ai_quotation_pre05_06.py tests/unit/test_presale_ai_quotation_pre07.py` 通过。
  - `PYTHONPATH=. ruff check app/services/presale/presale_ai_quotation_service.py tests/unit/test_presale_ai_quotation_pre05_06.py tests/unit/test_presale_ai_quotation_pre07.py` 通过。
  - `git diff --check` 通过。

## 2026-07-04 继续：PRE-08/PRE-09 商机 AI mock 回退与需求增量回填

- 修复目标：`ai-enrich-requirement` 和 `ai-quote-estimate` 不能把 AIClientService 的 `*-mock` 降级响应当成真实 AI 结果返回 200；需求增强不能用空字段整行覆盖人工已填内容。
- 现场确认：
  - `ai_quote_estimate()` 原来拿到 AI 响应后直接 `_extract_json()`，只要 JSON 能解析就 200 返回。
  - `ai_enrich_requirement()` 原来同样不看 `model`，且需求表更新时固定写 `product_object/ct/interface/site/acceptance/safety` 六列，AI 空字符串会清掉已有人工值。
- 代码面：
  - 新增 `_raise_if_mock_ai_response()`，对 `model.endswith("-mock")` 的 AI 响应统一返回 502，当前接入报价估算和需求完善两个端点。
  - 新增 `_clean_ai_text()`，将 AI 空字符串和 `"null"` 当作无新值。
  - 需求表 upsert 改为增量：已有记录只更新 AI 非空字段；无记录时插入清洗后的字段，空值保持 `NULL`。
  - 响应里的 `requirement` 改返回合并后的当前字段，而不是仅返回本次 AI 原始字段。
- 验证：
  - 新增 `tests/unit/test_sales_opportunity_ai_mock_guard_pre08_09.py`，先红后绿：报价估算 `-mock` 返回 502；需求完善 `-mock` 返回 502 且不改人工字段；正常非 mock 部分字段返回时只合并非空字段。
  - `PYTHONPATH=. pytest -q tests/unit/test_sales_opportunity_ai_mock_guard_pre08_09.py tests/unit/test_presale_ai_mock_guard.py tests/unit/test_presale_requirement_bridge.py` 通过（14 个用例）。
  - `PYTHONPATH=. python -m py_compile app/api/v1/endpoints/sales/opportunity_workflow.py tests/unit/test_sales_opportunity_ai_mock_guard_pre08_09.py` 通过。
  - `PYTHONPATH=. ruff check app/api/v1/endpoints/sales/opportunity_workflow.py tests/unit/test_sales_opportunity_ai_mock_guard_pre08_09.py` 通过。

## 2026-07-04 继续：PRE-10/PRE-11 状态校正

- PRE-10：`tests/unit/test_presale_requirement_bridge.py` 在本轮 PRE-08/PRE-09 周边回归中再次通过，tracker 从“已修待验”校正为“已验证”。
- PRE-11：代码已存在 mock 守卫和 BOM 真实价格/待询价逻辑，`tests/unit/test_presale_ai_mock_guard.py` 在本轮回归中通过，tracker 从“待修”校正为“已验证”；本轮未新增 PRE-11 业务代码。

## 2026-07-04 继续：PRE-12/PRE-13 导出假成功止损

- PRE-12 现场对账：
  - 审计提到的 `presale_ai_export_service.py` / `presale_ai_routes.py` 源文件已不存在，只剩历史 pycache/跳过式旧测试引用。
  - `app/api/v1/api.py` 明确下线老 AI 方案栈：`presale_ai_routes` 不再注册，方案统一走 `/presale/proposals`。
  - 因此本轮未重建旧 PDF/Word/Excel 导出，只把 tracker 标为“已验证-旧链路下线”；后续若新方案栈要导出，应在 `/presale/proposals` 体系下重新设计，不要复活旧假成功路由。
- PRE-13 代码面：
  - `/presale/ai/export-report` 原来只拼 `file_url` 且 `file_size=0`，没有文件生成和下载路由。
  - 新增 CSV/XLSX/PDF 文件生成 helper，导出目录为 `settings.UPLOAD_DIR/presale_ai_reports`。
  - 返回真实 `file_name/file_size/file_url`；新增 `GET /presale/ai/downloads/{file_name}`，带文件名/path 安全检查。
- 验证：
  - 新增 `tests/unit/test_presale_ai_export_report_pre13.py`，先红后绿：导出 CSV 后文件真实存在、`file_size>0`、内容含 usage 记录，下载路由返回同一路径。
  - `PYTHONPATH=. pytest -q tests/unit/test_presale_ai_export_report_pre13.py tests/unit/test_presale_ai_integration_coverage.py` 通过（2 个用例）。
  - `PYTHONPATH=. python -m py_compile app/api/v1/presale_ai_integration.py tests/unit/test_presale_ai_export_report_pre13.py` 通过。
  - `PYTHONPATH=. ruff check app/api/v1/presale_ai_integration.py tests/unit/test_presale_ai_export_report_pre13.py` 通过。

## 2026-07-04 继续：PRE-14 售前工单状态字典统一

- 修复目标：售前工单不能同时存在 `PROCESSING` 和 `IN_PROGRESS` 两套“处理中”，`REVIEW` 也不能作为新建方案评审工单的死路状态。
- 代码面：
  - `TicketStatusEnum` 增加规范值 `IN_PROGRESS`，保留 `PROCESSING/REVIEW` 作为历史兼容。
  - `tickets/utils.py` 新增 `canonical_ticket_status()` 和 `expand_ticket_status_filter()`：响应层把 `PROCESSING` 归一为 `IN_PROGRESS`、`REVIEW` 归一为 `PENDING`；查询 `status=IN_PROGRESS/PENDING` 时同时命中历史别名。
  - `tickets/crud.py` 新建 `SOLUTION_REVIEW` 工单 now 直接 `PENDING`，不再落 `REVIEW`；列表筛选使用扩展状态集合。
  - `tickets/operations.py` 接单和进度更新按规范状态判断，历史 `REVIEW` 可作为待接单接单，历史 `PROCESSING` 可继续更新进度并落新状态 `IN_PROGRESS`。
  - 看板/分析/任务管理活跃状态集合加入 `IN_PROGRESS`。
  - 新增 `migrations/20260704_presale_ticket_status_normalization_sqlite.sql` 清洗存量 `PROCESSING→IN_PROGRESS`、`REVIEW→PENDING`。
- 验证：
  - 新增 `tests/unit/test_presale_ticket_status_pre14.py`，先红后绿：`PROCESSING` 可按 `IN_PROGRESS` 查询和更新；`REVIEW` 响应为 `PENDING` 且可接单；新建 `SOLUTION_REVIEW` 返回 `PENDING`。
  - `PYTHONPATH=. pytest -q tests/unit/test_presale_ticket_status_pre14.py` 通过（3 个用例）。
  - `PYTHONPATH=. python -m py_compile app/models/presale/core.py app/api/v1/endpoints/presale/tickets/utils.py app/api/v1/endpoints/presale/tickets/crud.py app/api/v1/endpoints/presale/tickets/operations.py app/api/v1/endpoints/presale/dashboard.py app/api/v1/endpoints/presale/analytics.py app/api/v1/endpoints/presale/task_management.py tests/unit/test_presale_ticket_status_pre14.py` 通过。
  - `PYTHONPATH=. ruff check app/models/presale/core.py app/api/v1/endpoints/presale/tickets/utils.py app/api/v1/endpoints/presale/tickets/crud.py app/api/v1/endpoints/presale/tickets/operations.py app/api/v1/endpoints/presale/dashboard.py app/api/v1/endpoints/presale/analytics.py app/api/v1/endpoints/presale/task_management.py tests/unit/test_presale_ticket_status_pre14.py` 通过。
  - 迁移 SQL 在临时 SQLite 库实测通过：结果为 `IN_PROGRESS|1`、`PENDING|2`。
  - API 级 `tests/api/test_presales_contract_api.py -k ticket_update_and_complete_accept_json_body` 未作为通过证据：本地 TestClient/httpx 版本不兼容，fixture 初始化时报 `Client.__init__() got an unexpected keyword argument 'app'`，未进入业务断言。

## 2026-07-04 继续：PRE-15 售前移动端假实现下线

- 修复目标：`/presale-mobile` 整域不能继续暴露硬编码 AI 问答、STT/TTS、拜访准备、快速估价和客户快照；前端无任何消费，属于僵尸假实现。
- 现场确认：
  - `frontend/src` 无 `/presale-mobile` 调用；生产移动端页面走 `/mobile/*`。
  - `presale_mobile_service.py` 仍含大量模拟返回，但仅通过 `api.py` 的 `/presale-mobile` 挂载暴露。
- 代码面：
  - `app/api/v1/api.py` 移除 `/presale-mobile` router include，改为显式下线注释。
  - 保留服务/endpoint 源码不删除，避免影响旧 import 测试；后续若要做实，应在真实移动端产品入口重新设计 AI/语音/估价链路。
- 验证：
  - 新增 `tests/unit/test_presale_mobile_downline_pre15.py`，先红后绿：`api.py` 不再包含 `prefix="/presale-mobile"` 或 `tags=["presale-mobile"]`。
  - `PYTHONPATH=. pytest -q tests/unit/test_presale_mobile_downline_pre15.py` 通过（1 个用例）。
  - `PYTHONPATH=. python -m py_compile app/api/v1/api.py tests/unit/test_presale_mobile_downline_pre15.py` 通过。
  - `PYTHONPATH=. ruff check app/api/v1/api.py tests/unit/test_presale_mobile_downline_pre15.py` 通过。

## 2026-07-04 继续：PRE-17/PRE-18 状态校正

- `PYTHONPATH=. pytest -q tests/unit/test_text_similarity_retrieval.py` 通过（4 个用例），覆盖中文 bigram 相似度、模板检索、知识库相似度、相似案例粗召回+精排。
- tracker 将 PRE-17 从“已修待验(短期)”校正为“已验证(短期)”，PRE-18 从“已修待验”校正为“已验证”。

## 2026-07-04 继续：PRE-20 AI 工作流空壳止损

- 修复目标：`/presale/ai/workflow/start` 不能在没有执行器的情况下把第一步置为 `RUNNING`，让用户误以为工作流正在自动执行。
- 代码面：
  - `PresaleAIIntegrationService.start_workflow(auto_run=True)` now 直接 `ValueError`，不创建任何日志。
  - `auto_run=False` 保留为“创建待执行计划”：5 个步骤均为 `PENDING`，用于后续真实执行器接入。
  - API 层将该 `ValueError` 转为 HTTP 501，明确表达“自动运行执行器未实现”。
- 验证：
  - 新增 `tests/unit/test_presale_ai_workflow_pre20.py`，先红后绿：`auto_run=True` 拒绝且不落库；`auto_run=False` 创建 5 条全 `PENDING` 计划，状态查询为 pending/0%。
  - `PYTHONPATH=. pytest -q tests/unit/test_presale_ai_workflow_pre20.py tests/unit/test_presale_ai_integration_coverage.py tests/unit/test_presale_ai_export_report_pre13.py` 通过（4 个用例）。
  - `PYTHONPATH=. python -m py_compile app/services/presale/presale_ai_integration.py app/api/v1/presale_ai_integration.py tests/unit/test_presale_ai_workflow_pre20.py` 通过。
  - `PYTHONPATH=. ruff check app/services/presale/presale_ai_integration.py app/api/v1/presale_ai_integration.py tests/unit/test_presale_ai_workflow_pre20.py` 通过。

## 2026-07-04 继续：PRE-24 遗留脏数据字典收敛

- 修复目标：`presale_ai_quotation.quotation_type` 存量非法值不能导致历史列表 ORM Enum 加载崩溃；`opportunities.assessment_status` 不能继续同时写/查 `REQUESTED`、`ASSESSMENT_COMPLETED` 和规范状态。
- 现场确认：
  - `data/app.db.presale_ai_quotation.quotation_type` 含 `AUTO/MANUAL/NORMAL`，以及合法的 `BASIC/STANDARD/PREMIUM`（SQLAlchemy Enum 实际存大写 name）。
  - `data/app.db.opportunities.assessment_status` 为 `ASSESSMENT_COMPLETED(51)`、`COMPLETED(4)`、空值 191。
  - 单条报价读取已有 PRE-07 raw SQL 兼容；历史列表仍 ORM `.all()`，碰到非法 Enum 会 `LookupError`。
- 代码面：
  - 新增 `app/services/presale/assessment_status.py`：统一 `REQUESTED→PENDING`、`ASSESSMENT_IN_PROGRESS→IN_PROGRESS`、`ASSESSMENT_COMPLETED→COMPLETED`，并提供未完成/已完成 SQL 谓词。
  - `request_presale_support` 写入侧改为 `PENDING`，不再新增 `REQUESTED`。
  - 销售工作流预警与 AI Copilot “我的一天”缺评统计改用统一未完成评估谓词，兼容旧 `REQUESTED` 和规范 `PENDING/IN_PROGRESS`。
  - `AIQuotationGeneratorService.get_quotation_history()` 改 raw SQL 读取并复用归一化响应转换，避免非法 `AUTO/MANUAL/NORMAL` 触发 ORM Enum `LookupError`。
  - 新增 `migrations/20260704_presale_legacy_dictionary_cleanup_sqlite.sql`，清洗报价档位与商机评估状态；未直接改真实 `data/app.db`。
- 验证：
  - 新增 `tests/unit/test_presale_legacy_dictionary_pre24.py`，先红后绿：报价历史非法类型归一为 `standard`；申请售前支持落 `PENDING`；缺评统计包含 `REQUESTED/PENDING/IN_PROGRESS/ASSESSMENT_IN_PROGRESS`，排除 `COMPLETED/ASSESSMENT_COMPLETED`。
  - `PYTHONPATH=. pytest -q tests/unit/test_presale_legacy_dictionary_pre24.py` 通过（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_presale_legacy_dictionary_pre24.py tests/unit/test_sales_opportunity_ai_mock_guard_pre08_09.py tests/unit/test_presale_ai_quotation_pre07.py tests/unit/test_presale_ai_quotation_pre05_06.py` 通过（10 个用例）。
  - `python -m py_compile app/services/presale/assessment_status.py app/services/presale/presale_ai_quotation_service.py app/api/v1/presale_ai_quotation.py app/api/v1/endpoints/sales/opportunity_workflow.py app/api/v1/endpoints/ai_copilot.py` 通过。
  - `ruff check app/services/presale/assessment_status.py app/services/presale/presale_ai_quotation_service.py app/api/v1/presale_ai_quotation.py app/api/v1/endpoints/sales/opportunity_workflow.py app/api/v1/endpoints/ai_copilot.py tests/unit/test_presale_legacy_dictionary_pre24.py` 通过。
  - 迁移 SQL 在临时 SQLite 库实测通过：`AUTO/MANUAL/NORMAL/空值→STANDARD`，`REQUESTED→PENDING`，`ASSESSMENT_IN_PROGRESS→IN_PROGRESS`，`ASSESSMENT_COMPLETED→COMPLETED`，空评估状态保持 `NULL`。

## 2026-07-04 继续：PRE-04 立项关卡拒绝自动空评估

- 修复目标：售前工单/方案完成时不能自动补一条 `COMPLETED + 推荐立项` 空评估就满足 PMO 立项关卡；立项必须依赖真实技术评估内容。
- 现场确认：
  - `complete_presale_source_assessment()` 找不到评估时会自动创建 `status=COMPLETED`、`decision=推荐立项`、`evaluated_at=now` 的空评估。
  - `submit_initiation()` 原来只检查交接包里有 `technical_assessment.current` 且 status 为 `COMPLETED`，没有检查评分/维度/风险/条件等实际内容。
- 代码面：
  - `TechnicalAssessment` 新增 `auto_generated` 字段；SQLite runtime schema patch 会自动补列。
  - 自动补建评估 now `auto_generated=True`；真实 `TechnicalAssessmentService.evaluate()` 完成评估时标回 `False`。
  - 交接包 `_build_technical_assessment_payload()` 输出 `auto_generated`。
  - PMO 关卡新增实质内容判定：`auto_generated=True` 直接不通过；非自动评估也必须至少有 `total_score/dimension_scores/item_scores/risks/similar_cases/conditions/ai_analysis/veto_rules` 之一。
  - 新增 `migrations/20260704_presale_assessment_auto_generated_sqlite.sql`：补列并把历史 `COMPLETED + 推荐立项 + 无评分/无维度/无风险/无内容` 记录标成占位评估；未直接改真实 `data/app.db`。
- 验证：
  - 新增 `tests/unit/test_presale_assessment_completion_pre04.py`，先红后绿：自动补建评估必须 `auto_generated=True`。
  - `test_pmo_initiation_service.py` 新增红绿用例：`COMPLETED` 但 `auto_generated=True` 且无实质内容时，提交立项抛 `缺少实际评估内容`。
  - `PYTHONPATH=. pytest -q tests/unit/test_pmo_initiation_service.py tests/unit/test_presale_assessment_completion_pre04.py tests/unit/test_technical_assessment_service.py tests/unit/test_presale_ticket_status_pre14.py` 通过（71 个用例）。
  - `python -m py_compile app/models/sales/technical_assessment.py app/models/base.py app/services/presale_assessment_completion.py app/services/technical_assessment_service.py app/services/project_workspace_service.py app/services/pmo_initiation/service.py app/api/v1/endpoints/sales/assessments/assessments.py app/schemas/sales/assessments.py tests/unit/test_presale_assessment_completion_pre04.py tests/unit/test_pmo_initiation_service.py` 通过。
  - `ruff check app/models/sales/technical_assessment.py app/models/base.py app/services/presale_assessment_completion.py app/services/technical_assessment_service.py app/services/project_workspace_service.py app/services/pmo_initiation/service.py app/api/v1/endpoints/sales/assessments/assessments.py app/schemas/sales/assessments.py tests/unit/test_presale_assessment_completion_pre04.py tests/unit/test_pmo_initiation_service.py` 通过。
  - 迁移 SQL 在临时 SQLite 库实测：历史空评估 `auto_generated=1`，有真实分数的完成评估和 PENDING 不变。

## 2026-07-04 继续：PROJ-02 立项审批必须指定 PM

- 修复目标：立项审批通过时不能在未指定项目经理的情况下把申请置为 `APPROVED`，否则会出现“已批准但未创建项目”的断链状态。
- 现场确认：
  - `PmoInitiationService.approve_initiation()` 原逻辑先写 `status=APPROVED`，仅当 `approved_pm_id` 存在时才调用 `_create_project_from_initiation()`。
  - 前端 `ReviewInitiationDialog` 有“暂不指定”选项，空 PM 时仍可提交审批通过。
- 代码面：
  - `approve_initiation()` now 在任何状态写入前检查 `approved_pm_id`，缺失则 `ValueError("审批通过必须指定项目经理，否则不会创建项目")`，不 add/commit。
  - 前端审批弹窗 now 空 PM 时 alert `审批通过前必须指定项目经理`，不调用 `onSubmit`；下拉占位改为 `请选择项目经理`。
- 验证：
  - `tests/unit/test_pmo_initiation_service.py` 将旧“无 PM 可审批通过”测试改为红绿回归：缺 PM 必须抛错，状态保持 `SUBMITTED`，不提交 DB。
  - 新增 `frontend/src/pages/InitiationManagement/components/__tests__/ReviewInitiationDialog.test.jsx`，覆盖空 PM 阻断和选中 PM 正常提交。
  - `PYTHONPATH=. pytest -q tests/unit/test_pmo_initiation_service.py` 通过（37 个用例）。
  - `npm --prefix frontend test -- --run src/pages/InitiationManagement/components/__tests__/ReviewInitiationDialog.test.jsx --silent` 通过（2 个用例）。
  - `python -m py_compile app/services/pmo_initiation/service.py tests/unit/test_pmo_initiation_service.py` 通过。
  - `ruff check app/services/pmo_initiation/service.py tests/unit/test_pmo_initiation_service.py` 通过。
  - `npm exec eslint src/pages/InitiationManagement/components/ReviewInitiationDialog.jsx src/pages/InitiationManagement/components/__tests__/ReviewInitiationDialog.test.jsx`（cwd=`frontend`）通过。

## 2026-07-04 继续：PROJ-03 合同立项带真实字段

- 修复目标：合同列表/合同详情发起 PMO 立项时不能直接后台创建一条 `由合同 xxx 发起立项` 的占位需求；应把合同真实需求、金额、客户、编号、交付日期带到立项表单，由人确认后创建。
- 现场确认：
  - `ContractManagement.handleCreateProject()` 原来查重后直接调用 `pmoApi.initiations.create()`，`requirement_summary` 固定拼占位文本。
  - `ContractDetail.handleCreateInitiation()` 同样直接创建占位立项。
  - `InitiationManagement` 只识别 `handoff=presale`，不识别 `handoff=contract`。
- 代码面：
  - 新增 `buildContractInitiationPath()`，统一把合同字段映射为 `/pmo/initiations?handoff=contract...`，优先带出真实 `requirement_summary/requirement_description/scope/technical_requirements`，不再生成占位需求。
  - 合同列表 normalize now 保留需求、交付日期、金额、客户、方案等立项交接字段。
  - 合同列表页/详情页 now 保留“已有立项则打开详情”，没有已有立项则跳转新建立项表单，不直接创建草稿。
  - 立项页 now 识别 `handoff=contract` 并预填字段；合同交接不调用售前 workbench 上下文。
- 验证：
  - 新增/更新前端红绿用例：合同列表入口、合同详情入口、立项页 contract handoff 预填。
  - `npm --prefix frontend test -- --run src/pages/__tests__/ContractManagement.test.jsx src/pages/__tests__/ContractDetail.test.jsx src/pages/__tests__/InitiationManagement.test.jsx --silent` 通过（14 个用例）。
  - `npm exec eslint src/pages/ContractManagement.jsx src/pages/ContractDetail.jsx src/pages/InitiationManagement/index.jsx src/pages/__tests__/ContractManagement.test.jsx src/pages/__tests__/ContractDetail.test.jsx src/pages/__tests__/InitiationManagement.test.jsx src/utils/pmoInitiations.js`（cwd=`frontend`）通过。
  - `git diff --check` 通过。

## 2026-07-04 继续：PROJ-04 项目阶段/状态禁止跨级直跳

- 修复目标：项目阶段和状态不能通过 direct PUT 或 `stage-advance` 从 `S1→S9`、`ST01→ST30` 这类跨级直跳绕过阶段门。
- 现场确认：
  - `projects/status/status_crud.py` direct PUT 只校验枚举值，不校验旧值到新值是否合法。
  - `stage_advance_service.validate_stage_advancement()` 原来允许任意向前跳，只拒绝倒退/相同阶段。
  - direct PUT 历史日志回调参数名与 `StatusUpdateService` 不匹配，导致更新成功但日志回调报 warning。
- 代码面：
  - direct PUT 阶段/状态更新 now 增加顺序流转守卫：当前值必须有效，且只能转换到下一阶段/下一状态；相同值仍按“未变化”处理。
  - `stage-advance` now 只能推进到相邻下一阶段，`S1→S9`、`S2→S5` 均返回 400。
  - 修复 `history_cb(..., reason=None)` 参数名，恢复 direct PUT 状态日志写入。
- 验证：
  - 新增 `tests/unit/test_project_status_guard_proj04.py`，先红后绿覆盖 `S1→S9`、`ST01→ST30` 拒绝且原值不变。
  - 更新旧测试预期：跨级跳转不再视为合法推进。
  - `PYTHONPATH=. pytest -q tests/unit/test_project_status_guard_proj04.py tests/unit/test_stage_advance_service.py tests/unit/test_service_edge_cases.py tests/unit/test_state_machines_depth.py` 通过（124 个用例）。
  - `PYTHONPATH=. ruff check app/api/v1/endpoints/projects/status/status_crud.py app/services/stage_advance_service.py tests/unit/test_project_status_guard_proj04.py tests/unit/test_stage_advance_service.py tests/unit/test_service_edge_cases.py` 通过。
  - `PYTHONPATH=. python -m py_compile app/api/v1/endpoints/projects/status/status_crud.py app/services/stage_advance_service.py tests/unit/test_project_status_guard_proj04.py tests/unit/test_stage_advance_service.py tests/unit/test_service_edge_cases.py` 通过。
  - API TestClient 节点受当前本地 `starlette TestClient` / `httpx` 版本不兼容阻断，报 `Client.__init__() got an unexpected keyword argument 'app'`，未作为本次逻辑失败处理。

## 2026-07-04 继续：PROJ-05 项目 status 三套词汇表清洗

- 修复目标：`projects.status` 不再混用 `COMPLETED/EXECUTING/archived/STxx`；读侧兼容旧数据，写侧收口到 `stage + STxx`，归档只使用 `is_archived`。
- 现场确认：
  - 本地 `data/app.db` 只读统计存在 `COMPLETED=45`、`EXECUTING=35`、`ST01=24`，旧完成行均有 `actual_end_date`。
  - `archive_project()` 原来把 `status` 写成 `archived`；`ai_delivery` 和部分定时/报表/成本入口仍按 `EXECUTING/COMPLETED` 或误把 `S4/S5` 写在 `status` 字段上过滤。
- 代码面：
  - 新增 `app/services/project_status_normalization.py`：统一提供旧状态归一化、打开项目、交付项目、已完成、归档、取消和状态筛选 helper。
  - 项目列表/导出/QueryOptimizer/KPI/报表中心/PMO cockpit/项目统计/定时任务/AI 交付/AI 产能/预算/成本超支/延期/排产/资源冲突/历史复用等入口改用 helper 或 `Project.stage`。
  - 归档接口 now 只写 `is_archived=True/False`，保留原 `status`，状态日志 old/new status 均记录真实旧状态。
  - 新增 `migrations/20260704_project_status_normalization_sqlite.sql`：`COMPLETED/CLOSED/DONE/FINISHED → S9/ST30`；`EXECUTING/IN_PROGRESS/ACTIVE/ARCHIVED/空值 → 当前 stage 对应 STxx`；旧 `ARCHIVED` 同时置 `is_archived=1`。
- 验证：
  - 新增 `tests/unit/test_project_status_normalization_proj05.py`，覆盖旧状态归一化、open/delivery 过滤、旧 status 参数兼容、归档不污染 status。
  - 迁移 SQL 在临时 SQLite 库实测通过：`COMPLETED/S3→ST30/S9/H4`，`EXECUTING/S5→ST10/S5`，`archived/S4→ST07/S4/is_archived=1`，`NULL/S2→ST03/S2`。
  - `PYTHONPATH=. pytest -q tests/unit/test_project_status_normalization_proj05.py` 通过（4 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_project_status_normalization_proj05.py tests/unit/test_project_status_guard_proj04.py tests/services/test_otd_scan_service.py tests/unit/test_analysis_reports_rpt03.py tests/unit/test_project_monthly_report_rpt02.py tests/unit/test_resource_overview_misc02.py` 通过（29 个用例）。
  - `PYTHONPATH=. pytest -q tests/services/test_query_optimizer.py tests/unit/test_cache_service.py` 通过（49 个通过，1 个 Redis 依赖按原配置跳过）。
  - `PYTHONPATH=. ruff check ...`（PROJ-05 涉及 Python 文件 + 新测试）通过；`PYTHONPATH=. python -m py_compile ...` 通过；`git diff --check` 通过。

## 2026-07-04 继续：PROJ-07 阶段门旁路收口

- 修复目标：S8→S9 必须经过阶段门；终验收通过不能直接写项目 `stage=S9` 绕过回款率门；superuser 不能未显式跳过就自动免检。
- 现场确认：
  - `perform_gate_check()` 在 `skip_gate_check=False` 时仍对 `current_user_is_superuser=True` 直接返回通过。
  - `trigger_warranty_period()` 在 FINAL 验收通过时直接 `project.stage="S9"`、`actual_end_date=today`，不看 S8→S9 的回款率/终验收/设备交付门。
  - 旧 async `acceptance/acceptance_service.py::_update_project_to_warranty()` 也会直接把 `S8/ST08` 写成 `S9/ST30`。
  - 扩展回归时发现 `stage_transition_checks.execute_stage_transition()` 仍导入旧路径 `app.api.v1.endpoints.projects.utils.check_gate`，在当前包结构/测试替身下会断，影响自动阶段流转链路。
- 代码面：
  - `perform_gate_check()` now 只有 `skip_gate_check=True` 且 superuser 才跳门，并返回 `{"skipped": True, "reason": "管理员显式跳过阶段门校验"}`；superuser 未显式跳过时同普通用户一样执行真实 gate。
  - `advance_project_stage()` now 对显式跳门的响应保留 skip 结果，并把 `管理员显式跳过阶段门校验` 写进阶段变更日志原因。
  - `trigger_warranty_period()` now 先调用 `check_auto_stage_transition_after_acceptance()`；若 S8→S9 自动流转未通过且项目仍非 S9，则不写实际结束日期、不更新机台 S9。
  - 旧 async 验收服务 now 只在项目已是 S9/ST30 时补质保字段，不再负责推进阶段。
  - `stage_transition_checks` now 解析真实 `projects.gate_checks.check_gate`，同时兼容旧测试 patch 路径。
- 验证：
  - `tests/unit/test_stage_advance_service.py` 新增红绿：superuser 未显式 skip 时必须执行 gate；显式 skip 返回跳门痕迹。
  - `tests/unit/test_acceptance_completion_service.py` 新增红绿：终验收自动流转被回款门挡住时项目保持 S8。
  - `tests/unit/test_acceptance_service.py` 新增红绿：旧 async 服务不能 S8→S9 直推，已入 S9 时才补质保字段。
  - `PYTHONPATH=. pytest -q tests/unit/test_stage_advance_service.py tests/unit/test_acceptance_completion_service.py tests/unit/test_acceptance_service.py tests/unit/test_stage_transition_checks.py tests/unit/test_stage_transition_checks_service.py tests/unit/test_stage_transition_service.py tests/unit/test_project_status_guard_proj04.py` 通过（99 个通过，8 个按现有测试数据条件跳过）。
  - `PYTHONPATH=. ruff check app/services/stage_advance_service.py app/api/v1/endpoints/projects/status/stages.py app/services/acceptance_completion_service.py app/services/acceptance/acceptance_service.py app/services/stage_transition_checks.py tests/unit/test_stage_advance_service.py tests/unit/test_acceptance_completion_service.py tests/unit/test_acceptance_service.py` 通过。
  - `PYTHONPATH=. python -m py_compile app/services/stage_advance_service.py app/api/v1/endpoints/projects/status/stages.py app/services/acceptance_completion_service.py app/services/acceptance/acceptance_service.py app/services/stage_transition_checks.py tests/unit/test_stage_advance_service.py tests/unit/test_acceptance_completion_service.py tests/unit/test_acceptance_service.py` 通过；`git diff --check` 通过。

## 2026-07-04 继续：PROJ-08 任务进度加权汇总接线

- 修复目标：`aggregate_task_progress()` 不能把项目进度写成任务进度简单平均；应复用现有按 `estimated_hours` 加权的项目进度聚合口径。
- 现场确认：
  - `ProgressAggregationService.aggregate_project_progress()` 已经按 `estimated_hours` 计算 `overall_progress`。
  - `aggregate_task_progress()` 原来仍用 `sum(progress) / count(task)` 写回 `Project.progress_pct`，导致 1 小时任务和 9 小时任务等权。
  - 同函数阶段聚合仍看旧的 `TaskUnified.stage`，当前真实字段是 `project_stage`。
- 代码面：
  - `aggregate_task_progress()` now 调用 `ProgressAggregationService.aggregate_project_progress(project_id, db)["overall_progress"]` 写回项目进度。
  - 阶段聚合 now 用 `TaskUnified.project_stage` 过滤，并按 `estimated_hours` 加权；当总权重为 0 时回退平均值，避免除零。
  - 进度分支测试同步修正到当前 `TaskUnified`/`TaskForecastItem` schema，整份分支测试可直接运行。
- 验证：
  - 新增红绿用例：1 小时 100% + 9 小时 0% 的项目，`aggregate_task_progress()` 必须写回 10.0，不是 50.0。
  - `PYTHONPATH=. pytest -q tests/services/test_progress_service.py tests/services/test_progress_service_extended.py app/tests/services/project_management/test_progress_service_branches.py` 通过（74 个用例）。
  - `ruff check app/services/progress_service.py app/tests/services/project_management/test_progress_service_branches.py tests/services/test_progress_service.py tests/services/test_progress_service_extended.py` 通过。
  - `python -m py_compile app/services/progress_service.py app/tests/services/project_management/test_progress_service_branches.py tests/services/test_progress_service.py tests/services/test_progress_service_extended.py` 通过；`git diff --check` 通过。

## 2026-07-04 继续：PROJ-09 甘特依赖驱动排期级联

- 修复目标：甘特依赖不能只保存画线关系；新增依赖后应按依赖类型和 lag_days 推迟后继任务计划日期，并继续影响后续链路；关键路径也不能把所有依赖都当 FS 串行长度。
- 现场确认：
  - `add_dependency()` 原来只插入 `task_dependencies`，不改 `task_unified.plan_start_date/plan_end_date`。
  - `get_critical_path()` 原来用 `longest_path_to(predecessor) + lag_days`，未使用 FS/SS/FF/SF 语义。
  - 单元测试库已有 ORM `task_dependencies` 表，缺少该 endpoint 假定的 `created_at`，`_ensure_table()` 只补 `project_id`。
- 代码面：
  - `_ensure_table()` now 幂等补齐历史表的 `created_at` 列。
  - 新增 `_cascade_reschedule_project()`：读取项目任务和依赖，按 FS/SS/FF/SF + lag_days 计算后继最早开始日，只向后推迟、不自动提前；任务被推迟后继续迭代级联后续任务。
  - `add_dependency()` now 在同一事务内插入依赖并执行级联重排，响应返回 `schedule_adjustments`，前端可据此刷新甘特图。
  - `get_critical_path()` now 基于依赖类型计算 earliest start/finish：FS 看前置完成，SS 看前置开始，FF/SF 通过后继工期反推开始日。
- 验证：
  - 新增 `tests/unit/test_gantt_dependency_proj09.py`，覆盖 FS A→B→C 级联推迟、SS lag 语义、SS 关键路径不误算成串行 9 天。
  - `PYTHONPATH=. pytest -q tests/unit/test_gantt_dependency_proj09.py` 通过（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_gantt_dependency_proj09.py tests/schemas/test_progress.py::TestGanttTaskItem tests/schemas/test_progress.py::TestTaskDependencyCreate` 通过（7 个用例）。
  - `ruff check app/api/v1/endpoints/gantt_dependency.py tests/unit/test_gantt_dependency_proj09.py` 通过；`python -m py_compile app/api/v1/endpoints/gantt_dependency.py tests/unit/test_gantt_dependency_proj09.py` 通过。

## 2026-07-04 继续：PROJ-11 成本归集口径收口

- 修复目标：成本归集不应等全量扫描才反映收货，不应把采购订单总额/下单日期当作实际成本，不应把在制工单按硬编码 200 元/小时入账。
- 代码面：
  - 采购成本 now 优先使用 `PurchaseOrder.received_amount`，税额按已收货金额比例折算，成本日期优先取显式收货日期，其次取最新未作废收货单日期。
  - `create_goods_receipt()` 和 `update_goods_receipt_status(...RECEIVED)` now 在同一事务内触发 `CostCollectionService.collect_from_purchase_order()`，收货创建/确认后即可更新项目实际成本。
  - 批量归集 now 覆盖 `RECEIVING/PARTIAL_RECEIVED/PARTIALLY_RECEIVED`，部分收货订单不必等全收才能补账。
  - 工单成本 now 只认 `COMPLETED/DONE`，`IN_PROGRESS` 会删除既有实际成本并重算项目；已完成工单按 `Worker.hourly_rate` 或显式传入费率计算，不再使用硬编码 200。
- 闭环补充：
  - `cancel_goods_receipt()` now 提供收货单作废入口，作废时回减订单行 `received_qty`、重算采购订单 `received_amount/status`，并调用成本归集删除/更新对应采购实际成本。
  - `collect_from_purchase_order()` now 在订单不处于收货/完成状态时删除旧采购成本并重算项目；收货金额归零时不再回退为订单总额。
  - `collect_from_ecn()` now 支持负向 `cost_impact` 作为冲减成本记录；`cost_impact == 0` 会删除既有 ECN 成本记录并重算，成本增加才触发预算预警。
  - 新增 `normalize_project_cost_records()`，按来源修复历史 `project_costs` 空 `source_module/cost_type/cost_category/cost_basis`；`BOM_COST` 旧默认 `ACTUAL` 会改回 `PLAN`，并重算受影响项目 actual_cost。
- 验证：
  - `PYTHONPATH=. pytest -q tests/services/test_cost_collection_business_docs.py` 通过（6 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_m2_cost_purchase_notification_strategy.py::TestCostCollectionService tests/unit/test_cost_collection_n3.py tests/unit/test_cost_collection_service_coverage.py` 通过（46 个用例）。
  - `PYTHONPATH=. pytest -q tests/services/test_cost_collection_business_docs.py tests/unit/test_m2_cost_purchase_notification_strategy.py::TestCostCollectionService tests/unit/test_cost_collection_n3.py tests/unit/test_cost_collection_service_coverage.py` 通过（52 个用例）。
  - `ruff check app/services/cost/cost_collection_service.py app/api/v1/endpoints/purchase/receipts.py tests/services/test_cost_collection_business_docs.py` 通过；`python -m py_compile app/services/cost/cost_collection_service.py app/api/v1/endpoints/purchase/receipts.py tests/services/test_cost_collection_business_docs.py` 通过。
  - `PYTHONPATH=. pytest -q tests/services/test_cost_collection_business_docs.py tests/api/test_purchase_receipts_workflow_contracts.py` 未能完成 API 层合约测试：当前本地 `starlette TestClient` / `httpx` 版本不兼容，初始化时报 `Client.__init__() got an unexpected keyword argument 'app'`，业务逻辑未执行。
  - `PYTHONPATH=. pytest -q tests/services/test_cost_collection_business_docs.py tests/unit/test_cost_collection_n3.py tests/unit/test_cost_collection_service_coverage.py tests/unit/test_m2_cost_purchase_notification_strategy.py::TestCostCollectionService` 通过（56 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_cost_forecast_branches.py::TestCostCollectionECN::test_collect_ecn_negative_cost_impact` 通过。
  - `ruff check app/services/cost/cost_collection_service.py app/api/v1/endpoints/purchase/receipts.py tests/services/test_cost_collection_business_docs.py tests/unit/test_cost_collection_n3.py tests/unit/test_cost_collection_service_coverage.py tests/unit/test_cost_forecast_branches.py` 通过。
  - `python -m py_compile app/services/cost/cost_collection_service.py app/api/v1/endpoints/purchase/receipts.py tests/services/test_cost_collection_business_docs.py tests/unit/test_cost_collection_n3.py tests/unit/test_cost_collection_service_coverage.py tests/unit/test_cost_forecast_branches.py` 通过。

## 2026-07-04 继续：PROJ-13 工时成本只认已审批工时

- 修复目标：成本超支分析里的人工成本、实际工时和人员归责不能把 `DRAFT/PENDING/SUBMITTED` 等未审批工时算入成本。
- 现场确认：
  - 第二轮审计已更正：`cost_overrun_analysis_service.py` 的时薪硬编码 100 半项已改为 `HourlyRateService`，剩余核心问题是审批状态过滤缺失。
  - `_calculate_labor_cost()`、`_calculate_actual_hours()`、`analyze_accountability()` 原来都只按 `Timesheet.project_id` 查询，未限制 `status == APPROVED`。
- 代码面：
  - `CostOverrunAnalysisService` 新增 `_approved_timesheet_query()`，人工成本和归责分析统一只读已审批工时。
  - `_calculate_actual_hours()` 同步加 `Timesheet.status == APPROVED`，避免成本原因判断里的“工时超支”被草稿/待审工时放大。
  - 修正旧测试中的过期 import 路径，从 `app.services.cost_overrun_analysis_service` 改为当前真实路径 `app.services.cost.cost_overrun_analysis_service`。
- 验证：
  - 新增真实 DB 回归：2h APPROVED + 10h DRAFT + 8h PENDING 只产生 2h、246 元人工成本；归责分析不包含未审批工时用户。
  - `PYTHONPATH=. pytest -q tests/unit/test_cost_overrun_analysis_service.py tests/unit/test_cost_overrun_analysis_service_coverage.py` 通过（10 个用例）。
  - `ruff check app/services/cost/cost_overrun_analysis_service.py tests/unit/test_cost_overrun_analysis_service.py tests/unit/test_cost_overrun_analysis_service_coverage.py` 通过；`python -m py_compile app/services/cost/cost_overrun_analysis_service.py tests/unit/test_cost_overrun_analysis_service.py tests/unit/test_cost_overrun_analysis_service_coverage.py` 通过。

## 2026-07-04 继续：PROJ-15 定时成本超支扫描排除计划成本

- 修复目标：`check_project_cost_overrun()` 不能直接 `sum(ProjectCost.amount)`，否则 BOM/计划成本会被当作实际成本触发误报。
- 代码面：
  - `project_scheduled_tasks.py` 引入 `actual_project_cost_filter()`。
  - 成本超支定时扫描 now 在 `ProjectCost.project_id == project.id` 外追加实际成本过滤，只统计 ACTUAL 口径；旧 `cost_basis IS NULL` 按既有兼容逻辑仍视为 ACTUAL。
- 验证：
  - 新增单元回归确认 `actual_project_cost_filter()` 被传入成本查询。
  - `PYTHONPATH=. pytest -q tests/unit/test_project_scheduled_tasks.py::TestCheckProjectCostOverrun tests/unit/test_scheduled_tasks_h2.py::TestProjectScheduledTasksExtended::test_check_project_cost_overrun_callable tests/unit/test_scheduled_tasks_h2.py::TestProjectScheduledTasksExtended::test_check_project_cost_overrun_no_projects` 通过（11 个用例）。
  - `ruff check app/utils/scheduled_tasks/project_scheduled_tasks.py tests/unit/test_project_scheduled_tasks.py` 通过；`python -m py_compile app/utils/scheduled_tasks/project_scheduled_tasks.py tests/unit/test_project_scheduled_tasks.py` 通过。

## 2026-07-04 继续：PROJ-18 四维健康趋势成本维修正

- 修复目标：健康趋势风险拆解的成本维不能一直满分；应从项目真实成本字段计算预算使用率，并识别当前系统真实成本超支枚举。
- 现场确认：
  - `Project` 模型只有 `budget_amount` 和 `actual_cost`，没有 `budget_used_pct` 字段，原 `_calc_cost_score()` 的预算使用率恒回 0。
  - `AlertRuleTypeEnum` 当前真实成本超支类型是 `COST_OVERRUN`，原代码仍匹配 `BUDGET_OVERRUN/COST_VARIANCE`。
- 代码面：
  - `HealthTrendService` 新增 `_budget_used_pct()`，按 `Project.actual_cost / Project.budget_amount * 100` 计算预算使用率。
  - `_calc_cost_score()` now 使用真实预算使用率参与成本效率扣分。
  - 成本类告警 now 匹配 `AlertRuleTypeEnum.COST_OVERRUN.value`，待处理成本超支告警每条扣 10 分。
  - 旧 `MagicMock` 冒烟用例收紧为明确的异常/回归断言，避免裸 mock 触发日期和计数魔法方法。
- 验证：
  - 新增真实 DB 回归：`actual_cost=150、budget=100、progress=50` 时成本分低于 100；`COST_OVERRUN` 待处理告警会把成本分扣到 90。
  - `PYTHONPATH=. pytest -q tests/unit/test_health_trend_service.py tests/unit/test_health_trend_service_coverage.py` 通过（12 个用例）。
  - `ruff check app/services/health_trend_service.py tests/unit/test_health_trend_service.py tests/unit/test_health_trend_service_coverage.py` 通过；`python -m py_compile app/services/health_trend_service.py tests/unit/test_health_trend_service.py tests/unit/test_health_trend_service_coverage.py` 通过。

## 2026-07-04 继续：PROJ-17/19 主健康度与快照分维可信化

- 修复目标：
  - 主健康度计算器不能继续只看状态/进度/问题/缺料而忽略成本风险。
  - 完全没有计划、进度、成本基线的数据不能默认 H1 绿灯。
  - 每日健康度快照不能继续把四个分维写成同一个总健康度，且不能把成本/进度指标硬编码 0。
- 现场确认：
  - `health_calculator.py` 原 `calculate_health()` 只做 H4/H3/H2/H1 级联，H2 风险未包含成本。
  - `project_scheduled_tasks.daily_health_snapshot()` 原写入 `schedule/cost/quality/resource_health = new_health`，`schedule_variance/cost_variance/budget_used_pct` 全为 0。
  - `project_health_tasks.daily_health_snapshot()` 是另一条同名快照实现，原只写综合健康度和少量计数，不写四维。
- 代码面：
  - `HealthTrendService` 新增公开 `calculate_dimension_scores(project)`，供快照复用 PROJ-18 修过的四维评分。
  - `HealthCalculator` 新增成本风险规则：预算未建但有实际成本、预算使用率 >100%、待处理 `COST_OVERRUN` 告警均判为 H2 风险。
  - `HealthCalculator` 新增无基线数据保护：计划、进度、成本基线全缺时不再返回 H1。
  - `HealthCalculator.build_health_snapshot_data()` 统一构建快照字段：四维健康度、综合分、未处理预警/问题、里程碑、进度偏差、预算使用率、成本偏差。
  - `project_scheduled_tasks.py` 和 `project_health_tasks.py` 两条快照任务 now 都调用同一套快照构造逻辑落库。
  - 顺手修正旧健康度分支测试里的过期模型用法：`AlertRule.condition` 和 `IssueTypeEnum.TASK` 已不是当前 schema。
- 验证：
  - 新增/修正回归覆盖：实际成本 125/预算 100 返回 H2；完全无健康度基线返回 H2；快照写入 cost_health、budget_used_pct、cost_variance、schedule_variance 等真实字段。
  - `PYTHONPATH=. pytest -q tests/unit/test_health_calculator.py tests/unit/test_health_calculator_coverage.py app/tests/services/project_management/test_health_calculator_branches.py tests/unit/test_project_scheduled_tasks.py::TestDailyHealthSnapshotInProjectScheduled tests/unit/test_project_health_tasks.py::TestDailyHealthSnapshot` 通过（65 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_health_trend_service.py tests/unit/test_health_trend_service_coverage.py` 通过（12 个用例）。
  - `ruff check app/services/health_calculator.py app/services/health_trend_service.py app/utils/scheduled_tasks/project_scheduled_tasks.py app/utils/scheduled_tasks/project_health_tasks.py tests/unit/test_health_calculator.py tests/unit/test_project_scheduled_tasks.py tests/unit/test_project_health_tasks.py app/tests/services/project_management/test_health_calculator_branches.py` 通过。
  - `python -m py_compile app/services/health_calculator.py app/services/health_trend_service.py app/utils/scheduled_tasks/project_scheduled_tasks.py app/utils/scheduled_tasks/project_health_tasks.py tests/unit/test_health_calculator.py tests/unit/test_project_scheduled_tasks.py tests/unit/test_project_health_tasks.py app/tests/services/project_management/test_health_calculator_branches.py` 通过；`git diff --check` 通过。

## 2026-07-04 继续：PROJ-20 变更审批回写项目基线

- 修复目标：项目变更请求审批通过后不能只改变更单状态；必须把已审批的时间/成本影响落实到项目基线，拒绝/退回不能动项目。
- 现场确认：
  - `ProjectChangeRequestsService.approve_change_request()` 原来只写 `ChangeRequest` 审批字段和 `ChangeApprovalRecord`，不写 `Project`、`ProjectMilestone` 或 `ProjectCost`。
  - `project_change_impact_service.execute_linkage()` 虽有 ECN 联动逻辑，但其模型强依赖 `ecn_id`，与普通 `ChangeRequest` 没有调用关系。
- 红测：
  - 新增 `tests/unit/test_project_change_baseline_proj20.py`，先失败在批准后查不到 `ProjectCost(source_type=CHANGE_REQUEST)`，且项目计划结束日/里程碑/实际成本未变化。
- 代码面：
  - `approve_change_request(...APPROVED...)` now 在同一事务调用 `_apply_approved_change_to_project_baseline()`。
  - 时间影响：`time_impact` 或 `impact_details.schedule.delay_days` 会顺延 `Project.planned_end_date`。
  - 里程碑影响：`impact_details.schedule.affected_milestones[].milestone_id` 指定时只更新指定里程碑；未指定时更新项目未完成里程碑。
  - 成本影响：`cost_impact` 或 `impact_details.cost.total/additional/amount` 会创建 ACTUAL 口径 `ProjectCost`，source 追溯到 `CHANGE_REQUEST`，并同步累加 `Project.actual_cost`。
  - 幂等保护：若同一变更已有成本记录则不重复累加；`impact_details.baseline_application` 记录应用时间、执行人、延期、里程碑更新和成本记录 ID。
  - 拒绝审批路径保持只更新变更状态，不改项目基线。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_project_change_baseline_proj20.py tests/unit/test_project_change_notifications_proj21.py` 通过（4 个用例）。
  - `ruff check app/services/project_change_requests/service.py tests/unit/test_project_change_baseline_proj20.py tests/unit/test_project_change_notifications_proj21.py` 通过。
  - `python -m py_compile app/services/project_change_requests/service.py tests/unit/test_project_change_baseline_proj20.py tests/unit/test_project_change_notifications_proj21.py` 通过；`git diff --check` 通过。

## 2026-07-04 继续：PROJ-14 预算超支预警链路接实

- 修复目标（本轮小切口）：成本归集后不能继续只调用简版 `CostAlertService.check_budget_execution()` 建预警记录；应接入富版 `BudgetAlertService.check_and_alert()`，让预算超支预警进入通知/动作中心链路。
- 现场确认：
  - `CostCollectionService._check_budget_alert()` 原来调用静态 `CostAlertService.check_budget_execution()`，只生成 `AlertRecord`。
  - 富版 `BudgetAlertService.check_and_alert()` 已存在，会构建预算执行状态、按黄/橙/红分级、创建/更新预警，并调用 `_dispatch_notifications()` 通知项目经理和部门负责人。
  - 成本归集中另有 ECN/BOM 两处直调旧服务，未统一走 helper。
- 代码面：
  - `CostCollectionService._check_budget_alert()` now 调 `BudgetAlertService(db).check_and_alert(project_id, trigger_source, source_id)`。
  - ECN 和 BOM 成本归集 now 也统一走 `_check_budget_alert()`。
  - 保留 `CostAlertService` legacy 导出作为旧测试/旧 patch 兼容目标，但实际链路不再使用它。
  - `tests/services/test_cost_collection_business_docs.py` 的 patch 点切到 `BudgetAlertService.check_and_alert`，并新增断言：采购成本归集必须调用富版预算预警服务。
- 闭环补充：
  - `BudgetAlertService` now 从启用的 `AlertRule` 读取预算阈值配置：`threshold_value`=黄色、`threshold_min`=橙色、`threshold_max`=红色；无规则时保持 `BudgetAlertConfig` 默认 80/90/100。
  - 新增 `check_budget_soft_intercept()`，用“已发生成本 + 已承诺成本 + 本次提交金额”计算 projected execution rate；预计触红时返回 `requires_approval=True`、`allowed=False`。
  - `purchase/orders_refactored.py#create_purchase_order` now 在写库前计算采购单金额并调用预算软拦截；无 override 时 409 且不落库，带 `budget_override=true` 时允许创建并在响应里回传 `budget_guard`。
  - 新增 `tests/unit/test_budget_alert_config_proj14.py`，覆盖阈值配置、红线软拦截、override 放行、采购入口不落库/放行两条路径。
- 验证：
  - `PYTHONPATH=. pytest -q tests/services/test_cost_collection_business_docs.py` 通过（7 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_m2_cost_purchase_notification_strategy.py::TestCostCollectionService tests/unit/test_cost_collection_n3.py tests/unit/test_cost_collection_service_coverage.py` 通过（46 个用例）。
  - `PYTHONPATH=. pytest -q tests/services/test_cost_collection_business_docs.py tests/unit/test_m2_cost_purchase_notification_strategy.py::TestCostCollectionService tests/unit/test_cost_collection_n3.py tests/unit/test_cost_collection_service_coverage.py` 通过（53 个用例）。
  - `ruff check app/services/cost/cost_collection_service.py tests/services/test_cost_collection_business_docs.py` 通过。
  - `python -m py_compile app/services/cost/cost_collection_service.py tests/services/test_cost_collection_business_docs.py` 通过；`git diff --check` 通过。
  - `PYTHONPATH=. pytest -q tests/unit/test_budget_alert_config_proj14.py` 通过（5 个用例）。
  - `PYTHONPATH=. pytest -q tests/services/test_cost_collection_business_docs.py tests/unit/test_m2_cost_purchase_notification_strategy.py::TestCostCollectionService tests/unit/test_cost_collection_n3.py tests/unit/test_cost_collection_service_coverage.py tests/unit/test_budget_alert_config_proj14.py` 通过（58 个用例）。
  - `ruff check app/services/budget_alert_service.py app/api/v1/endpoints/purchase/orders_refactored.py tests/unit/test_budget_alert_config_proj14.py` 通过。
  - `python -m py_compile app/services/budget_alert_service.py app/api/v1/endpoints/purchase/orders_refactored.py tests/unit/test_budget_alert_config_proj14.py` 通过。

## 2026-07-04 继续：PROJ-16 EVM 系统数据推导

- 修复目标：EVM 不能继续只依赖人工录入 PV/EV/AC/BAC；项目已有预算、计划起止、进度和实际成本时，应能自动生成当前挣值口径。
- 现场确认：
  - `EVMCalculator` 纯数学公式真实存在，问题在数据入口。
  - `/projects/{id}/costs/evm` 原来只读 `earned_value_data`，无手工快照直接 404。
  - `/projects/{id}/costs/evm/metrics` 原来要求前端同时传 `pv/ev/ac/bac`，仍是手填计算器。
- 代码面：
  - `EVMService.calculate_system_evm_data()` now 从项目真实字段推导 SYSTEM 快照：`BAC=Project.budget_amount`，`PV=BAC*计划完成率`，`EV=BAC*progress_pct`，`AC=Project.actual_cost`。
  - 计划完成率按 `planned_start_date/planned_end_date/period_date` 线性推导并夹在 0-100；无计划日期时回退项目实际进度。
  - `/evm` 和 `/evm/trend` now 优先用已记录快照，无快照时返回系统推导快照，不再把“没手工 EVM 数据”当业务 404。
  - `/evm/metrics` now 支持两种模式：传齐 `pv/ev/ac/bac` 时保持手工公式计算；不传时按项目自动推导；只传部分参数返回 400。
  - 修正 `EVMDataResponse.created_at` 类型为 `datetime`，避免真实模型时间戳被 date schema 拒绝。
  - 修正旧 EVM 场景测试：CPI<1 时标准 ETC 会高于剩余预算，断言改为标准公式结果。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_evm_system_data_proj16.py` 通过（4 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_evm_calculator.py tests/unit/test_batch2_evm_service.py tests/unit/test_i6_core_services.py::TestEVMCalculator tests/unit/test_evm_system_data_proj16.py` 通过（89 个用例）。
  - `ruff check app/services/evm_service.py app/api/v1/endpoints/projects/costs/evm.py tests/unit/test_evm_system_data_proj16.py tests/unit/test_evm_calculator.py` 通过。
  - `python -m py_compile app/services/evm_service.py app/api/v1/endpoints/projects/costs/evm.py tests/unit/test_evm_system_data_proj16.py tests/unit/test_evm_calculator.py` 通过。

## 2026-07-04 继续：PROD-01 现场调试接口落库

- 修复目标：`/field/tasks` 不能继续作为兼容假壳；签到、进度、问题、完工返回成功时必须写入现场调试真实表。
- 现场确认：
  - `field_commissioning.py` 原来 list/detail/dashboard/checkin/progress/issue/complete 全是空列表、404 或只返回成功消息。
  - `data/app.db` 已有 `field_tasks`、`field_checkins`、`field_issues` 三张表，但代码层缺少 ORM 模型和端点持久化路径。
- 代码面：
  - 新增 `app/models/field_commissioning.py`，注册 `FieldTask`、`FieldCheckin`、`FieldIssue`，并在 `app/models/__init__.py` 导出，隔离测试库也能 create_all。
  - `/field/tasks` now 从 `field_tasks` 读取，支持 `status/assigned_to` 筛选；`/field/dashboard` now 统计任务状态和未关闭问题。
  - `/field/tasks/{id}/checkin` now 校验任务与经纬度，写 `field_checkins`，并把 pending 任务推进为 in_progress。
  - `/progress` now 写 `field_tasks.progress/progress_note/status`；100% 时补完工时间。
  - `/issue` now 写 `field_issues`，并回填 `field_tasks.progress_note` 方便旧界面查看。
  - `/complete` now 写 `completed/progress=100/progress_note/completion_signature/completion_time`，兼容前端 `signature` 和 `completion_note`。
- 验证：
  - `PYTHONPATH=. pytest -q tests/api/test_field_commissioning_persistence_prod01.py` 通过（1 个用例，覆盖签到/进度/问题/完工真实落库）。
  - `PYTHONPATH=. pytest -q tests/audit_p0/test_p0_09_field_checkin_fake.py` 通过（3 个用例）。
  - `PYTHONPATH=. python -m py_compile app/api/v1/endpoints/field_commissioning.py app/models/field_commissioning.py tests/api/test_field_commissioning_persistence_prod01.py` 通过。
  - `PYTHONPATH=. python - <<'PY' ...` 导入 `app.models.field_commissioning` 和现场调试 router 通过（router routes=7）。
  - `ruff check app/api/v1/endpoints/field_commissioning.py app/models/field_commissioning.py tests/api/test_field_commissioning_persistence_prod01.py` 通过。
  - `git diff --check -- app/api/v1/endpoints/field_commissioning.py app/models/field_commissioning.py app/models/__init__.py tests/api/test_field_commissioning_persistence_prod01.py FUNCTIONAL_AUDIT_TRACKER.md PROJECT_NOTES.md` 通过。

## 2026-07-04 继续：AS-04 工程师派工冲突检测

- 修复目标：工程师冲突检测不能因为 `engineer_task_assignments` 缺表而静默返回 0；安装调试派工也不能绕过冲突检测直接派单。
- 现场确认：
  - `tests/audit_p0/test_p0_14_dispatch_conflict.py` 红灯：沙箱库缺 `engineer_task_assignments`，重叠任务无法插入，冲突检测空转。
  - `EngineerSchedulingService.detect_task_conflicts()` 已有重叠算法骨架，但依赖事实表和日期规范化不足。
- 代码面：
  - 新增 `migrations/20260704_engineer_task_assignments_sqlite.sql`，并对本地 `data/app.db` 执行非破坏性建表/重建，保留 SQLite 时间戳默认值，满足审计沙箱直接复制真实库的前置。
  - `EngineerSchedulingService.ensure_task_assignment_table()` now 用 SQLite 原生 DDL 幂等建表，不再用会产生无默认时间戳的 ORM DDL；`_query_task_assignments()` 不再缺表返回 `[]`。
  - `detect_task_conflicts()` now 规范化 `planned_start_date/planned_end_date` 字符串，非法日期返回 400；重叠区间返回 `conflict_project_id/overlap_start/overlap_end`。
  - `/engineer-scheduling/assignments` 统一走同一建表入口。
  - `installation_dispatch/workflow.py#assign` 和 `batch-assign` now 在状态机前调用冲突检测；有不同项目重叠任务时返回 409，并把成功派工同步为 `EngineerTaskAssignment(IDISPATCH-{order_id})`，作为后续冲突事实。
- 验证：
  - `PYTHONPATH=. pytest -q tests/audit_p0/test_p0_14_dispatch_conflict.py` 通过（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_dispatch_conflict_guard_as04.py` 通过（1 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_engineer_scheduling_service_coverage.py` 通过（18 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_production_services_integration.py -k detect_task_conflicts` 通过（1 个用例）。
  - `PYTHONPATH=. pytest -q tests/audit_p0/test_p0_14_dispatch_conflict.py tests/unit/test_dispatch_conflict_guard_as04.py -m 'audit_p0 or not audit_p0'` 通过（4 个用例）。
  - `ruff check app/api/v1/endpoints/field_commissioning.py app/models/field_commissioning.py tests/api/test_field_commissioning_persistence_prod01.py app/services/engineer_scheduling_service.py app/api/v1/endpoints/engineer_scheduling.py app/api/v1/endpoints/installation_dispatch/workflow.py tests/unit/test_dispatch_conflict_guard_as04.py tests/audit_p0/test_p0_14_dispatch_conflict.py tests/unit/test_engineer_scheduling_service_coverage.py` 通过。
  - `PYTHONPATH=. python -m py_compile app/api/v1/endpoints/field_commissioning.py app/models/field_commissioning.py tests/api/test_field_commissioning_persistence_prod01.py app/services/engineer_scheduling_service.py app/api/v1/endpoints/engineer_scheduling.py app/api/v1/endpoints/installation_dispatch/workflow.py tests/unit/test_dispatch_conflict_guard_as04.py tests/audit_p0/test_p0_14_dispatch_conflict.py tests/unit/test_engineer_scheduling_service_coverage.py` 通过。
  - `git diff --check -- app/services/engineer_scheduling_service.py app/api/v1/endpoints/engineer_scheduling.py app/api/v1/endpoints/installation_dispatch/workflow.py app/models/__init__.py tests/unit/test_dispatch_conflict_guard_as04.py tests/audit_p0/test_p0_14_dispatch_conflict.py migrations/20260704_engineer_task_assignments_sqlite.sql data/app.db` 通过。

## 2026-07-04 继续：HR-10 工程师绩效结果落库

- 修复目标：工程师五维绩效不能继续只算维度分、`performance_result` 读出来全空；计算入口必须把总分、等级、五维分项和岗位信息写回结果表，供排名和奖金链读取。
- 现场确认：
  - `PerformanceCalculator.calculate_dimension_score()` 能返回五维分，但不落库。
  - `EngineerPerformanceService` 原来只有算分/排名读取，没有“计算并保存 PerformanceResult”的入口。
  - `data/app.db.performance_result` 存在空壳行：只有 `period_id/user_id`，`total_score/job_type/level` 等关键字段为空。
  - `app.models.__init__` 原来未导入工程师绩效模型，测试/初始化通过 `app.models` create_all 时不会注册 `engineer_profile/engineer_dimension_config` 等表。
- 红测：
  - 新增 `tests/unit/test_engineer_performance_result_persistence_hr10.py`，先红在 `EngineerPerformanceService` 缺少 `calculate_and_save_result()`。
  - 测试覆盖：计算后必须生成完整 `PerformanceResult`；五维分、总分、等级、岗位、部门、排名、indicator_scores 均非空；重复计算更新同一行不重复插入。
- 代码面：
  - `EngineerPerformanceService.calculate_and_save_result()` now 解析周期、用户、工程师档案和权重配置，调用现有计算器计算五维与总分，然后 upsert `performance_result`。
  - 分数字段映射沿用现有读取口径：technical→`workload_score`，execution→`task_score`，cost_quality→`quality_score`，knowledge→`growth_score`，collaboration→`collaboration_score`。
  - 保存时写入 `user_name/department/job_type/job_level/indicator_scores/status/calculated_at/original_total_score`。
  - 保存后刷新同周期 `company_rank/dept_rank`，让排名/概览可直接读取。
  - 新增 `/engineer-performance/engineer/calculate/{user_id}` 和 `/engineer-performance/engineer/calculate/batch` 两个受 `performance:manage` 保护的计算落库入口。
  - `app.models.__init__` now 导入工程师绩效模型，保证隔离测试库和 create_all 初始化能注册相关表。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_engineer_performance_result_persistence_hr10.py` 通过。
  - `PYTHONPATH=. pytest -q tests/unit/test_engineer_performance_result_persistence_hr10.py tests/unit/test_performance_calculator.py tests/services/test_performance_calculator.py` 通过（52 个用例）。
  - `PYTHONPATH=. python3.14 - <<'PY' ...` 确认 `/engineer-performance/engineer/calculate/batch` 和 `/engineer-performance/engineer/calculate/{user_id}` 已注册。
  - `ruff check app/services/engineer_performance/engineer_performance_service.py app/api/v1/endpoints/engineer_performance/engineer.py app/models/__init__.py tests/unit/test_engineer_performance_result_persistence_hr10.py` 通过。
  - `python3.14 -m py_compile app/services/engineer_performance/engineer_performance_service.py app/api/v1/endpoints/engineer_performance/engineer.py app/models/__init__.py tests/unit/test_engineer_performance_result_persistence_hr10.py` 通过。
  - `git diff --check -- app/services/engineer_performance/engineer_performance_service.py app/api/v1/endpoints/engineer_performance/engineer.py app/models/__init__.py tests/unit/test_engineer_performance_result_persistence_hr10.py` 通过。
  - 注意：HR-16 的奖金触发/发放链路仍需单独验收；本次只是疏通其 `PerformanceResult` 上游。

## 2026-07-04 继续：HR-16 绩效奖金串联

- 修复目标：HR-10 已能生成 `PerformanceResult` 后，绩效奖金入口不能继续空转；应能从绩效结果和绩效奖金规则生成 `bonus_calculations`。
- 现场确认：
  - `bonus/calculation.py#calculate_performance_bonus` 会查 `PERFORMANCE_BASED` 规则并写 `BonusCalculation`，但本地 `bonus_rules` 只有填充数据 `NORMAL/AUTO/MANUAL`，无绩效规则。
  - schema/测试中常见规则类型是 `PERFORMANCE`，端点只查 `PERFORMANCE_BASED`，导致同一业务类型词表断裂。
  - `BonusCalculatorBase.get_coefficient_by_level()` 按旧枚举 `EXCELLENT/GOOD/...` 取系数；HR-10 新结果等级是 `S/A/B/C/D`，A 级会落到默认 1.0。
  - `generate_calculation_code()` 原来只到秒级，批量或重复计算会撞 `bonus_calculations.calculation_code` 唯一索引。
- 红测：
  - 新增 `tests/unit/test_performance_bonus_chain_hr16.py`，覆盖 `PERFORMANCE` 别名规则能被计算入口找到、A 级按 1.2 系数出奖金、同一 `rule_id + performance_result_id` 重复计算只保留一条记录、不完整绩效结果不发奖金。
- 代码面：
  - `BonusCalculatorBase.get_active_rules()` now 支持奖金类型别名组：`PERFORMANCE_BASED/PERFORMANCE/PERFORMANCE_BONUS` 等。
  - `get_coefficient_by_level()` now 兼容 `S/A/B/C/D` 和旧 `EXCELLENT/GOOD/QUALIFIED/...`，其中 A=1.2、S=1.5、B=1.0。
  - `generate_calculation_code()` now 使用微秒时间戳 + 随机尾巴，避免同秒批量计算撞唯一索引。
  - `PerformanceBonusCalculator.calculate()` now 拒绝不完整绩效结果；同一规则与绩效结果幂等 upsert，避免重复计算记录。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_performance_bonus_chain_hr16.py` 通过（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_performance_bonus_chain_hr16.py tests/unit/test_bonus_approval_gate.py tests/unit/test_bonus_presale.py tests/unit/test_presale_bonus.py tests/unit/test_team_coverage.py tests/unit/test_sales_coverage.py` 通过（25 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_services_p5_coverage.py::TestBonusCalculatorBase` 通过（4 个用例）。
  - `ruff check app/services/bonus/base.py app/services/bonus/performance.py tests/unit/test_performance_bonus_chain_hr16.py` 通过。
  - `python3.14 -m py_compile app/services/bonus/base.py app/services/bonus/performance.py tests/unit/test_performance_bonus_chain_hr16.py` 通过。
  - `git diff --check -- app/services/bonus/base.py app/services/bonus/performance.py tests/unit/test_performance_bonus_chain_hr16.py` 通过。
  - 注意：奖金审批/发放权限和流程属于 HR-17，本次未扩大修改。

## 2026-07-04 继续：APPR-14 合同交付日期带入项目计划

- 修复目标：合同签订自动创建/更新项目时，不能继续读取不存在的 `contract.delivery_deadline`，导致项目 `planned_end_date` 为空。
- 现场确认：
  - `Contract` 模型没有 `delivery_deadline` 字段。
  - 当前合同链路的真实交付日期在关联 `QuoteVersion.delivery_date`。
  - `ContractStatusHandler.handle_contract_signed()` 自动建项目路径只读幽灵字段；已关联项目路径也没有同步 `planned_end_date`。
- 红测：
  - 新增 `tests/unit/test_contract_project_delivery_date_appr14.py`，覆盖合同签订自动建项目、合同已关联项目两条路径。
  - 红灯时两条路径的 `Project.planned_end_date` 均为 `None`。
- 代码面：
  - 新增 `resolve_contract_delivery_date()`：优先兼容旧 `contract.delivery_deadline`/`contract.delivery_date`，再回退 `QuoteVersion.delivery_date`。
  - 自动建项目 now 用解析后的交付日期写 `Project.planned_end_date`。
  - 已关联项目 now 在签订处理时同步 `planned_end_date`，不清空已有计划日期。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_contract_project_delivery_date_appr14.py` 通过（2 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_status_handlers.py tests/unit/test_status_transition_service.py tests/unit/test_data_sync_service.py tests/unit/test_data_sync_service_deep.py` 通过（79 个用例）。
  - `ruff check app/services/status_handlers/contract_handler.py tests/unit/test_contract_project_delivery_date_appr14.py` 通过。
  - `python3.14 -m py_compile app/services/status_handlers/contract_handler.py tests/unit/test_contract_project_delivery_date_appr14.py` 通过。
  - `git diff --check -- app/services/status_handlers/contract_handler.py tests/unit/test_contract_project_delivery_date_appr14.py` 通过。

## 2026-07-04 继续：PEER-01/02 合同通用更新状态守卫

- 修复目标：通用 `PUT /sales/contracts/{id}` 不能直接改 `status`，否则可把 `CANCELLED/voided/pending_approval` 改回 `SIGNED`，绕过签署校验和审批实例。
- 现场确认：
  - `ContractUpdate` schema 暴露 `status`。
  - `basic.py#update_contract` 原来 `model_dump()` 后直接 `_map_contract_payload_to_model()`，field map 中包含 `status -> status`，没有状态机/审批实例校验。
- 红测：
  - 新增 `tests/unit/test_contract_status_update_guard_peer01_02.py`。
  - 覆盖：`CANCELLED -> SIGNED`、`pending_approval -> SIGNED` 都必须 400 且数据库状态不变；普通字段如 `contract_name` 仍可更新。
- 代码面：
  - `update_contract()` now 在映射和 `setattr` 前拦截 `status` 字段，返回 400：合同状态不可通过通用更新接口修改，请使用签署/作废/审批等专用流程。
  - 创建合同路径后续已由 APPR-13 收口为默认 `DRAFT`，不受本次守卫影响。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_contract_status_update_guard_peer01_02.py` 通过（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_contract_status_update_guard_peer01_02.py tests/unit/api/sales/test_contract_project_creation.py tests/unit/test_sales_scope_tail.py::TestContractSignProjectScope::test_create_contract_project_has_scope_check` 通过（21 个用例）。
  - `ruff check app/api/v1/endpoints/sales/contracts/basic.py tests/unit/test_contract_status_update_guard_peer01_02.py` 通过。
  - `python3.14 -m py_compile app/api/v1/endpoints/sales/contracts/basic.py tests/unit/test_contract_status_update_guard_peer01_02.py` 通过。
  - `git diff --check -- app/api/v1/endpoints/sales/contracts/basic.py tests/unit/test_contract_status_update_guard_peer01_02.py` 通过。
  - 注意：APPR-13 已于 2026-07-04 收口代码语义并补存量迁移脚本；真实库迁移脚本仍待发布/执行。

## 2026-07-04 继续：APPR-18 报价明细复制为合同交付物

- 修复目标：从报价创建合同后，不能只生成合同头而丢掉报价明细；否则 G4 合同转项目门禁要求交付物时，用户必须人工重录。
- 现场确认：
  - `create_contract_from_quote()` 原来查询报价明细只用于 G3 校验，创建合同后直接 commit，`contract_deliverables` 为空。
  - `validate_g4_contract_to_project()` 要求合同交付物非空，且至少有一个 `required_for_payment=True` 的交付物。
  - 当前 `ContractDeliverable` ORM 只有名称、类型、付款必需、模板引用等字段；schema 中规格/数量/交期暂未落表，本次不扩表。
- 红测：
  - 新增 `tests/unit/test_contract_from_quote_deliverables_appr18.py`。
  - 红灯时 from-quote 后查询 `contract_deliverables` 得到空列表。
- 代码面：
  - 新增 `_create_deliverables_from_quote_items()`：按报价明细生成合同交付物。
  - 映射规则：`deliverable_name=item_name/specification/报价明细序号`，`deliverable_type=item_type/cost_category/QUOTE_ITEM`，`required_for_payment=True`，`template_ref=quote_item:{id}`。
  - `create_contract_from_quote()` now 在合同 flush 后写入报价明细交付物。
  - 普通 `create_contract()` 若带 `quote_version_id` 且未手填交付物，也自动从报价明细生成合同交付物。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_contract_from_quote_deliverables_appr18.py` 通过。
  - `PYTHONPATH=. pytest -q tests/unit/test_contract_from_quote_deliverables_appr18.py tests/unit/test_finance_reports_rpt05.py::test_contract_from_quote_inherits_quote_tax_breakdown tests/unit/api/sales/test_contract_project_creation.py tests/unit/test_contract_status_update_guard_peer01_02.py` 通过（22 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_status_handlers.py tests/unit/test_status_transition_service.py tests/unit/test_data_sync_service.py tests/unit/test_data_sync_service_deep.py` 通过（79 个用例）。
  - `ruff check app/api/v1/endpoints/sales/contracts/basic.py tests/unit/test_contract_from_quote_deliverables_appr18.py tests/unit/test_contract_status_update_guard_peer01_02.py` 通过。
  - `python3.14 -m py_compile app/api/v1/endpoints/sales/contracts/basic.py tests/unit/test_contract_from_quote_deliverables_appr18.py tests/unit/test_contract_status_update_guard_peer01_02.py` 通过。
  - `git diff --check -- app/api/v1/endpoints/sales/contracts/basic.py tests/unit/test_contract_from_quote_deliverables_appr18.py tests/unit/test_contract_status_update_guard_peer01_02.py FUNCTIONAL_AUDIT_TRACKER.md PROJECT_NOTES.md` 通过。
  - 注意：`tests/api/test_sales_quote_item_contracts.py` 当前在本机因 `starlette TestClient` 与 httpx 版本不兼容报 `Client.__init__() got an unexpected keyword argument 'app'`，未作为 APPR-18 业务失败处理。

## 2026-07-04 继续：AS-05 服务工单状态机

- 修复目标：服务工单不能经通用状态接口从 `PENDING` 直接跳到 `RESOLVED/CLOSED`，关闭必须先经过解决态。
- 现场确认：
  - 工作区已有半成品改动：`ServiceTicketStatusEnum` 旁新增 `SERVICE_TICKET_STATUS_TRANSITIONS`，`status.py` 已接入 `validate_service_ticket_transition()` 和 `StatusUpdateService.transition_rules`。
  - 本轮未回退该半成品，而是按现有实现补验收和落账。
  - 矩阵当前为 `PENDING→IN_PROGRESS→RESOLVED→CLOSED`，`CLOSED` 不允许再流转。
- 红测/验收：
  - `tests/unit/test_service_ticket_state_machine_as05.py` 覆盖 `PENDING` 不能直跳 `RESOLVED`，也不能直接 close； happy path 必须按 `PENDING→IN_PROGRESS→RESOLVED→CLOSED`。
  - 第一次红灯确认旧路径会放行 `PENDING→RESOLVED`；矩阵接入后目标测试通过。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_service_ticket_state_machine_as05.py` 通过（2 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_service_ticket_notifications_as23.py` 通过（7 个用例）。
  - `PYTHONPATH=. pytest -q tests/unit/test_status_update_service.py tests/unit/test_status_update_service_coverage.py` 通过（18 个用例）。
  - `ruff check app/api/v1/endpoints/service/tickets/status.py app/models/service/enums.py tests/unit/test_service_ticket_state_machine_as05.py tests/unit/test_service_ticket_notifications_as23.py tests/unit/test_status_update_service.py tests/unit/test_status_update_service_coverage.py` 通过。
  - `python3.14 -m py_compile app/api/v1/endpoints/service/tickets/status.py app/models/service/enums.py tests/unit/test_service_ticket_state_machine_as05.py` 通过。
  - `git diff --check -- app/api/v1/endpoints/service/tickets/status.py app/models/service/enums.py tests/unit/test_service_ticket_state_machine_as05.py` 通过。
  - 注意：AS-05 审计里提到的 48 条历史枚举外脏值，本次没有直接改库；仍应走数据清洗专项。

## 2026-07-04 继续：TEN-01 租户管理 API 接真实路由

- 修复目标：`app/api/v1/endpoints/tenants.py` 不能继续作为四路盲猜导入 shim；主路由打印“租户管理模块加载成功”时，必须真的暴露 `/tenants` 管理接口。
- 现场确认：
  - 旧 `tenants.py` 依次尝试导入 `.access_control/.auth/.multi_tenancy/.settings.tenants`，全部不存在后落成空 `APIRouter()`。
  - `TenantService`、`Tenant` 模型、`TenantCreate/TenantUpdate/TenantResponse/TenantStatsResponse` schema 已存在，可支撑最小真实管理 API。
- 红测：
  - 新增 `tests/unit/test_tenant_management_routes_ten01.py`。
  - 红灯时 `tenants.router.routes` 为空，且模块没有 `list_tenants/create_tenant/get_tenant/update_tenant/get_tenant_stats` 等函数。
- 代码面：
  - `tenants.py` now 定义 `APIRouter(prefix="/tenants")`。
  - 接通列表、创建、详情、更新、软删除、初始化、统计接口到 `TenantService`。
  - 所有 endpoint 使用 `deps.require_super_admin`，并在函数内再次 `_ensure_super_admin()`，保证直接函数调用测试也不会绕过权限。
  - `ValueError` 转 400，不存在租户转 404。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_tenant_management_routes_ten01.py` 通过（3 个用例）。
  - `STRICT_API_ROUTER=false PYTHONPATH=. python3.14 - <<'PY' ...` 确认主 `api_router` 包含 `/tenants/`、`/tenants/{tenant_id}`、`/tenants/{tenant_id}/init`、`/tenants/{tenant_id}/stats`。
  - `PYTHONPATH=. pytest -q tests/unit/test_tenant_management_routes_ten01.py tests/api/test_deps.py::TestRequireSuperAdmin tests/api/test_deps.py::TestRequireTenantAdmin` 通过（9 个用例）。
  - `ruff check app/api/v1/endpoints/tenants.py tests/unit/test_tenant_management_routes_ten01.py` 通过。
  - `python3.14 -m py_compile app/api/v1/endpoints/tenants.py tests/unit/test_tenant_management_routes_ten01.py` 通过。
  - `git diff --check -- app/api/v1/endpoints/tenants.py tests/unit/test_tenant_management_routes_ten01.py` 通过。
  - 注意：本机完整 strict API 导入仍会因缺 `pyotp` 在认证模块先失败；这不是 TEN-01 新增问题。TEN-02/03/04/06 的隔离框架、业务表 tenant_id 和 fail-open 问题仍未处理。

## 2026-07-04 继续：PERM-06 账号解锁 API

- 修复目标：账号锁定服务已经存在，但 `account_unlock.py` 不能继续是 placeholder；无 Redis 的 DB 降级锁定也不能只能等窗口或人工改库。
- 现场确认：
  - 旧 `account_unlock.py` 多路盲猜导入失败后只注册 `GET /` placeholder。
  - 主路由将该 router 挂在 `/account-unlock`；lazy API 另挂 `/admin/account-lockout`。
  - `AccountLockoutService.unlock_account()` 原来只删 Redis key；无 Redis 即返回 False，DB 降级锁定没有解锁出口。
- 红测：
  - 新增 `tests/unit/test_account_unlock_api_perm06.py`。
  - 红灯时 router 只有 `/`，模块没有 `unlock_account/get_account_lockout_status`；无 Redis 下 DB 锁定记录不能通过 API 解锁。
- 代码面：
  - `account_unlock.py` now 暴露：`GET /locked-accounts`、`GET /{username}/status`、`GET /{username}/history`、`POST /{username}/unlock`。
  - 所有 endpoint 使用 `deps.require_super_admin`，函数内也显式 `_ensure_super_admin()`，避免直接调用绕过。
  - `AccountLockoutService.unlock_account()` now 同时尝试清 Redis 和 DB 降级失败计数。
  - DB 降级解锁将窗口内失败记录标记为 `failure_reason="admin_unlocked"`、`locked=False`，并让 `_get_attempt_stats_from_db()` 排除这些记录，保留审计痕迹但不再计入锁定。
- 验证：
  - `PYTHONPATH=. pytest -q tests/unit/test_account_unlock_api_perm06.py` 通过（3 个用例）。
  - `PYTHONPATH=. pytest -q tests/services/test_account_lockout_service.py tests/unit/test_account_lockout_service.py tests/unit/test_account_lockout_service_coverage.py tests/unit/test_account_lockout_extended_deep.py tests/unit/test_account_lockout_business_logic.py` 通过（57 个用例）。
  - `STRICT_API_ROUTER=false PYTHONPATH=. python3.14 - <<'PY' ...` 确认主 `api_router` 包含 `/account-unlock/locked-accounts`、`/{username}/status`、`/{username}/history`、`/{username}/unlock`。
  - `PYTHONPATH=. pytest -q tests/unit/test_account_unlock_api_perm06.py tests/api/test_deps.py::TestRequireSuperAdmin` 通过（6 个用例）。
  - `ruff check app/api/v1/endpoints/account_unlock.py app/services/account_lockout_service.py tests/unit/test_account_unlock_api_perm06.py` 通过。
  - `python3.14 -m py_compile app/api/v1/endpoints/account_unlock.py app/services/account_lockout_service.py tests/unit/test_account_unlock_api_perm06.py` 通过。
  - `git diff --check -- app/api/v1/endpoints/account_unlock.py app/services/account_lockout_service.py tests/unit/test_account_unlock_api_perm06.py` 通过。
  - 注意：完整 strict API 导入仍受缺 `pyotp` 影响；本次用 `STRICT_API_ROUTER=false` 验证非认证模块路由挂载。

## 2026-07-04 继续：功能审计 AS-20 保修判断与过保收费

- 修复项：`AS-20`。售后现场服务原来只看 `AfterSalesWarranty`，没有启用 `ProjectWarranty`，也没有过保收费字段；`/projects/{id}/warranty` 读接口看不到项目质保来源。
- 红测：
  - 新增 `tests/unit/test_after_sales_warranty_as20.py`。
  - 覆盖：`ProjectWarranty` 在有效期内时，现场服务必须判定在保；质保读接口必须返回 `project_warranty` 来源；项目核心质保已过期时，现场服务必须记录 `service_fee/travel_cost/total_cost` 与收费状态。
- 代码面：
  - `after_sales.py` 新增统一保修评估：优先 `AfterSalesWarranty`，其次 `ProjectWarranty`，最后回落 `Project.warranty_start_date/warranty_end_date`。
  - `get_warranty()` now 返回 `source/is_under_warranty/charge_required`，保留原 `AfterSalesWarranty` 字段兼容。
  - `create_field_service()` now 写入 `is_warranty/warranty_source`；过保服务支持 `service_fee/travel_cost/parts_cost/total_cost`，并写 `charge_required/charge_reason/charge_status`。
  - `AfterSalesFieldService` 补 `service_fee/warranty_source/charge_required/charge_reason/charge_status`。
  - `_ensure_after_sales_tables()` 对旧库补列，并 `checkfirst` 确保 `project_warranties` 表存在。
  - 新增迁移 `migrations/20260704_after_sales_warranty_billing_sqlite.sql`；新建表脚本 `20260704_after_sales_tables_sqlite.sql` 同步包含 AS-20 字段。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_after_sales_warranty_as20.py` 通过（3 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_after_sales_warranty_as20.py tests/unit/test_after_sales_field_service_as18.py tests/unit/test_after_sales_spare_parts_as08.py tests/unit/test_after_sales_tables_as09.py` 通过（19 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_after_sales_warranty_as20.py tests/unit/test_after_sales_field_service_as18.py tests/unit/test_after_sales_spare_parts_as08.py tests/unit/test_after_sales_as07.py tests/unit/test_after_sales_tables_as09.py tests/unit/test_service_ticket_notifications_as23.py tests/unit/test_service_ticket_state_machine_as05.py tests/api/test_service_ticket_crud_contracts.py tests/api/test_openapi_route_contracts.py::test_after_sales_routes_are_registered` 通过（33 个用例）。
  - `.venv/bin/ruff check app/api/v1/endpoints/after_sales.py app/models/after_sales.py tests/unit/test_after_sales_warranty_as20.py` 通过。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/after_sales.py app/models/after_sales.py tests/unit/test_after_sales_warranty_as20.py` 通过。
  - SQLite 内存验证：新库建表脚本和旧表增补 AS-20 迁移均能得到 `service_fee/warranty_source/charge_required/charge_reason/charge_status` 列。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-20` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 AS-21 关单回访与满意度调查提交

- 修复项：`AS-21`。服务工单关单原来只发工单关闭通知，不创建客户回访；满意度调查 `send` 只改状态不触达；前端已有 `/service/surveys/{id}/submit` 调用但后端没有路由，客户评分只能靠员工 update 代填。
- 红测：
  - 新增 `tests/unit/test_service_ticket_surveys_as21.py`。
  - 覆盖：关闭已解决服务工单后必须生成 `SERVICE` 满意度调查并创建真实通知；客户提交调查必须走 `submit_customer_satisfaction()`，写回 `COMPLETED/response_date/overall_score/feedback`。
- 代码面：
  - `service/surveys.py` 新增 `create_service_ticket_satisfaction_survey()`，从服务工单关联项目/客户带出客户名、联系人、邮箱/电话、项目编号/名称，创建 `CustomerSatisfaction` 并标记发送。
  - `send_customer_satisfaction()` now 复用 `mark_customer_satisfaction_sent()`，不再只是改状态；会通过统一通知服务创建 `SURVEY_SENT` 站内通知，`source_type=customer_satisfaction`。
  - 新增 `POST /service/surveys/{survey_id}/submit`，不要求员工登录依赖，已发送/待回复调查可由客户提交，完成后写 `response_date` 和评分反馈。
  - `ServiceTicketClose` 成功后 now 调用回访调查创建/发送；失败只记录日志，不反向破坏已完成的关单动作。
  - `schemas/service.py` 新增 `CustomerSatisfactionSubmit`。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_service_ticket_surveys_as21.py` 通过（2 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_service_ticket_surveys_as21.py tests/unit/test_service_ticket_notifications_as23.py tests/unit/test_service_ticket_state_machine_as05.py tests/api/test_service_ticket_crud_contracts.py` 通过（13 个用例）。
  - `.venv/bin/python -m pytest -q tests/api/test_service_permissions_scope.py::test_surveys_only_return_current_users_owned_data` 通过。
  - `npm --prefix frontend test -- --run src/services/api/__tests__/routeContracts.test.js -t "service"` 运行后该文件 31 项均 skipped；该契约文件没有 service 分组，不作为失败。
  - `.venv/bin/ruff check app/api/v1/endpoints/service/surveys.py app/api/v1/endpoints/service/tickets/status.py app/schemas/service.py tests/unit/test_service_ticket_surveys_as21.py` 通过。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/service/surveys.py app/api/v1/endpoints/service/tickets/status.py app/schemas/service.py tests/unit/test_service_ticket_surveys_as21.py` 通过。
  - 直接导入 service router 验证 `/surveys/{survey_id}/submit` 已注册；导入时仅出现 Redis 未配置 warning。
- 边界：本轮解决服务工单关单回访、调查发送站内触达、客户提交路由；没有新增外部邮件/SMS 网关，也没有给调查表加公开 token 字段。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-21` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 AS-22 故障诊断 AI 上下文与降级语义

- 修复项：`AS-22`。`/ai-eng/fault-diagnosis` 原来虽然真调 LLM，但 prompt 只包含用户输入的设备类型/故障现象，没有注入历史服务工单和服务知识库；AI 空结果直接 502，前端也无法区分正常 AI 诊断与降级建议。
- 红测：
  - 新增 `tests/unit/test_ai_engineering_fault_as22.py`。
  - 覆盖：prompt 必须包含“历史服务工单”和“服务知识库”，并带入相似工单方案/根因和知识库文章；AI 返回空结果时必须返回 `ai_generated=false/degraded=true/degraded_reason=AI_DIAGNOSIS_UNAVAILABLE`。
- 代码面：
  - `ai_engineering.py` 新增 `_fault_context()`，按故障关键词检索 `ServiceTicket.problem_desc/solution/root_cause/problem_type` 和已发布 `KnowledgeBase.title/content/category`，最多各取 5 条。
  - `fault_diagnosis()` prompt now 注入历史服务工单和服务知识库上下文。
  - 成功结果补 `context_sources/ai_generated/degraded`；AI 调用异常或空结果时返回规则降级建议，不再抛 502 伪装成“请补充故障描述”。
  - `FaultDiagnosis.jsx` 显示降级提示和上下文来源计数，避免规则降级结果看起来像正常 AI 输出。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_ai_engineering_fault_as22.py` 通过（2 个用例）。
  - `.venv/bin/ruff check app/api/v1/endpoints/ai_engineering.py tests/unit/test_ai_engineering_fault_as22.py` 通过。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/ai_engineering.py tests/unit/test_ai_engineering_fault_as22.py` 通过。
  - `npm exec eslint src/pages/FaultDiagnosis.jsx` 在 `frontend/` 下通过。
- 边界：本轮只补“检索上下文 + 降级语义 + 前端提示”，没有接向量检索、RAG 召回排序或外部知识库。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-22` 已改为 `已验证`。

## 2026-07-04 继续：功能审计 AS-24 派工占用账与外勤工时落账

- 修复项：`AS-24`。安装调试派工 assign 阶段已有 `EngineerTaskAssignment` 占用账，但 start/complete/cancel 不同步 assignment 状态；complete 也不生成 `Timesheet`，导致外勤实际工时不进入工时/成本台账。
- 现场额外发现：完工状态机自动创建 `ServiceRecord` 的 `generate_record_no` import 指向 `app.api.v1.endpoints.service`，实际函数在 `service.number_utils`，导致完工时 warning 并跳过服务记录。
- 红测：
  - 新增 `tests/unit/test_installation_dispatch_as24.py`。
  - 覆盖：start 后 `EngineerTaskAssignment` 必须变 `IN_PROGRESS` 且写 `actual_start_date`；complete 后 assignment 必须 `COMPLETED`、写 `actual_hours/actual_end_date`，并生成 `Timesheet(assign_id/task_id)`；完工自动服务记录必须生成 `service_record_id`。
- 代码面：
  - `installation_dispatch/workflow.py` 新增 `_ensure_dispatch_assignment()`、`_sync_dispatch_assignment_status()`、`_upsert_dispatch_timesheet()`。
  - `start_installation_dispatch_order()` now 同步 assignment 为 `IN_PROGRESS`。
  - `complete_installation_dispatch_order()` now 同步 assignment 为 `COMPLETED`，并创建/更新关联 `Timesheet`：`user_id/project_id/work_date/hours/task_id/assign_id/task_name/work_content/work_result`。
  - `cancel_installation_dispatch_order()` now 同步 assignment 为 `CANCELLED`。
  - `core/state_machine/installation_dispatch.py` 修正服务记录编号 import 为 `app.api.v1.endpoints.service.number_utils.generate_record_no`。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_installation_dispatch_as24.py` 通过（2 个用例）。
  - `.venv/bin/ruff check app/api/v1/endpoints/installation_dispatch/workflow.py app/core/state_machine/installation_dispatch.py tests/unit/test_installation_dispatch_as24.py` 通过。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/installation_dispatch/workflow.py app/core/state_machine/installation_dispatch.py tests/unit/test_installation_dispatch_as24.py` 通过。
  - `.venv/bin/python -m pytest -q tests/unit/test_installation_dispatch_as24.py tests/unit/test_engineer_scheduling_as17.py tests/unit/test_dispatch_conflict_guard_as04.py tests/audit_p0/test_p0_14_dispatch_conflict.py tests/unit/test_after_sales_field_service_as18.py` 通过（10 个用例）。
- 边界：本轮只保证安装派工占用账同步与完工工时进入 `Timesheet`；工时审批、财务成本同步仍沿用现有 timesheet 流程。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `AS-24` 已改为 `已验证`。

## 2026-07-04 继续：PERM-12 禁用权限码不再静默消失

- 修复目标：`api_permissions.is_active=0` 的权限码继续不授予，但不能在角色仍引用时静默从用户权限集合里消失，至少要有可观测告警。
- 红测：
  - `tests/unit/test_permission_engine.py::TestLoadPermissions::test_inactive_assigned_permission_is_denied_with_warning`。
  - 红灯确认：旧 `_load_permissions_from_db()` 返回 `{"sales:read"}`，但日志里没有 inactive 权限提示。
- 代码面：
  - `permission_engine._load_permissions_from_db()` now 同一次递归角色查询带回 `ap.is_active`。
  - active 权限才进入授权集合；inactive 权限集中打一条 warning，包含 `user/tenant/permissions`。
  - 顺手把旧测试 patch 点对齐当前 PERM-13 后的真实 cache service 路径与 revision 参数；`auth.check_permission` 测试对齐 `_load_user_permissions_from_db()` 当前入口。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_permission_engine.py` 通过（11 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_permission_cache_perm13.py tests/unit/test_permission_alias_perm14.py tests/unit/test_security.py -k 'permission or require_permission'` 通过（15 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_permission_service_branches.py -k 'cache or invalidate_role_and_users or role_user_ids'` 通过（13 个用例）。
  - `.venv/bin/python -m ruff check app/core/permission_engine.py tests/unit/test_permission_engine.py` 通过。
  - `python3.14 -m py_compile app/core/permission_engine.py tests/unit/test_permission_engine.py` 通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PERM-12` 已改为 `已验证`。

## 2026-07-04 继续：PERM-23 权限覆盖率 JSON 重生成

- 修复目标：`PERMISSION_COVERAGE_AUDIT.json` 仍停留在 2026-06-21，PERM-11 的裸奔端点基线已与当前代码不一致。
- 操作：
  - 运行 `.venv/bin/python scripts/audit_permission_coverage.py --json-only`。
  - 仅重生成 `PERMISSION_COVERAGE_AUDIT.json`，未额外生成 Markdown 报告。
- 当前摘要：
  - `audit_time=2026-07-04T15:36:47.312117`。
  - 总端点 `2980`。
  - `PERMISSION=1030`（34.6%）。
  - `AUTH_ONLY=1808`（60.7%）。
  - `NONE=142`（4.8%）。
  - 唯一权限码 `206`。
- 台账：
  - `PERM-23` 已改为 `已验证`。
  - `PERM-11` 仍为 `修复中`，但证据基线已同步为 `2980 路由：PERMISSION 1030/AUTH_ONLY 1808/NONE 142`。

## 2026-07-04 继续：PERM-20 重置密码撤销目标用户会话

- 修复目标：当前用户改密已撤销当前 token，但管理员重置目标用户密码后，目标用户原有活跃 session 仍可继续用。
- 红测：
  - 新增 `tests/unit/test_password_reset_sessions_perm20.py`。
  - 红灯确认：直接调用 `reset_user_password()` 后，目标用户 `UserSession.is_active` 仍为 `True`。
- 代码面：
  - `UserSyncService.reset_user_password()` 在密码更新提交后调用 `SessionService.revoke_all_sessions(db, user_id)`。
  - 保持原返回结构 `(True, new_password)` 不变；新增日志记录撤销 session 数量。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_password_reset_sessions_perm20.py` 通过（1 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_password_reset_sessions_perm20.py tests/unit/test_user_sync_service.py` 通过（20 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_session_service.py -k 'revoke_all_sessions or revoke_session'` 通过（4 个用例）。
  - `.venv/bin/python -m pytest -q tests/test_session_management.py::TestSessionService::test_revoke_all_sessions` 通过（1 个用例）。
  - `.venv/bin/python -m ruff check app/services/user_sync_service.py tests/unit/test_password_reset_sessions_perm20.py` 通过。
  - `python3.14 -m py_compile app/services/user_sync_service.py tests/unit/test_password_reset_sessions_perm20.py` 通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PERM-20` 已改为 `已验证`。

## 2026-07-04 继续：HR-18 团队奖金 Excel 分配合计校验

- 修复目标：奖金 Excel 分配导入原来只校验记录/用户存在，不校验同一团队分配或计算记录下的发放金额合计，可能把 1 万总奖金分出 3 万。
- 红测：
  - 新增 `tests/unit/test_bonus_allocation_totals_hr18.py`。
  - 红灯确认：`TeamBonusAllocation.total_bonus_amount=10000`，Excel 两行合计 `30000` 时，旧 parser 仍返回 2 条 `valid_rows` 且无错误。
- 代码面：
  - `parse_allocation_sheet()` now 先保留 `(row_num, data)`，再按 `team_allocation_id` 或 `calculation_id` 分组做跨行合计校验。
  - `team_allocation_id` 组校验 `sum(distributed_amount) == TeamBonusAllocation.total_bonus_amount`。
  - `calculation_id` 组校验 `sum(distributed_amount) == BonusCalculation.calculated_amount`。
  - 容差 `0.01`；不匹配时整组行写入错误并从 `valid_rows` 移除。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_bonus_allocation_totals_hr18.py` 通过（1 个用例）。
  - `.venv/bin/python -m pytest -q tests/api/test_hr_bonus_permission_contracts.py tests/unit/test_bonus_approval_gate.py` 通过（7 个用例）。
  - `.venv/bin/python -m ruff check app/services/bonus/bonus_allocation_parser.py tests/unit/test_bonus_allocation_totals_hr18.py` 通过。
  - `python3.14 -m py_compile app/services/bonus/bonus_allocation_parser.py tests/unit/test_bonus_allocation_totals_hr18.py` 通过。
  - 注意：`tests/unit/test_bonus_allocation_parser_service.py` 当前仍因历史旧导入路径 `app.services.bonus_allocation_parser` 全量报 `ModuleNotFoundError`；`tests/unit/test_bonus_parser_deep.py` 里部分用例按旧函数签名调用，也会失败，未作为 HR-18 回归失败处理。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `HR-18` 已改为 `已验证`。

## 2026-07-04 继续：ADMIN-04 备份校验 checksum 不可绕过

- 修复目标：`verify_backup.sh` 原来只有在 `.md5` sidecar 存在时才校验 MD5；缺 sidecar 的 gzip SQL dump 只要能恢复进 SQLite 就会被放行。
- 红测：
  - 扩展 `tests/unit/test_backup_admin01_03.py::test_verify_backup_requires_checksum_sidecar`。
  - 红灯确认：构造一个无 `.md5` 的有效 gzip SQL dump，旧脚本返回 `0` 并打印 `Verification passed`。
- 代码面：
  - `verify_backup.sh` now 强制要求 `${backup_file}.md5` 存在。
  - 缺 checksum、空 checksum、MD5 不匹配均直接失败；通过 MD5 后才继续读取 gzip、导入 SQLite 内存库并跑 `PRAGMA integrity_check`。
  - 保留脚本可执行位。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_backup_admin01_03.py::test_verify_backup_requires_checksum_sidecar` 通过。
  - `.venv/bin/python -m pytest -q tests/unit/test_backup_admin01_03.py` 通过（4 个用例）。
  - `bash -n scripts/verify_backup.sh` 通过。
  - `.venv/bin/python -m ruff check tests/unit/test_backup_admin01_03.py` 通过。
  - `python3.14 -m py_compile tests/unit/test_backup_admin01_03.py` 通过。
  - `git diff --check -- scripts/verify_backup.sh tests/unit/test_backup_admin01_03.py` 通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `ADMIN-04` 已改为 `已验证`。

## 2026-07-04 继续：HR-24 协作评价自动补齐打标降权

- 修复目标：`auto_complete_missing_ratings()` 原来把缺评直接填 3 分/75 分，且无任何标记，进入绩效时和真人评分同权，稀释区分度。
- 红测：
  - `tests/unit/test_collaboration_ratings.py::TestRatingManager::test_auto_complete_missing_ratings` 扩展断言自动补齐必须 `is_auto_completed=True` 且 `rating_weight=0.50`。
  - `tests/unit/test_collaboration_statistics.py::TestRatingStatistics::test_get_average_score_uses_rating_weight` 新增加权平均断言：真人 100 分权重 1.00、自动 75 分权重 0.50，平均应为 91.67，而不是 87.50。
- 代码面：
  - `CollaborationRating` 增加 `rating_weight/is_auto_completed/auto_completed_at/auto_completion_reason`。
  - `submit_rating()` 明确写真人评价权重 1.00，并清自动补齐标记。
  - `auto_complete_missing_ratings()` 默认仍填 75 分，但写自动补齐标记、原因和 0.50 权重。
  - `RatingStatistics.get_average_collaboration_score()` 与统计页平均分 now 按权重计算；旧数据无权重或非法权重按 1.00 兼容。
  - 新增迁移 `migrations/20260704_collaboration_rating_auto_completion_sqlite.sql`。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_collaboration_ratings.py::TestRatingManager::test_auto_complete_missing_ratings` 通过。
  - `.venv/bin/python -m pytest -q tests/unit/test_collaboration_statistics.py::TestRatingStatistics::test_get_average_score_uses_rating_weight` 通过。
  - `.venv/bin/python -m pytest -q tests/unit/test_collaboration_ratings.py tests/unit/test_collaboration_statistics.py tests/unit/test_collaboration_rating_service_zero_coverage.py` 通过（33 个用例）。
  - `.venv/bin/python -m ruff check app/models/engineer_performance/common.py app/services/collaboration_rating/ratings.py app/services/collaboration_rating/statistics.py tests/unit/test_collaboration_ratings.py tests/unit/test_collaboration_statistics.py` 通过。
  - `python3.14 -m py_compile app/models/engineer_performance/common.py app/services/collaboration_rating/ratings.py app/services/collaboration_rating/statistics.py tests/unit/test_collaboration_ratings.py tests/unit/test_collaboration_statistics.py` 通过。
  - SQLite 迁移在内存表上验证新增 `rating_weight/is_auto_completed/auto_completed_at/auto_completion_reason` 列。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `HR-24` 已改为 `已验证`。

## 2026-07-04 继续：SALES-19 发票作废红冲审计链

- 修复目标：已收款发票作废不应要求先删除回款；应保留原回款痕迹，并生成可追溯红冲记录，避免审计链断裂。
- 红测：
  - 扩展 `tests/api/test_sales_invoice_gate_contracts.py`。
  - `test_void_paid_invoice_creates_red_credit_without_deleting_payment` 红灯确认：旧 `PUT /sales/invoices/{id}/void` 对已收款发票返回 400 `已收款的发票不能作废，请先处理收款`。
  - `test_invoice_amount_limit_ignores_red_credit_invoice_amounts` 红灯确认：旧合同累计开票校验把 `RED_CREDIT` 负票计入总额，错误放行超合同额新发票。
- 代码面：
  - `sales/invoices/operations.py`：已开票发票作废时创建 `invoice_type=RED_CREDIT` 的负数红冲发票，复制合同/项目/付款节点/购买方信息，金额、税额、含税总额、已收金额按负数记录；红冲单 `payment_status=REVERSED`，原票改 `CANCELLED` 并追加作废原因和红冲发票号。
  - 原发票不清空 `paid_amount/paid_date/payment_status`，用于保留原始回款审计痕迹；接口返回 `red_invoice_id/red_invoice_code`。
  - `sales/invoices/basic.py`：合同累计开票金额校验排除 `RED_CREDIT` 与非正金额，避免红冲负票虚增可开票额度。
- 验证：
  - `.venv/bin/python -m pytest -q tests/api/test_sales_invoice_gate_contracts.py::test_void_paid_invoice_creates_red_credit_without_deleting_payment tests/api/test_sales_invoice_gate_contracts.py::test_invoice_amount_limit_ignores_red_credit_invoice_amounts` 通过。
  - `.venv/bin/python -m pytest -q tests/api/test_sales_invoice_gate_contracts.py` 通过（9 个用例）。
  - `.venv/bin/python -m pytest -q tests/api/test_sales_payment_record_contracts.py` 通过（4 个用例）。
  - `.venv/bin/python -m ruff check app/api/v1/endpoints/sales/invoices/operations.py app/api/v1/endpoints/sales/invoices/basic.py tests/api/test_sales_invoice_gate_contracts.py` 通过。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/sales/invoices/operations.py app/api/v1/endpoints/sales/invoices/basic.py tests/api/test_sales_invoice_gate_contracts.py` 通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `SALES-19` 已改为 `已验证`。

## 2026-07-04 继续：PROJ-23 终验收后售后移交主链路补齐

- 修复目标：验收完成主链路不能只生成定期保养计划；需要形成可查询的售后移交事实，包括 ACTIVE 质保档、项目质保字段、机台质保/客户归属，避免售后人工重建。
- 红测：
  - 新增 `tests/unit/test_project_after_sales_handover_proj23.py`。
  - 红灯确认：旧 `ProjectDataFlowService.transfer_to_after_sales()` 只返回 4 条保养计划，`AfterSalesWarranty` 为 0，返回结构也没有 `warranty_created/warranty_id`。
  - 红灯确认：重复移交时保养计划能跳过，但质保档仍为 0，无法证明移交幂等。
- 代码面：
  - `project_data_flow_service.transfer_to_after_sales()` now 创建或复用 `AfterSalesWarranty(status=ACTIVE)`，质保开始日期取 `project.warranty_start_date / actual_end_date / planned_end_date / today`，质保月数缺省 12。
  - 项目 `warranty_period_months/warranty_start_date/warranty_end_date` 只补空，不覆盖已有人工字段。
  - 机台 `warranty/customer_id` 只补空；返回 `warranty_created/warranty_id/warranty_no/warranty_start/warranty_end/machines_backfilled`。
  - 定期保养计划继续沿用原 1/3/6/12 个月口径，并和质保移交共用同一个起算日。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_project_after_sales_handover_proj23.py` 通过（2 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_acceptance_aftersales_handover.py` 通过（4 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_acceptance_completion_service.py tests/unit/test_equipment_maintenance_reminder_as14.py` 通过（22 个用例）。
  - `.venv/bin/python -m ruff check app/services/project_data_flow_service.py tests/unit/test_project_after_sales_handover_proj23.py` 通过。
  - `.venv/bin/python -m py_compile app/services/project_data_flow_service.py tests/unit/test_project_after_sales_handover_proj23.py` 通过。
- 边界：ITR 当前是验收/工单/问题的 read model，没有独立移交表；本轮保证验收后售后事实落库，ITR 继续读取验收上下文。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROJ-23` 已改为 `已验证`。

## 2026-07-04 继续：PROJ-24 项目复盘 AI 降级语义止损

- 修复目标：项目复盘生成遇到 AI mock/降级响应时，不能把预售方案类演示内容当作真实复盘 AI 结果写入。
- 红测：
  - 扩展 `tests/unit/test_review_report_generator.py`。
  - 红灯确认：`AIClientService.generate_solution()` 返回 `model=glm-5-mock` 和“非标自动化生产线方案”类内容时，旧生成器仍写 `ai_generated=True`，且复盘摘要混入预售方案文案。
- 代码面：
  - `ProjectReviewReportGenerator` 接入 `is_mock_response()`，识别 `*-mock` 后写 `ai_generated=False/ai_generated_at=None`。
  - `ai_metadata` 保留真实返回模型与 token 用量，并追加 `degraded=True/degraded_reason=AI_REVIEW_UNAVAILABLE`。
  - 降级内容改为基于项目名称、工期、成本、变更次数等字段生成规则复盘底稿；不再解析或入库预售方案 mock 文本。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_review_report_generator.py::TestProjectReviewReportGenerator::test_generate_report_marks_mock_ai_response_as_degraded` 红后绿通过。
  - `.venv/bin/python -m pytest -q tests/unit/test_review_report_generator.py tests/unit/test_report_generator_coverage.py` 通过（31 个用例）。
  - `ALIBABA_API_KEY= AI_DEFAULT_MODEL= ZHIPU_API_KEY= OPENAI_API_KEY= KIMI_API_KEY= .venv/bin/python -m pytest -q tests/api/test_project_review_api.py::TestReviewsAPI::test_generate_review_report` 通过。
  - `.venv/bin/python -m pytest -q tests/api/test_batch7_route_contracts.py::test_project_reviews_list_coerces_legacy_null_defaults tests/api/test_batch7_route_contracts.py::test_sqlite_schema_patch_adds_project_review_ai_columns` 通过（2 个用例）。
  - `.venv/bin/python -m ruff check app/services/project_review_ai/report_generator.py tests/unit/test_review_report_generator.py` 通过。
  - `.venv/bin/python -m py_compile app/services/project_review_ai/report_generator.py tests/unit/test_review_report_generator.py` 通过。
- 边界：本机 `.env/.env.local` 有真实阿里百炼 key 时，原 API 测试会实际出网并因外部模型耗时超过 30 秒断言失败；离线验证已用空 key 覆盖，确认 mock/degraded 链路和路由契约可用。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROJ-24` 已改为 `已验证`。

## 2026-07-04 继续：PROJ-26 自动组队接入立项与动态经验分

- 修复目标：自动组队不能只看项目表少量字段；立项审批里的预计工时、资源要求、技术难度要进入角色/工时建议，工程师经验维度也不能固定给满 20 分。
- 红测：
  - 新增 `tests/unit/test_team_generation_proj26.py`。
  - 红灯确认：项目存在已批准 `PmoProjectInitiation(estimated_hours=320, resource_requirements=视觉/软件...)` 时，旧 `generate_team_plan()` 不返回立项来源、不会补视觉/软件角色，也没有按 320 小时分摊。
  - 红灯确认：同一工程师有/无历史完成任务时，旧 `_calculate_role_match()` 得分同为 100，经验维度固定满分。
- 代码面：
  - `TeamGenerationService._analyze_project_requirements()` 回查已批准立项，带出 `source/initiation_id/estimated_hours/resource_requirements/technical_difficulty/project_level`。
  - `_determine_roles()` 根据立项资源要求补充电气、机械、视觉、软件、测试角色，并按立项预计总工时归一分摊到本次角色。
  - `_calculate_role_match()` 的经验 20 分 now 来自历史 `EngineerTaskAssignment`：完成数量、质量评分、准时率、返工率；缺历史时回退 `EngineerCapacity` 能力画像。
  - 兼容原合同金额估算路径；无立项或旧库缺表时仍可按项目字段生成基础方案。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_team_generation_proj26.py` 通过（2 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_team_generation_service_coverage.py tests/unit/test_final_zero_coverage_auto.py::TestTeamGenerationService` 通过（2 个用例）。
  - `.venv/bin/python -m pytest -q tests/api/test_openapi_route_contracts.py::test_batch3_dynamic_detail_routes_are_registered` 通过。
  - `.venv/bin/python -m ruff check app/services/team_generation_service.py tests/unit/test_team_generation_proj26.py` 通过。
  - `.venv/bin/python -m py_compile app/services/team_generation_service.py tests/unit/test_team_generation_proj26.py` 通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROJ-26` 已改为 `已验证`。

## 2026-07-04 继续：PROD-18 生产排程显式工单依赖

- 修复目标：生产排程不能只按优先级/资源空闲排单；当后置工单依赖前置工单时，后置开始时间必须晚于前置完工，甘特图也要回显依赖关系。
- 红测：
  - 新增 `tests/unit/test_production_schedule_dependencies_prod18.py`。
  - 红灯确认：`constraints={"dependencies": {"后置工单": ["前置工单"]}}` 时，旧贪心算法仍因后置工单 `URGENT` 把它排到前置前面。
  - 红灯确认：排程记录已有依赖元数据时，旧 `generate_gantt_data()` 仍返回 `dependencies=[]`。
- 代码面：
  - `ProductionScheduleService` 新增依赖解析，兼容 `constraints.dependencies` 的 dict/list 形式，以及工单对象上的 `depends_on_work_order_ids/predecessor_work_order_ids/dependencies` 动态字段。
  - 贪心排程先按优先级排序，再做依赖拓扑校正；排每个工单时取所有前置工单结束时间作为最早可开工时间。
  - 每条后置排程写入 `constraints_met={"dependencies": {"predecessors": [...], "enforced": True}}`。
  - 启发式优化交换后再次执行依赖时间校正，避免优化步骤把依赖打散。
  - 甘特图按 `constraints_met.dependencies.predecessors` 把前置工单 ID 映射为前置排程任务 ID，前端不再拿空依赖。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_production_schedule_dependencies_prod18.py` 通过（2 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_production_schedule_n2.py` 通过（44 个用例）。
  - `.venv/bin/python -m ruff check app/services/production_schedule_service.py tests/unit/test_production_schedule_dependencies_prod18.py` 通过。
  - `.venv/bin/python -m py_compile app/services/production_schedule_service.py tests/unit/test_production_schedule_dependencies_prod18.py` 通过。
  - `tests/test_production_schedule.py` 当前因历史导入 `ResourceConflict` 重命名在模块级 skip，未作为本轮失败。
- 边界：本轮是短期闭环，让现有单工单模型通过显式依赖约束可用；完整工艺路线、同一工单多工序拆解和依赖维护 UI 仍需后续专项。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROD-18` 已改为 `已验证`。

## 2026-07-04 继续：PROD-19 委外交付超交拦截与收货确认

- 修复目标：外协订单需要能挂生产工单；创建交付不能超过订单剩余数量；交付后需要有收货确认端点，把实收数量、收货人、订单状态串起来。
- 红测：
  - 新增 `tests/unit/test_outsourcing_delivery_prod19.py`。
  - 红灯确认：`OutsourcingOrderCreate` 不接收 `work_order_id`。
  - 红灯确认：已交 4 / 订单 10 时继续交付 7 未被挡住，并且返回阶段还会因 `vendor.vendor_name` 字段漂移崩溃。
  - 红灯确认：`receive_outsourcing_delivery()` 不存在。
  - 红灯确认：创建订单走到金额计算时 `Decimal * float` 报错，且无法落 `work_order_id`。
- 代码面：
  - `OutsourcingOrder` 增加 `work_order_id`、`work_order` 关系和索引；新增迁移 `migrations/20260704_outsourcing_work_order_receipt_sqlite.sql`。
  - `OutsourcingOrderCreate/Response/ListResponse` 增加 `work_order_id`；创建订单时校验工单存在且属于同项目。
  - 订单金额税额计算改为 Decimal 全链路，避免运行时 TypeError。
  - 交付创建前先验证全部明细剩余数量，超交返回 400 `交付数量超出订单剩余数量`，避免先写库后失败。
  - 新增 `PUT /outsourcing-deliveries/{delivery_id}/receive`，默认按交付数量全量收货，也支持 payload 指定实收数量；写 `received_quantity/received_at/received_by`，并同步订单明细与订单 `RECEIVED/IN_PROGRESS` 状态。
  - 交付响应统一用 `Vendor.supplier_name`，修复旧 `vendor_name` 漂移。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_outsourcing_delivery_prod19.py` 红后绿通过（4 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_outsourcing_delivery_prod19.py tests/unit/test_schemas_import_coverage.py tests/api/test_null_response_defaults.py::test_list_endpoints_coerce_legacy_null_response_fields tests/api/test_batch14_route_contracts.py::test_batch5_outsourcing_readonly_routes_tolerate_legacy_nulls tests/api/test_path_param_route_contracts.py::test_outsourcing_task_qualification_and_document_routes_tolerate_legacy_nulls` 通过；schema import 模块里历史缺失模块按原逻辑 skip。
  - `.venv/bin/python -m ruff check app/models/outsourcing.py app/schemas/outsourcing.py app/api/v1/endpoints/outsourcing/orders.py app/api/v1/endpoints/outsourcing/deliveries.py tests/unit/test_outsourcing_delivery_prod19.py` 通过。
  - `.venv/bin/python -m py_compile app/models/outsourcing.py app/schemas/outsourcing.py app/api/v1/endpoints/outsourcing/orders.py app/api/v1/endpoints/outsourcing/deliveries.py tests/unit/test_outsourcing_delivery_prod19.py` 通过。
  - `import app.main` 路由清单确认 `PUT /api/v1/outsourcing-deliveries/{delivery_id}/receive` 已注册。
  - `git diff --check -- app/models/outsourcing.py app/schemas/outsourcing.py app/api/v1/endpoints/outsourcing/orders.py app/api/v1/endpoints/outsourcing/deliveries.py tests/unit/test_outsourcing_delivery_prod19.py migrations/20260704_outsourcing_work_order_receipt_sqlite.sql` 通过。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROD-19` 已改为 `已验证`。

## 2026-07-04 继续：PROD-20 ECN 到采购影响传导

- 修复目标：ECN 影响采购不能依赖人工先建 `EcnAffectedOrder`；`MODIFY` 分支不能空 `pass` 后把影响单标成已处理。
- 红测：
  - 新增 `tests/unit/test_ecn_purchase_sync_prod20.py`。
  - 红灯确认：只有 `EcnAffectedMaterial(material_id=...)` 和有效采购订单行时，旧 `sync_to_purchase()` 返回 `updated_count=0` 且没有生成采购影响单。
  - 红灯确认：已有 `EcnAffectedOrder(action_type=MODIFY)` 时，旧逻辑只把影响单标为 `PROCESSED`，采购单没有任何 ECN 待处理痕迹。
- 代码面：
  - `EcnIntegrationService.sync_to_purchase()` 先调用 `_ensure_purchase_affected_orders()`，按受影响物料反查非 `CANCELLED/DRAFT` 的采购订单行，按采购单幂等生成 `EcnAffectedOrder(order_type=PURCHASE, action_type=MODIFY)`。
  - 影响描述 now 汇总物料编码、变更类型、数量/规格/供应商/成本影响。
  - `MODIFY` 不自动改采购数量/价格，也不改采购单主状态；改为写 `EcnAffectedOrder.status=CHANGE_REQUIRED`、处理人/时间和默认处理说明，采购单 `remark` 追加 `[ECN ...] 采购需评审...`，让采购人员在原状态下处理变更。
  - `CANCEL` 分支保留取消采购单行为，并补 ECN 备注；返回结果增加 `created_count/cancelled_count/change_required_count`。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_ecn_purchase_sync_prod20.py` 红后绿通过（2 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_ecn_purchase_sync_prod20.py tests/unit/test_ecn_integration_service_coverage.py tests/unit/test_ecn_material_impact_service_coverage.py tests/unit/test_ecn_bom_auto_sync_prod07.py` 通过（25 个用例）。
  - `.venv/bin/python -m ruff check app/services/ecn/integration/ecn_integration_service.py tests/unit/test_ecn_purchase_sync_prod20.py` 通过。
  - `.venv/bin/python -m py_compile app/services/ecn/integration/ecn_integration_service.py tests/unit/test_ecn_purchase_sync_prod20.py` 通过。
  - `import app.main` 路由清单确认 `POST /api/v1/ecns/{ecn_id}/sync-to-purchase` 与 `POST /api/v1/ecns/batch-sync-to-purchase` 已注册。
  - `git diff --check -- app/services/ecn/integration/ecn_integration_service.py tests/unit/test_ecn_purchase_sync_prod20.py` 通过。
- 边界：本轮不直接改采购单行数量/价格，避免绕过采购确认；后续若要自动改行项目，应先定义采购变更审批/重签规则。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROD-20` 已改为 `已验证`。

## 2026-07-04 继续：PROD-21 移动扫码开工离线队列与 iOS 降级

- 修复目标：车间移动端扫码开工不能在网络抖动时直接失败丢操作；iOS/无 `BarcodeDetector` 的浏览器不能只弹 alert 中断扫码流程。
- 红测：
  - 新增 `frontend/src/pages/mobile/__tests__/mobileScanStartHelpers.test.js`。
  - 红灯确认：离线开工队列 helper 不存在，无法写入/重放本地待同步开工请求。
- 代码面：
  - 新增 `mobileScanStartHelpers.js`：
    - `enqueueOfflineStartWorkReport()` 将离线开工写入 `localStorage` 的 `mobile.scanStart.offlineStartQueue.v1` 队列，保留工单 ID、工单号、任务名、备注、客户端 ID 和排队时间。
    - `flushOfflineStartWorkReports()` 联网后顺序补传，成功移除，失败保留。
    - `isLikelyOfflineStartError()` 识别离线/网络错误，避免把 500 等服务端错误误入本地队列。
    - `getCameraScanUnavailableMessage()` 对 iOS/无 `BarcodeDetector` 给手动输入/系统相机降级提示。
  - `MobileScanStart.jsx` 接入离线队列：开工 API 网络失败时暂存本地并提示“联网后自动补传”；页面加载和 `online` 事件会尝试补传队列。
  - 相机扫码遇到无 `BarcodeDetector` 不再 `alert()`，改为页面错误提示，保留扫码枪/键盘输入通道。
- 验证：
  - `npm run test:run -- src/pages/mobile/__tests__/mobileScanStartHelpers.test.js` 红后绿通过（4 个用例）。
  - `npx eslint src/pages/mobile/MobileScanStart.jsx src/pages/mobile/mobileScanStartHelpers.js src/pages/mobile/__tests__/mobileScanStartHelpers.test.js` 通过。
  - `npm run build` 通过；仍有项目既有的大 chunk/重复动态导入 warning，非本轮新增失败。
  - `git diff --check -- frontend/src/pages/mobile/MobileScanStart.jsx frontend/src/pages/mobile/mobileScanStartHelpers.js frontend/src/pages/mobile/__tests__/mobileScanStartHelpers.test.js FUNCTIONAL_AUDIT_TRACKER.md PROJECT_NOTES.md` 通过。
- 边界：本轮未引入图片二维码解码库；iOS 页面内拍照后自动识别仍需后续引入 jsQR/原生扫码桥接。当前已保证手工/扫码枪输入和离线开工不中断。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROD-21` 已改为 `已验证`。

## 2026-07-04 继续：PROD-23 状态机治理双轨收口

- 修复目标：采购订单状态不能由直提/直审、旧 `PurchaseService`、统一审批适配器各自直接赋值；生产报工开工/完工审批也不能用内联 if 绕过已有工单状态机。
- 红测：
  - 新增 `tests/unit/test_state_governance_prod23.py`。
  - 红灯确认：`submit_purchase_order()` 和 `approve_purchase_order()` 不调用共享采购状态迁移 helper。
  - 红灯确认：`start_work_report()` 和完工报工审批不调用 `work_order_state_machine.validate_transition()`，即使状态机拦截也会继续写状态。
- 代码面：
  - 新增 `app/services/purchase/order_state_machine.py`，集中定义 `PURCHASE_ORDER_TRANSITIONS`、`validate_purchase_order_transition()`、`transition_purchase_order_status()`。
  - `orders_refactored.py` 提交/审批、`PurchaseService.submit/approve`、`approval_engine/adapters/purchase.py` 的 submit/approved/rejected/withdrawn 回调统一走采购订单状态机。
  - `work_reports.py` 新增 `_validate_work_order_transition()`，开工报工进入 `STARTED`、完工报工审批进入 `COMPLETED` 时统一复用已有工单状态机。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_state_governance_prod23.py` 红后绿通过（4 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_state_governance_prod23.py tests/unit/test_state_machines_depth.py::TestPurchaseOrderMachine tests/unit/test_api_p6_coverage.py::TestWorkReports` 通过（24 个用例）。
  - `.venv/bin/python -m pytest -q tests/api/test_purchase_workflow_contracts.py` 通过（2 个用例）。
  - `.venv/bin/python -m pytest -q tests/api/test_purchase_receipts_workflow_contracts.py` 通过（6 个用例）。
  - `.venv/bin/python -m pytest -q tests/integration/test_purchase_api.py::TestPurchaseOrdersAPI::test_submit_purchase_order tests/integration/test_purchase_api.py::TestPurchaseOrdersAPI::test_approve_purchase_order` 通过（2 个用例）。
  - `.venv/bin/python -m ruff check app/services/purchase/order_state_machine.py app/api/v1/endpoints/purchase/orders_refactored.py app/services/purchase/purchase_service.py app/services/approval_engine/adapters/purchase.py app/api/v1/endpoints/production/work_reports.py tests/unit/test_state_governance_prod23.py` 通过。
  - `.venv/bin/python -m py_compile app/services/purchase/order_state_machine.py app/api/v1/endpoints/purchase/orders_refactored.py app/services/purchase/purchase_service.py app/services/approval_engine/adapters/purchase.py app/api/v1/endpoints/production/work_reports.py` 通过。
  - `import app.main` 路由清单确认采购 submit/approve、采购 workflow submit/action、报工 start/approve 路由均已注册。
- 边界：采购收货状态流转仍保留在收货业务函数内，本轮只收口审批/提交双轨；后续若要全采购生命周期中央状态机，可把收货 `PARTIAL_RECEIVED/RECEIVED/CLOSED` 也迁入同一 helper。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROD-23` 已改为 `已验证`。

## 2026-07-04 继续：PROD-24 委外成本按质检合格量确认

- 修复目标：委外订单审批通过不能直接把订单全额计入项目实际成本；实际成本应随质检合格数量确认，不合格/未检数量不能提前入账。
- 红测：
  - 新增 `tests/unit/test_outsourcing_cost_collection_prod24.py`。
  - 红灯确认：订单 10 件、单价 100、合格 6 件时，旧 `collect_from_outsourcing_order()` 仍按订单总额 1000 入账，而不是 600。
  - 红灯确认：合格量为 0 且已有旧 1000 元外协成本时，旧逻辑继续保留全额成本，不会冲减项目实际成本。
- 代码面：
  - `CostCollectionService._outsourcing_qualified_cost_basis()` 读取真实 `OutsourcingOrderItem` 明细，按 `qualified_quantity * unit_price` 汇总外协实际成本。
  - 税额按确认成本占订单总额比例折算；成本描述追加 `合格数量：已合格/订单数量`，方便审计。
  - 合格确认成本为 0 时不创建 `ProjectCost`；如已有历史成本，则删除并调用 `_recalculate_project_actual_cost()` 重算项目实际成本。
  - 非真实 SQLAlchemy 订单对象（旧 MagicMock 单测/降级调用）保留订单总额兜底，避免误伤既有 mock 覆盖。
- 验证：
  - `.venv/bin/python -m pytest -q tests/unit/test_outsourcing_cost_collection_prod24.py` 红后绿通过（2 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_outsourcing_cost_collection_prod24.py tests/unit/test_cost_collection_service_coverage.py::TestCollectFromOutsourcingOrder tests/unit/test_cost_collection_n3.py::TestCollectFromOutsourcingOrder tests/unit/test_cost_forecast_branches.py::TestCostCollectionOutsourcingOrder` 通过（12 个用例）。
  - `.venv/bin/python -m pytest -q tests/services/test_cost_collection_business_docs.py` 通过（10 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_outsourcing_delivery_prod19.py` 通过（4 个用例）。
  - `.venv/bin/python -m pytest -q tests/api/test_outsourcing.py::TestOutsourcingInspections` 通过 1 个、skip 1 个（旧测试无交付数据时按原逻辑 skip）。
  - `.venv/bin/python -m ruff check app/services/cost/cost_collection_service.py tests/unit/test_outsourcing_cost_collection_prod24.py` 通过。
  - `.venv/bin/python -m py_compile app/services/cost/cost_collection_service.py tests/unit/test_outsourcing_cost_collection_prod24.py` 通过。
- 边界：本轮未改付款条件和应付账款确认；只是把项目实际成本从“审批全额”改为“质检合格确认”。如后续要做暂估/应付，需要单独建成本基础或付款计划口径。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `PROD-24` 已改为 `已验证`。

## 2026-07-04 继续：HR-04 组织员工/部门删除接口补齐

- 修复目标：前端 `employeeApi.delete()` / `departmentApi.delete()` 已固定调用 `/org/employees/{id}` 和 `/org/departments/{id}`，后端必须注册对应 DELETE 路由，不能继续 405。
- 红测：
  - 新增 `tests/api/test_org_delete_hr04.py`。
  - 红灯确认：`DELETE /api/v1/org/employees/{id}` 返回 405，员工无法从前端删除。
  - 红灯确认：`DELETE /api/v1/org/departments/{id}` 返回 405，部门无法从前端删除。
  - 红灯确认：有在职员工的部门删除应被拦截，而不是盲删。
- 代码面：
  - `organization/employees.py` 新增 `DELETE /employees/{emp_id}`，采用软停用：`is_active=False`、`employment_status=resigned`，保留员工历史资料。
  - `organization/departments_refactored.py` 新增 `DELETE /departments/{dept_id}`，采用软停用：`is_active=False`。
  - 部门删除前检查启用子部门和在职员工，存在则 400，避免破坏组织/员工历史关系。
  - 删除权限按软状态更新处理，沿用现有 `hr:update` 权限，不新增未种子的 `hr:delete`。
- 验证：
  - `.venv/bin/python -m pytest -q tests/api/test_org_delete_hr04.py` 红后绿通过（3 个用例）。
  - `.venv/bin/python -m pytest -q tests/api/test_org_delete_hr04.py tests/api/test_organization.py tests/api/test_org_api.py` 通过（19 passed、2 skipped；skip 为既有 schema/旧 API mismatch）。
  - `.venv/bin/python -m pytest -q tests/api/test_hr_bonus_permission_contracts.py::test_org_employee_and_hr_profile_endpoints_require_hr_permissions` 通过。
  - `.venv/bin/python -m ruff check app/api/v1/endpoints/organization/employees.py app/api/v1/endpoints/organization/departments_refactored.py tests/api/test_org_delete_hr04.py` 通过。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/organization/employees.py app/api/v1/endpoints/organization/departments_refactored.py tests/api/test_org_delete_hr04.py` 通过。
  - `import app.main` 路由清单确认 `DELETE /api/v1/org/employees/{emp_id}` 与 `DELETE /api/v1/org/departments/{dept_id}` 已注册。
- 边界：HR-03/HR-05 已在后续小步完成部门 ID 优先主链路；更复杂的部门同义词和历史字符串清洗仍留给数据治理专项。
- 台账：`FUNCTIONAL_AUDIT_TRACKER.md` 中 `HR-04` 已改为 `已验证`。

## 2026-07-04 维护：根目录清理与报告归档

- 清理目标：减少 `/Users/flw/non-standard-automation-pm` 根目录报告/阶段性文档堆积，保留代码、配置、启动脚本和核心入口文件。
- 已归档：
  - 根目录验收报告、审计报告、路线图、Backlog、矩阵、设计稿、`PERMISSION_COVERAGE_AUDIT.json` 等 45 个文件已移至 `docs/root-docs-archive/20260704/`。
  - `FUNCTIONAL_AUDIT_TRACKER.md` 也已移至 `docs/root-docs-archive/20260704/FUNCTIONAL_AUDIT_TRACKER.md`；后续更新功能审计台账请写这个新路径。
  - `RELEASE_GUIDE.md` 已移至 `docs/deployment/RELEASE_GUIDE.md`。
  - `DB-SYNC-README.md` 已移至 `docs/development/DB-SYNC-README.md`。
- 已删除/移走的本地产物：
  - 根目录重复 `app.db` 已移至废纸篓；开发默认数据库仍是 `data/app.db`。
  - `.gstack/db-backups`、`.gstack/qa-reports`、`.gstack/tmp`、`frontend/dist`、`frontend/test-results`、`.ruff_cache`、`.pytest_cache` 和旧 `__pycache__` 已移至废纸篓。
- 保留根目录：
  - `AGENTS.md`、`README.md`、`CHANGELOG.md`、`PROJECT_NOTES.md`、`pyproject.toml`、`pytest.ini`、`ruff.toml`、`requirements-dev.txt`、`vercel.json`、启动/同步脚本，以及源码/数据/迁移/测试目录。
- 未清理的大头：
  - `frontend/node_modules` 和 `.venv` 当时有 Vite/pytest 进程占用，先不动；如停掉服务后需要进一步瘦身，可删除后重新安装依赖。

## 2026-07-04 维护：过时文档归档

- 清理目标：减少 `docs/` 下“实施完成/交付总结/最终报告/阶段状态”类一次性文档对当前资料入口的干扰。
- 已归档：
  - 34 个明显过时的一次性文档已通过 `git mv` 移至 `docs/archive/stale-docs-20260704/`，并新增 `docs/archive/stale-docs-20260704/README.md` 记录归档标准与清单。
  - 重点归档类型包括旧进度台账、旧交付总结、旧代码质量报告、AI Agent 子任务实施报告、权限/2FA/EVM/售前 AI/工时提醒等阶段性完成报告。
- 暂不归档：
  - `docs/api/` 的 API summary 文档虽然日期较老且多处写有 `2025-01-XX`，但需要和真实路由对账后再处理。
  - `docs/design/`、`docs/deployment/`、`docs/security/` 中仍可能作为规范、运行手册或安全要求使用的文档，先保留。
  - `docs/root-docs-archive/20260704/` 是本轮根目录清理新收纳的验收/审计材料，不重复归档。

## 2026-07-05 维护：毛利率分析能力提升方案复验收尾

- 修复目标：按 `docs/毛利率分析能力提升方案.md` 的验收标准补齐毛利率专项测试与覆盖率，消除旧测试和当前 ORM 实现之间的不一致。
- 代码面：
  - `app/api/v1/endpoints/margin_prediction.py` 增加 `get_cost_variance()` 兼容别名，实际复用 `get_margin_variance()`。
  - `app/services/margin_permission_service.py` 增加可选 `db` 初始化，兼容既有测试和实例化使用。
- 测试面：
  - `tests/test_margin_prediction_api.py` 从旧 `db.execute()` mock 口径改为当前 ORM 查询口径，并补 BOM 成本汇总测试。
  - `tests/unit/test_profit_analysis_service_coverage.py` 补 `calculate_project_profit`、`calculate_gross_margin`、`allocate_costs` 分支测试。
- 验证：
  - `.venv/bin/python -m pytest -q tests/test_margin_prediction_api.py tests/unit/test_margin_permission_service_coverage.py` 通过（10 个用例）。
  - `.venv/bin/python -m pytest -q tests/unit/test_profit_analysis_service_coverage.py` 通过（8 个用例）。
  - 毛利率专项覆盖率命令通过（120 passed）；`profit_analysis_service.py` 覆盖率 94%，`margin_prediction.py` 覆盖率 92%，均超过方案要求。
  - `.venv/bin/python -m ruff check app/api/v1/endpoints/margin_prediction.py app/services/margin_permission_service.py tests/test_margin_prediction_api.py tests/unit/test_profit_analysis_service_coverage.py tests/unit/test_margin_permission_service_coverage.py` 通过。
  - `.venv/bin/python -m py_compile app/api/v1/endpoints/margin_prediction.py app/services/margin_permission_service.py tests/test_margin_prediction_api.py tests/unit/test_profit_analysis_service_coverage.py tests/unit/test_margin_permission_service_coverage.py` 通过。

## 2026-07-05 维护：销售目标 V2 合并退役

- 清理目标：收口 `sales_targets` 与 `sales_targets_v2` / `target_breakdown_logs` 的销售目标双轨，保留 `/sales/targets` 现有正式主链。
- 执行结果：
  - 真实库 `data/app.db` 删除后业务表数为 565。
  - `sales_targets_v2` 28 行和 `target_breakdown_logs` 20 行已归档到 `data/retired_unused_tables_archive_20260705_121036.db`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_121036.db`。
  - 14 行有效 V2 目标拆成正式 `sales_targets` 的 56 行，指标映射为 `sales_target -> CONTRACT_AMOUNT`、`payment_target -> COLLECTION_AMOUNT`、`lead_target -> LEAD_COUNT`、`opportunity_target -> OPPORTUNITY_COUNT`。
  - 14 行明显生成脏数据（`target_year=4/7/10/13/16/19/22/25` 等）只归档，不写入正式目标表。
  - V2 的 `new_customer_target`、`deal_target` 暂无正式目标枚举承接，只保存在归档原始行中，未强行污染正式目标看板。
- 代码面：
  - `scripts/retire_unused_tables_20260705.py` 增加销售目标 V2 合并逻辑、合并 manifest、并把 `sales_targets_v2` / `target_breakdown_logs` 纳入退役表集合。
  - `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` 增加两张 V2 表的防回潮 drop。
  - `app/models/sales/__init__.py` 停止注册 `SalesTargetV2` / `TargetBreakdownLog`，避免主模型元数据重新带回 V2 表。
  - `tests/unit/test_unused_table_retirement.py` 增加“先合并再退役”守护测试，并断言 V2 表不再进入主模型元数据。
- 验证：
  - `.venv/bin/python -m pytest tests/unit/test_unused_table_retirement.py tests/unit/test_shortage_alert_task_backfill.py -q` 通过（14 passed）。
  - `.venv/bin/ruff check scripts/retire_unused_tables_20260705.py tests/unit/test_unused_table_retirement.py app/models/sales/__init__.py` 通过。
  - `.venv/bin/python -m py_compile scripts/retire_unused_tables_20260705.py tests/unit/test_unused_table_retirement.py` 通过。
  - `sqlite3 data/app.db` 复核 `sales_targets_v2` / `target_breakdown_logs` 已不存在，`sales_targets` 现有 85 行。
- 边界：`app/services/sales_target_service.py`、`app/api/v1/endpoints/sales/targets_standalone.py`、`app/schemas/sales_target.py` 仍是未挂载的 V2 代码残留；主模型和主路由已断开。后续如继续深清理，可删除这些未挂载文件及其专用测试。

## 2026-07-05 维护：旧权限表合并退役

- 清理目标：收口旧 `permissions` / `role_permissions` 与新 `api_permissions` / `role_api_permissions` 双轨，保留当前统一权限引擎主链。
- 执行结果：
  - 真实库 `data/app.db` 删除后业务表数为 563。
  - 旧 `permissions` 323 行、旧 `role_permissions` 6 行已归档到 `data/retired_unused_tables_archive_20260705_121755.db`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_121755.db`。
  - 旧角色权限 6 条全部迁到 `role_api_permissions`。
  - 其中 4 个权限码复用既有 `api_permissions`，2 个已绑定但缺失的新权限码补入 `api_permissions`：`advantage_products:product:manage`、`advantage_products:product:read`。
  - 旧 `permissions` 中 317 个未被角色绑定的权限定义只归档，不写入新权限中心，避免旧种子污染权限管理页。
  - `permission_cache_revisions` 已 bump `system` 与 `tenant:1` 两个 scope。
- 代码面：
  - `scripts/retire_unused_tables_20260705.py` 增加旧权限合并逻辑和 `legacy_permission_merge_manifest`，并把 `role_permissions` / `permissions` 纳入退役表集合。
  - `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` 增加两张旧权限表的防回潮 drop。
  - `tests/unit/test_unused_table_retirement.py` 增加“只迁已绑定旧权限”的守护测试，防止把未绑定旧权限种子整包复活。
- 验证：
  - `.venv/bin/python -m pytest tests/unit/test_unused_table_retirement.py tests/unit/test_shortage_alert_task_backfill.py tests/unit/test_permission_engine.py tests/unit/test_permission_cache_perm13.py -q` 通过（29 passed）。
  - `.venv/bin/ruff check scripts/retire_unused_tables_20260705.py tests/unit/test_unused_table_retirement.py app/models/sales/__init__.py` 通过。
  - `.venv/bin/python -m py_compile scripts/retire_unused_tables_20260705.py tests/unit/test_unused_table_retirement.py` 通过。
  - `import app.main` 通过，路由加载失败 0；`Base.metadata.tables` 中 `permissions` / `role_permissions` 均不存在。
  - `sqlite3 data/app.db` 复核旧权限两表已不存在，`api_permissions=364`、`role_api_permissions=1056`。
- 边界：部分历史脚本/迁移仍含旧 `permissions` / `role_permissions` 字样，用于旧库诊断或历史迁移；运行主链和真实库已不再依赖旧表。后续如做脚本卫生，可把旧导出/诊断脚本改查新权限链或移入 archive。

## 2026-07-05 维护：售前方案模板复数表合并退役

- 清理目标：收口 `presale_solution_template` 与旧 AI 模板表 `presale_solution_templates` 双轨，保留正式售前方案模板表作为唯一事实源。
- 执行结果：
  - 真实库 `data/app.db` 删除后业务表数为 562。
  - 旧 `presale_solution_templates` 3 行已归档到 `data/retired_unused_tables_archive_20260705_122850.db`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_122850.db`。
  - 旧表 3 行按 `code` 对齐正式表 `template_no`，均命中既有正式模板编号，记录为 `updated_existing=3`，没有新增重复模板。
  - 旧表 3 行本身是占位 seed，没有额外有效方案内容；正式表仍保留原有 3 条模板记录。
- 代码面：
  - `app/services/presale/presale_ai_service.py` 改读正式 `PresaleSolutionTemplate`，兼容映射 `test_type -> equipment_type`、`use_count -> usage_count`、`content_template -> solution_content`。
  - `app/services/presale/ammo_library_service.py` 原生 SQL 改查 `presale_solution_template`，弹药库方案推荐不再依赖旧复数表。
  - `app/models/presale_ai_solution.py` 中 `PresaleAISolutionTemplate` 改为正式模板模型兼容别名，避免 SQLAlchemy metadata 重建 `presale_solution_templates`。
  - `scripts/retire_unused_tables_20260705.py` 增加旧 AI 模板合并逻辑和 `presale_solution_template_merge_manifest`，并把旧复数表纳入退役集合。
  - `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` 增加旧复数表防回潮 drop；`scripts/ghost_tables_baseline.json` 移除旧模型基线项。
- 验证：
  - `.venv/bin/python -m pytest tests/unit/test_unused_table_retirement.py tests/unit/test_presale_ai_service.py tests/unit/test_presale_ai_mock_guard.py -q` 通过（45 passed）。
  - `.venv/bin/ruff check app/services/presale/presale_ai_service.py app/services/presale/ammo_library_service.py app/models/presale_ai_solution.py app/core/database/tenant_scope.py scripts/retire_unused_tables_20260705.py tests/unit/test_presale_ai_service.py tests/unit/test_unused_table_retirement.py` 通过。
  - `Base.metadata.tables` 中 `presale_solution_templates=False`、`presale_solution_template=True`。
  - `sqlite3 data/app.db` 复核 `presale_solution_templates` 已不存在，`presale_solution_template` 仍有 3 行。
  - `PRAGMA foreign_key_check` 未新增问题；仍只有既有 `work_order -> worker`、`stock_count_detail -> stock_count_task`、`permission_audits -> users`、`presale_expenses -> projects`。
- 边界：历史迁移文件仍含 `presale_solution_templates` 的创建/回滚定义，属于旧版本迁移记录；运行主链、模型 metadata 和真实库已不再依赖旧表。

## 2026-07-05 维护：空 solution_versions 表和绑定验证原型链退役

- 清理目标：收口空 `solution_versions` 表及其配套的绑定校验原型链，避免售前方案、报价版本、成本估算继续指向一张没有数据、没有正式 API 主入口的旧表。
- 执行结果：
  - 真实库 `data/app.db` 删除后业务表数为 561。
  - `solution_versions` 0 行已归档到 `data/retired_unused_tables_archive_20260705_123626.db`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_123626.db`。
  - `presale_ai_solution.current_version_id`、`quote_versions.solution_version_id`、`presale_ai_cost_estimation.solution_version_id` 当前均无非空数据，本轮拆除 FK/关系，仅保留可空兼容列。
- 代码面：
  - 删除 `SolutionVersion` 模型、Schema 和销售模型导出，`Base.metadata.tables` 不再注册 `solution_versions`。
  - 删除未挂载的绑定校验服务、对应单测、前端 `solutionVersionService`、绑定校验卡片/弹窗和销售版本历史组件。
  - `scripts/retire_unused_tables_20260705.py` 与 `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` 增加 `solution_versions` 防回潮删除。
  - `scripts/ghost_tables_baseline.json` 移除 `SolutionVersion(solution_versions)` 基线项。
- 验证：
  - `.venv/bin/python -m pytest tests/unit/test_unused_table_retirement.py tests/unit/test_presale_ai_service.py tests/unit/test_presale_ai_mock_guard.py -q` 通过（46 passed）。
  - `.venv/bin/ruff check app/models/presale_ai_solution.py app/models/sales/quotes.py app/models/sales/presale_ai_cost.py app/models/sales/__init__.py scripts/retire_unused_tables_20260705.py tests/unit/test_unused_table_retirement.py` 通过。
  - `.venv/bin/python -m py_compile app/models/presale_ai_solution.py app/models/sales/quotes.py app/models/sales/presale_ai_cost.py app/models/sales/__init__.py scripts/retire_unused_tables_20260705.py tests/unit/test_unused_table_retirement.py` 通过。
  - `import app.main` 通过，路由加载失败 0；`Base.metadata.tables` 中 `solution_versions=False`，且无模型 FK 指向 `solution_versions`。
  - `npm --prefix frontend run build` 通过；只有既有 Node/Vite 警告和 chunk size 警告。
  - `sqlite3 data/app.db` 复核 `solution_versions` 已不存在；归档库 manifest 记录 `solution_versions row_count=0`。
  - `PRAGMA foreign_key_check` 未新增问题；仍只有既有 `work_order -> worker`、`stock_count_detail -> stock_count_task`、`permission_audits -> users`、`presale_expenses -> projects`。

## 2026-07-05 维护：空数据范围规则表退役

- 清理目标：收口空 `role_data_scopes` / `data_scope_rules`。这套资源级自定义数据范围表在 PERM-16 已确认“死在实践中”，真实运行口径是 `roles.data_scope`。
- 执行结果：
  - 真实库 `data/app.db` 删除后业务表数为 559。
  - `role_data_scopes` 0 行、`data_scope_rules` 0 行已归档到 `data/retired_unused_tables_archive_20260705_124356.db`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_124356.db`。
- 代码面：
  - `DataScopeRule` / `RoleDataScope` 改为非 ORM 兼容壳，不再注册 SQLAlchemy 表；`Role.data_scopes`、`Tenant.data_scope_rules` 关系已移除。
  - `PermissionService.get_user_data_scopes()` 改为从有效角色 `data_scope` 取最大范围，并给销售、报价、工时、工程绩效等常用 resource key 保留兼容映射。
  - `DataScopeServiceEnhanced` 增加 `*` 兜底；`CustomRuleService.get_custom_rule()` 不再查询旧表。
  - 租户共享白名单 `_SHARED_WHEN_NULL_MODEL_NAMES` 移除 `DataScopeRule`，不再把退役表当共享配置模型处理。
  - `scripts/retire_unused_tables_20260705.py`、`migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` 和 `scripts/ghost_tables_baseline.json` 已同步。
- 验证：
  - 新增守护测试先红后绿：ORM metadata 不再包含两张表；退役脚本能归档并按依赖顺序删除空表。
  - `.venv/bin/python -m pytest tests/unit/test_unused_table_retirement.py::test_retired_models_are_not_registered_in_sqlalchemy_metadata tests/unit/test_unused_table_retirement.py::test_retire_unused_tables_archives_empty_data_scope_tables_before_drop -q` 通过。
  - `.venv/bin/python -m pytest tests/unit/test_g3_permission_service.py::TestGetUserDataScopes tests/unit/test_permission_service_branches.py::TestPermissionServiceBranches::test_get_user_data_scopes_all tests/unit/test_permission_service_branches.py::TestPermissionServiceBranches::test_get_user_data_scopes_priority tests/unit/test_engperf_data_scope.py::TestDataScopeMerge::test_multiple_roles_take_highest_scope tests/unit/test_permission_and_data_scope_normalization.py::test_data_scope_rule_get_scope_config_dict_parses_json_string tests/unit/test_permission_service_practical.py::TestPermissionService::test_get_user_permissions_basic -q` 通过。
  - `import app.models` 元数据复核：`data_scope_rules=False`、`role_data_scopes=False`，且无 FK 指向这两张表。
  - `sqlite3 data/app.db` 复核两张表已不存在；归档库 manifest 记录两张表均为 0 行。
  - `PRAGMA foreign_key_check` 未新增问题；仍只有既有 `work_order -> worker`、`stock_count_detail -> stock_count_task`、`permission_audits -> users`、`presale_expenses -> projects`。

## 2026-07-05 维护：售后旧工单影子表并入中心服务工单

- 清理目标：收口旧 `after_sales_support_tickets` 与中心 `service_tickets` 的售后工单双轨。AS-07 已经把售后中心创建/列表改到中心服务工单，本轮删除空影子表并处理依附外键。
- 执行结果：
  - 真实库 `data/app.db` 删除后业务表数为 558，空表数为 61。
  - `after_sales_support_tickets` 0 行已归档到 `data/retired_unused_tables_archive_20260705_125345.db`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_125345.db`。
  - 保留 `after_sales_field_services`、`after_sales_sla`、`after_sales_satisfaction`；脚本重建这 3 张空依附表，把 `ticket_id` 外键从旧影子表改指向 `service_tickets`。
- 代码面：
  - 删除 `AfterSalesSupportTicket` ORM 和模型导出，`Base.metadata.tables` 不再注册 `after_sales_support_tickets`。
  - `AfterSalesFieldService.ticket_id`、`AfterSalesSLA.ticket_id`、`AfterSalesSatisfaction.ticket_id` 改为 FK 到 `service_tickets.id`。
  - `after_sales.py` 去掉 legacy 工单查询/格式化；工单列表、创建、升级统一使用 `ServiceTicket`。
  - `project_after_sales_view.py` 售后总览改从 `ServiceTicket` 汇总支持工单。
  - `scripts/retire_unused_tables_20260705.py` 增加针对空售后依附表的安全重建逻辑，避免删除旧表后留下无效 FK。
- 验证：
  - 新增守护测试先红后绿：ORM metadata 不含旧表；退役脚本能归档旧表、重建依附表并把外键改到 `service_tickets`。
  - 真实库复核：`after_sales_support_tickets` 已不存在；3 张依附表仍存在；三者 `ticket_id` 均指向 `service_tickets.id`。
  - `PRAGMA foreign_key_check` 未新增问题；仍只有既有 `work_order -> worker`、`stock_count_detail -> stock_count_task`、`permission_audits -> users`、`presale_expenses -> projects`。
- 边界：本轮不是删除售后模块；质保、备件、现场服务、SLA、满意度、知识库等售后表继续保留。

## 2026-07-05 维护：项目变更旧审批明细并入统一审批日志

- 清理目标：收口 `change_approval_records` 与统一审批动作日志的双轨。项目变更主事实继续保留在 `change_requests`，审批动作历史统一写 `approval_action_logs`。
- 执行结果：
  - 真实库 `data/app.db` 删除后业务表数为 557，空表数为 61。
  - `change_approval_records` 3 行已归档到 `data/retired_unused_tables_archive_20260705_130451.db`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_130451.db`。
  - 迁移新增 `approval_instances=3`、`approval_action_logs=3`；旧表 3 条 `decision` 均为脏值 `ch230356`，按 `change_requests.status` 推断 2 条 `APPROVE`，1 条保留为 `COMMENT`，原值写入 `action_detail`。
- 代码面：
  - `ChangeApprovalRecord` 改为非 ORM 兼容壳，不再注册 `change_approval_records`。
  - `ProjectChangeRequestsService.approve_change_request()` 不再写旧表，改写统一 `ApprovalActionLog`。
  - `ProjectChangeRequestsService.get_approval_records()` 改从 `approval_instances` / `approval_action_logs` 回放旧接口字段。
  - `scripts/retire_unused_tables_20260705.py` 增加旧项目变更审批明细迁移逻辑，并把旧表纳入退役集合。
  - `tests/api/test_path_param_route_contracts.py` 的旧表插入用例改为统一审批日志，避免测试回潮。
- 验证：
  - 新增守护测试先红后绿：服务层不再 add `ChangeApprovalRecord`，退役脚本会先迁移再删除旧表。
  - `.venv/bin/python -m pytest tests/unit/test_unused_table_retirement.py tests/unit/test_project_change_requests_service.py -q` 通过（57 passed）。
  - 真实库复核：`change_approval_records` 已不存在；`PROJECT_CHANGE_REQUEST` 统一实例 3 条、动作日志 3 条。
  - `PRAGMA foreign_key_check` 未新增问题；仍只有既有 `work_order -> worker`、`stock_count_detail -> stock_count_task`、`permission_audits -> users`、`presale_expenses -> projects`。

## 2026-07-05 维护：工时旧审批日志退役

- 清理目标：收口 `timesheet_approval_log` 与统一审批动作日志的双轨。工时审批接口已经使用 `ApprovalEngineService`，审批历史统一读 `approval_action_logs`。
- 执行结果：
  - 真实库 `data/app.db` 删除后业务表数为 556，空表数为 61。
  - `timesheet_approval_log` 20 行已归档到 `data/retired_unused_tables_archive_20260705_132031.db`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_132031.db`。
  - 20 行旧日志均无 `timesheet_id` / `batch_id`，且 `action` 全是 `timesheet_appr230118` 脏值；判定为孤儿生成残留，只归档、不伪造统一审批实例。
- 代码面：
  - `TimesheetApprovalLog` 改为非 ORM 兼容壳，不再注册 `timesheet_approval_log`。
  - `scripts/retire_unused_tables_20260705.py` 增加有锚点旧工时日志迁入 `approval_instances` / `approval_action_logs` 的逻辑；无锚点行跳过但保留外部归档。
  - 工时集成测试改为写入/查询 `ApprovalInstance` + `ApprovalActionLog`，不再手工造旧表日志。
  - `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` 增加旧表 DROP 防回潮；`scripts/ghost_tables_baseline.json` 移除 `TimesheetApprovalLog(timesheet_approval_log)`。
- 验证：
  - 新增守护测试先红后绿：有 `timesheet_id` 的旧日志会迁入统一审批日志，无实体锚点旧日志只归档跳过。
  - `pytest tests/unit/test_unused_table_retirement.py -q` 通过（12 passed）。
  - `pytest tests/integration/test_timesheet_flow_integration.py -q` 通过（8 passed）。
  - 真实库复核：`timesheet_approval_log` 已不存在；`approval_instances` / `approval_action_logs` 的 `TIMESHEET` 计数仍为 0，未被孤儿脏数据污染。
  - `PRAGMA foreign_key_check` 未新增问题；仍只有既有 `work_order -> worker`、`stock_count_detail -> stock_count_task`、`permission_audits -> users`、`presale_expenses -> projects`。

## 2026-07-05 维护：ECN旧审批表并入统一审批任务

- 清理目标：收口 `ecn_approvals` / `ecn_approval_matrix` 与统一审批引擎的双轨。ECN 审批主链保留 `approval_instances` / `approval_tasks` / `approval_action_logs`。
- 执行结果：
  - 真实库 `data/app.db` 删除后业务表数为 554。
  - `ecn_approvals` 3 行、`ecn_approval_matrix` 3 行已归档到 `data/retired_unused_tables_archive_20260705_133524.db`。
  - 删除前整库备份：`data/app.before_unused_tables_drop_20260705_133524.db`。
  - 3 条旧 `ecn_approvals` 都缺少有效审批人/审批结果，判定为生成残留；只归档不伪造统一审批日志。真实库 ECN 统一审批保持 `approval_instances=1`、`approval_action_logs=7`。
- 代码面：
  - `EcnApproval` / `EcnApprovalMatrix` 改为非 ORM 兼容壳，不再注册 `ecn_approvals` / `ecn_approval_matrix`。
  - ECN 评估完成后改调用 `EcnApprovalService` 提交统一审批；旧审批矩阵创建记录逻辑移除。
  - ECN 超时提醒、定时任务、物料干系人、评估通知、工程看板统计均改读统一审批任务。
  - `EcnApprovalAdapter.create_ecn_approval_records()` 兼容旧方法名，但只返回统一 `ApprovalTask`，不再同步旧表。
  - `scripts/retire_unused_tables_20260705.py` 增加 ECN 旧审批迁移/归档逻辑；`migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` 增加旧表 DROP；`scripts/ghost_tables_baseline.json` 移除旧矩阵 ghost。
- 验证：
  - 新增守护测试先红后绿：旧 ECN 审批行有有效锚点时会迁入统一审批实例/日志；无效行只归档跳过。
  - `python -m pytest tests/unit/test_unused_table_retirement.py tests/unit/test_ecn_scheduler_service.py -q` 通过（29 passed）。
  - `python -m ruff check ...` 和 `python -m py_compile ...` 通过。
  - `from app.main import app` 路由加载通过，路由失败汇总 0 项。
  - 真实库复核：`ecn_approvals` / `ecn_approval_matrix` 已不存在；归档库两表各 3 行，manifest 完整；`PRAGMA foreign_key_check` 未新增问题，仍只有既有孤儿外键项。
