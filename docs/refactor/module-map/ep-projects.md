以下为 `app/api/v1/endpoints/projects/` 子包（共 114 个 .py 文件）的逐文件归域清单。

说明：main.py 实际加载的路由聚合器是 `app/api/v1/api.py`（非 api_lazy/medium/minimal 变体）；本包的活路由挂载点是 `projects/__init__.py`。凡未被 `projects/__init__.py` 聚合、也未被 `api.py` 单独注册的路由文件视为未挂载。本包为 endpoint 层，无建表，tenant_id 检查不适用。

| 路径 | 域 | 文件数 | 总行数 | 跨域依赖 | 死代码嫌疑 | 备注 |
|---|---|---|---|---|---|---|
| `__init__.py` | project | 1 | 252 | — | 无 | 项目模块主路由聚合器，include 约35个子路由/子包 |
| `core.py` + `project_crud.py` + `project_board.py` + `project_clone.py` + `project_stats.py` | project | 5 | 707 | — | 无 | core.py 是聚合器，`from . import project_board,project_clone,project_crud,project_stats` 后 include；项目基础CRUD/看板/统计/克隆，全部活 |
| `templates.py` + `template_crud.py` + `template_projects.py` + `template_versions.py` + `template_analytics.py` | project | 5 | 925 | — | 无 | templates.py 聚合器，include 四个 template_* 子模块；模板CRUD/从模板建项目/版本管理/智能推荐，全部活 |
| `status.py` | project | 1 | 16 | — | 疑似(死/被同名包 shadow) | 仅 `from .status import router` 的 compat 壳；同目录存在 `status/` 包，`from . import status` 解析到包而非本文件，本文件从未被导入 |
| `status/` (batch,health,health_viz,stages,status_crud) | project | 6 | 1008 | stage_instance, status_update_service | 无 | 项目状态/健康度/阶段推进/批量操作；status.py(904行)拆出的活实现 |
| `overview.py` | project | 1 | 260 | 多模块只读聚合 | 无 | 项目与各模块关联数据的总览视图 |
| `pipeline.py` | project | 1 | 260 | — | 无 | 跨项目阶段流水线视图 |
| `archive.py` | project | 1 | 290 | — | 无 | 项目归档/取消归档/归档列表 |
| `cache.py` | project | 1 | 155 | — | 无 | 项目缓存统计/清理/重置 |
| `sync.py` + `sync_utils.py` | project | 2 | 353 | **sales**(Contract), data_sync_service | 无 | 合同数据同步/ERP集成；跨 sales 域 |
| `utils.py` + `serialization.py` + `code_generation.py` | project | 3 | 108 | gate_checks | 无 | 编号生成/序列化/ERP同步等 helper，被 sync/payment_plans/utils 引用 |
| `data_flow.py` | project | 1 | 91 | — | 无 | WBS/BOM/里程碑/验收向后续模块生成数据的全链路数据流 |
| `payment_plans.py` | project→cost-finance | 1 | 222 | — | 无 | 项目付款计划；偏财务，可考虑迁 cost-finance |
| `workspace.py` | project | 1 | 279 | **issue**(Issue) | 无 | 项目工作空间：奖金/会议/问题/文档聚合；经 `project_workspace.py` 壳在 api.py 注册（活） |
| `contributions.py` | **performance-hr** | 1 | 218 | — | 无 | 项目贡献度评分/报告，用 project_contribution_service；经 `project_contributions.py` 壳在 api.py 注册（活）。绩效属性，应迁 performance-hr |
| `risks.py` + `risk_analytics.py` | project | 2 | 716 | pmo(PmoProjectRisk) | 无 | 风险CRUD/矩阵/汇总 + 风险趋势/报表；均活（risks 挂 projects-risks-v2） |
| `ext_risks.py` | project | 1 | 366 | pmo | 疑似(死/未挂载) | 完整风险CRUD路由，全仓零引用；已被 risks.py + risk_analytics.py 取代 |
| `extended.py` | project | 1 | 119 | data_scope | 无 | 项目扩展记录 CRUD/统计（挂 /extensions）；ext_* 系列历史从此拆出 |
| `ext_best_practices.py` | **strategy-pmo** | 1 | 241 | — | 无 | 项目最佳实践管理，应迁 strategy-pmo |
| `ext_lessons.py` | **strategy-pmo** | 1 | 306 | — | 无 | 经验教训CRUD/分类/知识复用，应迁 strategy-pmo |
| `ext_reviews.py` | project/strategy-pmo | 1 | 348 | — | 无 | 项目复盘报告CRUD/统计；复盘知识可归 strategy-pmo |
| `ext_relations.py` | project | 1 | 300 | — | 无 | 项目间关联/依赖关系管理 |
| `ext_resources.py` | project/performance-hr | 1 | 381 | — | 无 | 项目资源分配/负载/统计 |
| `change_requests.py` + `change_impact.py` | **ecn** | 2 | 520 | project.change_impact(ProjectChangeImpact) | 无 | 项目变更申请 + 项目-变更单联动；change_impact 经 api.py:1065 单独注册。工程变更域，应迁 ecn |
| `costs/` (crud,analysis,budget,forecast,evm,labor,allocation,summary,alert,review,profit_optimization,cost_prediction_ai,ecn_cost_summary) | **cost-finance** | 14 | 2739 | **cost**(CostService,CostForecastService,cost_basis,labor/allocation/review svc), evm_service, budget_alert/analysis, profit_analysis；`ecn_cost_summary`→**ecn** | 无 | 项目成本/预算/EVM/预测/人工/分摊/利润优化/AI成本预测。整体应迁 cost-finance；ecn_cost_summary 偏 ecn |
| `financial_costs.py` | **cost-finance** | 1 | 266 | — | 无 | 财务历史项目成本查询，应迁 cost-finance |
| `cost_benchmark.py` | **cost-finance** | 1 | 215 | project.cost_benchmark_service | 疑似(死/路由未挂载) | 4个成本对标端点，router 全仓无 include，未挂载；应迁 cost-finance |
| `material_progress.py` | **bom-material/inventory** | 1 | 159 | material_progress_service | 无 | 项目物料到料进度可视化，应迁 bom-material/inventory-kitting |
| `schedule_prediction.py` | project | 1 | 459 | — | 无 | 进度预测（项目内 + 全局概览，同一 router 挂两个前缀） |
| `milestones/` (crud,workflow) | project | 3 | 366 | — | 无 | 项目里程碑CRUD/工作流 |
| `machines/` (crud,custom) | project | 3 | 530 | machine_service, machine_custom | 无 | 项目设备/机台管理 |
| `members/` (crud) | project | 2 | 475 | — | 无 | 项目成员管理 |
| `roles/` (configs,leads,overview,team_members) | project | 5 | 756 | — | 无 | 项目角色/负责人/团队成员配置 |
| `stages/` (crud,tree,timeline,status_updates,stage_operations,node_operations,node_assignment,custom_nodes) | project | 9 | 927 | stage_instance | 无 | 项目阶段树/时间线/节点分配/状态更新 |
| `progress/` (summary) | project | 2 | 306 | progress(Task) | 无 | 项目进度汇总 |
| `gate_checks/` (gate_common,gate_s1_s2…s8_s9) | project(集成枢纽) | 10 | 967 | **sales**(Contract,contract.status_service), **technical_review**(TechnicalReview,ReviewIssue), **bom-material**(BomHeader,BomItem), **procurement/outsourcing**(OutsourcingOrder), **acceptance**(AcceptanceOrder/Issue/Report), **issue**(Issue) | 无 | 阶段门 S1→S9 校验，纯函数无 router，经 check_gate 被 stage_transition_checks 调用。跨域依赖最重，重构拆分需最后动 |
| `evaluations/` (crud,custom) | project | 3 | 354 | project_evaluation_service | 无 | 项目评价/评分（用 project_evaluation 模型） |
| `resource_plan/` (crud,assignment,custom) | project/performance-hr | 4 | 581 | resource_plan_service | 无 | 项目阶段资源计划/人员指派；资源调度属性可归 performance-hr |
| `timesheet/` (crud,custom) | **performance-hr** | 3 | 354 | **timesheet**(Timesheet 模型) | 无 | 项目工时管理，应迁 performance-hr |
| `work_logs/` (crud) | **performance-hr** | 2 | 123 | — | 无 | 项目工作日志，应迁 performance-hr |
| `workload/` (crud) | **performance-hr** | 2 | 331 | — | 无 | 项目工作量管理，应迁 performance-hr |
| `approvals/` (submit_new,action_new,cancel_new,status_new,history_new) | **platform-approval**(业务桥接,已废弃) | 6 | 697 | **platform-approval**(ApprovalEngineService, models.approval) | 疑似(标记 DEPRECATED,但仍注册) | 项目审批的旧桥接，`__init__` 头明确 [DEPRECATED] 请改用 /api/v1/approvals/；仍在 projects/__init__:215 挂载，属活着的废弃层 |

