import { useState, useCallback, useEffect } from "react";
import { technicalAssessmentApi as assessmentApi } from "../../../services/api";

function normalizeAssessments(response) {
  const data = response?.data;
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(response?.items)) return response.items;
  return [];
}

function normalizeEvaluationPayload(result) {
  if (result?.requirement_data) {
    return {
      requirement_data: result.requirement_data,
      enable_ai: Boolean(result.enable_ai),
    };
  }

  return {
    requirement_data: result || {},
    enable_ai: false,
  };
}

/**
 * 技术评估数据 Hook
 */
export function useTechnicalAssessment(sourceType, sourceId) {
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [filters, setFilters] = useState({ status: "", type: "" });

  const numericSourceId = Number(sourceId);
  const canLoad = Boolean(sourceType && sourceId);

  const loadAssessments = useCallback(async () => {
    if (!canLoad) {
      setAssessments([]);
      setError(null);
      setLoading(false);
      return [];
    }

    try {
      setLoading(true);
      setError(null);

      let response;
      if (sourceType === "lead") {
        response = await assessmentApi.getLeadAssessments(numericSourceId);
      } else if (sourceType === "opportunity") {
        response = await assessmentApi.getOpportunityAssessments(numericSourceId);
      } else {
        throw new Error("不支持的技术评估来源");
      }

      const items = normalizeAssessments(response).filter((item) => {
        const statusMatched =
          !filters.status ||
          filters.status === "all" ||
          item.status === filters.status;
        const typeMatched =
          !filters.type ||
          filters.type === "all" ||
          item.source_type === filters.type;
        return statusMatched && typeMatched;
      });

      setAssessments(items);
      return items;
    } catch (err) {
      setAssessments([]);
      setError(err.response?.data?.detail || err.message);
      return [];
    } finally {
      setLoading(false);
    }
  }, [canLoad, filters.status, filters.type, numericSourceId, sourceType]);

  const createAssessment = useCallback(
    async (data = {}) => {
      if (!canLoad) {
        return { success: false, error: "缺少技术评估来源" };
      }

      try {
        if (sourceType === "lead") {
          await assessmentApi.applyForLead(numericSourceId, data);
        } else if (sourceType === "opportunity") {
          await assessmentApi.applyForOpportunity(numericSourceId, data);
        } else {
          throw new Error("不支持的技术评估来源");
        }

        await loadAssessments();
        return { success: true };
      } catch (err) {
        return { success: false, error: err.response?.data?.detail || err.message };
      }
    },
    [canLoad, loadAssessments, numericSourceId, sourceType]
  );

  const submitAssessment = useCallback(
    async (id, result) => {
      try {
        await assessmentApi.evaluate(id, normalizeEvaluationPayload(result));
        await loadAssessments();
        return { success: true };
      } catch (err) {
        return { success: false, error: err.response?.data?.detail || err.message };
      }
    },
    [loadAssessments]
  );

  useEffect(() => {
    loadAssessments();
  }, [loadAssessments]);

  return {
    assessments,
    loading,
    error,
    filters,
    setFilters,
    loadAssessments,
    createAssessment,
    submitAssessment,
  };
}
