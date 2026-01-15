/**
 * Customer 360 Configuration Constants
 * 客户360度视图配置常量
 * 客户数据管理和360度视图相关配置
 */

// ==================== 客户类型配置 ====================
export const customerTypeConfigs = {
  STRATEGIC: {
    label: "战略客户",
    color: "bg-purple-500",
    textColor: "text-purple-50",
    icon: "👑",
    description: "长期合作，高价值客户"
  },
  VIP: {
    label: "VIP客户",
    color: "bg-pink-500",
    textColor: "text-pink-50",
    icon: "⭐",
    description: "高价值，重点维护客户"
  },
  KEY: {
    label: "重点客户",
    color: "bg-blue-500",
    textColor: "text-blue-50",
    icon: "🎯",
    description: "重要业务来源客户"
  },
  REGULAR: {
    label: "普通客户",
    color: "bg-green-500",
    textColor: "text-green-50",
    icon: "👤",
    description: "常规业务往来客户"
  },
  POTENTIAL: {
    label: "潜在客户",
    color: "bg-amber-500",
    textColor: "text-amber-50",
    icon: "🌱",
    description: "具有发展潜力的客户"
  },
  FORMER: {
    label: "流失客户",
    color: "bg-red-500",
    textColor: "text-red-50",
    icon: "❌",
    description: "已停止合作客户"
  },
};

// ==================== 客户状态配置 ====================
export const customerStatusConfigs = {
  ACTIVE: {
    label: "活跃",
    color: "bg-emerald-500",
    textColor: "text-emerald-50",
    icon: "✅",
    description: "正常业务往来中"
  },
  INACTIVE: {
    label: "非活跃",
    color: "bg-slate-500",
    textColor: "text-slate-50",
    icon: "⏸️",
    description: "暂停业务往来"
  },
  PROSPECT: {
    label: "潜在",
    color: "bg-blue-500",
    textColor: "text-blue-50",
    icon: "🔍",
    description: "正在开发中的客户"
  },
  CHURN: {
    label: "流失中",
    color: "bg-orange-500",
    textColor: "text-orange-50",
    icon: "⚠️",
    description: "即将流失风险"
  },
  LOYAL: {
    label: "忠诚",
    color: "bg-green-600",
    textColor: "text-green-50",
    icon: "💖",
    description: "高忠诚度客户"
  },
};

// ==================== 客户行业配置 ====================
export const customerIndustryConfigs = {
  ELECTRONICS: {
    label: "电子行业",
    color: "bg-blue-500",
    textColor: "text-blue-50",
    icon: "💻",
    sub_categories: ["消费电子", "工业电子", "汽车电子", "医疗电子"]
  },
  MANUFACTURING: {
    label: "制造业",
    color: "bg-green-500",
    textColor: "text-green-50",
    icon: "🏭",
    sub_categories: ["机械设备", "自动化设备", "精密制造", "新能源"]
  },
  AUTOMOTIVE: {
    label: "汽车行业",
    color: "bg-red-500",
    textColor: "text-red-50",
    icon: "🚗",
    sub_categories: ["整车制造", "零部件", "新能源汽车", "智能驾驶"]
  },
  AEROSPACE: {
    label: "航空航天",
    color: "bg-indigo-500",
    textColor: "text-indigo-50",
    icon: "✈️",
    sub_categories: ["飞机制造", "航空发动机", "航天器", "航空电子"]
  },
  MEDICAL: {
    label: "医疗设备",
    color: "bg-purple-500",
    textColor: "text-purple-50",
    icon: "🏥",
    sub_categories: ["诊断设备", "治疗设备", "监护设备", "医疗影像"]
  },
  ENERGY: {
    label: "能源行业",
    color: "bg-yellow-500",
    textColor: "text-yellow-50",
    icon: "⚡",
    sub_categories: ["电力设备", "新能源", "储能", "智能电网"]
  },
  COMMUNICATION: {
    label: "通信行业",
    color: "bg-cyan-500",
    textColor: "text-cyan-50",
    icon: "📡",
    sub_categories: ["通信设备", "网络设备", "光通信", "卫星通信"]
  },
  CONSUMER: {
    label: "消费电子",
    color: "bg-pink-500",
    textColor: "text-pink-50",
    icon: "📱",
    sub_categories: ["手机", "电脑", "家电", "智能硬件"]
  },
};

