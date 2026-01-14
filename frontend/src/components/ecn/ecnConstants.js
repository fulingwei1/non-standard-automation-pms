/**
 * ECN 配置常量
 * 提取自 ECNDetail.jsx，供多个组件共享
 */

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

export const typeConfigs = {
  // 客户相关（3种）
  CUSTOMER_REQUIREMENT: { label: "客户需求变更", color: "bg-blue-500" },
  CUSTOMER_SPEC: { label: "客户规格调整", color: "bg-blue-400" },
  CUSTOMER_FEEDBACK: { label: "客户现场反馈", color: "bg-blue-600" },

  // 设计变更（5种）
  MECHANICAL_STRUCTURE: { label: "机械结构变更", color: "bg-cyan-500" },
  ELECTRICAL_SCHEME: { label: "电气方案变更", color: "bg-cyan-400" },
  SOFTWARE_ALGORITHM: { label: "软件算法变更", color: "bg-cyan-600" },
  BOM_CHANGE: { label: "BOM清单调整", color: "bg-cyan-300" },
  DRAWING_UPDATE: { label: "图纸更新", color: "bg-cyan-700" },

  // 质量相关（4种）
  QUALITY_ISSUE: { label: "质量问题", color: "bg-red-500" },
  DEFECT_FIX: { label: "缺陷修复", color: "bg-red-400" },
  RELIABILITY_IMPROVE: { label: "可靠性改进", color: "bg-red-600" },
  SAFETY_COMPLIANCE: { label: "安全合规", color: "bg-red-700" },

  // 成本优化（3种）
  COST_REDUCTION: { label: "成本优化", color: "bg-green-500" },
  ALTERNATIVE_MATERIAL: { label: "替代料", color: "bg-green-400" },
  SUPPLIER_CHANGE: { label: "供应商变更", color: "bg-green-600" },

  // 工艺改进（3种）
  PROCESS_OPTIMIZATION: { label: "工艺优化", color: "bg-purple-500" },
  MANUFACTURING_IMPROVE: { label: "制造改善", color: "bg-purple-400" },
  EFFICIENCY_ENHANCE: { label: "效率提升", color: "bg-purple-600" },

  // 其他（4种）
  REGULATION_COMPLIANCE: { label: "法规合规", color: "bg-orange-500" },
  TECHNOLOGY_UPGRADE: { label: "技术升级", color: "bg-indigo-500" },
  LIFECYCLE_MANAGE: { label: "生命周期管理", color: "bg-pink-500" },
  OTHER: { label: "其他", color: "bg-gray-500" },
};

export const priorityConfigs = {
  LOW: { label: "低", color: "bg-gray-500" },
  MEDIUM: { label: "中", color: "bg-blue-500" },
  HIGH: { label: "高", color: "bg-amber-500" },
  URGENT: { label: "紧急", color: "bg-red-500" },
};

export const evalResultConfigs = {
  APPROVE: { label: "通过", color: "bg-emerald-500" },
  REJECT: { label: "驳回", color: "bg-red-500" },
  CONDITIONAL: { label: "有条件通过", color: "bg-amber-500" },
};

export const taskStatusConfigs = {
  TODO: { label: "待办", color: "bg-slate-500" },
  IN_PROGRESS: { label: "进行中", color: "bg-blue-500" },
  COMPLETED: { label: "已完成", color: "bg-emerald-500" },
  BLOCKED: { label: "阻塞", color: "bg-red-500" },
};

export const rootCauseOptions = [
  { value: "DESIGN_ERROR", label: "设计问题" },
  { value: "MATERIAL_DEFECT", label: "物料缺陷" },
  { value: "PROCESS_ERROR", label: "工艺问题" },
  { value: "EXTERNAL_FACTOR", label: "外部因素" },
  { value: "COMMUNICATION", label: "沟通问题" },
  { value: "PLANNING", label: "计划问题" },
  { value: "OTHER", label: "其他" },
];

export const getStatusBadge = (status) => {
  const config = statusConfigs[status] || { label: status, color: "bg-gray-500" };
  return { ...config, text: config.label };
};

export const getTypeBadge = (type) => {
  const config = typeConfigs[type] || { label: type, color: "bg-gray-500" };
  return { ...config, text: config.label };
};

export const getPriorityBadge = (priority) => {
  const config = priorityConfigs[priority] || { label: priority, color: "bg-gray-500" };
  return { ...config, text: config.label };
};
