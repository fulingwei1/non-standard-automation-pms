import { api } from "./client.js";

export const materialReadinessApi = {
  // 获取物料齐套列表
  list: (params) => api.get("/assembly/material-readiness", { params }),

  // 批量获取项目齐套率（用于项目健康监控视图）
  getBatchKitRate: (projectIds) =>
    api.post("/assembly/material-readiness/batch-kit-rate", {
      project_ids: projectIds,
    }),

  // 获取单个项目的齐套率详情
  getProjectKitRate: (projectId) =>
    api.get(`/assembly/material-readiness/project/${projectId}/kit-rate`),

  // 获取齐套率统计汇总
  getKitRateSummary: (params) =>
    api.get("/assembly/material-readiness/summary", { params }),
};
