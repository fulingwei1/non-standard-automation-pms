// Project detail page constants
// 项目详情页面常量定义

export const PROJECT_STAGES_DETAIL = [
  {
    code: 'S1',
    name: '需求进入',
    description: '客户需求收集、评估和录入',
    color: '#10B981',
    bgColor: '#D1FAE5',
    icon: '📝',
    order: 1,
    status: {
      ACTIVE: '进行中',
      COMPLETED: '已完成',
      PENDING: '未开始',
      DELAYED: '已延期'
    }
  },
  {
    code: 'S2',
    name: '方案设计',
    description: '技术方案制定、设计和评审',
    color: '#3B82F6',
    bgColor: '#DBEAFE',
    icon: '🎯',
    order: 2,
    status: {
      ACTIVE: '进行中',
      COMPLETED: '已完成',
      PENDING: '未开始',
      DELAYED: '已延期'
    }
  },
  {
    code: 'S3',
    name: '采购备料',
    description: '物料采购、供应商管理和库存准备',
    color: '#F59E0B',
    bgColor: '#FEF3C7',
    icon: '📦',
    order: 3,
    status: {
      ACTIVE: '进行中',
      COMPLETED: '已完成',
      PENDING: '未开始',
      DELAYED: '已延期'
    }
  },
  {
    code: 'S4',
    name: '加工制造',
    description: '零部件加工、制造和质量控制',
    color: '#EF4444',
    bgColor: '#FEE2E2',
    icon: '🔧',
    order: 4,
    status: {
      ACTIVE: '进行中',
      COMPLETED: '已完成',
      PENDING: '未开始',
      DELAYED: '已延期'
    }
  },
  {
    code: 'S5',
    name: '装配调试',
    description: '设备装配、电气连接和系统调试',
    color: '#8B5CF6',
    bgColor: '#EDE9FE',
    icon: '⚙️',
    order: 5,
    status: {
      ACTIVE: '进行中',
      COMPLETED: '已完成',
      PENDING: '未开始',
      DELAYED: '已延期'
    }
  },
  {
    code: 'S6',
    name: '出厂验收 (FAT)',
    description: '工厂验收测试、功能验证和文档交付',
    color: '#EC4899',
    bgColor: '#FCE7F3',
    icon: '✅',
    order: 6,
    status: {
      ACTIVE: '进行中',
      COMPLETED: '已完成',
      PENDING: '未开始',
      DELAYED: '已延期'
    }
  },
  {
    code: 'S7',
    name: '包装发运',
    description: '设备包装、物流安排和发运准备',
    color: '#06B6D4',
    bgColor: '#CFFAFE',
    icon: '🚚',
    order: 7,
    status: {
      ACTIVE: '进行中',
      COMPLETED: '已完成',
      PENDING: '未开始',
      DELAYED: '已延期'
    }
  },
  {
    code: 'S8',
    name: '现场安装 (SAT)',
    description: '现场安装、调试和客户培训',
    color: '#14B8A6',
    bgColor: '#CCFBF1',
    icon: '🏭',
    order: 8,
    status: {
      ACTIVE: '进行中',
      COMPLETED: '已完成',
      PENDING: '未开始',
      DELAYED: '已延期'
    }
  },
  {
    code: 'S9',
    name: '质保结项',
    description: '质保期服务、项目总结和资料归档',
    color: '#6366F1',
    bgColor: '#E0E7FF',
    icon: '📊',
    order: 9,
    status: {
      ACTIVE: '进行中',
      COMPLETED: '已完成',
      PENDING: '未开始',
      DELAYED: '已延期'
    }
  }
];

export const PROJECT_STATUS = {
  ACTIVE: {
    code: 'ACTIVE',
    name: '进行中',
    color: '#3B82F6',
    bgColor: '#DBEAFE',
    icon: '🔄'
  },
  COMPLETED: {
    code: 'COMPLETED',
    name: '已完成',
    color: '#10B981',
    bgColor: '#D1FAE5',
    icon: '✅'
  },
  DELAYED: {
    code: 'DELAYED',
    name: '已延期',
    color: '#EF4444',
    bgColor: '#FEE2E2',
    icon: '⚠️'
  },
  SUSPENDED: {
    code: 'SUSPENDED',
    name: '已暂停',
    color: '#F59E0B',
    bgColor: '#FEF3C7',
    icon: '⏸️'
  },
  CANCELLED: {
    code: 'CANCELLED',
    name: '已取消',
    color: '#6B7280',
    bgColor: '#F3F4F6',
    icon: '❌'
  }
};

