/**
 * Customer Service Constants - 客户服务模块统一常量配置
 *
 * 合并自：
 * - components/customer-service/customerServiceConstants.js
 * - components/customer-service-dashboard/customerServiceConstants.js
 */

// ==================== 服务类型配置 ====================
export const SERVICE_TYPES = {
  TECHNICAL_SUPPORT: { value: 'technical_support', label: '技术支持', color: '#1890ff', icon: '🔧' },
  FIELD_SERVICE: { value: 'field_service', label: '现场服务', color: '#52c41a', icon: '👷' },
  WARRANTY: { value: 'warranty', label: '质保服务', color: '#faad14', icon: '🛡️' },
  TRAINING: { value: 'training', label: '培训服务', color: '#722ed1', icon: '📚' },
  CONSULTATION: { value: 'consultation', label: '咨询服务', color: '#13c2c2', icon: '💡' },
  MAINTENANCE: { value: 'maintenance', label: '维护服务', color: '#eb2f96', icon: '🔨' }
};

// ==================== 工单状态配置 ====================
export const TICKET_STATUS = {
  OPEN: { value: 'open', label: '待处理', color: '#ff4d4f' },
  IN_PROGRESS: { value: 'in_progress', label: '处理中', color: '#faad14' },
  PENDING_CUSTOMER: { value: 'pending_customer', label: '待客户确认', color: '#1890ff' },
  RESOLVED: { value: 'resolved', label: '已解决', color: '#52c41a' },
  CLOSED: { value: 'closed', label: '已关闭', color: '#8c8c8c' },
  REOPENED: { value: 'reopened', label: '重新打开', color: '#722ed1' }
};

// ==================== 优先级配置 ====================
export const PRIORITY_LEVELS = {
  CRITICAL: { value: 'critical', label: '紧急', color: '#ff4d4f', weight: 4, responseTime: '1小时' },
  HIGH: { value: 'high', label: '高', color: '#fa8c16', weight: 3, responseTime: '4小时' },
  MEDIUM: { value: 'medium', label: '中', color: '#1890ff', weight: 2, responseTime: '24小时' },
  LOW: { value: 'low', label: '低', color: '#52c41a', weight: 1, responseTime: '72小时' }
};

// ==================== 满意度等级配置 ====================
export const SATISFACTION_LEVELS = {
  VERY_SATISFIED: { value: 'very_satisfied', label: '非常满意', color: '#52c41a', score: 5 },
  SATISFIED: { value: 'satisfied', label: '满意', color: '#1890ff', score: 4 },
  NEUTRAL: { value: 'neutral', label: '一般', color: '#faad14', score: 3 },
  DISSATISFIED: { value: 'dissatisfied', label: '不满意', color: '#fa8c16', score: 2 },
  VERY_DISSATISFIED: { value: 'very_dissatisfied', label: '非常不满意', color: '#ff4d4f', score: 1 }
};

// ==================== 服务阶段配置 ====================
export const SERVICE_PHASES = {
  S1: { value: 's1', label: '需求分析', description: '客户需求收集与分析' },
  S2: { value: 's2', label: '方案设计', description: '技术方案设计' },
  S3: { value: 's3', label: '设备采购', description: '设备材料采购' },
  S4: { value: 's4', label: '施工准备', description: '现场施工准备' },
  S5: { value: 's5', label: '安装施工', description: '设备安装施工' },
  S6: { value: 's6', label: '系统调试', description: '系统集成调试' },
  S7: { value: 's7', label: '初步验收', description: '初步验收测试' },
  S8: { value: 's8', label: '现场交付', description: '现场交付使用' },
  S9: { value: 's9', label: '质保结项', description: '质保期结束结项' }
};

// ==================== 响应渠道配置 ====================
export const RESPONSE_CHANNELS = {
  PHONE: { value: 'phone', label: '电话', icon: '📞' },
  EMAIL: { value: 'email', label: '邮件', icon: '📧' },
  WEBSITE: { value: 'website', label: '官网', icon: '🌐' },
  WECHAT: { value: 'wechat', label: '微信', icon: '💬' },
  SYSTEM: { value: 'system', label: '系统', icon: '💻' },
  ON_SITE: { value: 'on_site', label: '现场', icon: '📍' }
};

// ==================== 解决方式配置 ====================
export const RESOLUTION_METHODS = {
  REMOTE: { value: 'remote', label: '远程解决', icon: '🌐' },
  ON_SITE: { value: 'on_site', label: '现场处理', icon: '👷' },
  REPLACEMENT: { value: 'replacement', label: '更换设备', icon: '🔄' },
  REPAIR: { value: 'repair', label: '维修处理', icon: '🔧' },
  TRAINING: { value: 'training', label: '培训指导', icon: '📚' },
  ESCALATION: { value: 'escalation', label: '升级处理', icon: '⬆️' }
};

// ==================== 质保类型配置 ====================
export const WARRANTY_TYPES = {
  STANDARD: { value: 'standard', label: '标准质保', duration: '12个月' },
  EXTENDED: { value: 'extended', label: '延长质保', duration: '24个月' },
  PREMIUM: { value: 'premium', label: '高级质保', duration: '36个月' },
  LIFETIME: { value: 'lifetime', label: '终身质保', duration: '永久' }
};

// ==================== 性能指标配置 ====================
export const PERFORMANCE_METRICS = {
  RESPONSE_TIME: { label: '响应时间', unit: '小时', target: 4 },
  RESOLUTION_TIME: { label: '解决时间', unit: '小时', target: 24 },
  FIRST_CONTACT_RESOLUTION: { label: '首次解决率', unit: '%', target: 75 },
  CUSTOMER_SATISFACTION: { label: '客户满意度', unit: '分', target: 4.5 },
  SERVICE_LEVEL_AGREEMENT: { label: 'SLA达成率', unit: '%', target: 95 }
};

// ==================== 升级等级配置 ====================
export const ESCALATION_LEVELS = {
  L1: { value: 'l1', label: 'L1客服', description: '一线客服支持' },
  L2: { value: 'l2', label: 'L2技术', description: '二线技术支持' },
  L3: { value: 'l3', label: 'L3专家', description: '三线专家支持' },
  L4: { value: 'l4', label: 'L4研发', description: '研发团队支持' }
};

// ==================== 表格配置 ====================
export const TABLE_CONFIG = {
  pagination: { pageSize: 10, showSizeChanger: true },
  scroll: { x: 1400, y: 500 },
  size: 'middle'
};

