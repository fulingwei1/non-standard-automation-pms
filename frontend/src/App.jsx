import { useState } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { cn } from './lib/utils'

// Layout Components
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'

// Pages
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import ProjectList from './pages/ProjectList'
import ProjectDetail from './pages/ProjectDetail'
import ProjectBoard from './pages/ProjectBoard'
import NotificationCenter from './pages/NotificationCenter'
import Timesheet from './pages/Timesheet'
import Settings from './pages/Settings'
import ScheduleBoard from './pages/ScheduleBoard'
import MaterialAnalysis from './pages/MaterialAnalysis'
import PurchaseOrders from './pages/PurchaseOrders'
import TaskCenter from './pages/TaskCenter'
import OperationDashboard from './pages/OperationDashboard'
import ApprovalCenter from './pages/ApprovalCenter'
import Acceptance from './pages/Acceptance'
import AssemblerTaskCenter from './pages/AssemblerTaskCenter'
import EngineerWorkstation from './pages/EngineerWorkstation'
import SalesWorkstation from './pages/SalesWorkstation'
import BusinessSupportWorkstation from './pages/BusinessSupportWorkstation'
import ProcurementEngineerWorkstation from './pages/ProcurementEngineerWorkstation'
import PurchaseOrderDetail from './pages/PurchaseOrderDetail'
import MaterialTracking from './pages/MaterialTracking'
import SupplierManagement from './pages/SupplierManagement'
import CustomerList from './pages/CustomerList'
import OpportunityBoard from './pages/OpportunityBoard'
import LeadAssessment from './pages/LeadAssessment'
import QuotationList from './pages/QuotationList'
import ProductionManagerDashboard from './pages/ProductionManagerDashboard'
import ContractList from './pages/ContractList'
import ContractDetail from './pages/ContractDetail'
import PaymentManagement from './pages/PaymentManagement'
import InvoiceManagement from './pages/InvoiceManagement'
import SalesProjectTrack from './pages/SalesProjectTrack'
import BiddingDetail from './pages/BiddingDetail'
import PunchIn from './pages/PunchIn'

// Pre-sales Pages
import PresalesWorkstation from './pages/PresalesWorkstation'
import PresalesTasks from './pages/PresalesTasks'
import SolutionList from './pages/SolutionList'
import SolutionDetail from './pages/SolutionDetail'
import RequirementSurvey from './pages/RequirementSurvey'
import BiddingCenter from './pages/BiddingCenter'
import KnowledgeBase from './pages/KnowledgeBase'
import IssueManagement from './pages/IssueManagement'

// Placeholder Pages
const PlaceholderPage = ({ title }) => (
  <motion.div
    initial={{ opacity: 0, y: 20 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -20 }}
    className="flex flex-col items-center justify-center h-[60vh] text-center"
  >
    <div className="text-6xl mb-4">🚧</div>
    <h1 className="text-2xl font-semibold text-white mb-2">{title}</h1>
    <p className="text-slate-400">该功能正在开发中，敬请期待</p>
  </motion.div>
)

// Main Layout
function MainLayout({ children, onLogout }) {
  const [sidebarCollapsed, setSidebarCollapsed] = useState(false)
  const [user] = useState({ name: '管理员', email: 'admin@example.com' })

  return (
    <div className="min-h-screen bg-surface-0">
      {/* Sidebar */}
      <Sidebar
        collapsed={sidebarCollapsed}
        onToggle={() => setSidebarCollapsed(!sidebarCollapsed)}
        onLogout={onLogout}
      />

      {/* Header */}
      <Header
        sidebarCollapsed={sidebarCollapsed}
        user={user}
        onLogout={onLogout}
      />

      {/* Main Content */}
      <main
        className={cn(
          'pt-16 min-h-screen transition-all duration-300',
          sidebarCollapsed ? 'pl-[72px]' : 'pl-60'
        )}
      >
        <div className="p-6">
          <AnimatePresence mode="wait">{children}</AnimatePresence>
        </div>
      </main>
    </div>
  )
}

function App() {
  const [isAuthenticated, setIsAuthenticated] = useState(
    !!localStorage.getItem('token')
  )

  const handleLogout = () => {
    localStorage.removeItem('token')
    setIsAuthenticated(false)
  }

  const handleLoginSuccess = () => {
    setIsAuthenticated(true)
  }

  // Not authenticated - show login
  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  // Authenticated - show main app
  return (
    <Router>
      <MainLayout onLogout={handleLogout}>
        <Routes>
          {/* Dashboard */}
          <Route path="/" element={<Dashboard />} />
          <Route path="/operation" element={<OperationDashboard />} />

          {/* Project Management */}
          <Route path="/board" element={<ProjectBoard />} />
          <Route path="/projects" element={<ProjectList />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/schedule" element={<ScheduleBoard />} />
          <Route path="/tasks" element={<TaskCenter />} />
          <Route path="/assembly-tasks" element={<AssemblerTaskCenter />} />
          <Route path="/workstation" element={<EngineerWorkstation />} />
          
          {/* Production Management */}
          <Route path="/production-dashboard" element={<ProductionManagerDashboard />} />

          {/* Sales Routes */}
          <Route path="/sales-dashboard" element={<SalesWorkstation />} />
          <Route path="/business-support" element={<BusinessSupportWorkstation />} />
          <Route path="/customers" element={<CustomerList />} />
          <Route path="/opportunities" element={<OpportunityBoard />} />
          <Route path="/lead-assessment" element={<LeadAssessment />} />
          <Route path="/quotations" element={<QuotationList />} />
          <Route path="/contracts" element={<ContractList />} />
          <Route path="/contracts/:id" element={<ContractDetail />} />
          <Route path="/payments" element={<PaymentManagement />} />
          <Route path="/invoices" element={<InvoiceManagement />} />
          <Route path="/sales-projects" element={<SalesProjectTrack />} />
          <Route path="/bidding/:id" element={<BiddingDetail />} />

          {/* Pre-sales Routes */}
          <Route path="/presales-dashboard" element={<PresalesWorkstation />} />
          <Route path="/presales-tasks" element={<PresalesTasks />} />
          <Route path="/solutions" element={<SolutionList />} />
          <Route path="/solutions/:id" element={<SolutionDetail />} />
          <Route path="/requirement-survey" element={<RequirementSurvey />} />
          <Route path="/bidding" element={<BiddingCenter />} />
          <Route path="/knowledge-base" element={<KnowledgeBase />} />

          {/* Operations */}
          <Route path="/procurement-dashboard" element={<ProcurementEngineerWorkstation />} />
          <Route path="/purchases" element={<PurchaseOrders />} />
          <Route path="/purchases/:id" element={<PurchaseOrderDetail />} />
          <Route path="/materials" element={<MaterialTracking />} />
          <Route path="/material-analysis" element={<MaterialAnalysis />} />
          <Route path="/suppliers" element={<SupplierManagement />} />
          <Route path="/alerts" element={<PlaceholderPage title="预警中心" />} />

          {/* Quality & Acceptance */}
          <Route path="/acceptance" element={<Acceptance />} />
          <Route path="/approvals" element={<ApprovalCenter />} />
          <Route path="/issues" element={<IssueManagement />} />

          {/* Personal Center */}
          <Route path="/notifications" element={<NotificationCenter />} />
          <Route path="/timesheet" element={<Timesheet />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/punch-in" element={<PunchIn />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </MainLayout>
    </Router>
  )
}

export default App
