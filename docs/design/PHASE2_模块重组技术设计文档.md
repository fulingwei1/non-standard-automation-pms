# Phase 2 技术设计文档 - 模块重组方案

> **文档版本**: v1.0
> **创建日期**: 2026-01-25
> **作者**: PMO技术团队
> **状态**: 设计完成，待实施

---

## 一、项目概述

### 1.1 目标

将分散在多个模块的功能进行重组，形成3个独立的大模块：
1. **成本报价管理**：整合所有成本报价相关功能
2. **变更管理**：整合所有ECN变更相关功能
3. **进度跟踪**：整合所有进度跟踪相关功能

### 1.2 背景

当前系统功能分散在多个模块：
- **成本报价相关**：分散在销售管理、采购管理、财务管理、采购工程师菜单中
- **变更管理相关**：分散在项目管理模块
- **进度跟踪相关**：分散在项目管理模块

这种分散导致：
- 用户查找困难
- 功能定位不清晰
- 代码重复维护困难

### 1.3 范围

本次重组涉及后端API、前端路由、菜单配置，不涉及数据库表结构调整（仅新增索引和关联字段）。

---

## 二、模块架构设计

### 2.1 成本报价管理模块

#### 2.1.1 模块结构

```
app/api/v1/endpoints/cost_quote/
├── __init__.py              # 路由聚合
├── quotes.py                # 报价管理
├── cost_management.py        # 报价成本管理
├── cost_analysis.py         # 报价成本分析
├── material_costs.py        # 物料成本管理
├── financial_costs.py       # 财务成本管理
├── budget.py               # 成本预算管理
└── templates.py            # 模板与CPQ配置
```

#### 2.1.2 API路由设计

```python
# app/api/v1/endpoints/cost_quote/__init__.py

from fastapi import APIRouter
from . import quotes, cost_management, cost_analysis, material_costs, financial_costs, budget, templates

router = APIRouter()

# 报价管理
router.include_router(quotes.router, prefix="/quotes", tags=["cost-quote-quotes"])

# 成本管理
router.include_router(cost_management.router, prefix="/cost-management", tags=["cost-quote-costs"])

# 成本分析
router.include_router(cost_analysis.router, prefix="/cost-analysis", tags=["cost-quote-analysis"])

# 物料成本
router.include_router(material_costs.router, prefix="/material-costs", tags=["cost-quote-materials"])

# 财务成本
router.include_router(financial_costs.router, prefix="/financial-costs", tags=["cost-quote-financial"])

# 成本预算
router.include_router(budget.router, prefix="/budget", tags=["cost-quote-budget"])

# 模板与CPQ
router.include_router(templates.router, prefix="/templates", tags=["cost-quote-templates"])
```

#### 2.1.3 路由迁移映射表

| 原路由 | 新路由 | 说明 |
|---------|---------|------|
| `/api/v1/sales/quotes` | `/api/v1/cost-quote/quotes` | 报价列表/详情 |
| `/api/v1/sales/quotes/:id/cost` | `/api/v1/cost-quote/cost-management/quotes/:id` | 报价成本管理 |
| `/api/v1/sales/quotes/:id/cost-analysis` | `/api/v1/cost-quote/cost-analysis/quotes/:id` | 报价成本分析 |
| `/api/v1/sales/purchase-material-costs` | `/api/v1/cost-quote/material-costs` | 物料成本（去重） |
| `/api/v1/financial-costs` | `/api/v1/cost-quote/financial-costs` | 财务成本 |
| `/api/v1/sales/templates` | `/api/v1/cost-quote/templates` | 模板与CPQ |

#### 2.1.4 重定向策略

```python
# app/api/v1/endpoints/__deprecated__.py

from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse

deprecated_router = APIRouter()

@deprecated_router.get("/sales/quotes")
@deprecated_router.get("/sales/quotes/{path:path}")
async def redirect_quotes(path: str):
    """旧报价路由重定向"""
    return RedirectResponse(
        url=f"/api/v1/cost-quote/quotes/{path}",
        status_code=301
    )

@deprecated_router.get("/sales/purchase-material-costs")
async def redirect_material_costs():
    """旧物料成本路由重定向"""
    return RedirectResponse(
        url="/api/v1/cost-quote/material-costs",
        status_code=301
    )

# 在 api.py 中注册
api_router.include_router(
    deprecated_router,
    prefix="/api/v1",
    tags=["deprecated-redirects"]
)
```

