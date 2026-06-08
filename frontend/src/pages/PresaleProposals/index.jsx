import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Sparkles,
  FileText,
  ClipboardCheck,
  GitBranch,
  RefreshCw,
  PlusCircle,
  DollarSign,
  TrendingUp,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Button,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from "../../components/ui";
import { presaleApi, presaleWorkbenchApi } from "../../services/api";
import { extractItems, formatWan, normalizeSolution } from "./utils";
import SolutionListTab from "./SolutionListTab";
import SolutionGenerateTab from "./SolutionGenerateTab";
import SolutionReviewTab from "./SolutionReviewTab";
import SolutionVersionsTab from "./SolutionVersionsTab";

function createEmptyHandoffContext() {
  return {
    costing: { baseline: null },
    quotes: { items: [], total: 0 },
  };
}

function parseContextId(value) {
  if (!value) {
    return null;
  }

  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function appendContextParam(params, key, value) {
  if (value !== undefined && value !== null && value !== "") {
    params.set(key, String(value));
  }
}

function extractContextSolutions(context) {
  const payload = context?.solutions;
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  return [];
}

function normalizeHandoffContext(context) {
  const rawQuotes = context?.quotes;
  const quoteItems = Array.isArray(rawQuotes)
    ? rawQuotes
    : Array.isArray(rawQuotes?.items)
      ? rawQuotes.items
      : [];

  return {
    costing: {
      baseline: context?.costing?.baseline || null,
    },
    quotes: {
      items: quoteItems,
      total: Number(rawQuotes?.total ?? quoteItems.length) || 0,
    },
  };
}

function pickFirstText(...values) {
  return values.find((value) => value !== undefined && value !== null && String(value).trim()) || "";
}

function safeParseList(value) {
  if (!value) {
    return [];
  }
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      if (Array.isArray(parsed)) {
        return parsed.map((item) => String(item).trim()).filter(Boolean);
      }
    } catch {
      return value
        .split(/[\n,，;；]/)
        .map((item) => item.trim())
        .filter(Boolean);
    }
  }
  return [];
}

function inferTestType(detail = {}) {
  const text = [
    detail.test_type,
    detail.application_scenario,
    detail.target_object_type,
    detail.requirement_items,
    detail.technical_spec,
  ].join(" ").toUpperCase();

  if (text.includes("EOL")) {
    return "EOL";
  }
  if (text.includes("ICT")) {
    return "ICT";
  }
  if (text.includes("老化") || text.includes("BURN")) {
    return "BURN_IN";
  }
  if (text.includes("视觉") || text.includes("VISION")) {
    return "VISION";
  }
  return "FCT";
}

