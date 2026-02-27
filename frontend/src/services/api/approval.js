/**
 * 统一审批服务
 *
 * 迁移到统一审批系统 API (/api/v1/approvals/)
 *
 * 旧的 ECN/Sales 审批 API 已被统一审批系统替代
 *
 * @deprecated 旧的审批 API 请迁移到此服务
 */

import { api } from "./client.js";

/**
 * 提交审批（统一接口）
 *
 * @param {Object} data - 审批数据
 * @param {string} data.entity_type - 实体类型：ECN/QUOTE/CONTRACT/INVOICE
 * @param {number} data.entity_id - 实体ID
 * @param {string} data.title - 审批标题
 * @param {string} data.summary - 审批摘要
 * @param {string} data.urgency - 紧急程度：NORMAL/URGENT/CRITICAL
 * @param {number[]} data.cc_user_ids - 抄送人ID列表
 *
 * @returns {Promise} 审批实例信息
 */
export const submitApproval = (data) => {
  return api.post("/approvals/submit", data);
};

/**
 * 通过审批
 *
 * @param {number} instance_id - 审批实例ID
 * @param {string} comment - 审批意见
 *
 * @returns {Promise} 审批结果
 */
export const approveApproval = (instance_id, comment) => {
  return api.post(`/approvals/tasks/${instance_id}/approve`, {
    decision: "APPROVE",
    comment: comment
  });
};

/**
 * 驳回审批
 *
 * @param {number} instance_id - 审批实例ID
 * @param {string} comment - 驳回理由
 *
 * @returns {Promise} 审批结果
 */
export const rejectApproval = (instance_id, comment) => {
  return api.post(`/approvals/tasks/${instance_id}/reject`, {
    decision: "REJECT",
    comment: comment
  });
};

/**
 * 委托审批（新功能）
 *
 * @param {number} instance_id - 审批实例ID
 * @param {number} delegate_to_id - 被委托人ID
 * @param {string} comment - 委托说明
 *
 * @returns {Promise} 委托结果
 */
export const delegateApproval = (instance_id, delegate_to_id, comment) => {
  return api.post(`/approvals/${instance_id}/delegate`, {
    decision: "DELEGATE",
    delegate_to_id: delegate_to_id,
    comment: comment
  });
};

/**
 * 撤回审批
 *
 * @param {number} instance_id - 审批实例ID
 * @param {string} comment - 撤回理由
 *
 * @returns {Promise} 撤回结果
 */
export const withdrawApproval = (instance_id, comment) => {
  return api.post(`/approvals/${instance_id}/withdraw`, {
    decision: "WITHDRAW",
    comment: comment
  });
};

/**
 * 查询审批历史
 *
 * @param {number} instance_id - 审批实例ID
 *
 * @returns {Promise} 审批历史记录
 */
export const getApprovalHistory = (instance_id) => {
  return api.get(`/approvals/${instance_id}/history`);
};

/**
 * 查询审批详情
 *
 * @param {number} instance_id - 审批实例ID
 *
 * @returns {Promise} 审批实例详情
 */
export const getApprovalDetail = (instance_id) => {
  return api.get(`/approvals/${instance_id}/detail`);
};

/**
 * 查询我的待审批任务
 *
 * @returns {Promise} 待审批任务列表
 */
export const getMyApprovalTasks = () => {
  return api.get("/approvals/my-tasks");
};

/**
 * 提交 ECN 审批
 *
 * @param {number} ecn_id - ECN ID
 * @param {string} title - 审批标题
 * @param {string} summary - 审批摘要
 * @param {string} urgency - 紧急程度
 * @param {number[]} cc_user_ids - 抄送人
 *
 * @returns {Promise} 审批实例
 */
export const submitEcnApproval = (
  ecn_id,
  title = "",
  summary = "",
  urgency = "NORMAL",
  cc_user_ids = []
) => {
  return submitApproval({
    entity_type: "ECN",
    entity_id: ecn_id,
    title: title || "ECN 审批",
    summary: summary,
    urgency: urgency,
    cc_user_ids: cc_user_ids
  });
};

/**
 * 提交报价审批
 *
 * @param {number} quote_id - 报价ID
 * @param {string} title - 审批标题
 * @param {string} summary - 审批摘要
 * @param {string} urgency - 紧急程度
 * @param {number[]} cc_user_ids - 抄送人
 *
 * @returns {Promise} 审批实例
 */
