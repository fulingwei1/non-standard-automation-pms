/**
 * useAnalytics Hook 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';

// Mock 源码依赖的 API 模块
vi.mock('../../services/api/analytics', () => ({
  workloadAnalyticsApi: {
    overview: vi.fn().mockResolvedValue({
      data: {
        average_utilization: 85,
        utilization_change: '+5%',
        department_stats: [],
      },
    }),
    bottlenecks: vi.fn().mockResolvedValue({
      data: {
        items: [
          {
            id: 1,
            severity: 'HIGH',
            employee_name: '张工',
            conflict_type: '超负荷',
            created_at: '2026-03-01T10:00:00',
          },
        ],
      },
    }),
  },
}));

vi.mock('../../services/api/projects', () => ({
  projectApi: {
    getStats: vi.fn().mockResolvedValue({
      data: {
        active_count: 12,
        active_change: '+2',
        completed_this_month: 5,
        completed_change: '+1',
        pending_tickets: 8,
        tickets_change: '-3',
        monthly_trend: [
          { month: '2026-01', completed: 3, active: 10 },
          { month: '2026-02', completed: 5, active: 12 },
        ],
        stage_distribution: [
          { name: '需求', count: 4 },
          { name: '设计', count: 3 },
          { name: '实施', count: 5 },
        ],
      },
    }),
  },
}));

import { useAnalytics } from '../useAnalytics';

describe('useAnalytics', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('should initialize with loading state', () => {
    const { result } = renderHook(() => useAnalytics());

    expect(result.current.loading).toBe(true);
    expect(result.current.error).toBe(null);
    expect(result.current.kpis).toHaveLength(0);
  });

  it('should load analytics data successfully', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    }, { timeout: 5000 });

    expect(result.current.kpis.length).toBeGreaterThan(0);
    expect(result.current.projectTrend.length).toBeGreaterThan(0);
    expect(result.current.statusDistribution.length).toBeGreaterThan(0);
  });

  it('should return KPIs with correct structure', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.kpis.length).toBe(4);
    }, { timeout: 5000 });

    const kpi = result.current.kpis[0];
    expect(kpi).toHaveProperty('id');
    expect(kpi).toHaveProperty('label');
    expect(kpi).toHaveProperty('value');
    expect(kpi).toHaveProperty('change');
    expect(kpi).toHaveProperty('trend');
    expect(kpi).toHaveProperty('icon');
  });

  it('should return project trend data', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.projectTrend.length).toBeGreaterThan(0);
    }, { timeout: 5000 });

    const trendData = result.current.projectTrend[0];
    expect(trendData).toHaveProperty('date');
    expect(trendData).toHaveProperty('完成');
    expect(trendData).toHaveProperty('进行中');
  });

  it('should return status distribution data', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.statusDistribution.length).toBeGreaterThan(0);
    }, { timeout: 5000 });

    const distribution = result.current.statusDistribution[0];
    expect(distribution).toHaveProperty('name');
    expect(distribution).toHaveProperty('value');
    expect(distribution).toHaveProperty('color');
  });

  it('should support manual refresh', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    }, { timeout: 5000 });

    act(() => {
      result.current.refresh();
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    }, { timeout: 5000 });

    expect(result.current.kpis).toBeDefined();
  });

  it('should cleanup on unmount', () => {
    const { unmount } = renderHook(() => 
      useAnalytics({ autoRefresh: true, refreshInterval: 5000 })
    );

    // Should not throw on unmount
    expect(() => unmount()).not.toThrow();
  });

  it('should provide lastUpdated after loading', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    }, { timeout: 5000 });

    // lastUpdated is set to new Date() after successful load
    expect(result.current.lastUpdated).toBeInstanceOf(Date);
  });

  it('should maintain data structure consistency', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    }, { timeout: 5000 });

    expect(result.current).toHaveProperty('kpis');
    expect(result.current).toHaveProperty('projectTrend');
    expect(result.current).toHaveProperty('statusDistribution');
    expect(result.current).toHaveProperty('monthlyStats');
    expect(result.current).toHaveProperty('activities');
    expect(result.current).toHaveProperty('loading');
    expect(result.current).toHaveProperty('error');
    expect(result.current).toHaveProperty('refresh');
    expect(result.current).toHaveProperty('lastUpdated');
  });
});
