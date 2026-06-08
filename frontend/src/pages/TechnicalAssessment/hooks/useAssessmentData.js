import { useState, useEffect } from "react";
import { presaleWorkbenchApi, technicalAssessmentApi } from "../../../services/api";
import { normalizeAssessmentSourceType } from "../../../lib/assessmentSource";

function normalizeAssessments(response) {
  const candidates = [
    response?.formatted,
    response?.data?.data,
    response?.data,
    response,
  ];

  for (const candidate of candidates) {
    if (Array.isArray(candidate)) return candidate;
    if (Array.isArray(candidate?.items)) return candidate.items;
  }

  return [];
}

function parseContextId(value) {
  if (!value) {
    return null;
  }

  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function setIfPresent(target, key, value) {
  if (value !== undefined && value !== null && value !== "") {
    target[key] = value;
  }
}

function parseListValue(value) {
  if (!value) {
    return [];
  }
  if (Array.isArray(value)) {
    return value.map((item) => String(item).trim()).filter(Boolean);
  }
  if (typeof value === "object") {
    return Object.values(value).map((item) => String(item).trim()).filter(Boolean);
  }
  if (typeof value === "string") {
    try {
      const parsed = JSON.parse(value);
      return parseListValue(parsed);
    } catch {
      return value
        .split(/[\n,，、;；]/)
        .map((item) => item.trim())
        .filter(Boolean);
    }
  }
  return [String(value).trim()].filter(Boolean);
}

function joinDetailText(...values) {
  return values
    .flatMap((value) => parseListValue(value))
    .join(" ")
    .toLowerCase();
}

function mapRequirementMaturity(value) {
  const maturity = Number(value);
  if (!Number.isFinite(maturity)) {
    return "";
  }
  if (maturity >= 4) {
    return "mature";
  }
  if (maturity >= 3) {
    return "medium";
  }
  return "low";
}

function inferProcessDifficulty(detail) {
  const taktTime = Number(detail?.cycle_time_seconds);
  const workstationCount = Number(detail?.workstation_count);
  const technicalSpecCount = parseListValue(detail?.technical_spec).length;

  if (
    (Number.isFinite(taktTime) && taktTime > 0 && taktTime <= 8) ||
    (Number.isFinite(workstationCount) && workstationCount >= 4) ||
    technicalSpecCount >= 5
  ) {
    return "high";
  }
  if (
    (Number.isFinite(taktTime) && taktTime > 0 && taktTime <= 20) ||
    (Number.isFinite(workstationCount) && workstationCount >= 2) ||
    technicalSpecCount >= 2
  ) {
    return "medium";
  }
  return "";
}

function inferPrecisionRequirement(detail) {
  const text = joinDetailText(
    detail?.technical_spec,
    detail?.key_metrics_spec,
    detail?.acceptance_basis,
    detail?.test_scope,
  );
  if (!text) {
    return "";
  }
  if (/(0\.0[0-9]|微米|μm|um|极高精度)/i.test(text)) {
    return "extreme";
  }
  if (/(精度|高精度|视觉|mm|毫米|±)/i.test(text)) {
    return "high";
  }
  return "normal";
}

function inferSampleSupport(detail) {
  const text = joinDetailText(detail?.sample_availability);
  if (!text) {
    return "";
  }
  if (/(无|没有|none|unavailable)/i.test(text)) {
    return "none";
  }
  if (/(部分|有限|少量|limited)/i.test(text)) {
    return "limited";
  }
  if (/(可提供|已有|齐全|available|yes)/i.test(text)) {
    return "available";
  }
  return "";
}

function inferResourceOccupancy(detail) {
  const text = joinDetailText(
    detail?.customer_support_resources,
    detail?.customer_supplied_materials,
    detail?.power_supply,
    detail?.air_supply,
    detail?.environment,
  );
  if (!text) {
    return "";
  }
  if (/(无|缺|不可|none|unavailable)/i.test(text)) {
    return "unavailable";
  }
  if (/(部分|有限|待确认|limited|pending)/i.test(text)) {
    return "tight";
  }
  if (/(可提供|齐全|具备|available|ready)/i.test(text)) {
    return "available";
  }
  return "";
}

function inferDeliveryFeasibility(detail) {
  const maturity = Number(detail?.requirement_maturity);
  if (Number.isFinite(maturity)) {
    if (maturity >= 4 && (detail?.has_sow || detail?.has_interface_doc || detail?.has_drawing_doc)) {
      return "feasible";
    }
    if (maturity >= 3) {
      return "tight";
    }
    return "risky";
  }
  return "";
}

function inferChangeRisk(detail) {
  const maturity = Number(detail?.requirement_maturity);
  const riskFactors = parseListValue(detail?.key_risk_factors);
  if ((Number.isFinite(maturity) && maturity <= 2) || riskFactors.length > 0) {
    return "high";
  }
  if (detail?.is_frozen && Number.isFinite(maturity) && maturity >= 4) {
    return "low";
  }
  if (Number.isFinite(maturity)) {
    return "medium";
  }
  return "";
}

function addAssessmentScoringDefaults(data, detail) {
  if (!detail) {
    return;
  }

  setIfPresent(data, "tech_maturity", data.tech_maturity || mapRequirementMaturity(detail.requirement_maturity));
  setIfPresent(data, "process_difficulty", data.process_difficulty || inferProcessDifficulty(detail));
  setIfPresent(data, "precision_requirement", data.precision_requirement || inferPrecisionRequirement(detail));
  setIfPresent(data, "sample_support", data.sample_support || inferSampleSupport(detail));
  setIfPresent(data, "resource_occupancy", data.resource_occupancy || inferResourceOccupancy(detail));
  setIfPresent(data, "delivery_feasibility", data.delivery_feasibility || inferDeliveryFeasibility(detail));
  setIfPresent(data, "change_risk", data.change_risk || inferChangeRisk(detail));
}

function emptyCollaboration() {
  return {
    openItems: { items: [], total: 0, blocking_count: 0 },
    requirementFreezes: { items: [], total: 0 },
    aiClarifications: { items: [], total: 0 },
  };
}

const REQUIREMENT_META_KEYS = new Set([
  "source_type",
  "source_id",
  "project_id",
  "presale_ticket_id",
  "requirement_detail_id",
]);

function hasRequirementInput(requirementData = {}) {
  return Object.entries(requirementData).some(([key, value]) => {
    if (REQUIREMENT_META_KEYS.has(key)) {
      return false;
    }
    if (value === undefined || value === null || value === "") {
      return false;
    }
    if (Array.isArray(value)) {
      return value.length > 0;
    }
    return true;
  });
}

function isOpenAssessment(assessment) {
  return ["PENDING", "IN_PROGRESS"].includes(String(assessment?.status || "").toUpperCase());
}

function getAssessmentTicketId(assessment) {
  return assessment?.presale_ticket_id ?? assessment?.presaleTicketId ?? null;
}

function selectCurrentAssessment(assessments, selectedAssessmentId, presaleTicketId) {
  const requestedAssessment = selectedAssessmentId
    ? assessments.find((item) => String(item.id) === String(selectedAssessmentId))
    : null;
  if (requestedAssessment) {
    return requestedAssessment;
  }

  if (presaleTicketId) {
    const ticketAssessment = assessments.find(
      (item) => String(getAssessmentTicketId(item)) === String(presaleTicketId),
    );
    if (ticketAssessment) {
      return ticketAssessment;
    }

    const openUnboundAssessment = assessments.find(
      (item) => !getAssessmentTicketId(item) && isOpenAssessment(item),
    );
    if (openUnboundAssessment) {
      return openUnboundAssessment;
    }
  }

  return assessments[0] || null;
}

function buildRequirementDataFromDetail(
  detail,
  { sourceType, sourceId, presaleTicketId, projectId } = {},
) {
  const data = {};
  setIfPresent(data, "source_type", sourceType);
  setIfPresent(data, "source_id", sourceId);
  setIfPresent(data, "presale_ticket_id", presaleTicketId);
  setIfPresent(data, "project_id", projectId);

  if (!detail) {
    return data;
  }

  [
    "customer_factory_location",
    "target_object_type",
    "application_scenario",
    "delivery_mode",
    "expected_delivery_date",
    "requirement_source",
    "requirement_maturity",
    "has_sow",
    "has_interface_doc",
    "has_drawing_doc",
    "cycle_time_seconds",
    "workstation_count",
    "acceptance_method",
    "acceptance_basis",
    "requirement_items",
    "technical_spec",
    "delivery_requirements",
    "special_notes",
  ].forEach((key) => setIfPresent(data, key, detail[key]));

  setIfPresent(data, "requirement_detail_id", detail.id);
  setIfPresent(data, "lead_id", detail.lead_id);

  if (detail.has_sow !== undefined && detail.has_sow !== null) {
    data.hasSOW = detail.has_sow;
  }
  if (detail.requirement_maturity !== undefined && detail.requirement_maturity !== null) {
    data.requirementMaturity = detail.requirement_maturity;
  }
  if (detail.cycle_time_seconds !== undefined && detail.cycle_time_seconds !== null) {
    data.takt_time_s = detail.cycle_time_seconds;
    data.targetTakt = detail.cycle_time_seconds;
  }
  addAssessmentScoringDefaults(data, detail);

  return data;
}

/**
 * Hook for loading and managing assessment data for a specific source
 */
export function useAssessmentData(
  sourceType,
  sourceId,
  selectedAssessmentId,
  presaleTicketId,
  projectId,
) {
  const [assessment, setAssessment] = useState(null);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [requirementData, setRequirementData] = useState({});
  const [collaboration, setCollaboration] = useState(emptyCollaboration());
  const [enableAI, setEnableAI] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const normalizedSourceType = normalizeAssessmentSourceType(sourceType);
  const numericSourceId = parseContextId(sourceId);
  const numericPresaleTicketId = parseContextId(presaleTicketId);
  const numericProjectId = parseContextId(projectId);

  const loadAssessment = async () => {
    try {
      setLoading(true);
      let result = [];
      let contextRequirementData = {};
      let contextCollaboration = emptyCollaboration();

      if (normalizedSourceType === "lead") {
        const response = await technicalAssessmentApi.getLeadAssessments(
          parseInt(sourceId)
        );
        result = normalizeAssessments(response);
      } else if (normalizedSourceType === "opportunity") {
        const response = await technicalAssessmentApi.getOpportunityAssessments(
          parseInt(sourceId)
        );
        result = normalizeAssessments(response);
      }

      if (numericSourceId && presaleWorkbenchApi?.loadContext) {
        try {
          const contextParams = {
            sourceType: normalizedSourceType,
            sourceId: numericSourceId,
          };
          if (numericPresaleTicketId) {
            contextParams.presaleTicketId = numericPresaleTicketId;
          }

          const context = await presaleWorkbenchApi.loadContext(contextParams);
          contextRequirementData = buildRequirementDataFromDetail(
            context?.assessment?.requirementDetail,
            {
              sourceType: normalizedSourceType,
              sourceId: numericSourceId,
              presaleTicketId: numericPresaleTicketId,
              projectId: numericProjectId,
            },
          );
          contextCollaboration = context?.collaboration || emptyCollaboration();
        } catch (contextError) {
          console.warn("加载售前需求上下文失败:", contextError);
        }
      }

      setAssessments(result);
      setAssessment(selectCurrentAssessment(result, selectedAssessmentId, numericPresaleTicketId));
      setRequirementData(contextRequirementData);
      setCollaboration(contextCollaboration);
    } catch (error) {
      console.error("加载评估失败:", error);
      setAssessments([]);
      setAssessment(null);
      setRequirementData({});
      setCollaboration(emptyCollaboration());
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssessment();
  }, [normalizedSourceType, sourceId, selectedAssessmentId, presaleTicketId, projectId]);

  const handleApplyAssessment = async () => {
    try {
      const payload = {};
      if (numericPresaleTicketId) {
        payload.presale_ticket_id = numericPresaleTicketId;
      }

      let response;
      if (normalizedSourceType === "lead") {
        response = await technicalAssessmentApi.applyForLead(
          parseInt(sourceId),
          payload
        );
      } else if (normalizedSourceType === "opportunity") {
        response = await technicalAssessmentApi.applyForOpportunity(
          parseInt(sourceId),
          payload
        );
      } else {
        throw new Error("不支持的技术评估来源");
      }

      if (response.data?.data?.assessment_id) {
        await loadAssessment();
        alert("技术评估申请已提交");
      }
    } catch (error) {
      console.error("申请评估失败:", error);
      alert("申请评估失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleEvaluate = async () => {
    if (!hasRequirementInput(requirementData)) {
      alert("请先填写需求数据");
      return;
    }

    if (!assessment) {
      alert("请先申请技术评估");
      return;
    }

    try {
      setEvaluating(true);
      const response = await technicalAssessmentApi.evaluate(assessment.id, {
        requirement_data: requirementData,
        enable_ai: enableAI,
      });

      setAssessment(response.data);
      await loadAssessment();
      alert("技术评估完成");
    } catch (error) {
      console.error("执行评估失败:", error);
      alert("执行评估失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setEvaluating(false);
    }
  };

  return {
    assessment,
    setAssessment,
    assessments,
    loading,
    evaluating,
    requirementData,
    setRequirementData,
    collaboration,
    enableAI,
    setEnableAI,
    showHistory,
    setShowHistory,
    handleApplyAssessment,
    handleEvaluate,
  };
}
