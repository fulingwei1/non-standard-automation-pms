# 数据库表存废台账（第一版）

日期：2026-07-05

数据库：`/Users/flw/non-standard-automation-pm/data/app.db`

本版目标：先收口明显的业务重复、新旧双轨、生成残留。不要据此直接删表；任何删表/合表都必须另起迁移任务，先备份，再跑引用扫描和回归。

## 当前总览

| 指标 | 数量 | 说明 |
|---|---:|---|
| 业务表总数 | 553 | 排除 `sqlite_%` 内部表；2026-07-05 未启用报价成本历史表退役后复核 |
| 空表 | 61 | 已存在 schema，但当前无数据 |
| 非空 1-3 行小表 | 225 | 其中很多是批量种子或脚手架数据 |
| 刚好 3 行表 | 213 | 高度疑似自动生成 demo/seed 数据 |
| 无 SQLAlchemy 模型表 | 10 | 需要特别谨慎，可能是迁移残留/裸 SQL 表/历史表 |
| 后端代码零引用表 | 0 | 不含迁移/docs/test 引用；按 `app/` 精确表名扫描 |
| 完全同字段结构重复组 | 0 | 当前不是“复制表”问题，而是同业务多套实现并存 |

## 状态口径

| 状态 | 含义 |
|---|---|
| 保留 | 当前主链读写或明确业务事实源 |
| 合并 | 应并入主事实源，但要先做字段映射、数据迁移和回归 |
| 只读历史 | 保留一个周期用于审计、回滚、ID 映射或历史追溯 |
| 废弃 | 已确认不应再作为业务读写源；归档/备份/回归通过后删除 |
| 废弃候选 | 无主链消费、空表或纯种子残留；确认后可迁移删除 |
| 待确认 | 有模型/服务或少量数据，但产品归属、入口或事实源不清 |
| 隔离保留 | 名字像重复，但实际属于不同业务域；建议改名或补文档 |

## 2026-07-05 补充：审批统一处理进度

- 主事实源已定为统一审批引擎：`approval_templates`、`approval_instances`、`approval_tasks`、`approval_action_logs`。
- 销售域旧审批配置路由 `/sales/approval-workflows` 已从销售聚合路由移除，旧路由文件 `sales/workflows.py` 已删除；审批办理、待办和动作继续走统一 `/approvals`。
- 销售报价、发票、合同审批适配器已停止回写 `quote_approvals`、`invoice_approvals`、`contract_approvals` 这类专用审批表。
- 兼容门面 `ApprovalWorkflowService` 和销售审批超时提醒已改查 `approval_instances/approval_tasks`，不再依赖 `approval_records/approval_workflow_steps`。
- 新增归档脚本 `scripts/consolidate_legacy_approval_tables.py`，在临时复制库中演练 `--drop-legacy-tables`：共归档 125 行到 `legacy_approval_archives`，并删除 11 张旧审批表；真实 `data/app.db` 未执行删除。
- 后续已在真实库执行旧审批表归档删除：真实 `data/app.db` 中 11 张旧审批表已不存在，`legacy_approval_archives` 保留 125 行只读历史；详见 `PROJECT_NOTES.md` 的“真实库旧审批表删除与统一引擎收口”。
- 流程/状态机另起台账：`docs/database/process-engine-survival-ledger-20260705.md`。

## 2026-07-05 补充：报价双轨收口路线

- 正式销售报价事实源保持唯一：`quotes`、`quote_versions`、`quote_items`。
- `presale_ai_quotation` 不作为合同、审批、销售报表的正式金额源；定位改为“AI 生成报价草稿/比选工作台”。
- 新增 `AIQuotationGeneratorService.promote_to_sales_quote()` 与 `/presale/ai/quotation/{quotation_id}/promote-to-sales-quote`：人工采纳某个 AI 草稿后，复制到正式 `quotes/quote_versions/quote_items`，并把 AI 草稿标记为 `ACCEPTED`，备注保存 `promoted_quote_id`。
- `quotation_versions` 继续作为 AI 草稿版本快照保留；它不替代正式 `quote_versions`。
- 本轮未删除 `presale_ai_quotation` / `quotation_versions`，也未自动把真实库 9 条 AI 草稿转正式报价；真实转化需要业务选择哪一档报价。

## 2026-07-05 补充：当前可删除候选复核

本段基于当前真实库 `data/app.db` 复核，不使用旧快照。检查口径：

- 行数：`sqlite3 data/app.db`
- ORM 模型：扫描 `app/**/*.py` 的 `__tablename__`
- 应用引用：精确边界扫描 `app`、`frontend/src`、`scripts`
- 结构风险：检查外键、视图、触发器；当前候选未被视图/触发器挂住

### A. 第一批低风险删除迁移候选

这些表要走“备份 -> 迁移脚本 -> 回归”的删除流程，但业务上已经可以列入第一批。

