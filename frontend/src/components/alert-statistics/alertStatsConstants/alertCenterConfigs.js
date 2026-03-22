/**
 * 预警中心配置 - Alert Center Configs
 * 包含预警级别、状态、类型、规则、通知、优先级等配置
 */

// ==================== 预警级别配置 ====================
export const ALERT_LEVELS = {
 CRITICAL: {
 label: "严重",
 level: 5,
  color: "bg-red-500",
 icon: "AlertTriangle",
 bgColor: "bg-red-500/10",
 borderColor: "border-red-500/30",
  textColor: "text-red-400",
  urgency: "immediate",
  autoEscalate: true,
 notificationSound: "critical",
 visualPriority: "highest"
 },
 HIGH: {
 label: "高",
 level: 4,
 color: "bg-orange-500",
  icon: "AlertCircle",
 bgColor: "bg-orange-500/10",
 borderColor: "border-orange-500/30",
  textColor: "text-orange-400",
 urgency: "urgent",
  autoEscalate: true,
 notificationSound: "high",
 visualPriority: "high"
 },
 MEDIUM: {
 label: "中",
  level: 3,
  color: "bg-amber-500",
  icon: "AlertCircle",
  bgColor: "bg-amber-500/10",
 borderColor: "border-amber-500/30",
 textColor: "text-amber-400",
 urgency: "normal",
 autoEscalate: false,
 notificationSound: "medium",
 visualPriority: "medium"
 },
 LOW: {
 label: "低",
  level: 2,
 color: "bg-blue-500",
  icon: "Info",
 bgColor: "bg-blue-500/10",
  borderColor: "border-blue-500/30",
  textColor: "text-blue-400",
  urgency: "low",
 autoEscalate: false,
 notificationSound: "low",
 visualPriority: "low"
 },
 INFO: {
 label: "信息",
 level: 1,
 color: "bg-gray-500",
 icon: "Info",
  bgColor: "bg-gray-500/10",
 borderColor: "border-gray-500/30",
 textColor: "text-gray-400",
 urgency: "info",
  autoEscalate: false,
 notificationSound: "info",
 visualPriority: "info"
 }
};

// ==================== 预警状态配置 ====================
export const ALERT_STATUS = {
 PENDING: {
 label: "待处理",
 color: "bg-amber-500",
  icon: "Clock",
 description: "新产生的预警，等待处理",
 nextActions: ["确认", "分配", "忽略"],
 canEdit: true,
 canDelete: true
 },
 ACKNOWLEDGED: {
  label: "已确认",
  color: "bg-blue-500",
 icon: "CheckCircle2",
 description: "预警已被确认，正在处理中",
  nextActions: ["分配", "处理", "升级"],
  canEdit: true,
  canDelete: false
 },
 ASSIGNED: {
 label: "已分配",
  color: "bg-purple-500",
 icon: "User",
  description: "预警已分配给具体处理人",
 nextActions: ["处理", "重新分配", "升级"],
  canEdit: true,
 canDelete: false
  },
 IN_PROGRESS: {
  label: "处理中",
 color: "bg-indigo-500",
 icon: "RefreshCw",
  description: "预警正在处理过程中",
 nextActions: ["暂停", "解决", "升级"],
 canEdit: true,
 canDelete: false
 },
 RESOLVED: {
  label: "已解决",
 color: "bg-emerald-500",
  icon: "CheckCircle2",
 description: "预警问题已解决",
 nextActions: ["验证", "关闭", "重新打开"],
 canEdit: false,
 canDelete: false
 },
  CLOSED: {
 label: "已关闭",
 color: "bg-slate-500",
  icon: "XCircle",
 description: "预警已关闭处理流程",
 nextActions: ["重新打开"],
  canEdit: false,
 canDelete: true
  },
 IGNORED: {
 label: "已忽略",
 color: "bg-gray-500",
 icon: "X",
  description: "预警被忽略，不进行处理",
  nextActions: ["重新考虑"],
 canEdit: true,
 canDelete: true
 }
};

// ==================== 预警类型配置 ====================
export const ALERT_TYPES = {
 PROJECT: {
 label: "项目预警",
  category: "项目管理",
  icon: "FolderOpen",
 subtypes: {
  DELAY: { label: "进度延期", severity: "HIGH" },
  BUDGET: { label: "预算超支", severity: "CRITICAL" },
 MILESTONE: { label: "里程碑逾期", severity: "HIGH" },
   RESOURCE: { label: "资源不足", severity: "MEDIUM" },
  QUALITY: { label: "质量风险", severity: "MEDIUM" }
 }
 },
 SYSTEM: {
 label: "系统预警",
  category: "系统监控",
 icon: "Monitor",
  subtypes: {
  PERFORMANCE: { label: "性能异常", severity: "HIGH" },
 SECURITY: { label: "安全威胁", severity: "CRITICAL" },
  CAPACITY: { label: "容量不足", severity: "MEDIUM" },
  BACKUP: { label: "备份失败", severity: "HIGH" },
  CONNECTIVITY: { label: "连接中断", severity: "CRITICAL" }
 }
 },
 BUSINESS: {
  label: "业务预警",
 category: "业务监控",
  icon: "TrendingUp",
 subtypes: {
  SALES: { label: "销售下滑", severity: "MEDIUM" },
   INVENTORY: { label: "库存异常", severity: "HIGH" },
 CUSTOMER: { label: "客户投诉", severity: "HIGH" },
  FINANCIAL: { label: "财务异常", severity: "CRITICAL" },
  COMPLIANCE: { label: "合规风险", severity: "MEDIUM" }
  }
 },
 OPERATION: {
 label: "运营预警",
  category: "运营管理",
 icon: "Settings",
 subtypes: {
 EQUIPMENT: { label: "设备故障", severity: "HIGH" },
 MAINTENANCE: { label: "维护超期", severity: "MEDIUM" },
 SAFETY: { label: "安全事故", severity: "CRITICAL" },
  COMPLAINT: { label: "客诉激增", severity: "HIGH" },
  STAFF: { label: "人员异常", severity: "MEDIUM" }
 }
 },
 QUALITY: {
  label: "质量预警",
 category: "质量管理",
 icon: "Shield",
  subtypes: {
  DEFECT: { label: "质量缺陷", severity: "HIGH" },
 INSPECTION: { label: "检验失败", severity: "MEDIUM" },
  CERTIFICATION: { label: "认证问题", severity: "MEDIUM" },
 RECALL: { label: "产品召回", severity: "CRITICAL" },
  COMPLIANCE: { label: "标准违规", severity: "HIGH" }
  }
  }
};

