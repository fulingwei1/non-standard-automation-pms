/**
 * 技术评估工作台 - 核心 Hook
 * 封装全部 state、useEffect、数据加载和操作处理器
 */

import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import { presaleWorkbenchApi } from "../../../services/api";
import {
  emptyListPayload,
  buildRequirementText,
  formatDate,
  formatSourceType,
  normalizeDimensionScores,
  safeJsonParse,
  getDecisionMeta,
  getStatusMeta,
} from "../constants";

export function useTechnicalAssessment() {
  const { sourceType, sourceId } = useParams();
  const [searchParams] = useSearchParams();
  const normalizedSourceType = String(sourceType || "").toLowerCase();
  const numericSourceId = Number(sourceId);
  const presaleTicketId = Number(searchParams.get("ticketId")) || null;

  // --- 核心状态 ---
  const [workbench, setWorkbench] = useState(null);
  const [selectedAssessmentId, setSelectedAssessmentId] = useState(null);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [savingRequirement, setSavingRequirement] = useState(false);
  const [enableAI, setEnableAI] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const [error, setError] = useState(null);
  const [requirementText, setRequirementText] = useState("{}");
  const [requirementDirty, setRequirementDirty] = useState(false);
  const [assessmentArtifacts, setAssessmentArtifacts] = useState({
    risks: emptyListPayload,
    versions: emptyListPayload,
  });
  const [artifactFailures, setArtifactFailures] = useState([]);
  const [artifactLoading, setArtifactLoading] = useState(false);

  // --- 初始加载工作台上下文 ---
  useEffect(() => {
    let cancelled = false;

    const loadContext = async () => {
      try {
        setLoading(true);
        setError(null);
        const data = await presaleWorkbenchApi.loadContext({
          sourceType: normalizedSourceType,
          sourceId: numericSourceId,
          presaleTicketId,
        });

        if (cancelled) {
          return;
        }

        setWorkbench(data);
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        setError(loadError.response?.data?.detail || loadError.message || "加载失败");
      } finally {
        if (!cancelled) {
          setLoading(false);
        }
      }
    };

    loadContext();

    return () => {
      cancelled = true;
    };
  }, [normalizedSourceType, numericSourceId, presaleTicketId]);

  // --- 派生数据（从 workbench 中提取） ---
  const assessments = workbench?.assessment?.items || [];
  const latestAssessment = workbench?.assessment?.current || null;
  const selectedAssessment =
    assessments.find((item) => item.id === selectedAssessmentId) || latestAssessment;
  const requirementDetail = workbench?.assessment?.requirementDetail || null;
  const structuredRisks = assessmentArtifacts?.risks?.items || [];
  const versions = assessmentArtifacts?.versions?.items || [];
  const assessmentTemplates = workbench?.templates?.assessment?.items || [];
  const technicalTemplates = workbench?.templates?.technical?.items || [];
  const solutions = workbench?.solutions?.items || [];
  const gateConfigs = workbench?.funnel?.gateConfigs?.items || [];
  const stages = workbench?.funnel?.stages?.items || [];
  const transitionLogs = workbench?.funnel?.transitionLogs?.items || [];
  const dwellAlerts = workbench?.funnel?.dwellAlerts?.items || [];
  const partialFailures = workbench?.meta?.failures || [];

  // --- 自动选中评估记录 ---
  useEffect(() => {
    if (assessments.length === 0) {
      setSelectedAssessmentId(null);
      return;
    }

    const hasSelected = assessments.some((item) => item.id === selectedAssessmentId);
    if (!hasSelected) {
      setSelectedAssessmentId(assessments[0].id);
    }
  }, [assessments, selectedAssessmentId]);

  // --- 同步需求文本（仅在用户未编辑时） ---
  useEffect(() => {
    if (requirementDirty) {
      return;
    }
    setRequirementText(buildRequirementText(requirementDetail));
  }, [requirementDetail, requirementDirty]);

  // --- 加载评估结构化明细（风险 + 版本快照） ---
  useEffect(() => {
    let cancelled = false;

    if (!selectedAssessment?.id) {
      setAssessmentArtifacts({
        risks: emptyListPayload,
        versions: emptyListPayload,
      });
      setArtifactFailures([]);
      setArtifactLoading(false);
      return () => {
        cancelled = true;
      };
    }

    const fallbackArtifacts =
      selectedAssessment.id === latestAssessment?.id
        ? {
            risks: workbench?.assessment?.risks || emptyListPayload,
            versions: workbench?.assessment?.versions || emptyListPayload,
          }
        : {
            risks: emptyListPayload,
            versions: emptyListPayload,
          };

    setAssessmentArtifacts(fallbackArtifacts);
    setArtifactFailures([]);
    setArtifactLoading(true);

    const loadAssessmentArtifacts = async () => {
      try {
        const data = await presaleWorkbenchApi.loadAssessmentArtifacts(selectedAssessment.id);
        if (cancelled) {
          return;
        }
        setAssessmentArtifacts({
          risks: data.risks,
          versions: data.versions,
        });
        setArtifactFailures(data.meta?.failures || []);
      } catch (loadError) {
        if (cancelled) {
          return;
        }
        setAssessmentArtifacts(fallbackArtifacts);
        setArtifactFailures([
          {
            key: "assessmentArtifacts",
            message:
              loadError.response?.data?.detail || loadError.message || "加载评估结构化明细失败",
          },
        ]);
      } finally {
        if (!cancelled) {
          setArtifactLoading(false);
        }
      }
    };

    loadAssessmentArtifacts();

    return () => {
      cancelled = true;
    };
  }, [
    latestAssessment?.id,
    selectedAssessment?.id,
    workbench?.assessment?.risks,
    workbench?.assessment?.versions,
  ]);

  // --- 计算衍生值 ---
  const dimensionScores = useMemo(
    () => normalizeDimensionScores(selectedAssessment?.dimension_scores),
    [selectedAssessment?.dimension_scores],
  );
  const legacyRisks = useMemo(
    () => safeJsonParse(selectedAssessment?.risks, []),
    [selectedAssessment?.risks],
  );
  const similarCases = useMemo(
    () => safeJsonParse(selectedAssessment?.similar_cases, []),
    [selectedAssessment?.similar_cases],
  );
  const conditions = useMemo(
    () => safeJsonParse(selectedAssessment?.conditions, []),
    [selectedAssessment?.conditions],
  );
  const selectedAssessmentStatus = getStatusMeta(selectedAssessment?.status);
  const selectedDecision = getDecisionMeta(selectedAssessment?.decision);

  const totalRiskCount = structuredRisks.length || legacyRisks.length;
  const trendSeries = assessments
    .filter((item) => item.total_score !== null && item.total_score !== undefined)
    .map((item, index) => ({
      date: item.evaluated_at || item.created_at,
      value: item.total_score,
      label: `评估${index + 1}`,
    }))
    .sort((left, right) => new Date(left.date) - new Date(right.date));

  const comparisonSeries = assessments
    .filter((item) => item.dimension_scores)
    .slice(0, 5)
    .map((item, index) => ({
      name: `评估${index + 1} (${item.total_score ?? 0}分)`,
      scores: normalizeDimensionScores(item.dimension_scores) || {},
    }));

  // --- 操作处理器 ---
  const reloadWorkbench = async () => {
    const refreshed = await presaleWorkbenchApi.loadContext({
      sourceType: normalizedSourceType,
      sourceId: numericSourceId,
      presaleTicketId,
    });
    setWorkbench(refreshed);
    return refreshed;
  };

  const parseRequirementPayload = () => {
    if (!requirementText.trim()) {
      return requirementDetail || {};
    }

    try {
      return JSON.parse(requirementText);
    } catch {
      throw new Error("需求数据不是合法的 JSON");
    }
  };

  const mergeRequirementDetail = (detail) => {
    if (!detail) {
      return;
    }

    setWorkbench((current) => {
      if (!current?.assessment) {
        return current;
      }

      return {
        ...current,
        assessment: {
          ...current.assessment,
          requirementDetail: detail,
        },
      };
    });
  };

  const persistRequirementDetail = async (
    parsedRequirementData,
    { reload = false, showSuccess = false } = {},
  ) => {
    if (normalizedSourceType !== "lead") {
      return null;
    }

    setSavingRequirement(true);
    try {
      const response = await presaleWorkbenchApi.saveRequirementDetail(
        numericSourceId,
        parsedRequirementData,
        {
          hasExisting: Boolean(requirementDetail?.id),
        },
      );
      const savedDetail = presaleWorkbenchApi.unwrapResponse(response);
      mergeRequirementDetail(savedDetail);
      setRequirementDirty(false);

      if (reload) {
        await reloadWorkbench();
      }

      if (showSuccess) {
        alert("需求详情已保存");
      }

      return savedDetail;
    } finally {
      setSavingRequirement(false);
    }
  };

  const handleApplyAssessment = async () => {
    try {
      await presaleWorkbenchApi.applyAssessment(normalizedSourceType, numericSourceId, {});
      setRequirementDirty(false);
      await reloadWorkbench();
      alert("技术评估申请已提交");
    } catch (applyError) {
      alert(`申请评估失败: ${applyError.response?.data?.detail || applyError.message}`);
    }
  };

  const handleSaveRequirement = async () => {
    let parsedRequirementData;
    try {
      parsedRequirementData = parseRequirementPayload();
    } catch (parseError) {
      alert(parseError.message);
      return;
    }

    try {
      await persistRequirementDetail(parsedRequirementData, {
        reload: true,
        showSuccess: true,
      });
    } catch (saveError) {
      alert(`保存需求详情失败: ${saveError.response?.data?.detail || saveError.message}`);
    }
  };

  const handleEvaluate = async () => {
    if (!selectedAssessment) {
      alert("请先申请技术评估");
      return;
    }

    let parsedRequirementData;
    try {
      parsedRequirementData = parseRequirementPayload();
    } catch (parseError) {
      alert(parseError.message);
      return;
    }

    if (!parsedRequirementData || Object.keys(parsedRequirementData).length === 0) {
      alert("请先填写需求数据");
      return;
    }

    try {
      setEvaluating(true);
      if (normalizedSourceType === "lead" && requirementDirty) {
        await persistRequirementDetail(parsedRequirementData);
      }
      await presaleWorkbenchApi.evaluateAssessment(selectedAssessment.id, {
        requirement_data: parsedRequirementData,
        enable_ai: enableAI,
      });
      setRequirementDirty(false);
      await reloadWorkbench();
      alert("技术评估完成");
    } catch (evaluateError) {
      alert(`执行评估失败: ${evaluateError.response?.data?.detail || evaluateError.message}`);
    } finally {
      setEvaluating(false);
    }
  };

  const handleExportReport = () => {
    if (!selectedAssessment) {
      return;
    }

    const report = {
      评估编号: selectedAssessment.id,
      来源类型: formatSourceType(normalizedSourceType),
      来源ID: selectedAssessment.source_id,
      评估状态: selectedAssessmentStatus.label,
      总分: selectedAssessment.total_score,
      决策建议: selectedDecision.label,
      评估时间: formatDate(selectedAssessment.evaluated_at),
      评估人: selectedAssessment.evaluator_name || "未知",
      维度评分: dimensionScores,
      风险分析: structuredRisks.length > 0 ? structuredRisks : legacyRisks,
      相似案例: similarCases,
      立项条件: conditions,
      工作台上下文: {
        方案数量: solutions.length,
        评估模板数量: assessmentTemplates.length,
        技术模板数量: technicalTemplates.length,
        活跃预警数量: dwellAlerts.length,
      },
    };

    const dataStr = JSON.stringify(report, null, 2);
    const dataBlob = new Blob([dataStr], { type: "application/json" });
    const url = URL.createObjectURL(dataBlob);
    const link = document.createElement("a");
    link.href = url;
    link.download = `技术评估报告_${selectedAssessment.id}_${new Date().toISOString().split("T")[0]}.json`;
    link.click();
    URL.revokeObjectURL(url);
  };

  // --- 返回全部状态和处理器 ---
  return {
    // 路由参数
    normalizedSourceType,
    numericSourceId,

    // 加载与错误
    loading,
    error,

    // 工作台数据
    workbench,
    assessments,
    selectedAssessment,
    selectedAssessmentId,
    setSelectedAssessmentId,
    requirementDetail,

    // 评估结构化明细
    structuredRisks,
    versions,
    artifactFailures,
    artifactLoading,

    // 模板 / 方案 / 漏斗
    assessmentTemplates,
    technicalTemplates,
    solutions,
    gateConfigs,
    stages,
    transitionLogs,
    dwellAlerts,
    partialFailures,

    // 计算值
    dimensionScores,
    legacyRisks,
    similarCases,
    conditions,
    selectedAssessmentStatus,
    selectedDecision,
    totalRiskCount,
    trendSeries,
    comparisonSeries,

    // 需求编辑
    requirementText,
    setRequirementText,
    requirementDirty,
    setRequirementDirty,
    enableAI,
    setEnableAI,
    savingRequirement,

    // UI 状态
    evaluating,
    showHistory,
    setShowHistory,

    // 操作处理器
    handleApplyAssessment,
    handleSaveRequirement,
    handleEvaluate,
    handleExportReport,
  };
}
