import { useState, useCallback, useEffect, useMemo } from "react";
import { contractApi } from "../../../services/api";

export function useContractList() {
  const [contracts, setContracts] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedContract, setSelectedContract] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);

  // Legacy filter shape kept for consumers that rely on the { status, type, keyword } API
  const [filters, setFilters] = useState({ status: "", type: "", keyword: "" });
  const [pagination, setPagination] = useState({
    page: 1,
    pageSize: 20,
    total: 0,
  });

  const loadContracts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page: pagination.page,
        page_size: pagination.pageSize,
      };
      if (filters.status && filters.status !== "all")
        params.status = filters.status;
      if (filters.type && filters.type !== "all") params.type = filters.type;
      if (filters.keyword) params.keyword = filters.keyword;

      const response = await contractApi.list(params);
      const data = response.data || response;
      const items = data.items || data || [];
      setContracts(Array.isArray(items) ? items : []);
      if (data.total) setPagination((prev) => ({ ...prev, total: data.total }));
    } catch (err) {
      console.error("Contract API error:", err);
      setError("加载合同数据失败，请稍后重试");
      setContracts([]);
    } finally {
      setLoading(false);
    }
  }, [pagination.page, pagination.pageSize, filters]);

  useEffect(() => {
    loadContracts();
  }, [loadContracts]);

  // Client-side filter applied on top of whatever the API returned
  const filteredContracts = useMemo(() => {
    return (contracts || []).filter((contract) => {
      const searchLower = (searchTerm || "").toLowerCase();
      const matchesSearch =
        !searchTerm ||
        (contract.name || "").toLowerCase().includes(searchLower) ||
        (contract.id || "").toLowerCase().includes(searchLower) ||
        (contract.customerShort || "").toLowerCase().includes(searchLower);
      const matchesStatus =
        selectedStatus === "all" || contract.status === selectedStatus;
      return matchesSearch && matchesStatus;
    });
  }, [contracts, searchTerm, selectedStatus]);

  // Aggregate stats derived from the full contracts list
  const stats = useMemo(() => {
    const active = (contracts || []).filter((c) => c.status === "active");
    return {
      total: contracts.length,
      active: active.length,
      completed: (contracts || []).filter((c) => c.status === "completed")
        .length,
      totalValue: active.reduce((sum, c) => sum + (c.totalAmount || 0), 0),
      paidValue: active.reduce((sum, c) => sum + (c.paidAmount || 0), 0),
      pendingValue: active.reduce(
        (sum, c) => sum + ((c.totalAmount || 0) - (c.paidAmount || 0)),
        0
      ),
    };
  }, [contracts]);

  const handleContractClick = useCallback((contract) => {
    setSelectedContract(contract);
  }, []);

  return {
    // Raw data
    contracts,
    loading,
    error,
    // Derived
    filteredContracts,
    stats,
    // UI state — search / status filter (inline client-side)
    searchTerm,
    setSearchTerm,
    selectedStatus,
    setSelectedStatus,
    // UI state — panels / dialogs
    selectedContract,
    setSelectedContract,
    showCreateDialog,
    setShowCreateDialog,
    // Handlers
    handleContractClick,
    loadContracts,
    // Legacy filter / pagination API
    filters,
    setFilters,
    pagination,
    setPagination,
  };
}
