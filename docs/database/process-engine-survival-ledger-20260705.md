# 流程引擎与配套表存废台账

日期：2026-07-05

数据库：`/Users/flw/non-standard-automation-pm/data/app.db`

目标：把“审批引擎”“工作流程引擎”“状态机”“领域 workflow 服务”分层，防止同一业务继续多套表、多套入口、新旧双轨并存。

## 口径

| 类型 | 含义 | 当前主线 |
|---|---|---|
| 审批引擎 | 有人审批、待办、通过/驳回/转审/抄送 | `ApprovalEngineService` + `approval_*` 主表 |
| 业务状态机 | 控制业务对象状态能否从 A 转到 B | `app/core/state_machine/*` + `state_transition_logs` |
| 领域 workflow 服务 | 业务模块对审批/状态机的包装入口 | 保留薄门面，不能自建审批事实表 |
| 状态变更 hook | 状态变更后的副作用注册器 | `app/common/workflow/engine.py`，建议后续改名 |
| 旧审批 workflow | 旧版 `WorkflowEngine` 和 `legacy_approval_*` 模型 | 废弃候选，仅测试兼容 |

## 引擎存废

| 对象 | 状态 | 证据 | 处置 |
|---|---|---|---|
| `app/services/approval_engine/engine/*` / `ApprovalEngineService` | 保留 | 当前审批提交、任务、动作、查询主实现 | 作为唯一审批执行引擎 |
| `app/models/approval/*` | 保留 | 统一审批模板、流程、节点、实例、任务、日志模型 | 作为审批事实源 |
| `/api/v1/approvals/*` | 保留 | 全局审批模板/实例/任务/待办/代理入口 | 作为通用审批中心唯一入口 |
| `app/services/approval_workflow_service.py` | 合并保留 | 旧 service 名称仍被测试/旧调用使用，但内部转 `ApprovalEngineService` | 保留兼容门面，不允许回写旧表 |
| `app/services/base_approval_workflow.py` | 保留 | 采购、外协等领域审批薄封装，内部走 `ApprovalEngineService` | 保留为领域门面 |
| `app/services/approval_engine/workflow_engine.py` | 废弃候选 | 文件头已声明 deprecated；运行代码不应引用 | 只留测试兼容，后续改测试后删除 |
| `app/services/approval_engine/models.py` 中 `LegacyApproval*` | 废弃候选 | 真实库无 `legacy_approval_*` 表；不在 `app.models` metadata 主线中注册 | 跟随旧 `workflow_engine.py` 删除 |
| `app/core/state_machine/*` | 保留 | ECN、问题单、里程碑、安装派工、报价等状态规则 | 作为业务状态转换主框架 |
| `app/common/workflow/engine.py` | 改名候选/隔离保留 | 只是状态变更 handler registry，被 CRUD/里程碑 handler 用 | 后续改名为 `status_transition_handlers` 或并入状态机 hook |
| `app/services/sales/funnel_state_machine.py` | 保留/待统一 | 销售漏斗阶段门有专用语义和日志 | 保留，后续评估是否共用 `state_transition_logs` |

## 配套表存废

