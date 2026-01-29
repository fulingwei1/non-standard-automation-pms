import { api } from "./client.js";



export const authApi = {
  login: (formData) => {
    // FastAPI的OAuth2PasswordRequestForm需要application/x-www-form-urlencoded格式
    if (formData instanceof URLSearchParams) {
      return api.post("/auth/login", formData.toString(), {
        headers: {
          "Content-Type": "application/x-www-form-urlencoded",
        },
      });
    }
    // 如果已经是FormData，使用multipart/form-data
    return api.post("/auth/login", formData, {
      headers: {
        "Content-Type": "multipart/form-data",
      },
    });
  },
  me: () => api.get("/auth/me"),
  refresh: () => api.post("/auth/refresh"),
  logout: () => api.post("/auth/logout"),
  changePassword: (data) => api.put("/auth/password", data),
  /**
   * 获取当前用户的完整权限数据
   * @returns {Promise<{permissions: string[], menus: object[], dataScopes: object}>}
   */
  getPermissions: () => api.get("/auth/permissions"),
};

export const userApi = {
  list: (params) => api.get("/users/", { params }),
  get: (id) => api.get(`/users/${id}`),
  create: (data) => api.post("/users/", data),
  update: (id, data) => api.put(`/users/${id}`, data),
  delete: (id) => api.delete(`/users/${id}`),
  assignRoles: (id, roleIds) => api.put(`/users/${id}/roles`, roleIds),
  // 用户同步相关
  syncFromEmployees: (params = {}) =>
    api.post("/users/sync-from-employees", params),
  createFromEmployee: (employeeId, autoActivate = false) =>
    api.post(
      `/users/create-from-employee/${employeeId}?auto_activate=${autoActivate}`,
    ),
  toggleActive: (id, isActive) =>
    api.put(`/users/${id}/toggle-active`, { is_active: isActive }),
  resetPassword: (id) => api.put(`/users/${id}/reset-password`),
  batchToggleActive: (userIds, isActive) =>
    api.post("/users/batch-toggle-active", {
      user_ids: userIds,
      is_active: isActive,
    }),
};

export const roleApi = {
  list: (params) => api.get("/roles/", { params }),
  get: (id) => api.get(`/roles/${id}`),
  create: (data) => api.post("/roles/", data),
  update: (id, data) => api.put(`/roles/${id}`, data),
  delete: (id) => api.delete(`/roles/${id}`),
  assignPermissions: (id, permissionIds) =>
    api.put(`/roles/${id}/permissions`, { permission_ids: permissionIds }),
  permissions: (params) => api.get("/roles/permissions", { params }),
  // 菜单配置相关
  getNavGroups: (id) => api.get(`/roles/${id}/nav-groups`),
  updateNavGroups: (id, navGroups) =>
    api.put(`/roles/${id}/nav-groups`, navGroups),
  getMyNavGroups: () => api.get("/roles/my/nav-groups"),
  getAllConfig: () => api.get("/roles/config/all"),
  // 角色继承相关
  getDetail: (id) => api.get(`/roles/${id}/detail`),
  getInheritanceTree: () => api.get("/roles/inheritance-tree"),
  compare: (roleIds) => api.post("/roles/compare", roleIds),
  // 角色模板相关
  listTemplates: (params) => api.get("/roles/templates/", { params }),
  getTemplate: (id) => api.get(`/roles/templates/${id}`),
  createTemplate: (data) => api.post("/roles/templates/", data),
  updateTemplate: (id, data) => api.put(`/roles/templates/${id}`, data),
  deleteTemplate: (id) => api.delete(`/roles/templates/${id}`),
  createFromTemplate: (templateId, data) =>
    api.post(`/roles/templates/${templateId}/create-role`, null, { params: data }),
};

// 权限矩阵 API
export const permissionApi = {
  getMatrix: () => api.get("/permissions/matrix"),
  getDependencies: () => api.get("/permissions/dependencies"),
  getByRole: (roleId, includeInherited = true) =>
    api.get(`/permissions/by-role/${roleId}`, { params: { include_inherited: includeInherited } }),
};
