/**
 * 战略管理模块路由配置
 */
import { Route } from "react-router-dom";

import StrategyDashboard from "../../pages/Strategy";
import StrategyMap from "../../pages/StrategyMap";
import CSFList from "../../pages/CSFList";
import KPIList from "../../pages/KPIList";
import AnnualWorkList from "../../pages/AnnualWorkList";
import Decomposition from "../../pages/Decomposition";
import StrategyCalendar from "../../pages/StrategyCalendar";
import YearComparison from "../../pages/YearComparison";
import AIStrategyAssistant from "../../pages/AIStrategyAssistant";
import TeamGeneration from "../../pages/TeamGeneration";
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

      {/* 战略地图 */}
      <Route
        path="/strategy/map"
        element={
          <StrategyProtectedRoute>
            <StrategyMap />
          </StrategyProtectedRoute>
        }
      />

      {/* CSF 关键成功因素管理 */}
      <Route
        path="/strategy/csf"
        element={
          <StrategyProtectedRoute>
            <CSFList />
          </StrategyProtectedRoute>
        }
      />

      {/* KPI 指标管理 */}
      <Route
        path="/strategy/kpi"
        element={
          <StrategyProtectedRoute>
            <KPIList />
          </StrategyProtectedRoute>
        }
      />

      {/* 年度重点工作管理 */}
      <Route
        path="/strategy/annual-work"
        element={
          <StrategyProtectedRoute>
            <AnnualWorkList />
          </StrategyProtectedRoute>
        }
      />

      {/* 战略目标分解 */}
      <Route
        path="/strategy/decomposition"
        element={
          <StrategyProtectedRoute>
            <Decomposition />
          </StrategyProtectedRoute>
        }
      />

      {/* 战略日历 */}
      <Route
        path="/strategy/calendar"
        element={
          <StrategyProtectedRoute>
            <StrategyCalendar />
          </StrategyProtectedRoute>
        }
      />

      {/* 战略同比分析 */}
      <Route
        path="/strategy/comparison"
        element={
          <StrategyProtectedRoute>
            <YearComparison />
          </StrategyProtectedRoute>
        }
      />

      {/* AI战略辅助 */}
      <Route
        path="/strategy/ai-assistant"
        element={
          <StrategyProtectedRoute>
            <AIStrategyAssistant />
          </StrategyProtectedRoute>
        }
      />

      {/* AI自动组队 */}
      <Route
        path="/strategy/team-generation/:projectId"
        element={
          <StrategyProtectedRoute>
            <TeamGeneration />
          </StrategyProtectedRoute>
        }
      />
    </>
  );
}
