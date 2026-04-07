import { lazyLoad } from "../lazyLoad";

const PMODashboard = lazyLoad(() => import("../../pages/PMODashboard"));
const InitiationManagement = lazyLoad(() => import("../../pages/InitiationManagement"));
const ProjectPhaseManagement = lazyLoad(() => import("../../pages/ProjectPhaseManagement"));
const RiskManagement = lazyLoad(() => import("../../pages/RiskManagement"));
const ProjectClosureManagement = lazyLoad(() => import("../../pages/ProjectClosureManagement"));
const ProjectReviewList = lazyLoad(() => import("../../pages/ProjectReviewList"));
const ProjectReviewDetail = lazyLoad(() => import("../../pages/ProjectReviewDetail"));
const LessonsLearnedLibrary = lazyLoad(() => import("../../pages/LessonsLearnedLibrary"));
const BestPracticeRecommendations = lazyLoad(() => import("../../pages/BestPracticeRecommendations"));
const ResourceOverview = lazyLoad(() => import("../../pages/ResourceOverview"));
const MeetingManagement = lazyLoad(() => import("../../pages/MeetingManagement"));
const RiskWall = lazyLoad(() => import("../../pages/RiskWall"));
const WeeklyReport = lazyLoad(() => import("../../pages/WeeklyReport"));

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
