# 全系统模块合并蓝图

## 结论

售前技术支持和项目管理只是第一批暴露问题的模块。这个系统要真正给 100-200 人的非标自动化公司用起来，不能按“页面/数据库表/开发批次”组织模块，而要按公司经营主线组织。

全系统主线应收口为：

`战略目标 -> 线索/商机 -> 售前技术 -> 报价/合同 -> 立项 -> 项目交付 -> 工程/BOM -> 采购/仓储 -> 生产/装配 -> 质量/验收 -> 服务/复盘 -> 财务/绩效`

合并不是把所有页面塞成一个页面，而是建立少数几个“业务工作台”，每个工作台内部再分视图。旧页面先保留为兼容入口或子视图，稳定后再清理。

## 当前系统实际分散情况

从现有前端路由看，系统已经有这些模块文件：

- `dashboardRoutes.jsx`
- `strategyRoutes.jsx`
- `salesRoutes.jsx`
- `presalesRoutes.jsx`
- `projectRoutes.jsx`
- `pmoRoutes.jsx`
- `procurementRoutes.jsx`
- `warehouseRoutes.jsx`
- `productionRoutes.jsx`
- `qualityRoutes.jsx`
- `financeRoutes.jsx`
- `hrRoutes.jsx`
- `systemRoutes.jsx`

从后端 endpoint 看，至少覆盖：

- `sales`
- `presale`
- `projects`
- `pmo`
- `technical_review`
- `technical_spec`
- `rd_project`
- `bom`
- `material`
- `material_demands`
- `purchase`
- `procurement`
- `warehouse`
- `shortage`
- `production`
- `assembly_kit`
- `quality`
- `acceptance`
- `installation_dispatch`
- `service`
- `finance/cost/standard_costs/budget`
- `timesheet`
- `performance/hr/qualification/staff_matching`
- `reports/dashboard/analytics`
- `approvals/permissions/users/organization`

所以后续合并必须覆盖全链路，不能只修售前和项目。

## 合并后的一级业务入口

建议最终一级入口控制在 10 个左右：

1. 经营驾驶舱
2. 销售经营中心
3. 售前技术中心
4. 项目交付中心
5. 工程技术中心
6. 供应链中心
7. 生产执行中心
8. 质量交付服务中心
9. 财务经营中心
10. 人力与组织中心
11. 系统治理中心

这些不是都要一次做完。先建统一入口和上下文，再逐步迁移旧页面。

## 1. 经营驾驶舱

### 主入口

`/executive/workbench`

### 合并对象

- 管理驾驶舱
- 战略分析
- 战略地图
- CSF/KPI
- 年度重点工作
- 管理节拍
- 关键决策
- 经营报表

### 当前散点

- `/admin-dashboard`
- `/gm-dashboard`
- `/chairman-dashboard`
- `/operation`
- `/business-reports`
- `/strategy/analysis`
- `/strategy/map`
- `/strategy/csf`
- `/strategy/kpi`
- `/strategy/annual-work`
- `/management-rhythm-dashboard`
- `/key-decisions`

### 工作台视图

- 公司经营总览
- 销售目标与预测
- 订单/项目/交付负荷
- 毛利和现金流
- 重大风险和关键决策
- 战略目标拆解

### 聚合接口

`GET /api/v1/executive/workbench/overview`

核心返回：

- revenue_pipeline
- order_backlog
- project_health
- delivery_risk
- gross_margin
- cash_collection
- strategic_kpis
- key_decisions

## 2. 销售经营中心

### 主入口

`/sales/workstation`

### 合并对象

- 线索
- 客户
- 商机
- 销售漏斗
- 投标入口
- 报价
- 合同
- 回款/发票视图
- 销售团队
- 销售预测

### 当前散点

- `/sales/workstation`
- `/sales/leads`
- `/sales/opportunities`
- `/sales/funnel`
- `/sales/customers`
- `/cost-quotes/quotes`
- `/sales/contracts`
- `/sales/receivables`
- `/invoices`
- `/sales/team-center`
- `/sales/forecast-dashboard`

### 工作台视图

- 销售漏斗
- 客户与线索
- 商机推进
- 售前协同
- 报价合同
- 回款风险
- 团队目标

