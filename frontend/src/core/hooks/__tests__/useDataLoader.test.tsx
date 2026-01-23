/**
 * useDataLoader Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { useDataLoader, useDataLoaderWithRetry } from '../useDataLoader';

// 创建测试用的 QueryClient
const createWrapper = () => {
  const queryClient = new QueryClient({
    defaultOptions: {
      queries: {
        retry: false,
      },
    },
  });
  return ({ children }: { children: ReactNode }) => (
    <QueryClientProvider client={queryClient}>
      {children}
    </QueryClientProvider>
  );
};

describe('useDataLoader', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should load data successfully', async () => {
    const mockData = { id: 1, name: 'Test' };
    const mockQueryFn = vi.fn().mockResolvedValue(mockData);

    const { result } = renderHook(
      () => useDataLoader(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(result.current.data).toEqual(mockData);
    expect(mockQueryFn).toHaveBeenCalledTimes(1);
  });

  it('should handle loading state', async () => {
    const mockQueryFn = vi.fn().mockImplementation(
      () => new Promise(resolve => setTimeout(() => resolve({ id: 1 }), 100))
    );

    const { result } = renderHook(
      () => useDataLoader(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(true);

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });
  });

  it('should handle error state', async () => {
    const mockError = new Error('Test error');
    const mockQueryFn = vi.fn().mockRejectedValue(mockError);

    const { result } = renderHook(
      () => useDataLoader(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isError).toBe(true);
    });

    expect(result.current.error).toEqual(mockError);
  });

  it('should respect enabled option', () => {
    const mockQueryFn = vi.fn().mockResolvedValue({ id: 1 });

    const { result } = renderHook(
      () => useDataLoader(['test'], mockQueryFn, { enabled: false }),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(false);
    expect(mockQueryFn).not.toHaveBeenCalled();
  });

  it('should refetch when refetch is called', async () => {
    const mockData = { id: 1, name: 'Test' };
    const mockQueryFn = vi.fn().mockResolvedValue(mockData);

    const { result } = renderHook(
      () => useDataLoader(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    });

    expect(mockQueryFn).toHaveBeenCalledTimes(1);

    await result.current.refetch();

    expect(mockQueryFn).toHaveBeenCalledTimes(2);
  });
});

describe('useDataLoaderWithRetry', () => {
  it('should retry on failure', async () => {
    let attemptCount = 0;
    const mockQueryFn = vi.fn().mockImplementation(() => {
      attemptCount++;
      if (attemptCount < 3) {
        return Promise.reject(new Error('Test error'));
      }
      return Promise.resolve({ id: 1 });
    });

    const { result } = renderHook(
      () => useDataLoaderWithRetry(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isSuccess).toBe(true);
    }, { timeout: 5000 });

    expect(mockQueryFn).toHaveBeenCalledTimes(3);
    expect(result.current.data).toEqual({ id: 1 });
  });
});
