# 项目管理模块前端闭环审计报告

> 审计日期：2026-03-26
> 审计范围：`frontend/src/pages/` 中所有项目管理相关页面、路由、菜单、服务
> 审计目的：盘清页面入口、数据打通状态、API 对接情况，不涉及业务代码修改

---

## 一、总体概况

| 指标 | 数据 |
|------|------|
| 项目相关页面总数 | 35+ |
| 路由条目 | 50+ (含重定向) |
| API 服务文件 | 10+ |
| 自定义 Hooks | 10+ |
| 技术栈 | React 19 + Vite + Tailwind + Ant Design + Zustand + React Router 7 |

---

## 二、审计目标页面专项分析

### 2.1 ProjectManagementPage

**结论：该名称不存在。** 代码库中无 `ProjectManagementPage` 组件。项目管理主入口实际为：

- **ProjectBoard** (`/board`) — 主看板页，支持 card/kanban/matrix/list/pipeline/timeline/tree 7种视图
- **ProjectList** (`/projects`) — 旧列表页，路由已重定向至 `/board?view=card`

### 2.2 ResourceConflictView

**结论：该名称不存在。** 资源冲突功能分布在以下页面中：

- **ResourceOverview** (`/gantt-resource?tab=resource`) — 900+ 行，含跨项目资源时间线和冲突高亮（分配 >100% 标红）
- **GanttAndResource** (`/gantt-resource`) — 整合甘特图 + 资源视图 + 冲突检测
- **memberApi.checkConflicts()** — API 层有冲突检测接口

### 2.3 ProjectTemplateManagement

**结论：该名称不存在。** 模板管理功能由以下页面承担：

- **StageTemplateManagement** — 阶段模板 CRUD（含 mock 降级）
- **StageTemplateEditor** — 阶段模板节点编辑器（含 mock 降级）
- **WBSTemplateManagement** — WBS 模板管理（已移除 mock，API 直连）
- **AssemblyTemplateManagement** — 装配模板管理（有 TODO: 调用 API 未实现）

---

## 三、核心审计表

