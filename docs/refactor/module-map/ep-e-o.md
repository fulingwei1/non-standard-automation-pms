| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|------|----|-------|-------|---------|----------|------|
| engineer_performance/ | performance-hr | 14 | 3107 | engineering(design_review_sync_service)、strategy-pmo(knowledge_auto_identification/knowledge_contribution_service)、issues/project(debug_issue_sync_service)、performance-hr(bonus.solution_engineer_bonus_service) | 无 | 工程师绩效评价：数据采集/协作评分/上级评价/排名/趋势/知识贡献/反馈汇总，聚合 router 挂 /engineer-performance |
| engineer_scheduling.py | performance-hr | 1 | 482 | project | 无 | 工程师排班/产能与任务指派，走 engineer_scheduling_service |
| engineers/ | project | 7 | 1185 | platform-approval(approval_engine)、platform-notify(notification_dispatcher) | 无 | 工程师视角的项目/任务/进度更新/证明材料/延期报告/进度可视化，挂 /engineers |
| export_docs.py | platform-file | 1 | 68 | presale(presale_proposal + presale.docx_exporter)、audit_pack | 无 | 通用文档导出 API，实际导出售前方案与审计包 docx |
| field_commissioning.py | production | 1 | 309 | 无（自域 field_commissioning） | 无 | 现场调试签到/问题/任务管理 |
| finance_reports.py | cost-finance | 1 | 421 | sales(contracts/invoices)、project.financial、budget、platform-auth(data_scope) | 无 | 财务报表页数据：预算/成本/回款计划汇总 |
| gantt_dependency.py | project | 1 | 633 | 无 | 无 | 甘特图依赖关系与关键路径计算，挂 /gantt |
| hourly_rate/ | performance-hr | 3 | 479 | 无（自域 hourly_rate + hourly_rate_service） | 无 | 用户时薪配置 CRUD 与查询（供人工成本计算），挂 /hourly-rates |
| hr_management/ | performance-hr | 5 | 999 | platform-auth(organization models) | 无 | 人事事务(入离职/转正/调岗/晋升/调薪)、合同、到期提醒、人事看板，挂 /hr |
| installation_dispatch/ | production | 5 | 869 | performance-hr(engineer_scheduling_service/engineer_capacity)、project、performance-hr(timesheet) | 无 | 安装调试派工单 CRUD/状态流转/统计，挂 /installation-dispatch |
| inventory/ | inventory-kitting | 2 | 648 | 无（inventory_management_service/stock_count_service） | 无 | 库存管理/物料全流程跟踪，router 自带 /inventory 前缀 |
| inventory_analysis.py | inventory-kitting | 1 | 303 | 无（material 模型） | 无 | 库存分析统计，挂 /inventory-analysis |
| issues/ | project | 13 | 3056 | acceptance、aftersales(service)、cost-finance(issue_cost_service)、platform-file(import_export_engine)、platform-auth(data_scope) | 无 | 问题管理：CRUD/状态流转/统计/批量/导入导出/看板/模板，挂 /issues |
| itr.py | aftersales | 1 | 79 | 无（itr_service） | 无 | ITR 服务流程端点，挂 /itr |
| kit_check/ | inventory-kitting | 5 | 719 | bom-material(material 模型)、production、project、procurement(services.purchase)、shortage | 无 | 齐套检查工单/执行/开工确认/历史，router 自带 /kit-check |
| kit_rate/ | inventory-kitting | 6 | 776 | bom-material(material)、project、procurement(purchase.in_transit) | 无 | 齐套率(机台/项目/看板/统一)计算与缺料清单 |
| knowledge/ | strategy-pmo | 5 | 480 | 无 | 疑似(禁用遗留占位) | __init__ 为 501 兜底 stub，明确声明 legacy 自动抽取路由已禁用；未在任何 api 聚合器挂载，包内 alerts/extraction/induction/search 为死代码 |
| labor_cost_detail.py | cost-finance | 1 | 26 | 无 | 疑似(compat shim) | 兼容加载器，实际解析到 cost_endpoints/labor_cost_detail，挂 /labor-cost |
| lessons_learned.py | strategy-pmo | 1 | 312 | engineering/project(project_review 模型) | 无 | 经验教训/踩坑库，挂 /lessons |
| management_rhythm/ | strategy-pmo | 12 | 2793 | cost-finance(budget/project.financial/cost.cost_basis)、project、analytics(report_framework)、platform-file(meeting_report_docx) | 无 | 经营节律：配置/会议/行动项/看板/会议地图/指标/报表，挂 /management-rhythm |
| management_rhythm_compat.py | strategy-pmo | 1 | 206 | 无 | 无 | management-rhythm demo 页兼容路由，与上表同前缀先注册 |
| margin_dashboard.py | cost-finance | 1 | 163 | project(otd._require_pmo_or_admin)、cost-finance(dashboard.margin_*/profit_analysis) | 无 | 毛利看板端点 |
| margin_prediction.py | cost-finance | 1 | 413 | project | 无 | 毛利预测，挂 /margin-prediction |
| material/ | inventory-kitting | 5 | 1367 | procurement(material_procurement_optimization_service/purchase)、project(project.core/lifecycle/project_risk)、platform-notify(notification)、inventory-kitting(kitting_optimization_service) | 疑似(仅 lazy 挂载) | 物料跟踪/采购优化/项目融合/物料同步；活动 api.py 未挂载，仅 api_lazy.py 注册 material.tracking 一个子路由（api_lazy 为死代码），故整体在生效路由中未挂载 |
| material_demands/ | procurement | 5 | 561 | bom-material(material)、project、procurement(purchase/in_transit) | 无 | 物料需求计划(MRP)：需求对比/生成采购需求/时间表/交期预测，挂 /material-demands |
| materials/ | bom-material | 5 | 571 | production、procurement(purchase)、shortage、procurement(vendor) | 无 | 物料主数据 CRUD/分类/供应商关联/仓储统计，挂 /materials |
| my/ | performance-hr | 1 | 243 | project(project 服务/task_center)、performance-hr(timesheet/work_log) | 无 | 个人视角聚合：我的项目/工作量/工时/任务/工作日志，挂 /my |
| notifications/ | platform-notify | 3 | 363 | 无（notification 模型） | 无 | 通知 CRUD 与通知设置，挂 /notifications |
| organization/ | platform-auth | 10 | 1730 | platform-file(import_export_engine)、performance-hr(employee_import/hr_profile_import_service) | 无 | 组织架构：部门/员工/职级/岗位/单位/人事档案/分配/批量导入，挂 /org |
| otd.py | project | 1 | 456 | cost-finance(otd.margin_export_service) | 无 | OTD 交期达成率(趋势/对比/导出)，含 _require_pmo_or_admin 被 margin/threshold 复用 |
| otd_thresholds.py | project | 1 | 65 | 无（复用 otd._require_pmo_or_admin） | 无 | OTD 阈值配置 |
| outsourcing/ | procurement | 12 | 2543 | production、project、procurement(vendor)、cost-finance(cost_collection_service)、platform-auth(data_scope) | 无 | 外协管理：供应商/订单/交付/质量/进度/付款/流转，挂 outsourcing router |

