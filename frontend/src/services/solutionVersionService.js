/**
 * 方案版本和绑定验证服务
 * 支持成本-方案-报价三位一体绑定
 */
import api from './api';

class SolutionVersionService {
  // ============ 方案版本管理 ============

  /**
   * 创建方案版本
   * @param {number} solutionId - 方案ID
   * @param {Object} versionData - 版本数据
   */
  async createVersion(solutionId, versionData) {
    const response = await api.post(
      `/api/v1/sales/solutions/${solutionId}/versions`,
      versionData
    );
    return response.data;
  }

  /**
   * 获取版本历史
   * @param {number} solutionId - 方案ID
   */
  async getVersionHistory(solutionId) {
    const response = await api.get(
      `/api/v1/sales/solutions/${solutionId}/versions`
    );
    return response.data;
  }

  /**
   * 获取版本详情
   * @param {number} versionId - 版本ID
   */
  async getVersion(versionId) {
    const response = await api.get(
      `/api/v1/sales/solution-versions/${versionId}`
    );
    return response.data;
  }

  /**
   * 更新版本内容（仅 draft 状态可更新）
   * @param {number} versionId - 版本ID
   * @param {Object} updateData - 更新数据
   */
  async updateVersion(versionId, updateData) {
    const response = await api.put(
      `/api/v1/sales/solution-versions/${versionId}`,
      updateData
    );
    return response.data;
  }

  /**
   * 提交版本审核
   * @param {number} versionId - 版本ID
   */
  async submitForReview(versionId) {
    const response = await api.post(
      `/api/v1/sales/solution-versions/${versionId}/submit`
    );
    return response.data;
  }

  /**
   * 审批版本
   * @param {number} versionId - 版本ID
   * @param {string} action - 审批动作：approve / reject
   * @param {string} comments - 审批意见
   */
  async approveVersion(versionId, action, comments = '') {
    const response = await api.post(
      `/api/v1/sales/solution-versions/${versionId}/approve`,
      { action, comments }
    );
    return response.data;
  }

  /**
   * 对比两个版本
   * @param {number} versionId1 - 版本1 ID
   * @param {number} versionId2 - 版本2 ID
   */
  async compareVersions(versionId1, versionId2) {
    const response = await api.get('/api/v1/sales/solution-versions/compare', {
      params: { version_id_1: versionId1, version_id_2: versionId2 },
    });
    return response.data;
  }

  // ============ 绑定验证 ============

  /**
   * 验证报价绑定
   * @param {number} quoteVersionId - 报价版本ID
   */
  async validateBinding(quoteVersionId) {
    const response = await api.post(
      `/api/v1/sales/quote-versions/${quoteVersionId}/validate-binding`
    );
    return response.data;
  }

  /**
   * 同步成本到报价
   * @param {number} quoteVersionId - 报价版本ID
   */
  async syncCostToQuote(quoteVersionId) {
    const response = await api.post(
      `/api/v1/sales/quote-versions/${quoteVersionId}/sync-cost`
    );
    return response.data;
  }

  /**
   * 检查方案版本更新影响
   * @param {number} versionId - 方案版本ID
   */
  async checkUpdateImpact(versionId) {
    const response = await api.get(
      `/api/v1/sales/solution-versions/${versionId}/impact`
    );
    return response.data;
  }

  /**
   * 绑定方案和成本到报价
   * @param {number} quoteVersionId - 报价版本ID
   * @param {number} solutionVersionId - 方案版本ID
   * @param {number} costEstimationId - 成本估算ID
   */
  async bindQuoteVersion(quoteVersionId, solutionVersionId, costEstimationId) {
    const response = await api.post(
      `/api/v1/sales/quote-versions/${quoteVersionId}/bind`,
      null,
      {
        params: {
          solution_version_id: solutionVersionId,
          cost_estimation_id: costEstimationId,
        },
      }
    );
    return response.data;
  }
}

export const solutionVersionService = new SolutionVersionService();