// ==================== 图表颜色配置 ====================
export const CHART_COLORS = {
  POSITIVE: '#52c41a',
  WARNING: '#faad14',
  NEGATIVE: '#ff4d4f',
  PRIMARY: '#1890ff',
  SECONDARY: '#722ed1'
};

// ==================== 默认筛选配置 ====================
export const DEFAULT_FILTERS = {
  status: null,
  priority: null,
  serviceType: null,
  dateRange: null,
  engineer: null
};

// ==================== 仪表盘相关配置（来自 customer-service-dashboard） ====================

// 客户状态配置
export const customerStatusConfigs = {
  ACTIVE: { label: "活跃客户", color: "bg-green-500", textColor: "text-green-50", icon: "✅" },
  INACTIVE: { label: "非活跃客户", color: "bg-gray-500", textColor: "text-gray-50", icon: "⏸️" },
  VIP: { label: "VIP客户", color: "bg-purple-500", textColor: "text-purple-50", icon: "⭐" },
  AT_RISK: { label: "流失风险客户", color: "bg-orange-500", textColor: "text-orange-50", icon: "⚠️" },
  LOST: { label: "已流失客户", color: "bg-red-500", textColor: "text-red-50", icon: "❌" },
  NEW: { label: "新客户", color: "bg-blue-500", textColor: "text-blue-50", icon: "🆕" },
};

// 服务优先级配置（Tailwind风格）
export const servicePriorityConfigs = {
  LOW: { label: "低优先级", color: "bg-gray-500", textColor: "text-gray-50", bg: "bg-gray-100", icon: "🔵" },
  MEDIUM: { label: "中优先级", color: "bg-blue-500", textColor: "text-blue-50", bg: "bg-blue-100", icon: "🟡" },
  HIGH: { label: "高优先级", color: "bg-orange-500", textColor: "text-orange-50", bg: "bg-orange-100", icon: "🟠" },
  URGENT: { label: "紧急", color: "bg-red-500", textColor: "text-red-50", bg: "bg-red-100", icon: "🔴" },
  CRITICAL: { label: "严重", color: "bg-red-700", textColor: "text-red-50", bg: "bg-red-200", icon: "🚨" },
};

// 服务类型配置（Tailwind风格）
export const serviceTypeConfigs = {
  TECHNICAL_SUPPORT: { label: "技术支持", color: "bg-blue-500", textColor: "text-blue-50", icon: "🔧" },
  CONSULTATION: { label: "咨询服务", color: "bg-green-500", textColor: "text-green-50", icon: "💬" },
  COMPLAINT: { label: "投诉处理", color: "bg-red-500", textColor: "text-red-50", icon: "📢" },
  REQUEST: { label: "服务请求", color: "bg-purple-500", textColor: "text-purple-50", icon: "📋" },
  MAINTENANCE: { label: "维护服务", color: "bg-orange-500", textColor: "text-orange-50", icon: "🔧" },
  TRAINING: { label: "培训服务", color: "bg-yellow-500", textColor: "text-yellow-50", icon: "🎓" },
  BILLING: { label: "账单咨询", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "💰" },
  OTHER: { label: "其他", color: "bg-gray-500", textColor: "text-gray-50", icon: "📦" },
};

// 满意度等级配置（Tailwind风格）
export const satisfactionLevelConfigs = {
  VERY_SATISFIED: { label: "非常满意", color: "bg-green-500", textColor: "text-green-50", score: 5, icon: "😊" },
  SATISFIED: { label: "满意", color: "bg-green-400", textColor: "text-green-50", score: 4, icon: "🙂" },
  NEUTRAL: { label: "一般", color: "bg-yellow-500", textColor: "text-yellow-50", score: 3, icon: "😐" },
  DISSATISFIED: { label: "不满意", color: "bg-orange-500", textColor: "text-orange-50", score: 2, icon: "😕" },
  VERY_DISSATFIED: { label: "非常不满意", color: "bg-red-500", textColor: "text-red-50", score: 1, icon: "😠" },
};

// 服务渠道配置（Tailwind风格）
export const serviceChannelConfigs = {
  PHONE: { label: "电话", color: "bg-blue-500", textColor: "text-blue-50", icon: "📞" },
  EMAIL: { label: "邮件", color: "bg-purple-500", textColor: "text-purple-50", icon: "📧" },
  LIVE_CHAT: { label: "在线客服", color: "bg-green-500", textColor: "text-green-50", icon: "💬" },
  WECHAT: { label: "微信", color: "bg-green-600", textColor: "text-green-50", icon: "💚" },
  TICKET: { label: "工单系统", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "🎫" },
  VISIT: { label: "现场服务", color: "bg-orange-500", textColor: "text-orange-50", icon: "🏢" },
};

// 服务状态配置（Tailwind风格）
export const serviceStatusConfigs = {
  NEW: { label: "新建", color: "bg-gray-500", textColor: "text-gray-50", icon: "🆕" },
  ASSIGNED: { label: "已分配", color: "bg-blue-500", textColor: "text-blue-50", icon: "👤" },
  IN_PROGRESS: { label: "处理中", color: "bg-yellow-500", textColor: "text-yellow-50", icon: "⚡" },
  AWAITING_RESPONSE: { label: "等待回复", color: "bg-orange-500", textColor: "text-orange-50", icon: "⏳" },
  RESOLVED: { label: "已解决", color: "bg-green-500", textColor: "text-green-50", icon: "✅" },
  CLOSED: { label: "已关闭", color: "bg-slate-500", textColor: "text-slate-50", icon: "🔒" },
  ESCALATED: { label: "已升级", color: "bg-red-500", textColor: "text-red-50", icon: "📢" },
};

// 客户服务指标配置
export const serviceMetricConfigs = {
  RESPONSE_TIME: { label: "首次响应时间", unit: "分钟", icon: "⏱️", target: "< 30" },
  RESOLUTION_TIME: { label: "平均解决时间", unit: "小时", icon: "🕐", target: "< 24" },
  SATISFACTION_RATE: { label: "客户满意度", unit: "%", icon: "⭐", target: "> 90" },
  FIRST_CONTACT_RESOLUTION: { label: "首次解决率", unit: "%", icon: "🎯", target: "> 75" },
  ESCALATION_RATE: { label: "升级率", unit: "%", icon: "📈", target: "< 5" },
  REPEAT_ISSUE_RATE: { label: "重复问题率", unit: "%", icon: "🔄", target: "< 10" },
};

