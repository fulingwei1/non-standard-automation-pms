/**
 * ECN Configuration Constants
 * ECN (Engineering Change Notice) 配置常量
 * 工程变更通知配置常量
 *
 * This is the main ECN constants file.
 * ecnManagementConstants.js re-exports from this file.
 */

// ECN 状态配置
export const statusConfigs = {
 DRAFT: { label: "草稿", color: "bg-slate-500", textColor: "text-slate-50" },
 SUBMITTED: { label: "已提交", color: "bg-blue-500", textColor: "text-blue-50" },
 EVALUATING: { label: "评估中", color: "bg-amber-500", textColor: "text-amber-50" },
 EVALUATED: { label: "评估完成", color: "bg-amber-600", textColor: "text-amber-50" },
 PENDING_APPROVAL: { label: "待审批", color: "bg-purple-500", textColor: "text-purple-50" },
  APPROVED: { label: "已批准", color: "bg-emerald-500", textColor: "text-emerald-50" },
  REJECTED: { label: "已驳回", color: "bg-red-500", textColor: "text-red-50" },
  EXECUTING: { label: "执行中", color: "bg-violet-500", textColor: "text-violet-50" },
 PENDING_VERIFY: { label: "待验证", color: "bg-indigo-500", textColor: "text-indigo-50" },
 COMPLETED: { label: "已完成", color: "bg-green-500", textColor: "text-green-50" },
 CLOSED: { label: "已关闭", color: "bg-gray-500", textColor: "text-gray-50" },
 CANCELLED: { label: "已取消", color: "bg-gray-500", textColor: "text-gray-50" },
};

