import { useState, useEffect } from "react";
import { progressApi } from "../../../services/api";
import { ISSUE_TYPES } from "../constants";

/**
 * Manages all state and async logic for the DependencyCheck page.
 * Distinct from the generic useDependencyCheck hook which operates on the
 * flat dependency list API.
 */
export function useProjectDependencyCheck(id) {
  const [loading, setLoading] = useState(true);
  const [project, setProject] = useState(null);
  const [dependencyData, setDependencyData] = useState(null);
  const [previewData, setPreviewData] = useState(null);
  const [processing, setProcessing] = useState(false);
  const [errorMessage, setErrorMessage] = useState("");
  const [successMessage, setSuccessMessage] = useState("");

  // Auto-fix toggles
  const [autoFixTiming, setAutoFixTiming] = useState(false);
  const [autoFixMissing, setAutoFixMissing] = useState(true);

  // Dialog visibility
  const [showPreviewDialog, setShowPreviewDialog] = useState(false);
  const [showConfirmDialog, setShowConfirmDialog] = useState(false);

  useEffect(() => {
    console.log("[DependencyCheck] useEffect triggered - id:", id);
    if (!id) {
      console.error("[DependencyCheck] No project ID available");
      setErrorMessage("项目ID不可用");
      setLoading(false);
      return;
    }
    fetchProject();
    fetchDependencyCheck();
     
  }, [id]);

  const fetchProject = async () => {
    try {
      const res = await fetch(`/api/v1/projects/${id}`).then((r) => r.json());
      setProject(res.data?.data || res.data);
    } catch (error) {
      console.error("Failed to fetch project:", error);
    }
  };

  const fetchDependencyCheck = async () => {
    try {
      setLoading(true);
      setErrorMessage("");
      console.log("[DependencyCheck] Fetching dependency check for project:", id);
      const res = await progressApi.analytics.checkDependencies(id);
      console.log("[DependencyCheck] API response:", res);

      const data = res.data?.data || res.data;
      console.log("[DependencyCheck] Final data to set:", data);

      if (!data) {
        throw new Error("API returned no data");
      }

      setDependencyData(data);
      console.log("[DependencyCheck] Dependency data set successfully");
    } catch (error) {
      console.error("[DependencyCheck] Failed to fetch dependency data:", error);
      console.error("[DependencyCheck] Error response:", error.response?.data);
      setErrorMessage("依赖检查数据加载失败，请稍后重试。");
    } finally {
      setLoading(false);
    }
  };

  const handlePreview = async () => {
    try {
      setProcessing(true);

      const checkRes = await progressApi.analytics.checkDependencies(id);
      const depData = checkRes.data?.data || checkRes.data;

      const preview = {
        has_cycle: depData?.has_cycle || false,
        cycle_count: depData?.cycle_paths?.length || 0,
        cycle_paths: depData?.cycle_paths || [],
        issue_count: depData?.issues?.length || 0,
        issues: depData?.issues || [],
        preview_actions: {
          will_fix_timing:
            depData?.issues?.filter(
              (i) => i.issue_type === ISSUE_TYPES.TIMING_CONFLICT && autoFixTiming
            ).length || 0,
          will_remove_missing:
            depData?.issues?.filter(
              (i) => i.issue_type === ISSUE_TYPES.MISSING_PREDECESSOR && autoFixMissing
            ).length || 0,
          will_skip_cycles: depData?.cycle_paths?.length || 0,
          will_send_notifications:
            depData?.has_cycle ||
            depData?.issues?.some(
              (i) => i.severity === "HIGH" || i.severity === "URGENT"
            ),
        },
      };

      setPreviewData(preview);
      setShowPreviewDialog(true);
    } catch (error) {
      console.error("Failed to preview dependency check:", error);
      setErrorMessage("预览失败，请稍后重试。");
    } finally {
      setProcessing(false);
    }
  };

  const handleFixDependencies = async () => {
    try {
      setProcessing(true);
      setShowConfirmDialog(false);
      setErrorMessage("");
      setSuccessMessage("");

      const res = await progressApi.autoProcess.fixDependencies(id, {
        auto_fix_timing: autoFixTiming,
        auto_fix_missing: autoFixMissing,
      });

      if (res.data?.success) {
        setSuccessMessage("依赖问题已成功修复！");
        await fetchDependencyCheck();
        setTimeout(() => setSuccessMessage(""), 3000);
      } else {
        setErrorMessage("修复依赖问题失败：" + (res.data?.error || "未知错误"));
      }
    } catch (error) {
      console.error("Failed to fix dependencies:", error);
      setErrorMessage("修复依赖问题失败：" + (error.message || "未知错误"));
    } finally {
      setProcessing(false);
    }
  };

  // Derived categorised issue lists
  const cycleIssues = dependencyData?.cycle_paths || [];
  const timingIssues =
    dependencyData?.issues?.filter(
      (i) => i.issue_type === ISSUE_TYPES.TIMING_CONFLICT
    ) || [];
  const missingIssues =
    dependencyData?.issues?.filter(
      (i) => i.issue_type === ISSUE_TYPES.MISSING_PREDECESSOR
    ) || [];
  const otherIssues =
    dependencyData?.issues?.filter(
      (i) =>
        ![ISSUE_TYPES.TIMING_CONFLICT, ISSUE_TYPES.MISSING_PREDECESSOR].includes(
          i.issue_type
        )
    ) || [];

  return {
    // Loading / data
    loading,
    project,
    dependencyData,
    previewData,
    processing,
    errorMessage,
    successMessage,
    // Derived lists
    cycleIssues,
    timingIssues,
    missingIssues,
    otherIssues,
    // Auto-fix options
    autoFixTiming,
    setAutoFixTiming,
    autoFixMissing,
    setAutoFixMissing,
    // Dialog state
    showPreviewDialog,
    setShowPreviewDialog,
    showConfirmDialog,
    setShowConfirmDialog,
    // Actions
    fetchDependencyCheck,
    handlePreview,
    handleFixDependencies,
  };
}
