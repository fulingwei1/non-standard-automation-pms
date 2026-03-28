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
import AfterSalesCenter from '../pages/AfterSales/AfterSalesCenter';
import ProjectOverviewDashboard from '../pages/ProjectOverviewDashboard';
import ProjectDeliveryScheduleList from "../pages/ProjectDeliverySchedule/ScheduleList";
import ProjectDeliveryScheduleGantt from "../pages/ProjectDeliverySchedule/ScheduleGantt";
import ProjectDeliveryScheduleCreate from "../pages/ProjectDeliverySchedule/ScheduleCreate";
import ProjectDeliveryScheduleTaskFill from "../pages/ProjectDeliverySchedule/TaskFill";

export function AppRoutes() {
  return (
    <Routes>
      {/* 根路径重定向到工作台 */}
      <Route path="/" element={<Navigate to="/dashboard" replace />} />
      {/* 销售漏斗：显式声明确保优先匹配 */}
      <Route path="/sales/funnel" element={<SalesFunnel />} />
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
      {/* 项目总览 */}
      <Route path="/projects/:projectId/overview-dashboard" element={<ProjectOverviewDashboard />} />
      {/* 售后服务 */}
      <Route path="/projects/:projectId/after-sales" element={<AfterSalesCenter />} />
      {/* 项目交付排产计划 */}
      {/* 项目总览 */}
      <Route path="/projects/:projectId/overview-dashboard" element={<ProjectOverviewDashboard />} />
      {/* 售后服务 */}
      <Route path="/projects/:projectId/after-sales" element={<AfterSalesCenter />} />
      {/* 项目交付排产 - 项目子模块 */}
      <Route path="/projects/:projectId/delivery" element={<ProjectDeliveryScheduleGantt />} />
      <Route path="/projects/:projectId/delivery/create" element={<ProjectDeliveryScheduleCreate />} />
      <Route path="/projects/:projectId/delivery/task-fill/:department" element={<ProjectDeliveryScheduleTaskFill />} />
      {/* Catch-all route for unmatched paths */}
      <Route path="*" element={<Navigate to="/workstation/management" replace />} />
    </Routes>
  );
}
