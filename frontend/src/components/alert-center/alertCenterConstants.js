/**
 * Alert Center Constants - 预警中心配置常量
 * 包含预警级别、状态、类型、规则、通知方式等配置
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

// ==================== 预警处理配置 ====================
export const ALERT_ACTIONS = {
  ACKNOWLEDGE: {
    label: "确认预警",
    icon: "CheckCircle2",
    description: "确认收到预警，表示已知悉",
    allowedStatus: ["PENDING"],
    nextStatus: "ACKNOWLEDGED",
    requiredFields: ["acknowledged_by", "acknowledged_time", "note"]
  },
  ASSIGN: {
    label: "分配处理",
    icon: "User",
    description: "将预警分配给具体处理人",
    allowedStatus: ["PENDING", "ACKNOWLEDGED"],
    nextStatus: "ASSIGNED",
    requiredFields: ["assigned_to", "assigned_by", "assignment_note"]
  },
  ESCALATE: {
    label: "升级预警",
    icon: "TrendingUp",
    description: "将预警升级给更高级别处理",
    allowedStatus: ["PENDING", "ACKNOWLEDGED", "ASSIGNED", "IN_PROGRESS"],
    nextStatus: "ESCALATED",
    requiredFields: ["escalated_to", "escalated_by", "escalation_reason"]
  },
  RESOLVE: {
    label: "解决预警",
    icon: "CheckCircle2",
    description: "标记预警问题已解决",
    allowedStatus: ["ASSIGNED", "IN_PROGRESS", "ESCALATED"],
    nextStatus: "RESOLVED",
    requiredFields: ["resolved_by", "resolved_time", "resolution_method", "resolution_note"]
  },
  CLOSE: {
    label: "关闭预警",
    icon: "XCircle",
    description: "关闭预警处理流程",
    allowedStatus: ["RESOLVED"],
    nextStatus: "CLOSED",
    requiredFields: ["closed_by", "closed_time", "closure_reason"]
  },
  IGNORE: {
    label: "忽略预警",
    icon: "X",
    description: "忽略预警，不进行处理",
    allowedStatus: ["PENDING"],
    nextStatus: "IGNORED",
    requiredFields: ["ignored_by", "ignored_time", "ignore_reason"]
  }
};

// ==================== 预警统计指标配置 ====================
export const ALERT_METRICS = {
  RESPONSE_TIME: {
    label: "响应时间",
    description: "从预警产生到首次处理的平均时间",
    unit: "分钟",
    calculation: "(first_action_time - created_time) / 60",
    target: {
      CRITICAL: 5,
      HIGH: 30,
      MEDIUM: 120,
      LOW: 480
    }
  },
  RESOLUTION_TIME: {
    label: "解决时间",
    description: "从预警产生到问题解决的平均时间",
    unit: "小时",
    calculation: "(resolved_time - created_time) / 3600",
    target: {
      CRITICAL: 1,
      HIGH: 4,
      MEDIUM: 24,
      LOW: 72
    }
  },
  ESCALATION_RATE: {
    label: "升级率",
    description: "预警升级处理的比例",
    unit: "%",
    calculation: "(escalated_count / total_count) * 100",
    target: {
      CRITICAL: 10,
      HIGH: 15,
      MEDIUM: 20,
      LOW: 25
    }
  },
  FALSE_POSITIVE_RATE: {
    label: "误报率",
    description: "被判定为误报的预警比例",
    unit: "%",
    calculation: "(false_positive_count / total_count) * 100",
    target: 5
  },
  MTBF: {
    label: "平均故障间隔",
    description: "系统预警的平均间隔时间",
    unit: "小时",
    calculation: "total_period / failure_count",
    target: 168 // 一周
  },
  MTTR: {
    label: "平均修复时间",
    description: "预警修复的平均时间",
    unit: "小时",
    calculation: "total_downtime / failure_count",
    target: 4
  }
};

// ==================== 预警时间配置 ====================
export const ALERT_TIME_CONFIG = {
  BUSINESS_HOURS: {
    START: "09:00",
    END: "18:00",
    WORK_DAYS: [1, 2, 3, 4, 5],
    HOLIDAYS: [], // 节假日列表
    TIMEZONE: "Asia/Shanghai"
  },
  RESPONSE_TIME_WINDOWS: {
    IMMEDIATE: { max: 5, unit: "minutes" },
    URGENT: { max: 30, unit: "minutes" },
    HIGH: { max: 120, unit: "minutes" },
    NORMAL: { max: 480, unit: "minutes" },
    LOW: { max: 1440, unit: "minutes" }
  },
  ESCALATION_TIME_WINDOWS: {
    CRITICAL: { intervals: [5, 15, 30], unit: "minutes" },
    HIGH: { intervals: [30, 120, 240], unit: "minutes" },
    MEDIUM: { intervals: [120, 480, 720], unit: "minutes" },
    LOW: { intervals: [480, 1440, 2880], unit: "minutes" }
  }
};

// ==================== 工具函数 ====================

/**
 * 获取预警级别配置
 */
