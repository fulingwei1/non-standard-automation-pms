import { lazy } from "react";
import { Route, Navigate } from "react-router-dom";
import {
  ProcurementProtectedRoute,
  ProductionProtectedRoute,
} from "../../components/common/ProtectedRoute";

// ---- 懒加载页面组件（采购模块） ----
const ProcurementExecutionCenter = lazy(() => import("../../pages/ProcurementExecutionCenter"));
const MaterialCenter = lazy(() => import("../../pages/MaterialCenter"));
const ProcurementAnalysisCenter = lazy(() => import("../../pages/ProcurementAnalysisCenter"));
const PurchaseOrders = lazy(() => import("../../pages/PurchaseOrders"));
const PurchaseOrderDetail = lazy(() => import("../../pages/PurchaseOrderDetail"));
const PurchaseRequestList = lazy(() => import("../../pages/PurchaseRequestList"));
const PurchaseRequestNew = lazy(() => import("../../pages/PurchaseRequestNew"));
const PurchaseRequestDetail = lazy(() => import("../../pages/PurchaseRequestDetail"));
const PurchaseOrderFromBOM = lazy(() => import("../../pages/PurchaseOrderFromBOM"));
const ArrivalManagement = lazy(() => import("../../pages/ArrivalManagement"));
const GoodsReceiptNew = lazy(() => import("../../pages/GoodsReceiptNew"));
const GoodsReceiptDetail = lazy(() => import("../../pages/GoodsReceiptDetail"));
const MaterialList = lazy(() => import("../../pages/MaterialList"));
const MaterialTracking = lazy(() => import("../../pages/MaterialTracking"));
const MaterialReadiness = lazy(() => import("../../pages/MaterialReadiness"));
const ProcurementAnalysis = lazy(() => import("../../pages/ProcurementAnalysis"));
const InventoryAnalysis = lazy(() => import("../../pages/InventoryAnalysis"));
const BudgetManagement = lazy(() => import("../../pages/BudgetManagement"));
const CostAnalysis = lazy(() => import("../../pages/CostAnalysis"));
const MaterialDemandSummary = lazy(() => import("../../pages/MaterialDemandSummary"));
const BOMManagement = lazy(() => import("../../pages/BOMManagement"));
const KitRateBoard = lazy(() => import("../../pages/KitRateBoard"));
const TimeBasedKitRateBoard = lazy(() => import("../../pages/TimeBasedKitRateBoard"));
const KitCheck = lazy(() => import("../../pages/KitCheck"));
const MaterialAnalysis = lazy(() => import("../../pages/MaterialAnalysis"));
const AssemblyKitBoard = lazy(() => import("../../pages/AssemblyKitBoard"));
const BomAssemblyAttrs = lazy(() => import("../../pages/BomAssemblyAttrs"));
const SupplierManagement = lazy(() => import("../../pages/SupplierManagement"));
const SupplierPriceTrend = lazy(() => import("../../pages/SupplierPriceTrend"));
const ShortageManagement = lazy(() => import("../../pages/ShortageManagement"));
const ShortageReportNew = lazy(() => import("../../pages/ShortageReportNew"));
const ShortageReportDetail = lazy(() => import("../../pages/ShortageReportDetail"));
const ArrivalDetail = lazy(() => import("../../pages/ArrivalDetail"));
const SubstitutionDetail = lazy(() => import("../../pages/SubstitutionDetail"));
const TransferDetail = lazy(() => import("../../pages/TransferDetail"));
const SubstitutionNew = lazy(() => import("../../pages/SubstitutionNew"));
const TransferNew = lazy(() => import("../../pages/TransferNew"));
const ArrivalNew = lazy(() => import("../../pages/ArrivalNew"));

export function ProcurementRoutes() {
  return (
    <>
      <Route path="/procurement/execution-center" element={<ProcurementExecutionCenter />} />
      <Route path="/procurement/material-center" element={<MaterialCenter />} />
      <Route path="/procurement/analysis-center" element={<ProcurementAnalysisCenter />} />
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
        path="/projects/:projectId/time-based-kit-rate"
        element={
          <ProcurementProtectedRoute>
            <TimeBasedKitRateBoard />
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
        element={<Navigate to="/arrival-tracking" replace />}
      />
      <Route path="/suppliers" element={<SupplierManagement />} />
      <Route
        path="/supplier-price"
        element={
          <ProcurementProtectedRoute>
            <SupplierPriceTrend />
          </ProcurementProtectedRoute>
        }
      />
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
        path="/arrival-tracking/:id"
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
      <Route
        path="/arrival-tracking/new"
        element={
          <ProcurementProtectedRoute>
            <ArrivalNew />
          </ProcurementProtectedRoute>
        }
      />
    </>
  );
}
