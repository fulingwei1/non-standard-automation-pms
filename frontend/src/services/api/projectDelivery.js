/**
 * 项目交付排产计划 API
 */
import { api } from './index';

const unwrapApiResponse = (response) =>
  response?.formatted ?? response?.data?.data ?? response?.data ?? response;

export const projectDeliveryApi = {
  async getSchedules(params = {}) {
    return unwrapApiResponse(await api.get('/project-delivery/schedules', { params }));
  },
  async getSchedule(id) {
    return unwrapApiResponse(await api.get(`/project-delivery/schedules/${id}`));
  },
  async createSchedule(data) {
    return unwrapApiResponse(await api.post('/project-delivery/schedules', data));
  },
  async confirmSchedule(id) {
    return unwrapApiResponse(await api.post(`/project-delivery/schedules/${id}/confirm`));
  },
  async getTasks(id) {
    return unwrapApiResponse(await api.get(`/project-delivery/schedules/${id}/tasks`));
  },
  async createTask(scheduleId, data) {
    return unwrapApiResponse(await api.post(`/project-delivery/schedules/${scheduleId}/tasks`, data));
  },
  async getLongCyclePurchases(id) {
    return unwrapApiResponse(await api.get(`/project-delivery/schedules/${id}/long-cycle-purchases`));
  },
  async createLongCyclePurchase(scheduleId, data) {
    return unwrapApiResponse(await api.post(`/project-delivery/schedules/${scheduleId}/long-cycle-purchases`, data));
  },
  async getMechanicalDesigns(id) {
    return unwrapApiResponse(await api.get(`/project-delivery/schedules/${id}/mechanical-designs`));
  },
  async createMechanicalDesign(scheduleId, data) {
    return unwrapApiResponse(await api.post(`/project-delivery/schedules/${scheduleId}/mechanical-designs`, data));
  },
  async getChangeLogs(id) {
    return unwrapApiResponse(await api.get(`/project-delivery/schedules/${id}/changes`));
  },
  async createChangeLog(scheduleId, data) {
    return unwrapApiResponse(await api.post(`/project-delivery/schedules/${scheduleId}/changes`, data));
  },
  async getGanttData(id) {
    return unwrapApiResponse(await api.get(`/project-delivery/schedules/${id}/gantt`));
  },
  async getConflicts(id) {
    return unwrapApiResponse(await api.get(`/project-delivery/schedules/${id}/conflicts`));
  },
};
