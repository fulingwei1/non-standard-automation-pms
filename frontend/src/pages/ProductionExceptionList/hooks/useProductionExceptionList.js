import { useState, useEffect, useMemo, useCallback } from "react";
import { productionApi, projectApi } from "../../../services/api";
import { confirmAction } from "@/lib/confirmAction";
import { DEFAULT_NEW_EXCEPTION, DEFAULT_HANDLE_DATA } from "../constants";

/**
 * Custom hook encapsulating all state and API logic for
 * the Production Exception List page.
 */
export function useProductionExceptionList() {
  const [loading, setLoading] = useState(true);
  const [exceptions, setExceptions] = useState([]);
  const [projects, setProjects] = useState([]);

  // Filters
  const [searchKeyword, setSearchKeyword] = useState("");
  const [filterProject, setFilterProject] = useState("");
  const [filterType, setFilterType] = useState("");
  const [filterLevel, setFilterLevel] = useState("");
  const [filterStatus, setFilterStatus] = useState("");

  // Dialog visibility
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showHandleDialog, setShowHandleDialog] = useState(false);

  // Selected record & form state
  const [selectedException, setSelectedException] = useState(null);
  const [newException, setNewException] = useState(DEFAULT_NEW_EXCEPTION);
  const [handleData, setHandleData] = useState(DEFAULT_HANDLE_DATA);

  // ── Data fetchers ──────────────────────────────────────────────────────────

  const fetchProjects = useCallback(async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 });
      setProjects(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch projects:", error);
    }
  }, []);

  const fetchExceptions = useCallback(async () => {
    try {
      setLoading(true);
      const params = {};
      if (filterProject) params.project_id = filterProject;
      if (filterType) params.exception_type = filterType;
      if (filterLevel) params.exception_level = filterLevel;
      if (filterStatus) params.status = filterStatus;
      if (searchKeyword) params.search = searchKeyword;
      const res = await productionApi.exceptions.list(params);
      setExceptions(res.data?.items || res.data || []);
    } catch (error) {
      console.error("Failed to fetch exceptions:", error);
    } finally {
      setLoading(false);
    }
  }, [filterProject, filterType, filterLevel, filterStatus, searchKeyword]);

  useEffect(() => {
    fetchProjects();
    fetchExceptions();
  }, [fetchProjects, fetchExceptions]);

  // ── Filtered list ──────────────────────────────────────────────────────────

  const filteredExceptions = useMemo(() => {
    return (exceptions || []).filter((exc) => {
      if (!searchKeyword) return true;
      const keyword = searchKeyword.toLowerCase();
      return (
        exc.exception_no?.toLowerCase().includes(keyword) ||
        exc.title?.toLowerCase().includes(keyword) ||
        exc.description?.toLowerCase().includes(keyword)
      );
    });
  }, [exceptions, searchKeyword]);

  // ── CRUD handlers ──────────────────────────────────────────────────────────

  const handleCreateException = async () => {
    if (!newException.title) {
      alert("请填写异常标题");
      return;
    }
    try {
      await productionApi.exceptions.create(newException);
      setShowCreateDialog(false);
      setNewException(DEFAULT_NEW_EXCEPTION);
      fetchExceptions();
    } catch (error) {
      console.error("Failed to create exception:", error);
      alert("上报异常失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleViewDetail = async (excId) => {
    try {
      const res = await productionApi.exceptions.get(excId);
      setSelectedException(res.data || res);
      setShowDetailDialog(true);
    } catch (error) {
      console.error("Failed to fetch exception detail:", error);
    }
  };

  const handleException = async () => {
    if (!selectedException) return;
    try {
      await productionApi.exceptions.handle(selectedException.id, handleData);
      setShowHandleDialog(false);
      setHandleData(DEFAULT_HANDLE_DATA);
      fetchExceptions();
      if (showDetailDialog) {
        handleViewDetail(selectedException.id);
      }
    } catch (error) {
      console.error("Failed to handle exception:", error);
      alert("处理异常失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleClose = async (excId) => {
    if (!await confirmAction("确认关闭此异常？")) return;
    try {
      await productionApi.exceptions.close(excId);
      fetchExceptions();
      if (showDetailDialog) {
        handleViewDetail(excId);
      }
    } catch (error) {
      console.error("Failed to close exception:", error);
      alert("关闭异常失败: " + (error.response?.data?.detail || error.message));
    }
  };

  return {
    // Data
    loading,
    projects,
    filteredExceptions,
    // Filters
    searchKeyword, setSearchKeyword,
    filterProject, setFilterProject,
    filterType, setFilterType,
    filterLevel, setFilterLevel,
    filterStatus, setFilterStatus,
    // Dialogs
    showCreateDialog, setShowCreateDialog,
    showDetailDialog, setShowDetailDialog,
    showHandleDialog, setShowHandleDialog,
    // Selection & forms
    selectedException, setSelectedException,
    newException, setNewException,
    handleData, setHandleData,
    // Actions
    handleCreateException,
    handleViewDetail,
    handleException,
    handleClose,
  };
}