### 统一上下文

`GET /api/v1/sales/workstation/context`

按 `customer_id / lead_id / opportunity_id / quote_id / contract_id` 拉通：

- customer
- lead
- opportunity
- presale_ticket
- technical_assessment
- solutions
- quotes
- contracts
- receivables
- next_actions

## 3. 售前技术中心

### 主入口

`/presales/workbench`

### 合并对象

- 售前工单
- 需求包
- 技术评估
- 技术方案
- 成本估算
- 技术参数模板
- 投标技术支持
- 售前工程师负荷
- 售前数据分析

### 当前散点

- `/presales-workbench`
- `/sales/presale-workbench`
- `/presales-dashboard`
- `/presales-manager-dashboard`
- `/sales/presales-tasks`
- `/presales/technical-solutions`
- `/sales/assessments/:sourceType/:sourceId`
- `/presales/solutions`
- `/presales/cost-estimation`
- `/presales/technical-parameters`
- `/presales/bids`
- `/presales/presale-analytics`

### 工作台视图

- 总览
- 需求与评估
- 工单执行
- 方案与成本
- 投标报价协同
- 经理调度

### 聚合接口

`GET /api/v1/presale/workbench/overview`

`GET /api/v1/presale/workbench/context`

上下文按 `source_type + source_id + ticket_id` 串：

- lead/opportunity
- ticket
- current_assessment
- solutions
- cost_estimates
- technical_templates
- gate_status
- open_items
- next_actions

## 4. 项目交付中心

### 主入口

`/project/workbench`

### 合并对象

- 合同转项目
- 立项
- 项目看板
- 项目详情/工作区
- 阶段/WBS/任务
- 甘特和资源
- 工时
- 项目成本
- 风险/问题/变更
- 周报
- 结项和复盘

### 当前散点

- `/board`
- `/projects/:id`
- `/projects/:id/workspace`
- `/pmo/dashboard`
- `/pmo/initiations`
- `/progress-tracking/...`
- `/gantt-resource`
- `/ai-project-tools`
- `/project-health-monitor`
- `/project/cost-center`
- `/project-closing`
- `/tasks`
- `/milestones`
- `/schedule`
- `/ecn`

### 工作台视图

- 项目总览
- 项目启动
- 计划与 WBS
- 资源与工时
- 进度与交付
- 成本与毛利
- 风险/变更/问题
- 验收与复盘

### 聚合接口

`GET /api/v1/projects/{project_id}/workspace/context`

返回：

- project
- contract
- opportunity
- quote
- presale_solution
- baseline_cost
- team
- milestones
- tasks
- schedule
- resources
- timesheets
- costs
- risks
- changes
- issues
- acceptance
- lessons
- next_actions

## 5. 工程技术中心

### 主入口

`/engineering/workbench`

### 合并对象

- 技术评审
- 技术规格
- ECN
- 研发项目
- 工程师工作台
- 工程经验知识
- 设计问题统计
- 技术文档

### 当前散点

- `/technical-reviews`
- `/technical-spec/...`
- `/ecn`
- `/change-management/ecn-center`
- `/rd-projects`
- `/rd-cost`
- `/workstation`
- `/engineer-recommendation`
- `/engineer-knowledge`

### 工作台视图

- 工程任务
- 技术评审
- 设计输出
- ECN 变更
- 研发项目
- 工程知识
- 工程绩效输入

### 聚合接口

`GET /api/v1/engineering/workbench/overview`

`GET /api/v1/projects/{project_id}/engineering/context`

按 `project_id / machine_id / ecn_id / review_id` 串：

- specs
- reviews
- drawings/documents
- ecn
- engineering_tasks
- open_issues
- lessons

## 6. 供应链中心

### 主入口

`/supply-chain/workbench`

### 合并对象

- BOM
- 物料主数据
- 物料需求
- 缺料
- 采购申请
- 采购订单
- 供应商
- 到货
- 仓储
- 库存
- 替代料
- 齐套率

### 当前散点

