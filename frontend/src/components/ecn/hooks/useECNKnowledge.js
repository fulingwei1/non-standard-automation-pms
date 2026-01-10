/**
 * useECNKnowledge Hook
 * 管理 ECN 知识库相关的状态和逻辑
 */
import { useState, useCallback } from "react";
import { ecnApi } from "../../../services/api";

const initialSolutionTemplateForm = {
  template_name: "",
  template_category: "",
  keywords: [],
};

export function useECNKnowledge(ecnId, ecn, refetchECN) {
  const [similarEcns, setSimilarEcns] = useState([]);
  const [solutionRecommendations, setSolutionRecommendations] = useState([]);
  const [extractedSolution, setExtractedSolution] = useState(null);
  const [loadingKnowledge, setLoadingKnowledge] = useState(false);
  const [showSolutionTemplateDialog, setShowSolutionTemplateDialog] =
    useState(false);
  const [solutionTemplateForm, setSolutionTemplateForm] = useState(
    initialSolutionTemplateForm,
  );

  // 提取解决方案
  const handleExtractSolution = useCallback(async () => {
    setLoadingKnowledge(true);
    try {
      const result = await ecnApi.extractSolution(ecnId, true);
      setExtractedSolution(result.data);
      await refetchECN();
      return {
        success: true,
        message: "解决方案提取成功",
      };
    } catch (error) {
      return {
        success: false,
        message: "提取失败: " + (error.response?.data?.detail || error.message),
      };
    } finally {
      setLoadingKnowledge(false);
    }
  }, [ecnId, refetchECN]);

  // 查找相似ECN
  const handleFindSimilarEcns = useCallback(async () => {
    setLoadingKnowledge(true);
    try {
      const result = await ecnApi.getSimilarEcns(ecnId, {
        top_n: 5,
        min_similarity: 0.3,
      });
      setSimilarEcns(result.data?.similar_ecns || []);
      return {
        success: true,
        message: `找到 ${result.data?.similar_ecns?.length || 0} 个相似ECN`,
      };
    } catch (error) {
      return {
        success: false,
        message: "查找失败: " + (error.response?.data?.detail || error.message),
      };
    } finally {
      setLoadingKnowledge(false);
    }
  }, [ecnId]);

  // 推荐解决方案
  const handleRecommendSolutions = useCallback(async () => {
    setLoadingKnowledge(true);
    try {
      const result = await ecnApi.recommendSolutions(ecnId, { top_n: 5 });
      setSolutionRecommendations(result.data?.recommendations || []);
      return {
        success: true,
        message: `推荐了 ${result.data?.recommendations?.length || 0} 个解决方案`,
      };
    } catch (error) {
      return {
        success: false,
        message: "推荐失败: " + (error.response?.data?.detail || error.message),
      };
    } finally {
      setLoadingKnowledge(false);
    }
  }, [ecnId]);

  // 应用解决方案模板
  const handleApplySolutionTemplate = useCallback(
    async (templateId) => {
      try {
        await ecnApi.applySolutionTemplate(ecnId, templateId);
        await refetchECN();
        return {
          success: true,
          message: "解决方案已应用",
        };
      } catch (error) {
        return {
          success: false,
          message:
            "应用失败: " + (error.response?.data?.detail || error.message),
        };
      }
    },
    [ecnId, refetchECN],
  );

  // 创建解决方案模板
  const handleCreateSolutionTemplate = useCallback(async () => {
    try {
      await ecnApi.createSolutionTemplate(ecnId, {
        template_name:
          solutionTemplateForm.template_name ||
          `${ecn?.ecn_title} - 解决方案模板`,
        template_category:
          solutionTemplateForm.template_category || ecn?.ecn_type,
        keywords: solutionTemplateForm.keywords,
      });
      setShowSolutionTemplateDialog(false);
      setSolutionTemplateForm(initialSolutionTemplateForm);
      return {
        success: true,
        message: "解决方案模板创建成功",
      };
    } catch (error) {
      return {
        success: false,
        message: "创建失败: " + (error.response?.data?.detail || error.message),
      };
    }
  }, [ecnId, ecn, solutionTemplateForm]);

  return {
    // 数据状态
    similarEcns,
    solutionRecommendations,
    extractedSolution,
    loadingKnowledge,
    // 对话框状态
    showSolutionTemplateDialog,
    setShowSolutionTemplateDialog,
    solutionTemplateForm,
    setSolutionTemplateForm,
    // 操作方法
    handleExtractSolution,
    handleFindSimilarEcns,
    handleRecommendSolutions,
    handleApplySolutionTemplate,
    handleCreateSolutionTemplate,
  };
}
