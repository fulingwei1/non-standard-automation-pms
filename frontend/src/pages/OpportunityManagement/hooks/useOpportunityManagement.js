/**
 * 商机管理 - 核心 Hook
 * 封装全部 state、数据加载、CRUD 操作
 */

import { useState, useEffect, useMemo, useCallback } from "react";
import { useNavigate } from "react-router-dom";
import { opportunityApi, customerApi, userApi, presaleApi } from "../../../services/api";
import {
  INITIAL_FORM_DATA,
  INITIAL_GATE_DATA,
  INITIAL_REVIEW_FORM,
  buildDetailForm,
  isGatePassed,
  PAGE_SIZE,
} from "../constants";

export function useOpportunityManagement() {
  const navigate = useNavigate();

  // 列表数据
  const [opportunities, setOpportunities] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [owners, setOwners] = useState([]);
  const [loading, setLoading] = useState(false);
  const [total, setTotal] = useState(0);

  // 筛选与分页
  const [searchTerm, setSearchTerm] = useState("");
  const [stageFilter, setStageFilter] = useState("all");
  const [ownerFilter, setOwnerFilter] = useState("all");
  const [customerFilter, setCustomerFilter] = useState("all");
  const [viewMode, setViewMode] = useState("grid");
  const [page, setPage] = useState(1);

  // 选中与对话框
  const [selectedOpp, setSelectedOpp] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [showGateDialog, setShowGateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showReviewDialog, setShowReviewDialog] = useState(false);

  // 表单数据
  const [formData, setFormData] = useState(INITIAL_FORM_DATA);
  const [gateData, setGateData] = useState(INITIAL_GATE_DATA);
  const [reviewForm, setReviewForm] = useState(INITIAL_REVIEW_FORM);
  const [reviewTarget, setReviewTarget] = useState(null);
  const [reviewSubmitting, setReviewSubmitting] = useState(false);

  // 详情编辑
  const [detailEditing, setDetailEditing] = useState(false);
  const [detailSaving, setDetailSaving] = useState(false);
  const [detailForm, setDetailForm] = useState(null);

  // 阶段变更中的 loading 状态
  const [stageUpdating, setStageUpdating] = useState({});

  // ── 数据加载 ──────────────────────────────────────────────

  const loadOpportunities = useCallback(async ({ silent = false } = {}) => {
    if (!silent) setLoading(true);
    try {
      const params = {
        page,
        page_size: PAGE_SIZE,
        keyword: searchTerm || undefined,
        stage: stageFilter !== "all" ? stageFilter : undefined,
        owner_id: ownerFilter !== "all" ? ownerFilter : undefined,
        customer_id: customerFilter !== "all" ? customerFilter : undefined,
      };
      const response = await opportunityApi.list(params);
      if (response.data?.items) {
        setOpportunities(response.data.items);
        setTotal(response.data.total || 0);
      }
    } catch (error) {
    } finally {
      if (!silent) setLoading(false);
    }
  }, [page, searchTerm, stageFilter, ownerFilter, customerFilter]);

  const loadCustomers = useCallback(async () => {
    try {
      const response = await customerApi.list({ page: 1, page_size: 100 });
      if (response.data?.items) {
        setCustomers(response.data.items);
      }
    } catch (error) {
    }
  }, []);

  const loadOwners = useCallback(async () => {
    try {
      const response = await userApi.list({ page: 1, page_size: 100 });
      const paginatedData = response.formatted || response.data;
      if (paginatedData?.items) {
        setOwners(paginatedData.items);
      }
    } catch (error) {
    }
  }, []);

  useEffect(() => {
    loadOpportunities();
  }, [loadOpportunities]);

  useEffect(() => {
    loadCustomers();
    loadOwners();
  }, [loadCustomers, loadOwners]);

  // ── CRUD 操作 ─────────────────────────────────────────────

  const resetForm = useCallback(() => {
    setFormData(INITIAL_FORM_DATA);
  }, []);

  const handleCreate = useCallback(async () => {
    try {
      await opportunityApi.create(formData);
      setShowCreateDialog(false);
      resetForm();
      loadOpportunities();
    } catch (error) {
      alert("创建商机失败: " + (error.response?.data?.detail || error.message));
    }
  }, [formData, resetForm, loadOpportunities]);

  const handleEdit = useCallback((opp) => {
    setSelectedOpp(opp);
    setFormData({
      customer_id: opp.customer_id || "",
      opp_name: opp.opp_name || "",
      project_type: opp.project_type || "",
      equipment_type: opp.equipment_type || "",
      stage: opp.stage || "DISCOVERY",
      est_amount: opp.est_amount || "",
      est_margin: opp.est_margin || "",
      budget_range: opp.budget_range || "",
      decision_chain: opp.decision_chain || "",
      delivery_window: opp.delivery_window || "",
      acceptance_basis: opp.acceptance_basis || "",
      requirement: opp.requirement || {
        product_object: "",
        ct_seconds: "",
        interface_desc: "",
        site_constraints: "",
        acceptance_criteria: "",
      },
    });
  }, []);

  const handleSubmitGate = useCallback(async () => {
    if (!selectedOpp) return;
    try {
      await opportunityApi.submitGate(selectedOpp.id, gateData);
      setShowGateDialog(false);
      setSelectedOpp(null);
      loadOpportunities();
    } catch (error) {
      alert("提交阶段门失败: " + (error.response?.data?.detail || error.message));
    }
  }, [selectedOpp, gateData, loadOpportunities]);

  const handleStageChange = useCallback(async (opp, newStage) => {
    if (!opp || opp.stage === newStage) return;
    const prevStage = opp.stage;
    setStageUpdating((prev) => ({ ...prev, [opp.id]: true }));
    try {
      const response = await opportunityApi.update(opp.id, { stage: newStage });
      const updated = response.data || { ...opp, stage: newStage };
      setOpportunities((prev) =>
        (prev || []).map((item) => (item.id === opp.id ? { ...item, ...updated } : item))
      );
      if (selectedOpp?.id === opp.id) {
        setSelectedOpp((prev) => (prev ? { ...prev, ...updated } : prev));
      }
      await loadOpportunities({ silent: true });
    } catch (error) {
      alert("更新商机阶段失败: " + (error.response?.data?.detail || error.message));
      setOpportunities((prev) =>
        (prev || []).map((item) =>
          item.id === opp.id ? { ...item, stage: prevStage } : item
        )
      );
    } finally {
      setStageUpdating((prev) => {
        const next = { ...prev };
        delete next[opp.id];
        return next;
      });
    }
  }, [selectedOpp, loadOpportunities]);

  // ── 详情查看与编辑 ───────────────────────────────────────

  const handleViewDetail = useCallback(async (opp) => {
    try {
      const response = await opportunityApi.get(opp.id);
      if (response.data) {
        setSelectedOpp(response.data);
        setShowDetailDialog(true);
      }
    } catch (error) {
      setSelectedOpp(opp);
      setShowDetailDialog(true);
    }
  }, []);

  useEffect(() => {
    if (selectedOpp) {
      setDetailForm(buildDetailForm(selectedOpp));
      setDetailEditing(false);
    }
  }, [selectedOpp]);

  const handleDetailSave = useCallback(async () => {
    if (!selectedOpp || !detailForm) return;
    setDetailSaving(true);
    try {
      const requirementValues = detailForm.requirement || {};
      const requirementHasValue = Object.values(requirementValues).some(
        (value) => value !== "" && value !== null && value !== undefined
      );
      const requirementPayload =
        requirementHasValue || selectedOpp.requirement ? requirementValues : undefined;
      const payload = {
        opp_name: detailForm.opp_name,
        stage: detailForm.stage,
        project_type: detailForm.project_type,
        equipment_type: detailForm.equipment_type,
        probability: detailForm.probability,
        est_amount: detailForm.est_amount,
        est_margin: detailForm.est_margin,
        expected_close_date: detailForm.expected_close_date || null,
        budget_range: detailForm.budget_range,
        decision_chain: detailForm.decision_chain,
        delivery_window: detailForm.delivery_window,
        acceptance_basis: detailForm.acceptance_basis,
        risk_level: detailForm.risk_level,
        score: detailForm.score,
        priority_score: detailForm.priority_score,
        requirement_maturity: detailForm.requirement_maturity,
        assessment_status: detailForm.assessment_status,
        requirement: requirementPayload,
      };
      const response = await opportunityApi.update(selectedOpp.id, payload);
      const updated = response.data || { ...selectedOpp, ...payload };
      setSelectedOpp(updated);
      setOpportunities((prev) =>
        (prev || []).map((item) => (item.id === selectedOpp.id ? { ...item, ...updated } : item))
      );
      setDetailEditing(false);
      await loadOpportunities({ silent: true });
    } catch (error) {
      alert("更新商机详情失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setDetailSaving(false);
    }
  }, [selectedOpp, detailForm, loadOpportunities]);

  // ── 方案评审 ─────────────────────────────────────────────

  const openReviewDialog = useCallback((opp) => {
    if (!isGatePassed(opp?.gate_status)) {
      alert("商机阶段门未通过，无法申请评审");
      return;
    }
    const title = opp?.opp_name
      ? `方案评审申请 - ${opp.opp_name}`
      : "方案评审申请";
    setReviewTarget(opp);
    setReviewForm({
      title,
      description: opp?.opp_code ? `商机编号：${opp.opp_code}` : "",
      urgency: "NORMAL",
      expected_date: "",
    });
    setShowReviewDialog(true);
  }, []);

  const handleCreateReviewTicket = useCallback(async () => {
    if (!reviewTarget) return;
    if (!reviewForm.title.trim()) {
      alert("请输入申请标题");
      return;
    }
    setReviewSubmitting(true);
    try {
      await presaleApi.tickets.create({
        title: reviewForm.title.trim(),
        ticket_type: "SOLUTION_REVIEW",
        urgency: reviewForm.urgency,
        description: reviewForm.description?.trim() || undefined,
        customer_id: reviewTarget.customer_id || undefined,
        customer_name: reviewTarget.customer_name || undefined,
        opportunity_id: reviewTarget.id,
        expected_date: reviewForm.expected_date || undefined,
      });
      setShowReviewDialog(false);
      setReviewTarget(null);
      alert("方案评审已提交");
      navigate("/presales-tasks?type=review&status=reviewing");
    } catch (error) {
      alert("提交方案评审失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setReviewSubmitting(false);
    }
  }, [reviewTarget, reviewForm, navigate]);

  // ── 统计 ─────────────────────────────────────────────────

  const stats = useMemo(() => ({
    total,
    discovery: (opportunities || []).filter((o) => o.stage === "DISCOVERY").length,
    proposal: (opportunities || []).filter((o) => o.stage === "PROPOSAL").length,
    won: (opportunities || []).filter((o) => o.stage === "WON").length,
    totalAmount: (opportunities || []).reduce(
      (sum, o) => sum + (parseFloat(o.est_amount) || 0),
      0
    ),
  }), [opportunities, total]);

  const detailData = detailEditing && detailForm ? detailForm : selectedOpp;

  return {
    // 列表数据
    opportunities,
    customers,
    owners,
    loading,
    total,
    stats,

    // 筛选
    searchTerm, setSearchTerm,
    stageFilter, setStageFilter,
    ownerFilter, setOwnerFilter,
    customerFilter, setCustomerFilter,
    viewMode, setViewMode,
    page, setPage,

    // 选中与对话框
    selectedOpp, setSelectedOpp,
    showCreateDialog, setShowCreateDialog,
    showGateDialog, setShowGateDialog,
    showDetailDialog, setShowDetailDialog,
    showReviewDialog, setShowReviewDialog,
    stageUpdating,

    // 表单
    formData, setFormData,
    gateData, setGateData,
    reviewForm, setReviewForm,
    reviewSubmitting,

    // 详情编辑
    detailEditing, setDetailEditing,
    detailSaving,
    detailForm, setDetailForm,
    detailData,

    // 操作
    handleCreate,
    handleEdit,
    handleSubmitGate,
    handleStageChange,
    handleViewDetail,
    handleDetailSave,
    openReviewDialog,
    handleCreateReviewTicket,
    resetForm,
    buildDetailForm,

    // 常量
    PAGE_SIZE,
  };
}
