/**
 * ECN BOM API Client
 * ECN 工程变更→BOM 联动 API 调用
 */

import { api } from "./client.js";

const toEcnPriority = (value) => {
  const key = String(value || "").toLowerCase();
  return (
    {
      low: "LOW",
      medium: "NORMAL",
      normal: "NORMAL",
      high: "HIGH",
      urgent: "URGENT",
    }[key] || "NORMAL"
  );
};

const toEcnCreatePayload = (data = {}) => {
  const projectId = data.project_id || data.affected_projects?.[0];
  return {
    ecn_title: data.ecn_title || data.title,
    ecn_type: data.ecn_type || data.change_type,
    source_type: data.source_type || "MANUAL",
    source_no: data.source_no || data.ecn_no || undefined,
    source_id: data.source_id || undefined,
    project_id: Number(projectId),
    machine_id: data.machine_id || undefined,
    change_reason: data.change_reason || data.description || data.title,
    change_description: data.change_description || data.description || data.title,
    change_scope: data.change_scope || "PARTIAL",
    priority: toEcnPriority(data.priority),
    urgency: toEcnPriority(data.urgency || data.priority),
    cost_impact: data.cost_impact || 0,
    schedule_impact_days: data.schedule_impact_days || 0,
    attachments: data.attachments || undefined,
  };
};

const toEcnListParams = (params = {}) => ({
  status: params.status,
  ecn_type: params.ecn_type || params.change_type,
  project_id: params.project_id,
  machine_id: params.machine_id,
  keyword: params.keyword,
  page: params.page || 1,
  page_size: params.page_size || 20,
});

export const ecnBomApi = {
  /**
   * 创建 ECN 工程变更通知
   */
  create: (data) => api.post("/ecns", toEcnCreatePayload(data)),

  /**
   * 获取 ECN 列表
   */
  list: (params) => api.get("/ecns", { params: toEcnListParams(params) }),

  /**
   * 获取 ECN 详情
   */
  get: (id) => api.get(`/ecns/${id}`),

  /**
   * 更新 ECN
   */
  update: (id, data) =>
    api.put(`/ecns/${id}`, {
      ecn_title: data.ecn_title || data.title,
      change_reason: data.change_reason || data.description,
      change_description: data.change_description || data.description,
      change_scope: data.change_scope || "PARTIAL",
      priority: data.priority ? toEcnPriority(data.priority) : undefined,
      urgency: data.urgency ? toEcnPriority(data.urgency) : undefined,
      cost_impact: data.cost_impact,
      schedule_impact_days: data.schedule_impact_days,
    }),

  /**
   * 将 ECN 变更应用到 BOM
   */
  applyToBom: (id) => api.post(`/ecns/${id}/sync-to-bom`),

  /**
   * 获取 ECN 变更影响分析
   */
  getImpact: (id) => api.get(`/ecns/${id}/bom-impact-summary`),
};
