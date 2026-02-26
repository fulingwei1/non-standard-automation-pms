/**
 * 智能缺料预警系统 API 客户端
 * Team 3 - Smart Shortage Alert System
 */

import api from "./client.js";

const BASE_PATH = "/shortage/smart";

/**
 * 1. 获取预警列表
 * GET /shortage/smart/alerts
 */
export const getAlerts = (params = {}) => {
  return api.get(`${BASE_PATH}/alerts`, { params });
};

/**
 * 2. 获取预警详情
 * GET /shortage/smart/alerts/{id}
 */
export const getAlertDetail = (id) => {
  return api.get(`${BASE_PATH}/alerts/${id}`);
};

/**
 * 3. 触发扫描
 * POST /shortage/smart/scan
 */
export const triggerScan = (data = {}) => {
  return api.post(`${BASE_PATH}/scan`, {
    project_id: data.project_id || null,
    material_id: data.material_id || null,
    days_ahead: data.days_ahead || 30,
  });
};

/**
 * 4. 获取AI推荐方案
 * GET /shortage/smart/alerts/{id}/solutions
 */
export const getAlertSolutions = (alertId) => {
  return api.get(`${BASE_PATH}/alerts/${alertId}/solutions`);
};

/**
 * 5. 标记预警解决
 * POST /shortage/smart/alerts/{id}/resolve
 */
export const resolveAlert = (alertId, data = {}) => {
  return api.post(`${BASE_PATH}/alerts/${alertId}/resolve`, data);
};

/**
 * 6. 获取需求预测
 * GET /shortage/smart/forecast/{material_id}
 */
export const getForecast = (materialId, params = {}) => {
  return api.get(`${BASE_PATH}/forecast/${materialId}`, {
    params: {
      forecast_horizon_days: params.forecast_horizon_days || 30,
      algorithm: params.algorithm || "EXP_SMOOTHING",
      historical_days: params.historical_days || 90,
      project_id: params.project_id || null,
    },
  });
};

/**
 * 7. 获取缺料趋势分析
 * GET /shortage/smart/analysis/trend
 */
export const getTrendAnalysis = (params = {}) => {
  return api.get(`${BASE_PATH}/analysis/trend`, { params });
};

/**
 * 8. 获取根因分析
 * GET /shortage/smart/analysis/root-cause
 */
export const getRootCauseAnalysis = (params = {}) => {
  return api.get(`${BASE_PATH}/analysis/root-cause`, { params });
};

/**
 * 9. 获取项目影响分析
 * GET /shortage/smart/impact/projects
 */
export const getProjectImpactAnalysis = (params = {}) => {
  return api.get(`${BASE_PATH}/impact/projects`, { params });
};

/**
 * 10. 订阅通知
 * POST /shortage/smart/notifications/subscribe
 */
export const subscribeNotifications = (data) => {
  return api.post(`${BASE_PATH}/notifications/subscribe`, data);
};

// 导出所有 API
export default {
  getAlerts,
  getAlertDetail,
  triggerScan,
  getAlertSolutions,
  resolveAlert,
  getForecast,
  getTrendAnalysis,
  getRootCauseAnalysis,
  getProjectImpactAnalysis,
  subscribeNotifications,
};