---

### 2.2 变更管理模块

#### 2.2.1 模块结构

```
app/api/v1/endpoints/change_management/
├── __init__.py              # 路由聚合
├── ecns.py                  # ECN管理（列表、详情）
├── evaluations.py            # ECN评估
├── approvals.py              # ECN审批
├── execution.py              # ECN执行
├── impacts.py                # ECN影响分析
└── tasks.py                 # ECN任务管理
```

#### 2.2.2 API路由设计

```python
# app/api/v1/endpoints/change_management/__init__.py

from fastapi import APIRouter
from . import ecns, evaluations, approvals, execution, impacts, tasks

router = APIRouter()

# ECN管理
router.include_router(ecns.router, prefix="/ecns", tags=["change-ecns"])

# ECN评估
router.include_router(evaluations.router, prefix="/ecns/{ecn_id}/evaluations", tags=["change-evaluations"])

# ECN审批
router.include_router(approvals.router, prefix="/ecns/{ecn_id}/approvals", tags=["change-approvals"])

# ECN执行
router.include_router(execution.router, prefix="/ecns/{ecn_id}/execution", tags=["change-execution"])

# ECN影响分析
router.include_router(impacts.router, prefix="/ecns/{ecn_id}/impacts", tags=["change-impacts"])

# ECN任务
router.include_router(tasks.router, prefix="/ecns/{ecn_id}/tasks", tags=["change-tasks"])
```

#### 2.2.3 路由迁移映射表

| 原路由 | 新路由 | 说明 |
|---------|---------|------|
| `/api/v1/ecn` | `/api/v1/change-management/ecns` | ECN列表/详情 |
| `/api/v1/ecn/:id` | `/api/v1/change-management/ecns/:id` | ECN详情 |
| `/api/v1/ecn-types` | `/api/v1/change-management/ecn-types` | ECN类型管理 |
| `/api/v1/ecn/overdue-alerts` | `/api/v1/change-management/ecns/overdue-alerts` | ECN逾期预警 |
| `/api/v1/ecn/statistics` | `/api/v1/change-management/ecns/statistics` | ECN统计 |

#### 2.2.4 重定向策略

```python
@deprecated_router.get("/ecn")
@deprecated_router.get("/ecn/{path:path}")
async def redirect_ecns(path: str):
    """旧ECN路由重定向"""
    return RedirectResponse(
        url=f"/api/v1/change-management/ecns/{path}",
        status_code=301
    )
```

---

### 2.3 进度跟踪模块

#### 2.3.1 模块结构

```
app/api/v1/endpoints/progress_tracking/
├── __init__.py              # 路由聚合
├── tasks.py                 # 任务中心
├── progress_entry.py         # 进度填报
├── board.py                 # 进度看板（项目看板、排期看板）
├── wbs.py                  # WBS管理
├── milestones.py            # 里程碑管理
├── reports.py              # 进度报告
├── gantt.py                # 甘特图
├── forecast.py             # 进度预测
├── analysis.py             # 进度分析
└── dependencies.py         # 依赖关系管理
```

#### 2.3.2 API路由设计

```python
# app/api/v1/endpoints/progress_tracking/__init__.py

from fastapi import APIRouter
from . import tasks, progress_entry, board, wbs, milestones, reports, gantt, forecast, analysis, dependencies

router = APIRouter()

# 任务管理
router.include_router(tasks.router, prefix="/tasks", tags=["progress-tasks"])

# 进度填报
router.include_router(progress_entry.router, prefix="/progress-entry", tags=["progress-entry"])

# 进度看板
router.include_router(board.router, prefix="/board", tags=["progress-board"])

# WBS管理
router.include_router(wbs.router, prefix="/wbs", tags=["progress-wbs"])

# 里程碑管理
router.include_router(milestones.router, prefix="/milestones", tags=["progress-milestones"])

# 进度报告
router.include_router(reports.router, prefix="/reports", tags=["progress-reports"])

# 甘特图
router.include_router(gantt.router, prefix="/gantt", tags=["progress-gantt"])

# 进度预测
router.include_router(forecast.router, prefix="/forecast", tags=["progress-forecast"])

# 进度分析
router.include_router(analysis.router, prefix="/analysis", tags=["progress-analysis"])

# 依赖关系
router.include_router(dependencies.router, prefix="/dependencies", tags=["progress-dependencies"])
```

