import { api } from "./client.js";

const compactPayload = (payload) =>
  Object.fromEntries(Object.entries(payload).filter(([, value]) => value !== undefined));

const getApprovalComment = (data = {}) => data.comment ?? data.reason ?? data.remark ?? "";

export const paymentApprovalApi = {
  list: (params = {}) => {
    const { tab = "pending", ...queryParams } = params || {};
    const endpoint =
      tab === "processed" ? "/approvals/pending/processed" : "/approvals/pending/mine";

    return api.get(endpoint, { params: queryParams });
  },
  approve: (id, data = {}) =>
    api.post(
      `/approvals/tasks/${id}/approve`,
      compactPayload({
        comment: getApprovalComment(data),
        attachments: data.attachments,
        eval_data: data.eval_data,
      })
    ),
  reject: (id, data = {}) =>
    api.post(
      `/approvals/tasks/${id}/reject`,
      compactPayload({
        comment: getApprovalComment(data),
        reject_to: data.reject_to,
        attachments: data.attachments,
      })
    ),
};
