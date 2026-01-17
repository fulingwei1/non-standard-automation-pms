/**
 * useSalesTeamFilters - 筛选器状态管理 Hook
 * 负责管理团队筛选器的状态和操作
 */

import { useState, useCallback, useMemo, useRef, useEffect } from "react";
import {
  getDefaultDateRange,
  QUICK_RANGE_PRESETS,
  formatAutoRefreshTime,
} from "../constants/salesTeamConstants";

// 自动刷新高亮显示时长（毫秒）
const AUTO_REFRESH_HIGHLIGHT_DURATION = 2400;

export const useSalesTeamFilters = (defaultRange) => {
  const resolvedDefaultRange = defaultRange || getDefaultDateRange();

  // 筛选状态
  const [filters, setFilters] = useState({
    departmentId: "all",
    region: "",
    startDate: resolvedDefaultRange.start,
    endDate: resolvedDefaultRange.end,
  });

  // 快捷时间段激活状态
  const [activeQuickRange, setActiveQuickRange] = useState("month");

  // 日期错误状态
  const [dateError, setDateError] = useState("");

  // 自动刷新状态
  const [lastAutoRefreshAt, setLastAutoRefreshAt] = useState(null);
  const [highlightAutoRefresh, setHighlightAutoRefresh] = useState(false);

  // 自动刷新定时器
  const autoRefreshTimerRef = useRef(null);

  /**
   * 处理筛选条件变化
   */
  const handleFilterChange = useCallback((field, value) => {
    // 如果是日期字段，清除快捷时间段选择
    if (field === "startDate" || field === "endDate") {
      setActiveQuickRange("");
    }
    setFilters((prev) => ({
      ...prev,
      [field]: value,
    }));
  }, []);

  /**
   * 应用快捷时间段
   */
  const handleApplyQuickRange = useCallback((rangeKey) => {
    const preset = QUICK_RANGE_PRESETS.find((item) => item.key === rangeKey);
    if (!preset) return;
    const range = preset.getRange();
    setFilters((prev) => ({
      ...prev,
      startDate: range.start,
      endDate: range.end,
    }));
    setActiveQuickRange(rangeKey);
  }, []);

  /**
   * 重置所有筛选条件
   */
  const handleResetFilters = useCallback(() => {
    const range = getDefaultDateRange();
    setFilters({
      departmentId: "all",
      region: "",
      startDate: range.start,
      endDate: range.end,
    });
    setActiveQuickRange("month");
  }, []);

  /**
   * 触发自动刷新提示
   */
  const triggerAutoRefreshToast = useCallback(() => {
    const refreshTime = new Date();
    setLastAutoRefreshAt(refreshTime);
    setHighlightAutoRefresh(true);
    if (autoRefreshTimerRef.current) {
      clearTimeout(autoRefreshTimerRef.current);
    }
    autoRefreshTimerRef.current = setTimeout(() => {
      setHighlightAutoRefresh(false);
    }, AUTO_REFRESH_HIGHLIGHT_DURATION);
  }, []);

  /**
   * 验证日期范围
   */
  const validateDateRange = useCallback(() => {
    if (filters.startDate && filters.endDate) {
      const start = new Date(filters.startDate);
      const end = new Date(filters.endDate);
      if (start > end) {
        setDateError("开始日期不能晚于结束日期");
        return false;
      }
    }
    setDateError("");
    return true;
  }, [filters.startDate, filters.endDate]);

  /**
   * 获取筛选器摘要（用于显示）
   */
  const filterSummary = useMemo(() => {
    return {
      ...filters,
      isValid: !dateError,
      lastRefreshTime: lastAutoRefreshAt
        ? formatAutoRefreshTime(lastAutoRefreshAt)
        : null,
    };
  }, [filters, dateError, lastAutoRefreshAt]);

  /**
   * 清理定时器
   */
  useEffect(() => {
    return () => {
      if (autoRefreshTimerRef.current) {
        clearTimeout(autoRefreshTimerRef.current);
      }
    };
  }, []);

  return {
    // 状态
    filters,
    activeQuickRange,
    dateError,
    lastAutoRefreshAt,
    highlightAutoRefresh,
    filterSummary,

    // 操作方法
    handleFilterChange,
    handleApplyQuickRange,
    handleResetFilters,
    triggerAutoRefreshToast,
    validateDateRange,
  };
};