function buildGenerationPrefill(context) {
  const detail = context?.assessment?.requirementDetail || {};
  const assessment = context?.assessment?.current || null;
  const ticket = context?.ticket || {};
  const requirementItems = safeParseList(detail.requirement_items);
  const technicalSpec = safeParseList(detail.technical_spec);
  const hasRequirementContext = Boolean(
    detail.id ||
      detail.requirement_version ||
      detail.target_object_type ||
      detail.application_scenario ||
      detail.cycle_time_seconds ||
      detail.workstation_count ||
      detail.acceptance_basis ||
      detail.acceptance_method ||
      requirementItems.length ||
      technicalSpec.length ||
      assessment?.id ||
      ticket.id,
  );

  if (!hasRequirementContext) {
    return null;
  }

  const targetObject = pickFirstText(detail.target_object_type, ticket.product_name, "非标自动化测试对象");
  const scenario = pickFirstText(detail.application_scenario, ticket.opportunity_name, ticket.title);
  const acceptance = pickFirstText(detail.acceptance_basis, detail.acceptance_method);
  const summaryParts = [
    targetObject ? `被测对象：${targetObject}` : "",
    scenario ? `应用场景：${scenario}` : "",
    detail.cycle_time_seconds ? `节拍目标：${detail.cycle_time_seconds}s` : "",
    detail.workstation_count ? `工位数量：${detail.workstation_count}` : "",
    acceptance ? `验收口径：${acceptance}` : "",
    requirementItems.length ? `关键需求：${requirementItems.slice(0, 4).join("、")}` : "",
    technicalSpec.length ? `技术约束：${technicalSpec.slice(0, 4).join("、")}` : "",
    assessment?.total_score != null ? `技术评估：${assessment.total_score}分${assessment.decision ? `，${assessment.decision}` : ""}` : "",
  ].filter(Boolean);

  if (summaryParts.length === 0) {
    return null;
  }

  return {
    name: `${targetObject}${scenario ? `-${scenario}` : ""}售前技术方案`,
    solutionType: "CUSTOM",
    industry: pickFirstText(detail.industry, ticket.industry, "新能源"),
    testType: inferTestType(detail),
    requirementSummary: summaryParts.join("\n"),
    contextPayload: {
      requirement_detail_id: detail.id,
      requirement_version: detail.requirement_version,
      presale_ticket_id: ticket.id,
      technical_assessment_id: assessment?.id,
      technical_assessment_score: assessment?.total_score,
      technical_assessment_decision: assessment?.decision,
      takt_time_s: detail.cycle_time_seconds,
      workstation_count: detail.workstation_count,
      acceptance_basis: acceptance,
    },
  };
}

function buildContextTechnicalSpecLines(contextPayload = {}) {
  const lines = [
    contextPayload.requirement_version ? `需求版本：${contextPayload.requirement_version}` : "",
    contextPayload.requirement_detail_id ? `需求明细ID：${contextPayload.requirement_detail_id}` : "",
    contextPayload.presale_ticket_id ? `售前工单ID：${contextPayload.presale_ticket_id}` : "",
    contextPayload.technical_assessment_id ? `技术评估ID：${contextPayload.technical_assessment_id}` : "",
    contextPayload.technical_assessment_score != null
      ? `技术评估：${contextPayload.technical_assessment_score}分${
          contextPayload.technical_assessment_decision
            ? `，${contextPayload.technical_assessment_decision}`
            : ""
        }`
      : "",
    contextPayload.takt_time_s ? `节拍目标：${contextPayload.takt_time_s}s` : "",
    contextPayload.workstation_count ? `工位数量：${contextPayload.workstation_count}` : "",
    contextPayload.acceptance_basis ? `验收口径：${contextPayload.acceptance_basis}` : "",
  ].filter(Boolean);

  return lines.length > 0 ? ["", "售前上下文追溯：", ...lines] : [];
}

function mergeGenerationPrefill(previous, prefill) {
  if (!prefill) {
    return previous;
  }

  return {
    ...previous,
    name: previous.name || prefill.name || "",
    solutionType: previous.solutionType || prefill.solutionType || "CUSTOM",
    industry: previous.industry || prefill.industry || "新能源",
    testType: previous.testType || prefill.testType || "FCT",
    requirementSummary: previous.requirementSummary || prefill.requirementSummary || "",
    contextPayload: {
      ...(previous.contextPayload || {}),
      ...(prefill.contextPayload || {}),
    },
  };
}

function getQuoteCurrentVersion(quote) {
  return quote?.current_version || quote?.currentVersion || quote?.version || null;
}

function getQuoteAmount(quote) {
  const currentVersion = getQuoteCurrentVersion(quote);
  return (
    currentVersion?.total_price ??
    currentVersion?.totalPrice ??
    quote?.total_price ??
    quote?.totalPrice ??
    null
  );
}

function getQuoteMargin(quote) {
  const currentVersion = getQuoteCurrentVersion(quote);
  return (
    currentVersion?.gross_margin ??
    currentVersion?.grossMargin ??
    quote?.gross_margin ??
    quote?.grossMargin ??
    null
  );
}

function formatWanAmount(amount) {
  if (amount === null || amount === undefined || amount === "") {
    return "-";
  }

  const numeric = Number(amount);
  return Number.isFinite(numeric) ? `${formatWan(numeric)} 万` : "-";
}

