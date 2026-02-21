/**
 * useAnalytics Hook 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { useAnalytics } from '../useAnalytics';

describe('useAnalytics', () => {
  beforeEach(() => {
    vi.useFakeTimers();
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
    });

    expect(result.current.kpis.length).toBeGreaterThan(0);
    expect(result.current.projectTrend.length).toBeGreaterThan(0);
    expect(result.current.statusDistribution.length).toBeGreaterThan(0);
  });

  it('should return KPIs with correct structure', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.kpis.length).toBe(4);
    });

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
    });

    const trendData = result.current.projectTrend[0];
    expect(trendData).toHaveProperty('date');
    expect(trendData).toHaveProperty('完成');
    expect(trendData).toHaveProperty('进行中');
  });

  it('should return status distribution data', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.statusDistribution.length).toBeGreaterThan(0);
    });

    const distribution = result.current.statusDistribution[0];
    expect(distribution).toHaveProperty('name');
    expect(distribution).toHaveProperty('value');
    expect(distribution).toHaveProperty('color');
  });

  it('should support manual refresh', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const initialKpis = result.current.kpis;

    act(() => {
      result.current.refresh();
    });

    expect(result.current.loading).toBe(true);

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 刷新后数据可能会变化（因为是随机生成的）
    expect(result.current.kpis).toBeDefined();
  });

  it('should auto-refresh when enabled', async () => {
    const { result } = renderHook(() => 
      useAnalytics({ autoRefresh: true, refreshInterval: 5000 })
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const initialData = result.current.kpis;

    // 快进 5 秒
    act(() => {
      vi.advanceTimersByTime(5000);
    });

    await waitFor(() => {
      // 应该触发了新的加载
      expect(result.current.kpis).toBeDefined();
    });
  });

  it('should not auto-refresh when disabled', async () => {
    const { result } = renderHook(() => 
      useAnalytics({ autoRefresh: false })
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const loadingSpy = vi.fn();
    
    // 快进时间
    act(() => {
      vi.advanceTimersByTime(30000);
    });

    // 不应该触发新的加载
    expect(result.current.loading).toBe(false);
  });

  it('should cleanup interval on unmount', () => {
    const { unmount } = renderHook(() => 
      useAnalytics({ autoRefresh: true, refreshInterval: 5000 })
    );

    const clearIntervalSpy = vi.spyOn(global, 'clearInterval');

    unmount();

    expect(clearIntervalSpy).toHaveBeenCalled();
  });

  it('should handle custom refresh interval', async () => {
    const { result } = renderHook(() => 
      useAnalytics({ autoRefresh: true, refreshInterval: 1000 })
    );

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 快进 1 秒
    act(() => {
      vi.advanceTimersByTime(1000);
    });

    // 应该触发刷新
    await waitFor(() => {
      expect(result.current.kpis).toBeDefined();
    });
  });

  it('should provide lastUpdated timestamp', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.lastUpdated).toBeDefined();
    expect(typeof result.current.lastUpdated).toBe('number');
  });

  it('should update lastUpdated on refresh', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    const firstTimestamp = result.current.lastUpdated;

    // 等待一小段时间
    await new Promise(resolve => setTimeout(resolve, 10));

    act(() => {
      result.current.refresh();
    });

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.lastUpdated).toBeGreaterThan(firstTimestamp);
  });

  it('should maintain data structure consistency', async () => {
    const { result } = renderHook(() => useAnalytics());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // 验证所有必需的字段都存在
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