| 表 | 行数 | 复核结果 | 删除前动作 |
|---|---:|---|---|
| `lead_requirement_basic_v2` | 0 | 仅 V2 空模型/ghost baseline；主链使用 `lead_requirement_details` | 删除 V2 模型导出和空表；先保留 V1 主链 |
| `lead_requirement_technical_v2` | 0 | 同上，仅依附 `lead_requirement_basic_v2` | 跟随 V2 基表删除 |
| `lead_requirement_facility_v2` | 0 | 同上，仅依附 `lead_requirement_basic_v2` | 跟随 V2 基表删除 |
| `currency_rates` | 7 | 无 ORM、无 app/frontend/scripts 引用、无外键 | 导出快照后删除 |
| `currency_history` | 20 | 无 ORM、无 app/frontend/scripts 引用、无外键 | 导出快照后删除 |
| `ecn_records` | 3 | 无 ORM、app 零引用；当前 ECN 主表是 `ecn` 及 `ecn_*` 子表 | 导出快照后删除，不能误删 `ecn_approvals`/`ecn_approval_matrix` |
| `shortage_alerts` | 3 | 无 ORM、无真实 SQL 读写；当前运营主表是 `material_shortages`，智能层是 `shortage_alerts_enhanced` | 导出快照后删除 |
| `mat_shortage_alert` | 3 | 无 ORM，仅调度配置字符串引用；缺料主链已是 `material_shortages`/智能层 | 确认调度 callable 不再写旧表后删除 |
| `quotation_templates` | 3 | 只有未启用模型/Schema；正式报价模板主链是 `quote_templates` | 删除未启用模型/Schema 后删表 |

### B. 有数据但像原型/种子残留，建议归档后整组删除

| 表组 | 行数 | 复核结果 | 删除前动作 |
|---|---:|---|---|
| `investors` / `funding_rounds` / `funding_records` / `equity_structures` / `funding_usages` | 3/3/3/3/3 | 无 ORM、无 app/frontend 引用；只有 `scripts/generate_finance_data.py` 这类生成脚本 | 整组导出后删除；删除顺序先子表后父表 |
| `department_default_roles` / `department_role_admins` / `role_template_permissions` | 6/6/6 | 无 ORM、无 app/frontend 引用；只剩旧角色脚本/种子残留 | 若不保留“部门默认角色/角色模板”功能，归档后删除 |
| `role_audits` | 20 | 无 ORM、无 app/frontend/scripts 引用；当前权限审计主表是 `permission_audits` | 如需留历史，转入归档；否则删除 |

### C. 只读历史，暂不建议立刻删

| 表 | 行数 | 原因 |
|---|---:|---|
| `legacy_approval_archives` | 125 | 11 张旧审批表已删后的唯一历史归档，至少保留一个审计/回滚周期 |
| `tasks_deprecated` | 131 | 旧任务表冻结体，`task_unified` 已是主链，但仍需短期追溯 |
| `task_id_map` | 131 | 旧任务 ID 到新任务 ID 的追溯映射，和 `tasks_deprecated` 同生命周期 |

### D. 不能直接删，必须先合并或改代码

| 表 | 行数 | 原因 |
|---|---:|---|
| `role_data_scopes` / `data_scope_rules` | 0/0 | 已在第八批处理中退役：真实口径改为 `roles.data_scope`，旧自定义数据范围表为空且不再注册 ORM |
| `sales_targets_v2` / `target_breakdown_logs` | 28/20 | 已在第四批处理中合并退役：有效 V2 目标拆入 `sales_targets`，原表和分解日志外部归档 |
| `presale_solution_templates` | 3 | 已在第六批处理中合并退役：服务改读 `presale_solution_template`，原表外部归档 |
| `solution_versions` | 0 | 已在第七批处理中退役：原型绑定链为空且无后端 API 主入口，保留兼容列但拆除 FK 和模型 |
| `after_sales_support_tickets` | 0 | 已在第九批处理中退役：售后工单统一走中心 `service_tickets`，3 张空依附表保留并改指中心工单 |
| `change_approval_records` | 3 | 已在第十批处理中退役：审批明细迁入 `approval_instances` / `approval_action_logs`，旧表外部归档 |
| `funnel_transition_logs` | 0 | 空表但销售漏斗状态机有专用消费，不能按空表删除 |
| `ecn_approvals` / `ecn_approval_matrix` | 3/3 | 已在第十二批处理中合并退役：ECN 审批运行链路改走统一审批任务，旧审批记录/矩阵外部归档 |
| `timesheet_approval_log` | 20 | 已在第十一批处理中退役：20 条均无 `timesheet_id`/`batch_id`，只外部归档、不迁入统一审批 |

### E. 第一批删除执行结果

已对真实库 `data/app.db` 执行第一批删除；删除前已做整库备份，所有被删表 schema/数据已写入外部 SQLite 归档库。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_113611.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_113611.db` |
| 删除脚本 | `scripts/retire_unused_tables_20260705.py` |
| 防回潮迁移 | `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` |
| 删除表 | `lead_requirement_facility_v2`、`lead_requirement_technical_v2`、`lead_requirement_basic_v2`、`funding_records`、`equity_structures`、`funding_usages`、`funding_rounds`、`investors`、`department_default_roles`、`department_role_admins`、`role_template_permissions`、`role_audits`、`currency_rates`、`currency_history`、`ecn_records`、`shortage_alerts`、`mat_shortage_alert`、`quotation_templates` |
| 删除后表数 | 572 |
| 模型收口 | 已删除 `LeadRequirement*V2` 空模型和未启用 `QuotationTemplate` 模型，防止 `create_all` 重新建表 |
| 外键检查 | 删除前后 `PRAGMA foreign_key_check` 输出完全一致；仍有既有非本轮问题：`work_order -> worker`、`stock_count_detail -> stock_count_task`、`permission_audits -> users`、`presale_expenses -> projects` |

### F. 第二批删除执行结果：旧 RBAC 残留

已对真实库 `data/app.db` 执行第二批旧 RBAC 残留删除。当前权限主链是 `user_roles` / `role_api_permissions` / `permission_audits`；本轮不动主链。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_114553.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_114553.db` |
| 删除视图 | `v_user_active_roles` |
| 删除表 | `role_exclusions`、`user_role_assignments` |
| 删除后表数 | 570 |
| 归档行数 | `role_exclusions=6`、`user_role_assignments=6` |
| 外键检查 | 删除前后 `PRAGMA foreign_key_check` 输出完全一致；未新增 FK 脏数据 |
| 剩余无模型表 | `ai_settings`、`ai_standard_modules`、`bom_versions`、`jwt_token_blacklist`、`legacy_approval_archives`、`lessons_learned`、`outsourcing_vendors`、`payments`、`permission_cache_revisions`、`permissions`、`position_role_mapping`、`role_permissions`、`suppliers`、`task_id_map`、`tasks_deprecated` |

