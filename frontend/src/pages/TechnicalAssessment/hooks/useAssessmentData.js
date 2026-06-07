import { useState, useEffect } from "react";
import { presaleWorkbenchApi, technicalAssessmentApi } from "../../../services/api";

function normalizeAssessments(response) {
  const data = response?.data;
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(response?.items)) return response.items;
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

function emptyCollaboration() {
  return {
    openItems: { items: [], total: 0, blocking_count: 0 },
    requirementFreezes: { items: [], total: 0 },
    aiClarifications: { items: [], total: 0 },
  };
}

function buildRequirementDataFromDetail(detail, { sourceType, sourceId } = {}) {
  if (!detail) {
    return {};
  }

  const data = {};
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

  setIfPresent(data, "source_type", sourceType);
  setIfPresent(data, "source_id", sourceId);
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

  return data;
}

/**
 * Hook for loading and managing assessment data for a specific source
 */
export function useAssessmentData(sourceType, sourceId, selectedAssessmentId, presaleTicketId) {
  const [assessment, setAssessment] = useState(null);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [requirementData, setRequirementData] = useState({});
  const [collaboration, setCollaboration] = useState(emptyCollaboration());
  const [enableAI, setEnableAI] = useState(false);
  const [showHistory, setShowHistory] = useState(false);
  const numericSourceId = parseContextId(sourceId);
  const numericPresaleTicketId = parseContextId(presaleTicketId);

  const loadAssessment = async () => {
    try {
      setLoading(true);
      let result = [];
      let contextRequirementData = {};
      let contextCollaboration = emptyCollaboration();

      if (sourceType === "lead") {
        const response = await technicalAssessmentApi.getLeadAssessments(
          parseInt(sourceId)
        );
        result = normalizeAssessments(response);
      } else if (sourceType === "opportunity") {
        const response = await technicalAssessmentApi.getOpportunityAssessments(
          parseInt(sourceId)
        );
        result = normalizeAssessments(response);
      }

      if (numericSourceId && presaleWorkbenchApi?.loadContext) {
        try {
          const contextParams = {
            sourceType,
            sourceId: numericSourceId,
          };
          if (numericPresaleTicketId) {
            contextParams.presaleTicketId = numericPresaleTicketId;
          }

          const context = await presaleWorkbenchApi.loadContext(contextParams);
          contextRequirementData = buildRequirementDataFromDetail(
            context?.assessment?.requirementDetail,
            { sourceType, sourceId: numericSourceId },
          );
          contextCollaboration = context?.collaboration || emptyCollaboration();
        } catch (contextError) {
          console.warn("加载售前需求上下文失败:", contextError);
        }
      }

      const requestedAssessment = selectedAssessmentId
        ? result.find((item) => String(item.id) === String(selectedAssessmentId))
        : null;

      setAssessments(result);
      setAssessment(requestedAssessment || result[0] || null);
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
  }, [sourceType, sourceId, selectedAssessmentId, presaleTicketId]);

  const handleApplyAssessment = async () => {
    try {
      const payload = {};
      if (numericPresaleTicketId) {
        payload.presale_ticket_id = numericPresaleTicketId;
      }

      let response;
      if (sourceType === "lead") {
        response = await technicalAssessmentApi.applyForLead(
          parseInt(sourceId),
          payload
        );
      } else {
        response = await technicalAssessmentApi.applyForOpportunity(
          parseInt(sourceId),
          payload
        );
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
    if (!requirementData || Object.keys(requirementData).length === 0) {
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
