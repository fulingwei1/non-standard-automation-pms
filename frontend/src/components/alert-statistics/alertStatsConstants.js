/**
 * Alert Statistics Configuration Constants - 告警统计配置常量
 * 包含告警类型、级别、状态、时间维度等统计配置
 *
 * 这是告警常量的主文件（primary file），合并了以下来源：
 * - alertStatsConstants.js (原有统计配置)
 * - alertCenterConstants.js (预警中心配置)
 * - alertStatsConstants.js (已是 re-export shim)
 */

// ==================== 告警统计类型配置 ====================
export const ALERT_STAT_TYPES = {
 OVERVIEW: {
 label: "总体概览",
 description: "告警总体统计信息",
  icon: "BarChart3",
 metrics: ["total", "pending", "resolved", "processing", "ignored"]
 },
 BY_LEVEL: {
  label: "按级别统计",
 description: "按告警级别分类统计",
  icon: "AlertTriangle",
   metrics: ["critical", "high", "medium", "low", "info"]
  },
 BY_STATUS: {
 label: "按状态统计",
  description: "按告警状态分类统计",
  icon: "Circle",
 metrics: ["pending", "acknowledged", "assigned", "in_progress", "resolved", "closed", "ignored"]
 },
 BY_TYPE: {
 label: "按类型统计",
 description: "按告警类型分类统计",
 icon: "Tag",
 metrics: ["project", "system", "business", "operation", "quality"]
  },
 BY_TIME: {
  label: "时间趋势",
 description: "告警时间趋势分析",
  icon: "Clock",
  metrics: ["daily", "weekly", "monthly", "hourly"]
 },
 BY_PROJECT: {
 label: "项目分布",
  description: "按项目维度告警分布",
  icon: "FolderOpen",
 metrics: ["active", "delayed", "completed", "on_hold"]
  },
 BY_RULE: {
 label: "规则统计",
 description: "按告警规则统计",
 icon: "Settings",
 metrics: ["active_rules", "triggered_rules", "efficiency", "accuracy"]
 },
 BY_RESPONSE: {
 label: "响应统计",
 description: "告警响应时效统计",
  icon: "Timer",
 metrics: ["avg_response", "avg_resolution", "sla_compliance", "escalation_rate"]
  }
};

// ==================== 告警级别统计配置 ====================
export const ALERT_LEVEL_STATS = {
 CRITICAL: {
  label: "严重",
 value: 5,
 color: "rgb(239, 68, 68)",
 bgColor: "rgba(239, 68, 68, 0.1)",
  borderColor: "rgb(239, 68, 68)",
  priority: 1,
  targetResponseTime: 5,
 targetResolutionTime: 1,
  trendDirection: "down"
 },
 HIGH: {
 label: "高",
 value: 4,
  color: "rgb(251, 146, 60)",
  bgColor: "rgba(251, 146, 60, 0.1)",
 borderColor: "rgb(251, 146, 60)",
 priority: 2,
  targetResponseTime: 30,
 targetResolutionTime: 4,
 trendDirection: "stable"
 },
 MEDIUM: {
 label: "中",
 value: 3,
  color: "rgb(245, 158, 11)",
 bgColor: "rgba(245, 158, 11, 0.1)",
  borderColor: "rgb(245, 158, 11)",
  priority: 3,
  targetResponseTime: 120,
  targetResolutionTime: 24,
  trendDirection: "up"
 },
 LOW: {
  label: "低",
 value: 2,
 color: "rgb(59, 130, 246)",
 bgColor: "rgba(59, 130, 246, 0.1)",
  borderColor: "rgb(59, 130, 246)",
 priority: 4,
 targetResponseTime: 480,
 targetResolutionTime: 72,
 trendDirection: "stable"
 },
 INFO: {
   label: "信息",
 value: 1,
  color: "rgb(107, 114, 128)",
  bgColor: "rgba(107, 114, 128, 0.1)",
 borderColor: "rgb(107, 114, 128)",
 priority: 5,
 targetResponseTime: 1440,
  targetResolutionTime: 168,
 trendDirection: "down"
 }
};

