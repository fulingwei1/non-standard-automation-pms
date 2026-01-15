/**
 * Worker Workstation Constants - 工人工作站配置常量
 * 包含工单状态、报工类型、技能等级、绩效指标等配置
 */

// ==================== 工单状态配置 ====================
export const WORK_ORDER_STATUS = {
  PENDING: { 
    label: "待派工", 
    color: "bg-slate-500",
    description: "等待分配的工单",
    canStart: false,
    canReport: false,
    canComplete: false
  },
  ASSIGNED: { 
    label: "已派工", 
    color: "bg-blue-500",
    description: "已分配给工人但未开始",
    canStart: true,
    canReport: false,
    canComplete: false
  },
  STARTED: { 
    label: "已开始", 
    color: "bg-amber-500",
    description: "已经开始生产",
    canStart: false,
    canReport: true,
    canComplete: false
  },
  IN_PROGRESS: { 
    label: "进行中", 
    color: "bg-amber-500",
    description: "正在生产中",
    canStart: false,
    canReport: true,
    canComplete: true
  },
  PAUSED: { 
    label: "已暂停", 
    color: "bg-purple-500",
    description: "临时暂停的生产",
    canStart: true,
    canReport: false,
    canComplete: false
  },
  COMPLETED: { 
    label: "已完成", 
    color: "bg-emerald-500",
    description: "生产完成",
    canStart: false,
    canReport: false,
    canComplete: false
  },
  CANCELLED: { 
    label: "已取消", 
    color: "bg-gray-500",
    description: "已取消的工单",
    canStart: false,
    canReport: false,
    canComplete: false
  }
};

// ==================== 报工类型配置 ====================
export const REPORT_TYPE = {
  START: { 
    label: "开工", 
    color: "bg-blue-500",
    description: "开始生产的报工",
    icon: "PlayCircle",
    requires: ["work_order_id", "start_note"],
    nextStatus: "STARTED"
  },
  PROGRESS: { 
    label: "进度", 
    color: "bg-amber-500",
    description: "生产进度报工",
    icon: "TrendingUp",
    requires: ["work_order_id", "progress_percent", "progress_note"],
    nextStatus: "IN_PROGRESS"
  },
  COMPLETE: { 
    label: "完工", 
    color: "bg-emerald-500",
    description: "完成生产的报工",
    icon: "CheckCircle2",
    requires: ["work_order_id", "completed_qty", "qualified_qty", "work_hours"],
    nextStatus: "COMPLETED"
  }
};

// ==================== 技能等级配置 ====================
export const SKILL_LEVELS = {
  BEGINNER: { 
    label: "初级工", 
    level: 1,
    color: "bg-gray-500",
    description: "刚入职工人",
    maxWorkOrderType: ["简单装配"],
    maxComplexity: 1
  },
  INTERMEDIATE: { 
    label: "中级工", 
    level: 2,
    color: "bg-blue-500",
    description: "有一定经验的工人",
    maxWorkOrderType: ["简单装配", "复杂装配", "测试"],
    maxComplexity: 2
  },
  SENIOR: { 
    label: "高级工", 
    level: 3,
    color: "bg-purple-500",
    description: "经验丰富的工人",
    maxWorkOrderType: ["简单装配", "复杂装配", "测试", "调试"],
    maxComplexity: 3
  },
  EXPERT: { 
    label: "技师", 
    level: 4,
    color: "bg-amber-500",
    description: "技术专家",
    maxWorkOrderType: ["全部"],
    maxComplexity: 4
  },
  MASTER: { 
    label: "高级技师", 
    level: 5,
    color: "bg-emerald-500",
    description: "资深技术专家",
    maxWorkOrderType: ["全部"],
    maxComplexity: 5
  }
};

// ==================== 工单类型配置 ====================
export const WORK_ORDER_TYPES = {
  ASSEMBLY: { 
    label: "装配", 
    category: "production",
    complexity: 2,
    estimatedHours: 4,
    requiredSkills: ["中级工", "高级工"]
  },
  TESTING: { 
    label: "测试", 
    category: "quality",
    complexity: 3,
    estimatedHours: 2,
    requiredSkills: ["中级工", "高级工", "技师"]
  },
  DEBUGGING: { 
    label: "调试", 
    category: "quality",
    complexity: 4,
    estimatedHours: 6,
    requiredSkills: ["高级工", "技师", "高级技师"]
  },
  PACKAGING: { 
    label: "包装", 
    category: "logistics",
    complexity: 1,
    estimatedHours: 1,
    requiredSkills: ["初级工", "中级工"]
  },
  MAINTENANCE: { 
    label: "维护", 
    category: "maintenance",
    complexity: 3,
    estimatedHours: 3,
    requiredSkills: ["中级工", "高级工"]
  },
  REPAIR: { 
    label: "维修", 
    category: "maintenance",
    complexity: 4,
    estimatedHours: 5,
    requiredSkills: ["高级工", "技师", "高级技师"]
  },
  INSTALLATION: { 
    label: "安装", 
    category: "service",
    complexity: 3,
    estimatedHours: 8,
    requiredSkills: ["中级工", "高级工", "技师"]
  }
};

