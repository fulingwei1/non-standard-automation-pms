/**
 * 预警处理与默认配置 - Alert Actions, Metrics, Time Config & Defaults
 * 包含预警操作、指标、时间、权限、默认值等配置
 */

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
