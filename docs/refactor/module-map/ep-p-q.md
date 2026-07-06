progress_compat.py 是项目进度/WBS/里程碑的旧版兼容路由，归 project 域。我已有全部结论，直接输出最终结果。

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|------|-----|--------|--------|----------|-----------|------|
| performance/ | performance-hr | 17 | 3171 | project(Project/ProjectMember/progress.Task)、platform-auth(organization.Department/Employee) | 无 | 绩效管理主包：考核任务/个人·团队·项目绩效/申诉/员工·经理·HR端API/集成，含子包 individual/（我的·用户·趋势绩效） |
| performance_contract.py | performance-hr | 1 | 9 | 无 | 疑似(兼容 shim，仅 re-export .performance.contract) | 绩效合约路由兼容导出文件 |
| permissions/ | platform-auth | 3 | 720 | 无 | 无 | 权限管理：ApiPermission/Role CRUD + 权限矩阵，依赖 permission_management service |
| pitfalls/ | strategy-pmo | 2 | 249 | 无 | 无 | 踩坑库 CRUD（crud_refactored 为活跃版），依赖 pitfall service |
| pm_involvement.py | performance-hr | 1 | 9 | 无 | 疑似(兼容 shim，仅 re-export .performance.pm_involvement) | PM参与度路由兼容导出文件 |
| pm_monthly_check.py | strategy-pmo | 1 | 47 | cost-finance(经 dashboard.pm_monthly_check_service 算毛利健康度) | 无 | 挂 /pmo/pm-monthly-check，PM月度自检表（在管项目利润健康度+8项动作），实时聚合不入库 |
| pmo/ | strategy-pmo | 7 | 1853 | project(Project、project.closure_readiness_service) | 无 | PMO主包：立项/阶段/风险/结项/驾驶舱cockpit/会议 |
| presale/ | presale | 20 | 7274 | sales(sales.Lead/Opportunity/Contract/TechnicalAssessment/sales_funnel、sales.gate_validators)、project(project.Customer)、performance-hr(pm_involvement_service)、platform-ai(ai_job_service) | 无 | 售前主包：工单/方案proposals/模板/技术参数/投标bids/统计/分析/看板/任务/费用/方案对比/预测/工作台，含子包 tickets/ |
| presale_agent_metrics.py | presale | 1 | 119 | 无 | 无 | 售前AI Agent 指标（PresaleAgentMetric）只读查询 |
| presale_agent_revisions.py | presale | 1 | 302 | 无 | 无 | 售前AI Agent 方案修订记录（PresaleAgentRevision）CRUD |
| presale_analytics/ | presale | 7 | 999 | project(Project/Customer/Machine)、performance-hr(timesheet.Timesheet)、cost-finance(report_labor_cost) | 无 | 售前数据分析（原 presales_integration 改名）：线索转化/中标率/资源投入/销售人员绩效/仪表板 |
| presale_proposals.py | presale | 1 | 296 | platform-ai(ai_client_service、presale_agent_orchestrator)、platform-notify(proposal_notifier) | 无 | 售前方案 PresaleProposal/Version CRUD + AI改写 + 评审通知 |
| presale_usage_feedback.py | presale | 1 | 137 | 无 | 无 | 售前功能使用反馈（PresaleUsageFeedback）采集 |
| procurement/ | procurement | 3 | 539 | 无 | 无 | 采购分析包（原聚合 router 已下线），仅 analysis(/procurement-analysis) + supplier_price_trend(/supplier-price) 被 api.py 直连挂载 |
| production/ | production | 32 | 6576 | bom-material(material.Material)、inventory-kitting(inventory.OutboundService/stock_update)、project(Project) | 无 | 生产管理主包：车间/工位/工人/计划/工单/报工/异常/领料/物料追踪/进度/排程/质量/产能，含子包 capacity/、work_orders/ |
| production_daily_reports.py | production | 1 | 242 | 无 | 无 | 生产日报 ProductionDailyReport 聚合（关联 WorkReport/WorkOrder/Worker/Workshop） |
| progress_compat.py | project | 1 | 891 | 无(仅依赖 project 域 progress.Task/WbsTemplate、project.Project/Milestone) | 无 | 旧版进度跟踪页兼容路由，挂 /progress；WBS模板/任务/依赖/里程碑进度（去重后仅保留 /progress 前缀） |
| project_contributions.py | project | 1 | 6 | 无 | 疑似(兼容 shim，re-export .projects.contributions，指向 projects/ 包) | 项目贡献度路由兼容导出文件 |
| project_delivery/ | project | 7 | 323 | 无(仅 project_delivery_service) | 无 | 项目交付排产计划：排程/任务/采购/设计/变更/甘特，均挂 /project-delivery/schedules |
| project_legacy_compat.py | project | 1 | 82 | 无 | 疑似(遗留别名，前端旧路径 /projects/{id}/members·/stages 薄别名) | 旧版项目成员/阶段列表兼容路由，底层走 ProjectMembersService/StageInstance |
| project_review/ | project | 5 | 731 | presale(presale_knowledge_case.PresaleKnowledgeCase) | 无 | 项目复盘：复盘reviews/经验教训lessons/对比comparison/知识knowledge，依赖 project_review_ai(AI提取/对比/同步) |
| project_workspace.py | project | 1 | 28 | 无 | 疑似(兼容 shim，re-export .projects.workspace，指向 projects/ 包) | 项目工作台路由兼容导出文件（含多级 ImportError 兜底占位） |
| purchase/ | procurement | 7 | 1977 | bom-material(material.Material/BomHeader)、inventory-kitting(inventory.inbound_service)、cost-finance(cost_collection_service、budget_alert_service) | 无 | 采购管理主包（拆自 purchase.py）：订单/申请/收货/建议/审批工作流，挂 /purchase-orders，vendor.Vendor 同域 |
| qualification/ | performance-hr | 5 | 729 | 无 | 无 | 任职资格管理：资格等级/岗位能力模型/员工资格/资格评估，依赖 qualification_service |
| quality_risk.py | 待定(project/production 语义模糊) | 1 | 27 | 无 | 疑似(多级 ImportError 全部落空→返回 placeholder router) | 质量风险兼容 shim，目标模块 .quality/.qualityrisk/.common./.admin 均不存在，实际仅暴露占位 `{'message':'quality_risk module placeholder'}` |
| quote_actual_compare.py | cost-finance | 1 | 9 | 无 | 疑似(兼容 shim，仅 re-export .cost_endpoints.quote_actual_compare) | 报价vs实际成本对比路由兼容导出文件（真实实现在 cost_endpoints/，挂 /quote-compare） |