## 异常发现

**死文件 / 未挂载路由：**
- `ext_risks.py`（366行）：完整的项目风险 CRUD 路由（`/{project_id}/risks` 等 7 个端点），全仓库零引用、未被任何聚合器 include。功能已由 `risks.py`（挂 projects-risks-v2）+ `risk_analytics.py` 取代。建议删除。
- `cost_benchmark.py`（215行）：定义了 4 个成本对标端点的 `router`，但该 router 在任何地方都没有被 `include_router`（`api.py`/`__init__.py`/api_lazy 均无），端点实际不可达。属未挂载死路由。
- `status.py`（16行）：内容仅 `from .status import router` 的向后兼容壳。同目录同时存在 `status/` 包，Python 导入解析中包优先于同名模块，故 `projects/__init__.py` 的 `from . import status` 拿到的是 `status/` 包，本 `status.py` 永不被导入，是被 shadow 的僵尸文件。

**重复 / 并存实现（重构未清尾）：**
- 状态管理：`status.py`（旧 904 行拆分说明保留的壳）与 `status/` 包并存，前者已死。
- CRUD 聚合模式：`core.py`→`project_{crud,board,clone,stats}.py`、`templates.py`→`template_{crud,projects,versions,analytics}.py` 是同一种"聚合器 + 子模块"拆分（均为活代码），但与 `project_crud.py` 命名易和 `app/services/project_crud` 混淆。
- 风险功能三份：`risks.py`（v2 活）、`risk_analytics.py`（分析 活）、`ext_risks.py`（死）——同一 `/{project_id}/risks` 路径语义，`ext_risks` 为遗留尸体。
- `extended.py` 与 `ext_*` 系列：`ext_best_practices` 文件头注明"从 extended.py 拆分"，但 `extended.py` 仍保留一套 `/extensions` 通用扩展记录端点，属拆分残留，需确认 `/extensions` 是否仍被前端使用。

