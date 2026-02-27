import { api } from "./client.js";



export const orgApi = {
  departments: (params) => api.get("/org/departments", { params }),
  departmentTree: (params) => api.get("/org/departments/tree", { params }),
  createDepartment: (data) => api.post("/org/departments", data),
  updateDepartment: (id, data) => api.put(`/org/departments/${id}`, data),
  getDepartment: (id) => api.get(`/org/departments/${id}`),
  getDepartmentUsers: (id, params) =>
    api.get(`/org/departments/${id}/users`, { params }),
  employees: () => api.get("/org/employees"),
};

export const organizationApi = {
  importEmployees: (formData) =>
    api.post("/org/employees/import", formData, {
      headers: { "Content-Type": "multipart/form-data" },
      timeout: 60000,
    }),

  // ============================================================
  // 组织架构管理 API (新版)
  // ============================================================

  // 获取组织单元树
  getOrgTree: (params) => api.get("/org/units/tree", { params }),

  // 获取组织单元列表
  listOrgUnits: (params) => api.get("/org/units/", { params }),

  // 获取单个组织单元
  getOrgUnit: (id) => api.get(`/org/units/${id}`),

  // 创建组织单元
  createOrgUnit: (data) => api.post("/org/units/", data),

  // 更新组织单元
  updateOrgUnit: (id, data) => api.put(`/org/units/${id}`, data),

  // 删除组织单元
  deleteOrgUnit: (id) => api.delete(`/org/units/${id}`),

  // 获取组织单元下的员工
  getOrgUnitEmployees: (id, params) => api.get(`/org/units/${id}/employees`, { params }),

  // ============================================================
  // 岗位管理 API
  // ============================================================

  // 获取岗位列表
  listPositions: (params) => api.get("/org/positions/", { params }),

  // 获取单个岗位
  getPosition: (id) => api.get(`/org/positions/${id}`),

  // 创建岗位
  createPosition: (data) => api.post("/org/positions/", data),

  // 更新岗位
  updatePosition: (id, data) => api.put(`/org/positions/${id}`, data),

  // 删除岗位
  deletePosition: (id) => api.delete(`/org/positions/${id}`),

  // 获取岗位的默认角色
  getPositionRoles: (id) => api.get(`/org/positions/${id}/roles`),

  // 设置岗位的默认角色
  setPositionRoles: (id, roleIds) => api.put(`/org/positions/${id}/roles`, { role_ids: roleIds }),

  // ============================================================
  // 职级管理 API
  // ============================================================

  // 获取职级列表
  listJobLevels: (params) => api.get("/org/job-levels/", { params }),

  // 创建职级
  createJobLevel: (data) => api.post("/org/job-levels/", data),

  // 更新职级
  updateJobLevel: (id, data) => api.put(`/org/job-levels/${id}`, data),

  // ============================================================
  // 员工组织分配 API
  // ============================================================

  // 获取员工的组织分配
  getEmployeeAssignments: (employeeId) => api.get(`/org/${employeeId}/assignments`),

  // 创建员工组织分配
  createEmployeeAssignment: (data) => api.post("/org/assignments/", data),

  // 更新员工组织分配
  updateEmployeeAssignment: (id, data) => api.put(`/org/assignments/${id}`, data),

  // 删除员工组织分配
  deleteEmployeeAssignment: (id) => api.delete(`/org/assignments/${id}`),
};
