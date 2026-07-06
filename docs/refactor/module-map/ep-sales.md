I have all data needed. Here is the final report.

---

范围：`app/api/v1/endpoints/sales/`（128 个 .py 文件，含 8 个子包）。活跃路由聚合链：`app/main.py` → `app/api/v1/api.py`（第 119 行挂载 `sales/__init__.py` 聚合 router，另第 300 行单独挂载 `activity_minutes`）。以下"是否注册"均以此为准。

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|---|---|---|---|---|---|---|
| customers.py, contacts.py, customer_tags.py | sales | 3 | 1142 | models.project.customer（Customer 模型放在 project 包） | 无 | 客户档案/联系人/客户标签 CRUD，sales 核心 |
| leads/（actions,batch,crud,follow_ups,__init__） | sales | 5 | 1329 | services.lead_priority_scoring | 无 | 线索 CRUD/批量/跟进，已模块化的活跃实现 |
| leads.py | sales | 1 | 11 | — | 疑似(compat shim，仅 re-export .leads，且被同名包目录遮蔽，__init__ 导入的是包) | 向后兼容空壳，死文件 |
| priority.py | sales | 1 | ~200 | — | 无 | 线索优先级排序（注册于 leads 之前） |
| requirements.py, requirement_details.py, requirement_freezes.py, ai_clarifications.py | presale（候选迁出） | 4 | 666 | — | 无 | 需求详情/需求冻结/AI 澄清；requirements.py 聚合其余三者。属"需求提取"，建议迁 presale |
| opportunities.py, opportunity_crud.py, opportunity_workflow.py, opportunity_analytics.py | sales | 4 | ~2500 | models.project, services.presale.cpq_pricing_service, status_transition_service | 无 | 商机聚合器+CRUD+工作流(阶段门/评分/赢输,64KB巨файл)+分析导出。workflow/analytics 经 opportunities.py 二级挂载 |
| opportunity_batch.py, opportunity_health.py | sales | 2 | ~700 | — | 无 | 商机批量操作、健康度评估 |
| activity_minutes.py | sales | 1 | ~600 | services.ai_client_service | 无 | 会议纪要上传→AI解读→关联商机(经 api.py:300 单独挂载，非经 __init__) |
| quotes.py, quote_quotes_crud.py, quote_items.py, quote_versions.py, quote_status.py, quote_approval.py, quote_per_id_approval.py, quote_templates.py, quote_exports.py, quote_delivery.py, intelligent_quote.py | presale（候选迁出） | 11 | ~4200 | services.presale.cpq_pricing_service, services.quote_approval, excel/pdf 导出 | 无 | 报价全生命周期(CRUD/明细/版本/状态/审批/模板/导出/交付/AI智能报价)。报价属售前活动，整簇建议迁 presale |
| quote_comparison.py | presale（候选迁出） | 1 | ~300 | — | 疑似(未注册，0 引用) | 报价对比分析，未挂载死文件 |
| quote_costs.py, cost_management.py, cost_matching.py, cost_reminder.py, cost_templates.py, purchase_material_costs.py | cost-finance（候选迁出） | 6 | ~3000 | services.cost.labor_cost_service, models.material | 无 | 报价成本/物料成本匹配/成本模板/采购物料成本。cost_management 聚合后 4 者，均活跃。属成本域 |
| quick_cost_recommendation.py | cost-finance（候选迁出） | 1 | ~330 | — | 疑似(未注册，0 引用) | 一键成本推荐，未挂载死文件 |
| margin_alerts.py | cost-finance（候选迁出） | 1 | ~530 | — | 疑似(未注册，0 引用，21KB) | 毛利率预警(配置/检查/审批)，未挂载死文件 |
| cost_overrun.py | analytics/cost-finance | 1 | ~70 | services.cost.cost_overrun_analysis_service | 无 | 成本过高分析，注册中 |
| contracts/（approval,attachment_security,basic,contracts,deliverables,enhanced,enhanced_*,export,payment_plans,sign_project,__init__） | sales | 13 | 2880 | endpoints.approval_submit_guard, services.contract_approval, models.project | 疑似(enhanced.py / enhanced_attachments/status/terms.py 与 basic.py 并存，且 attachment_security.py、contracts.py 未在 __init__ 聚合中 include) | 合同管理。__init__ 只 include approval/basic/deliverables/enhanced/export/payment_plans/sign_project；contracts.py 由外层 __init__ 单独挂载(contracts_contracts) |
| contract_milestones.py | sales | 1 | ~180 | — | 无 | 合同里程碑提醒(挂 /contracts 前缀) |
| invoices/（basic,export,legacy,operations,workflow,__init__） | sales | 6 | 1577 | services.approval_engine | 疑似(legacy.py 兼容旧版路由与 basic/operations 并存) | 发票管理，legacy 为旧版兼容层 |
| payments/（payment_exports,payment_plans,payment_records,payment_statistics,__init__） | sales | 5 | 1519 | services.payment_adjustment_service, payment_statistics_service | 无 | 回款/收款计划/回款统计/导出 |
| receivables.py, collection_priority.py, disputes.py | sales | 3 | ~530 | — | 无 | 应收账款/催款优先级/回款争议 |
| targets.py | sales | 1 | ~450 | — | 无 | 销售目标管理(活跃) |
| targets_standalone.py | sales | 1 | ~250 | schemas.sales_target | 疑似(未注册，0 引用，与 targets.py 重复) | 独立版销售目标端点，死文件 |
| team/（crud,members,org,pk,ranking,statistics,teams_ranking,utils,__init__） | sales / performance-hr | 9 | 2192 | models.organization | 无 | 销售团队/成员/组织/PK/排名/统计。ranking/pk 偏业绩激励，可考虑 performance-hr |
| teams_standalone.py | sales | 1 | ~180 | schemas.sales_team | 疑似(未注册，0 引用，与 team/ 包重复) | 独立版团队端点，死文件 |
| organization.py | sales | 1 | ~730 | models.organization | 无 | 销售组织架构 4 层层级(挂 /organization) |
| performance.py, collaboration.py, mobile.py | sales / performance-hr | 3 | ~1300 | — | 无 | 销售绩效激励(排行/提成/PK)、销售协同、移动端支持。performance 偏 performance-hr |
| accountability.py | analytics（候选迁出） | 1 | ~80 | services.pipeline_accountability_service | 无 | 深度归责分析，属经营分析 |
| assessments/（assessments,failure_cases,open_items,scoring_rules,__init__）, assessment_templates.py | presale（候选迁出） | 6 | 2830 | services.ai_assessment_service, services.presale.assessment_status, technical_assessment_service | 无 | 技术评估/失败案例/评估项/评分规则/评估模板。属"技术评估/售前知识案例"，建议迁 presale |
| dashboard.py | analytics | 1 | ~350 | — | 无 | 销售仪表盘(个人业绩/团队排名/管道/预测) |
| statistics.py, statistics_core.py, statistics_prediction.py, statistics_quotes.py, statistics_reports.py | analytics（候选迁出） | 5 | ~2200 | excel_export_service | 无 | 销售统计(漏斗/阶段/预测/报价统计/报表)。statistics.py 聚合后 4 者。跨域统计属 analytics |
| sales_funnel.py, funnel.py, conversion_analysis.py | analytics / sales | 3 | ~1400 | services.pipeline_health_service | 无 | 漏斗管理(pipeline/optimization/overview 三 router)、漏斗状态机、全链路转化率分析 |
| sales_forecast.py | analytics / sales | 1 | ~150 | services.SalesForecastService | 无 | 销售预测(forecast + forecast_enhanced 两 router) |
| loss_analysis.py, delay_analysis.py, cross_analysis.py, information_gap.py, health.py | analytics（候选迁出） | 5 | ~750 | services.loss_deep_analysis_service, delay_root_cause_service, information_gap_analysis_service, pipeline_break_analysis_service | 无 | 未中标/延期/交叉/信息缺口/全链条健康度分析，属经营分析域 |
| recommendations.py | sales / analytics | 1 | ~150 | — | 疑似(未注册，0 引用；同名 recommendation_service 属别处) | 销售智能推荐 API，未挂载死文件 |
| automation.py | sales | 1 | ~430 | — | 无 | 销售自动化(自动跟进/邮件序列/任务/报告) |
| follow_up_reminders.py | sales | 1 | ~180 | — | 无 | 智能跟进提醒(挂 /follow-up) |
| expenses.py | presale/cost-finance（候选迁出） | 1 | ~270 | models.presale_expense, models.presale | 无 | 售前费用管理，明确依赖 presale 模型，建议迁 presale |
| operation_logs.py | platform-infra / sales | 1 | ~100 | — | 无 | 销售业务操作日志查询 |
| data_audit.py | sales | 1 | ~450 | models.sales.data_audit, services.sales.data_audit_service | 无 | 销售数据变更审核(提交/审批数据变更) |
| regions.py | sales | 1 | ~90 | schemas.sales_team | 疑似(未注册，0 引用；api.py:1206 已注释禁用 sales_regions) | 销售区域管理端点，死文件 |
| templates/（common,contract_templates,cpq_rules,quote_templates,__init__） | presale/sales | 5 | 1525 | services.presale.cpq_pricing_service | 疑似(quote_templates.py 与顶层 quote_templates.py 功能重叠) | 报价模板/合同模板/CPQ 规则集聚合。CPQ/报价模板偏 presale |
| utils/（code_generation,common,gate_validation,quote_item_validation,solution_review,stage_guard,__init__） | sales（工具层） | 7 | 1018 | — | 无 | 销售模块公共工具：编码生成/通用函数/阶段门校验/阶段守卫。被多模块复用，非路由 |

