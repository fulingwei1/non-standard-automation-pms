/**
 * Lead Assessment Constants
 * 线索评估系统常量配置
 */

export const LEAD_SOURCES = [
  { value: 'website', label: '官网', color: '#1890ff', weight: 3, score: 15, icon: '🌐' },
  { value: 'referral', label: '推荐', color: '#52c41a', weight: 5, score: 25, icon: '🤝' },
  { value: 'cold_call', label: '电销', color: '#faad14', weight: 2, score: 10, icon: '☎️' },
  { value: 'exhibition', label: '展会', color: '#722ed1', weight: 4, score: 20, icon: '🏟️' },
  { value: 'social_media', label: '社交媒体', color: '#13c2c2', weight: 3, score: 15, icon: '📣' },
  { value: 'advertising', label: '广告', color: '#eb2f96', weight: 2, score: 10, icon: '📢' },
  { value: 'partner', label: '合作伙伴', color: '#f5222d', weight: 4, score: 20, icon: '🧩' },
  { value: 'other', label: '其他', color: '#8c8c8c', weight: 1, score: 5, icon: '📌' }
];

export const LEAD_STATUS = {
  NEW: { value: 'new', label: '新线索', color: '#1890ff' },
  CONTACTED: { value: 'contacted', label: '已联系', color: '#52c41a' },
  QUALIFIED: { value: 'qualified', label: '已合格', color: '#13c2c2' },
  CONVERTED: { value: 'converted', label: '已转化', color: '#722ed1' },
  LOST: { value: 'lost', label: '已流失', color: '#ff4d4f' },
  UNQUALIFIED: { value: 'unqualified', label: '不合格', color: '#8c8c8c' }
};

export const QUALIFICATION_LEVELS = {
  HOT: { value: 'hot', label: '热线索', color: '#ff4d4f', score: { min: 80, max: 100 }, priority: 1 },
  WARM: { value: 'warm', label: '温线索', color: '#faad14', score: { min: 60, max: 79 }, priority: 2 },
  COLD: { value: 'cold', label: '冷线索', color: '#1890ff', score: { min: 40, max: 59 }, priority: 3 },
  UNQUALIFIED: { value: 'unqualified', label: '不合格', color: '#8c8c8c', score: { min: 0, max: 39 }, priority: 4 }
};

export const INDUSTRY_TYPES = {
  MANUFACTURING: { value: 'manufacturing', label: '制造业', weight: 4 },
  TECHNOLOGY: { value: 'technology', label: '科技', weight: 5 },
  HEALTHCARE: { value: 'healthcare', label: '医疗', weight: 4 },
  EDUCATION: { value: 'education', label: '教育', weight: 3 },
  FINANCE: { value: 'finance', label: '金融', weight: 5 },
  RETAIL: { value: 'retail', label: '零售', weight: 2 },
  CONSTRUCTION: { value: 'construction', label: '建筑', weight: 4 },
  ENERGY: { value: 'energy', label: '能源', weight: 5 },
  GOVERNMENT: { value: 'government', label: '政府', weight: 3 },
  OTHER: { value: 'other', label: '其他', weight: 2 }
};

export const COMPANY_SIZES = {
  STARTUP: { value: 'startup', label: '初创企业', weight: 2, employees: '1-10' },
  SMALL: { value: 'small', label: '小型企业', weight: 3, employees: '11-50' },
  MEDIUM: { value: 'medium', label: '中型企业', weight: 4, employees: '51-200' },
  LARGE: { value: 'large', label: '大型企业', weight: 5, employees: '201-1000' },
  ENTERPRISE: { value: 'enterprise', label: '企业集团', weight: 5, employees: '1000+' }
};

export const BUDGET_RANGES = [
  { value: 'low', label: '低预算', description: '0-10万', weight: 1 },
  { value: 'medium', label: '中等预算', description: '10-50万', weight: 3 },
  { value: 'high', label: '高预算', description: '50-100万', weight: 4 },
  { value: 'very_high', label: '超高预算', description: '100万+', weight: 5 }
];

export const LEAD_STATUSES = Object.values(LEAD_STATUS);

export const LEAD_PRIORITIES = [
  { value: 'urgent', label: '紧急', color: '#ff4d4f', weight: 4 },
  { value: 'high', label: '高', color: '#fa8c16', weight: 3 },
  { value: 'medium', label: '中', color: '#1890ff', weight: 2 },
  { value: 'low', label: '低', color: '#52c41a', weight: 1 }
];

export const LEAD_TYPES = [
  { value: 'new', label: '新客户', score: 5 },
  { value: 'existing', label: '存量客户', score: 3 },
  { value: 'partner', label: '合作伙伴', score: 4 },
  { value: 'unknown', label: '未知', score: 0 }
];

export const INDUSTRIES = Object.values(INDUSTRY_TYPES).map((industry) => ({
  value: industry.value,
  label: industry.label,
  priority: industry.weight ?? 1
}));

export const DECISION_TIMELINES = [
  { value: 'immediate', label: '1个月内', score: 5 },
  { value: 'short', label: '1-3个月', score: 4 },
  { value: 'medium', label: '3-6个月', score: 3 },
  { value: 'long', label: '6-12个月', score: 2 },
  { value: 'very_long', label: '12个月以上', score: 1 }
];

export const SCORE_THRESHOLDS = {
  excellent: { min: 80, label: '优秀', color: '#52c41a' },
  good: { min: 60, max: 79.99, label: '良好', color: '#1890ff' },
  average: { min: 40, max: 59.99, label: '一般', color: '#faad14' },
  poor: { max: 39.99, label: '较差', color: '#ff4d4f' }
};

