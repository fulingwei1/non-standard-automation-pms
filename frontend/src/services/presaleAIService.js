/**
 * 售前 AI 服务（重建版）：需求分析 → 确认回填 → 方案/三档报价。
 *
 * 核心约定：方案生成与三档报价都传 requirement_analysis_id，
 * 后端自动带出已存分析内容——需求只录一次，不再前端重贴。
 * 重 AI 生成走后台任务（提交返回 job_id，轮询 /ai-jobs/{id}）。
 */
import api from "./api";

const unwrap = (r) => r.data?.data ?? r.data;

export const presaleAIService = {
  /** AI 需求分析（同步，<数秒） */
  analyzeRequirement: (payload) =>
    api.post("/presale/ai/analyze-requirement", payload).then(unwrap),

  /** 读取分析结果 */
  getAnalysis: (analysisId) =>
    api.get(`/presale/ai/analysis/${analysisId}`).then(unwrap),

  /** 人工确认分析：状态 approved + 增量回填商机需求（不覆盖人工值） */
  confirmAnalysis: (analysisId) =>
    api.post(`/presale/ai/analysis/${analysisId}/confirm`).then(unwrap),

  /** 提交方案生成后台任务（requirement_analysis_id 自动带出分析内容） */
  submitGenerateSolution: (payload) =>
    api.post("/presale/ai/generate-solution", payload).then(unwrap),

  /** 提交三档报价后台任务（base_requirements 为空时从分析记录组装） */
  submitThreeTierQuotation: (payload) =>
    api.post("/ai-jobs/three-tier-quotations", payload).then(unwrap),

  /** 轮询后台任务状态/结果 */
  getJob: (jobId) => api.get(`/ai-jobs/${jobId}`).then(unwrap),
};

export default presaleAIService;
