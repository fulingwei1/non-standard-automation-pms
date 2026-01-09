import { lazy } from 'react'

// Production Pages
const ProductionDashboard = lazy(() => import('../pages/ProductionDashboard'))
const ProductionManagerDashboard = lazy(() => import('../pages/ProductionManagerDashboard'))
const ManufacturingDirectorDashboard = lazy(() => import('../pages/ManufacturingDirectorDashboard'))
const WorkOrderManagement = lazy(() => import('../pages/WorkOrderManagement'))
const WorkOrderDetail = lazy(() => import('../pages/WorkOrderDetail'))
const DispatchManagement = lazy(() => import('../pages/DispatchManagement'))
const InstallationDispatchManagement = lazy(() => import('../pages/InstallationDispatchManagement'))
const ProductionPlanList = lazy(() => import('../pages/ProductionPlanList'))
const WorkReportList = lazy(() => import('../pages/WorkReportList'))
const MaterialRequisitionList = lazy(() => import('../pages/MaterialRequisitionList'))
const MaterialRequisitionDetail = lazy(() => import('../pages/MaterialRequisitionDetail'))
const ProductionExceptionList = lazy(() => import('../pages/ProductionExceptionList'))
const WorkshopManagement = lazy(() => import('../pages/WorkshopManagement'))
const WorkerManagement = lazy(() => import('../pages/WorkerManagement'))
const WorkerWorkstation = lazy(() => import('../pages/WorkerWorkstation'))
const OutsourcingOrderList = lazy(() => import('../pages/OutsourcingOrderList'))
const OutsourcingOrderDetail = lazy(() => import('../pages/OutsourcingOrderDetail'))
const AcceptanceOrderList = lazy(() => import('../pages/AcceptanceOrderList'))
const AcceptanceExecution = lazy(() => import('../pages/AcceptanceExecution'))
const AcceptanceTemplateManagement = lazy(() => import('../pages/AcceptanceTemplateManagement'))
const ShortageManagementBoard = lazy(() => import('../pages/ShortageManagementBoard'))
const ShortageReportList = lazy(() => import('../pages/ShortageReportList'))
const ArrivalTrackingList = lazy(() => import('../pages/ArrivalTrackingList'))
const WorkloadBoard = lazy(() => import('../pages/WorkloadBoard'))
const WorkshopTaskBoard = lazy(() => import('../pages/WorkshopTaskBoard'))
const AssemblyKitBoard = lazy(() => import('../pages/AssemblyKitBoard'))

export const productionRoutes = [
  { path: '/production-dashboard', element: <ProductionDashboard /> },
  { path: '/production-manager-dashboard', element: <ProductionManagerDashboard /> },
  { path: '/manufacturing-director-dashboard', element: <ManufacturingDirectorDashboard /> },
  { path: '/work-orders', element: <WorkOrderManagement /> },
  { path: '/work-orders/:id', element: <WorkOrderDetail /> },
  { path: '/dispatch-management', element: <DispatchManagement /> },
  { path: '/installation-dispatch', element: <InstallationDispatchManagement /> },
  { path: '/production-plans', element: <ProductionPlanList /> },
  { path: '/work-reports', element: <WorkReportList /> },
  { path: '/material-requisitions', element: <MaterialRequisitionList /> },
  { path: '/material-requisitions/:id', element: <MaterialRequisitionDetail /> },
  { path: '/production-exceptions', element: <ProductionExceptionList /> },
  { path: '/workshops', element: <WorkshopManagement /> },
  { path: '/workers', element: <WorkerManagement /> },
  { path: '/worker-workstation', element: <WorkerWorkstation /> },
  { path: '/outsourcing-orders', element: <OutsourcingOrderList /> },
  { path: '/outsourcing-orders/:id', element: <OutsourcingOrderDetail /> },
  { path: '/acceptance-orders', element: <AcceptanceOrderList /> },
  { path: '/acceptance-orders/:id/execute', element: <AcceptanceExecution /> },
  { path: '/acceptance-templates', element: <AcceptanceTemplateManagement /> },
  { path: '/shortage-management-board', element: <ShortageManagementBoard /> },
  { path: '/shortage-reports', element: <ShortageReportList /> },
  { path: '/arrival-tracking', element: <ArrivalTrackingList /> },
  { path: '/workload-board', element: <WorkloadBoard /> },
  { path: '/workshops/:id/task-board', element: <WorkshopTaskBoard /> },
  { path: '/assembly-kit', element: <AssemblyKitBoard />, wrapper: 'production' },
]
