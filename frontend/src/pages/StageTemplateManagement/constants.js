// 项目类型常量
export const PROJECT_TYPES = {
  STANDARD: { label: "标准项目", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
  CUSTOM: { label: "定制项目", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
  RD: { label: "研发项目", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
  MAINTENANCE: { label: "维保项目", color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
};

export const INITIAL_FORM_DATA = {
  template_code: "",
  template_name: "",
  description: "",
  project_type: "STANDARD",
  is_default: false,
  is_active: true,
};
