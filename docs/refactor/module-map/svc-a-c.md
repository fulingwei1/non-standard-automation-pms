# 归域扫描清单：`app/services` 从 `acceptance/` 到 `customer_service.py`

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|---|---|---|---|---|---|---|
| acceptance/ | acceptance | 3 | 562 | sales(开票触发) | 无 | 验收单服务：验收完成后自动触发开票，含报告编号/内容生成工具 |
| acceptance_approval/ | acceptance | 2 | 453 | — | 无 | 验收单审批桥接（对接 approval_engine），业务专属审批归 acceptance |
| acceptance_completion_service.py | acceptance | 1 | 345 | sales(invoice_auto_service)、performance-hr(bonus)、project(progress/data_flow/status_transition) | 无 | 验收完成收尾编排：触发开票、奖金、进度回填、状态流转 |
| acceptance_report_service.py | acceptance | 1 | 175 | — | 无 | 验收报告 PDF 生成、版本号与编号、落盘 |
| account_lockout_service.py | platform-auth | 1 | 549 | — | 无 | 账户锁定/暴力破解防护：登录失败计数、IP 黑名单、解锁（Redis+DB） |
| advantage_product_import_service.py | presale | 1 | 136 | — | 无 | 优势/竞品产品库 Excel 导入（供售前方案与线索匹配用） |
| ai_assessment_service.py | presale | 1 | 221 | — | 无 | 需求 AI 分析（通义千问）：需求评估+相似度，被 sales/assessments 端点调用 |
| ai_client_service.py | platform-ai | 1 | 727 | — | 无 | 通用 AI 客户端：OpenAI/Kimi/GLM-5，含 mock、embedding、图像分析、工具调用 |
| ai_emotion_service.py | presale | 1 | 660 | — | 无 | 售前情绪分析：情感/意向/流失预警+跟进提醒 |
| ai_feedback_service.py | platform-ai | 1 | 88 | — | 无 | AI 产出采纳/驳回反馈记录与采纳率统计 |
| ai_job_service.py | platform-ai | 1 | 313 | presale(三档报价/方案生成 handler) | 无 | AI 后台任务框架：进程内线程池+DB 状态跟踪，注册业务 handler |
| ai_planning/ | project | 6 | 2044 | — | 无 | AI 项目规划：WBS 分解、计划生成、资源/排期优化（GLM 驱动） |
| ai_quote_calibration_service.py | presale | 1 | 101 | sales(Contract、contract.status_service) | 无 | 三档 AI 报价 vs 成交合同金额定期勾稽对账 |
| ai_service.py | platform-ai | 1 | 226 | — | 疑似(仅 tests 引用，生产无导入，功能被 ai_client_service 取代) | 旧版 Kimi AI 服务类 |
| ai_structured_output.py | platform-ai | 1 | 49 | — | 无 | LLM 返回 JSON 的尽力解析工具函数 |
| alert/ | platform-notify | 18 | 4257 | — | 无 | 通用告警引擎：规则引擎、异常事件、升级/订阅/趋势/效率、里程碑告警、微信/PDF 输出 |
| approval_engine/ | platform-approval | 40 | 10236 | (adapters 桥接各业务) | 部分(见异常) | 统一审批引擎：workflow 编排、条件路由、执行、通知、各业务 adapter |
| approval_workflow_service.py | platform-approval | 1 | 296 | — | 无 | 审批工作流门面：启动/审批/驳回/撤回，封装 ApprovalEngineService |
| assembly_attr_recommender.py | inventory-kitting | 1 | 361 | — | 无 | BOM 装配属性智能推荐（历史/分类/关键词/供应商多级规则） |
| assembly_kit_optimizer.py | inventory-kitting | 1 | 335 | — | 无 | 齐套分析优化建议：预计到货日优化、加急/替代/优先级建议 |
| assembly_kit_service.py | inventory-kitting | 1 | 952 | procurement(purchase/in_transit)、bom-material(material)、project | 无 | 装配工艺齐套分析主服务：阶段套件率、物料分配、到货交期 |
| assembly_kit_service_enhanced.py | inventory-kitting | 1 | 377 | procurement(purchase) | 无 | 齐套增强版：春节影响、承诺交期、相似物料历史交期（继承主服务） |
| backup_service.py | platform-infra | 1 | 513 | — | 无 | 数据库/文件备份：创建/校验/恢复/清理/统计（SQLite） |
| base_approval_workflow.py | platform-approval | 1 | 366 | — | 无 | 审批工作流抽象基类，供采购/外协/合同/ECN/验收/报价继承 |
| best_practice_service.py | strategy-pmo | 1 | 550 | procurement(vendor)、bom-material(material)、project | 无 | 行业最佳实践规则：ABC 物料分级、供应商重分类、缺料升级、齐套目标 |
| best_practices/ | strategy-pmo | 2 | 336 | — | 无 | 最佳实践条目 CRUD/查询业务逻辑 |
| bom_attributes/ | bom-material | 2 | 388 | — | 无 | BOM 装配属性服务（AssemblyStage/Template 关联维护） |
| bom_service.py | bom-material | 1 | 130 | — | 无 | BOM 主数据 CRUD（BaseService 派生） |
| bonus/ | performance-hr | 14 | 2489 | presale/sales/project(各类奖金触发源) | 无 | 奖金计算引擎：验收/绩效/售前/项目/销售/团队奖金分配 |
| budget_alert_service.py | cost-finance | 1 | 892 | procurement(purchase/outsourcing)、project | 无 | 预算执行预警：执行率监控、软拦截、告警生成 |
| budget_analysis_service.py | cost-finance | 1 | 246 | project | 无 | 预算 vs 实际对比与趋势分析 |
| budget_execution_check_service.py | cost-finance | 1 | 232 | project | 无 | 预算执行检查：告警级别判定、告警记录创建（函数式） |
| business_rules.py | 待定 | 1 | 664 | — | 疑似(仅 tests 引用) | 跨域纯函数业务规则库（毛利/套件率/SPI/付款节点/FAT/缺料），不归单一业务域 |
| business_support_reports/ | sales | 2 | 402 | — | 无 | 商务支持销售报表（日/周/月报）业务逻辑 |
| business_support_utils/ | sales | 2 | 401 | — | 无 | 商务支持订单工具：编码生成、通知、序列化/响应转换 |
| cache/ | platform-infra | 4 | 991 | — | 无 | 缓存层：Redis 缓存、业务缓存、销售模块专用缓存 |
| cache_service.py | platform-infra | 1 | 330 | — | 无 | 通用缓存服务（Redis+内存降级），含项目缓存便捷方法 |
| channel_handlers/ | platform-notify | 1 | 98 | — | 无 | 通知渠道处理器基类与渠道定义（抽象基础，被 notification 复用） |
| collaboration_rating/ | performance-hr | 5 | 691 | — | 无 | 跨部门协作评价服务（含选择器/统计/评分子模块） |
| collaboration_service.py | performance-hr | 1 | 283 | — | 疑似(与 collaboration_rating/ 并存，同用 engineer_performance.CollaborationRating) | 跨部门协作评价服务（另一实现，含协作矩阵/待评列表） |
| comparison_calculation_service.py | strategy-pmo | 1 | 261 | analytics(metric_calculation_service) | 无 | 经营节奏指标环比/同比/年度同比计算 |
| conflict_mediation_service.py | performance-hr | 1 | 521 | project(ProjectStageResourcePlan) | 无 | 资源冲突自动调解：替代人选、排期调整、负荷均衡建议 |
| contract_approval/ | sales | 2 | 565 | — | 无 | 合同审批业务桥接（提交/待办/审批/批量/撤回/历史），业务专属审批归 sales |
| cost/ | cost-finance | 14 | 5725 | procurement/project(成本归集来源) | 无 | 成本管理套件：归集/看板/预警/预测/超支/分摊/工时成本/Facade |
| cost_collection_service.py | cost-finance | 1 | 8 | — | 疑似(兼容 shim，无人导入顶层路径) | 转发到 cost.cost_collection_service 的旧路径 shim |
| cost_forecast_service.py | cost-finance | 1 | 14 | — | 疑似(兼容 shim，无人导入顶层路径) | 转发到 cost.cost_forecast_service 的旧路径 shim |
| cost_prediction_service.py | cost-finance | 1 | 16 | — | 疑似(兼容 shim，无人导入顶层路径) | 转发到 cost.cost_prediction_service 的旧路径 shim |
| culture_wall_service.py | performance-hr | 1 | 300 | — | 无 | 文化墙：内容/个人目标/已读记录/通知 |
| customer_360_service.py | sales | 1 | 212 | project、aftersales(service) | 无 | 客户 360 视图聚合（订单/合同/报价/发票/项目/服务工单/满意度） |
| customer_service.py | sales | 1 | 120 | project(Customer 模型) | 无 | 客户主数据 CRUD，删除前校验关联项目、更新后同步到项目/合同 |
| change_impact_ai_service.py | ecn | 1 | 653 | presale(glm_service) | 疑似(仅 tests 引用，生产走 project_change_impact_service) | GLM-5 变更影响 AI 分析（连锁反应/依赖深度/风险） |
| change_impact_analysis_service.py | ecn | 1 | 256 | — | 疑似(仅 tests 引用) | 变更影响分析（进度/成本/资源/关联项目），函数式 |
| change_response_suggestion_service.py | ecn | 1 | 223 | — | 疑似(仅 tests 引用) | 变更应对方案生成（批准/修改/缓解三类建议） |

