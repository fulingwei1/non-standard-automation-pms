import { lazy } from "react";
import { Route } from "react-router-dom";
import { WarehouseProtectedRoute } from "../../components/common/ProtectedRoute";

// ---- 懒加载页面组件（仓储模块） ----
const WarehouseWorkstation = lazy(() => import("../../pages/warehouse/WarehouseWorkstation"));
const InboundList = lazy(() => import("../../pages/warehouse/InboundList"));
const InboundNew = lazy(() => import("../../pages/warehouse/InboundNew"));
const InboundDetail = lazy(() => import("../../pages/warehouse/InboundDetail"));
const OutboundList = lazy(() => import("../../pages/warehouse/OutboundList"));
const OutboundNew = lazy(() => import("../../pages/warehouse/OutboundNew"));
const OutboundDetail = lazy(() => import("../../pages/warehouse/OutboundDetail"));
const InventoryList = lazy(() => import("../../pages/warehouse/InventoryList"));
const StockAlerts = lazy(() => import("../../pages/warehouse/StockAlerts"));
const StockCount = lazy(() => import("../../pages/warehouse/StockCount"));
const LocationManagement = lazy(() => import("../../pages/warehouse/LocationManagement"));
const TimeBasedKitRateBoard = lazy(() => import("../../pages/TimeBasedKitRateBoard"));

export function WarehouseRoutes() {
  return (
    <>
      {/* 仓储工作台首页 */}
      <Route
        path="/workstation/warehouse"
        element={
          <WarehouseProtectedRoute>
            <WarehouseWorkstation />
          </WarehouseProtectedRoute>
        }
      />

      {/* 入库管理 */}
      <Route
        path="/warehouse/inbound"
        element={
          <WarehouseProtectedRoute>
            <InboundList />
          </WarehouseProtectedRoute>
        }
      />
      <Route
        path="/warehouse/inbound/new"
        element={
          <WarehouseProtectedRoute>
            <InboundNew />
          </WarehouseProtectedRoute>
        }
      />
      <Route
        path="/warehouse/inbound/:id"
        element={
          <WarehouseProtectedRoute>
            <InboundDetail />
          </WarehouseProtectedRoute>
        }
      />

      {/* 出库管理 */}
      <Route
        path="/warehouse/outbound"
        element={
          <WarehouseProtectedRoute>
            <OutboundList />
          </WarehouseProtectedRoute>
        }
      />
      <Route
        path="/warehouse/outbound/new"
        element={
          <WarehouseProtectedRoute>
            <OutboundNew />
          </WarehouseProtectedRoute>
        }
      />
      <Route
        path="/warehouse/outbound/:id"
        element={
          <WarehouseProtectedRoute>
            <OutboundDetail />
          </WarehouseProtectedRoute>
        }
      />

      {/* 库存管理 */}
      <Route
        path="/warehouse/inventory"
        element={
          <WarehouseProtectedRoute>
            <InventoryList />
          </WarehouseProtectedRoute>
        }
      />

      {/* 库存预警 */}
      <Route
        path="/warehouse/alerts"
        element={
          <WarehouseProtectedRoute>
            <StockAlerts />
          </WarehouseProtectedRoute>
        }
      />

      {/* 盘点管理 */}
      <Route
        path="/warehouse/count"
        element={
          <WarehouseProtectedRoute>
            <StockCount />
          </WarehouseProtectedRoute>
        }
      />

      {/* 库位管理 */}
      <Route
        path="/warehouse/locations"
        element={
          <WarehouseProtectedRoute>
            <LocationManagement />
          </WarehouseProtectedRoute>
        }
      />

      {/* 基于时间的齐套率预警看板 */}
      <Route
        path="/warehouse/projects/:projectId/time-based-kit-rate"
        element={
          <WarehouseProtectedRoute>
            <TimeBasedKitRateBoard />
          </WarehouseProtectedRoute>
        }
      />
    </>
  );
}
