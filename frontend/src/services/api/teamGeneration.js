import { api } from "./client.js";

export const teamGenerationApi = {
  // AI 生成团队
  generateTeam: (projectId) => api.post(`/team-generation/projects/${projectId}/generate-team`),
  
  // 保存方案
  saveTeamPlan: (projectId, teamData) =>
    api.post(`/team-generation/projects/${projectId}/save-team-plan`, teamData),
  
  // 获取方案详情
  getTeamPlan: (planId) => api.get(`/team-generation/team-plans/${planId}`),
  
  // 提交审批
  submitTeamPlan: (planId) => api.post(`/team-generation/team-plans/${planId}/submit`),
  
  // 审批方案
  approveTeamPlan: (planId, decision, comments) =>
    api.post(`/team-generation/team-plans/${planId}/approve`, { decision, comments }),
};
