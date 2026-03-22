/**
 * Payment Config Constants - 支付管理系统配置数据
 * 支付类型、状态、账龄、催收、信用评级、统计指标、提醒类型等纯数据配置
 */

// ==================== 支付类型配置 ====================

export const PAYMENT_TYPES = {
  DEPOSIT: {
    key: 'deposit',
    label: '签约款',
    description: '合同签订时的首付款',
    ratio: '30%',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    icon: 'DollarSign',
    priority: 1,
    dueDays: 7,
    taxable: true
  },
  PROGRESS: {
    key: 'progress',
    label: '进度款',
    description: '按项目进度支付的款项',
    ratio: '40%',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    icon: 'TrendingUp',
    priority: 2,
    dueDays: 15,
    taxable: true
  },
  DELIVERY: {
    key: 'delivery',
    label: '发货款',
    description: '产品发货后的付款',
    ratio: '20%',
    color: 'bg-purple-500',
    textColor: 'text-purple-400',
    bgColor: 'bg-purple-500/10',
    borderColor: 'border-purple-500/30',
    icon: 'Truck',
    priority: 3,
    dueDays: 10,
    taxable: true
  },
  ACCEPTANCE: {
    key: 'acceptance',
    label: '验收款',
    description: '项目验收合格后的付款',
    ratio: '5%',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    icon: 'CheckCircle2',
    priority: 4,
    dueDays: 7,
    taxable: true
  },
  WARRANTY: {
    key: 'warranty',
    label: '质保金',
    description: '质量保证金，质保期满后退还',
    ratio: '5%',
    color: 'bg-slate-500',
    textColor: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/30',
    icon: 'Shield',
    priority: 5,
    dueDays: 30,
    taxable: false
  }
};

export const PAYMENT_TYPE_OPTIONS = Object.values(PAYMENT_TYPES);

// ==================== 支付状态配置 ====================

export const PAYMENT_STATUS = {
  PAID: {
    key: 'paid',
    label: '已到账',
    description: '款项已收到',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
    borderColor: 'border-emerald-500/30',
    icon: 'CheckCircle2',
    canEdit: false,
    canCancel: false,
    nextActions: []
  },
  PENDING: {
    key: 'pending',
    label: '待收款',
    description: '等待客户付款',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
    borderColor: 'border-blue-500/30',
    icon: 'Clock',
    canEdit: true,
    canCancel: true,
    nextActions: ['send_reminder', 'apply_invoice', 'mark_paid']
  },
  OVERDUE: {
    key: 'overdue',
    label: '已逾期',
    description: '付款已超过截止日期',
    color: 'bg-red-500',
    textColor: 'text-red-400',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-red-500/30',
    icon: 'AlertTriangle',
    canEdit: true,
    canCancel: false,
    nextActions: ['send_urgent_reminder', 'escalate', 'legal_action']
  },
  INVOICED: {
    key: 'invoiced',
    label: '已开票',
    description: '发票已开出，等待付款',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    bgColor: 'bg-amber-500/10',
    borderColor: 'border-amber-500/30',
    icon: 'FileText',
    canEdit: true,
    canCancel: true,
    nextActions: ['send_invoice', 'follow_up', 'mark_paid']
  },
  CANCELLED: {
    key: 'cancelled',
    label: '已取消',
    description: '支付已取消',
    color: 'bg-slate-500',
    textColor: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
    borderColor: 'border-slate-500/30',
    icon: 'X',
    canEdit: false,
    canCancel: false,
    nextActions: []
  }
};

export const PAYMENT_STATUS_OPTIONS = Object.values(PAYMENT_STATUS);

// ==================== 发票状态配置 ====================

export const INVOICE_STATUS = {
  DRAFT: {
    key: 'draft',
    label: '草稿',
    color: 'bg-slate-500',
    textColor: 'text-slate-400',
    icon: 'FileText'
  },
  ISSUED: {
    key: 'issued',
    label: '已开具',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    icon: 'Send'
  },
  SENT: {
    key: 'sent',
    label: '已发送',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    icon: 'Mail'
  },
  PAID: {
    key: 'paid',
    label: '已付款',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    icon: 'CheckCircle2'
  },
  CANCELLED: {
    key: 'cancelled',
    label: '已作废',
    color: 'bg-red-500',
    textColor: 'text-red-400',
    icon: 'X'
  }
};

export const INVOICE_STATUS_OPTIONS = Object.values(INVOICE_STATUS);

// ==================== 账龄分析配置 ====================

