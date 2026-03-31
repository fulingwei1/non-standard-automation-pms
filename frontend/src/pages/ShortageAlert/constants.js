/**
 * ShortageAlert — config maps
 * Keys match the API values used by shortageAlertApi.
 */

export const statusConfigs = {
  PENDING: { label: "待处理", color: "bg-blue-500" },
  ACKNOWLEDGED: { label: "已确认", color: "bg-amber-500" },
  PROCESSING: { label: "处理中", color: "bg-purple-500" },
  RESOLVED: { label: "已解决", color: "bg-emerald-500" },
  CLOSED: { label: "已关闭", color: "bg-slate-500" },
};

export const levelConfigs = {
  LEVEL1: { label: "一级预警", color: "bg-red-500", urgency: "紧急" },
  LEVEL2: { label: "二级预警", color: "bg-orange-500", urgency: "重要" },
  LEVEL3: { label: "三级预警", color: "bg-amber-500", urgency: "一般" },
  LEVEL4: { label: "四级预警", color: "bg-blue-500", urgency: "提醒" },
};

export const TERMINAL_STATUSES = new Set(["RESOLVED", "CLOSED"]);

export const DEFAULT_HANDLE_DATA = {
  solution: "",
  status: "PROCESSING",
  remark: "",
};