#### 2.3.3 路由迁移映射表

| 原路由 | 新路由 | 说明 |
|---------|---------|------|
| `/api/v1/tasks` | `/api/v1/progress-tracking/tasks` | 任务中心 |
| `/api/v1/board` | `/api/v1/progress-tracking/board` | 项目看板 |
| `/api/v1/schedule` | `/api/v1/progress-tracking/board/schedule` | 排期看板 |
| `/projects/:id/tasks` | `/api/v1/progress-tracking/tasks?project_id=` | 项目任务列表 |
| `/projects/:id/board` | `/api/v1/progress-tracking/board?project_id=` | 项目看板 |
| `/projects/:id/gantt` | `/api/v1/progress-tracking/gantt?project_id=` | 项目甘特图 |
| `/projects/:id/wbs` | `/api/v1/progress-tracking/wbs?project_id=` | 项目WBS |
| `/projects/:id/milestones` | `/api/v1/progress-tracking/milestones?project_id=` | 项目里程碑 |

#### 2.3.4 重定向策略

```python
@deprecated_router.get("/tasks")
@deprecated_router.get("/tasks/{path:path}")
async def redirect_tasks(path: str):
    """旧任务路由重定向"""
    return RedirectResponse(
        url=f"/api/v1/progress-tracking/tasks/{path}",
        status_code=301
    )

@deprecated_router.get("/board")
@deprecated_router.get("/schedule")
async def redirect_board(path: str):
    """旧看板路由重定向"""
    return RedirectResponse(
        url=f"/api/v1/progress-tracking/board/{path}",
        status_code=301
    )
```

---

## 三、前端模块架构设计

### 3.1 侧边栏菜单配置

```typescript
// frontend/src/components/layout/Sidebar.tsx

const defaultNavGroups: NavGroup[] = [
  // ... 保留的其他模块

  {
    title: "成本报价管理",
    icon: "💰",
    items: [
      { title: "报价管理", path: "/cost-quote/quotes" },
      { title: "成本管理", path: "/cost-quote/cost-management" },
      { title: "成本分析", path: "/cost-quote/cost-analysis" },
      { title: "模板管理", path: "/cost-quote/templates" },
    ]
  },
  {
    title: "变更管理",
    icon: "🔄",
    items: [
      { title: "ECN管理", path: "/change-management/ecns" },
      { title: "影响分析", path: "/change-management/impacts" },
    ]
  },
  {
    title: "进度跟踪",
    icon: "📊",
    items: [
      { title: "任务中心", path: "/progress-tracking/tasks" },
      { title: "进度看板", path: "/progress-tracking/board" },
      { title: "WBS管理", path: "/progress-tracking/wbs" },
      { title: "里程碑", path: "/progress-tracking/milestones" },
      { title: "进度报告", path: "/progress-tracking/reports" },
      { title: "甘特图", path: "/progress-tracking/gantt" },
    ]
  },

  // 移除或调整的原模块
  // - 销售管理：移除报价相关菜单项
  // - 采购管理：移除物料成本相关菜单项
  // - 财务管理：移除财务成本相关菜单项（或合并到成本报价）
  // - 项目管理：移除任务中心、进度看板、里程碑相关菜单项
]
```

### 3.2 前端路由配置

