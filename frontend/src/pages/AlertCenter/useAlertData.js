/**
 * Custom hook for Alert Center data management
 * Handles state, data loading, batch operations, and exports
 */

import { useState, useMemo, useEffect, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { toast } from "../../components/ui/toast";
import { alertApi, projectApi } from "../../services/api";

export default function useAlertData() {
  const navigate = useNavigate();
  const [alerts, setAlerts] = useState([]);
  const [stats, setStats] = useState({
    total: 0,
    pending: 0,
    resolved: 0,
    critical: 0,
    today_new: 0,
    urgent: 0,
    warning: 0
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [pageSize] = useState(20);
  const [searchQuery, setSearchQuery] = useState("");
  const [selectedLevel, setSelectedLevel] = useState("ALL");
  const [selectedStatus, setSelectedStatus] = useState("ALL");
  const [selectedProject, setSelectedProject] = useState("ALL");
  const [dateRange, setDateRange] = useState({ start: "", end: "" });
  const [showDetail, setShowDetail] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [showResolveDialog, setShowResolveDialog] = useState(false);
  const [showCloseDialog, setShowCloseDialog] = useState(false);
  const [resolveResult, setResolveResult] = useState("");
  const [_closeReason, setCloseReason] = useState("");
  const [selectedAlerts, setSelectedAlerts] = useState(new Set());
  const [sortBy, setSortBy] = useState("triggered_at");
  const [sortOrder, _setSortOrder] = useState("desc");
  const [projects, setProjects] = useState([]);

  // 加载项目列表
  const loadProjects = useCallback(async () => {
    try {
      const response = await projectApi.list({ page: 1, page_size: 1000 });
      const data = response.data || response;
      const projectList = data.items || data || [];

      const transformedProjects = (projectList || []).map((project) => ({
        id: project.id || project.project_code,
        name: project.project_name || ""
      }));

      setProjects(transformedProjects);
    } catch (error) {
      console.error("Failed to load projects:", error);
      const mockProjects = [
      { id: 1, name: "测试项目A" },
      { id: 2, name: "测试项目B" },
      { id: 3, name: "测试项目C" }];

      setProjects(mockProjects);
    }
  }, []);

  // 加载预警数据
  const loadAlerts = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const params = {
        page,
        page_size: pageSize
      };

      if (selectedLevel !== "ALL") {
        params.alert_level = selectedLevel;
      }
      if (selectedStatus !== "ALL") {
        params.status = selectedStatus === "ACTIVE" ? "PENDING" : selectedStatus;
      }
      if (selectedProject !== "ALL") {
        params.project_id = parseInt(selectedProject);
      }
      if (dateRange.start) {
        params.date_from = dateRange.start;
      }
      if (dateRange.end) {
        params.date_to = dateRange.end;
      }
      if (searchQuery) {
        params.keyword = searchQuery;
      }

      params.ordering = sortOrder === "desc" ? `-${sortBy}` : sortBy;

      const response = await alertApi.list(params);
      const data = response.data?.data || response.data || response;

      setAlerts(data.items || data || []);
      setTotal(data.total || data?.length || 0);
    } catch (error) {
      console.error("Failed to load alerts:", error);
      setError(error.response?.data?.detail || error.message || "加载预警失败");
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  }, [page, pageSize, selectedLevel, selectedStatus, selectedProject, dateRange, searchQuery, sortBy, sortOrder]);

  // 加载统计数据
  const loadStatistics = useCallback(async () => {
    try {
      const response = await alertApi.statistics();
      const data = response.data?.data || response.data || {};

      setStats({
        total: data.total || 0,
        pending: data.pending || 0,
        resolved: data.resolved || 0,
        critical: data.critical || 0,
        today_new: data.today_new || 0,
        urgent: data.urgent || 0,
        warning: data.warning || 0
      });
    } catch (error) {
      console.error("Failed to load statistics:", error);
    }
  }, []);

  // 初始化加载
  useEffect(() => {
    loadProjects();
  }, []);

  useEffect(() => {
    loadAlerts();
    loadStatistics();
  }, [loadAlerts, loadStatistics]);

  // 批量确认预警
  const handleBatchAcknowledge = useCallback(async () => {
    if (selectedAlerts.size === 0) {return;}

    try {
      const promises = Array.from(selectedAlerts).map((id) =>
      alertApi.acknowledge(id)
      );
      await Promise.all(promises);
      await loadAlerts();
      await loadStatistics();
      const count = selectedAlerts.size;
      setSelectedAlerts(new Set());
      toast.success(`已批量确认 ${count} 条预警`);
    } catch (error) {
      console.error("Failed to batch acknowledge:", error);
      toast.error("批量确认失败，请稍后重试");
    }
  }, [selectedAlerts, loadAlerts, loadStatistics]);

  // 批量解决预警
  const handleBatchResolve = useCallback(async () => {
    if (selectedAlerts.size === 0) {return;}

    try {
      const promises = Array.from(selectedAlerts).map((id) =>
      alertApi.resolve(id, { resolution_method: "批量解决", resolution_note: "批量操作" })
      );
      await Promise.all(promises);
      await loadAlerts();
      await loadStatistics();
      const count = selectedAlerts.size;
      setSelectedAlerts(new Set());
      toast.success(`已批量解决 ${count} 条预警`);
    } catch (error) {
      console.error("Failed to batch resolve:", error);
      toast.error("批量解决失败，请稍后重试");
    }
  }, [selectedAlerts, loadAlerts, loadStatistics]);

  // 导出Excel
  const handleExportExcel = useCallback(async () => {
    try {
      const params = {
        project_id: selectedProject !== "ALL" ? parseInt(selectedProject) : undefined,
        alert_level: selectedLevel !== "ALL" ? selectedLevel : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        start_date: dateRange.start || undefined,
        end_date: dateRange.end || undefined
      };

      const response = await alertApi.exportExcel(params);
      const blob = new Blob([response.data], {
        type: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
      });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `预警报表_${new Date().toISOString().split("T")[0]}.xlsx`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("Excel导出成功");
    } catch (error) {
      console.error("Failed to export Excel:", error);
      toast.error("导出失败，请稍后重试");
    }
  }, [selectedProject, selectedLevel, selectedStatus, dateRange]);

  // 导出PDF
  const handleExportPdf = useCallback(async () => {
    try {
      const params = {
        project_id: selectedProject !== "ALL" ? parseInt(selectedProject) : undefined,
        alert_level: selectedLevel !== "ALL" ? selectedLevel : undefined,
        status: selectedStatus !== "ALL" ? selectedStatus : undefined,
        start_date: dateRange.start || undefined,
        end_date: dateRange.end || undefined
      };

      const response = await alertApi.exportPdf(params);
      const blob = new Blob([response.data], { type: "application/pdf" });
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.setAttribute(
        "download",
        `预警报表_${new Date().toISOString().split("T")[0]}.pdf`
      );
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);
      toast.success("PDF导出成功");
    } catch (error) {
      console.error("Failed to export PDF:", error);
      toast.error("导出失败，请稍后重试");
    }
  }, [selectedProject, selectedLevel, selectedStatus, dateRange]);

  // 查看详情
  const handleViewDetail = useCallback((alert) => {
    setSelectedAlert(alert);
    setShowDetail(true);
  }, []);

  // 单个确认
  const handleAcknowledge = useCallback(async (alertId) => {
    try {
      await alertApi.acknowledge(alertId);
      await loadAlerts();
      await loadStatistics();
      toast.success("预警确认成功");
    } catch (error) {
      console.error("Failed to acknowledge:", error);
      toast.error("确认失败，请稍后重试");
    }
  }, [loadAlerts, loadStatistics]);

  // 解决预警
  const handleResolve = useCallback(async (alertId, result) => {
    try {
      await alertApi.resolve(alertId, {
        resolution_method: "手动解决",
        resolution_note: result
      });
      setShowResolveDialog(false);
      setResolveResult("");
      await loadAlerts();
      await loadStatistics();
      toast.success("预警解决成功");
    } catch (error) {
      console.error("Failed to resolve:", error);
      toast.error("解决失败，请稍后重试");
    }
  }, [loadAlerts, loadStatistics]);

  // 关闭预警
  const _handleClose = useCallback(async (alertId, reason) => {
    try {
      await alertApi.close(alertId, {
        closure_reason: reason
      });
      setShowCloseDialog(false);
      setCloseReason("");
      await loadAlerts();
      await loadStatistics();
      toast.success("预警关闭成功");
    } catch (error) {
      console.error("Failed to close:", error);
      toast.error("关闭失败，请稍后重试");
    }
  }, [loadAlerts, loadStatistics]);

  // 筛选和搜索
  const filteredAlerts = useMemo(() => {
    const sorted = [...alerts].sort((a, b) => {
      let aValue = a[sortBy];
      let bValue = b[sortBy];

      if (sortBy === "triggered_at" && aValue) {
        aValue = new Date(aValue).getTime();
        bValue = new Date(bValue).getTime();
      }

      if (sortOrder === "desc") {
        return aValue > bValue ? -1 : aValue < bValue ? 1 : 0;
      } else {
        return aValue > bValue ? 1 : aValue < bValue ? -1 : 0;
      }
    });

    return sorted;
  }, [alerts, sortBy, sortOrder]);

  // 处理复选框选择
  const handleSelectAll = useCallback(() => {
    if (selectedAlerts.size === filteredAlerts.length) {
      setSelectedAlerts(new Set());
    } else {
      setSelectedAlerts(new Set((filteredAlerts || []).map((alert) => alert.id)));
    }
  }, [filteredAlerts, selectedAlerts.size]);

  const handleSelectOne = useCallback((alertId, selected) => {
    const newSelected = new Set(selectedAlerts);
    if (selected) {
      newSelected.add(alertId);
    } else {
      newSelected.delete(alertId);
    }
    setSelectedAlerts(newSelected);
  }, [selectedAlerts]);

  // 键盘快捷键
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (
      (e.ctrlKey || e.metaKey) &&
      e.key === "a" &&
      e.target.tagName !== "INPUT" &&
      e.target.tagName !== "TEXTAREA")
      {
        e.preventDefault();
        handleSelectAll();
      }
    };

    window.addEventListener("keydown", handleKeyDown);
    return () => window.removeEventListener("keydown", handleKeyDown);
  }, [
  showDetail,
  showResolveDialog,
  showCloseDialog,
  filteredAlerts,
  handleSelectAll]
  );

  // 快速操作处理
  const handleQuickAction = useCallback((action) => {
    switch (action) {
      case 'createAlert':
        navigate('/alerts/create');
        break;
      case 'manageRules':
        navigate('/alerts/rules');
        break;
      case 'notificationSettings':
        navigate('/alerts/notifications');
        break;
      case 'exportReport':
        handleExportExcel();
        break;
    }
  }, [navigate, handleExportExcel]);

  return {
    // State
    alerts,
    stats,
    loading,
    error,
    page,
    total,
    pageSize,
    searchQuery,
    selectedLevel,
    selectedStatus,
    selectedProject,
    dateRange,
    showDetail,
    selectedAlert,
    showResolveDialog,
    showCloseDialog,
    resolveResult,
    selectedAlerts,
    sortBy,
    sortOrder,
    projects,
    filteredAlerts,
    navigate,

    // Setters
    setPage,
    setSearchQuery,
    setSelectedLevel,
    setSelectedStatus,
    setSelectedProject,
    setDateRange,
    setShowDetail,
    setSelectedAlert,
    setShowResolveDialog,
    setShowCloseDialog,
    setResolveResult,
    setSelectedAlerts,
    setSortBy,

    // Handlers
    loadAlerts,
    handleBatchAcknowledge,
    handleBatchResolve,
    handleExportExcel,
    handleExportPdf,
    handleViewDetail,
    handleAcknowledge,
    handleResolve,
    handleSelectAll,
    handleSelectOne,
    handleQuickAction
  };
}
