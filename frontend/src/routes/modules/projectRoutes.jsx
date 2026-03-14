import { Route, Navigate } from "react-router-dom";
import { ProjectReviewProtectedRoute } from "../../components/common/ProtectedRoute";

// ProjectList 已整合到 ProjectBoard 的卡片视图
// import ProjectList from "../../pages/ProjectList";
import ProjectDetail from "../../pages/ProjectDetail";
import ProjectWorkspace from "../../pages/ProjectWorkspace";
import ProjectContributionReport from "../../pages/ProjectContributionReport";
import ProjectBoard from "../../pages/ProjectBoard";
// ProjectGantt 已废弃，重定向到 GanttAndResource
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
import AssemblyTemplateManagement from "../../pages/AssemblyTemplateManagement";
import EngineerRecommendation from "../../pages/EngineerRecommendation";
import EngineerWorkloadBoard from "../../pages/EngineerWorkloadBoard";
import EngineerWorkstation from "../../pages/EngineerWorkstation";
// ProjectStageView 已整合到 ProjectBoard 的流水线视图
// import ProjectStageView from "../../pages/ProjectStageView";
import ProjectTimelineView from "../../pages/ProjectTimelineView";
import PresalesTasks from "../../pages/PresalesTasks";
import ProjectListWithCost from "../../pages/ProjectListWithCost";
import ResourceOverview from "../../pages/ResourceOverview";
import AcceptanceManagement from "../../pages/AcceptanceManagement";
import GanttDependency from "../../pages/GanttDependency";
import ECNManagement from "../../pages/ECNManagement";
import FieldCommissioning from "../../pages/FieldCommissioning";
import AssemblyKitBoard from "../../pages/AssemblyKitBoard";
import TemplateConfigList from "../../pages/TemplateConfigList";
import MarginPrediction from "../../pages/MarginPrediction";
import ScheduleOptimization from "../../pages/ScheduleOptimization";
import ScheduleGeneration from "../../pages/ScheduleGeneration";
import ScheduleGenerationEntry from "../../pages/ScheduleGenerationEntry";
import EngineerRecommendationEntry from "../../pages/EngineerRecommendationEntry";
import PMODashboard from "../../pages/PMODashboard";
import ProjectClosing from "../../pages/ProjectClosing";
import AIProjectTools from "../../pages/AIProjectTools";
import GanttAndResource from "../../pages/GanttAndResource";
import ProjectHealthMonitor from "../../pages/ProjectHealthMonitor";
import TimeCostMarginFlow from "../../pages/TimeCostMarginFlow";
import ProjectDashboardCenter from "../../pages/ProjectDashboardCenter";
import ProjectCostCenter from "../../pages/ProjectCostCenter";

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
