import { lazy } from 'react'

// HR Pages
const HRManagerDashboard = lazy(() => import('../pages/HRManagerDashboard'))
const AdministrativeManagerWorkstation = lazy(() => import('../pages/AdministrativeManagerWorkstation'))

// Performance Management
const PerformanceManagement = lazy(() => import('../pages/PerformanceManagement'))
const PerformanceRanking = lazy(() => import('../pages/PerformanceRanking'))
const PerformanceIndicators = lazy(() => import('../pages/PerformanceIndicators'))
const PerformanceResults = lazy(() => import('../pages/PerformanceResults'))
const MonthlySummary = lazy(() => import('../pages/MonthlySummary'))
const MyPerformance = lazy(() => import('../pages/MyPerformance'))
const MyBonus = lazy(() => import('../pages/MyBonus'))
const EvaluationTaskList = lazy(() => import('../pages/EvaluationTaskList'))
const EvaluationScoring = lazy(() => import('../pages/EvaluationScoring'))
const EvaluationWeightConfig = lazy(() => import('../pages/EvaluationWeightConfig'))

// Qualification Management
const QualificationManagement = lazy(() => import('../pages/QualificationManagement'))
const QualificationLevelForm = lazy(() => import('../pages/QualificationLevelForm'))
const CompetencyModelForm = lazy(() => import('../pages/CompetencyModelForm'))
const EmployeeQualificationForm = lazy(() => import('../pages/EmployeeQualificationForm'))
const QualificationAssessmentList = lazy(() => import('../pages/QualificationAssessmentList'))

// AI Staff Matching
const TagManagement = lazy(() => import('../pages/TagManagement'))
const EmployeeProfileList = lazy(() => import('../pages/EmployeeProfileList'))
const EmployeeProfileDetail = lazy(() => import('../pages/EmployeeProfileDetail'))
const ProjectStaffingNeed = lazy(() => import('../pages/ProjectStaffingNeed'))
const AIStaffMatching = lazy(() => import('../pages/AIStaffMatching'))

export const hrRoutes = [
  // HR Dashboard
  { path: '/hr-manager-dashboard', element: <HRManagerDashboard /> },
  { path: '/administrative-dashboard', element: <AdministrativeManagerWorkstation /> },

  // Performance Management
  { path: '/performance', element: <PerformanceManagement /> },
  { path: '/performance/ranking', element: <PerformanceRanking /> },
  { path: '/performance/indicators', element: <PerformanceIndicators /> },
  { path: '/performance/results', element: <PerformanceResults /> },
  { path: '/performance/results/:employeeId', element: <PerformanceResults /> },

  // Personal Performance
  { path: '/personal/monthly-summary', element: <MonthlySummary /> },
  { path: '/personal/my-performance', element: <MyPerformance /> },
  { path: '/personal/my-bonus', element: <MyBonus /> },

  // Evaluation
  { path: '/evaluation-tasks', element: <EvaluationTaskList /> },
  { path: '/evaluation/:taskId', element: <EvaluationScoring /> },
  { path: '/evaluation-weight-config', element: <EvaluationWeightConfig /> },

  // Qualification Management
  { path: '/qualifications', element: <QualificationManagement /> },
  { path: '/qualifications/levels/new', element: <QualificationLevelForm /> },
  { path: '/qualifications/levels/:id', element: <QualificationLevelForm /> },
  { path: '/qualifications/levels/:id/edit', element: <QualificationLevelForm /> },
  { path: '/qualifications/models/new', element: <CompetencyModelForm /> },
  { path: '/qualifications/models/:id', element: <CompetencyModelForm /> },
  { path: '/qualifications/models/:id/edit', element: <CompetencyModelForm /> },
  { path: '/qualifications/employees/certify', element: <EmployeeQualificationForm /> },
  { path: '/qualifications/employees/:employeeId', element: <EmployeeQualificationForm /> },
  { path: '/qualifications/employees/:employeeId/view', element: <EmployeeQualificationForm /> },
  { path: '/qualifications/employees/:employeeId/promote', element: <EmployeeQualificationForm /> },
  { path: '/qualifications/assessments', element: <QualificationAssessmentList /> },

  // AI Staff Matching
  { path: '/staff-matching/tags', element: <TagManagement /> },
  { path: '/staff-matching/profiles', element: <EmployeeProfileList /> },
  { path: '/staff-matching/profiles/:id', element: <EmployeeProfileDetail /> },
  { path: '/staff-matching/staffing-needs', element: <ProjectStaffingNeed /> },
  { path: '/staff-matching/matching', element: <AIStaffMatching /> },
]
