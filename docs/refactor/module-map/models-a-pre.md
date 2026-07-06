## 归域清单：app/models（acceptance.py → presale_usage_feedback.py）

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|------|----|--------|--------|----------|-----------|------|
| acceptance.py | acceptance | 1 | 366 | 无(FK项目) | 无 | 验收模板/类别/检查项/验收单/明细/问题/签字/报告，验收交付核心 |
| admin_office.py | 待定 | 1 | 113 | 无 | 无 | 行政办公：办公用品/车辆/资产/费用，无对应业务域（行政后勤） |
| advantage_product.py | presale | 1 | 660 | 无 | 无 | 优势产品/行业分类目录，供售前AI方案匹配+中标率预测+销售线索选型（跨 sales） |
| after_sales.py | aftersales | 1 | 297 | 无 | 无 | 售后反馈/维保/质保/备件/现场服务/SLA/满意度/知识，售后全套 |
| ai_feedback.py | platform-ai | 1 | 30 | 无 | 无 | ai_output_feedbacks，通用 AI 输出反馈 |
| ai_job.py | platform-ai | 1 | 30 | 无 | 无 | ai_generation_jobs，通用 AI 异步任务记录 |
| alert.py | platform-notify | 1 | 498 | 无(含project健康快照) | 无 | 告警规则/记录/通知/异常事件/处置/升级/统计/订阅，通用告警异常引擎 |
| api_key.py | platform-auth | 1 | 66 | 无 | 无 | api_keys，API 密钥凭证 |
| assembly_kit.py | inventory-kitting | 1 | 530 | 无(FK bom) | 无 | MES装配阶段/模板+物料就绪/缺料/齐套率快照/排产建议，装配齐套桥接（跨 production） |
| audit_pack.py | platform-file | 1 | 64 | 无 | 无 | audit_pack_requests，审计资料包导出请求 |
| base.py | platform-infra | 1 | 1492 | 无 | 无 | SQLAlchemy Base 声明基类+各类 Mixin+建表/自愈迁移引导，无 TenantMixin（tenant_id 逐表手写） |
| bonus.py | performance-hr | 1 | 291 | 无 | 无 | 奖金规则/计算/分配/团队分配/分配表，奖金管理 |
| budget.py | cost-finance | 1 | 171 | 无 | 无 | 项目预算/预算项/成本分摊规则 |
| change_impact.py | ecn | 1 | 242 | 无 | 无 | change_impact_analysis/change_response_suggestions 变更影响分析（经 __init__ 再导出被 service 使用，存活；注意与 project/change_impact.py 并存） |
| change_request.py | ecn | 1 | 261 | 依赖 enums(共享) | 无 | change_requests/change_notifications 变更请求与通知 |
| company_certification.py | sales | 1 | 42 | 无 | 无 | company_certifications 企业资质证书（投标用） |
| company_profile.py | sales | 1 | 37 | 无 | 疑似(全库0引用) | company_profile 公司简介，无任何 service/api 引用 |
| competitor.py | sales | 1 | 58 | 无 | 疑似(全库0引用) | competitors 竞争对手，模型类无任何引用 |
| cost_prediction.py | cost-finance | 1 | 319 | 无 | 无 | cost_prediction/cost_optimization_suggestions，经 __init__ 再导出，被引用46处（存活） |
| culture_wall.py | performance-hr | 1 | 158 | 无 | 无 | 文化墙内容/个人目标/阅读记录 |
| culture_wall_config.py | performance-hr | 1 | 64 | 无 | 无 | 文化墙配置 |
| dashboard_chart_config.py | analytics | 1 | 30 | 无 | 无 | dashboard_chart_configs 看板图表配置 |
| earned_value.py | cost-finance | 1 | 233 | 无 | 无 | earned_value_data/snapshots，EVM挣值，被引用44处（存活） |
| employee_encrypted_example.py | platform-infra | 1 | 163 | 无 | 疑似(示例文件0引用) | 加密字段类型演示样例，非生产模型 |
| encrypted_types.py | platform-infra | 1 | 200 | 无 | 无 | SQLAlchemy 自定义加密字段类型（无表） |
| engineer_capacity.py | performance-hr | 1 | 232 | 无 | 无 | 工程师产能/任务分配/负荷预警，资源调度（跨 engineering） |
| field_commissioning.py | production | 1 | 80 | 无 | 无 | 现场任务/签到/问题，现场调试 |
| holiday.py | performance-hr | 1 | 144 | 无 | 无 | holidays 节假日日历（供排班/工时），全局参考数据 |
| hourly_rate.py | cost-finance | 1 | 75 | 无 | 无 | hourly_rate_configs 工时费率配置（成本核算） |
| installation_dispatch.py | production | 1 | 144 | 无 | 无 | installation_dispatch_orders 安装派工单 |
| inventory_tracking.py | inventory-kitting | 1 | 434 | 无 | 无 | 物料事务/库存/预留/调整/盘点任务与明细，库存台账 |
| issue.py | project | 1 | 355 | 依赖 enums.acceptance | 无 | 问题/解决方案模板/跟进/统计快照/问题模板，问题跟踪，被引用37处 |
| kitting_optimization.py | inventory-kitting | 1 | 140 | 无 | 无 | expedite_records/material_alternatives 催料记录/替代料 |
| knowledge_base.py | strategy-pmo | 1 | 205 | 无 | 无 | knowledge_entries/knowledge_alerts 结项知识自动沉淀+坑点预警 |
| login_attempt.py | platform-auth | 1 | 34 | 无 | 无 | login_attempts 登录尝试（账号锁定） |
| management_rhythm.py | strategy-pmo | 1 | 546 | 无 | 无 | 管理节律配置/战略会议/行动项/看板快照/会议报告/指标定义，经营节律 |
| material.py | bom-material | 1 | 300 | 无 | 无 | 物料分类/物料/供应商/BOM头/BOM项/缺料，物料BOM主数据，被引用90处 |
| material_progress_subscription.py | procurement | 1 | 50 | 无 | 无 | material_progress_subscriptions 物料进度订阅提醒 |
| notification.py | platform-notify | 1 | 105 | 无 | 无 | notifications/notification_settings 通用通知 |
| organization.py | platform-auth | 1 | 609 | 方法内 import project.customer | 无 | 部门/员工/HR档案/HR事务/合同/薪资/组织单元/岗位/职级/岗位角色，组织+HR混装，被引用83处（拆分候选：薪资/合同/HR事务→performance-hr） |
| otd_risk_snapshot.py | project | 1 | 85 | 无 | 无 | otd_risk_snapshots 交期(OTD)风险快照 |
| otd_threshold_config.py | project | 1 | 193 | 无 | 无 | otd_threshold_configs 交期风险阈值配置 |
| outsourcing.py | procurement | 1 | 411 | import vendor(同域) | 无 | 外协订单/明细/交付/检验/付款/评价/进度，外协管理 |
| permission.py | platform-auth | 1 | 218 | 无 | 无 | permission_groups/menu_permissions/role_menus 权限组/菜单权限/角色菜单 |
| pipeline_analysis.py | sales | 1 | 113 | 无 | 疑似(仅exports聚合器引用,service/api 0引用) | pipeline_break_records/health_snapshots/accountability_records 销售管道断裂分析 |
| pitfall.py | strategy-pmo | 1 | 148 | 无 | 无 | pitfalls/recommendations/learning_progress 踩坑库/推荐/学习进度 |
| presale.py | presale | 1 | 494 | 无 | 疑似(被 presale/ 包遮蔽,不可达) | 售前工单/交付物/方案/成本/模板/客户技术档案/投标 旧版；与 presale/ 同名包并存，Python 包优先→本模块被完全遮蔽（死代码），且9表全缺 tenant_id |
| presale_agent_metric.py | presale | 1 | 83 | 无 | 无 | presale_agent_metrics 售前 AI Agent 指标 |
| presale_agent_revision.py | presale | 1 | 69 | 无 | 无 | presale_agent_revisions 售前 AI Agent 修订 |
| presale_ai.py | presale | 1 | 209 | 无 | 无 | 售前 AI 相关5表 |
| presale_ai_emotion_analysis.py | presale | 1 | 53 | 无 | 无 | 售前 AI 情绪分析 |
| presale_ai_qa.py | presale | 1 | 40 | 无 | 无 | 售前 AI 问答 |
| presale_ai_quotation.py | presale | 1 | 117 | 无 | 无 | 售前 AI 报价2表 |
| presale_ai_requirement_analysis.py | presale | 1 | 66 | 无 | 无 | 售前 AI 需求分析/提取 |
| presale_ai_solution.py | presale | 1 | 128 | import presale(同域) | 无 | 售前 AI 方案2表 |
| presale_emotion_trend.py | presale | 1 | 34 | 无 | 无 | 售前情绪趋势 |
| presale_expense.py | presale | 1 | 117 | 无 | 无 | presale_expenses 售前费用 |
| presale_follow_up_reminder.py | presale | 1 | 51 | 无 | 无 | 售前跟进提醒 |
| presale_knowledge_case.py | presale | 1 | 59 | 无 | 无 | 售前知识案例 |
| presale_mobile.py | presale | 1 | 126 | 无 | 无 | 售前移动端4表 |
| presale_proposal.py | presale | 1 | 81 | 无 | 无 | presale_proposals/presale_proposal_versions 方案与版本 |
| presale_usage_feedback.py | presale | 1 | 70 | 无 | 无 | presale_usage_feedback 售前使用反馈 |
| ai_planning/ | project | 3(+init) | 394 | 无 | 无 | AI项目规划：计划模板/WBS建议/资源分配，业务专属AI归 project |
| approval/ | platform-approval | 6(+init) | 1155 | 无 | 无 | 统一审批引擎：模板/流程定义/实例/任务/日志/代理 |
| bom/ | cost-finance | 1(+init) | 167 | 无 | 无 | cost_breakdowns/project_cost_summaries 成本拆解与汇总（放错目录，实为成本域） |
| business_support/ | sales | 10(+init) | 1005 | 无 | 无 | 商务支持：投标/合同/发票/收款/销售订单/交付/对账/登记；内含 acceptance.py(AcceptanceTracking，偏 acceptance 域) |
| ecn/ | ecn | 9(+init) | 1006 | 无 | 无 | 工程变更全套：类型/矩阵/核心/评估审批/执行/影响/成本/日志/物料处置/责任模板 |
| engineer_performance/ | engineering | 5(+init) | 902 | 无 | 无 | 工程师技术绩效：机械/电气/测试评价+设计复用/PLC/图纸/bug/代码评审（跨 performance-hr） |
| enums/ | platform-infra | 9(+init) | 1436 | 被各业务域依赖 | 无 | 跨域共享枚举（acceptance/material/project/sales/stage/strategy/workflow 等），无表 |
| exports/ | platform-infra | 8(+init) | 1454 | re-export 全域模型 | 疑似(仅向后兼容聚合层) | 模型统一再导出兼容层(exports/complete/*)，被 models/__init__ `import *`，无自有表 |
| performance/ | performance-hr | 6(+init) | 745 | 无 | 无 | 绩效：合同/周期指标/结果评价/申诉调整/贡献排名/月度体系 |
| pmo/ | strategy-pmo | 5(+init) | 662 | 无 | 无 | PMO：立项/阶段/变更/风险/成本/会议/资源/收尾 |
| presale/ | presale | 2(+init) | 761 | 无 | 无 | 售前核心(core，presale.py 重构后的存活版，含 tenant_id)+技术参数模板 |

## 异常发现

**死代码 / 遮蔽**
- `presale.py`（顶层，494行）被同名包 `presale/` 完全遮蔽：`from app.models.presale import ...` 在 Python 中优先解析到包（`presale/__init__.py`→`presale/core.py`），顶层模块不可达。它是重构前的旧版（core.py 是其重构继任者），属死代码，且9张表全部缺 `tenant_id`。建议删除。
- `company_profile.py`（company_profile 表）：全库 0 引用，疑似死代码。
- `competitor.py`（competitors 表）：模型类全库 0 引用，疑似死代码（sales 下另有 competitor_analysis 端点但不引用此模型）。
- `pipeline_analysis.py`（3表）：仅被 `exports/complete/other_modules.py` 聚合器再导出，service/api 0 引用，疑似死代码。
- `employee_encrypted_example.py`：加密字段类型演示样例，0 引用，非生产模型。

**重复 / 并存实现**
- 变更影响双实现并存：顶层 `change_impact.py`（ChangeImpactAnalysis/ChangeResponseSuggestion，存活）与 `project/change_impact.py`（ProjectChangeImpact，存活），两套不同表并行。
- `exports/`（尤其 `exports/complete/*`，8文件1454行）是纯向后兼容再导出层，与真实模型模块重复维护同名符号，重构时应清理。

**放错位置的文件**
- `bom/cost_breakdown.py`：位于 bom/ 目录，实际是成本拆解/项目成本汇总（cost-finance 域），应迁至 cost-finance。
- `business_support/acceptance.py`（AcceptanceTracking/AcceptanceTrackingRecord）：位于商务支持包，语义偏 acceptance 验收域。
- `organization.py`：组织架构(platform-auth)与 HR薪资/合同/HR事务(performance-hr)混装于单文件，属跨域混装，拆分候选。

**缺 tenant_id 的表（多租户风险）**
- advantage_product.py：`industries` / `industry_category_mappings` / `advantage_product_categories` / `advantage_products` / `new_product_requests`（5张全缺）
- knowledge_base.py：`knowledge_entries` / `knowledge_alerts`
- audit_pack.py：`audit_pack_requests`
- company_certification.py：`company_certifications`
- company_profile.py：`company_profile`（且死代码）
- competitor.py：`competitors`（且死代码）
- presale.py（死代码/被遮蔽）：9张表全缺（`presale_support_tickets` 等）
- presale_agent_metric.py：`presale_agent_metrics`
- presale_agent_revision.py：`presale_agent_revisions`
- presale_proposal.py：`presale_proposals` / `presale_proposal_versions`
- presale_usage_feedback.py：`presale_usage_feedback`
- ai_planning/：`ai_project_plan_templates` / `ai_wbs_suggestions` / `ai_resource_allocations`（3张全缺）
- bom/cost_breakdown.py：`cost_breakdowns` / `project_cost_summaries`
- employee_encrypted_example.py：`employee_encrypted_examples`（样例）
- holiday.py：`holidays`（全局节假日参考数据，疑为有意不分租户，需确认）

说明：base.py 无 TenantMixin，`tenant_id` 逐表手写，上述文件的表未声明该列。范围内其余文件（acceptance/admin_office/after_sales/alert/assembly_kit/bonus/budget/change_*/cost_prediction/culture_wall*/earned_value/engineer_capacity/inventory_tracking/issue/kitting_optimization/management_rhythm/material/notification/organization/otd_*/outsourcing/permission/pitfall/presale_ai*/presale_expense 等，以及 approval/business_support/ecn/engineer_performance/performance/pmo/presale 各子包所有表）均含 tenant_id。