结论：继续“按无模型表删”的空间已经很小。剩余无模型表里，`ai_settings`、`ai_standard_modules`、`permission_cache_revisions`、`jwt_token_blacklist`、`position_role_mapping` 等仍有运行代码直接读写。后续清理必须转向“合并类表”；其中权限旧表已在第五批完成，售前方案模板双轨已在第六批完成，空 `solution_versions` 已在第七批完成，空数据范围规则表已在第八批完成，售后旧工单影子表已在第九批完成，项目变更旧审批明细已在第十批完成，工时旧审批日志已在第十一批完成，仍待处理的是 ECN 审批迁统一引擎。

### G. 第三批删除执行结果：只读历史表外部归档

已对真实库 `data/app.db` 执行第三批只读历史表删除。历史数据不再留在主库；需要追溯时查本轮外部归档库或整库备份。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_120303.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_120303.db` |
| 删除表 | `legacy_approval_archives`、`tasks_deprecated`、`task_id_map` |
| 删除后表数 | 567 |
| 归档行数 | `legacy_approval_archives=125`、`tasks_deprecated=131`、`task_id_map=131` |
| 外键检查 | 删除前后 `PRAGMA foreign_key_check` 输出完全一致；未新增 FK 脏数据 |
| 剩余无模型表 | `ai_settings`、`ai_standard_modules`、`bom_versions`、`jwt_token_blacklist`、`lessons_learned`、`outsourcing_vendors`、`payments`、`permission_cache_revisions`、`permissions`、`position_role_mapping`、`role_permissions`、`suppliers` |

结论：当前按 `app/` 精确表名扫描，后端代码零引用表已经为 0。继续清理“没用表”不能再靠粗删，只能进入合并/迁移类工作：例如 ECN 审批迁统一审批引擎、售前 AI 报价草稿并入正式报价链。

### H. 第四批合并退役执行结果：销售目标 V2 并入正式目标表

已对真实库 `data/app.db` 执行销售目标双轨收口。正式事实源保留 `sales_targets`；V2 原表和目标分解日志不再留在主库。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_121036.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_121036.db` |
| 合并脚本 | `scripts/retire_unused_tables_20260705.py` |
| 防回潮迁移 | `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` |
| 合并策略 | V2 有效目标拆成正式表四类指标：`CONTRACT_AMOUNT`、`COLLECTION_AMOUNT`、`LEAD_COUNT`、`OPPORTUNITY_COUNT` |
| 合并结果 | V2 源表 28 行；14 行有效目标写入 `sales_targets` 56 行；14 行生成脏数据只归档、不进正式表 |
| 删除表 | `target_breakdown_logs`、`sales_targets_v2` |
| 删除后表数 | 565 |
| 模型收口 | `app/models/sales/__init__.py` 已停止注册 `SalesTargetV2` / `TargetBreakdownLog`，防止主模型元数据带回旧表 |
| 归档校验 | 归档库保留 `sales_targets_v2=28`、`target_breakdown_logs=20`，并记录 `sales_target_v2_merge_manifest`：`inserted=56`、`skipped=14` |

边界：V2 的 `new_customer_target`、`deal_target` 当前没有正式 `sales_targets` 枚举承接，已随原始 V2 行保存在归档库，未强行塞进正式目标看板。

### I. 第五批合并退役执行结果：旧权限表并入新权限引擎

