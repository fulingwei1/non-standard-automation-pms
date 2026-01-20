import { useState, useCallback, useEffect } from 'react';

/**
 * 通用API请求Hook
 * 
 * @param {Function} apiFunction - API函数
 * @param {Object} options - 配置选项
 * @param {boolean} options.immediate - 是否立即执行
 * @param {any} options.initialData - 初始数据
 * @param {Function} options.onSuccess - 成功回调
 * @param {Function} options.onError - 错误回调
 * 
 * @example
 * const { data, loading, error, execute } = useApi(
 *   () => userApi.list({ page: 1 }),
 *   { immediate: true }
 * );
 */
export function useApi(apiFunction, options = {}) {
  const {
    immediate = false,
    initialData = null,
    onSuccess,
    onError,
  } = options;

  const [data, setData] = useState(initialData);
  const [loading, setLoading] = useState(immediate);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiFunction(...args);
      const result = response.data || response;
      setData(result);
      onSuccess?.(result);
      return { success: true, data: result };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || '请求失败';
      setError(errorMessage);
      onError?.(err);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [apiFunction, onSuccess, onError]);

  // 立即执行
  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [immediate, execute]);

  return {
    data,
    loading,
    error,
    execute,
    setData,
    reset: () => {
      setData(initialData);
      setError(null);
    },
  };
}

/**
 * API Mutation Hook (用于创建、更新、删除等操作)
 * 
 * @param {Function} apiFunction - API函数
 * @param {Object} options - 配置选项
 * 
 * @example
 * const { mutate, loading, error } = useApiMutation(
 *   (data) => userApi.create(data),
 *   { onSuccess: () => toast.success('创建成功') }
 * );
 * 
 * await mutate({ name: 'John' });
 */
export function useApiMutation(apiFunction, options = {}) {
  const { onSuccess, onError } = options;

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const mutate = useCallback(async (...args) => {
    try {
      setLoading(true);
      setError(null);
      const response = await apiFunction(...args);
      const result = response.data || response;
      onSuccess?.(result);
      return { success: true, data: result };
    } catch (err) {
      const errorMessage = err.response?.data?.detail || err.message || '操作失败';
      setError(errorMessage);
      onError?.(err);
      return { success: false, error: errorMessage };
    } finally {
      setLoading(false);
    }
  }, [apiFunction, onSuccess, onError]);

  return {
    mutate,
    loading,
    error,
    reset: () => setError(null),
  };
}
