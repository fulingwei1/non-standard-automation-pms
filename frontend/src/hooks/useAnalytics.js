/**
 * useAnalytics.js
 *
 * 分析仪表盘数据层 Hook
 * 从后端 API 获取 KPI、图表数据、实时动态等
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import { workloadAnalyticsApi } from '../services/api/analytics';
import { projectApi } from '../services/api/projects';

// ============================================
// Data Transformation Utilities
// ============================================

/**
 * 将宽格式数据转换为长格式（适用于 LineChart）
 */
export const transformToLongFormat = (data, dateField = 'date') => {
  const result = [];
  data.forEach(item => {
    Object.keys(item).forEach(key => {
      if (key !== dateField) {
        result.push({
          [dateField]: item[dateField],
          category: key,
          value: item[key]
        });
      }
    });
  });
  return result;
};

/**
 * 计算总计值
 */
export const calculateTotal = (data, valueKey = 'value') => {
  return data.reduce((sum, item) => sum + (item[valueKey] || 0), 0);
};

// ============================================
// Fallback mock generators (used when API fails)
// ============================================

const generateFallbackKPIs = () => [
  { id: 'active_projects', label: '进行中项目', value: '--', change: '--', trend: 'up', icon: 'Folder' },
  { id: 'completed_month', label: '本月完成', value: '--', change: '--', trend: 'up', icon: 'CheckCircle' },
  { id: 'pending_tickets', label: '待处理工单', value: '--', change: '--', trend: 'up', icon: 'AlertCircle' },
  { id: 'equipment_utilization', label: '设备利用率', value: '--', change: '--', trend: 'up', icon: 'Activity' },
];

// ============================================
// Custom Hook: useAnalytics
// ============================================

