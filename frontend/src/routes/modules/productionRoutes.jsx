import { Route, Navigate } from "react-router-dom";

import WorkOrderManagement from "../../pages/WorkOrderManagement";
import WorkOrderDetail from "../../pages/WorkOrderDetail";
import DispatchManagement from "../../pages/DispatchManagement";
import InstallationDispatchManagement from "../../pages/InstallationDispatchManagement";
import ProductionPlanList from "../../pages/ProductionPlanList";
import ProductionBoard from "../../pages/ProductionBoard";
import WorkReportList from "../../pages/WorkReportList";
import MaterialRequisitionList from "../../pages/MaterialRequisitionList";
import MaterialRequisitionDetail from "../../pages/MaterialRequisitionDetail";
import ProductionExceptionList from "../../pages/ProductionExceptionList";
import WorkshopManagement from "../../pages/WorkshopManagement";
import WorkerManagement from "../../pages/WorkerManagement";
import OutsourcingOrderList from "../../pages/OutsourcingOrderList";
import OutsourcingOrderDetail from "../../pages/OutsourcingOrderDetail";
import AcceptanceOrderList from "../../pages/AcceptanceOrderList";
import AcceptanceExecution from "../../pages/AcceptanceExecution";
import AcceptanceTemplateManagement from "../../pages/AcceptanceTemplateManagement";
import ShortageManagementBoard from "../../pages/ShortageManagementBoard";
import ShortageReportList from "../../pages/ShortageReportList";
import ArrivalTrackingList from "../../pages/ArrivalTrackingList";
import WorkloadBoard from "../../pages/WorkloadBoard";
import WorkshopTaskBoard from "../../pages/WorkshopTaskBoard";

export function ProductionRoutes() {
  return (
    <>
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
      <Route
        path="/shortage-management-board"
        element={<ShortageManagementBoard />}
      />
      <Route path="/shortage-reports" element={<ShortageReportList />} />
      <Route path="/arrival-tracking" element={<ArrivalTrackingList />} />
      <Route path="/workload-board" element={<WorkloadBoard />} />
      <Route path="/workshops/:id/task-board" element={<WorkshopTaskBoard />} />
      <Route path="/production-board" element={<ProductionBoard />} />
    </>
  );
}
