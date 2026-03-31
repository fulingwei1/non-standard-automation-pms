export const STATUS_CONFIG = {
  PENDING: {
    label: "待受理",
    badgeClass: "bg-slate-500/20 text-slate-200 border border-slate-500/40",
    dotClass: "bg-slate-400",
  },
  ACCEPTED: {
    label: "已接单",
    badgeClass: "bg-blue-500/20 text-blue-300 border border-blue-500/40",
    dotClass: "bg-blue-400",
  },
  IN_PROGRESS: {
    label: "处理中",
    badgeClass: "bg-amber-500/20 text-amber-300 border border-amber-500/40",
    dotClass: "bg-amber-400",
  },
  COMPLETED: {
    label: "已完成",
    badgeClass: "bg-emerald-500/20 text-emerald-300 border border-emerald-500/40",
    dotClass: "bg-emerald-400",
  },
};

export const BOARD_STATUS_ORDER = ["PENDING", "ACCEPTED", "IN_PROGRESS", "COMPLETED"];

export const PRIORITY_CONFIG = {
  LOW: {
    label: "低",
    badgeClass: "bg-slate-500/20 text-slate-200 border border-slate-500/40",
    weight: 1,
  },
  NORMAL: {
    label: "普通",
    badgeClass: "bg-blue-500/20 text-blue-300 border border-blue-500/40",
    weight: 2,
  },
  HIGH: {
    label: "高",
    badgeClass: "bg-amber-500/20 text-amber-300 border border-amber-500/40",
    weight: 3,
  },
  URGENT: {
    label: "紧急",
    badgeClass: "bg-red-500/20 text-red-300 border border-red-500/40",
    weight: 4,
  },
};

export const TYPE_LABELS = {
  SOLUTION_DESIGN: "方案设计",
  SOLUTION_REVIEW: "方案评审",
  TECHNICAL_EXCHANGE: "技术交流",
  COST_ESTIMATE: "成本核算",
  TENDER_SUPPORT: "投标支持",
  REQUIREMENT_RESEARCH: "需求调研",
  FEASIBILITY_ASSESSMENT: "可行性评估",
};
