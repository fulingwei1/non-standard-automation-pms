I have enough to compile the report.

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|---|---|---|---|---|---|---|
| app/services/node_task_service.py | project | 1 | 445 | 无（仅 project 域 stage_instance 模型） | 无 | 阶段节点下的子任务 CRUD/排序/开始完成跳过/进度统计，被 endpoints/node_tasks.py 使用 |
| app/services/notification_service.py | platform-notify | 1 | 420 | 无 | 无（compat facade，5 处 app 引用+89 tests） | 向后兼容门面，把旧 NotificationService 接口转调 notification/ 包的 UnifiedNotificationService |
| app/services/notification_utils.py | platform-notify | 1 | 4 | 无 | 无（compat 再导出，5 app 引用） | 旧导入路径的兼容 shim，`from notification.notification_utils import *` |
| app/services/payment_adjustment_service.py | sales | 1 | 429 | project(Project/ProjectMilestone/ProjectPaymentPlan) | 无 | 按里程碑自动/手动调整收款计划、记录调整历史并发通知 |
| app/services/payment_statistics_service.py | sales | 1 | 210 | 无 | 无（1 app 引用+12 tests） | 发票/开票统计：按月/客户/状态聚合金额、逾期金额计算（纯函数集） |
| app/services/pdf_content_builders.py | acceptance | 1 | 369 | 无 | 疑似(0 app 引用，仅 tests 33 + generate_test_stubs 脚本) | 构建验收单 PDF 各区块(基本信息/统计/结论/问题/签字/页脚)，无活跃调用方 |
| app/services/pdf_export_service.py | platform-file | 1 | 452 | sales(Quote/Contract/Invoice 模型) | 无 | 通用 PDF 导出：报价/合同/发票转 PDF + create_pdf_response |
| app/services/pdf_styles.py | platform-file | 1 | 188 | 无 | 无（2 app 引用） | reportlab 通用 PDF 样式/表格样式定义 |
| app/services/performance_analysis_service.py | performance-hr | 1 | 688 | project(Project/ProjectMilestone/StatusLog)、alert(健康快照) | 无 | 基于项目健康/预算/进度/风险打分的 PM 绩效排名、团队效率、改进跟踪 |
| app/services/performance_feedback_service.py | performance-hr | 1 | 448 | engineering(engineer_performance 模型) | 无 | 工程师绩效反馈：维度趋势、能力变化识别、个性化反馈文案生成 |
| app/services/performance_integration_service.py | performance-hr | 1 | 249 | 无（qualification_service 同域 HR） | 无 | 绩效分与资质分融合计算，产出综合绩效分 |
| app/services/performance_stats_service.py | performance-hr | 1 | 258 | project、cost-finance(timesheet) | 疑似(0 app 引用，仅 3 tests；endpoints 里的 get_performance_stats 是同名路由函数非本类) | 用户/部门绩效统计、技能专长分析 |
| app/services/performance_trend_service.py | performance-hr | 1 | 281 | 无 | 无 | 工程师/部门绩效趋势、能力变化识别、部门对比 |
| app/services/permission_audit_service.py | platform-auth | 1 | 16 | 无 | 无（compat 再导出，2 app 引用） | 旧路径 shim，转导出 permission_management/permission_audit_service |
| app/services/permission_cache_service.py | platform-auth | 1 | 50 | 无 | 无（compat，3 app 引用+30 tests） | 兼容旧导入路径的权限缓存服务子类，允许旧测试 patch CacheService |
| app/services/permission_service.py | platform-auth | 1 | 19 | 无 | 无（compat 再导出，51 tests） | 旧路径 shim，转导出 permission_management/permission_service |
| app/services/pipeline_accountability_service.py | sales | 1 | 323 | project(Project)、cost-finance(hourly_rate_service/timesheet) | 无 | 全链条断链问责：按阶段/人/部门归因断链成本影响 |
| app/services/pipeline_break_analysis_service.py | sales | 1 | 530 | project(合同→项目断链检测引用 Project) | 无 | 售前→回款全链条断链检测/原因/模式/预警，含数据权限 scope |
| app/services/pipeline_health_service.py | sales | 1 | 411 | project(Project) | 无 | 线索/商机/报价/合同/回款各环节及整链健康度计算 |
| app/services/pm_involvement_service.py | presale | 1 | 378 | project(Project)、sales(Lead/Opportunity) | 无 | 基于售前工单判断 PM 介入时机、找相似项目/标准方案、生成通知 |
| app/services/notification/ | platform-notify | 19 | 2504 | 无 | 无（28 处外部引用） | 通知系统：UnifiedNotificationService 主入口 + dispatcher/queue + channels(薄适配) + handlers(旧版 SMTP/微信具体实现，经 unified_adapter 桥接) |
| app/services/otd/ | project | 8 | 2817 | ecn、acceptance、aftersales、procurement(purchase)、cost-finance(profit_analysis/budget_alert)、engineering(technical_review)、platform-ai(ai_client)、platform-file(import_export)、analytics(dashboard) | 无（19 app 引用） | OTD 交期编排层：每日全景扫描 + 7 核心指标 + 阈值/趋势/对比；margin_export 为毛利率导出（偏 cost-finance） |
| app/services/outsourcing_workflow/ | procurement | 2 | 84 | platform-approval(BaseApprovalWorkflow)、cost-finance(cost_collection) | 无（1 app 引用） | 外协审批工作流：继承通用审批引擎，定义外协单业务配置 |
| app/services/performance_collector/ | performance-hr | 11 | 1542 | engineering(design/engineer_performance)、ecn、bom-material(material)、project(progress/project_evaluation)、performance-hr(work_log) | 无（2 app 引用） | 工程师绩效数据自动采集：从设计/ECN/BOM/知识/项目/工作日志各系统抽取并聚合评价数据 |
| app/services/performance_service/ | performance-hr | 6 | 672 | 无 | 无（4 app 引用） | 绩效管理核心：分数计算/评估/历史/角色，聚合于 __init__ 保持兼容 |
| app/services/permission_management/ | platform-auth | 5 | 1372 | 无 | 无（28 app 引用） | 权限管理主实现：CRUD/角色权限关联/用户权限查询/缓存/审计，多租户隔离 |
| app/services/pitfall/ | strategy-pmo | 2 | 205 | 无 | 无（1 app 引用） | 踩坑库：踩坑记录 CRUD 与搜索 |
| app/services/pmo_cockpit/ | strategy-pmo | 2 | 650 | project(project 模型/project_status_normalization)、platform-auth(organization/user) | 无（1 app 引用） | PMO 驾驶舱：驾驶舱/风险墙/周报/资源总览业务逻辑 |
| app/services/pmo_initiation/ | strategy-pmo | 2 | 998 | presale(PresaleSolution/Ticket)、sales(Contract/Opportunity/Quote/OpenItem/payment_plan)、project(Customer/Project/project_workspace) | 无（1 app 引用） | PMO 立项管理：立项单与售前方案/商机/合同/付款计划/项目工作台的打通 |

