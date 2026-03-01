import api from "./client.js";

export const engineerApi = {
  // 获取工程师能力模型
  getCapacity: (engineerId) =>
    api.get(`/engineer-scheduling/engineers/${engineerId}/capacity`),

  // 更新能力模型
  updateCapacity: (engineerId) =>
    api.post(`/engineer-scheduling/engineers/${engineerId}/capacity/update`),

  // 分析工作量
  analyzeWorkload: (engineerId, params) =>
    api.get(`/engineer-scheduling/engineers/${engineerId}/workload`, { params }),

  // 检测冲突
  detectConflicts: (engineerId, taskData) =>
    api.post(`/engineer-scheduling/engineers/${engineerId}/conflict-detect`, taskData),

  // 生成预警
  generateWarnings: (params) =>
    api.post("/engineer-scheduling/warnings/generate", null, { params }),

  // 获取排产报告
  getSchedulingReport: (projectId) =>
    api.get(`/engineer-scheduling/projects/${projectId}/scheduling-report`),

  // AI 能力评估
  getAiCapability: (engineerId) =>
    api.get(`/engineer-scheduling/engineers/${engineerId}/ai-capability`),
  updateAiCapability: (engineerId) =>
    api.post(`/engineer-scheduling/engineers/${engineerId}/ai-capability/update`),

  // 核心能力评估
  getCoreCapabilities: (engineerId) =>
    api.get(`/engineer-scheduling/engineers/${engineerId}/core-capabilities`),
  updateCoreCapabilities: (engineerId) =>
    api.post(`/engineer-scheduling/engineers/${engineerId}/core-capabilities/update`),
};
