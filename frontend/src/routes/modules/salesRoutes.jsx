import { Route } from "react-router-dom";
import { FinanceProtectedRoute } from "../../components/common/ProtectedRoute";

import SalesReports from "../../pages/SalesReports";
import SalesTeam from "../../pages/SalesTeam";
import SalesTarget from "../../pages/SalesTarget";
import CpqConfigurator from "../../pages/CpqConfigurator";
import ContractApproval from "../../pages/ContractApproval";
import CustomerList from "../../pages/CustomerList";
import OpportunityBoard from "../../pages/OpportunityBoard";
import LeadAssessment from "../../pages/LeadAssessment";
import QuotationList from "../../pages/QuotationList";
import ContractList from "../../pages/ContractList";
import ContractDetail from "../../pages/ContractDetail";
import PaymentManagement from "../../pages/PaymentManagement";
import InvoiceManagement from "../../pages/invoice";
import SalesProjectTrack from "../../pages/SalesProjectTrack";
import SalesFunnel from "../../pages/SalesFunnel";
import BiddingDetail from "../../pages/BiddingDetail";
import LeadManagement from "../../pages/LeadManagement";
import OpportunityManagement from "../../pages/OpportunityManagement";
import TechnicalAssessment from "../../pages/TechnicalAssessment";
import LeadRequirementDetail from "../../pages/LeadRequirementDetail";
import OpenItemsManagement from "../../pages/OpenItemsManagement";
import RequirementFreezeManagement from "../../pages/RequirementFreezeManagement";
import AIClarificationChat from "../../pages/AIClarificationChat";
import QuoteManagementCenter from "../../pages/QuoteManagementCenter";
import QuoteCostManagement from "../../pages/QuoteCostManagement";
import CostTemplateManagement from "../../pages/CostTemplateManagement";
import PurchaseMaterialCostManagement from "../../pages/PurchaseMaterialCostManagement";
import FinancialCostUpload from "../../pages/FinancialCostUpload";
import ContractManagement from "../../pages/ContractManagement";
import ReceivableManagement from "../../pages/ReceivableManagement";
import SalesStatistics from "../../pages/SalesStatistics";
import LossAnalysis from "../../pages/LossAnalysis";
import PresaleExpenseManagement from "../../pages/PresaleExpenseManagement";
import LeadPriorityManagement from "../../pages/LeadPriorityManagement";
import PipelineBreakAnalysis from "../../pages/PipelineBreakAnalysis";
import AccountabilityAnalysis from "../../pages/AccountabilityAnalysis";
import PipelineHealthMonitoring from "../../pages/PipelineHealthMonitoring";
import DelayAnalysis from "../../pages/DelayAnalysis";
import CostOverrunAnalysis from "../../pages/CostOverrunAnalysis";
import InformationGapAnalysis from "../../pages/InformationGapAnalysis";
import LeadDetail from "../../pages/LeadDetail";
import OpportunityDetail from "../../pages/OpportunityDetail";
import QuoteCostAnalysis from "../../pages/QuoteCostAnalysis";
import QuoteCreateEdit from "../../pages/QuoteCreateEdit";
import QuoteManagement from "../../pages/QuoteManagement";
import SalesTemplateCenter from "../../pages/SalesTemplateCenter";
import PresalesTasks from "../../pages/PresalesTasks";

// AI 销售助手相关组件
import { default as SalesAIAssistant } from "../../pages/SalesAI";
import IntelligentQuote from "../../pages/SalesAI/IntelligentQuote";
import SalesAutomation from "../../pages/SalesAI/Automation";
import ForecastDashboard from "../../pages/SalesAI/ForecastDashboard";
import FunnelOptimization from "../../pages/SalesAI/FunnelOptimization";
import Customer360 from "../../pages/SalesAI/Customer360";
import PerformanceIncentive from "../../pages/SalesAI/PerformanceIncentive";
import Collaboration from "../../pages/SalesAI/Collaboration";
import RelationshipMaturity from "../../pages/SalesAI/RelationshipMaturity";
import WinRatePrediction from "../../pages/SalesAI/WinRatePrediction";
import CompetitorAnalysis from "../../pages/SalesAI/CompetitorAnalysis";
import SalesOrganization from "../../pages/SalesAI/SalesOrganization";
import DataQuality from "../../pages/SalesAI/DataQuality";
import RoleBasedView from "../../pages/SalesAI/RoleBasedView";


export function SalesRoutes() {
  return (
    <>
      <Route path="/sales-reports" element={<SalesReports />} />
      <Route path="/sales-team" element={<SalesTeam />} />
      <Route path="/sales/team" element={<SalesTeam />} />
      <Route path="/sales/team/ranking" element={<SalesTeam />} />
      <Route path="/sales/targets" element={<SalesTarget />} />
      <Route path="/contract-approval" element={<ContractApproval />} />
      <Route path="/sales/contracts/approval" element={<ContractApproval />} />
      <Route path="/customers" element={<CustomerList />} />
      <Route path="/sales/customers" element={<CustomerList />} />
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
      <Route path="/sales/leads" element={<LeadManagement />} />
      <Route path="/sales/leads/:id" element={<LeadDetail />} />
      <Route path="/sales/opportunities" element={<OpportunityManagement />} />
      <Route path="/sales/opportunities/:id" element={<OpportunityDetail />} />
      <Route path="/sales/presales-tasks" element={<PresalesTasks />} />
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
      <Route path="/cost-quotes/quotes/:id/cost" element={<QuoteCostManagement />} />
      <Route path="/cost-quotes/material-costs" element={<PurchaseMaterialCostManagement />} />
      <Route path="/cost-quotes/financial-costs" element={<FinancialCostUpload />} />
      <Route path="/cost-quotes/templates" element={<QuoteManagementCenter />} />
      <Route path="/sales/quotes" element={<QuoteManagementCenter />} />
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
      {/* AI 销售助手相关路由 */}
      <Route path="/sales/ai-assistant" element={<SalesAIAssistant />} />
      <Route path="/sales/intelligent-quote" element={<IntelligentQuote />} />
      <Route path="/sales/automation" element={<SalesAutomation />} />
      <Route path="/sales/forecast-dashboard" element={<ForecastDashboard />} />
      <Route path="/sales/funnel-optimization" element={<FunnelOptimization />} />
      <Route path="/sales/customer-360/:id" element={<Customer360 />} />
      <Route path="/sales/performance-incentive" element={<PerformanceIncentive />} />
      <Route path="/sales/collaboration" element={<Collaboration />} />
      <Route path="/sales/relationship-maturity" element={<RelationshipMaturity />} />
      <Route path="/sales/win-rate-prediction/:id" element={<WinRatePrediction />} />
      <Route path="/sales/competitor-analysis" element={<CompetitorAnalysis />} />
      <Route path="/sales/organization" element={<SalesOrganization />} />
      <Route path="/sales/data-quality" element={<DataQuality />} />
      <Route path="/sales/role-based-view" element={<RoleBasedView />} />
    </>
  );
}
