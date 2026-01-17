/**
 * usePreloadData - 数据预加载Hook
 * 结合 Intersection Observer 实现智能数据预加载
 */
import { useState } from "react";
import { usePreload } from "./useIntersectionObserver";

/**
 * 数据预加载Hook
 * 当元素进入视口时自动加载数据
 */
export function usePreloadData(config) {
  const {
    fetchFn,
    cacheKey,
    enabled = true,
    preloadDistance = 200,
    onSuccess,
    onError,
  } = config;

  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [hasLoaded, setHasLoaded] = useState(false);

  // 检查缓存
  const getCachedData = () => {
    if (!cacheKey) return null;
    try {
      const cached = localStorage.getItem(cacheKey);
      if (cached) {
        const { data: cachedData, timestamp } = JSON.parse(cached);
        const now = Date.now();
        // 缓存5分钟
        if (now - timestamp < 5 * 60 * 1000) {
          return cachedData;
        }
        localStorage.removeItem(cacheKey);
      }
    } catch (e) {
      console.warn("Failed to read cache:", e);
    }
    return null;
  };

  // 保存到缓存
  const setCachedData = (dataToCache) => {
    if (!cacheKey) return;
    try {
      localStorage.setItem(
        cacheKey,
        JSON.stringify({
          data: dataToCache,
          timestamp: Date.now(),
        })
      );
    } catch (e) {
      console.warn("Failed to save cache:", e);
    }
  };

  // 加载数据
  const loadData = async () => {
    if (hasLoaded || loading) return;

    // 先检查缓存
    const cached = getCachedData();
    if (cached) {
      setData(cached);
      setHasLoaded(true);
      if (onSuccess) onSuccess(cached);
      return;
    }

    try {
      setLoading(true);
      setError(null);

      const result = await fetchFn();
      const resultData = result?.data || result;

      setData(resultData);
      setCachedData(resultData);
      setHasLoaded(true);

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
        console.error("Preload data error:", err);
      }
    } finally {
      setLoading(false);
    }
  };

  // 使用 Intersection Observer 触发预加载
  const { elementRef, hasPreloaded } = usePreload(loadData, {
    enabled,
    preloadDistance,
  });

  return {
    elementRef,
    data,
    loading,
    error,
    hasPreloaded,
    hasLoaded,
    refetch: loadData,
  };
}
