/**
 * 项目交付排产计划 API
 */
import { api } from './index';

export const projectDeliveryApi = {
  async getSchedules(params = {}) { const q = new URLSearchParams(params).toString(); return await api.get(`/project-delivery/schedules?${q}`); },
  async getSchedule(id) { return await api.get(`/project-delivery/schedules/${id}`); },
  async createSchedule(data) { return await api.post('/project-delivery/schedules', data); },
  async confirmSchedule(id) { return await api.post(`/project-delivery/schedules/${id}/confirm`); },
  async getTasks(id) { return await api.get(`/project-delivery/schedules/${id}/tasks`); },
  async createTask(scheduleId, data) { return await api.post(`/project-delivery/schedules/${scheduleId}/tasks`, data); },
  async getLongCyclePurchases(id) { return await api.get(`/project-delivery/schedules/${id}/long-cycle-purchases`); },
  async createLongCyclePurchase(scheduleId, data) { return await api.post(`/project-delivery/schedules/${scheduleId}/long-cycle-purchases`, data); },
  async getMechanicalDesigns(id) { return await api.get(`/project-delivery/schedules/${id}/mechanical-designs`); },
  async createMechanicalDesign(scheduleId, data) { return await api.post(`/project-delivery/schedules/${scheduleId}/mechanical-designs`, data); },
  async getChangeLogs(id) { return await api.get(`/project-delivery/schedules/${id}/changes`); },
  async createChangeLog(scheduleId, data) { return await api.post(`/project-delivery/schedules/${scheduleId}/changes`, data); },
  async getGanttData(id) { return await api.get(`/project-delivery/schedules/${id}/gantt`); },
  async getConflicts(id) { return await api.get(`/project-delivery/schedules/${id}/conflicts`); },
};