export const getAlertLevelConfig = (level) => {
  return ALERT_LEVELS[level] || ALERT_LEVELS.INFO;
};

/**
 * 获取预警状态配置
 */
export const getAlertStatusConfig = (status) => {
  return ALERT_STATUS[status] || ALERT_STATUS.PENDING;
};

/**
 * 获取预警类型配置
 */
export const getAlertTypeConfig = (type) => {
  return ALERT_TYPES[type] || ALERT_TYPES.SYSTEM;
};

/**
 * 获取预警规则配置
 */
export const getAlertRuleConfig = (ruleType) => {
  return ALERT_RULES[ruleType] || ALERT_RULES.THRESHOLD;
};

/**
 * 获取通知渠道配置
 */
export const getNotificationChannelConfig = (channel) => {
  return NOTIFICATION_CHANNELS[channel] || NOTIFICATION_CHANNELS.SYSTEM;
};

/**
 * 计算预警响应时间
 */
export const calculateResponseTime = (createdTime, firstActionTime) => {
  if (!createdTime || !firstActionTime) return 0;
  
  const created = new Date(createdTime);
  const action = new Date(firstActionTime);
  const diffMs = action - created;
  return Math.round(diffMs / (1000 * 60)); // 返回分钟
};

/**
 * 计算预警解决时间
 */
export const calculateResolutionTime = (createdTime, resolvedTime) => {
  if (!createdTime || !resolvedTime) return 0;
  
  const created = new Date(createdTime);
  const resolved = new Date(resolvedTime);
  const diffMs = resolved - created;
  return Math.round(diffMs / (1000 * 60 * 60)); // 返回小时
};

/**
 * 检查响应时间是否达标
 */
export const checkResponseTimeSLA = (responseTime, alertLevel) => {
  const levelConfig = getAlertLevelConfig(alertLevel);
  const targetTime = ALERT_TIME_CONFIG.RESPONSE_TIME_WINDOWS[levelConfig.urgency.toUpperCase()];
  
  return responseTime <= targetTime.max;
};

/**
 * 检查解决时间是否达标
 */
export const checkResolutionTimeSLA = (resolutionTime, alertLevel) => {
  const levelConfig = getAlertLevelConfig(alertLevel);
  const targetTime = ALERT_METRICS.RESOLUTION_TIME.target[levelConfig.level];
  
  return resolutionTime <= targetTime;
};

/**
 * 获取预警的下一个可执行操作
 */
export const getAvailableActions = (alert) => {
  const statusConfig = getAlertStatusConfig(alert.status);
  return statusConfig ? statusConfig.nextActions : [];
};

/**
 * 验证预警规则配置
 */
export const validateAlertRule = (rule) => {
  const errors = [];
  
  // 验证必填字段
  if (!rule.name || rule.name.trim() === '') {
    errors.push('规则名称不能为空');
  }
  
  if (!rule.condition || rule.condition.trim() === '') {
    errors.push('触发条件不能为空');
  }
  
  if (!rule.threshold && rule.rule_type !== 'TIME_BASED') {
    errors.push('阈值不能为空');
  }
  
  // 验证数值范围
  if (rule.threshold && (isNaN(rule.threshold) || rule.threshold <= 0)) {
    errors.push('阈值必须是正数');
  }
  
  // 验证通知配置
  if (rule.notification_channels && rule.notification_channels.length === 0) {
    errors.push('至少需要配置一个通知渠道');
  }
  
  return errors;
};

/**
 * 生成预警编号
 */
export const generateAlertNumber = (type, date = new Date()) => {
  const typeCode = type.substring(0, 3).toUpperCase();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const sequence = Math.floor(Math.random() * 1000).toString().padStart(3, '0');
  
  return `ALT${typeCode}${year}${month}${day}${sequence}`;
};

/**
 * 获取预警统计摘要
 */
