import { useState, useEffect, useMemo, useCallback } from "react";
import { exceptionApi, projectApi } from "../../../services/api";
import { DEFAULT_NEW_EXCEPTION, DEFAULT_HANDLE_DATA } from "../constants";

/**
 * 异常管理完整状态 Hook
 * Encapsulates all data-fetching, filter, dialog and form logic
 * for the ExceptionManagement page.
 */
export function useExceptionManagement() {
  // ── Data ─────────────────────────────────────────────────────────────────
  const [loading, setLoading] = useState(true);
  const [exceptions, setExceptions] = useState([]);
  const [projects, setProjects] = useState([]);
  const [error, setError] = useState(null);

  // ── Filters ───────────────────────────────────────────────────────────────
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterSeverity, setFilterSeverity] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  // ── Dialog visibility ─────────────────────────────────────────────────────
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showHandleDialog, setShowHandleDialog] = useState(false);
  const [selectedException, setSelectedException] = useState(null);

  // ── Form state ────────────────────────────────────────────────────────────
  const [newException, setNewException] = useState(DEFAULT_NEW_EXCEPTION);
  const [handleData, setHandleData] = useState(DEFAULT_HANDLE_DATA);

  // ── Fetch helpers ─────────────────────────────────────────────────────────
  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (err) {
      console.error("Failed to fetch projects:", err);
    }
  }, []);

  const fetchExceptions = useCallback(async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject) params.project_id = filterProject;
      if (filterType) params.event_type = filterType;
      if (filterSeverity) params.severity = filterSeverity;
      if (filterStatus) params.status = filterStatus;
      if (searchKeyword) params.keyword = searchKeyword;

      const res = await exceptionApi.list(params);
      setExceptions(res.data?.items || res.data || []);
      setError(null);
    } catch (err) {
      console.error("Failed to fetch exceptions:", err);
      setError(err.message);
      setExceptions([]);
    } finally {
      setLoading(false);
    }
  }, [filterProject, filterType, filterSeverity, filterStatus, searchKeyword]);

  useEffect(() => {
    fetchProjects();
    fetchExceptions();
  }, [fetchProjects, fetchExceptions]);

  // ── Computed ──────────────────────────────────────────────────────────────
  const filteredExceptions = useMemo(() => {
    if (!searchKeyword) return exceptions;
    const keyword = searchKeyword.toLowerCase();
    return exceptions.filter(
      (ex) =>
        ex.event_no?.toLowerCase().includes(keyword) ||
        ex.event_title?.toLowerCase().includes(keyword) ||
        ex.event_description?.toLowerCase().includes(keyword)
    );
  }, [exceptions, searchKeyword]);

  // ── Actions ───────────────────────────────────────────────────────────────
  const handleCreateException = useCallback(async () => {
    if (!newException.event_title) {
      alert("请填写异常标题");
      return;
    }
    try {
      await exceptionApi.create(newException);
      setShowCreateDialog(false);
      setNewException(DEFAULT_NEW_EXCEPTION);
      fetchExceptions();
    } catch (err) {
      console.error("Failed to create exception:", err);
      alert(
        err.response?.data?.detail || err.message || "创建异常失败，请稍后重试"
      );
    }
  }, [newException, fetchExceptions]);

  const handleViewDetail = useCallback(async (exceptionId) => {
    try {
      const res = await exceptionApi.get(exceptionId);
      setSelectedException(res.data || res);
      setShowDetailDialog(true);
    } catch (err) {
      console.error("Failed to fetch exception detail:", err);
    }
  }, []);

  const handleException = useCallback(async () => {
    if (!selectedException) return;
    try {
      await exceptionApi.update(selectedException.id, {
        status: handleData.next_status,
        action_description: handleData.action_description || "",
        action_type: handleData.action_type,
      });
      setShowHandleDialog(false);
      setHandleData(DEFAULT_HANDLE_DATA);
      fetchExceptions();
      if (showDetailDialog) {
        handleViewDetail(selectedException.id);
      }
    } catch (err) {
      console.error("Failed to handle exception:", err);
      alert(
        err.response?.data?.detail || err.message || "处理异常失败，请稍后重试"
      );
    }
  }, [
    selectedException,
    handleData,
    fetchExceptions,
    showDetailDialog,
    handleViewDetail,
  ]);

  const openHandleDialog = useCallback((exception) => {
    setSelectedException(exception);
    setShowHandleDialog(true);
  }, []);

  return {
    // data
    loading,
    exceptions,
    filteredExceptions,
    projects,
    error,
    // filters
    searchKeyword,
    setSearchKeyword,
    filterProject,
    setFilterProject,
    filterType,
    setFilterType,
    filterSeverity,
    setFilterSeverity,
    filterStatus,
    setFilterStatus,
    // dialogs
    showCreateDialog,
    setShowCreateDialog,
    showDetailDialog,
    setShowDetailDialog,
    showHandleDialog,
    setShowHandleDialog,
    selectedException,
    setSelectedException,
    // form
    newException,
    setNewException,
    handleData,
    setHandleData,
    // actions
    handleCreateException,
    handleViewDetail,
    handleException,
    openHandleDialog,
  };
}
