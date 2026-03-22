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
