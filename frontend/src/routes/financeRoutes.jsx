import { lazy } from 'react'

// Finance Pages
const FinanceManagerDashboard = lazy(() => import('../pages/FinanceManagerDashboard'))
const CostAccounting = lazy(() => import('../pages/CostAccounting'))
const PaymentApproval = lazy(() => import('../pages/PaymentApproval'))
const ProjectSettlement = lazy(() => import('../pages/ProjectSettlement'))
const FinancialReports = lazy(() => import('../pages/FinancialReports'))
const PaymentManagement = lazy(() => import('../pages/PaymentManagement'))
const InvoiceManagement = lazy(() => import('../pages/InvoiceManagement'))

export const financeRoutes = [
  { path: '/finance-manager-dashboard', element: <FinanceManagerDashboard />, wrapper: 'finance' },
  { path: '/costs', element: <CostAccounting /> },
  { path: '/payment-approval', element: <PaymentApproval /> },
  { path: '/settlement', element: <ProjectSettlement /> },
  { path: '/financial-reports', element: <FinancialReports /> },
  { path: '/payments', element: <PaymentManagement />, wrapper: 'finance' },
  { path: '/invoices', element: <InvoiceManagement />, wrapper: 'finance' },
]