export const submitQuoteApproval = (
  quote_id,
  title = "",
  summary = "",
  urgency = "NORMAL",
  cc_user_ids = []
) => {
  return submitApproval({
    entity_type: "QUOTE",
    entity_id: quote_id,
    title: title || "报价审批",
    summary: summary,
    urgency: urgency,
    cc_user_ids: cc_user_ids
  });
};

/**
 * 提交合同审批
 *
 * @param {number} contract_id - 合同ID
 * @param {string} title - 审批标题
 * @param {string} summary - 审批摘要
 * @param {string} urgency - 紧急程度
 * @param {number[]} cc_user_ids - 抄送人
 *
 * @returns {Promise} 审批实例
 */
export const submitContractApproval = (
  contract_id,
  title = "",
  summary = "",
  urgency = "NORMAL",
  cc_user_ids = []
) => {
  return submitApproval({
    entity_type: "CONTRACT",
    entity_id: contract_id,
    title: title || "合同审批",
    summary: summary,
    urgency: urgency,
    cc_user_ids: cc_user_ids
  });
};

/**
 * 提交发票审批
 *
 * @param {number} invoice_id - 发票ID
 * @param {string} title - 审批标题
 * @param {string} summary - 审批摘要
 * @param {string} urgency - 紧急程度
 * @param {number[]} cc_user_ids - 抄送人
 *
 * @returns {Promise} 审批实例
 */
export const submitInvoiceApproval = (
  invoice_id,
  title = "",
  summary = "",
  urgency = "NORMAL",
  cc_user_ids = []
) => {
  return submitApproval({
    entity_type: "INVOICE",
    entity_id: invoice_id,
    title: title || "发票审批",
    summary: summary,
    urgency: urgency,
    cc_user_ids: cc_user_ids
  });
};

/**
 * 审批状态映射
 *
 * 旧状态 → 新状态
 *
 * SUBMITTED → PENDING
 * EVALUATING → IN_PROGRESS
 * EVALUATED → IN_PROGRESS
 * PENDING_APPROVAL → PENDING
 * APPROVED → APPROVED
 * REJECTED → REJECTED
 */
export const APPROVAL_STATUS = {
  PENDING: "PENDING",
  IN_PROGRESS: "IN_PROGRESS",
  APPROVED: "APPROVED",
  REJECTED: "REJECTED",
  WITHDRAWN: "WITHDRAWN",
  DELEGATED: "DELEGATED"
};

/**
 * 获取状态配置
 *
 * @param {string} status - 状态代码
 *
 * @returns {Object} 状态配置 {label, color, icon}
 */
export const getStatusConfig = (status) => {
  const statusConfigs = {
    [APPROVAL_STATUS.PENDING]: {
      label: "待审批",
      color: "orange",
      icon: "⏳"
    },
    [APPROVAL_STATUS.IN_PROGRESS]: {
      label: "审批中",
      color: "blue",
      icon: "🔄"
    },
    [APPROVAL_STATUS.APPROVED]: {
      label: "已通过",
      color: "green",
      icon: "✅"
    },
    [APPROVAL_STATUS.REJECTED]: {
      label: "已驳回",
      color: "red",
      icon: "❌"
    },
    [APPROVAL_STATUS.WITHDRAWN]: {
      label: "已撤回",
      color: "gray",
      icon: "↩️"
    },
    [APPROVAL_STATUS.DELEGATED]: {
      label: "已委托",
      color: "purple",
      icon: "👤"
    }
  };

  return statusConfigs[status] || {
    label: "未知",
    color: "gray",
    icon: "❓"
  };
};

/**
 * 计算审批进度百分比
 *
 * @param {number} current_level - 当前节点层级
 * @param {number} total_levels - 总节点数
 *
 * @returns {number} 进度百分比 (0-100)
 */
export const calculateProgress = (current_level, total_levels) => {
  if (!total_levels || total_levels === 0) {
    return 0;
  }
  return Math.round((current_level / total_levels) * 100);
};

/**
 * 统一审批 API
 */
export const unifiedApprovalApi = {
  // 基础操作
  submitApproval,
  approveApproval,
  rejectApproval,
  delegateApproval,
  withdrawApproval,
  getApprovalHistory,
  getApprovalDetail,
  getMyApprovalTasks,

  // 实体专用方法
  submitEcnApproval,
  submitQuoteApproval,
  submitContractApproval,
  submitInvoiceApproval,

  // 工具方法
  APPROVAL_STATUS,
  getStatusConfig,
  calculateProgress
};

export default unifiedApprovalApi;
