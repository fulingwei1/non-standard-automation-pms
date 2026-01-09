import { lazy } from 'react'

// PMO Pages
const PMODashboard = lazy(() => import('../pages/PMODashboard'))
const InitiationManagement = lazy(() => import('../pages/InitiationManagement'))
const ProjectPhaseManagement = lazy(() => import('../pages/ProjectPhaseManagement'))
const RiskManagement = lazy(() => import('../pages/RiskManagement'))
const ProjectClosureManagement = lazy(() => import('../pages/ProjectClosureManagement'))
const ProjectReviewList = lazy(() => import('../pages/ProjectReviewList'))
const ProjectReviewDetail = lazy(() => import('../pages/ProjectReviewDetail'))
const LessonsLearnedLibrary = lazy(() => import('../pages/LessonsLearnedLibrary'))
const BestPracticeRecommendations = lazy(() => import('../pages/BestPracticeRecommendations'))
const TechnicalReviewList = lazy(() => import('../pages/TechnicalReviewList'))
const TechnicalReviewDetail = lazy(() => import('../pages/TechnicalReviewDetail'))
const ResourceOverview = lazy(() => import('../pages/ResourceOverview'))
const MeetingManagement = lazy(() => import('../pages/MeetingManagement'))
const RiskWall = lazy(() => import('../pages/RiskWall'))
const WeeklyReport = lazy(() => import('../pages/WeeklyReport'))
const SpecMatchCheck = lazy(() => import('../pages/SpecMatchCheck'))

// R&D Project Management
const RdProjectList = lazy(() => import('../pages/RdProjectList'))
const RdProjectDetail = lazy(() => import('../pages/RdProjectDetail'))
const RdCostEntry = lazy(() => import('../pages/RdCostEntry'))
const RdCostSummary = lazy(() => import('../pages/RdCostSummary'))
const RdCostReports = lazy(() => import('../pages/RdCostReports'))
const RdProjectWorklogs = lazy(() => import('../pages/RdProjectWorklogs'))
const RdProjectDocuments = lazy(() => import('../pages/RdProjectDocuments'))

export const pmoRoutes = [
  // PMO Dashboard
  { path: '/pmo/dashboard', element: <PMODashboard /> },
  { path: '/pmo/initiations', element: <InitiationManagement /> },
  { path: '/pmo/initiations/:id', element: <InitiationManagement /> },
  { path: '/pmo/phases', element: <ProjectPhaseManagement /> },
  { path: '/pmo/phases/:projectId', element: <ProjectPhaseManagement /> },
  { path: '/pmo/risks', element: <RiskManagement /> },
  { path: '/pmo/risks/:projectId', element: <RiskManagement /> },
  { path: '/pmo/closure', element: <ProjectClosureManagement /> },
  { path: '/pmo/closure/:projectId', element: <ProjectClosureManagement /> },
  { path: '/pmo/resource-overview', element: <ResourceOverview /> },
  { path: '/pmo/meetings', element: <MeetingManagement /> },
  { path: '/pmo/risk-wall', element: <RiskWall /> },
  { path: '/pmo/weekly-report', element: <WeeklyReport /> },

  // Project Reviews
  { path: '/projects/reviews', element: <ProjectReviewList />, wrapper: 'projectReview' },
  { path: '/projects/reviews/:reviewId', element: <ProjectReviewDetail />, wrapper: 'projectReview' },
  { path: '/projects/reviews/:reviewId/edit', element: <ProjectReviewDetail />, wrapper: 'projectReview' },
  { path: '/projects/reviews/new', element: <ProjectReviewDetail />, wrapper: 'projectReview' },
  { path: '/projects/lessons-learned', element: <LessonsLearnedLibrary />, wrapper: 'projectReview' },
  { path: '/projects/best-practices/recommend', element: <BestPracticeRecommendations />, wrapper: 'projectReview' },
  { path: '/projects/:projectId/best-practices/recommend', element: <BestPracticeRecommendations />, wrapper: 'projectReview' },

  // Technical Reviews
  { path: '/technical-reviews', element: <TechnicalReviewList /> },
  { path: '/technical-reviews/new', element: <TechnicalReviewDetail /> },
  { path: '/technical-reviews/:reviewId', element: <TechnicalReviewDetail /> },
  { path: '/technical-reviews/:reviewId/edit', element: <TechnicalReviewDetail /> },
  { path: '/spec-match-check', element: <SpecMatchCheck /> },

  // R&D Projects
  { path: '/rd-projects', element: <RdProjectList /> },
  { path: '/rd-projects/:id', element: <RdProjectDetail /> },
  { path: '/rd-projects/:id/worklogs', element: <RdProjectWorklogs /> },
  { path: '/rd-projects/:id/documents', element: <RdProjectDocuments /> },
  { path: '/rd-projects/:id/cost-entry', element: <RdCostEntry /> },
  { path: '/rd-projects/:id/cost-summary', element: <RdCostSummary /> },
  { path: '/rd-projects/:id/reports', element: <RdCostReports /> },
  { path: '/rd-cost-entry', element: <RdCostEntry /> },
  { path: '/rd-cost-summary', element: <RdCostSummary /> },
  { path: '/rd-cost-reports', element: <RdCostReports /> },
]
