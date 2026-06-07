import { Route, Navigate } from "react-router-dom";
import { ProjectReviewProtectedRoute } from "../../components/common/ProtectedRoute";
import { PresalesCenterRedirect } from "./presalesRedirects";
import { ProjectManagementCenterRedirect } from "./projectRedirects";

// ProjectList 已整合到 ProjectBoard 的卡片视图
// import ProjectList from "../../pages/ProjectList";
import ProjectDetail from "../../pages/ProjectDetail";
import ProjectWorkspace from "../../pages/ProjectWorkspace";
import ProjectContributionReport from "../../pages/ProjectContributionReport";
import ProgressReport from "../../pages/ProgressReport";
import ProgressBoard from "../../pages/ProgressBoard";
import ProgressForecast from "../../pages/ProgressForecast";
import DependencyCheck from "../../pages/DependencyCheck";
import MilestoneRateReport from "../../pages/MilestoneRateReport";
import DelayReasonsReport from "../../pages/DelayReasonsReport";
import ProjectTaskList from "../../pages/ProjectTaskList";
import MachineManagement from "../../pages/MachineManagement";
import MilestoneManagement from "../../pages/MilestoneManagement";
import AssemblerTaskCenter from "../../pages/AssemblerTaskCenter";
import EngineerRecommendation from "../../pages/EngineerRecommendation";
import EngineerWorkloadBoard from "../../pages/EngineerWorkloadBoard";
import EngineerWorkstation from "../../pages/EngineerWorkstation";
// ProjectStageView 已整合到 ProjectBoard 的流水线视图
// import ProjectStageView from "../../pages/ProjectStageView";
import ProjectTimelineView from "../../pages/ProjectTimelineView";
import ProjectListWithCost from "../../pages/ProjectListWithCost";
import AcceptanceManagement from "../../pages/AcceptanceManagement";
import ECNManagement from "../../pages/ECNManagement";
import ECNCostImpact from "../../pages/ECNCostImpact";
import ECNMaterialImpact from "../../pages/ECNMaterialImpact";
import MaterialProgressView from "../../pages/MaterialProgressView";
import FieldCommissioning from "../../pages/FieldCommissioning";
import TemplateConfigList from "../../pages/TemplateConfigList";
import MarginPrediction from "../../pages/MarginPrediction";
import ScheduleOptimization from "../../pages/ScheduleOptimization";
import ScheduleGeneration from "../../pages/ScheduleGeneration";
import SchedulePlansList from "../../pages/SchedulePlansList";
import SchedulePlanDetail from "../../pages/SchedulePlanDetail";
import ProjectManagementCenter from "../../pages/ProjectManagementCenter";

