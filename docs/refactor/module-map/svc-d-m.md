归域扫描完成。范围：`app/services` 下从 `dashboard/` 到 `milestone_service.py`（含两端）共 68 个顶层条目。

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|------|----|-------|--------|---------|-----------|------|
| dashboard/ | analytics | 24 | 5878 | cost-finance, project, presale, production, sales（adapters 聚合各域数据） | 无 | 经营看板服务包：BaseDashboardService 基类 + 各角色/毛利/PM 月检/业务支撑仪表盘 + adapters/ 15 个域视图适配器 |
| dashboard_adapter.py | analytics | 1 | 16 | 无 | 疑似(向后兼容 re-export，无任何引用者，真实实现在 dashboard/dashboard_adapter.py) | 仅 re-export dashboard.dashboard_adapter，已无人 import |
| dashboard_adapters/ | analytics | 0(仅__init__) | 34 | 无 | 无 | 仅 unified.py `import` 触发适配器注册的空壳包 |
| data_integrity/ | platform-infra | 6 | 778 | 无 | 无 | 数据完整性保障服务：多重继承组合 check/auto_fix/report/reminders/export 各 Mixin |
| data_scope/ | platform-auth | 9 | 1559 | 无 | 无 | 基于角色的数据权限过滤引擎；含 data_scope_service.py 与 data_scope_service_enhanced.py 并存 |
| data_sync_service.py | project | 1 | 387 | sales(Contract, contract.status_service) | 无 | 把合同状态/金额同步到项目及回款计划的数据同步服务 |
| database/ | platform-infra | 1 | 474 | 无 | 疑似(仅测试+scripts/performance_benchmark.py 引用，无运行时 service/endpoint 使用) | query_optimizer：预加载/分页优化的查询构造工具 QueryOptimizer |
| debug_issue_sync_service.py | engineering | 1 | 284 | project(Issue) | 无 | 把机械调试问题/测试Bug记录与通用 Issue 双向自动同步 |
| delay_root_cause_service.py | project | 1 | 267 | 无 | 无 | 项目延期深度分析（任务/进度维度的延期根因） |
| delivery_validation_service.py | sales | 1 | 406 | bom-material(Material) | 无 | 基于报价与物料交期的交期校验服务 |
| design_review_sync_service.py | engineering | 1 | 204 | project(Project), (technical_review) | 无 | 设计评审记录自动同步服务 |
| document_file_lifecycle.py | platform-file | 1 | 79 | 无 | 疑似(运行时无引用，仅 scripts/scan_project_document_orphans.py + 测试使用) | 扫描项目文档孤儿文件的生命周期辅助函数 |
| docx_content_builders.py | platform-file | 1 | 349 | 无 | 无 | 通用 Word(docx) 文档格式化/表格/段落内容构建器 |
| ecn/ | ecn | 22 | 5439 | bom-material, procurement（bom_analysis/material_impact 涉及） | 无 | 工程变更(ECN)完整子系统：自动分配/成本影响/物料影响/调度 + approval/bom_analysis/integration/knowledge/notification 子包 |
| ecn_auto_assign_service.py | ecn | 1 | 20 | 无 | 疑似(向后兼容 re-export，端点已直接 import ecn.ecn_auto_assign_service) | 仅转发 ecn.ecn_auto_assign_service |
| ecn_cost_impact_service/ | ecn | 0(仅__init__) | 33 | 无 | 无 | 兼容别名包，re-export ecn.ecn_cost_impact_service（仍有引用者） |
| ecn_scheduler.py | ecn | 1 | 31 | 无 | 疑似(向后兼容入口，调度配置直接指向 ecn.ecn_scheduler) | 转发 ecn.ecn_scheduler 的 run/check 函数 |
| employee_import_service.py | performance-hr | 1 | 334 | 无 | 无 | 员工 Excel 导入（含姓名列识别、staff_matching 落库） |
| employee_performance/ | performance-hr | 1 | 509 | 无 | 无 | 员工绩效服务 EmployeePerformanceService |
| engineer_performance/ | performance-hr | 6 | 1934 | 无 | 无 | 工程师绩效评价子系统：维度配置/计算器/画像/排名/数据权限 |
| engineer_scheduling_service.py | performance-hr | 1 | 979 | 无 | 无 | 工程师智能排产与产能风险预警服务（基于 engineer_capacity） |
| equipment_maintenance_service.py | production | 1 | 181 | 无 | 无 | 设备保养提醒服务（Equipment/Workshop + 告警规则） |
| evm_service.py | cost-finance | 1 | 634 | 无 | 无 | 挣值管理(EVM)计算器（PV/EV/AC/CPI/SPI） |
| excel_export_service.py | platform-file | 1 | 358 | 无 | 无 | 通用 Excel 导出服务 |
| excel_template_service.py | platform-file | 1 | 225 | 无 | 无 | 通用 Excel 导入模板生成 |
| export/ | platform-file | 1 | 373 | 无 | 无 | 导出水印服务（PDF/Excel 加操作者/时间水印） |
| field_service_work_log_service.py | production | 1 | 230 | performance-hr(work_log_service) | 无 | 依据安装派工单自动生成外出服务工作日志 |
| file_upload_service.py | platform-file | 1 | 491 | 无 | 无 | 通用文件上传服务（hash/uuid/存储） |
| health_calculator.py | project | 1 | 711 | 无 | 无 | 项目健康度计算（多维度加权，联动 health_trend_service） |
| health_trend_service.py | project | 1 | 597 | 无 | 无 | 项目健康度趋势快照与维度权重 |
| hourly_rate_service.py | cost-finance | 1 | 313 | performance-hr(User/Department) | 无 | 时薪费率配置服务（用户/角色/部门/默认优先级） |
| hr_profile_import_service.py | performance-hr | 1 | 321 | 无 | 无 | 员工 HR 档案 Excel 导入 |
| import_export_engine.py | platform-file | 1 | 139 | 无 | 无 | Excel 导出引擎（封装 ExcelExportService） |
| information_gap_analysis_service.py | sales | 1 | 276 | 无 | 无 | 销售信息把握不足分析（Lead/Opportunity/Quote） |
| inventory/ | inventory-kitting | 9 | 940 | 无 | 无 | 库存管理子系统：出入库/预留/库存查询更新/事务/调拨 + facade |
| inventory_analysis_service.py | inventory-kitting | 1 | 510 | procurement(purchase) | 疑似(仅测试引用；活跃实现为 inventory/analysis_service.py) | 库存分析（呆滞/周转），疑为旧平铺版 |
| inventory_management_service.py | inventory-kitting | 1 | 10 | 无 | 无 | 兼容 re-export inventory 包的 facade/异常 |
| invoice_auto_service/ | sales | 5 | 618 | project(ProjectMilestone/PaymentPlan), acceptance | 无 | 依据验收/里程碑自动生成开票的服务（base/creation/validation/notifications/main） |
| invoice_service.py | sales | 1 | 15 | 无 | 无 | 发票服务存根（仅生成发票代码，stub 实现） |
| issue_cost_service.py | cost-finance | 1 | 112 | project(ProjectCost), performance-hr(Timesheet) | 无 | 问题成本关联（把工时/项目成本归集到 issue） |
| issue_statistics_service.py | project | 1 | 274 | 无 | 无 | 问题统计（状态/严重度/优先级/类型分布，基于 SyncStatisticsService） |
| itr_analytics_service.py | aftersales | 1 | 423 | 无 | 疑似(仅测试引用；itr_service.py 为活跃 ITR 服务) | 服务工单解决时长分析等，疑为旧分析模块 |
| itr_service.py | aftersales | 1 | 505 | project(Issue), acceptance | 无 | ITR/服务工单核心服务（工单时间线、SLA、满意度） |
| job_duty_task_service.py | performance-hr | 1 | 193 | 无 | 疑似(仅测试引用，无运行时使用) | 岗位职责模板到期自动生成待办任务 |
| kit_rate/ | inventory-kitting | 1 | 608 | 无 | 无 | 齐套率服务 KitRateService |
| kit_rate_statistics_service.py | inventory-kitting | 1 | 205 | project(Project) | 无 | 齐套率统计（按项目 BOM 计算齐套情况） |
| kitting_optimization_service.py | inventory-kitting | 1 | 1404 | bom-material(Material), procurement | 无 | 齐套优化：替代料/加急/库存事务的大型优化服务 |
| knowledge/ | strategy-pmo | 4 | 1125 | ecn, project | 无 | 知识自动沉淀：从 ECN/Issue/项目/评审提取，最佳实践归纳 + 踩坑预警 + 搜索 |
| knowledge_auto_identification_service.py | aftersales | 1 | 318 | performance-hr(engineer_performance) | 无 | 从服务工单自动识别知识点（ServiceTicket→KnowledgeBase） |
| knowledge_contribution_service.py | performance-hr | 1 | 360 | 无 | 无 | 工程师知识贡献记录服务（计入 engineer_performance） |
| knowledge_extraction_service.py | aftersales | 1 | 236 | project(SolutionTemplate) | 无 | 从服务工单抽取知识条目（service.KnowledgeBase） |
| lead_priority_scoring/ | sales | 8 | 696 | 无 | 无 | 销售线索/商机优先级评分引擎（多 Mixin 组合） |
| loss_deep_analysis_service.py | sales | 1 | 478 | project(Project), performance-hr(Timesheet), cost-finance(hourly_rate_service) | 无 | 丢单深度分析（丢单原因、投入成本核算） |
| machine_custom/ | project | 1 | 417 | bom-material, aftersales(服务历史) | 无 | 机台定制服务：机台进度/BOM/文档/服务历史 |
| machine_service.py | project | 1 | 286 | 无 | 无 | 机台管理服务（机台编码生成、CRUD，Machine 属 project 模型） |
| manager_evaluation_service.py | performance-hr | 1 | 398 | 无 | 无 | 部门经理绩效评价服务 |
| manager_performance/ | performance-hr | 1 | 468 | 无 | 无 | 经理绩效服务 ManagerPerformanceService |
| margin_permission_service.py | cost-finance | 1 | 254 | platform-auth(User) | 疑似(仅测试引用，无运行时使用) | 项目毛利可见性权限（角色→可见级别） |
| material/ | bom-material | 1 | 157 | 无 | 无 | BOMService（BOM 查询，被 bom/bom_approve 端点使用） |
| material_category_service.py | bom-material | 1 | 49 | 无 | 无 | 物料分类 CRUD（BaseService） |
| material_procurement_optimization_service.py | procurement | 1 | 744 | ecn(Ecn/EcnAffectedMaterial), bom-material, inventory-kitting | 无 | 物料采购优化（结合 ECN/库存/缺料给采购建议） |
| material_progress_service.py | procurement | 1 | 398 | bom-material, project, (vendor) | 无 | 物料到货进度跟踪（PO/供应商/订阅） |
| material_service.py | bom-material | 1 | 105 | 无 | 无 | 物料主数据 CRUD（BaseService） |
| material_transfer_service.py | inventory-kitting | 1 | 532 | project(Project), shortage | 疑似(仅测试+scripts/import_services_batch2 引用，无运行时使用) | 物料调拨服务（项目间库存调拨、来源建议、事务） |
| meeting_report_docx_service.py | strategy-pmo | 1 | 223 | 无 | 无 | 经营节奏会议报告 Word 生成（渲染 meeting_report_helpers 结构化数据） |
| meeting_report_helpers.py | strategy-pmo | 1 | 415 | 无 | 无 | 经营节奏会议报告数据聚合（management_rhythm/ActionItem） |
| metric_calculation_service.py | strategy-pmo | 1 | 398 | acceptance, ecn, project(Issue) | 无 | 经营节奏指标计算服务（management_rhythm 指标） |
| milestone_service.py | project | 1 | 62 | 无 | 疑似(仅测试+scripts 引用；活跃里程碑逻辑为 app.services.project.ProjectMilestoneService) | 里程碑 CRUD（BaseService），疑为旧平铺版被 project 包取代 |

