import { api } from "./client.js";

export const multiCurrencyApi = {
  /**
   * 获取汇率列表
   */
  getRates: () => api.get("/currency/rates"),

  /**
   * 更新汇率
   * @param {Object} data - { currency, rate, note? }
   */
  updateRate: (data) => api.post("/currency/rates", data),

  /**
   * 汇率转换
   * @param {Object} params - { from_currency, to_currency, amount }
   */
  convert: (params) => api.get("/currency/convert", { params }),

  /**
   * 获取汇率历史
   * @param {Object} params - { currency?, limit? }
   */
  getHistory: (params) => api.get("/currency/history", { params }),

  /**
   * 获取项目多币种汇总
   * @param {number} projectId
   */
  getProjectSummary: (projectId) => api.get(`/currency/project-summary/${projectId}`),
};
