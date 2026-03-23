import { lazy } from "react";
import { Route, Navigate } from "react-router-dom";
import { FinanceProtectedRoute } from "../../components/common/ProtectedRoute";

// ---- 懒加载页面组件（销售模块） ----

// 客户管理
const CustomerList = lazy(() => import("../../pages/CustomerList"));
const CustomerDetail = lazy(() => import("../../pages/CustomerManagement/CustomerDetail"));

// 线索管理
const LeadManagement = lazy(() => import("../../pages/LeadManagement"));
const LeadDetail = lazy(() => import("../../pages/LeadDetail"));
const LeadAssessment = lazy(() => import("../../pages/LeadAssessment"));
const LeadRequirementDetail = lazy(() => import("../../pages/LeadRequirementDetail"));
const LeadPriorityManagement = lazy(() => import("../../pages/LeadPriorityManagement"));

// 商机管理
const OpportunityBoard = lazy(() => import("../../pages/OpportunityBoard"));
const OpportunityDetail = lazy(() => import("../../pages/OpportunityDetail"));
const OpportunityManagement = lazy(() => import("../../pages/OpportunityManagement"));

// 报价管理
const QuotationList = lazy(() => import("../../pages/QuotationList"));
const QuoteManagementCenter = lazy(() => import("../../pages/QuoteManagementCenter"));
const QuoteManagement = lazy(() => import("../../pages/QuoteManagement"));
const QuoteCreateEdit = lazy(() => import("../../pages/QuoteCreateEdit"));
const QuoteCostManagement = lazy(() => import("../../pages/QuoteCostManagement"));
const QuoteCostAnalysis = lazy(() => import("../../pages/QuoteCostAnalysis"));
const CostTemplateManagement = lazy(() => import("../../pages/CostTemplateManagement"));
const PurchaseMaterialCostManagement = lazy(() => import("../../pages/PurchaseMaterialCostManagement"));
const FinancialCostUpload = lazy(() => import("../../pages/FinancialCostUpload"));
const CpqConfigurator = lazy(() => import("../../pages/CpqConfigurator"));

// 合同管理
const ContractList = lazy(() => import("../../pages/ContractList"));
const ContractDetail = lazy(() => import("../../pages/ContractDetail"));
const ContractApproval = lazy(() => import("../../pages/ContractApproval"));
const ContractManagement = lazy(() => import("../../pages/ContractManagement"));

// 财务相关
const PaymentManagement = lazy(() => import("../../pages/PaymentManagement"));
const InvoiceManagement = lazy(() => import("../../pages/invoice"));
const ReceivableManagement = lazy(() => import("../../pages/ReceivableManagement"));
const PresaleExpenseManagement = lazy(() => import("../../pages/PresaleExpenseManagement"));

// 销售团队
const SalesTeam = lazy(() => import("../../pages/SalesTeam"));
const SalesTeamCenter = lazy(() => import("../../pages/SalesTeamCenter"));

// 销售漏斗
const SalesFunnel = lazy(() => import("../../pages/SalesFunnel"));

// 售前相关
const PresalesTasks = lazy(() => import("../../pages/PresalesTasks"));
const SalesPresaleWorkbench = lazy(() => import("../../pages/SalesPresaleWorkbench"));
const TechnicalAssessment = lazy(() => import("../../pages/TechnicalAssessment"));
const OpenItemsManagement = lazy(() => import("../../pages/OpenItemsManagement"));
const RequirementFreezeManagement = lazy(() => import("../../pages/RequirementFreezeManagement"));
const AIClarificationChat = lazy(() => import("../../pages/AIClarificationChat"));

// AI 销售助手
const IntelligentQuote = lazy(() => import("../../pages/SalesAI/IntelligentQuote"));
const SalesAutomation = lazy(() => import("../../pages/SalesAI/Automation"));
const ForecastDashboard = lazy(() => import("../../pages/SalesAI/ForecastDashboard"));
const Customer360 = lazy(() => import("../../pages/SalesAI/Customer360"));
const PerformanceIncentive = lazy(() => import("../../pages/SalesAI/PerformanceIncentive"));
const Collaboration = lazy(() => import("../../pages/SalesAI/Collaboration"));
const RelationshipMaturity = lazy(() => import("../../pages/SalesAI/RelationshipMaturity"));
const WinRatePrediction = lazy(() => import("../../pages/SalesAI/WinRatePrediction"));
const CompetitorAnalysis = lazy(() => import("../../pages/SalesAI/CompetitorAnalysis"));
const SalesOrganization = lazy(() => import("../../pages/SalesAI/SalesOrganization"));
const DataQuality = lazy(() => import("../../pages/SalesAI/DataQuality"));
const RoleBasedView = lazy(() => import("../../pages/SalesAI/RoleBasedView"));

// 分析相关
const SalesReports = lazy(() => import("../../pages/SalesReports"));
const SalesOpportunityCenter = lazy(() => import("../../pages/SalesOpportunityCenter"));
const SalesStatistics = lazy(() => import("../../pages/SalesStatistics"));
const SalesProjectTrack = lazy(() => import("../../pages/SalesProjectTrack"));
const BiddingDetail = lazy(() => import("../../pages/BiddingDetail"));
const SalesTemplateCenter = lazy(() => import("../../pages/SalesTemplateCenter"));
const LossAnalysis = lazy(() => import("../../pages/LossAnalysis"));
const PipelineBreakAnalysis = lazy(() => import("../../pages/PipelineBreakAnalysis"));
const AccountabilityAnalysis = lazy(() => import("../../pages/AccountabilityAnalysis"));
const PipelineHealthMonitoring = lazy(() => import("../../pages/PipelineHealthMonitoring"));
const DelayAnalysis = lazy(() => import("../../pages/DelayAnalysis"));
const CostOverrunAnalysis = lazy(() => import("../../pages/CostOverrunAnalysis"));
const InformationGapAnalysis = lazy(() => import("../../pages/InformationGapAnalysis"));

