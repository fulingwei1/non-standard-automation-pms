/**
 * Quote Management Constants
 * 报价管理系统常量配置
 * 包含报价状态、优先级、类型、审批流程等配置
 */

import { cn, formatDate, formatDateTime, formatCurrency } from "../../lib/utils";

export { cn, formatDate, formatDateTime, formatCurrency };

// ==================== 报价状态配置 ====================
export const quoteStatusConfig = {
  DRAFT: {
    label: "草稿",
    value: "DRAFT",
    color: "text-slate-400 bg-slate-400/10 border-slate-400/30",
    bg: "bg-slate-500",
    icon: "FileText",
    order: 1,
    description: "报价草稿，尚未提交审批"
  },
  IN_REVIEW: {
    label: "审批中",
    value: "IN_REVIEW",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    bg: "bg-amber-500",
    icon: "Clock",
    order: 2,
    description: "报价正在审批流程中"
  },
  APPROVED: {
    label: "已批准",
    value: "APPROVED",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    bg: "bg-blue-500",
    icon: "CheckCircle2",
    order: 3,
    description: "报价已通过审批"
  },
  SENT: {
    label: "已发送",
    value: "SENT",
    color: "text-purple-400 bg-purple-400/10 border-purple-400/30",
    bg: "bg-purple-500",
    icon: "Send",
    order: 4,
    description: "报价已发送给客户"
  },
  EXPIRED: {
    label: "过期",
    value: "EXPIRED",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    bg: "bg-red-500",
    icon: "XCircle",
    order: 5,
    description: "报价已过期"
  },
  REJECTED: {
    label: "被拒",
    value: "REJECTED",
    color: "text-red-500 bg-red-500/10 border-red-500/30",
    bg: "bg-red-600",
    icon: "XCircle",
    order: 6,
    description: "报价被拒绝"
  },
  ACCEPTED: {
    label: "已接受",
    value: "ACCEPTED",
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    bg: "bg-emerald-500",
    icon: "CheckCircle2",
    order: 7,
    description: "报价已被客户接受"
  },
  CONVERTED: {
    label: "已转订单",
    value: "CONVERTED",
    color: "text-green-400 bg-green-400/10 border-green-400/30",
    bg: "bg-green-500",
    icon: "CheckCircle2",
    order: 8,
    description: "报价已转换为销售订单"
  }
};

// ==================== 报价优先级配置 ====================
export const quotePriorityConfig = {
  URGENT: {
    label: "紧急",
    value: "URGENT",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    level: 4,
    description: "需要立即处理的报价"
  },
  HIGH: {
    label: "高",
    value: "HIGH",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    level: 3,
    description: "高优先级报价"
  },
  MEDIUM: {
    label: "中",
    value: "MEDIUM",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    level: 2,
    description: "普通优先级报价"
  },
  LOW: {
    label: "低",
    value: "LOW",
    color: "text-slate-400 bg-slate-400/10 border-slate-400/30",
    level: 1,
    description: "低优先级报价"
  }
};

// ==================== 报价类型配置 ====================
export const quoteTypeConfig = {
  STANDARD: {
    label: "标准报价",
    value: "STANDARD",
    color: "text-blue-400 bg-blue-400/10 border-blue-400/30",
    icon: "FileText",
    description: "标准产品报价"
  },
  CUSTOM: {
    label: "定制报价",
    value: "CUSTOM",
    color: "text-purple-400 bg-purple-400/10 border-purple-400/30",
    icon: "Settings",
    description: "定制化产品报价"
  },
  SERVICE: {
    label: "服务报价",
    value: "SERVICE",
    color: "text-green-400 bg-green-400/10 border-green-400/30",
    icon: "Users",
    description: "服务类报价"
  },
  PROJECT: {
    label: "项目报价",
    value: "PROJECT",
    color: "text-orange-400 bg-orange-400/10 border-orange-400/30",
    icon: "Folder",
    description: "项目制报价"
  }
};

// ==================== 审批状态配置 ====================
export const approvalStatusConfig = {
  PENDING: {
    label: "待审批",
    value: "PENDING",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30",
    icon: "Clock"
  },
  APPROVED: {
    label: "已通过",
    value: "APPROVED",
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30",
    icon: "CheckCircle2"
  },
  REJECTED: {
    label: "已拒绝",
    value: "REJECTED",
    color: "text-red-400 bg-red-400/10 border-red-400/30",
    icon: "XCircle"
  }
};

