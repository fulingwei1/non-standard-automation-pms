// Stage configuration — front-end friendly keys and DB enum values (S1-S9)
export const stageConfig = {
  // Front-end friendly names
  solution: {
    label: "方案设计",
    color: "bg-violet-500",
    textColor: "text-violet-400",
    order: 1,
  },
  design: {
    label: "结构设计",
    color: "bg-blue-500",
    textColor: "text-blue-400",
    order: 2,
  },
  procurement: {
    label: "采购备料",
    color: "bg-cyan-500",
    textColor: "text-cyan-400",
    order: 3,
  },
  assembly: {
    label: "装配调试",
    color: "bg-amber-500",
    textColor: "text-amber-400",
    order: 4,
  },
  fat: {
    label: "出厂验收",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
    order: 5,
  },
  shipping: {
    label: "包装发运",
    color: "bg-purple-500",
    textColor: "text-purple-400",
    order: 6,
  },
  sat: {
    label: "现场调试",
    color: "bg-pink-500",
    textColor: "text-pink-400",
    order: 7,
  },
  warranty: {
    label: "质保结项",
    color: "bg-slate-500",
    textColor: "text-slate-400",
    order: 8,
  },
  // DB enum values (S1-S9)
  S1: { label: "需求进入", color: "bg-violet-500", textColor: "text-violet-400", order: 1 },
  S2: { label: "方案设计", color: "bg-blue-500", textColor: "text-blue-400", order: 2 },
  S3: { label: "采购备料", color: "bg-cyan-500", textColor: "text-cyan-400", order: 3 },
  S4: { label: "加工制造", color: "bg-teal-500", textColor: "text-teal-400", order: 4 },
  S5: { label: "装配调试", color: "bg-amber-500", textColor: "text-amber-400", order: 5 },
  S6: { label: "出厂验收", color: "bg-emerald-500", textColor: "text-emerald-400", order: 6 },
  S7: { label: "包装发运", color: "bg-purple-500", textColor: "text-purple-400", order: 7 },
  S8: { label: "现场安装", color: "bg-pink-500", textColor: "text-pink-400", order: 8 },
  S9: { label: "质保结项", color: "bg-slate-500", textColor: "text-slate-400", order: 9 },
};

export const defaultStageConf = {
  label: "未知阶段",
  color: "bg-slate-500",
  textColor: "text-slate-400",
  order: 0,
};

// Health configuration — front-end friendly keys and DB enum values (H1-H4)
export const healthConfig = {
  // Front-end friendly names
  good: { label: "正常", color: "bg-emerald-500", textColor: "text-emerald-400" },
  warning: { label: "有风险", color: "bg-amber-500", textColor: "text-amber-400" },
  critical: { label: "阻塞", color: "bg-red-500", textColor: "text-red-400" },
  // DB enum values (H1-H4)
  H1: { label: "正常", color: "bg-emerald-500", textColor: "text-emerald-400" },
  H2: { label: "有风险", color: "bg-amber-500", textColor: "text-amber-400" },
  H3: { label: "阻塞", color: "bg-red-500", textColor: "text-red-400" },
  H4: { label: "已完结", color: "bg-slate-500", textColor: "text-slate-400" },
};

export const defaultHealthConf = {
  label: "未知",
  color: "bg-slate-500",
  textColor: "text-slate-400",
};
