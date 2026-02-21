/**
 * usePagination Hook 测试
 */

import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { usePagination } from '../usePagination';

describe('usePagination', () => {
  it('should initialize with default values', () => {
    const { result } = renderHook(() => usePagination());

    expect(result.current.page).toBe(1);
    expect(result.current.pageSize).toBe(20);
    expect(result.current.total).toBe(0);
    expect(result.current.totalPages).toBe(1);
    expect(result.current.hasPrev).toBe(false);
    expect(result.current.hasNext).toBe(false);
  });

  it('should initialize with custom options', () => {
    const { result } = renderHook(() => 
      usePagination({
        initialPage: 2,
        initialPageSize: 10,
        total: 100
      })
    );

    expect(result.current.page).toBe(2);
    expect(result.current.pageSize).toBe(10);
    expect(result.current.total).toBe(100);
    expect(result.current.totalPages).toBe(10);
  });

  it('should calculate total pages correctly', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100, initialPageSize: 20 })
    );

    expect(result.current.totalPages).toBe(5);
  });

  it('should calculate total pages with remainder', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 95, initialPageSize: 20 })
    );

    expect(result.current.totalPages).toBe(5);
  });

  it('should provide correct params object', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100, initialPageSize: 20 })
    );

    expect(result.current.params).toEqual({
      page: 1,
      page_size: 20,
      offset: 0
    });

    act(() => {
      result.current.setPage(3);
    });

    expect(result.current.params).toEqual({
      page: 3,
      page_size: 20,
      offset: 40
    });
  });

  it('should go to specific page', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100 })
    );

    act(() => {
      result.current.setPage(3);
    });

    expect(result.current.page).toBe(3);
  });

  it('should not go beyond total pages', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100, initialPageSize: 20 })
    );

    act(() => {
      result.current.setPage(10);
    });

    expect(result.current.page).toBe(5); // max pages
  });

  it('should not go below page 1', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100 })
    );

    act(() => {
      result.current.setPage(-1);
    });

    expect(result.current.page).toBe(1);

    act(() => {
      result.current.setPage(0);
    });

    expect(result.current.page).toBe(1);
  });

  it('should go to previous page', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100, initialPage: 3 })
    );

    act(() => {
      result.current.prevPage();
    });

    expect(result.current.page).toBe(2);
  });

  it('should not go to previous page when on first page', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100 })
    );

    act(() => {
      result.current.prevPage();
    });

    expect(result.current.page).toBe(1);
  });

  it('should go to next page', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100 })
    );

    act(() => {
      result.current.nextPage();
    });

    expect(result.current.page).toBe(2);
  });

  it('should not go to next page when on last page', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100, initialPageSize: 20, initialPage: 5 })
    );

    act(() => {
      result.current.nextPage();
    });

    expect(result.current.page).toBe(5);
  });

  it('should calculate hasPrev correctly', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100 })
    );

    expect(result.current.hasPrev).toBe(false);

    act(() => {
      result.current.nextPage();
    });

    expect(result.current.hasPrev).toBe(true);
  });

  it('should calculate hasNext correctly', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100, initialPageSize: 20 })
    );

    expect(result.current.hasNext).toBe(true);

    act(() => {
      result.current.setPage(5);
    });

    expect(result.current.hasNext).toBe(false);
  });

  it('should reset to initial page', () => {
    const { result } = renderHook(() => 
      usePagination({ initialPage: 2, total: 100 })
    );

    act(() => {
      result.current.setPage(5);
    });

    expect(result.current.page).toBe(5);

    act(() => {
      result.current.reset();
    });

    expect(result.current.page).toBe(2);
  });

  it('should update page size', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100 })
    );

    act(() => {
      result.current.setPageSize(50);
    });

    expect(result.current.pageSize).toBe(50);
    expect(result.current.totalPages).toBe(2);
  });

  it('should update total', () => {
    const { result } = renderHook(() => 
      usePagination()
    );

    act(() => {
      result.current.setTotal(150);
    });

    expect(result.current.total).toBe(150);
    expect(result.current.totalPages).toBe(8);
  });

  it('should update from API response', () => {
    const { result } = renderHook(() => 
      usePagination()
    );

    act(() => {
      result.current.updateFromResponse({
        total: 200,
        page: 3
      });
    });

    expect(result.current.total).toBe(200);
    expect(result.current.page).toBe(3);
  });

  it('should handle partial response update', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 100, initialPage: 2 })
    );

    act(() => {
      result.current.updateFromResponse({ total: 150 });
    });

    expect(result.current.total).toBe(150);
    expect(result.current.page).toBe(2); // page unchanged
  });

  it('should handle zero total', () => {
    const { result } = renderHook(() => 
      usePagination({ total: 0 })
    );

    expect(result.current.totalPages).toBe(1);
    expect(result.current.hasNext).toBe(false);
    expect(result.current.hasPrev).toBe(false);
  });

  it('should maintain function reference stability', () => {
    const { result, rerender } = renderHook(() => 
      usePagination()
    );

    const firstSetPage = result.current.setPage;
    const firstPrevPage = result.current.prevPage;
    const firstNextPage = result.current.nextPage;

    rerender();

    expect(result.current.setPage).toBe(firstSetPage);
    expect(result.current.prevPage).toBe(firstPrevPage);
    expect(result.current.nextPage).toBe(firstNextPage);
  });
});
