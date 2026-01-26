/**
 * 战略仪表板 Hook
 * 管理战略总览页面的状态和数据
 */
import { useState, useEffect, useCallback, useMemo } from "react";
import { message } from "antd";
import {
  strategyApi,
  dashboardApi,
  reviewApi,
  comparisonApi,
} from "../../../services/api";

export function useStrategyDashboard() {
  // ============================================
  // 状态定义
  // ============================================
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [activeStrategy, setActiveStrategy] = useState(null);
  const [strategies, setStrategies] = useState([]);
  const [overview, setOverview] = useState(null);
  const [health, setHealth] = useState(null);
  const [executionStatus, setExecutionStatus] = useState(null);
  const [myStrategy, setMyStrategy] = useState(null);
  const [quickStats, setQuickStats] = useState(null);
  const [multiYearTrend, setMultiYearTrend] = useState(null);
  const [selectedStrategyId, setSelectedStrategyId] = useState(null);
  const [activeTab, setActiveTab] = useState("overview");

  // ============================================
  // 数据加载
  // ============================================

  // 加载战略列表
  const loadStrategies = useCallback(async () => {
    try {
      const response = await strategyApi.list({ limit: 10 });
      setStrategies(response.data?.items || []);
    } catch (error) {
      console.error("加载战略列表失败:", error);
    }
  }, []);

  // 加载当前生效战略
  const loadActiveStrategy = useCallback(async () => {
    try {
      const response = await strategyApi.getActive();
      const strategy = response.data;
      setActiveStrategy(strategy);
      setSelectedStrategyId(strategy?.id);
      return strategy;
    } catch (error) {
      console.error("加载生效战略失败:", error);
      return null;
    }
  }, []);

  // 加载战略概览
  const loadOverview = useCallback(async (strategyId) => {
    if (!strategyId) return;
    try {
      const response = await dashboardApi.getOverview(strategyId);
      setOverview(response.data);
    } catch (error) {
      console.error("加载战略概览失败:", error);
    }
  }, []);

  // 加载健康度数据
  const loadHealth = useCallback(async (strategyId) => {
    if (!strategyId) return;
    try {
      const response = await reviewApi.getHealth(strategyId);
      setHealth(response.data);
    } catch (error) {
      console.error("加载健康度失败:", error);
    }
  }, []);

  // 加载执行状态
  const loadExecutionStatus = useCallback(async (strategyId) => {
    if (!strategyId) return;
    try {
      const response = await dashboardApi.getExecutionStatus(strategyId);
      setExecutionStatus(response.data);
    } catch (error) {
      console.error("加载执行状态失败:", error);
    }
  }, []);

  // 加载我的战略
  const loadMyStrategy = useCallback(async () => {
    try {
      const response = await dashboardApi.getMyStrategy();
      setMyStrategy(response.data);
    } catch (error) {
      console.error("加载我的战略失败:", error);
    }
  }, []);

  // 加载快速统计
  const loadQuickStats = useCallback(async () => {
    try {
      const response = await dashboardApi.getQuickStats();
      setQuickStats(response.data);
    } catch (error) {
      console.error("加载快速统计失败:", error);
    }
  }, []);

  // 加载多年趋势
  const loadMultiYearTrend = useCallback(async () => {
    try {
      const response = await comparisonApi.getMultiYearTrend(3);
      setMultiYearTrend(response.data);
    } catch (error) {
      console.error("加载多年趋势失败:", error);
    }
  }, []);

  // 加载所有数据
  const loadAllData = useCallback(async () => {
    setLoading(true);
    try {
      // 先加载战略列表和活跃战略
      await loadStrategies();
      const strategy = await loadActiveStrategy();
      await loadQuickStats();
      await loadMyStrategy();
      await loadMultiYearTrend();

      // 如果有活跃战略，加载详细数据
      if (strategy?.id) {
        await Promise.all([
          loadOverview(strategy.id),
          loadHealth(strategy.id),
          loadExecutionStatus(strategy.id),
        ]);
      }
    } catch (error) {
      console.error("加载数据失败:", error);
      message.error("加载数据失败");
    } finally {
      setLoading(false);
    }
  }, [
    loadStrategies,
    loadActiveStrategy,
    loadQuickStats,
    loadMyStrategy,
    loadMultiYearTrend,
    loadOverview,
    loadHealth,
    loadExecutionStatus,
  ]);

  // 刷新数据
  const refresh = useCallback(async () => {
    setRefreshing(true);
    try {
      if (selectedStrategyId) {
        await Promise.all([
          loadOverview(selectedStrategyId),
          loadHealth(selectedStrategyId),
          loadExecutionStatus(selectedStrategyId),
        ]);
      }
      await loadQuickStats();
      await loadMyStrategy();
      message.success("数据已刷新");
    } catch (_error) {
      message.error("刷新失败");
    } finally {
      setRefreshing(false);
    }
  }, [
    selectedStrategyId,
    loadOverview,
    loadHealth,
    loadExecutionStatus,
    loadQuickStats,
    loadMyStrategy,
  ]);

  // 切换战略
  const handleStrategyChange = useCallback(
    async (strategyId) => {
      setSelectedStrategyId(strategyId);
      setLoading(true);
      try {
        await Promise.all([
          loadOverview(strategyId),
          loadHealth(strategyId),
          loadExecutionStatus(strategyId),
        ]);
      } finally {
        setLoading(false);
      }
    },
    [loadOverview, loadHealth, loadExecutionStatus]
  );

  // ============================================
  // 计算属性
  // ============================================

  // 健康度统计
  const healthStats = useMemo(() => {
    if (!health?.dimensions) return null;

    const dimensions = health.dimensions;
    const avgScore = health.overall_score;

    return {
      overall: {
        score: avgScore,
        level: health.overall_level,
      },
      dimensions: dimensions.map((d) => ({
        dimension: d.dimension,
        name: d.dimension_name,
        score: d.score,
        level: d.level,
        kpiCount: d.kpi_count,
        csfCount: d.csf_count,
        kpiOnTrack: d.kpi_on_track,
        kpiAtRisk: d.kpi_at_risk,
        kpiOffTrack: d.kpi_off_track,
      })),
      trend: health.trend || [],
    };
  }, [health]);

  // 执行状态统计
  const executionStats = useMemo(() => {
    if (!executionStatus?.items) return null;

    const items = executionStatus.items;
    let totalKpi = 0;
    let totalOnTrack = 0;
    let totalAtRisk = 0;
    let totalOffTrack = 0;
    let totalWork = 0;
    let totalCompleted = 0;

    items.forEach((item) => {
      totalKpi += item.kpi_total || 0;
      totalOnTrack += item.kpi_on_track || 0;
      totalAtRisk += item.kpi_at_risk || 0;
      totalOffTrack += item.kpi_off_track || 0;
      totalWork += item.work_total || 0;
      totalCompleted += item.work_completed || 0;
    });

    return {
      kpi: {
        total: totalKpi,
        onTrack: totalOnTrack,
        atRisk: totalAtRisk,
        offTrack: totalOffTrack,
        onTrackRate: totalKpi > 0 ? (totalOnTrack / totalKpi) * 100 : 0,
      },
      work: {
        total: totalWork,
        completed: totalCompleted,
        completionRate: totalWork > 0 ? (totalCompleted / totalWork) * 100 : 0,
      },
      byDimension: items,
    };
  }, [executionStatus]);

  // 我的任务统计
  const myStats = useMemo(() => {
    if (!myStrategy) return null;

    return {
      kpiCount: myStrategy.my_kpis?.length || 0,
      workCount: myStrategy.my_annual_works?.length || 0,
      personalKpiCount: myStrategy.my_personal_kpis?.length || 0,
      totalKpi: myStrategy.total_kpi_count || 0,
      completedKpi: myStrategy.completed_kpi_count || 0,
    };
  }, [myStrategy]);

  // ============================================
  // 初始化
  // ============================================

  useEffect(() => {
    loadAllData();
  }, [loadAllData]);

  // ============================================
  // 返回接口
  // ============================================

  return {
    // 状态
    loading,
    refreshing,
    activeTab,
    setActiveTab,
    selectedStrategyId,

    // 数据
    activeStrategy,
    strategies,
    overview,
    health,
    executionStatus,
    myStrategy,
    quickStats,
    multiYearTrend,

    // 计算属性
    healthStats,
    executionStats,
    myStats,

    // 操作
    refresh,
    handleStrategyChange,
  };
}
