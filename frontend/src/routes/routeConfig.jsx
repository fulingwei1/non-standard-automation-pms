import { Routes, Route, Navigate } from "react-router-dom";
import { AppProtectedRoute } from "../components/common/AppProtectedRoute";
import {
  ProcurementProtectedRoute,
  FinanceProtectedRoute,
  ProductionProtectedRoute,
  ProjectReviewProtectedRoute,
} from "../components/common/ProtectedRoute";

// 导入所有页面组件（保持原有导入）
import Dashboard from "../pages/Dashboard";
import ProjectList from "../pages/ProjectList";
import ProjectDetail from "../pages/ProjectDetail";
import ProjectWorkspace from "../pages/ProjectWorkspace";
import ProjectContributionReport from "../pages/ProjectContributionReport";
import ProjectBoard from "../pages/ProjectBoard";
import ProjectGantt from "../pages/ProjectGantt";
import WBSTemplateManagement from "../pages/WBSTemplateManagement";
import ProgressReport from "../pages/ProgressReport";
import ProgressBoard from "../pages/ProgressBoard";
import ProgressForecast from "../pages/ProgressForecast";
import DependencyCheck from "../pages/DependencyCheck";
import MilestoneRateReport from "../pages/MilestoneRateReport";
import DelayReasonsReport from "../pages/DelayReasonsReport";
import NotificationCenter from "../pages/NotificationCenter";
import Timesheet from "../pages/Timesheet";
import TimesheetDashboard from "../pages/TimesheetDashboard";
import TimesheetBatchOperations from "../pages/TimesheetBatchOperations";
import Settings from "../pages/Settings";
import ScheduleBoard from "../pages/ScheduleBoard";
import MaterialReadiness from "../pages/MaterialReadiness";
import ProcurementAnalysis from "../pages/ProcurementAnalysis";
import InventoryAnalysis from "../pages/InventoryAnalysis";
import PurchaseOrders from "../pages/PurchaseOrders";
import PurchaseRequestList from "../pages/PurchaseRequestList";
import PurchaseRequestNew from "../pages/PurchaseRequestNew";
import PurchaseRequestDetail from "../pages/PurchaseRequestDetail";
import PurchaseOrderFromBOM from "../pages/PurchaseOrderFromBOM";
import GoodsReceiptNew from "../pages/GoodsReceiptNew";
import GoodsReceiptDetail from "../pages/GoodsReceiptDetail";
import TaskCenter from "../pages/TaskCenter";
import OperationDashboard from "../pages/OperationDashboard";
import ApprovalCenter from "../pages/ApprovalCenter";
import Acceptance from "../pages/Acceptance";
import AssemblerTaskCenter from "../pages/AssemblerTaskCenter";
import EngineerWorkstation from "../pages/EngineerWorkstation";
import SalesWorkstation from "../pages/SalesWorkstation";
import SalesDirectorWorkstation from "../pages/SalesDirectorWorkstation";
import SalesManagerWorkstation from "../pages/SalesManagerWorkstation";
import SalesReports from "../pages/SalesReports";
import SalesTeam from "../pages/SalesTeam";
import SalesTarget from "../pages/SalesTarget";
import CpqConfigurator from "../pages/CpqConfigurator";
import ContractApproval from "../pages/ContractApproval";
import ChairmanWorkstation from "../pages/ChairmanWorkstation";
import GeneralManagerWorkstation from "../pages/GeneralManagerWorkstation";
import BusinessSupportWorkstation from "../pages/BusinessSupportWorkstation";
import ProcurementEngineerWorkstation from "../pages/ProcurementEngineerWorkstation";
import PurchaseOrderDetail from "../pages/PurchaseOrderDetail";
import MaterialTracking from "../pages/MaterialTracking";
import MaterialList from "../pages/MaterialList";
import SupplierManagement from "../pages/SupplierManagement";
import ShortageManagement from "../pages/ShortageManagement";
import BOMManagement from "../pages/BOMManagement";
import KitRateBoard from "../pages/KitRateBoard";
import AssemblyKitBoard from "../pages/AssemblyKitBoard";
import BomAssemblyAttrs from "../pages/BomAssemblyAttrs";
import ArrivalManagement from "../pages/ArrivalManagement";
import ProjectTaskList from "../pages/ProjectTaskList";
import MaterialDemandSummary from "../pages/MaterialDemandSummary";
import MachineManagement from "../pages/MachineManagement";
import MilestoneManagement from "../pages/MilestoneManagement";
import ExceptionManagement from "../pages/ExceptionManagement";
import ShortageAlert from "../pages/ShortageAlert";
import ECNManagement from "../pages/ECNManagement";
import ECNDetail from "../pages/ECNDetail";
import ECNTypeManagement from "../pages/ECNTypeManagement";
import ECNOverdueAlerts from "../pages/ECNOverdueAlerts";
import ECNStatistics from "../pages/ECNStatistics";
import WorkOrderManagement from "../pages/WorkOrderManagement";
import ProductionDashboard from "../pages/ProductionDashboard";
import WorkshopTaskBoard from "../pages/WorkshopTaskBoard";
import ProductionPlanList from "../pages/ProductionPlanList";
import WorkReportList from "../pages/WorkReportList";
import MaterialRequisitionList from "../pages/MaterialRequisitionList";
import ProductionExceptionList from "../pages/ProductionExceptionList";
import OutsourcingOrderList from "../pages/OutsourcingOrderList";
import OutsourcingOrderDetail from "../pages/OutsourcingOrderDetail";
import AcceptanceOrderList from "../pages/AcceptanceOrderList";
import AcceptanceTemplateManagement from "../pages/AcceptanceTemplateManagement";
import ShortageManagementBoard from "../pages/ShortageManagementBoard";
import WorkloadBoard from "../pages/WorkloadBoard";
import ShortageReportList from "../pages/ShortageReportList";
import ArrivalTrackingList from "../pages/ArrivalTrackingList";
import WorkOrderDetail from "../pages/WorkOrderDetail";
import WorkshopManagement from "../pages/WorkshopManagement";
import WorkerManagement from "../pages/WorkerManagement";
import WorkerWorkstation from "../pages/WorkerWorkstation";
import MaterialRequisitionDetail from "../pages/MaterialRequisitionDetail";
import BudgetManagement from "../pages/BudgetManagement";
import CostAnalysis from "../pages/CostAnalysis";
import AdminDashboard from "../pages/AdminDashboard";
import StrategyAnalysis from "../pages/StrategyAnalysis";
import KeyDecisions from "../pages/KeyDecisions";
import ManagementRhythmDashboard from "../pages/ManagementRhythmDashboard";
import MeetingMap from "../pages/MeetingMap";
import StrategicMeetingManagement from "../pages/StrategicMeetingManagement";
import StrategicMeetingDetail from "../pages/StrategicMeetingDetail";
import MeetingReports from "../pages/MeetingReports";
import CultureWall from "../pages/CultureWall";
import Shipments from "../pages/Shipments";
import DeliveryManagement from "../pages/DeliveryManagement";
import Documents from "../pages/Documents";
import FinanceManagerDashboard from "../pages/FinanceManagerDashboard";
import CostAccounting from "../pages/CostAccounting";
import PaymentApproval from "../pages/PaymentApproval";
import ProjectSettlement from "../pages/ProjectSettlement";
import FinancialReports from "../pages/FinancialReports";
import ExecutiveDashboard from "../pages/ExecutiveDashboard";
import HRManagerDashboard from "../pages/HRManagerDashboard";
import AdministrativeManagerWorkstation from "../pages/AdministrativeManagerWorkstation";
import PerformanceManagement from "../pages/PerformanceManagement";
import PerformanceRanking from "../pages/PerformanceRanking";
import PerformanceIndicators from "../pages/PerformanceIndicators";
import PerformanceResults from "../pages/PerformanceResults";
import MonthlySummary from "../pages/MonthlySummary";
import MyPerformance from "../pages/MyPerformance";
import MyBonus from "../pages/MyBonus";
import EvaluationTaskList from "../pages/EvaluationTaskList";
import EvaluationScoring from "../pages/EvaluationScoring";
import EvaluationWeightConfig from "../pages/EvaluationWeightConfig";
import QualificationManagement from "../pages/QualificationManagement";
import QualificationLevelForm from "../pages/QualificationLevelForm";
import CompetencyModelForm from "../pages/CompetencyModelForm";
import EmployeeQualificationForm from "../pages/EmployeeQualificationForm";
import QualificationAssessmentList from "../pages/QualificationAssessmentList";
import CustomerList from "../pages/CustomerList";
import OpportunityBoard from "../pages/OpportunityBoard";
import LeadAssessment from "../pages/LeadAssessment";
import QuotationList from "../pages/QuotationList";
import ContractList from "../pages/ContractList";
import ContractDetail from "../pages/ContractDetail";
import PaymentManagement from "../pages/PaymentManagement";
import InvoiceManagement from "../pages/InvoiceManagement";
import SalesProjectTrack from "../pages/SalesProjectTrack";
import SalesFunnel from "../pages/SalesFunnel";
import BiddingDetail from "../pages/BiddingDetail";
import LeadManagement from "../pages/LeadManagement";
import OpportunityManagement from "../pages/OpportunityManagement";
import TechnicalAssessment from "../pages/TechnicalAssessment";
import LeadRequirementDetail from "../pages/LeadRequirementDetail";
import OpenItemsManagement from "../pages/OpenItemsManagement";
import RequirementFreezeManagement from "../pages/RequirementFreezeManagement";
import AIClarificationChat from "../pages/AIClarificationChat";
import QuoteManagement from "../pages/QuoteManagement";
import QuoteCostManagement from "../pages/QuoteCostManagement";
import QuoteCostAnalysis from "../pages/QuoteCostAnalysis";
import CostTemplateManagement from "../pages/CostTemplateManagement";
import PurchaseMaterialCostManagement from "../pages/PurchaseMaterialCostManagement";
import FinancialCostUpload from "../pages/FinancialCostUpload";
import ContractManagement from "../pages/ContractManagement";
import ReceivableManagement from "../pages/ReceivableManagement";
import SalesStatistics from "../pages/SalesStatistics";
import SalesTemplateCenter from "../pages/SalesTemplateCenter";
import LossAnalysis from "../pages/LossAnalysis";
import PresaleExpenseManagement from "../pages/PresaleExpenseManagement";
import LeadPriorityManagement from "../pages/LeadPriorityManagement";
import PipelineBreakAnalysis from "../pages/PipelineBreakAnalysis";
import AccountabilityAnalysis from "../pages/AccountabilityAnalysis";
import PipelineHealthMonitoring from "../pages/PipelineHealthMonitoring";
import DelayAnalysis from "../pages/DelayAnalysis";
import CostOverrunAnalysis from "../pages/CostOverrunAnalysis";
import InformationGapAnalysis from "../pages/InformationGapAnalysis";
import PresalesWorkstation from "../pages/PresalesWorkstation";
import PresalesManagerWorkstation from "../pages/PresalesManagerWorkstation";
import PresalesTasks from "../pages/PresalesTasks";
import SolutionList from "../pages/SolutionList";
import SolutionDetail from "../pages/SolutionDetail";
import RequirementSurvey from "../pages/RequirementSurvey";
import BiddingCenter from "../pages/BiddingCenter";
import KnowledgeBase from "../pages/KnowledgeBase";
import ProcurementManagerDashboard from "../pages/ProcurementManagerDashboard";
import ProductionManagerDashboard from "../pages/ProductionManagerDashboard";
import ManufacturingDirectorDashboard from "../pages/ManufacturingDirectorDashboard";
import DispatchManagement from "../pages/DispatchManagement";
import InstallationDispatchManagement from "../pages/InstallationDispatchManagement";
import AcceptanceExecution from "../pages/AcceptanceExecution";
import PMODashboard from "../pages/PMODashboard";
import InitiationManagement from "../pages/InitiationManagement";
import ProjectPhaseManagement from "../pages/ProjectPhaseManagement";
import RiskManagement from "../pages/RiskManagement";
import ProjectClosureManagement from "../pages/ProjectClosureManagement";
import ProjectReviewList from "../pages/ProjectReviewList";
import ProjectReviewDetail from "../pages/ProjectReviewDetail";
import LessonsLearnedLibrary from "../pages/LessonsLearnedLibrary";
import BestPracticeRecommendations from "../pages/BestPracticeRecommendations";
import ResourceOverview from "../pages/ResourceOverview";
import MeetingManagement from "../pages/MeetingManagement";
import RiskWall from "../pages/RiskWall";
import WeeklyReport from "../pages/WeeklyReport";
import RdProjectList from "../pages/RdProjectList";
import RdProjectDetail from "../pages/RdProjectDetail";
import RdProjectWorklogs from "../pages/RdProjectWorklogs";
import RdProjectDocuments from "../pages/RdProjectDocuments";
import RdCostEntry from "../pages/RdCostEntry";
import RdCostSummary from "../pages/RdCostSummary";
import RdCostReports from "../pages/RdCostReports";
import TagManagement from "../pages/TagManagement";
import EmployeeProfileList from "../pages/EmployeeProfileList";
import EmployeeProfileDetail from "../pages/EmployeeProfileDetail";
import ProjectStaffingNeed from "../pages/ProjectStaffingNeed";
import AIStaffMatching from "../pages/AIStaffMatching";
import WorkCenter from "../pages/WorkCenter";
import WorkLog from "../pages/WorkLog";
import WorkLogConfig from "../pages/WorkLogConfig";
import UserManagement from "../pages/UserManagement";
import RoleManagement from "../pages/RoleManagement";
import PermissionManagement from "../pages/PermissionManagement";
import ProjectRoleTypeManagement from "../pages/ProjectRoleTypeManagement";
import SchedulerMonitoringDashboard from "../pages/SchedulerMonitoringDashboard";
import SchedulerConfigManagement from "../pages/SchedulerConfigManagement";
import CustomerManagement from "../pages/CustomerManagement";
import Customer360 from "../pages/Customer360";
import SupplierManagementData from "../pages/SupplierManagementData";
import DepartmentManagement from "../pages/DepartmentManagement";
import MobileWorkerTaskList from "../pages/mobile/MobileWorkerTaskList";
import MobileScanStart from "../pages/mobile/MobileScanStart";
import MobileProgressReport from "../pages/mobile/MobileProgressReport";
import MobileCompleteReport from "../pages/mobile/MobileCompleteReport";
import MobileExceptionReport from "../pages/mobile/MobileExceptionReport";
import MobileMaterialRequisition from "../pages/mobile/MobileMaterialRequisition";
import MobileScanShortage from "../pages/mobile/MobileScanShortage";
import MobileShortageReport from "../pages/mobile/MobileShortageReport";
import MobileMyShortageReports from "../pages/mobile/MobileMyShortageReports";
import PermissionDebug from "../pages/PermissionDebug";
import ShortageReportNew from "../pages/ShortageReportNew";
import ShortageReportDetail from "../pages/ShortageReportDetail";
import ArrivalDetail from "../pages/ArrivalDetail";
import SubstitutionDetail from "../pages/SubstitutionDetail";
import TransferDetail from "../pages/TransferDetail";
import SubstitutionNew from "../pages/SubstitutionNew";
import TransferNew from "../pages/TransferNew";
import ArrivalNew from "../pages/ArrivalNew";
import AlertCenter from "../pages/AlertCenter";
import AlertDetail from "../pages/AlertDetail";
import AlertRuleConfig from "../pages/AlertRuleConfig";
import AlertStatistics from "../pages/AlertStatistics";
import AlertSubscription from "../pages/AlertSubscription";
import AlertSubscriptionSettings from "../pages/AlertSubscriptionSettings";
import IssueManagement from "../pages/IssueManagement";
import IssueTemplateManagement from "../pages/IssueTemplateManagement";
import IssueStatisticsSnapshot from "../pages/IssueStatisticsSnapshot";
import TechnicalSpecManagement from "../pages/TechnicalSpecManagement";
import TechnicalReviewList from "../pages/TechnicalReviewList";
import TechnicalReviewDetail from "../pages/TechnicalReviewDetail";
import SpecMatchCheck from "../pages/SpecMatchCheck";
import CustomerServiceDashboard from "../pages/CustomerServiceDashboard";
import ServiceTicketManagement from "../pages/ServiceTicketManagement";
import ServiceRecord from "../pages/ServiceRecord";
import CustomerCommunication from "../pages/CustomerCommunication";
import CustomerSatisfaction from "../pages/CustomerSatisfaction";
import ServiceAnalytics from "../pages/ServiceAnalytics";
import ServiceKnowledgeBase from "../pages/ServiceKnowledgeBase";
import AuditLogs from "../pages/AuditLogs";
import DataImportExport from "../pages/DataImportExport";
import HourlyRateManagement from "../pages/HourlyRateManagement";
import HRManagement from "../pages/HRManagement";
import PresalesIntegration from "../pages/PresalesIntegration";
import ProjectRoles from "../pages/ProjectRoles";
import EngineerPerformanceDashboard from "../pages/EngineerPerformanceDashboard";
import EngineerPerformanceRanking from "../pages/EngineerPerformanceRanking";
import EngineerPerformanceDetail from "../pages/EngineerPerformanceDetail";
import EngineerCollaboration from "../pages/EngineerCollaboration";
import EngineerKnowledge from "../pages/EngineerKnowledge";

