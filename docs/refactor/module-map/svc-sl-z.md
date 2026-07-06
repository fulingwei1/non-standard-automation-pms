以下为归域清单（范围：`app/services` 下 `sla_service.py` 至 `work_log_service.py`）。

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|---|---|---|---|---|---|---|
| sla_service.py | aftersales | 1 | 281 | 无（models.service/sla 同域） | 无 | SLA 策略匹配、SLA 监控创建/更新、超时预警扫描 |
| solution_credit_service.py | presale | 1 | 444 | 无 | 无 | 方案生成积分：余额查询/扣费/退款/管理员充值，供 solution_credits 端点 |
| spec_match_service.py | engineering | 1 | 198 | 依赖 procurement(PurchaseOrderItem)、bom-material(BomItem) 模型 | 无 | 校验采购项/BOM 项是否满足技术规格要求，产出匹配统计 |
| stage_advance_service.py | project | 1 | 276 | → cost-finance(cost_review_service)、production(生成安装派工单) | 无 | 项目阶段推进：门禁校验、阶段/状态更新、生成成本复盘报告 |
| stage_approval_bridge.py | project | 1 | 352 | 依赖 platform-approval 模型 | 疑似(app 内无引用，仅 tests) | 阶段→审批实例桥接、判断审批是否放行；业务专属审批桥归 project |
| stage_transition_checks.py | project | 1 | 239 | → sales(contract.status_service)，依赖 acceptance/sales/material 模型 | 无 | S3→S9 各阶段流转门禁检查（合同/BOM/验收/付款条件） |
| status_transition_service.py | project | 1 | 388 | 内部委派 status_handlers（同域）、stage_transition_checks（同域） | 无 | 项目状态机：合同/BOM/缺料/FAT/SAT/验收等事件驱动的自动状态与阶段跃迁 |
| status_update_service.py | project | 1 | 312 | 无 | 无 | 通用状态更新引擎（值校验+转换规则+变更历史+联动），服务于项目状态体系 |
| stock_count_service.py | inventory-kitting | 1 | 558 | → platform(data_scope)；inventory_management_service 同域 | 无 | 库存盘点任务创建/执行/差异审批/调整/历史分析 |
| supplier_performance_evaluator.py | procurement | 1 | 550 | 无 | 无 | 供应商绩效评估：交期/质量/价格/响应四维打分+评级+排名+批量评估 |
| task_progress_service.py | project | 1 | 10 | 无 | 疑似(纯 re-export，规范实现在 progress_service.py) | 向后兼容包装器，转发 progress_service |
| team_generation_service.py | project | 1 | 648 | 依赖 strategy-pmo(pmo)、engineer_capacity 模型 | 无 | 项目团队方案自动生成：角色识别+工程师匹配+工时估算+负载均衡 |
| technical_assessment_service.py | presale | 1 | 1167 | 无 | 无 | 售前技术评估：评分规则计算、相似案例匹配、评估结果生成 |
| template_recommendation_service.py | project | 1 | 317 | 无 | 无 | 项目模板推荐：客户/金额/历史模式多维打分 |
| template_report_data_service.py | analytics | 1 | 232 | → analytics(template_report.core 同域) | 疑似(app 内无引用，仅 tests) | 为模板报表构建渲染上下文（指标/分节/图表） |
| template_report_service.py | analytics | 1 | 40 | → analytics(template_report.core 同域) | 无 | 模板报表生成薄封装，被 report_framework 适配器使用 |
| tenant_service.py | platform-auth | 1 | 343 | 无 | 无 | 租户 CRUD、租户编码生成、登录/配额检查、租户初始化与统计 |
| ticket_assignment_service.py | aftersales | 1 | 154 | 依赖 project(ProjectMember) 模型 | 无 | 为服务工单查可指派的项目成员、查工单关联项目 |
| timesheet_records.py | performance-hr | 1 | 267 | 无 | 无 | 工时记录列表/创建/批量/详情/更新/删除（活跃版，被 timesheet/records 端点使用） |
| two_factor_service.py | platform-auth | 1 | 410 | 无 | 无 | 2FA：TOTP 密钥/二维码、验证、启用/停用、备份码管理 |
| unified_notification_service.py | platform-notify | 1 | 4 | → platform-notify(notification 子包) | 疑似(纯 re-export 兼容层) | 向后兼容导入路径，转发 notification.unified_notification_service |
| urgent_purchase_from_shortage_service.py | procurement | 1 | 461 | 依赖 inventory-kitting(ShortageReport)、material 模型 | 无 | 由缺料预警/缺料报告自动生成紧急采购申请，含自动触发 |
| user_import_service.py | platform-auth | 1 | 381 | 无 | 无 | Excel/CSV 批量导入用户、校验、角色创建、生成模板 |
| user_sync_service.py | platform-auth | 1 | 333 | → platform(session_service)，依赖 organization(Employee) | 无 | 员工→用户同步、按岗位配角色、密码重置、启停用 |
| user_workload_service.py | performance-hr | 1 | 200 | 依赖 strategy-pmo(PmoResourceAllocation)、project(Task) | 无 | 计算用户工作负载：工作日/任务工时/项目与每日负载 |
| vendor_service.py | procurement | 1 | 97 | 无（BaseService） | 无 | 供应商 Vendor 的 CRUD 与列表（BaseService 泛型实现） |
| work_log_auto_generator.py | performance-hr | 1 | 267 | 依赖 project、timesheet 模型 | 无 | 从工时记录自动生成工作日志、批量/昨日生成 |
| work_log_service.py | performance-hr | 1 | 401 | 依赖 project、timesheet 模型 | 无 | 工作日志 CRUD、@提及、关联进度、双向同步工时 |
| staff_matching/ | performance-hr | 5 | 1192 | → platform-ai(ai_client_service) | 无 | AI 驱动 6 维加权人员智能匹配（候选管理/画像聚合/打分/匹配引擎） |
| stage_instance/ | project | 7 | 1150 | 无 | 无 | 阶段实例：初始化/节点操作/流转/进度查询/调整，多 Mixin 组合 |
| stage_template/ | project | 8 | 951 | 无 | 无 | 阶段模板：模板/节点/阶段 CRUD、默认模板、导入导出、变更日志 |
| statistics/ | analytics | 1 | 168 | 无 | 无 | 同步统计服务基类与聚合协议（供 timesheet/cost/performance 复用） |
| status_handlers/ | project | 5 | 1199 | → sales(presale_quote_context)；回指 status_transition_service（同域） | 无 | 按领域拆分的状态事件处理器（合同/物料/验收/ECN/里程碑），延迟导入避循环 |
| strategy/ | strategy-pmo | 25 | 5584 | 无 | 无 | 战略管理套件：战略/CSF/KPI 采集与快照/年度重点/分解树/复盘/健康度/同比 |
| team_performance/ | performance-hr | 1 | 564 | 无 | 无 | 团队绩效服务（从 performance/team 端点提取），按部门/周期汇总 |
| template_report/ | analytics | 6 | 754 | → cost-finance(report_labor_cost)、project(project_status_normalization) | 无 | 模板报表核心：公司/部门/项目/分析等多类报表 Mixin |
| timesheet/ | performance-hr | 18 | 6257 | → cost-finance(hourly_rate_service、labor_cost_service)、platform-notify(notification_dispatcher) | 部分疑似(见异常) | 工时聚合/加班/预测/质量/同步 + 提醒扫描器；含重复的 records 子包 |
| unified_import/ | platform-file | 7 | 899 | → project(project_import)、performance-hr(employee/hr_profile import)、bom-material(bom)、procurement(material) | 无 | 统一导入引擎：BOM/物料/任务/工时/用户等分派到各 importer |
| views/ | project | 4 | 232 | 只读跨域读取 aftersales/delivery/procurement/production 数据 | 无 | 项目关联只读视图（交付/采购/生产/售后聚合概览） |
| win_rate_prediction_service/ | sales | 7 | 1320 | 依赖 sales(presale_ai_win_rate)、project 模型 | 疑似(app 内无引用，仅 tests；端点用本地 utils 而非本服务) | 中标率预测：因子计算/历史/分析/AI 预测，聚合含 Old 兼容类 |
| work_log_ai/ | performance-hr | 5 | 583 | → platform-ai | 疑似(app 内完全无引用，仅 tests) | 工作日志 AI 分析：prompt 构建/规则引擎/项目匹配/AI 分析 |

