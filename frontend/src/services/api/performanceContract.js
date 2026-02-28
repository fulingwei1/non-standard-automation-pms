/**
 * 绩效合约管理 API 服务
 */
import { api } from "./client.js";

// ============================================
// 绩效合约管理
// ============================================
export const performanceContractApi = {
  // 创建合约
  create: (data) => api.post("/performance-contract/", null, { params: data }),

  // 列表查询
  list: (params) => api.get("/performance-contract/", { params }),

  // 详情（含指标条目）
  get: (id) => api.get(`/performance-contract/${id}`),

  // 更新合约
  update: (id, data) => api.put(`/performance-contract/${id}`, null, { params: data }),

  // 添加指标条目
  addItem: (contractId, data) =>
    api.post(`/performance-contract/${contractId}/items`, null, { params: data }),

  // 更新指标条目
  updateItem: (contractId, itemId, data) =>
    api.put(`/performance-contract/${contractId}/items/${itemId}`, null, { params: data }),

  // 删除指标条目
  deleteItem: (contractId, itemId) =>
    api.delete(`/performance-contract/${contractId}/items/${itemId}`),

  // 提交审批
  submit: (contractId) =>
    api.post(`/performance-contract/${contractId}/submit`),

  // 签署确认
  sign: (contractId, signAs) =>
    api.post(`/performance-contract/${contractId}/sign`, null, { params: { sign_as: signAs } }),

  // 批量评分
  evaluate: (contractId, evaluations) =>
    api.post(`/performance-contract/${contractId}/evaluate`, { evaluations }),

  // Dashboard 总览
  getDashboard: (params) => api.get("/performance-contract/dashboard", { params }),

  // 从战略生成合约条目
  generateFromStrategy: (contractId, strategyId, options = {}) =>
    api.post(`/performance-contract/${contractId}/generate-from-strategy`, null, {
      params: {
        strategy_id: strategyId,
        include_kpis: options.includeKpis !== false,
        include_annual_works: options.includeAnnualWorks !== false,
      },
    }),
};

// ============================================
// 便捷方法
// ============================================

/**
 * 获取合约类型标签
 */
export const getContractTypeLabel = (type) => {
  const labels = {
    L1: "公司级",
    L2: "部门级",
    L3: "个人级",
  };
  return labels[type] || type;
};

/**
 * 获取状态标签配置
 */
export const getStatusConfig = (status) => {
  const configs = {
    draft: { label: "草稿", color: "bg-slate-500/20 text-slate-400 border-slate-500/30" },
    pending_review: { label: "待审核", color: "bg-amber-500/20 text-amber-400 border-amber-500/30" },
    pending_sign: { label: "待签署", color: "bg-blue-500/20 text-blue-400 border-blue-500/30" },
    active: { label: "执行中", color: "bg-emerald-500/20 text-emerald-400 border-emerald-500/30" },
    completed: { label: "已完成", color: "bg-purple-500/20 text-purple-400 border-purple-500/30" },
    terminated: { label: "已终止", color: "bg-red-500/20 text-red-400 border-red-500/30" },
  };
  return configs[status] || { label: status, color: "bg-slate-500/20 text-slate-400" };
};

/**
 * 获取指标类别标签
 */
export const getCategoryLabel = (category) => {
  const labels = {
    业绩指标: "业绩",
    管理指标: "管理",
    能力指标: "能力",
    态度指标: "态度",
  };
  return labels[category] || category;
};

/**
 * 计算得分百分比
 */
export const calculateScorePercentage = (score, maxScore = 100) => {
  if (!score) return 0;
  return Math.min(100, Math.round((score / maxScore) * 100));
};

/**
 * 根据得分获取颜色
 */
export const getScoreColor = (score) => {
  if (!score) return "text-slate-400";
  if (score >= 90) return "text-emerald-400";
  if (score >= 80) return "text-blue-400";
  if (score >= 70) return "text-amber-400";
  if (score >= 60) return "text-orange-400";
  return "text-red-400";
};
