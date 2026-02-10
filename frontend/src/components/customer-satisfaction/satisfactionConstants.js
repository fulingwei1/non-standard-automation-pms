/**
 * Customer Satisfaction Management Constants
 * 客户满意度管理系统常量配置
 * 包含满意度评分、反馈类型、分析维度等配置
 */

import { cn, formatDate, formatDateTime } from "../../lib/utils";

export { cn, formatDate, formatDateTime };

// ==================== 满意度评分等级配置 ====================
export const satisfactionScoreConfig = {
  excellent: {
    label: "非常满意",
    value: 5,
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    progress: "bg-emerald-500",
    description: "超出预期，体验极佳"
  },
  good: {
    label: "满意",
    value: 4,
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    progress: "bg-blue-500",
    description: "符合预期，体验良好"
  },
  average: {
    label: "一般",
    value: 3,
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    progress: "bg-amber-500",
    description: "基本符合预期，有改进空间"
  },
  poor: {
    label: "不满意",
    value: 2,
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    progress: "bg-orange-500",
    description: "未达预期，需要改进"
  },
  terrible: {
    label: "非常不满意",
    value: 1,
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    progress: "bg-red-500",
    description: "远低于预期，急需改进"
  }
};

// ==================== 反馈类型配置 ====================
export const feedbackTypeConfig = {
  product_quality: {
    label: "产品质量",
    value: "product_quality",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "Package"
  },
  service_support: {
    label: "服务支持",
    value: "service_support",
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    icon: "Headphones"
  },
  delivery_speed: {
    label: "交付速度",
    value: "delivery_speed",
    color: "text-purple-400 bg-purple-400/10 border-purple-400/30",
    icon: "Truck"
  },
  technical_solution: {
    label: "技术方案",
    value: "technical_solution",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    icon: "Cpu"
  },
  communication: {
    label: "沟通协调",
    value: "communication",
    color: "text-cyan-400 bg-cyan-400/10 border-cyan-400/30",
    icon: "MessageCircle"
  },
  price_value: {
    label: "价格价值",
    value: "price_value",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    icon: "DollarSign"
  },
  after_sales: {
    label: "售后服务",
    value: "after_sales",
    color: "text-pink-400 bg-pink-400/10 border-pink-400/30",
    icon: "Wrench"
  }
};

// ==================== 反馈状态配置 ====================
export const feedbackStatusConfig = {
  pending: {
    label: "待处理",
    value: "pending",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    icon: "Clock"
  },
  in_progress: {
    label: "处理中",
    value: "in_progress",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "RefreshCw"
  },
  resolved: {
    label: "已解决",
    value: "resolved",
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    icon: "CheckCircle2"
  },
  closed: {
    label: "已关闭",
    value: "closed",
    color: "text-slate-400 bg-slate-400/10 border-slate-400/30",
    icon: "XCircle"
  }
};

// ==================== 优先级配置 ====================
export const priorityConfig = {
  critical: {
    label: "紧急",
    value: "critical",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    icon: "AlertTriangle",
    responseTime: "2小时内"
  },
  high: {
    label: "高",
    value: "high",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    icon: "AlertCircle",
    responseTime: "24小时内"
  },
  medium: {
    label: "中",
    value: "medium",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    icon: "AlertSquare",
    responseTime: "3天内"
  },
  low: {
    label: "低",
    value: "low",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "Info",
    responseTime: "1周内"
  }
};

// ==================== 分析维度配置 ====================
export const analysisDimensionConfig = {
  overall_satisfaction: {
    label: "总体满意度",
    key: "overall_satisfaction",
    description: "客户对产品/服务的整体评价",
    weight: 0.25
  },
  product_performance: {
    label: "产品性能",
    key: "product_performance",
    description: "产品质量、稳定性、功能满足度",
    weight: 0.2
  },
  service_quality: {
    label: "服务质量",
    key: "service_quality",
    description: "响应速度、解决问题能力、服务态度",
    weight: 0.2
  },
  delivery_experience: {
    label: "交付体验",
    key: "delivery_experience",
    description: "交付准时性、包装质量、文档完整性",
    weight: 0.15
  },
  technical_support: {
    label: "技术支持",
    key: "technical_support",
    description: "技术方案、培训、售后服务",
    weight: 0.2
  }
};