// ECN 类型配置
export const typeConfigs = {
 // 客户相关（3种）
 CUSTOMER_REQUIREMENT: { label: "客户需求变更", color: "bg-blue-500", textColor: "text-blue-50", icon: "👤", category: "客户相关" },
  CUSTOMER_SPEC: { label: "客户规格调整", color: "bg-blue-400", textColor: "text-blue-50", icon: "📋", category: "客户相关" },
 CUSTOMER_FEEDBACK: { label: "客户现场反馈", color: "bg-blue-600", textColor: "text-blue-50", icon: "💬", category: "客户相关" },

 // 设计变更（5种）
 MECHANICAL_STRUCTURE: { label: "机械结构变更", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "⚙️", category: "设计变更" },
 ELECTRICAL_SCHEME: { label: "电气方案变更", color: "bg-cyan-400", textColor: "text-cyan-50", icon: "⚡", category: "设计变更" },
 SOFTWARE_UPDATE: { label: "软件更新", color: "bg-cyan-600", textColor: "text-cyan-50", icon: "💻", category: "设计变更" },
 PROCESS_OPTIMIZATION: { label: "工艺优化", color: "bg-cyan-700", textColor: "text-cyan-50", icon: "🔧", category: "设计变更" },
 DRAWING_MODIFICATION: { label: "图纸修改", color: "bg-cyan-800", textColor: "text-cyan-50", icon: "📐", category: "设计变更" },

 // 来自 ecnManagementConstants - 设计变更额外类型
 SOFTWARE_FUNCTION: { label: "软件功能变更", color: "bg-cyan-600", textColor: "text-cyan-50", icon: "💻", category: "设计变更" },
 TECH_OPTIMIZATION: { label: "技术方案优化", color: "bg-teal-500", textColor: "text-teal-50", icon: "🔧", category: "设计变更" },
 DESIGN_FIX: { label: "设计缺陷修复", color: "bg-teal-600", textColor: "text-teal-50", icon: "🔧", category: "设计变更" },

 // 来自 ecnManagementConstants - 测试相关（4种）
 TEST_STANDARD: { label: "测试标准变更", color: "bg-purple-500", textColor: "text-purple-50", icon: "📋", category: "测试相关" },
 TEST_FIXTURE: { label: "测试工装变更", color: "bg-purple-400", textColor: "text-purple-50", icon: "🔧", category: "测试相关" },
 CALIBRATION_SCHEME: { label: "校准方案变更", color: "bg-purple-600", textColor: "text-purple-50", icon: "📋", category: "测试相关" },
 TEST_PROGRAM: { label: "测试程序变更", color: "bg-violet-500", textColor: "text-violet-50", icon: "💻", category: "测试相关" },

 // 物料变更（3种）
 MATERIAL_SUBSTITUTION: { label: "物料替代", color: "bg-green-500", textColor: "text-green-50", icon: "🔄", category: "生产制造" },
  SUPPLIER_CHANGE: { label: "供应商变更", color: "bg-green-400", textColor: "text-green-50", icon: "🏭", category: "生产制造" },
 QUALITY_IMPROVEMENT: { label: "质量改进", color: "bg-green-600", textColor: "text-green-50", icon: "✅", category: "生产制造" },

 // 生产制造（2种）
  PROCESS_ADJUSTMENT: { label: "工艺调整", color: "bg-orange-500", textColor: "text-orange-50", icon: "🏗️", category: "生产制造" },
 EQUIPMENT_MODIFICATION: { label: "设备改造", color: "bg-orange-400", textColor: "text-orange-50", icon: "🔨", category: "生产制造" },

  // 来自 ecnManagementConstants - 生产制造额外类型
 PROCESS_IMPROVEMENT: { label: "工艺改进", color: "bg-orange-500", textColor: "text-orange-50", icon: "🔧", category: "生产制造" },
 MATERIAL_SUBSTITUTE: { label: "物料替代", color: "bg-orange-400", textColor: "text-orange-50", icon: "🔄", category: "生产制造" },
 COST_OPTIMIZATION: { label: "成本优化", color: "bg-amber-500", textColor: "text-amber-50", icon: "💰", category: "生产制造" },

 // 成本优化（2种）
 COST_REDUCTION: { label: "成本降低", color: "bg-purple-500", textColor: "text-purple-50", icon: "💰", category: "成本优化" },
  EFFICIENCY_IMPROVEMENT: { label: "效率提升", color: "bg-purple-400", textColor: "text-purple-50", icon: "📈", category: "成本优化" },

 // 法规合规（1种）
 REGULATORY_COMPLIANCE: { label: "法规合规", color: "bg-red-500", textColor: "text-red-50", icon: "⚖️", category: "法规合规" },

 // 纠正措施（3种）
  CORRECTIVE_ACTION: { label: "纠正措施", color: "bg-rose-500", textColor: "text-rose-50", icon: "🔍", category: "纠正措施" },
 PREVENTIVE_ACTION: { label: "预防措施", color: "bg-rose-400", textColor: "text-rose-50", icon: "🛡️", category: "纠正措施" },
  NONCONFORMANCE: { label: "不合格品处理", color: "bg-rose-600", textColor: "text-rose-50", icon: "❌", category: "纠正措施" },

 // 标准化（3种）
 STANDARDIZATION: { label: "标准化", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "📏", category: "标准化" },
 DOCUMENTATION_UPDATE: { label: "文档更新", color: "bg-indigo-400", textColor: "text-indigo-50", icon: "📚", category: "标准化" },
 VERSION_CONTROL: { label: "版本控制", color: "bg-indigo-600", textColor: "text-indigo-50", icon: "🔢", category: "标准化" },

  // 来自 ecnManagementConstants - 质量安全（3种）
 QUALITY_ISSUE: { label: "质量问题整改", color: "bg-red-500", textColor: "text-red-50", icon: "❌", category: "质量安全" },
  SAFETY_COMPLIANCE: { label: "安全合规变更", color: "bg-red-600", textColor: "text-red-50", icon: "⚠️", category: "质量安全" },
 RELIABILITY_IMPROVEMENT: { label: "可靠性改进", color: "bg-rose-500", textColor: "text-rose-50", icon: "✅", category: "质量安全" },

 // 来自 ecnManagementConstants - 项目管理（3种）
 SCHEDULE_ADJUSTMENT: { label: "进度调整", color: "bg-green-500", textColor: "text-green-50", icon: "📅", category: "项目管理" },
 DOCUMENT_UPDATE: { label: "文档更新", color: "bg-green-400", textColor: "text-green-50", icon: "📚", category: "项目管理" },
  DRAWING_CHANGE: { label: "图纸变更", color: "bg-emerald-500", textColor: "text-emerald-50", icon: "📐", category: "项目管理" },

 // 兼容旧版本
 DESIGN: { label: "设计变更", color: "bg-blue-500", textColor: "text-blue-50", icon: "📐", category: "设计变更" },
 MATERIAL: { label: "物料变更", color: "bg-amber-500", textColor: "text-amber-50", icon: "🔄", category: "生产制造" },
 PROCESS: { label: "工艺变更", color: "bg-purple-500", textColor: "text-purple-50", icon: "🔧", category: "生产制造" },
 SPECIFICATION: { label: "规格变更", color: "bg-green-500", textColor: "text-green-50", icon: "📋", category: "项目管理" },
 SCHEDULE: { label: "计划变更", color: "bg-orange-500", textColor: "text-orange-50", icon: "📅", category: "项目管理" },

 // 其他
 OTHER: { label: "其他", color: "bg-gray-500", textColor: "text-gray-50", icon: "📌", category: "其他" },
};

