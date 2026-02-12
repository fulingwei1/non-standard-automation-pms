/**
 * Approval Center Constants
 * 审批中心系统常量配置
 */

export const APPROVAL_TYPES = {
  PURCHASE: { value: 'purchase', label: '采购审批', color: '#1890ff', icon: '🛒' },
  EXPENSE: { value: 'expense', label: '费用审批', color: '#52c41a', icon: '💰' },
  LEAVE: { value: 'leave', label: '请假审批', color: '#722ed1', icon: '🏖️' },
  OVERTIME: { value: 'overtime', label: '加班审批', color: '#faad14', icon: '⏰' },
  TRAVEL: { value: 'travel', label: '出差审批', color: '#13c2c2', icon: '✈️' },
  CONTRACT: { value: 'contract', label: '合同审批', color: '#eb2f96', icon: '📋' },
  PROJECT: { value: 'project', label: '项目审批', color: '#f5222d', icon: '🚀' },
  REIMBURSEMENT: { value: 'reimbursement', label: '报销审批', color: '#8c8c8c', icon: '💸' }
};

export const APPROVAL_STATUS = {
  PENDING: { value: 'pending', label: '待审批', color: '#faad14' },
  APPROVED: { value: 'approved', label: '已通过', color: '#52c41a' },
  REJECTED: { value: 'rejected', label: '已拒绝', color: '#ff4d4f' },
  IN_PROGRESS: { value: 'in_progress', label: '审批中', color: '#1890ff' },
  CANCELLED: { value: 'cancelled', label: '已取消', color: '#8c8c8c' },
  RETURNED: { value: 'returned', label: '已退回', color: '#722ed1' }
};

export const APPROVAL_PRIORITY = {
  URGENT: { value: 'urgent', label: '紧急', color: '#ff4d4f', weight: 4 },
  HIGH: { value: 'high', label: '高', color: '#fa8c16', weight: 3 },
  NORMAL: { value: 'normal', label: '普通', color: '#1890ff', weight: 2 },
  LOW: { value: 'low', label: '低', color: '#52c41a', weight: 1 }
};

export const APPROVAL_ROLES = {
  INITIATOR: { value: 'initiator', label: '发起人' },
  REVIEWER: { value: 'reviewer', label: '审批人' },
  APPROVER: { value: 'approver', label: '最终批准人' },
  CC: { value: 'cc', label: '抄送人' },
  ADMIN: { value: 'admin', label: '管理员' }
};

export const WORKFLOW_STEPS = {
  SUBMIT: { value: 'submit', label: '提交申请', color: '#1890ff' },
  REVIEW: { value: 'review', label: '审核', color: '#722ed1' },
  APPROVE: { value: 'approve', label: '批准', color: '#52c41a' },
  FINAL_APPROVE: { value: 'final_approve', label: '最终批准', color: '#13c2c2' },
  EXECUTE: { value: 'execute', label: '执行', color: '#faad14' },
  COMPLETE: { value: 'complete', label: '完成', color: '#8c8c8c' }
};

export const APPROVAL_RULES = {
  AMOUNT_BASED: { value: 'amount_based', label: '金额规则', description: '基于金额的审批流程' },
  ROLE_BASED: { value: 'role_based', label: '角色规则', description: '基于角色的审批流程' },
  DEPARTMENT_BASED: { value: 'department_based', label: '部门规则', description: '基于部门的审批流程' },
  PROJECT_BASED: { value: 'project_based', label: '项目规则', description: '基于项目的审批流程' },
  CUSTOM: { value: 'custom', label: '自定义规则', description: '自定义审批规则' }
};

export const NOTIFICATION_TYPES = {
  EMAIL: { value: 'email', label: '邮件通知', icon: '📧' },
  SMS: { value: 'sms', label: '短信通知', icon: '📱' },
  WECHAT: { value: 'wechat', label: '微信通知', icon: '💬' },
  SYSTEM: { value: 'system', label: '系统通知', icon: '🔔' },
  APP_PUSH: { value: 'app_push', label: 'APP推送', icon: '📲' }
};

export const ACTION_TYPES = {
  APPROVE: { value: 'approve', label: '通过', color: '#52c41a' },
  REJECT: { value: 'reject', label: '拒绝', color: '#ff4d4f' },
  RETURN: { value: 'return', label: '退回', color: '#722ed1' },
  FORWARD: { value: 'forward', label: '转发', color: '#1890ff' },
  CANCEL: { value: 'cancel', label: '取消', color: '#8c8c8c' },
  REVOKE: { value: 'revoke', label: '撤销', color: '#faad14' }
};

export const DOCUMENT_TYPES = {
  PURCHASE_ORDER: { value: 'purchase_order', label: '采购单' },
  INVOICE: { value: 'invoice', label: '发票' },
  RECEIPT: { value: 'receipt', label: '收据' },
  CONTRACT: { value: 'contract', label: '合同' },
  QUOTATION: { value: 'quotation', label: '报价单' },
  EXPENSE_REPORT: { value: 'expense_report', label: '费用报告' },
  TRAVEL_PLAN: { value: 'travel_plan', label: '出差计划' },
  LEAVE_APPLICATION: { value: 'leave_application', label: '请假申请' }
};

export const TABLE_CONFIG = {
  pagination: { pageSize: 10, showSizeChanger: true },
  scroll: { x: 1400, y: 500 },
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
  type: null,
  status: null,
  priority: null,
  dateRange: null,
  initiator: null,
  approver: null
};

export const BATCH_ACTIONS = {
  BATCH_APPROVE: 'batch_approve',
  BATCH_REJECT: 'batch_reject',
  BATCH_RETURN: 'batch_return',
  BATCH_FORWARD: 'batch_forward',
  BATCH_CANCEL: 'batch_cancel'
};

export const APPROVAL_LIMITS = {
  PURCHASE_LIMITS: {
    manager: 10000,
    director: 50000,
    vp: 100000,
    ceo: 500000
  },
  EXPENSE_LIMITS: {
    manager: 5000,
    director: 20000,
    vp: 50000,
    ceo: 100000
  },
  LEAVE_LIMITS: {
    annual: 15,
    sick: 10,
    personal: 5,
    maternity: 180
  }
};