/**
 * Acceptance Management — custom hook encapsulating all state and data logic
 */

import { useState, useEffect, useMemo } from "react";

import { toast } from "../../components/ui";
import { acceptanceApi } from "../../services/api/acceptance";
import { projectApi } from "../../services/api/projects";

const useAcceptanceManagement = () => {
  const [loading, setLoading] = useState(false);
  const [projects, setProjects] = useState([]);
  const [records, setRecords] = useState([]);
  const [stats, setStats] = useState({ total: 0, passed: 0, failed: 0, pending: 0 });
  const [searchText, setSearchText] = useState("");
  const [filters, setFilters] = useState({ type: "", status: "" });
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [selectedRecord, setSelectedRecord] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);

  // 加载项目列表
  useEffect(() => {
    loadProjects();
  }, []);

  // 加载验收记录
  useEffect(() => {
    loadRecords();
  }, [filters]);

  const loadProjects = async () => {
    try {
      const res = await projectApi.list({ page: 1, page_size: 200 });
      const items = res?.data?.items || res?.data || [];
      setProjects(items);
    } catch (_err) {
      setProjects([]);
    }
  };

  const loadRecords = async () => {
    setLoading(true);
    try {
      const params = { page: 1, page_size: 100 };
      if (filters.type) params.acceptance_type = filters.type;
      if (filters.status) params.status = filters.status;

      const res = await acceptanceApi.list(params);
      const items = res?.data?.items || [];
      setRecords(items);

      // 计算统计
      const total = items.length;
      const passed = items.filter(r => r.status === "passed" || r.status === "signed").length;
      const failed = items.filter(r => r.status === "failed").length;
      const pending = items.filter(r => r.status === "draft" || r.status === "in_progress").length;

      setStats({ total, passed, failed, pending });
    } catch (_err) {
      toast.error("加载验收记录失败");
      setRecords([]);
      setStats({ total: 0, passed: 0, failed: 0, pending: 0 });
    } finally {
      setLoading(false);
    }
  };

  // 过滤数据
  const filteredRecords = useMemo(() => {
    return records.filter((record) => {
      const searchLower = (searchText || "").toLowerCase();
      const matchesSearch =
        !searchText ||
        (record.title || "").toLowerCase().includes(searchLower) ||
        (record.project_name || "").toLowerCase().includes(searchLower) ||
        (record.acceptance_code || "").toLowerCase().includes(searchLower) ||
        (record.customer_representative || "").toLowerCase().includes(searchLower);

      return matchesSearch;
    });
  }, [records, searchText]);

  const handleCreate = async (formData) => {
    try {
      await acceptanceApi.create(formData);
      toast.success("创建成功");
      setShowCreateDialog(false);
      loadRecords();
    } catch (_err) {
      toast.error("创建失败");
    }
  };

  const handleViewDetail = async (id) => {
    try {
      const res = await acceptanceApi.detail(id);
      setSelectedRecord(res?.data || res);
      setShowDetailDialog(true);
    } catch (_err) {
      toast.error("加载详情失败");
    }
  };

  const handleStart = async (id) => {
    try {
      await acceptanceApi.orders.start(id, { location: "" });
      toast.success("验收已开始");
      loadRecords();
    } catch (err) {
      toast.error(err?.response?.data?.detail || "开始验收失败");
    }
  };

  return {
    loading,
    projects,
    stats,
    filteredRecords,
    searchText,
    setSearchText,
    filters,
    setFilters,
    showCreateDialog,
    setShowCreateDialog,
    selectedRecord,
    showDetailDialog,
    setShowDetailDialog,
    handleCreate,
    handleViewDetail,
    handleStart,
    loadRecords,
  };
};

export default useAcceptanceManagement;
