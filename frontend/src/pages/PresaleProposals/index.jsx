import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Sparkles,
  FileText,
  ClipboardCheck,
  GitBranch,
  RefreshCw,
  PlusCircle,
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
import { presaleApi } from "../../services/api";
import { extractItems, normalizeSolution } from "./utils";
import SolutionListTab from "./SolutionListTab";
import SolutionGenerateTab from "./SolutionGenerateTab";
import SolutionReviewTab from "./SolutionReviewTab";
import SolutionVersionsTab from "./SolutionVersionsTab";

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

export default function PresaleProposals({ embedded = false } = {}) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const contextLeadId = searchParams.get("lead_id") || "";
  const contextTicketId = searchParams.get("ticket_id") || "";
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
  const contextOpportunityIdNumber = useMemo(
    () => parseContextId(contextOpportunityId),
    [contextOpportunityId],
  );
  const contextProjectIdNumber = useMemo(
    () => parseContextId(contextProjectId),
    [contextProjectId],
  );
  const [activeTab, setActiveTab] = useState("list");
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [solutions, setSolutions] = useState([]);
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

    try {
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
      const list = extractItems(response).map(normalizeSolution);
      const filteredList =
        statusFilter === "all"
          ? list
          : list.filter((solution) => solution.status === statusFilter);

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
    } catch (requestError) {
      console.error("加载方案失败:", requestError);
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
    return solutions.filter((solution) => ["DRAFT", "IN_PROGRESS", "REVIEWING"].includes(solution.status));
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
      const comment = reviewComments[solutionId] || (reviewStatus === "APPROVED" ? "方案符合交付标准" : "请补充风险控制与成本说明");
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
              setSelectedSolutionId={setSelectedSolutionId}
              setActiveTab={setActiveTab}
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