- `/procurement/execution-center`
- `/procurement/material-center`
- `/procurement/analysis-center`
- `/purchases`
- `/purchase-requests`
- `/suppliers`
- `/shortage/dashboard`
- `/arrival-tracking`
- `/warehouse/...`
- `/kit-check`
- `/material-analysis`
- `/assembly-kit`
- `/sales/purchase-material-costs`

### 工作台视图

- 物料需求
- BOM 与齐套
- 缺料处置
- 采购执行
- 到货与入库
- 库存与库位
- 供应商与价格
- 供应链分析

### 聚合接口

`GET /api/v1/supply-chain/workbench/overview`

`GET /api/v1/projects/{project_id}/supply-chain/context`

返回：

- bom
- material_demands
- shortage_items
- purchase_requests
- purchase_orders
- arrivals
- inventory
- substitutions
- supplier_risks
- kit_rate
- next_actions

## 7. 生产执行中心

### 主入口

`/production/workbench`

### 合并对象

- 生产计划
- 工单
- 装配任务
- 成套检查
- 领料
- 外协
- 现场资源
- 产能分析
- 异常
- 发货

### 当前散点

- `/production-board`
- `/production/execution-center`
- `/production/assembly-center`
- `/assembly-tasks`
- `/material-requisitions`
- `/kit-check`
- `/production/capacity-analysis`
- `/production/exception-center`
- `/outsourcing-orders`
- `/pmc/delivery-orders`

### 工作台视图

- 生产总览
- 工单执行
- 装配任务
- 领料与齐套
- 外协协同
- 异常处理
- 产能负荷
- 发货计划

### 聚合接口

`GET /api/v1/production/workbench/overview`

`GET /api/v1/projects/{project_id}/production/context`

返回：

- work_orders
- assembly_tasks
- material_requisitions
- kit_status
- capacity
- exceptions
- outsourcing_orders
- delivery_orders
- next_actions

## 8. 质量交付服务中心

### 主入口

`/delivery-service/workbench`

### 合并对象

- 来料/过程/出货检验
- 质量问题
- NC
- 安装派工
- FAT/SAT
- 验收订单
- 验收问题
- 客服工单
- 服务记录
- 客户沟通
- 满意度
- 服务知识库

### 当前散点

- `/quality/...`
- `/acceptance`
- `/delivery/acceptance-center`
- `/installation-dispatch`
- `/service/center`
- `/service-tickets`
- `/service-records`
- `/customer-communications`
- `/customer-satisfaction`
- `/service-knowledge-base`

### 工作台视图

- 质量总览
- 检验与 NC
- 验收准备
- 安装与现场
- 验收问题
- 服务工单
- 客户满意度
- 服务知识沉淀

### 聚合接口

`GET /api/v1/delivery-service/workbench/overview`

`GET /api/v1/projects/{project_id}/delivery-service/context`

返回：

- inspections
- quality_issues
- nc_items
- installation_dispatch
- acceptance_orders
- acceptance_issues
- service_tickets
- service_records
- customer_feedback
- next_actions

## 9. 财务经营中心

### 主入口

`/finance/workbench`

### 合并对象

- 报价成本
- 项目成本
- 标准成本
- 财务成本上传
- 工时成本
- 付款审批
- 项目结算
- 应收发票
- 多币种
- 经营分析

### 当前散点

- `/finance/cost-center`
- `/costs`
- `/financial-costs`
- `/payment-approval`
- `/settlement`
- `/financial-reports`
- `/multi-currency`
- `/finance/analytics-dashboard`
- `/quote-compare`
- `/cost-variance`
- `/labor-cost`
- `/project/cost-center`
- `/sales/receivables`
- `/invoices`

### 工作台视图

- 财务总览
- 报价/项目成本
- 预算与实际
- 付款与应收
- 结算
- 毛利分析
- 工时成本
- 财务报表

### 聚合接口

`GET /api/v1/finance/workbench/overview`

`GET /api/v1/projects/{project_id}/finance/context`

返回：

- quote_cost
- project_budget
- actual_cost
- labor_cost
- material_cost
- payment_requests
- receivables
- invoices
- settlement
- margin
- next_actions

## 10. 人力与组织中心

### 主入口

`/people/workbench`

### 合并对象

- 员工
- 部门
- 组织
- 岗位
- 考勤
- 工时
- 绩效
- 工程师绩效
- 任职资格
- 人岗匹配
- 个人奖金/绩效