// ==================== 预警规则配置 ====================
export const ALERT_RULES = {
 THRESHOLD: {
 label: "阈值规则",
 description: "基于数值阈值触发的规则",
 conditions: ["大于", "小于", "等于", "不等于", "区间"],
 applicableTypes: ["SYSTEM", "BUSINESS", "QUALITY"],
  examples: [
  "CPU使用率 > 80%",
  "库存量 < 安全库存",
  "缺陷率 > 5%"
 ]
 },
 TIME_BASED: {
  label: "时间规则",
  description: "基于时间条件触发的规则",
  conditions: ["超时", "临近", "定时", "周期性"],
 applicableTypes: ["PROJECT", "OPERATION"],
 examples: [
 "任务超时2小时",
 "维护到期前3天提醒",
  "每日数据备份检查"
 ]
  },
 PATTERN: {
 label: "模式规则",
 description: "基于数据模式匹配的规则",
 conditions: ["趋势变化", "异常波动", "重复模式", "关联检测"],
  applicableTypes: ["BUSINESS", "QUALITY"],
 examples: [
 "销售连续3天下降",
 "质量数据异常波动",
 "系统错误重复出现"
 ]
  },
 COMPOSITE: {
 label: "复合规则",
 description: "多条件组合的复杂规则",
 conditions: ["与", "或", "非", "条件组合"],
 applicableTypes: ["ALL"],
 examples: [
  "CPU > 80% 且 内存 > 90%",
  "预算超支 或 进度延期"
  ]
 }
};

// ==================== 通知方式配置 ====================
export const NOTIFICATION_CHANNELS = {
 EMAIL: {
 label: "邮件通知",
 icon: "Mail",
 enabled: true,
  configurable: true,
 deliveryTime: "instant",
 supports: ["text", "html", "attachments"],
 priority: ["low", "normal", "high", "urgent"]
 },
 SMS: {
  label: "短信通知",
  icon: "MessageSquare",
 enabled: true,
 configurable: true,
 deliveryTime: "instant",
  supports: ["text"],
  maxLength: 160,
  priority: ["normal", "urgent"]
  },
 WEBHOOK: {
 label: "Webhook通知",
  icon: "Link",
 enabled: false,
 configurable: true,
 deliveryTime: "instant",
 supports: ["json", "xml"],
  requires: ["url", "authentication"]
 },
  PUSH: {
  label: "推送通知",
  icon: "Bell",
 enabled: true,
 configurable: true,
  deliveryTime: "instant",
 supports: ["title", "body", "actions"],
  platforms: ["web", "mobile", "desktop"]
 },
 VOICE: {
 label: "语音通知",
 icon: "Phone",
  enabled: false,
 configurable: true,
  deliveryTime: "instant",
  supports: ["text_to_speech"],
  requires: ["phone_number"]
  },
 SYSTEM: {
  label: "系统通知",
  icon: "MonitorSpeaker",
  enabled: true,
  configurable: false,
 deliveryTime: "instant",
 supports: ["desktop", "sound", "visual"]
 }
};

// ==================== 预警优先级配置 ====================
export const ALERT_PRIORITY = {
 IMMEDIATE: {
 label: "立即处理",
  level: 1,
 responseTime: "5分钟内",
  escalationTime: "15分钟",
 autoEscalate: true,
 notifyLevel: ["CRITICAL", "HIGH"],
 allowedActions: ["立即处理", "紧急上报", "系统干预"]
 },
 URGENT: {
 label: "紧急处理",
 level: 2,
  responseTime: "30分钟内",
 escalationTime: "2小时",
  autoEscalate: true,
  notifyLevel: ["CRITICAL", "HIGH"],
 allowedActions: ["立即处理", "协调资源", "升级上报"]
 },
  HIGH: {
 label: "高优先级",
 level: 3,
 responseTime: "2小时内",
  escalationTime: "8小时",
 autoEscalate: false,
 notifyLevel: ["HIGH", "MEDIUM"],
 allowedActions: ["计划处理", "资源协调", "监控跟踪"]
 },
 NORMAL: {
 label: "普通优先级",
 level: 4,
  responseTime: "8小时内",
 escalationTime: "24小时",
 autoEscalate: false,
 notifyLevel: ["MEDIUM", "LOW"],
 allowedActions: ["正常处理", "纳入计划", "定期跟进"]
 },
 LOW: {
 label: "低优先级",
  level: 5,
 responseTime: "24小时内",
 escalationTime: "72小时",
  autoEscalate: false,
 notifyLevel: ["LOW", "INFO"],
 allowedActions: ["批量处理", "定期清理", "归档记录"]
 }
};
