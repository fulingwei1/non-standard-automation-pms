/**
 * ProductionExceptionList — shared config maps
 * Keys must match the values returned by the backend API.
 */

export const statusConfigs = {
  REPORTED: { label: "已上报", color: "bg-blue-500" },
  IN_PROGRESS: { label: "处理中", color: "bg-amber-500" },
  RESOLVED: { label: "已解决", color: "bg-emerald-500" },
  CLOSED: { label: "已关闭", color: "bg-slate-500" },
};

export const typeConfigs = {
  MATERIAL: { label: "物料异常", color: "bg-amber-500" },
  EQUIPMENT: { label: "设备异常", color: "bg-red-500" },
  QUALITY: { label: "质量异常", color: "bg-purple-500" },
  OTHER: { label: "其他", color: "bg-slate-500" },
};

export const levelConfigs = {
  CRITICAL: { label: "严重", color: "bg-red-500" },
  MAJOR: { label: "重要", color: "bg-orange-500" },
  MINOR: { label: "一般", color: "bg-amber-500" },
  LOW: { label: "轻微", color: "bg-blue-500" },
};

export const DEFAULT_NEW_EXCEPTION = {
  exception_type: "MATERIAL",
  exception_level: "MINOR",
  title: "",
  description: "",
  work_order_id: null,
  project_id: null,
  workshop_id: null,
  equipment_id: null,
  impact_hours: 0,
  impact_cost: 0,
  remark: "",
};

export const DEFAULT_HANDLE_DATA = {
  handle_plan: "",
  handle_result: "",
};