## 异常发现

**死代码群（仅被 tests 引用或无引用，生产链路无导入）：**
- `ai_service.py` — 旧 Kimi 服务，功能已被 `ai_client_service.py` 取代，仅测试导入。
- `business_rules.py` — 664 行纯规则库，仅 4 个测试文件导入，无任何生产 service/endpoint 使用。
- ECN 变更三件套 `change_impact_ai_service.py` / `change_impact_analysis_service.py` / `change_response_suggestion_service.py` — 均仅 tests 引用；生产变更影响端点 (`app/api/v1/endpoints/projects/change_impact.py`) 实际用的是 `project_change_impact_service`（范围外）。三者疑为被取代的平行实现。

**兼容 shim 尸体（顶层薄转发层，全项目均改用 `app.services.cost.*` 子包路径，无人再走顶层）：**
- `cost_collection_service.py`(8行)、`cost_forecast_service.py`(14行)、`cost_prediction_service.py`(16行) — 可安全删除。

**重复/并存实现：**
- 跨部门协作评价存在两套：`collaboration_service.py`（顶层）与 `collaboration_rating/`（子包），二者都基于 `app.models.engineer_performance.CollaborationRating`，功能重叠，重构时需合并（建议保留结构更清晰的 `collaboration_rating/`）。
- 最佳实践存在两处：`best_practice_service.py`（ABC 分级/供应商重分类等操作规则）与 `best_practices/`（实践条目 CRUD），职责不同但命名易混，建议归并到 strategy-pmo 下明确区分。
- `approval_engine/workflow_engine.py` 头部带 `[DEPRECATED]` 且运行时 `warnings.warn`，为保留测试兼容的旧引擎，与 `approval_engine/engine/` 新实现并存，属计划删除的尸体（注意：`app/common/workflow/engine.py` 的 `workflow_engine` 是另一套状态机，非本文件）。

**放错位置/归域存疑：**
- `business_rules.py` 跨毛利/套件率/SPI/付款/FAT/缺料多域，标为 `待定`；若保留应下沉为 `platform` 级共享规则库而非停留在 services 顶层。
- `alert/milestone_alert_service.py` 位于通用告警引擎包内但强项目语义（里程碑到期预警），拆分时需注意它对 project 域的耦合。

**多租户检查：** 本次扫描范围为 services 层，未涉及 models 表定义，`tenant_id` 字段核查不适用（N/A）。