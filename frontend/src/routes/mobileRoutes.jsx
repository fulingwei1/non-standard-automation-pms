import { lazy } from 'react'

// Mobile Pages
const MobileWorkerTaskList = lazy(() => import('../pages/mobile/MobileWorkerTaskList'))
const MobileScanStart = lazy(() => import('../pages/mobile/MobileScanStart'))
const MobileProgressReport = lazy(() => import('../pages/mobile/MobileProgressReport'))
const MobileCompleteReport = lazy(() => import('../pages/mobile/MobileCompleteReport'))
const MobileExceptionReport = lazy(() => import('../pages/mobile/MobileExceptionReport'))
const MobileMaterialRequisition = lazy(() => import('../pages/mobile/MobileMaterialRequisition'))
const MobileScanShortage = lazy(() => import('../pages/mobile/MobileScanShortage'))
const MobileShortageReport = lazy(() => import('../pages/mobile/MobileShortageReport'))
const MobileMyShortageReports = lazy(() => import('../pages/mobile/MobileMyShortageReports'))

export const mobileRoutes = [
  { path: '/mobile/tasks', element: <MobileWorkerTaskList /> },
  { path: '/mobile/scan-start', element: <MobileScanStart /> },
  { path: '/mobile/progress-report', element: <MobileProgressReport /> },
  { path: '/mobile/complete-report', element: <MobileCompleteReport /> },
  { path: '/mobile/exception-report', element: <MobileExceptionReport /> },
  { path: '/mobile/material-requisition', element: <MobileMaterialRequisition /> },
  { path: '/mobile/scan-shortage', element: <MobileScanShortage /> },
  { path: '/mobile/shortage-report', element: <MobileShortageReport /> },
  { path: '/mobile/my-shortage-reports', element: <MobileMyShortageReports /> },
]
