/**
 * QuoteCreateEdit constants and default values
 */

export const DEFAULT_FORM_DATA = {
  opportunity_id: null,
  customer_id: null,
  solution_id: null,
  presale_ticket_id: null,
  quote_code: "",
  quote_name: "",
  valid_days: 30,
  lead_time_days: 60,
  payment_terms: "",
  delivery_terms: "",
  risk_terms: "",
  note: "",
};

export const DEFAULT_VERSION_DATA = {
  version_no: "V1.0",
  total_price: 0,
  cost_total: 0,
  tax_rate: 13,
  tax_amount: 0,
  amount_with_tax: 0,
  lead_time_days: 60,
  risk_terms: "",
  note: "",
};

export const DEFAULT_ITEM = {
  item_name: "",
  item_code: "",
  specification: "",
  qty: 1,
  unit: "套",
  unit_price: 0,
  cost: 0,
  amount: 0,
  cost_amount: 0,
  station_count: 1,
  ct_seconds: 0,
  uph: 0,
  fixture_qty: 0,
  camera_count: 0,
  light_count: 0,
  operator_hours: 0,
  engineering_hours: 0,
  material_cost: 0,
  labor_cost: 0,
  overhead_cost: 0,
  total_cost: 0,
  remark: "",
};

export const COST_LINKED_FIELDS = ["material_cost", "labor_cost", "overhead_cost"];

export const ITEM_SUBMIT_FIELDS = [
  "item_name",
  "item_code",
  "specification",
  "qty",
  "unit",
  "unit_price",
  "cost",
  "station_count",
  "ct_seconds",
  "uph",
  "fixture_qty",
  "camera_count",
  "light_count",
  "operator_hours",
  "engineering_hours",
  "material_cost",
  "labor_cost",
  "overhead_cost",
  "total_cost",
  "remark",
];

export const quoteStatusConfigs = {
  draft: { label: "草稿" },
  pending: { label: "待审批" },
  approved: { label: "已审批" },
  sent: { label: "已发送" },
};

export const validityOptions = [
  { value: 7, label: "7天" },
  { value: 15, label: "15天" },
  { value: 30, label: "30天" },
];
