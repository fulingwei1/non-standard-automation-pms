/**
 * ECN Management Configuration
 * ECN管理相关常量和配置
 */

// 状态配置
export const statusConfigs = {
  DRAFT: { label: "草稿", color: "bg-slate-500" },
  SUBMITTED: { label: "已提交", color: "bg-blue-500" },
  EVALUATING: { label: "评估中", color: "bg-amber-500" },
  EVALUATED: { label: "评估完成", color: "bg-amber-600" },
  PENDING_APPROVAL: { label: "待审批", color: "bg-purple-500" },
  APPROVED: { label: "已批准", color: "bg-emerald-500" },
  REJECTED: { label: "已驳回", color: "bg-red-500" },
  EXECUTING: { label: "执行中", color: "bg-violet-500" },
  PENDING_VERIFY: { label: "待验证", color: "bg-indigo-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
  CLOSED: { label: "已关闭", color: "bg-gray-500" },
  CANCELLED: { label: "已取消", color: "bg-gray-500" },
};

// 类型配置
export const typeConfigs = {
  // 客户相关（3种）- 蓝色系
  CUSTOMER_REQUIREMENT: {
    label: "客户需求变更",
    color: "bg-blue-500",
    category: "客户相关",
  },
  CUSTOMER_SPEC: {
    label: "客户规格调整",
    color: "bg-blue-400",
    category: "客户相关",
  },
  CUSTOMER_FEEDBACK: {
    label: "客户现场反馈",
    color: "bg-blue-600",
    category: "客户相关",
  },

  // 设计变更（5种）- 青色系
  MECHANICAL_STRUCTURE: {
    label: "机械结构变更",
    color: "bg-cyan-500",
    category: "设计变更",
  },
  ELECTRICAL_SCHEME: {
    label: "电气方案变更",
    color: "bg-cyan-400",
    category: "设计变更",
  },
  SOFTWARE_FUNCTION: {
    label: "软件功能变更",
    color: "bg-cyan-600",
    category: "设计变更",
  },
  TECH_OPTIMIZATION: {
    label: "技术方案优化",
    color: "bg-teal-500",
    category: "设计变更",
  },
  DESIGN_FIX: {
    label: "设计缺陷修复",
    color: "bg-teal-600",
    category: "设计变更",
  },

  // 测试相关（4种）- 紫色系
  TEST_STANDARD: {
    label: "测试标准变更",
    color: "bg-purple-500",
    category: "测试相关",
  },
  TEST_FIXTURE: {
    label: "测试工装变更",
    color: "bg-purple-400",
    category: "测试相关",
  },
  CALIBRATION_SCHEME: {
    label: "校准方案变更",
    color: "bg-purple-600",
    category: "测试相关",
  },
  TEST_PROGRAM: {
    label: "测试程序变更",
    color: "bg-violet-500",
    category: "测试相关",
  },

  // 生产制造（4种）- 橙色系
  PROCESS_IMPROVEMENT: {
    label: "工艺改进",
    color: "bg-orange-500",
    category: "生产制造",
  },
  MATERIAL_SUBSTITUTE: {
    label: "物料替代",
    color: "bg-orange-400",
    category: "生产制造",
  },
  SUPPLIER_CHANGE: {
    label: "供应商变更",
    color: "bg-orange-600",
    category: "生产制造",
  },
  COST_OPTIMIZATION: {
    label: "成本优化",
    color: "bg-amber-500",
    category: "生产制造",
  },

  // 质量安全（3种）- 红色系
  QUALITY_ISSUE: {
    label: "质量问题整改",
    color: "bg-red-500",
    category: "质量安全",
  },
  SAFETY_COMPLIANCE: {
    label: "安全合规变更",
    color: "bg-red-600",
    category: "质量安全",
  },
  RELIABILITY_IMPROVEMENT: {
    label: "可靠性改进",
    color: "bg-rose-500",
    category: "质量安全",
  },

  // 项目管理（3种）- 绿色系
  SCHEDULE_ADJUSTMENT: {
    label: "进度调整",
    color: "bg-green-500",
    category: "项目管理",
  },
  DOCUMENT_UPDATE: {
    label: "文档更新",
    color: "bg-green-400",
    category: "项目管理",
  },
  DRAWING_CHANGE: {
    label: "图纸变更",
    color: "bg-emerald-500",
    category: "项目管理",
  },

  // 兼容旧版本
  DESIGN: { label: "设计变更", color: "bg-blue-500", category: "设计变更" },
  MATERIAL: { label: "物料变更", color: "bg-amber-500", category: "生产制造" },
  PROCESS: { label: "工艺变更", color: "bg-purple-500", category: "生产制造" },
  SPECIFICATION: {
    label: "规格变更",
    color: "bg-green-500",
    category: "项目管理",
  },
  SCHEDULE: { label: "计划变更", color: "bg-orange-500", category: "项目管理" },
  OTHER: { label: "其他", color: "bg-slate-500", category: "其他" },
};

// 优先级配置
export const priorityConfigs = {
  URGENT: { label: "紧急", color: "bg-red-500" },
  HIGH: { label: "高", color: "bg-orange-500" },
  MEDIUM: { label: "中", color: "bg-amber-500" },
  LOW: { label: "低", color: "bg-blue-500" },
};

// 评估结果配置
export const evalResultConfigs = {
  APPROVED: { label: "通过", color: "bg-green-500" },
  CONDITIONAL: { label: "有条件通过", color: "bg-yellow-500" },
  REJECTED: { label: "不通过", color: "bg-red-500" },
};

// 任务状态配置
export const taskStatusConfigs = {
  PENDING: { label: "待开始", color: "bg-slate-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500" },
  COMPLETED: { label: "已完成", color: "bg-green-500" },
};

// 批量操作选项
export const batchOperations = [
  { value: "batch_submit", label: "批量提交", icon: "CheckCircle2" },
  { value: "batch_close", label: "批量关闭", icon: "X" },
  { value: "batch_export", label: "批量导出", icon: "Download" },
];

// 订单类型配置
export const orderTypes = [
  { value: "PURCHASE", label: "采购订单" },
  { value: "OUTSOURCING", label: "外协订单" },
];

// 物料变更类型配置
export const materialChangeTypes = [
  { value: "UPDATE", label: "更新" },
  { value: "DELETE", label: "删除" },
  { value: "ADD", label: "新增" },
];

// 筛选选项
export const filterOptions = {
  types: Object.keys(typeConfigs).map(key => ({
    value: key,
    label: typeConfigs[key].label,
    category: typeConfigs[key].category
  })),
  statuses: Object.keys(statusConfigs).map(key => ({
    value: key,
    label: statusConfigs[key].label
  })),
  priorities: Object.keys(priorityConfigs).map(key => ({
    value: key,
    label: priorityConfigs[key].label
  }))
};

// 默认表单数据
export const defaultECNForm = {
  ecn_title: "",
  ecn_type: "CUSTOMER_REQUIREMENT",
  project_id: null,
  machine_id: null,
  priority: "MEDIUM",
  urgency: "NORMAL",
  change_reason: "",
  change_description: "",
  change_scope: "PARTIAL",
  source_type: "MANUAL",
};

export const defaultEvaluationForm = {
  eval_dept: "",
  impact_analysis: "",
  cost_estimate: 0,
  schedule_estimate: 0,
  resource_requirement: "",
  risk_assessment: "",
  eval_result: "APPROVED",
  eval_opinion: "",
  conditions: "",
};

export const defaultTaskForm = {
  task_name: "",
  task_type: "",
  task_dept: "",
  task_description: "",
  deliverables: "",
  assignee_id: null,
  planned_start: "",
  planned_end: "",
};

export const defaultMaterialForm = {
  material_id: null,
  bom_item_id: null,
  material_code: "",
  material_name: "",
  specification: "",
  change_type: "UPDATE",
  old_quantity: "",
  old_specification: "",
  old_supplier_id: null,
  new_quantity: "",
  new_specification: "",
  new_supplier_id: null,
  cost_impact: 0,
  remark: "",
};

export const defaultOrderForm = {
  order_type: "PURCHASE",
  order_id: null,
  order_no: "",
  impact_description: "",
  action_type: "",
  action_description: "",
};

// 辅助函数
export const getStatusLabel = (status) => {
  return statusConfigs[status]?.label || status;
};

export const getTypeLabel = (type) => {
  return typeConfigs[type]?.label || type;
};

export const getPriorityLabel = (priority) => {
  return priorityConfigs[priority]?.label || priority;
};

export const getCategoryTypes = (category) => {
  return Object.keys(typeConfigs)
    .filter(key => typeConfigs[key].category === category)
    .map(key => ({
      value: key,
      label: typeConfigs[key].label,
      color: typeConfigs[key].color
    }));
};

// 获取状态颜色
export const getStatusColor = (status) => {
  return statusConfigs[status]?.color || "bg-gray-500";
};

// 获取类型颜色
export const getTypeColor = (type) => {
  return typeConfigs[type]?.color || "bg-gray-500";
};

// 获取优先级颜色
export const getPriorityColor = (priority) => {
  return priorityConfigs[priority]?.color || "bg-gray-500";
};

// 按类别分组类型
export const getTypesByCategory = () => {
  const categories = {};
  Object.keys(typeConfigs).forEach(key => {
    const config = typeConfigs[key];
    if (!categories[config.category]) {
      categories[config.category] = [];
    }
    categories[config.category].push({
      value: key,
      label: config.label,
      color: config.color
    });
  });
  return categories;
};