## 异常发现

**死文件（未挂载任何活跃路由，0 外部引用）：**
- `leads.py` — compat shim，仅 `from .leads import router` re-export，且被同名 `leads/` 包目录遮蔽（`__init__` 导入的 `leads` 解析为包）。
- `targets_standalone.py` — 与已注册的 `targets.py` 功能重复的独立版目标端点。
- `teams_standalone.py` — 与已注册的 `team/` 包功能重复的独立版团队端点。
- `regions.py` — 销售区域端点，api.py:1204-1207 明确注释"sales_regions 只是 sales router 的兼容 shim，取消挂载，前端未调用"。
- `recommendations.py` — 销售智能推荐 API，未注册。
- `quote_comparison.py` — 报价对比分析，未注册。
- `quick_cost_recommendation.py` — 一键成本推荐，未注册。
- `margin_alerts.py` — 毛利率预警(21KB)，未注册。

**重复/并存实现（compat/legacy/enhanced）：**
- `invoices/legacy.py` — 显式"兼容旧版路由"，与 `basic.py`/`operations.py`/`workflow.py` 并存（legacy 仍被 include，属活跃但为旧版尸体候选）。
- `contracts/enhanced.py` + `enhanced_attachments.py` + `enhanced_status.py` + `enhanced_terms.py` 与 `basic.py`/`deliverables.py` 并存；且 `contracts/attachment_security.py`、`contracts/contracts.py` 未被 `contracts/__init__.py` 聚合（contracts.py 由上层 `__init__` 以 `contracts_contracts` 单独挂载，attachment_security 疑似未挂载）。
- `templates/quote_templates.py` 与顶层 `quote_templates.py` 双份报价模板实现；顶层 `targets.py`/`targets_standalone.py`、`team/`/`teams_standalone.py` 亦为"包版 vs 单文件版"双实现。
- `statistics.py`/`statistics_core|prediction|quotes|reports.py`、`opportunities.py`/`opportunity_crud|workflow|analytics.py`、`cost_management.py`/`cost_matching|reminder|templates|purchase_material_costs.py`、`requirements.py`/`requirement_details|freezes|ai_clarifications.py` 均为"聚合器 + 子模块"二级挂载模式（活跃，非死代码，但增加了排查复杂度）。