已对真实库 `data/app.db` 执行权限旧表收口。当前权限主链为 `api_permissions` / `role_api_permissions` / `user_roles` / `permission_audits`；旧 `permissions` / `role_permissions` 不再作为业务读写源。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_121755.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_121755.db` |
| 合并脚本 | `scripts/retire_unused_tables_20260705.py` |
| 防回潮迁移 | `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` |
| 合并策略 | 只迁移旧 `role_permissions` 中实际被角色绑定的权限；未绑定旧权限定义只归档、不写入新权限中心 |
| 合并结果 | 旧 `permissions` 323 行、旧 `role_permissions` 6 行；4 个权限码复用既有 `api_permissions`，2 个已绑定但缺失的新权限码补入 `api_permissions`；6 条角色绑定写入 `role_api_permissions` |
| 删除表 | `role_permissions`、`permissions` |
| 删除后表数 | 563 |
| 归档校验 | 归档库保留 `permissions=323`、`role_permissions=6`，并记录 `legacy_permission_merge_manifest`：`api_permission_existing=4`、`api_permission_inserted=2`、`role_api_permission_inserted=6` |

边界：旧 `permissions` 中 317 个未被角色绑定的权限定义没有迁入新权限中心，只保留在归档库，避免把旧种子权限重新污染当前权限管理页。

### J. 第六批合并退役执行结果：售前方案模板复数表并入正式模板表

已对真实库 `data/app.db` 执行售前方案模板双轨收口。正式事实源保留 `presale_solution_template`；旧 AI 方案模板复数表 `presale_solution_templates` 不再留在主库。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_122850.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_122850.db` |
| 合并脚本 | `scripts/retire_unused_tables_20260705.py` |
| 防回潮迁移 | `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` |
| 合并策略 | 按旧表 `code` 对齐正式表 `template_no`；新编号插入正式表，已有编号只补正式表空字段；旧表原始行全部进入归档库 |
| 合并结果 | 旧表 3 行均命中正式表已有编号，记录为 `updated_existing=3`；未新增重复模板 |
| 删除表 | `presale_solution_templates` |
| 删除后表数 | 562 |
| 模型收口 | `PresaleAISolutionTemplate` 改为 `PresaleSolutionTemplate` 兼容别名，`Base.metadata.tables` 不再注册 `presale_solution_templates` |
| 服务收口 | `PresaleAIService` 与 `AmmoLibraryService` 均改读 `presale_solution_template`，字段映射为 `template_no/code`、`test_type/equipment_type`、`use_count/usage_count` |
| 归档校验 | 归档库保留 `presale_solution_templates=3`，并记录 `presale_solution_template_merge_manifest`：`updated_existing=3` |

边界：旧表 3 行本身也是占位 seed，没有额外有效方案内容；本轮没有制造新模板，只保留正式表原有 3 条记录。

### K. 第七批合并退役执行结果：空方案版本表和绑定原型链退役

已对真实库 `data/app.db` 执行空 `solution_versions` 表退役。该表没有业务数据，也没有实际后端 API 主入口；原先配套的绑定校验服务和前端组件属于未接入主链的“三位一体绑定”原型残留。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_123626.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_123626.db` |
| 删除脚本 | `scripts/retire_unused_tables_20260705.py` |
| 防回潮迁移 | `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` |
| 删除表 | `solution_versions` |
| 归档行数 | `solution_versions=0` |
| 删除后表数 | 561 |
| 模型收口 | 已删除 `SolutionVersion` 模型/Schema，`Base.metadata.tables` 不再注册 `solution_versions`，也没有任何模型 FK 指向该表 |
| 代码收口 | 已删除未挂载的绑定校验服务、死前端 service 和相关组件；`quote_versions.solution_version_id`、`presale_ai_cost_estimation.solution_version_id`、`presale_ai_solution.current_version_id` 仅保留为可空兼容列 |
| 回归验证 | 相关 pytest 46 个用例通过；ruff、py_compile、`import app.main`、前端 build 均通过；`PRAGMA foreign_key_check` 未新增问题 |

边界：本轮没有顺手删兼容列。三列当前均无非空数据，但删列会扩大迁移面，留给后续结构收缩窗口处理。

### L. 第八批合并退役执行结果：空数据范围规则表退役

已对真实库 `data/app.db` 执行空 `role_data_scopes` / `data_scope_rules` 表退役。PERM-16 已确认这套自定义资源级数据范围“死在实践中”，真实权限过滤口径为角色表 `roles.data_scope`。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_124356.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_124356.db` |
| 删除脚本 | `scripts/retire_unused_tables_20260705.py` |
| 防回潮迁移 | `migrations/20260705_z_drop_unused_residual_tables_sqlite.sql` |
| 删除表 | `role_data_scopes`、`data_scope_rules` |
| 归档行数 | `role_data_scopes=0`、`data_scope_rules=0` |
| 删除后表数 | 559 |
| 模型收口 | `DataScopeRule` / `RoleDataScope` 改为非 ORM 兼容壳；`Base.metadata.tables` 不再注册两张表，也没有 FK 指向它们 |
| 服务收口 | `PermissionService.get_user_data_scopes()` 改从有效角色 `data_scope` 取最大范围，并给销售、工时、工程绩效等资源键保留兼容映射 |
| 回归验证 | 相关 pytest 通过；`import app.models` 元数据检查通过；`PRAGMA foreign_key_check` 未新增问题 |

边界：前端/Schema 里仍保留 `data_scope_rules` 响应字段名，作为权限数据结构兼容字段，不再代表主库表。

### M. 第九批合并退役执行结果：售后旧工单影子表并入中心工单