// ==================== 告警状态统计配置 ====================
export const ALERT_STATUS_STATS = {
 PENDING: {
 label: "待处理",
 value: 1,
  color: "rgb(245, 158, 11)",
 bgColor: "rgba(245, 158, 11, 0.1)",
 borderColor: "rgb(245, 158, 11)",
 urgency: "high"
  },
 ACKNOWLEDGED: {
 label: "已确认",
 value: 2,
 color: "rgb(59, 130, 246)",
 bgColor: "rgba(59, 130, 246, 0.1)",
 borderColor: "rgb(59, 130, 246)",
 urgency: "medium"
 },
 ASSIGNED: {
 label: "已分配",
 value: 3,
 color: "rgb(147, 51, 234)",
 bgColor: "rgba(147, 51, 234, 0.1)",
  borderColor: "rgb(147, 51, 234)",
 urgency: "medium"
 },
 IN_PROGRESS: {
  label: "处理中",
 value: 4,
 color: "rgb(79, 70, 229)",
  bgColor: "rgba(79, 70, 229, 0.1)",
 borderColor: "rgb(79, 70, 229)",
 urgency: "medium"
 },
 RESOLVED: {
  label: "已解决",
 value: 5,
 color: "rgb(34, 197, 94)",
 bgColor: "rgba(34, 197, 94, 0.1)",
 borderColor: "rgb(34, 197, 94)",
 urgency: "low"
 },
 CLOSED: {
  label: "已关闭",
 value: 6,
 color: "rgb(107, 114, 128)",
  bgColor: "rgba(107, 114, 128, 0.1)",
 borderColor: "rgb(107, 114, 128)",
  urgency: "low"
 },
 IGNORED: {
 label: "已忽略",
 value: 7,
 color: "rgb(156, 163, 175)",
 bgColor: "rgba(156, 163, 175, 0.1)",
 borderColor: "rgb(156, 163, 175)",
 urgency: "none"
 }
};