// 客户服务Tab配置
export const customerServiceTabConfigs = [
  { value: "overview", label: "概览", icon: "📊" },
  { value: "tickets", label: "服务工单", icon: "🎫" },
  { value: "customers", label: "客户管理", icon: "👥" },
  { value: "reports", label: "服务报告", icon: "📈" },
  { value: "knowledge", label: "知识库", icon: "📚" },
  { value: "team", label: "团队管理", icon: "👨‍💼" },
  { value: "analytics", label: "数据分析", icon: "🔍" },
  { value: "settings", label: "系统设置", icon: "⚙️" },
];

// ==================== 统计计算函数 ====================

/**
 * 计算服务统计数据
 */
export const calculateServiceStats = (tickets = []) => {
  const total = tickets.length;
  const newTickets = tickets.filter(t => t.status === 'NEW').length;
  const assigned = tickets.filter(t => t.status === 'ASSIGNED').length;
  const inProgress = tickets.filter(t => t.status === 'IN_PROGRESS').length;
  const awaitingResponse = tickets.filter(t => t.status === 'AWAITING_RESPONSE').length;
  const resolved = tickets.filter(t => t.status === 'RESOLVED').length;
  const closed = tickets.filter(t => t.status === 'CLOSED').length;
  const escalated = tickets.filter(t => t.status === 'ESCALATED').length;

  // 按优先级统计
  const urgent = tickets.filter(t => t.priority === 'URGENT' || t.priority === 'CRITICAL').length;
  const high = tickets.filter(t => t.priority === 'HIGH').length;
  const medium = tickets.filter(t => t.priority === 'MEDIUM').length;
  const low = tickets.filter(t => t.priority === 'LOW').length;

  // 按满意度统计
  const satisfiedTickets = tickets.filter(t =>
    t.satisfaction === 'VERY_SATISFIED' || t.satisfaction === 'SATISFIED'
  ).length;
  const satisfactionRate = total > 0 ? Math.round((satisfiedTickets / total) * 100) : 0;

  // 计算平均解决时间
  const resolvedTickets = tickets.filter(t => t.resolutionTime);
  const avgResolutionTime = resolvedTickets.length > 0
    ? resolvedTickets.reduce((sum, t) => sum + t.resolutionTime, 0) / resolvedTickets.length
    : 0;

  // 升级率
  const escalationRate = total > 0 ? Math.round((escalated / total) * 100) : 0;

  return {
    total,
    new: newTickets,
    assigned,
    inProgress,
    awaitingResponse,
    resolved,
    closed,
    escalated,
    urgent,
    high,
    medium,
    low,
    satisfactionRate,
    avgResolutionTime: Math.round(avgResolutionTime),
    escalationRate,
  };
};

// ==================== 格式化函数 ====================

export const formatCustomerStatus = (status) => {
  return customerStatusConfigs[status]?.label || status;
};

export const formatServicePriority = (priority) => {
  return servicePriorityConfigs[priority]?.label || priority;
};

export const formatServiceType = (type) => {
  return serviceTypeConfigs[type]?.label || type;
};

export const formatSatisfactionLevel = (level) => {
  return satisfactionLevelConfigs[level]?.label || level;
};

export const formatServiceChannel = (channel) => {
  return serviceChannelConfigs[channel]?.label || channel;
};

export const formatServiceStatus = (status) => {
  return serviceStatusConfigs[status]?.label || status;
};

// ==================== 筛选函数 ====================

export const filterTicketsByStatus = (tickets, status) => {
  return tickets.filter(ticket => ticket.status === status);
};

export const filterTicketsByPriority = (tickets, priority) => {
  return tickets.filter(ticket => ticket.priority === priority);
};

export const filterTicketsByType = (tickets, type) => {
  return tickets.filter(ticket => ticket.type === type);
};

export const filterTicketsByCustomer = (tickets, customer) => {
  return tickets.filter(ticket =>
    ticket.customerName?.toLowerCase().includes(customer.toLowerCase()) ||
    ticket.customerId === customer
  );
};

// ==================== 排序函数 ====================

export const sortByPriority = (a, b) => {
  const priorityOrder = { CRITICAL: 0, URGENT: 1, HIGH: 2, MEDIUM: 3, LOW: 4 };
  const priorityA = priorityOrder[a.priority] || 5;
  const priorityB = priorityOrder[b.priority] || 5;
  return priorityA - priorityB;
};

export const sortByCreateTime = (a, b) => {
  return new Date(b.createTime) - new Date(a.createTime);
};

export const sortByResolutionTime = (a, b) => {
  return (a.resolutionTime || 0) - (b.resolutionTime || 0);
};

// ==================== 默认导出 ====================
export const SERVICE_DEFAULT = {
  // 基础配置
  SERVICE_TYPES,
  TICKET_STATUS,
  PRIORITY_LEVELS,
  SATISFACTION_LEVELS,
  SERVICE_PHASES,
  RESPONSE_CHANNELS,
  RESOLUTION_METHODS,
  WARRANTY_TYPES,
  PERFORMANCE_METRICS,
  ESCALATION_LEVELS,
  TABLE_CONFIG,
  CHART_COLORS,
  DEFAULT_FILTERS,
  // Tailwind风格配置
  customerStatusConfigs,
  servicePriorityConfigs,
  serviceTypeConfigs,
  satisfactionLevelConfigs,
  serviceChannelConfigs,
  serviceStatusConfigs,
  serviceMetricConfigs,
  customerServiceTabConfigs,
  // 函数
  calculateServiceStats,
  formatCustomerStatus,
  formatServicePriority,
  formatServiceType,
  formatSatisfactionLevel,
  formatServiceChannel,
  formatServiceStatus,
  filterTicketsByStatus,
  filterTicketsByPriority,
  filterTicketsByType,
  filterTicketsByCustomer,
  sortByPriority,
  sortByCreateTime,
  sortByResolutionTime,
};

export default SERVICE_DEFAULT;

// === Migrated from components/service/serviceTicketConstants.js ===
/**
 * Service Ticket Management Constants
 * 服务工单管理相关常量和配置
 */

// 工单状态配置
export const statusConfigs = {
  PENDING: {
    label: "待分配",
    color: "bg-slate-500",
    textColor: "text-slate-400",
    borderColor: "border-slate-500",
    icon: "🕐",
  },
  ASSIGNED: {
    label: "处理中",
    color: "bg-blue-500",
    textColor: "text-blue-400",
    borderColor: "border-blue-500",
    icon: "🔧",
  },
  IN_PROGRESS: {
    label: "处理中",
    color: "bg-blue-600",
    textColor: "text-blue-400",
    borderColor: "border-blue-600",
    icon: "⚙️",
  },
  PENDING_VERIFY: {
    label: "待验证",
    color: "bg-amber-500",
    textColor: "text-amber-400",
    borderColor: "border-amber-500",
    icon: "⏳",
  },
  CLOSED: {
    label: "已关闭",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
    borderColor: "border-emerald-500",
    icon: "✅",
  },
};

