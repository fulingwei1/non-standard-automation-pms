import { api } from "./client.js";

/**
 * 资源计划 API
 *
 * 用于项目阶段人员规划和分配管理
 */
export const resourcePlanApi = {
  // ==================== 资源计划 CRUD ====================

  /**
   * 获取项目资源计划列表
   * @param {number} projectId - 项目ID
   * @param {Object} params - 查询参数 { stage_code }
   */
  list: (projectId, params) =>
    api.get(`/projects/${projectId}/resource-plan/`, { params }),

  /**
   * 获取项目资源计划汇总（按阶段分组）
   * @param {number} projectId - 项目ID
   */
  summary: (projectId) =>
    api.get(`/projects/${projectId}/resource-plan/summary`),

  /**
   * 获取单个资源计划详情
   * @param {number} projectId - 项目ID
   * @param {number} planId - 资源计划ID
   */
  get: (projectId, planId) =>
    api.get(`/projects/${projectId}/resource-plan/${planId}`),

  /**
   * 创建资源计划
   * @param {number} projectId - 项目ID
   * @param {Object} data - 资源计划数据
   */
  create: (projectId, data) =>
    api.post(`/projects/${projectId}/resource-plan/`, data),

  /**
   * 更新资源计划
   * @param {number} projectId - 项目ID
   * @param {number} planId - 资源计划ID
   * @param {Object} data - 更新数据
   */
  update: (projectId, planId, data) =>
    api.put(`/projects/${projectId}/resource-plan/${planId}`, data),

  /**
   * 删除资源计划
   * @param {number} projectId - 项目ID
   * @param {number} planId - 资源计划ID
   */
  delete: (projectId, planId) =>
    api.delete(`/projects/${projectId}/resource-plan/${planId}`),

  // ==================== 人员分配 ====================

  /**
   * 分配员工到资源计划
   * @param {number} projectId - 项目ID
   * @param {number} planId - 资源计划ID
   * @param {Object} data - { employee_id, force }
   */
  assign: (projectId, planId, data) =>
    api.post(`/projects/${projectId}/resource-plan/${planId}/assign`, data),

  /**
   * 释放资源计划中的员工
   * @param {number} projectId - 项目ID
   * @param {number} planId - 资源计划ID
   */
  release: (projectId, planId) =>
    api.post(`/projects/${projectId}/resource-plan/${planId}/release`),

  /**
   * 检查分配冲突（预检查，不实际分配）
   * @param {number} projectId - 项目ID
   * @param {number} planId - 资源计划ID
   * @param {number} employeeId - 员工ID
   */
  checkConflict: (projectId, planId, employeeId) =>
    api.get(
      `/projects/${projectId}/resource-plan/${planId}/check-conflict/${employeeId}`
    ),
};

/**
 * 资源冲突 API
 *
 * 用于冲突检测和解决
 */
export const resourceConflictApi = {
  // ==================== 项目级冲突 ====================

  /**
   * 获取项目的所有资源冲突
   * @param {number} projectId - 项目ID
   * @param {Object} params - { include_resolved }
   */
  getProjectConflicts: (projectId, params) =>
    api.get(`/projects/${projectId}/resource-conflicts`, { params }),

  /**
   * 检查项目当前分配是否有冲突
   * @param {number} projectId - 项目ID
   */
  checkProjectConflicts: (projectId) =>
    api.get(`/projects/${projectId}/resource-conflicts/check`),

  // ==================== 全局冲突分析 ====================

  /**
   * 获取全局冲突列表
   * @param {Object} params - { severity, include_resolved, skip, limit }
   */
  list: (params) => api.get("/analytics/resource-conflicts", { params }),

  /**
   * 获取员工的冲突
   * @param {number} employeeId - 员工ID
   * @param {Object} params - { include_resolved }
   */
  getEmployeeConflicts: (employeeId, params) =>
    api.get(`/analytics/resource-conflicts/by-employee/${employeeId}`, {
      params,
    }),

  /**
   * 获取冲突汇总统计
   */
  summary: () => api.get("/analytics/resource-conflicts/summary"),

  /**
   * 标记冲突已解决
   * @param {number} conflictId - 冲突ID
   * @param {Object} data - { resolution_note }
   */
  resolve: (conflictId, data) =>
    api.post(`/analytics/resource-conflicts/${conflictId}/resolve`, data),
};
