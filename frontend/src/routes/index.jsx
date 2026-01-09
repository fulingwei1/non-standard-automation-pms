import { Suspense } from 'react'
import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { ProcurementProtectedRoute, FinanceProtectedRoute, ProductionProtectedRoute, ProjectReviewProtectedRoute } from '../components/common/ProtectedRoute'

// Import route configurations
import { dashboardRoutes } from './dashboardRoutes'
import { projectRoutes } from './projectRoutes'
import { salesRoutes } from './salesRoutes'
import { productionRoutes } from './productionRoutes'
import { procurementRoutes } from './procurementRoutes'
import { financeRoutes } from './financeRoutes'
import { hrRoutes } from './hrRoutes'
import { pmoRoutes } from './pmoRoutes'
import { serviceRoutes } from './serviceRoutes'
import { systemRoutes } from './systemRoutes'
import { mobileRoutes } from './mobileRoutes'

// Role-based dashboard redirect mapping
const roleDashboardMap = {
  chairman: '/chairman-dashboard',
  gm: '/gm-dashboard',
  admin: '/admin-dashboard',
  super_admin: '/admin-dashboard',
  sales_director: '/sales-director-dashboard',
  sales_manager: '/sales-manager-dashboard',
  sales: '/sales-dashboard',
  business_support: '/business-support',
  presales: '/presales-dashboard',
  presales_manager: '/presales-manager-dashboard',
  project_dept_manager: '/pmo/dashboard',
  pm: '/pmo/dashboard',
  pmc: '/pmo/dashboard',
  tech_dev_manager: '/workstation',
  rd_engineer: '/workstation',
  me_dept_manager: '/workstation',
  te_dept_manager: '/workstation',
  ee_dept_manager: '/workstation',
  me_engineer: '/workstation',
  te_engineer: '/workstation',
  ee_engineer: '/workstation',
  sw_engineer: '/workstation',
  procurement_manager: '/procurement-manager-dashboard',
  procurement_engineer: '/procurement-dashboard',
  manufacturing_director: '/manufacturing-director-dashboard',
  production_manager: '/production-dashboard',
  assembler: '/assembly-tasks',
  assembler_mechanic: '/assembly-tasks',
  assembler_electrician: '/assembly-tasks',
  customer_service_engineer: '/customer-service-dashboard',
  customer_service_manager: '/customer-service-dashboard',
  finance_manager: '/finance-manager-dashboard',
  hr_manager: '/hr-manager-dashboard',
  administrative_manager: '/administrative-dashboard',
}

// Loading fallback component
const LoadingFallback = () => (
  <div className="flex items-center justify-center h-64">
    <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500"></div>
  </div>
)

// Wrapper components mapping
const wrappers = {
  procurement: ProcurementProtectedRoute,
  finance: FinanceProtectedRoute,
  production: ProductionProtectedRoute,
  projectReview: ProjectReviewProtectedRoute,
}

// ProtectedRoute component for role-based redirect on root path
function ProtectedRoute({ children }) {
  const location = useLocation()

  if (location.pathname === '/') {
    const userStr = localStorage.getItem('user')
    if (userStr) {
      try {
        const user = JSON.parse(userStr)
        const role = user.role
        if (role && roleDashboardMap[role]) {
          return <Navigate to={roleDashboardMap[role]} replace />
        }
      } catch {
        localStorage.removeItem('user')
      }
    }
  }

  return children
}

// Helper to wrap element with protection if needed
const wrapElement = (element, wrapper, isProtected) => {
  let wrapped = element
  if (wrapper) {
    const Wrapper = wrappers[wrapper]
    if (Wrapper) {
      wrapped = <Wrapper>{wrapped}</Wrapper>
    }
  }
  if (isProtected) {
    wrapped = <ProtectedRoute>{wrapped}</ProtectedRoute>
  }
  return wrapped
}

// Helper to render route with Suspense
const renderRoute = (route) => {
  const element = (
    <Suspense fallback={<LoadingFallback />}>
      {wrapElement(route.element, route.wrapper, route.protected)}
    </Suspense>
  )
  return <Route key={route.path} path={route.path} element={element} />
}

// Combine all routes
const allRoutes = [
  ...dashboardRoutes,
  ...projectRoutes,
  ...salesRoutes,
  ...productionRoutes,
  ...procurementRoutes,
  ...financeRoutes,
  ...hrRoutes,
  ...pmoRoutes,
  ...serviceRoutes,
  ...systemRoutes,
  ...mobileRoutes,
]

// Main AppRoutes component
export default function AppRoutes() {
  return (
    <Routes>
      {allRoutes.map(renderRoute)}
      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  )
}

// Export route configs for external use
export {
  dashboardRoutes,
  projectRoutes,
  salesRoutes,
  productionRoutes,
  procurementRoutes,
  financeRoutes,
  hrRoutes,
  pmoRoutes,
  serviceRoutes,
  systemRoutes,
  mobileRoutes,
  allRoutes,
}
