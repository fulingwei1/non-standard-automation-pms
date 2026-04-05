/**
 * Workshop Management Constants - 车间管理常量
 */

export const typeConfigs = {
  MACHINING: { label: "机加车间", color: "bg-blue-500" },
  ASSEMBLY: { label: "装配车间", color: "bg-purple-500" },
  DEBUGGING: { label: "调试车间", color: "bg-emerald-500" },
};

export const DEFAULT_WORKSHOP_FORM = {
  workshop_code: "",
  workshop_name: "",
  workshop_type: "MACHINING",
  manager_id: null,
  location: "",
  capacity_hours: 0,
  description: "",
  is_active: true,
};
