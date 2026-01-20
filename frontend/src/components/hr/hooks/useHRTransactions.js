/**
 * useHRTransactions Hook
 * 管理人事事务相关的状态和逻辑
 */
import { useState, useEffect, useCallback } from "react";
import { hrApi } from "../../../services/api";

export function useHRTransactions() {
  const [transactions, setTransactions] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState({
    type: "all",
    status: "all",
    searchText: "",
  });
  const [statistics, setStatistics] = useState(null);

  // 事务类型映射
  const transactionTypeMap = {
    onboarding: { label: "入职", icon: "UserPlus", color: "emerald" },
    resignation: { label: "离职", icon: "UserMinus", color: "red" },
    confirmation: { label: "转正", icon: "UserCheck", color: "blue" },
    transfer: { label: "调岗", icon: "ArrowRightLeft", color: "amber" },
    promotion: { label: "晋升", icon: "TrendingUp", color: "purple" },
    salary_adjustment: {
      label: "调薪",
      icon: "BadgeDollarSign",
      color: "cyan",
    },
  };

  // 状态映射
  const statusMap = {
    pending: { label: "待处理", color: "amber" },
    approved: { label: "已批准", color: "blue" },
    completed: { label: "已完成", color: "emerald" },
    rejected: { label: "已拒绝", color: "red" },
  };

  // 加载事务列表
  const loadTransactions = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: 1,
        page_size: 50,
      };
      if (filter.type !== "all") {params.transaction_type = filter.type;}
      if (filter.status !== "all") {params.status = filter.status;}

      const response = await hrApi.transactions.list(params);
      setTransactions(response.data?.items || []);
    } catch (err) {
      console.error("加载人事事务失败:", err);
      // 使用模拟数据
      setTransactions([]);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  // 加载统计数据
  const loadStatistics = useCallback(async () => {
    try {
      const response = await hrApi.transactions.statistics();
      setStatistics(response.data);
    } catch (err) {
      console.error("加载统计数据失败:", err);
      setStatistics(null);
    }
  }, []);

  // 当筛选条件变化时重新加载
  useEffect(() => {
    loadTransactions();
    loadStatistics();
  }, [loadTransactions, loadStatistics]);

  return {
    // 数据
    transactions,
    statistics,
    // 加载状态
    loading,
    // 筛选条件
    filter,
    setFilter,
    // 映射表
    transactionTypeMap,
    statusMap,
    // 操作方法
    loadTransactions,
    loadStatistics,
  };
}
