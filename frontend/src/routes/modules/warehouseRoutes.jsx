import { Route } from "react-router-dom";
import { WarehouseProtectedRoute } from "../../components/common/ProtectedRoute";

import WarehouseWorkstation from "../../pages/warehouse/WarehouseWorkstation";
import InboundList from "../../pages/warehouse/InboundList";
import InboundDetail from "../../pages/warehouse/InboundDetail";
import InboundNew from "../../pages/warehouse/InboundNew";
import OutboundList from "../../pages/warehouse/OutboundList";
import OutboundDetail from "../../pages/warehouse/OutboundDetail";
import OutboundNew from "../../pages/warehouse/OutboundNew";
import InventoryList from "../../pages/warehouse/InventoryList";
import StockAlerts from "../../pages/warehouse/StockAlerts";
import StockCount from "../../pages/warehouse/StockCount";
import LocationManagement from "../../pages/warehouse/LocationManagement";
import TimeBasedKitRateBoard from "../../pages/TimeBasedKitRateBoard";

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
