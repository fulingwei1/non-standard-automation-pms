Based on my analysis, here is the module map for the assigned scope.

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|---|---|---|---|---|---|---|
| ppt_generator/ | platform-file | 11 | 613 | 无 | 疑似(仅 tests + scripts/create_full_ppt_refactored.py 引用，运行时/端点无引用；含 builders/ 薄再导出层) | python-pptx 生成项目介绍 PPT 的通用文档能力，含 base/content/table 三种 slide builder + compat 依赖兜底 |
| presale/ | presale | 23 | 9020 | sales(presale_ai_quotation/orchestrator 经 bridge 回填商机需求) | 无 | 售前 AI 全家桶：智能体编排、弹药库检索、竞争分析、销售教练、CPQ 报价、需求澄清/桥接、验厂资料包、方案 docx/html 导出、风险标签库；大量依赖 platform-ai(ai_client_service/ai_planning glm) |
| presale_ai_service.py | presale | 1 | 11 | 无 | 疑似(纯兼容再导出 presale.presale_ai_service，全仓无任何 import 者) | 向后兼容 shim，实际活跃代码走 presale 包内同名模块 |
| presale_assessment_completion.py | presale | 1 | 122 | sales(TechnicalAssessment 模型) | 无 | 售前工单与技术评估闭环共享逻辑，回写评估完成状态 |
| preset_stage_templates/ | project | 17 | 2854 | 无 | 无 | 项目阶段模板静态数据（完整生命周期/标准/快速/重复 + execution/standard 子模板），供项目建阶段初始化用 |
| procurement_analysis/ | procurement | 7 | 715 | 无 | 无 | 采购分析：成本趋势/交付绩效/价格/质量/请购效率五分析器 + 聚合门面 ProcurementAnalysisService 单例 |
| production/ | production | 8 | 4131 | 无 | 无 | 生产域端点业务逻辑：生产计划、工单派工+状态机、工人/车间、生产异常、生产质检（含 worker/exception 兼容服务） |
| production_progress_service.py | production | 1 | 686 | 无 | 无 | 生产进度跟踪：偏差计算引擎、瓶颈工位识别、进度预警规则引擎 |
| production_schedule_service.py | production | 1 | 1687 | 无 | 无 | 生产排程优化：资源冲突检测、排程调整日志、工人技能匹配 |
| profit_analysis_service.py | cost-finance | 1 | 876 | analytics(dashboard.margin_level_service) | 无 | 项目利润优化分析：毛利实时/目标对比、成本优化建议、高低利润根因 |
| progress_integration_service.py | project | 1 | 490 | inventory-kitting(shortage), ecn, acceptance | 无 | 进度跟踪与缺料/ECN/验收模块的联动服务 |
| progress_service.py | project | 1 | 956 | 无 | 无 | 统一进度服务（合并进度聚合/任务进度/自动化），保留旧函数签名兼容 |
| project/ | project | 11 | 3040 | cost-finance(cost_basis), performance-hr(timesheet/user_workload), analytics(dashboard) | 无 | 项目管理聚合服务（core/execution/resource/finance/analytics 5 核心 + milestone/machine/closure/cost_benchmark/risk），面向 /analytics 与项目主干 |
| project_change_impact_service.py | ecn | 1 | 552 | project(反向：评估/联动项目数据) | 无 | 项目-变更单联动：ECN 审批时评估变更对项目影响、执行后联动更新（即"变更影响分析"） |
| project_change_requests/ | project | 2 | 904 | 无(platform-approval/notify) | 无 | 项目级变更请求(ChangeRequest) CRUD 与审批/通知桥接 |
| project_contribution_service.py | project | 1 | 361 | performance-hr(bonus.project_bonus_service) | 无 | 项目贡献度计算：任务/工时/交付物指标聚合并关联奖金 |
| project_cost_aggregation_service.py | cost-finance | 1 | 221 | project(反向) | 无 | 批量聚合多项目成本，避免 N+1 查询 |
| project_cost_prediction/ | cost-finance | 3 | 1000 | 无 | 无 | 项目成本预测：GLM-5 AI 预测器 + EVM 计算，产出风险分析/优化建议 |
| project_crud/ | project | 2 | 390 | 无(data_scope/cache/stage_instance) | 无 | 项目核心 CRUD：列表筛选排序、创建更新删除、冗余字段维护、缓存管理 |
| project_data_flow_service.py | project | 1 | 461 | production, procurement, aftersales(各 views 概览) | 无 | 项目→生产/采购/交付/售后数据自动关联流转 |
| project_delivery_service.py | project | 1 | 637 | 无 | 无 | 项目交付排产计划 CRUD（长周期采购/机械设计/交付任务） |
| project_evaluation_service.py | project | 1 | 469 | 无 | 无 | 项目评价：维度评分、自动评分 |
| project_export_service.py | project | 1 | 314 | 无(platform-file: openpyxl) | 无 | 项目数据导出 Excel |
| project_import_service.py | project | 1 | 287 | 无(platform-file: import_export_engine) | 无 | 项目 Excel 导入 + 阶段初始化 |
| project_meeting_service.py | project | 1 | 215 | strategy-pmo(management_rhythm 会议模型) | 无 | 项目与战略会议(StrategicMeeting/行动项)的关联查询 |
| project_members/ | project | 2 | 388 | 无 | 无 | 项目成员管理：权限检查、成员增删、数据聚合 |
| project_performance/ | project | 2 | 468 | 无 | 无 | 项目绩效服务：权限检查、数据聚合、绩效报告生成 |
| project_relation_service.py | project | 1 | 117 | aftersales(after_sales_view) | 无 | 项目与生产/采购/交付/售后模块的关联查询（生产PO/交付计划）|
| project_relations_service.py | project | 1 | 555 | inventory-kitting(shortage.MaterialTransfer) | 疑似(全仓无 import 者，函数 get_material_transfer_relations 无调用方) | 项目关联关系服务（合并了已删的 relation_discovery），与 relation_service 并存 |
| project_report_auto/ | project | 4 | 1388 | cost-finance(cost_basis) | 无 | 项目周报/月报自动生成 + 推送（PDF/Excel 导出、干系人推送） |
| project_review_ai/ | project | 5 | 1310 | presale(knowledge_syncer 写 PresaleKnowledgeCase) | 无 | 项目复盘 AI：复盘报告生成、经验教训提取、历史对比、知识库同步 |
| project_risk/ | project | 3 | 1259 | 无 | 无 | 项目风险：自动风险识别(进度/成本/资源/质量)+风险 CRUD/升级 |
| project_solution_service.py | project | 1 | 254 | 无 | 无 | 解决方案库（基于 Issue/SolutionTemplate 的模板复用） |
| project_statistics_service.py | project | 1 | 525 | analytics(statistics.base) | 无 | 项目中心统一统计（SQL GROUP BY 收敛重复统计） |
| project_status_normalization.py | project | 1 | 165 | 无 | 无 | 项目生命周期状态规范化（S1-S9/STxx 与旧值 EXECUTING/COMPLETED 兼容映射），被 24 处引用的公共工具 |
| project_timeline_service.py | project | 1 | 192 | 无 | 无 | 项目时间线事件聚合（成本/文档/里程碑/状态日志） |
| project_workspace_service.py | project | 1 | 1703 | performance-hr(bonus), strategy-pmo(project_meeting), 读多域(presale/production/ecn/acceptance) | 无 | 项目工作空间聚合视图，跨域拉取待办/评估/BOM/工单等 |
| purchase/ | procurement | 3 | 417 | 无 | 无 | 采购管理服务（从 purchase.py 拆出）+ 采购单状态机 + 在途量共享助手 |
| purchase_intelligence/ | procurement | 2 | 638 | 无 | 疑似(活跃 api.py 未挂载；仅 api_lazy 非活跃变体引用一个不存在的端点文件；服务无 import 者) | 采购智能服务（供应商绩效评估驱动的智能采购） |
| purchase_order_from_bom_service.py | procurement | 1 | 503 | bom-material(BomHeader/Item/Material) | 无 | 从 BOM 生成采购订单，按供应商分组、过滤失效状态 |
| purchase_request_from_bom_service.py | procurement | 1 | 362 | bom-material(BomHeader/Item/Material) | 无 | 从 BOM 生成采购需求（请购），与上者高度相似 |
| purchase_suggestion_engine.py | procurement | 1 | 589 | inventory-kitting(缺料/安全库存) | 疑似(仅 tests + scripts/import_services_batch2 引用，运行时无引用) | 智能采购建议引擎：缺料/安全库存/历史消耗预测 + AI 荐供应商 |
| purchase_workflow/ | procurement | 2 | 74 | 无(platform-approval: base_approval_workflow) | 无 | 采购工作流薄封装，基于通用审批工作流基类 |
| qualification_service.py | performance-hr | 1 | 285 | 无 | 无 | 任职资格管理：认证、能力评估、晋升检查 |
| quality_risk_ai/ | production | 4 | 655 | 无 | 疑似(仅被同为死代码的 quality_risk_management 引用；test_recommendation_engine 为空 Stub) | 质量风险 AI：GLM-5 分析工作日志识别质量风险 + 关键词提取 + 测试推荐(stub) |
| quality_risk_management/ | production | 2 | 617 | production(quality_risk_ai 同域) | 疑似(全仓无 import 者；活跃 quality_risk 端点为逐级回退到空 APIRouter 的 shim) | 质量风险管理服务层（编排 quality_risk_ai），无活跃调用方 |
| quality_service.py | production | 1 | 717 | 无 | 无 | 质量管理：质检、SPC 分析、质量预警、返工/纠正措施 |
| quotation_pdf_service.py | presale | 1 | 370 | 无(platform-file: reportlab) | 无 | 报价单 PDF 生成（reportlab，缺依赖时降级） |
| quote_approval/ | presale | 2 | 567 | sales(quote_operation_audit) | 无 | 报价审批服务：提交审批/审批操作/查状态，桥接通用审批引擎(platform-approval) |