/**
 * 应用路由配置组件
 */
export function AppRoutes() {
  return (
    <Routes>
      {/* Dashboard */}
      <Route
        path="/"
        element={
          <AppProtectedRoute>
            <Dashboard />
          </AppProtectedRoute>
        }
      />
      <Route
        path="/chairman-dashboard"
        element={
          <AppProtectedRoute>
            <ChairmanWorkstation />
          </AppProtectedRoute>
        }
      />
      <Route
        path="/gm-dashboard"
        element={
          <AppProtectedRoute>
            <GeneralManagerWorkstation />
          </AppProtectedRoute>
        }
      />
      <Route path="/admin-dashboard" element={<AdminDashboard />} />
      <Route path="/operation" element={<OperationDashboard />} />
      <Route path="/strategy-analysis" element={<StrategyAnalysis />} />
      <Route path="/key-decisions" element={<KeyDecisions />} />
      <Route
        path="/management-rhythm-dashboard"
        element={<ManagementRhythmDashboard />}
      />
      <Route path="/meeting-map" element={<MeetingMap />} />
      <Route
        path="/strategic-meetings"
        element={<StrategicMeetingManagement />}
      />
      <Route
        path="/strategic-meetings/:id"
        element={<StrategicMeetingDetail />}
      />
      <Route path="/meeting-reports" element={<MeetingReports />} />
      <Route path="/meeting-reports/:id" element={<MeetingReports />} />
      <Route path="/culture-wall" element={<CultureWall />} />
      <Route path="/shipments" element={<Shipments />} />
      <Route path="/pmc/delivery-plan" element={<DeliveryManagement />} />
      <Route path="/pmc/delivery-orders" element={<DeliveryManagement />} />
      <Route path="/pmc/delivery-orders/:id" element={<DeliveryManagement />} />
      <Route
        path="/pmc/delivery-orders/:id/edit"
        element={<DeliveryManagement />}
      />
      <Route path="/pmc/delivery-orders/new" element={<DeliveryManagement />} />
      <Route path="/documents" element={<Documents />} />

      {/* Project Management */}
      {/* 进度跟踪模块 - 新路由 */}
      <Route path="/progress-tracking/tasks" element={<TaskCenter />} />
      <Route path="/progress-tracking/board" element={<ProjectBoard />} />
      <Route path="/progress-tracking/schedule" element={<ScheduleBoard />} />
      <Route path="/progress-tracking/reports" element={<ProgressReport />} />
      <Route path="/progress-tracking/milestones" element={<MilestoneManagement />} />
      <Route path="/progress-tracking/wbs" element={<WBSTemplateManagement />} />
      <Route path="/progress-tracking/gantt" element={<ProjectGantt />} />
      {/* 向后兼容 - 保留旧路由 */}
      <Route path="/board" element={<ProjectBoard />} />
      <Route path="/projects" element={<ProjectList />} />
      <Route path="/projects/:id" element={<ProjectDetail />} />
      <Route path="/projects/:id/workspace" element={<ProjectWorkspace />} />
      <Route
        path="/projects/:id/contributions"
        element={<ProjectContributionReport />}
      />
      <Route path="/projects/:id/gantt" element={<ProjectGantt />} />
      <Route path="/projects/:id/tasks" element={<ProjectTaskList />} />
      <Route path="/projects/:id/machines" element={<MachineManagement />} />
      <Route
        path="/projects/:id/milestones"
        element={<MilestoneManagement />}
      />
      <Route
        path="/projects/:id/progress-report"
        element={<ProgressReport />}
      />
      <Route path="/projects/:id/progress-board" element={<ProgressBoard />} />
      <Route
        path="/projects/:id/progress-forecast"
        element={
          <ProjectReviewProtectedRoute>
            <ProgressForecast />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/:id/dependency-check"
        element={
          <ProjectReviewProtectedRoute>
            <DependencyCheck />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/:id/milestone-rate"
        element={<MilestoneRateReport />}
      />
      <Route
        path="/projects/:id/delay-reasons"
        element={<DelayReasonsReport />}
      />
      <Route path="/reports/milestone-rate" element={<MilestoneRateReport />} />
      <Route path="/reports/delay-reasons" element={<DelayReasonsReport />} />
      <Route path="/wbs-templates" element={<WBSTemplateManagement />} />
      <Route path="/schedule" element={<ScheduleBoard />} />
      <Route path="/tasks" element={<TaskCenter />} />
      <Route path="/assembly-tasks" element={<AssemblerTaskCenter />} />
      <Route path="/workstation" element={<EngineerWorkstation />} />

      {/* Production Management */}
      <Route path="/production-dashboard" element={<ProductionDashboard />} />
      <Route
        path="/production-manager-dashboard"
        element={<ProductionManagerDashboard />}
      />
      <Route
        path="/manufacturing-director-dashboard"
        element={<ManufacturingDirectorDashboard />}
      />
      <Route path="/work-orders" element={<WorkOrderManagement />} />
      <Route path="/work-orders/:id" element={<WorkOrderDetail />} />
      <Route path="/dispatch-management" element={<DispatchManagement />} />
      <Route
        path="/installation-dispatch"
        element={<InstallationDispatchManagement />}
      />
      <Route path="/production-plans" element={<ProductionPlanList />} />
      <Route path="/work-reports" element={<WorkReportList />} />
      <Route
        path="/material-requisitions"
        element={<MaterialRequisitionList />}
      />
      <Route
        path="/material-requisitions/:id"
        element={<MaterialRequisitionDetail />}
      />
      <Route
        path="/production-exceptions"
        element={<ProductionExceptionList />}
      />
      <Route path="/workshops" element={<WorkshopManagement />} />
      <Route path="/workers" element={<WorkerManagement />} />
      <Route path="/worker-workstation" element={<WorkerWorkstation />} />
      <Route path="/outsourcing-orders" element={<OutsourcingOrderList />} />
      <Route
        path="/outsourcing-orders/:id"
        element={<OutsourcingOrderDetail />}
      />
      <Route path="/acceptance-orders" element={<AcceptanceOrderList />} />
      <Route
        path="/acceptance-orders/:id/execute"
        element={<AcceptanceExecution />}
      />
      <Route
        path="/acceptance-templates"
        element={<AcceptanceTemplateManagement />}
      />
      <Route
        path="/shortage-management-board"
        element={<ShortageManagementBoard />}
      />
      <Route path="/shortage-reports" element={<ShortageReportList />} />
      <Route path="/arrival-tracking" element={<ArrivalTrackingList />} />
      <Route path="/workload-board" element={<WorkloadBoard />} />
      <Route path="/workshops/:id/task-board" element={<WorkshopTaskBoard />} />

      {/* Procurement Management */}
      <Route
        path="/procurement-manager-dashboard"
        element={<ProcurementManagerDashboard />}
      />

      {/* Finance Management */}
      <Route
        path="/finance-manager-dashboard"
        element={
          <FinanceProtectedRoute>
            <FinanceManagerDashboard />
          </FinanceProtectedRoute>
        }
      />
      <Route path="/costs" element={<CostAccounting />} />
      <Route path="/payment-approval" element={<PaymentApproval />} />
      <Route path="/settlement" element={<ProjectSettlement />} />
      <Route path="/financial-reports" element={<FinancialReports />} />
      <Route path="/executive-dashboard" element={<ExecutiveDashboard />} />

      {/* HR Management */}
      <Route path="/hr-manager-dashboard" element={<HRManagerDashboard />} />

      {/* Administrative Management */}
      <Route
        path="/administrative-dashboard"
        element={<AdministrativeManagerWorkstation />}
      />

      {/* Performance Management */}
      <Route path="/performance" element={<PerformanceManagement />} />
      <Route path="/performance/ranking" element={<PerformanceRanking />} />
      <Route
        path="/performance/indicators"
        element={<PerformanceIndicators />}
      />
      <Route path="/performance/results" element={<PerformanceResults />} />
      <Route
        path="/performance/results/:employeeId"
        element={<PerformanceResults />}
      />

      {/* Personal Performance Pages */}
      <Route path="/personal/monthly-summary" element={<MonthlySummary />} />
      <Route path="/personal/my-performance" element={<MyPerformance />} />
      <Route path="/personal/my-bonus" element={<MyBonus />} />

      {/* Evaluation Pages */}
      <Route path="/evaluation-tasks" element={<EvaluationTaskList />} />
      <Route path="/evaluation/:taskId" element={<EvaluationScoring />} />
      <Route
        path="/evaluation-weight-config"
        element={<EvaluationWeightConfig />}
      />

      {/* Qualification Management */}
      <Route path="/qualifications" element={<QualificationManagement />} />
      <Route
        path="/qualifications/levels/new"
        element={<QualificationLevelForm />}
      />
      <Route
        path="/qualifications/levels/:id"
        element={<QualificationLevelForm />}
      />
      <Route
        path="/qualifications/levels/:id/edit"
        element={<QualificationLevelForm />}
      />
      <Route
        path="/qualifications/models/new"
        element={<CompetencyModelForm />}
      />
      <Route
        path="/qualifications/models/:id"
        element={<CompetencyModelForm />}
      />
      <Route
        path="/qualifications/models/:id/edit"
        element={<CompetencyModelForm />}
      />
      <Route
        path="/qualifications/employees/certify"
        element={<EmployeeQualificationForm />}
      />
      <Route
        path="/qualifications/employees/:employeeId"
        element={<EmployeeQualificationForm />}
      />
      <Route
        path="/qualifications/employees/:employeeId/view"
        element={<EmployeeQualificationForm />}
      />
      <Route
        path="/qualifications/employees/:employeeId/promote"
        element={<EmployeeQualificationForm />}
      />
      <Route
        path="/qualifications/assessments"
        element={<QualificationAssessmentList />}
      />

      {/* Engineer Performance Evaluation */}
      <Route
        path="/engineer-performance"
        element={<EngineerPerformanceDashboard />}
      />
      <Route
        path="/engineer-performance/ranking"
        element={<EngineerPerformanceRanking />}
      />
      <Route
        path="/engineer-performance/engineer/:userId"
        element={<EngineerPerformanceDetail />}
      />
      <Route
        path="/engineer-performance/collaboration"
        element={<EngineerCollaboration />}
      />
      <Route
        path="/engineer-performance/knowledge"
        element={<EngineerKnowledge />}
      />

      {/* Sales Routes */}
      <Route path="/sales-dashboard" element={<SalesWorkstation />} />
      <Route
        path="/sales-director-dashboard"
        element={<SalesDirectorWorkstation />}
      />
      <Route
        path="/sales-manager-dashboard"
        element={<SalesManagerWorkstation />}
      />
      <Route path="/sales-reports" element={<SalesReports />} />
      <Route path="/sales-team" element={<SalesTeam />} />
      <Route path="/sales/targets" element={<SalesTarget />} />
      <Route path="/contract-approval" element={<ContractApproval />} />
      <Route
        path="/business-support"
        element={<BusinessSupportWorkstation />}
      />
      <Route path="/customers" element={<CustomerList />} />
      <Route path="/opportunities" element={<OpportunityBoard />} />
      <Route path="/lead-assessment" element={<LeadAssessment />} />
      <Route path="/quotations" element={<QuotationList />} />
      <Route path="/contracts" element={<ContractList />} />
      <Route path="/contracts/:id" element={<ContractDetail />} />
      <Route
        path="/payments"
        element={
          <FinanceProtectedRoute>
            <PaymentManagement />
          </FinanceProtectedRoute>
        }
      />
      <Route
        path="/invoices"
        element={
          <FinanceProtectedRoute>
            <InvoiceManagement />
          </FinanceProtectedRoute>
        }
      />
      <Route path="/sales-projects" element={<SalesProjectTrack />} />
      <Route path="/sales-funnel" element={<SalesFunnel />} />
      <Route path="/bidding/:id" element={<BiddingDetail />} />
      {/* New Sales Module Routes */}
      <Route path="/sales/leads" element={<LeadManagement />} />
      <Route path="/sales/opportunities" element={<OpportunityManagement />} />
      <Route
        path="/sales/assessments/:sourceType/:sourceId"
        element={<TechnicalAssessment />}
      />
      <Route
        path="/sales/leads/:leadId/requirement"
        element={<LeadRequirementDetail />}
      />
      <Route
        path="/sales/:sourceType/:sourceId/open-items"
        element={<OpenItemsManagement />}
      />
      <Route
        path="/sales/:sourceType/:sourceId/requirement-freezes"
        element={<RequirementFreezeManagement />}
      />
      <Route
        path="/sales/:sourceType/:sourceId/ai-clarifications"
        element={<AIClarificationChat />}
      />
      {/* 成本报价管理模块 - 新路由 */}
      <Route path="/cost-quotes/quotes" element={<QuoteManagement />} />
      <Route path="/cost-quotes/quotes/:id/cost" element={<QuoteCostManagement />} />
      <Route path="/cost-quotes/quotes/:id/cost-analysis" element={<QuoteCostAnalysis />} />
      <Route path="/cost-quotes/material-costs" element={<PurchaseMaterialCostManagement />} />
      <Route path="/cost-quotes/financial-costs" element={<FinancialCostUpload />} />
      <Route path="/cost-quotes/cost-analysis" element={<QuoteCostAnalysis />} />
      <Route path="/cost-quotes/templates" element={<SalesTemplateCenter />} />
      {/* 向后兼容 - 保留旧路由 */}
      <Route path="/sales/quotes" element={<QuoteManagement />} />
      <Route path="/sales/quotes/:id/cost" element={<QuoteCostManagement />} />
      <Route path="/sales/quotes/:id/cost-analysis" element={<QuoteCostAnalysis />} />
      <Route path="/sales/cost-templates" element={<CostTemplateManagement />} />
      <Route path="/sales/purchase-material-costs" element={<PurchaseMaterialCostManagement />} />
      <Route path="/financial-costs" element={<FinancialCostUpload />} />
      <Route path="/sales/contracts" element={<ContractManagement />} />
      <Route path="/sales/receivables" element={<ReceivableManagement />} />
      <Route path="/sales/statistics" element={<SalesStatistics />} />
      <Route path="/sales/templates" element={<SalesTemplateCenter />} />
      <Route path="/sales/cpq" element={<CpqConfigurator />} />
      <Route path="/sales/loss-analysis" element={<LossAnalysis />} />
      <Route path="/sales/presale-expenses" element={<PresaleExpenseManagement />} />
      <Route path="/sales/priority" element={<LeadPriorityManagement />} />
      <Route path="/sales/pipeline-break-analysis" element={<PipelineBreakAnalysis />} />
      <Route path="/sales/accountability-analysis" element={<AccountabilityAnalysis />} />
      <Route path="/sales/health-monitoring" element={<PipelineHealthMonitoring />} />
      <Route path="/sales/delay-analysis" element={<DelayAnalysis />} />
      <Route path="/sales/cost-overrun-analysis" element={<CostOverrunAnalysis />} />
      <Route path="/sales/information-gap-analysis" element={<InformationGapAnalysis />} />

      {/* Pre-sales Routes */}
      <Route path="/presales-dashboard" element={<PresalesWorkstation />} />
      <Route
        path="/presales-manager-dashboard"
        element={<PresalesManagerWorkstation />}
      />
      <Route path="/presales-tasks" element={<PresalesTasks />} />
      <Route path="/solutions" element={<SolutionList />} />
      <Route path="/solutions/:id" element={<SolutionDetail />} />
      <Route path="/requirement-survey" element={<RequirementSurvey />} />
      <Route path="/bidding" element={<BiddingCenter />} />
      <Route path="/knowledge-base" element={<KnowledgeBase />} />

      {/* Operations */}
      <Route
        path="/procurement-dashboard"
        element={<ProcurementEngineerWorkstation />}
      />
      <Route
        path="/purchases"
        element={
          <ProcurementProtectedRoute>
            <PurchaseOrders />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/purchases/:id"
        element={
          <ProcurementProtectedRoute>
            <PurchaseOrderDetail />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/purchase-requests"
        element={
          <ProcurementProtectedRoute>
            <PurchaseRequestList />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/purchase-requests/new"
        element={
          <ProcurementProtectedRoute>
            <PurchaseRequestNew />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/purchase-requests/:id"
        element={
          <ProcurementProtectedRoute>
            <PurchaseRequestDetail />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/purchase-requests/:id/edit"
        element={
          <ProcurementProtectedRoute>
            <PurchaseRequestNew />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/purchases/from-bom"
        element={
          <ProcurementProtectedRoute>
            <PurchaseOrderFromBOM />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/purchases/receipts"
        element={
          <ProcurementProtectedRoute>
            <ArrivalManagement />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/purchases/receipts/new"
        element={
          <ProcurementProtectedRoute>
            <GoodsReceiptNew />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/purchases/receipts/:id"
        element={
          <ProcurementProtectedRoute>
            <GoodsReceiptDetail />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/materials"
        element={
          <ProcurementProtectedRoute>
            <MaterialList />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/material-tracking"
        element={
          <ProcurementProtectedRoute>
            <MaterialTracking />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/material-readiness"
        element={
          <ProcurementProtectedRoute>
            <MaterialReadiness />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/procurement-analysis"
        element={
          <ProcurementProtectedRoute>
            <ProcurementAnalysis />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/inventory-analysis"
        element={
          <ProcurementProtectedRoute>
            <InventoryAnalysis />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/budgets"
        element={
          <ProcurementProtectedRoute>
            <BudgetManagement />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/cost-analysis"
        element={
          <ProcurementProtectedRoute>
            <CostAnalysis />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/material-demands"
        element={
          <ProcurementProtectedRoute>
            <MaterialDemandSummary />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/bom"
        element={
          <ProcurementProtectedRoute>
            <BOMManagement />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/kit-rate"
        element={
          <ProcurementProtectedRoute>
            <KitRateBoard />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/assembly-kit"
        element={
          <ProductionProtectedRoute>
            <AssemblyKitBoard />
          </ProductionProtectedRoute>
        }
      />
      <Route
        path="/bom-assembly-attrs"
        element={
          <ProcurementProtectedRoute>
            <BomAssemblyAttrs />
          </ProcurementProtectedRoute>
        }
      />
      {/* 变更管理模块 - 新路由 */}
      <Route path="/change-management/ecn" element={<ECNManagement />} />
      <Route path="/change-management/ecn/:id" element={<ECNDetail />} />
      <Route path="/change-management/ecn-types" element={<ECNTypeManagement />} />
      <Route path="/change-management/ecn/overdue-alerts" element={<ECNOverdueAlerts />} />
      <Route path="/change-management/ecn/statistics" element={<ECNStatistics />} />
      {/* 向后兼容 - 保留旧路由 */}
      <Route path="/ecn" element={<ECNManagement />} />
      <Route path="/ecn/:id" element={<ECNDetail />} />
      <Route path="/ecn-types" element={<ECNTypeManagement />} />
      <Route path="/ecn/overdue-alerts" element={<ECNOverdueAlerts />} />
      <Route path="/ecn/statistics" element={<ECNStatistics />} />
      <Route path="/exceptions" element={<ExceptionManagement />} />
      <Route path="/shortage-alerts" element={<ShortageAlert />} />
      <Route
        path="/arrivals"
        element={
          <ProcurementProtectedRoute>
            <ArrivalManagement />
          </ProcurementProtectedRoute>
        }
      />
      <Route path="/suppliers" element={<SupplierManagement />} />
      <Route
        path="/shortage"
        element={
          <ProcurementProtectedRoute>
            <ShortageManagement />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/shortage/reports/new"
        element={
          <ProcurementProtectedRoute>
            <ShortageReportNew />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/shortage/reports/:id"
        element={
          <ProcurementProtectedRoute>
            <ShortageReportDetail />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/shortage/arrivals/:id"
        element={
          <ProcurementProtectedRoute>
            <ArrivalDetail />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/shortage/substitutions/:id"
        element={
          <ProcurementProtectedRoute>
            <SubstitutionDetail />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/shortage/transfers/:id"
        element={
          <ProcurementProtectedRoute>
            <TransferDetail />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/shortage/substitutions/new"
        element={
          <ProcurementProtectedRoute>
            <SubstitutionNew />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/shortage/transfers/new"
        element={
          <ProcurementProtectedRoute>
            <TransferNew />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/shortage/arrivals/new"
        element={
          <ProcurementProtectedRoute>
            <ArrivalNew />
          </ProcurementProtectedRoute>
        }
      />
      <Route path="/alerts" element={<AlertCenter />} />
      <Route path="/alerts/:id" element={<AlertDetail />} />
      <Route path="/alert-rules" element={<AlertRuleConfig />} />
      <Route path="/alert-statistics" element={<AlertStatistics />} />
      <Route path="/alert-subscription" element={<AlertSubscription />} />
      <Route
        path="/alerts/subscriptions"
        element={<AlertSubscriptionSettings />}
      />
      <Route
        path="/settings/alert-subscriptions"
        element={<AlertSubscriptionSettings />}
      />

      {/* Quality & Acceptance */}
      <Route path="/acceptance" element={<Acceptance />} />
      <Route path="/approvals" element={<ApprovalCenter />} />
      <Route path="/issues" element={<IssueManagement />} />
      <Route path="/issue-templates" element={<IssueTemplateManagement />} />
      <Route
        path="/issue-statistics-snapshot"
        element={<IssueStatisticsSnapshot />}
      />

      {/* Technical Spec Management */}
      <Route path="/technical-spec" element={<TechnicalSpecManagement />} />

      {/* Technical Review Management */}
      <Route path="/technical-reviews" element={<TechnicalReviewList />} />
      <Route
        path="/technical-reviews/new"
        element={<TechnicalReviewDetail />}
      />
      <Route
        path="/technical-reviews/:reviewId"
        element={<TechnicalReviewDetail />}
      />
      <Route
        path="/technical-reviews/:reviewId/edit"
        element={<TechnicalReviewDetail />}
      />
      <Route path="/spec-match-check" element={<SpecMatchCheck />} />

      {/* Customer Service */}
      <Route
        path="/customer-service-dashboard"
        element={<CustomerServiceDashboard />}
      />
      <Route path="/service-tickets" element={<ServiceTicketManagement />} />
      <Route path="/service-records" element={<ServiceRecord />} />
      <Route
        path="/customer-communications"
        element={<CustomerCommunication />}
      />
      <Route path="/customer-satisfaction" element={<CustomerSatisfaction />} />
      <Route path="/service-analytics" element={<ServiceAnalytics />} />
      <Route
        path="/service-knowledge-base"
        element={<ServiceKnowledgeBase />}
      />

      {/* PMO Routes */}
      <Route path="/pmo/dashboard" element={<PMODashboard />} />
      <Route path="/pmo/initiations" element={<InitiationManagement />} />
      <Route path="/pmo/initiations/:id" element={<InitiationManagement />} />
      <Route path="/pmo/phases" element={<ProjectPhaseManagement />} />
      <Route
        path="/pmo/phases/:projectId"
        element={<ProjectPhaseManagement />}
      />
      <Route path="/pmo/risks" element={<RiskManagement />} />
      <Route path="/pmo/risks/:projectId" element={<RiskManagement />} />
      <Route path="/pmo/closure" element={<ProjectClosureManagement />} />
      <Route
        path="/pmo/closure/:projectId"
        element={<ProjectClosureManagement />}
      />
      <Route
        path="/projects/reviews"
        element={
          <ProjectReviewProtectedRoute>
            <ProjectReviewList />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/reviews/:reviewId"
        element={
          <ProjectReviewProtectedRoute>
            <ProjectReviewDetail />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/reviews/:reviewId/edit"
        element={
          <ProjectReviewProtectedRoute>
            <ProjectReviewDetail />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/reviews/new"
        element={
          <ProjectReviewProtectedRoute>
            <ProjectReviewDetail />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/lessons-learned"
        element={
          <ProjectReviewProtectedRoute>
            <LessonsLearnedLibrary />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/best-practices/recommend"
        element={
          <ProjectReviewProtectedRoute>
            <BestPracticeRecommendations />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route
        path="/projects/:projectId/best-practices/recommend"
        element={
          <ProjectReviewProtectedRoute>
            <BestPracticeRecommendations />
          </ProjectReviewProtectedRoute>
        }
      />
      <Route path="/pmo/resource-overview" element={<ResourceOverview />} />
      <Route path="/pmo/meetings" element={<MeetingManagement />} />
      <Route path="/pmo/risk-wall" element={<RiskWall />} />
      <Route path="/pmo/weekly-report" element={<WeeklyReport />} />

      {/* R&D Project Management */}
      <Route path="/rd-projects" element={<RdProjectList />} />
      <Route path="/rd-projects/:id" element={<RdProjectDetail />} />
      <Route path="/rd-projects/:id/worklogs" element={<RdProjectWorklogs />} />
      <Route
        path="/rd-projects/:id/documents"
        element={<RdProjectDocuments />}
      />
      <Route path="/rd-projects/:id/cost-entry" element={<RdCostEntry />} />
      <Route path="/rd-projects/:id/cost-summary" element={<RdCostSummary />} />
      <Route path="/rd-projects/:id/reports" element={<RdCostReports />} />
      <Route path="/rd-cost-entry" element={<RdCostEntry />} />
      <Route path="/rd-cost-summary" element={<RdCostSummary />} />
      <Route path="/rd-cost-reports" element={<RdCostReports />} />

      {/* AI Staff Matching */}
      <Route path="/staff-matching/tags" element={<TagManagement />} />
      <Route
        path="/staff-matching/profiles"
        element={<EmployeeProfileList />}
      />
      <Route
        path="/staff-matching/profiles/:id"
        element={<EmployeeProfileDetail />}
      />
      <Route
        path="/staff-matching/staffing-needs"
        element={<ProjectStaffingNeed />}
      />
      <Route path="/staff-matching/matching" element={<AIStaffMatching />} />

      {/* Personal Center */}
      <Route path="/work-center" element={<WorkCenter />} />
      <Route path="/notifications" element={<NotificationCenter />} />
      <Route path="/timesheet" element={<Timesheet />} />
      <Route path="/timesheet/dashboard" element={<TimesheetDashboard />} />
      <Route path="/timesheet/batch" element={<TimesheetBatchOperations />} />
      <Route path="/work-log" element={<WorkLog />} />
      <Route path="/work-log/config" element={<WorkLogConfig />} />
      <Route path="/settings" element={<Settings />} />

      {/* System Management */}
      <Route path="/user-management" element={<UserManagement />} />
      <Route path="/role-management" element={<RoleManagement />} />
      <Route path="/permission-management" element={<PermissionManagement />} />
      <Route
        path="/project-role-types"
        element={<ProjectRoleTypeManagement />}
      />
      <Route
        path="/scheduler-monitoring"
        element={<SchedulerMonitoringDashboard />}
      />
      <Route path="/scheduler-config" element={<SchedulerConfigManagement />} />
      <Route path="/audit-logs" element={<AuditLogs />} />
      <Route path="/data-import-export" element={<DataImportExport />} />
      <Route path="/hourly-rates" element={<HourlyRateManagement />} />
      <Route path="/hr-management" element={<HRManagement />} />
      <Route path="/presales-integration" element={<PresalesIntegration />} />
      <Route path="/projects/:id/roles" element={<ProjectRoles />} />

      {/* Master Data Management */}
      <Route path="/customer-management" element={<CustomerManagement />} />
      <Route path="/customers/:id/360" element={<Customer360 />} />
      <Route
        path="/supplier-management-data"
        element={<SupplierManagementData />}
      />
      <Route path="/department-management" element={<DepartmentManagement />} />

      {/* Mobile Pages */}
      <Route path="/mobile/tasks" element={<MobileWorkerTaskList />} />
      <Route path="/mobile/scan-start" element={<MobileScanStart />} />
      <Route
        path="/mobile/progress-report"
        element={<MobileProgressReport />}
      />
      <Route
        path="/mobile/complete-report"
        element={<MobileCompleteReport />}
      />
      <Route
        path="/mobile/exception-report"
        element={<MobileExceptionReport />}
      />
      <Route
        path="/mobile/material-requisition"
        element={<MobileMaterialRequisition />}
      />
      <Route path="/mobile/scan-shortage" element={<MobileScanShortage />} />
      <Route
        path="/mobile/shortage-report"
        element={<MobileShortageReport />}
      />
      <Route
        path="/mobile/my-shortage-reports"
        element={<MobileMyShortageReports />}
      />

      {/* Debug Routes */}
      <Route path="/debug/permissions" element={<PermissionDebug />} />

      {/* Fallback */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
