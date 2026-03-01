import { Routes, Route, Navigate } from "react-router-dom";
import {
  DashboardRoutes,
  ProjectRoutes,
  SalesRoutes,
  ProcurementRoutes,
  ProductionRoutes,
  FinanceRoutes,
  HRRoutes,
  PresalesRoutes,
  PMORoutes,
  SystemRoutes,
  StrategyRoutes,
  WarehouseRoutes,
  QualityRoutes
} from "./modules";
import SalesFunnel from "../pages/SalesFunnel";
import PresaleAnalytics from "../pages/PresaleAnalytics";

export function AppRoutes() {
  return (
    <Routes>
      {/* 根路径重定向到工作台 */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      {/* 销售漏斗与销售分析：显式声明确保优先匹配，避免被 * 或其它路由抢占 */}
      <Route path="/sales/funnel" element={<SalesFunnel />} />
      <Route path="/sales/sales-analysis" element={<PresaleAnalytics />} />
      {DashboardRoutes()}
      {ProjectRoutes()}
      {SalesRoutes()}
      {ProcurementRoutes()}
      {ProductionRoutes()}
      {FinanceRoutes()}
      {HRRoutes()}
      {PresalesRoutes()}
      {PMORoutes()}
      {SystemRoutes()}
      {StrategyRoutes()}
      {WarehouseRoutes()}
      {QualityRoutes()}
      {/* Catch-all route for unmatched paths */}
      <Route path="*" element={<Navigate to="/workstation/management" replace />} />
    </Routes>
  );
}