## 异常发现

**死代码群 / 未挂载：**
- `presale_ai_service.py`（顶层）：纯兼容再导出 shim，全仓零引用者，活跃逻辑在 `presale/presale_ai_service.py`。可删。
- `project_relations_service.py`（复数）：零 import 者，与活跃的 `project_relation_service.py`（单数）并存，属重复/僵尸实现。
- `purchase_suggestion_engine.py`：仅 tests 与 `scripts/import_services_batch2.py` 引用，运行时/端点无引用。
- `purchase_intelligence/`（服务包）：无任何 service/endpoint import；只有非活跃的 `api/v1/api_lazy.py` 尝试挂载一个**并不存在**的端点文件 `endpoints/purchase_intelligence.py`（try/except 吞异常）。`app/main.py` 实际使用 `app/api/v1/api.py`，未挂载。
- `quality_risk_management/` + `quality_risk_ai/`：一个死代码簇。`quality_risk_management` 无任何调用方；`quality_risk_ai` 仅被前者引用。活跃 `api.py` 挂载的 `endpoints/quality_risk.py` 是一个逐级回退（`.qualityrisk`→`.quality`→`.common.quality_risk`→`.admin.quality_risk`→空 `APIRouter`）的 shim，且这些目标文件均不存在，最终落到空路由，故该质量风险 AI 功能整体未生效。其中 `quality_risk_ai/test_recommendation_engine.py` 本身就是返回空的 Stub。
- `ppt_generator/`：运行时零引用，仅 tests 与 `scripts/create_full_ppt_refactored.py` 使用；包内 `builders/`（base/content/table）是对顶层 `*_builder.py` 的薄再导出层，测试对 `generator.PPTGeneratorService`/`builders.base` 等的引用与实际导出名（`PresentationGenerator`/`base_builder`）不一致，测试多为 try/except 容错桩。

