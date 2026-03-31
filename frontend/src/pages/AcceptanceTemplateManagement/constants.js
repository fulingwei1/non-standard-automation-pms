// Constants for Acceptance Template Management

export const typeConfigs = {
  FAT: { label: "出厂验收", color: "bg-blue-500" },
  SAT: { label: "现场验收", color: "bg-purple-500" },
  FINAL: { label: "终验收", color: "bg-emerald-500" },
};

export const statusConfigs = {
  active: { label: "启用", color: "bg-emerald-500" },
  inactive: { label: "停用", color: "bg-slate-500" },
};

export const DEFAULT_TEMPLATE_FORM = {
  template_name: "",
  template_type: "FAT",
  category: "",
  description: "",
  version: "1.0",
};

export const DEFAULT_NEW_ITEM = {
  item_code: "",
  item_name: "",
  category_name: "",
  acceptance_criteria: "",
  standard_value: "",
  unit: "",
  is_required: true,
  is_key_item: false,
};
