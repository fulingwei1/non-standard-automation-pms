import { Route } from "react-router-dom";
import { FinanceProtectedRoute } from "../../components/common/ProtectedRoute";

import FinanceManagerDashboard from "../../pages/FinanceManagerDashboard";
import CostAccounting from "../../pages/CostAccounting";
import PaymentApproval from "../../pages/PaymentApproval";
import ProjectSettlement from "../../pages/ProjectSettlement";
import FinancialReports from "../../pages/FinancialReports";
import ExecutiveDashboard from "../../pages/executive-dashboard";

export function FinanceRoutes() {
  return (
    <>
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
    </>
  );
}