**重复 / 并存实现：**
- `project_relation_service.py`（单数，活跃）vs `project_relations_service.py`（复数，死）——功能重叠的关联查询。
- `purchase_order_from_bom_service.py` 与 `purchase_request_from_bom_service.py` 头部常量与依赖几乎一致，存在大量重复逻辑（PO vs 请购）。
- `quality_service.py`（顶层，通用质量/SPC）与 `production/quality_service.py`（端点层质检列表逻辑）两套质量服务并存，职责需厘清。
- `progress_service.py`、`production_progress_service.py`、`progress_integration_service.py` 三个进度服务分属 project/production 两域但命名相近，易混。

**放错位置 / 归域存疑：**
- `project_change_impact_service.py` 位于 `project*` 命名下，但实为 ECN "变更影响分析"，建议归 `ecn`。
- `project_cost_aggregation_service.py` / `project_cost_prediction/` / `profit_analysis_service.py` 顶着 project 前缀，实为成本/EVM/毛利逻辑，归 `cost-finance`。
- `project_meeting_service.py` 完全依赖 `management_rhythm`（strategy-pmo）的会议模型，仅做项目侧关联。

**tenant_id 检查：** 本次范围为 services 层，非 models，未逐表核查 tenant_id（N/A）。附带观察：`project_status_normalization.py`、`purchase/order_state_machine.py`、`presale/risk_taxonomy.py` 等为纯静态映射/枚举工具，不涉及租户数据。