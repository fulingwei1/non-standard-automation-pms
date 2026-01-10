/**
 * useECNDetail Hook
 * 管理 ECN 详情页面的核心数据和状态
 */
import { useState, useEffect, useCallback } from "react";
import { ecnApi } from "../../../services/api";

export function useECNDetail(ecnId) {
  const [loading, setLoading] = useState(true);
  const [ecn, setEcn] = useState(null);
  const [evaluations, setEvaluations] = useState([]);
  const [approvals, setApprovals] = useState([]);
  const [tasks, setTasks] = useState([]);
  const [affectedMaterials, setAffectedMaterials] = useState([]);
  const [affectedOrders, setAffectedOrders] = useState([]);
  const [logs, setLogs] = useState([]);
  const [evaluationSummary, setEvaluationSummary] = useState(null);
  const [activeTab, setActiveTab] = useState("info");

  const fetchECNDetail = useCallback(async () => {
    if (!ecnId) return;

    try {
      setLoading(true);
      const [
        ecnRes,
        evalsRes,
        approvalsRes,
        tasksRes,
        materialsRes,
        ordersRes,
        logsRes,
        summaryRes,
      ] = await Promise.all([
        ecnApi.get(ecnId).catch(() => ({ data: null })),
        ecnApi.getEvaluations(ecnId).catch(() => ({ data: [] })),
        ecnApi.getApprovals(ecnId).catch(() => ({ data: [] })),
        ecnApi.getTasks(ecnId).catch(() => ({ data: [] })),
        ecnApi.getAffectedMaterials(ecnId).catch(() => ({ data: [] })),
        ecnApi.getAffectedOrders(ecnId).catch(() => ({ data: [] })),
        ecnApi.getLogs(ecnId).catch(() => ({ data: [] })),
        ecnApi.getEvaluationSummary(ecnId).catch(() => ({ data: null })),
      ]);

      setEcn(ecnRes.data || ecnRes);
      setEvaluations(evalsRes.data || []);
      setApprovals(approvalsRes.data || []);
      setTasks(tasksRes.data || []);
      setAffectedMaterials(materialsRes.data || []);
      setAffectedOrders(ordersRes.data || []);
      setLogs(logsRes.data || []);
      setEvaluationSummary(summaryRes.data);
    } catch (error) {
      console.error("Failed to fetch ECN detail:", error);
    } finally {
      setLoading(false);
    }
  }, [ecnId]);

  useEffect(() => {
    fetchECNDetail();
  }, [fetchECNDetail]);

  // ECN 操作函数
  const handleSubmit = useCallback(async () => {
    try {
      await ecnApi.submit(ecnId, { remark: "提交ECN申请" });
      await fetchECNDetail();
      return { success: true, message: "ECN已提交" };
    } catch (error) {
      return {
        success: false,
        message: "提交失败: " + (error.response?.data?.detail || error.message),
      };
    }
  }, [ecnId, fetchECNDetail]);

  const handleStartExecution = useCallback(async () => {
    try {
      await ecnApi.startExecution(ecnId, { remark: "开始执行ECN" });
      await fetchECNDetail();
      return { success: true, message: "ECN执行已开始" };
    } catch (error) {
      return {
        success: false,
        message:
          "开始执行失败: " + (error.response?.data?.detail || error.message),
      };
    }
  }, [ecnId, fetchECNDetail]);

  const handleVerify = useCallback(
    async (verifyForm) => {
      try {
        await ecnApi.verify(ecnId, verifyForm);
        await fetchECNDetail();
        return { success: true, message: "验证完成" };
      } catch (error) {
        return {
          success: false,
          message:
            "验证失败: " + (error.response?.data?.detail || error.message),
        };
      }
    },
    [ecnId, fetchECNDetail],
  );

  const handleClose = useCallback(
    async (closeForm) => {
      try {
        await ecnApi.close(ecnId, closeForm);
        await fetchECNDetail();
        return { success: true, message: "ECN已关闭" };
      } catch (error) {
        return {
          success: false,
          message:
            "关闭失败: " + (error.response?.data?.detail || error.message),
        };
      }
    },
    [ecnId, fetchECNDetail],
  );

  return {
    // 数据
    loading,
    ecn,
    evaluations,
    approvals,
    tasks,
    affectedMaterials,
    affectedOrders,
    logs,
    evaluationSummary,
    // UI 状态
    activeTab,
    setActiveTab,
    // 操作方法
    refetch: fetchECNDetail,
    handleSubmit,
    handleStartExecution,
    handleVerify,
    handleClose,
  };
}
