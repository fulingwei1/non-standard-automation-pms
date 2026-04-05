import { Navigate, Route } from "react-router-dom";
import {
  ProcurementProtectedRoute,
  ProductionProtectedRoute
} from "../../components/common/ProtectedRoute";
import { lazyLoad } from "../lazyLoad";

const PurchaseOrders = lazyLoad(() => import("../../pages/PurchaseOrders"));
const PurchaseOrderDetail = lazyLoad(() => import("../../pages/PurchaseOrderDetail"));
const PurchaseRequestList = lazyLoad(() => import("../../pages/PurchaseRequestList"));
const PurchaseRequestNew = lazyLoad(() => import("../../pages/PurchaseRequestNew"));
const PurchaseRequestDetail = lazyLoad(() => import("../../pages/PurchaseRequestDetail"));
const PurchaseOrderFromBOM = lazyLoad(() => import("../../pages/PurchaseOrderFromBOM"));
const GoodsReceiptNew = lazyLoad(() => import("../../pages/GoodsReceiptNew"));
const GoodsReceiptDetail = lazyLoad(() => import("../../pages/GoodsReceiptDetail"));
const MaterialList = lazyLoad(() => import("../../pages/MaterialList"));
const MaterialTracking = lazyLoad(() => import("../../pages/MaterialTracking"));
const MaterialReadiness = lazyLoad(() => import("../../pages/MaterialReadiness"));
const ProcurementAnalysis = lazyLoad(() => import("../../pages/ProcurementAnalysis"));
const InventoryAnalysis = lazyLoad(() => import("../../pages/InventoryAnalysis"));
const BudgetManagement = lazyLoad(() => import("../../pages/BudgetManagement"));
const CostAnalysis = lazyLoad(() => import("../../pages/CostAnalysis"));
const MaterialDemandSummary = lazyLoad(() => import("../../pages/MaterialDemandSummary"));
const BOMManagement = lazyLoad(() => import("../../pages/BOMManagement"));
const KitRateBoard = lazyLoad(() => import("../../pages/KitRateBoard"));
const KitCheck = lazyLoad(() => import("../../pages/KitCheck"));
const MaterialAnalysis = lazyLoad(() => import("../../pages/MaterialAnalysis"));
const AssemblyKitBoard = lazyLoad(() => import("../../pages/AssemblyKitBoard"));
const BomAssemblyAttrs = lazyLoad(() => import("../../pages/BomAssemblyAttrs"));
const ArrivalManagement = lazyLoad(() => import("../../pages/ArrivalManagement"));
const SupplierManagement = lazyLoad(() => import("../../pages/SupplierManagement"));
const ShortageManagement = lazyLoad(() => import("../../pages/ShortageManagement"));
const ShortageReportNew = lazyLoad(() => import("../../pages/ShortageReportNew"));
const ShortageReportDetail = lazyLoad(() => import("../../pages/ShortageReportDetail"));
const ArrivalDetail = lazyLoad(() => import("../../pages/ArrivalDetail"));
const SubstitutionDetail = lazyLoad(() => import("../../pages/SubstitutionDetail"));
const TransferDetail = lazyLoad(() => import("../../pages/TransferDetail"));
const SubstitutionNew = lazyLoad(() => import("../../pages/SubstitutionNew"));
const TransferNew = lazyLoad(() => import("../../pages/TransferNew"));
const ArrivalNew = lazyLoad(() => import("../../pages/ArrivalNew"));
const SupplierPriceTrend = lazyLoad(() => import("../../pages/SupplierPriceTrend"));
const TimeBasedKitRateBoard = lazyLoad(() => import("../../pages/TimeBasedKitRateBoard"));
const ProcurementExecutionCenter = lazyLoad(() => import("../../pages/ProcurementExecutionCenter"));
const MaterialCenter = lazyLoad(() => import("../../pages/MaterialCenter"));
const ProcurementAnalysisCenter = lazyLoad(() => import("../../pages/ProcurementAnalysisCenter"));

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
