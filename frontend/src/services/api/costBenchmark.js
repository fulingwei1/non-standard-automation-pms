import { api } from "./client.js";

/**
 * 成本对标 API
 * 用于项目成本与历史项目的对标分析
 */
export const costBenchmarkApi = {
  // 查找相似项目
  findSimilarProjects: (projectId, params) =>
    api.get(`/projects/${projectId}/similar-projects`, { params }),

  // 创建对标分析
  createBenchmark: (projectId, data) =>
    api.post(`/projects/${projectId}/cost-benchmark`, data),

  // 获取项目的对标记录
  getBenchmarks: (projectId) =>
    api.get(`/projects/${projectId}/cost-benchmark`),

  // 生成对标报告
  generateReport: (projectId) =>
    api.get(`/projects/${projectId}/cost-benchmark/report`),

  // 获取劳动力成本明细
  getLaborCosts: (projectId) =>
    api.get(`/projects/${projectId}/labor-costs`),

  // 更新劳动力成本
  updateLaborCost: (projectId, data) =>
    api.post(`/projects/${projectId}/labor-costs`, data),

  // 获取成本分解
  getCostBreakdown: (projectId) =>
    api.get(`/projects/${projectId}/cost-breakdown`),
};