| 页面 | 路由 | 数据来源 | 当前状态 | 主要问题 | 建议优先级 |
|------|------|----------|----------|----------|------------|
| **ProjectBoard** | `/board` | `projectApi.list()`, `milestoneApi`, `stageViewsHook` | ✅ 已打通 | 无重大问题，主入口，功能完整 | — |
| **ProjectDetail** | `/projects/:id` | `projectApi.get()`, `machineApi`, `stageApi`, `milestoneApi`, `memberApi`, `costApi`, `documentApi` | ✅ 已打通 | 7 个并行 API 调用，Promise.allSettled 容错 | — |
| **ProjectList** | `/projects` | `projectApi.list()` | ⚠️ 半打通 | 路由已重定向到 `/board?view=card`，此页面事实上被废弃但代码仍保留 | P3 清理 |
| **ProjectGantt** | `/projects/:id/gantt` | 重定向至 `/gantt-resource` | ⚠️ 半打通 | 单独页面仅做重定向中转 | P3 清理 |
| **GanttAndResource** | `/gantt-resource` | `progressApi`, `resourceApi` | ✅ 已打通 | 整合甘特+资源+冲突，功能完整 | — |
| **ResourceOverview** | `/gantt-resource?tab=resource` | `resourceApi` | ✅ 已打通 | 冲突高亮已实现，分配 >100% 标红 | — |
| **ProjectPhaseManagement** | 嵌入于项目详情 | `pmoApi.phases.*` | ✅ 已打通 | 1000+ 行，含入口检查/出口检查/门禁审核 | — |
| **ProjectTaskList** | `/projects/:id/tasks` | `progressApi.tasks.*`, `progressApi.reports.getSummary()` | ✅ 已打通 | 完整 CRUD + 筛选 + 进度追踪 | — |
| **ProjectClosing** | `/project-closing` | 懒加载 3 子模块 | ✅ 已打通 | 整合结项/复盘/经验教训，结构清晰 | — |
| **ProjectReviewList** | `/project-closing?tab=review` | `reviewApi` + **mock 降级** | ⚠️ 半打通 | API 失败时回退到硬编码 mock 数据（3 条），用户可能看到假数据而不知情 | **P1** |
| **ProjectReviewDetail** | 详情弹窗/页 | `useProjectReviewDetail` hook | ✅ 已打通 | 892 行，指标/发现/建议完整 | — |
| **ProjectHealthMonitor** | `/project-health-monitor` | `projectApi`, `marginPredictionApi`, `materialReadinessApi` | ✅ 已打通 | 整合健康度+齐套率+毛利率 | — |
| **ProjectDashboardCenter** | `/project/dashboard-center` | 组合 PMODashboard + ProjectHealthMonitor | ✅ 已打通 | Tab 容器页，无自有数据 | — |
| **ProjectCostCenter** | `/project/cost-center` | 组合 BudgetManagement + TimeCostMarginFlow | ✅ 已打通 | Tab 容器页，无自有数据 | — |
| **PMODashboard** | `/pmo/dashboard` | 真实 API（注释标注 `Mock data removed`) | ✅ 已打通 | 已移除 mock | — |
| **ProjectWorkspace** | `/projects/:id/workspace` | `projectWorkspaceApi.*` | ✅ 已打通 | 会议/奖金/问题/方案库 | — |
| **ProjectContributionReport** | `/projects/:id/contributions` | `projectContributionApi.*` | ✅ 已打通 | 贡献度评分与报告 | — |
| **ProjectRoles** | 嵌入于项目详情 | `projectRoleApi.*`, `userApi` | ✅ 已打通 | 659 行，角色配置+负责人+成员管理 | — |
| **ProjectSettlement** | 结算管理 | `settlementApi.*` | ✅ 已打通 | mock 已移除（注释 `Mock data - 已移除，使用真实API`） | — |
| **ProjectStaffingNeed** | 人员需求 | `staffMatchingApi` | ✅ 已打通 | mock 已移除（3 行注释确认） | — |
| **ProjectListWithCost** | `/project-list-with-cost` | `projectApi`, `costApi` | ✅ 已打通 | 519 行，带成本的项目列表 | — |
| **ProjectTimelineView** | `/projects/:id/timeline` | `progressApi` | ✅ 已打通 | 项目阶段时间线可视化 | — |
| **StageTemplateManagement** | 阶段模板管理 | `stageTemplateApi` + **mock 降级** | ⚠️ 半打通 | API 失败时回退 mock 数据（111-149 行） | **P2** |
| **StageTemplateEditor** | 阶段模板编辑 | `stageTemplateApi` + **mock 降级** | ⚠️ 半打通 | API 失败时回退 mock 数据（115-188 行） | **P2** |
| **WBSTemplateManagement** | `/wbs-templates` | `progressApi.wbsTemplates.*` | ✅ 已打通 | 注释 `不再使用mock数据`，API 直连 | — |
| **AssemblyTemplateManagement** | `/assembly-template-management` | 本地状态 | 🔴 纯壳子 | 有两处 `TODO: 调用 API`，保存/删除操作未对接后端 | **P1** |
| **RdProjectList** | R&D 项目列表 | `rdProjectApi.*` | ✅ 已打通 | 研发项目完整 CRUD | — |
| **RdProjectDetail** | R&D 项目详情 | `useRdProjectDetail` hook | ✅ 已打通 | 845 行 | — |
| **SalesProjectTrack** | `/sales-projects` | `salesProjectApi` | ✅ 已打通 | mock 已移除 | — |
| **AIProjectTools** | `/ai-project-tools` | 调用 AI 接口 | ✅ 已打通 | 排期生成+工程师推荐 | — |
| **PresaleTemplates** | 售前模板 | API + **MOCK_TEMPLATES 降级** | ⚠️ 半打通 | 39 行硬编码完整 mock 数据，有 `usingMockData` 状态标识，但用户侧提示不够醒目 | **P2** |
| **ScheduleBoard** | `/schedule` | `scheduleApi` | ✅ 已打通 | 排期看板 | — |
| **TaskCenter** | `/tasks` | `progressApi.tasks.*` | ✅ 已打通 | 全局任务中心 | — |

---

## 四、路由与菜单审计

### 4.1 路由文件

主路由文件：`frontend/src/routes/modules/projectRoutes.jsx`（182 行）

**重定向汇总：**

| 源路由 | 目标 | 备注 |
|--------|------|------|
| `/projects` | `/board?view=card` | ProjectList 已被 ProjectBoard 替代 |
| `/projects/:id/gantt` | `/gantt-resource?tab=task` | 甘特图整合 |
| `/gantt` | `/gantt-resource?tab=gantt` | 同上 |
| `/resource-overview` | `/gantt-resource?tab=resource` | 资源视图整合 |
| `/schedule-generation` | `/ai-project-tools?tab=schedule` | AI 工具整合 |
| `/engineer-recommendation` | `/ai-project-tools?tab=engineer` | AI 工具整合 |
| `/pmo/closure` | `/project-closing?tab=closure` | 结项整合 |
| `/projects/reviews` | `/project-closing?tab=review` | 复盘整合 |
| `/lessons-learned` | `/project-closing?tab=lessons` | 经验教训整合 |
| `/stage-view` | `/board?view=pipeline` | 阶段视图整合进看板 |