```typescript
// frontend/src/App.tsx

const routes = [
  // ... 保留的其他路由

  // 成本报价管理模块路由
  {
    path: "/cost-quote",
    element: <CostQuoteLayout />,
    children: [
      { path: "quotes", element: <QuotesList /> },
      { path: "quotes/:id", element: <QuoteDetail /> },
      { path: "cost-management", element: <CostManagement /> },
      { path: "cost-management/:id", element: <CostDetail /> },
      { path: "cost-analysis", element: <CostAnalysis /> },
      { path: "cost-analysis/:id", element: <QuoteCostAnalysis /> },
      { path: "material-costs", element: <MaterialCosts /> },
      { path: "material-costs/:id", element: <MaterialCostDetail /> },
      { path: "financial-costs", element: <FinancialCosts /> },
      { path: "budget", element: <BudgetManagement /> },
      { path: "budget/:id", element: <BudgetDetail /> },
      { path: "templates", element: <TemplatesManagement /> },
      { path: "templates/quotes", element: <QuoteTemplates /> },
      { path: "templates/costs", element: <CostTemplates /> },
      { path: "templates/cpq", element: <CPQConfig /> },
    ]
  },

  // 变更管理模块路由
  {
    path: "/change-management",
    element: <ChangeManagementLayout />,
    children: [
      { path: "ecns", element: <ECNList /> },
      { path: "ecns/create", element: <ECNCreate /> },
      { path: "ecns/:id", element: <ECNDetail /> },
      { path: "ecns/:id/evaluations", element: <ECNEvaluations /> },
      { path: "ecns/:id/approvals", element: <ECNApprovals /> },
      { path: "ecns/:id/execution", element: <ECNExecution /> },
      { path: "ecns/:id/impacts", element: <ECNImpacts /> },
      { path: "ecns/:id/tasks", element: <ECNTasks /> },
      { path: "impacts", element: <ImpactsAnalysis /> },
    ]
  },

  // 进度跟踪模块路由
  {
    path: "/progress-tracking",
    element: <ProgressTrackingLayout />,
    children: [
      { path: "tasks", element: <TasksCenter /> },
      { path: "tasks/:id", element: <TaskDetail /> },
      { path: "tasks/create", element: <TaskCreate /> },
      { path: "progress-entry", element: <ProgressEntry /> },
      { path: "board", element: <ProgressBoard /> },
      { path: "board/project", element: <ProjectBoard /> },
      { path: "board/schedule", element: <ScheduleBoard /> },
      { path: "wbs", element: <WBSManagement /> },
      { path: "wbs/templates", element: <WBSTemplates /> },
      { path: "wbs/:project_id", element: <ProjectWBS /> },
      { path: "milestones", element: <MilestonesManagement /> },
      { path: "milestones/:id", element: <MilestoneDetail /> },
      { path: "reports", element: <ProgressReports /> },
      { path: "reports/daily", element: <DailyReport /> },
      { path: "reports/weekly", element: <WeeklyReport /> },
      { path: "reports/monthly", element: <MonthlyReport /> },
      { path: "gantt", element: <GanttChart /> },
      { path: "gantt/:project_id", element: <ProjectGantt /> },
      { path: "forecast", element: <ProgressForecast /> },
      { path: "forecast/:project_id", element: <ProjectForecast /> },
      { path: "analysis", element: <ProgressAnalysis /> },
      { path: "analysis/:project_id", element: <ProjectAnalysis /> },
      { path: "dependencies", element: <DependenciesManagement /> },
      { path: "dependencies/:project_id", element: <ProjectDependencies /> },
    ]
  },
]
```

---

## 四、实施计划

### 4.1 Phase 2.1: 成本报价管理模块重组

**预计工作量**: 3天

| 任务 | 预计时间 | 负责人 |
|------|----------|--------|
| 创建模块目录结构 | 0.5天 | 后端开发 |
| 迁移报价管理功能 | 0.5天 | 后端开发 |
| 迁移成本管理功能 | 0.5天 | 后端开发 |
| 迁移成本分析功能 | 0.5天 | 后端开发 |
| 迁移物料成本功能 | 0.5天 | 后端开发 |
| 迁移财务成本功能 | 0.5天 | 后端开发 |
| 迁移模板与CPQ功能 | 0.5天 | 后端开发 |
| 配置路由和重定向 | 0.5天 | 后端开发 |
| 测试验证 | 0.5天 | 测试开发 |

### 4.2 Phase 2.2: 变更管理模块重组

**预计工作量**: 2天

| 任务 | 预计时间 | 负责人 |
|------|----------|--------|
| 创建模块目录结构 | 0.5天 | 后端开发 |
| 迁移ECN管理功能 | 0.5天 | 后端开发 |
| 迁移ECN评估功能 | 0.5天 | 后端开发 |
| 迁移ECN审批功能 | 0.5天 | 后端开发 |
| 迁移ECN执行功能 | 0.5天 | 后端开发 |
| 迁移ECN影响分析功能 | 0.5天 | 后端开发 |
| 迁移ECN任务管理功能 | 0.5天 | 后端开发 |
| 配置路由和重定向 | 0.5天 | 后端开发 |
| 测试验证 | 0.5天 | 测试开发 |