**放错位置（应迁出 project 域）的文件群：**
- cost-finance：`costs/`（14文件2739行，依赖 cost 域一整套 service）、`financial_costs.py`、`cost_benchmark.py`（且已死）；`payment_plans.py` 亦偏财务。
- ecn：`change_requests.py` + `change_impact.py`（工程变更）、以及 `costs/ecn_cost_summary.py`。
- performance-hr：`timesheet/`（依赖 `app.models.timesheet`）、`work_logs/`、`workload/`、`contributions.py`（贡献度评分）；`resource_plan/` 可议。
- strategy-pmo：`ext_best_practices.py`、`ext_lessons.py`（经验教训/踩坑）、`ext_reviews.py`（复盘）。
- bom-material / inventory-kitting：`material_progress.py`（物料到料进度）。
- platform-approval：`approvals/`（已 DEPRECATED 的项目审批桥接，仍在注册）。

**跨域耦合枢纽（重构排序关键）：** `gate_checks/` 是全包跨域依赖最集中处，单包内直接 import 了 sales / technical_review / bom-material / outsourcing / acceptance / issue 六个业务域的模型与 service（阶段门校验天然横跨价值链）；`sync.py` 依赖 sales(Contract)；`workspace.py` 依赖 issue。这三处决定了 project 域从大熔炉拆出时的解耦难度。

**多租户：** 本范围为 endpoint 层，无模型定义，tenant_id 检查不适用。