// ==================== 告警类型统计配置 ====================
export const ALERT_TYPE_STATS = {
 PROJECT: {
 label: "项目预警",
  category: "项目管理",
  icon: "\u{1F4C1}",
 color: "rgb(59, 130, 246)",
 bgColor: "rgba(59, 130, 246, 0.1)",
  borderColor: "rgb(59, 130, 246)",
  subtypes: {
 DELAY: { label: "进度延期", color: "rgb(239, 68, 68)" },
 BUDGET: { label: "预算超支", color: "rgb(245, 158, 11)" },
 MILESTONE: { label: "里程碑逾期", color: "rgb(251, 146, 60)" },
 RESOURCE: { label: "资源不足", color: "rgb(34, 197, 94)" },
  QUALITY: { label: "质量风险", color: "rgb(147, 51, 234)" }
  }
 },
 SYSTEM: {
  label: "系统告警",
 category: "系统监控",
 icon: "\u{1F4BB}",
  color: "rgb(147, 51, 234)",
 bgColor: "rgba(147, 51, 234, 0.1)",
  borderColor: "rgb(147, 51, 234)",
 subtypes: {
  PERFORMANCE: { label: "性能异常", color: "rgb(239, 68, 68)" },
  SECURITY: { label: "安全威胁", color: "rgb(239, 68, 68)" },
 CAPACITY: { label: "容量不足", color: "rgb(245, 158, 11)" },
   BACKUP: { label: "备份失败", color: "rgb(251, 146, 60)" },
   CONNECTIVITY: { label: "连接中断", color: "rgb(239, 68, 68)" }
 }
 },
 BUSINESS: {
  label: "业务告警",
 category: "业务监控",
 icon: "\u{1F4CA}",
 color: "rgb(34, 197, 94)",
   bgColor: "rgba(34, 197, 94, 0.1)",
 borderColor: "rgb(34, 197, 94)",
 subtypes: {
   SALES: { label: "销售下滑", color: "rgb(251, 146, 60)" },
 INVENTORY: { label: "库存异常", color: "rgb(239, 68, 68)" },
 CUSTOMER: { label: "客户投诉", color: "rgb(245, 158, 11)" },
  FINANCIAL: { label: "财务异常", color: "rgb(239, 68, 68)" },
  COMPLIANCE: { label: "合规风险", color: "rgb(147, 51, 234)" }
  }
 },
 OPERATION: {
 label: "运营告警",
 category: "运营管理",
 icon: "\u{2699}\u{FE0F}",
 color: "rgb(245, 158, 11)",
  bgColor: "rgba(245, 158, 11, 0.1)",
 borderColor: "rgb(245, 158, 11)",
 subtypes: {
  EQUIPMENT: { label: "设备故障", color: "rgb(239, 68, 68)" },
 MAINTENANCE: { label: "维护超期", color: "rgb(251, 146, 60)" },
  SAFETY: { label: "安全事故", color: "rgb(239, 68, 68)" },
 COMPLAINT: { label: "客诉激增", color: "rgb(245, 158, 11)" },
 STAFF: { label: "人员异常", color: "rgb(147, 51, 234)" }
 }
  },
 QUALITY: {
  label: "质量告警",
  category: "质量管理",
 icon: "\u{1F6E1}\u{FE0F}",
 color: "rgb(147, 51, 234)",
  bgColor: "rgba(147, 51, 234, 0.1)",
 borderColor: "rgb(147, 51, 234)",
  subtypes: {
  DEFECT: { label: "质量缺陷", color: "rgb(239, 68, 68)" },
 INSPECTION: { label: "检验失败", color: "rgb(245, 158, 11)" },
 CERTIFICATION: { label: "认证问题", color: "rgb(251, 146, 60)" },
  RECALL: { label: "产品召回", color: "rgb(239, 68, 68)" },
  COMPLIANCE: { label: "标准违规", color: "rgb(147, 51, 234)" }
 }
 }
};

// ==================== 时间维度配置 ====================
export const TIME_DIMENSIONS = {
 HOURLY: {
 label: "小时",
  description: "按小时统计",
 format: "HH:mm",
  intervals: 24,
  groupBy: "hour"
 },
  DAILY: {
 label: "日",
 description: "按天统计",
  format: "MM-DD",
  intervals: 30,
 groupBy: "day"
 },
 WEEKLY: {
  label: "周",
 description: "按周统计",
  format: "第W周",
 intervals: 12,
 groupBy: "week"
 },
 MONTHLY: {
 label: "月",
  description: "按月统计",
  format: "YYYY-MM",
  intervals: 12,
 groupBy: "month"
 },
 QUARTERLY: {
  label: "季度",
 description: "按季度统计",
  format: "Q季度",
 intervals: 4,
 groupBy: "quarter"
  }
};

// ==================== 统计图表类型配置 ====================
export const CHART_TYPES = {
 BAR: {
 label: "柱状图",
  description: "适合分类数据对比",
 icon: "BarChart",
 bestFor: ["level", "status", "type", "project"]
 },
  LINE: {
 label: "折线图",
  description: "适合时间趋势分析",
  icon: "LineChart",
 bestFor: ["time", "trend", "response"]
 },
 PIE: {
  label: "饼图",
 description: "适合占比分析",
 icon: "PieChart",
  bestFor: ["distribution", "proportion"]
 },
 AREA: {
 label: "面积图",
  description: "适合累积趋势分析",
  icon: "AreaChart",
 bestFor: ["cumulative", "volume"]
 },
 RADAR: {
 label: "雷达图",
 description: "适合多维度对比",
 icon: "RadarChart",
 bestFor: ["multi-dimension", "performance"]
 },
 FUNNEL: {
  label: "漏斗图",
 description: "适合流程转化分析",
  icon: "FunnelChart",
 bestFor: ["conversion", "process"]
 }
};

