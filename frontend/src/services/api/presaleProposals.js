// 售前方案协作 API
import api from "./client";

/** 从智能体结果创建方案 */
export async function createProposal(payload) {
  const { data } = await api.post("/presale-proposals", payload);
  return data?.data || data;
}

/** 迭代修改（提建议→agent改） */
export async function reviseProposal(proposalId, changeRequest) {
  const { data } = await api.post(`/presale-proposals/${proposalId}/revise`, {
    change_request: changeRequest,
  });
  return data?.data || data;
}

/** 提交审核 */
export async function submitProposal(proposalId) {
  const { data } = await api.post(`/presale-proposals/${proposalId}/submit`);
  return data?.data || data;
}

/** 审核操作（approve/reject） */
export async function reviewProposal(proposalId, action, comment) {
  const { data } = await api.post(`/presale-proposals/${proposalId}/review`, {
    action,
    comment,
  });
  return data?.data || data;
}

/** 方案列表 */
export async function listProposals(status = null, limit = 20) {
  const { data } = await api.get("/presale-proposals", {
    params: status ? { status } : { limit },
  });
  return data?.data || data;
}

/** 待审队列 */
export async function pendingProposals() {
  const { data } = await api.get("/presale-proposals/pending");
  return data?.data || data;
}

/** 方案详情（含迭代历史） */
export async function getProposalDetail(proposalId) {
  const { data } = await api.get(`/presale-proposals/${proposalId}`);
  return data?.data || data;
}
