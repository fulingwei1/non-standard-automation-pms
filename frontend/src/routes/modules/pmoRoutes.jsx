import { lazy } from "react";
import { Route } from "react-router-dom";
import { ProjectReviewProtectedRoute } from "../../components/common/ProtectedRoute";

// ---- 懒加载页面组件（PMO模块） ----
const PMODashboard = lazy(() => import("../../pages/PMODashboard"));
const InitiationManagement = lazy(() => import("../../pages/InitiationManagement"));
const ProjectPhaseManagement = lazy(() => import("../../pages/ProjectPhaseManagement"));
const RiskManagement = lazy(() => import("../../pages/RiskManagement"));
const ProjectClosureManagement = lazy(() => import("../../pages/ProjectClosureManagement"));
const ProjectReviewList = lazy(() => import("../../pages/ProjectReviewList"));
const ProjectReviewDetail = lazy(() => import("../../pages/ProjectReviewDetail"));
const LessonsLearnedLibrary = lazy(() => import("../../pages/LessonsLearnedLibrary"));
const BestPracticeRecommendations = lazy(() => import("../../pages/BestPracticeRecommendations"));
const ResourceOverview = lazy(() => import("../../pages/ResourceOverview"));
const MeetingManagement = lazy(() => import("../../pages/MeetingManagement"));
const RiskWall = lazy(() => import("../../pages/RiskWall"));
const WeeklyReport = lazy(() => import("../../pages/WeeklyReport"));

export function PMORoutes() {
  return (
    <>
      <Route path="/pmo/dashboard" element={<PMODashboard />} />
      <Route path="/pmo/initiations" element={<InitiationManagement />} />
      <Route path="/pmo/initiations/:id" element={<InitiationManagement />} />
      <Route path="/pmo/phases" element={<ProjectPhaseManagement />} />
      <Route
        path="/pmo/phases/:projectId"
        element={<ProjectPhaseManagement />}
      />
      <Route path="/pmo/risks" element={<RiskManagement />} />
      <Route path="/pmo/risks/:projectId" element={<RiskManagement />} />
      <Route path="/pmo/closure" element={<ProjectClosureManagement />} />
      <Route
        path="/pmo/closure/:projectId"
        element={<ProjectClosureManagement />}
      />
      <Route
        path="/projects/reviews"
        element={
          <ProjectReviewProtectedRoute>
            <ProjectReviewList />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/reviews/:reviewId"
        element={
          <ProjectReviewProtectedRoute>
            <ProjectReviewDetail />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/reviews/:reviewId/edit"
        element={
          <ProjectReviewProtectedRoute>
            <ProjectReviewDetail />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/reviews/new"
        element={
          <ProjectReviewProtectedRoute>
            <ProjectReviewDetail />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/lessons-learned"
        element={
          <ProjectReviewProtectedRoute>
            <LessonsLearnedLibrary />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/best-practices/recommend"
        element={
          <ProjectReviewProtectedRoute>
            <BestPracticeRecommendations />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/:projectId/best-practices/recommend"
        element={
          <ProjectReviewProtectedRoute>
            <BestPracticeRecommendations />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route path="/pmo/resource-overview" element={<ResourceOverview />} />
      <Route path="/pmo/meetings" element={<MeetingManagement />} />
      <Route path="/pmo/risk-wall" element={<RiskWall />} />
      <Route path="/pmo/weekly-report" element={<WeeklyReport />} />
    </>
  );
}