// ==================== 统计指标配置 ====================
export const STAT_METRICS = {
 COUNT: {
  label: "数量",
  description: "告警总数",
 unit: "个",
 format: "number",
  precision: 0
 },
 RATE: {
  label: "比率",
  description: "百分比统计",
 unit: "%",
 format: "percentage",
  precision: 1
  },
 AVERAGE: {
 label: "平均值",
  description: "平均响应/解决时间",
 unit: "分钟",
 format: "number",
 precision: 1
 },
 TREND: {
 label: "趋势",
  description: "同比/环比变化",
 unit: "%",
  format: "trend",
 precision: 1
 },
 DISTRIBUTION: {
 label: "分布",
 description: "告警分布情况",
 unit: "",
 format: "distribution",
  precision: 0
 }
};

// ==================== 过滤器配置 ====================
export const FILTER_CONFIGS = {
 TIME_RANGE: {
  label: "时间范围",
 options: [
 { value: "today", label: "今天" },
  { value: "yesterday", label: "昨天" },
  { value: "week", label: "本周" },
 { value: "month", label: "本月" },
 { value: "quarter", label: "本季度" },
  { value: "year", label: "本年" },
   { value: "custom", label: "自定义" }
  ]
 },
  LEVEL: {
  label: "告警级别",
 options: [
  { value: "all", label: "全部" },
  { value: "critical", label: "严重" },
  { value: "high", label: "高" },
  { value: "medium", label: "中" },
 { value: "low", label: "低" },
 { value: "info", label: "信息" }
  ]
 },
 STATUS: {
 label: "告警状态",
 options: [
 { value: "all", label: "全部" },
  { value: "pending", label: "待处理" },
 { value: "acknowledged", label: "已确认" },
  { value: "assigned", label: "已分配" },
  { value: "in_progress", label: "处理中" },
  { value: "resolved", label: "已解决" },
  { value: "closed", label: "已关闭" },
  { value: "ignored", label: "已忽略" }
 ]
 },
  TYPE: {
  label: "告警类型",
 options: [
  { value: "all", label: "全部" },
 { value: "project", label: "项目预警" },
  { value: "system", label: "系统告警" },
  { value: "business", label: "业务告警" },
   { value: "operation", label: "运营告警" },
  { value: "quality", label: "质量告警" }
 ]
  },
 PROJECT: {
 label: "项目",
 options: [
  { value: "all", label: "全部项目" },
 { value: "active", label: "进行中项目" },
 { value: "delayed", label: "延期项目" },
  { value: "completed", label: "已完成项目" }
 ]
  }
};

// ==================== 图表颜色配置 ====================
// 用于统计图表的标准颜色
export const CHART_COLORS = {
 PRIMARY: "#1890ff",
 SUCCESS: "#52c41a",
 WARNING: "#faad14",
 ERROR: "#ff4d4f",
  CRITICAL: "#cf1322",
 INFO: "#8c8c8c",
 PURPLE: "#722ed1",
  CYAN: "#13c2c2",
 MAGENTA: "#eb2f96",
 GEEKBLUE: "#2f54eb"
};

// ==================== 统计指标详细配置 ====================
// 用于 AlertOverview / AlertPerformance 等组件
export const STATISTICS_METRICS = {
  TOTAL_ALERTS: {
 label: "告警总数",
 unit: "个",
 description: "统计周期内告警总量"
 },
 ACTIVE_ALERTS: {
  label: "活跃告警",
 unit: "个",
 description: "当前未解决的告警数量"
  },
  RESOLVED_RATE: {
 label: "解决率",
  unit: "%",
  description: "已解决告警占比"
 },
 AVG_RESOLUTION_TIME: {
  label: "平均解决时间",
 unit: "小时",
  description: "告警平均解决耗时"
 },
 ESCALATION_RATE: {
 label: "升级率",
 unit: "%",
 description: "告警升级处理的比例"
 },
 FALSE_POSITIVE_RATE: {
 label: "误报率",
 unit: "%",
 description: "被判定为误报的告警比例"
 }
};

