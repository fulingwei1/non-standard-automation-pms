/**
 * Customer Satisfaction Constants
 * 客户满意度管理系统常量配置
 */

export const SATISFACTION_LEVELS = {
  VERY_SATISFIED: { value: 5, label: '非常满意', color: '#52c41a', icon: '😊' },
  SATISFIED: { value: 4, label: '满意', color: '#1890ff', icon: '🙂' },
  NEUTRAL: { value: 3, label: '一般', color: '#faad14', icon: '😐' },
  DISSATISFIED: { value: 2, label: '不满意', color: '#ff7a45', icon: '😕' },
  VERY_DISSATISFIED: { value: 1, label: '非常不满意', color: '#ff4d4f', icon: '😞' }
};

export const SURVEY_STATUS = {
  DRAFT: { value: 'draft', label: '草稿', color: '#d9d9d9' },
  ACTIVE: { value: 'active', label: '进行中', color: '#52c41a' },
  COMPLETED: { value: 'completed', label: '已完成', color: '#1890ff' },
  CANCELLED: { value: 'cancelled', label: '已取消', color: '#ff4d4f' }
};

export const SURVEY_TYPES = {
  SERVICE: { value: 'service', label: '服务满意度' },
  PRODUCT: { value: 'product', label: '产品满意度' },
  SUPPORT: { value: 'support', label: '技术支持满意度' },
  OVERALL: { value: 'overall', label: '综合满意度' }
};

export const QUESTION_TYPES = {
  RATING: { value: 'rating', label: '评分题' },
  TEXT: { value: 'text', label: '文本题' },
  CHOICE: { value: 'choice', label: '选择题' },
  MULTIPLE_CHOICE: { value: 'multiple_choice', label: '多选题' }
};

export const ANALYSIS_PERIODS = {
  WEEK: { value: 'week', label: '最近一周' },
  MONTH: { value: 'month', label: '最近一月' },
  QUARTER: { value: 'quarter', label: '最近一季' },
  YEAR: { value: 'year', label: '最近一年' }
};

export const FEEDBACK_CATEGORIES = {
  QUALITY: { value: 'quality', label: '质量问题' },
  SERVICE: { value: 'service', label: '服务问题' },
  DELIVERY: { value: 'delivery', label: '交付问题' },
  COMMUNICATION: { value: 'communication', label: '沟通问题' },
  PRICING: { value: 'pricing', label: '价格问题' },
  OTHER: { value: 'other', label: '其他问题' }
};

export const CHART_COLORS = {
  POSITIVE: '#52c41a',
  NEUTRAL: '#faad14',
  NEGATIVE: '#ff4d4f',
  PRIMARY: '#1890ff',
  SECONDARY: '#722ed1'
};

export const EXPORT_FORMATS = {
  EXCEL: { value: 'excel', label: 'Excel表格' },
  PDF: { value: 'pdf', label: 'PDF报告' },
  CSV: { value: 'csv', label: 'CSV数据' },
  JSON: { value: 'json', label: 'JSON数据' }
};

export const DEFAULT_FILTERS = {
  dateRange: null,
  surveyType: null,
  status: null,
  satisfactionLevel: null,
  category: null
};

export const TABLE_CONFIG = {
  pagination: { pageSize: 10, showSizeChanger: true },
  scroll: { x: 1200, y: 400 },
  size: 'middle'
};