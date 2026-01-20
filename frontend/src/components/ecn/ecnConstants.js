/**
 * ECN Configuration Constants
 * ECN (Engineering Change Notice) 配置常量
 * 工程变更通知配置常量
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
  CUSTOMER_REQUIREMENT: { label: "客户需求变更", color: "bg-blue-500", textColor: "text-blue-50", icon: "👤" },
  CUSTOMER_SPEC: { label: "客户规格调整", color: "bg-blue-400", textColor: "text-blue-50", icon: "📋" },
  CUSTOMER_FEEDBACK: { label: "客户现场反馈", color: "bg-blue-600", textColor: "text-blue-50", icon: "💬" },

  // 设计变更（5种）
  MECHANICAL_STRUCTURE: { label: "机械结构变更", color: "bg-cyan-500", textColor: "text-cyan-50", icon: "⚙️" },
  ELECTRICAL_SCHEME: { label: "电气方案变更", color: "bg-cyan-400", textColor: "text-cyan-50", icon: "⚡" },
  SOFTWARE_UPDATE: { label: "软件更新", color: "bg-cyan-600", textColor: "text-cyan-50", icon: "💻" },
  PROCESS_OPTIMIZATION: { label: "工艺优化", color: "bg-cyan-700", textColor: "text-cyan-50", icon: "🔧" },
  DRAWING_MODIFICATION: { label: "图纸修改", color: "bg-cyan-800", textColor: "text-cyan-50", icon: "📐" },

  // 物料变更（3种）
  MATERIAL_SUBSTITUTION: { label: "物料替代", color: "bg-green-500", textColor: "text-green-50", icon: "🔄" },
  SUPPLIER_CHANGE: { label: "供应商变更", color: "bg-green-400", textColor: "text-green-50", icon: "🏭" },
  QUALITY_IMPROVEMENT: { label: "质量改进", color: "bg-green-600", textColor: "text-green-50", icon: "✅" },

  // 生产制造（2种）
  PROCESS_ADJUSTMENT: { label: "工艺调整", color: "bg-orange-500", textColor: "text-orange-50", icon: "🏗️" },
  EQUIPMENT_MODIFICATION: { label: "设备改造", color: "bg-orange-400", textColor: "text-orange-50", icon: "🔨" },

  // 成本优化（2种）
  COST_REDUCTION: { label: "成本降低", color: "bg-purple-500", textColor: "text-purple-50", icon: "💰" },
  EFFICIENCY_IMPROVEMENT: { label: "效率提升", color: "bg-purple-400", textColor: "text-purple-50", icon: "📈" },

  // 法规合规（1种）
  REGULATORY_COMPLIANCE: { label: "法规合规", color: "bg-red-500", textColor: "text-red-50", icon: "⚖️" },

  // 纠正措施（3种）
  CORRECTIVE_ACTION: { label: "纠正措施", color: "bg-rose-500", textColor: "text-rose-50", icon: "🔍" },
  PREVENTIVE_ACTION: { label: "预防措施", color: "bg-rose-400", textColor: "text-rose-50", icon: "🛡️" },
  NONCONFORMANCE: { label: "不合格品处理", color: "bg-rose-600", textColor: "text-rose-50", icon: "❌" },

  // 标准化（3种）
  STANDARDIZATION: { label: "标准化", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "📏" },
  DOCUMENTATION_UPDATE: { label: "文档更新", color: "bg-indigo-400", textColor: "text-indigo-50", icon: "📚" },
  VERSION_CONTROL: { label: "版本控制", color: "bg-indigo-600", textColor: "text-indigo-50", icon: "🔢" },

  // 其他
  OTHER: { label: "其他", color: "bg-gray-500", textColor: "text-gray-50", icon: "📌" },
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

export default {
  statusConfigs,
  typeConfigs,
  priorityConfigs,
  taskTypeConfigs,
  taskStatusConfigs,
  approvalStatusConfigs,
  evaluationStatusConfigs,
  impactTypeConfigs,
  logTypeConfigs,
  tabConfigs,
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
};