// 优先级配置
export const priorityConfigs = {
 LOW: { label: "低", color: "bg-slate-500", textColor: "text-slate-50", value: 1 },
  MEDIUM: { label: "中", color: "bg-blue-500", textColor: "text-blue-50", value: 2 },
 HIGH: { label: "高", color: "bg-orange-500", textColor: "text-orange-50", value: 3 },
 URGENT: { label: "紧急", color: "bg-red-500", textColor: "text-red-50", value: 4 },
 CRITICAL: { label: "关键", color: "bg-purple-500", textColor: "text-purple-50", value: 5 },
};

// 任务类型配置
export const taskTypeConfigs = {
 BOM_UPDATE: { label: "BOM更新", color: "bg-blue-500", textColor: "text-blue-50" },
 DRAWING_UPDATE: { label: "图纸更新", color: "bg-green-500", textColor: "text-green-50" },
 PROGRAM_UPDATE: { label: "程序更新", color: "bg-purple-500", textColor: "text-purple-50" },
 PURCHASE_ADJUST: { label: "采购调整", color: "bg-orange-500", textColor: "text-orange-50" },
 QUALITY_CHECK: { label: "质量检查", color: "bg-red-500", textColor: "text-red-50" },
 PRODUCTION_CHANGE: { label: "生产变更", color: "bg-cyan-500", textColor: "text-cyan-50" },
 DOCUMENT_UPDATE: { label: "文档更新", color: "bg-indigo-500", textColor: "text-indigo-50" },
 OTHER: { label: "其他", color: "bg-gray-500", textColor: "text-gray-50" },
};

// 任务状态配置
export const taskStatusConfigs = {
  PENDING: { label: "待开始", color: "bg-slate-500", textColor: "text-slate-50" },
 IN_PROGRESS: { label: "进行中", color: "bg-blue-500", textColor: "text-blue-50" },
 COMPLETED: { label: "已完成", color: "bg-green-500", textColor: "text-green-50" },
 DELAYED: { label: "已延期", color: "bg-red-500", textColor: "text-red-50" },
 CANCELLED: { label: "已取消", color: "bg-gray-500", textColor: "text-gray-50" },
};

// 审批状态配置
export const approvalStatusConfigs = {
 PENDING: { label: "待审批", color: "bg-yellow-500", textColor: "text-yellow-50" },
 APPROVED: { label: "已批准", color: "bg-green-500", textColor: "text-green-50" },
 REJECTED: { label: "已驳回", color: "bg-red-500", textColor: "text-red-50" },
 CANCELLED: { label: "已取消", color: "bg-gray-500", textColor: "text-gray-50" },
};

