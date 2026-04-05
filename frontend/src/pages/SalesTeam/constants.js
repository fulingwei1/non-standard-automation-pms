/**
 * SalesTeam page constants
 */

// Organization level colors for tree nodes
export const LEVEL_COLORS = {
  GM: "border-purple-500 bg-purple-500/10",
  Director: "border-blue-500 bg-blue-500/10",
  Manager: "border-green-500 bg-green-500/10",
  Sales: "border-slate-500 bg-slate-500/10",
};

// Organization hierarchy definitions
export const ORG_HIERARCHY = [
  { level: "L1", name: "销售总经理", code: "GM", scope: "全公司", report: "CEO", manage: "所有总监" },
  { level: "L2", name: "销售总监", code: "Director", scope: "分公司", report: "销售总经理", manage: "2-3 个经理" },
  { level: "L3", name: "销售经理", code: "Manager", scope: "销售团队", report: "销售总监", manage: "3-5 人" },
  { level: "L4", name: "销售", code: "Sales", scope: "个人", report: "销售经理", manage: "-" },
];

// Default create team form values
export const DEFAULT_CREATE_TEAM_FORM = {
  team_name: "",
  team_code: "",
  team_type: "REGION",
  department_id: "",
  leader_id: "",
  description: "",
};

// Team type options
export const TEAM_TYPE_OPTIONS = [
  { value: "REGION", label: "按区域" },
  { value: "INDUSTRY", label: "按行业" },
  { value: "SCALE", label: "按规模" },
  { value: "OTHER", label: "其他" },
];