## 异常发现

- **死代码嫌疑（2 个顶层文件）**：
  - `pdf_content_builders.py`：0 处 app 引用，仅被 33 个 tests 和 `scripts/generate_test_stubs.py` 触及；验收单 PDF 区块构建器已无活跃调用方（对应的 acceptance_report/completion 服务均未引用）。
  - `performance_stats_service.py`：0 处 app 引用，仅 3 个 tests；注意 `app/api/v1/endpoints/presale/statistics.py` 里的 `get_performance_stats` 是同名路由函数，并非本类的使用者，易误判为"有引用"。

- **兼容 shim 群（4 个薄转发文件，非死代码但属重构可清理项）**：`notification_service.py`、`notification_utils.py`、`permission_audit_service.py`、`permission_cache_service.py`、`permission_service.py` 均为旧导入路径的向后兼容层，真实实现已迁至 `notification/` 与 `permission_management/` 子包。它们仍被大量 tests 依赖（notification_service 89、permission_service 51 等），迁移时需同步改测试。

- **notification 包内的双层并存实现（非死代码，易误判）**：`notification/channels/`（薄适配器，被 UnifiedNotificationService 使用）与 `notification/handlers/`（旧版 SMTP/企业微信 API 的具体实现，经 `handlers/unified_adapter.py` 与 `channels/*_handler.py` 桥接）并存。两者都活跃，channels 委托给 handlers，勿当重复实现删除。

- **放错位置的文件**：`otd/margin_export_service.py`（毛利率 Dashboard 导出）业务上属 cost-finance，却置于 project 域的 OTD 编排包内。

- **跨域耦合最重的编排点**：`otd/` 子包横跨 ecn/acceptance/aftersales/procurement/cost-finance/engineering/analytics/platform-ai 等近 10 个域，是重构拆分时的高风险交汇点；`pmo_initiation/` 同时依赖 presale+sales+project 三业务域。

- **多租户检查**：本范围为 services 层，未定义数据表；无 tenant_id 相关发现（不适用）。