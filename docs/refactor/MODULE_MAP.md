# 模块化重构·归域清单（MODULE_MAP）

> 生成日期：2026-07-06。方法：16 个并行扫描任务覆盖 app/services（866 文件）、app/api/v1/endpoints（894 文件）、app/models（256 文件）及平台层（core/common/middleware/plugins/utils，165 文件），逐条目读代码定域（非按文件名猜测）、grep 核实引用与路由挂载。
> 逐文件明细见 `docs/refactor/module-map/` 下 16 份分片报告（svc-*/ep-*/models-*/platform）。

## 0. 总体结论

- 后端约 53 万行，按技术分层平铺（services/endpoints/models 三大目录），业务域之间无边界。
- **死代码约 2 万行**（保守估计，含整包级死链、未挂载路由、被同名包遮蔽的模块、纯 re-export shim），应在迁移前先删。
- **路由基准**：`app/main.py` 只加载 `app/api/v1/api.py`（main.py:11,103，auth 在 main.py:91-96 先行注册）。`api_lazy.py`/`api_medium.py`/`api_minimal.py`/`api_minimal_backup.py` 四个变体全部无引用，是死代码。endpoint 死活判断以"是否被 api.py 路由链挂载"为准。
- **插件骨架未接线**：`app/plugins/`（core.py 476 行 + hooks.py 488 行）框架完整但全仓零 import，installed/ 无任何插件。可作为未来"模块注册/按租户开通"机制的起点，或删除重建。
- **多租户缺口**：约 60 张表缺 `tenant_id`（其中约 11 张属死代码）。`models/base.py` 无 TenantMixin，tenant_id 逐表手写——这是缺口的根因。
- **若干生效路由返回假数据/空壳**（见 §6 生产隐患），与功能审计"末梢假"的结论互相印证。

## 1. 目标域划分（21 个域）

**平台层（6）**：platform-auth（租户/用户/权限/数据权限/会话/2FA/组织）、platform-approval（审批引擎）、platform-notify（通知/告警）、platform-file（文件/导入导出/Excel/PDF/docx）、platform-ai（AI 网关/jobs/feedback）、platform-infra（缓存/备份/调度器/监控/状态机引擎/通用 CRUD 基类）。

**业务域（15）**：presale（售前评估/AI 报价/方案/技术评估/需求提取）、sales（客户/合同/订单/回款/开票/目标/漏斗）、project（项目主干/阶段/里程碑/进度/风险/任务中心/OTD）、engineering（技术评审/技术规格/研发项目/工程师技术绩效）、ecn（工程变更/变更影响）、bom-material（BOM/物料主数据）、procurement（采购/外协/供应商）、inventory-kitting（库存/齐套/缺料/仓库）、production（车间/工单/报工/安装派工/现场/设备/质量）、acceptance（验收/交付）、aftersales（售后/服务工单/ITR/SLA）、cost-finance（成本/预算/EVM/毛利/结算/标准成本）、performance-hr（绩效/奖金/工时/排班/人员匹配/HR/文化墙）、analytics（看板/报表中心/report_framework/经营统计）、strategy-pmo（战略/PMO/经营节奏/最佳实践/知识库/踩坑库）。

**待定项**：admin_compat.py + models/admin_office.py（行政办公，价值链外，建议独立小域 `admin-office` 或并入 performance-hr）；`ai_more.py`/`ai_planning.py`（endpoints，单文件横跨多域的 AI 收尾批，重构时按功能点拆回各业务域）；`business_rules.py`（跨域规则库，若保留应下沉 platform）；`company_certifications`（资质证书，倾向 sales 投标用）。

## 2. 各域主要资产速览