// ==================== 客户来源渠道配置 ====================
export const customerSourceConfigs = {
  REFERRAL: {
    label: "客户推荐",
    color: "bg-green-500",
    textColor: "text-green-50",
    icon: "👥",
    description: "老客户推荐"
  },
  EXHIBITION: {
    label: "展会渠道",
    color: "bg-blue-500",
    textColor: "text-blue-50",
    icon: "🎪",
    description: "行业展会获取"
  },
  ONLINE: {
    label: "线上渠道",
    color: "bg-purple-500",
    textColor: "text-purple-50",
    icon: "🌐",
    description: "网络平台获取"
  },
  DIRECT: {
    label: "直接拜访",
    color: "bg-orange-500",
    textColor: "text-orange-50",
    icon: "🏢",
    description: "主动开发客户"
  },
  PARTNER: {
    label: "合作伙伴",
    color: "bg-teal-500",
    textColor: "text-teal-50",
    icon: "🤝",
    description: "合作伙伴推荐"
  },
  TENDER: {
    label: "招标项目",
    color: "bg-red-500",
    textColor: "text-red-50",
    icon: "📋",
    description: "招标项目获取"
  },
  OTHER: {
    label: "其他来源",
    color: "bg-slate-500",
    textColor: "text-slate-50",
    icon: "📌",
    description: "其他渠道"
  },
};

// ==================== 互动类型配置 ====================
export const interactionTypeConfigs = {
  PHONE: {
    label: "电话沟通",
    color: "bg-blue-500",
    textColor: "text-blue-50",
    icon: "📞",
    duration_range: "10-30分钟"
  },
  EMAIL: {
    label: "邮件往来",
    color: "bg-green-500",
    textColor: "text-green-50",
    icon: "📧",
    duration_range: "异步"
  },
  MEETING: {
    label: "会议",
    color: "bg-purple-500",
    textColor: "text-purple-50",
    icon: "👥",
    duration_range: "30-120分钟"
  },
  VISIT: {
    label: "拜访",
    color: "bg-orange-500",
    textColor: "text-orange-50",
    icon: "🚶",
    duration_range: "1-4小时"
  },
  VIDEO: {
    label: "视频会议",
    color: "bg-red-500",
    textColor: "text-red-50",
    icon: "📹",
    duration_range: "30-60分钟"
  },
  WECHAT: {
    label: "微信沟通",
    color: "bg-emerald-500",
    textColor: "text-emerald-50",
    icon: "💬",
    duration_range: "5-15分钟"
  },
  QUOTE: {
    label: "报价",
    color: "bg-amber-500",
    textColor: "text-amber-50",
    icon: "💰",
    duration_range: "1-3天"
  },
  CONTRACT: {
    label: "合同签订",
    color: "bg-indigo-500",
    textColor: "text-indigo-50",
    icon: "📄",
    duration_range: "1周"
  },
  SERVICE: {
    label: "售后服务",
    color: "bg-pink-500",
    textColor: "text-pink-50",
    icon: "🔧",
    duration_range: "2-4小时"
  },
  COMPLAINT: {
    label: "投诉处理",
    color: "bg-red-600",
    textColor: "text-red-50",
    icon: "⚠️",
    duration_range: "1-3天"
  },
};

// ==================== 合同状态配置 ====================
export const contractStatusConfigs = {
  DRAFT: {
    label: "草稿",
    color: "bg-slate-500",
    textColor: "text-slate-50",
    icon: "📝",
    description: "合同草稿阶段"
  },
  PENDING: {
    label: "待审批",
    color: "bg-yellow-500",
    textColor: "text-yellow-50",
    icon: "⏳",
    description: "等待内部审批"
  },
  NEGOTIATING: {
    label: "洽谈中",
    color: "bg-orange-500",
    textColor: "text-orange-50",
    icon: "🤝",
    description: "与客户洽谈"
  },
  APPROVED: {
    label: "已批准",
    color: "bg-blue-500",
    textColor: "text-blue-50",
    icon: "✅",
    description: "内部审批通过"
  },
  SIGNED: {
    label: "已签约",
    color: "bg-green-500",
    textColor: "text-green-50",
    icon: "✍️",
    description: "双方已签约"
  },
  EXECUTING: {
    label: "执行中",
    color: "bg-purple-500",
    textColor: "text-purple-50",
    icon: "🚀",
    description: "合同执行中"
  },
  COMPLETED: {
    label: "已完成",
    color: "bg-emerald-500",
    textColor: "text-emerald-50",
    icon: "✅",
    description: "合同已履行完毕"
  },
  TERMINATED: {
    label: "已终止",
    color: "bg-red-500",
    textColor: "text-red-50",
    icon: "🛑",
    description: "合同提前终止"
  },
  EXPIRED: {
    label: "已过期",
    color: "bg-gray-500",
    textColor: "text-gray-50",
    icon: "⏰",
    description: "合同已过期"
  },
};

