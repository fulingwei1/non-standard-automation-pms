import { useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  CheckCircle2,
  Eye,
  FileText,
  Layers,
  Loader2,
  Search,
  Sparkles,
  Star,
  Wand2,
} from "lucide-react";

import { PageHeader } from "../components/layout";
import {
  Badge,
  Button,
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
  Dialog,
  DialogBody,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  Input,
  toast,
} from "../components/ui";
import { fadeIn, staggerContainer } from "../lib/animations";
import { cn, formatDate } from "../lib/utils";
import { presaleApi } from "../services/api";

const MOCK_TEMPLATES = [
  {
    id: "tmpl-discovery-001",
    name: "工业自动化需求调研模板",
    category: "需求调研",
    description:
      "用于制造业客户首次交流，覆盖业务痛点、产线节拍、关键约束与预算窗口。",
    tags: ["首访", "痛点梳理", "需求访谈"],
    scenarios: ["首次商机沟通", "售前立项会", "客户需求澄清"],
    outline: [
      {
        title: "业务背景与目标",
        bullets: ["客户现状", "核心改造目标", "期望收益"],
      },
      {
        title: "技术与现场约束",
        bullets: ["设备接口", "空间条件", "交付周期"],
      },
      {
        title: "风险与下一步",
        bullets: ["高风险项", "关键决策点", "后续行动计划"],
      },
    ],
    deliverables: ["需求调研报告", "问题清单", "优先级矩阵"],
    rating: 4.7,
    ratingCount: 28,
    applyCount: 92,
    owner: "解决方案部",
    updatedAt: "2026-02-20",
  },
  {
    id: "tmpl-solution-002",
    name: "标准产线方案设计模板",
    category: "方案设计",
    description:
      "适用于中大型产线升级项目，包含系统架构、实施边界、交付范围与验收策略。",
    tags: ["系统架构", "交付边界", "实施方案"],
    scenarios: ["方案设计阶段", "技术评审前准备"],
    outline: [
      { title: "总体架构", bullets: ["系统拓扑", "软硬件清单", "集成策略"] },
      { title: "实施计划", bullets: ["里程碑", "资源配置", "风险应对"] },
      { title: "价值测算", bullets: ["ROI模型", "成本收益", "回收周期"] },
    ],
    deliverables: ["方案说明书", "实施计划", "投资回报测算表"],
    rating: 4.5,
    ratingCount: 41,
    applyCount: 134,
    owner: "售前架构组",
    updatedAt: "2026-02-16",
  },
  {
    id: "tmpl-bid-003",
    name: "投标应答与条款映射模板",
    category: "投标支持",
    description:
      "聚焦招标文件快速拆解，支持技术应答、偏离表、风险条款识别与应对建议。",
    tags: ["技术应答", "偏离项", "条款映射"],
    scenarios: ["投标文件编制", "技术偏离评审"],
    outline: [
      { title: "招标要求解析", bullets: ["关键条款", "合规性检查", "评分点映射"] },
      { title: "应答矩阵", bullets: ["逐条应答", "证明材料", "责任人"] },
      { title: "风险闭环", bullets: ["风险等级", "规避动作", "审批意见"] },
    ],
    deliverables: ["应答矩阵", "偏离说明", "风险清单"],
    rating: 4.8,
    ratingCount: 19,
    applyCount: 67,
    owner: "投标管理组",
    updatedAt: "2026-02-10",
  },
  {
    id: "tmpl-cost-004",
    name: "售前成本估算模板",
    category: "成本估算",
    description:
      "通过标准BOM、工时与服务项结构快速估算项目成本，支持多版本报价场景。",
    tags: ["BOM", "工时估算", "报价支持"],
    scenarios: ["售前报价", "方案比选", "毛利预测"],
    outline: [
      { title: "成本分层", bullets: ["材料", "人工", "外协与运维"] },
      { title: "参数假设", bullets: ["数量假设", "汇率假设", "折扣规则"] },
      { title: "结果输出", bullets: ["成本汇总", "毛利测算", "敏感度分析"] },
    ],
    deliverables: ["成本测算表", "毛利分析", "假设说明"],
    rating: 4.3,
    ratingCount: 36,
    applyCount: 116,
    owner: "商务成本组",
    updatedAt: "2026-01-28",
  },
  {
    id: "tmpl-demo-005",
    name: "客户答辩演示模板",
    category: "答辩演示",
    description:
      "支持客户高层汇报与技术答辩，强调价值主张、成功案例与落地保障机制。",
    tags: ["客户答辩", "价值呈现", "案例沉淀"],
    scenarios: ["方案答辩会", "高层汇报", "竞争性演示"],
    outline: [
      { title: "价值主张", bullets: ["业务价值", "成本价值", "组织价值"] },
      { title: "能力证明", bullets: ["案例数据", "交付资质", "团队能力"] },
      { title: "落地保障", bullets: ["治理机制", "里程碑控制", "服务承诺"] },
    ],
    deliverables: ["演示PPT", "答辩话术", "Q&A清单"],
    rating: 4.6,
    ratingCount: 22,
    applyCount: 74,
    owner: "行业方案组",
    updatedAt: "2026-02-14",
  },
];