export function ProjectRoutes() {
  return (
    <>
      {/* 项目管理统一中心 */}
      <Route path="/project/management-center" element={<ProjectManagementCenter />} />
      <Route path="/project/dashboard-center" element={<ProjectManagementCenterRedirect tab="dashboard" />} />
      <Route path="/project/cost-center" element={<ProjectManagementCenterRedirect tab="cost" />} />
      <Route path="/pmo/dashboard" element={<ProjectManagementCenterRedirect tab="dashboard" params={{ dashboardTab: "pmo" }} />} />

      {/* 全局进度看板 */}
      <Route path="/progress-board" element={<ProgressBoard />} />

      {/* 全局里程碑管理 */}
      <Route path="/milestones" element={<ProjectManagementCenterRedirect tab="tracking" params={{ trackingTab: "milestones" }} />} />

      {/* 项目收尾 - 整合结项、复盘、经验教训 */}
      <Route path="/project-closing" element={<ProjectManagementCenterRedirect tab="closing" />} />

      {/* AI项目工具 - 整合智能排计划、工程师调度 */}
      <Route path="/ai-project-tools" element={<ProjectManagementCenterRedirect tab="ai" />} />

      {/* 甘特与资源 - 整合任务甘特图、资源全景 */}
      <Route path="/gantt-resource" element={<ProjectManagementCenterRedirect tab="planning" />} />

      {/* 项目健康监控 - 整合齐套率、健康度、毛利率 */}
      <Route path="/project-health-monitor" element={<ProjectManagementCenterRedirect tab="dashboard" params={{ dashboardTab: "health" }} />} />

      {/* 工时成本毛利联动视图 */}
      <Route path="/time-cost-margin-flow" element={<ProjectManagementCenterRedirect tab="cost" params={{ costTab: "margin" }} />} />

      {/* 旧路由重定向到项目收尾 */}
      <Route path="/pmo/closure" element={<ProjectManagementCenterRedirect tab="closing" params={{ closingTab: "closure" }} />} />
      <Route path="/projects/reviews" element={<ProjectManagementCenterRedirect tab="closing" params={{ closingTab: "review" }} />} />
      <Route path="/lessons-learned" element={<ProjectManagementCenterRedirect tab="closing" params={{ closingTab: "lessons" }} />} />
      <Route path="/projects/lessons-learned" element={<ProjectManagementCenterRedirect tab="closing" params={{ closingTab: "lessons" }} />} />

      {/* 旧路由重定向到AI项目工具 */}
      <Route path="/schedule-generation" element={<ProjectManagementCenterRedirect tab="ai" params={{ aiTab: "schedule" }} />} />
      <Route path="/engineer-recommendation" element={<ProjectManagementCenterRedirect tab="ai" params={{ aiTab: "engineer" }} />} />

      {/* 旧路由重定向到甘特与资源 */}
      <Route path="/gantt" element={<ProjectManagementCenterRedirect tab="planning" params={{ planningTab: "task" }} />} />
      <Route path="/resource-overview" element={<ProjectManagementCenterRedirect tab="planning" params={{ planningTab: "resource" }} />} />

      {/* 旧路由重定向到项目中心 */}
      <Route path="/projects" element={<ProjectManagementCenterRedirect tab="board" params={{ view: "card" }} />} />

      {/* 项目阶段视图 - 重定向到项目中心的流水线视图 */}
      <Route path="/stage-view" element={<ProjectManagementCenterRedirect tab="board" params={{ view: "pipeline" }} />} />
      <Route path="/projects/stage-view" element={<ProjectManagementCenterRedirect tab="board" params={{ view: "pipeline" }} />} />

      {/* 进度跟踪模块 - 新路由 */}
      <Route path="/progress-tracking/tasks" element={<ProjectManagementCenterRedirect tab="tasks" />} />
      <Route path="/progress-tracking/board" element={<ProjectManagementCenterRedirect tab="board" />} />
      <Route path="/progress-tracking/schedule" element={<ProjectManagementCenterRedirect tab="tracking" params={{ trackingTab: "schedule" }} />} />
      <Route path="/progress-tracking/reports" element={<ProjectManagementCenterRedirect tab="tracking" params={{ trackingTab: "reports" }} />} />
      <Route path="/progress-tracking/milestones" element={<ProjectManagementCenterRedirect tab="tracking" params={{ trackingTab: "milestones" }} />} />
      <Route path="/progress-tracking/wbs" element={<ProjectManagementCenterRedirect tab="tracking" params={{ trackingTab: "wbs" }} />} />
      <Route path="/progress-tracking/gantt" element={<ProjectManagementCenterRedirect tab="planning" params={{ planningTab: "task" }} />} />
      <Route path="/progress-tracking/timeline" element={<ProjectManagementCenterRedirect tab="board" params={{ view: "timeline" }} />} />

      {/* 向后兼容 - 保留旧路由 */}
      <Route path="/board" element={<ProjectManagementCenterRedirect tab="board" />} />
      <Route path="/projects/:id" element={<ProjectDetail />} />
      <Route path="/projects/:id/workspace" element={<ProjectWorkspace />} />
      <Route
        path="/projects/:id/contributions"
        element={<ProjectContributionReport />}
      />
      <Route path="/projects/:id/gantt" element={<ProjectManagementCenterRedirect tab="planning" params={{ planningTab: "task" }} />} />
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
      <Route path="/wbs-templates" element={<ProjectManagementCenterRedirect tab="tracking" params={{ trackingTab: "wbs" }} />} />
      <Route path="/schedule" element={<ProjectManagementCenterRedirect tab="tracking" params={{ trackingTab: "schedule" }} />} />
      <Route path="/ecn" element={<ECNManagement />} />
      <Route path="/ecn/:ecnId/cost-impact" element={<ECNCostImpact />} />
      <Route path="/ecn/:ecnId/material-impact" element={<ECNMaterialImpact />} />
      <Route path="/field-commissioning" element={<FieldCommissioning />} />
      <Route path="/projects/:projectId/material-progress" element={<MaterialProgressView />} />
      <Route path="/projects/:id/schedule-generation" element={<ScheduleGeneration />} />
      <Route path="/schedule-plans" element={<SchedulePlansList />} />
      <Route path="/schedule-plans/:planId" element={<SchedulePlanDetail />} />
      <Route path="/progress-tracking/resource-overview" element={<ProjectManagementCenterRedirect tab="planning" params={{ planningTab: "resource" }} />} />
      <Route path="/project-list-with-cost" element={<ProjectListWithCost />} />
      <Route path="/projects/:projectId/schedule-optimization" element={<ScheduleOptimization />} />
      <Route path="/projects/:projectId/engineer-recommendation" element={<EngineerRecommendation />} />
      <Route path="/projects/:projectId/engineer-workload-board" element={<EngineerWorkloadBoard />} />
      <Route path="/project-presales-tasks" element={<PresalesCenterRedirect tab="reviews" />} />
      <Route path="/tasks" element={<ProjectManagementCenterRedirect tab="tasks" />} />
      <Route path="/assembly-tasks" element={<AssemblerTaskCenter />} />
      <Route path="/workstation" element={<EngineerWorkstation />} />
      <Route path="/acceptance" element={<AcceptanceManagement />} />
      <Route path="/template-configs" element={<TemplateConfigList />} />
      <Route path="/margin-prediction" element={<MarginPrediction />} />
    </>
  );
}
