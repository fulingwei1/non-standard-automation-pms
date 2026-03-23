/**
 * 售前方案管理常量配置
 */

export const STATUS_CONFIG = {
  DRAFT: { label: "草稿", className: "bg-slate-500/20 text-slate-200 border-slate-400/30" },
  IN_PROGRESS: { label: "编写中", className: "bg-blue-500/20 text-blue-200 border-blue-400/30" },
  REVIEWING: { label: "评审中", className: "bg-amber-500/20 text-amber-200 border-amber-400/30" },
  APPROVED: { label: "已通过", className: "bg-emerald-500/20 text-emerald-200 border-emerald-400/30" },
  REJECTED: { label: "已驳回", className: "bg-red-500/20 text-red-200 border-red-400/30" },
};

export const TYPE_OPTIONS = [
  { value: "CUSTOM", label: "定制化方案" },
  { value: "STANDARD", label: "标准方案" },
  { value: "UPGRADE", label: "升级改造" },
  { value: "INTEGRATION", label: "系统集成" },
];

export const INDUSTRY_OPTIONS = ["新能源", "3C电子", "汽车零部件", "医疗器械", "半导体", "通用制造"];

export const TEST_TYPE_OPTIONS = [
  { value: "ICT", label: "ICT 测试" },
  { value: "FCT", label: "FCT 测试" },
  { value: "EOL", label: "EOL 测试" },
  { value: "VISION", label: "视觉检测" },
  { value: "ASSEMBLY", label: "组装线" },
];

export const AI_TEMPLATE_SUGGESTIONS = [
  { title: "快交付方案", description: "优先复用成熟模块，适合交期紧张项目", days: "4-6 周" },
  { title: "平衡成本方案", description: "在性能与成本间取得平衡，适合大多数量产项目", days: "6-8 周" },
  { title: "高性能方案", description: "强调高精度与扩展性，适合技术标竞争项目", days: "8-10 周" },
];

// 默认生成器表单值
export const DEFAULT_GENERATOR_FORM = {
  name: "",
  solutionType: "CUSTOM",
  industry: "新能源",
  testType: "FCT",
  requirementSummary: "",
  estimatedCost: "",
  suggestedPrice: "",
  estimatedHours: "",
  estimatedDuration: "",
};

// 工具函数
export function normalizeSolutionStatus(status, reviewStatus) {
  const currentStatus = String(status || "").toUpperCase();
  const currentReviewStatus = String(reviewStatus || "").toUpperCase();

  if (currentStatus === "APPROVED" || currentStatus === "DELIVERED" || currentStatus === "WON") return "APPROVED";
  if (currentStatus === "REJECTED" || currentStatus === "LOST") return "REJECTED";
  if (currentStatus === "REVIEW" || currentStatus === "REVIEWING" || currentReviewStatus === "PENDING" || currentReviewStatus === "REVIEWING") return "REVIEWING";
  if (currentStatus === "IN_PROGRESS" || currentStatus === "SUBMITTED") return "IN_PROGRESS";
  return "DRAFT";
}

export function extractItems(response) {
  const payload = response?.data ?? response;
  if (Array.isArray(payload)) return payload;
  if (Array.isArray(payload?.items)) return payload.items;
  if (Array.isArray(payload?.data?.items)) return payload.data.items;
  if (Array.isArray(payload?.data)) return payload.data;
  return [];
}

export function normalizeSolution(solution) {
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
    status: normalizeSolutionStatus(solution?.status, solution?.review_status),
    version: solution?.version || "V1.0",
    reviewStatus: solution?.review_status,
    reviewComment: solution?.review_comment,
    createdAt: solution?.created_at,
    updatedAt: solution?.updated_at,
  };
}

export function formatDate(value) {
  if (!value) return "-";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return String(value);
  return date.toLocaleString("zh-CN", { year: "numeric", month: "2-digit", day: "2-digit", hour: "2-digit", minute: "2-digit" });
}

export function formatWan(amount) {
  if (!amount) return "0.0";
  return (Number(amount) / 10000).toFixed(1);
}

export function getStatusConfig(status) {
  return STATUS_CONFIG[status] || { label: status || "未知", className: "bg-slate-500/20 text-slate-200 border-slate-400/30" };
}

export function calculateCompleteness(solution) {
  let score = 20;
  if (solution.requirementSummary && solution.requirementSummary !== "暂无需求摘要") score += 25;
  if (solution.solutionOverview && solution.solutionOverview !== "暂无方案概述") score += 25;
  if (solution.technicalSpec && solution.technicalSpec !== "暂无技术规格") score += 20;
  if (solution.estimatedCost > 0 || solution.suggestedPrice > 0) score += 10;
  return Math.min(score, 100);
}
