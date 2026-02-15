# 路由配置更新示例

## 文件路径
`frontend/src/routes/modules/projectRoutes.jsx`

---

## 方案A: 添加新路由（保留原有项目列表）

### 1. 添加导入

在文件顶部添加：

```jsx
import ProjectListWithCost from "../../pages/ProjectListWithCost";
```

完整示例：

```jsx
import { Route } from "react-router-dom";
import { ProjectReviewProtectedRoute } from "../../components/common/ProtectedRoute";

import ProjectList from "../../pages/ProjectList";
import ProjectListWithCost from "../../pages/ProjectListWithCost";  // ← 新增
import ProjectDetail from "../../pages/ProjectDetail";
// ... 其他导入 ...
```

### 2. 添加路由

在 `ProjectRoutes()` 函数中添加：

```jsx
export function ProjectRoutes() {
  return (
    <>
      {/* 项目成本列表 - 新增 */}
      <Route path="/projects-cost" element={<ProjectListWithCost />} />
      
      {/* 原有路由 */}
      <Route path="/projects" element={<ProjectList />} />
      <Route path="/projects/:id" element={<ProjectDetail />} />
      {/* ... 其他路由 ... */}
    </>
  );
}
```

**访问地址**: `http://localhost:5173/projects-cost`

---

## 方案B: 替换原有项目列表（推荐）

### 1. 添加导入

```jsx
import ProjectListWithCost from "../../pages/ProjectListWithCost";
```

### 2. 替换路由

```jsx
export function ProjectRoutes() {
  return (
    <>
      {/* 项目列表 - 使用成本增强版本 */}
      <Route path="/projects" element={<ProjectListWithCost />} />
      <Route path="/projects/:id" element={<ProjectDetail />} />
      {/* ... 其他路由 ... */}
    </>
  );
}
```

**访问地址**: `http://localhost:5173/projects`

---

## 完整示例（方案B）

```jsx
import { Route } from "react-router-dom";
import { ProjectReviewProtectedRoute } from "../../components/common/ProtectedRoute";

// ========== 导入列表 ==========
import ProjectListWithCost from "../../pages/ProjectListWithCost"; // ← 替换 ProjectList
import ProjectDetail from "../../pages/ProjectDetail";
import ProjectWorkspace from "../../pages/ProjectWorkspace";
import ProjectContributionReport from "../../pages/ProjectContributionReport";
import ProjectBoard from "../../pages/ProjectBoard";
import ProjectGantt from "../../pages/ProjectGantt";
import WBSTemplateManagement from "../../pages/WBSTemplateManagement";
import ProgressReport from "../../pages/ProgressReport";
import ProgressBoard from "../../pages/ProgressBoard";
import ProgressForecast from "../../pages/ProgressForecast";
import DependencyCheck from "../../pages/DependencyCheck";
import MilestoneRateReport from "../../pages/MilestoneRateReport";
import DelayReasonsReport from "../../pages/DelayReasonsReport";
import TaskCenter from "../../pages/TaskCenter";
import ScheduleBoard from "../../pages/ScheduleBoard";
import ProjectTaskList from "../../pages/ProjectTaskList";
import MachineManagement from "../../pages/MachineManagement";
import MilestoneManagement from "../../pages/MilestoneManagement";
import AssemblerTaskCenter from "../../pages/AssemblerTaskCenter";
import EngineerWorkstation from "../../pages/EngineerWorkstation";
import ProjectStageView from "../../pages/ProjectStageView";
import ProjectTimelineView from "../../pages/ProjectTimelineView";

// ========== 路由定义 ==========
export function ProjectRoutes() {
  return (
    <>
      {/* 项目阶段视图 - 22阶段三视图 */}
      <Route path="/stage-view" element={<ProjectStageView />} />
      <Route path="/projects/stage-view" element={<ProjectStageView />} />

      {/* 进度跟踪模块 - 新路由 */}
      <Route path="/progress-tracking/tasks" element={<TaskCenter />} />
      <Route path="/progress-tracking/board" element={<ProjectBoard />} />
      <Route path="/progress-tracking/schedule" element={<ScheduleBoard />} />
      <Route path="/progress-tracking/reports" element={<ProgressReport />} />
      <Route path="/progress-tracking/milestones" element={<MilestoneManagement />} />
      <Route path="/progress-tracking/wbs" element={<WBSTemplateManagement />} />
      <Route path="/progress-tracking/gantt" element={<ProjectGantt />} />
      <Route path="/progress-tracking/timeline" element={<ProjectTimelineView />} />

      {/* 向后兼容 - 保留旧路由 */}
      <Route path="/board" element={<ProjectBoard />} />
      
      {/* ========== 项目列表 - 使用成本增强版本 ========== */}
      <Route path="/projects" element={<ProjectListWithCost />} />
      {/* ========================================== */}
      
      <Route path="/projects/:id" element={<ProjectDetail />} />
      <Route path="/projects/:id/workspace" element={<ProjectWorkspace />} />
      <Route
        path="/projects/:id/contributions"
        element={<ProjectContributionReport />}
      />
      <Route path="/projects/:id/gantt" element={<ProjectGantt />} />
      <Route path="/projects/:id/timeline" element={<ProjectTimelineView />} />
      <Route path="/projects/:id/tasks" element={<ProjectTaskList />} />
      <Route path="/projects/:id/machines" element={<MachineManagement />} />
      <Route
        path="/projects/:id/milestones"
        element={<MilestoneManagement />}
      />
      <Route
        path="/projects/:id/progress-report"
        element={<ProgressReport />}
      />
      <Route path="/projects/:id/progress-board" element={<ProgressBoard />} />
      <Route
        path="/projects/:id/progress-forecast"
        element={
          <ProjectReviewProtectedRoute>
            <ProgressForecast />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/:id/dependency-check"
        element={
          <ProjectReviewProtectedRoute>
            <DependencyCheck />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/:id/milestone-rate"
        element={<MilestoneRateReport />}
      />
      <Route
        path="/projects/:id/delay-reasons"
        element={<DelayReasonsReport />}
      />
      <Route path="/reports/milestone-rate" element={<MilestoneRateReport />} />
      <Route path="/reports/delay-reasons" element={<DelayReasonsReport />} />
      <Route path="/wbs-templates" element={<WBSTemplateManagement />} />
      <Route path="/schedule" element={<ScheduleBoard />} />
      <Route path="/tasks" element={<TaskCenter />} />
      <Route path="/assembly-tasks" element={<AssemblerTaskCenter />} />
      <Route path="/workstation" element={<EngineerWorkstation />} />
    </>
  );
}
```

---

## 验证

更新路由后，重启开发服务器：

```bash
npm run dev
# 或
pnpm dev
```

访问项目列表页面，应该看到成本增强版本。

---

## 回滚

如果需要回滚到原来的版本：

1. 恢复备份文件：
   ```bash
   cp src/routes/modules/projectRoutes.jsx.backup.* src/routes/modules/projectRoutes.jsx
   ```

2. 或者手动将导入改回：
   ```jsx
   import ProjectList from "../../pages/ProjectList";
   ```

   路由改回：
   ```jsx
   <Route path="/projects" element={<ProjectList />} />
   ```

---

## 导航菜单更新（可选）

如果使用方案A（新增路由），可能需要更新导航菜单。

找到导航菜单配置文件（通常在 `src/config/` 或 `src/components/layout/` 中），添加：

```jsx
{
  label: "项目成本列表",
  path: "/projects-cost",
  icon: DollarSign,
}
```

或者

```jsx
{
  label: "项目列表（含成本）",
  path: "/projects-cost",
  icon: DollarSign,
}
```
