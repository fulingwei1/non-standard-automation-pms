import { api } from "./client.js";

export const scheduleGenerationApi = {
  // 生成两种模式计划
  generateBothModes: (projectId) =>
    api.post(`/schedule-generation/projects/${projectId}/generate-both-modes`),
  
  // 生成单一模式
  generateSchedule: (projectId, mode = 'NORMAL') =>
    api.post(`/schedule-generation/projects/${projectId}/generate-schedule`, null, {
      params: { mode },
    }),
  
  // 保存计划
  saveSchedule: (projectId, scheduleData) =>
    api.post(`/schedule-generation/projects/${projectId}/save-schedule`, scheduleData),
  
  // 获取计划详情
  getSchedulePlan: (planId) =>
    api.get(`/schedule-generation/schedule-plans/${planId}`),
  
  // 调整任务
  updateTask: (taskId, taskData) =>
    api.put(`/schedule-generation/schedule-tasks/${taskId}`, taskData),
};