// 紧急程度配置
export const urgencyConfigs = {
  URGENT: {
    label: "紧急",
    color: "text-red-400",
    bg: "bg-red-500/20",
    borderColor: "border-red-500/30",
    level: 4,
    icon: "🚨",
  },
  HIGH: {
    label: "高",
    color: "text-orange-400",
    bg: "bg-orange-500/20",
    borderColor: "border-orange-500/30",
    level: 3,
    icon: "⚠️",
  },
  MEDIUM: {
    label: "中",
    color: "text-yellow-400",
    bg: "bg-yellow-500/20",
    borderColor: "border-yellow-500/30",
    level: 2,
    icon: "📋",
  },
  LOW: {
    label: "低",
    color: "text-blue-400",
    bg: "bg-blue-500/20",
    borderColor: "border-blue-500/30",
    level: 1,
    icon: "📝",
  },
  NORMAL: {
    label: "普通",
    color: "text-slate-400",
    bg: "bg-slate-500/20",
    borderColor: "border-slate-500/30",
    level: 1,
    icon: "📄",
  },
};

// 问题类型配置
export const problemTypeConfigs = {
  软件问题: {
    label: "软件问题",
    icon: "💻",
    color: "bg-blue-500",
    category: "技术问题",
    description: "系统软件、应用程序相关问题",
  },
  机械问题: {
    label: "机械问题",
    icon: "⚙️",
    color: "bg-orange-500",
    category: "技术问题",
    description: "设备机械部件故障或异常",
  },
  电气问题: {
    label: "电气问题",
    icon: "⚡",
    color: "bg-yellow-500",
    category: "技术问题",
    description: "电气系统、电路、电源问题",
  },
  操作问题: {
    label: "操作问题",
    icon: "👤",
    color: "bg-purple-500",
    category: "用户问题",
    description: "用户操作不当或培训问题",
  },
  安装问题: {
    label: "安装问题",
    icon: "🏗️",
    color: "bg-cyan-500",
    category: "安装调试",
    description: "设备安装、调试相关问题",
  },
  维护问题: {
    label: "维护问题",
    icon: "🔧",
    color: "bg-green-500",
    category: "安装调试",
    description: "设备维护、保养相关问题",
  },
  培训问题: {
    label: "培训问题",
    icon: "📚",
    color: "bg-indigo-500",
    category: "用户问题",
    description: "用户培训、知识传递问题",
  },
  配置问题: {
    label: "配置问题",
    icon: "⚙️",
    color: "bg-pink-500",
    category: "技术问题",
    description: "系统配置、参数设置问题",
  },
  网络问题: {
    label: "网络问题",
    icon: "🌐",
    color: "bg-teal-500",
    category: "技术问题",
    description: "网络连接、通信问题",
  },
  其他: {
    label: "其他",
    icon: "📋",
    color: "bg-slate-500",
    category: "其他",
    description: "其他未分类问题",
  },
};

// 排序选项配置
export const sortOptions = [
  { value: "reported_time", label: "报告时间" },
  { value: "status", label: "状态" },
  { value: "urgency", label: "紧急程度" },
  { value: "assigned_time", label: "分配时间" },
  { value: "closed_time", label: "关闭时间" },
];

// 筛选选项配置
export const filterOptions = {
  statuses: [
    { value: "ALL", label: "所有状态" },
    { value: "PENDING", label: "待分配" },
    { value: "ASSIGNED", label: "处理中" },
    { value: "IN_PROGRESS", label: "处理中" },
    { value: "PENDING_VERIFY", label: "待验证" },
    { value: "CLOSED", label: "已关闭" },
  ],
  urgencies: [
    { value: "ALL", label: "所有级别" },
    { value: "URGENT", label: "紧急" },
    { value: "HIGH", label: "高" },
    { value: "MEDIUM", label: "中" },
    { value: "LOW", label: "低" },
    { value: "NORMAL", label: "普通" },
  ],
  problemTypes: [
    { value: "ALL", label: "所有类型" },
    ...Object.keys(problemTypeConfigs).map(key => ({
      value: key,
      label: problemTypeConfigs[key].label,
      icon: problemTypeConfigs[key].icon,
      category: problemTypeConfigs[key].category
    }))
  ],
};

// 批量操作选项
export const batchOperations = [
  { 
    value: "batch_assign", 
    label: "批量分配", 
    icon: "User",
    description: "将选中的工单分配给工程师"
  },
  { 
    value: "batch_close", 
    label: "批量关闭", 
    icon: "CheckCircle2",
    description: "批量关闭已完成的工单"
  },
  { 
    value: "batch_escalate", 
    label: "批量升级", 
    icon: "AlertTriangle",
    description: "将紧急工单升级处理"
  },
  { 
    value: "batch_export", 
    label: "批量导出", 
    icon: "Download",
    description: "导出工单数据到Excel"
  },
];

// 默认表单数据
export const defaultTicketForm = {
  title: "",
  description: "",
  problem_type: "其他",
  urgency: "NORMAL",
  customer_id: null,
  contact_phone: "",
  contact_email: "",
  machine_id: null,
  project_id: null,
  location: "",
  attachments: [],
};

export const defaultAssignForm = {
  engineer_id: null,
  assigned_time: "",
  notes: "",
  estimated_hours: 0,
};

export const defaultCloseForm = {
  solution: "",
  satisfaction: 5,
  feedback: "",
  close_time: "",
  resolved_by: "",
};

// 工单状态流转规则
export const statusTransitions = {
  PENDING: ["ASSIGNED", "CLOSED"],
  ASSIGNED: ["IN_PROGRESS", "CLOSED"],
  IN_PROGRESS: ["PENDING_VERIFY", "CLOSED"],
  PENDING_VERIFY: ["CLOSED", "IN_PROGRESS"],
  CLOSED: [], // 终态
};

// 辅助函数
export const getStatusLabel = (status) => {
  return statusConfigs[status]?.label || status;
};

export const getStatusColor = (status) => {
  return statusConfigs[status]?.color || "bg-slate-500";
};

export const getUrgencyLabel = (urgency) => {
  return urgencyConfigs[urgency]?.label || urgency;
};

export const getUrgencyColor = (urgency) => {
  return urgencyConfigs[urgency]?.color || "text-slate-400";
};

