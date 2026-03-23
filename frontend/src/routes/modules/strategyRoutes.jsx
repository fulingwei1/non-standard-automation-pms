/**
 * 战略管理模块路由配置
 */
import { lazy } from "react";
import { Route, Navigate } from "react-router-dom";
import { StrategyProtectedRoute } from "../../components/common/ProtectedRoute";

// ---- 懒加载页面组件（战略模块） ----
const StrategyDashboard = lazy(() => import("../../pages/Strategy"));
const ExecutiveDashboard = lazy(() => import("../../pages/executive-dashboard"));
const StrategyMap = lazy(() => import("../../pages/StrategyMap"));
const CSFList = lazy(() => import("../../pages/CSFList"));
const KPIList = lazy(() => import("../../pages/KPIList"));
const AnnualWorkList = lazy(() => import("../../pages/AnnualWorkList"));
const Decomposition = lazy(() => import("../../pages/Decomposition"));
const StrategyCalendar = lazy(() => import("../../pages/StrategyCalendar"));
const YearComparison = lazy(() => import("../../pages/YearComparison"));
const AIStrategyAssistant = lazy(() => import("../../pages/AIStrategyAssistant"));
const TeamGeneration = lazy(() => import("../../pages/TeamGeneration"));

export function StrategyRoutes() {
  return (
    <>
      {/* 战略分析（主页面） */}
      <Route
        path="/strategy/analysis"
        element={
          <StrategyProtectedRoute>
            <StrategyDashboard />
          </StrategyProtectedRoute>
        }
      />
      {/* 兼容旧链接：/strategy、/strategy/dashboard 重定向到战略分析 */}
      <Route path="/strategy" element={<Navigate to="/strategy/analysis" replace />} />
      <Route path="/strategy/dashboard" element={<Navigate to="/strategy/analysis" replace />} />

      {/* 决策驾驶舱 */}
      <Route
        path="/strategy/strategy-dashboard"
        element={
          <StrategyProtectedRoute>
            <ExecutiveDashboard />
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

      {/* 重点工作管理 */}
      <Route
        path="/strategy/annual-work"
        element={
          <StrategyProtectedRoute>
            <AnnualWorkList />
          </StrategyProtectedRoute>
        }
      />

      {/* 战略分解 */}
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