function formatMargin(value) {
  if (value === null || value === undefined || value === "") {
    return "-";
  }

  const numeric = Number(value);
  if (!Number.isFinite(numeric)) {
    return "-";
  }

  const percent = Math.abs(numeric) <= 1 ? numeric * 100 : numeric;
  return `${percent.toFixed(1)}%`;
}

function PresaleHandoffSummary({ handoffContext }) {
  const baseline = handoffContext?.costing?.baseline || null;
  const quoteItems = handoffContext?.quotes?.items || [];
  const quoteTotal = Number(handoffContext?.quotes?.total ?? quoteItems.length) || 0;
  const latestQuote = quoteItems[0] || null;

  if (!baseline && quoteTotal <= 0) {
    return null;
  }

  const baselineName =
    baseline?.solution_name ||
    baseline?.solution_no ||
    (baseline?.solution_id ? `方案 #${baseline.solution_id}` : "未绑定方案");
  const quoteCode =
    latestQuote?.quote_code ||
    latestQuote?.quoteCode ||
    (latestQuote?.id ? `报价 #${latestQuote.id}` : "待生成报价");
  const margin = baseline?.gross_margin_rate ?? getQuoteMargin(latestQuote);

  return (
    <div className="mt-4 rounded-xl border border-cyan-400/20 bg-cyan-500/5 p-4 shadow-sm">
      <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <p className="text-sm font-semibold text-slate-100">售前方案闭环状态</p>
          <p className="mt-1 text-xs text-slate-400">{baselineName}</p>
        </div>
        <span className="w-fit rounded-full border border-emerald-400/30 bg-emerald-500/10 px-3 py-1 text-xs font-medium text-emerald-200">
          {quoteTotal > 0 ? `已生成 ${quoteTotal} 张报价` : "待生成报价"}
        </span>
      </div>

      <div className="mt-4 grid gap-3 md:grid-cols-3">
        <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <DollarSign className="h-4 w-4 text-cyan-300" />
            成本基线
          </div>
          <p className="mt-2 text-lg font-semibold text-slate-100">
            {formatWanAmount(baseline?.estimated_cost)}
          </p>
          <p className="mt-1 text-xs text-slate-500">
            建议报价 {formatWanAmount(baseline?.suggested_price)}
          </p>
        </div>

        <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <FileText className="h-4 w-4 text-violet-300" />
            报价单
          </div>
          <p className="mt-2 text-lg font-semibold text-slate-100">{quoteCode}</p>
          <p className="mt-1 text-xs text-slate-500">
            报价金额 {formatWanAmount(getQuoteAmount(latestQuote))}
          </p>
        </div>

        <div className="rounded-lg border border-white/10 bg-slate-950/40 p-3">
          <div className="flex items-center gap-2 text-xs text-slate-400">
            <TrendingUp className="h-4 w-4 text-emerald-300" />
            毛利率
          </div>
          <p className="mt-2 text-lg font-semibold text-slate-100">
            {formatMargin(margin)}
          </p>
          <p className="mt-1 text-xs text-slate-500">来自成本基线/当前报价版本</p>
        </div>
      </div>
    </div>
  );
}

function filterSolutions(solutions, { statusFilter, searchKeyword }) {
  const keyword = searchKeyword.trim().toLowerCase();
  return solutions.filter((solution) => {
    const matchesStatus = statusFilter === "all" || solution.status === statusFilter;
    if (!matchesStatus) {
      return false;
    }
    if (!keyword) {
      return true;
    }
    return [
      solution.name,
      solution.solutionNo,
      solution.industry,
      solution.requirementSummary,
      solution.solutionOverview,
    ].some((value) => String(value || "").toLowerCase().includes(keyword));
  });
}