// ==================== 绩效指标配置 ====================
export const PERFORMANCE_METRICS = {
  EFFICIENCY: {
    label: "工作效率",
    weight: 0.3,
    description: "实际工时与计划工时的比率",
    calculation: "plan_hours / actual_hours",
    target: 0.95,
    unit: "%"
  },
  QUALITY: {
    label: "质量合格率",
    weight: 0.3,
    description: "合格数量与完成数量的比率",
    calculation: "qualified_qty / completed_qty",
    target: 0.98,
    unit: "%"
  },
  TIMELINESS: {
    label: "及时完成率",
    weight: 0.2,
    description: "按时完成工单的比例",
    calculation: "on_time_orders / total_orders",
    target: 0.90,
    unit: "%"
  },
  ATTENDANCE: {
    label: "出勤率",
    weight: 0.1,
    description: "实际出勤天数与应出勤天数的比率",
    calculation: "actual_days / scheduled_days",
    target: 0.95,
    unit: "%"
  },
  SKILL_IMPROVEMENT: {
    label: "技能提升",
    weight: 0.1,
    description: "技能培训和认证完成情况",
    calculation: "completed_trainings / required_trainings",
    target: 0.80,
    unit: "%"
  }
};

// ==================== 培训类型配置 ====================
export const TRAINING_TYPES = {
  ONBOARDING: {
    label: "入职培训",
    category: "basic",
    duration: 40,
    requiredFor: ["初级工"],
    modules: ["安全规范", "设备操作", "质量标准", "工作流程"]
  },
  SKILL_UPGRADE: {
    label: "技能提升",
    category: "technical",
    duration: 16,
    requiredFor: ["中级工", "高级工"],
    modules: ["高级操作", "故障诊断", "工艺优化"]
  },
  SAFETY_TRAINING: {
    label: "安全培训",
    category: "safety",
    duration: 8,
    requiredFor: ["全部"],
    modules: ["安全规程", "应急处理", "防护设备"]
  },
  QUALITY_TRAINING: {
    label: "质量培训",
    category: "quality",
    duration: 12,
    requiredFor: ["中级工", "高级工", "技师"],
    modules: ["质量标准", "检验方法", "问题分析"]
  },
  EQUIPMENT_TRAINING: {
    label: "设备培训",
    category: "equipment",
    duration: 24,
    requiredFor: ["高级工", "技师"],
    modules: ["设备原理", "维护保养", "故障排除"]
  }
};

// ==================== 工作优先级配置 ====================
export const WORK_PRIORITIES = {
  LOW: { 
    label: "低", 
    level: 1,
    color: "bg-gray-500",
    description: "常规工作，可正常安排"
  },
  NORMAL: { 
    label: "普通", 
    level: 2,
    color: "bg-blue-500",
    description: "标准优先级工作"
  },
  HIGH: { 
    label: "高", 
    level: 3,
    color: "bg-amber-500",
    description: "需要优先处理的工作"
  },
  URGENT: { 
    label: "紧急", 
    level: 4,
    color: "bg-red-500",
    description: "需要立即处理的工作"
  },
  CRITICAL: { 
    label: "危急", 
    level: 5,
    color: "bg-purple-500",
    description: "影响生产线的紧急工作"
  }
};

// ==================== 快捷数量配置 ====================
export const QUICK_QUANTITY_OPTIONS = {
  ALL: { label: "全部完成", value: "all" },
  QUARTER: { label: "1/4", value: 0.25 },
  HALF: { label: "1/2", value: 0.5 },
  THREE_QUARTERS: { label: "3/4", value: 0.75 },
  COMMON: [
    { label: "10个", value: 10 },
    { label: "50个", value: 50 },
    { label: "100个", value: 100 },
    { label: "500个", value: 500 }
  ]
};

// ==================== 时间计算配置 ====================
export const TIME_CONFIG = {
  WORK_HOURS_PER_DAY: 8,
  WORK_MINUTES_PER_HOUR: 60,
  BREAK_DURATION: 1, // 休息时间（小时）
  OVERTIME_THRESHOLD: 8, // 加班阈值（小时）
  DEFAULT_ROUNDING: 0.25 // 默认时间舍入（小时）
};

