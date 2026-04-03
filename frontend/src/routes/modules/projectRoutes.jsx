import { Route, Navigate } from "react-router-dom";
import { ProjectReviewProtectedRoute } from "../../components/common/ProtectedRoute";
import { lazyLoad } from "../lazyLoad";

const ProjectDetail = lazyLoad(() => import("../../pages/ProjectDetail"));
const ProjectWorkspace = lazyLoad(() => import("../../pages/ProjectWorkspace"));
const ProjectContributionReport = lazyLoad(() => import("../../pages/ProjectContributionReport"));
const ProjectBoard = lazyLoad(() => import("../../pages/ProjectBoard"));
const WBSTemplateManagement = lazyLoad(() => import("../../pages/WBSTemplateManagement"));
const ProgressReport = lazyLoad(() => import("../../pages/ProgressReport"));
const ProgressBoard = lazyLoad(() => import("../../pages/ProgressBoard"));
const ProgressForecast = lazyLoad(() => import("../../pages/ProgressForecast"));
const DependencyCheck = lazyLoad(() => import("../../pages/DependencyCheck"));
const MilestoneRateReport = lazyLoad(() => import("../../pages/MilestoneRateReport"));
const DelayReasonsReport = lazyLoad(() => import("../../pages/DelayReasonsReport"));
const TaskCenter = lazyLoad(() => import("../../pages/TaskCenter"));
const ScheduleBoard = lazyLoad(() => import("../../pages/ScheduleBoard"));
const ProjectTaskList = lazyLoad(() => import("../../pages/ProjectTaskList"));
const MachineManagement = lazyLoad(() => import("../../pages/MachineManagement"));
const MilestoneManagement = lazyLoad(() => import("../../pages/MilestoneManagement"));
const AssemblerTaskCenter = lazyLoad(() => import("../../pages/AssemblerTaskCenter"));
const EngineerRecommendation = lazyLoad(() => import("../../pages/EngineerRecommendation"));
const EngineerWorkloadBoard = lazyLoad(() => import("../../pages/EngineerWorkloadBoard"));
const EngineerWorkstation = lazyLoad(() => import("../../pages/EngineerWorkstation"));
const ProjectTimelineView = lazyLoad(() => import("../../pages/ProjectTimelineView"));
const PresalesTasks = lazyLoad(() => import("../../pages/PresalesTasks"));
const ProjectListWithCost = lazyLoad(() => import("../../pages/ProjectListWithCost"));
const ResourceOverview = lazyLoad(() => import("../../pages/ResourceOverview"));
const AcceptanceManagement = lazyLoad(() => import("../../pages/AcceptanceManagement"));
const GanttDependency = lazyLoad(() => import("../../pages/GanttDependency"));
const ECNManagement = lazyLoad(() => import("../../pages/ECNManagement"));
const FieldCommissioning = lazyLoad(() => import("../../pages/FieldCommissioning"));
const AssemblyKitBoard = lazyLoad(() => import("../../pages/AssemblyKitBoard"));
const TemplateConfigList = lazyLoad(() => import("../../pages/TemplateConfigList"));
const MarginPrediction = lazyLoad(() => import("../../pages/MarginPrediction"));
const ScheduleOptimization = lazyLoad(() => import("../../pages/ScheduleOptimization"));
const ScheduleGeneration = lazyLoad(() => import("../../pages/ScheduleGeneration"));
const ScheduleGenerationEntry = lazyLoad(() => import("../../pages/ScheduleGenerationEntry"));
const EngineerRecommendationEntry = lazyLoad(() => import("../../pages/EngineerRecommendationEntry"));
const PMODashboard = lazyLoad(() => import("../../pages/PMODashboard"));
const ProjectClosing = lazyLoad(() => import("../../pages/ProjectClosing"));
const AIProjectTools = lazyLoad(() => import("../../pages/AIProjectTools"));
const GanttAndResource = lazyLoad(() => import("../../pages/GanttAndResource"));
const ProjectHealthMonitor = lazyLoad(() => import("../../pages/ProjectHealthMonitor"));
const TimeCostMarginFlow = lazyLoad(() => import("../../pages/TimeCostMarginFlow"));
const ProjectDashboardCenter = lazyLoad(() => import("../../pages/ProjectDashboardCenter"));
const ProjectCostCenter = lazyLoad(() => import("../../pages/ProjectCostCenter"));

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
