/**
 * 售前技术方案 API
 *
 * 管理技术方案的 CRUD 操作，包括成本估算的保存
 */

import { api } from "./client";

export const presaleSolutionApi = {
  // 方案列表
  list: (params = {}) =>
    api.get("/presale/solutions", { params }),

  // 方案详情
  get: (id) =>
    api.get(`/presale/solutions/${id}`),

  // 创建方案
  create: (data) =>
    api.post("/presale/solutions", data),

  // 更新方案（包括成本估算）
  update: (id, data) =>
    api.put(`/presale/solutions/${id}`, data),

  // 获取方案成本明细
  getCost: (id) =>
    api.get(`/presale/solutions/${id}/cost`),

  // 提交方案审核
  submitReview: (id) =>
    api.put(`/presale/solutions/${id}/review`, {
      review_status: "REVIEW",
    }),

  // 审核方案
  review: (id, data) =>
    api.put(`/presale/solutions/${id}/review`, data),

  // 获取方案版本历史
  getVersions: (id) =>
    api.get(`/presale/solutions/${id}/versions`),

  // 保存成本估算
  // 这是一个便捷方法，实际调用 update
  saveCostEstimate: (id, costData) =>
    api.put(`/presale/solutions/${id}`, {
      estimated_cost: costData.estimated_cost,
      suggested_price: costData.suggested_price,
      cost_breakdown: costData.cost_breakdown,
    }),

  // 根据项目ID查找关联方案（一个项目可能有多个投标方案）
  findByProject: (projectId, params = {}) =>
    api.get("/presale/solutions", {
      params: { project_id: projectId, ...params },
    }),

  // 根据商机ID查找关联方案
  findByOpportunity: (opportunityId, params = {}) =>
    api.get("/presale/solutions", {
      params: { opportunity_id: opportunityId, ...params },
    }),

  // 根据工单ID查找关联方案
  findByTicket: (ticketId, params = {}) =>
    api.get("/presale/solutions", {
      params: { ticket_id: ticketId, ...params },
    }),
};
