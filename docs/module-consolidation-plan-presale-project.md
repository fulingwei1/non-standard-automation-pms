# 售前技术支持与项目管理模块合并方案

> 本文是全系统模块合并的第一批落地细化。全局方案见 `docs/system-module-consolidation-blueprint.md`，覆盖销售、售前、项目、工程、供应链、生产、质量交付、财务、人力和系统治理。

## 结论

可以合并，而且应该合并。

当前系统的问题不是单点功能不足，而是同一条业务链被拆成了多个入口、多个状态口径、多个相互不完全对账的页面。正确做法不是一次性删模块，而是先建立统一入口、统一业务对象、统一状态流，再逐步把旧页面变成兼容入口或子视图。

目标主线：

`线索/商机 -> 售前支持 -> 技术评估 -> 方案/成本 -> 报价 -> 合同 -> 立项 -> 项目交付 -> 验收/复盘`

## 当前散点

### 售前技术支持

现有入口分散在：

- 销售侧售前工作台：`/sales/presale-workbench`
- 售前工程师工作台：`/presales-dashboard`
- 售前经理工作台：`/presales-manager-dashboard`
- 售前工单：`/sales/presales-tasks`、`/presales-tasks`
- 技术评估：`/sales/assessments/:sourceType/:sourceId`
- 技术方案：`/presales/solutions`
- 方案详情：`/solutions/:id`
- 技术参数模板：`/presales/technical-parameters`
- 成本估算：`/presales/cost-estimation`
- 投标：`/presales/bids`
- 模板库：`/presales/templates`、`/presale-templates`
- 项目侧售前工单：`/project-presales-tasks`

后端也分散在：

- `/api/v1/sales/assessments...`
- `/api/v1/sales/funnel...`
- `/api/v1/presale/tickets...`
- `/api/v1/presale/proposals/solutions...`
- `/api/v1/presale/technical-parameters...`
- `/api/v1/presale/tenders...`

已经修过的一处关键闭环：

- 方案评审通过后，已能反写商机技术评估，G2 阶段门可以识别真实 `TechnicalAssessment`。

### 项目管理

项目管理也有类似散点：

- 项目看板：`/board`
- 项目详情：`/projects/:id`
- 项目工作区：`/projects/:id/workspace`
- PMO 驾驶舱：`/pmo/dashboard`
- 进度跟踪：`/progress-tracking/...`
- 甘特与资源：`/gantt-resource`
- AI 项目工具：`/ai-project-tools`
- 项目健康：`/project-health-monitor`
- 项目成本中心：`/project/cost-center`
- 项目收尾：`/project-closing`
- 里程碑、任务、资源、风险、变更、验收、复盘散在不同路径

这会导致 PM、工程、采购、装配、老板看到的是不同切片，而不是同一个项目上下文。

## 合并原则

1. 不做大爆炸重构

先统一入口和数据口径，旧路由先保留并重定向。等新入口稳定后，再逐步下线旧入口。

2. 一个业务对象一条主线

售前以 `opportunity_id / presale_ticket_id / assessment_id / solution_id` 串起来。

项目以 `project_id` 串起合同、立项、WBS、任务、资源、成本、风险、变更、验收、复盘。

3. 一个模块一个工作台

用户不应该在菜单里猜功能位置。每个大模块只保留一个主入口：

- 售前技术支持：`/presales/workbench`
- 项目管理：`/project/management-center`
- 销售闭环：`/sales/workstation`

4. 旧功能变子视图，不做重复页面

例如售前工单、技术评估、方案、成本估算、模板、投标，不再作为彼此孤立的一级入口，而是统一挂到售前工作台下的不同视图。

5. 状态必须服务流程

不能只显示状态字段。状态要能驱动下一步动作，例如：

- 商机缺技术评估 -> 申请售前支持
- 工单处理中 -> 售前工程师补需求/评估/方案
- 方案评审通过 -> G2 可以报价
- 合同签署 -> 立项/项目创建
- 项目启动 -> WBS/资源/采购/风险自动进入项目上下文

## 售前技术支持合并后的形态

### 统一入口

新主入口：

`/presales/workbench`

旧入口兼容：

- `/presales-workbench` -> `/presales/workbench`
- `/sales/presale-workbench` -> `/presales/workbench`
- `/sales/presales-workbench` -> `/presales/workbench`
- `/presales-dashboard` 保留为“售前执行视图”
- `/presales-manager-dashboard` 保留为“售前经理视图”

### 工作台一级视图

售前工作台建议保留 6 个视图：

1. 总览
   - 工单数量、待处理、超期、方案数量、评估状态、漏斗健康、SLA。

2. 需求与评估
   - 线索/商机需求包、技术评估、风险、未决事项、需求冻结。

3. 工单执行
   - 售前支持工单、分派、进度、交付物、满意度。

4. 方案与成本
   - 方案列表、方案详情、成本估算、技术参数模板、方案评审。

5. 投标与报价协同
   - 投标记录、方案/成本/报价联动、赢率预测。

6. 经理看板
   - 工程师负荷、响应时效、瓶颈、返工、赢单贡献。

### 当前落地状态