export const PROJECT_HEALTH = {
  H1: {
    code: 'H1',
    name: '正常',
    description: '项目按计划正常进行',
    color: '#10B981',
    bgColor: '#D1FAE5',
    textColor: '#065F46',
    progress: 100
  },
  H2: {
    code: 'H2',
    name: '有风险',
    description: '存在一定风险，需要关注',
    color: '#F59E0B',
    bgColor: '#FEF3C7',
    textColor: '#92400E',
    progress: 70
  },
  H3: {
    code: 'H3',
    name: '阻塞',
    description: '项目遇到严重问题，需要处理',
    color: '#EF4444',
    bgColor: '#FEE2E2',
    textColor: '#991B1B',
    progress: 30
  },
  H4: {
    code: 'H4',
    name: '已完结',
    description: '项目已完成',
    color: '#6B7280',
    bgColor: '#F3F4F6',
    textColor: '#374151',
    progress: 0
  }
};

export const PROJECT_ROLES = {
  PROJECT_MANAGER: {
    code: 'PM',
    name: '项目经理',
    color: '#3B82F6',
    permissions: ['project:read', 'project:write', 'project:manage', 'team:manage']
  },
  TECHNICAL_MANAGER: {
    code: 'TM',
    name: '技术经理',
    color: '#8B5CF6',
    permissions: ['project:read', 'project:write', 'tech:manage']
  },
  ENGINEER: {
    code: 'ENG',
    name: '工程师',
    color: '#10B981',
    permissions: ['project:read', 'project:write']
  },
  PURCHASING: {
    code: 'PUR',
    name: '采购员',
    color: '#F59E0B',
    permissions: ['project:read', 'purchase:write']
  },
  QUALITY: {
    code: 'QA',
    name: '质检员',
    color: '#EC4899',
    permissions: ['project:read', 'quality:write']
  },
  SALES: {
    code: 'SALE',
    name: '销售',
    color: '#06B6D4',
    permissions: ['project:read', 'sales:write']
  }
};

export const PROJECT_METRICS = {
  BUDGET: {
    code: 'BUDGET',
    name: '预算使用率',
    unit: '%',
    icon: '💰',
    thresholds: {
      WARNING: 80,
      CRITICAL: 95
    }
  },
  SCHEDULE: {
    code: 'SCHEDULE',
    name: '进度偏差',
    unit: '天',
    icon: '📅',
    thresholds: {
      WARNING: 5,
      CRITICAL: 10
    }
  },
  QUALITY: {
    code: 'QUALITY',
    name: '质量指数',
    unit: '分',
    icon: '🎯',
    thresholds: {
      WARNING: 80,
      CRITICAL: 60
    }
  },
  RISK: {
    code: 'RISK',
    name: '风险指数',
    unit: '级',
    icon: '⚠️',
    thresholds: {
      WARNING: 3,
      CRITICAL: 5
    }
  }
};

export const DOCUMENT_CATEGORIES = [
  {
    code: 'CONTRACT',
    name: '合同文档',
    description: '项目合同、协议、附件等',
    icon: '📄',
    color: '#3B82F6'
  },
  {
    code: 'TECHNICAL',
    name: '技术文档',
    description: '设计图纸、技术规格书、BOM等',
    icon: '📐',
    color: '#8B5CF6'
  },
  {
    code: 'MANAGEMENT',
    name: '管理文档',
    description: '项目计划、会议记录、报告等',
    icon: '📋',
    color: '#10B981'
  },
  {
    code: 'QUALITY',
    name: '质量文档',
    description: '检验报告、验收单、证书等',
    icon: '📊',
    color: '#F59E0B'
  },
  {
    code: 'COMMUNICATION',
    name: '沟通记录',
    description: '邮件往来、会议纪要等',
    icon: '💬',
    color: '#EC4899'
  }
];

export const MILESTONE_STATUSES = {
  NOT_STARTED: {
    code: 'NOT_STARTED',
    name: '未开始',
    color: '#9CA3AF',
    bgColor: '#F3F4F6'
  },
  IN_PROGRESS: {
    code: 'IN_PROGRESS',
    name: '进行中',
    color: '#F59E0B',
    bgColor: '#FEF3C7'
  },
  COMPLETED: {
    code: 'COMPLETED',
    name: '已完成',
    color: '#10B981',
    bgColor: '#D1FAE5'
  },
  DELAYED: {
    code: 'DELAYED',
    name: '已延期',
    color: '#EF4444',
    bgColor: '#FEE2E2'
  }
};

export const PROJECT_PRIORITY = {
  HIGH: {
    code: 'HIGH',
    name: '高',
    color: '#EF4444',
    icon: '🔥'
  },
  MEDIUM: {
    code: 'MEDIUM',
    name: '中',
    color: '#F59E0B',
    icon: '⚡'
  },
  LOW: {
    code: 'LOW',
    name: '低',
    color: '#10B981',
    icon: '📈'
  }
};