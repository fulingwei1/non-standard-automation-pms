import { lazyLoad } from "../lazyLoad";

const WarehouseWorkstation = lazyLoad(() => import("../../pages/warehouse/WarehouseWorkstation"));
const InboundList = lazyLoad(() => import("../../pages/warehouse/InboundList"));
const InboundDetail = lazyLoad(() => import("../../pages/warehouse/InboundDetail"));
const InboundNew = lazyLoad(() => import("../../pages/warehouse/InboundNew"));
const OutboundList = lazyLoad(() => import("../../pages/warehouse/OutboundList"));
const OutboundDetail = lazyLoad(() => import("../../pages/warehouse/OutboundDetail"));
const OutboundNew = lazyLoad(() => import("../../pages/warehouse/OutboundNew"));
const InventoryList = lazyLoad(() => import("../../pages/warehouse/InventoryList"));
const StockAlerts = lazyLoad(() => import("../../pages/warehouse/StockAlerts"));
const StockCount = lazyLoad(() => import("../../pages/warehouse/StockCount"));
const LocationManagement = lazyLoad(() => import("../../pages/warehouse/LocationManagement"));
const TimeBasedKitRateBoard = lazyLoad(() => import("../../pages/TimeBasedKitRateBoard"));

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
