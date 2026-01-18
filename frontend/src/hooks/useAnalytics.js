/**
 * useAnalytics.js
 * 
 * 分析仪表盘数据层 Hook
 * 提供 KPI、图表数据、实时动态等数据获取与状态管理
 * 
 * Features:
 * - 模拟 API 数据获取
 * - 自动定时刷新（polling）
 * - 加载/错误状态管理
 * - 数据转换工具函数
 */

import { useState, useEffect, useCallback, useRef } from 'react';

// ============================================
// Mock Data - 模拟后端 API 数据
// ============================================

const generateMockKPIs = () => [
  { 
    id: 'active_projects',
    label: '进行中项目', 
    value: Math.floor(20 + Math.random() * 10), 
    change: `${Math.floor(Math.random() * 20)}%`, 
    trend: Math.random() > 0.3 ? 'up' : 'down',
    icon: 'Folder'
  },
  { 
    id: 'completed_month',
    label: '本月完成', 
    value: Math.floor(5 + Math.random() * 8), 
    change: `${Math.floor(Math.random() * 30)}%`, 
    trend: Math.random() > 0.4 ? 'up' : 'down',
    icon: 'CheckCircle'
  },
  { 
    id: 'pending_tickets',
    label: '待处理工单', 
    value: Math.floor(10 + Math.random() * 15), 
    change: `${Math.floor(Math.random() * 15)}%`, 
    trend: Math.random() > 0.5 ? 'up' : 'down',
    icon: 'AlertCircle'
  },
  { 
    id: 'equipment_utilization',
    label: '设备利用率', 
    value: `${Math.floor(75 + Math.random() * 20)}%`, 
    change: `${Math.floor(Math.random() * 10)}%`, 
    trend: Math.random() > 0.4 ? 'up' : 'down',
    icon: 'Activity'
  }
];

const generateProjectTrendData = () => {
  const months = ['2024-08', '2024-09', '2024-10', '2024-11', '2024-12', '2025-01'];
  return months.map(date => ({
    date,
    完成: Math.floor(3 + Math.random() * 10),
    进行中: Math.floor(8 + Math.random() * 15)
  }));
};

const generateStatusDistribution = () => [
  { name: '方案设计', value: Math.floor(5 + Math.random() * 5), color: '#8b5cf6' },
  { name: '采购备料', value: Math.floor(4 + Math.random() * 5), color: '#3b82f6' },
  { name: '装配调试', value: Math.floor(3 + Math.random() * 5), color: '#10b981' },
  { name: '出厂验收', value: Math.floor(2 + Math.random() * 4), color: '#f59e0b' },
  { name: '现场交付', value: Math.floor(1 + Math.random() * 4), color: '#6366f1' },
];

const generateMonthlyStats = () => {
  const months = ['1月', '2月', '3月', '4月', '5月', '6月'];
  return months.map(name => ({
    name,
    new: Math.floor(2 + Math.random() * 6),
    completed: Math.floor(2 + Math.random() * 6)
  }));
};

const generateResourceData = () => {
  const weeks = ['W1', 'W2', 'W3', 'W4', 'W5'];
  return weeks.map(name => ({
    name,
    mechanical: Math.floor(50 + Math.random() * 40),
    electrical: Math.floor(40 + Math.random() * 50)
  }));
};

const ACTIVITY_TEMPLATES = [
  { type: 'project', template: '项目 PJ{id} 进入{stage}阶段' },
  { type: 'alert', template: '设备 PN{id} 物料延迟预警' },
  { type: 'success', template: '项目 PJ{id} 通过 FAT 验收' },
  { type: 'info', template: '新采购订单 PO-{date}-{seq} 已生成' },
  { type: 'project', template: '项目 PJ{id} 完成方案评审' },
  { type: 'alert', template: '项目 PJ{id} 进度延迟警告' },
  { type: 'success', template: '设备 PN{id} 调试完成' },
];

const STAGES = ['方案设计', '采购备料', '加工制造', '装配调试', '出厂验收', '现场安装'];

const generateActivity = (index) => {
  const template = ACTIVITY_TEMPLATES[Math.floor(Math.random() * ACTIVITY_TEMPLATES.length)];
  const now = new Date();
  const randomMinutes = Math.floor(Math.random() * 60 * 24);
  
  let message = template.template
    .replace('{id}', `25011${String(Math.floor(Math.random() * 100)).padStart(3, '0')}`)
    .replace('{stage}', STAGES[Math.floor(Math.random() * STAGES.length)])
    .replace('{date}', '20250118')
    .replace('{seq}', String(Math.floor(Math.random() * 100)).padStart(2, '0'));

  const timeLabel = randomMinutes < 60 
    ? `${randomMinutes}分钟前`
    : randomMinutes < 60 * 24 
      ? `${Math.floor(randomMinutes / 60)}小时前`
      : `${Math.floor(randomMinutes / 60 / 24)}天前`;

  return {
    id: `activity-${now.getTime()}-${index}`,
    type: template.type,
    message,
    time: timeLabel,
    timestamp: now.getTime() - randomMinutes * 60 * 1000
  };
};

