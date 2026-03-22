/**
 * 图表与过滤器配置 - Chart & Filter Configs
 * 包含时间维度、图表类型、统计指标、过滤器、颜色等配置
 */

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