| 域 | 主要代码位置（示例，非穷举） | 备注 |
|---|---|---|
| presale | services/presale/(23 文件 9020 行) + 售前 AI 全家桶 + api/v1/presale_ai_*.py + endpoints/presale*(20+7 文件) + models/presale_*(20+ 文件)；**另有大量报价/需求/评估代码错放在 endpoints/sales/**（见 §5） | 行业卖点域，AI 集成最重 |
| sales | services/sales/(46 文件 11297 行) + endpoints/sales/(128 文件，约半数应迁出) + models/sales/(20 文件 4473 行) | 最大熔炉，Customer 模型错放在 models/project |
| project | endpoints/projects/(114 文件，约 1/4 应迁出) + services/project*/stage*/progress*/otd/ + models/project/ 等 | 主干域；gate_checks 与 otd 是跨域枢纽 |
| cost-finance | services/cost/(14 文件 5725 行) + evm/budget/profit/hourly_rate + endpoints/projects/costs/(2739 行应迁入) + cost_endpoints/ + standard_costs/ | 大量代码顶着 project/sales 前缀 |
| performance-hr | services/bonus/(2489)+timesheet/(6257)+performance*/engineer_performance/staff_matching + endpoints/performance/(3171)/bonus/(2089)/timesheet/(2540)/hr_management 等 | 体量第二大的业务域 |
| analytics | services/report_framework/(41 文件 6031 行)+dashboard/(5878)+report* + endpoints/report_center/(2198)/analytics/dashboard* | 报表三套入口并存需收敛（§4） |
| ecn | services/ecn/(28 文件 5439 行) + endpoints/ecn/(21 文件 4852 行) + models/ecn/(10 文件) + 错放的 projects/change_requests 等 | 相对完整，另有仅 tests 引用的平行三件套（死代码） |
| production | endpoints/production/(32 文件 6576 行) + services/production/(4131)+排程/质量 + models/production/(21 文件 2550 行) | 质量风险 AI 子功能整体未接线 |
| inventory-kitting | services/shortage*/inventory/kit_rate/assembly_kit* + endpoints/shortage/(3202)/assembly_kit/(2317)/kit_check/kit_rate/warehouse/inventory | warehouse 9 张表全缺 tenant_id |
| procurement | endpoints/purchase/(1977)/outsourcing/(2543)/material_demands + services/purchase*/outsourcing_workflow/procurement_analysis + models/purchase/outsourcing/vendor | procurement/ 与 purchase/ 两包并存 |
| acceptance | endpoints/acceptance/(21 文件 3286 行) + services/acceptance* + models/acceptance.py | 与 bonus/invoice 有触发耦合 |
| aftersales | endpoints/service/(22 文件 3767 行)/after_sales.py(1294)/sla/itr + services/service//sla/itr + models/service/ | |
| engineering | endpoints/technical_review/technical_spec/rd_project + services/spec_match/debug_issue_sync/design_review_sync + models/engineer_performance/(902)/technical_*/rd_project | |
| strategy-pmo | services/strategy/(25 文件 5584 行)/pmo_*/knowledge/pitfall/meeting_report* + endpoints/strategy/pmo/management_rhythm/(2793)/lessons_learned + models/strategy/pmo/management_rhythm | pmo_initiation 依赖 presale+sales+project |
| bom-material | endpoints/bom/(1767)/materials + services/bom*/material* + models/material.py(被 90 处引用) | models/bom/ 里实为成本表（错放） |
| platform-* | approval_engine/(40 文件 10236 行)、notification/(19 文件)、alert/(18 文件 4257 行)、permission_management、data_scope、cache、unified_import、core/common/middleware/utils | utils/scheduled_tasks/(24 文件 5526 行)按业务域拆分 |

## 3. 死代码清单（迁移前先删）

> **进度（2026-07-06）**：§3.1+§3.3+§3.4 已由批1完成（commit 9c110a979，-1.0万行）；§3.2 已由批2完成（commit 11dbb1494，-3.4万行）。两批合计 288 文件、约 -4.4 万行，路由表 2985 条与清理前完全一致。
> 例外与修正：`company_profile.py`/`competitor.py` **不是死代码**（表被售前AI裸SQL使用），已按 DB schema 重建保留；`document_file_lifecycle.py` 豁免（与 scan_project_document_orphans.py 是活的运维工具对）；`plugins/` 暂留（候选改造为模块注册机制）；`exports/` 兼容层暂留（迁移时随域清理）；`sales/event_listeners.py` 暂留待业务确认（疑似该接线的功能而非该删的代码）。