const generateRecentActivities = (count = 6) => {
  return Array.from({ length: count }, (_, i) => generateActivity(i))
    .sort((a, b) => b.timestamp - a.timestamp);
};

// ============================================
// Data Transformation Utilities
// ============================================

/**
 * 将宽格式数据转换为长格式（适用于 LineChart）
 * @param {Array} data - 宽格式数据 [{ date, key1, key2, ... }]
 * @param {string} dateField - 日期字段名
 * @returns {Array} 长格式数据 [{ date, category, value }]
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
 * @param {Array} data - 数据数组
 * @param {string} valueKey - 值字段名
 * @returns {number}
 */
export const calculateTotal = (data, valueKey = 'value') => {
  return data.reduce((sum, item) => sum + (item[valueKey] || 0), 0);
};

// ============================================
// Custom Hook: useAnalytics
// ============================================

/**
 * 分析仪表盘数据 Hook
 * 
 * @param {Object} options - 配置选项
 * @param {number} options.refreshInterval - 自动刷新间隔（毫秒），0 表示禁用
 * @param {boolean} options.autoFetch - 是否自动获取数据
 * @returns {Object} 数据与状态
 * 
 * @example
 * const { kpis, projectTrend, activities, loading, error, refresh } = useAnalytics({ refreshInterval: 30000 });
 */
export function useAnalytics(options = {}) {
  const { 
    refreshInterval = 30000, // 默认 30 秒刷新
    autoFetch = true 
  } = options;

  // State
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);

  // Data State
  const [kpis, setKpis] = useState([]);
  const [projectTrend, setProjectTrend] = useState([]);
  const [statusDistribution, setStatusDistribution] = useState([]);
  const [monthlyStats, setMonthlyStats] = useState([]);
  const [resourceData, setResourceData] = useState([]);
  const [activities, setActivities] = useState([]);

  // Refs for cleanup
  const intervalRef = useRef(null);

  /**
   * 获取所有仪表盘数据
   */
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // 模拟 API 延迟
      await new Promise(resolve => setTimeout(resolve, 500 + Math.random() * 500));

      // 模拟偶发错误（概率 5%）
      if (Math.random() < 0.05) {
        throw new Error('网络请求失败，请稍后重试');
      }

      // 生成模拟数据
      setKpis(generateMockKPIs());
      setProjectTrend(generateProjectTrendData());
      setStatusDistribution(generateStatusDistribution());
      setMonthlyStats(generateMonthlyStats());
      setResourceData(generateResourceData());
      setActivities(generateRecentActivities(6));

      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message || '数据加载失败');
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 仅刷新活动列表（轻量级更新）
   */
  const refreshActivities = useCallback(async () => {
    try {
      await new Promise(resolve => setTimeout(resolve, 200));
      
      // 添加新活动到列表顶部
      const newActivity = generateActivity(Date.now());
      setActivities(prev => [newActivity, ...prev.slice(0, 5)]);
      setLastUpdated(new Date());
    } catch (err) {
      console.error('Failed to refresh activities:', err);
    }
  }, []);

  /**
   * 手动刷新全部数据
   */
  const refresh = useCallback(() => {
    return fetchData();
  }, [fetchData]);

  // 初始加载
  useEffect(() => {
    if (autoFetch) {
      fetchData();
    }
  }, [autoFetch, fetchData]);

  // 定时刷新
  useEffect(() => {
    if (refreshInterval > 0) {
      intervalRef.current = setInterval(() => {
        refreshActivities();
      }, refreshInterval);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [refreshInterval, refreshActivities]);

  // 计算派生数据
  const totalProjects = calculateTotal(statusDistribution, 'value');
  const lineChartData = transformToLongFormat(projectTrend, 'date');

  return {
    // 原始数据
    kpis,
    projectTrend,
    statusDistribution,
    monthlyStats,
    resourceData,
    activities,
    
    // 转换后的数据
    lineChartData,
    totalProjects,

    // 状态
    loading,
    error,
    lastUpdated,

    // 方法
    refresh,
    refreshActivities
  };
}

export default useAnalytics;