// ==================== 客户评分配置 ====================
export const customerScoreConfigs = {
  EXCELLENT: {
    label: "优秀",
    color: "bg-green-500",
    textColor: "text-green-50",
    score_range: "90-100",
    description: "各方面表现优秀，深度合作"
  },
  GOOD: {
    label: "良好",
    color: "bg-blue-500",
    textColor: "text-blue-50",
    score_range: "80-89",
    description: "表现良好，稳定合作"
  },
  AVERAGE: {
    label: "一般",
    color: "bg-yellow-500",
    textColor: "text-yellow-50",
    score_range: "70-79",
    description: "表现一般，有待提升"
  },
  BELOW_AVERAGE: {
    label: "较差",
    color: "bg-orange-500",
    textColor: "text-orange-50",
    score_range: "60-69",
    description: "表现较差，需要关注"
  },
  POOR: {
    label: "差",
    color: "bg-red-500",
    textColor: "text-red-50",
    score_range: "0-59",
    description: "表现很差，需重点改进"
  },
};

// ==================== 客户标签配置 ====================
export const customerTagConfigs = {
  HIGH_VALUE: {
    label: "高价值",
    color: "bg-purple-500",
    textColor: "text-purple-50",
    icon: "💎",
    description: "年采购额高"
  },
  LONG_TERM: {
    label: "长期合作",
    color: "bg-green-500",
    textColor: "text-green-50",
    icon: "📅",
    description: "合作时间长"
  },
  TECH_LEADER: {
    label: "技术领先",
    color: "bg-blue-500",
    textColor: "text-blue-50",
    icon: "🔬",
    description: "技术要求高"
  },
  PRICE_SENSITIVE: {
    label: "价格敏感",
    color: "bg-orange-500",
    textColor: "text-orange-50",
    icon: "💰",
    description: "对价格敏感"
  },
  QUALITY_FOCUS: {
    label: "质量导向",
    color: "bg-emerald-500",
    textColor: "text-emerald-50",
    icon: "🏆",
    description: "重视质量"
  },
  INNOVATIVE: {
    label: "创新导向",
    color: "bg-pink-500",
    textColor: "text-pink-50",
    icon: "💡",
    description: "喜欢创新"
  },
  RISK_AVERSE: {
    label: "风险规避",
    color: "bg-red-500",
    textColor: "text-red-50",
    icon: "🛡️",
    description: "规避风险"
  },
  FAST_DECISION: {
    label: "决策快速",
    color: "bg-cyan-500",
    textColor: "text-cyan-50",
    icon: "⚡",
    description: "决策速度快"
  },
  INTERNATIONAL: {
    label: "国际客户",
    color: "bg-indigo-500",
    textColor: "text-indigo-50",
    icon: "🌍",
    description: "跨国业务"
  },
  DOMESTIC: {
    label: "国内客户",
    color: "bg-slate-500",
    textColor: "text-slate-50",
    icon: "🇨🇳",
    description: "国内业务"
  },
};

// ==================== Customer 360 Tab 配置 ====================
export const customer360TabConfigs = [
  { value: "overview", label: "客户概览", icon: "📊" },
  { value: "interactions", label: "互动历史", icon: "📝" },
  { value: "purchases", label: "采购记录", icon: "🛒" },
  { value: "projects", label: "项目历史", icon: "🚀" },
  { value: "contracts", label: "合同管理", icon: "📄" },
  { value: "service", label: "服务记录", icon: "🔧" },
  { value: "finance", label: "财务分析", icon: "💰" },
  { value: "team", label: "对接团队", icon: "👥" },
  { value: "notes", label: "备注信息", icon: "📝" },
  { value: "timeline", label: "时间轴", icon: "📅" },
];

// ==================== 默认数据配置 ====================
export const DEFAULT_CUSTOMER_360_DATA = {
  // 基本信息
  basic_info: {
    customer_code: "",
    customer_name: "",
    customer_type: "REGULAR",
    industry: "ELECTRONICS",
    status: "ACTIVE",
    source: "DIRECT",
    established_date: null,
    registration_number: "",
    tax_number: "",
    legal_representative: "",
    contact_person: "",
    position: "",
    phone: "",
    email: "",
    website: "",
    address: "",
    description: "",
  },

  // 联系信息
  contact_info: {
    phone_primary: "",
    phone_secondary: "",
    email_primary: "",
    email_secondary: "",
    fax: "",
    address_shipping: "",
    address_billing: "",
    contact_persons: [],
  },

  // 业务信息
  business_info: {
    annual_revenue: 0,
    employee_count: 0,
    main_products: [],
    market_position: "",
    competitor_info: "",
    business_scope: "",
  },

  // 统计信息
  statistics: {
    total_projects: 0,
    total_contracts: 0,
    total_amount: 0,
    avg_contract_amount: 0,
    last_contact_date: null,
    next_contact_date: null,
    customer_score: 0,
    risk_level: "LOW",
  },

  // 标签信息
  tags: [],

  // 最新动态
  recent_activities: [],
};

