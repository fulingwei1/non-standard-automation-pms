/**
 * useHRContracts Hook
 * 管理合同管理相关的状态和逻辑
 */
import { useState, useEffect, useCallback, useMemo } from "react";
import { hrApi } from "../../../services/api";

export function useHRContracts() {
  const [contracts, setContracts] = useState([]);
  const [reminders, setReminders] = useState([]);
  const [loading, setLoading] = useState(true);
  const [activeSubTab, setActiveSubTab] = useState("all");
  const [filter, setFilter] = useState({
    status: "all",
    searchText: "",
  });

  // 合同类型映射
  const contractTypeMap = {
    fixed_term: "固定期限",
    indefinite: "无固定期限",
    project: "项目制",
    intern: "实习协议",
    labor_dispatch: "劳务派遣",
  };

  // 合同状态映射
  const contractStatusMap = {
    draft: { label: "草稿", color: "slate" },
    active: { label: "生效中", color: "emerald" },
    expired: { label: "已到期", color: "red" },
    terminated: { label: "已终止", color: "amber" },
    renewed: { label: "已续签", color: "blue" },
  };

  // 提醒类型映射
  const reminderTypeMap = {
    two_months: { label: "提前两月", color: "blue", days: 60 },
    one_month: { label: "提前一月", color: "amber", days: 30 },
    two_weeks: { label: "提前两周", color: "orange", days: 14 },
    expired: { label: "已到期", color: "red", days: 0 },
  };

  // 加载合同列表
  const loadContracts = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: 1,
        page_size: 50,
      };
      if (filter.status !== "all") params.status = filter.status;

      const response = await hrApi.contracts.list(params);
      setContracts(response.data?.items || []);
    } catch (err) {
      console.error("加载合同数据失败:", err);
      setContracts([]);
    } finally {
      setLoading(false);
    }
  }, [filter.status]);

  // 加载提醒列表
  const loadReminders = useCallback(async () => {
    try {
      const response = await hrApi.reminders.list({ status: "pending" });
      setReminders(response.data?.items || []);
    } catch (err) {
      console.error("加载提醒数据失败:", err);
      setReminders([]);
    }
  }, []);

  // 当筛选条件变化时重新加载
  useEffect(() => {
    loadContracts();
    loadReminders();
  }, [loadContracts, loadReminders]);

  // 筛选合同
  const filteredContracts = useMemo(() => {
    return contracts.filter((c) => {
      if (filter.searchText) {
        const search = filter.searchText.toLowerCase();
        const name = c.employee?.name?.toLowerCase() || "";
        const code = c.employee?.employee_code?.toLowerCase() || "";
        const contractNo = c.contract_no?.toLowerCase() || "";
        if (
          !name.includes(search) &&
          !code.includes(search) &&
          !contractNo.includes(search)
        )
          return false;
      }
      return true;
    });
  }, [contracts, filter.searchText]);

  return {
    // 数据
    contracts: filteredContracts,
    reminders,
    // 加载状态
    loading,
    // 子 Tab 状态
    activeSubTab,
    setActiveSubTab,
    // 筛选条件
    filter,
    setFilter,
    // 映射表
    contractTypeMap,
    contractStatusMap,
    reminderTypeMap,
    // 操作方法
    loadContracts,
    loadReminders,
  };
}
