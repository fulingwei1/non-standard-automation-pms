// 销售机会看板配置常量

export const OPPORTUNITY_STAGES = {
  DISCOVERY: 'DISCOVERY',
  QUALIFIED: 'QUALIFIED',
  PROPOSAL: 'PROPOSAL',
  NEGOTIATION: 'NEGOTIATION',
  WON: 'WON',
  LOST: 'LOST',
};

export const OPPORTUNITY_STAGE_CONFIGS = {
  [OPPORTUNITY_STAGES.DISCOVERY]: {
    label: "需求发现",
    color: "bg-violet-500",
    textColor: "text-violet-400",
    probability: 10,
    frontendKey: "lead",
    icon: "Lightbulb",
  },
  [OPPORTUNITY_STAGES.QUALIFIED]: {
    label: "已合格",
    color: "bg-blue-500",
    textColor: "text-blue-400",
    probability: 30,
    frontendKey: "contact",
    icon: "CheckCircle",
  },
  [OPPORTUNITY_STAGES.PROPOSAL]: {
    label: "方案报价",
    color: "bg-amber-500",
    textColor: "text-amber-400",
    probability: 50,
    frontendKey: "quote",
    icon: "FileText",
  },
  [OPPORTUNITY_STAGES.NEGOTIATION]: {
    label: "合同谈判",
    color: "bg-pink-500",
    textColor: "text-pink-400",
    probability: 75,
    frontendKey: "negotiate",
    icon: "MessageSquare",
  },
  [OPPORTUNITY_STAGES.WON]: {
    label: "签约赢单",
    color: "bg-emerald-500",
    textColor: "text-emerald-400",
    probability: 100,
    frontendKey: "won",
    icon: "CheckCircle2",
  },
  [OPPORTUNITY_STAGES.LOST]: {
    label: "签约输单",
    color: "bg-red-500",
    textColor: "text-red-400",
    probability: 0,
    frontendKey: "lost",
    icon: "XCircle",
  },
};

export const OPPORTUNITY_PRIORITY = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
};

export const OPPORTUNITY_PRIORITY_CONFIGS = {
  [OPPORTUNITY_PRIORITY.HIGH]: { 
    label: "高优先级", 
    color: "bg-red-500",
    textColor: "text-red-400",
    icon: "AlertTriangle" 
  },
  [OPPORTUNITY_PRIORITY.MEDIUM]: { 
    label: "中优先级", 
    color: "bg-amber-500",
    textColor: "text-amber-400",
    icon: "Clock" 
  },
  [OPPORTUNITY_PRIORITY.LOW]: {
    label: "低优先级",
    color: "bg-green-500",
    textColor: "text-green-400",
    icon: "TrendingDown"
  },
};

export const OPPORTUNITY_TYPE = {
  NEW_BUSINESS: 'new_business',
  EXISTING_BUSINESS: 'existing_business',
  PARTNER: 'partner',
  INTERNAL: 'internal',
};

export const OPPORTUNITY_TYPE_CONFIGS = {
  [OPPORTUNITY_TYPE.NEW_BUSINESS]: { 
    label: "新业务", 
    color: "bg-blue-500",
    description: "来自新客户的销售机会" 
  },
  [OPPORTUNITY_TYPE.EXISTING_BUSINESS]: { 
    label: "现有业务", 
    color: "bg-emerald-500",
    description: "来自现有客户的增购机会" 
  },
  [OPPORTUNITY_TYPE.PARTNER]: { 
    label: "合作伙伴", 
    color: "bg-purple-500",
    description: "通过合作伙伴引入的机会" 
  },
  [OPPORTUNITY_TYPE.INTERNAL]: { 
    label: "内部推荐", 
    color: "bg-amber-500",
    description: "公司内部推荐的机会" 
  },
};

