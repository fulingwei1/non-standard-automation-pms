Based on my analysis, here is the归域清单 for my assigned range.

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|------|-----|--------|--------|----------|-----------|------|
| app/services/rd_report_data_service.py | analytics | 1 | 268 | engineering(RdProject/RdCost)、performance-hr(Timesheet) | 无 | 研发费用报表数据构建（加计扣除辅助账），被 report_framework/adapters/rd_expense 调用 |
| app/services/relationship_scoring_service.py | sales | 1 | 765 | 无 | 无 | 客户关系成熟度六维度评分，被 customer_360 / relationship_maturity 端点使用 |
| app/services/report/ | analytics | 2 | 732 | performance-hr(Timesheet) | 无 | 工时报表业务逻辑层 ReportService，被 endpoints/report.py 使用 |
| app/services/report_data_generation/ | analytics | 5 | 995 | 多域(部门/项目/分析报表) | 无 | 报表中心数据生成（core+权限+dept/project/analysis 报表+router），被 report_center 端点使用 |
| app/services/report_excel_service.py | platform-file / analytics | 1 | 376 | 无 | 无 | 报表 Excel 导出（总览+明细+图表），被 report 端点、scheduled_tasks、project_report_auto 复用 |
| app/services/report_framework/ | analytics | 41 | 6031 | 全域(adapters 覆盖 sales/acceptance/timesheet/rd_expense/shortage/project/meeting/department) | 无 | 通用报表框架（engine/config/data_source/expressions/formatters/generators/renderers+13个业务 adapter），报表中心核心，62处引用 |
| app/services/report_labor_cost.py | cost-finance | 1 | 61 | performance-hr(Timesheet)、依赖 HourlyRateService | 无 | 共享工时人工成本计算 helper，6处引用（presale/waste 等） |
| app/services/report_service.py | analytics | 1 | 493 | performance-hr(Timesheet) | 疑似(与 report/report_service.py 并存) | 工时报表自动生成服务，被 scheduled_tasks/report_tasks 使用；与 report/ 包内同名 ReportService 重复 |
| app/services/requirement_extraction_service.py | performance-hr | 1 | 469 | project(Project)、engineering(project_requirements/EngineerRecommendation) | 疑似(仅 tests 引用) | 项目需求 AI 抽取+工程师能力匹配推荐，app/ 内无生产引用 |
| app/services/resource_allocation_service/ | performance-hr | 7 | 605 | production(经由 scheduling_suggestion 消费) | 无 | 资源分配服务（allocation/worker/workstation/conflicts），经 scheduling_suggestion_service→assembly_kit 端点存活 |
| app/services/resource_plan_service.py | performance-hr | 1 | 628 | project(Project/Task)、依赖 Timesheet/Department | 无 | 项目阶段资源计划 CRUD+人员负载/部门工作量分析，被 projects/resource_plan 端点使用（含已合并的 ResourcePlanningService） |
| app/services/resource_scheduling/ | performance-hr | 2 | 722 | performance-hr(resource_scheduling_ai_service) | 疑似(仅 tests+scripts；端点是 501 禁用 shim) | 资源调度服务（冲突检测/方案推荐/利用率），对应端点 resource_scheduling.py 已禁用，改用 /engineer-scheduling |
| app/services/resource_scheduling_ai_service.py | performance-hr | 1 | 848 | project(Project) | 疑似(仅被上面已死的 resource_scheduling 包引用) | GLM 资源调度 AI（冲突检测/建议），唯一消费者是死掉的 resource_scheduling 包 |
| app/services/resource_waste_analysis/ | presale | 8 | 806 | 依赖 HourlyRateService | 疑似(仅 tests；presale 端点未 import 本包) | 售前资源浪费分析（waste_calculation/salesperson/failure_patterns/investment/trends），端点 presale_analytics/resource_analysis 自行用 report_labor_cost 算，未用本包 |
| app/services/revenue_service.py | cost-finance | 1 | 199 | sales(Invoice)、project(Project) | 无 | 从合同/发票获取项目营业收入数据（合同额/已收/已开票） |
| app/services/role_management/ | platform-auth | 2 | 1181 | 无 | 疑似(与 role_service.py 职责重叠) | 角色管理业务逻辑（含权限审计 PermissionAuditService），被 roles.py 端点使用 |
| app/services/role_service.py | platform-auth | 1 | 168 | 无 | 疑似(与 role_management 并存) | 基于 BaseService 的角色 CRUD，与 RoleManagementService 同在 roles.py 端点使用 |
| app/services/sales/ | sales | 46 | 11297 | presale(presale_quote_context 桥接售前方案)、platform-notify(reminder→NotificationDispatcher) | 无 | 销售域大包：合同(contract/)+成本估算(cost/)+推荐引擎(engines/)+报价/漏斗状态机/阶段门/健康度/催款/毛利预警/各实体操作审计等，136处引用 |
| app/services/sales_ai_assistant_service.py | sales | 1 | 733 | 依赖 platform-ai(AIClientService) | 无 | AI 销售助手（带降级标注），被 sales 相关端点使用 |
| app/services/sales_forecast_service.py | sales | 1 | 569 | 无 | 无 | 销售预测（公司/团队/个人分解+准确性追踪），被 sales/sales_forecast 端点使用 |
| app/services/sales_prediction_service.py | sales | 1 | 462 | 无 | 疑似轻微(与 sales_forecast 功能重叠) | 销售预测服务，被 statistics_prediction / opportunity_analytics 端点使用 |
| app/services/sales_ranking_service.py | sales | 1 | 406 | 无(内 import sales_team_service 同域) | 无 | 销售排名计算与配置 |
| app/services/sales_reminder/ | sales | 8 | 1330 | platform-notify(NotificationDispatcher) | 无 | 销售提醒扫描器（合同到期/发票/里程碑/收款/漏斗流转提醒），11处引用 |
| app/services/sales_target_service.py | sales | 1 | 434 | 无 | 无 | 销售目标 CRUD（SalesTargetV2/分解日志/团队） |
| app/services/sales_team_service.py | sales | 1 | 657 | 无 | 无 | 销售团队 CRUD+区域+成员+目标，5处引用 |
| app/services/schedule_generation_service.py | project | 1 | 460 | 无 | 无 | AI 智能排程（ProjectSchedulePlan/ScheduleTask），被 schedule_generation 端点使用 |
| app/services/schedule_optimization_service.py | project | 1 | 564 | 无 | 疑似(仅 tests+scripts 引用) | AI 排程优化分析，app/ 内无生产引用 |
| app/services/schedule_prediction_service.py | project | 1 | 817 | 依赖 platform-ai(AIClientService) | 无 | 进度预测服务，被 projects/schedule_prediction 端点使用 |
| app/services/scheduling_suggestion_service.py | production | 1 | 434 | performance-hr(resource_allocation_service)、inventory-kitting(MaterialReadiness)、sales(Customer) | 无 | 排产建议服务（Machine/物料齐套），被 assembly_kit/scheduling 端点使用 |
| app/services/service/ | aftersales | 3 | 1266 | 无 | 无 | 服务工单/服务记录/工单通知（含 ServiceTicket 兼容层），7处引用 |
| app/services/session_service.py | platform-auth | 1 | 582 | 无 | 无 | 用户会话创建/查询/安全控制，6处引用 |
| app/services/shortage/ | inventory-kitting | 4 | 2127 | 无 | 无 | 缺料管理主服务（management/reports/需求预测引擎/智能预警引擎），6处引用 |
| app/services/shortage_alerts/ | inventory-kitting | 2 | 527 | inventory-kitting(shortage.demand_forecast/smart_alert_engine) | 无 | 缺料预警业务逻辑，封装 shortage 引擎 |
| app/services/shortage_analytics/ | inventory-kitting | 2 | 423 | 无 | 无 | 缺料分析（提取自 shortage/analytics/dashboard 端点） |
| app/services/shortage_report_service.py | inventory-kitting | 1 | 15 | 无 | 疑似(向后兼容 re-export wrapper) | 仅 re-export shortage.shortage_reports_service，仅 tests+scripts 引用 |

