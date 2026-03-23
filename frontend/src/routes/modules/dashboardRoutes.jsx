import { lazy } from "react";
import { Route, Navigate } from "react-router-dom";
import { AppProtectedRoute } from "../../components/common/AppProtectedRoute";

// ---- 懒加载页面组件（按需加载，减少初始 bundle 体积） ----
const UnifiedDashboard = lazy(() => import("../../pages/UnifiedDashboard"));
const ProductionBoard = lazy(() => import("../../pages/ProductionBoard"));
const AdminDashboard = lazy(() => import("../../pages/AdminDashboard"));
const ChairmanWorkstation = lazy(() => import("../../pages/ChairmanWorkstation"));
const AdministrativeApprovals = lazy(() => import("../../pages/AdministrativeApprovals"));
const AdministrativeExpenses = lazy(() => import("../../pages/AdministrativeExpenses"));
const OfficeSuppliesManagement = lazy(() => import("../../pages/OfficeSuppliesManagement"));
const VehicleManagement = lazy(() => import("../../pages/VehicleManagement"));
const FixedAssetsManagement = lazy(() => import("../../pages/FixedAssetsManagement"));
const OperationDashboard = lazy(() => import("../../pages/OperationDashboard"));
const KeyDecisions = lazy(() => import("../../pages/KeyDecisions"));
const ManagementRhythmDashboard = lazy(() => import("../../pages/ManagementRhythmDashboard"));
const MeetingMap = lazy(() => import("../../pages/MeetingMap"));
const StrategicMeetingManagement = lazy(() => import("../../pages/StrategicMeetingManagement"));
const StrategicMeetingDetail = lazy(() => import("../../pages/StrategicMeetingDetail"));
const MeetingReports = lazy(() => import("../../pages/MeetingReports"));
const CultureWall = lazy(() => import("../../pages/CultureWall"));
const Shipments = lazy(() => import("../../pages/Shipments"));
const DeliveryManagement = lazy(() => import("../../pages/DeliveryManagement"));
const Documents = lazy(() => import("../../pages/Documents"));