// 评估状态配置
export const evaluationStatusConfigs = {
 PENDING: { label: "待评估", color: "bg-slate-500", textColor: "text-slate-50" },
  IN_PROGRESS: { label: "评估中", color: "bg-blue-500", textColor: "text-blue-50" },
 COMPLETED: { label: "评估完成", color: "bg-green-500", textColor: "text-green-50" },
 APPROVED: { label: "已批准", color: "bg-emerald-500", textColor: "text-emerald-50" },
 REJECTED: { label: "已驳回", color: "bg-red-500", textColor: "text-red-50" },
};

// 评估结果配置（来自 ecnManagementConstants）
export const evalResultConfigs = {
 APPROVED: { label: "通过", color: "bg-green-500" },
 CONDITIONAL: { label: "有条件通过", color: "bg-yellow-500" },
 REJECTED: { label: "不通过", color: "bg-red-500" },
};

// 影响类型配置
export const impactTypeConfigs = {
 COST: { label: "成本影响", color: "bg-red-500", textColor: "text-red-50", icon: "💰" },
 SCHEDULE: { label: "进度影响", color: "bg-orange-500", textColor: "text-orange-50", icon: "📅" },
 QUALITY: { label: "质量影响", color: "bg-purple-500", textColor: "text-purple-50", icon: "✅" },
  TECHNICAL: { label: "技术影响", color: "bg-blue-500", textColor: "text-blue-50", icon: "🔧" },
 SAFETY: { label: "安全影响", color: "bg-red-600", textColor: "text-red-50", icon: "⚠️" },
 ENVIRONMENTAL: { label: "环境影响", color: "bg-green-500", textColor: "text-green-50", icon: "🌱" },
 REGULATORY: { label: "法规影响", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "⚖️" },
 CUSTOMER: { label: "客户影响", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "👤" },
};

// 变更日志类型配置
export const logTypeConfigs = {
  CREATED: { label: "创建", color: "bg-blue-500", textColor: "text-blue-50", icon: "➕" },
 UPDATED: { label: "更新", color: "bg-green-500", textColor: "text-green-50", icon: "✏️" },
 APPROVED: { label: "批准", color: "bg-emerald-500", textColor: "text-emerald-50", icon: "✅" },
 REJECTED: { label: "驳回", color: "bg-red-500", textColor: "text-red-50", icon: "❌" },
 EVALUATED: { label: "评估", color: "bg-amber-500", textColor: "text-amber-50", icon: "📊" },
 EXECUTED: { label: "执行", color: "bg-violet-500", textColor: "text-violet-50", icon: "🔨" },
 COMPLETED: { label: "完成", color: "bg-green-600", textColor: "text-green-50", icon: "🎉" },
  CANCELLED: { label: "取消", color: "bg-gray-500", textColor: "text-gray-50", icon: "🚫" },
};

// Tab 配置
export const tabConfigs = [
 { value: "info", label: "基本信息", icon: "📋" },
 { value: "evaluations", label: "评估管理", icon: "📊" },
 { value: "approvals", label: "审批流程", icon: "✅" },
 { value: "tasks", label: "执行任务", icon: "🔨" },
 { value: "affected", label: "影响分析", icon: "📈" },
 { value: "knowledge", label: "知识库", icon: "📚" },
 { value: "integration", label: "模块集成", icon: "🔗" },
 { value: "logs", label: "变更日志", icon: "📜" },
];

// 批量操作选项（来自 ecnManagementConstants）
export const batchOperations = [
 { value: "batch_submit", label: "批量提交", icon: "CheckCircle2" },
 { value: "batch_close", label: "批量关闭", icon: "X" },
 { value: "batch_export", label: "批量导出", icon: "Download" },
];

// 订单类型配置（来自 ecnManagementConstants）
export const orderTypes = [
 { value: "PURCHASE", label: "采购订单" },
 { value: "OUTSOURCING", label: "外协订单" },
];

// 物料变更类型配置（来自 ecnManagementConstants）
export const materialChangeTypes = [
  { value: "UPDATE", label: "更新" },
 { value: "DELETE", label: "删除" },
 { value: "ADD", label: "新增" },
];

// 筛选选项（来自 ecnManagementConstants）
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

// 默认表单数据（来自 ecnManagementConstants）
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