// ==================== 默认数据配置 ====================
export const DEFAULT_SATISFACTION_STATS = {
  totalResponses: 0,
  averageScore: 0,
  responseRate: 0,
  positiveRate: 0,
  resolvedRate: 0,
  pendingFeedback: 0,
  totalCustomers: 0,
  satisfiedCustomers: 0
};

export const DEFAULT_FEEDBACK_DATA = {
  id: "",
  customerId: "",
  customerName: "",
  customerLevel: "regular",
  rating: 0,
  feedbackType: "product_quality",
  content: "",
  status: "pending",
  priority: "medium",
  createdAt: "",
  resolvedAt: "",
  assignedTo: "",
  resolution: ""
};

// ==================== 快速筛选配置 ====================
export const QUICK_FILTER_OPTIONS = [
  {
    key: "all",
    label: "全部反馈",
    filter: () => true
  },
  {
    key: "pending",
    label: "待处理",
    filter: (item) => item.status === "pending"
  },
  {
    key: "in_progress",
    label: "处理中",
    filter: (item) => item.status === "in_progress"
  },
  {
    key: "resolved",
    label: "已解决",
    filter: (item) => item.status === "resolved"
  },
  {
    key: "high_priority",
    label: "高优先级",
    filter: (item) => ["critical", "high"].includes(item.priority)
  },
  {
    key: "positive",
    label: "正面反馈",
    filter: (item) => item.rating >= 4
  },
  {
    key: "negative",
    label: "负面反馈",
    filter: (item) => item.rating <= 2
  }
];

// ==================== 图表类型配置 ====================
export const CHART_TYPE_CONFIG = {
  trend: {
    label: "满意度趋势",
    value: "trend",
    description: "展示满意度随时间的变化趋势"
  },
  distribution: {
    label: "评分分布",
    value: "distribution",
    description: "展示各评分等级的分布情况"
  },
  type_analysis: {
    label: "类型分析",
    value: "type_analysis",
    description: "按反馈类型分析满意度情况"
  },
  department: {
    label: "部门对比",
    value: "department",
    description: "不同部门的满意度对比"
  },
  customer_segment: {
    label: "客户分层",
    value: "customer_segment",
    description: "不同客户等级的满意度对比"
  }
};

// ==================== 工具函数 ====================

// 获取满意度评分配置
export const getSatisfactionScoreConfig = (score) => {
  if (score >= 5) {return satisfactionScoreConfig.excellent;}
  if (score >= 4) {return satisfactionScoreConfig.good;}
  if (score >= 3) {return satisfactionScoreConfig.average;}
  if (score >= 2) {return satisfactionScoreConfig.poor;}
  return satisfactionScoreConfig.terrible;
};

// 获取反馈类型配置
export const getFeedbackTypeConfig = (type) => {
  return feedbackTypeConfig[type] || feedbackTypeConfig.product_quality;
};

// 获取反馈状态配置
export const getFeedbackStatusConfig = (status) => {
  return feedbackStatusConfig[status] || feedbackStatusConfig.pending;
};

// 获取优先级配置
export const getPriorityConfig = (priority) => {
  return priorityConfig[priority] || priorityConfig.medium;
};

// 格式化满意度评分
export const formatSatisfactionScore = (score) => {
  if (!score) {return "-";}
  return `${score.toFixed(1)}分`;
};

// 计算满意度等级
export const getSatisfactionLevel = (score) => {
  if (score >= 4.5) {return "excellent";}
  if (score >= 3.5) {return "good";}
  if (score >= 2.5) {return "average";}
  if (score >= 1.5) {return "poor";}
  return "terrible";
};

// 计算正面反馈比例
export const calculatePositiveRate = (feedbacks) => {
  if (!feedbacks || feedbacks.length === 0) {return 0;}
  const positiveCount = feedbacks.filter(f => f.rating >= 4).length;
  return ((positiveCount / feedbacks.length) * 100).toFixed(1);
};

// 计算解决率
export const calculateResolutionRate = (feedbacks) => {
  if (!feedbacks || feedbacks.length === 0) {return 0;}
  const resolvedCount = feedbacks.filter(f => ["resolved", "closed"].includes(f.status)).length;
  return ((resolvedCount / feedbacks.length) * 100).toFixed(1);
};

// 生成满意度颜色
export const getSatisfactionColor = (score) => {
  const config = getSatisfactionScoreConfig(score);
  return config.color;
};

