/**
 * Customer Service Constants
 * 客服管理系统常量配置
 */

export const SERVICE_TYPES = {
  TECHNICAL_SUPPORT: { value: 'technical_support', label: '技术支持', color: '#1890ff', icon: '🔧' },
  FIELD_SERVICE: { value: 'field_service', label: '现场服务', color: '#52c41a', icon: '👷' },
  WARRANTY: { value: 'warranty', label: '质保服务', color: '#faad14', icon: '🛡️' },
  TRAINING: { value: 'training', label: '培训服务', color: '#722ed1', icon: '📚' },
  CONSULTATION: { value: 'consultation', label: '咨询服务', color: '#13c2c2', icon: '💡' },
  MAINTENANCE: { value: 'maintenance', label: '维护服务', color: '#eb2f96', icon: '🔨' }
};

export const TICKET_STATUS = {
  OPEN: { value: 'open', label: '待处理', color: '#ff4d4f' },
  IN_PROGRESS: { value: 'in_progress', label: '处理中', color: '#faad14' },
  PENDING_CUSTOMER: { value: 'pending_customer', label: '待客户确认', color: '#1890ff' },
  RESOLVED: { value: 'resolved', label: '已解决', color: '#52c41a' },
  CLOSED: { value: 'closed', label: '已关闭', color: '#8c8c8c' },
  REOPENED: { value: 'reopened', label: '重新打开', color: '#722ed1' }
};

export const PRIORITY_LEVELS = {
  CRITICAL: { value: 'critical', label: '紧急', color: '#ff4d4f', weight: 4, responseTime: '1小时' },
  HIGH: { value: 'high', label: '高', color: '#fa8c16', weight: 3, responseTime: '4小时' },
  MEDIUM: { value: 'medium', label: '中', color: '#1890ff', weight: 2, responseTime: '24小时' },
  LOW: { value: 'low', label: '低', color: '#52c41a', weight: 1, responseTime: '72小时' }
};

export const SATISFACTION_LEVELS = {
  VERY_SATISFIED: { value: 'very_satisfied', label: '非常满意', color: '#52c41a', score: 5 },
  SATISFIED: { value: 'satisfied', label: '满意', color: '#1890ff', score: 4 },
  NEUTRAL: { value: 'neutral', label: '一般', color: '#faad14', score: 3 },
  DISSATISFIED: { value: 'dissatisfied', label: '不满意', color: '#fa8c16', score: 2 },
  VERY_DISSATISFIED: { value: 'very_dissatisfied', label: '非常不满意', color: '#ff4d4f', score: 1 }
};

export const SERVICE_PHASES = {
  S1: { value: 's1', label: '需求分析', description: '客户需求收集与分析' },
  S2: { value: 's2', label: '方案设计', description: '技术方案设计' },
  S3: { value: 's3', label: '设备采购', description: '设备材料采购' },
  S4: { value: 's4', label: '施工准备', description: '现场施工准备' },
  S5: { value: 's5', label: '安装施工', description: '设备安装施工' },
  S6: { value: 's6', label: '系统调试', description: '系统集成调试' },
  S7: { value: 's7', label: '初步验收', description: '初步验收测试' },
  S8: { value: 's8', label: '现场交付', description: '现场交付使用' },
  S9: { value: 's9', label: '质保结项', description: '质保期结束结项' }
};

export const RESPONSE_CHANNELS = {
  PHONE: { value: 'phone', label: '电话', icon: '📞' },
  EMAIL: { value: 'email', label: '邮件', icon: '📧' },
  WEBSITE: { value: 'website', label: '官网', icon: '🌐' },
  WECHAT: { value: 'wechat', label: '微信', icon: '💬' },
  SYSTEM: { value: 'system', label: '系统', icon: '💻' },
  ON_SITE: { value: 'on_site', label: '现场', icon: '📍' }
};

export const RESOLUTION_METHODS = {
  REMOTE: { value: 'remote', label: '远程解决', icon: '🌐' },
  ON_SITE: { value: 'on_site', label: '现场处理', icon: '👷' },
  REPLACEMENT: { value: 'replacement', label: '更换设备', icon: '🔄' },
  REPAIR: { value: 'repair', label: '维修处理', icon: '🔧' },
  TRAINING: { value: 'training', label: '培训指导', icon: '📚' },
  ESCALATION: { value: 'escalation', label: '升级处理', icon: '⬆️' }
};

export const WARRANTY_TYPES = {
  STANDARD: { value: 'standard', label: '标准质保', duration: '12个月' },
  EXTENDED: { value: 'extended', label: '延长质保', duration: '24个月' },
  PREMIUM: { value: 'premium', label: '高级质保', duration: '36个月' },
  LIFETIME: { value: 'lifetime', label: '终身质保', duration: '永久' }
};

export const PERFORMANCE_METRICS = {
  RESPONSE_TIME: { label: '响应时间', unit: '小时', target: 4 },
  RESOLUTION_TIME: { label: '解决时间', unit: '小时', target: 24 },
  FIRST_CONTACT_RESOLUTION: { label: '首次解决率', unit: '%', target: 75 },
  CUSTOMER_SATISFACTION: { label: '客户满意度', unit: '分', target: 4.5 },
  SERVICE_LEVEL_AGREEMENT: { label: 'SLA达成率', unit: '%', target: 95 }
};

export const ESCALATION_LEVELS = {
  L1: { value: 'l1', label: 'L1客服', description: '一线客服支持' },
  L2: { value: 'l2', label: 'L2技术', description: '二线技术支持' },
  L3: { value: 'l3', label: 'L3专家', description: '三线专家支持' },
  L4: { value: 'l4', label: 'L4研发', description: '研发团队支持' }
};

export const TABLE_CONFIG = {
  pagination: { pageSize: 10, showSizeChanger: true },
  scroll: { x: 1400, y: 500 },
  size: 'middle'
};

export const CHART_COLORS = {
  POSITIVE: '#52c41a',
  WARNING: '#faad14',
  NEGATIVE: '#ff4d4f',
  PRIMARY: '#1890ff',
  SECONDARY: '#722ed1'
};

export const DEFAULT_FILTERS = {
  status: null,
  priority: null,
  serviceType: null,
  dateRange: null,
  engineer: null
};