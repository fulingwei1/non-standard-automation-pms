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
};
