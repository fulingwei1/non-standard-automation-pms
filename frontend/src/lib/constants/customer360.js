/**
 * Customer 360 View Constants
 * 客户360度视图系统常量配置
 */

export const CUSTOMER_TYPES = {
  ENTERPRISE: { value: 'enterprise', label: '企业客户', color: '#1890ff', icon: '🏢' },
  SMB: { value: 'smb', label: '中小企业', color: '#52c41a', icon: '🏪' },
  INDIVIDUAL: { value: 'individual', label: '个人客户', color: '#722ed1', icon: '👤' },
  GOVERNMENT: { value: 'government', label: '政府机构', color: '#faad14', icon: '🏛️' },
  EDUCATION: { value: 'education', label: '教育机构', color: '#13c2c2', icon: '🎓' }
};

export const CUSTOMER_STATUS = {
  ACTIVE: { value: 'active', label: '活跃客户', color: '#52c41a' },
  INACTIVE: { value: 'inactive', label: '非活跃客户', color: '#8c8c8c' },
  PROSPECT: { value: 'prospect', label: '潜在客户', color: '#1890ff' },
  CHURNED: { value: 'churned', label: '流失客户', color: '#ff4d4f' },
  SUSPENDED: { value: 'suspended', label: '暂停合作', color: '#faad14' }
};

export const CUSTOMER_LEVELS = {
  PLATINUM: { value: 'platinum', label: '铂金客户', color: '#722ed1', minOrder: 1000000 },
  GOLD: { value: 'gold', label: '黄金客户', color: '#faad14', minOrder: 500000 },
  SILVER: { value: 'silver', label: '白银客户', color: '#8c8c8c', minOrder: 100000 },
  BRONZE: { value: 'bronze', label: '青铜客户', color: '#d46b08', minOrder: 50000 }
};

export const ORDER_STATUS = {
  DRAFT: { value: 'draft', label: '草稿', color: '#d9d9d9' },
  CONFIRMED: { value: 'confirmed', label: '已确认', color: '#1890ff' },
  IN_PRODUCTION: { value: 'in_production', label: '生产中', color: '#faad14' },
  SHIPPED: { value: 'shipped', label: '已发货', color: '#722ed1' },
  DELIVERED: { value: 'delivered', label: '已交付', color: '#52c41a' },
  CANCELLED: { value: 'cancelled', label: '已取消', color: '#ff4d4f' }
};

export const PAYMENT_STATUS = {
  PENDING: { value: 'pending', label: '待支付', color: '#faad14' },
  PARTIAL: { value: 'partial', label: '部分支付', color: '#1890ff' },
  PAID: { value: 'paid', label: '已支付', color: '#52c41a' },
  OVERDUE: { value: 'overdue', label: '逾期未付', color: '#ff4d4f' },
  REFUNDED: { value: 'refunded', label: '已退款', color: '#722ed1' }
};

export const SERVICE_LEVELS = {
  PREMIUM: { value: 'premium', label: '高级服务', color: '#722ed1', responseTime: '2小时' },
  STANDARD: { value: 'standard', label: '标准服务', color: '#1890ff', responseTime: '24小时' },
  BASIC: { value: 'basic', label: '基础服务', color: '#52c41a', responseTime: '72小时' }
};

export const SATISFACTION_SCORES = {
  EXCELLENT: { min: 4.5, max: 5, label: '非常满意', color: '#52c41a' },
  GOOD: { min: 3.5, max: 4.5, label: '满意', color: '#1890ff' },
  AVERAGE: { min: 2.5, max: 3.5, label: '一般', color: '#faad14' },
  POOR: { min: 1, max: 2.5, label: '不满意', color: '#ff4d4f' }
};

export const PROJECT_PHASES = {
  REQUIREMENT: { value: 'requirement', label: '需求分析', color: '#1890ff' },
  DESIGN: { value: 'design', label: '方案设计', color: '#722ed1' },
  DEVELOPMENT: { value: 'development', label: '开发实施', color: '#faad14' },
  TESTING: { value: 'testing', label: '测试验收', color: '#13c2c2' },
  DEPLOYMENT: { value: 'deployment', label: '部署上线', color: '#52c41a' },
  MAINTENANCE: { value: 'maintenance', label: '运维支持', color: '#8c8c8c' }
};

export const COMMUNICATION_CHANNELS = {
  PHONE: { value: 'phone', label: '电话', icon: '📞' },
  EMAIL: { value: 'email', label: '邮件', icon: '📧' },
  WECHAT: { value: 'wechat', label: '微信', icon: '💬' },
  MEETING: { value: 'meeting', label: '会议', icon: '🤝' },
  SITE_VISIT: { value: 'site_visit', label: '现场拜访', icon: '📍' }
};

export const BUSINESS_METRICS = {
  LIFETIME_VALUE: { label: '客户终身价值', unit: '元' },
  PURCHASE_FREQUENCY: { label: '购买频率', unit: '次/年' },
  AVERAGE_ORDER: { label: '平均订单金额', unit: '元' },
  RESPONSE_TIME: { label: '平均响应时间', unit: '小时' },
  SATISFACTION_RATE: { label: '满意度', unit: '分' },
  PROJECT_SUCCESS_RATE: { label: '项目成功率', unit: '%' }
};

export const TABLE_CONFIG = {
  pagination: { pageSize: 10, showSizeChanger: true },
  scroll: { x: 1200, y: 400 },
  size: 'middle'
};

export const CHART_COLORS = {
  PRIMARY: '#1890ff',
  SUCCESS: '#52c41a',
  WARNING: '#faad14',
  ERROR: '#ff4d4f',
  PURPLE: '#722ed1',
  CYAN: '#13c2c2'
};

export const DEFAULT_FILTERS = {
  dateRange: null,
  status: null,
  type: null,
  level: null
};