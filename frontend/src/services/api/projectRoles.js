import { api } from "./client.js";



export const projectRoleApi = {
  // 项目角色配置
  configs: {
    get: (projectId) => api.get(`/projects/${projectId}/roles/configs`),
    batchUpdate: (projectId, data) =>
      api.put(`/projects/${projectId}/roles/configs`, data),
    init: (projectId) =>
      api.post(`/projects/${projectId}/roles/configs/init`),
  },

  // 项目负责人管理
  leads: {
    list: (projectId, includeTeam = false) =>
      api.get(`/projects/${projectId}/roles/leads`, {
        params: { include_team: includeTeam },
      }),
    get: (projectId, memberId) =>
      api.get(`/projects/${projectId}/roles/leads/${memberId}`),
    create: (projectId, data) =>
      api.post(`/projects/${projectId}/roles/leads`, data),
    update: (projectId, memberId, data) =>
      api.put(`/projects/${projectId}/roles/leads/${memberId}`, data),
    delete: (projectId, memberId) =>
      api.delete(`/projects/${projectId}/roles/leads/${memberId}`),
  },

  // 团队成员管理
  team: {
    list: (projectId, leadMemberId) =>
      api.get(
        `/projects/${projectId}/roles/leads/${leadMemberId}/team`,
      ),
    add: (projectId, leadMemberId, data) =>
      api.post(
        `/projects/${projectId}/roles/leads/${leadMemberId}/team`,
        data,
      ),
    remove: (projectId, leadMemberId, memberId) =>
      api.delete(
        `/projects/${projectId}/roles/leads/${leadMemberId}/team/${memberId}`,
      ),
  },

  // 项目角色概览
  getOverview: (projectId) =>
    api.get(`/projects/${projectId}/roles/overview`),
};

export const projectRolesApi = {
  // 项目角色配置
  roleConfigs: {
    list: (projectId) => api.get(`/projects/${projectId}/roles/configs`),
    init: (projectId) =>
      api.post(`/projects/${projectId}/roles/configs/init`),
    batchUpdate: (projectId, data) =>
      api.put(`/projects/${projectId}/roles/configs`, data),
  },
  // 项目负责人
  leads: {
    list: (projectId, includeTeam = false) =>
      api.get(`/projects/${projectId}/roles/leads`, {
        params: { include_team: includeTeam },
      }),
    create: (projectId, data) =>
      api.post(`/projects/${projectId}/roles/leads`, data),
    update: (projectId, memberId, data) =>
      api.put(`/projects/${projectId}/roles/leads/${memberId}`, data),
    delete: (projectId, memberId) =>
      api.delete(`/projects/${projectId}/roles/leads/${memberId}`),
  },
  // 团队成员
  teamMembers: {
    list: (projectId, leadId) =>
      api.get(`/projects/${projectId}/roles/leads/${leadId}/team`),
    create: (projectId, leadId, data) =>
      api.post(
        `/projects/${projectId}/roles/leads/${leadId}/team`,
        data,
      ),
    delete: (projectId, leadId, memberId) =>
      api.delete(
        `/projects/${projectId}/roles/leads/${leadId}/team/${memberId}`,
      ),
  },
  // 角色概览
  getRoleOverview: (projectId) =>
    api.get(`/projects/${projectId}/roles/overview`),
};
