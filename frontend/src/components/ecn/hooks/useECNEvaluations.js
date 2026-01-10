/**
 * useECNEvaluations Hook
 * 管理 ECN 评估相关的状态和逻辑
 */
import { useState, useCallback } from "react";
import { ecnApi } from "../../../services/api";

const initialEvaluationForm = {
  eval_dept: "",
  impact_analysis: "",
  cost_estimate: 0,
  schedule_estimate: 0,
  resource_requirement: "",
  risk_assessment: "",
  eval_result: "APPROVED",
  eval_opinion: "",
  conditions: "",
};

export function useECNEvaluations(ecnId, refetchECN) {
  const [showEvaluationDialog, setShowEvaluationDialog] = useState(false);
  const [evaluationForm, setEvaluationForm] = useState(initialEvaluationForm);

  // 创建评估
  const handleCreateEvaluation = useCallback(async () => {
    if (!evaluationForm.eval_dept) {
      return {
        success: false,
        message: "请选择评估部门",
      };
    }

    try {
      await ecnApi.createEvaluation(ecnId, evaluationForm);
      setShowEvaluationDialog(false);
      setEvaluationForm(initialEvaluationForm);
      await refetchECN();
      return {
        success: true,
        message: "评估已创建",
      };
    } catch (error) {
      return {
        success: false,
        message:
          "创建评估失败: " + (error.response?.data?.detail || error.message),
      };
    }
  }, [ecnId, evaluationForm, refetchECN]);

  // 提交评估
  const handleSubmitEvaluation = useCallback(
    async (evaluationId) => {
      try {
        await ecnApi.submitEvaluation(evaluationId);
        await refetchECN();
        return {
          success: true,
          message: "评估已提交",
        };
      } catch (error) {
        return {
          success: false,
          message:
            "提交失败: " + (error.response?.data?.detail || error.message),
        };
      }
    },
    [refetchECN],
  );

  // 重置表单
  const resetForm = useCallback(() => {
    setEvaluationForm(initialEvaluationForm);
  }, []);

  return {
    // 对话框状态
    showEvaluationDialog,
    setShowEvaluationDialog,
    // 表单状态
    evaluationForm,
    setEvaluationForm,
    // 操作方法
    handleCreateEvaluation,
    handleSubmitEvaluation,
    resetForm,
  };
}
