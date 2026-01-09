import { lazy } from 'react'

// System Management Pages
const UserManagement = lazy(() => import('../pages/UserManagement'))
const RoleManagement = lazy(() => import('../pages/RoleManagement'))
const PermissionManagement = lazy(() => import('../pages/PermissionManagement'))
const ProjectRoleTypeManagement = lazy(() => import('../pages/ProjectRoleTypeManagement'))
const SchedulerMonitoringDashboard = lazy(() => import('../pages/SchedulerMonitoringDashboard'))
const SchedulerConfigManagement = lazy(() => import('../pages/SchedulerConfigManagement'))

// Master Data Management
const CustomerManagement = lazy(() => import('../pages/CustomerManagement'))
const Customer360 = lazy(() => import('../pages/Customer360'))
const SupplierManagementData = lazy(() => import('../pages/SupplierManagementData'))
const DepartmentManagement = lazy(() => import('../pages/DepartmentManagement'))

// Alert Management
const AlertCenter = lazy(() => import('../pages/AlertCenter'))
const AlertRuleConfig = lazy(() => import('../pages/AlertRuleConfig'))
const AlertDetail = lazy(() => import('../pages/AlertDetail'))
const AlertStatistics = lazy(() => import('../pages/AlertStatistics'))
const AlertSubscription = lazy(() => import('../pages/AlertSubscription'))
const AlertSubscriptionSettings = lazy(() => import('../pages/AlertSubscriptionSettings'))

// Quality & Exceptions
const Acceptance = lazy(() => import('../pages/Acceptance'))
const ApprovalCenter = lazy(() => import('../pages/ApprovalCenter'))
const IssueManagement = lazy(() => import('../pages/IssueManagement'))
const IssueTemplateManagement = lazy(() => import('../pages/IssueTemplateManagement'))
const IssueStatisticsSnapshot = lazy(() => import('../pages/IssueStatisticsSnapshot'))
const TechnicalSpecManagement = lazy(() => import('../pages/TechnicalSpecManagement'))
const ExceptionManagement = lazy(() => import('../pages/ExceptionManagement'))
const ShortageAlert = lazy(() => import('../pages/ShortageAlert'))

// ECN Management
const ECNManagement = lazy(() => import('../pages/ECNManagement'))
const ECNDetail = lazy(() => import('../pages/ECNDetail'))
const ECNTypeManagement = lazy(() => import('../pages/ECNTypeManagement'))
const ECNOverdueAlerts = lazy(() => import('../pages/ECNOverdueAlerts'))
const ECNStatistics = lazy(() => import('../pages/ECNStatistics'))

// Personal Center
const WorkCenter = lazy(() => import('../pages/WorkCenter'))
const NotificationCenter = lazy(() => import('../pages/NotificationCenter'))
const Timesheet = lazy(() => import('../pages/Timesheet'))
const WorkLog = lazy(() => import('../pages/WorkLog'))
const WorkLogConfig = lazy(() => import('../pages/WorkLogConfig'))
const Settings = lazy(() => import('../pages/Settings'))
const PunchIn = lazy(() => import('../pages/PunchIn'))

// Debug
const PermissionDebug = lazy(() => import('../pages/PermissionDebug'))

export const systemRoutes = [
  // System Management
  { path: '/user-management', element: <UserManagement /> },
  { path: '/role-management', element: <RoleManagement /> },
  { path: '/permission-management', element: <PermissionManagement /> },
  { path: '/project-role-types', element: <ProjectRoleTypeManagement /> },
  { path: '/scheduler-monitoring', element: <SchedulerMonitoringDashboard /> },
  { path: '/scheduler-config', element: <SchedulerConfigManagement /> },

  // Master Data
  { path: '/customer-management', element: <CustomerManagement /> },
  { path: '/customers/:id/360', element: <Customer360 /> },
  { path: '/supplier-management-data', element: <SupplierManagementData /> },
  { path: '/department-management', element: <DepartmentManagement /> },

  // Alerts
  { path: '/alerts', element: <AlertCenter /> },
  { path: '/alerts/:id', element: <AlertDetail /> },
  { path: '/alert-rules', element: <AlertRuleConfig /> },
  { path: '/alert-statistics', element: <AlertStatistics /> },
  { path: '/alert-subscription', element: <AlertSubscription /> },
  { path: '/alerts/subscriptions', element: <AlertSubscriptionSettings /> },
  { path: '/settings/alert-subscriptions', element: <AlertSubscriptionSettings /> },

  // Quality & Exceptions
  { path: '/acceptance', element: <Acceptance /> },
  { path: '/approvals', element: <ApprovalCenter /> },
  { path: '/issues', element: <IssueManagement /> },
  { path: '/issue-templates', element: <IssueTemplateManagement /> },
  { path: '/issue-statistics-snapshot', element: <IssueStatisticsSnapshot /> },
  { path: '/technical-spec', element: <TechnicalSpecManagement /> },
  { path: '/exceptions', element: <ExceptionManagement /> },

  // ECN
  { path: '/ecns', element: <ECNManagement /> },
  { path: '/ecns/:id', element: <ECNDetail /> },
  { path: '/ecn-types', element: <ECNTypeManagement /> },
  { path: '/ecn-overdue-alerts', element: <ECNOverdueAlerts /> },
  { path: '/ecn-statistics', element: <ECNStatistics /> },

  // Personal Center
  { path: '/work-center', element: <WorkCenter /> },
  { path: '/notifications', element: <NotificationCenter /> },
  { path: '/timesheet', element: <Timesheet /> },
  { path: '/work-log', element: <WorkLog /> },
  { path: '/work-log/config', element: <WorkLogConfig /> },
  { path: '/settings', element: <Settings /> },
  { path: '/punch-in', element: <PunchIn /> },

  // Debug
  { path: '/debug/permissions', element: <PermissionDebug /> },
]
