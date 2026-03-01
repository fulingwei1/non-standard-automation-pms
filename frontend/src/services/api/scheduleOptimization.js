import { api } from "./client.js";

export const scheduleOptimizationApi = {
  // 优化潜力分析
  analyzeOptimization: (projectId) =>
    api.get(`/schedule-optimization/projects/${projectId}/optimization-analysis`),
  
  // 自动生成 BOM
  autoGenerateBom: (projectId) =>
    api.post(`/schedule-optimization/projects/${projectId}/auto-generate-bom`),
  
  // 自动创建采购
  autoCreatePurchase: (projectId) =>
    api.post(`/schedule-optimization/projects/${projectId}/auto-create-purchase`),
};