## 异常发现

- **死代码群（资源调度）**：`resource_scheduling/`（包）与 `resource_scheduling_ai_service.py` 构成一条死链——对应端点 `app/api/v1/endpoints/resource_scheduling.py` 已是返回 501 的禁用 shim（注释指向 `/engineer-scheduling`），二者仅被 tests 和 `scripts/import_services_batch3.py` 引用。
- **疑似死代码（仅 tests 引用）**：`requirement_extraction_service.py`、`schedule_optimization_service.py`、`resource_waste_analysis/`（端点 `presale_analytics/resource_analysis.py` 自行用 `report_labor_cost` 计算，未 import 本包）。
- **兼容 wrapper / 尸体**：`shortage_report_service.py` 仅 15 行 re-export 到 `shortage/shortage_reports_service.py`，实现已迁移，wrapper 仅剩 tests/scripts 引用。
- **重复/并存实现（报表）**：`report_service.py`（顶层，被 scheduled_tasks 使用）与 `report/report_service.py`（被 endpoints/report.py 使用）均定义 `ReportService` 且都是"工时报表"，实现重复、消费者不同，属并存双实现。
- **重复/并存实现（角色）**：`role_service.py`（BaseService CRUD 版 `RoleService`）与 `role_management/service.py`（`RoleManagementService`，含权限审计）职责重叠，且同在 `roles.py` 端点被并列 import。
- **重复/并存实现（销售预测）**：`sales_forecast_service.py`（`SalesForecastService`）与 `sales_prediction_service.py`（`SalesPredictionService`）功能高度重叠，分别被不同 sales 端点使用。
- **悬空 import**：`app/api/v1/endpoints/report_center/generate/comparison.py:31` 局部 import `app.services.report_data_generation_service`（`report_data_service`），但该文件在 `app/services/` 下**不存在**（只有同名的 `report_data_generation/` 包），为断裂引用。
- **跨域依赖热点**：`report_framework/` 的 adapters 层直接依赖几乎所有业务域的 services/models（sales/acceptance/timesheet/rd_expense/shortage/project/meeting/department），是重构时耦合最重的报表聚合中心，应作为拆分的重点边界。
- **多租户检查**：本范围为 services 层，未直接定义 ORM 表，tenant_id 检查不适用（N/A）。