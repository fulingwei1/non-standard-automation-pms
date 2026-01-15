/**
 * Alert Statistics Constants
 * 告警统计分析系统常量配置
 */

export const ALERT_TYPES = {
  SYSTEM: { value: 'system', label: '系统告警', color: '#ff4d4f', icon: '🔴' },
  BUSINESS: { value: 'business', label: '业务告警', color: '#faad14', icon: '🟡' },
  PERFORMANCE: { value: 'performance', label: '性能告警', color: '#1890ff', icon: '🔵' },
  SECURITY: { value: 'security', label: '安全告警', color: '#722ed1', icon: '🟣' },
  RESOURCE: { value: 'resource', label: '资源告警', color: '#13c2c2', icon: '🟢' },
  QUALITY: { value: 'quality', label: '质量告警', color: '#eb2f96', icon: '🟪' }
};

export const ALERT_LEVELS = {
  CRITICAL: { value: 'critical', label: '紧急', color: '#ff4d4f', weight: 5, responseTime: '15分钟' },
  HIGH: { value: 'high', label: '高', color: '#fa8c16', weight: 4, responseTime: '30分钟' },
  MEDIUM: { value: 'medium', label: '中', color: '#faad14', weight: 3, responseTime: '2小时' },
  LOW: { value: 'low', label: '低', color: '#1890ff', weight: 2, responseTime: '24小时' },
  INFO: { value: 'info', label: '信息', color: '#52c41a', weight: 1, responseTime: '72小时' }
};

export const ALERT_STATUS = {
  ACTIVE: { value: 'active', label: '活跃', color: '#ff4d4f' },
  RESOLVED: { value: 'resolved', label: '已解决', color: '#52c41a' },
  SUPPRESSED: { value: 'suppressed', label: '已抑制', color: '#8c8c8c' },
  ACKNOWLEDGED: { value: 'acknowledged', label: '已确认', color: '#1890ff' },
  ESCALATED: { value: 'escalated', label: '已升级', color: '#722ed1' }
};

export const TIME_PERIODS = {
  LAST_HOUR: { value: 'last_hour', label: '最近1小时', range: 1 },
  LAST_24H: { value: 'last_24h', label: '最近24小时', range: 24 },
  LAST_7D: { value: 'last_7d', label: '最近7天', range: 168 },
  LAST_30D: { value: 'last_30d', label: '最近30天', range: 720 },
  LAST_QUARTER: { value: 'last_quarter', label: '最近一季度', range: 2160 },
  LAST_YEAR: { value: 'last_year', label: '最近一年', range: 8760 }
};

export const STATISTICS_METRICS = {
  TOTAL_ALERTS: { label: '告警总数', unit: '条' },
  ACTIVE_ALERTS: { label: '活跃告警', unit: '条' },
  RESOLVED_RATE: { label: '解决率', unit: '%' },
  AVG_RESOLUTION_TIME: { label: '平均解决时间', unit: '分钟' },
  ESCALATION_RATE: { label: '升级率', unit: '%' },
  FALSE_POSITIVE_RATE: { label: '误报率', unit: '%' }
};

export const CHART_TYPES = {
  LINE: { value: 'line', label: '趋势图', icon: '📈' },
  BAR: { value: 'bar', label: '柱状图', icon: '📊' },
  PIE: { value: 'pie', label: '饼图', icon: '🥧' },
  HEATMAP: { value: 'heatmap', label: '热力图', icon: '🗺️' },
  GAUGE: { value: 'gauge', label: '仪表盘', icon: '⚡' }
};

export const EXPORT_FORMATS = {
  CSV: { value: 'csv', label: 'CSV表格', icon: '📄' },
  EXCEL: { value: 'excel', label: 'Excel报告', icon: '📊' },
  PDF: { value: 'pdf', label: 'PDF文档', icon: '📋' },
  JSON: { value: 'json', label: 'JSON数据', icon: '🗄️' }
};

export const FILTER_CATEGORIES = {
  TYPE: 'type',
  LEVEL: 'level',
  STATUS: 'status',
  SOURCE: 'source',
  TIME_RANGE: 'timeRange'
};

export const TABLE_CONFIG = {
  pagination: { pageSize: 20, showSizeChanger: true },
  scroll: { x: 1000, y: 400 },
  size: 'middle'
};

export const CHART_COLORS = {
  CRITICAL: '#ff4d4f',
  HIGH: '#fa8c16',
  MEDIUM: '#faad14',
  LOW: '#1890ff',
  INFO: '#52c41a',
  SUCCESS: '#52c41a',
  WARNING: '#faad14',
  ERROR: '#ff4d4f',
  PRIMARY: '#1890ff',
  SECONDARY: '#722ed1'
};

export const DEFAULT_FILTERS = {
  type: null,
  level: null,
  status: null,
  timeRange: 'last_7d',
  source: null
};

export const DASHBOARD_LAYOUTS = {
  GRID: { value: 'grid', label: '网格布局', columns: 3 },
  LIST: { value: 'list', label: '列表布局', columns: 1 },
  COMPACT: { value: 'compact', label: '紧凑布局', columns: 4 }
};