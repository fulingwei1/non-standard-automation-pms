// Status configs for shortage reports (API keys)
export const statusConfigs = {
  REPORTED: { label: "已上报", color: "bg-blue-500", icon: "Clock" },
  CONFIRMED: { label: "已确认", color: "bg-amber-500", icon: "CheckCircle2" },
  HANDLING: { label: "处理中", color: "bg-purple-500", icon: "RefreshCw" },
  RESOLVED: { label: "已解决", color: "bg-emerald-500", icon: "CheckCircle2" },
};

// Urgent level configs for shortage reports (API keys)
export const urgentLevelConfigs = {
  NORMAL: { label: "普通", color: "text-slate-400" },
  URGENT: { label: "紧急", color: "text-amber-400" },
  CRITICAL: { label: "特急", color: "text-red-400" },
};

// Legacy status configs (kept for backward-compatibility with older data shapes)
export const shortageStatusConfigs = {
  open: { label: "待处理", color: "bg-red-500" },
  purchasing: { label: "采购中", color: "bg-amber-500" },
  resolved: { label: "已解决", color: "bg-emerald-500" },
};

// Legacy priority configs (kept for backward-compatibility with older data shapes)
export const priorityConfigs = {
  low: { label: "低", color: "bg-slate-500" },
  medium: { label: "中", color: "bg-amber-500" },
  high: { label: "高", color: "bg-orange-500" },
  critical: { label: "紧急", color: "bg-red-500" },
};