// ==================== 兼容导出（来自 customerSatisfactionConstants.js）====================

// 满意度等级配置（简化版，用于向后兼容）
export const SATISFACTION_LEVELS = {
  VERY_SATISFIED: { value: 5, label: '非常满意', color: '#52c41a', icon: '😊' },
  SATISFIED: { value: 4, label: '满意', color: '#1890ff', icon: '🙂' },
  NEUTRAL: { value: 3, label: '一般', color: '#faad14', icon: '😐' },
  DISSATISFIED: { value: 2, label: '不满意', color: '#ff7a45', icon: '😕' },
  VERY_DISSATISFIED: { value: 1, label: '非常不满意', color: '#ff4d4f', icon: '😞' }
};

// 调研状态配置
export const SURVEY_STATUS = {
  DRAFT: { value: 'draft', label: '草稿', color: '#d9d9d9' },
  ACTIVE: { value: 'active', label: '进行中', color: '#52c41a' },
  COMPLETED: { value: 'completed', label: '已完成', color: '#1890ff' },
  CANCELLED: { value: 'cancelled', label: '已取消', color: '#ff4d4f' }
};

// 调研类型配置
export const SURVEY_TYPES = {
  SERVICE: { value: 'service', label: '服务满意度' },
  PRODUCT: { value: 'product', label: '产品满意度' },
  SUPPORT: { value: 'support', label: '技术支持满意度' },
  OVERALL: { value: 'overall', label: '综合满意度' }
};

// 问题类型配置
export const QUESTION_TYPES = {
  RATING: { value: 'rating', label: '评分题' },
  TEXT: { value: 'text', label: '文本题' },
  CHOICE: { value: 'choice', label: '选择题' },
  MULTIPLE_CHOICE: { value: 'multiple_choice', label: '多选题' }
};

// 分析周期配置
export const ANALYSIS_PERIODS = {
  WEEK: { value: 'week', label: '最近一周' },
  MONTH: { value: 'month', label: '最近一月' },
  QUARTER: { value: 'quarter', label: '最近一季' },
  YEAR: { value: 'year', label: '最近一年' }
};

// 反馈分类配置
export const FEEDBACK_CATEGORIES = {
  QUALITY: { value: 'quality', label: '质量问题' },
  SERVICE: { value: 'service', label: '服务问题' },
  DELIVERY: { value: 'delivery', label: '交付问题' },
  COMMUNICATION: { value: 'communication', label: '沟通问题' },
  PRICING: { value: 'pricing', label: '价格问题' },
  OTHER: { value: 'other', label: '其他问题' }
};

// 图表颜色配置
export const CHART_COLORS = {
  POSITIVE: '#52c41a',
  NEUTRAL: '#faad14',
  NEGATIVE: '#ff4d4f',
  PRIMARY: '#1890ff',
  SECONDARY: '#722ed1'
};

// 导出格式配置
export const EXPORT_FORMATS = {
  EXCEL: { value: 'excel', label: 'Excel表格' },
  PDF: { value: 'pdf', label: 'PDF报告' },
  CSV: { value: 'csv', label: 'CSV数据' },
  JSON: { value: 'json', label: 'JSON数据' }
};

// 默认筛选配置
export const DEFAULT_FILTERS = {
  dateRange: null,
  surveyType: null,
  status: null,
  satisfactionLevel: null,
  category: null
};

// 表格配置
export const TABLE_CONFIG = {
  pagination: { pageSize: 10, showSizeChanger: true },
  scroll: { x: 1200, y: 400 },
  size: 'middle'
};

// 导出配置对象
export const satisfactionConstants = {
  satisfactionScoreConfig,
  feedbackTypeConfig,
  feedbackStatusConfig,
  priorityConfig,
  analysisDimensionConfig,
  DEFAULT_SATISFACTION_STATS,
  DEFAULT_FEEDBACK_DATA,
  QUICK_FILTER_OPTIONS,
  CHART_TYPE_CONFIG,
  // 兼容导出
  SATISFACTION_LEVELS,
  SURVEY_STATUS,
  SURVEY_TYPES,
  QUESTION_TYPES,
  ANALYSIS_PERIODS,
  FEEDBACK_CATEGORIES,
  CHART_COLORS,
  EXPORT_FORMATS,
  DEFAULT_FILTERS,
  TABLE_CONFIG,
};