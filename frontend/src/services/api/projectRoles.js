import { api } from "./client.js";



export const projectRoleApi = {
  // 角色类型管理
  types: {
    list: (params) => api.get("/project-roles/types", { params }),
    get: (id) => api.get(`/project-roles/types/${id}`),
    create: (data) => api.post("/project-roles/types", data),
    update: (id, data) => api.put(`/project-roles/types/${id}`, data),
    delete: (id) => api.delete(`/project-roles/types/${id}`),
  },

  // 项目角色配置
  configs: {
    get: (projectId) => api.get(`/project-roles/projects/${projectId}/configs`),
    batchUpdate: (projectId, data) =>
      api.put(`/project-roles/projects/${projectId}/configs`, data),
    init: (projectId) =>
      api.post(`/project-roles/projects/${projectId}/configs/init`),
  },

  // 项目负责人管理
  leads: {
    list: (projectId) => api.get(`/project-roles/projects/${projectId}/leads`),
    get: (projectId, memberId) =>
      api.get(`/project-roles/projects/${projectId}/leads/${memberId}`),
    create: (projectId, data) =>
      api.post(`/project-roles/projects/${projectId}/leads`, data),
    update: (projectId, memberId, data) =>
      api.put(`/project-roles/projects/${projectId}/leads/${memberId}`, data),
    delete: (projectId, memberId) =>
      api.delete(`/project-roles/projects/${projectId}/leads/${memberId}`),
  },

  // 团队成员管理
  team: {
    list: (projectId, leadMemberId) =>
      api.get(
        `/project-roles/projects/${projectId}/leads/${leadMemberId}/team`,
      ),
    add: (projectId, leadMemberId, data) =>
      api.post(
        `/project-roles/projects/${projectId}/leads/${leadMemberId}/team`,
        data,
      ),
    remove: (projectId, leadMemberId, memberId) =>
      api.delete(
        `/project-roles/projects/${projectId}/leads/${leadMemberId}/team/${memberId}`,
      ),
  },

  // 项目角色概览
  getOverview: (projectId) =>
    api.get(`/project-roles/projects/${projectId}/overview`),
};

export const projectRolesApi = {
  // 角色类型
  roleTypes: {
    list: (params) => api.get("/project-roles/types", { params }),
    create: (data) => api.post("/project-roles/types", data),
    get: (id) => api.get(`/project-roles/types/${id}`),
    update: (id, data) => api.put(`/project-roles/types/${id}`, data),
    delete: (id) => api.delete(`/project-roles/types/${id}`),
  },
  // 项目角色配置
  roleConfigs: {
    list: (projectId) =>
      api.get(`/project-roles/projects/${projectId}/role-configs`),
    init: (projectId) =>
      api.post(`/project-roles/projects/${projectId}/role-configs/init`),
    batchUpdate: (projectId, data) =>
      api.put(`/project-roles/projects/${projectId}/role-configs`, data),
  },
  // 项目负责人
  leads: {
    list: (projectId, includeTeam = false) =>
      api.get(`/project-roles/projects/${projectId}/leads`, {
        params: { include_team: includeTeam },
      }),
    create: (projectId, data) =>
      api.post(`/project-roles/projects/${projectId}/leads`, data),
    update: (projectId, memberId, data) =>
      api.put(`/project-roles/projects/${projectId}/leads/${memberId}`, data),
    delete: (projectId, memberId) =>
      api.delete(`/project-roles/projects/${projectId}/leads/${memberId}`),
  },
  // 团队成员
  teamMembers: {
    list: (projectId, leadId) =>
      api.get(`/project-roles/projects/${projectId}/leads/${leadId}/team`),
    create: (projectId, leadId, data) =>
      api.post(
        `/project-roles/projects/${projectId}/leads/${leadId}/team`,
        data,
      ),
    delete: (projectId, leadId, memberId) =>
      api.delete(
        `/project-roles/projects/${projectId}/leads/${leadId}/team/${memberId}`,
      ),
  },
  // 角色概览
  getRoleOverview: (projectId) =>
    api.get(`/project-roles/projects/${projectId}/role-overview`),
};
