/**
 * 📦 材料分析管理系统 - 配置常量
 * 材料状态、类型、测试标准、合规要求等核心配置
 */

// ==================== 材料状态配置 ====================

export const MATERIAL_STATUS = {
  ARRIVED: {
    key: 'arrived',
    label: '已到货',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    icon: 'CheckCircle',
    description: '材料已到达仓库'
  },
  IN_TRANSIT: {
    key: 'in_transit',
    label: '在途',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    icon: 'Truck',
    description: '材料正在运输途中'
  },
  DELAYED: {
    key: 'delayed',
    label: '延期',
    color: 'bg-red-500',
    textColor: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    icon: 'AlertTriangle',
    description: '材料交付延期'
  },
  NOT_ORDERED: {
    key: 'not_ordered',
    label: '未下单',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    icon: 'Clock',
    description: '尚未下单采购'
  },
  TESTING: {
    key: 'testing',
    label: '测试中',
    color: 'bg-purple-500',
    textColor: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    icon: 'Flask',
    description: '正在进行质量测试'
  },
  APPROVED: {
    key: 'approved',
    label: '已批准',
    color: 'bg-green-500',
    textColor: 'text-green-400',
    bgColor: 'bg-green-500/10',
    borderColor: 'border-green-500/30',
    icon: 'CheckCircle2',
    description: '测试通过，批准使用'
  },
  REJECTED: {
    key: 'rejected',
    label: '已拒绝',
    color: 'bg-red-600',
    textColor: 'text-red-400',
    bgColor: 'bg-red-600/10',
    borderColor: 'border-red-600/30',
    icon: 'XCircle',
    description: '测试失败，拒绝使用'
  }
};

export const MATERIAL_STATUS_OPTIONS = Object.values(MATERIAL_STATUS);

// ==================== 材料类型配置 ====================

export const MATERIAL_TYPES = {
  RAW_MATERIAL: {
    key: 'raw_material',
    label: '原材料',
    icon: 'Package',
    color: 'bg-blue-500',
    description: '基础原材料，如金属、塑料等',
    unit: 'kg',
    testRequired: true,
    complianceRequired: true
  },
  COMPONENT: {
    key: 'component',
    label: '零部件',
    icon: 'Cpu',
    color: 'bg-purple-500',
    description: '电子或机械零部件',
    unit: 'pcs',
    testRequired: true,
    complianceRequired: true
  },
  FASTENER: {
    key: 'fastener',
    label: '紧固件',
    icon: 'Wrench',
    color: 'bg-gray-500',
    description: '螺丝、螺母、螺栓等紧固件',
    unit: 'pcs',
    testRequired: false,
    complianceRequired: false
  },
  CABLE: {
    key: 'cable',
    label: '线缆',
    icon: 'Cable',
    color: 'bg-orange-500',
    description: '各种规格的电线电缆',
    unit: 'm',
    testRequired: true,
    complianceRequired: true
  },
  PCB: {
    key: 'pcb',
    label: 'PCB板',
    icon: 'Zap',
    color: 'bg-green-500',
    description: '印刷电路板',
    unit: 'pcs',
    testRequired: true,
    complianceRequired: true
  },
  ENCLOSURE: {
    key: 'enclosure',
    label: '外壳',
    icon: 'Box',
    color: 'bg-indigo-500',
    description: '设备外壳、机箱等',
    unit: 'pcs',
    testRequired: false,
    complianceRequired: false
  },
  CONSUMABLE: {
    key: 'consumable',
    label: '耗材',
    icon: 'Droplet',
    color: 'bg-cyan-500',
    description: '焊料、胶水、清洁剂等',
    unit: 'kg/L',
    testRequired: true,
    complianceRequired: true
  }
};

export const MATERIAL_TYPE_OPTIONS = Object.values(MATERIAL_TYPES);

// ==================== 材料优先级配置 ====================