### 当前散点

- `/employees`
- `/departments`
- `/organization-management`
- `/position-management`
- `/attendance-management`
- `/timesheet`
- `/timesheet/dashboard`
- `/performance`
- `/hr/performance-center`
- `/engineer-performance`
- `/qualifications`
- `/hr/talent-matching-center`
- `/personal/my-performance`
- `/personal/my-bonus`

### 工作台视图

- 组织人员
- 考勤工时
- 绩效任务
- 工程师绩效
- 任职资格
- 人岗匹配
- 个人中心

### 聚合接口

`GET /api/v1/people/workbench/overview`

按 `user_id / department_id / project_id` 返回：

- employee
- attendance
- timesheets
- performance_tasks
- qualifications
- staffing_needs
- project_assignments
- bonus_summary

## 11. 系统治理中心

### 主入口

`/system/workbench`

### 合并对象

- 用户
- 角色
- 权限
- 菜单
- 主数据
- 审批模板
- 通知
- 数据导入导出
- 报表模板
- 备份
- 审计
- 租户

### 当前散点

- `/user-management`
- `/role-management`
- `/permissions`
- `/departments`
- `/customer-management`
- `/supplier-management-data`
- `/approvals`
- `/notifications`
- `/data-import-export`
- `/report-center`
- `/backup`
- `/audit`

### 工作台视图

- 账号权限
- 组织主数据
- 业务主数据
- 审批与通知
- 导入导出
- 报表配置
- 审计备份
- 系统健康

## 全系统统一对象链

要真正合并，必须确定“对象链”，所有模块围绕同一批 ID 传递。

| 阶段 | 主对象 | 关键关联 |
| --- | --- | --- |
| 客户经营 | `customer_id` | contacts, communication, satisfaction |
| 线索 | `lead_id` | requirement, assessment, source |
| 商机 | `opportunity_id` | customer, presale_ticket, assessment |
| 售前 | `presale_ticket_id` | assessment, solution, cost, tender |
| 报价 | `quote_id` | opportunity, solution, cost, margin |
| 合同 | `contract_id` | quote, customer, payment terms |
| 立项 | `initiation_id` | contract, opportunity, baseline |
| 项目 | `project_id` | contract, team, scope, milestones |
| 工程 | `review_id / ecn_id / spec_id` | project, machine, BOM |
| 物料 | `bom_id / material_id` | project, demand, purchase |
| 采购 | `purchase_request_id / purchase_order_id` | material, supplier, arrival |
| 仓储 | `inventory_id / location_id` | material, inbound, outbound |
| 生产 | `work_order_id` | project, BOM, assembly, requisition |
| 质量 | `inspection_id / nc_id` | material, work_order, project |
| 交付 | `acceptance_order_id / dispatch_id` | project, customer, issue |
| 服务 | `service_ticket_id` | customer, project, acceptance |
| 财务 | `settlement_id / invoice_id` | contract, project, cost |
| 人力 | `user_id / department_id` | role, project assignment, timesheet |

## 统一状态口径

每个中心都可以有自己的内部状态，但跨模块必须收敛成可驱动动作的状态。

建议建立统一状态层：

- `NOT_STARTED`
- `PENDING`
- `IN_PROGRESS`
- `REVIEW`
- `APPROVED`
- `BLOCKED`
- `COMPLETED`
- `CANCELLED`

跨模块动作必须明确输入和输出：

- 方案评审通过 -> G2 技术评估通过
- 合同签署 -> 可立项
- 立项通过 -> 项目创建/阶段模板应用
- BOM 发布 -> 物料需求生成
- 采购到货 -> 齐套率更新
- 生产完工 -> 可发起验收
- 验收通过 -> 可结算/复盘
- 服务关闭 -> 满意度/知识库沉淀

## 全链路归并矩阵

这次合并不能只看“售前 + 项目”。售前技术支持只是第一个典型问题：入口散、上下文散、完成结果不回流。后面的项目、工程、采购、生产、质量、财务也要用同一套口径处理。

