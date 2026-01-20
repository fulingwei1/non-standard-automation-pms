import { Route } from "react-router-dom";
import {
  ProcurementProtectedRoute,
  ProductionProtectedRoute
} from "../../components/common/ProtectedRoute";

import ProcurementEngineerWorkstation from "../../pages/ProcurementEngineerWorkstation";
import ProcurementManagerDashboard from "../../pages/ProcurementManagerDashboard";
import PurchaseOrders from "../../pages/PurchaseOrders";
import PurchaseOrderDetail from "../../pages/PurchaseOrderDetail";
import PurchaseRequestList from "../../pages/PurchaseRequestList";
import PurchaseRequestNew from "../../pages/PurchaseRequestNew";
import PurchaseRequestDetail from "../../pages/PurchaseRequestDetail";
import PurchaseOrderFromBOM from "../../pages/PurchaseOrderFromBOM";
import GoodsReceiptNew from "../../pages/GoodsReceiptNew";
import GoodsReceiptDetail from "../../pages/GoodsReceiptDetail";
import MaterialList from "../../pages/MaterialList";
import MaterialTracking from "../../pages/MaterialTracking";
import MaterialReadiness from "../../pages/MaterialReadiness";
import ProcurementAnalysis from "../../pages/ProcurementAnalysis";
import InventoryAnalysis from "../../pages/InventoryAnalysis";
import BudgetManagement from "../../pages/BudgetManagement";
import CostAnalysis from "../../pages/CostAnalysis";
import MaterialDemandSummary from "../../pages/MaterialDemandSummary";
import BOMManagement from "../../pages/BOMManagement";
import KitRateBoard from "../../pages/KitRateBoard";
import KitCheck from "../../pages/KitCheck";
import MaterialAnalysis from "../../pages/MaterialAnalysis";
import AssemblyKitBoard from "../../pages/AssemblyKitBoard";
import BomAssemblyAttrs from "../../pages/BomAssemblyAttrs";
import ArrivalManagement from "../../pages/ArrivalManagement";
import SupplierManagement from "../../pages/SupplierManagement";
import ShortageManagement from "../../pages/ShortageManagement";
import ShortageReportNew from "../../pages/ShortageReportNew";
import ShortageReportDetail from "../../pages/ShortageReportDetail";
import ArrivalDetail from "../../pages/ArrivalDetail";
import SubstitutionDetail from "../../pages/SubstitutionDetail";
import TransferDetail from "../../pages/TransferDetail";
import SubstitutionNew from "../../pages/SubstitutionNew";
import TransferNew from "../../pages/TransferNew";
import ArrivalNew from "../../pages/ArrivalNew";

export function ProcurementRoutes() {
  return (
    <>
      <Route
        path="/procurement-manager-dashboard"
        element={<ProcurementManagerDashboard />}
      />
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
        path="/kit-check"
        element={
          <ProcurementProtectedRoute>
            <KitCheck />
          </ProcurementProtectedRoute>
        }
      />
      <Route
        path="/material-analysis"
        element={
          <ProcurementProtectedRoute>
            <MaterialAnalysis />
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
    </>
  );
}
