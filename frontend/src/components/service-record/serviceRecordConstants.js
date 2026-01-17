/**
 * Service Record Constants - 服务记录配置常量
 * 包含服务类型、状态、优先级、反馈评级、报告模板等配置
 */

// ==================== 服务类型配置 ====================
export const SERVICE_TYPES = {
  INSTALLATION: {
    label: "安装调试",
    category: "technical",
    icon: "Wrench",
    estimatedHours: { min: 4, max: 8 },
    difficulty: "medium",
    requiredSkills: ["电气知识", "机械安装", "调试经验"],
    checklist: [
    "现场环境检查",
    "设备安装定位",
    "电气连接测试",
    "功能调试验证",
    "安全规范检查",
    "客户操作培训"]

  },
  TRAINING: {
    label: "操作培训",
    category: "education",
    icon: "Users",
    estimatedHours: { min: 2, max: 4 },
    difficulty: "low",
    requiredSkills: ["教学能力", "产品知识", "沟通技巧"],
    checklist: [
    "培训需求确认",
    "培训材料准备",
    "理论培训实施",
    "实操演示指导",
    "考核评估",
    "培训证书发放"]

  },
  MAINTENANCE: {
    label: "定期维护",
    category: "maintenance",
    icon: "RefreshCw",
    estimatedHours: { min: 2, max: 6 },
    difficulty: "low",
    requiredSkills: ["设备维护", "故障诊断", "预防性维护"],
    checklist: [
    "维护计划确认",
    "设备清洁检查",
    "功能测试验证",
    "易损件检查",
    "维护记录更新",
    "下次维护计划"]

  },
  REPAIR: {
    label: "故障维修",
    category: "repair",
    icon: "AlertTriangle",
    estimatedHours: { min: 3, max: 12 },
    difficulty: "high",
    requiredSkills: ["故障诊断", "维修技术", "应急处理"],
    checklist: [
    "故障现象确认",
    "原因分析诊断",
    "维修方案制定",
    "备件准备更换",
    "功能测试验证",
    "预防建议提供"]

  },
  UPGRADE: {
    label: "升级改造",
    category: "technical",
    icon: "TrendingUp",
    estimatedHours: { min: 6, max: 16 },
    difficulty: "high",
    requiredSkills: ["系统升级", "软硬件集成", "项目管理"],
    checklist: [
    "升级方案设计",
    "兼容性检查",
    "升级实施执行",
    "数据迁移备份",
    "功能验证测试",
    "文档更新完善"]

  },
  CONSULTATION: {
    label: "技术咨询",
    category: "consultation",
    icon: "FileText",
    estimatedHours: { min: 1, max: 4 },
    difficulty: "low",
    requiredSkills: ["专业知识", "解决方案", "客户沟通"],
    checklist: [
    "需求分析确认",
    "技术方案建议",
    "问题解答指导",
    "改进建议提供",
    "后续跟踪服务",
    "知识分享传递"]

  }
};

// ==================== 服务状态配置 ====================
export const SERVICE_STATUS = {
  SCHEDULED: {
    label: "已安排",
    color: "bg-blue-500",
    icon: "Calendar",
    description: "服务已安排，等待执行",
    nextActions: ["开始服务", "修改安排", "取消服务"],
    canEdit: true,
    canCancel: true
  },
  IN_PROGRESS: {
    label: "进行中",
    color: "bg-amber-500",
    icon: "Clock",
    description: "服务正在进行中",
    nextActions: ["完成服务", "暂停服务", "添加备注"],
    canEdit: true,
    canCancel: false
  },
  PAUSED: {
    label: "已暂停",
    color: "bg-purple-500",
    icon: "PauseCircle",
    description: "服务暂时暂停",
    nextActions: ["继续服务", "取消服务"],
    canEdit: true,
    canCancel: true
  },
  COMPLETED: {
    label: "已完成",
    color: "bg-emerald-500",
    icon: "CheckCircle2",
    description: "服务已完成",
    nextActions: ["查看报告", "客户确认", "评价服务"],
    canEdit: false,
    canCancel: false
  },
  CANCELLED: {
    label: "已取消",
    color: "bg-gray-500",
    icon: "XCircle",
    description: "服务已取消",
    nextActions: ["查看原因", "重新安排"],
    canEdit: false,
    canCancel: false
  },
  PENDING_REVIEW: {
    label: "待审核",
    color: "bg-orange-500",
    icon: "Eye",
    description: "服务报告待审核",
    nextActions: ["审核报告", "要求修改", "确认通过"],
    canEdit: false,
    canCancel: false
  }
};

