import { Route } from "react-router-dom";
import { FinanceProtectedRoute } from "../../components/common/ProtectedRoute";

import CostAccounting from "../../pages/CostAccounting";
import PaymentApproval from "../../pages/PaymentApproval";
import ProjectSettlement from "../../pages/ProjectSettlement";
import FinancialReports from "../../pages/FinancialReports";
import ExecutiveDashboard from "../../pages/executive-dashboard";
import MarginPrediction from "../../pages/MarginPrediction";
import CostCollection from "../../pages/CostCollection";

export function FinanceRoutes() {
  return (
    <>
      <Route path="/costs" element={<CostAccounting />} />
      <Route path="/payment-approval" element={<PaymentApproval />} />
      <Route path="/settlement" element={<ProjectSettlement />} />
      <Route path="/financial-reports" element={<FinancialReports />} />
      <Route path="/margin-prediction" element={<MarginPrediction />} />
      <Route path="/cost-collection" element={<CostCollection />} />
      <Route path="/executive-dashboard" element={<ExecutiveDashboard />} />
    </>
  );
}