// ==================== 风险等级配置 ====================
export const riskLevelConfigs = {
  LOW: {
    label: "低风险",
    color: "bg-green-500",
    textColor: "text-green-50",
    icon: "😊",
    description: "业务稳定，风险较低"
  },
  MEDIUM: {
    label: "中风险",
    color: "bg-yellow-500",
    textColor: "text-yellow-50",
    icon: "😐",
    description: "存在一定风险，需要关注"
  },
  HIGH: {
    label: "高风险",
    color: "bg-orange-500",
    textColor: "text-orange-50",
    icon: "😟",
    description: "风险较高，需重点监控"
  },
  CRITICAL: {
    label: "严重风险",
    color: "bg-red-500",
    textColor: "text-red-50",
    icon: "😱",
    description: "风险严重，立即处理"
  },
};

// ==================== 工具函数 ====================

// 获取客户类型配置
export const getCustomerTypeConfig = (type) => {
  return customerTypeConfigs[type] || customerTypeConfigs.REGULAR;
};

// 获取客户状态配置
export const getCustomerStatusConfig = (status) => {
  return customerStatusConfigs[status] || customerStatusConfigs.ACTIVE;
};

// 获取客户行业配置
export const getCustomerIndustryConfig = (industry) => {
  return customerIndustryConfigs[industry] || customerIndustryConfigs.ELECTRONICS;
};

// 获取客户来源配置
export const getCustomerSourceConfig = (source) => {
  return customerSourceConfigs[source] || customerSourceConfigs.DIRECT;
};

// 获取互动类型配置
export const getInteractionTypeConfig = (type) => {
  return interactionTypeConfigs[type] || interactionTypeConfigs.PHONE;
};

// 获取合同状态配置
export const getContractStatusConfig = (status) => {
  return contractStatusConfigs[status] || contractStatusConfigs.DRAFT;
};

// 获取客户评分配置
export const getCustomerScoreConfig = (score) => {
  if (score >= 90) return customerScoreConfigs.EXCELLENT;
  if (score >= 80) return customerScoreConfigs.GOOD;
  if (score >= 70) return customerScoreConfigs.AVERAGE;
  if (score >= 60) return customerScoreConfigs.BELOW_AVERAGE;
  return customerScoreConfigs.POOR;
};

// 获取风险等级配置
export const getRiskLevelConfig = (level) => {
  return riskLevelConfigs[level] || riskLevelConfigs.LOW;
};

// 格式化客户类型
export const formatCustomerType = (type) => {
  return getCustomerTypeConfig(type).label;
};

// 格式化客户状态
export const formatCustomerStatus = (status) => {
  return getCustomerStatusConfig(status).label;
};

// 格式客户行业
export const formatCustomerIndustry = (industry) => {
  return getCustomerIndustryConfig(industry).label;
};

// 格式化客户来源
export const formatCustomerSource = (source) => {
  return getCustomerSourceConfig(source).label;
};

// 格式化互动类型
export const formatInteractionType = (type) => {
  return getInteractionTypeConfig(type).label;
};

// 格式化合同状态
export const formatContractStatus = (status) => {
  return getContractStatusConfig(status).label;
};

// 格式化客户评分
export const formatCustomerScore = (score) => {
  const config = getCustomerScoreConfig(score);
  return `${config.score_range}分 - ${config.label}`;
};

// 格式化风险等级
export const formatRiskLevel = (level) => {
  return getRiskLevelConfig(level).label;
};

// 计算客户活跃度
export const calculateCustomerActivity = (interactions, days = 90) => {
  const cutoffDate = new Date();
  cutoffDate.setDate(cutoffDate.getDate() - days);

  const recentInteractions = interactions.filter(
    interaction => new Date(interaction.interaction_date) >= cutoffDate
  );

  return {
    total_count: recentInteractions.length,
    phone_count: recentInteractions.filter(i => i.type === 'PHONE').length,
    meeting_count: recentInteractions.filter(i => i.type === 'MEETING').length,
    visit_count: recentInteractions.filter(i => i.type === 'VISIT').length,
    last_interaction_date: recentInteractions.length > 0
      ? recentInteractions[0].interaction_date
      : null,
  };
};

