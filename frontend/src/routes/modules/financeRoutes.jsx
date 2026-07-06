import { Route, Navigate } from "react-router-dom";
import { lazyLoad } from "../lazyLoad";
import { ModuleProtectedRoute } from "../../lib/permission";

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

const protect = (element, permission, moduleName) => (
  <ModuleProtectedRoute permission={permission} moduleName={moduleName}>
    {element}
  </ModuleProtectedRoute>
);

export function FinanceRoutes() {
  return (
    <>
      <Route
        path="/finance/cost-center"
        element={protect(<FinanceCostCenter />, "cost:accounting:read", "成本中心")}
      />
      <Route path="/costs" element={protect(<CostAccounting />, "cost:accounting:read", "成本核算")} />
      <Route path="/payment-approval" element={protect(<PaymentApproval />, "payment:approve", "付款审批")} />
      <Route path="/settlement" element={protect(<ProjectSettlement />, "settlement:read", "项目结算")} />
      <Route path="/financial-reports" element={protect(<FinancialReports />, "finance:report:read", "财务报表")} />
      {/* 毛利率预测已整合到报价管理页面的毛利分析 Tab */}
      <Route path="/margin-prediction" element={<Navigate to="/cost-quotes/quotes" replace />} />
      <Route path="/cost-collection" element={protect(<CostCollection />, "cost:accounting:read", "成本归集")} />
      <Route path="/quote-compare" element={protect(<QuoteActualCompare />, "cost:accounting:read", "报价成本对账")} />
      <Route path="/cost-variance" element={protect(<CostVarianceAnalysis />, "cost:accounting:read", "成本差异分析")} />
      <Route path="/labor-cost" element={protect(<LaborCostDetail />, "cost:accounting:read", "人工成本")} />
      <Route path="/multi-currency" element={protect(<MultiCurrency />, "finance:read", "多币种管理")} />
      <Route path="/executive-dashboard" element={<Navigate to="/strategy/strategy-dashboard" replace />} />
      <Route
        path="/finance/analytics-dashboard"
        element={protect(<AnalyticsDashboard />, "finance:report:read", "财务分析")}
      />
    </>
  );
}
