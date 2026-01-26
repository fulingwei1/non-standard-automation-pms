/**
 * 战略管理模块路由配置
 */
import { Route } from "react-router-dom";

import StrategyDashboard from "../../pages/Strategy";
import { StrategyProtectedRoute } from "../../components/common/ProtectedRoute";

export function StrategyRoutes() {
  return (
    <>
      {/* 战略仪表板 */}
      <Route
        path="/strategy"
        element={
          <StrategyProtectedRoute>
            <StrategyDashboard />
          </StrategyProtectedRoute>
        }
      />
      <Route
        path="/strategy/dashboard"
        element={
          <StrategyProtectedRoute>
            <StrategyDashboard />
          </StrategyProtectedRoute>
        }
      />

      {/* TODO: 后续添加更多战略模块路由 */}
      {/* <Route path="/strategy/map" element={<StrategyProtectedRoute><StrategyMap /></StrategyProtectedRoute>} /> */}
      {/* <Route path="/strategy/csf" element={<StrategyProtectedRoute><CSFList /></StrategyProtectedRoute>} /> */}
      {/* <Route path="/strategy/kpi" element={<StrategyProtectedRoute><KPIList /></StrategyProtectedRoute>} /> */}
      {/* <Route path="/strategy/annual-work" element={<StrategyProtectedRoute><AnnualWorkList /></StrategyProtectedRoute>} /> */}
      {/* <Route path="/strategy/decomposition" element={<StrategyProtectedRoute><Decomposition /></StrategyProtectedRoute>} /> */}
      {/* <Route path="/strategy/calendar" element={<StrategyProtectedRoute><StrategyCalendar /></StrategyProtectedRoute>} /> */}
      {/* <Route path="/strategy/comparison" element={<StrategyProtectedRoute><YearComparison /></StrategyProtectedRoute>} /> */}
    </>
  );
}
