/**
 * useDashboardData - 统一的工作台数据获取Hook
 * 提供数据获取、缓存、错误处理等功能
 */
import { useState, useEffect, useCallback, useRef } from "react";

export function useDashboardData({
  fetchFn,
  cacheKey,
  cacheTime = 5 * 60 * 1000, // 默认5分钟缓存
  enabled = true,
  refetchInterval,
  onSuccess,
  onError,
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const cacheRef = useRef(null);
  const intervalRef = useRef(null);

  // 从缓存读取数据
  const getCachedData = useCallback(() => {
    if (!cacheKey) return null;
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const { data: cachedData, timestamp } = JSON.parse(cached);
        const now = Date.now();
        if (now - timestamp < cacheTime) {
          return cachedData;
        }
        // 缓存过期，清除
        localStorage.removeItem(cacheKey);
      }
    } catch (e) {
      console.warn("Failed to read cache:", e);
    }
    return null;
  }, [cacheKey, cacheTime]);

  // 保存数据到缓存
  const setCachedData = useCallback(
    (dataToCache) => {
      if (!cacheKey) return;
      try {
        localStorage.setItem(
          cacheKey,
          JSON.stringify({
            data: dataToCache,
            timestamp: Date.now(),
          }),
        );
      } catch (e) {
        console.warn("Failed to save cache:", e);
      }
    },
    [cacheKey],
  );

  // 获取数据
  const fetchData = useCallback(
    async (force = false) => {
      if (!enabled) return;

      // 如果不是强制刷新，先尝试从缓存读取
      if (!force && cacheKey) {
        const cached = getCachedData();
        if (cached) {
          setData(cached);
          setLoading(false);
          return;
        }
      }

      try {
        setLoading(true);
        setError(null);

        const result = await fetchFn();
        const resultData = result?.data || result;

        setData(resultData);
        setCachedData(resultData);

        if (onSuccess) {
          onSuccess(resultData);
        }
      } catch (err) {
        const errorMessage =
          err?.response?.data?.detail || err?.message || "数据加载失败";
        setError(errorMessage);
        if (onError) {
          onError(err);
        } else {
          console.error("Dashboard data fetch error:", err);
        }
      } finally {
        setLoading(false);
      }
    },
    [
      enabled,
      fetchFn,
      cacheKey,
      getCachedData,
      setCachedData,
      onSuccess,
      onError,
    ],
  );

  // 初始加载
  useEffect(() => {
    if (enabled) {
      fetchData();
    }
  }, [enabled, fetchData]);

  // 定时刷新
  useEffect(() => {
    if (refetchInterval && enabled) {
      intervalRef.current = setInterval(() => {
        fetchData(true);
      }, refetchInterval);

      return () => {
        if (intervalRef.current) {
          clearInterval(intervalRef.current);
        }
      };
    }
  }, [refetchInterval, enabled, fetchData]);

  // 手动刷新
  const refetch = useCallback(() => {
    fetchData(true);
  }, [fetchData]);

  // 清除缓存
  const clearCache = useCallback(() => {
    if (cacheKey) {
      localStorage.removeItem(cacheKey);
    }
  }, [cacheKey]);

  return {
    data,
    loading,
    error,
    refetch,
    clearCache,
  };
}

/**
 * useMultipleDashboardData - 并行获取多个数据源
 */
export function useMultipleDashboardData(queries) {
  const [results, setResults] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    const fetchAll = async () => {
      try {
        setLoading(true);
        setError(null);

        const promises = queries.map((query) =>
          query.fetchFn().catch((err) => ({
            error: err?.response?.data?.detail || err?.message || "加载失败",
            key: query.key,
          })),
        );

        const results = await Promise.allSettled(promises);
        const dataMap = {};

        results.forEach((result, index) => {
          const key = queries[index].key;
          if (result.status === "fulfilled") {
            if (result.value.error) {
              dataMap[key] = { error: result.value.error };
            } else {
              dataMap[key] = {
                data: result.value?.data || result.value,
              };
            }
          } else {
            dataMap[key] = { error: result.reason?.message || "加载失败" };
          }
        });

        setResults(dataMap);
      } catch (err) {
        setError(err?.message || "数据加载失败");
      } finally {
        setLoading(false);
      }
    };

    if (queries.length > 0) {
      fetchAll();
    }
  }, [queries]);

  return { results, loading, error };
}
