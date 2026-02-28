/**
 * ECN BOM API Client
 * ECN 工程变更→BOM 联动 API 调用
 */

import { api } from "./client.js";

export const ecnBomApi = {
  /**
   * 创建 ECN 工程变更通知
   */
  create: (data) =>
    api.post("/ecn/", null, {
      params: {
        ecn_no: data.ecn_no,
        title: data.title,
        description: data.description,
        change_type: data.change_type,
        affected_projects: JSON.stringify(data.affected_projects),
        priority: data.priority,
        created_by: data.created_by,
      },
    }),

  /**
   * 获取 ECN 列表
   */
  list: (params) =>
    api.get("/ecn/", {
      params: {
        status: params?.status,
        change_type: params?.change_type,
        page: params?.page || 1,
        page_size: params?.page_size || 20,
      },
    }),

  /**
   * 获取 ECN 详情
   */
  get: (id) => api.get(`/ecn/${id}`),

  /**
   * 更新 ECN
   */
  update: (id, data) =>
    api.put(`/ecn/${id}`, null, {
      params: {
        title: data.title,
        description: data.description,
        change_type: data.change_type,
        affected_projects: data.affected_projects
          ? JSON.stringify(data.affected_projects)
          : undefined,
        status: data.status,
        priority: data.priority,
      },
    }),

  /**
   * 将 ECN 变更应用到 BOM
   */
  applyToBom: (id) => api.post(`/ecn/${id}/apply-to-bom`),

  /**
   * 获取 ECN 变更影响分析
   */
  getImpact: (id) => api.get(`/ecn/${id}/impact`),
};