### 3.1 路由与平台层
- `app/api/v1/api_lazy.py`、`api_medium.py`、`api_minimal.py`、`api_minimal_backup.py` — 四个路由聚合变体，零引用
- `app/api/v1/ai_planning.py`（根级 486 行）— 被 endpoints/ai_planning.py 取代
- `app/api/response_helpers.py`（237 行）、`app/core/scoring_config.py`（225 行）— 零引用
- `app/plugins/` 整包（约 1000 行）— 未接线（或保留改造为模块注册机制）
- `app/utils/scheduled_tasks_new.py`、`app/middleware/rate_limit_middleware.py`、`app/core/config.py.secure`、`app/core/decorators/`（空壳）
- `app/api/v1/endpoints/base_crud_router.py`（async 版 224 行）— 活的是 _sync 版

### 3.2 services 层（仅 tests/scripts 引用、生产链路无人调用）
- 资源调度死链：`resource_scheduling/`（722）+ `resource_scheduling_ai_service.py`（848）
- 质量风险死簇：`quality_risk_management/`（617）+ `quality_risk_ai/`（655）
- ECN 平行三件套：`change_impact_ai_service.py`（653）、`change_impact_analysis_service.py`（256）、`change_response_suggestion_service.py`（223）— 生产走 project_change_impact_service
- `win_rate_prediction_service/`（1320，端点用本地 utils 未用本包）、`resource_waste_analysis/`（806）、`work_log_ai/`（583）、`ppt_generator/`（613）、`business_rules.py`（664）、`purchase_suggestion_engine.py`（589）、`purchase_intelligence/`（638）、`schedule_optimization_service.py`（564）、`project_relations_service.py`（555，与单数版并存）、`inventory_analysis_service.py`（510）、`requirement_extraction_service.py`（469）、`itr_analytics_service.py`（423）、`database/query_optimizer.py`（474）、`material_transfer_service.py`（532）、`pdf_content_builders.py`（369）、`stage_approval_bridge.py`（352）、`performance_stats_service.py`（258）、`margin_permission_service.py`（254）、`ai_service.py`（226，被 ai_client_service 取代）、`template_report_data_service.py`（232）、`job_duty_task_service.py`（193）、`milestone_service.py`（62）、`document_file_lifecycle.py`（79）、`timesheet/records/` 子包（460，仅被死的 api_medium 引用）
- 纯转发 shim 尸体（无人走旧路径）：`cost_collection/forecast/prediction_service.py`（8/14/16 行）、`presale_ai_service.py`（11）、`dashboard_adapter.py`（16）、`ecn_auto_assign_service.py`（20）、`ecn_scheduler.py`（31）、`shortage_report_service.py`（15）

### 3.3 endpoints 层（未挂载/被遮蔽/501 禁用）
- projects/ 包内：`ext_risks.py`（366）、`cost_benchmark.py`（215）、`status.py`（16，被 status/ 包遮蔽）
- sales/ 包内：`leads.py`（遮蔽壳）、`targets_standalone.py`、`teams_standalone.py`、`regions.py`、`recommendations.py`、`quote_comparison.py`、`quick_cost_recommendation.py`、`margin_alerts.py`（21KB）
- 顶层：`costs.py`（448）、`dashboard/layout.py`（172）、`change_impact.py`（34，501 shim）、`ecn_bom.py`（21，空 router）、`knowledge/`（480，501 禁用包）、`material/`（1367，仅死掉的 api_lazy 引用）、`ai_strategy.py`（23）、`best_practice.py`（170）、`resource_overview.py`/`resource_scheduling.py`（501 shim）、`sales_regions/targets/teams.py`（api.py 中已注释）

### 3.4 models 层
- `models/presale.py`（顶层 494 行 9 张表）— 被同名 presale/ 包遮蔽，永不可达
- `company_profile.py`、`competitor.py`、`pipeline_analysis.py`、`employee_encrypted_example.py` — 零引用
- `project/labor_cost_detail.py`（191，未导出未引用，且属 cost-finance）
- `sales/event_listeners.py`（342）— register 函数全仓无调用，事件从未生效（**注意：这可能是个未接线的功能缺陷而非该删的代码，需业务确认**）
- `exports/` 兼容再导出层（1454 行）— 逐步清理

## 4. 重复/并存实现（迁移时二选一收敛）