export function useAnalytics(options = {}) {
  const {
    refreshInterval = 30000,
    autoFetch = true
  } = options;

  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  const [kpis, setKpis] = useState([]);
  const [projectTrend, setProjectTrend] = useState([]);
  const [statusDistribution, setStatusDistribution] = useState([]);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [resourceData, setResourceData] = useState([]);
  const [activities, setActivities] = useState([]);

  const intervalRef = useRef(null);

  /**
   * 从后端 API 获取仪表盘数据
   */
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // 并行请求多个 API
      const [projectStatsRes, workloadRes, bottlenecksRes] = await Promise.allSettled([
        projectApi.getStats(),
        workloadAnalyticsApi.overview(),
        workloadAnalyticsApi.bottlenecks(),
      ]);

      // --- KPIs ---
      const projectStats = projectStatsRes.status === 'fulfilled'
        ? (projectStatsRes.value?.data || projectStatsRes.value || {})
        : {};

      const workloadData = workloadRes.status === 'fulfilled'
        ? (workloadRes.value?.data || workloadRes.value || {})
        : {};

      const kpiList = [
        {
          id: 'active_projects',
          label: '进行中项目',
          value: projectStats.active_count ?? projectStats.in_progress ?? '--',
          change: projectStats.active_change ?? '',
          trend: 'up',
          icon: 'Folder'
        },
        {
          id: 'completed_month',
          label: '本月完成',
          value: projectStats.completed_this_month ?? projectStats.completed_count ?? '--',
          change: projectStats.completed_change ?? '',
          trend: 'up',
          icon: 'CheckCircle'
        },
        {
          id: 'pending_tickets',
          label: '待处理工单',
          value: projectStats.pending_tickets ?? projectStats.overdue_count ?? '--',
          change: projectStats.tickets_change ?? '',
          trend: (projectStats.pending_tickets ?? 0) > 10 ? 'down' : 'up',
          icon: 'AlertCircle'
        },
        {
          id: 'equipment_utilization',
          label: '设备利用率',
          value: workloadData.average_utilization
            ? `${Math.round(workloadData.average_utilization)}%`
            : (projectStats.utilization ?? '--'),
          change: workloadData.utilization_change ?? '',
          trend: 'up',
          icon: 'Activity'
        }
      ];
      setKpis(kpiList);

      // --- Project Trend (月度趋势) ---
      const trendData = projectStats.monthly_trend || projectStats.trends || [];
      if (trendData.length > 0) {
        setProjectTrend(trendData.map(item => ({
          date: item.month || item.date || item.period,
          完成: item.completed ?? item.closed ?? 0,
          进行中: item.active ?? item.in_progress ?? 0
        })));
      }

      // --- Status Distribution ---
      const stages = projectStats.stage_distribution || projectStats.status_distribution || [];
      const stageColors = ['#8b5cf6', '#3b82f6', '#10b981', '#f59e0b', '#6366f1', '#ef4444'];
      if (stages.length > 0) {
        setStatusDistribution(stages.map((item, idx) => ({
          name: item.name || item.stage || item.status,
          value: item.count ?? item.value ?? 0,
          color: item.color || stageColors[idx % stageColors.length]
        })));
      }

      // --- Monthly Stats (立项/结项) ---
      const monthly = projectStats.monthly_stats || [];
      if (monthly.length > 0) {
        setMonthlyStats(monthly.map(item => ({
          name: item.name || item.month,
          new: item.new ?? item.created ?? 0,
          completed: item.completed ?? item.closed ?? 0
        })));
      }

      // --- Resource Data (from workload API) ---
      const deptStats = workloadData.department_stats || workloadData.departments || [];
      if (deptStats.length > 0) {
        // Group by period or use department breakdown
        const resourceByPeriod = {};
        deptStats.forEach(dept => {
          const periods = dept.periods || [{ name: dept.department_name || dept.name, mechanical: dept.mechanical_load, electrical: dept.electrical_load }];
          periods.forEach(p => {
            const key = p.name || p.period;
            if (!resourceByPeriod[key]) {
              resourceByPeriod[key] = { name: key, mechanical: 0, electrical: 0 };
            }
            resourceByPeriod[key].mechanical += p.mechanical ?? p.mechanical_load ?? dept.avg_allocation ?? 0;
            resourceByPeriod[key].electrical += p.electrical ?? p.electrical_load ?? 0;
          });
        });
        setResourceData(Object.values(resourceByPeriod));
      }

      // --- Activities (from bottlenecks or recent project events) ---
      const bottlenecks = bottlenecksRes.status === 'fulfilled'
        ? (bottlenecksRes.value?.data?.items || bottlenecksRes.value?.data || [])
        : [];

      if (bottlenecks.length > 0) {
        setActivities(bottlenecks.slice(0, 6).map((item, idx) => ({
          id: item.id || `activity-${idx}`,
          type: item.severity === 'HIGH' ? 'alert' : item.severity === 'LOW' ? 'success' : 'info',
          message: item.message || item.description || `${item.employee_name || '资源'} - ${item.conflict_type || '负载异常'}`,
          time: item.created_at ? new Date(item.created_at).toLocaleString('zh-CN', { hour: '2-digit', minute: '2-digit' }) : '',
          timestamp: item.created_at ? new Date(item.created_at).getTime() : Date.now() - idx * 60000
        })));
      }

      setLastUpdated(new Date());
    } catch (err) {
      console.error('Analytics fetch error:', err);
      setError(err.message || '数据加载失败');
      // Set fallback KPIs so UI doesn't break
      if (kpis.length === 0) {
        setKpis(generateFallbackKPIs());
      }
    } finally {
      setLoading(false);
    }
  }, []);

  const refresh = useCallback(() => fetchData(), [fetchData]);

  // Auto-fetch on mount
  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, [autoFetch, fetchData]);

  // Polling
  useEffect(() => {
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(fetchData, refreshInterval);
      return () => {
        if (intervalRef.current) clearInterval(intervalRef.current);
      };
    }
  }, [refreshInterval, fetchData]);

  const totalProjects = calculateTotal(statusDistribution, 'value');
  const lineChartData = transformToLongFormat(projectTrend, 'date');

  return {
    kpis,
    projectTrend,
    statusDistribution,
    monthlyStats,
    resourceData,
    activities,
    lineChartData,
    totalProjects,
    loading,
    error,
    lastUpdated,
    refresh,
    refreshActivities: refresh,
  };
}

export default useAnalytics;
