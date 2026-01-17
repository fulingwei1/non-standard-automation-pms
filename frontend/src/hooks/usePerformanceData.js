import { useState, useEffect } from "react";
import { performanceApi } from "../services/api";

/**
 * 自定义Hook：管理绩效数据加载
 */
export const usePerformanceData = (fallbackData) => {
  const [isLoading, setIsLoading] = useState(false);
  const [performanceData, setPerformanceData] = useState(null);
  const [error, setError] = useState(null);

  const loadPerformanceData = async () => {
    try {
      setIsLoading(true);
      setError(null);
      const response = await performanceApi.getMyPerformance();
      setPerformanceData(response.data);
    } catch (err) {
      console.error("加载绩效数据失败:", err);
      setError(err.response?.data?.detail || "加载失败");
      // Fallback to mock data
      setPerformanceData(fallbackData);
    } finally {
      setIsLoading(false);
    }
  };

  useEffect(() => {
    loadPerformanceData();
  }, []); // fallbackData 通常是常量，不需要作为依赖

  return {
    performanceData,
    isLoading,
    error,
    refetch: loadPerformanceData,
  };
};