## 异常发现

- **死代码/占位 stub**：`quality_risk.py` 挂在 `/quality-risk` 且在活跃路由链中被注册，但其 4 级 `ImportError` 兜底目标（`.quality`/`.qualityrisk`/`.common.quality_risk`/`.admin.quality_risk`）在 endpoints 目录下均不存在，运行时必然落到 fallback，只返回 `{'message':'quality_risk module placeholder'}` —— 实为无功能占位端点，前端若真有质量风险功能则未接通。

- **兼容 shim 群（仅 re-export，本身无逻辑）**：`performance_contract.py`、`pm_involvement.py`、`project_contributions.py`、`project_workspace.py`、`quote_actual_compare.py` 五个顶层文件都是 1 个 `from .xxx import router` 的转发文件。其中 `project_contributions.py`、`project_workspace.py` 转发进 `projects/` 包（不在本次扫描范围，需并表核对目标是否存在）；`project_workspace.py` 还带多级 ImportError 占位兜底。重构时这些应折叠回各自真实模块，路由前缀在 api.py 侧保留即可。

- **遗留别名**：`project_legacy_compat.py` 为前端旧路径 `/projects/{id}/members`、`/projects/{id}/stages` 提供薄别名，功能与 projects 包内正式路由重复，属计划淘汰的过渡代码。

- **放错位置/命名不一致**：`quote_actual_compare.py`（cost-finance 语义）、`quality_risk.py` 的真实/目标实现都在 `cost_endpoints/`、其它包内，顶层散落的这些 shim 使 endpoints 根目录既有业务包又有转发文件，边界混乱。`procurement/` 与 `purchase/` 同属 procurement 域却分成两个包（前者只剩分析、后者是订单主干），`procurement/__init__.py` 明确记载原聚合 router（suppliers/price/kitting-analysis）已因无消费方/与顶层 /suppliers 重复而下线——属已清理的死代码残留说明。

- **跨域耦合热点（重构拆分需优先解耦）**：`presale/` 与 `presale_analytics/` 深度依赖 `sales`、`project`；`production/`、`purchase/` 双双依赖 `bom-material` + `inventory-kitting`（+ purchase 依赖 cost-finance）；`project_review/` 反向依赖 `presale`（PresaleKnowledgeCase）；`performance/`、`pmo/`、`progress_compat/` 依赖 `project`。

- **多租户 tenant_id 检查**：本范围为 endpoints（路由层），不含表定义，未涉及 tenant_id 字段核查（应由 models 扫描 agent 覆盖）。

- **未核实**：`progress_compat.py` 仅读取头部与 imports（891 行未逐行细读），但 docstring/imports 已明确其为 project 域进度兼容路由，死代码嫌疑判为无。

（注：本范围内所有目录/文件均已确认注册进 `app.main` 实际生效的 `app.api.v1.api:api_router`，无"仅在 backup/minimal 变体注册"的疑似未挂载项。）