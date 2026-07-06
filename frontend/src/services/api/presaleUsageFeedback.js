// 售前智能体使用反馈 API
import api from "./client";

/**
 * 提交使用反馈
 */
export async function submitUsageFeedback(payload) {
  const { data } = await api.post("/presale-usage-feedback", payload);
  return data?.data || data;
}

/**
 * 查看反馈列表
 */
export async function listUsageFeedback(limit = 20) {
  const { data } = await api.get("/presale-usage-feedback", { params: { limit } });
  return data?.data || data;
}

/**
 * 统计使用效果
 */
export async function usageFeedbackStats() {
  const { data } = await api.get("/presale-usage-feedback/stats");
  return data?.data || data;
}
