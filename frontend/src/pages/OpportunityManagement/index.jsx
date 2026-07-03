/**
 * Opportunity Management Page - Sales opportunity management
 * Features: Opportunity list, creation, update, gate management
 */

import { useState, useEffect, useMemo } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import {
  Search,
  Filter,
  Plus,
  Target,
  DollarSign,
  Clock,
  LayoutGrid,
  List,
  TrendingUp,
  ArrowRight
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  Button,
  Input,
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger
} from "../../components/ui";
import { cn } from "../../lib/utils";
import {
  opportunityApi,
  customerApi,
  userApi,
  presaleApi,
  presaleWorkbenchApi,
} from "../../services/api";
import { stageConfig, isGatePassed } from "./constants";
import OpportunityGrid from "./OpportunityGrid";
import OpportunityTable from "./OpportunityTable";
import CreateDialog from "./CreateDialog";
import GateDialog from "./GateDialog";
import DetailDialog from "./DetailDialog";
import ReviewDialog from "./ReviewDialog";

const appendReviewLine = (lines, label, value, suffix = "") => {
  if (value === undefined || value === null || value === "") {
    return;
  }
  lines.push(`${label}：${value}${suffix}`);
};

const buildReviewDescription = (opp) => {
  if (!opp) {
    return "";
  }

  const requirement = opp.requirement || {};
  const stageLabel = stageConfig[opp.stage]?.label || opp.stage;
  const lines = [];

  appendReviewLine(lines, "商机编号", opp.opp_code);
  appendReviewLine(lines, "客户", opp.customer_name);
  appendReviewLine(lines, "负责人", opp.owner_name);
  appendReviewLine(lines, "预计金额", opp.est_amount);
  appendReviewLine(lines, "阶段", stageLabel);
  appendReviewLine(lines, "项目类型", opp.project_type);
  appendReviewLine(lines, "设备类型", opp.equipment_type);
  appendReviewLine(lines, "赢率", opp.probability, "%");
  appendReviewLine(lines, "产品对象", requirement.product_object);
  appendReviewLine(lines, "节拍", requirement.ct_seconds, " 秒");
  appendReviewLine(lines, "接口", requirement.interface_desc);
  appendReviewLine(lines, "现场约束", requirement.site_constraints);
  appendReviewLine(lines, "验收依据", requirement.acceptance_criteria);

  return lines.join("\n");
};

const SUPPORT_TICKET_TYPE = "TECHNICAL_SUPPORT";
const ASSESSMENT_TICKET_TYPE = "FEASIBILITY_ASSESSMENT";
const REVIEW_TICKET_TYPE = "SOLUTION_REVIEW";
const ACTIVE_SUPPORT_STATUSES = new Set([
  "PENDING",
  "ACCEPTED",
  "IN_PROGRESS",
  "PROCESSING",
]);

const getTicketTitlePrefix = (ticketType) =>
  ({
    [ASSESSMENT_TICKET_TYPE]: "技术评估申请",
    [REVIEW_TICKET_TYPE]: "方案评审申请",
  })[ticketType] || "售前支持申请";

const buildTicketTitle = (opp, ticketType = SUPPORT_TICKET_TYPE) =>
  opp?.opp_name
    ? `${getTicketTitlePrefix(ticketType)} - ${opp.opp_name}`
    : getTicketTitlePrefix(ticketType);

const normalizeTicketStatusForUrl = (status, ticketType) => {
  if (ticketType === REVIEW_TICKET_TYPE) {
    return "reviewing";
  }
  const normalized = String(status || "").toUpperCase();
  if (["ACCEPTED", "IN_PROGRESS", "PROCESSING"].includes(normalized)) {
    return "in_progress";
  }
  if (["COMPLETED", "CLOSED", "CANCELLED"].includes(normalized)) {
    return "completed";
  }
  return "pending";
};

const buildPresalesTicketBoardPath = ({
  ticketType = SUPPORT_TICKET_TYPE,
  status,
  leadId,
  opportunityId,
  ticketId,
}) => {
  const params = new URLSearchParams();
  params.set("tab", "reviews");
  params.set(
    "type",
    ({
      [ASSESSMENT_TICKET_TYPE]: "assessment",
      [REVIEW_TICKET_TYPE]: "review",
    })[ticketType] || "support",
  );
  params.set("status", normalizeTicketStatusForUrl(status, ticketType));
  if (leadId) {
    params.set("lead_id", String(leadId));
  }
  if (opportunityId) {
    params.set("opportunity_id", String(opportunityId));
  }
  if (ticketId) {
    params.set("ticket_id", String(ticketId));
  }
  return `/presales/technical-solutions?${params.toString()}`;
};