已对真实库 `data/app.db` 执行旧售后技术支持工单表 `after_sales_support_tickets` 退役。售后中心创建、列表、升级统一走中心服务工单 `service_tickets`，不再维护影子工单表。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_125345.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_125345.db` |
| 删除脚本 | `scripts/retire_unused_tables_20260705.py` |
| 删除表 | `after_sales_support_tickets` |
| 归档行数 | `after_sales_support_tickets=0` |
| 删除后表数 | 558 |
| 模型收口 | 删除 `AfterSalesSupportTicket` ORM；`Base.metadata.tables` 不再注册 `after_sales_support_tickets`，也无 FK 指向该表 |
| 依附表处理 | 保留 `after_sales_field_services`、`after_sales_sla`、`after_sales_satisfaction`，并把 `ticket_id` 外键从旧影子表改指向 `service_tickets` |
| 服务收口 | 售后工单列表/创建/升级和项目售后总览统一读写 `ServiceTicket` |
| 回归验证 | 退役守护测试先红后绿；真实库 FK 检查未新增问题 |

边界：这不是删除售后模块；质保、备件、现场服务、SLA、满意度、知识库等售后表继续保留。只删除了已经被中心服务工单替代的旧影子工单表。

### N. 第十批合并退役执行结果：项目变更审批明细并入统一审批日志

已对真实库 `data/app.db` 执行旧项目变更审批明细表 `change_approval_records` 退役。项目变更主状态继续保留在 `change_requests`，审批动作历史统一进入 `approval_instances` / `approval_action_logs`。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_130451.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_130451.db` |
| 删除脚本 | `scripts/retire_unused_tables_20260705.py` |
| 删除表 | `change_approval_records` |
| 归档行数 | `change_approval_records=3` |
| 迁移结果 | 新增 `approval_instances=3`、`approval_action_logs=3`，无跳过 |
| 删除后表数 | 557 |
| 模型收口 | `ChangeApprovalRecord` 改为非 ORM 兼容壳；`Base.metadata.tables` 不再注册旧表，也无 FK 指向旧表 |
| 服务收口 | `ProjectChangeRequestsService.approve_change_request()` 不再写旧表；审批明细查询改读统一审批日志 |
| 脏数据处理 | 旧表 3 条 `decision` 均为脏值 `ch230356`；迁移按 `change_requests.status` 推断 2 条 `APPROVE`，1 条保留为 `COMMENT`，原值写入 `action_detail` |
| 回归验证 | 退役守护测试和项目变更服务测试通过；真实库 FK 检查未新增问题 |

边界：这不是把项目变更主表并入审批表。`change_requests` 仍是项目变更事实主表；统一审批只承接“谁在何时做了什么审批动作”的审计日志。

### O. 第十一批合并退役执行结果：工时旧审批日志退役

已对真实库 `data/app.db` 执行旧工时审批日志表 `timesheet_approval_log` 退役。当前工时审批接口已经走 `ApprovalEngineService`，审批历史读取统一 `approval_action_logs`；旧表不再作为业务读写源。

| 项 | 结果 |
|---|---|
| 整库备份 | `data/app.before_unused_tables_drop_20260705_132031.db` |
| 外部归档库 | `data/retired_unused_tables_archive_20260705_132031.db` |
| 删除脚本 | `scripts/retire_unused_tables_20260705.py` |
| 删除表 | `timesheet_approval_log` |
| 归档行数 | `timesheet_approval_log=20` |
| 迁移结果 | 源表 20 行，全部缺少 `timesheet_id`/`batch_id`，判定为孤儿生成残留；未新增 `approval_instances` / `approval_action_logs` |
| 删除后表数 | 556 |
| 模型收口 | `TimesheetApprovalLog` 改为非 ORM 兼容壳；`Base.metadata.tables` 不再注册旧表，也无 FK 指向旧表 |
| 测试收口 | 工时集成测试改写为使用 `ApprovalInstance` / `ApprovalActionLog`，不再手工造旧表日志 |
| 回归验证 | 退役脚本测试、工时集成测试通过；真实库 FK 检查未新增问题 |

边界：这不是删除工时模块，也不是删除统一工时审批。`timesheet` / `timesheet_batch` 继续保留；有锚点的历史审批日志脚本会迁入统一审批日志，无锚点脏数据只外部归档。

## 第一批存废台账

### 1. 任务表双轨

| 表 | 行数 | 状态 | 证据 | 处置建议 |
|---|---:|---|---|---|
| `task_unified` | 222 | 保留 | `PROJECT_NOTES.md:2916-2967` 记录 P2/P3/P4 已完成，单一事实源为 `task_unified`；代码仍大量查询 `TaskUnified` | 作为任务唯一主表继续保留 |
| `tasks_deprecated` | 主库已删除 | 已归档/废弃 | 第三批只读历史表已外部归档删除 | 需要追溯时查 `data/retired_unused_tables_archive_20260705_120303.db` |
| `task_id_map` | 主库已删除 | 已归档/废弃 | 第三批只读历史表已外部归档删除 | 需要追溯时查同批归档库 |

结论：这一组已经不是“待修双轨”，而是收尾期历史表。不要继续围绕旧任务表修业务。

### 2. 销售目标双轨

| 表 | 行数 | 状态 | 证据 | 处置建议 |
|---|---:|---|---|---|
| `sales_targets` | 85 | 保留 | `/sales/targets` 正式路由使用 `SalesTarget`，前端销售目标页调用 `/sales/targets`；本轮已承接 V2 有效目标 56 行 | 当前主事实源 |
| `sales_targets_v2` | 28 | 已合并/废弃 | V2 路由未挂主入口；本轮有效目标已拆入 `sales_targets`，原始 28 行在外部归档库 | 主库已删除，禁止继续作为业务读写源 |
| `target_breakdown_logs` | 20 | 已归档/废弃 | 只依附 `sales_targets_v2`，本轮随 V2 外部归档 | 主库已删除 |

结论：销售目标双轨已收口。后续目标能力只补 `sales_targets` 主链，不再维护 V2 独立服务链。

### 3. 销售正式报价 vs 售前 AI 报价

