| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
| --- | --- | --- | --- | --- | --- | --- |
| app/models/production/ | production | 21 | 2550 | 无 | 无 | 车间/工位/工人技能/设备与OEE/工序/生产计划/工单/报工/生产异常处理流与PDCA与知识/领料齐套/物料批次追踪/质检返工/排产冲突 |
| app/models/project/ | project | 14 | 3285 | project→engineering(document.py import rd_project.RdProject);Customer 被 sales 依赖;core.py import platform organization.Department | 疑似(labor_cost_detail.py 死) | 项目核心与机台/生命周期阶段状态/团队与贡献/财务成本里程碑/文档模板版本/资源计划冲突/风险历史快照/成本预测与基准/客户/进度预测(schedule_prediction 活) |
| app/models/project/labor_cost_detail.py | cost-finance | 1 | 191 | 无 | 疑似(无任何 import 使用,未在 project/__init__ 导出) | 项目人工成本明细与汇总;放错域(应属 cost-finance)且无引用,死代码;无 tenant_id |
| app/models/sales/ | sales | 20 | 4473 | sales→project(sales/__init__ import project.customer.Customer) | 疑似(event_listeners.py 未注册) | 联系人/合同与条款附件/发票争议/线索商机/报价CPQ模板/区域/团队PK快照/技术评估需求冻结/评估模板/销售漏斗状态机与阀门/毛利预警/AI赢率与成本估算/操作日志/数据审核/客户关系评分/目标排名 |
| app/models/sales/event_listeners.py | sales | 1 | 342 | 无(内部 import sales services/models,同域) | 疑似(register_sales_event_listeners() 全仓无调用者) | SQLAlchemy 事件监听器,合同/报价/发票→商机/合同联动;定义齐全但注册函数从未被调用,未接线死代码 |
| app/models/service/ | aftersales | 5 | 794 | 无 | 无 | 客服服务工单(含项目关联/抄送人)/服务记录/客户沟通与满意度调查模板/服务知识库 |
| app/models/shortage/ | inventory-kitting | 6 | 988 | 无 | 疑似(smart_alert.ShortageAlert 已标废弃) | 缺料上报/到货跟踪/物料替代与调拨/工单BOM与需求齐套检查/处理日志与缺料日报;ShortageAlert 废弃改用 AlertRecord.target_type='SHORTAGE',仍被 alerts.py 保活 |
| app/models/strategy/ | strategy-pmo | 5 | 923 | 无 | 无 | 战略/CSF/KPI 与历史数据源/年度重点工作与项目关联/部门目标与个人KPI分解/战略审视日历/战略对比 |
| app/models/progress.py | project | 1 | 379 | 无(import task_center.TaskUnified 属同域) | 无 | WBS 模板与模板任务/项目任务与依赖/进度日志/计划基线与基线任务/进度报告 |
| app/models/project_delivery.py | project | 1 | 417 | 无 | 无 | 项目交付排产计划/交付任务/长周期采购/机械设计/变更日志/任务依赖 |
| app/models/project_evaluation.py | project | 1 | 180 | 无 | 无 | 项目评价记录与评价维度配置 |
| app/models/project_margin_snapshot.py | cost-finance | 1 | 69 | 无 | 无 | 每日项目毛利率快照,供毛利率趋势/健康度分析 |
| app/models/project_requirements.py | project | 1 | 133 | 无 | 无 | 项目需求与工程师能力匹配推荐;无 tenant_id |
| app/models/project_review.py | project | 1 | 227 | 无 | 无 | 项目复盘报告/经验教训/最佳实践(结项复盘沉淀) |
| app/models/project_risk.py | project | 1 | 139 | 无 | 无 | 项目风险(类型/概率/影响/自动评分);无 tenant_id |
| app/models/project_role.py | project | 1 | 165 | 无 | 无 | 项目角色类型与配置(可后台配置负责人角色);ProjectRoleType/Config 被 3 处 service/api 使用 |
| app/models/project_schedule.py | project | 1 | 137 | 无 | 无 | 项目智能排程计划与排程任务;无 tenant_id |
| app/models/project_team.py | project | 1 | 170 | 无 | 无 | 项目组团队计划/成员/组建审批;无 tenant_id |
| app/models/project_template_config.py | project | 1 | 134 | 无 | 无 | 项目模板可视化配置(阶段/节点启用禁用与排序裁剪);无 tenant_id |
| app/models/purchase.py | procurement | 1 | 353 | 无 | 无 | 采购订单与明细/收货单与明细/请购单与明细 |
| app/models/purchase_intelligence.py | procurement | 1 | 309 | 无 | 无 | 智能采购:采购建议/供应商报价/供应商绩效/采购订单跟踪;类被 3 处 service 使用 |
| app/models/qualification.py | performance-hr | 1 | 266 | 无 | 无 | 任职资格等级/岗位能力模型/员工任职资格/资格评估记录 |
| app/models/quality_risk_detection.py | project | 1 | 231 | 无 | 无 | AI 分析工作日志与项目数据识别质量风险并给出测试建议 |
| app/models/rd_project.py | engineering | 1 | 326 | 无 | 无 | 研发项目与分类/研发费用与类型/费用分摊规则/加计扣除报表记录(IPO/高企合规) |
| app/models/report.py | analytics | 1 | 231 | 无 | 无 | 工时报表自动生成子系统:报表模板/归档/收件人配置;report_template 表无 tenant_id,且表名与 report_center 冲突 |
| app/models/report_center.py | analytics | 1 | 413 | 无 | 无 | 报表中心:模板/定义/生成记录/订阅/数据导入导出任务/导入模板 |
| app/models/resource_scheduling.py | performance-hr | 1 | 443 | 无 | 无 | 资源冲突检测/调度建议/需求预测/利用率分析/调度日志;5 表全无 tenant_id |
| app/models/scheduler_config.py | platform-infra | 1 | 98 | 无 | 无 | 定时服务执行频率与启用配置;其 JSONType 被 stage_instance/stage_template 借用 |
| app/models/session.py | platform-auth | 1 | 94 | 无 | 无 | 用户登录会话,支持多设备登录与会话管理 |
| app/models/sla.py | aftersales | 1 | 144 | 无 | 无 | SLA 策略与 SLA 监控记录 |
| app/models/staff_matching.py | performance-hr | 1 | 356 | 无 | 无 | AI 人员匹配:标签字典/员工标签评估/扩展档案/项目绩效历史/项目人员需求/AI 匹配日志 |
| app/models/stage_instance.py | project | 1 | 247 | 无(import scheduler_config.JSONType 属平台) | 无 | 项目阶段实例/节点实例/节点子任务(运行时) |
| app/models/stage_template.py | project | 1 | 193 | 无(import scheduler_config.JSONType 属平台) | 无 | 阶段模板/大阶段定义/小节点定义/模板变更历史(定义层) |
| app/models/standard_cost.py | cost-finance | 1 | 133 | 无 | 无 | 标准成本库项与标准成本历史记录 |
| app/models/state_machine.py | platform-infra | 1 | 50 | 无 | 无 | 通用统一状态转换审计日志 |
| app/models/task_center.py | project | 1 | 380 | 无 | 无 | 个人任务中心:统一任务/岗位职责模板/操作日志/评论/提醒/完成证明 |
| app/models/technical_review.py | engineering | 1 | 265 | 无 | 无 | 技术评审(PDR/DDR/PRR/FRR/ARR)/参与人/材料/检查项记录/评审问题 |
| app/models/technical_spec.py | engineering | 1 | 111 | 无 | 无 | 技术规格需求与规格匹配记录 |
| app/models/tenant.py | platform-auth | 1 | 95 | 无 | 无 | 租户主表(多租户核心);自身无 tenant_id 属正常 |
| app/models/timesheet.py | performance-hr | 1 | 373 | 无 | 无 | 工时记录/批次/汇总/加班申请/工时规则/审批日志 |
| app/models/timesheet_reminder.py | performance-hr | 1 | 251 | 无 | 无 | 工时提醒配置/提醒记录/异常记录;3 表全无 tenant_id |
| app/models/two_factor.py | platform-auth | 1 | 77 | 无 | 无 | 2FA 密钥与一次性备份码 |
| app/models/user.py | platform-auth | 1 | 380 | 无 | 无 | 用户/角色/API 权限/角色-权限/用户-角色/角色模板/权限审计/方案额度交易与配置 |
| app/models/user_dashboard_layout.py | analytics | 1 | 41 | 无 | 无 | 用户按角色自定义仪表盘组件排列与显隐;无 tenant_id |
| app/models/vendor.py | procurement | 1 | 119 | 无 | 无 | 统一供应商(合并 suppliers 与 outsourcing_vendors,vendor_type 区分) |
| app/models/warehouse.py | inventory-kitting | 1 | 176 | 无 | 无 | 仓库/库位/入库单与明细/出库单与明细/库存/盘点单与明细;9 表全无 tenant_id |
| app/models/work_log.py | performance-hr | 1 | 162 | 无 | 无 | 工作日志/日志配置/@提及关联 |