const CATEGORY_STYLE_MAP = {
  需求调研: "bg-blue-500/10 text-blue-300 border-blue-500/30",
  方案设计: "bg-violet-500/10 text-violet-300 border-violet-500/30",
  投标支持: "bg-emerald-500/10 text-emerald-300 border-emerald-500/30",
  成本估算: "bg-amber-500/10 text-amber-300 border-amber-500/30",
  答辩演示: "bg-cyan-500/10 text-cyan-300 border-cyan-500/30",
};

function normalizeStringArray(value) {
  if (!value) {
    return [];
  }

  if (Array.isArray(value)) {
    return value
      .map((item) => (typeof item === "string" ? item.trim() : ""))
      .filter(Boolean);
  }

  if (typeof value === "string") {
    return value
      .split(/[,\n，]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }

  return [];
}

function normalizeOutline(value) {
  if (!value) {
    return [];
  }

  let parsedValue = value;
  if (typeof parsedValue === "string") {
    try {
      parsedValue = JSON.parse(parsedValue);
    } catch (_error) {
      parsedValue = [];
    }
  }

  if (!Array.isArray(parsedValue)) {
    return [];
  }

  return parsedValue.map((section, index) => {
    if (typeof section === "string") {
      return { title: section, bullets: [] };
    }
    const title =
      section?.title ||
      section?.name ||
      section?.section_name ||
      `章节 ${index + 1}`;
    const bullets = normalizeStringArray(
      section?.bullets || section?.items || section?.points || section?.content,
    );
    return { title, bullets };
  });
}

function normalizeTemplate(item, index = 0) {
  const ratingRaw =
    item?.avg_rating ?? item?.rating_score ?? item?.rating ?? item?.score ?? 4.5;
  const rating = Number.isFinite(Number(ratingRaw))
    ? Math.min(5, Math.max(0, Number(ratingRaw)))
    : 4.5;

  const ratingCountRaw = item?.rating_count ?? item?.ratingCount ?? 0;
  const ratingCount = Number.isFinite(Number(ratingCountRaw))
    ? Math.max(0, Number(ratingCountRaw))
    : 0;

  const applyCountRaw =
    item?.apply_count ?? item?.usage_count ?? item?.used_count ?? 0;
  const applyCount = Number.isFinite(Number(applyCountRaw))
    ? Math.max(0, Number(applyCountRaw))
    : 0;

  const outline = normalizeOutline(
    item?.outline ||
      item?.template_outline ||
      item?.preview_outline ||
      item?.sections,
  );

  return {
    id: item?.id || item?.template_id || `template-${index + 1}`,
    name: item?.template_name || item?.name || `售前模板 ${index + 1}`,
    category: item?.category || item?.template_category || item?.type || "通用",
    description:
      item?.description ||
      item?.summary ||
      "该模板覆盖标准售前活动，可用于快速复用与协同交付。",
    tags: normalizeStringArray(item?.tags || item?.keywords),
    scenarios: normalizeStringArray(
      item?.scenarios || item?.applicable_scenarios || item?.applicable_scene,
    ),
    outline,
    deliverables: normalizeStringArray(
      item?.deliverables || item?.outputs || item?.output_items,
    ),
    rating,
    ratingCount,
    applyCount,
    owner:
      item?.owner_name ||
      item?.owner ||
      item?.created_by_name ||
      item?.created_by ||
      "售前团队",
    updatedAt:
      item?.updated_at ||
      item?.updatedAt ||
      item?.last_modified_at ||
      item?.created_at ||
      new Date().toISOString(),
  };
}

function RatingStars({ value }) {
  return (
    <div className="flex items-center gap-1">
      {[1, 2, 3, 4, 5].map((star) => (
        <Star
          key={star}
          className={cn(
            "h-4 w-4",
            star <= Math.round(value)
              ? "text-amber-400 fill-amber-400"
              : "text-slate-600",
          )}
        />
      ))}
    </div>
  );
}

export default function PresaleTemplates() {
  const [loading, setLoading] = useState(true);
  const [usingMockData, setUsingMockData] = useState(false);
  const [templates, setTemplates] = useState([]);
  const [keyword, setKeyword] = useState("");
  const [selectedCategory, setSelectedCategory] = useState("all");
  const [previewTemplate, setPreviewTemplate] = useState(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [applyingTemplateId, setApplyingTemplateId] = useState(null);
  const [ratingTemplateId, setRatingTemplateId] = useState(null);
  const [myRatings, setMyRatings] = useState({});

  useEffect(() => {
    const loadTemplates = async () => {
      try {
        setLoading(true);
        const response = await presaleApi.templates.list({ page: 1, page_size: 100 });
        const payload = response?.data;
        const items =
          payload?.items ||
          payload?.data?.items ||
          payload?.data ||
          response?.items ||
          response?.data ||
          [];

        if (Array.isArray(items) && items.length > 0) {
          setTemplates(items.map((item, index) => normalizeTemplate(item, index)));
          setUsingMockData(false);
          return;
        }

        setTemplates(MOCK_TEMPLATES);
        setUsingMockData(true);
      } catch (_error) {
        setTemplates(MOCK_TEMPLATES);
        setUsingMockData(true);
      } finally {
        setLoading(false);
      }
    };

    loadTemplates();
  }, []);

  const categories = useMemo(() => {
    const counter = (templates || []).reduce((acc, template) => {
      const key = template.category || "通用";
      acc[key] = (acc[key] || 0) + 1;
      return acc;
    }, {});

    const dynamicCategories = Object.entries(counter).map(([category, count]) => ({
      key: category,
      label: category,
      count,
    }));

    return [
      { key: "all", label: "全部模板", count: templates.length },
      ...dynamicCategories,
    ];
  }, [templates]);

  const filteredTemplates = useMemo(() => {
    const lowerKeyword = keyword.trim().toLowerCase();

    return (templates || []).filter((template) => {
      const matchCategory =
        selectedCategory === "all" || template.category === selectedCategory;

      if (!matchCategory) {
        return false;
      }

      if (!lowerKeyword) {
        return true;
      }

      const searchableText = [
        template.name,
        template.description,
        ...(template.tags || []),
        ...(template.scenarios || []),
      ]
        .join(" ")
        .toLowerCase();

      return searchableText.includes(lowerKeyword);
    });
  }, [keyword, selectedCategory, templates]);

  const stats = useMemo(() => {
    const totalApplyCount = (templates || []).reduce(
      (sum, template) => sum + (template.applyCount || 0),
      0,
    );
    const averageRating =
      templates.length > 0
        ? templates.reduce((sum, template) => sum + (template.rating || 0), 0) /
          templates.length
        : 0;

    return {
      total: templates.length,
      categories: Math.max(0, categories.length - 1),
      totalApplyCount,
      averageRating,
    };
  }, [categories.length, templates]);

  const applyTemplate = async (template) => {
    if (!template) {
      return;
    }

    setApplyingTemplateId(template.id);

    const nextApplyCount = (template.applyCount || 0) + 1;
    setTemplates((prev) =>
      (prev || []).map((item) =>
        item.id === template.id ? { ...item, applyCount: nextApplyCount } : item,
      ),
    );

    try {
      await presaleApi.templates.update(template.id, {
        apply_count: nextApplyCount,
      });
      toast.success(`模板「${template.name}」已应用`);
    } catch (_error) {
      toast.warning(`模板「${template.name}」已本地应用，后台同步稍后重试`);
    } finally {
      setApplyingTemplateId(null);
    }
  };

  const rateTemplate = async (template, score) => {
    if (!template || !score) {
      return;
    }

    setRatingTemplateId(template.id);
    setMyRatings((prev) => ({ ...prev, [template.id]: score }));

    const nextRatingCount = (template.ratingCount || 0) + 1;
    const nextRating =
      ((template.rating || 0) * (template.ratingCount || 0) + score) /
      nextRatingCount;

    setTemplates((prev) =>
      (prev || []).map((item) =>
        item.id === template.id
          ? { ...item, rating: nextRating, ratingCount: nextRatingCount }
          : item,
      ),
    );

    try {
      await presaleApi.templates.update(template.id, { rating: score });
      toast.success(`已提交 ${score} 星评分`);
    } catch (_error) {
      toast.warning("评分已本地保存，后台同步稍后重试");
    } finally {
      setRatingTemplateId(null);
    }
  };

  const openPreview = async (template) => {
    if (!template) {
      return;
    }

    setPreviewTemplate(template);
    setPreviewLoading(true);

    try {
      const response = await presaleApi.templates.get(template.id);
      const detailData = response?.data?.data || response?.data || {};
      const mergedTemplate = normalizeTemplate(
        { ...template, ...detailData },
        0,
      );
      setPreviewTemplate(mergedTemplate);
    } catch (_error) {
      setPreviewTemplate(template);
    } finally {
      setPreviewLoading(false);
    }
  };

  return (
    <motion.div
      className="space-y-6"
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <PageHeader
        title="售前模板库"
        description="统一管理模板分类、快速预览、模板应用和团队评分反馈。"
      />

      {usingMockData && (
        <motion.div variants={fadeIn}>
          <div className="rounded-xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-sm text-amber-200">
            当前展示内置模板数据，接口连通后会自动切换为真实模板库。
          </div>
        </motion.div>
      )}

      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 gap-4 md:grid-cols-2 xl:grid-cols-4"
      >
        <Card className="bg-surface-1/50">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">模板总数</p>
                <p className="mt-1 text-2xl font-semibold text-white">
                  {stats.total}
                </p>
              </div>
              <Layers className="h-6 w-6 text-blue-300" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-1/50">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">分类覆盖</p>
                <p className="mt-1 text-2xl font-semibold text-white">
                  {stats.categories}
                </p>
              </div>
              <Sparkles className="h-6 w-6 text-violet-300" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-1/50">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">累计应用</p>
                <p className="mt-1 text-2xl font-semibold text-white">
                  {stats.totalApplyCount}
                </p>
              </div>
              <CheckCircle2 className="h-6 w-6 text-emerald-300" />
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-1/50">
          <CardContent className="p-5">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">平均评分</p>
                <p className="mt-1 text-2xl font-semibold text-white">
                  {stats.averageRating.toFixed(1)}
                </p>
              </div>
              <Star className="h-6 w-6 text-amber-300" />
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardContent className="space-y-4 p-5">
            <div className="flex flex-col gap-3 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex flex-wrap gap-2">
                {(categories || []).map((category) => (
                  <Button
                    key={category.key}
                    size="sm"
                    variant={
                      selectedCategory === category.key ? "default" : "outline"
                    }
                    onClick={() => setSelectedCategory(category.key)}
                  >
                    {category.label}
                    <span className="ml-1 text-xs text-slate-300">
                      {category.count}
                    </span>
                  </Button>
                ))}
              </div>

              <div className="w-full lg:w-80">
                <Input
                  value={keyword}
                  onChange={(event) => setKeyword(event.target.value)}
                  placeholder="搜索模板名称、标签或应用场景"
                  icon={Search}
                />
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 gap-4 xl:grid-cols-2"
      >
        {loading ? (
          <Card className="xl:col-span-2 bg-surface-1/50">
            <CardContent className="flex min-h-[220px] items-center justify-center">
              <div className="flex items-center gap-2 text-slate-300">
                <Loader2 className="h-5 w-5 animate-spin" />
                <span>正在加载模板库...</span>
              </div>
            </CardContent>
          </Card>
        ) : filteredTemplates.length === 0 ? (
          <Card className="xl:col-span-2 bg-surface-1/50">
            <CardContent className="flex min-h-[220px] items-center justify-center text-slate-400">
              未找到符合条件的模板，请调整分类或关键词。
            </CardContent>
          </Card>
        ) : (
          filteredTemplates.map((template) => (
            <Card key={template.id} className="bg-surface-1/50">
              <CardHeader className="space-y-3 pb-0">
                <div className="flex items-start justify-between gap-3">
                  <div className="space-y-2">
                    <Badge
                      className={cn(
                        "border",
                        CATEGORY_STYLE_MAP[template.category] ||
                          "bg-slate-500/10 text-slate-300 border-slate-500/30",
                      )}
                    >
                      {template.category}
                    </Badge>
                    <CardTitle className="text-base text-white">
                      {template.name}
                    </CardTitle>
                  </div>
                  <Badge variant="outline" className="shrink-0">
                    {template.owner}
                  </Badge>
                </div>
                <CardDescription className="min-h-[40px] text-slate-400">
                  {template.description}
                </CardDescription>
              </CardHeader>

              <CardContent className="space-y-4">
                <div className="flex flex-wrap gap-2">
                  {(template.tags || []).length > 0 ? (
                    (template.tags || []).map((tag) => (
                      <span
                        key={tag}
                        className="rounded-lg border border-white/10 bg-white/5 px-2 py-1 text-xs text-slate-300"
                      >
                        {tag}
                      </span>
                    ))
                  ) : (
                    <span className="text-xs text-slate-500">暂无标签</span>
                  )}
                </div>

                <div className="grid grid-cols-1 gap-2 text-sm text-slate-300 md:grid-cols-3">
                  <div className="flex items-center gap-2">
                    <Star className="h-4 w-4 text-amber-400" />
                    <span>
                      {template.rating.toFixed(1)} ({template.ratingCount}人)
                    </span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Wand2 className="h-4 w-4 text-emerald-400" />
                    <span>{template.applyCount} 次应用</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="h-4 w-4 text-blue-400" />
                    <span>{formatDate(template.updatedAt)}</span>
                  </div>
                </div>

                <div className="flex items-center gap-2">
                  <RatingStars value={template.rating} />
                  <span className="text-xs text-slate-400">团队评分</span>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <Button
                    size="sm"
                    variant="outline"
                    onClick={() => openPreview(template)}
                  >
                    <Eye className="h-4 w-4" />
                    模板预览
                  </Button>
                  <Button
                    size="sm"
                    variant="success"
                    loading={applyingTemplateId === template.id}
                    onClick={() => applyTemplate(template)}
                  >
                    <Wand2 className="h-4 w-4" />
                    应用模板
                  </Button>
                </div>

                <div className="rounded-xl border border-white/10 bg-white/5 p-3">
                  <p className="mb-2 text-xs text-slate-400">请为模板评分</p>
                  <div className="flex items-center gap-1">
                    {[1, 2, 3, 4, 5].map((score) => (
                      <button
                        key={`${template.id}-score-${score}`}
                        type="button"
                        disabled={ratingTemplateId === template.id}
                        className="rounded p-1 transition hover:bg-white/10 disabled:opacity-50"
                        onClick={() => rateTemplate(template, score)}
                      >
                        <Star
                          className={cn(
                            "h-4 w-4",
                            score <= (myRatings[template.id] || 0)
                              ? "fill-amber-400 text-amber-400"
                              : "text-slate-600 hover:text-amber-300",
                          )}
                        />
                      </button>
                    ))}
                    <span className="ml-2 text-xs text-slate-400">
                      {myRatings[template.id]
                        ? `你已评分 ${myRatings[template.id]} 星`
                        : "点击星级提交评分"}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </motion.div>

      <Dialog
        open={Boolean(previewTemplate)}
        onOpenChange={(open) => {
          if (!open) {
            setPreviewTemplate(null);
          }
        }}
      >
        <DialogContent className="max-w-3xl">
          <DialogHeader>
            <DialogTitle>{previewTemplate?.name || "模板预览"}</DialogTitle>
            <DialogDescription>
              查看模板结构与交付内容，确认后可直接应用到当前售前任务。
            </DialogDescription>
          </DialogHeader>

          <DialogBody className="space-y-6">
            {previewLoading ? (
              <div className="flex min-h-[220px] items-center justify-center text-slate-300">
                <Loader2 className="mr-2 h-5 w-5 animate-spin" />
                正在加载模板详情...
              </div>
            ) : (
              <>
                <div className="flex flex-wrap items-center gap-2">
                  <Badge
                    className={cn(
                      "border",
                      CATEGORY_STYLE_MAP[previewTemplate?.category] ||
                        "bg-slate-500/10 text-slate-300 border-slate-500/30",
                    )}
                  >
                    {previewTemplate?.category || "通用模板"}
                  </Badge>
                  <Badge variant="outline">
                    <FileText className="mr-1 h-3 w-3" />
                    应用 {previewTemplate?.applyCount || 0} 次
                  </Badge>
                  <Badge variant="outline">
                    <Star className="mr-1 h-3 w-3 text-amber-400" />
                    {previewTemplate?.rating?.toFixed(1) || "0.0"}
                  </Badge>
                </div>

                <div className="rounded-xl border border-white/10 bg-white/5 p-4">
                  <p className="text-sm text-slate-200">
                    {previewTemplate?.description}
                  </p>
                </div>

                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-white">适用场景</h4>
                  <div className="flex flex-wrap gap-2">
                    {(previewTemplate?.scenarios || []).length > 0 ? (
                      (previewTemplate?.scenarios || []).map((scenario) => (
                        <span
                          key={scenario}
                          className="rounded-lg border border-blue-500/30 bg-blue-500/10 px-2 py-1 text-xs text-blue-200"
                        >
                          {scenario}
                        </span>
                      ))
                    ) : (
                      <span className="text-xs text-slate-500">
                        暂无适用场景描述
                      </span>
                    )}
                  </div>
                </div>

                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-white">模板大纲</h4>
                  {(previewTemplate?.outline || []).length > 0 ? (
                    <div className="space-y-3">
                      {(previewTemplate?.outline || []).map((section, index) => (
                        <div
                          key={`${section.title}-${index}`}
                          className="rounded-xl border border-white/10 bg-white/5 p-3"
                        >
                          <p className="text-sm font-medium text-white">
                            {index + 1}. {section.title}
                          </p>
                          {(section.bullets || []).length > 0 && (
                            <ul className="mt-2 space-y-1 text-xs text-slate-300">
                              {(section.bullets || []).map((bullet) => (
                                <li key={bullet}>- {bullet}</li>
                              ))}
                            </ul>
                          )}
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-xs text-slate-500">
                      暂无模板大纲数据
                    </div>
                  )}
                </div>

                <div className="space-y-3">
                  <h4 className="text-sm font-medium text-white">交付物清单</h4>
                  {(previewTemplate?.deliverables || []).length > 0 ? (
                    <ul className="space-y-1 text-sm text-slate-300">
                      {(previewTemplate?.deliverables || []).map((item) => (
                        <li key={item}>- {item}</li>
                      ))}
                    </ul>
                  ) : (
                    <div className="rounded-xl border border-white/10 bg-white/5 p-3 text-xs text-slate-500">
                      暂无交付物定义
                    </div>
                  )}
                </div>
              </>
            )}
          </DialogBody>

          <DialogFooter>
            <Button variant="outline" onClick={() => setPreviewTemplate(null)}>
              关闭
            </Button>
            <Button
              variant="success"
              loading={applyingTemplateId === previewTemplate?.id}
              onClick={async () => {
                await applyTemplate(previewTemplate);
                setPreviewTemplate(null);
              }}
            >
              立即应用模板
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