// ==================== 表格配置 ====================
// 用于 AlertDetails 组件的表格展示
export const TABLE_CONFIG = {
 pagination: {
 pageSize: 10,
 showSizeChanger: true,
 pageSizeOptions: ["10", "20", "50", "100"],
 showTotal: (total) => `共 ${total} 条`
 },
 scroll: { x: 1200 },
 size: "middle"
};

// ============================================================
// 以下常量来自预警中心 (alertCenterConstants.js)
// ============================================================

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

// ==================== 默认配置 ====================
export const DEFAULT_STAT_CONFIG = {
 type: 'OVERVIEW',
 timeDimension: 'DAILY',
 chartType: 'BAR',
 filters: {
  timeRange: 'month',
  level: 'all',
  status: 'all',
  type: 'all',
 project: 'all'
 }
};

export const DEFAULT_CHART_CONFIG = {
 height: 300,
 showGrid: true,
 showPoints: true,
 showLegend: true,
 showTooltip: true,
 animations: true
};

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

// ==================== 时间周期配置 ====================
// 用于 AlertStatistics 页面的时间筛选
export const TIME_PERIODS = {
 LAST_1H: { label: "最近1小时", value: "last_1h", hours: 1 },
 LAST_24H: { label: "最近24小时", value: "last_24h", hours: 24 },
 LAST_7D: { label: "最近7天", value: "last_7d", hours: 168 },
 LAST_30D: { label: "最近30天", value: "last_30d", hours: 720 },
 LAST_90D: { label: "最近90天", value: "last_90d", hours: 2160 },
 CUSTOM: { label: "自定义", value: "custom", hours: null }
};