| 主题 | 并存双方 | 活体判断 |
|---|---|---|
| 工时报表 | services/report_service.py vs services/report/report_service.py | 双活（消费者不同），合并 |
| 报表入口 | /report + /reports + /report-center 三套 | 收敛到 report_center（report_framework 引擎） |
| 报表模型 | models/report.py vs models/report_center.py | **两者都声明 `report_template` 表名，冲突**，需改名合并 |
| 角色管理 | role_service.py vs role_management/ | 双活同被 roles.py 引用，合并 |
| 销售预测 | sales_forecast_service.py vs sales_prediction_service.py | 双活，功能重叠 |
| 协作评价 | collaboration_service.py vs collaboration_rating/ | 建议保留子包版 |
| 限流 | core/rate_limit.py(壳)/core/rate_limiting.py(活)/core/middleware/rate_limiting.py(活)/middleware/rate_limit_middleware.py(死) | 四处并存收敛为一 |
| 分页/树 | utils/pagination.py vs common/pagination.py；utils/tree.py vs common/tree_builder.py | 收敛到 common |
| 审批引擎 | approval_engine/workflow_engine.py（DEPRECATED）vs approval_engine/engine/ | 删旧 |
| 合同增强 | contracts/enhanced*.py vs basic.py；invoices/legacy.py | 需清尾 |
| 物料端点 | materials/(活)/material/(死)/material_demands/(活) | 三包收敛为二 |
| 齐套服务 | assembly_kit_service.py vs _enhanced.py | 双活（继承关系），可合并 |
| 兼容 shim 群 | services 旧路径转发（notification/permission 系列，被大量 tests 引用）；endpoints 顶层转发（performance_contract/pm_involvement/project_contributions/project_workspace/quote_actual_compare/cost_collection/cost_variance_analysis/dashboard_stats/dashboard_unified/labor_cost_detail 等） | 迁移时随域折叠，同步改 tests |

## 5. 放错位置（迁移映射）

**endpoints/sales/ →**（128 文件约半数迁出）
- → presale：报价簇 11 文件（quotes/quote_*/intelligent_quote）+ 需求簇 4 文件（requirements/requirement_*/ai_clarifications）+ 技术评估簇 6 文件（assessments/+assessment_templates）+ expenses.py + templates/（CPQ/报价模板）
- → cost-finance：quote_costs/cost_management/cost_matching/cost_reminder/cost_templates/purchase_material_costs
- → analytics：statistics 五件套、loss/delay/cross_analysis、information_gap、health、accountability、conversion_analysis
- → performance-hr（可议）：performance.py、team/pk.py、team/ranking.py

**endpoints/projects/ →**
- → cost-finance：costs/(14 文件 2739 行)、financial_costs.py、payment_plans.py(可议)
- → ecn：change_requests.py、change_impact.py、costs/ecn_cost_summary.py
- → performance-hr：timesheet/、work_logs/、workload/、contributions.py、resource_plan/(可议)
- → strategy-pmo：ext_best_practices.py、ext_lessons.py、ext_reviews.py(可议)
- → bom-material/inventory：material_progress.py

**平台层混入业务 →**
- core/：sales_permissions.py→sales、production_config.py→production、permissions/timesheet.py→performance-hr；state_machine/ 各业务状态机（acceptance/ecn/installation_dispatch/issue/milestone/opportunity/quote）随业务域走，引擎（base/decorators/exceptions）留 platform
- common/：crud/sales_query_builder.py→sales
- utils/：risk_calculator/project_utils/exports/→project、spec_matcher/spec_match_service/spec_extractor/→presale；scheduled_tasks/(24 文件 5526 行)与 scheduler_config/(14 文件)按业务域拆，调度框架留 platform

**models →**
- **Customer 模型在 models/project 包内**（sales 16 处依赖）——拆分 sales/project 前必须先归位 sales
- organization.py（609 行）：组织架构(platform-auth)与 HR 薪资/合同/事务(performance-hr)混装，需拆
- models/bom/cost_breakdown.py→cost-finance；project_margin_snapshot.py、standard_cost.py→cost-finance；business_support/acceptance.py→acceptance
- services/otd/margin_export_service.py→cost-finance；project_change_impact_service.py→ecn；project_cost_aggregation/project_cost_prediction/profit_analysis→cost-finance

## 6. 生产隐患（生效路由返回假数据/空壳）