export const MATERIAL_PRIORITY = {
  CRITICAL: {
    key: 'critical',
    label: '关键物料',
    level: 1,
    color: 'bg-red-500',
    textColor: 'text-red-400',
    borderColor: 'border-red-500/30',
    impact: 'high',
    description: '影响核心功能的关键材料',
    leadTimeDays: 14,
    stockThreshold: 10
  },
  IMPORTANT: {
    key: 'important',
    label: '重要物料',
    level: 2,
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    borderColor: 'border-amber-500/30',
    impact: 'medium',
    description: '影响产品性能的重要材料',
    leadTimeDays: 7,
    stockThreshold: 20
  },
  NORMAL: {
    key: 'normal',
    label: '普通物料',
    level: 3,
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    borderColor: 'border-blue-500/30',
    impact: 'low',
    description: '一般用途的常规材料',
    leadTimeDays: 3,
    stockThreshold: 50
  },
  OPTIONAL: {
    key: 'optional',
    label: '可选物料',
    level: 4,
    color: 'bg-gray-500',
    textColor: 'text-gray-400',
    borderColor: 'border-gray-500/30',
    impact: 'low',
    description: '非必需的可选材料',
    leadTimeDays: 1,
    stockThreshold: 100
  }
};

export const MATERIAL_PRIORITY_OPTIONS = Object.values(MATERIAL_PRIORITY);

// ==================== 测试类型配置 ====================

export const TEST_TYPES = {
  DIMENSIONAL: {
    key: 'dimensional',
    label: '尺寸测试',
    icon: 'Ruler',
    color: 'bg-blue-500',
    duration: '30分钟',
    equipment: '三坐标测量仪',
    description: '检测材料尺寸精度'
  },
  MECHANICAL: {
    key: 'mechanical',
    label: '机械性能测试',
    icon: 'Activity',
    color: 'bg-green-500',
    duration: '2小时',
    equipment: '万能试验机',
    description: '拉伸、弯曲、硬度等测试'
  },
  ELECTRICAL: {
    key: 'electrical',
    label: '电气性能测试',
    icon: 'Zap',
    color: 'bg-yellow-500',
    duration: '1小时',
    equipment: '示波器、万用表',
    description: '电阻、电容、绝缘等测试'
  },
  CHEMICAL: {
    key: 'chemical',
    label: '化学成分分析',
    icon: 'Flask',
    color: 'bg-purple-500',
    duration: '4小时',
    equipment: '光谱仪、色谱仪',
    description: '材料成分分析'
  },
  ENVIRONMENTAL: {
    key: 'environmental',
    label: '环境测试',
    icon: 'Cloud',
    color: 'bg-cyan-500',
    duration: '24小时',
    equipment: '环境试验箱',
    description: '温湿度、盐雾等测试'
  },
  RELIABILITY: {
    key: 'reliability',
    label: '可靠性测试',
    icon: 'Shield',
    color: 'bg-indigo-500',
    duration: '168小时',
    equipment: '可靠性试验台',
    description: '寿命、耐久性测试'
  },
  ROHS: {
    key: 'rohs',
    label: 'RoHS测试',
    icon: 'Leaf',
    color: 'bg-green-600',
    duration: '2小时',
    equipment: 'X射线荧光分析仪',
    description: '有害物质检测'
  }
};

export const TEST_TYPE_OPTIONS = Object.values(TEST_TYPES);

// ==================== 合规标准配置 ====================

export const COMPLIANCE_STANDARDS = {
  ISO9001: {
    key: 'iso9001',
    label: 'ISO 9001',
    fullLabel: 'ISO 9001 质量管理体系',
    category: 'quality',
    scope: 'all',
    mandatory: true,
    description: '国际质量管理体系标准',
    validPeriod: '3年',
    auditFrequency: '年度'
  },
  ISO14001: {
    key: 'iso14001',
    label: 'ISO 14001',
    fullLabel: 'ISO 14001 环境管理体系',
    category: 'environmental',
    scope: 'all',
    mandatory: false,
    description: '国际环境管理体系标准',
    validPeriod: '3年',
    auditFrequency: '年度'
  },
  IATF16949: {
    key: 'iatf16949',
    label: 'IATF 16949',
    fullLabel: 'IATF 16949 汽车质量管理体系',
    category: 'automotive',
    scope: 'automotive',
    mandatory: true,
    description: '汽车行业质量管理体系标准',
    validPeriod: '3年',
    auditFrequency: '半年'
  },
  ROHS: {
    key: 'rohs',
    label: 'RoHS 3.0',
    fullLabel: 'RoHS 3.0 有害物质限制',
    category: 'environmental',
    scope: 'electronics',
    mandatory: true,
    description: '有害物质限制指令',
    validPeriod: '持续',
    auditFrequency: '批次'
  },
  REACH: {
    key: 'reach',
    label: 'REACH',
    fullLabel: 'REACH 化学品注册评估授权',
    category: 'chemical',
    scope: 'chemical',
    mandatory: true,
    description: '欧盟化学品法规',
    validPeriod: '持续',
    auditFrequency: '年度'
  },
  UL: {
    key: 'ul',
    label: 'UL认证',
    fullLabel: 'UL 安全认证',
    category: 'safety',
    scope: 'electronics',
    mandatory: false,
    description: '美国安全认证标准',
    validPeriod: '5年',
    auditFrequency: '季度'
  },
  CE: {
    key: 'ce',
    label: 'CE认证',
    fullLabel: 'CE 欧盟符合性认证',
    category: 'safety',
    scope: 'all',
    mandatory: true,
    description: '欧盟符合性认证',
    validPeriod: '5年',
    auditFrequency: '年度'
  }
};