截至 2026-06-07，已先把售前技术支持的执行入口收敛到：

`/presales/technical-solutions`

中心内已包含：

- 需求调研
- 方案管理
- 技术参数
- 成本估算
- 投标支持
- 知识模板
- 工单看板

以下旧入口已改为兼容跳转：

- `/requirement-survey` -> `tab=surveys`
- `/presales/solutions`、`/solutions` -> `tab=solutions`
- `/presales/technical-parameters` -> `tab=parameters`
- `/presales/cost-estimation` -> `tab=cost`
- `/bidding`、`/presales/bids` -> `tab=bids`
- `/presales/templates`、`/presale-templates` -> `tab=knowledge`
- `/presales-tasks`、`/presales/ticket-board`、`/presales/assessments` -> `tab=reviews`
- `/sales/presales-tasks`、`/project-presales-tasks` -> `tab=reviews`，并保留原查询参数。

本次没有把全局 `/knowledge-base` 并入售前中心。它仍作为公司级知识库保留，售前专用模板走 `PresaleTemplates`。

### 统一数据上下文

建议后端新增聚合接口，前端不再自己拼十几个接口：

`GET /api/v1/presale/workbench/overview`

返回：

- tickets
- assessments
- solutions
- technical_templates
- tenders
- funnel_health
- alerts
- workload

上下文接口：

`GET /api/v1/presale/workbench/context`

参数：

- `source_type=LEAD|OPPORTUNITY`
- `source_id`
- `ticket_id`

返回同一业务上下文：

- lead/opportunity
- ticket
- current_assessment
- solutions
- costs
- gate_status
- open_items
- requirement_freezes
- next_actions

### 售前核心动作

统一成这些动作，而不是散落按钮：

- 申请售前支持
- 分派售前工程师
- 补充需求包
- 发起/执行技术评估
- 创建方案
- 提交方案评审
- 审批方案
- 估算成本
- 推进 G2 报价
- 关闭工单

## 项目管理合并后的形态

### 统一入口

新主入口：

`/project/management-center`

旧入口兼容：

- `/board` -> `/project/management-center?tab=board`
- `/projects` -> `/project/management-center?tab=board&view=card`
- `/stage-view`、`/projects/stage-view` -> `/project/management-center?tab=board&view=pipeline`
- `/pmo/dashboard`、`/project/dashboard-center` -> `/project/management-center?tab=dashboard`
- `/project-health-monitor` -> `/project/management-center?tab=dashboard&dashboardTab=health`
- `/progress-tracking/tasks`、`/tasks` -> `/project/management-center?tab=tasks`
- `/progress-tracking/schedule`、`/schedule` -> `/project/management-center?tab=tracking&trackingTab=schedule`
- `/progress-tracking/reports` -> `/project/management-center?tab=tracking&trackingTab=reports`
- `/progress-tracking/milestones`、`/milestones` -> `/project/management-center?tab=tracking&trackingTab=milestones`
- `/progress-tracking/wbs`、`/wbs-templates` -> `/project/management-center?tab=tracking&trackingTab=wbs`
- `/gantt-resource`、`/gantt` -> `/project/management-center?tab=planning`
- `/resource-overview`、`/progress-tracking/resource-overview` -> `/project/management-center?tab=planning&planningTab=resource`
- `/ai-project-tools` -> `/project/management-center?tab=ai`
- `/schedule-generation`、`/engineer-recommendation` -> `/project/management-center?tab=ai`
- `/project/cost-center` -> `/project/management-center?tab=cost`
- `/time-cost-margin-flow` -> `/project/management-center?tab=cost&costTab=margin`
- `/project-closing` -> `/project/management-center?tab=closing`
- `/pmo/closure`、`/projects/reviews`、`/lessons-learned` -> `/project/management-center?tab=closing`

### 项目工作台一级视图

项目管理第一版已经合成 8 个视图：

1. 看板
   - 全部项目、卡片视图、看板、列表、流水线视图。

2. 驾驶舱
   - PMO 总览、项目健康监控。

3. 任务
   - 个人/项目任务中心。

4. 进度
   - 排期看板、进度报告、里程碑、WBS 模板。

5. 计划资源
   - 任务甘特、资源甘特、人员负荷。

6. 成本
   - 预算、工时成本、毛利联动。

7. 收尾
   - 结项、复盘、经验教训。

8. AI 工具
   - 智能排计划、工程师调度。

暂未并入中心的专业深链继续保留，例如 `/projects/:id/*`、ECN 详情、验收详情、项目物料进度等。这些页面不作为一级菜单暴露，后续从项目详情和项目中心上下文进入。

### 项目统一上下文

建议后端新增：

`GET /api/v1/projects/{project_id}/workspace/context`

返回：

- project
- contract
- customer
- opportunity
- presale_solution
- team
- milestones
- tasks
- schedule
- resources
- costs
- risks
- changes
- issues
- acceptance
- lessons
- next_actions

这样项目详情、项目看板、PMO、甘特、成本、复盘都不再各查各的。

## 权限和菜单合并

### 售前权限

建议收口到：