| 业务段 | 合并后中心 | 统一入口 | 主上下文 | 必须回流的状态/结果 | 第一验收断点 |
| --- | --- | --- | --- | --- | --- |
| 销售/商机 | 销售经营中心 | `/sales/workstation` | `customer_id / lead_id / opportunity_id` | 售前评估状态、方案结论、报价状态、合同状态 | 商机能看到售前工单、评估、方案和下一步 |
| 售前技术 | 售前技术中心 | `/presales/workbench` | `opportunity_id / presale_ticket_id / assessment_id / solution_id` | 工单完成结论、交付物、技术评估、成本建议、G2 结果 | 完成工单后销售侧能看到评审结论 |
| 报价/合同 | 销售经营中心 + 财务经营中心 | `/sales/workstation?view=quote` | `quote_id / contract_id` | 方案引用、成本基线、毛利、合同签署结果 | 报价能读取售前方案和成本，不重复录入 |
| 立项/项目 | 项目交付中心 | `/project/workbench` | `project_id / contract_id / opportunity_id` | 项目章程、范围、里程碑、预算、团队 | 合同转项目带入售前方案和成本基线 |
| 工程技术 | 工程技术中心 | `/engineering/workbench` | `project_id / review_id / ecn_id / spec_id` | 技术评审结论、设计输出、ECN 影响、工程未决项 | PM 能在项目上下文看到工程问题和 ECN |
| BOM/采购/仓储 | 供应链中心 | `/supply-chain/workbench` | `project_id / bom_id / material_id / purchase_order_id` | BOM 发布、物料需求、缺料、到货、齐套率、库存 | 项目能看到齐套率和关键缺料 |
| 生产/装配 | 生产执行中心 | `/production/workbench` | `project_id / work_order_id / assembly_task_id` | 工单进度、领料、装配完成、异常、发货状态 | 生产异常能反写项目风险 |
| 质量/验收/服务 | 质量交付服务中心 | `/delivery-service/workbench` | `project_id / acceptance_order_id / service_ticket_id` | 检验结果、NC、验收问题、服务关闭、满意度 | 验收通过能驱动结算和复盘 |
| 财务/经营 | 财务经营中心 | `/finance/workbench` | `project_id / quote_id / contract_id / settlement_id` | 预算、实际成本、收款、发票、结算、毛利 | 项目能对比报价成本、预算和实际成本 |
| 人力/绩效 | 人力与组织中心 | `/people/workbench` | `user_id / department_id / project_id` | 工时、负荷、能力标签、项目贡献、绩效 | 绩效从真实项目工时和交付贡献取数 |
| 系统治理 | 系统治理中心 | `/system/workbench` | `user_id / role_id / permission_code / menu_id` | 权限、菜单、审批、通知、审计 | 岗位菜单和按钮权限可解释、可测试 |

## 统一协同任务模型

售前技术支持、项目问题、工程评审、ECN、采购缺料、生产异常、验收问题，本质都是“跨部门协同任务”。不要每个模块都重新造一套散工单。

建议沉淀一个通用协同任务口径，先不一定马上新建大表，但新功能都按这个字段组织：

- `source_domain`：来源中心，例如 `sales / project / production`
- `source_id`：来源对象，例如 `opportunity_id / project_id / work_order_id`
- `target_domain`：承接中心，例如 `presale / engineering / supply_chain`
- `task_type`：协同类型，例如 `SOLUTION_REVIEW / ECN_REVIEW / SHORTAGE_RESOLVE`
- `assignee_id / owner_role`：责任人或责任角色
- `deliverables`：方案、图纸、报价资料、检验报告等交付物
- `completion_note`：完成说明、评审结论、异常处理结论
- `outcome`：`APPROVED / REJECTED / NEED_MORE_INFO / RISK_ACCEPTED`
- `next_actions`：下一步动作，必须可回到来源对象
- `linked_project_id / opportunity_id / contract_id`：关键业务链路 ID

第一批先在售前工单上补齐 `completion_note` 和完成进度回流；后续项目、工程、采购、生产、验收都按同一模式补。

## 菜单合并方式

不是把菜单越砍越少，而是让一级菜单按岗位任务清晰。

建议一级菜单：

- 经营
- 销售
- 售前
- 项目
- 工程
- 供应链
- 生产
- 质量交付
- 财务
- 人力
- 系统

