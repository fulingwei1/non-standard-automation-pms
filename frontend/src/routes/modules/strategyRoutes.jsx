import { Route, Navigate } from "react-router-dom";
import { StrategyProtectedRoute } from "../../components/common/ProtectedRoute";
import { lazyLoad } from "../lazyLoad";

const StrategyDashboard = lazyLoad(() => import("../../pages/Strategy"));
const StrategyMap = lazyLoad(() => import("../../pages/StrategyMap"));
const CSFList = lazyLoad(() => import("../../pages/CSFList"));
const KPIList = lazyLoad(() => import("../../pages/KPIList"));
const AnnualWorkList = lazyLoad(() => import("../../pages/AnnualWorkList"));
const Decomposition = lazyLoad(() => import("../../pages/Decomposition"));
const StrategyCalendar = lazyLoad(() => import("../../pages/StrategyCalendar"));
const YearComparison = lazyLoad(() => import("../../pages/YearComparison"));
const AIStrategyAssistant = lazyLoad(() => import("../../pages/AIStrategyAssistant"));
const TeamGeneration = lazyLoad(() => import("../../pages/TeamGeneration"));
const ExecutiveDashboard = lazyLoad(() => import("../../pages/executive-dashboard"));

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
