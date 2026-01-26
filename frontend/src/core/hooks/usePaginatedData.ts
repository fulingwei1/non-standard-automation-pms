/**
 * 通用分页数据Hook
 * 统一处理分页、筛选、搜索
 */

import { useState, useCallback, useMemo } from 'react';
import { useQuery } from '@tanstack/react-query';

export interface PaginationParams {
  page: number;
  pageSize: number;
  filters?: Record<string, any>;
  keyword?: string;
  orderBy?: string;
  orderDirection?: 'asc' | 'desc';
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  pageSize: number;
  pages: number;
}

export interface UsePaginatedDataOptions {
  initialPage?: number;
  initialPageSize?: number;
  initialFilters?: Record<string, any>;
  initialKeyword?: string;
  enabled?: boolean;
}

/**
 * 通用分页数据Hook
 * 
 * @example
 * ```tsx
 * const {
 *   data,
 *   total,
 *   pagination,
 *   filters,
 *   keyword,
 *   isLoading,
 *   handlePageChange,
 *   handleFilterChange,
 *   setKeyword,
 *   refetch
 * } = usePaginatedData(
 *   ['projects'],
 *   (params) => projectApi.listProjects(params)
 * );
 * ```
 */
export function usePaginatedData<T>(
  queryKey: (string | number)[],
  queryFn: (params: PaginationParams) => Promise<PaginatedResponse<T>>,
  options?: UsePaginatedDataOptions
) {
  const {
    initialPage = 1,
    initialPageSize = 20,
    initialFilters = {},
    initialKeyword = '',
    enabled = true,
  } = options || {};

  const [pagination, setPagination] = useState({
    page: initialPage,
    pageSize: initialPageSize,
  });

  const [filters, setFilters] = useState<Record<string, any>>(initialFilters);
  const [keyword, setKeyword] = useState(initialKeyword);
  const [orderBy, setOrderBy] = useState<string | undefined>();
  const [orderDirection, setOrderDirection] = useState<'asc' | 'desc'>('desc');

  // 构建查询参数
  const queryParams = useMemo(() => ({
    page: pagination.page,
    pageSize: pagination.pageSize,
    filters,
    keyword: keyword || undefined,
    orderBy,
    orderDirection,
  }), [pagination, filters, keyword, orderBy, orderDirection]);

  // 执行查询
  const {
    data,
    isLoading,
    error,
    refetch,
  } = useQuery({
    queryKey: [...queryKey, queryParams],
    queryFn: () => queryFn(queryParams),
    enabled,
  });

  // 分页变更处理
  const handlePageChange = useCallback((page: number, pageSize: number) => {
    setPagination({ page, pageSize });
  }, []);

  // 筛选变更处理
  const handleFilterChange = useCallback((newFilters: Record<string, any>) => {
    setFilters(newFilters);
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一页
  }, []);

  // 关键词变更处理
  const handleKeywordChange = useCallback((newKeyword: string) => {
    setKeyword(newKeyword);
    setPagination(prev => ({ ...prev, page: 1 })); // 重置到第一页
  }, []);

  // 排序变更处理
  const handleSortChange = useCallback((field: string, direction: 'asc' | 'desc') => {
    setOrderBy(field);
    setOrderDirection(direction);
  }, []);

  // 重置筛选
  const resetFilters = useCallback(() => {
    setFilters(initialFilters);
    setKeyword(initialKeyword);
    setPagination({ page: 1, pageSize: initialPageSize });
  }, [initialFilters, initialKeyword, initialPageSize]);

  return {
    // 数据
    data: data?.items ?? [],
    total: data?.total ?? 0,
    pages: data?.pages ?? 0,
    
    // 状态
    pagination,
    filters,
    keyword,
    orderBy,
    orderDirection,
    isLoading,
    error,
    
    // 操作方法
    handlePageChange,
    handleFilterChange,
    setKeyword: handleKeywordChange,
    handleSortChange,
    resetFilters,
    refetch,
  };
}
