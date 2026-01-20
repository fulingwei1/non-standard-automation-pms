/**
 * Alert Statistics Configuration Constants - 告警统计配置常量
 * 包含告警类型、级别、状态、时间维度等统计配置
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
    icon: "📁",
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
    icon: "💻",
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
    icon: "📊",
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
    icon: "⚙️",
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
    icon: "🛡️",
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
    { value: "custom", label: "自定义" }]

  },
  LEVEL: {
    label: "告警级别",
    options: [
    { value: "all", label: "全部" },
    { value: "critical", label: "严重" },
    { value: "high", label: "高" },
    { value: "medium", label: "中" },
    { value: "low", label: "低" },
    { value: "info", label: "信息" }]

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
    { value: "ignored", label: "已忽略" }]

  },
  TYPE: {
    label: "告警类型",
    options: [
    { value: "all", label: "全部" },
    { value: "project", label: "项目预警" },
    { value: "system", label: "系统告警" },
    { value: "business", label: "业务告警" },
    { value: "operation", label: "运营告警" },
    { value: "quality", label: "质量告警" }]

  },
  PROJECT: {
    label: "项目",
    options: [
    { value: "all", label: "全部项目" },
    { value: "active", label: "进行中项目" },
    { value: "delayed", label: "延期项目" },
    { value: "completed", label: "已完成项目" }]

  }
};

// ==================== 工具函数 ====================

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
      return '↑';
    case 'down':
      return '↓';
    default:
      return '→';
  }
};

/**
 * 生成时间序列数据
 */
export const generateTimeSeries = (data, timeDimension) => {
  const { groupBy: _groupBy, intervals } = TIME_DIMENSIONS[timeDimension];

  // 这里根据实际数据格式生成时间序列
  // 返回格式: { labels: [], values: [] }
  return {
    labels: Array.from({ length: intervals }, (_, i) => `时间${i + 1}`),
    values: Array.from({ length: intervals }, () => Math.floor(Math.random() * 100))
  };
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

export default {
  ALERT_STAT_TYPES,
  ALERT_LEVEL_STATS,
  ALERT_STATUS_STATS,
  ALERT_TYPE_STATS,
  TIME_DIMENSIONS,
  CHART_TYPES,
  STAT_METRICS,
  FILTER_CONFIGS,
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
  DEFAULT_STAT_CONFIG,
  DEFAULT_CHART_CONFIG
};