// ==================== 版本状态配置 ====================
export const versionStatusConfig = {
  ACTIVE: {
    label: "当前版本",
    value: "ACTIVE",
    color: "text-emerald-400 bg-emerald-400/10 border-emerald-400/30"
  },
  SUPERSEDED: {
    label: "已废弃",
    value: "SUPERSEDED",
    color: "text-slate-400 bg-slate-400/10 border-slate-400/30"
  },
  DRAFT: {
    label: "草稿",
    value: "DRAFT",
    color: "text-amber-400 bg-amber-400/10 border-amber-400/30"
  }
};

// ==================== 付款条件配置 ====================
export const paymentTermsConfig = {
  PREPAID: {
    label: "预付款",
    value: "PREPAID",
    description: "发货前全额付款"
  },
  NET_30: {
    label: "30天账期",
    value: "NET_30",
    description: "收货后30天内付款"
  },
  NET_60: {
    label: "60天账期",
    value: "NET_60",
    description: "收货后60天内付款"
  },
  NET_90: {
    label: "90天账期",
    value: "NET_90",
    description: "收货后90天内付款"
  },
  MILESTONE: {
    label: "里程碑付款",
    value: "MILESTONE",
    description: "按项目里程碑付款"
  }
};

// ==================== 交付条件配置 ====================
export const deliveryTermsConfig = {
  EXW: {
    label: "工厂交货",
    value: "EXW",
    description: "在卖方工厂交货"
  },
  FOB: {
    label: "船上交货",
    value: "FOB",
    description: "在指定港口船上交货"
  },
  CIF: {
    label: "成本加保险运费",
    value: "CIF",
    description: "成本、保险费加运费"
  },
  DDP: {
    label: "完税后交货",
    value: "DDP",
    description: "在指定目的地完税后交货"
  }
};

// ==================== 默认统计数据配置 ====================
export const DEFAULT_QUOTE_STATS = {
  total: 0,
  draft: 0,
  inReview: 0,
  approved: 0,
  sent: 0,
  expired: 0,
  rejected: 0,
  accepted: 0,
  converted: 0,
  totalAmount: 0,
  avgAmount: 0,
  avgMargin: 0,
  conversionRate: 0,
  thisMonth: 0,
  lastMonth: 0,
  growth: 0
};

// ==================== 排序选项配置 ====================
export const QUOTE_SORT_OPTIONS = [
  { value: "created_desc", label: "创建时间（最新）" },
  { value: "created_asc", label: "创建时间（最早）" },
  { value: "updated_desc", label: "更新时间（最新）" },
  { value: "updated_asc", label: "更新时间（最早）" },
  { value: "amount_desc", label: "报价金额（高到低）" },
  { value: "amount_asc", label: "报价金额（低到高）" },
  { value: "valid_until_asc", label: "有效期（即将到期）" },
  { value: "valid_until_desc", label: "有效期（最远到期）" },
  { value: "title_asc", label: "标题（A-Z）" },
  { value: "title_desc", label: "标题（Z-A）" }
];

// ==================== 视图模式配置 ====================
export const QUOTE_VIEW_MODES = [
  {
    value: "list",
    label: "列表视图",
    icon: "List",
    description: "传统的表格列表形式展示"
  },
  {
    value: "card",
    label: "卡片视图",
    icon: "Grid",
    description: "卡片形式展示报价信息"
  }
];

// ==================== 有效期配置 ====================
export const VALIDITY_PERIODS = [
  { value: 7, label: "7天" },
  { value: 15, label: "15天" },
  { value: 30, label: "30天" },
  { value: 60, label: "60天" },
  { value: 90, label: "90天" },
  { value: 180, label: "180天" },
  { value: 365, label: "1年" }
];

// ==================== 工具函数 ====================

// 获取报价状态配置
export const getQuoteStatusConfig = (status) => {
  return quoteStatusConfig[status] || quoteStatusConfig.DRAFT;
};

// 获取报价优先级配置
export const getQuotePriorityConfig = (priority) => {
  return quotePriorityConfig[priority] || quotePriorityConfig.MEDIUM;
};

// 获取报价类型配置
export const getQuoteTypeConfig = (type) => {
  return quoteTypeConfig[type] || quoteTypeConfig.STANDARD;
};

// 获取审批状态配置
export const getApprovalStatusConfig = (status) => {
  return approvalStatusConfig[status] || approvalStatusConfig.PENDING;
};

// 获取版本状态配置
export const getVersionStatusConfig = (status) => {
  return versionStatusConfig[status] || versionStatusConfig.DRAFT;
};

// 检查报价是否过期
export const isQuoteExpired = (quote) => {
  if (!quote.valid_until || ['ACCEPTED', 'CONVERTED', 'REJECTED'].includes(quote.status)) {
    return false;
  }
  return new Date(quote.valid_until) < new Date();
};