| 表 | 行数 | 状态 | 证据 | 处置建议 |
|---|---:|---|---|---|
| `quotes` | 275 | 保留 | 销售合同链路主报价表，`app/models/sales/quotes.py`、`sales/quotes.py`、`sales/quote_versions.py` 等主链使用 | 销售报价事实源 |
| `quote_versions` | 275 | 保留 | 正式报价版本表，合同、成本、审批均依赖 | 保留 |
| `quote_items` | 697 | 保留 | 正式报价明细表，销售金额/成本主链依赖 | 保留 |
| `quote_templates` | 3 | 保留 | 销售报价模板生命周期已接入 `/sales` 路由 | 保留，但后续可和新版结构化模板入口做 API 层去重 |
| `quote_template_versions` | 3 | 保留 | `quote_templates` 子表 | 保留 |
| `quote_cost_templates` | 3 | 保留 | 报价成本模板，近期 PERM-07 已补审计日志 | 保留 |
| `quote_cost_histories` | 主库已删除 | 已归档/废弃 | 模型注释为“未启用”，运行代码无读写；3 行历史金额/成本关键字段为空，已外部归档删除 | 禁止复活，报价成本变更审计走 `sales_operation_logs` |
| `quote_cost_approvals` | 主库已删除 | 已归档/废弃 | 销售侧专用审批表，与统一审批引擎重叠；旧审批表归档删除时已处理 | 不再作为业务读写源 |
| `quote_approvals` | 主库已删除 | 已归档/废弃 | 销售侧报价审批表；报价审批适配器已停止回写旧表，真实库已删 | 不再作为业务读写源 |
| `presale_ai_quotation` | 9 | 保留（AI草稿源） | `/presale/ai/generate-quotation` 与三档报价仍写入；已新增采纳入口转正式 `quotes/quote_versions/quote_items` | 只保留为 AI 草稿/比选，不作为正式报价事实源 |
| `quotation_versions` | 9 | 保留（AI草稿历史） | `AIQuotationGeneratorService` 创建 AI 报价版本快照 | 跟随 AI 草稿生命周期保留；正式版本只看 `quote_versions` |
| `quotation_approvals` | 主库已删除 | 已归档/废弃 | AI 报价自有审批表已纳入旧审批表归档删除 | 不再作为业务读写源 |
| `quotation_templates` | 主库已删除 | 已归档/废弃 | 未启用报价模板残留，第一批未用表清理已删除 | 禁止复活，模板能力走 `quote_templates` |

结论：报价双轨已改成“正式报价唯一事实源 + AI 草稿源”。AI 生成结果只有在人工采纳后才进入 `quotes/quote_versions/quote_items`，合同、审批、报表不得直接把 `presale_ai_quotation` 当正式报价金额源。

### 4. 售前方案模板双轨

| 表 | 行数 | 状态 | 证据 | 处置建议 |
|---|---:|---|---|---|
| `presale_solution_template` | 3 | 保留 | `app/api/v1/endpoints/presale/templates.py` 正式模板 CRUD 使用该表 | 当前售前模板管理主表 |
| `presale_solution_templates` | 3 | 已合并/废弃 | 旧 AI 方案模板复数表；本轮服务已改读正式 `presale_solution_template`，原始 3 行在外部归档库 | 主库已删除，禁止继续作为业务读写源 |
| `solution_templates` | 4 | 隔离保留 | 属于问题/故障解决方案模板，不是售前方案模板 | 保留，但命名需在文档中区分 |
| `solution_versions` | 0 | 已归档/废弃 | 表为空，绑定校验服务和前端组件均未接入主链；第七批已拆 FK、删模型并外部归档 | 主库已删除；后续如要做方案版本化，应在正式售前方案/报价链上重建，不复活旧表 |

结论：售前方案模板双轨和空方案版本原型链都已收口。后续售前模板管理、AI 模板匹配、弹药库推荐统一读写 `presale_solution_template`；方案版本能力如要恢复，应接正式方案/报价主链。

### 5. 资源冲突表

| 表 | 行数 | 状态 | 证据 | 处置建议 |
|---|---:|---|---|---|
| `resource_conflicts` | 3 | 保留 | `app/api/v1/endpoints/analytics/resource_conflicts.py` 写明持久化到 `resource_conflicts`；模型在 `app/models/project/resource_plan.py` | 项目阶段资源计划冲突主表 |
| `resource_conflict` | 主库已改名 | 已改名/废弃 | 原生产排程冲突表；已改名为 `production_resource_conflicts` | 禁止复活旧裸名 |
| `production_resource_conflicts` | 3 | 保留 | `app/models/production/production_schedule.py` 中 `ProductionResourceConflict` 用于生产排程冲突 | 生产排程冲突主表，不与项目资源冲突表合并 |

结论：这组名字像重复，实际是两个业务域。已通过改名隔离：项目资源计划冲突继续用 `resource_conflicts`，生产排程冲突改为 `production_resource_conflicts`。

### 6. 缺料/预警表多轨

| 表 | 行数 | 状态 | 证据 | 处置建议 |
|---|---:|---|---|---|
| `material_shortages` | 6 | 保留 | `app/api/v1/endpoints/shortage/detection/alerts.py` 明确标为日常 CRUD 单一事实源 | 缺料预警状态流转主表 |
| `shortage_alerts_enhanced` | 3 | 隔离保留 | `app/models/shortage/smart_alert.py` 为智能缺料预警表；`shortage/smart_alerts.py` 的 list/detail/resolve 已标 deprecated，但 scan/forecast/solution 仍使用 | 保留为智能层派生/预测表，避免替代主 CRUD |
| `shortage_handling_plans` | 3 | 保留 | `shortage_alerts_enhanced` 的处理方案子表 | 跟随智能层保留 |
| `material_demand_forecasts` | 3 | 保留 | 智能缺料预测子表 | 跟随智能层保留 |
| `shortage_alerts` | 主库已删除 | 已归档/废弃 | 第一批未用表清理已外部归档删除；当前主入口已转 `material_shortages`/智能层 | 禁止复活旧表 |
| `mes_shortage_detail` | 8 | 保留 | 装配齐套缺料详情，`assembly_kit/shortage_alerts.py` 查询 `ShortageDetail` | 不与缺料预警表合并 |
| `mat_shortage_alert` | 主库已删除 | 已归档/废弃 | 第一批未用表清理已外部归档删除；调度依赖已改到真实使用表 | 禁止复活旧表 |