- `stage_templates.py`：挂 /stage-templates，所有 try 导入失败，**返回硬编码假模板数据**
- `schedule_optimization.py`：挂 /schedule-optimization，只返回占位/空结果
- `quality_risk.py`：挂 /quality-risk，4 级 fallback 目标全不存在，只返回 placeholder——质量风险 AI 功能整体未生效（对应 services 死簇）
- `competitor_analysis.py`：578 行硬编码演示数据，整模块 501 下架但仍挂在 /competitor
- `timesheet_reminders.py`：把整个 timesheet 包 router 重复挂到 /timesheet-reminders，名不符实
- `timesheet/analytics.py`：因 Pydantic 递归错误被注释禁用
- `win_rate_prediction.py`（704 行）：无 service 层全内联，疑似含 mock，需核查数据真实性
- `invoice_service.py`：stub 实现（仅生成发票编码）
- 悬空 import：`report_center/generate/comparison.py:31` 引用不存在的 `app.services.report_data_generation_service`
- `sales/event_listeners.py`：合同/报价/发票→商机联动监听器定义完整但从未注册（疑似功能缺陷）

## 7. 跨域耦合枢纽（决定拆分顺序，最后动）

1. `endpoints/projects/gate_checks/`（S1→S9 阶段门，直接 import sales/technical_review/bom/outsourcing/acceptance/issue 六域）
2. `services/otd/`（横跨近 10 个域的交期编排）
3. `services/report_framework/` adapters + `services/dashboard/` adapters（报表/看板聚合全域）
4. `services/pmo_initiation/`（presale+sales+project）、`project_workspace_service.py`（1703 行跨域聚合）
5. `services/performance_collector/`（从 5 个域采集绩效数据）、`services/unified_import/`（分派 4 个域的 importer）
6. 平台层反向依赖业务：users/ 端点 import project/rd_project/timesheet 模型

处理原则：这些"天然跨域"的编排/聚合代码不强行塞进单一业务域，而是作为依赖各域公共接口的**组合层（composition layer）**，等各域接口稳定后最后迁。

## 8. 多租户 tenant_id 缺口（约 60 张表）

**活代码中的缺口（优先补）**：
- warehouse.py 9 张（warehouses/库位/出入库/盘点/inventory）
- resource_scheduling.py 5 张、advantage_product.py 5 张、project_team.py 3 张、project_template_config.py 3 张、timesheet_reminder.py 3 张、ai_planning/ 3 张
- project_requirements 2、project_schedule 2、knowledge_base 2、bom/cost_breakdown 2、presale_proposal 2
- project_risks、report_template（report.py 内）、user_dashboard_layouts、audit_pack_requests、company_certifications、presale_agent_metrics、presale_agent_revisions、presale_usage_feedback 各 1
- holiday.py（holidays，疑为有意全局共享，需确认）

**死代码中的缺口（随删除消失）**：models/presale.py 9 张、labor_cost_detail 2 张、company_profile/competitor/employee_encrypted_example 各 1。

**根因修复**：models/base.py 增加 TenantMixin（tenant_id + 索引 + 默认过滤），新表强制继承；存量表出 alembic 迁移补列。

## 9. 重构路线建议

1. **P0 清障（1-2 周）**：删 §3 死代码约 2 万行（每删一批跑分批测试）；修 §6 生产隐患（假数据端点要么接通要么下架）；补 §8 活代码 tenant_id。
2. **P1 立规（并行）**：建 `app/modules/` 目录 + manifest 约定；上 import-linter 锁跨域 import（先对已清晰的域生效）；建 `tenant_modules` 表 + 路由/菜单闸门。
3. **P2 首模块试点：presale**（相对独立、AI 集成新、行业卖点）：把散在 endpoints/sales/ 的报价/需求/评估簇、utils/ 的 spec_*、api/v1 根的 presale_ai_* 全部归拢进 modules/presale/，按模块跑测试，闭环该域审计项后升级 L2 试点。
4. **P3 逐域滚动**：cost-finance（从 projects/costs 和 sales/cost_* 归拢）→ performance-hr → analytics（收敛三套报表）→ 其余域；Customer 模型归位 sales 在拆 sales/project 前完成。
5. **最后**：§7 组合层（gate_checks/otd/报表 adapters/工作台聚合）改造为依赖各模块公共接口。

模块成熟度门槛（上线闸门）：L0 原型 → L1 内测（自有租户）→ L2 试点（指定租户，前提：该域审计项清零 + import-linter 无违规 + 模块测试全绿）→ L3 GA。
