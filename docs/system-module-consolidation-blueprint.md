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
5. 开始项目 `workspace/context` API。
6. 每做一个中心，补一组路由测试、聚合接口测试、最小 E2E 冒烟测试。

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