// ==================== 优先级配置 ====================
export const SERVICE_PRIORITY = {
  LOW: {
    label: "低",
    level: 1,
    color: "bg-gray-500",
    description: "常规服务，可正常安排",
    responseTime: "48小时内",
    slaHours: 72
  },
  NORMAL: {
    label: "普通",
    level: 2,
    color: "bg-blue-500",
    description: "标准服务，按时处理",
    responseTime: "24小时内",
    slaHours: 48
  },
  HIGH: {
    label: "高",
    level: 3,
    color: "bg-amber-500",
    description: "重要服务，优先处理",
    responseTime: "12小时内",
    slaHours: 24
  },
  URGENT: {
    label: "紧急",
    level: 4,
    color: "bg-red-500",
    description: "紧急服务，立即处理",
    responseTime: "4小时内",
    slaHours: 8
  },
  CRITICAL: {
    label: "危急",
    level: 5,
    color: "bg-purple-500",
    description: "严重影响生产，立即响应",
    responseTime: "1小时内",
    slaHours: 4
  }
};

// ==================== 客户反馈评级配置 ====================
export const FEEDBACK_RATINGS = {
  EXCELLENT: {
    label: "非常满意",
    score: 5,
    color: "bg-emerald-500",
    icon: "Star",
    description: "服务超出预期，非常满意",
    followUpRequired: false,
    autoPublish: true
  },
  SATISFIED: {
    label: "满意",
    score: 4,
    color: "bg-blue-500",
    icon: "ThumbsUp",
    description: "服务符合预期，基本满意",
    followUpRequired: false,
    autoPublish: true
  },
  NEUTRAL: {
    label: "一般",
    score: 3,
    color: "bg-amber-500",
    icon: "Minus",
    description: "服务基本满足要求，有改进空间",
    followUpRequired: true,
    autoPublish: false
  },
  DISSATISFIED: {
    label: "不满意",
    score: 2,
    color: "bg-orange-500",
    icon: "ThumbsDown",
    description: "服务未达预期，存在问题",
    followUpRequired: true,
    autoPublish: false
  },
  VERY_DISSATISFIED: {
    label: "非常不满意",
    score: 1,
    color: "bg-red-500",
    icon: "XCircle",
    description: "服务严重不足，需要改进",
    followUpRequired: true,
    autoEscalate: true,
    autoPublish: false
  }
};

// ==================== 服务质量问题分类 ====================
export const ISSUE_CATEGORIES = {
  TECHNICAL: {
    label: "技术问题",
    subcategories: [
    "设备故障",
    "软件bug",
    "兼容性问题",
    "性能问题",
    "安全漏洞"]

  },
  SERVICE: {
    label: "服务问题",
    subcategories: [
    "响应不及时",
    "技术能力不足",
    "态度问题",
    "沟通不清晰",
    "服务不完整"]

  },
  PRODUCT: {
    label: "产品问题",
    subcategories: [
    "设计缺陷",
    "质量问题",
    "功能不符",
    "文档不清",
    "配件缺失"]

  },
  PROCESS: {
    label: "流程问题",
    subcategories: [
    "预约不便",
    "流程繁琐",
    "信息不准确",
    "协调不畅",
    "反馈滞后"]

  }
};

// ==================== 服务报告模板配置 ====================
export const REPORT_TEMPLATES = {
  BASIC: {
    label: "基础报告",
    sections: [
    "服务概述",
    "问题描述",
    "解决方案",
    "服务结果",
    "客户确认"],

    requiredFields: ["service_date", "customer_name", "description", "result"],
    optionalFields: ["photos", "recommendations"]
  },
  DETAILED: {
    label: "详细报告",
    sections: [
    "服务概述",
    "问题背景",
    "检查过程",
    "故障分析",
    "解决方案",
    "实施过程",
    "测试验证",
    "服务结果",
    "客户培训",
    "预防建议",
    "客户确认"],

    requiredFields: [
    "service_date", "customer_name", "background", "check_process",
    "analysis", "solution", "implementation", "test_result", "result"],

    optionalFields: ["photos", "training_materials", "maintenance_plan"]
  },
  MAINTENANCE: {
    label: "维护报告",
    sections: [
    "维护概述",
    "设备状态",
    "维护项目",
    "检查结果",
    "更换部件",
    "性能参数",
    "维护建议",
    "下次计划",
    "客户确认"],

    requiredFields: [
    "maintenance_date", "equipment_status", "maintenance_items",
    "check_results", "result", "next_plan"],

    optionalFields: ["photos", "performance_data", "parts_replaced"]
  }
};

