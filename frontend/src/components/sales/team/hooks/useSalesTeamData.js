/**
 * useSalesTeamData - 团队数据获取 Hook
 * 负责获取和处理销售团队数据
 */

import { useState, useCallback, useEffect, useMemo as _useMemo } from "react";
import {
  salesStatisticsApi,
  salesTeamApi,
  salesTargetApi,
  customerApi,
  orgApi } from
"../../../../services/api";
import {
  transformTeamMember,
  calculateTeamStats,
  aggregateTargets } from
"../utils/salesTeamTransformers";
import { DEFAULT_TEAM_STATS } from "@/lib/constants/salesTeam";

export const useSalesTeamData = (filters, defaultRange, triggerAutoRefreshToast) => {
  const [loading, setLoading] = useState(false);
  const [teamMembers, setTeamMembers] = useState([]);
  const [teamStats, setTeamStats] = useState(DEFAULT_TEAM_STATS);
  const [error, setError] = useState(null);
  const [departmentOptions, setDepartmentOptions] = useState([
  { label: "全部", value: "all" }]
  );
  const [regionOptions, setRegionOptions] = useState([]);

  /**
   * 更新区域选项列表
   */
  const updateRegionOptions = useCallback((members) => {
    const options = Array.from(
      new Set(
        members.map((member) => (member.region || "").trim()).filter(Boolean)
      )
    ).sort((a, b) => a.localeCompare(b, "zh-Hans-CN"));
    setRegionOptions(options);
  }, []);

  /**
   * 获取部门列表
   */
  useEffect(() => {
    const fetchDepartments = async () => {
      try {
        const res = await orgApi.departments({ page: 1, page_size: 100 });
        const payload = res.data?.data || res.data || res;
        const list = payload.items || payload.data || [];
        const options = Array.isArray(list) ?
        list.map((dept) => ({
          label: dept.dept_name || dept.name || `部门${dept.id}`,
          value: String(dept.id)
        })) :
        [];
        setDepartmentOptions([{ label: "全部", value: "all" }, ...options]);
      } catch (err) {
        console.error("获取部门列表失败:", err);
      }
    };
    fetchDepartments();
  }, []);

  /**
   * 获取团队数据
   */
  const fetchTeamData = useCallback(async () => {
    setLoading(true);
    try {
      const requestParams = {};
      // department_id 为 "all" 时不传递该参数（后端期望 Optional[int]）
      if (filters.departmentId && filters.departmentId !== "all") {
        requestParams.department_id = parseInt(filters.departmentId, 10);
      }
      if (filters.region) {requestParams.region = filters.region.trim();}
      if (filters.startDate) {requestParams.start_date = filters.startDate;}
      if (filters.endDate) {requestParams.end_date = filters.endDate;}

      const startDateValue = filters.startDate ?
      new Date(filters.startDate) :
      new Date(defaultRange.start);
      const endDateValue = filters.endDate ?
      new Date(filters.endDate) :
      new Date(defaultRange.end);
      const targetPeriodValue = filters.startDate ?
      filters.startDate.slice(0, 7) :
      `${startDateValue.getFullYear()}-${String(startDateValue.getMonth() + 1).padStart(2, "0")}`;

      // 并行请求多个接口
      const [teamRes, summaryRes, targetRes, customerRes] =
      await Promise.allSettled([
      salesTeamApi.getTeam(requestParams),
      salesStatisticsApi.summary({
        start_date: filters.startDate || defaultRange.start,
        end_date: filters.endDate || defaultRange.end
      }),
      salesTargetApi.list({
        target_scope: "TEAM",
        target_period: "MONTHLY",
        period_value: targetPeriodValue,
        status: "ACTIVE",
        page: 1,
        page_size: 100
      }),
      customerApi.list({
        page: 1,
        page_size: 100
      })]
      );

      // 处理团队成员数据
      let normalizedMembers = [];
      if (teamRes.status === "fulfilled") {
        const payload =
        teamRes.value.data?.data || teamRes.value.data || teamRes.value || {};
        const list = payload.team_members || payload.items || [];
        normalizedMembers = Array.isArray(list) ?
        list.map(transformTeamMember) :
        [];
      }

      // 如果没有团队成员数据，优雅地处理
      if (!normalizedMembers.length) {
        console.warn("No team members found");
        setTeamMembers([]);
        setTeamStats(calculateTeamStats([], {}));
        updateRegionOptions([]);
        setError(null);
        triggerAutoRefreshToast();
        return;
      }

      setTeamMembers(normalizedMembers);
      updateRegionOptions(normalizedMembers);

      // 处理汇总数据
      const summaryRaw =
      summaryRes.status === "fulfilled" ?
      summaryRes.value.data?.data ||
      summaryRes.value.data ||
      summaryRes.value ||
      {} :
      {};

      // 处理目标数据
      let targetSummary = null;
      if (targetRes.status === "fulfilled") {
        const payload =
        targetRes.value.data?.data ||
        targetRes.value.data ||
        targetRes.value ||
        {};
        const list =
        payload.items || payload.data?.items || payload.team_targets || [];
        targetSummary = aggregateTargets(Array.isArray(list) ? list : []);
      }

      // 处理客户数据
      let customerSummary = null;
      if (customerRes.status === "fulfilled") {
        const payload =
        customerRes.value.data?.data ||
        customerRes.value.data ||
        customerRes.value ||
        {};
        const list = payload.items || payload.data?.items || [];
        const totalCustomers =
        payload.total ?? payload.data?.total ?? payload.count ?? null;
        const newCustomersInRange = Array.isArray(list) ?
        list.filter((customer) => {
          const createdAt = customer.created_at || customer.createdAt;
          if (!createdAt) {return false;}
          const createdDate = new Date(createdAt);
          return (
            createdDate >= startDateValue && createdDate <= endDateValue);

        }).length :
        null;
        customerSummary = {
          totalCustomers,
          newCustomersThisMonth: newCustomersInRange
        };
      }

      // 合并所有数据
      const enrichedSummary = {
        ...summaryRaw,
        team_target_value:
        targetSummary?.targetValue ?? summaryRaw?.team_target_value,
        team_actual_value:
        targetSummary?.actualValue ?? summaryRaw?.team_actual_value,
        team_completion_rate: targetSummary ?
        Number(targetSummary.completionRate.toFixed(1)) :
        summaryRaw?.team_completion_rate,
        customer_total:
        customerSummary?.totalCustomers ?? summaryRaw?.customer_total,
        customer_new_this_month:
        customerSummary?.newCustomersThisMonth ??
        summaryRaw?.customer_new_this_month
      };

      setTeamStats(calculateTeamStats(normalizedMembers, enrichedSummary));
      setError(null);
      triggerAutoRefreshToast();
    } catch (err) {
      console.error("Failed to fetch sales team data:", err);
      setError(err.response?.data?.detail || err.message || "获取团队数据失败");
      setTeamMembers([]);
      setTeamStats(DEFAULT_TEAM_STATS);
      updateRegionOptions([]);
      triggerAutoRefreshToast();
    } finally {
      setLoading(false);
    }
  }, [
  filters.departmentId,
  filters.region,
  filters.startDate,
  filters.endDate,
  defaultRange,
  triggerAutoRefreshToast,
  updateRegionOptions]
  );

  return {
    // 数据状态
    loading,
    teamMembers,
    teamStats,
    error,
    departmentOptions,
    regionOptions,

    // 操作方法
    fetchTeamData
  };
};