**放错域/应迁出 sales 的文件（大熔炉重灾区）：**
- 迁 **presale**：整个报价簇（`quotes.py`、`quote_quotes_crud/items/versions/status/approval/per_id_approval/templates/exports/delivery.py`、`intelligent_quote.py`、`quote_comparison.py`）+ 需求簇（`requirements.py`、`requirement_details/freezes.py`、`ai_clarifications.py`）+ 技术评估簇（`assessments/` 包、`assessment_templates.py`）+ `expenses.py`(依赖 models.presale_expense) + `templates/`(CPQ/报价模板)。代码依赖 `app.services.presale.cpq_pricing_service`/`assessment_status`/`technical_assessment_service` 佐证。
- 迁 **cost-finance**：`quote_costs.py`、`cost_management.py`、`cost_matching.py`、`cost_reminder.py`、`cost_templates.py`、`purchase_material_costs.py`、`quick_cost_recommendation.py`、`margin_alerts.py`。依赖 `app.services.cost.*`。
- 迁 **analytics**：`statistics*.py` 五件套、`accountability.py`、`loss_analysis.py`、`delay_analysis.py`、`cross_analysis.py`、`information_gap.py`、`health.py`、`conversion_analysis.py`（跨域经营分析，依赖 `services.*_analysis_service`）。
- 可考虑迁 **performance-hr**：`performance.py`、`team/pk.py`、`team/ranking.py`、`teams_standalone.py`（业绩排行/提成/PK 属绩效激励）。

**跨域耦合（业务域↔业务域，影响拆分顺序）：**
- sales → **project**：`models.project`(16 次)、尤其 `models.project.customer`（Customer 模型竟位于 project 包，客户主数据与 project 强耦合，拆分前需先把 Customer 模型归位 sales）。
- sales → **presale**：`services.presale.cpq_pricing_service`、`assessment_status`；`models.presale`、`models.presale_expense`。
- sales → **cost-finance**：`services.cost.cost_overrun_analysis_service`、`labor_cost_service`。
- sales → **bom-material**：`models.material`、`models.advantage_product`。
- sales → **platform-approval**：`services.approval_engine`、`contract_approval`、`quote_approval`、`endpoints.approval_submit_guard`（各业务审批桥接，随业务域走）。

**多租户检查**：本范围为 endpoints，不含表定义；涉及的 `models.sales.data_audit` 等表定义在 models 包，未在本范围内，无法判定 tenant_id，留给 models 扫描 agent。

**说明**：部分行数为分组内单文件的估算（分组总行已用 `wc -l` 批量核算，个别单文件行数按占比估）；子包总行数为 `cat 子包/*.py | wc -l` 精确值。