export const AGING_PERIODS = {
  CURRENT: {
    key: 'current',
    label: '当前',
    minDays: 0,
    maxDays: 0,
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    riskLevel: 'low'
  },
  DAYS_1_30: {
    key: 'days_1_30',
    label: '1-30天',
    minDays: 1,
    maxDays: 30,
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    riskLevel: 'low'
  },
  DAYS_31_60: {
    key: 'days_31_60',
    label: '31-60天',
    minDays: 31,
    maxDays: 60,
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    riskLevel: 'medium'
  },
  DAYS_61_90: {
    key: 'days_61_90',
    label: '61-90天',
    minDays: 61,
    maxDays: 90,
    color: 'bg-orange-500',
    textColor: 'text-orange-400',
    riskLevel: 'high'
  },
  DAYS_OVER_90: {
    key: 'days_over_90',
    label: '90天以上',
    minDays: 91,
    maxDays: 999,
    color: 'bg-red-500',
    textColor: 'text-red-400',
    riskLevel: 'critical'
  }
};

export const AGING_PERIOD_OPTIONS = Object.values(AGING_PERIODS);

// ==================== 催收级别配置 ====================

export const COLLECTION_LEVELS = {
  NORMAL: {
    key: 'normal',
    label: '正常',
    description: '按正常流程催收',
    interval: 7,
    methods: ['email', 'phone'],
    template: 'normal_reminder',
    priority: 'low'
  },
  WARNING: {
    key: 'warning',
    label: '预警',
    description: '需要重点关注',
    interval: 3,
    methods: ['email', 'phone', 'sms'],
    template: 'warning_reminder',
    priority: 'medium'
  },
  URGENT: {
    key: 'urgent',
    label: '紧急',
    description: '需要立即处理',
    interval: 1,
    methods: ['phone', 'sms', 'visit'],
    template: 'urgent_reminder',
    priority: 'high'
  },
  CRITICAL: {
    key: 'critical',
    label: '严重',
    description: '需要升级处理',
    interval: 0,
    methods: ['legal', 'management'],
    template: 'critical_reminder',
    priority: 'critical'
  }
};

export const COLLECTION_LEVEL_OPTIONS = Object.values(COLLECTION_LEVELS);

// ==================== 催收方式配置 ====================

export const COLLECTION_METHODS = {
  EMAIL: {
    key: 'email',
    label: '邮件',
    icon: 'Mail',
    cost: 0.1,
    effectiveness: 0.6,
    description: '发送催收邮件'
  },
  PHONE: {
    key: 'phone',
    label: '电话',
    icon: 'Phone',
    cost: 2.0,
    effectiveness: 0.8,
    description: '电话催收'
  },
  SMS: {
    key: 'sms',
    label: '短信',
    icon: 'MessageSquare',
    cost: 0.5,
    effectiveness: 0.7,
    description: '发送催收短信'
  },
  LETTER: {
    key: 'letter',
    label: '信函',
    icon: 'FileText',
    cost: 5.0,
    effectiveness: 0.9,
    description: '发送催收函'
  },
  VISIT: {
    key: 'visit',
    label: '上门',
    icon: 'Users',
    cost: 50.0,
    effectiveness: 0.95,
    description: '上门催收'
  },
  LEGAL: {
    key: 'legal',
    label: '法律',
    icon: 'Scale',
    cost: 1000.0,
    effectiveness: 0.98,
    description: '法律途径催收'
  }
};

export const COLLECTION_METHOD_OPTIONS = Object.values(COLLECTION_METHODS);

// ==================== 支付方式配置 ====================

export const PAYMENT_METHODS = {
  CASH: {
    key: 'cash',
    label: '现金',
    icon: 'Banknote',
    fee: 0,
    description: '现金支付',
    receiptRequired: true
  },
  BANK_TRANSFER: {
    key: 'bank_transfer',
    label: '银行转账',
    icon: 'Building2',
    fee: 0.005,
    description: '银行转账',
    receiptRequired: true
  },
  CHECK: {
    key: 'check',
    label: '支票',
    icon: 'FileText',
    fee: 0.001,
    description: '支票支付',
    receiptRequired: true
  },
  CREDIT_CARD: {
    key: 'credit_card',
    label: '信用卡',
    icon: 'CreditCard',
    fee: 0.025,
    description: '信用卡支付',
    receiptRequired: false
  },
  ALIPAY: {
    key: 'alipay',
    label: '支付宝',
    icon: 'Smartphone',
    fee: 0.006,
    description: '支付宝支付',
    receiptRequired: false
  },
  WECHAT: {
    key: 'wechat',
    label: '微信',
    icon: 'MessageSquare',
    fee: 0.006,
    description: '微信支付',
    receiptRequired: false
  },
  OTHER: {
    key: 'other',
    label: '其他',
    icon: 'MoreHorizontal',
    fee: 0,
    description: '其他支付方式',
    receiptRequired: true
  }
};

