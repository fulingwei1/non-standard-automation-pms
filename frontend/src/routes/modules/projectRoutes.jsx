import { lazy } from "react";
import { Route, Navigate } from "react-router-dom";
import { ProjectReviewProtectedRoute } from "../../components/common/ProtectedRoute";

// ---- 懒加载页面组件（项目管理模块） ----
const ProjectDashboardCenter = lazy(() => import("../../pages/ProjectDashboardCenter"));
const ProjectCostCenter = lazy(() => import("../../pages/ProjectCostCenter"));
const PMODashboard = lazy(() => import("../../pages/PMODashboard"));
const ProgressBoard = lazy(() => import("../../pages/ProgressBoard"));
const MilestoneManagement = lazy(() => import("../../pages/MilestoneManagement"));
const ProjectClosing = lazy(() => import("../../pages/ProjectClosing"));
const AIProjectTools = lazy(() => import("../../pages/AIProjectTools"));
const GanttAndResource = lazy(() => import("../../pages/GanttAndResource"));
const ProjectHealthMonitor = lazy(() => import("../../pages/ProjectHealthMonitor"));
const TimeCostMarginFlow = lazy(() => import("../../pages/TimeCostMarginFlow"));
const TaskCenter = lazy(() => import("../../pages/TaskCenter"));
const ProjectBoard = lazy(() => import("../../pages/ProjectBoard"));
const ScheduleBoard = lazy(() => import("../../pages/ScheduleBoard"));
const ProgressReport = lazy(() => import("../../pages/ProgressReport"));
const WBSTemplateManagement = lazy(() => import("../../pages/WBSTemplateManagement"));
const ProjectTimelineView = lazy(() => import("../../pages/ProjectTimelineView"));
const ProjectDetail = lazy(() => import("../../pages/ProjectDetail"));
const ProjectWorkspace = lazy(() => import("../../pages/ProjectWorkspace"));
const ProjectContributionReport = lazy(() => import("../../pages/ProjectContributionReport"));
const ProjectTaskList = lazy(() => import("../../pages/ProjectTaskList"));
const MachineManagement = lazy(() => import("../../pages/MachineManagement"));
const ProgressForecast = lazy(() => import("../../pages/ProgressForecast"));
const DependencyCheck = lazy(() => import("../../pages/DependencyCheck"));
const MilestoneRateReport = lazy(() => import("../../pages/MilestoneRateReport"));
const DelayReasonsReport = lazy(() => import("../../pages/DelayReasonsReport"));
const ECNManagement = lazy(() => import("../../pages/ECNManagement"));
const FieldCommissioning = lazy(() => import("../../pages/FieldCommissioning"));
const ScheduleGeneration = lazy(() => import("../../pages/ScheduleGeneration"));
const ResourceOverview = lazy(() => import("../../pages/ResourceOverview"));
const ProjectListWithCost = lazy(() => import("../../pages/ProjectListWithCost"));
const ScheduleOptimization = lazy(() => import("../../pages/ScheduleOptimization"));
const EngineerRecommendation = lazy(() => import("../../pages/EngineerRecommendation"));
const EngineerWorkloadBoard = lazy(() => import("../../pages/EngineerWorkloadBoard"));
const PresalesTasks = lazy(() => import("../../pages/PresalesTasks"));
const AssemblerTaskCenter = lazy(() => import("../../pages/AssemblerTaskCenter"));
const EngineerWorkstation = lazy(() => import("../../pages/EngineerWorkstation"));
const AcceptanceManagement = lazy(() => import("../../pages/AcceptanceManagement"));
const TemplateConfigList = lazy(() => import("../../pages/TemplateConfigList"));
const MarginPrediction = lazy(() => import("../../pages/MarginPrediction"));

// ProjectList 已整合到 ProjectBoard 的卡片视图
// ProjectGantt 已废弃，重定向到 GanttAndResource
// ProjectStageView 已整合到 ProjectBoard 的流水线视图