### 4.3 Phase 2.3: 进度跟踪模块重组

**预计工作量**: 3天

| 任务 | 预计时间 | 负责人 |
|------|----------|--------|
| 创建模块目录结构 | 0.5天 | 后端开发 |
| 迁移任务中心功能 | 0.5天 | 后端开发 |
| 迁移进度填报功能 | 0.5天 | 后端开发 |
| 迁移进度看板功能 | 0.5天 | 后端开发 |
| 迁移WBS管理功能 | 0.5天 | 后端开发 |
| 迁移里程碑管理功能 | 0.5天 | 后端开发 |
| 迁移进度报告功能 | 0.5天 | 后端开发 |
| 迁移甘特图功能 | 0.5天 | 后端开发 |
| 迁移进度预测功能 | 0.5天 | 后端开发 |
| 迁移进度分析功能 | 0.5天 | 后端开发 |
| 迁移依赖关系功能 | 0.5天 | 后端开发 |
| 配置路由和重定向 | 0.5天 | 后端开发 |
| 测试验证 | 0.5天 | 测试开发 |

**总工作量**: 约8-10天

---

## 五、前端实施计划

### 5.1 成本报价管理模块前端

**预计工作量**: 3天

| 任务 | 预计时间 | 负责人 |
|------|----------|--------|
| 创建模块布局组件 | 0.5天 | 前端开发 |
| 迁移报价管理页面 | 0.5天 | 前端开发 |
| 迁移成本管理页面 | 0.5天 | 前端开发 |
| 迁移成本分析页面 | 0.5天 | 前端开发 |
| 迁移物料成本页面 | 0.5天 | 前端开发 |
| 迁移财务成本页面 | 0.5天 | 前端开发 |
| 迁移模板与CPQ页面 | 0.5天 | 前端开发 |
| 更新侧边栏菜单 | 0.5天 | 前端开发 |
| 测试验证 | 0.5天 | 测试开发 |

### 5.2 变更管理模块前端

**预计工作量**: 2天

| 任务 | 预计时间 | 负责人 |
|------|----------|--------|
| 创建模块布局组件 | 0.5天 | 前端开发 |
| 迁移ECN管理页面 | 0.5天 | 前端开发 |
| 迁移ECN评估页面 | 0.5天 | 前端开发 |
| 迁移ECN审批页面 | 0.5天 | 前端开发 |
| 迁移ECN执行页面 | 0.5天 | 前端开发 |
| 迁移ECN影响分析页面 | 0.5天 | 前端开发 |
| 迁移ECN任务管理页面 | 0.5天 | 前端开发 |
| 更新侧边栏菜单 | 0.5天 | 前端开发 |
| 测试验证 | 0.5天 | 测试开发 |

### 5.3 进度跟踪模块前端

**预计工作量**: 3天

| 任务 | 预计时间 | 负责人 |
|------|----------|--------|
| 创建模块布局组件 | 0.5天 | 前端开发 |
| 迁移任务中心页面 | 0.5天 | 前端开发 |
| 迁移进度填报页面 | 0.5天 | 前端开发 |
| 迁移进度看板页面 | 0.5天 | 前端开发 |
| 迁移WBS管理页面 | 0.5天 | 前端开发 |
| 迁移里程碑管理页面 | 0.5天 | 前端开发 |
| 迁移进度报告页面 | 0.5天 | 前端开发 |
| 迁移甘特图页面 | 0.5天 | 前端开发 |
| 迁移进度预测页面 | 0.5天 | 前端开发 |
| 迁移进度分析页面 | 0.5天 | 前端开发 |
| 迁移依赖关系页面 | 0.5天 | 前端开发 |
| 更新侧边栏菜单 | 0.5天 | 前端开发 |
| 测试验证 | 0.5天 | 测试开发 |

**总工作量**: 约8-10天

---

## 六、API端点迁移清单

### 6.1 成本报价管理

| 序号 | 原端点 | 新端点 | 动作 |
|------|---------|---------|------|
| 1 | `/api/v1/sales/quotes` | `/api/v1/cost-quote/quotes` | 迁移 |
| 2 | `/api/v1/sales/quotes/:id/cost` | `/api/v1/cost-quote/cost-management/quotes/:id` | 迁移 |
| 3 | `/api/v1/sales/quotes/:id/cost-analysis` | `/api/v1/cost-quote/cost-analysis/quotes/:id` | 迁移 |
| 4 | `/api/v1/sales/templates` | `/api/v1/cost-quote/templates` | 迁移 |
| 5 | `/api/v1/sales/purchase-material-costs` | `/api/v1/cost-quote/material-costs` | 迁移 |
| 6 | `/api/v1/financial-costs` | `/api/v1/cost-quote/financial-costs` | 迁移 |

