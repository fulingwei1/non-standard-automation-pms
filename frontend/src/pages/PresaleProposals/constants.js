export const STATUS_CONFIG = {
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
