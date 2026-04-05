import { Route, Navigate } from "react-router-dom";
import { lazyLoad } from "../lazyLoad";

const CapacityAnalysis = lazyLoad(() => import("../../pages/CapacityAnalysis"));
const WorkOrderManagement = lazyLoad(() => import("../../pages/WorkOrderManagement"));
const WorkOrderDetail = lazyLoad(() => import("../../pages/WorkOrderDetail"));
const DispatchManagement = lazyLoad(() => import("../../pages/DispatchManagement"));
const InstallationDispatchManagement = lazyLoad(() => import("../../pages/InstallationDispatchManagement"));
const ProductionPlanList = lazyLoad(() => import("../../pages/ProductionPlanList"));
const ProductionBoard = lazyLoad(() => import("../../pages/ProductionBoard"));
const WorkReportList = lazyLoad(() => import("../../pages/WorkReportList"));
const MaterialRequisitionList = lazyLoad(() => import("../../pages/MaterialRequisitionList"));
const MaterialRequisitionDetail = lazyLoad(() => import("../../pages/MaterialRequisitionDetail"));
const ProductionExceptionList = lazyLoad(() => import("../../pages/ProductionExceptionList"));
const WorkshopManagement = lazyLoad(() => import("../../pages/WorkshopManagement"));
const WorkerManagement = lazyLoad(() => import("../../pages/WorkerManagement"));
const OutsourcingOrderList = lazyLoad(() => import("../../pages/OutsourcingOrderList"));
const OutsourcingOrderDetail = lazyLoad(() => import("../../pages/OutsourcingOrderDetail"));
const AcceptanceOrderList = lazyLoad(() => import("../../pages/AcceptanceOrderList"));
const AcceptanceExecution = lazyLoad(() => import("../../pages/AcceptanceExecution"));
const AcceptanceTemplateManagement = lazyLoad(() => import("../../pages/AcceptanceTemplateManagement"));
const ShortageManagementBoard = lazyLoad(() => import("../../pages/ShortageManagementBoard"));
const ShortageReportList = lazyLoad(() => import("../../pages/ShortageReportList"));
const ArrivalTrackingList = lazyLoad(() => import("../../pages/ArrivalTrackingList"));
const WorkloadBoard = lazyLoad(() => import("../../pages/WorkloadBoard"));
const WorkshopTaskBoard = lazyLoad(() => import("../../pages/WorkshopTaskBoard"));
const AssemblyTemplateManagement = lazyLoad(() => import("../../pages/AssemblyTemplateManagement"));
const ScheduleOptimization = lazyLoad(() => import("../../pages/ScheduleOptimization"));
const ExceptionCenter = lazyLoad(() => import("../../pages/ExceptionCenter"));
const ProductionExecutionCenter = lazyLoad(() => import("../../pages/ProductionExecutionCenter"));
const AssemblyCenter = lazyLoad(() => import("../../pages/AssemblyCenter"));
const FieldResourceCenter = lazyLoad(() => import("../../pages/FieldResourceCenter"));

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