## 异常发现

**死代码群（仅测试/脚本引用，运行时无 endpoint/service 使用）：**
- `inventory_analysis_service.py`、`itr_analytics_service.py`、`job_duty_task_service.py`、`margin_permission_service.py`、`material_transfer_service.py`、`milestone_service.py`、`database/query_optimizer.py`、`document_file_lifecycle.py`（后者另有运维脚本引用）。这些均只被 `tests/` 或 `scripts/import_services_batch2.py`、`scripts/performance_benchmark.py`、`scripts/scan_project_document_orphans.py` 引用。

**向后兼容 re-export 尸体（真实实现已迁入子包，端点/调度直接指向新路径，旧顶层 shim 无引用）：**
- `dashboard_adapter.py` → 真实实现 `dashboard/dashboard_adapter.py`
- `ecn_auto_assign_service.py` → 真实实现 `ecn/ecn_auto_assign_service.py`
- `ecn_scheduler.py` → 真实实现 `ecn/ecn_scheduler.py`
（`inventory_management_service.py`、`ecn_cost_impact_service/`、`dashboard_adapters/` 也是兼容层，但仍有活跃引用者，非死代码。）

**并存/重复实现（需判定活体）：**
- `inventory_analysis_service.py`（顶层，疑似死）vs `inventory/analysis_service.py`（活跃，inventory 包内）。
- `milestone_service.py`（顶层 `MilestoneService`，疑似死）vs `app.services.project.ProjectMilestoneService`（端点实际使用）；另有 `sales.contract_milestone_service.ContractMilestoneService` 为合同里程碑，功能不同不冲突。
- `data_scope/` 内 `data_scope_service.py` 与 `data_scope_service_enhanced.py` 并存（`_enhanced` 并存版本，需确认哪个是活体）。
- `itr_analytics_service.py`（疑似死）与 `itr_service.py`（活跃）职责重叠于 ITR 分析。

**放错位置/域归属存疑：**
- `machine_service.py` / `machine_custom/` 处理"机台"，Machine 模型挂在 `app.models.project`，故归 project；但机台定制含 BOM/服务历史，实际横跨 bom-material 与 aftersales。
- 顶层 `knowledge_extraction_service.py` / `knowledge_auto_identification_service.py`（基于 aftersales 的 ServiceTicket 知识）与子包 `knowledge/`（基于 ECN/项目/评审的 strategy-pmo 知识沉淀）为两套不同"知识"实现，命名相近易混淆，分属 aftersales 与 strategy-pmo。
- `dashboard/` 包内含 `dashboard_adapter.py` 与顶层同名 `dashboard_adapter.py` 两处，仅包内为活体。

多租户 tenant_id 检查不适用（本范围为 services，无表定义）。