import { useState, useEffect, useCallback, useRef } from 'react';

/**
 * 防抖值 Hook
 * 
 * @param {any} value - 要防抖的值
 * @param {number} delay - 延迟时间（毫秒）
 * 
 * @example
 * const [searchTerm, setSearchTerm] = useState('');
 * const debouncedSearch = useDebounce(searchTerm, 500);
 * 
 * useEffect(() => {
 *   // 只在防抖值变化时搜索
 *   search(debouncedSearch);
 * }, [debouncedSearch]);
 */
export function useDebounce(value, delay = 500) {
  const [debouncedValue, setDebouncedValue] = useState(value);

  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedValue(value);
    }, delay);

    return () => {
      clearTimeout(timer);
    };
  }, [value, delay]);

  return debouncedValue;
}

/**
 * 防抖回调 Hook
 * 
 * @param {Function} callback - 要防抖的回调函数
 * @param {number} delay - 延迟时间（毫秒）
 * 
 * @example
 * const debouncedSearch = useDebouncedCallback((term) => {
 *   api.search(term);
 * }, 500);
 * 
 * <input onChange={(e) => debouncedSearch(e.target.value)} />
 */
export function useDebouncedCallback(callback, delay = 500) {
  const timeoutRef = useRef(null);

  const debouncedCallback = useCallback((...args) => {
    if (timeoutRef.current) {
      clearTimeout(timeoutRef.current);
    }

    timeoutRef.current = setTimeout(() => {
      callback(...args);
    }, delay);
  }, [callback, delay]);

  // 清理
  useEffect(() => {
    return () => {
      if (timeoutRef.current) {
        clearTimeout(timeoutRef.current);
      }
    };
  }, []);

  return debouncedCallback;
}
