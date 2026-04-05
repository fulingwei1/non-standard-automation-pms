// 岗位类别配置
export const POSITION_CATEGORIES = [
  { value: "MANAGEMENT", label: "管理类", color: "text-purple-600 bg-purple-50" },
  { value: "TECHNICAL", label: "技术类", color: "text-blue-600 bg-blue-50" },
  { value: "SALES", label: "销售类", color: "text-green-600 bg-green-50" },
  { value: "FINANCE", label: "财务类", color: "text-yellow-600 bg-yellow-50" },
  { value: "PRODUCTION", label: "生产类", color: "text-orange-600 bg-orange-50" },
  { value: "SUPPORT", label: "支持类", color: "text-gray-600 bg-gray-50" },
];

// 获取类别配置
export const getCategoryConfig = (category) => {
  return POSITION_CATEGORIES.find((c) => c.value === category) || POSITION_CATEGORIES[5];
};

// 默认表单数据
export const DEFAULT_FORM_DATA = {
  position_code: "",
  position_name: "",
  position_category: "TECHNICAL",
  org_unit_id: null,
  description: "",
  sort_order: 0,
  is_active: true,
};