// 计算客户价值评分
export const calculateCustomerValueScore = (customer) => {
  const weights = {
    revenue: 0.3,
    projects: 0.2,
    contracts: 0.2,
    activity: 0.15,
    satisfaction: 0.15,
  };

  const revenue_score = Math.min(customer.statistics?.total_amount / 1000000, 100) * 10;
  const projects_score = Math.min(customer.statistics?.total_projects * 10, 100);
  const contracts_score = Math.min(customer.statistics?.total_contracts * 20, 100);
  const activity_score = calculateCustomerActivity(customer.interactions || {}).total_count * 5;
  const satisfaction_score = customer.statistics?.customer_score || 50;

  return {
    total_score: Math.round(
      revenue_score * weights.revenue +
      projects_score * weights.projects +
      contracts_score * weights.contracts +
      activity_score * weights.activity +
      satisfaction_score * weights.satisfaction
    ),
    breakdown: {
      revenue: Math.round(revenue_score),
      projects: Math.round(projects_score),
      contracts: Math.round(contracts_score),
      activity: Math.round(activity_score),
      satisfaction: Math.round(satisfaction_score),
    },
  };
};

// 排序函数
export const sortByCustomerScore = (a, b) => {
  const scoreA = a.statistics?.customer_score || 0;
  const scoreB = b.statistics?.customer_score || 0;
  return scoreB - scoreA;
};

export const sortByTotalAmount = (a, b) => {
  const amountA = a.statistics?.total_amount || 0;
  const amountB = b.statistics?.total_amount || 0;
  return amountB - amountA;
};

export const sortByLastContact = (a, b) => {
  const dateA = new Date(a.statistics?.last_contact_date || '1970-01-01');
  const dateB = new Date(b.statistics?.last_contact_date || '1970-01-01');
  return dateB - dateA;
};

// 验证函数
export const isValidCustomerType = (type) => {
  return Object.keys(customerTypeConfigs).includes(type);
};

export const isValidCustomerStatus = (status) => {
  return Object.keys(customerStatusConfigs).includes(status);
};

export const isValidCustomerIndustry = (industry) => {
  return Object.keys(customerIndustryConfigs).includes(industry);
};

export const isValidInteractionType = (type) => {
  return Object.keys(interactionTypeConfigs).includes(type);
};

export const isValidContractStatus = (status) => {
  return Object.keys(contractStatusConfigs).includes(status);
};

// 过滤函数
export const filterByCustomerType = (customers, type) => {
  return customers.filter(customer => customer.customer_type === type);
};

export const filterByCustomerStatus = (customers, status) => {
  return customers.filter(customer => customer.status === status);
};

export const filterByCustomerIndustry = (customers, industry) => {
  return customers.filter(customer => customer.industry === industry);
};

export const filterByCustomerSource = (customers, source) => {
  return customers.filter(customer => customer.source === source);
};

export const filterByRiskLevel = (customers, level) => {
  return customers.filter(customer => customer.statistics?.risk_level === level);
};

export default {
  customerTypeConfigs,
  customerStatusConfigs,
  customerIndustryConfigs,
  customerSourceConfigs,
  interactionTypeConfigs,
  contractStatusConfigs,
  customerScoreConfigs,
  customerTagConfigs,
  riskLevelConfigs,
  customer360TabConfigs,
  DEFAULT_CUSTOMER_360_DATA,
  getCustomerTypeConfig,
  getCustomerStatusConfig,
  getCustomerIndustryConfig,
  getCustomerSourceConfig,
  getInteractionTypeConfig,
  getContractStatusConfig,
  getCustomerScoreConfig,
  getRiskLevelConfig,
  formatCustomerType,
  formatCustomerStatus,
  formatCustomerIndustry,
  formatCustomerSource,
  formatInteractionType,
  formatContractStatus,
  formatCustomerScore,
  formatRiskLevel,
  calculateCustomerActivity,
  calculateCustomerValueScore,
  sortByCustomerScore,
  sortByTotalAmount,
  sortByLastContact,
  isValidCustomerType,
  isValidCustomerStatus,
  isValidCustomerIndustry,
  isValidInteractionType,
  isValidContractStatus,
  filterByCustomerType,
  filterByCustomerStatus,
  filterByCustomerIndustry,
  filterByCustomerSource,
  filterByRiskLevel,
};