// 工具函数
export const getPriorityValue = (item) => {
 if (!item.priority) {return 0;}
 return priorityConfigs[item.priority]?.value || 0;
};

export const getStatusConfig = (status) => {
 return statusConfigs[status] || statusConfigs.DRAFT;
};

export const getTypeConfig = (type) => {
 return typeConfigs[type] || typeConfigs.OTHER;
};

export const getPriorityConfig = (priority) => {
 return priorityConfigs[priority] || priorityConfigs.MEDIUM;
};

export const formatPriority = (priority) => {
 return getPriorityConfig(priority).label;
};

export const formatStatus = (status) => {
 return getStatusConfig(status).label;
};

export const formatType = (type) => {
 return getTypeConfig(type).label;
};

// 排序函数
export const sortByPriority = (a, b) => {
 return getPriorityValue(b) - getPriorityValue(a);
};

export const sortByStatus = (a, b) => {
 const statusOrder = ['DRAFT', 'SUBMITTED', 'EVALUATING', 'PENDING_APPROVAL', 'APPROVED', 'EXECUTING', 'COMPLETED'];
 const aIndex = statusOrder.indexOf(a.status);
  const bIndex = statusOrder.indexOf(b.status);
 return aIndex - bIndex;
};

// 验证函数
export const isValidStatus = (status) => {
 return Object.keys(statusConfigs).includes(status);
};

export const isValidType = (type) => {
 return Object.keys(typeConfigs).includes(type);
};

export const isValidPriority = (priority) => {
 return Object.keys(priorityConfigs).includes(priority);
};

// 过滤函数
export const filterByStatus = (items, status) => {
 return items.filter(item => item.status === status);
};

export const filterByType = (items, type) => {
 return items.filter(item => item.type === type);
};

export const filterByPriority = (items, priority) => {
 return items.filter(item => item.priority === priority);
};

// 辅助函数 - 标签获取（来自 ecnManagementConstants）
export const getStatusLabel = (status) => {
 return statusConfigs[status]?.label || status;
};

export const getTypeLabel = (type) => {
 return typeConfigs[type]?.label || type;
};

export const getPriorityLabel = (priority) => {
 return priorityConfigs[priority]?.label || priority;
};

// 颜色获取函数（来自 ecnManagementConstants）
export const getStatusColor = (status) => {
 return statusConfigs[status]?.color || "bg-gray-500";
};

export const getTypeColor = (type) => {
 return typeConfigs[type]?.color || "bg-gray-500";
};

export const getPriorityColor = (priority) => {
 return priorityConfigs[priority]?.color || "bg-gray-500";
};

// 按类别分组类型（来自 ecnManagementConstants）
export const getCategoryTypes = (category) => {
  return Object.keys(typeConfigs)
  .filter(key => typeConfigs[key].category === category)
  .map(key => ({
  value: key,
 label: typeConfigs[key].label,
  color: typeConfigs[key].color
  }));
};

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

export default {
 statusConfigs,
 typeConfigs,
 priorityConfigs,
 taskTypeConfigs,
 taskStatusConfigs,
 approvalStatusConfigs,
  evaluationStatusConfigs,
 evalResultConfigs,
  impactTypeConfigs,
 logTypeConfigs,
 tabConfigs,
 batchOperations,
 orderTypes,
 materialChangeTypes,
 filterOptions,
 defaultECNForm,
  defaultEvaluationForm,
 defaultTaskForm,
 defaultMaterialForm,
  defaultOrderForm,
 getPriorityValue,
  getStatusConfig,
  getTypeConfig,
 getPriorityConfig,
 formatPriority,
 formatStatus,
 formatType,
 sortByPriority,
 sortByStatus,
 isValidStatus,
 isValidType,
 isValidPriority,
 filterByStatus,
 filterByType,
 filterByPriority,
 getStatusLabel,
 getTypeLabel,
 getPriorityLabel,
 getStatusColor,
 getTypeColor,
 getPriorityColor,
 getCategoryTypes,
 getTypesByCategory,
};
