import { Route, Navigate } from "react-router-dom";

import CostAccounting from "../../pages/CostAccounting";
import PaymentApproval from "../../pages/PaymentApproval";
import ProjectSettlement from "../../pages/ProjectSettlement";
import FinancialReports from "../../pages/FinancialReports";
import CostCollection from "../../pages/CostCollection";
import QuoteActualCompare from "../../pages/QuoteActualCompare";
import CostVarianceAnalysis from "../../pages/CostVarianceAnalysis";
import LaborCostDetail from "../../pages/LaborCostDetail";
import MultiCurrency from "../../pages/MultiCurrency";
import AnalyticsDashboard from "../../pages/AnalyticsDashboard";
import FinanceCostCenter from "../../pages/FinanceCostCenter";

export function FinanceRoutes() {
  return (
    <>
      <Route path="/finance/cost-center" element={<FinanceCostCenter />} />
      <Route path="/costs" element={<CostAccounting />} />
      <Route path="/payment-approval" element={<PaymentApproval />} />
      <Route path="/settlement" element={<ProjectSettlement />} />
      <Route path="/financial-reports" element={<FinancialReports />} />
      {/* 毛利率预测已整合到报价管理页面的毛利分析 Tab */}
      <Route path="/margin-prediction" element={<Navigate to="/cost-quotes/quotes" replace />} />
      <Route path="/cost-collection" element={<CostCollection />} />
      <Route path="/quote-compare" element={<QuoteActualCompare />} />
      <Route path="/cost-variance" element={<CostVarianceAnalysis />} />
      <Route path="/labor-cost" element={<LaborCostDetail />} />
      <Route path="/multi-currency" element={<MultiCurrency />} />
      <Route path="/executive-dashboard" element={<Navigate to="/strategy/strategy-dashboard" replace />} />
      <Route path="/finance/analytics-dashboard" element={<AnalyticsDashboard />} />
    </>
  );
}