### 6.2 变更管理

| 序号 | 原端点 | 新端点 | 动作 |
|------|---------|---------|------|
| 1 | `/api/v1/ecn` | `/api/v1/change-management/ecns` | 迁移 |
| 2 | `/api/v1/ecn/:id` | `/api/v1/change-management/ecns/:id` | 迁移 |
| 3 | `/api/v1/ecn-types` | `/api/v1/change-management/ecn-types` | 迁移 |
| 4 | `/api/v1/ecn/overdue-alerts` | `/api/v1/change-management/ecns/overdue-alerts` | 迁移 |
| 5 | `/api/v1/ecn/statistics` | `/api/v1/change-management/ecns/statistics` | 迁移 |

### 6.3 进度跟踪

| 序号 | 原端点 | 新端点 | 动作 |
|------|---------|---------|------|
| 1 | `/api/v1/tasks` | `/api/v1/progress-tracking/tasks` | 迁移 |
| 2 | `/api/v1/tasks/:id` | `/api/v1/progress-tracking/tasks/:id` | 迁移 |
| 3 | `/api/v1/board` | `/api/v1/progress-tracking/board` | 迁移 |
| 4 | `/api/v1/schedule` | `/api/v1/progress-tracking/board/schedule` | 迁移 |
| 5 | `/api/v1/projects/:id/wbs` | `/api/v1/progress-tracking/wbs?project_id=` | 迁移 |
| 6 | `/api/v1/projects/:id/gantt` | `/api/v1/progress-tracking/gantt?project_id=` | 迁移 |

---

## 七、风险与应对

### 7.1 技术风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 路由变更导致404 | 用户无法访问 | 保留重定向，告知用户新路径 |
| 前端路由冲突 | 页面无法访问 | 测试路由配置，使用唯一路径 |
| API调用路径变更 | 前端功能失效 | 批量更新API调用，分阶段上线 |

### 7.2 业务风险

| 风险 | 影响 | 应对措施 |
|------|------|---------|
| 用户不适应新菜单 | 使用困难 | 充分培训，提供使用指南 |
| 历史链接失效 | 书签失效 | 重定向策略，逐步废弃旧路由 |

---

## 八、测试策略

### 8.1 后端测试

- [ ] 所有新端点API测试
- [ ] 重定向功能测试
- [ ] 权限测试
- [ ] 性能测试
- [ ] 数据一致性测试

### 8.2 前端测试

- [ ] 所有新页面功能测试
- [ ] 菜单导航测试
- [ ] 路由跳转测试
- [ ] 浏览器兼容性测试
- [ ] 用户体验测试

### 8.3 集成测试

- [ ] 前后端联调测试
- [ ] 完整流程测试
- [ ] 回归测试

---

## 九、成功指标

| 指标 | 目标值 |
|------|--------|
| 功能迁移完成率 | 100% |
| API端点覆盖率 | 100% |
| 前端页面完成率 | 100% |
| 测试覆盖率 | >90% |
| 用户培训覆盖率 | 100% |

---

## 十、总结

### 10.1 核心成果

完成3个模块的重组：

1. ✅ **成本报价管理**：整合所有成本报价相关功能到独立模块
2. ✅ **变更管理**：整合所有ECN变更相关功能到独立模块
3. ✅ **进度跟踪**：整合所有进度跟踪相关功能到独立模块

### 10.2 预期效果

- 📁 **模块清晰**：功能归类清晰，查找方便
- 🔄 **便于维护**：代码集中，降低维护成本
- 🎯 **用户友好**：菜单结构合理，操作流畅
- 📈 **扩展性强**：模块独立，便于后续扩展

### 10.3 后续工作

- 清理旧代码和旧路由（重定向保留3个月后）
- 优化模块性能
- 完善文档和培训材料

---

**文档版本**: v1.0
**创建日期**: 2026-01-25
**最后更新**: 2026-01-25
**负责人**: PMO技术团队