export const getProblemTypeIcon = (type) => {
  return problemTypeConfigs[type]?.icon || "📋";
};

export const getProblemTypeColor = (type) => {
  return problemTypeConfigs[type]?.color || "bg-slate-500";
};

// 按类别分组问题类型
export const getProblemTypesByCategory = () => {
  const categories = {};
  Object.keys(problemTypeConfigs).forEach(key => {
    const config = problemTypeConfigs[key];
    if (!categories[config.category]) {
      categories[config.category] = [];
    }
    categories[config.category].push({
      value: key,
      label: config.label,
      icon: config.icon,
      color: config.color,
      description: config.description,
    });
  });
  return categories;
};

// 检查状态是否可以流转
export const canTransition = (fromStatus, toStatus) => {
  return statusTransitions[fromStatus]?.includes(toStatus) || false;
};

// 获取可操作的状态
export const getNextStatuses = (currentStatus) => {
  return statusTransitions[currentStatus] || [];
};

// 工单优先级排序权重
export const urgencyWeights = {
  URGENT: 4,
  HIGH: 3,
  MEDIUM: 2,
  LOW: 1,
  NORMAL: 1,
};

// 工单统计计算函数
export const calculateTicketStats = (tickets) => {
  const stats = {
    total: tickets.length,
    pending: 0,
    inProgress: 0,
    pendingVerify: 0,
    closed: 0,
    urgent: 0,
    high: 0,
    avgResolutionTime: 0,
    satisfactionScore: 0,
  };

  let totalResolutionTime = 0;
  let resolvedCount = 0;
  let totalSatisfaction = 0;
  let satisfactionCount = 0;

  tickets.forEach(ticket => {
    // 状态统计
    switch (ticket.status) {
      case "PENDING":
        stats.pending++;
        break;
      case "ASSIGNED":
      case "IN_PROGRESS":
        stats.inProgress++;
        break;
      case "PENDING_VERIFY":
        stats.pendingVerify++;
        break;
      case "CLOSED":
        stats.closed++;
        break;
    }

    // 紧急程度统计
    if (ticket.urgency === "URGENT") {stats.urgent++;}
    if (ticket.urgency === "HIGH") {stats.high++;}

    // 解决时间计算
    if (ticket.resolved_time && ticket.reported_time) {
      const resolved = new Date(ticket.resolved_time);
      const reported = new Date(ticket.reported_time);
      const hours = (resolved - reported) / (1000 * 60 * 60);
      totalResolutionTime += hours;
      resolvedCount++;
    }

    // 满意度计算
    if (ticket.satisfaction) {
      totalSatisfaction += ticket.satisfaction;
      satisfactionCount++;
    }
  });

  stats.avgResolutionTime = resolvedCount > 0 ? totalResolutionTime / resolvedCount : 0;
  stats.satisfactionScore = satisfactionCount > 0 ? totalSatisfaction / satisfactionCount : 0;

  return stats;
};

// ==================== 兼容导出（来自 serviceTicket/serviceTicketConstants）====================
// 以下为使用中文键名的配置，用于向后兼容

// 中文键名状态配置
export const statusConfig = {
 待分配: {
  label: "待分配",
 color: "bg-slate-500",
 textColor: "text-slate-400",
 value: "PENDING",
 },
 处理中: {
 label: "处理中",
 color: "bg-blue-500",
  textColor: "text-blue-400",
 value: "IN_PROGRESS",
 },
 待验证: {
 label: "待验证",
 color: "bg-amber-500",
  textColor: "text-amber-400",
 value: "PENDING_VERIFY",
 },
 已关闭: {
 label: "已关闭",
 color: "bg-emerald-500",
  textColor: "text-emerald-400",
 value: "CLOSED",
 },
};

// 中文键名紧急程度配置
export const urgencyConfig = {
 紧急: {
  label: "紧急",
  color: "text-red-400",
 bg: "bg-red-500/20",
 value: "URGENT",
 icon: "🔥",
 },
 高: {
 label: "高",
 color: "text-orange-400",
 bg: "bg-orange-500/20",
  value: "HIGH",
  icon: "⚠️",
 },
 中: {
  label: "中",
 color: "text-yellow-400",
 bg: "bg-yellow-500/20",
 value: "MEDIUM",
 icon: "📋",
 },
 低: {
 label: "低",
 color: "text-slate-400",
 bg: "bg-slate-500/20",
 value: "LOW",
  icon: "📝",
 },
 普通: {
 label: "普通",
  color: "text-slate-400",
 bg: "bg-slate-500/20",
 value: "NORMAL",
  icon: "📄",
 },
};

// 中文键名问题类型配置
export const problemTypeConfig = {
  软件问题: { label: "软件问题", icon: "💻", value: "SOFTWARE" },
  机械问题: { label: "机械问题", icon: "⚙️", value: "MECHANICAL" },
 电气问题: { label: "电气问题", icon: "⚡", value: "ELECTRICAL" },
 操作问题: { label: "操作问题", icon: "👤", value: "OPERATION" },
 其他: { label: "其他", icon: "📋", value: "OTHER" },
};

// 中文值筛选选项
export const legacyFilterOptions = {
 status: [
 { label: "全部状态", value: "ALL" },
 { label: "待分配", value: "待分配" },
 { label: "处理中", value: "处理中" },
 { label: "待验证", value: "待验证" },
  { label: "已关闭", value: "已关闭" },
  ],
 urgency: [
 { label: "全部紧急程度", value: "ALL" },
 { label: "紧急", value: "紧急" },
  { label: "高", value: "高" },
 { label: "中", value: "中" },
 { label: "低", value: "低" },
 { label: "普通", value: "普通" },
 ],
 problemType: [
 { label: "全部类型", value: "ALL" },
  { label: "软件问题", value: "软件问题" },
  { label: "机械问题", value: "机械问题" },
 { label: "电气问题", value: "电气问题" },
  { label: "操作问题", value: "操作问题" },
 { label: "其他", value: "其他" },
 ],
};

// 表单默认值
export const defaultFormData = {
 project_code: "",
 machine_no: "",
 customer_name: "",
 problem_type: "",
 problem_desc: "",
 urgency: "普通",
 reported_by: "",
 reported_phone: "",
 assigned_to: "",
};

// 关闭工单默认值
export const defaultCloseData = {
 solution: "",
 root_cause: "",
 preventive_action: "",
  satisfaction: "",
 feedback: "",
};

// 后端状态映射到前端
export const backendToFrontendStatus = {
 PENDING: "待分配",
 ASSIGNED: "处理中",
 IN_PROGRESS: "处理中",
 PENDING_VERIFY: "待验证",
 CLOSED: "已关闭",
};

