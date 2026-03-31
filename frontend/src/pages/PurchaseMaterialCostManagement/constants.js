/**
 * Constants for Purchase Material Cost Management
 */

export const INITIAL_FORM_DATA = {
  material_code: "",
  material_name: "",
  specification: "",
  brand: "",
  unit: "件",
  material_type: "",
  is_standard_part: true,
  unit_cost: "",
  currency: "CNY",
  supplier_id: "",
  supplier_name: "",
  purchase_date: "",
  purchase_order_no: "",
  purchase_quantity: "",
  lead_time_days: "",
  is_active: true,
  match_priority: 0,
  match_keywords: "",
  remark: "",
};

export const CURRENCY_OPTIONS = [
  { value: "CNY", label: "CNY" },
  { value: "USD", label: "USD" },
  { value: "EUR", label: "EUR" },
];

export const STANDARD_FILTER_OPTIONS = [
  { value: "all", label: "全部" },
  { value: "standard", label: "标准件" },
  { value: "non-standard", label: "非标准件" },
];

export const ACTIVE_FILTER_OPTIONS = [
  { value: "all", label: "全部" },
  { value: "active", label: "启用" },
  { value: "inactive", label: "禁用" },
];
