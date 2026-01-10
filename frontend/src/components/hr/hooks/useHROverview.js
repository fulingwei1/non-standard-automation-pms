/**
 * useHROverview Hook
 * 管理 HR 概览 Tab 相关的状态和逻辑
 */
import { useState, useCallback } from "react";
import { hrApi } from "../../../services/api";

export function useHROverview() {
  const [pendingRecruitments, setPendingRecruitments] = useState([]);
  const [pendingReviews, setPendingReviews] = useState([]);
  const [departmentDistribution, setDepartmentDistribution] = useState([]);
  const [performanceDistribution, setPerformanceDistribution] = useState([]);
  const [loading, setLoading] = useState(false);

  // 加载待处理招聘
  const loadPendingRecruitments = useCallback(async () => {
    try {
      const response = await hrApi.recruitments.list({
        status: "pending",
        limit: 10,
      });
      setPendingRecruitments(response.data?.items || []);
    } catch (err) {
      console.error("加载待处理招聘失败:", err);
      setPendingRecruitments([]);
    }
  }, []);

  // 加载待绩效评审
  const loadPendingReviews = useCallback(async () => {
    try {
      const response = await hrApi.performance.list({
        status: "pending",
        limit: 10,
      });
      setPendingReviews(response.data?.items || []);
    } catch (err) {
      console.error("加载待绩效评审失败:", err);
      setPendingReviews([]);
    }
  }, []);

  // 加载部门分布
  const loadDepartmentDistribution = useCallback(async () => {
    try {
      const response = await hrApi.departments.statistics();
      setDepartmentDistribution(response.data || []);
    } catch (err) {
      console.error("加载部门分布失败:", err);
      setDepartmentDistribution([]);
    }
  }, []);

  // 加载绩效分布
  const loadPerformanceDistribution = useCallback(async () => {
    try {
      const response = await hrApi.performance.distribution();
      setPerformanceDistribution(response.data || []);
    } catch (err) {
      console.error("加载绩效分布失败:", err);
      setPerformanceDistribution([]);
    }
  }, []);

  // 加载所有数据
  const loadAll = useCallback(async () => {
    setLoading(true);
    try {
      await Promise.all([
        loadPendingRecruitments(),
        loadPendingReviews(),
        loadDepartmentDistribution(),
        loadPerformanceDistribution(),
      ]);
    } finally {
      setLoading(false);
    }
  }, [
    loadPendingRecruitments,
    loadPendingReviews,
    loadDepartmentDistribution,
    loadPerformanceDistribution,
  ]);

  return {
    // 数据
    pendingRecruitments,
    pendingReviews,
    departmentDistribution,
    performanceDistribution,
    // 加载状态
    loading,
    // 操作方法
    loadAll,
    loadPendingRecruitments,
    loadPendingReviews,
    loadDepartmentDistribution,
    loadPerformanceDistribution,
  };
}