const isReusablePresaleTicket = (ticket, ticketType) => (
  ticket?.ticket_type === ticketType &&
  ACTIVE_SUPPORT_STATUSES.has(String(ticket.status || "").toUpperCase())
);

const getTicketItems = (response) => {
  const payload = response?.formatted ?? response?.data?.data ?? response?.data ?? response;
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  return [];
};

const findReusablePresaleTicket = (tickets, ticketType) =>
  (tickets || []).find((ticket) => isReusablePresaleTicket(ticket, ticketType)) || null;

const normalizeEstimatedAmountWan = (amount) => {
  if (amount === undefined || amount === null || amount === "") {
    return undefined;
  }
  const numericAmount = Number(amount);
  return Number.isNaN(numericAmount) ? undefined : numericAmount / 10000;
};

const unwrapTicketId = (response) =>
  response?.data?.id || response?.data?.data?.id || response?.formatted?.id || null;

export default function OpportunityManagement({ embedded = false }) {
  const [opportunities, setOpportunities] = useState([]);
  const [customers, setCustomers] = useState([]);
  const [owners, setOwners] = useState([]);
  const [loading, setLoading] = useState(false);
  const [stageUpdating, setStageUpdating] = useState({});
  const [detailEditing, setDetailEditing] = useState(false);
  const [detailSaving, setDetailSaving] = useState(false);
  const [detailForm, setDetailForm] = useState(null);
  const [searchTerm, setSearchTerm] = useState("");
  const [stageFilter, setStageFilter] = useState("all");
  const [selectedOpp, setSelectedOpp] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [_showEditDialog, setShowEditDialog] = useState(false);
  const [showGateDialog, setShowGateDialog] = useState(false);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [showReviewDialog, setShowReviewDialog] = useState(false);
  const [reviewSubmitting, setReviewSubmitting] = useState(false);
  const [reviewTarget, setReviewTarget] = useState(null);
  const [viewMode, setViewMode] = useState("grid");
  const [ownerFilter, setOwnerFilter] = useState("all");
  const [customerFilter, setCustomerFilter] = useState("all");
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const pageSize = 20;
  const navigate = useNavigate();

  // 命令栏"新建商机"动作：带 ai_hint 进来时自动打开新建对话框并 AI 预填
  const [searchParams, setSearchParams] = useSearchParams();
  const [autofillHint, setAutofillHint] = useState("");
  useEffect(() => {
    const hint = searchParams.get("ai_hint");
    if (hint) {
      setAutofillHint(hint);
      setShowCreateDialog(true);
      setSearchParams({}, { replace: true });
    }
  }, [searchParams, setSearchParams]);

  const [formData, setFormData] = useState({
    customer_id: "",
    opp_name: "",
    project_type: "",
    equipment_type: "",
    stage: "DISCOVERY",
    est_amount: "",
    est_margin: "",
    budget_range: "",
    decision_chain: "",
    delivery_window: "",
    acceptance_basis: "",
    requirement: {
      product_object: "",
      ct_seconds: "",
      interface_desc: "",
      site_constraints: "",
      acceptance_criteria: ""
    }
  });

  const [gateData, setGateData] = useState({
    gate_status: "PASS",
    remark: ""
  });

  const [reviewForm, setReviewForm] = useState({
    ticket_type: SUPPORT_TICKET_TYPE,
    title: "",
    description: "",
    urgency: "NORMAL",
    expected_date: ""
  });

  const loadOpportunities = async ({ silent = false } = {}) => {
    if (!silent) {
      setLoading(true);
    }
    try {
      const params = {
        page,
        page_size: pageSize,
        keyword: searchTerm || undefined,
        stage: stageFilter !== "all" ? stageFilter : undefined,
        owner_id: ownerFilter !== "all" ? ownerFilter : undefined,
        customer_id: customerFilter !== "all" ? customerFilter : undefined
      };
      const response = await opportunityApi.list(params);
      if (response.data && response.data.items) {
        setOpportunities(response.data.items);
        setTotal(response.data.total || 0);
      }
    } catch (error) {
      console.error("加载商机列表失败:", error);
    } finally {
      if (!silent) {
        setLoading(false);
      }
    }
  };

  const loadCustomers = async () => {
    try {
      const response = await customerApi.list({ page: 1, page_size: 1000 });
      if (response.data && response.data.items) {
        setCustomers(response.data.items);
      }
    } catch (error) {
      console.error("加载客户列表失败:", error);
    }
  };

  const loadOwners = async () => {
    try {
      const response = await userApi.options({ page: 1, page_size: 100, is_active: true });
      // 使用统一响应格式处理
      const paginatedData = response.formatted || response.data;
      if (paginatedData?.items) {
        setOwners(paginatedData.items);
      }
    } catch (error) {
      console.error("加载负责人列表失败:", error);
    }
  };

  useEffect(() => {
    loadOpportunities();
  }, [page, searchTerm, stageFilter, ownerFilter, customerFilter]);

  useEffect(() => {
    loadCustomers();
    loadOwners();
  }, []);

  const handleCreate = async () => {
    try {
      await opportunityApi.create(formData);
      setShowCreateDialog(false);
      resetForm();
      loadOpportunities();
    } catch (error) {
      console.error("创建商机失败:", error);
      alert("创建商机失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const _handleUpdate = async () => {
    if (!selectedOpp) {return;}
    try {
      await opportunityApi.update(selectedOpp.id, formData);
      setShowEditDialog(false);
      setSelectedOpp(null);
      loadOpportunities();
    } catch (error) {
      console.error("更新商机失败:", error);
      alert("更新商机失败: " + (error.response?.data?.detail || error.message));
    }
  };

  const handleSubmitGate = async () => {
    if (!selectedOpp) {return;}
    try {
      await opportunityApi.submitGate(selectedOpp.id, gateData);
      setShowGateDialog(false);
      setSelectedOpp(null);
      loadOpportunities();
    } catch (error) {
      console.error("提交阶段门失败:", error);
      alert(
        "提交阶段门失败: " + (error.response?.data?.detail || error.message)
      );
    }
  };

  const handleEdit = (opp) => {
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
        acceptance_criteria: ""
      }
    });
    setShowEditDialog(true);
  };

  const handleStageChange = async (opp, newStage) => {
    if (!opp || opp.stage === newStage) {
      return;
    }
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
      console.error("更新商机阶段失败:", error);
      alert(
        "更新商机阶段失败: " + (error.response?.data?.detail || error.message)
      );
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
  };

  const resetForm = () => {
    setFormData({
      customer_id: "",
      opp_name: "",
      project_type: "",
      equipment_type: "",
      stage: "DISCOVERY",
      est_amount: "",
      est_margin: "",
      budget_range: "",
      decision_chain: "",
      delivery_window: "",
      acceptance_basis: "",
      requirement: {
        product_object: "",
        ct_seconds: "",
        interface_desc: "",
        site_constraints: "",
        acceptance_criteria: ""
      }
    });
  };

  const buildDetailForm = (opp) => ({
    opp_name: opp?.opp_name || "",
    stage: opp?.stage || "DISCOVERY",
    project_type: opp?.project_type || "",
    equipment_type: opp?.equipment_type || "",
    probability: opp?.probability ?? "",
    est_amount: opp?.est_amount ?? "",
    est_margin: opp?.est_margin ?? "",
    expected_close_date: opp?.expected_close_date ?
      String(opp.expected_close_date).slice(0, 10) :
      "",
    budget_range: opp?.budget_range || "",
    decision_chain: opp?.decision_chain || "",
    delivery_window: opp?.delivery_window || "",
    acceptance_basis: opp?.acceptance_basis || "",
    risk_level: opp?.risk_level || "",
    score: opp?.score ?? "",
    priority_score: opp?.priority_score ?? "",
    requirement_maturity: opp?.requirement_maturity ?? "",
    assessment_status: opp?.assessment_status || "",
    requirement: {
      product_object: opp?.requirement?.product_object || "",
      ct_seconds: opp?.requirement?.ct_seconds ?? "",
      interface_desc: opp?.requirement?.interface_desc || "",
      site_constraints: opp?.requirement?.site_constraints || "",
      acceptance_criteria: opp?.requirement?.acceptance_criteria || "",
      safety_requirement: opp?.requirement?.safety_requirement || "",
      attachments: opp?.requirement?.attachments || "",
      extra_json: opp?.requirement?.extra_json || ""
    }
  });

  useEffect(() => {
    if (selectedOpp) {
      setDetailForm(buildDetailForm(selectedOpp));
      setDetailEditing(false);
    }
  }, [selectedOpp]);

  const openPresaleSupportDialog = (opp) => {
    setReviewTarget(opp);
    setReviewForm({
      ticket_type: SUPPORT_TICKET_TYPE,
      title: buildTicketTitle(opp, SUPPORT_TICKET_TYPE),
      description: buildReviewDescription(opp),
      urgency: "NORMAL",
      expected_date: ""
    });
    setShowReviewDialog(true);
  };

  const handleReviewTicketTypeChange = (ticketType) => {
    setReviewForm((prev) => ({
      ...prev,
      ticket_type: ticketType,
      title: buildTicketTitle(reviewTarget, ticketType),
    }));
  };

  const handleCreateReviewTicket = async () => {
    if (!reviewTarget) {
      return;
    }
    if (!reviewForm.title.trim()) {
      alert("请输入申请标题");
      return;
    }
    const ticketType = reviewForm.ticket_type || SUPPORT_TICKET_TYPE;
    if (ticketType === REVIEW_TICKET_TYPE && !isGatePassed(reviewTarget?.gate_status)) {
      alert("商机阶段门未通过，无法申请方案评审");
      return;
    }
    setReviewSubmitting(true);
    try {
      if ([SUPPORT_TICKET_TYPE, ASSESSMENT_TICKET_TYPE].includes(ticketType)) {
        const context = await presaleWorkbenchApi.loadContext({
          sourceType: "opportunity",
          sourceId: reviewTarget.id,
        });
        let reusableTicket = isReusablePresaleTicket(context?.ticket, ticketType)
          ? context.ticket
          : null;

        if (!reusableTicket) {
          const ticketsResponse = await presaleApi.tickets.list({
            page: 1,
            page_size: 50,
            opportunity_id: reviewTarget.id,
            status: Array.from(ACTIVE_SUPPORT_STATUSES).join(","),
          });
          reusableTicket = findReusablePresaleTicket(
            getTicketItems(ticketsResponse),
            ticketType,
          );
        }

        if (reusableTicket) {
          setShowReviewDialog(false);
          setReviewTarget(null);
          navigate(buildPresalesTicketBoardPath({
            ticketType,
            status: reusableTicket.status,
            leadId: reviewTarget.lead_id || reusableTicket.lead_id,
            opportunityId: reviewTarget.id,
            ticketId: reusableTicket.id,
          }));
          return;
        }
      }

      const payload = {
        title: reviewForm.title.trim(),
        ticket_type: ticketType,
        urgency: reviewForm.urgency,
        description:
          reviewForm.description?.trim() ||
          buildReviewDescription(reviewTarget) ||
          undefined,
        customer_id: reviewTarget.customer_id || undefined,
        customer_name: reviewTarget.customer_name || undefined,
        lead_id: reviewTarget.lead_id || undefined,
        opportunity_id: reviewTarget.id,
        expected_date: reviewForm.expected_date || undefined
      };
      const estimatedAmount = normalizeEstimatedAmountWan(reviewTarget.est_amount);
      if (estimatedAmount !== undefined) {
        payload.estimated_amount = estimatedAmount;
      }

      const response = await presaleApi.tickets.create(payload);
      const ticketId = unwrapTicketId(response);
      setShowReviewDialog(false);
      setReviewTarget(null);
      alert(
        ({
          [ASSESSMENT_TICKET_TYPE]: "技术评估已提交",
          [REVIEW_TICKET_TYPE]: "方案评审已提交",
        })[ticketType] || "售前支持已提交"
      );
      navigate(buildPresalesTicketBoardPath({
        ticketType,
        status: ticketType === REVIEW_TICKET_TYPE ? "REVIEW" : "PENDING",
        leadId: reviewTarget.lead_id,
        opportunityId: reviewTarget.id,
        ticketId,
      }));
    } catch (error) {
      console.error("提交售前支持失败:", error);
      alert(
        "提交售前支持失败: " +
        (error.response?.data?.detail || error.message)
      );
    } finally {
      setReviewSubmitting(false);
    }
  };

  // 查看详情
  const handleViewDetail = async (opp) => {
    try {
      const response = await opportunityApi.get(opp.id);
      if (response.data) {
        setSelectedOpp(response.data);
        setShowDetailDialog(true);
      }
    } catch (error) {
      console.error("加载商机详情失败:", error);
      setSelectedOpp(opp);
      setShowDetailDialog(true);
    }
  };

  const handleDetailSave = async () => {
    if (!selectedOpp || !detailForm) {return;}
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
        requirement: requirementPayload
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
      console.error("更新商机详情失败:", error);
      alert(
        "更新商机详情失败: " + (error.response?.data?.detail || error.message)
      );
    } finally {
      setDetailSaving(false);
    }
  };

  const stats = useMemo(() => {
    return {
      total: total,
      discovery: (opportunities || []).filter((o) => o.stage === "DISCOVERY").length,
      proposal: (opportunities || []).filter((o) => o.stage === "PROPOSAL").length,
      won: (opportunities || []).filter((o) => o.stage === "WON").length,
      totalAmount: (opportunities || []).reduce(
        (sum, o) => sum + (parseFloat(o.est_amount) || 0),
        0
      )
    };
  }, [opportunities, total]);

  const detailData = detailEditing && detailForm ? detailForm : selectedOpp;

  const handleOpenGate = (opp) => {
    setSelectedOpp(opp);
    setShowGateDialog(true);
  };

  return (
    <div className="space-y-6 p-6">
      {!embedded ? (
        <PageHeader
          title="商机管理"
          description="管理销售商机，跟踪项目进展"
          action={
            <Button onClick={() => setShowCreateDialog(true)}>
              <Plus className="mr-2 h-4 w-4" />
              新建商机
            </Button>
          }
        />
      ) : null}


      {/* 统计卡片 */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">总商机数</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
              <Target className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">需求澄清</p>
                <p className="text-2xl font-bold text-white">
                  {stats.discovery}
                </p>
              </div>
              <Clock className="h-8 w-8 text-blue-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">报价中</p>
                <p className="text-2xl font-bold text-white">
                  {stats.proposal}
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-amber-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div>
                <p className="text-sm text-slate-400">预估金额</p>
                <p className="text-2xl font-bold text-white">
                  {(stats.totalAmount / 10000).toFixed(1)}万
                </p>
              </div>
              <DollarSign className="h-8 w-8 text-emerald-400" />
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Pipeline Mini Funnel */}
      <Card>
        <CardContent className="p-4">
          <div className="flex items-center gap-2 mb-3">
            <TrendingUp className="w-4 h-4 text-blue-400" />
            <span className="text-sm font-medium text-white">销售漏斗概览</span>
          </div>
          <div className="flex items-center gap-1">
            {["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION", "CLOSING", "WON"].map((stage, idx) => {
              const count = (opportunities || []).filter((o) => o.stage === stage).length;
              const conf = stageConfig[stage] || {};
              const maxCount = Math.max(1, ...(["DISCOVERY", "QUALIFICATION", "PROPOSAL", "NEGOTIATION", "CLOSING", "WON"].map(
                (s) => (opportunities || []).filter((o) => o.stage === s).length
              )));
              return (
                <div key={stage} className="flex-1 group cursor-pointer" onClick={() => setStageFilter(stageFilter === stage ? "all" : stage)}>
                  <div className="text-center mb-1">
                    <div className="text-xs text-slate-500">{conf.label || stage}</div>
                    <div className={cn("text-lg font-bold", conf.textColor || "text-white")}>{count}</div>
                  </div>
                  <div className={cn("h-2 rounded-full transition-all", stageFilter === stage ? "ring-2 ring-white/30" : "", conf.color || "bg-slate-600")} style={{ opacity: Math.max(0.3, count / maxCount) }} />
                  {idx < 5 && <div className="hidden md:flex justify-center mt-1"><ArrowRight className="w-3 h-3 text-slate-600" /></div>}
                </div>
              );
            })}
          </div>
        </CardContent>
      </Card>

      {/* 筛选栏 */}
      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col md:flex-row gap-4 items-center">
            <div className="flex-1 relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 h-4 w-4 text-slate-400" />
              <Input
                placeholder="搜索商机编码、名称..."
                value={searchTerm || "unknown"}
                onChange={(e) => setSearchTerm(e.target.value)}
                className="pl-10" />

            </div>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline">
                  <Filter className="mr-2 h-4 w-4" />
                  阶段:{" "}
                  {stageFilter === "all" ?
                  "全部" :
                  stageConfig[stageFilter]?.label}
                </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent>
              <DropdownMenuItem onClick={() => setStageFilter("all")}>
                全部
              </DropdownMenuItem>
              {Object.entries(stageConfig).map(([key, config]) =>
                <DropdownMenuItem
                  key={key}
                  onClick={() => setStageFilter(key)}>

                    {config.label}
                </DropdownMenuItem>
                )}
            </DropdownMenuContent>
          </DropdownMenu>
          <div className="flex gap-2">
            <select
              value={customerFilter || "unknown"}
              onChange={(e) => setCustomerFilter(e.target.value)}
              className="px-3 py-1 border rounded text-sm bg-slate-900 text-slate-300"
            >
              <option value="all">客户: 全部</option>
              {(customers || []).map((customer) => (
                <option key={customer.id} value={customer.id}>
                  {customer.customer_name}
                </option>
              ))}
            </select>
            <select
              value={ownerFilter || "unknown"}
              onChange={(e) => setOwnerFilter(e.target.value)}
              className="px-3 py-1 border rounded text-sm bg-slate-900 text-slate-300"
            >
              <option value="all">负责人: 全部</option>
              {(owners || []).map((owner) => (
                <option key={owner.id} value={owner.id}>
                  {owner.real_name || owner.username}
                </option>
              ))}
            </select>
            <Button
              variant={viewMode === "grid" ? "default" : "outline"}
              size="icon"
              onClick={() => setViewMode("grid")}
            >
              <LayoutGrid className="h-4 w-4" />
            </Button>
            <Button
              variant={viewMode === "list" ? "default" : "outline"}
              size="icon"
              onClick={() => setViewMode("list")}
            >
              <List className="h-4 w-4" />
            </Button>
          </div>
          </div>
        </CardContent>
      </Card>

      {/* 商机列表 */}
      {loading ?
      <div className="text-center py-12 text-slate-400">加载中...</div> :
      opportunities.length === 0 ?
      <Card>
          <CardContent className="p-12 text-center">
            <p className="text-slate-400">暂无商机数据</p>
          </CardContent>
      </Card> :

      (viewMode === "grid" ? (
        <OpportunityGrid
          opportunities={opportunities}
          stageUpdating={stageUpdating}
          onViewDetail={handleViewDetail}
          onEdit={handleEdit}
          onOpenGate={handleOpenGate}
          onStageChange={handleStageChange}
          onOpenReview={openPresaleSupportDialog}
        />
      ) : (
        <OpportunityTable
          opportunities={opportunities}
          stageUpdating={stageUpdating}
          onViewDetail={handleViewDetail}
          onEdit={handleEdit}
          onOpenGate={handleOpenGate}
          onStageChange={handleStageChange}
          onOpenReview={openPresaleSupportDialog}
        />
      ))
      }

      {/* 分页 */}
      {total > pageSize &&
      <div className="flex justify-center gap-2">
          <Button
          variant="outline"
          disabled={page === 1}
          onClick={() => setPage(page - 1)}>

            上一页
          </Button>
          <span className="flex items-center px-4 text-slate-400">
            第 {page} 页，共 {Math.ceil(total / pageSize)} 页
          </span>
          <Button
          variant="outline"
          disabled={page >= Math.ceil(total / pageSize)}
          onClick={() => setPage(page + 1)}>

            下一页
          </Button>
      </div>
      }

      {/* 创建商机对话框 */}
      <CreateDialog
        open={showCreateDialog}
        onOpenChange={(open) => {
          setShowCreateDialog(open);
          if (!open) setAutofillHint("");
        }}
        formData={formData}
        setFormData={setFormData}
        customers={customers}
        onCreate={handleCreate}
        autofillHint={autofillHint}
      />

      {/* 阶段门对话框 */}
      <GateDialog
        open={showGateDialog}
        onOpenChange={setShowGateDialog}
        gateData={gateData}
        setGateData={setGateData}
        onSubmitGate={handleSubmitGate}
      />

      {/* 详情对话框 */}
      <DetailDialog
        open={showDetailDialog}
        onOpenChange={setShowDetailDialog}
        selectedOpp={selectedOpp}
        detailEditing={detailEditing}
        setDetailEditing={setDetailEditing}
        detailForm={detailForm}
        setDetailForm={setDetailForm}
        detailSaving={detailSaving}
        detailData={detailData}
        buildDetailForm={buildDetailForm}
        onDetailSave={handleDetailSave}
      />

      {/* 方案评审申请对话框 */}
      <ReviewDialog
        open={showReviewDialog}
        onOpenChange={setShowReviewDialog}
        reviewForm={reviewForm}
        setReviewForm={setReviewForm}
        reviewSubmitting={reviewSubmitting}
        onCreateReviewTicket={handleCreateReviewTicket}
        onTicketTypeChange={handleReviewTicketTypeChange}
        canRequestSolutionReview={isGatePassed(reviewTarget?.gate_status)}
      />
    </div>
  );
}