| 表 | 行数 | 状态 | 说明 |
|---|---:|---|---|
| `approval_templates` | 10 | 保留 | 审批模板主表 |
| `approval_flow_definitions` | 13 | 保留 | 审批流程定义主表 |
| `approval_node_definitions` | 30 | 保留 | 审批节点定义主表 |
| `approval_routing_rules` | 3 | 保留 | 条件路由规则 |
| `approval_instances` | 12 | 保留 | 审批实例主表；含项目变更旧审批明细迁移生成的 3 条实例 |
| `approval_tasks` | 19 | 保留 | 审批待办任务主表 |
| `approval_action_logs` | 39 | 保留 | 审批动作日志主表；含项目变更旧审批明细迁移 3 条 |
| `approval_comments` | 3 | 保留 | 审批评论配套表 |
| `approval_carbon_copies` | 3 | 保留 | 审批抄送配套表 |
| `approval_countersign_results` | 4 | 保留 | 会签统计配套表 |
| `approval_delegates` | 3 | 保留 | 审批代理配置 |
| `approval_delegate_logs` | 20 | 保留 | 审批代理日志 |
| `legacy_approval_archives` | 125 | 已归档/主库已删 | 旧审批表历史已转入外部归档库，主库不再保留 |
| `state_transition_logs` | 20 | 保留 | 通用状态机审计日志 |
| `funnel_transition_logs` | 0 | 保留/待统一 | 销售漏斗阶段门日志，当前有专用服务消费 |
| `presale_ai_workflow_log` | 20 | 保留 | 售前 AI 执行步骤日志，不是审批表 |
| `exception_handling_flow` | 3 | 保留 | 生产异常处理流，领域事实表 |
| `ecn_approvals` | 3 | 已合并退役 | ECN 审批任务统一改读 `approval_instances` / `approval_tasks`，旧行只外部归档 |
| `ecn_approval_matrix` | 3 | 已合并退役 | 审批规则统一进入 `approval_templates` / `approval_flow_definitions` / `approval_node_definitions`，旧矩阵只外部归档 |
| `timesheet_approval_log` | 20 | 已归档退役 | 20 条均无工时/批次锚点，只外部归档；工时接口已走统一审批引擎 |
| `change_approval_records` | 3 | 已合并退役 | 项目变更审批明细已迁入 `approval_instances` / `approval_action_logs`，旧表外部归档并删除 |

## 本轮已整合

| 项 | 结果 |
|---|---|
| 发票模板编码 | 统一为真实库主线 `TPL_INVOICE`；运行代码不再使用 `SALES_INVOICE` |
| 发票审批入口 | `/sales/invoices` 不再二次挂载全局 `approvals_router`；通用审批只走 `/approvals` |
| 旧 workflow 引用 | 新增守护，禁止 `app/` 运行代码引用 deprecated `approval_engine.workflow_engine` |
| 项目变更审批明细 | `change_approval_records` 3 条归档后迁入统一审批日志；`ProjectChangeRequestsService` 不再写旧表 |
| 审批动作写入口 | 新增守护，`app/` 运行代码只有 `app/services/approval_engine/*` 可构造 `ApprovalActionLog`；项目变更改走 `ApprovalEngineService.record_action_log()` |
| 审批/状态历史边界 | 新增守护，禁止把 `STATUS_CHANGE` / `STATE_CHANGE` / `UPDATE_STATUS` / `TRANSITION` 当作审批动作写入；业务状态历史继续走 `state_transition_logs` 或领域日志 |
| 工时旧审批日志 | `timesheet_approval_log` 20 条无实体锚点，只外部归档并删除；工时测试改查统一审批日志 |
| ECN 旧审批表 | `ecn_approvals` / `ecn_approval_matrix` 已从服务、通知、看板、调度链路摘除；审批任务统一读 `approval_tasks` |

## 协作规则

1. 业务对象状态流转先过状态机，不能在 CRUD 里直接改终态。
2. 一旦需要人审批，业务服务只发起 `ApprovalEngineService.submit()`。
3. 审批通过/驳回后，由 adapter 回写业务状态或调用领域服务。
4. 审批动作历史只写 `approval_action_logs`；业务状态历史写 `state_transition_logs` 或领域专用日志。
5. 旧 `WorkflowEngine` 不再接新代码；测试迁完后删除。

## 下一批建议

1. `app/common/workflow/engine.py` 改名或并入状态机 hook，降低“又一个 workflow engine”的误解。
2. 清理 deprecated `approval_engine.workflow_engine.py` 的测试依赖，再删除 legacy module。
3. 继续处理空/孤儿业务表，优先找“有模型无真实表”或“真实表有脏样本但无运行入口”的对象。
