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
