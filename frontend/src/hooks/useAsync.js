import { useState, useCallback, useEffect } from 'react';

/**
 * 异步操作 Hook
 * 
 * @param {Function} asyncFunction - 异步函数
 * @param {Object} options - 配置选项
 * @param {boolean} options.immediate - 是否立即执行
 * 
 * @example
 * const { execute, status, value, error } = useAsync(
 *   async () => {
 *     const response = await fetch('/api/data');
 *     return response.json();
 *   },
 *   { immediate: true }
 * );
 */
export function useAsync(asyncFunction, options = {}) {
  const { immediate = false } = options;

  const [status, setStatus] = useState('idle'); // idle | pending | success | error
  const [value, setValue] = useState(null);
  const [error, setError] = useState(null);

  const execute = useCallback(async (...args) => {
    setStatus('pending');
    setValue(null);
    setError(null);

    try {
      const response = await asyncFunction(...args);
      setValue(response);
      setStatus('success');
      return { success: true, data: response };
    } catch (err) {
      setError(err);
      setStatus('error');
      return { success: false, error: err };
    }
  }, [asyncFunction]);

  useEffect(() => {
    if (immediate) {
      execute();
    }
  }, [execute, immediate]);

  return {
    execute,
    status,
    value,
    error,
    isIdle: status === 'idle',
    isPending: status === 'pending',
    isSuccess: status === 'success',
    isError: status === 'error',
    reset: () => {
      setStatus('idle');
      setValue(null);
      setError(null);
    },
  };
}
