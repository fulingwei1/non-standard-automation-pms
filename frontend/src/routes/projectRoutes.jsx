import { lazy } from 'react'

// Project Management Pages
const ProjectList = lazy(() => import('../pages/ProjectList'))
const ProjectDetail = lazy(() => import('../pages/ProjectDetail'))
const ProjectWorkspace = lazy(() => import('../pages/ProjectWorkspace'))
const ProjectContributionReport = lazy(() => import('../pages/ProjectContributionReport'))
const ProjectBoard = lazy(() => import('../pages/ProjectBoard'))
const ProjectGantt = lazy(() => import('../pages/ProjectGantt'))
const ProjectTaskList = lazy(() => import('../pages/ProjectTaskList'))
const MachineManagement = lazy(() => import('../pages/MachineManagement'))
const MilestoneManagement = lazy(() => import('../pages/MilestoneManagement'))
const ProgressReport = lazy(() => import('../pages/ProgressReport'))
const ProgressBoard = lazy(() => import('../pages/ProgressBoard'))
const MilestoneRateReport = lazy(() => import('../pages/MilestoneRateReport'))
const DelayReasonsReport = lazy(() => import('../pages/DelayReasonsReport'))
const WBSTemplateManagement = lazy(() => import('../pages/WBSTemplateManagement'))
const ScheduleBoard = lazy(() => import('../pages/ScheduleBoard'))
const TaskCenter = lazy(() => import('../pages/TaskCenter'))
const AssemblerTaskCenter = lazy(() => import('../pages/AssemblerTaskCenter'))
const EngineerWorkstation = lazy(() => import('../pages/EngineerWorkstation'))

export const projectRoutes = [
  { path: '/board', element: <ProjectBoard /> },
  { path: '/projects', element: <ProjectList /> },
  { path: '/projects/:id', element: <ProjectDetail /> },
  { path: '/projects/:id/workspace', element: <ProjectWorkspace /> },
  { path: '/projects/:id/contributions', element: <ProjectContributionReport /> },
  { path: '/projects/:id/gantt', element: <ProjectGantt /> },
  { path: '/projects/:id/tasks', element: <ProjectTaskList /> },
  { path: '/projects/:id/machines', element: <MachineManagement /> },
  { path: '/projects/:id/milestones', element: <MilestoneManagement /> },
  { path: '/projects/:id/progress-report', element: <ProgressReport /> },
  { path: '/projects/:id/progress-board', element: <ProgressBoard /> },
  { path: '/projects/:id/milestone-rate', element: <MilestoneRateReport /> },
  { path: '/projects/:id/delay-reasons', element: <DelayReasonsReport /> },
  { path: '/reports/milestone-rate', element: <MilestoneRateReport /> },
  { path: '/reports/delay-reasons', element: <DelayReasonsReport /> },
  { path: '/wbs-templates', element: <WBSTemplateManagement /> },
  { path: '/schedule', element: <ScheduleBoard /> },
  { path: '/tasks', element: <TaskCenter /> },
  { path: '/assembly-tasks', element: <AssemblerTaskCenter /> },
  { path: '/workstation', element: <EngineerWorkstation /> },
]
