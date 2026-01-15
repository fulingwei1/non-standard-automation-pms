/**
 * Customer Service Configuration Constants
 * 客户服务配置常量
 */

// 客户状态配置
export const customerStatusConfigs = {
  ACTIVE: { label: "活跃客户", color: "bg-green-500", textColor: "text-green-50", icon: "✅" },
  INACTIVE: { label: "非活跃客户", color: "bg-gray-500", textColor: "text-gray-50", icon: "⏸️" },
  VIP: { label: "VIP客户", color: "bg-purple-500", textColor: "text-purple-50", icon: "⭐" },
  AT_RISK: { label: "流失风险客户", color: "bg-orange-500", textColor: "text-orange-50", icon: "⚠️" },
  LOST: { label: "已流失客户", color: "bg-red-500", textColor: "text-red-50", icon: "❌" },
  NEW: { label: "新客户", color: "bg-blue-500", textColor: "text-blue-50", icon: "🆕" },
};

// 服务优先级配置
export const servicePriorityConfigs = {
  LOW: { label: "低优先级", color: "bg-gray-500", textColor: "text-gray-50", bg: "bg-gray-100", icon: "🔵" },
  MEDIUM: { label: "中优先级", color: "bg-blue-500", textColor: "text-blue-50", bg: "bg-blue-100", icon: "🟡" },
  HIGH: { label: "高优先级", color: "bg-orange-500", textColor: "text-orange-50", bg: "bg-orange-100", icon: "🟠" },
  URGENT: { label: "紧急", color: "bg-red-500", textColor: "text-red-50", bg: "bg-red-100", icon: "🔴" },
  CRITICAL: { label: "严重", color: "bg-red-700", textColor: "text-red-50", bg: "bg-red-200", icon: "🚨" },
};

// 服务类型配置
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

// 服务满意度配置
export const satisfactionLevelConfigs = {
  VERY_SATISFIED: { label: "非常满意", color: "bg-green-500", textColor: "text-green-50", score: 5, icon: "😊" },
  SATISFIED: { label: "满意", color: "bg-green-400", textColor: "text-green-50", score: 4, icon: "🙂" },
  NEUTRAL: { label: "一般", color: "bg-yellow-500", textColor: "text-yellow-50", score: 3, icon: "😐" },
  DISSATISFIED: { label: "不满意", color: "bg-orange-500", textColor: "text-orange-50", score: 2, icon: "😕" },
  VERY_DISSATFIED: { label: "非常不满意", color: "bg-red-500", textColor: "text-red-50", score: 1, icon: "😠" },
};

// 服务渠道配置
export const serviceChannelConfigs = {
  PHONE: { label: "电话", color: "bg-blue-500", textColor: "text-blue-50", icon: "📞" },
  EMAIL: { label: "邮件", color: "bg-purple-500", textColor: "text-purple-50", icon: "📧" },
  LIVE_CHAT: { label: "在线客服", color: "bg-green-500", textColor: "text-green-50", icon: "💬" },
  WECHAT: { label: "微信", color: "bg-green-600", textColor: "text-green-50", icon: "💚" },
  TICKET: { label: "工单系统", color: "bg-indigo-500", textColor: "text-indigo-50", icon: "🎫" },
  VISIT: { label: "现场服务", color: "bg-orange-500", textColor: "text-orange-50", icon: "🏢" },
};

// 服务状态配置
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

// 统计计算函数
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

  // 按满意度统计（假设数据中有satisfaction字段）
  const satisfiedTickets = tickets.filter(t =>
    t.satisfaction === 'VERY_SATISFIED' || t.satisfaction === 'SATISFIED'
  ).length;
  const satisfactionRate = total > 0 ? Math.round((satisfiedTickets / total) * 100) : 0;

  // 计算平均解决时间（假设数据中有resolutionTime字段，单位为小时）
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

// 格式化函数
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

// 过滤函数
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

// 排序函数
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

// 默认导出
export default {
  customerStatusConfigs,
  servicePriorityConfigs,
  serviceTypeConfigs,
  satisfactionLevelConfigs,
  serviceChannelConfigs,
  serviceStatusConfigs,
  serviceMetricConfigs,
  customerServiceTabConfigs,
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