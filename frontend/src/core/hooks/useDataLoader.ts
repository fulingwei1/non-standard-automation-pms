/**
 * 通用数据加载Hook
 * 统一处理数据加载、错误处理、加载状态
 */

import { useState, useEffect, useCallback } from 'react';
import { useQuery, UseQueryOptions } from '@tanstack/react-query';

export interface UseDataLoaderOptions<T> extends Omit<UseQueryOptions<T>, 'queryKey' | 'queryFn'> {
  enabled?: boolean;
  refetchInterval?: number;
}

/**
 * 通用数据加载Hook
 * 
 * @example
 * ```tsx
 * const { data, isLoading, error, refetch } = useDataLoader(
 *   ['projects', projectId],
 *   () => projectApi.getProject(projectId)
 * );
 * ```
 */
export function useDataLoader<T>(
  queryKey: (string | number)[],
  queryFn: () => Promise<T>,
  options?: UseDataLoaderOptions<T>
) {
  return useQuery({
    queryKey,
    queryFn,
    ...options,
  });
}

/**
 * 带自动重试的数据加载Hook
 */
export function useDataLoaderWithRetry<T>(
  queryKey: (string | number)[],
  queryFn: () => Promise<T>,
  options?: UseDataLoaderOptions<T>
) {
  return useQuery({
    queryKey,
    queryFn,
    retry: 3,
    retryDelay: (attemptIndex) => Math.min(1000 * 2 ** attemptIndex, 30000),
    ...options,
  });
}