export const SALES_SOURCE = {
  WEBSITE: 'website',
  REFERRAL: 'referral',
  COLD_CALL: 'cold_call',
  EMAIL: 'email',
  SOCIAL: 'social',
  EVENT: 'event',
  PARTNER: 'partner',
  OTHER: 'other',
};

export const SALES_SOURCE_CONFIGS = {
  [SALES_SOURCE.WEBSITE]: { 
    label: "官网", 
    color: "bg-blue-500",
    conversionRate: 0.15 
  },
  [SALES_SOURCE.REFERRAL]: { 
    label: "推荐", 
    color: "bg-emerald-500",
    conversionRate: 0.35 
  },
  [SALES_SOURCE.COLD_CALL]: { 
    label: "陌生电话", 
    color: "bg-red-500",
    conversionRate: 0.05 
  },
  [SALES_SOURCE.EMAIL]: { 
    label: "邮件", 
    color: "bg-amber-500",
    conversionRate: 0.12 
  },
  [SALES_SOURCE.SOCIAL]: { 
    label: "社交媒体", 
    color: "bg-purple-500",
    conversionRate: 0.18 
  },
  [SALES_SOURCE.EVENT]: { 
    label: "活动", 
    color: "bg-pink-500",
    conversionRate: 0.25 
  },
  [SALES_SOURCE.PARTNER]: { 
    label: "合作伙伴", 
    color: "bg-indigo-500",
    conversionRate: 0.30 
  },
  [SALES_SOURCE.OTHER]: { 
    label: "其他", 
    color: "bg-slate-500",
    conversionRate: 0.10 
  },
};

export const SALES_CYCLE = {
  SHORT: 'short',
  MEDIUM: 'medium',
  LONG: 'long',
};

export const SALES_CYCLE_CONFIGS = {
  [SALES_CYCLE.SHORT]: { 
    label: "短周期", 
    days: 30,
    color: "bg-emerald-500" 
  },
  [SALES_CYCLE.MEDIUM]: { 
    label: "中周期", 
    days: 90,
    color: "bg-amber-500" 
  },
  [SALES_CYCLE.LONG]: { 
    label: "长周期", 
    days: 180,
    color: "bg-red-500" 
  },
};

export const FORECAST_CONFIDENCE = {
  HIGH: 'high',
  MEDIUM: 'medium',
  LOW: 'low',
};

export const FORECAST_CONFIDENCE_CONFIGS = {
  [FORECAST_CONFIDENCE.HIGH]: { 
    label: "高信心", 
    value: 0.8,
    color: "bg-emerald-500" 
  },
  [FORECAST_CONFIDENCE.MEDIUM]: { 
    label: "中信心", 
    value: 0.5,
    color: "bg-amber-500" 
  },
  [FORECAST_CONFIDENCE.LOW]: { 
    label: "低信心", 
    value: 0.2,
    color: "bg-red-500" 
  },
};

