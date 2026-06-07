/**
 * 销售工作站 Hooks
 *
 * 提供 P0/P1 功能的数据获取 hooks：
 * - 智能跟进提醒
 * - 催款优先级排序
 * - 商机健康度评分
 * - 合同里程碑提醒
 */

import { useState, useEffect, useCallback } from "react";
import {
  followUpReminderApi,
  collectionPriorityApi,
  opportunityHealthApi,
  contractMilestoneApi,
  quickCostApi,
  quoteComparisonApi,
  salesStatisticsApi,
} from "../services/api/sales";
import { pmoApi } from "../services/api/pmo";

const getResponsePayload = (response) => response?.data?.data ?? response?.data ?? {};

function formatDateParam(date) {
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, "0");
  const day = String(date.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

function getCurrentMonthRange(now = new Date()) {
  return {
    start_date: formatDateParam(new Date(now.getFullYear(), now.getMonth(), 1)),
    end_date: formatDateParam(new Date(now.getFullYear(), now.getMonth() + 1, 0)),
  };
}

function readStoredUser() {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const rawUser = window.localStorage.getItem("user");
    return rawUser ? JSON.parse(rawUser) : null;
  } catch (_error) {
    return null;
  }
}

function countUniqueInitiations(items = []) {
  const keys = new Set();
  (items || []).forEach((item) => {
    const key = item?.contract_no || item?.project_id || item?.id;
    if (key) {
      keys.add(String(key));
    }
  });
  return keys.size;
}

/**
 * 智能跟进提醒 Hook
 */
export function useFollowUpReminders(options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { autoFetch = true, ...params } = options;

  const fetch = useCallback(async (fetchParams = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await followUpReminderApi.list({ ...params, ...fetchParams });
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "获取跟进提醒失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (autoFetch) {
      fetch();
    }
  }, [autoFetch]);

  return { data, loading, error, refetch: fetch };
}

/**
 * 跟进提醒汇总 Hook
 */
export function useFollowUpSummary() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await followUpReminderApi.getSummary();
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "获取跟进汇总失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, []);

  return { data, loading, error, refetch: fetch };
}

/**
 * 催款优先级 Hook
 */
export function useCollectionPriority(options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { autoFetch = true, ...params } = options;

  const fetch = useCallback(async (fetchParams = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await collectionPriorityApi.list({ ...params, ...fetchParams });
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "获取催款优先级失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (autoFetch) {
      fetch();
    }
  }, [autoFetch]);

  return { data, loading, error, refetch: fetch };
}

/**
 * 催款优先级汇总 Hook
 */
export function useCollectionSummary() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await collectionPriorityApi.getSummary();
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "获取催款汇总失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, []);

  return { data, loading, error, refetch: fetch };
}

/**
 * 商机健康度 Hook
 */
export function useOpportunityHealth(opportunityId) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    if (!opportunityId) {
      setLoading(false);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const response = await opportunityHealthApi.get(opportunityId);
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "获取商机健康度失败");
    } finally {
      setLoading(false);
    }
  }, [opportunityId]);

  useEffect(() => {
    fetch();
  }, [opportunityId]);

  return { data, loading, error, refetch: fetch };
}

/**
 * 商机健康度列表 Hook
 */
export function useOpportunityHealthList(options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { autoFetch = true, ...params } = options;

  const fetch = useCallback(async (fetchParams = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await opportunityHealthApi.list({ ...params, ...fetchParams });
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "获取商机健康度列表失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (autoFetch) {
      fetch();
    }
  }, [autoFetch]);

  return { data, loading, error, refetch: fetch };
}

/**
 * 商机健康度汇总 Hook
 */
export function useOpportunityHealthSummary() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await opportunityHealthApi.getSummary();
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "获取健康度汇总失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, []);

  return { data, loading, error, refetch: fetch };
}

/**
 * 合同里程碑 Hook
 */
export function useContractMilestones(options = {}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const { autoFetch = true, ...params } = options;

  const fetch = useCallback(async (fetchParams = {}) => {
    setLoading(true);
    setError(null);
    try {
      const response = await contractMilestoneApi.list({ ...params, ...fetchParams });
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "获取合同里程碑失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    if (autoFetch) {
      fetch();
    }
  }, [autoFetch]);

  return { data, loading, error, refetch: fetch };
}