// ==================== 导出格式配置 ====================
export const EXPORT_FORMATS = {
  PDF: { label: "PDF报告", value: "pdf", icon: "FileText", mimeType: "application/pdf" },
 EXCEL: { label: "Excel表格", value: "excel", icon: "Table", mimeType: "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
 CSV: { label: "CSV文件", value: "csv", icon: "FileSpreadsheet", mimeType: "text/csv" }
};

// ==================== 过滤分类配置 ====================
export const FILTER_CATEGORIES = {
 TYPE: { label: "告警类型", field: "type" },
 LEVEL: { label: "告警级别", field: "level" },
 STATUS: { label: "告警状态", field: "status" },
 SOURCE: { label: "告警来源", field: "source" },
 ASSIGNEE: { label: "处理人", field: "assignee" }
};

// ==================== 默认过滤器 ====================
export const DEFAULT_FILTERS = {
 type: null,
 level: null,
 status: null,
 source: null,
 assignee: null,
 timeRange: 'last_24h'
};

// ==================== 仪表盘布局配置 ====================
export const DASHBOARD_LAYOUTS = {
 GRID: { label: "网格", value: "grid", icon: "LayoutGrid" },
 LIST: { label: "列表", value: "list", icon: "List" },
 COMPACT: { label: "紧凑", value: "compact", icon: "Minimize2" }
};

// ==================== 工具函数（统计相关） ====================

/**
 * 获取告警级别统计配置
 */
export const getAlertLevelConfig = (level) => {
 return ALERT_LEVEL_STATS[level] || ALERT_LEVEL_STATS.INFO;
};

/**
 * 获取告警状态统计配置
 */
export const getAlertStatusConfig = (status) => {
  return ALERT_STATUS_STATS[status] || ALERT_STATUS_STATS.PENDING;
};

/**
 * 获取告警类型统计配置
 */
export const getAlertTypeConfig = (type) => {
 return ALERT_TYPE_STATS[type] || ALERT_TYPE_STATS.SYSTEM;
};

/**
 * 计算告警响应时间达标率
 */
export const calculateSLACompliance = (alerts) => {
 if (!alerts || alerts.length === 0) {return 0;}

 const compliantAlerts = alerts.filter((alert) => {
 const levelConfig = getAlertLevelConfig(alert.alert_level);
  const responseTime = calculateResponseTime(alert);
 return responseTime <= levelConfig.targetResponseTime;
  });

 return Math.round(compliantAlerts.length / alerts.length * 100);
};

/**
 * 计算平均响应时间
 */
export const calculateAverageResponseTime = (alerts) => {
 if (!alerts || alerts.length === 0) {return 0;}

 const alertsWithResponse = alerts.filter((alert) => alert.response_time);
 if (alertsWithResponse.length === 0) {return 0;}

 const totalTime = alertsWithResponse.reduce((sum, alert) =>
 sum + (alert.response_time || 0), 0
 );

 return Math.round(totalTime / alertsWithResponse.length);
};

/**
 * 计算单个告警的响应时间
 */
export const calculateResponseTime = (alert) => {
 if (!alert.created_at || !alert.first_action_time) {return 0;}

 const created = new Date(alert.created_at);
 const action = new Date(alert.first_action_time);
 const diffMs = action - created;
 return Math.round(diffMs / (1000 * 60)); // 返回分钟
};

/**
 * 格式化统计数据
 */
export const formatStatValue = (value, metric) => {
 const metricConfig = STAT_METRICS[metric];
  if (!metricConfig) {return value;}

 switch (metricConfig.format) {
  case 'percentage':
  return `${value.toFixed(metricConfig.precision)}${metricConfig.unit}`;
  case 'number':
  return value.toFixed(metricConfig.precision);
  case 'trend':
  return `${value > 0 ? '+' : ''}${value.toFixed(metricConfig.precision)}${metricConfig.unit}`;
 default:
 return value;
 }
};

/**
 * 获取趋势方向
 */
export const getTrendDirection = (current, previous) => {
 if (!previous) {return 'stable';}
 const change = (current - previous) / previous * 100;

 if (change > 5) {return 'up';}
 if (change < -5) {return 'down';}
 return 'stable';
};

/**
 * 获取趋势颜色
 */
export const getTrendColor = (direction) => {
  switch (direction) {
  case 'up':
  return 'text-red-500';
 case 'down':
   return 'text-emerald-500';
 default:
  return 'text-gray-500';
 }
};

/**
 * 获取趋势图标
 */
export const getTrendIcon = (direction) => {
 switch (direction) {
  case 'up':
  return '\u2191';
  case 'down':
 return '\u2193';
 default:
  return '\u2192';
 }
};

/**
 * 生成时间序列数据
 */
export const generateTimeSeries = (data, timeDimension) => {
 const { groupBy: _groupBy, intervals } = TIME_DIMENSIONS[timeDimension];

 // 根据实际数据格式生成时间序列
 // 返回格式: { labels: [], values: [] }
 return {
  labels: Array.from({ length: intervals }, (_, i) => `时间${i + 1}`),
 values: Array.from({ length: intervals }, () => Math.floor(Math.random() * 100))
 };
};

// ==================== 工具函数（预警中心相关） ====================

/**
 * 获取预警级别配置（预警中心版）
 */
export const getAlertCenterLevelConfig = (level) => {
 return ALERT_LEVELS[level] || ALERT_LEVELS.INFO;
};

/**
 * 获取预警状态配置（预警中心版）
 */
export const getAlertCenterStatusConfig = (status) => {
 return ALERT_STATUS[status] || ALERT_STATUS.PENDING;
};

/**
 * 获取预警类型配置（预警中心版）
 */
export const getAlertCenterTypeConfig = (type) => {
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
 * 计算预警响应时间（预警中心版，接受两个参数）
 */
export const calculateCenterResponseTime = (createdTime, firstActionTime) => {
 if (!createdTime || !firstActionTime) {return 0;}

 const created = new Date(createdTime);
 const action = new Date(firstActionTime);
 const diffMs = action - created;
 return Math.round(diffMs / (1000 * 60)); // 返回分钟
};

/**
 * 计算预警解决时间
 */
export const calculateResolutionTime = (createdTime, resolvedTime) => {
 if (!createdTime || !resolvedTime) {return 0;}

 const created = new Date(createdTime);
 const resolved = new Date(resolvedTime);
 const diffMs = resolved - created;
 return Math.round(diffMs / (1000 * 60 * 60)); // 返回小时
};

/**
 * 检查响应时间是否达标
 */
export const checkResponseTimeSLA = (responseTime, alertLevel) => {
 const levelConfig = getAlertCenterLevelConfig(alertLevel);
 const targetTime = ALERT_TIME_CONFIG.RESPONSE_TIME_WINDOWS[levelConfig.urgency.toUpperCase()];

 return responseTime <= targetTime.max;
};

/**
 * 检查解决时间是否达标
 */
export const checkResolutionTimeSLA = (resolutionTime, alertLevel) => {
 const levelConfig = getAlertCenterLevelConfig(alertLevel);
  const targetTime = ALERT_METRICS.RESOLUTION_TIME.target[levelConfig.level];

 return resolutionTime <= targetTime;
};

/**
 * 获取预警的下一个可执行操作
 */
export const getAvailableActions = (alert) => {
 const statusConfig = getAlertCenterStatusConfig(alert.status);
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
  summary.responseTime += calculateCenterResponseTime(alert.created_time, alert.first_action_time);
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
 if (!alert.created_time) {return false;}

 const created = new Date(alert.created_time);
 const elapsed = (currentTime - created) / (1000 * 60); // 分钟

 const levelConfig = getAlertCenterLevelConfig(alert.alert_level);
 if (!levelConfig.autoEscalate) {return false;}

  const escalationWindows = ALERT_TIME_CONFIG.ESCALATION_TIME_WINDOWS[levelConfig.level];
 return escalationWindows.intervals.some(interval => elapsed > interval);
};

/**
 * 获取预警严重程度分数
 */
export const getAlertSeverityScore = (level) => {
  const levelConfig = getAlertCenterLevelConfig(level);
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
 if (!timestamp) {return '-';}

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

// ==================== 默认导出 ====================
export default {
 ALERT_STAT_TYPES,
 ALERT_LEVEL_STATS,
 ALERT_STATUS_STATS,
 ALERT_TYPE_STATS,
 TIME_DIMENSIONS,
 CHART_TYPES,
 STAT_METRICS,
  FILTER_CONFIGS,
 CHART_COLORS,
 STATISTICS_METRICS,
  TABLE_CONFIG,
 ALERT_LEVELS,
 ALERT_STATUS,
 ALERT_TYPES,
 ALERT_RULES,
 NOTIFICATION_CHANNELS,
 ALERT_PRIORITY,
 ALERT_ACTIONS,
 ALERT_METRICS,
 ALERT_TIME_CONFIG,
 ALERT_STATUS_FLOW,
  ALERT_PERMISSIONS,
 DEFAULT_STAT_CONFIG,
 DEFAULT_CHART_CONFIG,
 DEFAULT_ALERT_CONFIG,
 DEFAULT_RULE_CONFIG,
 TIME_PERIODS,
  EXPORT_FORMATS,
 FILTER_CATEGORIES,
 DEFAULT_FILTERS,
 DASHBOARD_LAYOUTS,
 getAlertLevelConfig,
 getAlertStatusConfig,
 getAlertTypeConfig,
 calculateSLACompliance,
 calculateAverageResponseTime,
 calculateResponseTime,
 formatStatValue,
 getTrendDirection,
 getTrendColor,
 getTrendIcon,
 generateTimeSeries,
 getAlertCenterLevelConfig,
 getAlertCenterStatusConfig,
 getAlertCenterTypeConfig,
  getAlertRuleConfig,
  getNotificationChannelConfig,
  calculateCenterResponseTime,
 calculateResolutionTime,
 checkResponseTimeSLA,
 checkResolutionTimeSLA,
 getAvailableActions,
 validateAlertRule,
 generateAlertNumber,
 getAlertSummary,
 requiresEscalation,
 getAlertSeverityScore,
 isBusinessHour,
 formatAlertTime
};
