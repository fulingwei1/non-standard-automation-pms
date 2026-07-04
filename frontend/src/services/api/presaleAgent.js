// 售前智能体 API
// 后台任务模式：POST 提交 → 轮询 GET /ai-jobs/{id} 拿结果
import api from "./client";

/**
 * 提交售前智能体分析（后台任务）
 * @param {{requirement_text: string, customer_id?: number, industry_hint?: string, equipment_hint?: string,
 *          enable_deep_risk?: boolean, enable_deep_solution?: boolean}} payload
 *   - enable_deep_risk: 启用 Step7 自主风险深挖（+约 16s，带证据的供应链/成本风险）
 *   - enable_deep_solution: 启用 Step8 深度方案生成（+约 55s，完整子系统/设备选型/档位/周期）
 * @returns {Promise<{job_id: number, status: string, poll_url: string}>}
 */
export async function submitPresaleAgent(payload) {
  const { data } = await api.post("/ai-jobs/presale-agent", payload);
  return data?.data || data;
}

/**
 * 查询任务状态/结果
 * @param {number} jobId
 * @returns {Promise<{job_id:number, status:string, progress:number, result:any, error:string|null}>}
 */
export async function getPresaleAgentJob(jobId) {
  const { data } = await api.get(`/ai-jobs/${jobId}`);
  return data?.data || data;
}

/**
 * 轮询直到 SUCCESS/FAILED（带超时和取消）
 * @param {number} jobId
 * @param {(job)=>void} onUpdate 每次轮询到的中间状态回调（用于展示 progress）
 * @param {{intervalMs?:number, maxAttempts?:number, signal?:AbortSignal}} opts
 * @returns {Promise<any>} job.result
 */
export async function pollPresaleAgentJob(jobId, onUpdate, opts = {}) {
  const { intervalMs = 2500, maxAttempts = 60, signal } = opts;
  for (let i = 0; i < maxAttempts; i++) {
    if (signal?.aborted) throw new Error("已取消");
    await new Promise((r, rej) => {
      const t = setTimeout(r, intervalMs);
      signal?.addEventListener("abort", () => {
        clearTimeout(t);
        rej(new Error("已取消"));
      }, { once: true });
    });
    const job = await getPresaleAgentJob(jobId);
    onUpdate?.(job);
    if (job.status === "SUCCESS") return job.result;
    if (job.status === "FAILED") throw new Error(job.error || "智能体分析失败");
  }
  throw new Error("分析超时");
}

/**
 * 需求澄清（多轮对话）
 * @param {string} requirementText 本轮输入
 * @param {Array<{role:string,content:string}>} history 历史对话
 */
export async function clarifyRequirement(requirementText, history = []) {
  const { data } = await api.post("/ai-jobs/presale-clarify", {
    requirement_text: requirementText,
    history,
  });
  return data?.data || data;
}
export async function submitRevision(payload) {
  const { data } = await api.post("/presale-agent/revisions", payload);
  return data?.data || data;
}

/**
 * 查修订历史
 */
export async function listRevisions(limit = 20, majorOnly = false) {
  const { data } = await api.get("/presale-agent/revisions", {
    params: { limit, major_only: majorOnly },
  });
  return data?.data || data;
}

/**
 * 高频修改字段统计（AI 改进方向）
 */
export async function revisionStats(days = 30) {
  const { data } = await api.get(`/presale-agent/revisions/stats?days=${days}`);
  return data?.data || data;
}

export const presaleAgentApi = {
  submit: submitPresaleAgent,
  getJob: getPresaleAgentJob,
  poll: pollPresaleAgentJob,
  saveRevision: submitRevision,
  listRevisions,
  revisionStats,
  clarify: clarifyRequirement,
};

export default presaleAgentApi;