// 销售工作站
const SalesWorkstation = lazy(() => import("../../pages/SalesWorkstation"));

export function SalesRoutes() {
  return (
    <>
      {/* 销售漏斗（固定路径，放在最前避免被 /sales/:param 抢匹配） */}
      <Route path="/sales-funnel" element={<Navigate to="/sales/funnel" replace />} />
      <Route path="/sales/funnel" element={<SalesFunnel />} />
      {/* 销售目标已整合到销售预测页面 */}
      <Route path="/sales/targets" element={<Navigate to="/sales/forecast-dashboard" replace />} />
      <Route path="/sales/sales-analysis" element={<Navigate to="/presales/presale-analytics" replace />} />

      <Route path="/sales-reports" element={<SalesReports />} />
      <Route path="/sales/opportunity-center" element={<SalesOpportunityCenter />} />
      <Route path="/sales/team-center" element={<SalesTeamCenter />} />
      <Route path="/sales-team" element={<SalesTeam />} />
      <Route path="/sales/team" element={<SalesTeam />} />
      <Route path="/sales/team/ranking" element={<SalesTeam />} />
      <Route path="/contract-approval" element={<ContractApproval />} />
      <Route path="/sales/contracts/approval" element={<ContractApproval />} />
      <Route path="/customers" element={<Navigate to="/sales/customers" replace />} />
      <Route path="/sales/customers" element={<CustomerList />} />
      <Route path="/sales/customers/:id" element={<CustomerDetail />} />
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
      <Route path="/bidding/:id" element={<BiddingDetail />} />
      <Route path="/sales/leads" element={<LeadManagement />} />
      <Route path="/sales/leads/:id" element={<LeadDetail />} />
      <Route path="/sales/opportunities" element={<OpportunityManagement />} />
      <Route path="/sales/opportunities/:id" element={<OpportunityDetail />} />
      <Route path="/sales/presales-tasks" element={<PresalesTasks />} />
      <Route path="/sales/presales-workbench" element={<Navigate to="/sales/presale-workbench" replace />} />
      <Route path="/sales/presale-workbench" element={<SalesPresaleWorkbench />} />
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
      <Route path="/cost-quotes/quotes" element={<QuoteManagementCenter />} />
      <Route path="/cost-quotes/margin" element={<QuoteManagementCenter />} />
      <Route path="/cost-quotes/quotes/:id/cost" element={<QuoteCostManagement />} />
      <Route path="/cost-quotes/material-costs" element={<PurchaseMaterialCostManagement />} />
      <Route path="/cost-quotes/financial-costs" element={<FinancialCostUpload />} />
      <Route path="/cost-quotes/templates" element={<QuoteManagementCenter />} />
      <Route path="/sales/quotes" element={<QuoteManagementCenter />} />
      <Route path="/sales/quotes/margin" element={<QuoteManagementCenter />} />
      <Route path="/sales/quotes/management" element={<QuoteManagement />} />
      <Route path="/sales/quotes/create" element={<QuoteCreateEdit />} />
      <Route path="/sales/quotes/:id/edit" element={<QuoteCreateEdit />} />
      <Route path="/sales/quotes/:id/cost" element={<QuoteCostManagement />} />
      <Route path="/sales/quotes/:id/cost-analysis" element={<QuoteCostAnalysis />} />
      <Route path="/sales/cost-templates" element={<CostTemplateManagement />} />
      <Route path="/sales/purchase-material-costs" element={<PurchaseMaterialCostManagement />} />
      <Route path="/financial-costs" element={<FinancialCostUpload />} />
      <Route path="/sales/contracts" element={<ContractManagement />} />
      <Route path="/sales/receivables" element={<ReceivableManagement />} />
      <Route path="/sales/statistics" element={<SalesStatistics />} />
      <Route path="/sales/templates" element={<QuoteManagementCenter />} />
      <Route path="/sales/templates/center" element={<SalesTemplateCenter />} />
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
      {/* 销售工作站 */}
      <Route path="/sales/workstation" element={<SalesWorkstation />} />
      {/* AI 销售助手相关路由 */}
      <Route path="/sales/intelligent-quote" element={<IntelligentQuote />} />
      <Route path="/sales/automation" element={<SalesAutomation />} />
      <Route path="/sales/forecast-dashboard" element={<ForecastDashboard />} />
      <Route path="/sales/funnel-optimization" element={<Navigate to="/sales/funnel" replace />} />
      <Route path="/sales/customer-360" element={<Customer360 />} />
      <Route path="/sales/customer-360/:id" element={<Customer360 />} />
      <Route path="/sales/performance-incentive" element={<PerformanceIncentive />} />
      <Route path="/sales/collaboration" element={<Collaboration />} />
      <Route path="/sales/relationship-maturity" element={<RelationshipMaturity />} />
      <Route path="/sales/win-rate-prediction" element={<WinRatePrediction />} />
      <Route path="/sales/win-rate-prediction/:id" element={<WinRatePrediction />} />
      <Route path="/sales/competitor-analysis" element={<CompetitorAnalysis />} />
      <Route path="/sales/organization" element={<SalesOrganization />} />
      <Route path="/sales/data-quality" element={<DataQuality />} />
      <Route path="/sales/role-based-view" element={<RoleBasedView />} />
    </>
  );
}