每个一级菜单下优先放一个工作台，再放少量高频子入口。低频配置类入口放到对应工作台内，不作为一级导航。

## 权限合并方式

权限不要再按页面碎片无限扩张，应该按业务动作收口。

示例：

- `sales:read`
- `sales:opportunity:manage`
- `presale:ticket:process`
- `presale:solution:review`
- `project:plan`
- `project:risk:manage`
- `engineering:ecn:approve`
- `supply:purchase:execute`
- `warehouse:inventory:manage`
- `production:workorder:execute`
- `quality:inspection:manage`
- `delivery:acceptance:manage`
- `service:ticket:process`
- `finance:settlement:manage`
- `people:performance:manage`
- `system:permission:manage`

岗位看到的是工作台，系统内部再用细权限控制按钮和数据范围。

## 聚合接口模式

每个业务中心都应有两类 API：

### overview

用于工作台总览，返回数字、列表、预警、待办。

格式：

`GET /api/v1/{domain}/workbench/overview`

### context

用于单个业务对象上下文，返回完整链路。

格式：

`GET /api/v1/{domain}/workbench/context`

或者项目类：

`GET /api/v1/projects/{project_id}/{domain}/context`

前端不应该在页面里拼 10-20 个散接口。聚合接口可以内部复用旧服务，先不动底层表。

## 项目交接包 v1

从销售/售前进入后续模块，必须先落到项目交接包。否则后面的工程、采购、生产、验收会继续各自查一遍商机、合同、方案和成本，系统还是散的。

当前第一版接口：

`GET /api/v1/project-workspace/projects/{project_id}/workspace/context`

返回字段：

- `project`：项目基本信息、阶段、状态、健康度、合同金额。
- `contract`：合同编码、合同名称、合同金额、交期、付款条件、签约销售。
- `opportunity`：商机编码、商机名称、项目类型、设备类型、预估金额、验收依据。
- `quote`：报价编码、报价版本、报价金额、报价成本、毛利率、绑定状态。
- `presale_solutions`：售前方案、需求摘要、方案概要、技术规格、预估成本、建议报价。
- `baseline_cost`：项目预算、合同金额、报价成本、售前预估成本、成本来源。
- `handover_status`：是否齐套、缺少哪些关键交接项。

后续模块使用方式：

| 后续模块 | 从交接包直接读取 | 继续补充的数据 | 第一验收点 |
| --- | --- | --- | --- |
| 项目管理 | 合同、商机、售前方案、成本基线 | WBS、里程碑、项目团队、风险 | 项目启动不用重复录合同/方案/成本 |
| 工程技术 | 需求摘要、技术规格、验收依据 | 设计输出、技术评审、ECN、BOM | 工程评审能引用售前冻结需求 |
| 供应链 | 成本基线、设备类型、项目范围 | BOM、物料需求、采购、齐套率 | 采购按项目和关键缺料优先级执行 |
| 生产执行 | 项目范围、交期、BOM/齐套状态 | 工单、装配任务、领料、异常 | 生产异常能反写项目健康和交期风险 |
| 质量验收 | 验收依据、技术规格、交期 | 检验、NC、FAT/SAT、验收问题 | 验收问题能驱动项目风险和结算条件 |
| 财务经营 | 合同金额、报价成本、售前成本 | 实际成本、发票、回款、结算 | 项目毛利能从报价到实际对账 |
| 人力绩效 | 项目、团队、工时入口 | 负荷、能力、贡献、绩效 | 绩效从真实项目贡献取数 |

交接包不是最终大而全模型，而是后续模块共同依赖的最小上下文。后续每补一个中心，都先确认它是否能通过 `project_id` 拿到交接包，再补自己的领域数据。

## 后续模块最小接入契约

后续模块不能再各自从客户、商机、合同、方案里重复找资料。每个中心上线前先满足一个共同前提：

1. 能通过 `project_id` 读取项目交接包。
2. 能把本中心的关键状态反写到项目健康、风险或下一步动作。
3. 前端工作台只调本中心 `overview/context`，不在页面里拼多个散接口。

