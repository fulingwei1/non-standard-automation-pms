// Uppercase-key configs — match backend enum values used throughout ExceptionManagement
export const statusConfigs = {
  OPEN: { label: "待处理", color: "bg-blue-500" },
  PROCESSING: { label: "处理中", color: "bg-amber-500" },
  RESOLVED: { label: "已解决", color: "bg-emerald-500" },
  CLOSED: { label: "已关闭", color: "bg-slate-500" },
};

export const severityConfigs = {
  LOW: { label: "低", color: "bg-slate-500" },
  MEDIUM: { label: "中", color: "bg-amber-500" },
  HIGH: { label: "高", color: "bg-orange-500" },
  CRITICAL: { label: "严重", color: "bg-red-500" },
};

export const typeConfigs = {
  SCHEDULE: { label: "进度异常", color: "bg-blue-500" },
  QUALITY: { label: "质量异常", color: "bg-red-500" },
  COST: { label: "成本异常", color: "bg-amber-500" },
  RESOURCE: { label: "资源异常", color: "bg-purple-500" },
  MATERIAL: { label: "物料异常", color: "bg-cyan-500" },
  EQUIPMENT: { label: "设备异常", color: "bg-violet-500" },
  OTHER: { label: "其他", color: "bg-slate-500" },
};

export const DEFAULT_NEW_EXCEPTION = {
  project_id: null,
  machine_id: null,
  event_type: "OTHER",
  severity: "MEDIUM",
  event_title: "",
  event_description: "",
  impact_scope: "LOCAL",
  schedule_impact: 0,
  cost_impact: 0,
  responsible_user_id: null,
  due_date: "",
};

export const DEFAULT_HANDLE_DATA = {
  action_type: "HANDLE",
  action_description: "",
  next_status: "PROCESSING",
};
