import { api } from "./client.js";

function normalizeSourceType(sourceType) {
  return String(sourceType || "").toUpperCase();
}

function sourceAssessmentPath(sourceType, sourceId) {
  const normalizedType = normalizeSourceType(sourceType);
  if (normalizedType === "LEAD") {
    return `/sales/leads/${sourceId}/assessments`;
  }
  if (normalizedType === "OPPORTUNITY") {
    return `/sales/opportunities/${sourceId}/assessments`;
  }
  throw new Error("assessmentApi requires source_type LEAD or OPPORTUNITY");
}

function normalizeEvaluationPayload(data = {}) {
  if (data.requirement_data) {
    return {
      requirement_data: data.requirement_data,
      enable_ai: Boolean(data.enable_ai),
    };
  }
  return {
    requirement_data: data,
    enable_ai: false,
  };
}

export const assessmentApi = {
  list: ({ source_type, source_id } = {}) =>
    api.get(sourceAssessmentPath(source_type, source_id)),

  create: ({ source_type, source_id, evaluator_id } = {}) =>
    api.post(`${sourceAssessmentPath(source_type, source_id)}/apply`, {
      ...(evaluator_id ? { evaluator_id } : {}),
    }),

  submit: (id, data) =>
    api.post(`/sales/assessments/${id}/evaluate`, normalizeEvaluationPayload(data)),
};