// ==================== 服务成本配置 ====================
export const SERVICE_COSTS = {
  LABOR_RATES: {
    JUNIOR: 150, // 初级工程师 - 元/小时
    INTERMEDIATE: 250, // 中级工程师 - 元/小时
    SENIOR: 350, // 高级工程师 - 元/小时
    EXPERT: 500 // 专家 - 元/小时
  },
  TRAVEL_COSTS: {
    LOCAL: 0.8, // 本地交通 - 元/公里
    OUT_OF_TOWN: 1.2, // 外地交通 - 元/公里
    ACCOMMODATION: 300, // 住宿补贴 - 元/天
    MEALS: 150 // 餐补 - 元/天
  },
  MATERIAL_COSTS: {
    SMALL_PARTS: 50, // 小零件 - 元
    STANDARD_TOOLS: 100, // 标准工具 - 元
    SPECIAL_EQUIPMENT: 500, // 特殊设备 - 元/天
    CONSUMABLES: 30 // 消耗品 - 元
  }
};

// ==================== 服务时间配置 ====================
export const SERVICE_TIME_CONFIG = {
  WORKING_HOURS: {
    START: "08:00",
    END: "18:00",
    BREAK_START: "12:00",
    BREAK_END: "13:00",
    WORK_DAYS: [1, 2, 3, 4, 5], // 周一到周五
    HOLIDAYS: [] // 节假日列表
  },
  RESPONSE_TIMES: {
    URGENT: 2, // 紧急 - 2小时
    HIGH: 4, // 高 - 4小时
    NORMAL: 8, // 普通 - 8小时
    LOW: 24 // 低 - 24小时
  },
  SERVICE_WINDOWS: {
    MORNING: { start: "08:00", end: "12:00" },
    AFTERNOON: { start: "14:00", end: "18:00" },
    EVENING: { start: "18:00", end: "21:00" },
    WEEKEND: { start: "09:00", end: "17:00" }
  }
};

// ==================== 工具函数 ====================

/**
 * 获取服务类型配置
 */
export const getServiceTypeConfig = (type) => {
  return SERVICE_TYPES[type] || SERVICE_TYPES.CONSULTATION;
};

/**
 * 获取服务状态配置
 */
export const getServiceStatusConfig = (status) => {
  return SERVICE_STATUS[status] || SERVICE_STATUS.SCHEDULED;
};

/**
 * 获取优先级配置
 */
export const getPriorityConfig = (priority) => {
  return SERVICE_PRIORITY[priority] || SERVICE_PRIORITY.NORMAL;
};

/**
 * 获取反馈评级配置
 */
export const getFeedbackConfig = (rating) => {
  return FEEDBACK_RATINGS[rating] || FEEDBACK_RATINGS.NEUTRAL;
};

/**
 * 计算服务时长
 */
export const calculateServiceDuration = (startTime, endTime) => {
  if (!startTime || !endTime) return 0;

  const start = new Date(startTime);
  const end = new Date(endTime);
  const diffMs = end - start;
  const diffHours = diffMs / (1000 * 60 * 60);

  return Math.round(diffHours * 100) / 100; // 保留两位小数
};

/**
 * 计算服务响应时间
 */
export const calculateResponseTime = (requestTime, startTime) => {
  if (!requestTime || !startTime) return 0;

  const request = new Date(requestTime);
  const start = new Date(startTime);
  const diffMs = start - request;
  const diffHours = diffMs / (1000 * 60 * 60);

  return Math.round(diffHours * 100) / 100;
};

/**
 * 检查SLA是否达标
 */
export const checkSLACompliance = (responseTime, priority) => {
  const priorityConfig = getPriorityConfig(priority);
  return responseTime <= priorityConfig.slaHours;
};

/**
 * 计算服务成本
 */
export const calculateServiceCost = (engineerLevel, duration, distance = 0, materials = 0) => {
  const laborRate = SERVICE_COSTS.LABOR_RATES[engineerLevel] || SERVICE_COSTS.LABOR_RATES.INTERMEDIATE;
  const laborCost = laborRate * duration;
  const travelCost = distance * SERVICE_COSTS.TRAVEL_COSTS.LOCAL;
  const materialCost = materials;

  return {
    labor: laborCost,
    travel: travelCost,
    materials: materialCost,
    total: laborCost + travelCost + materialCost
  };
};

/**
 * 获取服务检查清单
 */
export const getServiceChecklist = (serviceType) => {
  const typeConfig = getServiceTypeConfig(serviceType);
  return typeConfig.checklist || [];
};

/**
 * 验证服务数据完整性
 */
export const validateServiceData = (data, template) => {
  const templateConfig = REPORT_TEMPLATES[template] || REPORT_TEMPLATES.BASIC;
  const errors = [];

  // 检查必填字段
  templateConfig.requiredFields.forEach((field) => {
    if (!data[field] || data[field] === '') {
      errors.push(`${field} 为必填项`);
    }
  });

  // 检查时间逻辑
  if (data.start_time && data.end_time) {
    if (new Date(data.end_time) <= new Date(data.start_time)) {
      errors.push('结束时间必须晚于开始时间');
    }
  }

  // 检查评分范围
  if (data.rating && (data.rating < 1 || data.rating > 5)) {
    errors.push('评分必须在1-5之间');
  }

  return errors;
};

