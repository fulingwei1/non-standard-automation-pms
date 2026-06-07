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

function compactParams(params = {}) {
  return Object.fromEntries(
    Object.entries(params).filter(([, value]) => (
      value !== undefined && value !== null && value !== ""
    )),
  );
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

  getOverview: (params = {}) =>
    api.get("/presale/workbench/overview", { params }),

  getContext: (params = {}) =>
    api.get("/presale/workbench/context", { params }),

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
  } = {}) {
    const response = await this.getOverview(compactParams({
      ticket_page: ticketParams.page,
      ticket_page_size: ticketParams.page_size,
      solution_page: solutionParams.page,
      solution_page_size: solutionParams.page_size,
    }));
    const overview = unwrapResponse(response) || {};
    const funnel = overview.funnel || {};

    return {
      tickets: normalizeListPayload(overview.tickets),
      solutions: normalizeListPayload(overview.solutions),
      templates: {
        assessment: normalizeListPayload(overview.templates?.assessment),
        technical: normalizeListPayload(overview.templates?.technical),
      },
      funnel: {
        summary: funnel.summary ?? null,
        health: funnel.health ?? null,
        conversion: funnel.conversion ?? null,
        dwellAlerts: normalizeListPayload(funnel.dwellAlerts),
      },
      meta: {
        failures: overview.meta?.failures || [],
      },
    };
  },

  async loadContext({
    sourceType,
    sourceId,
    entityType,
    entityId,
    presaleTicketId,
    transitionLogLimit = 20,
    activeAlertLimit = 10,
  } = {}) {
    const normalizedSourceType = normalizeSourceType(sourceType);
    const resolvedEntityType = normalizeEntityType(entityType || normalizedSourceType);
    const resolvedEntityId = entityId ?? sourceId;
    const response = await this.getContext(compactParams({
      source_type: normalizedSourceType,
      source_id: sourceId,
      entity_type: resolvedEntityType,
      entity_id: resolvedEntityId,
      presale_ticket_id: presaleTicketId,
      transition_log_limit: transitionLogLimit,
      active_alert_limit: activeAlertLimit,
    }));
    const context = unwrapResponse(response) || {};
    const assessment = context.assessment || {};
    const assessmentList = normalizeListPayload(assessment);
    const assessments = sortAssessmentsByLatest(assessmentList.items);
    const currentAssessment = assessment.current ?? assessments[0] ?? null;
    const funnel = context.funnel || {};

    return {
      source: context.source || {
        type: normalizedSourceType,
        id: sourceId,
      },
      ticket: context.ticket ?? null,
      assessment: {
        items: assessments,
        total: assessmentList.total,
        current: currentAssessment,
        requirementDetail: assessment.requirementDetail ?? null,
        risks: normalizeListPayload(assessment.risks),
        versions: normalizeListPayload(assessment.versions),
      },
      templates: {
        assessment: normalizeListPayload(context.templates?.assessment),
        technical: normalizeListPayload(context.templates?.technical),
      },
      solutions: normalizeListPayload(context.solutions),
      funnel: {
        entityType: funnel.entityType ?? resolvedEntityType,
        entityId: funnel.entityId ?? resolvedEntityId,
        gateConfigs: normalizeListPayload(funnel.gateConfigs),
        stages: normalizeListPayload(funnel.stages),
        transitionLogs: normalizeListPayload(funnel.transitionLogs),
        dwellAlerts: normalizeListPayload(funnel.dwellAlerts),
        gateStatus: funnel.gateStatus ?? null,
      },
      meta: {
        failures: context.meta?.failures || [],
      },
    };
  },
};

export default presaleWorkbenchApi;