### 4.2 菜单入口（按角色）

| 角色 | 菜单项 | 路由 |
|------|--------|------|
| 董事长/GM/VP | 项目看板、项目列表 | `/board`, `/projects` |
| GM/VP | 排期看板 | `/schedule` |
| 销售总监 | 项目看板、项目列表 | `/board`, `/projects` |
| 销售经理 | 项目进度、项目看板、项目列表 | `/sales-projects`, `/board`, `/projects` |
| 默认用户 | 项目看板、排期看板、任务中心 | `/board`, `/schedule`, `/tasks` |

配置文件：`frontend/src/lib/roleConfig/navigation.js`（328 行）

---

## 五、API 服务层审计

### 5.1 核心服务文件

| 服务文件 | 主要 API 对象 | 对接状态 |
|----------|---------------|----------|
| `services/api/projects.js` (252行) | `projectApi`, `machineApi`, `stageApi`, `milestoneApi`, `memberApi`, `costApi`, `settlementApi` | ✅ 完整 |
| `services/api/projectRoles.js` | `projectRoleApi` | ✅ 完整 |
| `services/api/projectSettlement.js` | `projectSettlementApi` | ✅ 完整 |
| `services/api/salesProject.js` | `salesProjectApi` | ✅ 完整 |
| `services/api/materialReadiness.js` | `materialReadinessApi` | ✅ 完整 |
| `services/api/templateConfig.js` | `templateConfigApi` | ✅ 完整 |

### 5.2 API 端点统计

- `projectApi`: 20+ 端点（CRUD + 阶段推进 + 缓存 + 健康度 + 统计）
- `machineApi`: 14 端点（CRUD + 进度 + BOM + 文档）
- `costApi`: 16 端点（CRUD + 分析 + 预算 + 毛利）
- `memberApi`: 8 端点（CRUD + 冲突检测 + 部门）
- `projectRoleApi`: 12 端点（配置 + 负责人 + 团队）

---

## 六、问题汇总与优先级建议

### 🔴 P1 — 必须处理

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 1 | **AssemblyTemplateManagement 未对接 API** | `AssemblyTemplateManagement.jsx:81,107` | 两处 `TODO: 调用 API`，保存和删除操作仅操作本地状态，数据无法持久化 |
| 2 | **ProjectReviewList mock 降级无明确提示** | `ProjectReviewList.jsx:100-192` | API 失败时静默回退到 3 条硬编码数据，用户无法区分真实数据与 mock 数据 |

### 🟡 P2 — 建议处理

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 3 | **StageTemplateManagement/Editor mock 降级** | `StageTemplateManagement.jsx:111`, `StageTemplateEditor.jsx:115` | API 失败时使用 mock 数据展示，标注为 "for demo"，生产环境应移除或加明确提示 |
| 4 | **PresaleTemplates mock 数据** | `PresaleTemplates.jsx:39-327` | 含完整 `MOCK_TEMPLATES` 数组，虽有 `usingMockData` 标识但提示不够醒目 |

### 🟢 P3 — 可选清理

| # | 问题 | 位置 | 说明 |
|---|------|------|------|
| 5 | **ProjectList 代码残留** | `ProjectList.jsx` | 路由已永久重定向至 `/board?view=card`，334 行代码可考虑移除 |
| 6 | **ProjectGantt 仅做重定向** | `ProjectGantt.jsx` | 188 行代码实际只做路由跳转，可简化 |
| 7 | **多处 "Mock data - 已移除" 注释** | `ProjectSettlement.jsx:42`, `SalesProjectTrack.jsx:148`, `ProjectStaffingNeed.jsx:73-76`, `PMODashboard.jsx:59`, `CostAnalysis.jsx:38`, `AdminDashboard.jsx:58-60` | 无功能影响，但注释残留可清理 |

---

## 七、结论

**整体评估：项目管理模块前端完成度较高（约 85%）。**

- 35+ 页面中，约 28 个已完全打通真实 API
- 4 个页面存在 mock 数据降级（ProjectReviewList、StageTemplate×2、PresaleTemplates）
- 1 个页面为纯壳子（AssemblyTemplateManagement）
- 2 个页面为废弃代码残留（ProjectList、ProjectGantt）

**用户提问的 3 个目标页面（ProjectManagementPage、ResourceConflictView、ProjectTemplateManagement）均不以该名称存在**，其功能已由其他命名的页面承担，建议核对需求文档与代码的命名映射。

---

*本报告由自动化审计生成，仅基于前端代码静态分析，未验证后端 API 实际可用性。*
