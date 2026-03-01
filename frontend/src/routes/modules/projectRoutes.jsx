import { Route } from "react-router-dom";
import { ProjectReviewProtectedRoute } from "../../components/common/ProtectedRoute";

import ProjectList from "../../pages/ProjectList";
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
import AssemblyTemplateManagement from "../../pages/AssemblyTemplateManagement";
import EngineerRecommendation from "../../pages/EngineerRecommendation";
import EngineerWorkloadBoard from "../../pages/EngineerWorkloadBoard";
import EngineerWorkstation from "../../pages/EngineerWorkstation";
import ProjectStageView from "../../pages/ProjectStageView";
import ProjectTimelineView from "../../pages/ProjectTimelineView";
import PresalesTasks from "../../pages/PresalesTasks";
import ProjectListWithCost from "../../pages/ProjectListWithCost";
import ResourceOverview from "../../pages/ResourceOverview";
import LessonsLearned from "../../pages/LessonsLearned";
import AcceptanceManagement from "../../pages/AcceptanceManagement";
import GanttDependency from "../../pages/GanttDependency";
import ECNManagement from "../../pages/ECNManagement";
import FieldCommissioning from "../../pages/FieldCommissioning";
import ScheduleOptimization from "../../pages/ScheduleOptimization";
import ScheduleGeneration from "../../pages/ScheduleGeneration";

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
      <Route path="/projects" element={<ProjectList />} />
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
      <Route path="/resource-overview" element={<ResourceOverview />} />
      <Route path="/gantt" element={<GanttDependency />} />
      <Route path="/ecn" element={<ECNManagement />} />
      <Route path="/field-commissioning" element={<FieldCommissioning />} />
      <Route path="/projects/:id/schedule-generation" element={<ScheduleGeneration />} />
      <Route path="/progress-tracking/resource-overview" element={<ResourceOverview />} />
      <Route path="/project-list-with-cost" element={<ProjectListWithCost />} />
      <Route path="/projects/:projectId/schedule-optimization" element={<ScheduleOptimization />} />
      <Route path="/projects/:projectId/engineer-recommendation" element={<EngineerRecommendation />} />
      <Route path="/projects/:projectId/engineer-workload-board" element={<EngineerWorkloadBoard />} />
      <Route path="/assembly-template-management" element={<AssemblyTemplateManagement />} />
      <Route path="/project-presales-tasks" element={<PresalesTasks />} />
      <Route path="/tasks" element={<TaskCenter />} />
      <Route path="/assembly-tasks" element={<AssemblerTaskCenter />} />
      <Route path="/workstation" element={<EngineerWorkstation />} />
      <Route path="/lessons-learned" element={<LessonsLearned />} />
      <Route path="/acceptance" element={<AcceptanceManagement />} />
    </>
  );
}
