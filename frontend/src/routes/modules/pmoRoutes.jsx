import { Route } from "react-router-dom";
import { ProjectReviewProtectedRoute } from "../../components/common/ProtectedRoute";

import PMODashboard from "../../pages/PMODashboard";
import InitiationManagement from "../../pages/InitiationManagement";
import ProjectPhaseManagement from "../../pages/ProjectPhaseManagement";
import RiskManagement from "../../pages/RiskManagement";
import ProjectClosureManagement from "../../pages/ProjectClosureManagement";
import ProjectReviewList from "../../pages/ProjectReviewList";
import ProjectReviewDetail from "../../pages/ProjectReviewDetail";
import LessonsLearnedLibrary from "../../pages/LessonsLearnedLibrary";
import BestPracticeRecommendations from "../../pages/BestPracticeRecommendations";
import ResourceOverview from "../../pages/ResourceOverview";
import MeetingManagement from "../../pages/MeetingManagement";
import RiskWall from "../../pages/RiskWall";
import WeeklyReport from "../../pages/WeeklyReport";

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