- `presale:read`
- `presale:ticket:create`
- `presale:ticket:assign`
- `presale:ticket:process`
- `presale:assessment:evaluate`
- `presale:solution:create`
- `presale:solution:review`
- `presale:manager`

销售人员可以申请和查看自己相关售前支持；售前工程师处理被分派工单；售前经理看全量和分派。

### 项目权限

建议收口到：

- `project:read`
- `project:create`
- `project:plan`
- `project:task:manage`
- `project:resource:manage`
- `project:cost:read`
- `project:risk:manage`
- `project:change:manage`
- `project:acceptance:manage`
- `project:closing:manage`
- `project:pmo`

菜单不直接按数据库表/页面命名，而按岗位任务命名。

## 实施路线

### Phase 0 - 盘点与冻结

目标：不再继续新增散入口。

动作：

- 拉出现有菜单、前端路由、后端路由、权限码矩阵。
- 标记每个入口属于“售前技术支持”还是“项目管理”。
- 给所有旧入口指定未来归属。

验收：

- 有一张入口归并表。
- 新功能只能进统一工作台或其子视图。

### Phase 1 - 售前入口合并

目标：用户只记一个售前入口。

动作：

- 建 `/presales/workbench` 作为统一入口。
- `/sales/presale-workbench`、`/presales-workbench` 重定向到统一入口。
- 在统一入口保留销售协同、售前执行、经理调度三个角色视图入口。
- 旧页面暂时保留。

验收：

- 销售、售前工程师、售前经理都能从统一入口进入自己的工作。
- 旧链接不 404。

### Phase 2 - 售前数据合并

目标：前端不再拼散接口。

动作：

- 新增 `/api/v1/presale/workbench/overview`。
- 新增 `/api/v1/presale/workbench/context`。
- 把售前工作台数据加载迁到聚合接口。
- 保留旧 API，内部可复用服务。

验收：

- 工作台一次加载能展示工单、评估、方案、模板、漏斗健康。
- 单个商机上下文能看到评估、工单、方案、G2 状态。

### Phase 3 - 售前流程合并

目标：销售到报价真正走通。

动作：

- 从商机一键申请售前支持。
- 工单接单后可补需求、发起/执行评估、创建方案。
- 方案评审通过后自动满足 G2 技术评估条件。
- 报价入口读取方案和成本。

验收：

- 从商机到报价不需要手工改状态。
- G2 阶段门失败原因可读，修完后可通过。

### Phase 4 - 项目入口合并

目标：项目管理只保留一个主入口。

动作：

- 已建 `/project/management-center`。
- 项目看板、PMO、任务、进度、甘特、资源、成本、健康、收尾、AI 工具进入同一中心页签。
- 旧路径重定向到对应 `tab`，并保留原查询参数。

验收：

- PM 从一个入口能完成项目总览、计划、资源、进度、成本、风险、验收。
- 老链接不 404。

### Phase 5 - 项目上下文合并

目标：项目模块不再各查各的。

动作：

- 新增 `/api/v1/projects/{project_id}/workspace/context`。
- 项目详情、项目工作区、甘特、成本、风险、验收统一读取该上下文。
- 合同转项目时带入销售、报价、售前方案、成本基线。

验收：

- 项目经理打开项目能看到合同、报价、售前方案、范围、预算、节点。
- 项目成本和售前成本能对账。

### Phase 6 - 清理重复模块

目标：真正变干净。

动作：

- 删除或归档无人访问的旧页面。
- 清理重复 API facade。
- 清理无效权限码和菜单。
- 给关键闭环补合同测试和 E2E 冒烟测试。

验收：

- 菜单减少，入口清晰。
- 用户路径比现在短。
- 核心闭环有测试保护。

## 不建议做的事

- 不建议一开始就删除旧页面，容易造成断链。
- 不建议只改菜单，不改数据上下文；这样只是表面合并。
- 不建议把售前技术评估完全并进销售模块；售前有自己的执行和经理视角。
- 不建议把项目管理所有页面塞进一个超大页面；应该是一个工作台，多视图，多上下文。

## 最近可执行的下一步

先沿着本次售前和项目中心化的样板继续做三件事：

1. 做售前到项目交接包：赢单后把客户、合同、需求、方案、参数、成本、风险、里程碑和未闭环事项带入项目。
2. 把项目中心的专业深链继续按项目上下文接入：技术评审、风险变更、ECN、验收、交付、售后。
3. 把售前中心和项目中心的数据加载从多个散接口逐步迁到统一上下文接口。

这三步完成后，系统才会从“很多模块都有”变成“从销售到交付能按一条线跑”。

## 最终验收口径

### 售前技术支持

销售人员能从商机进入售前支持，看到技术评估、售前工单、方案、成本、G2 阶段门状态。

售前工程师能从统一入口看到自己的工单，完成需求、评估、方案、成本、交付物。

售前经理能看到工单池、负荷、超期、方案评审、瓶颈。

### 项目管理

合同签署后能带着商机、报价、售前方案、成本基线进入项目。

项目经理能从一个项目工作台看到计划、任务、资源、工时、成本、风险、变更、验收、复盘。

老板能从项目总览看到真实健康度、延期、毛利和关键风险。
