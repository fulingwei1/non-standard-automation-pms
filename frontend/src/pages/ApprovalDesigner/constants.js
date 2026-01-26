/**
 * 审批流程设计器常量定义
 */

// 节点类型配置
export const NODE_TYPES = {
  START: {
    type: 'START',
    label: '开始',
    color: '#52c41a',
    icon: 'Play',
    description: '流程开始节点',
    maxCount: 1,
  },
  END: {
    type: 'END',
    label: '结束',
    color: '#8c8c8c',
    icon: 'Square',
    description: '流程结束节点',
    maxCount: 1,
  },
  APPROVAL: {
    type: 'APPROVAL',
    label: '审批',
    color: '#1677ff',
    icon: 'UserCheck',
    description: '审批节点，需要指定审批人',
  },
  CC: {
    type: 'CC',
    label: '抄送',
    color: '#722ed1',
    icon: 'Copy',
    description: '抄送节点，通知指定人员',
  },
  CONDITION: {
    type: 'CONDITION',
    label: '条件',
    color: '#fa8c16',
    icon: 'GitBranch',
    description: '条件分支节点',
  },
  PARALLEL: {
    type: 'PARALLEL',
    label: '并行',
    color: '#13c2c2',
    icon: 'Split',
    description: '并行网关，同时执行多个分支',
  },
};

// 审批模式
export const APPROVAL_MODES = {
  SINGLE: { value: 'SINGLE', label: '单人审批', description: '任意一人审批即可' },
  OR_SIGN: { value: 'OR_SIGN', label: '或签', description: '任一审批人通过即可' },
  AND_SIGN: { value: 'AND_SIGN', label: '会签', description: '所有审批人都需通过' },
  SEQUENTIAL: { value: 'SEQUENTIAL', label: '依次审批', description: '按顺序逐一审批' },
};

// 审批人类型
export const APPROVER_TYPES = {
  FIXED_USER: { value: 'FIXED_USER', label: '指定用户', icon: 'User' },
  ROLE: { value: 'ROLE', label: '指定角色', icon: 'Users' },
  DEPARTMENT_HEAD: { value: 'DEPARTMENT_HEAD', label: '部门主管', icon: 'UserCog' },
  DIRECT_MANAGER: { value: 'DIRECT_MANAGER', label: '直属上级', icon: 'ChevronUp' },
  FORM_FIELD: { value: 'FORM_FIELD', label: '表单字段', icon: 'FileText' },
  MULTI_DEPT: { value: 'MULTI_DEPT', label: '多部门', icon: 'Building' },
  DYNAMIC: { value: 'DYNAMIC', label: '动态计算', icon: 'Settings' },
};

// 条件操作符
export const CONDITION_OPERATORS = {
  EQUALS: { value: '==', label: '等于' },
  NOT_EQUALS: { value: '!=', label: '不等于' },
  GREATER: { value: '>', label: '大于' },
  GREATER_EQUALS: { value: '>=', label: '大于等于' },
  LESS: { value: '<', label: '小于' },
  LESS_EQUALS: { value: '<=', label: '小于等于' },
  IN: { value: 'in', label: '在...中' },
  NOT_IN: { value: 'not_in', label: '不在...中' },
  BETWEEN: { value: 'between', label: '介于' },
  CONTAINS: { value: 'contains', label: '包含' },
  IS_NULL: { value: 'is_null', label: '为空' },
};

// 超时操作
export const TIMEOUT_ACTIONS = {
  REMIND: { value: 'REMIND', label: '发送提醒', color: '#faad14' },
  AUTO_PASS: { value: 'AUTO_PASS', label: '自动通过', color: '#52c41a' },
  AUTO_REJECT: { value: 'AUTO_REJECT', label: '自动驳回', color: '#ff4d4f' },
  ESCALATE: { value: 'ESCALATE', label: '上报上级', color: '#1677ff' },
};

// 驳回目标
export const REJECT_TARGETS = {
  START: { value: 'START', label: '发起人' },
  PREV: { value: 'PREV', label: '上一节点' },
  SPECIFIC: { value: 'SPECIFIC', label: '指定节点' },
};

// 紧急程度
export const URGENCY_LEVELS = {
  NORMAL: { value: 'NORMAL', label: '普通', color: '#8c8c8c' },
  URGENT: { value: 'URGENT', label: '紧急', color: '#fa8c16' },
  CRITICAL: { value: 'CRITICAL', label: '特急', color: '#ff4d4f' },
};

// 模板分类
export const TEMPLATE_CATEGORIES = {
  HR: { value: 'HR', label: '人事行政', icon: 'Users', color: '#722ed1' },
  FINANCE: { value: 'FINANCE', label: '财务相关', icon: 'DollarSign', color: '#52c41a' },
  PROJECT: { value: 'PROJECT', label: '项目管理', icon: 'Briefcase', color: '#1677ff' },
  BUSINESS: { value: 'BUSINESS', label: '业务流程', icon: 'Building2', color: '#fa8c16' },
  PURCHASE: { value: 'PURCHASE', label: '采购审批', icon: 'ShoppingCart', color: '#13c2c2' },
  OTHER: { value: 'OTHER', label: '其他', icon: 'MoreHorizontal', color: '#8c8c8c' },
};

// 内置模板
export const BUILTIN_TEMPLATES = [
  { code: 'QUOTE_APPROVAL', name: '报价审批', category: 'BUSINESS' },
  { code: 'CONTRACT_APPROVAL', name: '合同审批', category: 'BUSINESS' },
  { code: 'INVOICE_APPROVAL', name: '发票审批', category: 'FINANCE' },
  { code: 'ECN_APPROVAL', name: 'ECN审批', category: 'PROJECT' },
  { code: 'PROJECT_APPROVAL', name: '项目审批', category: 'PROJECT' },
  { code: 'LEAVE_REQUEST', name: '请假申请', category: 'HR' },
  { code: 'PURCHASE_APPROVAL', name: '采购审批', category: 'PURCHASE' },
  { code: 'TIMESHEET_APPROVAL', name: '工时审批', category: 'HR' },
];

// 画布配置
export const CANVAS_CONFIG = {
  gridSize: 20,
  nodeWidth: 200,
  nodeHeight: 80,
  connectionOffset: 40,
  minZoom: 0.5,
  maxZoom: 2,
  defaultZoom: 1,
};