// ==================== 质量标准配置 ====================
export const QUALITY_STANDARDS = {
  ACCEPTABLE_DEFECT_RATE: 0.02, // 可接受的不良率 2%
  TARGET_QUALITY_RATE: 0.98, // 目标合格率 98%
  MINIMUM_QUALITY_RATE: 0.95, // 最低合格率 95%
  REWORK_THRESHOLD: 0.05, // 返工阈值 5%
  QUALITY_LEVELS: {
    EXCELLENT: { min: 0.99, label: "优秀", color: "bg-emerald-500" },
    GOOD: { min: 0.97, label: "良好", color: "bg-blue-500" },
    ACCEPTABLE: { min: 0.95, label: "合格", color: "bg-amber-500" },
  POOR: { min: 0, label: "不合格", color: "bg-red-500" }
  }
};

// ==================== 工具函数 ====================

/**
 * 计算进度百分比
 */
export const calculateProgress = (completed, planned) => {
  if (!planned || planned === 0) return 0;
  return Math.round((completed / planned) * 100);
};

/**
 * 计算工时
 */
export const calculateWorkHours = (startTime, endTime = null) => {
  const start = new Date(startTime);
  const end = endTime ? new Date(endTime) : new Date();
  const diffMs = end - start;
  const diffHours = diffMs / (1000 * 60 * 60);
  
  // 舍入到最近的15分钟
  return Math.round(diffHours * 4) / 4;
};

/**
 * 获取工单状态颜色
 */
export const getStatusColor = (status) => {
  return WORK_ORDER_STATUS[status]?.color || "bg-gray-500";
};

/**
 * 获取报工类型颜色
 */
export const getReportTypeColor = (type) => {
  return REPORT_TYPE[type]?.color || "bg-gray-500";
};

/**
 * 获取技能等级颜色
 */
export const getSkillLevelColor = (level) => {
  const skillLevel = Object.values(SKILL_LEVELS).find(skill => skill.level === level);
  return skillLevel?.color || "bg-gray-500";
};

/**
 * 验证报工数据
 */
export const validateReportData = (reportType, data, workOrder) => {
  const errors = [];
  
  switch (reportType) {
    case 'START':
      if (!data.start_note?.trim()) {
        errors.push("请填写开工说明");
      }
      break;
      
    case 'PROGRESS':
      if (!data.progress_percent || data.progress_percent <= 0) {
        errors.push("请填写有效的进度百分比");
      }
      if (data.progress_percent > 100) {
        errors.push("进度不能超过100%");
      }
      if (!data.progress_note?.trim()) {
        errors.push("请填写进度说明");
      }
      break;
      
    case 'COMPLETE':
      if (!data.completed_qty || data.completed_qty <= 0) {
        errors.push("请填写完成数量");
      }
      if (workOrder && data.completed_qty > workOrder.plan_qty) {
        errors.push(`完成数量不能超过计划数量 ${workOrder.plan_qty}`);
      }
      if (data.qualified_qty > data.completed_qty) {
        errors.push("合格数量不能超过完成数量");
      }
      if (!data.work_hours || data.work_hours <= 0) {
        errors.push("请填写工时");
      }
      break;
  }
  
  return errors;
};

/**
 * 计算绩效评分
 */
export const calculatePerformanceScore = (metrics) => {
  let totalScore = 0;
  let totalWeight = 0;
  
  Object.entries(PERFORMANCE_METRICS).forEach(([key, config]) => {
    const value = metrics[key];
    if (value !== undefined && value !== null) {
      const score = Math.min(value / config.target, 1.2); // 最高120分
      totalScore += score * config.weight;
      totalWeight += config.weight;
    }
  });
  
  return totalWeight > 0 ? (totalScore / totalWeight) * 100 : 0;
};

/**
 * 获取质量等级
 */
export const getQualityLevel = (qualifiedQty, completedQty) => {
  if (!completedQty || completedQty === 0) return null;
  
  const qualityRate = qualifiedQty / completedQty;
  
  for (const [level, config] of Object.entries(QUALITY_STANDARDS.QUALITY_LEVELS)) {
    if (qualityRate >= config.min) {
      return { level, ...config };
    }
  }
  
  return QUALITY_STANDARDS.QUALITY_LEVELS.POOR;
};

/**
 * 获取推荐的技能等级
 */