// 前端状态映射到后端
export const frontendToBackendStatus = {
 待分配: "PENDING",
 处理中: "IN_PROGRESS",
 待验证: "PENDING_VERIFY",
 已关闭: "CLOSED",
};

// 后端紧急程度映射到前端
export const backendToFrontendUrgency = {
 URGENT: "紧急",
 HIGH: "高",
 MEDIUM: "中",
 LOW: "低",
};

// 前端紧急程度映射到后端
export const frontendToBackendUrgency = {
 紧急: "URGENT",
 高: "HIGH",
 中: "MEDIUM",
 低: "LOW",
 普通: "NORMAL",
};

// 状态映射辅助函数
export const mapBackendStatus = (backendStatus) => {
  return backendToFrontendStatus[backendStatus] || backendStatus;
};

export const mapBackendUrgency = (backendUrgency) => {
 return backendToFrontendUrgency[backendUrgency] || backendUrgency;
};

export const mapFrontendStatus = (frontendStatus) => {
 return frontendToBackendStatus[frontendStatus] || frontendStatus;
};

export const mapFrontendUrgency = (frontendUrgency) => {
 return frontendToBackendUrgency[frontendUrgency] || frontendUrgency;
};

// 状态排序权重
export const statusOrderWeight = {
 待分配: 1,
 处理中: 2,
 待验证: 3,
 已关闭: 4,
};

// 紧急程度排序权重
export const urgencyOrderWeight = {
 紧急: 1,
 高: 2,
 中: 3,
 低: 4,
 普通: 5,
};

// 快捷键配置
export const keyboardShortcuts = {
 closeDialog: "Escape",
 focusSearch: "CmdOrCtrl + K",
 refresh: "F5",
};

// JSX 徽章函数（注意：需要在 JSX 环境中使用）
export const getStatusBadge = (status) => {
 const config = statusConfig[status];
  if (!config) {return status;}
 return `${config.label}`;
};

export const getUrgencyBadge = (urgency) => {
  const config = urgencyConfig[urgency];
 if (!config) {return urgency;}
 return `${config.icon} ${config.label}`;
};

export const getProblemTypeBadge = (problemType) => {
 const config = problemTypeConfig[problemType];
 if (!config) {return problemType;}
 return `${config.icon} ${config.label}`;
};

// 默认导出
export const SERVICE_TICKET_DEFAULT = {
 statusConfigs,
 urgencyConfigs,
 problemTypeConfigs,
 sortOptions,
 filterOptions,
 batchOperations,
 defaultTicketForm,
 defaultAssignForm,
 defaultCloseForm,
 statusTransitions,
 getStatusLabel,
 getStatusColor,
  getUrgencyLabel,
 getUrgencyColor,
 getProblemTypeIcon,
 getProblemTypeColor,
 getProblemTypesByCategory,
 canTransition,
  getNextStatuses,
 urgencyWeights,
 calculateTicketStats,
 // 兼容导出
 statusConfig,
 urgencyConfig,
 problemTypeConfig,
 legacyFilterOptions,
 defaultFormData,
  defaultCloseData,
 backendToFrontendStatus,
 frontendToBackendStatus,
 backendToFrontendUrgency,
 frontendToBackendUrgency,
  mapBackendStatus,
 mapBackendUrgency,
 mapFrontendStatus,
 mapFrontendUrgency,
 statusOrderWeight,
 urgencyOrderWeight,
 keyboardShortcuts,
 getStatusBadge,
 getUrgencyBadge,
 getProblemTypeBadge,
};

// === Migrated from components/delivery-management/deliveryConstants.js ===
/**
 * Delivery Management Configuration Constants
 * 配送管理配置常量
 * 物流配送任务管理配置常量
 *
 * This is the main delivery constants file.
 * deliveryManagementConstants.js re-exports from this file.
 */

// 配送状态配置
export const deliveryStatusConfigs = {
 PENDING: { label: "待配送", color: "bg-slate-500", textColor: "text-slate-50", icon: "📦" },
 PICKED_UP: { label: "已取货", color: "bg-blue-500", textColor: "text-blue-50", icon: "🚚" },
 IN_TRANSIT: { label: "运输中", color: "bg-orange-500", textColor: "text-orange-50", icon: "🛣️" },
 DELIVERED: { label: "已送达", color: "bg-green-500", textColor: "text-green-50", icon: "✅" },
 DELIVER_FAILED: { label: "配送失败", color: "bg-red-500", textColor: "text-red-50", icon: "❌" },
 RETURNED: { label: "已退回", color: "bg-gray-500", textColor: "text-gray-50", icon: "↩️" },
 CANCELLED: { label: "已取消", color: "bg-gray-500", textColor: "text-gray-50", icon: "🚫" },
};

// 配送优先级配置
export const deliveryPriorityConfigs = {
 LOW: { label: "低", color: "bg-slate-500", textColor: "text-slate-50", value: 1 },
 NORMAL: { label: "普通", color: "bg-blue-500", textColor: "text-blue-50", value: 2 },
 HIGH: { label: "高", color: "bg-orange-500", textColor: "text-orange-50", value: 3 },
 URGENT: { label: "紧急", color: "bg-red-500", textColor: "text-red-50", value: 4 },
 EXPRESS: { label: "特急", color: "bg-purple-500", textColor: "text-purple-50", value: 5 },
};

// 配送方式配置
export const deliveryMethodConfigs = {
  SELF_PICKUP: { label: "自提", color: "bg-blue-500", textColor: "text-blue-50", icon: "🏢" },
 STANDARD_DELIVERY: { label: "标准配送", color: "bg-green-500", textColor: "text-green-50", icon: "🚚" },
 EXPRESS_DELIVERY: { label: "快递配送", color: "bg-orange-500", textColor: "text-orange-50", icon: "🏃" },
 SPECIAL_DELIVERY: { label: "专车配送", color: "bg-purple-500", textColor: "text-purple-50", icon: "🚗" },
 OVERNIGHT: { label: "隔夜达", color: "bg-red-500", textColor: "text-red-50", icon: "🌙" },
};

// 配送类型配置
export const deliveryTypeConfigs = {
 NORMAL: { label: "常规配送", color: "bg-blue-500", textColor: "text-blue-50" },
 RETURN: { label: "退货配送", color: "bg-orange-500", textColor: "text-orange-50" },
 EXCHANGE: { label: "换货配送", color: "bg-purple-500", textColor: "text-purple-50" },
 REPLACEMENT: { label: "补货配送", color: "bg-green-500", textColor: "text-green-50" },
 SAMPLE: { label: "样品配送", color: "bg-amber-500", textColor: "text-amber-50" },
  URGENT: { label: "紧急配送", color: "bg-red-500", textColor: "text-red-50" },
};

