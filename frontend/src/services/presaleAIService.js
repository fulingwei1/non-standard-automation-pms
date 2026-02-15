/**
 * 售前AI服务
 * Team 10: 售前AI系统集成与前端UI
 */
import api from './api';

class PresaleAIService {
  // ============ 仪表盘统计 ============

  /**
   * 获取AI仪表盘统计数据
   * @param {number} days - 统计天数
   */
  async getDashboardStats(days = 30) {
    const response = await api.get('/api/v1/presale/ai/dashboard/stats', {
      params: { days },
    });
    return response.data;
  }

  // ============ 使用统计 ============

  /**
   * 获取AI使用统计
   * @param {Object} params - 查询参数
   */
  async getUsageStats(params = {}) {
    const response = await api.get('/api/v1/presale/ai/usage-stats', {
      params,
    });
    return response.data;
  }

  // ============ 反馈管理 ============

  /**
   * 提交AI反馈
   * @param {Object} feedbackData - 反馈数据
   */
  async submitFeedback(feedbackData) {
    const response = await api.post('/api/v1/presale/ai/feedback', feedbackData);
    return response.data;
  }

  /**
   * 获取指定AI功能的反馈
   * @param {string} aiFunction - AI功能名称
   * @param {Object} params - 查询参数
   */
  async getFeedbackByFunction(aiFunction, params = {}) {
    const response = await api.get(`/api/v1/presale/ai/feedback/${aiFunction}`, {
      params,
    });
    return response.data;
  }

  // ============ 工作流管理 ============

  /**
   * 启动AI工作流
   * @param {number} ticketId - 工单ID
   * @param {Object} initialData - 初始数据
   * @param {boolean} autoRun - 是否自动运行
   */
  async startWorkflow(ticketId, initialData = {}, autoRun = true) {
    const response = await api.post('/api/v1/presale/ai/workflow/start', {
      presale_ticket_id: ticketId,
      initial_data: initialData,
      auto_run: autoRun,
    });
    return response.data;
  }

  /**
   * 获取工作流状态
   * @param {number} ticketId - 工单ID
   */
  async getWorkflowStatus(ticketId) {
    const response = await api.get(
      `/api/v1/presale/ai/workflow/status/${ticketId}`
    );
    return response.data;
  }

  // ============ 批量处理 ============

  /**
   * 批量AI处理
   * @param {Object} batchRequest - 批量处理请求
   */
  async batchProcess(batchRequest) {
    const response = await api.post(
      '/api/v1/presale/ai/batch-process',
      batchRequest
    );
    return response.data;
  }

  // ============ 健康检查 ============

  /**
   * AI服务健康检查
   */
  async healthCheck() {
    const response = await api.get('/api/v1/presale/ai/health-check');
    return response.data;
  }

  // ============ 配置管理 ============

  /**
   * 更新AI配置
   * @param {string} aiFunction - AI功能名称
   * @param {Object} configData - 配置数据
   */
  async updateConfig(aiFunction, configData) {
    const response = await api.post('/api/v1/presale/ai/config/update', configData, {
      params: { ai_function: aiFunction },
    });
    return response.data;
  }

  /**
   * 获取所有AI配置
   */
  async getAllConfigs() {
    const response = await api.get('/api/v1/presale/ai/config');
    return response.data;
  }

  // ============ 审计日志 ============

  /**
   * 获取操作审计日志
   * @param {Object} params - 查询参数
   */
  async getAuditLogs(params = {}) {
    const response = await api.get('/api/v1/presale/ai/audit-log', {
      params,
    });
    return response.data;
  }

  // ============ 报告导出 ============

  /**
   * 导出AI使用报告
   * @param {Object} exportRequest - 导出请求
   */
  async exportReport(exportRequest) {
    const response = await api.post(
      '/api/v1/presale/ai/export-report',
      exportRequest
    );
    return response.data;
  }

  // ============ AI功能调用 ============

  /**
   * 需求理解AI
   * @param {Object} requirementData - 需求数据
   */
  async analyzeRequirement(requirementData) {
    const response = await api.post(
      '/api/v1/presale/ai/requirement/analyze',
      requirementData
    );
    return response.data;
  }

  /**
   * 方案生成AI
   * @param {Object} solutionData - 方案数据
   */
  async generateSolution(solutionData) {
    const response = await api.post(
      '/api/v1/presale/ai/solution/generate',
      solutionData
    );
    return response.data;
  }

  /**
   * 成本估算AI
   * @param {Object} costData - 成本数据
   */
  async estimateCost(costData) {
    const response = await api.post(
      '/api/v1/presale/ai/cost/estimate',
      costData
    );
    return response.data;
  }

  /**
   * 赢率预测AI
   * @param {Object} winRateData - 赢率数据
   */
  async predictWinRate(winRateData) {
    const response = await api.post(
      '/api/v1/presale/ai/winrate/predict',
      winRateData
    );
    return response.data;
  }

  /**
   * 报价生成AI
   * @param {Object} quotationData - 报价数据
   */
  async generateQuotation(quotationData) {
    const response = await api.post(
      '/api/v1/presale/ai/quotation/generate',
      quotationData
    );
    return response.data;
  }

  /**
   * 知识库推荐
   * @param {string} query - 查询内容
   */
  async searchKnowledge(query) {
    const response = await api.get('/api/v1/presale/ai/knowledge/search', {
      params: { query },
    });
    return response.data;
  }

  /**
   * 话术推荐
   * @param {Object} scriptData - 话术数据
   */
  async recommendScript(scriptData) {
    const response = await api.post(
      '/api/v1/presale/ai/script/recommend',
      scriptData
    );
    return response.data;
  }

  /**
   * 情绪分析
   * @param {Object} emotionData - 情绪数据
   */
  async analyzeEmotion(emotionData) {
    const response = await api.post(
      '/api/v1/presale/ai/emotion/analyze',
      emotionData
    );
    return response.data;
  }
}

export const presaleAIService = new PresaleAIService();