// 检查报价是否即将过期（7天内）
export const isQuoteExpiringSoon = (quote) => {
  if (!quote.valid_until || ['ACCEPTED', 'CONVERTED', 'REJECTED'].includes(quote.status)) {
    return false;
  }
  const now = new Date();
  const expiryDate = new Date(quote.valid_until);
  const daysUntilExpiry = Math.ceil((expiryDate - now) / (1000 * 60 * 60 * 24));
  return daysUntilExpiry > 0 && daysUntilExpiry <= 7;
};

// 计算毛利润
export const calculateGrossMargin = (totalPrice, costTotal) => {
  if (!totalPrice || !costTotal || totalPrice <= 0) {
    return 0;
  }
  return ((parseFloat(totalPrice) - parseFloat(costTotal)) / parseFloat(totalPrice) * 100).toFixed(2);
};

// 格式化报价编号
export const formatQuoteNumber = (id, prefix = "QT") => {
  if (!id) return "";
  const paddedId = String(id).padStart(6, '0');
  return `${prefix}-${paddedId}`;
};

// 计算转换率
export const calculateConversionRate = (converted, sent) => {
  if (!sent || sent === 0) return 0;
  return ((converted / sent) * 100).toFixed(1);
};

// 获取下一个版本号
export const getNextVersionNumber = (currentVersion) => {
  if (!currentVersion) return "V1";
  
  // 处理 V1, V2 等格式
  const match = currentVersion.match(/^V(\d+)$/);
  if (match) {
    const versionNumber = parseInt(match[1]) + 1;
    return `V${versionNumber}`;
  }
  
  // 处理其他格式，递增数字部分
  const numberMatch = currentVersion.match(/(\d+)$/);
  if (numberMatch) {
    const prefix = currentVersion.slice(0, -numberMatch[1].length);
    const versionNumber = parseInt(numberMatch[1]) + 1;
    return `${prefix}${versionNumber}`;
  }
  
  return "V2";
};

// 获取状态操作按钮
export const getQuoteStatusActions = (currentStatus) => {
  const actions = [];
  
  switch (currentStatus) {
    case 'DRAFT':
      actions.push(
        { label: '提交审批', action: 'submit', color: 'bg-blue-600' },
        { label: '编辑', action: 'edit', color: 'bg-slate-600' },
        { label: '删除', action: 'delete', color: 'bg-red-600' }
      );
      break;
    case 'IN_REVIEW':
      actions.push(
        { label: '批准', action: 'approve', color: 'bg-emerald-600' },
        { label: '拒绝', action: 'reject', color: 'bg-red-600' }
      );
      break;
    case 'APPROVED':
      actions.push(
        { label: '发送客户', action: 'send', color: 'bg-purple-600' },
        { label: '编辑', action: 'edit', color: 'bg-slate-600' }
      );
      break;
    case 'SENT':
      actions.push(
        { label: '标记接受', action: 'accept', color: 'bg-emerald-600' },
        { label: '标记过期', action: 'expire', color: 'bg-orange-600' },
        { label: '发送提醒', action: 'remind', color: 'bg-blue-600' }
      );
      break;
    case 'ACCEPTED':
      actions.push(
        { label: '转订单', action: 'convert', color: 'bg-green-600' }
      );
      break;
  }
  
  return actions;
};

// 验证报价数据
export const validateQuoteData = (data) => {
  const errors = [];
  
  if (!data.title || data.title.trim() === '') {
    errors.push('报价标题不能为空');
  }
  
  if (!data.customer_id) {
    errors.push('客户必须选择');
  }
  
  if (!data.opportunity_id) {
    errors.push('商机必须选择');
  }
  
  if (!data.valid_until) {
    errors.push('有效期必须设置');
  } else if (new Date(data.valid_until) <= new Date()) {
    errors.push('有效期必须是未来时间');
  }
  
  if (data.version) {
    if (!data.version.total_price || parseFloat(data.version.total_price) <= 0) {
      errors.push('报价总金额必须大于0');
    }
    
    if (!data.version.lead_time_days || parseInt(data.version.lead_time_days) <= 0) {
      errors.push('交货期必须大于0天');
    }
  }
  
  if (data.version?.items && data.version.items.length === 0) {
    errors.push('报价项目不能为空');
  }
  
  return errors;
};

// 导出配置对象
export const quoteConstants = {
  quoteStatusConfig,
  quotePriorityConfig,
  quoteTypeConfig,
  approvalStatusConfig,
  versionStatusConfig,
  paymentTermsConfig,
  deliveryTermsConfig,
  DEFAULT_QUOTE_STATS,
  QUOTE_SORT_OPTIONS,
  QUOTE_VIEW_MODES,
  VALIDITY_PERIODS
};
