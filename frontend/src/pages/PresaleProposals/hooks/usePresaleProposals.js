/**
 * 售前方案管理 Hook
 * 管理方案列表、生成、评审、版本等状态
 */

import { useCallback, useEffect, useMemo, useState } from "react";
import { presaleApi } from "../../../services/api";
import {
  extractItems,
  normalizeSolution,
  DEFAULT_GENERATOR_FORM,
} from '../constants';

export function usePresaleProposals() {
  const [activeTab, setActiveTab] = useState("list");
  const [statusFilter, setStatusFilter] = useState("all");
  const [searchKeyword, setSearchKeyword] = useState("");
  const [solutions, setSolutions] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const [generating, setGenerating] = useState(false);
  const [generationError, setGenerationError] = useState("");
  const [latestGenerated, setLatestGenerated] = useState(null);
  const [generatorForm, setGeneratorForm] = useState(DEFAULT_GENERATOR_FORM);

  const [reviewActionLoadingId, setReviewActionLoadingId] = useState(null);
  const [reviewComments, setReviewComments] = useState({});

  const [selectedSolutionId, setSelectedSolutionId] = useState("");
  const [selectedVersionId, setSelectedVersionId] = useState("");
  const [versions, setVersions] = useState([]);
  const [versionsLoading, setVersionsLoading] = useState(false);
  const [versionsError, setVersionsError] = useState("");

  // 加载方案列表
  const loadSolutions = useCallback(async () => {
    setLoading(true);
    setError("");
    try {
      const params = { page: 1, page_size: 100 };
      if (searchKeyword.trim()) params.keyword = searchKeyword.trim();
      const response = await presaleApi.solutions.list(params);
      const list = extractItems(response).map(normalizeSolution);
      const filteredList = statusFilter === "all" ? list : list.filter((s) => s.status === statusFilter);
      setSolutions(filteredList);
      if (filteredList.length > 0) {
        setSelectedSolutionId((prev) => prev || String(filteredList[0].id));
      }
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError?.message || "方案加载失败");
    } finally {
      setLoading(false);
    }
  }, [searchKeyword, statusFilter]);

  // 加载版本列表
  const loadVersions = useCallback(async (solutionId) => {
    if (!solutionId) { setVersions([]); setSelectedVersionId(""); return; }
    setVersionsLoading(true);
    setVersionsError("");
    try {
      const response = await presaleApi.solutions.getVersions(Number(solutionId));
      const list = extractItems(response).map(normalizeSolution);
      setVersions(list);
      if (list.length > 0) setSelectedVersionId(String(list[list.length - 1].id));
      else setSelectedVersionId("");
    } catch (requestError) {
      setVersions([]);
      setSelectedVersionId("");
      setVersionsError(requestError?.response?.data?.detail || requestError?.message || "版本加载失败");
    } finally {
      setVersionsLoading(false);
    }
  }, []);

  useEffect(() => { loadSolutions(); }, [loadSolutions]);
  useEffect(() => {
    if (activeTab === "versions") loadVersions(selectedSolutionId);
  }, [activeTab, selectedSolutionId, loadVersions]);

  // 统计数据
  const stats = useMemo(() => ({
    total: solutions.length,
    draft: solutions.filter((s) => s.status === "DRAFT").length,
    reviewing: solutions.filter((s) => s.status === "REVIEWING").length,
    approved: solutions.filter((s) => s.status === "APPROVED").length,
  }), [solutions]);

  // 评审队列
  const reviewQueue = useMemo(() =>
    solutions.filter((s) => ["DRAFT", "IN_PROGRESS", "REVIEWING"].includes(s.status)),
  [solutions]);

  // 当前选中版本
  const selectedVersion = useMemo(() => {
    if (!selectedVersionId) return null;
    return versions.find((v) => String(v.id) === String(selectedVersionId)) || null;
  }, [selectedVersionId, versions]);

  // 表单变更
  const handleGenerateFieldChange = (field, value) => {
    setGeneratorForm((prev) => ({ ...prev, [field]: value }));
  };

  // 应用模板建议
  const applyTemplateSuggestion = (template) => {
    const nextName = `${template.title} - ${new Date().toLocaleDateString("zh-CN")}`;
    const nextRequirement = `客户期望在 ${template.days} 内完成导入，重点关注交付节奏、系统稳定性与后续扩展能力。`;
    setGeneratorForm((prev) => ({ ...prev, name: nextName, requirementSummary: nextRequirement }));
  };

  // 生成方案
  const handleGenerateProposal = async () => {
    if (!generatorForm.name.trim()) { setGenerationError("请填写方案名称"); return; }
    setGenerating(true);
    setGenerationError("");
    try {
      const solutionOverview = `围绕${generatorForm.requirementSummary || "客户业务诉求"}构建三层方案结构：业务目标层、产线实现层、数据闭环层。`;
      const technicalSpec = ["1) 工站节拍与稼动率监控", "2) 测试数据与MES打通", "3) 模块化治具与快速换型"].join("\n");
      const payload = {
        name: generatorForm.name.trim(),
        solution_type: generatorForm.solutionType,
        industry: generatorForm.industry,
        test_type: generatorForm.testType,
        requirement_summary: generatorForm.requirementSummary,
        solution_overview: solutionOverview,
        technical_spec: technicalSpec,
      };
      if (generatorForm.estimatedCost) payload.estimated_cost = Number(generatorForm.estimatedCost);
      if (generatorForm.suggestedPrice) payload.suggested_price = Number(generatorForm.suggestedPrice);
      if (generatorForm.estimatedHours) payload.estimated_hours = Number(generatorForm.estimatedHours);
      if (generatorForm.estimatedDuration) payload.estimated_duration = Number(generatorForm.estimatedDuration);

      const response = await presaleApi.solutions.create(payload);
      const created = normalizeSolution(response?.data || response);
      setLatestGenerated(created);
      await loadSolutions();
      setSelectedSolutionId(String(created.id));
      setActiveTab("list");
    } catch (requestError) {
      setGenerationError(requestError?.response?.data?.detail || requestError?.message || "方案生成失败");
    } finally {
      setGenerating(false);
    }
  };

  // 评审操作
  const handleReviewAction = async (solutionId, reviewStatus) => {
    setReviewActionLoadingId(solutionId);
    try {
      const comment = reviewComments[solutionId] || (reviewStatus === "APPROVED" ? "方案符合交付标准" : "请补充风险控制与成本说明");
      await presaleApi.solutions.review(solutionId, { review_status: reviewStatus, review_comment: comment });
      await loadSolutions();
      if (activeTab === "versions") await loadVersions(selectedSolutionId || solutionId);
    } catch (requestError) {
      setError(requestError?.response?.data?.detail || requestError?.message || "方案评审失败");
    } finally {
      setReviewActionLoadingId(null);
    }
  };

  return {
    activeTab, setActiveTab,
    statusFilter, setStatusFilter,
    searchKeyword, setSearchKeyword,
    solutions, loading, error,
    stats, reviewQueue,
    // 生成
    generating, generationError, latestGenerated,
    generatorForm, handleGenerateFieldChange,
    applyTemplateSuggestion, handleGenerateProposal,
    // 评审
    reviewActionLoadingId, reviewComments, setReviewComments,
    handleReviewAction,
    // 版本
    selectedSolutionId, setSelectedSolutionId,
    selectedVersionId, setSelectedVersionId,
    versions, versionsLoading, versionsError,
    selectedVersion,
    // 操作
    loadSolutions,
  };
}
