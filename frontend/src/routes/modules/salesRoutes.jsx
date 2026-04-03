import { Route, Navigate } from "react-router-dom";
import { FinanceProtectedRoute } from "../../components/common/ProtectedRoute";
import { lazyLoad } from "../lazyLoad";

// 客户管理
const CustomerList = lazyLoad(() => import("../../pages/CustomerList"));
const CustomerDetail = lazyLoad(() => import("../../pages/CustomerManagement/CustomerDetail"));
const Customer360 = lazyLoad(() => import("../../pages/Customer360"));

// 线索管理
const LeadManagement = lazyLoad(() => import("../../pages/LeadManagement"));
const LeadDetail = lazyLoad(() => import("../../pages/LeadDetail"));
const LeadAssessment = lazyLoad(() => import("../../pages/LeadAssessment"));
const LeadRequirementDetail = lazyLoad(() => import("../../pages/LeadRequirementDetail"));
const LeadPriorityManagement = lazyLoad(() => import("../../pages/LeadPriorityManagement"));

// 商机管理
const OpportunityBoard = lazyLoad(() => import("../../pages/OpportunityBoard"));
const OpportunityManagement = lazyLoad(() => import("../../pages/OpportunityManagement"));
const OpportunityDetail = lazyLoad(() => import("../../pages/OpportunityDetail"));

// 报价管理
const QuotationList = lazyLoad(() => import("../../pages/QuotationList"));
const QuoteManagementCenter = lazyLoad(() => import("../../pages/QuoteManagementCenter"));
const QuoteManagement = lazyLoad(() => import("../../pages/QuoteManagement"));
const QuoteCreateEdit = lazyLoad(() => import("../../pages/QuoteCreateEdit"));
const QuoteCostManagement = lazyLoad(() => import("../../pages/QuoteCostManagement"));
const QuoteCostAnalysis = lazyLoad(() => import("../../pages/QuoteCostAnalysis"));
const CostTemplateManagement = lazyLoad(() => import("../../pages/CostTemplateManagement"));
const PurchaseMaterialCostManagement = lazyLoad(() => import("../../pages/PurchaseMaterialCostManagement"));
const FinancialCostUpload = lazyLoad(() => import("../../pages/FinancialCostUpload"));
const CpqConfigurator = lazyLoad(() => import("../../pages/CpqConfigurator"));

// 合同管理
const ContractList = lazyLoad(() => import("../../pages/ContractList"));
const ContractDetail = lazyLoad(() => import("../../pages/ContractDetail"));
const ContractManagement = lazyLoad(() => import("../../pages/ContractManagement"));
const ContractApproval = lazyLoad(() => import("../../pages/ContractApproval"));

// 财务相关
const PaymentManagement = lazyLoad(() => import("../../pages/PaymentManagement"));
const InvoiceManagement = lazyLoad(() => import("../../pages/invoice/InvoiceManagement"));
const ReceivableManagement = lazyLoad(() => import("../../pages/ReceivableManagement"));

// 销售团队
const SalesTeam = lazyLoad(() => import("../../pages/SalesTeam"));
const SalesTeamCenter = lazyLoad(() => import("../../pages/SalesTeamCenter"));
const SalesReports = lazyLoad(() => import("../../pages/SalesReports"));
const SalesStatistics = lazyLoad(() => import("../../pages/SalesStatistics"));
const SalesOrganization = lazyLoad(() => import("../../pages/SalesAI/SalesOrganization"));
const SalesOpportunityCenter = lazyLoad(() => import("../../pages/SalesOpportunityCenter"));

// 销售漏斗
const SalesFunnel = lazyLoad(() => import("../../pages/SalesFunnel"));

// 售前相关
const PresalesTasks = lazyLoad(() => import("../../pages/PresalesTasks"));
const SalesPresaleWorkbench = lazyLoad(() => import("../../pages/SalesPresaleWorkbench"));
const TechnicalAssessment = lazyLoad(() => import("../../pages/TechnicalAssessment"));
const OpenItemsManagement = lazyLoad(() => import("../../pages/OpenItemsManagement"));
const RequirementFreezeManagement = lazyLoad(() => import("../../pages/RequirementFreezeManagement"));
const AIClarificationChat = lazyLoad(() => import("../../pages/AIClarificationChat"));
const PresaleExpenseManagement = lazyLoad(() => import("../../pages/PresaleExpenseManagement"));
const BiddingDetail = lazyLoad(() => import("../../pages/BiddingDetail"));
const SalesProjectTrack = lazyLoad(() => import("../../pages/SalesProjectTrack"));
const SalesTemplateCenter = lazyLoad(() => import("../../pages/SalesTemplateCenter"));

// AI 销售助手
const IntelligentQuote = lazyLoad(() => import("../../pages/SalesAI/IntelligentQuote"));
const SalesAutomation = lazyLoad(() => import("../../pages/SalesAI/Automation"));
const ForecastDashboard = lazyLoad(() => import("../../pages/SalesAI/ForecastDashboard"));
const PerformanceIncentive = lazyLoad(() => import("../../pages/SalesAI/PerformanceIncentive"));
const Collaboration = lazyLoad(() => import("../../pages/SalesAI/Collaboration"));
const RelationshipMaturity = lazyLoad(() => import("../../pages/SalesAI/RelationshipMaturity"));
const WinRatePrediction = lazyLoad(() => import("../../pages/SalesAI/WinRatePrediction"));
const CompetitorAnalysis = lazyLoad(() => import("../../pages/SalesAI/CompetitorAnalysis"));
const DataQuality = lazyLoad(() => import("../../pages/SalesAI/DataQuality"));
const RoleBasedView = lazyLoad(() => import("../../pages/SalesAI/RoleBasedView"));

// 分析相关
const LossAnalysis = lazyLoad(() => import("../../pages/LossAnalysis"));
const PipelineBreakAnalysis = lazyLoad(() => import("../../pages/PipelineBreakAnalysis"));
const AccountabilityAnalysis = lazyLoad(() => import("../../pages/AccountabilityAnalysis"));
const PipelineHealthMonitoring = lazyLoad(() => import("../../pages/PipelineHealthMonitoring"));
const DelayAnalysis = lazyLoad(() => import("../../pages/DelayAnalysis"));
const CostOverrunAnalysis = lazyLoad(() => import("../../pages/CostOverrunAnalysis"));
const InformationGapAnalysis = lazyLoad(() => import("../../pages/InformationGapAnalysis"));

// 销售工作站
const SalesWorkstation = lazyLoad(() => import("../../pages/SalesWorkstation"));

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
