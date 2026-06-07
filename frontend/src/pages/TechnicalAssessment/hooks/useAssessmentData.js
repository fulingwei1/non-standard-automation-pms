import { useState, useEffect } from "react";
import { technicalAssessmentApi } from "../../../services/api";

function normalizeAssessments(response) {
  const data = response?.data;
  if (Array.isArray(data)) return data;
  if (Array.isArray(data?.items)) return data.items;
  if (Array.isArray(response?.items)) return response.items;
  return [];
}

/**
 * Hook for loading and managing assessment data for a specific source
 */
export function useAssessmentData(sourceType, sourceId) {
  const [assessment, setAssessment] = useState(null);
  const [assessments, setAssessments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [evaluating, setEvaluating] = useState(false);
  const [requirementData, setRequirementData] = useState({});
  const [enableAI, setEnableAI] = useState(false);
  const [showHistory, setShowHistory] = useState(false);

  const loadAssessment = async () => {
    try {
      setLoading(true);
      let result = [];

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

      setAssessments(result);
      setAssessment(result[0] || null);
    } catch (error) {
      console.error("加载评估失败:", error);
      setAssessments([]);
      setAssessment(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAssessment();
  }, [sourceType, sourceId]);

  const handleApplyAssessment = async () => {
    try {
      let response;
      if (sourceType === "lead") {
        response = await technicalAssessmentApi.applyForLead(
          parseInt(sourceId),
          {}
        );
      } else {
        response = await technicalAssessmentApi.applyForOpportunity(
          parseInt(sourceId),
          {}
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
    enableAI,
    setEnableAI,
    showHistory,
    setShowHistory,
    handleApplyAssessment,
    handleEvaluate,
  };
}
