import { lazy } from 'react'

// Dashboard Pages
const Dashboard = lazy(() => import('../pages/Dashboard'))
const ChairmanWorkstation = lazy(() => import('../pages/ChairmanWorkstation'))
const GeneralManagerWorkstation = lazy(() => import('../pages/GeneralManagerWorkstation'))
const AdminDashboard = lazy(() => import('../pages/AdminDashboard'))
const OperationDashboard = lazy(() => import('../pages/OperationDashboard'))
const ExecutiveDashboard = lazy(() => import('../pages/ExecutiveDashboard'))
const StrategyAnalysis = lazy(() => import('../pages/StrategyAnalysis'))
const KeyDecisions = lazy(() => import('../pages/KeyDecisions'))

// Management Rhythm
const ManagementRhythmDashboard = lazy(() => import('../pages/ManagementRhythmDashboard'))
const MeetingMap = lazy(() => import('../pages/MeetingMap'))
const StrategicMeetingManagement = lazy(() => import('../pages/StrategicMeetingManagement'))
const StrategicMeetingDetail = lazy(() => import('../pages/StrategicMeetingDetail'))
const MeetingReports = lazy(() => import('../pages/MeetingReports'))
const CultureWall = lazy(() => import('../pages/CultureWall'))

// Delivery
const Shipments = lazy(() => import('../pages/Shipments'))
const DeliveryManagement = lazy(() => import('../pages/DeliveryManagement'))
const Documents = lazy(() => import('../pages/Documents'))

export const dashboardRoutes = [
  { path: '/', element: <Dashboard />, protected: true },
  { path: '/chairman-dashboard', element: <ChairmanWorkstation />, protected: true },
  { path: '/gm-dashboard', element: <GeneralManagerWorkstation />, protected: true },
  { path: '/admin-dashboard', element: <AdminDashboard /> },
  { path: '/operation', element: <OperationDashboard /> },
  { path: '/strategy-analysis', element: <StrategyAnalysis /> },
  { path: '/key-decisions', element: <KeyDecisions /> },
  { path: '/executive-dashboard', element: <ExecutiveDashboard /> },
  { path: '/management-rhythm-dashboard', element: <ManagementRhythmDashboard /> },
  { path: '/meeting-map', element: <MeetingMap /> },
  { path: '/strategic-meetings', element: <StrategicMeetingManagement /> },
  { path: '/strategic-meetings/:id', element: <StrategicMeetingDetail /> },
  { path: '/meeting-reports', element: <MeetingReports /> },
  { path: '/meeting-reports/:id', element: <MeetingReports /> },
  { path: '/culture-wall', element: <CultureWall /> },
  { path: '/shipments', element: <Shipments /> },
  { path: '/pmc/delivery-plan', element: <DeliveryManagement /> },
  { path: '/pmc/delivery-orders', element: <DeliveryManagement /> },
  { path: '/pmc/delivery-orders/:id', element: <DeliveryManagement /> },
  { path: '/pmc/delivery-orders/:id/edit', element: <DeliveryManagement /> },
  { path: '/pmc/delivery-orders/new', element: <DeliveryManagement /> },
  { path: '/documents', element: <Documents /> },
]