结论：缺料域有“主 CRUD、智能派生、装配齐套、旧表残留”四层。不要再泛称 shortage alerts，必须说清具体表。

### 7. 线索需求详情 V1/V2

| 表 | 行数 | 状态 | 证据 | 处置建议 |
|---|---:|---|---|---|
| `lead_requirement_details` | 107 | 保留 | `sales/requirement_details.py`、`sales/requirement_freezes.py`、售前工作台均使用 `LeadRequirementDetail` | 当前主事实源 |
| `lead_requirement_basic_v2` | 主库已删除 | 已归档/废弃 | 第一批未用表清理已删除空 V2 模型和空表 | 后续需求详情继续走 `lead_requirement_details` |
| `lead_requirement_technical_v2` | 主库已删除 | 已归档/废弃 | 同上 | 禁止在旧 V2 空表上补功能 |
| `lead_requirement_facility_v2` | 主库已删除 | 已归档/废弃 | 同上 | 禁止在旧 V2 空表上补功能 |

结论：V2 拆表设计存在，但没有落地使用。继续在 V2 上修功能前，先决定是否真正迁移。

### 8. 审批表双轨

| 表 | 行数 | 状态 | 证据 | 处置建议 |
|---|---:|---|---|---|
| `approval_templates` | 10 | 保留 | 统一审批模板主表；各业务域模板归一入口 | 作为审批模板唯一主表 |
| `approval_instances` | 12 | 保留 | 统一审批实例主表 | 作为审批实例唯一主表 |
| `approval_tasks` | 19 | 保留 | 统一审批待办任务主表 | 作为审批任务唯一主表 |
| `approval_action_logs` | 39 | 保留 | 统一审批动作日志主表 | 作为审批动作历史唯一主表 |
| `approval_history` | 主库已删除 | 已归档/废弃 | 旧审批表归档删除已处理 | 不再作为业务读写源 |
| `approval_records` | 主库已删除 | 已归档/废弃 | 旧审批表归档删除已处理，`projects.approval_record_id` 已改指统一实例 | 不再作为业务读写源 |
| `approval_workflows` | 主库已删除 | 已归档/废弃 | 销售/任务侧旧审批工作流配置表已归档删除；`/sales/approval-workflows` 已移除 | 新配置走 `approval_templates` |
| `approval_workflow_steps` | 主库已删除 | 已归档/废弃 | 旧 workflow 子表已归档删除；销售提醒已改查统一 `approval_tasks` | 不再作为业务读写源 |
| `quote_approvals` | 主库已删除 | 已归档/废弃 | 销售侧报价审批历史已归档删除；报价审批适配器已停止回写旧表 | 不再作为业务读写源 |
| `invoice_approvals` | 主库已删除 | 已归档/废弃 | 销售侧发票审批历史已归档删除；发票审批适配器已停止回写旧表 | 不再作为业务读写源 |
| `contract_approvals` | 主库已删除 | 已归档/废弃 | 销售侧合同审批历史已归档删除；合同审批适配器已停止回写旧表 | 不再作为业务读写源 |
| `quote_cost_approvals` | 主库已删除 | 已归档/废弃 | 报价成本审批历史已归档删除 | 不再作为业务读写源 |
| `quotation_approvals` | 主库已删除 | 已归档/废弃 | 售前 AI 报价审批历史已归档删除 | 不再作为业务读写源 |
| `role_assignment_approvals` | 主库已删除 | 已归档/废弃 | 角色分配旧审批表已归档删除 | 不再作为业务读写源 |
| `task_approval_workflows` | 主库已删除 | 已归档/废弃 | 任务侧旧审批流程表已归档删除 | 不再作为业务读写源 |

结论：审批双轨已经从“待合并”推进到“统一引擎为主、旧表只读归档”。下一步不是继续往旧表补逻辑，而是在备份窗口内执行归档脚本并删除旧审批表。

ECN 更新：`ecn_approvals` / `ecn_approval_matrix` 已在第十二批处理中退役。ECN 审批、提醒、调度、看板统计和干系人识别均改读统一审批实例/任务；旧表只保留在外部归档库。

### 9. 权限/数据范围残留

