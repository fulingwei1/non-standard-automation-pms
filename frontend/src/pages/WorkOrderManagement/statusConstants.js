/**
 * Status and priority configuration maps used by the Work Order Management UI.
 * Keys are uppercase to match backend enum values.
 */
export const statusConfigs = {
  PENDING: { label: "待派工", color: "bg-slate-500" },
  ASSIGNED: { label: "已派工", color: "bg-blue-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-amber-500" },
  PAUSED: { label: "已暂停", color: "bg-purple-500" },
  COMPLETED: { label: "已完成", color: "bg-emerald-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" },
};

export const priorityConfigs = {
  URGENT: { label: "紧急", color: "bg-red-500" },
  HIGH: { label: "高", color: "bg-orange-500" },
  MEDIUM: { label: "中", color: "bg-amber-500" },
  LOW: { label: "低", color: "bg-blue-500" },
};

export const INITIAL_NEW_ORDER = {
  task_name: "",
  task_type: "ASSEMBLY",
  project_id: null,
  machine_id: null,
  workshop_id: null,
  workstation_id: null,
  process_id: null,
  material_name: "",
  specification: "",
  plan_qty: 0,
  standard_hours: 0,
  plan_start_date: "",
  plan_end_date: "",
  priority: "MEDIUM",
  work_content: "",
  remark: "",
};

export const INITIAL_ASSIGN_DATA = {
  assigned_to: null,
  workstation_id: null,
};
