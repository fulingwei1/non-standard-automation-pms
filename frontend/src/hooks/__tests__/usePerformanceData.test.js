/**
 * usePerformanceData Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { usePerformanceData } from '../usePerformanceData';
import { performanceApi } from '../../services/api';

// Mock API
vi.mock('../../services/api', async (importOriginal) => {
  const actual = await importOriginal();
  return {
    ...actual,
    default: {
      get: vi.fn(),
      post: vi.fn(),
      put: vi.fn(),
      delete: vi.fn(),
      patch: vi.fn(),
      defaults: { baseURL: '/api' },
    },
  };
});

describe('usePerformanceData', () => {
  const mockPerformanceData = {
    id: 1,
    user_id: 1,
    period: '2024-01',
    score: 85,
    rating: 'A',
    metrics: {
      quality: 90,
      efficiency: 80,
      collaboration: 85
    }
  };

  const mockFallbackData = {
    id: 2,
    user_id: 1,
    period: '2023-12',
    score: 75,
    rating: 'B'
  };

  beforeEach(() => {
    vi.clearAllMocks();

    performanceApi.getMyPerformance.mockResolvedValue({
      data: mockPerformanceData
    });
  });

  it('should initialize with loading state', () => {
    const { result } = renderHook(() => 
      usePerformanceData(mockFallbackData)
    );

    expect(result.current.isLoading).toBe(true);
    expect(result.current.performanceData).toBe(null);
    expect(result.current.error).toBe(null);
  });

  it('should load performance data successfully', async () => {
    const { result } = renderHook(() => 
      usePerformanceData(mockFallbackData)
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.performanceData).toEqual(mockPerformanceData);
    expect(result.current.error).toBe(null);
  });

  it('should call API on mount', async () => {

    
    renderHook(() => usePerformanceData(mockFallbackData));

    await waitFor(() => {
      expect(performanceApi.getMyPerformance).toHaveBeenCalledTimes(1);
    });
  });

  it('should handle API error with fallback data', async () => {

    const mockError = new Error('API Error');
    mockError.response = { data: { detail: 'Failed to load performance' } };
    performanceApi.getMyPerformance.mockRejectedValue(mockError);

    const { result } = renderHook(() => 
      usePerformanceData(mockFallbackData)
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe('Failed to load performance');
    expect(result.current.performanceData).toEqual(mockFallbackData);
  });

  it('should handle API error without detail message', async () => {

    const mockError = new Error('Network Error');
    performanceApi.getMyPerformance.mockRejectedValue(mockError);

    const { result } = renderHook(() => 
      usePerformanceData(mockFallbackData)
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.error).toBe('加载失败');
    expect(result.current.performanceData).toEqual(mockFallbackData);
  });

  it('should support manual refetch', async () => {

    
    const { result } = renderHook(() => 
      usePerformanceData(mockFallbackData)
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(performanceApi.getMyPerformance).toHaveBeenCalledTimes(1);

    // 手动刷新
    await result.current.refetch();

    expect(performanceApi.getMyPerformance).toHaveBeenCalledTimes(2);
  });

  it('should update loading state during refetch', async () => {
    const { result } = renderHook(() => 
      usePerformanceData(mockFallbackData)
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.isLoading).toBe(false);
  });

  it('should clear error on successful refetch', async () => {

    
    // 首次调用失败
    performanceApi.getMyPerformance.mockRejectedValueOnce(new Error('Error'));
    
    const { result } = renderHook(() => 
      usePerformanceData(mockFallbackData)
    );

    await waitFor(() => {
      expect(result.current.error).toBeTruthy();
    });

    // 重新成功
    performanceApi.getMyPerformance.mockResolvedValueOnce({
      data: mockPerformanceData
    });

    await act(async () => {
      await result.current.refetch();
    });

    expect(result.current.error).toBe(null);
    expect(result.current.performanceData).toEqual(mockPerformanceData);
  });

  it('should not reload on re-render', async () => {

    
    const { rerender } = renderHook(() => 
      usePerformanceData(mockFallbackData)
    );

    await waitFor(() => {
      expect(performanceApi.getMyPerformance).toHaveBeenCalledTimes(1);
    });

    rerender();

    expect(performanceApi.getMyPerformance).toHaveBeenCalledTimes(1);
  });

  it('should handle null fallback data', async () => {

    performanceApi.getMyPerformance.mockRejectedValue(new Error('Error'));

    const { result } = renderHook(() => 
      usePerformanceData(null)
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.performanceData).toBe(null);
  });

  it('should handle empty performance data', async () => {

    performanceApi.getMyPerformance.mockResolvedValue({ data: null });

    const { result } = renderHook(() => 
      usePerformanceData(mockFallbackData)
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.performanceData).toBe(null);
  });
});
