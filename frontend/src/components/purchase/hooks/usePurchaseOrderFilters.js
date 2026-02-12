/**
 * usePurchaseOrderFilters - 采购订单筛选管理 Hook
 * 管理搜索、状态筛选、排序等筛选逻辑
 */

import { useState, useCallback, useMemo } from "react";
import { PurchaseOrderUtils } from "@/lib/constants/procurement";

export const usePurchaseOrderFilters = (initialState = {}) => {
  // 搜索和筛选状态
  const [searchQuery, setSearchQuery] = useState(initialState.search || "");
  const [statusFilter, setStatusFilter] = useState(initialState.status || "all");
  const [sortBy, setSortBy] = useState(initialState.sortBy || "expected_date");
  const [sortOrder, setSortOrder] = useState(initialState.sortOrder || "asc");

  /**
   * 处理搜索输入变化
   */
  const handleSearchChange = useCallback((value) => {
    setSearchQuery(value);
  }, []);

  /**
   * 处理状态筛选变化
   */
  const handleStatusFilterChange = useCallback((value) => {
    setStatusFilter(value);
  }, []);

  /**
   * 处理排序字段变化
   */
  const handleSortChange = useCallback((value) => {
    setSortBy(value);
  }, []);

  /**
   * 切换排序顺序
   */
  const handleSortOrderToggle = useCallback(() => {
    setSortOrder((prev) => (prev === "asc" ? "desc" : "asc"));
  }, []);

  /**
   * 重置所有筛选条件
   */
  const handleReset = useCallback(() => {
    setSearchQuery("");
    setStatusFilter("all");
    setSortBy("expected_date");
    setSortOrder("asc");
  }, []);

  /**
   * 应用筛选和排序到订单列表
   */
  const applyFilters = useCallback(
    (orders) => {
      // 搜索过滤
      let filtered = PurchaseOrderUtils.searchOrders(orders, searchQuery);

      // 状态过滤
      if (statusFilter && statusFilter !== "all") {
        filtered = filtered.filter((order) => order.status === statusFilter);
      }

      // 排序
      filtered = PurchaseOrderUtils.sortOrders(filtered, sortBy, sortOrder);

      return filtered;
    },
    [searchQuery, statusFilter, sortBy, sortOrder]
  );

  /**
   * 获取筛选后的订单数量
   */
  const getFilteredCount = useCallback(
    (orders) => {
      return applyFilters(orders).length;
    },
    [applyFilters]
  );

  /**
   * 检查是否有激活的筛选条件
   */
  const hasActiveFilters = useMemo(() => {
    return searchQuery !== "" || statusFilter !== "all";
  }, [searchQuery, statusFilter]);

  /**
   * 获取激活的筛选条件数量
   */
  const activeFiltersCount = useMemo(() => {
    let count = 0;
    if (searchQuery !== "") {count++;}
    if (statusFilter !== "all") {count++;}
    return count;
  }, [searchQuery, statusFilter]);

  /**
   * 获取筛选条件的摘要文本
   */
  const getFiltersSummary = useCallback(() => {
    const summaries = [];

    if (searchQuery) {
      summaries.push(`搜索: "${searchQuery}"`);
    }

    if (statusFilter && statusFilter !== "all") {
      const statusLabels = {
        draft: "草稿",
        pending: "待收货",
        partial_received: "部分到货",
        completed: "已完成",
        delayed: "延期",
        cancelled: "已取消",
      };
      summaries.push(`状态: ${statusLabels[statusFilter] || statusFilter}`);
    }

    const sortLabels = {
      expected_date: "预计到货日期",
      createdDate: "创建日期",
      totalAmount: "订单金额",
    };

    summaries.push(
      `排序: ${sortLabels[sortBy] || sortBy} (${sortOrder === "asc" ? "升序" : "降序"})`
    );

    return summaries.join(" | ");
  }, [searchQuery, statusFilter, sortBy, sortOrder]);

  return {
    // 状态
    searchQuery,
    statusFilter,
    sortBy,
    sortOrder,
    hasActiveFilters,
    activeFiltersCount,
    // 方法
    setSearchQuery: handleSearchChange,
    setStatusFilter: handleStatusFilterChange,
    setSortBy: handleSortChange,
    setSortOrder: setSortOrder,
    toggleSortOrder: handleSortOrderToggle,
    resetFilters: handleReset,
    applyFilters,
    getFilteredCount,
    getFiltersSummary,
  };
};
