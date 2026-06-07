import { api } from "./client.js";

function resolveLeadId(params = {}) {
  return params.lead_id ?? params.leadId ?? params.source_id ?? params.sourceId;
}

function normalizeEvaluationPayload(data = {}) {
  if ("requirement_data" in data || "enable_ai" in data) {
    return {
      ...data,
      enable_ai: Boolean(data.enable_ai),
    };
  }

  return {
    requirement_data: data,
    enable_ai: false,
  };
}

export const leadAssessmentApi = {
  list: (params = {}) => {
    const leadId = resolveLeadId(params);
    return api.get(`/sales/leads/${leadId}/assessments`);
  },
  submit: (id, data) =>
    api.post(`/sales/assessments/${id}/evaluate`, normalizeEvaluationPayload(data)),
};