export function DashboardRoutes() {
  return (
    <>
      {/*
        ========== 新的工作台路由体系 ==========
        所有工作台都使用 UnifiedDashboard 组件
        通过用户角色自动显示对应内容
      */}
      {/* 管理工作台 */}
      <Route
        path="/workstation/management"
        element={
          <AppProtectedRoute>
            <UnifiedDashboard />
          </AppProtectedRoute>
        }
      />

      {/* 销售工作台 */}
      <Route
        path="/workstation/sales"
        element={
          <AppProtectedRoute>
            <UnifiedDashboard />
          </AppProtectedRoute>
        }
      />

      {/* 售前工作台 */}
      <Route
        path="/workstation/presales"
        element={
          <AppProtectedRoute>
            <UnifiedDashboard />
          </AppProtectedRoute>
        }
      />

      {/* 项目工作台 */}
      <Route
        path="/workstation/project"
        element={
          <AppProtectedRoute>
            <UnifiedDashboard />
          </AppProtectedRoute>
        }
      />

      {/* 工程技术工作台 */}
      <Route
        path="/workstation/engineering"
        element={
          <AppProtectedRoute>
            <UnifiedDashboard />
          </AppProtectedRoute>
        }
      />

      {/* 生产工作台 */}
      <Route
        path="/workstation/production"
        element={
          <AppProtectedRoute>
            <ProductionBoard />
          </AppProtectedRoute>
        }
      />

      {/* 采购工作台 */}
      <Route
        path="/workstation/procurement"
        element={
          <AppProtectedRoute>
            <UnifiedDashboard />
          </AppProtectedRoute>
        }
      />

      {/* 售后服务工作台 */}
      <Route
        path="/workstation/service"
        element={
          <AppProtectedRoute>
            <UnifiedDashboard />
          </AppProtectedRoute>
        }
      />

      {/*
        ========== 旧路由重定向 ==========
        为了向后兼容，旧的路由重定向到新的工作台
      */}
      <Route path="/dashboard" element={<Navigate to="/workstation/management" replace />} />
      <Route path="/workstation" element={<Navigate to="/workstation/management" replace />} />

      {/* 销售相关旧路由重定向 */}
      <Route path="/sales-dashboard" element={<Navigate to="/workstation/sales" replace />} />
      <Route path="/sales-director-dashboard" element={<Navigate to="/workstation/sales" replace />} />
      <Route path="/sales-manager-dashboard" element={<Navigate to="/workstation/sales" replace />} />

      {/* 售前相关旧路由重定向 */}
      <Route path="/business-support" element={<Navigate to="/presales/technical-solutions" replace />} />

      {/* 工程相关旧路由重定向 */}
      <Route path="/engineer-workstation" element={<Navigate to="/workstation/engineering" replace />} />

      {/* 生产相关旧路由重定向 */}
      <Route path="/production-dashboard" element={<Navigate to="/workstation/production" replace />} />
      <Route path="/manufacturing-director-dashboard" element={<Navigate to="/workstation/production" replace />} />
      <Route path="/production-manager-dashboard" element={<Navigate to="/workstation/production" replace />} />
      <Route path="/worker-workstation" element={<Navigate to="/workstation/production" replace />} />

      {/* 采购相关旧路由重定向 */}
      <Route path="/procurement-dashboard" element={<Navigate to="/workstation/procurement" replace />} />
      <Route path="/procurement-manager-dashboard" element={<Navigate to="/workstation/procurement" replace />} />

      {/* 售后服务相关旧路由重定向 */}
      <Route path="/customer-service-dashboard" element={<Navigate to="/workstation/service" replace />} />

      {/* 管理层旧路由重定向 */}
      <Route path="/chairman-dashboard" element={<Navigate to="/workstation/management" replace />} />
      <Route path="/gm-dashboard" element={<Navigate to="/workstation/management" replace />} />
      <Route path="/finance-manager-dashboard" element={<Navigate to="/workstation/management" replace />} />
      <Route path="/hr-manager-dashboard" element={<Navigate to="/workstation/management" replace />} />
      <Route path="/administrative-dashboard" element={<Navigate to="/workstation/management" replace />} />

      {/*
        ========== 其他独立页面路由 ==========
        不属于工作台系统的独立页面
      */}
      <Route path="/admin-dashboard" element={<AdminDashboard />} />
      <Route path="/chairman-workstation" element={<ChairmanWorkstation />} />
      <Route path="/administrative-approvals" element={<AdministrativeApprovals />} />
      <Route path="/administrative-expenses" element={<AdministrativeExpenses />} />
      <Route path="/office-supplies-management" element={<OfficeSuppliesManagement />} />
      <Route path="/vehicle-management" element={<VehicleManagement />} />
      <Route path="/fixed-assets-management" element={<FixedAssetsManagement />} />
      <Route path="/operation" element={<OperationDashboard />} />
      <Route path="/strategy-analysis" element={<Navigate to="/strategy/analysis" replace />} />
      <Route path="/key-decisions" element={<KeyDecisions />} />
      <Route
        path="/management-rhythm-dashboard"
        element={<ManagementRhythmDashboard />}
      />
      <Route path="/meeting-map" element={<MeetingMap />} />
      <Route
        path="/strategic-meetings"
        element={<StrategicMeetingManagement />}
      />
      <Route
        path="/strategic-meetings/:id"
        element={<StrategicMeetingDetail />}
      />
      <Route path="/meeting-reports" element={<MeetingReports />} />
      <Route path="/meeting-reports/:id" element={<MeetingReports />} />
      <Route path="/culture-wall" element={<CultureWall />} />
      <Route path="/shipments" element={<Shipments />} />
      <Route path="/pmc/delivery-plan" element={<DeliveryManagement />} />
      <Route path="/pmc/delivery-orders" element={<DeliveryManagement />} />
      <Route path="/pmc/delivery-orders/:id" element={<DeliveryManagement />} />
      <Route
        path="/pmc/delivery-orders/:id/edit"
        element={<DeliveryManagement />}
      />
      <Route path="/pmc/delivery-orders/new" element={<DeliveryManagement />} />
      <Route path="/documents" element={<Documents />} />
    </>
  );
}