export const getRecommendedSkillLevel = (workOrderType, complexity) => {
  const typeConfig = WORK_ORDER_TYPES[workOrderType];
  if (!typeConfig) return "INTERMEDIATE";
  
  // 根据复杂度推荐技能等级
  if (complexity >= 4) return "EXPERT";
  if (complexity >= 3) return "SENIOR";
  if (complexity >= 2) return "INTERMEDIATE";
  return "BEGINNER";
};

/**
 * 生成工作建议
 */
export const generateWorkSuggestions = (workOrder, workerLevel, recentPerformance) => {
  const suggestions = [];
  
  // 基于工单复杂度的建议
  if (workOrder.complexity > workerLevel) {
    suggestions.push("建议先寻求技术指导或协助");
  }
  
  // 基于最近绩效的建议
  if (recentPerformance.qualityRate < QUALITY_STANDARDS.TARGET_QUALITY_RATE) {
    suggestions.push("注意质量控制，建议加强检验");
  }
  
  if (recentPerformance.efficiency < 0.9) {
    suggestions.push("提升工作效率，注意工艺优化");
  }
  
  // 基于工单类型的建议
  const typeConfig = WORK_ORDER_TYPES[workOrder.type];
  if (typeConfig) {
    suggestions.push(`预计工时：${typeConfig.estimatedHours}小时`);
    suggestions.push(`所需技能：${typeConfig.requiredSkills.join("、")}`);
  }
  
  return suggestions;
};

/**
 * 格式化工时显示
 */
export const formatWorkHours = (hours) => {
  if (!hours || hours === 0) return "0小时";
  
  const wholeHours = Math.floor(hours);
  const minutes = Math.round((hours - wholeHours) * 60);
  
  if (wholeHours === 0) {
    return `${minutes}分钟`;
  } else if (minutes === 0) {
    return `${wholeHours}小时`;
  } else {
    return `${wholeHours}小时${minutes}分钟`;
  }
};

/**
 * 获取下一个可执行的操作
 */
export const getNextAvailableActions = (workOrder) => {
  const statusConfig = WORK_ORDER_STATUS[workOrder.status];
  const actions = [];
  
  if (statusConfig?.canStart) {
    actions.push({ type: 'START', label: '开工', ...REPORT_TYPE.START });
  }
  
  if (statusConfig?.canReport) {
    actions.push({ type: 'PROGRESS', label: '进度报工', ...REPORT_TYPE.PROGRESS });
  }
  
  if (statusConfig?.canComplete) {
    actions.push({ type: 'COMPLETE', label: '完工', ...REPORT_TYPE.COMPLETE });
  }
  
  return actions;
};

/**
 * 计算预计完成时间
 */
export const calculateEstimatedCompletion = (workOrder, workerEfficiency = 1.0) => {
  const typeConfig = WORK_ORDER_TYPES[workOrder.type];
  if (!typeConfig) return null;
  
  const estimatedHours = typeConfig.estimatedHours / workerEfficiency;
  const startTime = new Date(workOrder.assigned_time || workOrder.created_time);
  const completionTime = new Date(startTime.getTime() + estimatedHours * 60 * 60 * 1000);
  
  return completionTime;
};

// ==================== 导出默认配置 ====================
export const DEFAULT_WORK_ORDER_CONFIG = {
  status: 'PENDING',
  priority: 'NORMAL',
  type: 'ASSEMBLY',
  complexity: 2,
  estimatedHours: 4
};

export const DEFAULT_REPORT_CONFIG = {
  startData: {
    start_note: '',
    equipment_check: true,
    material_check: true
  },
  progressData: {
    progress_percent: 0,
    progress_note: '',
    current_issues: ''
  },
  completeData: {
    completed_qty: 0,
    qualified_qty: 0,
    defect_qty: 0,
    work_hours: 0,
    report_note: ''
  }
};

// ==================== 状态映射 ====================
export const STATUS_ACTION_MAP = {
  'PENDING': ['assign'],
  'ASSIGNED': ['start'],
  'STARTED': ['progress', 'pause'],
  'IN_PROGRESS': ['progress', 'complete', 'pause'],
  'PAUSED': ['resume', 'complete'],
  'COMPLETED': ['review'],
  'CANCELLED': []
};

// ==================== 权限配置 ====================
export const WORKER_PERMISSIONS = {
  'BEGINNER': ['view_own_orders', 'start_work', 'progress_report'],
  'INTERMEDIATE': ['view_own_orders', 'start_work', 'progress_report', 'complete_work'],
  'SENIOR': ['view_own_orders', 'start_work', 'progress_report', 'complete_work', 'quality_check'],
  'EXPERT': ['view_own_orders', 'start_work', 'progress_report', 'complete_work', 'quality_check', 'train_others'],
  'MASTER': ['all_permissions']
};