export const COMPLIANCE_STANDARD_OPTIONS = Object.values(COMPLIANCE_STANDARDS);

// ==================== 供应商等级配置 ====================

export const SUPPLIER_LEVELS = {
  A: {
    key: 'A',
    label: 'A级供应商',
    color: 'bg-green-500',
    textColor: 'text-green-400',
    borderColor: 'border-green-500/30',
    score: '90-100',
    description: '优秀供应商，质量可靠',
    preferred: true,
    auditFrequency: '年度'
  },
  B: {
    key: 'B',
    label: 'B级供应商',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    borderColor: 'border-blue-500/30',
    score: '80-89',
    description: '良好供应商，基本满足要求',
    preferred: true,
    auditFrequency: '半年'
  },
  C: {
    key: 'C',
    label: 'C级供应商',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    borderColor: 'border-amber-500/30',
    score: '70-79',
    description: '合格供应商，需改进',
    preferred: false,
    auditFrequency: '季度'
  },
  D: {
    key: 'D',
    label: 'D级供应商',
    color: 'bg-red-500',
    textColor: 'text-red-400',
    borderColor: 'border-red-500/30',
    score: '<70',
    description: '待改进供应商，考虑替换',
    preferred: false,
    auditFrequency: '月度'
  }
};

export const SUPPLIER_LEVEL_OPTIONS = Object.values(SUPPLIER_LEVELS);

// ==================== 影响等级配置 ====================

export const IMPACT_LEVELS = {
  HIGH: {
    key: 'high',
    label: '高影响',
    color: 'bg-red-500/20 text-red-400 border-red-500/30',
    value: 'high',
    description: '严重影响项目进度',
    threshold: 0.8,
    action: '立即处理'
  },
  MEDIUM: {
    key: 'medium',
    label: '中影响',
    color: 'bg-amber-500/20 text-amber-400 border-amber-500/30',
    value: 'medium',
    description: '可能影响项目进度',
    threshold: 0.6,
    action: '关注监控'
  },
  LOW: {
    key: 'low',
    label: '低影响',
    color: 'bg-slate-500/20 text-slate-400 border-slate-500/30',
    value: 'low',
    description: '影响较小',
    threshold: 0.4,
    action: '例行检查'
  }
};

export const IMPACT_LEVEL_OPTIONS = Object.values(IMPACT_LEVELS);

// ==================== 分析周期配置 ====================

export const ANALYSIS_PERIODS = {
  DAILY: {
    key: 'daily',
    label: '每日',
    days: 1,
    format: 'MM-DD',
    chartType: 'line',
    description: '每日数据分析'
  },
  WEEKLY: {
    key: 'weekly',
    label: '每周',
    days: 7,
    format: 'MM-DD',
    chartType: 'bar',
    description: '每周数据分析'
  },
  MONTHLY: {
    key: 'monthly',
    label: '每月',
    days: 30,
    format: 'YYYY-MM',
    chartType: 'bar',
    description: '每月数据分析'
  },
  QUARTERLY: {
    key: 'quarterly',
    label: '每季度',
    days: 90,
    format: 'YYYY-QQ',
    chartType: 'line',
    description: '每季度数据分析'
  }
};

export const ANALYSIS_PERIOD_OPTIONS = Object.values(ANALYSIS_PERIODS);

// ==================== 风险指标配置 ====================

