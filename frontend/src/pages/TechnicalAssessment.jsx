/**
 * Technical Assessment Page - 技术评估工作台
 * 使用统一工作台 API 聚合评估、模板、方案、风险和漏斗数据
 */

import { useEffect, useMemo, useState } from "react";
import { useParams, useSearchParams } from "react-router-dom";
import {
  AlertTriangle,
  CheckCircle2,
  Clock3,
  Download,
  FileJson,
  GitBranch,
  Layers3,
  Save,
  ShieldAlert,
  Target,
  Workflow,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Progress,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../components/ui";
import { presaleWorkbenchApi } from "../services/api";
import { ComparisonChart } from "../components/assessment/ComparisonChart";
import { RadarChart } from "../components/assessment/RadarChart";
import { TrendChart } from "../components/assessment/TrendChart";

const decisionConfig = {
  RECOMMEND: {
    label: "推荐立项",
    color: "bg-green-500",
    textColor: "text-green-400",
  },
  CONDITIONAL: {
    label: "有条件立项",
    color: "bg-yellow-500",
    textColor: "text-yellow-400",
  },
  DEFER: {
    label: "暂缓",
    color: "bg-orange-500",
    textColor: "text-orange-400",
  },
  NOT_RECOMMEND: {
    label: "不建议立项",
    color: "bg-red-500",
    textColor: "text-red-400",
  },
  推荐立项: {
    label: "推荐立项",
    color: "bg-green-500",
    textColor: "text-green-400",
  },
  有条件立项: {
    label: "有条件立项",
    color: "bg-yellow-500",
    textColor: "text-yellow-400",
  },
  暂缓: {
    label: "暂缓",
    color: "bg-orange-500",
    textColor: "text-orange-400",
  },
  不建议立项: {
    label: "不建议立项",
    color: "bg-red-500",
    textColor: "text-red-400",
  },
};

const statusConfig = {
  PENDING: {
    label: "待评估",
    color: "bg-gray-500",
    textColor: "text-gray-400",
  },
  IN_PROGRESS: {
    label: "评估中",
    color: "bg-blue-500",
    textColor: "text-blue-400",
  },
  COMPLETED: {
    label: "已完成",
    color: "bg-green-500",
    textColor: "text-green-400",
  },
  CANCELLED: {
    label: "已取消",
    color: "bg-red-500",
    textColor: "text-red-400",
  },
  SKIPPED: {
    label: "已跳过",
    color: "bg-slate-500",
    textColor: "text-slate-300",
  },
};

const dimensionLabels = {
  technology: "技术",
  business: "商务",
  resource: "资源",
  delivery: "交付",
  customer: "客户关系",
};

const funnelEntityLabels = {
  LEAD: "线索",
  OPPORTUNITY: "商机",
  QUOTE: "报价",
  CONTRACT: "合同",
};

const emptyListPayload = {
  items: [],
  total: 0,
};

function safeJsonParse(value, fallback) {
  if (!value) {
    return fallback;
  }
  if (typeof value === "object") {
    return value;
  }
  try {
    return JSON.parse(value);
  } catch {
    return fallback;
  }
}

function normalizeDimensionScores(rawScores) {
  const scores = safeJsonParse(rawScores, {});
  const normalized = {
    technology: scores.technology ?? scores.technical ?? 0,
    business: scores.business ?? scores.commercial ?? 0,
    resource: scores.resource ?? 0,
    delivery: scores.delivery ?? scores.timeline ?? 0,
    customer: scores.customer ?? scores.risk ?? 0,
  };
  return Object.values(normalized).some((score) => score !== 0) ? normalized : null;
}

function formatDate(value, withTime = true) {
  if (!value) {
    return "未记录";
  }
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }
  return withTime ? date.toLocaleString() : date.toLocaleDateString();
}

function formatSourceType(sourceType) {
  return sourceType === "lead" ? "线索" : "商机";
}

function buildRequirementText(requirementDetail) {
  if (!requirementDetail) {
    return "{}";
  }
  return JSON.stringify(requirementDetail, null, 2);
}

