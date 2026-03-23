import { lazy } from "react";
import { Route, Navigate } from "react-router-dom";

// ---- 懒加载页面组件（生产模块） ----
const ExceptionCenter = lazy(() => import("../../pages/ExceptionCenter"));
const ProductionExecutionCenter = lazy(() => import("../../pages/ProductionExecutionCenter"));
const AssemblyCenter = lazy(() => import("../../pages/AssemblyCenter"));
const FieldResourceCenter = lazy(() => import("../../pages/FieldResourceCenter"));
const WorkOrderManagement = lazy(() => import("../../pages/WorkOrderManagement"));
const WorkOrderDetail = lazy(() => import("../../pages/WorkOrderDetail"));
const DispatchManagement = lazy(() => import("../../pages/DispatchManagement"));
const InstallationDispatchManagement = lazy(() => import("../../pages/InstallationDispatchManagement"));
const ProductionPlanList = lazy(() => import("../../pages/ProductionPlanList"));
const WorkReportList = lazy(() => import("../../pages/WorkReportList"));
const MaterialRequisitionList = lazy(() => import("../../pages/MaterialRequisitionList"));
const MaterialRequisitionDetail = lazy(() => import("../../pages/MaterialRequisitionDetail"));
const ProductionExceptionList = lazy(() => import("../../pages/ProductionExceptionList"));
const WorkshopManagement = lazy(() => import("../../pages/WorkshopManagement"));
const WorkerManagement = lazy(() => import("../../pages/WorkerManagement"));
const OutsourcingOrderList = lazy(() => import("../../pages/OutsourcingOrderList"));
const OutsourcingOrderDetail = lazy(() => import("../../pages/OutsourcingOrderDetail"));
const AcceptanceOrderList = lazy(() => import("../../pages/AcceptanceOrderList"));
const AcceptanceExecution = lazy(() => import("../../pages/AcceptanceExecution"));
const AcceptanceTemplateManagement = lazy(() => import("../../pages/AcceptanceTemplateManagement"));
const ShortageManagementBoard = lazy(() => import("../../pages/ShortageManagementBoard"));
const ShortageReportList = lazy(() => import("../../pages/ShortageReportList"));
const ArrivalTrackingList = lazy(() => import("../../pages/ArrivalTrackingList"));
const WorkloadBoard = lazy(() => import("../../pages/WorkloadBoard"));
const WorkshopTaskBoard = lazy(() => import("../../pages/WorkshopTaskBoard"));
const ProductionBoard = lazy(() => import("../../pages/ProductionBoard"));
const AssemblyTemplateManagement = lazy(() => import("../../pages/AssemblyTemplateManagement"));
const ScheduleOptimization = lazy(() => import("../../pages/ScheduleOptimization"));
const CapacityAnalysis = lazy(() => import("../../pages/CapacityAnalysis"));

export function ProductionRoutes() {
  return (
    <>
      <Route path="/production/exception-center" element={<ExceptionCenter />} />
      <Route path="/production/execution-center" element={<ProductionExecutionCenter />} />
      <Route path="/production/assembly-center" element={<AssemblyCenter />} />
      <Route path="/production/resource-center" element={<FieldResourceCenter />} />
      <Route path="/work-orders" element={<WorkOrderManagement />} />
      <Route path="/work-orders/:id" element={<WorkOrderDetail />} />
      <Route path="/dispatch-management" element={<DispatchManagement />} />
      <Route
        path="/installation-dispatch"
        element={<InstallationDispatchManagement />}
      />
      <Route path="/production-plans" element={<ProductionPlanList />} />
      <Route path="/work-reports" element={<WorkReportList />} />
      <Route
        path="/material-requisitions"
        element={<MaterialRequisitionList />}
      />
      <Route
        path="/material-requisitions/:id"
        element={<MaterialRequisitionDetail />}
      />
      <Route
        path="/production-exceptions"
        element={<ProductionExceptionList />}
      />
      <Route path="/workshops" element={<WorkshopManagement />} />
      <Route path="/workers" element={<WorkerManagement />} />
      <Route path="/outsourcing-orders" element={<OutsourcingOrderList />} />
      <Route
        path="/outsourcing-orders/:id"
        element={<OutsourcingOrderDetail />}
      />
      <Route path="/acceptance-orders" element={<AcceptanceOrderList />} />
      <Route
        path="/acceptance-orders/:id/execute"
        element={<AcceptanceExecution />}
      />
      <Route
        path="/acceptance-templates"
        element={<AcceptanceTemplateManagement />}
      />
      <Route path="/shortage/dashboard" element={<ShortageManagementBoard />} />
      <Route
        path="/shortage-management-board"
        element={<Navigate to="/shortage/dashboard" replace />}
      />
      <Route path="/shortage-reports" element={<ShortageReportList />} />
      <Route path="/arrival-tracking" element={<ArrivalTrackingList />} />
      <Route path="/workload-board" element={<WorkloadBoard />} />
      <Route path="/workshops/:id/task-board" element={<WorkshopTaskBoard />} />
      <Route path="/production-board" element={<ProductionBoard />} />
      <Route
        path="/assembly-template-management"
        element={<AssemblyTemplateManagement />}
      />
      <Route
        path="/projects/:projectId/schedule-optimization"
        element={<ScheduleOptimization />}
      />
      <Route path="/production/capacity-analysis" element={<CapacityAnalysis />} />
    </>
  );
}
