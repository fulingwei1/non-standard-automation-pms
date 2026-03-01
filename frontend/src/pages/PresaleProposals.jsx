import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Sparkles,
  FileText,
  ClipboardCheck,
  GitBranch,
  Search,
  RefreshCw,
  PlusCircle,
  CheckCircle2,
  XCircle,
  ArrowRight,
  CalendarClock,
  Coins,
  Layers,
  MessageSquareText,
} from "lucide-react";
import { motion } from "framer-motion";
import { PageHeader } from "../components/layout";
import {
  Alert,
  AlertDescription,
  AlertTitle,
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Input,
  Progress,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Textarea,
} from "../components/ui";
import { presaleApi } from "../services/api";

const STATUS_CONFIG = {
  DRAFT: { label: "草稿", className: "bg-slate-500/20 text-slate-200 border-slate-400/30" },
  IN_PROGRESS: {
    label: "编写中",
    className: "bg-blue-500/20 text-blue-200 border-blue-400/30",
  },
  REVIEWING: {
    label: "评审中",
    className: "bg-amber-500/20 text-amber-200 border-amber-400/30",
  },
  APPROVED: {
    label: "已通过",
    className: "bg-emerald-500/20 text-emerald-200 border-emerald-400/30",
  },
  REJECTED: {
    label: "已驳回",
    className: "bg-red-500/20 text-red-200 border-red-400/30",
  },
};

const TYPE_OPTIONS = [
  { value: "CUSTOM", label: "定制化方案" },
  { value: "STANDARD", label: "标准方案" },
  { value: "UPGRADE", label: "升级改造" },
  { value: "INTEGRATION", label: "系统集成" },
];

const INDUSTRY_OPTIONS = ["新能源", "3C电子", "汽车零部件", "医疗器械", "半导体", "通用制造"];

const TEST_TYPE_OPTIONS = [
  { value: "ICT", label: "ICT 测试" },
  { value: "FCT", label: "FCT 测试" },
  { value: "EOL", label: "EOL 测试" },
  { value: "VISION", label: "视觉检测" },
  { value: "ASSEMBLY", label: "组装线" },
];

const AI_TEMPLATE_SUGGESTIONS = [
  {
    title: "快交付方案",
    description: "优先复用成熟模块，适合交期紧张项目",
    days: "4-6 周",
  },
  {
    title: "平衡成本方案",
    description: "在性能与成本间取得平衡，适合大多数量产项目",
    days: "6-8 周",
  },
  {
    title: "高性能方案",
    description: "强调高精度与扩展性，适合技术标竞争项目",
    days: "8-10 周",
  },
];

function extractItems(response) {
  const payload = response?.data ?? response;
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  if (Array.isArray(payload?.data?.items)) {
    return payload.data.items;
  }
  if (Array.isArray(payload?.data)) {
    return payload.data;
  }
  return [];
}

function normalizeSolution(solution) {
  return {
    id: solution?.id,
    solutionNo: solution?.solution_no || `SOL-${solution?.id || "NEW"}`,
    name: solution?.name || "未命名方案",
    solutionType: solution?.solution_type || "CUSTOM",
    industry: solution?.industry || "未分类行业",
    testType: solution?.test_type || "-",
    requirementSummary: solution?.requirement_summary || "暂无需求摘要",
    solutionOverview: solution?.solution_overview || "暂无方案概述",
    technicalSpec: solution?.technical_spec || "暂无技术规格",
    estimatedCost: Number(solution?.estimated_cost) || 0,
    suggestedPrice: Number(solution?.suggested_price) || 0,
    estimatedHours: Number(solution?.estimated_hours) || 0,
    estimatedDuration: Number(solution?.estimated_duration) || 0,
    status: solution?.status || "DRAFT",
    version: solution?.version || "V1.0",
    reviewStatus: solution?.review_status,
    reviewComment: solution?.review_comment,
    createdAt: solution?.created_at,
    updatedAt: solution?.updated_at,
  };
}