export default function PresaleProposals({ embedded = false } = {}) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const contextLeadId = searchParams.get("lead_id") || "";
  const contextTicketId = searchParams.get("ticket_id") || "";
  const contextCustomerId = searchParams.get("customer_id") || "";
  const contextOpportunityId = searchParams.get("opportunity_id") || "";
  const contextProjectId = searchParams.get("project_id") || "";
  const contextLeadIdNumber = useMemo(
    () => parseContextId(contextLeadId),
    [contextLeadId],
  );
  const contextTicketIdNumber = useMemo(
    () => parseContextId(contextTicketId),
    [contextTicketId],
  );
  const contextCustomerIdNumber = useMemo(
    () => parseContextId(contextCustomerId),
    [contextCustomerId],
  );
  const contextOpportunityIdNumber = useMemo(
    () => parseContextId(contextOpportunityId),
    [contextOpportunityId],
  );
  const contextProjectIdNumber = useMemo(
    () => parseContextId(contextProjectId),
    [contextProjectId],
  );
  const contextSourceType = contextOpportunityIdNumber
    ? "opportunity"
    : contextLeadIdNumber
      ? "lead"
      : "";
  const contextSourceId = contextOpportunityIdNumber || contextLeadIdNumber;
  const [activeTab, setActiveTab] = useState("list");
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [solutions, setSolutions] = useState([]);
  const [handoffContext, setHandoffContext] = useState(createEmptyHandoffContext);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [generating, setGenerating] = useState(false);
  const [generationError, setGenerationError] = useState("");
  const [latestGenerated, setLatestGenerated] = useState(null);
  const [generatorForm, setGeneratorForm] = useState({
    name: "",
    solutionType: "CUSTOM",
    industry: "新能源",
    testType: "FCT",
    requirementSummary: "",
    estimatedCost: "",
    suggestedPrice: "",
    estimatedHours: "",
    estimatedDuration: "",
    contextPayload: {},
  });

  const [reviewActionLoadingId, setReviewActionLoadingId] = useState(null);
  const [reviewComments, setReviewComments] = useState({});

  const [selectedSolutionId, setSelectedSolutionId] = useState("");
  const [selectedVersionId, setSelectedVersionId] = useState("");
  const [versions, setVersions] = useState([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [versionsError, setVersionsError] = useState("");

  const loadSolutions = useCallback(async () => {
    setLoading(true);
    setError("");
    setHandoffContext(createEmptyHandoffContext());

    try {
      const applySolutions = (items) => {
        const list = (items || []).map(normalizeSolution);
        const filteredList = filterSolutions(list, { statusFilter, searchKeyword });

        setSolutions(filteredList);

        if (filteredList.length > 0) {
          setSelectedSolutionId((previous) => {
            const stillVisible = filteredList.some(
              (solution) => String(solution.id) === String(previous),
            );
            return stillVisible ? previous : String(filteredList[0].id);
          });
        } else {
          setSelectedSolutionId("");
        }
      };

      if (contextSourceType && contextSourceId) {
        try {
          const contextParams = {
            sourceType: contextSourceType,
            sourceId: contextSourceId,
          };
          if (contextTicketIdNumber) {
            contextParams.presaleTicketId = contextTicketIdNumber;
          }
          const context = await presaleWorkbenchApi.loadContext(contextParams);
          setHandoffContext(normalizeHandoffContext(context));
          setGeneratorForm((previous) =>
            mergeGenerationPrefill(previous, buildGenerationPrefill(context)),
          );
          const contextSolutions = extractContextSolutions(context);
          if (contextSolutions.length > 0) {
            applySolutions(contextSolutions);
            return;
          }
        } catch (contextError) {
          console.warn("加载售前方案聚合上下文失败:", contextError);
          setHandoffContext(createEmptyHandoffContext());
        }
      }

      const params = { page: 1, page_size: 100 };
      if (searchKeyword.trim()) {
        params.keyword = searchKeyword.trim();
      }
      if (contextLeadIdNumber) {
        params.lead_id = contextLeadId;
      }
      if (contextOpportunityIdNumber) {
        params.opportunity_id = contextOpportunityId;
      }
      if (contextTicketIdNumber) {
        params.ticket_id = contextTicketId;
      }
      if (contextProjectIdNumber) {
        params.project_id = contextProjectId;
      }

      const response = await presaleApi.solutions.list(params);
      applySolutions(extractItems(response));
    } catch (requestError) {
      console.error("加载方案失败:", requestError);
      setHandoffContext(createEmptyHandoffContext());
      setError(requestError?.response?.data?.detail || requestError?.message || "方案加载失败");
    } finally {
      setLoading(false);
    }
  }, [
    contextLeadId,
    contextLeadIdNumber,
    contextOpportunityId,
    contextOpportunityIdNumber,
    contextProjectId,
    contextProjectIdNumber,
    contextSourceId,
    contextSourceType,
    contextTicketId,
    contextTicketIdNumber,
    searchKeyword,
    statusFilter,
  ]);

  const loadVersions = useCallback(async (solutionId) => {
    if (!solutionId) {
      setVersions([]);
      setSelectedVersionId("");
      return;
    }

    setVersionsLoading(true);
    setVersionsError("");

    try {
      const response = await presaleApi.solutions.getVersions(Number(solutionId));
      const list = extractItems(response).map(normalizeSolution);
      setVersions(list);

      if (list.length > 0) {
        const latestVersion = list[list.length - 1];
        setSelectedVersionId(String(latestVersion.id));
      } else {
        setSelectedVersionId("");
      }
    } catch (requestError) {
      console.error("加载版本失败:", requestError);
      setVersions([]);
      setSelectedVersionId("");
      setVersionsError(requestError?.response?.data?.detail || requestError?.message || "版本加载失败");
    } finally {
      setVersionsLoading(false);
    }
  }, []);

  useEffect(() => {
    loadSolutions();
  }, [loadSolutions]);

  useEffect(() => {
    if (activeTab === "versions") {
      loadVersions(selectedSolutionId);
    }
  }, [activeTab, selectedSolutionId, loadVersions]);

  const stats = useMemo(() => {
    return {
      total: solutions.length,
      draft: solutions.filter((solution) => solution.status === "DRAFT").length,
      reviewing: solutions.filter((solution) => solution.status === "REVIEWING").length,
      approved: solutions.filter((solution) => solution.status === "APPROVED").length,
    };
  }, [solutions]);

  const reviewQueue = useMemo(() => {
    return solutions.filter((solution) => solution.status === "REVIEWING");
  }, [solutions]);

  const selectedVersion = useMemo(() => {
    if (!selectedVersionId) {
      return null;
    }
    return versions.find((version) => String(version.id) === String(selectedVersionId)) || null;
  }, [selectedVersionId, versions]);

  const handleGenerateFieldChange = (field, value) => {
    setGeneratorForm((previous) => ({
      ...previous,
      [field]: value,
    }));
  };

  const applyTemplateSuggestion = (template) => {
    const nextName = `${template.title} - ${new Date().toLocaleDateString("zh-CN")}`;
    const nextRequirement = `客户期望在 ${template.days} 内完成导入，重点关注交付节奏、系统稳定性与后续扩展能力。`;

    setGeneratorForm((previous) => ({
      ...previous,
      name: nextName,
      requirementSummary: nextRequirement,
    }));
  };

  const handleGenerateProposal = async () => {
    if (!generatorForm.name.trim()) {
      setGenerationError("请填写方案名称");
      return;
    }

    setGenerating(true);
    setGenerationError("");

    try {
      const solutionOverview = `围绕${generatorForm.requirementSummary || "客户业务诉求"}构建三层方案结构：业务目标层、产线实现层、数据闭环层。`;
      const technicalSpec = [
        "1) 工站节拍与稼动率监控",
        "2) 测试数据与MES打通",
        "3) 模块化治具与快速换型",
        ...buildContextTechnicalSpecLines(generatorForm.contextPayload),
      ].join("\n");

      const payload = {
        name: generatorForm.name.trim(),
        solution_type: generatorForm.solutionType,
        industry: generatorForm.industry,
        test_type: generatorForm.testType,
        requirement_summary: generatorForm.requirementSummary,
        solution_overview: solutionOverview,
        technical_spec: technicalSpec,
      };
      if (contextLeadIdNumber) {
        payload.lead_id = contextLeadIdNumber;
      }
      if (contextOpportunityIdNumber) {
        payload.opportunity_id = contextOpportunityIdNumber;
      }
      if (contextTicketIdNumber) {
        payload.ticket_id = contextTicketIdNumber;
      }
      if (contextCustomerIdNumber) {
        payload.customer_id = contextCustomerIdNumber;
      }
      if (contextProjectIdNumber) {
        payload.project_id = contextProjectIdNumber;
      }

      if (generatorForm.estimatedCost) {
        payload.estimated_cost = Number(generatorForm.estimatedCost);
      }
      if (generatorForm.suggestedPrice) {
        payload.suggested_price = Number(generatorForm.suggestedPrice);
      }
      if (generatorForm.estimatedHours) {
        payload.estimated_hours = Number(generatorForm.estimatedHours);
      }
      if (generatorForm.estimatedDuration) {
        payload.estimated_duration = Number(generatorForm.estimatedDuration);
      }

      const response = await presaleApi.solutions.create(payload);
      const created = normalizeSolution(response?.data || response);
      setLatestGenerated(created);

      await loadSolutions();
      setSelectedSolutionId(String(created.id));
    } catch (requestError) {
      console.error("生成方案失败:", requestError);
      setGenerationError(requestError?.response?.data?.detail || requestError?.message || "方案生成失败");
    } finally {
      setGenerating(false);
    }
  };

  const handleReviewAction = async (solutionId, reviewStatus) => {
    setReviewActionLoadingId(solutionId);

    try {
      const defaultCommentMap = {
        REVIEW: "提交方案评审",
        APPROVED: "方案符合交付标准",
        REJECTED: "请补充风险控制与成本说明",
      };
      const comment = reviewComments[solutionId] || defaultCommentMap[reviewStatus] || "方案评审状态更新";
      await presaleApi.solutions.review(solutionId, {
        review_status: reviewStatus,
        review_comment: comment,
      });

      await loadSolutions();
      if (activeTab === "versions") {
        await loadVersions(selectedSolutionId || solutionId);
      }
    } catch (requestError) {
      console.error("方案评审失败:", requestError);
      setError(requestError?.response?.data?.detail || requestError?.message || "方案评审失败");
    } finally {
      setReviewActionLoadingId(null);
    }
  };

  const buildSolutionDetailPath = (solution) => {
    const params = new URLSearchParams();
    appendContextParam(params, "ticket_id", solution?.ticketId || contextTicketId);
    appendContextParam(params, "lead_id", solution?.leadId || contextLeadId);
    appendContextParam(params, "opportunity_id", solution?.opportunityId || contextOpportunityId);
    appendContextParam(params, "project_id", solution?.projectId || contextProjectId);
    const query = params.toString();
    return `/solutions/${solution.id}${query ? `?${query}` : ""}`;
  };

  const buildQuoteCreatePath = (solution) => {
    const params = new URLSearchParams();
    appendContextParam(params, "opportunity_id", solution?.opportunityId || contextOpportunityId);
    appendContextParam(params, "customer_id", solution?.customerId || contextCustomerId);
    appendContextParam(params, "solution_id", solution?.id);
    appendContextParam(params, "ticket_id", solution?.ticketId || contextTicketId);
    appendContextParam(params, "project_id", solution?.projectId || contextProjectId);
    const query = params.toString();
    return `/sales/quotes/create${query ? `?${query}` : ""}`;
  };

  const actionButtons = (
    <div className="flex items-center gap-2">
      <Button variant="outline" onClick={loadSolutions} disabled={loading}>
        <RefreshCw className={`mr-2 h-4 w-4 ${loading ? "animate-spin" : ""}`} />
        刷新数据
      </Button>
      <Button onClick={() => setActiveTab("generate")}>
        <PlusCircle className="mr-2 h-4 w-4" />
        新建方案
      </Button>
    </div>
  );

  const content = (
    <>
      {!embedded && (
        <PageHeader
          title="售前方案管理"
          description="方案列表、AI生成、方案评审与版本管理一体化协同"
          actions={actionButtons}
        />
      )}

      {embedded && (
        <div className="flex justify-end">
          {actionButtons}
        </div>
      )}

        {error && (
          <Alert className="mb-4 border-red-500/30 bg-red-500/10 text-red-100">
            <AlertTitle>操作提醒</AlertTitle>
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        <PresaleHandoffSummary handoffContext={handoffContext} />

        <Tabs value={activeTab} onValueChange={setActiveTab} className="mt-6 space-y-6">
          <TabsList className="grid h-auto w-full grid-cols-2 gap-2 lg:w-[760px] lg:grid-cols-4">
            <TabsTrigger value="list" className="gap-2 py-2">
              <FileText className="h-4 w-4" />
              方案列表
            </TabsTrigger>
            <TabsTrigger value="generate" className="gap-2 py-2">
              <Sparkles className="h-4 w-4" />
              方案生成
            </TabsTrigger>
            <TabsTrigger value="review" className="gap-2 py-2">
              <ClipboardCheck className="h-4 w-4" />
              方案评审
            </TabsTrigger>
            <TabsTrigger value="versions" className="gap-2 py-2">
              <GitBranch className="h-4 w-4" />
              版本管理
            </TabsTrigger>
          </TabsList>

          <TabsContent value="list">
            <SolutionListTab
              stats={stats}
              searchKeyword={searchKeyword}
              setSearchKeyword={setSearchKeyword}
              statusFilter={statusFilter}
              setStatusFilter={setStatusFilter}
              loading={loading}
              solutions={solutions}
              onViewSolution={(solution) => navigate(buildSolutionDetailPath(solution))}
              onCreateQuote={(solution) => navigate(buildQuoteCreatePath(solution))}
              setSelectedSolutionId={setSelectedSolutionId}
              setActiveTab={setActiveTab}
              onSubmitReview={(solution) => handleReviewAction(solution.id, "REVIEW")}
              reviewActionLoadingId={reviewActionLoadingId}
            />
          </TabsContent>

          <TabsContent value="generate">
            <SolutionGenerateTab
              generatorForm={generatorForm}
              handleGenerateFieldChange={handleGenerateFieldChange}
              applyTemplateSuggestion={applyTemplateSuggestion}
              generationError={generationError}
              generating={generating}
              handleGenerateProposal={handleGenerateProposal}
              setGeneratorForm={setGeneratorForm}
              latestGenerated={latestGenerated}
              onViewSolution={(solution) => navigate(buildSolutionDetailPath(solution))}
            />
          </TabsContent>

          <TabsContent value="review">
            <SolutionReviewTab
              reviewQueue={reviewQueue}
              reviewComments={reviewComments}
              setReviewComments={setReviewComments}
              reviewActionLoadingId={reviewActionLoadingId}
              handleReviewAction={handleReviewAction}
              setSelectedSolutionId={setSelectedSolutionId}
              setActiveTab={setActiveTab}
            />
          </TabsContent>

          <TabsContent value="versions">
            <SolutionVersionsTab
              solutions={solutions}
              selectedSolutionId={selectedSolutionId}
              setSelectedSolutionId={setSelectedSolutionId}
              versionsError={versionsError}
              versionsLoading={versionsLoading}
              versions={versions}
              selectedVersionId={selectedVersionId}
              setSelectedVersionId={setSelectedVersionId}
              selectedVersion={selectedVersion}
            />
          </TabsContent>
        </Tabs>
    </>
  );

  if (embedded) {
    return <div className="space-y-6">{content}</div>;
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        {content}
      </div>
    </div>
  );
}