## 异常发现

- **死代码/禁用包 `knowledge/`**：`__init__.py` 是一个显式 501 兜底 stub（"Legacy knowledge auto-extraction routes are disabled"），任何生效或非生效聚合器均未 include 它；包内 `alerts.py`/`extraction.py`/`induction.py`/`search.py`（合计 480 行）为随包一起搁置的死代码。活跃知识面为 `/knowledge-base` 与 `/service/knowledge-base`（不在本范围）。
- **`material/` 目录在生效路由中未挂载**：活动聚合器 `app/api/v1/api.py`（main.py 实际加载）无任何 `material` 目录的 include；只有 `api_lazy.py`（已确认为死代码）在第 283 行注册了 `material.tracking` 一个子路由。因此 `material/` 全部 5 文件/1367 行在实际服务中不可达，属放错层/半成品扩展模块。
- **`labor_cost_detail.py` 为多级 try/except 兼容 shim**：依次尝试 `cost_endpoints/costs/production/timesheet` 四处的 `labor_cost_detail`，实际仅 `cost_endpoints/labor_cost_detail.py` 存在并被解析，其余三条分支及最终 placeholder 分支为永不触发的兜底代码。
- **命名相近的三个物料模块并存**：`materials/`（物料主数据 CRUD，bom-material，已挂载）、`material/`（物料跟踪/采购优化，未挂载）、`material_demands/`（MRP，procurement，已挂载）职责重叠且分域，重构时需合并去重。
- **`management_rhythm` 与 `management_rhythm_compat` 并存**：两者以同一 `/management-rhythm` 前缀先后注册（compat 先、正式后），compat 为 demo 页兼容层，属并存实现。
- **跨域耦合较重的模块**：`engineer_performance/`（依赖 engineering/strategy-pmo/issues 多个业务域的 sync 服务）、`management_rhythm/`（依赖 cost-finance + analytics report_framework）、`issues/`（依赖 acceptance/aftersales/cost-finance）、`outsourcing/`（依赖 production/project/cost-finance）为拆分时的高耦合点，应优先解依赖。
- **归属分层争议项**：`organization/` 中 `employees.py`/`hr_profiles.py`（走 performance-hr 的 import 服务）与纯组织架构混在 platform-auth 包内；`hourly_rate/` 与 `my/` 横跨 performance-hr 与 cost-finance/project，重构时需按子文件再切。
- **多租户 tenant_id**：本范围为 endpoints 层，不定义表结构；未做表级 tenant_id 核查（应在 models 扫描范围内处理）。