import { useState, useEffect, useCallback } from "react";
import { shortageApi } from "../../../services/api";

/**
 * useShortageManagement
 *
 * Manages all state and data-fetching for the ShortageManagement page,
 * including: dashboard, reports (with search/pagination), arrivals,
 * substitutions, and transfers.
 */
export function useShortageManagement() {
  // Tab
  const [activeTab, setActiveTab] = useState("dashboard");

  // Data
  const [dashboardData, setDashboardData] = useState(null);
  const [reports, setReports] = useState([]);
  const [arrivals, setArrivals] = useState([]);
  const [substitutions, setSubstitutions] = useState([]);
  const [transfers, setTransfers] = useState([]);

  // UI state
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // Reports filters / pagination
  const [searchKeyword, setSearchKeyword] = useState("");
  const [statusFilter, setStatusFilter] = useState("");
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [total, setTotal] = useState(0);

  // Arrivals filters
  const [arrivalFilters, setArrivalFilters] = useState({
    status: "",
    is_delayed: false,
  });

  // ── Loaders ──────────────────────────────────────────────────────────────

  const loadDashboard = useCallback(async () => {
    try {
      const res = await shortageApi.statistics.dashboard();
      setDashboardData(res.data.data);
    } catch (err) {
      console.error("加载看板数据失败", err);
      setError(err.message);
    }
  }, []);

  const loadReports = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchKeyword || undefined,
        status: statusFilter || undefined,
      };
      const res = await shortageApi.reports.list(params);
      setReports(res.data.items || []);
      setTotal(res.data.total || 0);
    } catch (err) {
      console.error("加载缺料上报列表失败", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, searchKeyword, statusFilter]);

  const loadArrivals = useCallback(async () => {
    setLoading(true);
    try {
      const params = {
        page: 1,
        page_size: 20,
        status: arrivalFilters.status || undefined,
        is_delayed: arrivalFilters.is_delayed || undefined,
      };
      const res = await shortageApi.arrivals.list(params);
      setArrivals(res.data.items || []);
    } catch (err) {
      console.error("加载到货跟踪列表失败", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, [arrivalFilters]);

  const loadSubstitutions = useCallback(async () => {
    setLoading(true);
    try {
      const res = await shortageApi.substitutions.list({ page: 1, page_size: 20 });
      setSubstitutions(res.data.items || []);
    } catch (err) {
      console.error("加载物料替代列表失败", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  const loadTransfers = useCallback(async () => {
    setLoading(true);
    try {
      const res = await shortageApi.transfers.list({ page: 1, page_size: 20 });
      setTransfers(res.data.items || []);
    } catch (err) {
      console.error("加载物料调拨列表失败", err);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  }, []);

  /** Resolve a single shortage report; re-fetches list afterwards. */
  const resolveShortage = useCallback(
    async (id) => {
      try {
        await shortageApi.reports.resolve(id);
        await loadReports();
        return { success: true };
      } catch (err) {
        return { success: false, error: err.response?.data?.detail || err.message };
      }
    },
    [loadReports]
  );

  // ── Effects ──────────────────────────────────────────────────────────────

  // Always load dashboard on mount
  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  // Load tab-specific data when the active tab changes
  useEffect(() => {
    if (activeTab === "reports") {
      setPage(1);
      loadReports();
    } else if (activeTab === "arrivals") {
      loadArrivals();
    } else if (activeTab === "substitutions") {
      loadSubstitutions();
    } else if (activeTab === "transfers") {
      loadTransfers();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // Re-fetch reports when search / status filter changes (reset to page 1)
  useEffect(() => {
    if (activeTab === "reports") {
      setPage(1);
      loadReports();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [searchKeyword, statusFilter]);

  // Re-fetch reports when page changes (without resetting page)
  useEffect(() => {
    if (activeTab === "reports") {
      loadReports();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [page]);

  // Re-fetch arrivals when arrival filters change
  useEffect(() => {
    if (activeTab === "arrivals") {
      loadArrivals();
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [arrivalFilters]);

  // ── Return ────────────────────────────────────────────────────────────────

  return {
    // Tab
    activeTab,
    setActiveTab,

    // Data
    dashboardData,
    reports,
    arrivals,
    substitutions,
    transfers,

    // UI
    loading,
    error,

    // Reports filters / pagination
    searchKeyword,
    setSearchKeyword,
    statusFilter,
    setStatusFilter,
    page,
    setPage,
    pageSize,
    total,

    // Arrivals filters
    arrivalFilters,
    setArrivalFilters,

    // Actions
    loadDashboard,
    loadReports,
    loadArrivals,
    loadSubstitutions,
    loadTransfers,
    resolveShortage,
  };
}