/**
 * 合同里程碑汇总 Hook
 */
export function useContractMilestoneSummary() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const response = await contractMilestoneApi.getSummary();
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "获取里程碑汇总失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetch();
  }, []);

  return { data, loading, error, refetch: fetch };
}

/**
 * 一键成本推荐 Hook
 */
export function useQuickCost(type, id) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const fetch = useCallback(async () => {
    if (!id) return;
    setLoading(true);
    setError(null);
    try {
      const response =
        type === "opportunity"
          ? await quickCostApi.getForOpportunity(id)
          : await quickCostApi.getForQuote(id);
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "获取成本推荐失败");
    } finally {
      setLoading(false);
    }
  }, [type, id]);

  return { data, loading, error, fetch };
}

/**
 * 报价对比 Hook
 */
export function useQuoteComparison() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const compareVersions = useCallback(async (quoteId, versionIds) => {
    setLoading(true);
    setError(null);
    try {
      const response = await quoteComparisonApi.compareVersions(quoteId, versionIds);
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "对比报价版本失败");
    } finally {
      setLoading(false);
    }
  }, []);

  const compareByOpportunity = useCallback(async (oppId) => {
    setLoading(true);
    setError(null);
    try {
      const response = await quoteComparisonApi.compareByOpportunity(oppId);
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "对比商机报价失败");
    } finally {
      setLoading(false);
    }
  }, []);

  const compareWithCompetitor = useCallback(async (quoteId, competitorPrice, competitorName) => {
    setLoading(true);
    setError(null);
    try {
      const response = await quoteComparisonApi.compareWithCompetitor(
        quoteId,
        competitorPrice,
        competitorName
      );
      setData(response.data?.data || response.data);
    } catch (err) {
      setError(err.message || "对比竞品报价失败");
    } finally {
      setLoading(false);
    }
  }, []);

  return {
    data,
    loading,
    error,
    compareVersions,
    compareByOpportunity,
    compareWithCompetitor,
  };
}

/**
 * 销售工作站综合数据 Hook
 * 一次性获取所有工作站所需数据
 */
export function useSalesWorkstationData() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [data, setData] = useState({
    followUpSummary: null,
    collectionSummary: null,
    healthSummary: null,
    milestoneSummary: null,
    salesFunnelSummary: null,
    initiationSummary: null,
  });

  const fetchAll = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const currentUser = readStoredUser();
      const funnelParams = getCurrentMonthRange();
      const initiationParams = {
        page: 1,
        page_size: 100,
        ...(currentUser?.id ? { applicant_id: currentUser.id } : {}),
      };

      const [followUp, collection, health, milestone, funnel, initiations] = await Promise.allSettled([
        followUpReminderApi.getSummary(),
        collectionPriorityApi.getSummary(),
        opportunityHealthApi.getSummary(),
        contractMilestoneApi.getSummary(),
        salesStatisticsApi.funnel(funnelParams),
        pmoApi.initiations.list(initiationParams),
      ]);

      const initiationPayload = initiations.status === "fulfilled"
        ? getResponsePayload(initiations.value)
        : null;
      const initiationItems = Array.isArray(initiationPayload?.items)
        ? initiationPayload.items
        : [];
      const uniqueInitiationCount = countUniqueInitiations(initiationItems);

      setData({
        followUpSummary: followUp.status === "fulfilled" ? followUp.value.data?.data : null,
        collectionSummary: collection.status === "fulfilled" ? collection.value.data?.data : null,
        healthSummary: health.status === "fulfilled" ? health.value.data?.data : null,
        milestoneSummary: milestone.status === "fulfilled" ? milestone.value.data?.data : null,
        salesFunnelSummary: funnel.status === "fulfilled" ? getResponsePayload(funnel.value) : null,
        initiationSummary: initiationPayload
          ? {
            total_count: Number(initiationPayload.total || initiationItems.length || 0),
            unique_count: uniqueInitiationCount || Number(initiationPayload.total || 0),
          }
          : null,
      });
    } catch (err) {
      setError(err.message || "获取工作站数据失败");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchAll();
  }, []);

  return { data, loading, error, refetch: fetchAll };
}