| 中心 | 必须先接入的上游数据 | 本中心补充数据 | 必须反写的下游信号 | 最小接口 |
| --- | --- | --- | --- | --- |
| 工程技术 | 需求摘要、技术规格、验收依据、成本基线 | 技术评审、设计输出、ECN、BOM 草案、工程未决项 | 设计完成率、ECN 影响、工程风险 | `GET /api/v1/projects/{project_id}/engineering/context` |
| 供应链 | 项目范围、设备类型、成本基线、BOM 状态 | 物料需求、采购申请、采购订单、到货、库存、替代料 | 齐套率、关键缺料、采购延期 | `GET /api/v1/projects/{project_id}/supply-chain/context` |
| 生产执行 | 项目交期、BOM/齐套状态、技术输出 | 工单、装配任务、领料、外协、异常、发货计划 | 工单进度、异常风险、交期偏差 | `GET /api/v1/projects/{project_id}/production/context` |
| 质量交付服务 | 验收依据、技术规格、项目计划、客户信息 | 检验、NC、FAT/SAT、安装派工、验收问题、服务工单 | 验收状态、现场问题、客户满意度 | `GET /api/v1/projects/{project_id}/delivery-service/context` |
| 财务经营 | 合同金额、报价成本、售前预估、项目预算 | 实际成本、付款、发票、结算、毛利 | 毛利偏差、现金风险、结算状态 | `GET /api/v1/projects/{project_id}/finance/context` |
| 人力组织 | 项目团队、阶段计划、工程/生产任务 | 工时、负荷、能力标签、绩效贡献 | 资源缺口、超负荷、绩效输入 | `GET /api/v1/projects/{project_id}/people/context` |

这样做的顺序是先接上下文，再重构页面。否则只改菜单，后面模块仍然会断。

## 实施路线

### Phase 0 - 入口和模块盘点

目标：冻结新增散入口。

动作：

- 生成前端路由矩阵。
- 生成后端 endpoint 矩阵。
- 生成菜单与权限矩阵。
- 给每个旧入口指定归属中心。

验收：

- 每个页面都知道未来属于哪个中心。
- 新功能必须进入某个工作台或子视图。

### Phase 1 - 先合销售到项目主线

目标：先打通公司最核心的拿单到交付。

范围：

- 销售经营中心
- 售前技术中心
- 项目交付中心

动作：

- `/presales/workbench`
- `/project/workbench`
- 售前 overview/context
- 项目 workspace/context
- 商机 -> 售前 -> 方案 -> 报价 -> 合同 -> 立项 -> 项目的对象链

验收：

- 销售能从商机进入售前支持。
- 售前能完成评估、方案、成本。
- 方案通过后 G2 能过。
- 合同签署后能带售前方案和成本基线进入项目。

### Phase 2 - 合工程和项目交付

目标：项目不是只看进度，还能看到工程输出和变更。

范围：

- 项目交付中心
- 工程技术中心

动作：

- 工程 context 接入项目工作台。
- 技术评审、ECN、技术规格、研发项目归入工程中心。
- 项目页展示工程未决事项、设计输出、ECN 影响。

验收：

- 项目经理能在项目上下文看到技术评审和 ECN。
- 工程师能从工程中心看到自己关联项目任务。

### Phase 3 - 合供应链

目标：BOM、采购、缺料、仓库不再各看各的。

范围：

- 供应链中心
- 项目交付中心
- 生产执行中心

动作：

- 建 `/supply-chain/workbench`。
- 建项目供应链 context。
- BOM 发布后生成物料需求。
- 采购、到货、库存、齐套、缺料在同一上下文显示。

验收：

- PM 能看到项目齐套真实状态。
- 采购能按项目/BOM/缺料优先级执行。
- 仓库出入库能反写项目齐套。

### Phase 4 - 合生产执行

目标：计划、工单、装配、领料、外协、发货在一条线上。

范围：

- 生产执行中心
- 供应链中心
- 项目交付中心

动作：

- 建 `/production/workbench`。
- 生产工单关联项目、BOM、领料、装配任务。
- 异常进入统一异常中心，并反写项目风险。

验收：

- 生产看板能按项目看工单和装配状态。
- 缺料/异常能影响项目健康。

### Phase 5 - 合质量、验收、服务

