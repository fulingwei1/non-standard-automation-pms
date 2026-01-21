/**
 * 项目阶段视图数据获取 Hook
 */
import { useState, useEffect, useCallback } from "react";
import { stageViewsApi } from "../../../services/api";
import { VIEW_TYPES } from "../constants";

export function useStageViews(initialView = VIEW_TYPES.PIPELINE) {
  // 视图状态
  const [currentView, setCurrentView] = useState(initialView);
  const [selectedProjectId, setSelectedProjectId] = useState(null);

  // 数据状态
  const [pipelineData, setPipelineData] = useState(null);
  const [timelineData, setTimelineData] = useState(null);
  const [treeData, setTreeData] = useState(null);

  // 加载状态
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 筛选状态
  const [filters, setFilters] = useState({
    category: null,
    healthStatus: null,
    templateId: null,
    groupByTemplate: true, // 默认按模板分组
    search: "",
  });

  // 分页状态
  const [pagination, setPagination] = useState({
    skip: 0,
    limit: 50,
  });

  /**
   * 加载流水线视图数据
   */
  const loadPipelineData = useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const params = {
        ...pagination,
        category: filters.category || undefined,
        health_status: filters.healthStatus || undefined,
        template_id: filters.templateId || undefined,
        group_by_template: filters.groupByTemplate,
      };
      const response = await stageViewsApi.pipeline.get(params);
      setPipelineData(response.data);
    } catch (err) {
      console.error("加载流水线数据失败:", err);
      setError("加载流水线数据失败");
    } finally {
      setLoading(false);
    }
  }, [filters, pagination]);

  /**
   * 加载时间轴视图数据
   */
  const loadTimelineData = useCallback(async (projectId) => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await stageViewsApi.timeline.get(projectId, {
        include_nodes: true,
      });
      setTimelineData(response.data);
    } catch (err) {
      console.error("加载时间轴数据失败:", err);
      setError("加载时间轴数据失败");
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 加载分解树视图数据
   */
  const loadTreeData = useCallback(async (projectId) => {
    if (!projectId) return;
    setLoading(true);
    setError(null);
    try {
      const response = await stageViewsApi.tree.get(projectId, {
        include_tasks: true,
      });
      setTreeData(response.data);
    } catch (err) {
      console.error("加载分解树数据失败:", err);
      setError("加载分解树数据失败");
    } finally {
      setLoading(false);
    }
  }, []);

  /**
   * 切换视图
   */
  const switchView = useCallback((view, projectId = null) => {
    setCurrentView(view);
    if (projectId) {
      setSelectedProjectId(projectId);
    }
  }, []);

  /**
   * 更新筛选条件
   */
  const updateFilters = useCallback((newFilters) => {
    setFilters((prev) => ({ ...prev, ...newFilters }));
  }, []);

  /**
   * 刷新当前视图数据
   */
  const refresh = useCallback(() => {
    switch (currentView) {
      case VIEW_TYPES.PIPELINE:
        loadPipelineData();
        break;
      case VIEW_TYPES.TIMELINE:
        loadTimelineData(selectedProjectId);
        break;
      case VIEW_TYPES.TREE:
        loadTreeData(selectedProjectId);
        break;
      default:
        break;
    }
  }, [currentView, selectedProjectId, loadPipelineData, loadTimelineData, loadTreeData]);

  // 自动加载数据
  useEffect(() => {
    if (currentView === VIEW_TYPES.PIPELINE) {
      loadPipelineData();
    }
  }, [currentView, loadPipelineData]);

  useEffect(() => {
    if (currentView === VIEW_TYPES.TIMELINE && selectedProjectId) {
      loadTimelineData(selectedProjectId);
    }
  }, [currentView, selectedProjectId, loadTimelineData]);

  useEffect(() => {
    if (currentView === VIEW_TYPES.TREE && selectedProjectId) {
      loadTreeData(selectedProjectId);
    }
  }, [currentView, selectedProjectId, loadTreeData]);

  return {
    // 视图状态
    currentView,
    selectedProjectId,
    setSelectedProjectId,
    switchView,

    // 数据
    pipelineData,
    timelineData,
    treeData,

    // 状态
    loading,
    error,

    // 筛选
    filters,
    updateFilters,

    // 分页
    pagination,
    setPagination,

    // 操作
    refresh,
    loadPipelineData,
    loadTimelineData,
    loadTreeData,
  };
}

/**
 * 阶段状态操作 Hook
 */
export function useStageActions() {
  const [actionLoading, setActionLoading] = useState(false);
  const [actionError, setActionError] = useState(null);

  /**
   * 更新阶段状态
   */
  const updateStageStatus = useCallback(async (stageInstanceId, status, remark) => {
    setActionLoading(true);
    setActionError(null);
    try {
      await stageViewsApi.stages.updateStatus(stageInstanceId, { status, remark });
      return true;
    } catch (err) {
      console.error("更新阶段状态失败:", err);
      setActionError("更新阶段状态失败");
      return false;
    } finally {
      setActionLoading(false);
    }
  }, []);

  /**
   * 开始阶段
   */
  const startStage = useCallback(async (stageInstanceId, actualStartDate) => {
    setActionLoading(true);
    setActionError(null);
    try {
      await stageViewsApi.stages.start(stageInstanceId, actualStartDate);
      return true;
    } catch (err) {
      console.error("开始阶段失败:", err);
      setActionError("开始阶段失败");
      return false;
    } finally {
      setActionLoading(false);
    }
  }, []);

  /**
   * 完成阶段
   */
  const completeStage = useCallback(async (stageInstanceId, actualEndDate, autoStartNext) => {
    setActionLoading(true);
    setActionError(null);
    try {
      await stageViewsApi.stages.complete(stageInstanceId, actualEndDate, autoStartNext);
      return true;
    } catch (err) {
      console.error("完成阶段失败:", err);
      setActionError("完成阶段失败");
      return false;
    } finally {
      setActionLoading(false);
    }
  }, []);

  /**
   * 提交阶段评审
   */
  const submitReview = useCallback(async (stageInstanceId, reviewResult, reviewNotes) => {
    setActionLoading(true);
    setActionError(null);
    try {
      await stageViewsApi.stages.submitReview(stageInstanceId, {
        review_result: reviewResult,
        review_notes: reviewNotes,
      });
      return true;
    } catch (err) {
      console.error("提交评审失败:", err);
      setActionError("提交评审失败");
      return false;
    } finally {
      setActionLoading(false);
    }
  }, []);

  return {
    actionLoading,
    actionError,
    updateStageStatus,
    startStage,
    completeStage,
    submitReview,
  };
}

export default useStageViews;