export const RISK_INDICATORS = {
  DELAY_RISK: {
    key: 'delay_risk',
    label: '延期风险',
    threshold: 7,
    unit: '天',
    color: 'bg-red-500',
    description: '预计交付延期超过阈值'
  },
  QUALITY_RISK: {
    key: 'quality_risk',
    label: '质量风险',
    threshold: 5,
    unit: '%',
    color: 'bg-amber-500',
    description: '不合格品率超过阈值'
  },
  SUPPLY_RISK: {
    key: 'supply_risk',
    label: '供应风险',
    threshold: 20,
    unit: '%',
    color: 'bg-orange-500',
    description: '单一供应商依赖度'
  },
  COST_RISK: {
    key: 'cost_risk',
    label: '成本风险',
    threshold: 10,
    unit: '%',
    color: 'bg-purple-500',
    description: '成本超预算比例'
  },
  COMPLIANCE_RISK: {
    key: 'compliance_risk',
    label: '合规风险',
    threshold: 30,
    unit: '天',
    color: 'bg-indigo-500',
    description: '合规证书即将到期'
  }
};

export const RISK_INDICATOR_OPTIONS = Object.values(RISK_INDICATORS);

// ==================== 统计指标配置 ====================

export const ANALYSIS_METRICS = {
  READINESS_RATE: {
    key: 'readiness_rate',
    label: '齐套率',
    unit: '%',
    format: 'percentage',
    target: 95,
    description: '材料到货齐套率'
  },
  ON_TIME_DELIVERY: {
    key: 'on_time_delivery',
    label: '准时交付率',
    unit: '%',
    format: 'percentage',
    target: 90,
    description: '准时交付率'
  },
  QUALITY_RATE: {
    key: 'quality_rate',
    label: '合格率',
    unit: '%',
    format: 'percentage',
    target: 98,
    description: '材料检验合格率'
  },
  COST_EFFICIENCY: {
    key: 'cost_efficiency',
    label: '成本效率',
    unit: '%',
    format: 'percentage',
    target: 85,
    description: '成本控制效率'
  },
  INVENTORY_TURNOVER: {
    key: 'inventory_turnover',
    label: '库存周转率',
    unit: '次/年',
    format: 'decimal',
    target: 6,
    description: '库存周转次数'
  }
};

export const ANALYSIS_METRIC_OPTIONS = Object.values(ANALYSIS_METRICS);

// ==================== 工具函数 ====================

/**
 * 获取材料状态配置
 */
export function getMaterialStatus(status) {
  return MATERIAL_STATUS[status?.toUpperCase()] || MATERIAL_STATUS.NOT_ORDERED;
}

/**
 * 获取材料类型配置
 */
export function getMaterialType(type) {
  return MATERIAL_TYPES[type?.toUpperCase()] || MATERIAL_TYPES.RAW_MATERIAL;
}

/**
 * 获取材料优先级配置
 */
export function getMaterialPriority(priority) {
  return MATERIAL_PRIORITY[priority?.toUpperCase()] || MATERIAL_PRIORITY.NORMAL;
}

/**
 * 获取测试类型配置
 */
export function getTestType(type) {
  return TEST_TYPES[type?.toUpperCase()] || TEST_TYPES.DIMENSIONAL;
}

/**
 * 获取合规标准配置
 */
export function getComplianceStandard(standard) {
  return COMPLIANCE_STANDARDS[standard?.toUpperCase().replace('.', '')] || 
         COMPLIANCE_STANDARDS.ISO9001;
}

/**
 * 获取供应商等级配置
 */
export function getSupplierLevel(level) {
  return SUPPLIER_LEVELS[level?.toUpperCase()] || SUPPLIER_LEVELS.B;
}

/**
 * 获取影响等级配置
 */
export function getImpactLevel(level) {
  return IMPACT_LEVELS[level?.toUpperCase()] || IMPACT_LEVELS.LOW;
}

/**
 * 计算材料齐套率
 */
export function calculateReadinessRate(arrived, total) {
  return total > 0 ? Math.round((arrived / total) * 100) : 0;
}

/**
 * 评估材料风险等级
 */
export function assessMaterialRisk(material) {
  const risks = [];
  
  // 延期风险评估
  if (material.delayed > 5) {
    risks.push({
      type: 'delay',
      level: 'high',
      value: material.delayed,
      threshold: RISK_INDICATORS.DELAY_RISK.threshold
    });
  }
  
  // 质量风险评估
  if (material.defectRate > 5) {
    risks.push({
      type: 'quality',
      level: 'medium',
      value: material.defectRate,
      threshold: RISK_INDICATORS.QUALITY_RISK.threshold
    });
  }
  
  // 供应风险评估
  if (material.supplierConcentration > 80) {
    risks.push({
      type: 'supply',
      level: 'high',
      value: material.supplierConcentration,
      threshold: RISK_INDICATORS.SUPPLY_RISK.threshold
    });
  }
  
  return risks;
}