// 配送阶段配置
export const deliveryStageConfigs = {
 PREPARING: { label: "备货中", color: "bg-slate-500", textColor: "text-slate-50" },
 READY: { label: "已备货", color: "bg-blue-500", textColor: "text-blue-50" },
  DISPATCHED: { label: "已调度", color: "bg-orange-500", textColor: "text-orange-50" },
  LOADING: { label: "装车中", color: "bg-amber-500", textColor: "text-amber-50" },
 TRANSPORTING: { label: "运输中", color: "bg-purple-500", textColor: "text-purple-50" },
 UNLOADING: { label: "卸货中", color: "bg-indigo-500", textColor: "text-indigo-50" },
 COMPLETED: { label: "已完成", color: "bg-green-500", textColor: "text-green-50" },
 FAILED: { label: "已失败", color: "bg-red-500", textColor: "text-red-50" },
};

// 配送车辆状态配置
export const vehicleStatusConfigs = {
 AVAILABLE: { label: "可用", color: "bg-green-500", textColor: "text-green-50" },
 IN_USE: { label: "使用中", color: "bg-blue-500", textColor: "text-blue-50" },
 MAINTENANCE: { label: "维护中", color: "bg-orange-500", textColor: "text-orange-50" },
 REPAIRING: { label: "维修中", color: "bg-red-500", textColor: "text-red-50" },
 OFFLINE: { label: "离线", color: "bg-gray-500", textColor: "text-gray-50" },
};

// 配送司机状态配置
export const driverStatusConfigs = {
 ONLINE: { label: "在线", color: "bg-green-500", textColor: "text-green-50" },
 BUSY: { label: "忙碌", color: "bg-orange-500", textColor: "text-orange-50" },
 OFFLINE: { label: "离线", color: "bg-gray-500", textColor: "text-gray-50" },
 BREAK: { label: "休息", color: "bg-blue-500", textColor: "text-blue-50" },
};

// 配送异常类型配置
export const exceptionTypeConfigs = {
 DELAY: { label: "延迟", color: "bg-orange-500", textColor: "text-orange-50", icon: "⏰" },
 DAMAGE: { label: "损坏", color: "bg-red-500", textColor: "text-red-50", icon: "💥" },
 LOSS: { label: "丢失", color: "bg-red-500", textColor: "text-red-50", icon: "❓" },
 WRONG_ADDRESS: { label: "地址错误", color: "bg-orange-500", textColor: "text-orange-50", icon: "📍" },
 CUSTOMER_UNAVAILABLE: { label: "客户不在", color: "bg-orange-500", textColor: "text-orange-50", icon: "👤" },
 VEHICLE_ISSUE: { label: "车辆问题", color: "bg-red-500", textColor: "text-red-50", icon: "🚗" },
 DRIVER_ISSUE: { label: "司机问题", color: "bg-red-500", textColor: "text-red-50", icon: "🚙" },
  WEATHER: { label: "天气原因", color: "bg-blue-500", textColor: "text-blue-50", icon: "🌧️" },
 TRAFFIC: { label: "交通拥堵", color: "bg-orange-500", textColor: "text-orange-50", icon: "🚦" },
};

// 配送统计类型配置
export const statsTypeConfigs = {
 TOTAL_DELIVERIES: { label: "总配送量", color: "bg-blue-500", textColor: "text-blue-50" },
 SUCCESS_RATE: { label: "成功率", color: "bg-green-500", textColor: "text-green-50" },
 AVG_DELIVERY_TIME: { label: "平均配送时间", color: "bg-amber-500", textColor: "text-amber-50" },
 ON_TIME_RATE: { label: "准时率", color: "bg-purple-500", textColor: "text-purple-50" },
 DELAYED_DELIVERIES: { label: "延迟配送", color: "bg-orange-500", textColor: "text-orange-50" },
 FAILED_DELIVERIES: { label: "失败配送", color: "bg-red-500", textColor: "text-red-50" },
 CUSTOMER_SATISFACTION: { label: "客户满意度", color: "bg-cyan-500", textColor: "text-cyan-50" },
 VEHICLE_UTILIZATION: { label: "车辆利用率", color: "bg-indigo-500", textColor: "text-indigo-50" },
};

// 导出类型配置
export const exportTypeConfigs = {
 CSV: { label: "CSV", color: "bg-green-500", textColor: "text-green-50", icon: "📊" },
 EXCEL: { label: "Excel", color: "bg-blue-500", textColor: "text-blue-50", icon: "📈" },
 PDF: { label: "PDF", color: "bg-red-500", textColor: "text-red-50", icon: "📄" },
 JSON: { label: "JSON", color: "bg-purple-500", textColor: "text-purple-50", icon: "🔧" },
};

// 时间配置
export const timeSlotConfigs = {
 MORNING: { label: "上午 (08:00-12:00)", color: "bg-blue-500", textColor: "text-blue-50" },
 AFTERNOON: { label: "下午 (13:00-17:00)", color: "bg-green-500", textColor: "text-green-50" },
 EVENING: { label: "傍晚 (17:00-20:00)", color: "bg-orange-500", textColor: "text-orange-50" },
 NIGHT: { label: "夜间 (20:00-23:00)", color: "bg-purple-500", textColor: "text-purple-50" },
 ANYTIME: { label: "全天", color: "bg-slate-500", textColor: "text-slate-50" },
};

// Tab 配置
export const tabConfigs = [
 { value: "overview", label: "配送总览", icon: "📊" },
 { value: "tasks", label: "配送任务", icon: "📦" },
 { value: "vehicles", label: "车辆管理", icon: "🚚" },
 { value: "drivers", label: "司机管理", icon: "👨‍💼" },
 { value: "routes", label: "路径优化", icon: "🛣️" },
 { value: "tracking", label: "实时追踪", icon: "📍" },
 { value: "analytics", label: "数据分析", icon: "📈" },
  { value: "exceptions", label: "异常处理", icon: "⚠️" },
];

// 工具函数
export const getStatusConfig = (status) => {
 return deliveryStatusConfigs[status] || deliveryStatusConfigs.PENDING;
};

export const getPriorityConfig = (priority) => {
 return deliveryPriorityConfigs[priority] || deliveryPriorityConfigs.NORMAL;
};

export const getMethodConfig = (method) => {
 return deliveryMethodConfigs[method] || deliveryMethodConfigs.STANDARD_DELIVERY;
};

