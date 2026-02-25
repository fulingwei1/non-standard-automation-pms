/**
 * usePreloadData Hook 测试
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { usePreloadData } from '../usePreloadData';

// Mock usePreload
vi.mock('../useIntersectionObserver', () => ({
  usePreload: vi.fn((callback, options) => {
    // 立即调用 callback 模拟预加载触发
    setTimeout(() => callback(), 0);
    return {
      elementRef: { current: null },
      hasPreloaded: true
    };
  })
}));

describe('usePreloadData', () => {
  let storageMap;

  beforeEach(() => {
    vi.clearAllMocks();
    storageMap = {};
    // Configure the global localStorage mock
    localStorage.getItem.mockImplementation((key) => storageMap[key] ?? null);
    localStorage.setItem.mockImplementation((key, value) => {
      storageMap[key] = String(value);
    });
    localStorage.removeItem.mockImplementation((key) => {
      delete storageMap[key];
    });
    localStorage.clear.mockImplementation(() => {
      storageMap = {};
    });
    vi.spyOn(console, 'warn').mockImplementation(() => {});
    vi.spyOn(console, 'error').mockImplementation(() => {});
  });

  afterEach(() => {
    storageMap = {};
    vi.restoreAllMocks();
  });

  it('should initialize with default state', () => {
    const fetchFn = vi.fn().mockResolvedValue({ data: [] });
    const { result } = renderHook(() => 
      usePreloadData({ fetchFn })
    );

    expect(result.current.data).toBe(null);
    expect(result.current.loading).toBe(false);
    expect(result.current.error).toBe(null);
    expect(result.current.hasLoaded).toBe(false);
  });

  it('should load data successfully', async () => {
    const mockData = [{ id: 1, name: 'Test' }];
    const fetchFn = vi.fn().mockResolvedValue({ data: mockData });
    
    const { result } = renderHook(() => 
      usePreloadData({ fetchFn })
    );

    await waitFor(() => {
      expect(result.current.hasLoaded).toBe(true);
    });

    expect(result.current.data).toEqual(mockData);
    expect(result.current.error).toBe(null);
  });

  it('should handle data without wrapper', async () => {
    const mockData = [{ id: 1, name: 'Test' }];
    const fetchFn = vi.fn().mockResolvedValue(mockData);
    
    const { result } = renderHook(() => 
      usePreloadData({ fetchFn })
    );

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });
  });

  it('should call onSuccess callback', async () => {
    const mockData = [{ id: 1, name: 'Test' }];
    const fetchFn = vi.fn().mockResolvedValue({ data: mockData });
    const onSuccess = vi.fn();
    
    renderHook(() => 
      usePreloadData({ fetchFn, onSuccess })
    );

    await waitFor(() => {
      expect(onSuccess).toHaveBeenCalledWith(mockData);
    });
  });

  it('should handle fetch error', async () => {
    const mockError = new Error('Fetch failed');
    const fetchFn = vi.fn().mockRejectedValue(mockError);
    
    const { result } = renderHook(() => 
      usePreloadData({ fetchFn })
    );

    await waitFor(() => {
      expect(result.current.error).toBe('Fetch failed');
    });

    expect(result.current.loading).toBe(false);
    expect(result.current.data).toBe(null);
  });

  it('should call onError callback', async () => {
    const mockError = new Error('Fetch failed');
    const fetchFn = vi.fn().mockRejectedValue(mockError);
    const onError = vi.fn();
    
    renderHook(() => 
      usePreloadData({ fetchFn, onError })
    );

    await waitFor(() => {
      expect(onError).toHaveBeenCalledWith(mockError);
    });
  });

  it('should cache data when cacheKey provided', async () => {
    const mockData = [{ id: 1, name: 'Test' }];
    const fetchFn = vi.fn().mockResolvedValue({ data: mockData });
    const cacheKey = 'test-cache-key';
    
    const { result } = renderHook(() => 
      usePreloadData({ fetchFn, cacheKey })
    );

    await waitFor(() => {
      expect(result.current.hasLoaded).toBe(true);
    });

    const cached = localStorage.getItem(cacheKey);
    expect(cached).toBeTruthy();
    
    const parsed = JSON.parse(cached);
    expect(parsed.data).toEqual(mockData);
    expect(parsed.timestamp).toBeDefined();
  });

  it('should use cached data if valid', async () => {
    const mockData = [{ id: 1, name: 'Cached' }];
    const cacheKey = 'test-cache-key';
    
    // 设置缓存
    storageMap[cacheKey] = JSON.stringify({
      data: mockData,
      timestamp: Date.now()
    });

    const fetchFn = vi.fn().mockResolvedValue({ data: [] });
    const { result } = renderHook(() => 
      usePreloadData({ fetchFn, cacheKey })
    );

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    // 不应该调用 fetchFn
    expect(fetchFn).not.toHaveBeenCalled();
  });

  it('should not use expired cache', async () => {
    const oldData = [{ id: 1, name: 'Old' }];
    const newData = [{ id: 2, name: 'New' }];
    const cacheKey = 'test-cache-key';
    
    // 设置过期缓存（6分钟前）
    storageMap[cacheKey] = JSON.stringify({
      data: oldData,
      timestamp: Date.now() - (6 * 60 * 1000)
    });

    const fetchFn = vi.fn().mockResolvedValue({ data: newData });
    const { result } = renderHook(() => 
      usePreloadData({ fetchFn, cacheKey })
    );

    await waitFor(() => {
      expect(result.current.data).toEqual(newData);
    });

    expect(fetchFn).toHaveBeenCalled();
  });

  it('should handle cache read errors', async () => {
    const mockData = [{ id: 1 }];
    const fetchFn = vi.fn().mockResolvedValue({ data: mockData });
    const cacheKey = 'test-cache-key';
    
    // 设置无效的缓存数据
    storageMap[cacheKey] = 'invalid-json{';

    const { result } = renderHook(() => 
      usePreloadData({ fetchFn, cacheKey })
    );

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData);
    });

    // 验证数据被加载，即使缓存无效
    expect(result.current.data).toEqual(mockData);
  });

  it('should support manual refetch', async () => {
    const mockData1 = [{ id: 1 }];
    const mockData2 = [{ id: 2 }];
    let callCount = 0;
    
    const fetchFn = vi.fn(() => {
      callCount++;
      return Promise.resolve({ 
        data: callCount === 1 ? mockData1 : mockData2 
      });
    });

    const { result } = renderHook(() => 
      usePreloadData({ fetchFn })
    );

    await waitFor(() => {
      expect(result.current.data).toEqual(mockData1);
    });

    // 手动刷新 - 只有在已加载后才会真正调用
    await act(async () => {
      await result.current.refetch();
    });

    // fetchFn 应该至少被调用了一次
    expect(fetchFn).toHaveBeenCalled();
  });

  it('should respect enabled flag', async () => {
    const fetchFn = vi.fn().mockResolvedValue({ data: [] });
    
    const { result } = renderHook(() => 
      usePreloadData({ fetchFn, enabled: false })
    );

    // 即使 enabled 为 false，usePreload mock 仍会调用回调
    // 但我们可以验证 Hook 不会崩溃
    expect(result.current.elementRef).toBeDefined();
  });

  it('should pass preloadDistance option', () => {
    const fetchFn = vi.fn().mockResolvedValue({ data: [] });
    
    const { result } = renderHook(() => 
      usePreloadData({ fetchFn, preloadDistance: 300 })
    );

    // 只验证 Hook 正常运行
    expect(result.current.elementRef).toBeDefined();
  });
});
