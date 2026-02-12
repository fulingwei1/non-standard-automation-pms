/**
 * Contract Management Constants
 * 合同管理系统常量配置
 */

export const CONTRACT_TYPES = {
  SALES: { value: 'sales', label: '销售合同', color: '#1890ff', icon: '📋' },
  SERVICE: { value: 'service', label: '服务合同', color: '#52c41a', icon: '🔧' },
  PURCHASE: { value: 'purchase', label: '采购合同', color: '#722ed1', icon: '🛒' },
  MAINTENANCE: { value: 'maintenance', label: '维护合同', color: '#faad14', icon: '🔨' },
  LEASE: { value: 'lease', label: '租赁合同', color: '#13c2c2', icon: '🏠' },
  FRAMEWORK: { value: 'framework', label: '框架合同', color: '#eb2f96', icon: '📊' }
};

export const CONTRACT_STATUS = {
  DRAFT: { value: 'draft', label: '草稿', color: '#d9d9d9' },
  REVIEW: { value: 'review', label: '审核中', color: '#faad14' },
  APPROVED: { value: 'approved', label: '已批准', color: '#1890ff' },
  SIGNED: { value: 'signed', label: '已签署', color: '#52c41a' },
  EXECUTING: { value: 'executing', label: '执行中', color: '#722ed1' },
  COMPLETED: { value: 'completed', label: '已完成', color: '#13c2c2' },
  TERMINATED: { value: 'terminated', label: '已终止', color: '#ff4d4f' },
  EXPIRED: { value: 'expired', label: '已过期', color: '#8c8c8c' }
};

export const SIGNATURE_STATUS = {
  NOT_SIGNED: { value: 'not_signed', label: '未签署', color: '#d9d9d9' },
  PENDING: { value: 'pending', label: '待签署', color: '#faad14' },
  SIGNED: { value: 'signed', label: '已签署', color: '#52c41a' },
  REJECTED: { value: 'rejected', label: '已拒签', color: '#ff4d4f' }
};

export const PAYMENT_TERMS = {
  FULL_PAYMENT: { value: 'full_payment', label: '全款预付' },
  INSTALLMENT: { value: 'installment', label: '分期付款' },
  PROGRESS: { value: 'progress', label: '进度付款' },
  ACCEPTANCE: { value: 'acceptance', label: '验收付款' },
  MONTHLY: { value: 'monthly', label: '按月付款' }
};

export const RISK_LEVELS = {
  LOW: { value: 'low', label: '低风险', color: '#52c41a', weight: 1 },
  MEDIUM: { value: 'medium', label: '中风险', color: '#faad14', weight: 2 },
  HIGH: { value: 'high', label: '高风险', color: '#ff4d4f', weight: 3 },
  CRITICAL: { value: 'critical', label: '极高风险', color: '#8b0000', weight: 4 }
};

export const APPROVAL_LEVELS = {
  MANAGER: { value: 'manager', label: '经理审批' },
  DIRECTOR: { value: 'director', label: '总监审批' },
  VP: { value: 'vp', label: '副总裁审批' },
  CEO: { value: 'ceo', label: 'CEO审批' },
  BOARD: { value: 'board', label: '董事会审批' }
};

export const CONTRACT_TEMPLATES = {
  STANDARD_SALES: { value: 'standard_sales', label: '标准销售合同' },
  SERVICE_AGREEMENT: { value: 'service_agreement', label: '服务协议' },
  NDA: { value: 'nda', label: '保密协议' },
  MOU: { value: 'mou', label: '合作备忘录' }
};

export const DOCUMENT_TYPES = {
  CONTRACT: { value: 'contract', label: '合同正文' },
  ATTACHMENT: { value: 'attachment', label: '附件' },
  AMENDMENT: { value: 'amendment', label: '补充协议' },
  CANCELLATION: { value: 'cancellation', label: '取消协议' }
};

export const NOTIFICATION_EVENTS = {
  SIGNING_DUE: { value: 'signing_due', label: '签署到期' },
  PAYMENT_DUE: { value: 'payment_due', label: '付款到期' },
  EXPIRATION_WARNING: { value: 'expiration_warning', label: '到期提醒' },
  APPROVAL_REQUIRED: { value: 'approval_required', label: '需要审批' }
};

export const TABLE_CONFIG = {
  pagination: { pageSize: 10, showSizeChanger: true },
  scroll: { x: 1400, y: 500 },
  size: 'middle'
};

export const DEFAULT_FILTERS = {
  type: null,
  status: null,
  signatureStatus: null,
  riskLevel: null,
  dateRange: null,
  amountRange: null
};

export const CHART_COLORS = {
  POSITIVE: '#52c41a',
  WARNING: '#faad14',
  NEGATIVE: '#ff4d4f',
  PRIMARY: '#1890ff',
  SECONDARY: '#722ed1'
};