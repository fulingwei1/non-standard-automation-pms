import { lazy } from 'react'

// Procurement Pages
const ProcurementManagerDashboard = lazy(() => import('../pages/ProcurementManagerDashboard'))
const ProcurementEngineerWorkstation = lazy(() => import('../pages/ProcurementEngineerWorkstation'))
const PurchaseOrders = lazy(() => import('../pages/PurchaseOrders'))
const PurchaseOrderDetail = lazy(() => import('../pages/PurchaseOrderDetail'))
const PurchaseRequestList = lazy(() => import('../pages/PurchaseRequestList'))
const PurchaseRequestNew = lazy(() => import('../pages/PurchaseRequestNew'))
const PurchaseRequestDetail = lazy(() => import('../pages/PurchaseRequestDetail'))
const PurchaseOrderFromBOM = lazy(() => import('../pages/PurchaseOrderFromBOM'))
const GoodsReceiptNew = lazy(() => import('../pages/GoodsReceiptNew'))
const GoodsReceiptDetail = lazy(() => import('../pages/GoodsReceiptDetail'))
const ArrivalManagement = lazy(() => import('../pages/ArrivalManagement'))
const MaterialList = lazy(() => import('../pages/MaterialList'))
const MaterialTracking = lazy(() => import('../pages/MaterialTracking'))
const MaterialAnalysis = lazy(() => import('../pages/MaterialAnalysis'))
const BudgetManagement = lazy(() => import('../pages/BudgetManagement'))
const CostAnalysis = lazy(() => import('../pages/CostAnalysis'))
const MaterialDemandSummary = lazy(() => import('../pages/MaterialDemandSummary'))
const BOMManagement = lazy(() => import('../pages/BOMManagement'))
const KitRateBoard = lazy(() => import('../pages/KitRateBoard'))
const BomAssemblyAttrs = lazy(() => import('../pages/BomAssemblyAttrs'))
const SupplierManagement = lazy(() => import('../pages/SupplierManagement'))
const ShortageManagement = lazy(() => import('../pages/ShortageManagement'))
const ShortageReportNew = lazy(() => import('../pages/ShortageReportNew'))
const ShortageReportDetail = lazy(() => import('../pages/ShortageReportDetail'))
const ArrivalDetail = lazy(() => import('../pages/ArrivalDetail'))
const SubstitutionDetail = lazy(() => import('../pages/SubstitutionDetail'))
const TransferDetail = lazy(() => import('../pages/TransferDetail'))
const SubstitutionNew = lazy(() => import('../pages/SubstitutionNew'))
const TransferNew = lazy(() => import('../pages/TransferNew'))
const ArrivalNew = lazy(() => import('../pages/ArrivalNew'))
const KitCheck = lazy(() => import('../pages/KitCheck'))

export const procurementRoutes = [
  { path: '/procurement-manager-dashboard', element: <ProcurementManagerDashboard /> },
  { path: '/procurement-dashboard', element: <ProcurementEngineerWorkstation /> },
  { path: '/purchases', element: <PurchaseOrders />, wrapper: 'procurement' },
  { path: '/purchases/:id', element: <PurchaseOrderDetail />, wrapper: 'procurement' },
  { path: '/purchase-requests', element: <PurchaseRequestList />, wrapper: 'procurement' },
  { path: '/purchase-requests/new', element: <PurchaseRequestNew />, wrapper: 'procurement' },
  { path: '/purchase-requests/:id', element: <PurchaseRequestDetail />, wrapper: 'procurement' },
  { path: '/purchase-requests/:id/edit', element: <PurchaseRequestNew />, wrapper: 'procurement' },
  { path: '/purchases/from-bom', element: <PurchaseOrderFromBOM />, wrapper: 'procurement' },
  { path: '/purchases/receipts', element: <ArrivalManagement />, wrapper: 'procurement' },
  { path: '/purchases/receipts/new', element: <GoodsReceiptNew />, wrapper: 'procurement' },
  { path: '/purchases/receipts/:id', element: <GoodsReceiptDetail />, wrapper: 'procurement' },
  { path: '/materials', element: <MaterialList />, wrapper: 'procurement' },
  { path: '/material-tracking', element: <MaterialTracking />, wrapper: 'procurement' },
  { path: '/material-analysis', element: <MaterialAnalysis />, wrapper: 'procurement' },
  { path: '/budgets', element: <BudgetManagement />, wrapper: 'procurement' },
  { path: '/cost-analysis', element: <CostAnalysis />, wrapper: 'procurement' },
  { path: '/material-demands', element: <MaterialDemandSummary />, wrapper: 'procurement' },
  { path: '/bom', element: <BOMManagement />, wrapper: 'procurement' },
  { path: '/kit-rate', element: <KitRateBoard />, wrapper: 'procurement' },
  { path: '/bom-assembly-attrs', element: <BomAssemblyAttrs />, wrapper: 'procurement' },
  { path: '/arrivals', element: <ArrivalManagement />, wrapper: 'procurement' },
  { path: '/suppliers', element: <SupplierManagement /> },
  { path: '/shortage', element: <ShortageManagement />, wrapper: 'procurement' },
  { path: '/shortage/reports/new', element: <ShortageReportNew />, wrapper: 'procurement' },
  { path: '/shortage/reports/:id', element: <ShortageReportDetail />, wrapper: 'procurement' },
  { path: '/shortage/arrivals/:id', element: <ArrivalDetail />, wrapper: 'procurement' },
  { path: '/shortage/substitutions/:id', element: <SubstitutionDetail />, wrapper: 'procurement' },
  { path: '/shortage/transfers/:id', element: <TransferDetail />, wrapper: 'procurement' },
  { path: '/shortage/substitutions/new', element: <SubstitutionNew />, wrapper: 'procurement' },
  { path: '/shortage/transfers/new', element: <TransferNew />, wrapper: 'procurement' },
  { path: '/shortage/arrivals/new', element: <ArrivalNew />, wrapper: 'procurement' },
  { path: '/kit-check', element: <KitCheck />, wrapper: 'procurement' },
]
