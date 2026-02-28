import { api } from "./client.js";

/**
 * 工作量分析 API
 *
 * 用于部门和全局工作负载分析
 */
export const workloadAnalyticsApi = {
  // ==================== 部门工作量 ====================

  /**
   * 获取部门工作量汇总
   * @param {number} deptId - 部门ID
   * @param {Object} params - { start_date, end_date }
   */
  departmentSummary: (deptId, params) =>
    api.get(`/departments/${deptId}/workload`, { params }),

  /**
   * 获取部门工作负载分布（用于可视化）
   * @param {number} deptId - 部门ID
   * @param {Object} params - { start_date, end_date, view: 'distribution' }
   */
  departmentDistribution: (deptId, params) =>
    api.get(`/departments/${deptId}/workload`, { params: { ...params, view: 'distribution' } }),

  // ==================== 全局分析 ====================

  /**
   * 获取全局工作量概览
   * @param {Object} params - { start_date, end_date }
   */
  overview: (params) => api.get("/analytics/workload/overview", { params }),

  /**
   * 获取资源瓶颈分析
   * @param {Object} params - { start_date, end_date }
   */
  bottlenecks: (params) =>
    api.get("/analytics/workload/bottlenecks", { params }),
};

/**
 * 技能矩阵 API
 *
 * 用于技能分析和人员搜索
 */
export const skillMatrixApi = {
  // ==================== 全局技能矩阵 ====================

  /**
   * 获取全局技能矩阵
   * @param {Object} params - { tag_type }
   */
  matrix: (params) => api.get("/analytics/skill-matrix", { params }),

  /**
   * 获取技能列表（带人数统计）
   * @param {Object} params - { tag_type }
   */
  skills: (params) => api.get("/analytics/skill-matrix/skills", { params }),

  /**
   * 获取特定技能的人员列表
   * @param {string} skillCode - 技能编码
   * @param {Object} params - { min_score }
   */
  skillEmployees: (skillCode, params) =>
    api.get(`/analytics/skill-matrix/skills/${skillCode}`, { params }),

  /**
   * 按技能+可用性搜索人员
   * @param {Object} params - { skills, min_score, department_id, available_from, available_to, min_availability }
   */
  search: (params) => api.get("/analytics/skill-matrix/search", { params }),

  /**
   * 获取技能缺口分析
   */
  gaps: () => api.get("/analytics/skill-matrix/gaps"),

  // ==================== 部门技能矩阵 ====================

  /**
   * 获取部门技能矩阵
   * @param {number} deptId - 部门ID
   */
  departmentMatrix: (deptId) =>
    api.get(`/departments/${deptId}/skill-matrix`),
};