目标：质量问题、现场安装、验收、售后不再断开。

范围：

- 质量交付服务中心
- 项目交付中心
- 财务经营中心

动作：

- 建 `/delivery-service/workbench`。
- 检验、NC、安装派工、验收问题、服务工单进入统一上下文。
- 验收通过驱动结算和项目复盘。

验收：

- 项目能看到验收问题和服务遗留。
- 验收通过后财务能进入结算。
- 服务问题能沉淀知识库。

### Phase 6 - 合财务和经营分析

目标：报价成本、项目成本、实际成本、结算、毛利闭环。

范围：

- 财务经营中心
- 销售经营中心
- 项目交付中心

动作：

- 建 `/finance/workbench`。
- 报价成本、售前成本、项目预算、实际成本、结算对账。
- 财务指标回流经营驾驶舱。

验收：

- 每个项目能看到从报价到实际的成本差异。
- 老板能看到项目毛利和现金风险。

### Phase 7 - 合人力和组织能力

目标：工时、绩效、人岗匹配、任职资格服务项目交付。

范围：

- 人力与组织中心
- 项目交付中心
- 工程技术中心

动作：

- 建 `/people/workbench`。
- 工时、绩效、资格、人岗匹配进入项目资源上下文。
- 工程师负荷和能力标签服务排程、售前、项目。

验收：

- 项目资源分配能看到能力、负荷和历史绩效。
- 绩效能从项目贡献、工时、质量、协作自动取数。

### Phase 8 - 清理旧入口和权限

目标：系统真正变干净。

动作：

- 旧路由统一重定向或删除。
- 菜单压缩到业务中心。
- 权限码合并。
- 保留兼容 API，废弃前端不再使用的 facade。
- 建核心闭环 E2E 测试。

验收：

- 菜单明显减少。
- 新人能按岗位找到工作入口。
- 核心业务不用手工改状态。
- 每个中心有 overview/context 测试。

## 优先级排序

### 第一优先级

销售 -> 售前 -> 报价 -> 合同 -> 项目。

这是拿单和交付入口，直接决定系统能不能用起来。

### 第二优先级

项目 -> 工程 -> BOM -> 采购 -> 齐套。

这是非标自动化交付最大痛点，决定延期和缺料。

### 第三优先级

生产 -> 质量 -> 验收 -> 结算。

这是现金流和客户满意度闭环。

### 第四优先级

人力绩效、知识库、经营驾驶舱。

这些要建立在真实业务数据闭环上，否则容易变成好看的空看板。

## 不建议做的事

- 不建议按部门简单合并页面。
- 不建议只改菜单，不做上下文聚合。
- 不建议把所有模块做成一个超级页面。
- 不建议直接删除旧入口。
- 不建议继续新增散页面。
- 不建议前端继续自己拼多个不稳定接口。

## 最近一周可落地动作

1. 固化全系统归并矩阵。
2. 先做 `/presales/workbench` 统一入口。
3. 建售前 `overview/context` 聚合接口。
4. 设计 `/project/workbench` 的 view 参数和旧路由重定向。
5. 项目 `workspace/context` API 已进入 v1：先接合同、商机、报价成本、售前方案、成本基线。
6. 在项目工作台概览展示“项目交接包”，让 PM 先能用起来。
7. 下一步按同一口径补工程/BOM、采购齐套、生产工单、验收服务上下文。
8. 每做一个中心，补一组路由测试、聚合接口测试、最小 E2E 冒烟测试。

## 最终判断标准

一个 100-200 人非标自动化公司真正用起来，应该满足：

- 销售不用问售前在哪看，商机里能直接申请和跟踪。
- 售前不用在多个页面找需求、评估、方案、成本。
- PM 不用到处问进度，项目工作台能看到工程、采购、生产、质量、财务状态。
- 采购能按项目齐套和缺料优先级做事。
- 生产能按项目、工单、物料、异常组织现场。
- 质量和验收能直接影响项目健康和结算。
- 财务能从报价、预算、实际成本、结算看到毛利。
- 人力绩效能从真实项目贡献和工时取数。
- 老板看到的经营驾驶舱不是手工汇总，而是业务链路自然沉淀。
