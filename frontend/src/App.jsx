import { useState, useEffect } from 'react'
import { BrowserRouter as Router, Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import { cn } from './lib/utils'
import ErrorBoundary from './components/common/ErrorBoundary'
import { ProcurementProtectedRoute, FinanceProtectedRoute, ProductionProtectedRoute, ProjectReviewProtectedRoute } from './components/common/ProtectedRoute'

// Layout Components
import { Sidebar } from './components/layout/Sidebar'
import { Header } from './components/layout/Header'

// Pages
import Login from './pages/Login'
import Dashboard from './pages/Dashboard'
import ProjectList from './pages/ProjectList'
import ProjectDetail from './pages/ProjectDetail'
import ProjectBoard from './pages/ProjectBoard'
import ProjectGantt from './pages/ProjectGantt'
import WBSTemplateManagement from './pages/WBSTemplateManagement'
import ProgressReport from './pages/ProgressReport'
import ProgressBoard from './pages/ProgressBoard'
import MilestoneRateReport from './pages/MilestoneRateReport'
import DelayReasonsReport from './pages/DelayReasonsReport'
import NotificationCenter from './pages/NotificationCenter'
import Timesheet from './pages/Timesheet'
import Settings from './pages/Settings'
import ScheduleBoard from './pages/ScheduleBoard'
import MaterialAnalysis from './pages/MaterialAnalysis'
import PurchaseOrders from './pages/PurchaseOrders'
import PurchaseRequestList from './pages/PurchaseRequestList'
import PurchaseRequestNew from './pages/PurchaseRequestNew'
import PurchaseRequestDetail from './pages/PurchaseRequestDetail'
import PurchaseOrderFromBOM from './pages/PurchaseOrderFromBOM'
import GoodsReceiptNew from './pages/GoodsReceiptNew'
import GoodsReceiptDetail from './pages/GoodsReceiptDetail'
import TaskCenter from './pages/TaskCenter'
import OperationDashboard from './pages/OperationDashboard'
import ApprovalCenter from './pages/ApprovalCenter'
import Acceptance from './pages/Acceptance'
import AssemblerTaskCenter from './pages/AssemblerTaskCenter'
import EngineerWorkstation from './pages/EngineerWorkstation'
import SalesWorkstation from './pages/SalesWorkstation'
import SalesDirectorWorkstation from './pages/SalesDirectorWorkstation'
import SalesManagerWorkstation from './pages/SalesManagerWorkstation'
import SalesReports from './pages/SalesReports'
import SalesTeam from './pages/SalesTeam'
import ContractApproval from './pages/ContractApproval'
import ChairmanWorkstation from './pages/ChairmanWorkstation'
import GeneralManagerWorkstation from './pages/GeneralManagerWorkstation'
import BusinessSupportWorkstation from './pages/BusinessSupportWorkstation'
import ProcurementEngineerWorkstation from './pages/ProcurementEngineerWorkstation'
import PurchaseOrderDetail from './pages/PurchaseOrderDetail'
import MaterialTracking from './pages/MaterialTracking'
import MaterialList from './pages/MaterialList'
import SupplierManagement from './pages/SupplierManagement'
import ShortageManagement from './pages/ShortageManagement'
import BOMManagement from './pages/BOMManagement'
import KitRateBoard from './pages/KitRateBoard'
import AssemblyKitBoard from './pages/AssemblyKitBoard'
import BomAssemblyAttrs from './pages/BomAssemblyAttrs'
import ArrivalManagement from './pages/ArrivalManagement'
import ProjectTaskList from './pages/ProjectTaskList'
import MaterialDemandSummary from './pages/MaterialDemandSummary'
import MachineManagement from './pages/MachineManagement'
import MilestoneManagement from './pages/MilestoneManagement'
import ExceptionManagement from './pages/ExceptionManagement'
import ShortageAlert from './pages/ShortageAlert'
import ECNManagement from './pages/ECNManagement'
import ECNTypeManagement from './pages/ECNTypeManagement'
import ECNOverdueAlerts from './pages/ECNOverdueAlerts'
import ECNStatistics from './pages/ECNStatistics'
import WorkOrderManagement from './pages/WorkOrderManagement'
import ProductionDashboard from './pages/ProductionDashboard'
import WorkshopTaskBoard from './pages/WorkshopTaskBoard'
import ProductionPlanList from './pages/ProductionPlanList'
import WorkReportList from './pages/WorkReportList'
import MaterialRequisitionList from './pages/MaterialRequisitionList'
import ProductionExceptionList from './pages/ProductionExceptionList'
import OutsourcingOrderList from './pages/OutsourcingOrderList'
import OutsourcingOrderDetail from './pages/OutsourcingOrderDetail'
import AcceptanceOrderList from './pages/AcceptanceOrderList'
import AcceptanceTemplateManagement from './pages/AcceptanceTemplateManagement'
import ShortageManagementBoard from './pages/ShortageManagementBoard'
import WorkloadBoard from './pages/WorkloadBoard'
import ShortageReportList from './pages/ShortageReportList'
import ArrivalTrackingList from './pages/ArrivalTrackingList'
import WorkOrderDetail from './pages/WorkOrderDetail'
import WorkshopManagement from './pages/WorkshopManagement'
import WorkerManagement from './pages/WorkerManagement'
import WorkerWorkstation from './pages/WorkerWorkstation'
import MaterialRequisitionDetail from './pages/MaterialRequisitionDetail'
import BudgetManagement from './pages/BudgetManagement'
import CostAnalysis from './pages/CostAnalysis'
import DispatchManagement from './pages/DispatchManagement'
import AcceptanceExecution from './pages/AcceptanceExecution'
import ShortageReportDetail from './pages/ShortageReportDetail'
import ShortageReportNew from './pages/ShortageReportNew'
import ArrivalDetail from './pages/ArrivalDetail'
import SubstitutionDetail from './pages/SubstitutionDetail'
import TransferDetail from './pages/TransferDetail'
import SubstitutionNew from './pages/SubstitutionNew'
import TransferNew from './pages/TransferNew'
import ArrivalNew from './pages/ArrivalNew'
import KitCheck from './pages/KitCheck'
// Sales Module Pages
import LeadManagement from './pages/LeadManagement'
import OpportunityManagement from './pages/OpportunityManagement'
import CustomerList from './pages/CustomerList'
import OpportunityBoard from './pages/OpportunityBoard'
import LeadAssessment from './pages/LeadAssessment'
import TechnicalAssessment from './pages/TechnicalAssessment'
import LeadRequirementDetail from './pages/LeadRequirementDetail'
import OpenItemsManagement from './pages/OpenItemsManagement'
import RequirementFreezeManagement from './pages/RequirementFreezeManagement'
import AIClarificationChat from './pages/AIClarificationChat'
import QuotationList from './pages/QuotationList'
import QuoteManagement from './pages/QuoteManagement'
import ContractManagement from './pages/ContractManagement'
import ReceivableManagement from './pages/ReceivableManagement'
import SalesStatistics from './pages/SalesStatistics'
import SalesTemplateCenter from './pages/SalesTemplateCenter'
import ProductionManagerDashboard from './pages/ProductionManagerDashboard'
import ProcurementManagerDashboard from './pages/ProcurementManagerDashboard'
import ManufacturingDirectorDashboard from './pages/ManufacturingDirectorDashboard'
import FinanceManagerDashboard from './pages/FinanceManagerDashboard'
import CostAccounting from './pages/CostAccounting'
import PaymentApproval from './pages/PaymentApproval'
import ProjectSettlement from './pages/ProjectSettlement'
import FinancialReports from './pages/FinancialReports'
import HRManagerDashboard from './pages/HRManagerDashboard'
import AdministrativeManagerWorkstation from './pages/AdministrativeManagerWorkstation'
import ContractList from './pages/ContractList'
import ContractDetail from './pages/ContractDetail'
import PaymentManagement from './pages/PaymentManagement'
import InvoiceManagement from './pages/InvoiceManagement'
import SalesProjectTrack from './pages/SalesProjectTrack'
import SalesFunnel from './pages/SalesFunnel'
import StrategyAnalysis from './pages/StrategyAnalysis'
import KeyDecisions from './pages/KeyDecisions'
import Shipments from './pages/Shipments'
import Documents from './pages/Documents'
import BiddingDetail from './pages/BiddingDetail'
import PunchIn from './pages/PunchIn'

// Pre-sales Pages
import PresalesWorkstation from './pages/PresalesWorkstation'
import PresalesManagerWorkstation from './pages/PresalesManagerWorkstation'
import PresalesTasks from './pages/PresalesTasks'
import SolutionList from './pages/SolutionList'
import SolutionDetail from './pages/SolutionDetail'
import RequirementSurvey from './pages/RequirementSurvey'
import BiddingCenter from './pages/BiddingCenter'
import KnowledgeBase from './pages/KnowledgeBase'
import IssueManagement from './pages/IssueManagement'
import TechnicalSpecManagement from './pages/TechnicalSpecManagement'
// R&D Project Management Pages
import RdProjectList from './pages/RdProjectList'
import RdProjectDetail from './pages/RdProjectDetail'
import RdCostEntry from './pages/RdCostEntry'
import RdCostSummary from './pages/RdCostSummary'
import RdCostReports from './pages/RdCostReports'
import RdProjectWorklogs from './pages/RdProjectWorklogs'
import RdProjectDocuments from './pages/RdProjectDocuments'
import SpecMatchCheck from './pages/SpecMatchCheck'
// PMO Pages
import PMODashboard from './pages/PMODashboard'
import InitiationManagement from './pages/InitiationManagement'
import ProjectPhaseManagement from './pages/ProjectPhaseManagement'
import RiskManagement from './pages/RiskManagement'
import ProjectClosureManagement from './pages/ProjectClosureManagement'
import ProjectReviewList from './pages/ProjectReviewList'
import ProjectReviewDetail from './pages/ProjectReviewDetail'
import LessonsLearnedLibrary from './pages/LessonsLearnedLibrary'
import BestPracticeRecommendations from './pages/BestPracticeRecommendations'
import TechnicalReviewList from './pages/TechnicalReviewList'
import TechnicalReviewDetail from './pages/TechnicalReviewDetail'
import ResourceOverview from './pages/ResourceOverview'
import MeetingManagement from './pages/MeetingManagement'
import CustomerServiceDashboard from './pages/CustomerServiceDashboard'
import ServiceTicketManagement from './pages/ServiceTicketManagement'
import ServiceRecord from './pages/ServiceRecord'
import CustomerCommunication from './pages/CustomerCommunication'
import CustomerSatisfaction from './pages/CustomerSatisfaction'
import ServiceAnalytics from './pages/ServiceAnalytics'
import ServiceKnowledgeBase from './pages/ServiceKnowledgeBase'
import AdminDashboard from './pages/AdminDashboard'
import SchedulerMonitoringDashboard from './pages/SchedulerMonitoringDashboard'
import UserManagement from './pages/UserManagement'
import RiskWall from './pages/RiskWall'
import WeeklyReport from './pages/WeeklyReport'
import RoleManagement from './pages/RoleManagement'
import ProjectRoleTypeManagement from './pages/ProjectRoleTypeManagement'
import CustomerManagement from './pages/CustomerManagement'
import SupplierManagementData from './pages/SupplierManagementData'
import DepartmentManagement from './pages/DepartmentManagement'
import AlertCenter from './pages/AlertCenter'
import AlertRuleConfig from './pages/AlertRuleConfig'
import AlertDetail from './pages/AlertDetail'
import AlertStatistics from './pages/AlertStatistics'
import AlertSubscription from './pages/AlertSubscription'

// Mobile Pages
import MobileWorkerTaskList from './pages/mobile/MobileWorkerTaskList'
import MobileScanStart from './pages/mobile/MobileScanStart'
import MobileProgressReport from './pages/mobile/MobileProgressReport'
import MobileCompleteReport from './pages/mobile/MobileCompleteReport'
import MobileExceptionReport from './pages/mobile/MobileExceptionReport'
import MobileMaterialRequisition from './pages/mobile/MobileMaterialRequisition'
import MobileScanShortage from './pages/mobile/MobileScanShortage'
import MobileShortageReport from './pages/mobile/MobileShortageReport'
import MobileMyShortageReports from './pages/mobile/MobileMyShortageReports'

// Performance Management Pages
import PerformanceManagement from './pages/PerformanceManagement'
import QualificationManagement from './pages/QualificationManagement'
import QualificationLevelForm from './pages/QualificationLevelForm'
import CompetencyModelForm from './pages/CompetencyModelForm'
import EmployeeQualificationForm from './pages/EmployeeQualificationForm'
import QualificationAssessmentList from './pages/QualificationAssessmentList'
import PerformanceRanking from './pages/PerformanceRanking'
import PerformanceIndicators from './pages/PerformanceIndicators'
import PerformanceResults from './pages/PerformanceResults'
import MonthlySummary from './pages/MonthlySummary'
import MyPerformance from './pages/MyPerformance'
import MyBonus from './pages/MyBonus'
import EvaluationTaskList from './pages/EvaluationTaskList'
import EvaluationScoring from './pages/EvaluationScoring'
import EvaluationWeightConfig from './pages/EvaluationWeightConfig'

// AI Staff Matching Pages
import TagManagement from './pages/TagManagement'
import EmployeeProfileList from './pages/EmployeeProfileList'
import EmployeeProfileDetail from './pages/EmployeeProfileDetail'
import ProjectStaffingNeed from './pages/ProjectStaffingNeed'
import AIStaffMatching from './pages/AIStaffMatching'

// Role-based dashboard redirect mapping
const roleDashboardMap = {
  // 管理层
  chairman: '/chairman-dashboard',
  gm: '/gm-dashboard',
  admin: '/admin-dashboard',
  super_admin: '/admin-dashboard',

  // 销售/支持
  sales_director: '/sales-director-dashboard',
  sales_manager: '/sales-manager-dashboard',
  sales: '/sales-dashboard',
  business_support: '/business-support',
  presales: '/presales-dashboard',
  presales_manager: '/presales-manager-dashboard',

  // 项目管理 - 新增
  project_dept_manager: '/pmo/dashboard',
  pm: '/pmo/dashboard',
  pmc: '/pmo/dashboard',

  // 工程技术中心
  tech_dev_manager: '/workstation',
  rd_engineer: '/workstation',
  me_dept_manager: '/workstation',
  te_dept_manager: '/workstation',
  ee_dept_manager: '/workstation',
  me_engineer: '/workstation',
  te_engineer: '/workstation',
  ee_engineer: '/workstation',
  sw_engineer: '/workstation',

  // 采购部
  procurement_manager: '/procurement-manager-dashboard',
  procurement_engineer: '/procurement-dashboard',

  // 制造中心
  manufacturing_director: '/manufacturing-director-dashboard',
  production_manager: '/production-dashboard',
  assembler: '/assembly-tasks',
  assembler_mechanic: '/assembly-tasks',
  assembler_electrician: '/assembly-tasks',

  // 客户服务
  customer_service_engineer: '/customer-service-dashboard',
  customer_service_manager: '/customer-service-dashboard',

  // 后台支持
  finance_manager: '/finance-manager-dashboard',
  hr_manager: '/hr-manager-dashboard',
  administrative_manager: '/administrative-dashboard',
}

// Protected Route with role-based redirect
function ProtectedRoute({ children }) {
  const location = useLocation()
  
  // Check if user should be redirected to role-specific dashboard
  const userStr = localStorage.getItem('user')
  
  // Only redirect if we're on the root path
  if (location.pathname === '/' && userStr) {
    let user = null
    let role = null
    
    try {
      user = JSON.parse(userStr)
      role = user.role
    } catch (e) {
      // Ignore parse errors, but clear invalid user data
      console.warn('Invalid user data in localStorage:', e)
      localStorage.removeItem('user')
      return children
    }
    
    if (role) {
      const dashboardPath = roleDashboardMap[role]
      if (dashboardPath) {
        // 使用 replace 确保不会在历史记录中留下 '/' 路径
        return <Navigate to={dashboardPath} replace />
      }
    }
  }
  
  return children
}

// Route protection components are now imported from ProtectedRoute.jsx

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
  // Get user from localStorage
  const [user, setUser] = useState(() => {
    try {
      const userStr = localStorage.getItem('user')
      if (userStr) {
        return JSON.parse(userStr)
      }
    } catch (e) {
      console.warn('Failed to parse user from localStorage:', e)
    }
    return null
  })

  // Update user when localStorage changes
  useEffect(() => {
    const handleStorageChange = () => {
      try {
        const userStr = localStorage.getItem('user')
        if (userStr) {
          setUser(JSON.parse(userStr))
        } else {
          setUser(null)
        }
      } catch (e) {
        console.warn('Failed to parse user from localStorage:', e)
        setUser(null)
      }
    }

    // Listen for storage events (from other tabs)
    window.addEventListener('storage', handleStorageChange)
    
    // Also check on mount
    handleStorageChange()

    return () => {
      window.removeEventListener('storage', handleStorageChange)
    }
  }, [])

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

  // 监听 localStorage 中 token 的变化，同步认证状态
  useEffect(() => {
    const checkAuth = () => {
      const token = localStorage.getItem('token')
      setIsAuthenticated(!!token)
    }

    // 初始检查
    checkAuth()

    // 监听 storage 事件（跨标签页同步）
    window.addEventListener('storage', checkAuth)

    // 定期检查（防止其他代码直接修改 localStorage）
    const interval = setInterval(checkAuth, 1000)

    return () => {
      window.removeEventListener('storage', checkAuth)
      clearInterval(interval)
    }
  }, [])

  const handleLogout = () => {
    // 清理所有登录相关的数据
    localStorage.removeItem('token')
    localStorage.removeItem('user')
    setIsAuthenticated(false)
    // 跳转到登录页
    window.location.href = '/'
  }

  const handleLoginSuccess = () => {
    setIsAuthenticated(true)
    // 登录成功后，跳转逻辑由 ProtectedRoute 处理
    // 不需要在这里手动跳转，避免页面重新加载导致的闪退
    // ProtectedRoute 会在根路径 '/' 时自动跳转到对应的 dashboard
  }

  // Not authenticated - show login
  if (!isAuthenticated) {
    return <Login onLoginSuccess={handleLoginSuccess} />
  }

  // Authenticated - show main app
  return (
    <ErrorBoundary>
      <Router>
        <MainLayout onLogout={handleLogout}>
        <Routes>
          {/* Dashboard */}
          <Route path="/" element={
            <ProtectedRoute>
              <Dashboard />
            </ProtectedRoute>
          } />
          <Route path="/chairman-dashboard" element={
            <ProtectedRoute>
              <ChairmanWorkstation />
            </ProtectedRoute>
          } />
          <Route path="/gm-dashboard" element={
            <ProtectedRoute>
              <GeneralManagerWorkstation />
            </ProtectedRoute>
          } />
          <Route path="/admin-dashboard" element={<AdminDashboard />} />
          <Route path="/operation" element={<OperationDashboard />} />
          <Route path="/strategy-analysis" element={<StrategyAnalysis />} />
          <Route path="/key-decisions" element={<KeyDecisions />} />
          <Route path="/shipments" element={<Shipments />} />
          <Route path="/documents" element={<Documents />} />

          {/* Project Management */}
          <Route path="/board" element={<ProjectBoard />} />
          <Route path="/projects" element={<ProjectList />} />
          <Route path="/projects/:id" element={<ProjectDetail />} />
          <Route path="/projects/:id/gantt" element={<ProjectGantt />} />
          <Route path="/projects/:id/tasks" element={<ProjectTaskList />} />
          <Route path="/projects/:id/machines" element={<MachineManagement />} />
          <Route path="/projects/:id/milestones" element={<MilestoneManagement />} />
          <Route path="/projects/:id/progress-report" element={<ProgressReport />} />
          <Route path="/projects/:id/progress-board" element={<ProgressBoard />} />
          <Route path="/projects/:id/milestone-rate" element={<MilestoneRateReport />} />
          <Route path="/projects/:id/delay-reasons" element={<DelayReasonsReport />} />
          <Route path="/reports/milestone-rate" element={<MilestoneRateReport />} />
          <Route path="/reports/delay-reasons" element={<DelayReasonsReport />} />
          <Route path="/wbs-templates" element={<WBSTemplateManagement />} />
          <Route path="/schedule" element={<ScheduleBoard />} />
          <Route path="/tasks" element={<TaskCenter />} />
          <Route path="/assembly-tasks" element={<AssemblerTaskCenter />} />
          <Route path="/workstation" element={<EngineerWorkstation />} />
          
          {/* Production Management */}
          <Route path="/production-dashboard" element={<ProductionDashboard />} />
          <Route path="/production-manager-dashboard" element={<ProductionManagerDashboard />} />
          <Route path="/manufacturing-director-dashboard" element={<ManufacturingDirectorDashboard />} />
          <Route path="/work-orders" element={<WorkOrderManagement />} />
          <Route path="/work-orders/:id" element={<WorkOrderDetail />} />
          <Route path="/dispatch-management" element={<DispatchManagement />} />
          <Route path="/production-plans" element={<ProductionPlanList />} />
          <Route path="/work-reports" element={<WorkReportList />} />
          <Route path="/material-requisitions" element={<MaterialRequisitionList />} />
          <Route path="/material-requisitions/:id" element={<MaterialRequisitionDetail />} />
          <Route path="/production-exceptions" element={<ProductionExceptionList />} />
          <Route path="/workshops" element={<WorkshopManagement />} />
          <Route path="/workers" element={<WorkerManagement />} />
          <Route path="/worker-workstation" element={<WorkerWorkstation />} />
          <Route path="/outsourcing-orders" element={<OutsourcingOrderList />} />
          <Route path="/outsourcing-orders/:id" element={<OutsourcingOrderDetail />} />
          <Route path="/acceptance-orders" element={<AcceptanceOrderList />} />
          <Route path="/acceptance-orders/:id/execute" element={<AcceptanceExecution />} />
          <Route path="/acceptance-templates" element={<AcceptanceTemplateManagement />} />
          <Route path="/shortage-management-board" element={<ShortageManagementBoard />} />
          <Route path="/shortage-reports" element={<ShortageReportList />} />
          <Route path="/arrival-tracking" element={<ArrivalTrackingList />} />
          <Route path="/workload-board" element={<WorkloadBoard />} />
          <Route path="/workshops/:id/task-board" element={<WorkshopTaskBoard />} />
          
          {/* Procurement Management */}
          <Route path="/procurement-manager-dashboard" element={<ProcurementManagerDashboard />} />

          {/* Finance Management */}
          <Route path="/finance-manager-dashboard" element={
            <FinanceProtectedRoute>
              <FinanceManagerDashboard />
            </FinanceProtectedRoute>
          } />
          <Route path="/costs" element={<CostAccounting />} />
          <Route path="/payment-approval" element={<PaymentApproval />} />
          <Route path="/settlement" element={<ProjectSettlement />} />
          <Route path="/financial-reports" element={<FinancialReports />} />

          {/* HR Management */}
          <Route path="/hr-manager-dashboard" element={<HRManagerDashboard />} />

          {/* Administrative Management */}
          <Route path="/administrative-dashboard" element={<AdministrativeManagerWorkstation />} />

          {/* Performance Management */}
          <Route path="/performance" element={<PerformanceManagement />} />
          <Route path="/performance/ranking" element={<PerformanceRanking />} />
          <Route path="/performance/indicators" element={<PerformanceIndicators />} />
          <Route path="/performance/results" element={<PerformanceResults />} />
          <Route path="/performance/results/:employeeId" element={<PerformanceResults />} />

          {/* Personal Performance Pages */}
          <Route path="/personal/monthly-summary" element={<MonthlySummary />} />
          <Route path="/personal/my-performance" element={<MyPerformance />} />
          <Route path="/personal/my-bonus" element={<MyBonus />} />

          {/* Evaluation Pages */}
          <Route path="/evaluation-tasks" element={<EvaluationTaskList />} />
          <Route path="/evaluation/:taskId" element={<EvaluationScoring />} />
          <Route path="/evaluation-weight-config" element={<EvaluationWeightConfig />} />

          {/* Qualification Management */}
          <Route path="/qualifications" element={<QualificationManagement />} />
          <Route path="/qualifications/levels/new" element={<QualificationLevelForm />} />
          <Route path="/qualifications/levels/:id" element={<QualificationLevelForm />} />
          <Route path="/qualifications/levels/:id/edit" element={<QualificationLevelForm />} />
          <Route path="/qualifications/models/new" element={<CompetencyModelForm />} />
          <Route path="/qualifications/models/:id" element={<CompetencyModelForm />} />
          <Route path="/qualifications/models/:id/edit" element={<CompetencyModelForm />} />
          <Route path="/qualifications/employees/certify" element={<EmployeeQualificationForm />} />
          <Route path="/qualifications/employees/:employeeId" element={<EmployeeQualificationForm />} />
          <Route path="/qualifications/employees/:employeeId/view" element={<EmployeeQualificationForm />} />
          <Route path="/qualifications/employees/:employeeId/promote" element={<EmployeeQualificationForm />} />
          <Route path="/qualifications/assessments" element={<QualificationAssessmentList />} />

          {/* Sales Routes */}
          <Route path="/sales-dashboard" element={<SalesWorkstation />} />
          <Route path="/sales-director-dashboard" element={<SalesDirectorWorkstation />} />
          <Route path="/sales-manager-dashboard" element={<SalesManagerWorkstation />} />
          <Route path="/sales-reports" element={<SalesReports />} />
          <Route path="/sales-team" element={<SalesTeam />} />
          <Route path="/contract-approval" element={<ContractApproval />} />
          <Route path="/business-support" element={<BusinessSupportWorkstation />} />
          <Route path="/customers" element={<CustomerList />} />
          <Route path="/opportunities" element={<OpportunityBoard />} />
          <Route path="/lead-assessment" element={<LeadAssessment />} />
          <Route path="/quotations" element={<QuotationList />} />
          <Route path="/contracts" element={<ContractList />} />
          <Route path="/contracts/:id" element={<ContractDetail />} />
          <Route path="/payments" element={
            <FinanceProtectedRoute>
              <PaymentManagement />
            </FinanceProtectedRoute>
          } />
          <Route path="/invoices" element={
            <FinanceProtectedRoute>
              <InvoiceManagement />
            </FinanceProtectedRoute>
          } />
          <Route path="/sales-projects" element={<SalesProjectTrack />} />
          <Route path="/sales-funnel" element={<SalesFunnel />} />
          <Route path="/bidding/:id" element={<BiddingDetail />} />
          {/* New Sales Module Routes */}
          <Route path="/sales/leads" element={<LeadManagement />} />
          <Route path="/sales/opportunities" element={<OpportunityManagement />} />
          <Route path="/sales/assessments/:sourceType/:sourceId" element={<TechnicalAssessment />} />
          <Route path="/sales/leads/:leadId/requirement" element={<LeadRequirementDetail />} />
          <Route path="/sales/:sourceType/:sourceId/open-items" element={<OpenItemsManagement />} />
          <Route path="/sales/:sourceType/:sourceId/requirement-freezes" element={<RequirementFreezeManagement />} />
          <Route path="/sales/:sourceType/:sourceId/ai-clarifications" element={<AIClarificationChat />} />
          <Route path="/sales/quotes" element={<QuoteManagement />} />
          <Route path="/sales/contracts" element={<ContractManagement />} />
          <Route path="/sales/receivables" element={<ReceivableManagement />} />
          <Route path="/sales/statistics" element={<SalesStatistics />} />
          <Route path="/sales/templates" element={<SalesTemplateCenter />} />

          {/* Pre-sales Routes */}
          <Route path="/presales-dashboard" element={<PresalesWorkstation />} />
          <Route path="/presales-manager-dashboard" element={<PresalesManagerWorkstation />} />
          <Route path="/presales-tasks" element={<PresalesTasks />} />
          <Route path="/solutions" element={<SolutionList />} />
          <Route path="/solutions/:id" element={<SolutionDetail />} />
          <Route path="/requirement-survey" element={<RequirementSurvey />} />
          <Route path="/bidding" element={<BiddingCenter />} />
          <Route path="/knowledge-base" element={<KnowledgeBase />} />

          {/* Operations */}
          <Route path="/procurement-dashboard" element={<ProcurementEngineerWorkstation />} />
          <Route path="/purchases" element={
            <ProcurementProtectedRoute>
              <PurchaseOrders />
            </ProcurementProtectedRoute>
          } />
          <Route path="/purchases/:id" element={
            <ProcurementProtectedRoute>
              <PurchaseOrderDetail />
            </ProcurementProtectedRoute>
          } />
          <Route path="/purchase-requests" element={
            <ProcurementProtectedRoute>
              <PurchaseRequestList />
            </ProcurementProtectedRoute>
          } />
          <Route path="/purchase-requests/new" element={
            <ProcurementProtectedRoute>
              <PurchaseRequestNew />
            </ProcurementProtectedRoute>
          } />
          <Route path="/purchase-requests/:id" element={
            <ProcurementProtectedRoute>
              <PurchaseRequestDetail />
            </ProcurementProtectedRoute>
          } />
          <Route path="/purchase-requests/:id/edit" element={
            <ProcurementProtectedRoute>
              <PurchaseRequestNew />
            </ProcurementProtectedRoute>
          } />
          <Route path="/purchases/from-bom" element={
            <ProcurementProtectedRoute>
              <PurchaseOrderFromBOM />
            </ProcurementProtectedRoute>
          } />
          <Route path="/purchases/receipts" element={
            <ProcurementProtectedRoute>
              <ArrivalManagement />
            </ProcurementProtectedRoute>
          } />
          <Route path="/purchases/receipts/new" element={
            <ProcurementProtectedRoute>
              <GoodsReceiptNew />
            </ProcurementProtectedRoute>
          } />
          <Route path="/purchases/receipts/:id" element={
            <ProcurementProtectedRoute>
              <GoodsReceiptDetail />
            </ProcurementProtectedRoute>
          } />
          <Route path="/materials" element={
            <ProcurementProtectedRoute>
              <MaterialList />
            </ProcurementProtectedRoute>
          } />
          <Route path="/material-tracking" element={
            <ProcurementProtectedRoute>
              <MaterialTracking />
            </ProcurementProtectedRoute>
          } />
          <Route path="/material-analysis" element={
            <ProcurementProtectedRoute>
              <MaterialAnalysis />
            </ProcurementProtectedRoute>
          } />
          <Route path="/budgets" element={
            <ProcurementProtectedRoute>
              <BudgetManagement />
            </ProcurementProtectedRoute>
          } />
          <Route path="/cost-analysis" element={
            <ProcurementProtectedRoute>
              <CostAnalysis />
            </ProcurementProtectedRoute>
          } />
          <Route path="/material-demands" element={
            <ProcurementProtectedRoute>
              <MaterialDemandSummary />
            </ProcurementProtectedRoute>
          } />
          <Route path="/bom" element={
            <ProcurementProtectedRoute>
              <BOMManagement />
            </ProcurementProtectedRoute>
          } />
          <Route path="/kit-rate" element={
            <ProcurementProtectedRoute>
              <KitRateBoard />
            </ProcurementProtectedRoute>
          } />
          <Route path="/assembly-kit" element={
            <ProductionProtectedRoute>
              <AssemblyKitBoard />
            </ProductionProtectedRoute>
          } />
          <Route path="/bom-assembly-attrs" element={
            <ProcurementProtectedRoute>
              <BomAssemblyAttrs />
            </ProcurementProtectedRoute>
          } />
          <Route path="/arrivals" element={
            <ProcurementProtectedRoute>
              <ArrivalManagement />
            </ProcurementProtectedRoute>
          } />
          <Route path="/suppliers" element={<SupplierManagement />} />
          <Route path="/shortage" element={
            <ProcurementProtectedRoute>
              <ShortageManagement />
            </ProcurementProtectedRoute>
          } />
          <Route path="/shortage/reports/new" element={
            <ProcurementProtectedRoute>
              <ShortageReportNew />
            </ProcurementProtectedRoute>
          } />
          <Route path="/shortage/reports/:id" element={
            <ProcurementProtectedRoute>
              <ShortageReportDetail />
            </ProcurementProtectedRoute>
          } />
          <Route path="/shortage/arrivals/:id" element={
            <ProcurementProtectedRoute>
              <ArrivalDetail />
            </ProcurementProtectedRoute>
          } />
          <Route path="/shortage/substitutions/:id" element={
            <ProcurementProtectedRoute>
              <SubstitutionDetail />
            </ProcurementProtectedRoute>
          } />
          <Route path="/shortage/transfers/:id" element={
            <ProcurementProtectedRoute>
              <TransferDetail />
            </ProcurementProtectedRoute>
          } />
          <Route path="/shortage/substitutions/new" element={
            <ProcurementProtectedRoute>
              <SubstitutionNew />
            </ProcurementProtectedRoute>
          } />
          <Route path="/shortage/transfers/new" element={
            <ProcurementProtectedRoute>
              <TransferNew />
            </ProcurementProtectedRoute>
          } />
          <Route path="/shortage/arrivals/new" element={
            <ProcurementProtectedRoute>
              <ArrivalNew />
            </ProcurementProtectedRoute>
          } />
          <Route path="/kit-check" element={
            <ProcurementProtectedRoute>
              <KitCheck />
            </ProcurementProtectedRoute>
          } />
          <Route path="/alerts" element={<AlertCenter />} />
          <Route path="/exceptions" element={<ExceptionManagement />} />
          <Route path="/ecns" element={<ECNManagement />} />
          <Route path="/ecn-types" element={<ECNTypeManagement />} />
          <Route path="/ecn-overdue-alerts" element={<ECNOverdueAlerts />} />
          <Route path="/ecn-statistics" element={<ECNStatistics />} />
          <Route path="/alerts/:id" element={<AlertDetail />} />
          <Route path="/alert-rules" element={<AlertRuleConfig />} />
          <Route path="/alert-statistics" element={<AlertStatistics />} />
          <Route path="/alert-subscription" element={<AlertSubscription />} />

          {/* Quality & Acceptance */}
          <Route path="/acceptance" element={<Acceptance />} />
          <Route path="/approvals" element={<ApprovalCenter />} />
          <Route path="/issues" element={<IssueManagement />} />
          
          {/* Technical Spec Management */}
          <Route path="/technical-spec" element={<TechnicalSpecManagement />} />
          
          {/* Technical Review Management */}
          <Route path="/technical-reviews" element={<TechnicalReviewList />} />
          <Route path="/technical-reviews/new" element={<TechnicalReviewDetail />} />
          <Route path="/technical-reviews/:reviewId" element={<TechnicalReviewDetail />} />
          <Route path="/technical-reviews/:reviewId/edit" element={<TechnicalReviewDetail />} />
          <Route path="/spec-match-check" element={<SpecMatchCheck />} />

          {/* Customer Service */}
          <Route path="/customer-service-dashboard" element={<CustomerServiceDashboard />} />
          <Route path="/service-tickets" element={<ServiceTicketManagement />} />
          <Route path="/service-records" element={<ServiceRecord />} />
          <Route path="/customer-communications" element={<CustomerCommunication />} />
          <Route path="/customer-satisfaction" element={<CustomerSatisfaction />} />
          <Route path="/service-analytics" element={<ServiceAnalytics />} />
          <Route path="/service-knowledge-base" element={<ServiceKnowledgeBase />} />

          {/* PMO Management */}
          <Route path="/pmo/dashboard" element={<PMODashboard />} />
          <Route path="/pmo/initiations" element={<InitiationManagement />} />
          <Route path="/pmo/initiations/:id" element={<InitiationManagement />} />
          <Route path="/pmo/phases" element={<ProjectPhaseManagement />} />
          <Route path="/pmo/phases/:projectId" element={<ProjectPhaseManagement />} />
          <Route path="/pmo/risks" element={<RiskManagement />} />
          <Route path="/pmo/risks/:projectId" element={<RiskManagement />} />
          <Route path="/pmo/closure" element={<ProjectClosureManagement />} />
          <Route path="/pmo/closure/:projectId" element={<ProjectClosureManagement />} />
          <Route path="/projects/reviews" element={
            <ProjectReviewProtectedRoute>
              <ProjectReviewList />
            </ProjectReviewProtectedRoute>
          } />
          <Route path="/projects/reviews/:reviewId" element={
            <ProjectReviewProtectedRoute>
              <ProjectReviewDetail />
            </ProjectReviewProtectedRoute>
          } />
          <Route path="/projects/reviews/:reviewId/edit" element={
            <ProjectReviewProtectedRoute>
              <ProjectReviewDetail />
            </ProjectReviewProtectedRoute>
          } />
          <Route path="/projects/reviews/new" element={
            <ProjectReviewProtectedRoute>
              <ProjectReviewDetail />
            </ProjectReviewProtectedRoute>
          } />
          <Route path="/projects/lessons-learned" element={
            <ProjectReviewProtectedRoute>
              <LessonsLearnedLibrary />
            </ProjectReviewProtectedRoute>
          } />
          <Route path="/projects/best-practices/recommend" element={
            <ProjectReviewProtectedRoute>
              <BestPracticeRecommendations />
            </ProjectReviewProtectedRoute>
          } />
          <Route path="/projects/:projectId/best-practices/recommend" element={
            <ProjectReviewProtectedRoute>
              <BestPracticeRecommendations />
            </ProjectReviewProtectedRoute>
          } />
          <Route path="/pmo/resource-overview" element={<ResourceOverview />} />
          <Route path="/pmo/meetings" element={<MeetingManagement />} />
          <Route path="/pmo/risk-wall" element={<RiskWall />} />
          <Route path="/pmo/weekly-report" element={<WeeklyReport />} />

          {/* R&D Project Management */}
          <Route path="/rd-projects" element={<RdProjectList />} />
          <Route path="/rd-projects/:id" element={<RdProjectDetail />} />
          <Route path="/rd-projects/:id/worklogs" element={<RdProjectWorklogs />} />
          <Route path="/rd-projects/:id/documents" element={<RdProjectDocuments />} />
          <Route path="/rd-projects/:id/cost-entry" element={<RdCostEntry />} />
          <Route path="/rd-projects/:id/cost-summary" element={<RdCostSummary />} />
          <Route path="/rd-projects/:id/reports" element={<RdCostReports />} />
          <Route path="/rd-cost-entry" element={<RdCostEntry />} />
          <Route path="/rd-cost-summary" element={<RdCostSummary />} />
          <Route path="/rd-cost-reports" element={<RdCostReports />} />

          {/* AI Staff Matching */}
          <Route path="/staff-matching/tags" element={<TagManagement />} />
          <Route path="/staff-matching/profiles" element={<EmployeeProfileList />} />
          <Route path="/staff-matching/profiles/:id" element={<EmployeeProfileDetail />} />
          <Route path="/staff-matching/staffing-needs" element={<ProjectStaffingNeed />} />
          <Route path="/staff-matching/matching" element={<AIStaffMatching />} />

          {/* Personal Center */}
          <Route path="/notifications" element={<NotificationCenter />} />
          <Route path="/timesheet" element={<Timesheet />} />
          <Route path="/settings" element={<Settings />} />
          <Route path="/punch-in" element={<PunchIn />} />

          {/* System Management */}
          <Route path="/user-management" element={<UserManagement />} />
          <Route path="/role-management" element={<RoleManagement />} />
          <Route path="/project-role-types" element={<ProjectRoleTypeManagement />} />
          <Route path="/scheduler-monitoring" element={<SchedulerMonitoringDashboard />} />
          
          {/* Master Data Management */}
          <Route path="/customer-management" element={<CustomerManagement />} />
          <Route path="/supplier-management-data" element={<SupplierManagementData />} />
          <Route path="/department-management" element={<DepartmentManagement />} />

          {/* Mobile Pages - 移动端页面 */}
          <Route path="/mobile/tasks" element={<MobileWorkerTaskList />} />
          <Route path="/mobile/scan-start" element={<MobileScanStart />} />
          <Route path="/mobile/progress-report" element={<MobileProgressReport />} />
          <Route path="/mobile/complete-report" element={<MobileCompleteReport />} />
          <Route path="/mobile/exception-report" element={<MobileExceptionReport />} />
          <Route path="/mobile/material-requisition" element={<MobileMaterialRequisition />} />
          <Route path="/mobile/scan-shortage" element={<MobileScanShortage />} />
          <Route path="/mobile/shortage-report" element={<MobileShortageReport />} />
          <Route path="/mobile/my-shortage-reports" element={<MobileMyShortageReports />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
        </MainLayout>
      </Router>
    </ErrorBoundary>
  )
}

export default App