/**
 * 格式化测试结果
 */
export function formatTestResult(result) {
  if (!result) return { status: 'pending', value: '-' };
  
  return {
    status: result.passed ? 'pass' : 'fail',
    value: result.value || '-',
    unit: result.unit || '',
    tolerance: result.tolerance || '',
    actual: result.actual || 0,
    expected: result.expected || 0
  };
}

/**
 * 验证材料合规性
 */
export function validateCompliance(material, requiredStandards = []) {
  const results = [];
  
  for (const standardKey of requiredStandards) {
    const standard = getComplianceStandard(standardKey);
    const certificate = material.certificates?.find(c => c.standard === standardKey);
    
    results.push({
      standard,
      compliant: !!certificate && !isExpired(certificate.expiryDate),
      certificate,
      lastAudit: certificate?.lastAuditDate,
      nextAudit: certificate?.nextAuditDate
    });
  }
  
  return results;
}

/**
 * 检查证书是否过期
 */
export function isExpired(expiryDate) {
  if (!expiryDate) return true;
  return new Date(expiryDate) < new Date();
}

/**
 * 计算材料分析评分
 */
export function calculateAnalysisScore(material) {
  const weights = {
    quality: 0.3,
    delivery: 0.25,
    cost: 0.2,
    compliance: 0.15,
    risk: 0.1
  };
  
  const scores = {
    quality: material.qualityScore || 0,
    delivery: material.deliveryScore || 0,
    cost: material.costScore || 0,
    compliance: material.complianceScore || 0,
    risk: 100 - (material.riskScore || 0) // 风险分数需要反向计算
  };
  
  const weightedScore = Object.entries(weights).reduce(
    (total, [key, weight]) => total + (scores[key] * weight),
    0
  );
  
  return Math.round(weightedScore);
}

/**
 * 生成材料分析建议
 */
export function generateAnalysisSuggestions(material) {
  const suggestions = [];
  const score = calculateAnalysisScore(material);
  
  if (score < 60) {
    suggestions.push({
      type: 'critical',
      message: '材料综合评分过低，建议立即进行全面评估',
      actions: ['重新评估供应商', '加强质量检验', '考虑替代材料']
    });
  } else if (score < 80) {
    suggestions.push({
      type: 'warning',
      message: '材料表现需要改进',
      actions: ['优化采购策略', '加强供应商管理', '完善测试流程']
    });
  } else {
    suggestions.push({
      type: 'good',
      message: '材料表现良好，继续保持',
      actions: ['定期监控', '持续改进', '经验分享']
    });
  }
  
  return suggestions;
}

// ==================== 默认导出 ====================

export default {
  // 配置集合
  MATERIAL_STATUS,
  MATERIAL_TYPES,
  MATERIAL_PRIORITY,
  TEST_TYPES,
  COMPLIANCE_STANDARDS,
  SUPPLIER_LEVELS,
  IMPACT_LEVELS,
  ANALYSIS_PERIODS,
  RISK_INDICATORS,
  ANALYSIS_METRICS,
  
  // 选项集合
  MATERIAL_STATUS_OPTIONS,
  MATERIAL_TYPE_OPTIONS,
  MATERIAL_PRIORITY_OPTIONS,
  TEST_TYPE_OPTIONS,
  COMPLIANCE_STANDARD_OPTIONS,
  SUPPLIER_LEVEL_OPTIONS,
  IMPACT_LEVEL_OPTIONS,
  ANALYSIS_PERIOD_OPTIONS,
  RISK_INDICATOR_OPTIONS,
  ANALYSIS_METRIC_OPTIONS,
  
  // 工具函数
  getMaterialStatus,
  getMaterialType,
  getMaterialPriority,
  getTestType,
  getComplianceStandard,
  getSupplierLevel,
  getImpactLevel,
  calculateReadinessRate,
  assessMaterialRisk,
  formatTestResult,
  validateCompliance,
  isExpired,
  calculateAnalysisScore,
  generateAnalysisSuggestions
};