function getDecisionMeta(decision) {
  return decisionConfig[decision] || {
    label: decision || "未生成",
    color: "bg-slate-500",
    textColor: "text-slate-300",
  };
}

function getStatusMeta(status) {
  return statusConfig[status] || {
    label: status || "未知",
    color: "bg-slate-500",
    textColor: "text-slate-300",
  };
}

function getRiskLevelBadge(level) {
  if (level === "CRITICAL" || level === "HIGH") {
    return "bg-red-500";
  }
  if (level === "MEDIUM") {
    return "bg-yellow-500";
  }
  return "bg-slate-500";
}

export default function TechnicalAssessment() {
  const { sourceType, sourceId } = useParams();
  const [searchParams] = useSearchParams();
  const normalizedSourceType = String(sourceType || "").toLowerCase();
  const numericSourceId = Number(sourceId);
  const presaleTicketId = Number(searchParams.get("ticketId")) || null;

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
        console.error("加载技术评估工作台失败:", loadError);
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

  useEffect(() => {
    if (requirementDirty) {
      return;
    }
    setRequirementText(buildRequirementText(requirementDetail));
  }, [requirementDetail, requirementDirty]);

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
        console.error("加载评估结构化明细失败:", loadError);
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
      console.error("申请评估失败:", applyError);
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
      console.error("保存需求详情失败:", saveError);
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
      console.error("执行评估失败:", evaluateError);
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

  if (loading) {
    return <div className="p-6 text-slate-300">加载中...</div>;
  }

  return (
    <div className="min-h-screen bg-gray-950 text-white p-6">
      <PageHeader
        title="技术评估工作台"
        breadcrumbs={[
          { label: "销售管理", path: "/sales" },
          {
            label: normalizedSourceType === "lead" ? "线索管理" : "商机管理",
            path: normalizedSourceType === "lead" ? "/sales/leads" : "/sales/opportunities",
          },
          { label: "技术评估", path: "" },
        ]}
      />

      <div className="mt-6 space-y-6">
        {error && (
          <div className="rounded-lg border border-red-500/40 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}

        {partialFailures.length > 0 && (
          <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
            部分数据加载失败：
            {partialFailures.map((item) => ` ${item.key}(${item.message})`).join("；")}
          </div>
        )}

        <div className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4">
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="pt-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">评估记录</div>
                  <div className="text-3xl font-semibold">{assessments.length}</div>
                </div>
                <Layers3 className="h-8 w-8 text-blue-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="pt-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">风险台账</div>
                  <div className="text-3xl font-semibold">{totalRiskCount}</div>
                </div>
                <ShieldAlert className="h-8 w-8 text-red-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="pt-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">模板资产</div>
                  <div className="text-3xl font-semibold">
                    {assessmentTemplates.length + technicalTemplates.length}
                  </div>
                </div>
                <GitBranch className="h-8 w-8 text-purple-400" />
              </div>
            </CardContent>
          </Card>
          <Card className="bg-gray-900 border-gray-800">
            <CardContent className="pt-5">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-gray-400">活跃预警</div>
                  <div className="text-3xl font-semibold">{dwellAlerts.length}</div>
                </div>
                <Clock3 className="h-8 w-8 text-amber-400" />
              </div>
            </CardContent>
          </Card>
        </div>

        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <div className="flex flex-col gap-4 lg:flex-row lg:items-start lg:justify-between">
              <div className="space-y-2">
                <CardTitle>评估主状态</CardTitle>
                <div className="flex flex-wrap gap-2 text-sm text-gray-400">
                  <span>来源: {formatSourceType(normalizedSourceType)} #{numericSourceId}</span>
                  {workbench?.ticket?.ticket_no && <span>工单: {workbench.ticket.ticket_no}</span>}
                  <span>流程实体: {funnelEntityLabels[workbench?.funnel?.entityType] || "未识别"}</span>
                </div>
              </div>
              <div className="flex flex-wrap gap-2">
                {assessments.length > 1 && (
                  <Button variant="outline" onClick={() => setShowHistory((value) => !value)}>
                    {showHistory ? "隐藏历史" : "查看历史"}
                  </Button>
                )}
                {selectedAssessment?.status === "COMPLETED" && (
                  <Button
                    variant="outline"
                    className="border-blue-500 text-blue-300 hover:bg-blue-500/10"
                    onClick={handleExportReport}
                  >
                    <Download className="mr-2 h-4 w-4" />
                    导出报告
                  </Button>
                )}
                {!selectedAssessment && (
                  <Button className="bg-blue-600 hover:bg-blue-700" onClick={handleApplyAssessment}>
                    申请技术评估
                  </Button>
                )}
                {selectedAssessment?.status === "PENDING" && (
                  <Button
                    className="bg-green-600 hover:bg-green-700"
                    disabled={evaluating}
                    onClick={handleEvaluate}
                  >
                    {evaluating ? "评估中..." : "执行评估"}
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {selectedAssessment ? (
              <div className="space-y-4">
                <div className="flex flex-wrap items-center gap-3">
                  <Badge className={selectedAssessmentStatus.color}>
                    {selectedAssessmentStatus.label}
                  </Badge>
                  {selectedAssessment.decision && (
                    <Badge className={selectedDecision.color}>{selectedDecision.label}</Badge>
                  )}
                  <span className="text-sm text-gray-400">
                    评估人: {selectedAssessment.evaluator_name || "未分配"}
                  </span>
                  <span className="text-sm text-gray-400">
                    更新时间: {formatDate(selectedAssessment.evaluated_at || selectedAssessment.updated_at)}
                  </span>
                </div>

                {selectedAssessment.total_score !== null &&
                  selectedAssessment.total_score !== undefined && (
                    <div className="space-y-2">
                      <div className="flex items-center gap-4">
                        <div className="text-3xl font-semibold">{selectedAssessment.total_score}</div>
                        <div className="text-sm text-gray-400">总分 / 100</div>
                        <Progress value={selectedAssessment.total_score} className="flex-1" />
                      </div>
                      {dimensionScores && (
                        <div className="grid grid-cols-2 gap-3 text-sm text-gray-300 md:grid-cols-5">
                          {Object.entries(dimensionLabels).map(([key, label]) => (
                            <div key={key} className="rounded-lg bg-gray-800 px-3 py-2">
                              <div className="text-gray-400">{label}</div>
                              <div className="text-lg font-semibold">{dimensionScores[key] ?? 0}</div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
              </div>
            ) : (
              <div className="text-gray-400">尚未申请技术评估</div>
            )}
          </CardContent>
        </Card>

        {showHistory && assessments.length > 1 && (
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle>评估历史</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {assessments.map((item, index) => {
                  const itemStatus = getStatusMeta(item.status);
                  const itemDecision = getDecisionMeta(item.decision);
                  return (
                    <button
                      key={item.id}
                      type="button"
                      className={`w-full rounded-lg border px-4 py-3 text-left transition-colors ${
                        item.id === selectedAssessment?.id
                          ? "border-blue-500 bg-blue-500/10"
                          : "border-gray-800 bg-gray-950 hover:border-gray-700"
                      }`}
                      onClick={() => setSelectedAssessmentId(item.id)}
                    >
                      <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                        <div className="flex flex-wrap items-center gap-2">
                          <span className="text-sm text-gray-400">评估{index + 1}</span>
                          <Badge className={itemStatus.color}>{itemStatus.label}</Badge>
                          {item.decision && <Badge className={itemDecision.color}>{itemDecision.label}</Badge>}
                          <span className="text-sm font-semibold">{item.total_score ?? "--"}分</span>
                        </div>
                        <span className="text-xs text-gray-500">
                          {formatDate(item.evaluated_at || item.created_at)}
                        </span>
                      </div>
                    </button>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        )}

        {selectedAssessment?.status === "COMPLETED" && (
          <Card className="bg-gray-900 border-gray-800">
            <CardHeader>
              <CardTitle>评估结果</CardTitle>
            </CardHeader>
            <CardContent>
              <Tabs defaultValue="scores" className="w-full">
                <TabsList className="grid w-full grid-cols-6">
                  <TabsTrigger value="scores">评分详情</TabsTrigger>
                  <TabsTrigger value="trend">趋势分析</TabsTrigger>
                  <TabsTrigger value="comparison">对比分析</TabsTrigger>
                  <TabsTrigger value="risks">风险分析</TabsTrigger>
                  <TabsTrigger value="cases">相似案例</TabsTrigger>
                  <TabsTrigger value="ai">AI分析</TabsTrigger>
                </TabsList>

                <TabsContent value="scores" className="mt-4">
                  {dimensionScores ? (
                    <div className="space-y-6">
                      <div className="flex justify-center">
                        <RadarChart data={dimensionScores} size={400} maxScore={20} />
                      </div>

                      <div className="space-y-3">
                        {Object.entries(dimensionLabels).map(([dimension, label]) => (
                          <div key={dimension} className="space-y-1">
                            <div className="flex items-center justify-between text-sm">
                              <span className="text-gray-300">{label}</span>
                              <span className="font-semibold">{dimensionScores[dimension] ?? 0} / 20</span>
                            </div>
                            <Progress value={((dimensionScores[dimension] ?? 0) / 20) * 100} className="h-2" />
                          </div>
                        ))}
                      </div>

                      <div className="rounded-lg bg-gray-800 p-4">
                        <div className="mb-3 flex items-center gap-2">
                          <Target className="h-5 w-5 text-blue-400" />
                          <span className="font-semibold">决策建议</span>
                        </div>
                        <Badge className={selectedDecision.color}>{selectedDecision.label}</Badge>
                        {conditions.length > 0 && (
                          <div className="mt-4 space-y-2 text-sm text-gray-300">
                            {conditions.map((condition, index) => (
                              <div key={`${condition}-${index}`} className="rounded bg-gray-900 px-3 py-2">
                                {condition}
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="text-gray-400">暂无评分详情</div>
                  )}
                </TabsContent>

                <TabsContent value="trend" className="mt-4">
                  {trendSeries.length > 1 ? (
                    <div className="space-y-6">
                      <div className="rounded-lg bg-gray-800 p-4">
                        <div className="mb-4 text-sm font-semibold">评估分数趋势</div>
                        <TrendChart data={trendSeries} height={250} />
                      </div>

                      {dimensionScores && (
                        <div className="rounded-lg bg-gray-800 p-4">
                          <div className="mb-4 text-sm font-semibold">维度分数趋势</div>
                          <div className="space-y-4">
                            {Object.entries(dimensionLabels).map(([dimension, label]) => {
                              const series = assessments
                                .filter((item) => item.dimension_scores)
                                .map((item, index) => {
                                  const scores = normalizeDimensionScores(item.dimension_scores) || {};
                                  return {
                                    date: item.evaluated_at || item.created_at,
                                    value: scores[dimension] || 0,
                                    label: `评估${index + 1}`,
                                  };
                                })
                                .sort((left, right) => new Date(left.date) - new Date(right.date));

                              if (series.length === 0) {
                                return null;
                              }

                              return (
                                <div key={dimension} className="space-y-2">
                                  <div className="text-sm text-gray-300">{label}</div>
                                  <TrendChart data={series} height={150} />
                                </div>
                              );
                            })}
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="py-8 text-center text-gray-400">需要至少 2 次评估才能显示趋势分析</div>
                  )}
                </TabsContent>

                <TabsContent value="comparison" className="mt-4">
                  {comparisonSeries.length > 1 ? (
                    <div className="space-y-6">
                      <div className="rounded-lg bg-gray-800 p-4">
                        <div className="mb-4 text-sm font-semibold">评估维度对比</div>
                        <ComparisonChart data={comparisonSeries} height={300} />
                      </div>

                      <div className="rounded-lg bg-gray-800 p-4">
                        <div className="mb-4 text-sm font-semibold">总分对比</div>
                        <div className="space-y-3">
                          {assessments
                            .filter((item) => item.total_score !== null && item.total_score !== undefined)
                            .map((item, index) => (
                              <div key={item.id} className="flex items-center gap-4">
                                <div className="w-20 text-sm text-gray-300">评估{index + 1}</div>
                                <div className="flex-1">
                                  <div className="flex items-center gap-2">
                                    <div
                                      className="h-6 rounded bg-blue-500"
                                      style={{ width: `${item.total_score}%` }}
                                    />
                                    <span className="w-12 text-right text-sm font-semibold">
                                      {item.total_score}
                                    </span>
                                  </div>
                                </div>
                                <div className="w-28 text-right text-xs text-gray-500">
                                  {formatDate(item.evaluated_at || item.created_at, false)}
                                </div>
                              </div>
                            ))}
                        </div>
                      </div>
                    </div>
                  ) : (
                    <div className="py-8 text-center text-gray-400">需要至少 2 次评估才能显示对比分析</div>
                  )}
                </TabsContent>

                <TabsContent value="risks" className="mt-4">
                  {legacyRisks.length > 0 ? (
                    <div className="space-y-3">
                      {legacyRisks.map((risk, index) => (
                        <div key={`${risk.description || "risk"}-${index}`} className="rounded-lg bg-gray-800 p-4">
                          <div className="mb-2 flex items-center gap-2">
                            <AlertTriangle
                              className={`h-5 w-5 ${
                                risk.level === "HIGH" ? "text-red-400" : "text-yellow-400"
                              }`}
                            />
                            <Badge className={risk.level === "HIGH" ? "bg-red-500" : "bg-yellow-500"}>
                              {risk.level || "未评级"}
                            </Badge>
                            <span className="text-sm text-gray-400">{risk.dimension || "未分类"}</span>
                          </div>
                          <div className="text-sm text-gray-200">{risk.description}</div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-400">无风险记录</div>
                  )}
                </TabsContent>

                <TabsContent value="cases" className="mt-4">
                  {similarCases.length > 0 ? (
                    <div className="space-y-3">
                      {similarCases.map((caseItem, index) => (
                        <div key={`${caseItem.project_name || "case"}-${index}`} className="rounded-lg bg-gray-800 p-4">
                          <div className="mb-2 flex items-center justify-between">
                            <div className="font-semibold">{caseItem.project_name || "未命名案例"}</div>
                            <Badge>
                              相似度: {((caseItem.similarity_score || 0) * 100).toFixed(0)}%
                            </Badge>
                          </div>
                          <div className="mb-2 text-sm text-gray-300">
                            {caseItem.core_failure_reason || "无失败原因说明"}
                          </div>
                          <div className="text-sm text-gray-400">
                            {caseItem.lesson_learned || "无经验教训"}
                          </div>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="text-gray-400">无相似案例</div>
                  )}
                </TabsContent>

                <TabsContent value="ai" className="mt-4">
                  {selectedAssessment.ai_analysis ? (
                    <div className="whitespace-pre-wrap rounded-lg bg-gray-800 p-4 text-sm text-gray-200">
                      {selectedAssessment.ai_analysis}
                    </div>
                  ) : (
                    <div className="text-gray-400">未启用 AI 分析</div>
                  )}
                </TabsContent>
              </Tabs>
            </CardContent>
          </Card>
        )}

        <Card className="bg-gray-900 border-gray-800">
          <CardHeader>
            <CardTitle>工作台上下文</CardTitle>
          </CardHeader>
          <CardContent>
            <Tabs defaultValue="requirement" className="w-full">
              <TabsList className="grid w-full grid-cols-4">
                <TabsTrigger value="requirement">需求包</TabsTrigger>
                <TabsTrigger value="assets">模板与方案</TabsTrigger>
                <TabsTrigger value="risk-ledger">风险与版本</TabsTrigger>
                <TabsTrigger value="funnel">阶段门与漏斗</TabsTrigger>
              </TabsList>

              <TabsContent value="requirement" className="mt-4 space-y-4">
                <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="text-sm text-gray-400">需求版本</div>
                    <div className="mt-1 text-lg font-semibold">
                      {requirementDetail?.requirement_version || "未设置"}
                    </div>
                  </div>
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="text-sm text-gray-400">是否冻结</div>
                    <div className="mt-1 text-lg font-semibold">
                      {requirementDetail?.is_frozen ? "已冻结" : "未冻结"}
                    </div>
                  </div>
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="text-sm text-gray-400">验收方式</div>
                    <div className="mt-1 text-lg font-semibold">
                      {requirementDetail?.acceptance_method || "未填写"}
                    </div>
                  </div>
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="text-sm text-gray-400">目标节拍</div>
                    <div className="mt-1 text-lg font-semibold">
                      {requirementDetail?.cycle_time_seconds
                        ? `${requirementDetail.cycle_time_seconds} 秒`
                        : "未填写"}
                    </div>
                  </div>
                </div>

                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <FileJson className="h-4 w-4 text-blue-400" />
                    <span className="font-semibold">需求数据</span>
                  </div>
                  <textarea
                    className="h-72 w-full rounded border border-gray-700 bg-gray-950 p-3 font-mono text-sm text-white"
                    value={requirementText}
                    onChange={(event) => {
                      setRequirementDirty(true);
                      setRequirementText(event.target.value);
                    }}
                    readOnly={normalizedSourceType === "lead" && requirementDetail?.is_frozen}
                    placeholder='{"industry": "新能源", "budget_status": "明确"}'
                  />
                  <div className="mt-3 flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
                    <div className="flex items-center gap-2 text-sm text-gray-300">
                      <input
                        id="enable-ai"
                        type="checkbox"
                        checked={enableAI}
                        onChange={(event) => setEnableAI(event.target.checked)}
                      />
                      <label htmlFor="enable-ai">执行评估时启用 AI 分析</label>
                    </div>
                    {normalizedSourceType === "lead" && (
                      <Button
                        variant="outline"
                        className="border-blue-500 text-blue-300 hover:bg-blue-500/10"
                        disabled={
                          savingRequirement ||
                          !requirementDirty ||
                          Boolean(requirementDetail?.is_frozen)
                        }
                        onClick={handleSaveRequirement}
                      >
                        <Save className="mr-2 h-4 w-4" />
                        {savingRequirement ? "保存中..." : "保存需求"}
                      </Button>
                    )}
                  </div>
                  {normalizedSourceType === "lead" && requirementDetail?.is_frozen && (
                    <div className="mt-3 text-xs text-amber-200">
                      需求包已冻结，当前内容仅可查看，不能回写。
                    </div>
                  )}
                  {normalizedSourceType === "opportunity" && (
                    <div className="mt-3 text-xs text-gray-500">
                      商机来源暂不支持回写需求详情，当前 JSON 将直接用于本次评估。
                    </div>
                  )}
                </div>
              </TabsContent>

              <TabsContent value="assets" className="mt-4 space-y-4">
                <div className="grid gap-4 xl:grid-cols-3">
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <Layers3 className="h-4 w-4 text-purple-400" />
                      <span className="font-semibold">评估模板</span>
                    </div>
                    <div className="space-y-2">
                      {assessmentTemplates.slice(0, 5).map((template) => (
                        <div key={template.id} className="rounded bg-gray-950 px-3 py-2">
                          <div className="font-medium">{template.template_name}</div>
                          <div className="text-xs text-gray-400">
                            {template.category} · {template.version}
                          </div>
                        </div>
                      ))}
                      {assessmentTemplates.length === 0 && (
                        <div className="text-sm text-gray-400">暂无评估模板</div>
                      )}
                    </div>
                  </div>

                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-cyan-400" />
                      <span className="font-semibold">技术参数模板</span>
                    </div>
                    <div className="space-y-2">
                      {technicalTemplates.slice(0, 5).map((template) => (
                        <div key={template.id} className="rounded bg-gray-950 px-3 py-2">
                          <div className="font-medium">{template.name}</div>
                          <div className="text-xs text-gray-400">
                            {template.industry || "未分类"} · {template.test_type || "未分类"}
                          </div>
                        </div>
                      ))}
                      {technicalTemplates.length === 0 && (
                        <div className="text-sm text-gray-400">暂无技术模板</div>
                      )}
                    </div>
                  </div>

                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <CheckCircle2 className="h-4 w-4 text-green-400" />
                      <span className="font-semibold">关联方案</span>
                    </div>
                    <div className="space-y-2">
                      {solutions.slice(0, 5).map((solution) => (
                        <div key={solution.id} className="rounded bg-gray-950 px-3 py-2">
                          <div className="font-medium">
                            {solution.solution_name || solution.name || `方案 #${solution.id}`}
                          </div>
                          <div className="text-xs text-gray-400">
                            {solution.status || "未标记状态"}
                          </div>
                        </div>
                      ))}
                      {solutions.length === 0 && (
                        <div className="text-sm text-gray-400">暂无关联方案</div>
                      )}
                    </div>
                  </div>
                </div>
              </TabsContent>

	              <TabsContent value="risk-ledger" className="mt-4 space-y-4">
	                <div className="rounded-lg border border-slate-700 bg-slate-900/70 px-4 py-3 text-sm text-slate-300">
	                  当前结构化风险和版本快照已跟随所选评估记录切换。
	                  {selectedAssessment?.id ? ` 当前评估 ID: ${selectedAssessment.id}` : ""}
	                </div>
	                {artifactFailures.length > 0 && (
	                  <div className="rounded-lg border border-amber-500/40 bg-amber-500/10 px-4 py-3 text-sm text-amber-100">
	                    评估结构化明细加载存在部分失败：
	                    {artifactFailures.map((item) => ` ${item.key}(${item.message})`).join("；")}
	                  </div>
	                )}

	                <div className="grid gap-4 xl:grid-cols-2">
	                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <AlertTriangle className="h-4 w-4 text-red-400" />
                      <span className="font-semibold">结构化风险台账</span>
                    </div>
	                    <div className="space-y-3">
	                      {artifactLoading && structuredRisks.length === 0 && (
	                        <div className="text-sm text-gray-400">结构化风险加载中...</div>
	                      )}
	                      {structuredRisks.map((risk) => (
	                        <div key={risk.id} className="rounded bg-gray-950 px-3 py-3">
                          <div className="mb-2 flex items-center gap-2">
                            <Badge className={getRiskLevelBadge(risk.risk_level)}>
                              {risk.risk_level || "未评级"}
                            </Badge>
                            <span className="text-xs text-gray-500">{risk.risk_code}</span>
                          </div>
                          <div className="text-sm font-medium">
                            {risk.risk_title || risk.risk_type || "未命名风险"}
                          </div>
                          <div className="mt-1 text-sm text-gray-300">{risk.risk_description}</div>
                          {risk.mitigation_plan && (
                            <div className="mt-2 text-xs text-gray-400">
                              处置建议: {risk.mitigation_plan}
                            </div>
                          )}
                        </div>
                      ))}
                      {structuredRisks.length === 0 && (
                        <div className="text-sm text-gray-400">暂无结构化风险记录</div>
                      )}
                    </div>
                  </div>

                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <Workflow className="h-4 w-4 text-blue-400" />
                      <span className="font-semibold">版本快照</span>
                    </div>
	                    <div className="space-y-3">
	                      {artifactLoading && versions.length === 0 && (
	                        <div className="text-sm text-gray-400">版本快照加载中...</div>
	                      )}
	                      {versions.map((version) => (
	                        <div key={version.id} className="rounded bg-gray-950 px-3 py-3">
                          <div className="flex items-center justify-between gap-3">
                            <div className="font-medium">{version.version_no}</div>
                            <div className="text-xs text-gray-500">{formatDate(version.created_at)}</div>
                          </div>
                          <div className="mt-2 text-sm text-gray-300">
                            {version.change_summary || "无变更说明"}
                          </div>
                        </div>
                      ))}
                      {versions.length === 0 && (
                        <div className="text-sm text-gray-400">暂无版本快照</div>
                      )}
                    </div>
                  </div>
                </div>
              </TabsContent>

              <TabsContent value="funnel" className="mt-4 space-y-4">
                <div className="grid gap-4 xl:grid-cols-3">
                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <Target className="h-4 w-4 text-green-400" />
                      <span className="font-semibold">阶段定义</span>
                    </div>
                    <div className="space-y-2">
                      {stages.map((stage) => (
                        <div key={stage.id} className="rounded bg-gray-950 px-3 py-2">
                          <div className="flex items-center justify-between gap-3">
                            <span className="font-medium">{stage.stage_name}</span>
                            <span className="text-xs text-gray-500">{stage.stage_code}</span>
                          </div>
                          <div className="mt-1 text-xs text-gray-400">
                            {stage.required_gate || "无阶段门"} ·
                            {stage.expected_duration_days
                              ? ` 预计 ${stage.expected_duration_days} 天`
                              : " 未配置停留时长"}
                          </div>
                        </div>
                      ))}
                      {stages.length === 0 && <div className="text-sm text-gray-400">暂无阶段配置</div>}
                    </div>
                  </div>

                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <Clock3 className="h-4 w-4 text-amber-400" />
                      <span className="font-semibold">滞留预警</span>
                    </div>
                    <div className="space-y-2">
                      {dwellAlerts.map((alert) => (
                        <div key={alert.id} className="rounded bg-gray-950 px-3 py-2">
                          <div className="flex items-center gap-2">
                            <Badge className={alert.severity === "CRITICAL" ? "bg-red-500" : "bg-yellow-500"}>
                              {alert.severity}
                            </Badge>
                            <span className="font-medium">{alert.stage || "未知阶段"}</span>
                          </div>
                          <div className="mt-1 text-xs text-gray-400">
                            已停留 {alert.dwell_hours} 小时 / 阈值 {alert.threshold_hours} 小时
                          </div>
                        </div>
                      ))}
                      {dwellAlerts.length === 0 && <div className="text-sm text-gray-400">暂无活跃预警</div>}
                    </div>
                  </div>

                  <div className="rounded-lg bg-gray-800 p-4">
                    <div className="mb-3 flex items-center gap-2">
                      <GitBranch className="h-4 w-4 text-purple-400" />
                      <span className="font-semibold">阶段门规则</span>
                    </div>
                    <div className="space-y-2">
                      {gateConfigs.map((gate) => (
                        <div key={gate.id} className="rounded bg-gray-950 px-3 py-2">
                          <div className="font-medium">{gate.gate_type}</div>
                          <div className="text-sm text-gray-300">{gate.gate_name}</div>
                          <div className="mt-1 text-xs text-gray-400">
                            {gate.description || "无规则说明"}
                          </div>
                        </div>
                      ))}
                      {gateConfigs.length === 0 && <div className="text-sm text-gray-400">暂无阶段门规则</div>}
                    </div>
                  </div>
                </div>

                <div className="rounded-lg bg-gray-800 p-4">
                  <div className="mb-3 flex items-center gap-2">
                    <Workflow className="h-4 w-4 text-cyan-400" />
                    <span className="font-semibold">流转日志</span>
                  </div>
                  <div className="space-y-2">
                    {transitionLogs.map((log) => (
                      <div key={log.id} className="rounded bg-gray-950 px-3 py-3">
                        <div className="flex flex-col gap-2 md:flex-row md:items-center md:justify-between">
                          <div className="font-medium">
                            {log.from_stage || "起点"} → {log.to_stage || "终点"}
                          </div>
                          <div className="text-xs text-gray-500">{formatDate(log.transitioned_at)}</div>
                        </div>
                        <div className="mt-1 text-sm text-gray-300">
                          {log.transition_reason || log.reason || "无变更原因"}
                        </div>
                      </div>
                    ))}
                    {transitionLogs.length === 0 && <div className="text-sm text-gray-400">暂无流转记录</div>}
                  </div>
                </div>
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}
