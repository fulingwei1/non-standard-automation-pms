import { lazyLoad } from "../lazyLoad";

const CostAccounting = lazyLoad(() => import("../../pages/CostAccounting"));
const PaymentApproval = lazyLoad(() => import("../../pages/PaymentApproval"));
const ProjectSettlement = lazyLoad(() => import("../../pages/ProjectSettlement"));
const FinancialReports = lazyLoad(() => import("../../pages/FinancialReports"));
const CostCollection = lazyLoad(() => import("../../pages/CostCollection"));
const QuoteActualCompare = lazyLoad(() => import("../../pages/QuoteActualCompare"));
const CostVarianceAnalysis = lazyLoad(() => import("../../pages/CostVarianceAnalysis"));
const LaborCostDetail = lazyLoad(() => import("../../pages/LaborCostDetail"));
const MultiCurrency = lazyLoad(() => import("../../pages/MultiCurrency"));
const AnalyticsDashboard = lazyLoad(() => import("../../pages/AnalyticsDashboard"));
const FinanceCostCenter = lazyLoad(() => import("../../pages/FinanceCostCenter"));

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