export const getTypeConfig = (type) => {
 return deliveryTypeConfigs[type] || deliveryTypeConfigs.NORMAL;
};

export const getStageConfig = (stage) => {
 return deliveryStageConfigs[stage] || deliveryStageConfigs.PREPARING;
};

export const getVehicleStatusConfig = (status) => {
 return vehicleStatusConfigs[status] || vehicleStatusConfigs.OFFLINE;
};

export const getDriverStatusConfig = (status) => {
 return driverStatusConfigs[status] || driverStatusConfigs.OFFLINE;
};

export const getExceptionConfig = (type) => {
 return exceptionTypeConfigs[type] || exceptionTypeConfigs.DELAY;
};

export const getStatsConfig = (type) => {
 return statsTypeConfigs[type] || statsTypeConfigs.TOTAL_DELIVERIES;
};

export const getTimeSlotConfig = (slot) => {
 return timeSlotConfigs[slot] || timeSlotConfigs.ANYTIME;
};

export const formatStatus = (status) => {
  return getStatusConfig(status).label;
};

export const formatPriority = (priority) => {
 return getPriorityConfig(priority).label;
};

export const formatMethod = (method) => {
 return getMethodConfig(method).label;
};

export const formatType = (type) => {
 return getTypeConfig(type).label;
};

export const formatStage = (stage) => {
 return getStageConfig(stage).label;
};

export const getPriorityValue = (item) => {
 if (!item.priority) {return 0;}
 return getPriorityConfig(item.priority).value;
};

// 排序函数
export const sortByDeliveryPriority = (a, b) => {
 return getPriorityValue(b) - getPriorityValue(a);
};

export const sortByStatus = (a, b) => {
 const statusOrder = ['PENDING', 'PICKED_UP', 'IN_TRANSIT', 'DELIVERED', 'DELIVER_FAILED', 'RETURNED', 'CANCELLED'];
 const aIndex = statusOrder.indexOf(a.status);
  const bIndex = statusOrder.indexOf(b.status);
  return aIndex - bIndex;
};

export const sortByDeliveryTime = (a, b) => {
 const aTime = a.planned_delivery_time || a.created_at;
 const bTime = b.planned_delivery_time || b.created_at;
 return new Date(bTime) - new Date(aTime);
};

// 验证函数
export const isValidStatus = (status) => {
 return Object.keys(deliveryStatusConfigs).includes(status);
};

export const isValidPriority = (priority) => {
 return Object.keys(deliveryPriorityConfigs).includes(priority);
};

export const isValidMethod = (method) => {
 return Object.keys(deliveryMethodConfigs).includes(method);
};

export const isValidType = (type) => {
 return Object.keys(deliveryTypeConfigs).includes(type);
};

export const isValidStage = (stage) => {
 return Object.keys(deliveryStageConfigs).includes(stage);
};

// 过滤函数
export const filterByStatus = (items, status) => {
 return items.filter(item => item.status === status);
};

export const filterByPriority = (items, priority) => {
 return items.filter(item => item.priority === priority);
};

export const filterByMethod = (items, method) => {
 return items.filter(item => item.delivery_method === method);
};

export const filterByType = (items, type) => {
 return items.filter(item => item.delivery_type === type);
};

export const filterByDate = (items, startDate, endDate) => {
 return items.filter(item => {
 const deliveryDate = new Date(item.planned_delivery_time || item.created_at);
 return deliveryDate >= startDate && deliveryDate <= endDate;
 });
};

// ==================== 兼容导出（来自 deliveryManagementConstants）====================

export const DELIVERY_STATUS = {
  PENDING: { value: 'pending', label: '待发货', color: '#faad14' },
 PREPARING: { value: 'preparing', label: '准备中', color: '#1890ff' },
  SHIPPED: { value: 'shipped', label: '已发货', color: '#722ed1' },
 IN_TRANSIT: { value: 'in_transit', label: '在途', color: '#13c2c2' },
  DELIVERED: { value: 'delivered', label: '已送达', color: '#52c41a' },
 CANCELLED: { value: 'cancelled', label: '已取消', color: '#ff4d4f' }
};

export const DELIVERY_PRIORITY = {
 URGENT: { value: 'urgent', label: '紧急', color: '#ff4d4f' },
 HIGH: { value: 'high', label: '高', color: '#fa8c16' },
  NORMAL: { value: 'normal', label: '普通', color: '#1890ff' },
 LOW: { value: 'low', label: '低', color: '#52c41a' }
};

export const SHIPPING_METHODS = {
 EXPRESS: { value: 'express', label: '快递', days: '1-3天' },
 STANDARD: { value: 'standard', label: '标准物流', days: '3-7天' },
  FREIGHT: { value: 'freight', label: '货运', days: '7-15天' },
 SELF_PICKUP: { value: 'self_pickup', label: '自提', days: '0天' }
};

export const PACKAGE_TYPES = {
 STANDARD: { value: 'standard', label: '标准包装' },
 FRAGILE: { value: 'fragile', label: '易碎品包装' },
 LIQUID: { value: 'liquid', label: '液体包装' },
 OVERSIZE: { value: 'oversize', label: '超大件包装' }
};

export const DELIVERY_DEFAULT = {
 deliveryStatusConfigs,
 deliveryPriorityConfigs,
 deliveryMethodConfigs,
 deliveryTypeConfigs,
 deliveryStageConfigs,
 vehicleStatusConfigs,
 driverStatusConfigs,
 exceptionTypeConfigs,
 statsTypeConfigs,
 exportTypeConfigs,
  timeSlotConfigs,
 tabConfigs,
 getStatusConfig,
 getPriorityConfig,
 getMethodConfig,
 getTypeConfig,
  getStageConfig,
 getVehicleStatusConfig,
 getDriverStatusConfig,
 getExceptionConfig,
 getStatsConfig,
 getTimeSlotConfig,
 formatStatus,
 formatPriority,
 formatMethod,
 formatType,
  formatStage,
  getPriorityValue,
 sortByDeliveryPriority,
 sortByPriority: sortByDeliveryPriority,
 sortByStatus,
  sortByDeliveryTime,
 isValidStatus,
 isValidPriority,
  isValidMethod,
 isValidType,
 isValidStage,
 filterByStatus,
 filterByPriority,
 filterByMethod,
 filterByType,
 filterByDate,
 // 兼容导出
  DELIVERY_STATUS,
 DELIVERY_PRIORITY,
 SHIPPING_METHODS,
 PACKAGE_TYPES,
};
