import { api } from "./client.js";
import { technicalAssessmentApi } from "./engineering.js";
import { funnelApi } from "./funnel.js";
import { presaleApi } from "./presales.js";
import { presaleSolutionApi } from "./presaleSolution.js";
import { technicalParameterApi } from "./technicalParameter.js";

function unwrapResponse(response) {
  return response?.formatted ?? response?.data?.data ?? response?.data ?? null;
}

function normalizeListPayload(payload) {
  if (Array.isArray(payload)) {
    return {
      items: payload,
      total: payload.length,
    };
  }

  if (payload && Array.isArray(payload.items)) {
    return {
      ...payload,
      total: payload.total ?? payload.items.length,
    };
  }

  return {
    items: [],
    total: 0,
  };
}

function normalizeListResponse(response) {
  return normalizeListPayload(unwrapResponse(response));
}

function getErrorMessage(error) {
  const detail = error?.response?.data?.detail;
  if (typeof detail === "string" && detail) {
    return detail;
  }
  if (typeof error?.message === "string" && error.message) {
    return error.message;
  }
  return "未知错误";
}

function normalizeSourceType(sourceType) {
  return String(sourceType || "").trim().toLowerCase();
}

function normalizeEntityType(entityType) {
  if (!entityType) {
    return null;
  }
  return String(entityType).trim().toUpperCase();
}

function getAssessmentSortTime(assessment) {
  const timestamp =
    assessment?.evaluated_at ||
    assessment?.updated_at ||
    assessment?.created_at ||
    null;

  if (!timestamp) {
    return 0;
  }

  const date = new Date(timestamp);
  return Number.isNaN(date.getTime()) ? 0 : date.getTime();
}

function sortAssessmentsByLatest(assessments = []) {
  return [...assessments].sort((left, right) => {
    const timeDiff = getAssessmentSortTime(right) - getAssessmentSortTime(left);
    if (timeDiff !== 0) {
      return timeDiff;
    }
    return (right?.id ?? 0) - (left?.id ?? 0);
  });
}

function normalizeNumberField(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  const numericValue = Number(value);
  return Number.isNaN(numericValue) ? value : numericValue;
}

function normalizeJsonTextField(value) {
  if (value === "" || value === null || value === undefined) {
    return null;
  }

  if (typeof value === "string") {
    return value;
  }

  return JSON.stringify(value);
}

function normalizeRequirementDetailPayload(detail = {}) {
  const payload = { ...detail };

  [
    "id",
    "lead_id",
    "created_at",
    "updated_at",
    "requirement_version",
    "is_frozen",
    "frozen_at",
    "frozen_by",
    "frozen_by_name",
  ].forEach((field) => {
    delete payload[field];
  });

  payload.requirement_maturity = normalizeNumberField(payload.requirement_maturity);
  payload.cycle_time_seconds = normalizeNumberField(payload.cycle_time_seconds);
  payload.workstation_count = normalizeNumberField(payload.workstation_count);
  payload.expected_delivery_date =
    payload.expected_delivery_date === "" ? null : payload.expected_delivery_date;
  payload.requirement_items = normalizeJsonTextField(payload.requirement_items);
  payload.technical_spec = normalizeJsonTextField(payload.technical_spec);

  return Object.fromEntries(
    Object.entries(payload).filter(([, value]) => value !== undefined),
  );
}

function getAssessmentLoader(sourceType, sourceId) {
  if (sourceType === "lead") {
    return technicalAssessmentApi.getLeadAssessments(sourceId);
  }
  if (sourceType === "opportunity") {
    return technicalAssessmentApi.getOpportunityAssessments(sourceId);
  }
  throw new Error(`不支持的来源类型: ${sourceType}`);
}

async function collectSettled(taskMap) {
  const entries = Object.entries(taskMap);
  const settledEntries = await Promise.allSettled(entries.map(([, task]) => task));
  const data = {};
  const failures = [];

  settledEntries.forEach((result, index) => {
    const [key] = entries[index];
    if (result.status === "fulfilled") {
      data[key] = result.value;
      return;
    }

    data[key] = null;
    failures.push({
      key,
      message: getErrorMessage(result.reason),
    });
  });

  return { data, failures };
}