export const getAlertSummary = (alerts, dateRange = null) => {
  let filteredAlerts = alerts;
  
  if (dateRange) {
    filteredAlerts = alerts.filter(alert => {
      const alertDate = new Date(alert.created_time);
      return alertDate >= dateRange.start && alertDate <= dateRange.end;
    });
  }
  
  const summary = {
    total: filteredAlerts.length,
    byLevel: {},
    byStatus: {},
    byType: {},
    responseTime: 0,
    resolutionTime: 0,
    escalated: 0
  };
  
  filteredAlerts.forEach(alert => {
    // 按级别统计
    const level = alert.alert_level || 'INFO';
    summary.byLevel[level] = (summary.byLevel[level] || 0) + 1;
    
    // 按状态统计
    const status = alert.status || 'PENDING';
    summary.byStatus[status] = (summary.byStatus[status] || 0) + 1;
    
    // 按类型统计
    const type = alert.alert_type || 'SYSTEM';
    summary.byType[type] = (summary.byType[type] || 0) + 1;
    
    // 统计响应和解决时间
    if (alert.first_action_time) {
      summary.responseTime += calculateResponseTime(alert.created_time, alert.first_action_time);
    }
    
    if (alert.resolved_time) {
      summary.resolutionTime += calculateResolutionTime(alert.created_time, alert.resolved_time);
    }
    
    // 统计升级数量
    if (alert.escalated) {
      summary.escalated += 1;
    }
  });
  
  // 计算平均时间
  const actionableAlerts = filteredAlerts.filter(a => a.first_action_time);
  summary.avgResponseTime = actionableAlerts.length > 0 
    ? Math.round(summary.responseTime / actionableAlerts.length) 
    : 0;
  
  const resolvedAlerts = filteredAlerts.filter(a => a.resolved_time);
  summary.avgResolutionTime = resolvedAlerts.length > 0 
    ? Math.round(summary.resolutionTime / resolvedAlerts.length) 
    : 0;
  
  return summary;
};

/**
 * 检查是否需要升级
 */
export const requiresEscalation = (alert, currentTime = new Date()) => {
  if (!alert.created_time) return false;
  
  const created = new Date(alert.created_time);
  const elapsed = (currentTime - created) / (1000 * 60); // 分钟
  
  const levelConfig = getAlertLevelConfig(alert.alert_level);
  if (!levelConfig.autoEscalate) return false;
  
  const escalationWindows = ALERT_TIME_CONFIG.ESCALATION_TIME_WINDOWS[levelConfig.level];
  return escalationWindows.intervals.some(interval => elapsed > interval);
};

/**
 * 获取预警严重程度分数
 */
export const getAlertSeverityScore = (level) => {
  const levelConfig = getAlertLevelConfig(level);
  return levelConfig ? levelConfig.level : 1;
};

/**
 * 检查预警是否在工作时间
 */
export const isBusinessHour = (timestamp) => {
  const time = new Date(timestamp);
  const hour = time.getHours();
  const day = time.getDay();
  
  const { START, END, WORK_DAYS } = ALERT_TIME_CONFIG.BUSINESS_HOURS;
  
  return day >= WORK_DAYS[0] && day <= WORK_DAYS[WORK_DAYS.length - 1] &&
         hour >= parseInt(START.split(':')[0]) && 
         hour <= parseInt(END.split(':')[0]);
};

/**
 * 格式化预警时间显示
 */
export const formatAlertTime = (timestamp) => {
  if (!timestamp) return '-';
  
  const date = new Date(timestamp);
  const now = new Date();
  const diffMs = now - date;
  const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
  
  if (diffDays === 0) {
    return `今天 ${date.toLocaleTimeString()}`;
  } else if (diffDays === 1) {
    return `昨天 ${date.toLocaleTimeString()}`;
  } else if (diffDays < 7) {
    return `${diffDays}天前 ${date.toLocaleTimeString()}`;
  } else {
    return date.toLocaleString();
  }
};

// ==================== 导出默认配置 ====================
export const DEFAULT_ALERT_CONFIG = {
  level: 'INFO',
  status: 'PENDING',
  priority: 'NORMAL',
  autoEscalate: false,
  notificationChannels: ['SYSTEM']
};

export const DEFAULT_RULE_CONFIG = {
  name: '',
  description: '',
  rule_type: 'THRESHOLD',
  condition: 'greater',
  threshold: 0,
  notification_channels: ['SYSTEM'],
  enabled: true,
  severity: 'MEDIUM'
};

// ==================== 状态映射 ====================
export const ALERT_STATUS_FLOW = {
  'PENDING': ['ACKNOWLEDGE', 'ASSIGN', 'IGNORE'],
  'ACKNOWLEDGED': ['ASSIGN', 'ESCALATE'],
  'ASSIGNED': ['ESCALATE', 'RESOLVE'],
  'IN_PROGRESS': ['RESOLVE', 'ESCALATE', 'PAUSE'],
  'RESOLVED': ['CLOSE', 'REOPEN'],
  'CLOSED': ['REOPEN'],
  'IGNORED': ['REOPEN']
};

// ==================== 权限配置 ====================
export const ALERT_PERMISSIONS = {
  VIEW: ['admin', 'manager', 'operator', 'viewer'],
  CREATE: ['admin', 'manager'],
  EDIT: ['admin', 'manager'],
  DELETE: ['admin'],
  ASSIGN: ['admin', 'manager'],
  ESCALATE: ['admin', 'manager'],
  CONFIGURE_RULES: ['admin'],
  MANAGE_NOTIFICATIONS: ['admin', 'manager']
};