export const FOLLOW_UP_STRATEGIES = [
  { minScore: 80, strategy: '重点推进', frequency: 'daily', description: '高优先级强跟进，建议每日同步关键人并推动下一步。' },
  { minScore: 60, strategy: '积极跟进', frequency: 'every_2_days', description: '保持高频触达，尽快完成需求澄清和方案呈现。' },
  { minScore: 40, strategy: '定期跟进', frequency: 'weekly', description: '持续培育机会，按周推进关键节点与客户沟通。' },
  { minScore: 0, strategy: '低优先级培养', frequency: 'biweekly', description: '保持低频触达，聚焦线索质量提升与需求确认。' }
];

export const SCORING_CATEGORIES = [
  { id: 'budget', name: '预算匹配', weight: 25 },
  { id: 'authority', name: '决策权限', weight: 20 },
  { id: 'need', name: '需求强度', weight: 25 },
  { id: 'timeline', name: '决策周期', weight: 15 },
  { id: 'competition', name: '竞争态势', weight: 15 }
];

export const ASSESSMENT_QUESTIONS = {
  budget: [
    {
      id: 'budget_range',
      question: '预算范围是否明确？',
      type: 'select',
      weight: 1,
      options: [
        { value: 'unknown', label: '不明确', score: 1 },
        { value: 'rough', label: '大致明确', score: 3 },
        { value: 'clear', label: '非常明确', score: 5 }
      ]
    },
    {
      id: 'budget_fit',
      question: '预算与预期方案匹配度',
      type: 'rating',
      weight: 1
    }
  ],
  authority: [
    {
      id: 'decision_maker_access',
      question: '是否能直接触达决策人？',
      type: 'boolean',
      weight: 1
    },
    {
      id: 'decision_level',
      question: '决策层级清晰度',
      type: 'select',
      weight: 1,
      options: [
        { value: 'low', label: '不清晰', score: 1 },
        { value: 'medium', label: '部分清晰', score: 3 },
        { value: 'high', label: '非常清晰', score: 5 }
      ]
    }
  ],
  need: [
    {
      id: 'pain_level',
      question: '痛点强度/价值驱动程度',
      type: 'rating',
      weight: 1
    },
    {
      id: 'urgency',
      question: '需求是否紧急？',
      type: 'boolean',
      weight: 1
    }
  ],
  timeline: [
    {
      id: 'decision_timeline',
      question: '预计决策周期',
      type: 'select',
      weight: 1,
      options: [
        { value: 'immediate', label: '1个月内', score: 5 },
        { value: 'short', label: '1-3个月', score: 4 },
        { value: 'medium', label: '3-6个月', score: 3 },
        { value: 'long', label: '6-12个月', score: 2 },
        { value: 'very_long', label: '12个月以上', score: 1 }
      ]
    }
  ],
  competition: [
    {
      id: 'strong_competitor',
      question: '是否存在强势竞争对手？',
      type: 'boolean',
      weight: 1
    },
    {
      id: 'our_advantage',
      question: '我方优势明确程度',
      type: 'rating',
      weight: 1
    }
  ]
};

export const DECISION_MAKER_ROLES = {
  CEO: { value: 'ceo', label: 'CEO/总裁', weight: 5 },
  CTO: { value: 'cto', label: 'CTO/技术总监', weight: 4 },
  CMO: { value: 'cmo', label: 'CMO/营销总监', weight: 4 },
  PROCUREMENT: { value: 'procurement', label: '采购总监', weight: 3 },
  MANAGER: { value: 'manager', label: '部门经理', weight: 2 },
  SPECIALIST: { value: 'specialist', label: '专员', weight: 1 },
  OTHER: { value: 'other', label: '其他', weight: 1 }
};

export const ASSESSMENT_CRITERIA = {
  BUDGET: { label: '预算充足度', weight: 0.25, maxScore: 25 },
  AUTHORITY: { label: '决策权限', weight: 0.20, maxScore: 20 },
  NEED: { label: '需求紧迫性', weight: 0.25, maxScore: 25 },
  TIMELINE: { label: '时间计划', weight: 0.15, maxScore: 15 },
  COMPETITION: { label: '竞争情况', weight: 0.15, maxScore: 15 }
};

export const FOLLOW_UP_STATUS = {
  PENDING: { value: 'pending', label: '待跟进', color: '#faad14' },
  COMPLETED: { value: 'completed', label: '已完成', color: '#52c41a' },
  OVERDUE: { value: 'overdue', label: '已逾期', color: '#ff4d4f' },
  CANCELLED: { value: 'cancelled', label: '已取消', color: '#8c8c8c' }
};

export const TASK_TYPES = {
  CALL: { value: 'call', label: '电话沟通', icon: '📞' },
  MEETING: { value: 'meeting', label: '面谈拜访', icon: '🤝' },
  EMAIL: { value: 'email', label: '邮件跟进', icon: '📧' },
  PROPOSAL: { value: 'proposal', label: '方案发送', icon: '📋' },
  DEMO: { value: 'demo', label: '产品演示', icon: '🎯' },
  FOLLOW_UP: { value: 'follow_up', label: '常规跟进', icon: '🔄' }
};

export const SCORE_COLORS = {
  EXCELLENT: { min: 90, color: '#52c41a', label: '优秀' },
  GOOD: { min: 70, color: '#1890ff', label: '良好' },
  AVERAGE: { min: 50, color: '#faad14', label: '一般' },
  POOR: { min: 0, color: '#ff4d4f', label: '较差' }
};

export const TABLE_CONFIG = {
  pagination: { pageSize: 10, showSizeChanger: true },
  scroll: { x: 1400, y: 500 },
  size: 'middle'
};

export const DEFAULT_FILTERS = {
  source: null,
  status: null,
  qualification: null,
  industry: null,
  size: null,
  scoreRange: null,
  dateRange: null
};