export function ProjectRoutes() {
  return (
    <>
      {/* PMO 驾驶舱 */}
      <Route path="/project/dashboard-center" element={<ProjectDashboardCenter />} />
      <Route path="/project/cost-center" element={<ProjectCostCenter />} />
      <Route path="/pmo/dashboard" element={<PMODashboard />} />

      {/* 全局进度看板 */}
      <Route path="/progress-board" element={<ProgressBoard />} />

      {/* 全局里程碑管理 */}
      <Route path="/milestones" element={<MilestoneManagement />} />

      {/* 项目收尾 - 整合结项、复盘、经验教训 */}
      <Route path="/project-closing" element={<ProjectClosing />} />

      {/* AI项目工具 - 整合智能排计划、工程师调度 */}
      <Route path="/ai-project-tools" element={<AIProjectTools />} />

      {/* 甘特与资源 - 整合任务甘特图、资源全景 */}
      <Route path="/gantt-resource" element={<GanttAndResource />} />

      {/* 项目健康监控 - 整合齐套率、健康度、毛利率 */}
      <Route path="/project-health-monitor" element={<ProjectHealthMonitor />} />

      {/* 工时成本毛利联动视图 */}
      <Route path="/time-cost-margin-flow" element={<TimeCostMarginFlow />} />

      {/* 旧路由重定向到项目收尾 */}
      <Route path="/pmo/closure" element={<Navigate to="/project-closing?tab=closure" replace />} />
      <Route path="/projects/reviews" element={<Navigate to="/project-closing?tab=review" replace />} />
      <Route path="/lessons-learned" element={<Navigate to="/project-closing?tab=lessons" replace />} />

      {/* 旧路由重定向到AI项目工具 */}
      <Route path="/schedule-generation" element={<Navigate to="/ai-project-tools?tab=schedule" replace />} />
      <Route path="/engineer-recommendation" element={<Navigate to="/ai-project-tools?tab=engineer" replace />} />

      {/* 旧路由重定向到甘特与资源 */}
      <Route path="/gantt" element={<Navigate to="/gantt-resource?tab=gantt" replace />} />
      <Route path="/resource-overview" element={<Navigate to="/gantt-resource?tab=resource" replace />} />

      {/* 旧路由重定向到项目中心 */}
      <Route path="/projects" element={<Navigate to="/board?view=card" replace />} />

      {/* 项目阶段视图 - 重定向到项目中心的流水线视图 */}
      <Route path="/stage-view" element={<Navigate to="/board?view=pipeline" replace />} />
      <Route path="/projects/stage-view" element={<Navigate to="/board?view=pipeline" replace />} />

      {/* 进度跟踪模块 - 新路由 */}
      <Route path="/progress-tracking/tasks" element={<TaskCenter />} />
      <Route path="/progress-tracking/board" element={<ProjectBoard />} />
      <Route path="/progress-tracking/schedule" element={<ScheduleBoard />} />
      <Route path="/progress-tracking/reports" element={<ProgressReport />} />
      <Route path="/progress-tracking/milestones" element={<MilestoneManagement />} />
      <Route path="/progress-tracking/wbs" element={<WBSTemplateManagement />} />
      <Route path="/progress-tracking/gantt" element={<Navigate to="/gantt-resource?tab=task" replace />} />
      <Route path="/progress-tracking/timeline" element={<ProjectTimelineView />} />

      {/* 向后兼容 - 保留旧路由 */}
      <Route path="/board" element={<ProjectBoard />} />
      {/* /projects 已重定向到 /board?view=card */}
      <Route path="/projects/:id" element={<ProjectDetail />} />
      <Route path="/projects/:id/workspace" element={<ProjectWorkspace />} />
      <Route
        path="/projects/:id/contributions"
        element={<ProjectContributionReport />}
      />
      <Route path="/projects/:id/gantt" element={<Navigate to="/gantt-resource?tab=task" replace />} />
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
      <Route path="/ecn" element={<ECNManagement />} />
      <Route path="/field-commissioning" element={<FieldCommissioning />} />
      <Route path="/projects/:id/schedule-generation" element={<ScheduleGeneration />} />
      <Route path="/progress-tracking/resource-overview" element={<ResourceOverview />} />
      <Route path="/project-list-with-cost" element={<ProjectListWithCost />} />
      <Route path="/projects/:projectId/schedule-optimization" element={<ScheduleOptimization />} />
      <Route path="/projects/:projectId/engineer-recommendation" element={<EngineerRecommendation />} />
      <Route path="/projects/:projectId/engineer-workload-board" element={<EngineerWorkloadBoard />} />
      {/* 已移至 productionRoutes: /assembly-template-management */}
      <Route path="/project-presales-tasks" element={<PresalesTasks />} />
      <Route path="/tasks" element={<TaskCenter />} />
      <Route path="/assembly-tasks" element={<AssemblerTaskCenter />} />
      <Route path="/workstation" element={<EngineerWorkstation />} />
      <Route path="/acceptance" element={<AcceptanceManagement />} />
      <Route path="/template-configs" element={<TemplateConfigList />} />
      <Route path="/margin-prediction" element={<MarginPrediction />} />
    </>
  );
}
