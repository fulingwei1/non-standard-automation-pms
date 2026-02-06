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

export function AppRoutes() {
  return (
    <Routes>
  {/* 根路径重定向到工作台 */}
  <Route path="/" element={<Navigate to="/dashboard" replace />} />
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
