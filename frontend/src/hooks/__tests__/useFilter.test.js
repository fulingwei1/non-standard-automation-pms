/**
 * useFilter Hook 测试
 */

import { describe, it, expect } from 'vitest';
import { renderHook, act } from '@testing-library/react';
import { useFilter } from '../useFilter';

describe('useFilter', () => {
  it('should initialize with empty filters', () => {
    const { result } = renderHook(() => useFilter());

    expect(result.current.filters).toEqual({});
    expect(result.current.isEmpty).toBe(true);
    expect(result.current.activeCount).toBe(0);
  });

  it('should initialize with initial filters', () => {
    const initialFilters = {
      status: 'active',
      keyword: 'test',
      category: 'all'
    };

    const { result } = renderHook(() => useFilter(initialFilters));

    expect(result.current.filters).toEqual(initialFilters);
  });

  it('should set single filter', () => {
    const { result } = renderHook(() => useFilter({ status: 'all' }));

    act(() => {
      result.current.set('status', 'active');
    });

    expect(result.current.filters.status).toBe('active');
  });

  it('should set multiple filters at once', () => {
    const { result } = renderHook(() => useFilter());

    act(() => {
      result.current.setMultiple({
        status: 'active',
        keyword: 'search',
        category: 'tech'
      });
    });

    expect(result.current.filters).toEqual({
      status: 'active',
      keyword: 'search',
      category: 'tech'
    });
  });

  it('should reset all filters', () => {
    const initialFilters = {
      status: 'all',
      keyword: '',
      category: 'all'
    };

    const { result } = renderHook(() => useFilter(initialFilters));

    act(() => {
      result.current.setMultiple({
        status: 'active',
        keyword: 'search',
        category: 'tech'
      });
    });

    expect(result.current.filters).not.toEqual(initialFilters);

    act(() => {
      result.current.reset();
    });

    expect(result.current.filters).toEqual(initialFilters);
  });

  it('should reset single filter', () => {
    const initialFilters = {
      status: 'all',
      keyword: '',
      category: 'all'
    };

    const { result } = renderHook(() => useFilter(initialFilters));

    act(() => {
      result.current.setMultiple({
        status: 'active',
        keyword: 'search',
        category: 'tech'
      });
    });

    act(() => {
      result.current.resetOne('status');
    });

    expect(result.current.filters).toEqual({
      status: 'all',
      keyword: 'search',
      category: 'tech'
    });
  });

  it('should convert to query params excluding empty values', () => {
    const { result } = renderHook(() => useFilter({
      status: 'all',
      keyword: '',
      category: 'tech',
      id: null,
      name: 'test'
    }));

    const params = result.current.toQueryParams();

    expect(params).toEqual({
      category: 'tech',
      name: 'test'
    });
  });

  it('should calculate isEmpty correctly', () => {
    const { result } = renderHook(() => useFilter({
      status: 'all',
      keyword: '',
      category: null
    }));

    expect(result.current.isEmpty).toBe(true);

    act(() => {
      result.current.set('status', 'active');
    });

    expect(result.current.isEmpty).toBe(false);
  });

  it('should calculate activeCount correctly', () => {
    const { result } = renderHook(() => useFilter({
      status: 'all',
      keyword: '',
      category: null
    }));

    expect(result.current.activeCount).toBe(0);

    act(() => {
      result.current.setMultiple({
        status: 'active',
        keyword: 'search',
        category: 'tech'
      });
    });

    expect(result.current.activeCount).toBe(3);

    act(() => {
      result.current.set('keyword', '');
    });

    expect(result.current.activeCount).toBe(2);
  });

  it('should handle numeric values', () => {
    const { result } = renderHook(() => useFilter({ page: 1, limit: 0 }));

    act(() => {
      result.current.set('page', 2);
    });

    const params = result.current.toQueryParams();

    expect(params).toEqual({ page: 2, limit: 0 });
  });

  it('should handle boolean values', () => {
    const { result } = renderHook(() => useFilter({ isActive: false }));

    act(() => {
      result.current.set('isActive', true);
    });

    const params = result.current.toQueryParams();

    expect(params).toEqual({ isActive: true });
  });

  it('should preserve other filters when setting one', () => {
    const { result } = renderHook(() => useFilter({
      status: 'active',
      keyword: 'test',
      category: 'tech'
    }));

    act(() => {
      result.current.set('status', 'inactive');
    });

    expect(result.current.filters).toEqual({
      status: 'inactive',
      keyword: 'test',
      category: 'tech'
    });
  });

  it('should use setFilters to replace all filters', () => {
    const { result } = renderHook(() => useFilter({
      status: 'active',
      keyword: 'test'
    }));

    act(() => {
      result.current.setFilters({ category: 'tech' });
    });

    expect(result.current.filters).toEqual({ category: 'tech' });
  });

  it('should maintain function reference stability', () => {
    const { result, rerender } = renderHook(() => useFilter());

    const firstSet = result.current.set;
    const firstReset = result.current.reset;
    const firstToQueryParams = result.current.toQueryParams;

    rerender();

    expect(result.current.set).toBe(firstSet);
    expect(result.current.reset).toBe(firstReset);
    expect(result.current.toQueryParams).toBe(firstToQueryParams);
  });
});
