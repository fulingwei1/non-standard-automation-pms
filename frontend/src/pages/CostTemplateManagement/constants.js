/**
 * Constants for Cost Template Management
 */

export const TEMPLATE_TYPES = [
  { value: "STANDARD", label: "标准模板" },
  { value: "CUSTOM", label: "自定义模板" },
  { value: "PROJECT", label: "项目模板" },
];

export const TEMPLATE_TYPE_LABEL_MAP = {
  STANDARD: "标准",
  CUSTOM: "自定义",
  PROJECT: "项目",
};

export const INITIAL_FORM_DATA = {
  template_code: "",
  template_name: "",
  template_type: "STANDARD",
  equipment_type: "",
  industry: "",
  description: "",
  cost_structure: {
    categories: [],
  },
  is_active: true,
};

export const INITIAL_COST_ITEM = {
  item_name: "",
  specification: "",
  unit: "",
  default_qty: 1,
  default_unit_price: 0,
  default_cost: 0,
  lead_time_days: 0,
};
