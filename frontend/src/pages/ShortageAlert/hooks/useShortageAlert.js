import { useState, useEffect, useMemo, useCallback } from "react";
import { shortageAlertApi, projectApi } from "../../../services/api";
import { confirmAction } from "@/lib/confirmAction";
import { DEFAULT_HANDLE_DATA } from "../constants";

export function useShortageAlert() {
  const [loading, setLoading] = useState(true);
  const [alerts, setAlerts] = useState([]);
  const [projects, setProjects] = useState([]);
  const [summary, setSummary] = useState(null);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("all");
  const [filterStatus, setFilterStatus] = useState("all");
  const [filterLevel, setFilterLevel] = useState("all");

  // Dialogs
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showHandleDialog, setShowHandleDialog] = useState(false);
  const [selectedAlert, setSelectedAlert] = useState(null);

  // Handle-alert form state
  const [handleData, setHandleData] = useState(DEFAULT_HANDLE_DATA);

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  }, []);

  const fetchAlerts = useCallback(async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject && filterProject !== "all") params.project_id = filterProject;
      if (filterStatus && filterStatus !== "all") params.status = filterStatus;
      if (filterLevel && filterLevel !== "all") params.alert_level = filterLevel;
      if (searchKeyword) params.search = searchKeyword;
      const res = await shortageAlertApi.list(params);
      setAlerts(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch alerts:", error);
      setAlerts([]);
    } finally {
      setLoading(false);
    }
  }, [filterProject, filterStatus, filterLevel, searchKeyword]);

  const fetchSummary = useCallback(async () => {
    try {
      const res = await shortageAlertApi.getSummary();
      setSummary(res.data || res);
    } catch (error) {
      console.error("Failed to fetch summary:", error);
      setSummary({
        pending_count: 0,
        processing_count: 0,
        resolved_count: 0,
        total_count: 0,
      });
    }
  }, []);

  useEffect(() => {
    fetchProjects();
    fetchAlerts();
    fetchSummary();
  }, [fetchProjects, fetchAlerts, fetchSummary]);

  const handleViewDetail = useCallback(async (alertId) => {
    try {
      const res = await shortageAlertApi.get(alertId);
      setSelectedAlert(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch alert detail:", error);
    }
  }, []);

  const handleAcknowledge = useCallback(async (alertId) => {
    if (!await confirmAction("确认已收到此缺料预警？")) return;
    try {
      await shortageAlertApi.acknowledge(alertId);
      fetchAlerts();
      fetchSummary();
    } catch (error) {
      console.error("Failed to acknowledge alert:", error);
      const errorMessage =
        error.response?.data?.detail || error.message || "确认失败，请稍后重试";
      alert(errorMessage);
    }
  }, [fetchAlerts, fetchSummary]);

  const handleResolve = useCallback(async () => {
    if (!selectedAlert) return;
    try {
      await shortageAlertApi.resolve(selectedAlert.id, handleData);
      setShowHandleDialog(false);
      setHandleData(DEFAULT_HANDLE_DATA);
      fetchAlerts();
      fetchSummary();
      if (showDetailDialog) {
        handleViewDetail(selectedAlert.id);
      }
    } catch (error) {
      console.error("Failed to resolve alert:", error);
      const errorMessage =
        error.response?.data?.detail || error.message || "处理失败，请稍后重试";
      alert(errorMessage);
    }
  }, [selectedAlert, handleData, showDetailDialog, fetchAlerts, fetchSummary, handleViewDetail]);

  const openHandleDialog = useCallback((alert) => {
    setSelectedAlert(alert);
    setShowHandleDialog(true);
  }, []);

  const filteredAlerts = useMemo(() => {
    return (alerts || []).filter((alert) => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase();
        return (
          alert.material_code?.toLowerCase().includes(keyword) ||
          alert.material_name?.toLowerCase().includes(keyword) ||
          alert.project_name?.toLowerCase().includes(keyword)
        );
      }
      return true;
    });
  }, [alerts, searchKeyword]);

  const isUrgent = useCallback((alert) => {
    if (!alert.required_date) return false;
    const daysUntilRequired = Math.ceil(
      (new Date(alert.required_date) - new Date()) / (1000 * 60 * 60 * 24),
    );
    return daysUntilRequired <= 7 && daysUntilRequired >= 0;
  }, []);

  return {
    // data
    loading,
    filteredAlerts,
    projects,
    summary,
    // filters
    searchKeyword,
    setSearchKeyword,
    filterProject,
    setFilterProject,
    filterStatus,
    setFilterStatus,
    filterLevel,
    setFilterLevel,
    // dialogs
    showDetailDialog,
    setShowDetailDialog,
    showHandleDialog,
    setShowHandleDialog,
    selectedAlert,
    // form
    handleData,
    setHandleData,
    // actions
    handleViewDetail,
    handleAcknowledge,
    handleResolve,
    openHandleDialog,
    isUrgent,
  };
}