function formatDate(value) {
  if (!value) {
    return "-";
  }

  const date = new Date(value);
  if (Number.isNaN(date.getTime())) {
    return String(value);
  }

  return date.toLocaleString("zh-CN", {
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function formatWan(amount) {
  if (!amount) {
    return "0.0";
  }
  return (Number(amount) / 10000).toFixed(1);
}

function getStatusConfig(status) {
  return STATUS_CONFIG[status] || {
    label: status || "未知",
    className: "bg-slate-500/20 text-slate-200 border-slate-400/30",
  };
}

function calculateCompleteness(solution) {
  let score = 20;
  if (solution.requirementSummary && solution.requirementSummary !== "暂无需求摘要") {
    score += 25;
  }
  if (solution.solutionOverview && solution.solutionOverview !== "暂无方案概述") {
    score += 25;
  }
  if (solution.technicalSpec && solution.technicalSpec !== "暂无技术规格") {
    score += 20;
  }
  if (solution.estimatedCost > 0 || solution.suggestedPrice > 0) {
    score += 10;
  }
  return Math.min(score, 100);
}

export default function PresaleProposals() {
  const navigate = useNavigate();
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
      if (statusFilter !== "all") {
        params.status = statusFilter;
      }
      if (searchKeyword.trim()) {
        params.keyword = searchKeyword.trim();
      }

      const response = await presaleApi.solutions.list(params);
      const list = extractItems(response).map(normalizeSolution);
      setSolutions(list);

      if (list.length > 0) {
        setSelectedSolutionId((previous) => previous || String(list[0].id));
      }
    } catch (requestError) {
      console.error("加载方案失败:", requestError);
      setError(requestError?.response?.data?.detail || requestError?.message || "方案加载失败");
    } finally {
      setLoading(false);
    }
  }, [searchKeyword, statusFilter]);

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
      setActiveTab("list");
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

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
        <PageHeader
          title="售前方案管理"
          description="方案列表、AI生成、方案评审与版本管理一体化协同"
          actions={
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
          }
        />

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

          <TabsContent value="list" className="space-y-6">
            <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
              {[
                { label: "总方案数", value: stats.total, icon: Layers, color: "text-slate-100" },
                { label: "草稿", value: stats.draft, icon: FileText, color: "text-slate-300" },
                { label: "评审中", value: stats.reviewing, icon: ClipboardCheck, color: "text-amber-300" },
                { label: "已通过", value: stats.approved, icon: CheckCircle2, color: "text-emerald-300" },
              ].map((item) => (
                <Card key={item.label} className="border-white/10 bg-white/5 backdrop-blur">
                  <CardContent className="pt-5">
                    <div className="mb-2 flex items-center justify-between">
                      <p className="text-xs text-slate-400">{item.label}</p>
                      <item.icon className={`h-4 w-4 ${item.color}`} />
                    </div>
                    <p className={`text-3xl font-semibold ${item.color}`}>{item.value}</p>
                  </CardContent>
                </Card>
              ))}
            </div>

            <Card className="border-white/10 bg-white/5 backdrop-blur">
              <CardContent className="pt-6">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div className="relative w-full md:max-w-md">
                    <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2 text-slate-500" />
                    <Input
                      className="pl-9"
                      placeholder="搜索方案名称 / 编号"
                      value={searchKeyword}
                      onChange={(event) => setSearchKeyword(event.target.value)}
                    />
                  </div>

                  <Select value={statusFilter} onValueChange={setStatusFilter}>
                    <SelectTrigger className="w-full md:w-[200px]">
                      <SelectValue placeholder="筛选状态" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="all">全部状态</SelectItem>
                      {Object.entries(STATUS_CONFIG).map(([key, config]) => (
                        <SelectItem key={key} value={key}>
                          {config.label}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {loading ? (
              <div className="rounded-xl border border-white/10 bg-white/5 py-14 text-center text-slate-300">
                <RefreshCw className="mx-auto mb-3 h-6 w-6 animate-spin" />
                正在加载方案列表...
              </div>
            ) : (
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">
                {solutions.length > 0 ? (
                  solutions.map((solution) => {
                    const statusConfig = getStatusConfig(solution.status);
                    return (
                      <motion.div
                        key={solution.id}
                        initial={{ opacity: 0, y: 12 }}
                        animate={{ opacity: 1, y: 0 }}
                        transition={{ duration: 0.2 }}
                      >
                        <Card className="h-full border-white/10 bg-slate-900/70 transition-colors hover:border-cyan-400/50 hover:bg-slate-900">
                          <CardHeader>
                            <div className="mb-2 flex items-center justify-between gap-3">
                              <Badge className={statusConfig.className}>{statusConfig.label}</Badge>
                              <Badge variant="outline" className="border-white/20 text-slate-200">
                                {solution.version}
                              </Badge>
                            </div>
                            <CardTitle className="line-clamp-2 text-base">{solution.name}</CardTitle>
                            <CardDescription className="text-xs text-slate-400">
                              {solution.solutionNo} · {solution.industry}
                            </CardDescription>
                          </CardHeader>

                          <CardContent className="space-y-4">
                            <p className="line-clamp-3 text-sm text-slate-300">{solution.requirementSummary}</p>

                            <div className="grid grid-cols-2 gap-2 text-xs text-slate-400">
                              <div className="rounded-lg border border-white/10 bg-white/5 p-2">
                                <div className="mb-1 flex items-center gap-1">
                                  <Coins className="h-3.5 w-3.5" />
                                  预估成本
                                </div>
                                <div className="text-sm font-medium text-slate-100">
                                  {formatWan(solution.estimatedCost)} 万
                                </div>
                              </div>
                              <div className="rounded-lg border border-white/10 bg-white/5 p-2">
                                <div className="mb-1 flex items-center gap-1">
                                  <MessageSquareText className="h-3.5 w-3.5" />
                                  建议报价
                                </div>
                                <div className="text-sm font-medium text-cyan-200">
                                  {formatWan(solution.suggestedPrice)} 万
                                </div>
                              </div>
                            </div>

                            <div className="flex items-center justify-between text-xs text-slate-400">
                              <span className="inline-flex items-center gap-1">
                                <CalendarClock className="h-3.5 w-3.5" />
                                {formatDate(solution.updatedAt || solution.createdAt)}
                              </span>
                              <span>{solution.testType}</span>
                            </div>

                            <div className="flex gap-2">
                              <Button
                                variant="outline"
                                size="sm"
                                className="flex-1"
                                onClick={() => navigate(`/solutions/${solution.id}`)}
                              >
                                查看详情
                              </Button>
                              <Button
                                size="sm"
                                className="flex-1"
                                onClick={() => {
                                  setSelectedSolutionId(String(solution.id));
                                  setActiveTab("versions");
                                }}
                              >
                                版本管理
                              </Button>
                            </div>
                          </CardContent>
                        </Card>
                      </motion.div>
                    );
                  })
                ) : (
                  <div className="col-span-full rounded-xl border border-dashed border-white/20 py-16 text-center text-slate-400">
                    暂无符合条件的方案，尝试调整筛选条件
                  </div>
                )}
              </div>
            )}
          </TabsContent>

          <TabsContent value="generate" className="space-y-6">
            <div className="grid gap-4 xl:grid-cols-3">
              <Card className="xl:col-span-2 border-white/10 bg-white/5 backdrop-blur">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-cyan-200">
                    <Sparkles className="h-5 w-5" />
                    AI 方案生成
                  </CardTitle>
                  <CardDescription>
                    按业务需求快速产出技术方案，并自动生成可评审版本
                  </CardDescription>
                </CardHeader>

                <CardContent className="space-y-4">
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="space-y-2">
                      <p className="text-xs text-slate-400">方案名称</p>
                      <Input
                        placeholder="例如：新能源PACK线FCT测试方案"
                        value={generatorForm.name}
                        onChange={(event) => handleGenerateFieldChange("name", event.target.value)}
                      />
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs text-slate-400">方案类型</p>
                      <Select
                        value={generatorForm.solutionType}
                        onValueChange={(value) => handleGenerateFieldChange("solutionType", value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {TYPE_OPTIONS.map((type) => (
                            <SelectItem key={type.value} value={type.value}>
                              {type.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs text-slate-400">所属行业</p>
                      <Select
                        value={generatorForm.industry}
                        onValueChange={(value) => handleGenerateFieldChange("industry", value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {INDUSTRY_OPTIONS.map((industry) => (
                            <SelectItem key={industry} value={industry}>
                              {industry}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>

                    <div className="space-y-2">
                      <p className="text-xs text-slate-400">测试类型</p>
                      <Select
                        value={generatorForm.testType}
                        onValueChange={(value) => handleGenerateFieldChange("testType", value)}
                      >
                        <SelectTrigger>
                          <SelectValue />
                        </SelectTrigger>
                        <SelectContent>
                          {TEST_TYPE_OPTIONS.map((item) => (
                            <SelectItem key={item.value} value={item.value}>
                              {item.label}
                            </SelectItem>
                          ))}
                        </SelectContent>
                      </Select>
                    </div>
                  </div>

                  <div className="space-y-2">
                    <p className="text-xs text-slate-400">需求摘要</p>
                    <Textarea
                      placeholder="填写产线痛点、交付目标、关键性能指标，AI会自动生成方案结构"
                      rows={5}
                      value={generatorForm.requirementSummary}
                      onChange={(event) =>
                        handleGenerateFieldChange("requirementSummary", event.target.value)
                      }
                    />
                  </div>

                  <div className="grid gap-4 md:grid-cols-4">
                    <div className="space-y-2">
                      <p className="text-xs text-slate-400">预估成本 (元)</p>
                      <Input
                        type="number"
                        placeholder="1200000"
                        value={generatorForm.estimatedCost}
                        onChange={(event) =>
                          handleGenerateFieldChange("estimatedCost", event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs text-slate-400">建议报价 (元)</p>
                      <Input
                        type="number"
                        placeholder="1680000"
                        value={generatorForm.suggestedPrice}
                        onChange={(event) =>
                          handleGenerateFieldChange("suggestedPrice", event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs text-slate-400">预估工时</p>
                      <Input
                        type="number"
                        placeholder="220"
                        value={generatorForm.estimatedHours}
                        onChange={(event) =>
                          handleGenerateFieldChange("estimatedHours", event.target.value)
                        }
                      />
                    </div>
                    <div className="space-y-2">
                      <p className="text-xs text-slate-400">预估周期 (天)</p>
                      <Input
                        type="number"
                        placeholder="45"
                        value={generatorForm.estimatedDuration}
                        onChange={(event) =>
                          handleGenerateFieldChange("estimatedDuration", event.target.value)
                        }
                      />
                    </div>
                  </div>

                  {generationError && (
                    <Alert className="border-red-500/30 bg-red-500/10 text-red-100">
                      <AlertTitle>生成失败</AlertTitle>
                      <AlertDescription>{generationError}</AlertDescription>
                    </Alert>
                  )}

                  <div className="flex items-center gap-2">
                    <Button onClick={handleGenerateProposal} disabled={generating}>
                      <Sparkles className={`mr-2 h-4 w-4 ${generating ? "animate-pulse" : ""}`} />
                      {generating ? "正在生成..." : "生成并保存方案"}
                    </Button>
                    <Button
                      variant="outline"
                      onClick={() => {
                        setGeneratorForm((previous) => ({
                          ...previous,
                          name: "",
                          requirementSummary: "",
                        }));
                      }}
                    >
                      清空输入
                    </Button>
                  </div>
                </CardContent>
              </Card>

              <Card className="border-white/10 bg-slate-900/70">
                <CardHeader>
                  <CardTitle className="text-base">推荐生成模板</CardTitle>
                  <CardDescription>一键填入常用生成参数</CardDescription>
                </CardHeader>
                <CardContent className="space-y-3">
                  {AI_TEMPLATE_SUGGESTIONS.map((template) => (
                    <button
                      key={template.title}
                      type="button"
                      className="w-full rounded-lg border border-white/10 bg-white/5 p-3 text-left transition-colors hover:border-cyan-400/40 hover:bg-cyan-500/10"
                      onClick={() => applyTemplateSuggestion(template)}
                    >
                      <p className="text-sm font-medium text-slate-100">{template.title}</p>
                      <p className="mt-1 text-xs text-slate-400">{template.description}</p>
                      <p className="mt-2 text-xs text-cyan-200">交付周期参考：{template.days}</p>
                    </button>
                  ))}
                </CardContent>
              </Card>
            </div>

            {latestGenerated && (
              <Card className="border-cyan-400/30 bg-cyan-500/5">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-cyan-200">
                    <CheckCircle2 className="h-5 w-5" />
                    最近生成方案
                  </CardTitle>
                </CardHeader>
                <CardContent className="grid gap-4 md:grid-cols-3">
                  <div>
                    <p className="text-xs text-slate-400">方案名称</p>
                    <p className="mt-1 text-sm text-slate-100">{latestGenerated.name}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">方案编号</p>
                    <p className="mt-1 text-sm text-slate-100">{latestGenerated.solutionNo}</p>
                  </div>
                  <div>
                    <p className="text-xs text-slate-400">版本号</p>
                    <p className="mt-1 text-sm text-slate-100">{latestGenerated.version}</p>
                  </div>
                  <div className="md:col-span-3">
                    <Button
                      variant="outline"
                      onClick={() => navigate(`/solutions/${latestGenerated.id}`)}
                    >
                      打开方案详情
                      <ArrowRight className="ml-2 h-4 w-4" />
                    </Button>
                  </div>
                </CardContent>
              </Card>
            )}
          </TabsContent>

          <TabsContent value="review" className="space-y-4">
            {reviewQueue.length === 0 ? (
              <div className="rounded-xl border border-dashed border-white/20 py-16 text-center text-slate-400">
                当前没有待评审方案
              </div>
            ) : (
              reviewQueue.map((solution) => {
                const completeness = calculateCompleteness(solution);
                const statusConfig = getStatusConfig(solution.status);
                return (
                  <Card key={solution.id} className="border-white/10 bg-white/5 backdrop-blur">
                    <CardHeader>
                      <div className="flex flex-wrap items-center justify-between gap-3">
                        <div>
                          <CardTitle className="text-base">{solution.name}</CardTitle>
                          <CardDescription className="mt-1 text-xs">
                            {solution.solutionNo} · 版本 {solution.version}
                          </CardDescription>
                        </div>
                        <Badge className={statusConfig.className}>{statusConfig.label}</Badge>
                      </div>
                    </CardHeader>
                    <CardContent className="space-y-4">
                      <p className="text-sm text-slate-300">{solution.requirementSummary}</p>

                      <div>
                        <div className="mb-1 flex items-center justify-between text-xs text-slate-400">
                          <span>材料完整度</span>
                          <span>{completeness}%</span>
                        </div>
                        <Progress value={completeness} className="h-2" />
                      </div>

                      <Textarea
                        rows={3}
                        placeholder="填写评审意见（可选）"
                        value={reviewComments[solution.id] || ""}
                        onChange={(event) =>
                          setReviewComments((previous) => ({
                            ...previous,
                            [solution.id]: event.target.value,
                          }))
                        }
                      />

                      <div className="flex flex-wrap items-center gap-2">
                        <Button
                          onClick={() => handleReviewAction(solution.id, "APPROVED")}
                          disabled={reviewActionLoadingId === solution.id}
                        >
                          <CheckCircle2 className="mr-2 h-4 w-4" />
                          通过评审
                        </Button>
                        <Button
                          variant="outline"
                          className="border-red-400/40 text-red-100 hover:bg-red-500/10"
                          onClick={() => handleReviewAction(solution.id, "REJECTED")}
                          disabled={reviewActionLoadingId === solution.id}
                        >
                          <XCircle className="mr-2 h-4 w-4" />
                          驳回修改
                        </Button>
                        <Button
                          variant="ghost"
                          onClick={() => {
                            setSelectedSolutionId(String(solution.id));
                            setActiveTab("versions");
                          }}
                        >
                          <GitBranch className="mr-2 h-4 w-4" />
                          查看版本轨迹
                        </Button>
                      </div>
                    </CardContent>
                  </Card>
                );
              })
            )}
          </TabsContent>

          <TabsContent value="versions" className="space-y-4">
            <Card className="border-white/10 bg-white/5 backdrop-blur">
              <CardContent className="pt-6">
                <div className="flex flex-col gap-3 md:flex-row md:items-center md:justify-between">
                  <div>
                    <p className="text-sm font-medium text-slate-100">选择方案查看版本链</p>
                    <p className="text-xs text-slate-400">支持查看历史版本和评审记录</p>
                  </div>
                  <Select
                    value={selectedSolutionId || ""}
                    onValueChange={(value) => setSelectedSolutionId(value)}
                  >
                    <SelectTrigger className="w-full md:w-[320px]">
                      <SelectValue placeholder="请选择方案" />
                    </SelectTrigger>
                    <SelectContent>
                      {solutions.map((solution) => (
                        <SelectItem key={solution.id} value={String(solution.id)}>
                          {solution.name} ({solution.version})
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                </div>
              </CardContent>
            </Card>

            {versionsError && (
              <Alert className="border-red-500/30 bg-red-500/10 text-red-100">
                <AlertTitle>版本加载失败</AlertTitle>
                <AlertDescription>{versionsError}</AlertDescription>
              </Alert>
            )}

            {versionsLoading ? (
              <div className="rounded-xl border border-white/10 bg-white/5 py-12 text-center text-slate-300">
                <RefreshCw className="mx-auto mb-3 h-6 w-6 animate-spin" />
                正在加载版本记录...
              </div>
            ) : (
              <div className="grid gap-4 lg:grid-cols-3">
                <Card className="lg:col-span-1 border-white/10 bg-white/5">
                  <CardHeader>
                    <CardTitle className="text-base">版本时间线</CardTitle>
                    <CardDescription>共 {versions.length} 个版本</CardDescription>
                  </CardHeader>
                  <CardContent className="space-y-2">
                    {versions.length > 0 ? (
                      versions.map((version) => {
                        const isActive = String(version.id) === String(selectedVersionId);
                        const statusConfig = getStatusConfig(version.status);
                        return (
                          <button
                            key={version.id}
                            type="button"
                            onClick={() => setSelectedVersionId(String(version.id))}
                            className={`w-full rounded-lg border p-3 text-left transition-colors ${
                              isActive
                                ? "border-cyan-400/60 bg-cyan-500/10"
                                : "border-white/10 bg-white/5 hover:border-white/20"
                            }`}
                          >
                            <div className="mb-2 flex items-center justify-between gap-2">
                              <p className="text-sm font-medium text-slate-100">{version.version}</p>
                              <Badge className={statusConfig.className}>{statusConfig.label}</Badge>
                            </div>
                            <p className="text-xs text-slate-400">{formatDate(version.updatedAt || version.createdAt)}</p>
                          </button>
                        );
                      })
                    ) : (
                      <p className="py-8 text-center text-sm text-slate-400">当前方案暂无版本记录</p>
                    )}
                  </CardContent>
                </Card>

                <Card className="lg:col-span-2 border-white/10 bg-white/5">
                  <CardHeader>
                    <CardTitle className="text-base">版本详情</CardTitle>
                    <CardDescription>查看方案内容、评审意见与估算信息</CardDescription>
                  </CardHeader>
                  <CardContent>
                    {selectedVersion ? (
                      <div className="space-y-5">
                        <div className="flex flex-wrap items-center justify-between gap-3">
                          <div>
                            <p className="text-lg font-medium text-slate-100">{selectedVersion.name}</p>
                            <p className="text-xs text-slate-400">
                              {selectedVersion.solutionNo} · {selectedVersion.industry}
                            </p>
                          </div>
                          <Badge className={getStatusConfig(selectedVersion.status).className}>
                            {getStatusConfig(selectedVersion.status).label}
                          </Badge>
                        </div>

                        <div className="grid gap-3 md:grid-cols-2">
                          <div className="rounded-lg border border-white/10 bg-slate-900/60 p-3">
                            <p className="text-xs text-slate-400">需求摘要</p>
                            <p className="mt-1 text-sm text-slate-200">{selectedVersion.requirementSummary}</p>
                          </div>
                          <div className="rounded-lg border border-white/10 bg-slate-900/60 p-3">
                            <p className="text-xs text-slate-400">方案概述</p>
                            <p className="mt-1 text-sm text-slate-200">{selectedVersion.solutionOverview}</p>
                          </div>
                          <div className="rounded-lg border border-white/10 bg-slate-900/60 p-3 md:col-span-2">
                            <p className="text-xs text-slate-400">技术规格</p>
                            <pre className="mt-1 whitespace-pre-wrap text-sm text-slate-200">
                              {selectedVersion.technicalSpec}
                            </pre>
                          </div>
                        </div>

                        <div className="grid gap-3 sm:grid-cols-3">
                          <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                            <p className="text-xs text-slate-400">预估成本</p>
                            <p className="mt-1 text-sm text-slate-100">{formatWan(selectedVersion.estimatedCost)} 万</p>
                          </div>
                          <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                            <p className="text-xs text-slate-400">建议报价</p>
                            <p className="mt-1 text-sm text-cyan-200">{formatWan(selectedVersion.suggestedPrice)} 万</p>
                          </div>
                          <div className="rounded-lg border border-white/10 bg-white/5 p-3">
                            <p className="text-xs text-slate-400">更新时间</p>
                            <p className="mt-1 text-sm text-slate-100">{formatDate(selectedVersion.updatedAt || selectedVersion.createdAt)}</p>
                          </div>
                        </div>

                        {selectedVersion.reviewComment && (
                          <Alert className="border-amber-400/30 bg-amber-500/10">
                            <AlertTitle className="text-amber-100">评审意见</AlertTitle>
                            <AlertDescription className="text-amber-100/90">
                              {selectedVersion.reviewComment}
                            </AlertDescription>
                          </Alert>
                        )}
                      </div>
                    ) : (
                      <div className="py-14 text-center text-slate-400">请选择左侧版本查看详情</div>
                    )}
                  </CardContent>
                </Card>
              </div>
            )}
          </TabsContent>
        </Tabs>
      </div>
    </div>
  );
}