## 异常发现

**死代码群（仅被测试引用，实际路由/调用链中无引用）：**
- `stage_approval_bridge.py`（`StageApprovalBridge`）：app 代码零引用；schemas 里的 `StageApprovalBridgeEntry` 是同名无关类。
- `template_report_data_service.py`（`TemplateReportDataService`）：app 代码零引用。
- `win_rate_prediction_service/`（整个包）：app 代码零引用；活跃端点 `presale_analytics/win_rate.py` 用的是本地 `.utils`，未使用本服务。
- `work_log_ai/`（整个包）：app 代码彻底零引用，连 `work_log_service.py` 也未调用。

**重复/并存实现：**
- `TimesheetRecordsService` 存在两份：顶层 `timesheet_records.py`（267 行，活跃，被 `endpoints/timesheet/records.py` 使用）与子包 `timesheet/records/service.py`（460 行）。后者仅被非生效聚合器 `api_medium.py` 引用（`main.py` 实际加载的是 `app/api/v1/api.py`），**`timesheet/records/` 子包疑似死代码/尸体版本**。
- `timesheet/reminder/`（单数，2055 行，完整实现，被 scheduled_tasks 使用）与 `timesheet/reminders/`（复数，仅 service.py 薄封装，被活跃端点 `timesheet_reminders` 使用）并存；复数版仅转调单数版 `TimesheetReminderManager`，属包装层，两者均活。

**纯 re-export 兼容层（非死代码但为迁移残留）：**
- `task_progress_service.py` → 转发 `progress_service.py`。
- `unified_notification_service.py` → 转发 `notification.unified_notification_service`。

**归域需注意：**
- `status_update_service.py` docstring 自称"通用状态更新服务"，实为跨实体状态机引擎，此处随项目状态体系归 `project`，重构时可考虑下沉 platform 层。
- `statistics/` 是统计基类（infra 性质），随其被 analytics/timesheet/cost 复用归 `analytics`，亦可视作 platform-infra。
- `views/` 为跨域只读聚合视图，虽读 aftersales/procurement/production 数据，主体属 project 工作台视图。

**多租户（tenant_id）：** 本范围为 services 层，未扫 models 表结构；顺带发现 `stock_count_service`、`supplier_performance_evaluator` 构造函数强制携带 `tenant_id`，而多数其他服务（sla/status/timesheet 等）未在服务层显式隔离租户，租户过滤依赖上游，重构时需统一。