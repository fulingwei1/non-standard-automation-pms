/**
 * 紧急程度配置
 */
export const URGENCY_CONFIG = {
  NORMAL: { label: "普通", color: "bg-slate-500" },
  URGENT: { label: "紧急", color: "bg-orange-500" },
  CRITICAL: { label: "特急", color: "bg-red-500" },
};

/**
 * 状态配置
 */
export const STATUS_CONFIG = {
  PENDING: { label: "待审批", color: "bg-amber-500" },
  COMPLETED: { label: "已完成", color: "bg-emerald-500" },
  APPROVED: { label: "已通过", color: "bg-emerald-500" },
  REJECTED: { label: "已驳回", color: "bg-red-500" },
};

/**
 * 实体类型配置
 */
export const ENTITY_TYPE_CONFIG = {
  ECN: { label: "工程变更", color: "bg-purple-500" },
  QUOTE: { label: "报价", color: "bg-blue-500" },
  CONTRACT: { label: "合同", color: "bg-cyan-500" },
  INVOICE: { label: "发票", color: "bg-green-500" },
};