## 异常发现

**死代码群**
- `app/models/project/labor_cost_detail.py`：`ProjectLaborCostDetail` / `ProjectLaborCostSummary` 全仓仅自引用，未在 `project/__init__.py` 导出、无任何 service/endpoint import（endpoint `labor_cost_detail.py` 是占位 placeholder，走的是别的路径）。判定死代码。
- `app/models/sales/event_listeners.py`：`register_sales_event_listeners()` / `unregister_...()` 定义完整（合同/报价/发票→商机/合同联动），但全仓无任何调用者，事件从未注册生效。未接线死代码。

**重复 / 并存实现**
- `report.py` 与 `report_center.py` 均声明 `__tablename__ = "report_template"`，且都各自定义 `ReportTypeEnum`——表名冲突、两套报表生成框架并存（report.py 为工时报表专用，report_center.py 为通用报表中心）。重构时需合并或改名。

**废弃并存（尸体保活）**
- `shortage/smart_alert.ShortageAlert` 已在 `shortage/__init__.py` 与文件注释标注废弃（缺料预警统一走 `AlertRecord.target_type='SHORTAGE'`），但仍被 `shortage/alerts.py` `import ... # noqa` 保活，未彻底移除。

**放错位置的文件**
- `project/labor_cost_detail.py`（人工成本，应属 cost-finance）却在 project 子包内。
- `project_margin_snapshot.py`、`standard_cost.py`（成本/毛利模型，应属 cost-finance）散落在 models 顶层，未归入任何成本域聚合。

**无 tenant_id 的表清单（多租户缺口）**
- `project_requirements.py`：project_requirements、engineer_recommendations
- `project_risk.py`：project_risks
- `project_schedule.py`：project_schedule_plans、schedule_tasks
- `project_team.py`：project_team_plans、project_team_members、project_team_approvals
- `project_template_config.py`：project_template_configs、stage_configs、node_configs
- `resource_scheduling.py`：resource_conflict_detection、resource_scheduling_suggestions、resource_demand_forecast、resource_utilization_analysis、resource_scheduling_logs
- `timesheet_reminder.py`：timesheet_reminder_config、timesheet_reminder_record、timesheet_anomaly_record
- `user_dashboard_layout.py`：user_dashboard_layouts
- `warehouse.py`：warehouses、warehouse_locations、inbound_orders、inbound_order_items、outbound_orders、outbound_order_items、inventory、stock_count_orders、stock_count_items
- `report.py`：report_template（同文件的 report_archive、report_recipient 有 tenant_id，仅此表缺）
- `project/labor_cost_detail.py`：project_labor_cost_details、project_labor_cost_summaries（同属死代码）
- 说明：`tenant.py` 的 tenants 表自身无 tenant_id 属正常，不计入缺口。