// 业务工具函数
export const OpportunityUtils = {
  // 获取阶段配置
  getStageConfig(stage) {
    return OPPORTUNITY_STAGE_CONFIGS[stage] || OPPORTUNITY_STAGE_CONFIGS[OPPORTUNITY_STAGES.DISCOVERY];
  },

  // 获取优先级配置
  getPriorityConfig(priority) {
    return OPPORTUNITY_PRIORITY_CONFIGS[priority] || OPPORTUNITY_PRIORITY_CONFIGS[OPPORTUNITY_PRIORITY.MEDIUM];
  },

  // 获取类型配置
  getTypeConfig(type) {
    return OPPORTUNITY_TYPE_CONFIGS[type] || OPPORTUNITY_TYPE_CONFIGS[OPPORTUNITY_TYPE.NEW_BUSINESS];
  },

  // 获取来源配置
  getSourceConfig(source) {
    return SALES_SOURCE_CONFIGS[source] || SALES_SOURCE_CONFIGS[SALES_SOURCE.OTHER];
  },

  // 获取销售周期配置
  getSalesCycleConfig(cycle) {
    return SALES_CYCLE_CONFIGS[cycle] || SALES_CYCLE_CONFIGS[SALES_CYCLE.MEDIUM];
  },

  // 获取预测信心配置
  getForecastConfidenceConfig(confidence) {
    return FORECAST_CONFIDENCE_CONFIGS[confidence] || FORECAST_CONFIDENCE_CONFIGS[FORECAST_CONFIDENCE.MEDIUM];
  },

  // 计算机会评分
  calculateOpportunityScore(opportunity) {
    const stageScore = (this.getStageConfig(opportunity.stage)?.probability || 0);
    const priorityMultiplier = {
      [OPPORTUNITY_PRIORITY.HIGH]: 1.5,
      [OPPORTUNITY_PRIORITY.MEDIUM]: 1.0,
      [OPPORTUNITY_PRIORITY.LOW]: 0.7,
    }[opportunity.priority] || 1.0;

    const agePenalty = this.calculateAgePenalty(opportunity.createdDate);
    const amountBonus = this.calculateAmountBonus(opportunity.expectedAmount);

    return Math.round((stageScore * priorityMultiplier + amountBonus - agePenalty) * 100);
  },

  // 计算年龄惩罚
  calculateAgePenalty(createdDate) {
    if (!createdDate) return 0;
    const ageInDays = Math.floor((new Date() - new Date(createdDate)) / (1000 * 60 * 60 * 24));
    if (ageInDays > 180) return 10;
    if (ageInDays > 90) return 5;
    return 0;
  },

  // 计算金额奖励
  calculateAmountBonus(amount) {
    if (!amount) return 0;
    if (amount > 1000000) return 10;
    if (amount > 500000) return 7;
    if (amount > 100000) return 5;
    return 0;
  },

  // 判断是否为热门机会
  isHotOpportunity(opportunity) {
    return (
      this.calculateOpportunityScore(opportunity) > 70 ||
      opportunity.priority === OPPORTUNITY_PRIORITY.HIGH ||
      (opportunity.expectedAmount && opportunity.expectedAmount > 500000)
    );
  },

  // 计算预期收入
  calculateExpectedRevenue(opportunity) {
    const probability = this.getStageConfig(opportunity.stage)?.probability || 0;
    const amount = opportunity.expectedAmount || 0;
    return (probability / 100) * amount;
  },

  // 计算销售周期
  calculateSalesCycle(opportunity) {
    if (!opportunity.createdDate) return 0;
    const created = new Date(opportunity.createdDate);
    const now = new Date();
    return Math.floor((now - created) / (1000 * 60 * 60 * 24));
  },

  // 判断是否超期
  isOverdue(opportunity) {
    const expectedCloseDate = opportunity.expectedCloseDate;
    if (!expectedCloseDate) return false;
    return new Date(expectedCloseDate) < new Date();
  },

  // 计算超期天数
  getOverdueDays(opportunity) {
    const expectedCloseDate = opportunity.expectedCloseDate;
    if (!expectedCloseDate) return 0;
    const now = new Date();
    const expected = new Date(expectedCloseDate);
    if (expected > now) return 0;
    return Math.floor((now - expected) / (1000 * 60 * 60 * 24));
  },

  // 预测成交时间
  predictCloseDate(opportunity) {
    const stage = this.getStageConfig(opportunity.stage);
    const salesCycle = this.getSalesCycleConfig(opportunity.salesCycle);
    const averageStageDays = {
      [OPPORTUNITY_STAGES.DISCOVERY]: salesCycle.days * 0.2,
      [OPPORTUNITY_STAGES.QUALIFIED]: salesCycle.days * 0.4,
      [OPPORTUNITY_STAGES.PROPOSAL]: salesCycle.days * 0.6,
      [OPPORTUNITY_STAGES.NEGOTIATION]: salesCycle.days * 0.8,
    };

    const remainingDays = averageStageDays[stage.key] || 30;
    const predictedDate = new Date();
    predictedDate.setDate(predictedDate.getDate() + remainingDays);
    
    return predictedDate.toISOString().split('T')[0];
  },

  // 格式化金额
  formatCurrency(amount) {
    if (!amount) return '¥0';
    if (amount >= 10000) {
      return `¥${(amount / 10000).toFixed(1)}万`;
    }
    return `¥${amount.toLocaleString()}`;
  },

  // 格式化日期
  formatDate(date) {
    if (!date) return '';
    return new Date(date).toLocaleDateString('zh-CN');
  },

  // 按阶段分组机会
  groupByStage(opportunities) {
    const groups = {};
    Object.values(OPPORTUNITY_STAGES).forEach(stage => {
      const config = this.getStageConfig(stage);
      groups[config.frontendKey] = opportunities.filter(opp => opp.stage === stage);
    });
    return groups;
  },

  // 过滤机会
  filterOpportunities(opportunities, filters) {
    let filtered = [...opportunities];

    if (filters.searchQuery) {
      const query = filters.searchQuery.toLowerCase();
      filtered = filtered.filter(opp => 
        opp.name?.toLowerCase().includes(query) ||
        opp.customerName?.toLowerCase().includes(query) ||
        opp.contactName?.toLowerCase().includes(query)
      );
    }

    if (filters.priority && filters.priority !== 'all') {
      filtered = filtered.filter(opp => opp.priority === filters.priority);
    }

    if (filters.source && filters.source !== 'all') {
      filtered = filtered.filter(opp => opp.source === filters.source);
    }

    if (filters.type && filters.type !== 'all') {
      filtered = filtered.filter(opp => opp.type === filters.type);
    }

    if (filters.showHotOnly) {
      filtered = filtered.filter(opp => this.isHotOpportunity(opp));
    }

    if (filters.hideLost) {
      filtered = filtered.filter(opp => opp.stage !== OPPORTUNITY_STAGES.LOST);
    }

    return filtered;
  },

  // 生成销售漏斗数据
  generateFunnelData(opportunities) {
    const funnelData = [];
    
    Object.values(OPPORTUNITY_STAGES).forEach(stage => {
      const config = this.getStageConfig(stage);
      const stageOpportunities = opportunities.filter(opp => opp.stage === stage);
      const count = stageOpportunities.length;
      const totalValue = stageOpportunities.reduce((sum, opp) => sum + (opp.expectedAmount || 0), 0);
      
      funnelData.push({
        stage: stage,
        label: config.label,
        count: count,
        value: totalValue,
        probability: config.probability,
        color: config.color,
      });
    });

    return funnelData;
  },

  // 计算转化率
  calculateConversionRates(opportunities) {
    const stages = Object.values(OPPORTUNITY_STAGES);
    const conversionRates = {};
    
    for (let i = 0; i < stages.length - 1; i++) {
      const fromStage = stages[i];
      const toStage = stages[i + 1];
      
      const fromCount = opportunities.filter(opp => opp.stage === fromStage).length;
      const toCount = opportunities.filter(opp => opp.stage === toStage).length;
      
      const conversionRate = fromCount > 0 ? (toCount / fromCount * 100).toFixed(1) : 0;
      
      conversionRates[`${fromStage}_${toStage}`] = parseFloat(conversionRate);
    }

    return conversionRates;
  },

  // 生成销售预测
  generateSalesForecast(opportunities, period = 'month') {
    const now = new Date();
    const periodEnd = new Date();
    
    switch (period) {
      case 'quarter':
        periodEnd.setMonth(now.getMonth() + 3);
        break;
      case 'year':
        periodEnd.setFullYear(now.getFullYear() + 1);
        break;
      default:
        periodEnd.setMonth(now.getMonth() + 1);
    }

    const filteredOpportunities = opportunities.filter(opp => {
      const expectedCloseDate = new Date(opp.expectedCloseDate);
      return expectedCloseDate >= now && expectedCloseDate <= periodEnd;
    });

    const totalValue = filteredOpportunities.reduce((sum, opp) => sum + (opp.expectedAmount || 0), 0);
    const expectedRevenue = filteredOpportunities.reduce((sum, opp) => sum + this.calculateExpectedRevenue(opp), 0);

    const byStage = {};
    Object.values(OPPORTUNITY_STAGES).forEach(stage => {
      const stageOpportunities = filteredOpportunities.filter(opp => opp.stage === stage);
      byStage[stage] = {
        count: stageOpportunities.length,
        value: stageOpportunities.reduce((sum, opp) => sum + (opp.expectedAmount || 0), 0),
        expectedRevenue: stageOpportunities.reduce((sum, opp) => sum + this.calculateExpectedRevenue(opp), 0),
      };
    });

    return {
      period,
      totalValue,
      expectedRevenue,
      opportunityCount: filteredOpportunities.length,
      byStage,
    };
  },

  // 生成销售报告
  generateSalesReport(opportunities, startDate, endDate) {
    const filtered = opportunities.filter(opp => {
      const createdDate = new Date(opp.createdDate);
      return createdDate >= new Date(startDate) && createdDate <= new Date(endDate);
    });

    const wonDeals = filtered.filter(opp => opp.stage === OPPORTUNITY_STAGES.WON);
    const lostDeals = filtered.filter(opp => opp.stage === OPPORTUNITY_STAGES.LOST);

    const totalValue = wonDeals.reduce((sum, opp) => sum + (opp.expectedAmount || 0), 0);
    const averageDealSize = wonDeals.length > 0 ? totalValue / wonDeals.length : 0;
    const winRate = filtered.length > 0 ? (wonDeals.length / filtered.length * 100) : 0;

    const averageSalesCycle = wonDeals.reduce((sum, opp) => {
      return sum + this.calculateSalesCycle(opp);
    }, 0) / (wonDeals.length || 1);

    return {
      period: `${startDate} 至 ${endDate}`,
      totalOpportunities: filtered.length,
      wonDeals: wonDeals.length,
      lostDeals: lostDeals.length,
      winRate: winRate.toFixed(1),
      totalRevenue: totalValue,
      averageDealSize: averageDealSize,
      averageSalesCycle: Math.round(averageSalesCycle),
      funnelData: this.generateFunnelData(filtered),
      conversionRates: this.calculateConversionRates(filtered),
    };
  },

  // 验证机会数据
  validateOpportunity(opportunity) {
    const errors = [];
    
    if (!opportunity.name || opportunity.name.trim() === '') {
      errors.push('请输入机会名称');
    }
    
    if (!opportunity.customerId) {
      errors.push('请选择客户');
    }
    
    if (!opportunity.expectedAmount || opportunity.expectedAmount <= 0) {
      errors.push('请输入有效金额');
    }
    
    if (!opportunity.expectedCloseDate) {
      errors.push('请选择预期成交日期');
    }
    
    if (!opportunity.stage) {
      errors.push('请选择销售阶段');
    }
    
    const expectedCloseDate = new Date(opportunity.expectedCloseDate);
    if (expectedCloseDate < new Date()) {
      errors.push('预期成交日期不能早于今天');
    }

    return errors;
  },
};

export default {
  OPPORTUNITY_STAGES,
  OPPORTUNITY_STAGE_CONFIGS,
  OPPORTUNITY_PRIORITY,
  OPPORTUNITY_PRIORITY_CONFIGS,
  OPPORTUNITY_TYPE,
  OPPORTUNITY_TYPE_CONFIGS,
  SALES_SOURCE,
  SALES_SOURCE_CONFIGS,
  SALES_CYCLE,
  SALES_CYCLE_CONFIGS,
  FORECAST_CONFIDENCE,
  FORECAST_CONFIDENCE_CONFIGS,
  OpportunityUtils,
};