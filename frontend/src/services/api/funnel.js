/**
 * 销售漏斗状态机 API
 *
 * 提供阶段门验证、状态转换、滞留时间监控等功能
 */

import { api } from "./client.js";

export const funnelApi = {
  // ==================== 漏斗分析汇总 ====================

  /**
   * 获取销售漏斗汇总
   */
  getSummary: (params) => api.get("/sales/statistics/funnel", { params }),

  /**
   * 获取转化率分析
   */
  getConversionRates: (params) =>
    api.get("/sales/funnel/conversion-rates", { params }),

  /**
   * 获取瓶颈识别
   */
  getBottlenecks: (params) => api.get("/sales/funnel/bottlenecks", { params }),

  /**
   * 获取预测准确性
   */
  getPredictionAccuracy: (params) =>
    api.get("/sales/funnel/prediction-accuracy", { params }),

  /**
   * 获取漏斗健康度
   */
  getHealthDashboard: (params) =>
    api.get("/sales/funnel/health-dashboard", { params }),

  /**
   * 获取漏斗趋势
   */
  getTrends: (params) => api.get("/sales/funnel/trends", { params }),

  // ==================== 阶段门验证 ====================

  /**
   * 验证阶段门
   * @param {Object} data - { gate_type: 'G1'|'G2'|'G3'|'G4', entity_id: number, save_result: boolean }
   */
  validateGate: (data) => api.post("/sales/funnel/validate-gate", data),

  /**
   * 获取所有阶段门配置
   */
  getGateConfigs: () => api.get("/sales/funnel/gate-configs"),

  // ==================== 状态转换 ====================

  /**
   * 执行状态转换
   * @param {Object} data - { entity_type, entity_id, to_stage, reason, notes, skip_validation }
   */
  transition: (data) => api.post("/sales/funnel/transition", data),

  /**
   * 检查是否可以转换
   */
  canTransition: (params) => api.get("/sales/funnel/can-transition", { params }),

  /**
   * 线索转商机 (G1)
   */
  leadToOpportunity: (data) => api.post("/sales/funnel/lead-to-opportunity", data),

  /**
   * 商机转报价 (G2)
   */
  opportunityToQuote: (data) => api.post("/sales/funnel/opportunity-to-quote", data),

  /**
   * 报价转合同 (G3)
   */
  quoteToContract: (data) => api.post("/sales/funnel/quote-to-contract", data),

  // ==================== 漏斗阶段 ====================

  /**
   * 获取漏斗阶段配置
   */
  getStages: (entityType) =>
    api.get("/sales/funnel/stages", { params: { entity_type: entityType } }),

  /**
   * 获取状态转换日志
   */
  getTransitionLogs: (params) => api.get("/sales/funnel/transition-logs", { params }),

  // ==================== 滞留时间监控 ====================

  /**
   * 检查所有实体的滞留时间（通常由定时任务调用）
   */
  checkDwellTime: () => api.post("/sales/funnel/dwell-time/check"),

  /**
   * 获取滞留预警列表
   * @param {Object} params - { entity_type, severity, status, skip, limit }
   */
  getDwellTimeAlerts: (params) => api.get("/sales/funnel/dwell-time/alerts", { params }),

  /**
   * 确认预警
   */
  acknowledgeAlert: (alertId) =>
    api.post(`/sales/funnel/dwell-time/alerts/${alertId}/acknowledge`),

  /**
   * 解决预警
   */
  resolveAlert: (alertId, resolutionNote) =>
    api.post(`/sales/funnel/dwell-time/alerts/${alertId}/resolve`, null, {
      params: { resolution_note: resolutionNote },
    }),

  /**
   * 获取滞留时间统计
   */
  getStatistics: () => api.get("/sales/funnel/dwell-time/statistics"),
};

export default funnelApi;
