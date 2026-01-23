/**
 * usePaginatedData Hook 测试
 */

import { describe, it, expect, vi, beforeEach } from 'vitest';
import { renderHook, waitFor, act } from '@testing-library/react';
import { QueryClient, QueryClientProvider } from '@tanstack/react-query';
import { ReactNode } from 'react';
import { usePaginatedData } from '../usePaginatedData';

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

describe('usePaginatedData', () => {
  beforeEach(() => {
    vi.clearAllMocks();
  });

  it('should initialize with default values', () => {
    const mockQueryFn = vi.fn().mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      pages: 0,
    });

    const { result } = renderHook(
      () => usePaginatedData(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    expect(result.current.pagination.page).toBe(1);
    expect(result.current.pagination.pageSize).toBe(20);
    expect(result.current.filters).toEqual({});
    expect(result.current.keyword).toBe('');
  });

  it('should load paginated data', async () => {
    const mockData = {
      items: [{ id: 1, name: 'Item 1' }, { id: 2, name: 'Item 2' }],
      total: 2,
      page: 1,
      pageSize: 20,
      pages: 1,
    };

    const mockQueryFn = vi.fn().mockResolvedValue(mockData);

    const { result } = renderHook(
      () => usePaginatedData(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    expect(result.current.data).toEqual(mockData.items);
    expect(result.current.total).toBe(2);
    expect(mockQueryFn).toHaveBeenCalledWith({
      page: 1,
      pageSize: 20,
      filters: {},
      keyword: undefined,
      orderBy: undefined,
      orderDirection: 'desc',
    });
  });

  it('should handle page change', async () => {
    const mockQueryFn = vi.fn().mockResolvedValue({
      items: [],
      total: 0,
      page: 2,
      pageSize: 20,
      pages: 0,
    });

    const { result } = renderHook(
      () => usePaginatedData(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handlePageChange(2, 20);
    });

    await waitFor(() => {
      expect(result.current.pagination.page).toBe(2);
    });

    expect(mockQueryFn).toHaveBeenCalledWith(
      expect.objectContaining({ page: 2 })
    );
  });

  it('should handle filter change', async () => {
    const mockQueryFn = vi.fn().mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      pages: 0,
    });

    const { result } = renderHook(
      () => usePaginatedData(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleFilterChange({ status: 'active' });
    });

    await waitFor(() => {
      expect(result.current.filters).toEqual({ status: 'active' });
      expect(result.current.pagination.page).toBe(1); // 应该重置到第一页
    });
  });

  it('should handle keyword change', async () => {
    const mockQueryFn = vi.fn().mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      pages: 0,
    });

    const { result } = renderHook(
      () => usePaginatedData(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.setKeyword('test keyword');
    });

    await waitFor(() => {
      expect(result.current.keyword).toBe('test keyword');
      expect(result.current.pagination.page).toBe(1); // 应该重置到第一页
    });
  });

  it('should handle sort change', async () => {
    const mockQueryFn = vi.fn().mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      pages: 0,
    });

    const { result } = renderHook(
      () => usePaginatedData(['test'], mockQueryFn),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.handleSortChange('name', 'asc');
    });

    await waitFor(() => {
      expect(result.current.orderBy).toBe('name');
      expect(result.current.orderDirection).toBe('asc');
    });
  });

  it('should reset filters', async () => {
    const mockQueryFn = vi.fn().mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      pages: 0,
    });

    const { result } = renderHook(
      () => usePaginatedData(['test'], mockQueryFn, {
        initialFilters: { status: 'active' },
        initialKeyword: 'test',
      }),
      { wrapper: createWrapper() }
    );

    await waitFor(() => {
      expect(result.current.isLoading).toBe(false);
    });

    act(() => {
      result.current.resetFilters();
    });

    await waitFor(() => {
      expect(result.current.filters).toEqual({ status: 'active' });
      expect(result.current.keyword).toBe('test');
      expect(result.current.pagination.page).toBe(1);
    });
  });

  it('should respect enabled option', () => {
    const mockQueryFn = vi.fn().mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      pageSize: 20,
      pages: 0,
    });

    const { result } = renderHook(
      () => usePaginatedData(['test'], mockQueryFn, { enabled: false }),
      { wrapper: createWrapper() }
    );

    expect(result.current.isLoading).toBe(false);
    expect(mockQueryFn).not.toHaveBeenCalled();
  });
});