/**
 * 生成服务报告编号
 */
export const generateServiceReportNumber = (serviceType, date = new Date()) => {
  const typeCode = serviceType.substring(0, 2).toUpperCase();
  const year = date.getFullYear();
  const month = String(date.getMonth() + 1).padStart(2, '0');
  const day = String(date.getDate()).padStart(2, '0');
  const random = Math.floor(Math.random() * 1000).toString().padStart(3, '0');

  return `SR${typeCode}${year}${month}${day}${random}`;
};

/**
 * 获取服务状态变更历史
 */
export const getServiceStatusHistory = (records) => {
  if (!records || records.length === 0) return [];

  const history = [];
  let previousStatus = null;

  records.forEach((record, _index) => {
    if (record.status !== previousStatus) {
      history.push({
        timestamp: record.created_time,
        status: record.status,
        operator: record.operator || 'System',
        note: record.status_note || ''
      });
      previousStatus = record.status;
    }
  });

  return history;
};

/**
 * 获取推荐的下次服务时间
 */
export const getNextServiceRecommendation = (serviceType, lastServiceDate) => {
  const recommendations = {
    [SERVICE_TYPES.MAINTENANCE.label]: { days: 90, unit: 'quarterly' },
    [SERVICE_TYPES.TRAINING.label]: { days: 180, unit: 'semiannual' },
    [SERVICE_TYPES.CONSULTATION.label]: { days: 30, unit: 'monthly' },
    [SERVICE_TYPES.REPAIR.label]: { days: 7, unit: 'weekly' }
  };

  const serviceTypeConfig = getServiceTypeConfig(serviceType);
  const recommendation = recommendations[serviceTypeConfig.label];

  if (!recommendation) return null;

  const nextDate = new Date(lastServiceDate);
  nextDate.setDate(nextDate.getDate() + recommendation.days);

  return {
    date: nextDate,
    unit: recommendation.unit,
    reason: `基于${serviceTypeConfig.label}建议`
  };
};

/**
 * 计算服务完成率
 */
export const calculateServiceCompletionRate = (services, dateRange = null) => {
  let filteredServices = services;

  if (dateRange) {
    filteredServices = services.filter((service) => {
      const serviceDate = new Date(service.created_time);
      return serviceDate >= dateRange.start && serviceDate <= dateRange.end;
    });
  }

  const completedServices = filteredServices.filter((service) =>
  service.status === SERVICE_STATUS.COMPLETED.label
  );

  return filteredServices.length > 0 ?
  Math.round(completedServices.length / filteredServices.length * 100) :
  0;
};

/**
 * 获取服务质量评分
 */
export const getServiceQualityScore = (feedbacks) => {
  if (!feedbacks || feedbacks.length === 0) return 0;

  const totalScore = feedbacks.reduce((sum, feedback) => sum + feedback.rating, 0);
  return Math.round(totalScore / feedbacks.length * 100) / 100;
};

/**
 * 检查是否需要升级处理
 */
export const requiresEscalation = (feedback, issueCategory) => {
  const feedbackConfig = getFeedbackConfig(feedback.rating);

  return feedbackConfig.autoEscalate ||
  issueCategory === ISSUE_CATEGORIES.TECHNICAL.label ||
  feedback.rating <= 2; // 不满意或非常不满意
};

// ==================== 导出默认配置 ====================
export const DEFAULT_SERVICE_CONFIG = {
  type: 'CONSULTATION',
  priority: 'NORMAL',
  status: 'SCHEDULED',
  estimatedHours: 4,
  engineerLevel: 'INTERMEDIATE'
};

export const DEFAULT_REPORT_CONFIG = {
  template: 'BASIC',
  includePhotos: true,
  requireCustomerSignature: true,
  autoGeneratePDF: true
};

// ==================== 消息模板 ====================
export const SERVICE_MESSAGES = {
  SCHEDULE_CONFIRM: {
    title: "服务安排确认",
    template: "您的{serviceType}服务已安排在{date}，工程师{engineer}将为您提供服务。"
  },
  START_NOTIFICATION: {
    title: "服务开始通知",
    template: "工程师{engineer}已开始为您提供{serviceType}服务。"
  },
  COMPLETE_NOTIFICATION: {
    title: "服务完成通知",
    template: "您的{serviceType}服务已完成，请查看服务报告并提供反馈。"
  },
  FEEDBACK_REQUEST: {
    title: "服务反馈请求",
    template: "感谢您使用我们的服务，请对本次服务进行评价，您的反馈对我们很重要。"
  },
  FOLLOW_UP: {
    title: "服务回访",
    template: "我们想了解您对上次服务的满意度，是否有任何需要改进的地方？"
  }
};