| 表 | 行数 | 状态 | 证据 | 处置建议 |
|---|---:|---|---|---|
| `role_data_scopes` | 0 | 已归档/废弃 | PERM-16 已确认自定义数据范围层“死在实践中”；第八批已改由 `roles.data_scope` 承接 | 主库已删除，禁止继续作为业务读写源 |
| `data_scope_rules` | 0 | 已归档/废弃 | 旧资源级自定义规则表为空；第八批已从 ORM metadata 拆除 | 主库已删除；如未来要做自定义范围，应重建产品设计和管理入口 |
| `department_default_roles` | 主库已删除 | 已归档/废弃 | 第一批未用表清理已删除旧角色种子残留 | 不再作为业务读写源 |
| `department_role_admins` | 主库已删除 | 已归档/废弃 | 第一批未用表清理已删除旧角色种子残留 | 不再作为业务读写源 |
| `role_template_permissions` | 主库已删除 | 已归档/废弃 | 第一批未用表清理已删除旧角色种子残留 | 不再作为业务读写源 |
| `role_assignment_approvals` | 主库已删除 | 已归档/废弃 | 旧审批表归档删除已处理 | 见“审批表双轨” |
| `role_audits` | 主库已删除 | 已归档/废弃 | 第一批未用表清理已外部归档删除；当前权限审计主链为 `permission_audits` | 不再作为业务读写源 |
| `permissions` | 323 | 已合并/废弃 | 6 个实际角色绑定已迁入 `api_permissions`/`role_api_permissions`；317 个未绑定旧权限定义只归档 | 主库已删除，禁止继续作为业务读写源 |
| `role_permissions` | 6 | 已合并/废弃 | 已全部迁到 `role_api_permissions`，并 bump 权限缓存版本 | 主库已删除 |

结论：旧权限双轨已收口。后续权限能力只补 `api_permissions` / `role_api_permissions` 主链。

### 10. 其他生成残留候选

| 表 | 行数 | 状态 | 证据 | 处置建议 |
|---|---:|---|---|---|
| `currency_rates` | 主库已删除 | 已归档/废弃 | 第一批未用表清理已外部归档删除 | 多币种真实能力另走当前多币种模块，不复活旧残留 |
| `currency_history` | 主库已删除 | 已归档/废弃 | 第一批未用表清理已外部归档删除 | 同上 |
| `equity_structures` | 主库已删除 | 已归档/废弃 | 融资/股权 demo 残留已外部归档删除 | 不再留在 PMS 主库 |
| `funding_records` | 主库已删除 | 已归档/废弃 | 融资/股权 demo 残留已外部归档删除 | 不再留在 PMS 主库 |
| `funding_rounds` | 主库已删除 | 已归档/废弃 | 融资/股权 demo 残留已外部归档删除 | 不再留在 PMS 主库 |
| `funding_usages` | 主库已删除 | 已归档/废弃 | 融资/股权 demo 残留已外部归档删除 | 不再留在 PMS 主库 |
| `investors` | 主库已删除 | 已归档/废弃 | 融资/股权 demo 残留已外部归档删除 | 不再留在 PMS 主库 |

结论：这些不是重复表，但像“平台模板/融资 demo”混进了 PMS 主库。建议后续按业务域整体剥离。

## 优先级建议

| 优先级 | 动作 | 原因 |
|---|---|---|
| 已完成 | `tasks_deprecated/task_id_map` 外部归档并移出主库 | 主任务链已统一到 `task_unified` |
| 已完成 | `sales_targets_v2` / `target_breakdown_logs` 合并退役 | 销售目标主事实源已收口到 `sales_targets` |
| 已完成 | `permissions/role_permissions` 合并退役 | 已绑定旧权限迁入新权限链，未绑定旧种子外部归档 |
| 已完成 | 空 `solution_versions` 和未接入绑定原型链退役 | 主库删除空表，拆除模型 FK，保留可空兼容列 |
| 已完成 | 空 `role_data_scopes` / `data_scope_rules` 退役 | 数据范围真实口径收口到 `roles.data_scope` |
| 已完成 | `after_sales_support_tickets` 并入中心 `service_tickets` | 售后技术支持工单不再双轨，依附表 `ticket_id` 改指中心工单 |
| 已完成 | `change_approval_records` / `timesheet_approval_log` 审批旧表退役 | 项目变更审批动作已迁统一日志；工时旧日志无实体锚点，仅外部归档 |
| 已完成 | ECN 审批迁统一审批引擎 | `ecn_approvals` / `ecn_approval_matrix` 已归档删除，运行链路改读 `approval_instances` / `approval_tasks` |
| 已完成 | 定 `quotes` vs `presale_ai_quotation` 合并路线 | 正式报价唯一事实源已明确；AI 报价保留为草稿源并新增采纳转正式报价入口 |
| 已完成 | 清理空的 `lead_requirement_*_v2` | 空 V2 模型和空表已删除，主链保留 `lead_requirement_details` |
| 已完成 | 给 `resource_conflict` 改名 | 已改为 `production_resource_conflicts`，避免和项目资源冲突表混淆 |
| 已完成 | 清理 `shortage_alerts`、`mat_shortage_alert` 旧残留 | 两张旧缺料残留表已外部归档删除，主链保留 `material_shortages` 和智能层 |

## 下一步执行门槛

1. 先给每个“合并/废弃候选”表指定 owner 和主事实源。
2. 对废弃候选跑三件事：`rg` 引用扫描、OpenAPI 路由扫描、真实 DB 外键/视图/触发器扫描。
3. 对有数据的表先导出归档 SQL/CSV，再迁移或删除。
4. 删除前必须有迁移脚本、回滚脚本和最小回归测试。
5. 每次只清一个业务域，不要 600 张表一起动。

## 本轮只读检查命令

```bash
sqlite3 data/app.db "select count(*) from sqlite_master where type='table' and name not like 'sqlite_%';"
sqlite3 data/app.db "select name from sqlite_master where type='table' and name not like 'sqlite_%' order by name;"
sqlite3 data/app.db "pragma table_info(<table_name>);"
rg -n "<table_name>|<ModelName>" app frontend tests migrations docs -S
```