export const PAYMENT_METHOD_OPTIONS = Object.values(PAYMENT_METHODS);

// ==================== 客户信用等级配置 ====================

export const CREDIT_RATINGS = {
  AAA: {
    key: 'AAA',
    label: 'AAA级',
    description: '信用极佳',
    color: 'bg-emerald-500',
    textColor: 'text-emerald-400',
    creditLimit: 1000000,
    paymentTerms: 30,
    riskLevel: 'very_low'
  },
  AA: {
    key: 'AA',
    label: 'AA级',
    description: '信用优秀',
    color: 'bg-green-500',
    textColor: 'text-green-400',
    creditLimit: 500000,
    paymentTerms: 30,
    riskLevel: 'low'
  },
  A: {
    key: 'A',
    label: 'A级',
    description: '信用良好',
    color: 'bg-blue-500',
    textColor: 'text-blue-400',
    creditLimit: 200000,
    paymentTerms: 30,
    riskLevel: 'medium'
  },
  BBB: {
    key: 'BBB',
    label: 'BBB级',
    description: '信用一般',
    color: 'bg-amber-500',
    textColor: 'text-amber-400',
    creditLimit: 100000,
    paymentTerms: 15,
    riskLevel: 'medium_high'
  },
  BB: {
    key: 'BB',
    label: 'BB级',
    description: '信用较差',
    color: 'bg-orange-500',
    textColor: 'text-orange-400',
    creditLimit: 50000,
    paymentTerms: 7,
    riskLevel: 'high'
  },
  B: {
    key: 'B',
    label: 'B级',
    description: '信用差',
    color: 'bg-red-500',
    textColor: 'text-red-400',
    creditLimit: 10000,
    paymentTerms: 0,
    riskLevel: 'very_high'
  }
};

export const CREDIT_RATING_OPTIONS = Object.values(CREDIT_RATINGS);

// ==================== 统计指标配置 ====================

export const PAYMENT_METRICS = {
  TOTAL_RECEIVABLES: {
    key: 'total_receivables',
    label: '应收账款总额',
    unit: '¥',
    format: 'currency',
    description: '所有未收款项的总和'
  },
  OVERDUE_AMOUNT: {
    key: 'overdue_amount',
    label: '逾期金额',
    unit: '¥',
    format: 'currency',
    description: '已逾期的款项金额'
  },
  COLLECTION_RATE: {
    key: 'collection_rate',
    label: '回款率',
    unit: '%',
    format: 'percentage',
    description: '本期回款金额占总应收的比例'
  },
  DSO: {
    key: 'dso',
    label: 'DSO天数',
    unit: '天',
    format: 'number',
    description: '应收账款周转天数'
  },
  AGING_DAYS: {
    key: 'aging_days',
    label: '平均账龄',
    unit: '天',
    format: 'number',
    description: '应收账款的平均账龄'
  },
  INVOICE_COUNT: {
    key: 'invoice_count',
    label: '开票数量',
    unit: '张',
    format: 'number',
    description: '本期开具的发票数量'
  },
  COLLECTION_COUNT: {
    key: 'collection_count',
    label: '催收次数',
    unit: '次',
    format: 'number',
    description: '本期进行的催收操作次数'
  }
};

export const PAYMENT_METRIC_OPTIONS = Object.values(PAYMENT_METRICS);

// ==================== 提醒类型配置 ====================

export const REMINDER_TYPES = {
  DUE_DATE: {
    key: 'due_date',
    label: '到期提醒',
    description: '付款到期前提醒',
    daysBefore: [7, 3, 1],
    template: 'payment_due_reminder'
  },
  OVERDUE: {
    key: 'overdue',
    label: '逾期提醒',
    description: '付款逾期后提醒',
    daysAfter: [1, 7, 15, 30],
    template: 'payment_overdue_reminder'
  },
  INVOICE_ISSUED: {
    key: 'invoice_issued',
    label: '开票通知',
    description: '发票开具后通知',
    daysAfter: 1,
    template: 'invoice_issued_notification'
  },
  PAYMENT_RECEIVED: {
    key: 'payment_received',
    label: '收款确认',
    description: '收到付款后确认',
    daysAfter: 1,
    template: 'payment_received_confirmation'
  }
};

export const REMINDER_TYPE_OPTIONS = Object.values(REMINDER_TYPES);
