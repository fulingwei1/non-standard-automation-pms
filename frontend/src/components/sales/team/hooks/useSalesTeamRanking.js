/**
 * useSalesTeamRanking - 业绩排名数据 Hook
 * 负责获取和管理销售业绩排名数据
 */

import { useState, useEffect, useCallback, useMemo } from "react";
import { salesTeamApi } from "../../../../services/api";
import {
  DEFAULT_RANKING_METRICS,
  FALLBACK_RANKING_FIELDS,
  buildMetricDetailMap as _buildMetricDetailMap } from
"@/lib/constants/salesTeam";

export const useSalesTeamRanking = (filters, showRanking, dateError) => {
  const [loading, setRankingLoading] = useState(false);
  const [data, setRankingData] = useState([]);
  const [config, setRankingConfig] = useState(null);
  const [rankingType, setRankingType] = useState("score");

  /**
   * 获取排名数据
   */
  const fetchRanking = useCallback(async () => {
    if (!showRanking || dateError) {
      if (dateError) {
        setRankingData([]);
      }
      return;
    }
    setRankingLoading(true);
    try {
      const params = {
        ranking_type: rankingType,
        limit: 20
      };
      // department_id 为 "all" 时不传递该参数（后端期望 Optional[int]）
      if (filters.departmentId && filters.departmentId !== "all") {
        params.department_id = parseInt(filters.departmentId, 10);
      }
      if (filters.region) {params.region = filters.region.trim();}
      if (filters.startDate) {params.start_date = filters.startDate;}
      if (filters.endDate) {params.end_date = filters.endDate;}
      const res = await salesTeamApi.getRanking(params);
      const payload = res.data?.data || res.data || res;
      setRankingData(payload.rankings || []);
      setRankingConfig(payload.config || null);
    } catch (err) {
      console.error("Failed to fetch ranking data:", err);
      setRankingData([]);
      setRankingConfig(null);
    } finally {
      setRankingLoading(false);
    }
  }, [
  showRanking,
  rankingType,
  filters.departmentId,
  filters.region,
  filters.startDate,
  filters.endDate,
  dateError]
  );

  /**
   * 自动刷新排名数据
   */
  useEffect(() => {
    fetchRanking();
  }, [fetchRanking]);

  /**
   * 指标配置列表（按权重排序）
   */
  const metricConfigList = useMemo(() => {
    const metrics =
    config?.metrics?.length > 0 ?
    config.metrics :
    DEFAULT_RANKING_METRICS;
    return [...metrics].sort((a, b) => Number(b.weight || 0) - Number(a.weight || 0));
  }, [config]);

  /**
   * 排名选项列表
   */
  const rankingOptions = useMemo(() => {
    const options = [{ value: "score", label: "综合得分" }];
    const seenValues = new Set(["score"]);
    metricConfigList.forEach((metric) => {
      const value = metric.data_source || metric.key;
      if (!value || seenValues.has(value)) {return;}
      seenValues.add(value);
      options.push({
        value,
        label: metric.label || metric.key || value
      });
    });
    // 如果没有指标配置，使用备选字段
    if (options.length === 1) {
      FALLBACK_RANKING_FIELDS.forEach((field) => {
        if (seenValues.has(field.value)) {return;}
        seenValues.add(field.value);
        options.push(field);
      });
    }
    // 验证当前 rankingType 是否有效，如果无效则重置为 "score"
    if (!options.some((option) => option.value === rankingType)) {
      setRankingType("score");
    }
    return options;
  }, [metricConfigList, rankingType]);

  /**
   * 当前选中的排名选项
   */
  const selectedRankingOption = useMemo(
    () => rankingOptions.find((option) => option.value === rankingType),
    [rankingOptions, rankingType]
  );

  return {
    // 数据状态
    loading,
    data,
    config,
    rankingType,
    metricConfigList,
    rankingOptions,
    selectedRankingOption,

    // 操作方法
    setRankingType,
    refreshRanking: fetchRanking
  };
};