export const presaleWorkbenchApi = {
  unwrapResponse,
  normalizeListResponse,

  getAssessmentTemplates: (params = {}) =>
    api.get("/sales/assessment-templates", { params }),

  getAssessmentTemplate: (templateId, params = {}) =>
    api.get(`/sales/assessment-templates/${templateId}`, { params }),

  getAssessmentRisks: (assessmentId, params = {}) =>
    api.get(`/sales/assessments/${assessmentId}/risks`, { params }),

  createAssessmentRisk: (assessmentId, data) =>
    api.post(`/sales/assessments/${assessmentId}/risks`, data),

  getAssessmentVersions: (assessmentId) =>
    api.get(`/sales/assessments/${assessmentId}/versions`),

  createAssessmentVersion: (assessmentId, data) =>
    api.post(`/sales/assessments/${assessmentId}/versions`, data),

  async loadAssessmentArtifacts(assessmentId) {
    const detailData = await collectSettled({
      risks: this.getAssessmentRisks(assessmentId),
      versions: this.getAssessmentVersions(assessmentId),
    });

    return {
      risks: normalizeListResponse(detailData.data.risks),
      versions: normalizeListResponse(detailData.data.versions),
      meta: {
        failures: detailData.failures,
      },
    };
  },

  getAssessments(sourceType, sourceId) {
    return getAssessmentLoader(normalizeSourceType(sourceType), sourceId);
  },

  applyAssessment(sourceType, sourceId, data = {}) {
    const normalizedSourceType = normalizeSourceType(sourceType);
    if (normalizedSourceType === "lead") {
      return technicalAssessmentApi.applyForLead(sourceId, data);
    }
    if (normalizedSourceType === "opportunity") {
      return technicalAssessmentApi.applyForOpportunity(sourceId, data);
    }
    throw new Error(`不支持的来源类型: ${sourceType}`);
  },

  evaluateAssessment: (assessmentId, data) =>
    technicalAssessmentApi.evaluate(assessmentId, data),

  getRequirementDetail: (leadId) =>
    technicalAssessmentApi.getRequirementDetail(leadId),

  async saveRequirementDetail(leadId, detail, { hasExisting = false } = {}) {
    const payload = normalizeRequirementDetailPayload(detail);

    try {
      if (hasExisting) {
        return await technicalAssessmentApi.updateRequirementDetail(leadId, payload);
      }

      return await technicalAssessmentApi.createRequirementDetail(leadId, payload);
    } catch (error) {
      const status = error?.response?.status;
      if (hasExisting && status === 404) {
        return technicalAssessmentApi.createRequirementDetail(leadId, payload);
      }
      if (!hasExisting && status === 400) {
        return technicalAssessmentApi.updateRequirementDetail(leadId, payload);
      }
      throw error;
    }
  },

  getTechnicalTemplates: (params = {}) =>
    technicalParameterApi.list(params),

  getTechnicalTemplate: (templateId) =>
    technicalParameterApi.get(templateId),

  matchTechnicalTemplates: (params = {}) =>
    technicalParameterApi.match(params),

  estimateTechnicalCost: (data) =>
    technicalParameterApi.estimateCost(data),

  getSolutionsByTicket: (ticketId, params = {}) =>
    presaleSolutionApi.findByTicket(ticketId, params),

  getSolutionsByOpportunity: (opportunityId, params = {}) =>
    presaleSolutionApi.findByOpportunity(opportunityId, params),

  getSolutions: (params = {}) =>
    presaleSolutionApi.list(params),

  getTickets: (params = {}) =>
    presaleApi.tickets.list(params),

  getFunnelSummary: (params = {}) =>
    funnelApi.getSummary(params),

  getFunnelHealth: (params = {}) =>
    funnelApi.getHealthDashboard(params),

  getFunnelConversionRates: (params = {}) =>
    funnelApi.getConversionRates(params),

  validateGate: (data) =>
    funnelApi.validateGate(data),

  transition: (data) =>
    funnelApi.transition(data),

  async loadOverview({
    ticketParams = { page: 1, page_size: 6 },
    solutionParams = { page: 1, page_size: 6 },
    assessmentTemplateParams = { is_active: true, limit: 20 },
    technicalTemplateParams = { is_active: true, page: 1, page_size: 20 },
    alertParams = { status: "ACTIVE", limit: 8 },
    summaryParams = {},
    conversionParams = {},
  } = {}) {
    const overview = await collectSettled({
      tickets: this.getTickets(ticketParams),
      solutions: this.getSolutions(solutionParams),
      assessmentTemplates: this.getAssessmentTemplates(assessmentTemplateParams),
      technicalTemplates: this.getTechnicalTemplates(technicalTemplateParams),
      funnelSummary: this.getFunnelSummary(summaryParams),
      funnelHealth: this.getFunnelHealth(),
      conversionRates: this.getFunnelConversionRates(conversionParams),
      dwellAlerts: funnelApi.getDwellTimeAlerts(alertParams),
    });

    return {
      tickets: normalizeListResponse(overview.data.tickets),
      solutions: normalizeListResponse(overview.data.solutions),
      templates: {
        assessment: normalizeListResponse(overview.data.assessmentTemplates),
        technical: normalizeListResponse(overview.data.technicalTemplates),
      },
      funnel: {
        summary: unwrapResponse(overview.data.funnelSummary),
        health: unwrapResponse(overview.data.funnelHealth),
        conversion: unwrapResponse(overview.data.conversionRates),
        dwellAlerts: normalizeListResponse(overview.data.dwellAlerts),
      },
      meta: {
        failures: overview.failures,
      },
    };
  },

  async loadContext({
    sourceType,
    sourceId,
    entityType,
    entityId,
    presaleTicketId,
    assessmentTemplateParams = { is_active: true, limit: 50 },
    technicalTemplateParams = { is_active: true, page: 1, page_size: 20 },
    transitionLogLimit = 20,
    activeAlertLimit = 10,
    solutionParams = {},
  }) {
    const normalizedSourceType = normalizeSourceType(sourceType);
    const resolvedEntityType = normalizeEntityType(entityType || normalizedSourceType);
    const resolvedEntityId = entityId ?? sourceId;

    const primaryTasks = {
      assessments: this.getAssessments(normalizedSourceType, sourceId),
      assessmentTemplates: this.getAssessmentTemplates(assessmentTemplateParams),
      technicalTemplates: this.getTechnicalTemplates(technicalTemplateParams),
      gateConfigs: funnelApi.getGateConfigs(),
    };

    if (normalizedSourceType === "lead") {
      primaryTasks.requirementDetail = this.getRequirementDetail(sourceId);
    }

    if (presaleTicketId) {
      primaryTasks.ticket = presaleApi.tickets.get(presaleTicketId);
      primaryTasks.solutions = this.getSolutionsByTicket(presaleTicketId, solutionParams);
    } else if (normalizedSourceType === "opportunity") {
      primaryTasks.solutions = this.getSolutionsByOpportunity(sourceId, solutionParams);
    }

    if (resolvedEntityType && resolvedEntityId) {
      primaryTasks.stages = funnelApi.getStages(resolvedEntityType);
      primaryTasks.transitionLogs = funnelApi.getTransitionLogs({
        entity_type: resolvedEntityType,
        entity_id: resolvedEntityId,
        limit: transitionLogLimit,
      });
      primaryTasks.dwellAlerts = funnelApi.getDwellTimeAlerts({
        entity_type: resolvedEntityType,
        status: "ACTIVE",
        limit: activeAlertLimit,
      });
    }

    const primary = await collectSettled(primaryTasks);
    const assessmentList = normalizeListResponse(primary.data.assessments);
    const assessments = sortAssessmentsByLatest(assessmentList.items);
    const currentAssessment = assessments[0] ?? null;

    let risks = { items: [], total: 0 };
    let versions = { items: [], total: 0 };
    const failures = [...primary.failures];

    if (currentAssessment?.id) {
      const assessmentDetails = await collectSettled({
        risks: this.getAssessmentRisks(currentAssessment.id),
        versions: this.getAssessmentVersions(currentAssessment.id),
      });

      risks = normalizeListResponse(assessmentDetails.data.risks);
      versions = normalizeListResponse(assessmentDetails.data.versions);
      failures.push(...assessmentDetails.failures);
    }

    return {
      source: {
        type: normalizedSourceType,
        id: sourceId,
      },
      ticket: unwrapResponse(primary.data.ticket),
      assessment: {
        items: assessments,
        total: assessmentList.total,
        current: currentAssessment,
        requirementDetail: unwrapResponse(primary.data.requirementDetail),
        risks,
        versions,
      },
      templates: {
        assessment: normalizeListResponse(primary.data.assessmentTemplates),
        technical: normalizeListResponse(primary.data.technicalTemplates),
      },
      solutions: normalizeListResponse(primary.data.solutions),
      funnel: {
        entityType: resolvedEntityType,
        entityId: resolvedEntityId,
        gateConfigs: normalizeListPayload(unwrapResponse(primary.data.gateConfigs)),
        stages: normalizeListResponse(primary.data.stages),
        transitionLogs: normalizeListResponse(primary.data.transitionLogs),
        dwellAlerts: normalizeListResponse(primary.data.dwellAlerts),
      },
      meta: {
        failures,
      },
    };
  },
};

export default presaleWorkbenchApi;
