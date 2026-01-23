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
import QuoteManagement from "../../pages/QuoteManagement";
import QuoteCostManagement from "../../pages/QuoteCostManagement";
import CostTemplateManagement from "../../pages/CostTemplateManagement";
import PurchaseMaterialCostManagement from "../../pages/PurchaseMaterialCostManagement";
import FinancialCostUpload from "../../pages/FinancialCostUpload";
import ContractManagement from "../../pages/ContractManagement";
import ReceivableManagement from "../../pages/ReceivableManagement";
import SalesStatistics from "../../pages/SalesStatistics";
import SalesTemplateCenter from "../../pages/SalesTemplateCenter";
import LossAnalysis from "../../pages/LossAnalysis";
import PresaleExpenseManagement from "../../pages/PresaleExpenseManagement";
import LeadPriorityManagement from "../../pages/LeadPriorityManagement";
import PipelineBreakAnalysis from "../../pages/PipelineBreakAnalysis";
import AccountabilityAnalysis from "../../pages/AccountabilityAnalysis";
import PipelineHealthMonitoring from "../../pages/PipelineHealthMonitoring";
import DelayAnalysis from "../../pages/DelayAnalysis";
import CostOverrunAnalysis from "../../pages/CostOverrunAnalysis";
import InformationGapAnalysis from "../../pages/InformationGapAnalysis";

export function SalesRoutes() {
  return (
    <>
      <Route path="/sales-reports" element={<SalesReports />} />
      <Route path="/sales-team" element={<SalesTeam />} />
      <Route path="/sales/team" element={<SalesTeam />} />
      <Route path="/sales/team/ranking" element={<SalesTeam />} />
      <Route path="/sales/targets" element={<SalesTarget />} />
      <Route path="/contract-approval" element={<ContractApproval />} />
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
      <Route path="/cost-quotes/quotes" element={<QuoteManagement />} />
      <Route path="/cost-quotes/quotes/:id/cost" element={<QuoteCostManagement />} />
      <Route path="/cost-quotes/material-costs" element={<PurchaseMaterialCostManagement />} />
      <Route path="/cost-quotes/financial-costs" element={<FinancialCostUpload />} />
      <Route path="/cost-quotes/templates" element={<SalesTemplateCenter />} />
      <Route path="/sales/quotes" element={<QuoteManagement />} />
      <Route path="/sales/quotes/:id/cost" element={<QuoteCostManagement />} />
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
    </>
  );
}
