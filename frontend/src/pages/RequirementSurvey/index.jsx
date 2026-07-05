/**
 * 需求调研管理
 * 管理客户需求调研记录、现场勘察、问题跟踪
 */
import { useState, useEffect, useCallback } from "react";
import { useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  ClipboardList,
  Search,
  Plus,
  Calendar,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import {
  Card,
  CardContent,
} from "../../components/ui/card";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Textarea } from "../../components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { presaleApi, presaleWorkbenchApi } from "../../services/api";
import { surveyMethods, surveyStatuses } from "./constants";
import { mapTicketTypeToMethod, mapTicketStatus } from "./utils";
import SurveyCard from "./SurveyCard";
import SurveyDetailPanel from "./SurveyDetailPanel";

function parseContextId(value) {
  if (!value) {
    return null;
  }

  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

const INITIAL_SURVEY_FORM = {
  title: "",
  ticket_type: "REQUIREMENT_RESEARCH",
  urgency: "NORMAL",
  customer_name: "",
  expected_date: "",
  description: "",
};

const surveyTaskTypes = [
  { value: "REQUIREMENT_RESEARCH", label: "需求调研" },
  { value: "TECHNICAL_EXCHANGE", label: "技术交流" },
  { value: "SITE_VISIT", label: "现场勘察" },
];

function getTicketItems(response) {
  const payload = response?.formatted ?? response?.data?.data ?? response?.data ?? response;
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  return [];
}

function parseJsonList(value) {
  if (Array.isArray(value)) {
    return value.filter(Boolean);
  }
  if (!value || typeof value !== "string") {
    return [];
  }
  try {
    const parsed = JSON.parse(value);
    if (Array.isArray(parsed)) {
      return parsed.filter(Boolean);
    }
    if (parsed && typeof parsed === "object") {
      return Object.values(parsed).filter(Boolean);
    }
  } catch {
    return value
      .split(/[、,，\n]/)
      .map((item) => item.trim())
      .filter(Boolean);
  }
  return [];
}

function buildRequirementSummary(detail = {}, ticket = {}) {
  const parts = [
    detail.target_object_type ? `被测对象：${detail.target_object_type}` : "",
    detail.application_scenario ? `应用场景：${detail.application_scenario}` : "",
    detail.cycle_time_seconds ? `节拍：${detail.cycle_time_seconds}s` : "",
    detail.workstation_count ? `工位：${detail.workstation_count}` : "",
    detail.acceptance_basis ? `验收依据：${detail.acceptance_basis}` : "",
    detail.special_notes ? `备注：${detail.special_notes}` : "",
  ].filter(Boolean);

  return parts.join("；") || ticket.description || "已沉淀结构化需求包";
}

function buildDocumentAttachments(detail = {}) {
  return [
    detail.has_sow ? { name: "客户 SOW / URS", size: "已提供", type: "document" } : null,
    detail.has_interface_doc ? { name: "接口协议文档", size: "已提供", type: "document" } : null,
    detail.has_drawing_doc ? { name: "图纸 / 原理 / IO 清单", size: "已提供", type: "document" } : null,
  ].filter(Boolean);
}

function getOpenItemTitle(item = {}) {
  return (
    item.item_title ||
    item.title ||
    item.description ||
    item.item_code ||
    item.code ||
    ""
  );
}

function mapTicketToSurvey(ticket) {
  const method = mapTicketTypeToMethod(ticket.ticket_type);
  const methodConfig =
    (surveyMethods || []).find((m) => m.id === method) || surveyMethods[0];
  const leadId = ticket.lead_id || ticket.leadId || null;
  return {
    id: ticket.id,
    code: ticket.ticket_no || `SUR-${ticket.id}`,
    customer: ticket.customer_name || "",
    customerId: ticket.customer_id,
    contactPerson: ticket.applicant_name || "",
    contactPhone: "",
    method,
    methodName: methodConfig.name,
    status: mapTicketStatus(ticket.status),
    scheduledDate: ticket.expected_date || ticket.apply_time || "",
    completedDate: ticket.complete_time || null,
    location: ticket.description || "",
    engineer: ticket.assignee_name || ticket.owner_name || "",
    salesPerson: ticket.applicant_name || "",
    opportunity: ticket.opportunity_name || "",
    opportunityId: ticket.opportunity_id,
    leadId,
    requirementDetailPath: leadId ? `/sales/leads/${leadId}/requirement` : "",
    summary: ticket.description || ticket.requirement || "",
    productInfo: null,
    testRequirements: [],
    capacityRequirements: null,
    siteConditions: null,
    budget: "",
    timeline: ticket.deadline || "",
    competitors: [],
    pendingQuestions: [],
    attachments: [],
    comments: 0,
  };
}

function buildRequirementPackageSurvey(context) {
  const detail = context?.assessment?.requirementDetail;
  if (!detail) {
    return null;
  }

  const ticket = context?.ticket || {};
  const leadId = detail.lead_id || ticket.lead_id || null;
  const testRequirements = [
    ...parseJsonList(detail.requirement_items),
    ...parseJsonList(detail.technical_spec),
  ].map((item) => String(item));
  const pendingQuestions = (context?.collaboration?.openItems?.items || [])
    .map(getOpenItemTitle)
    .filter(Boolean);

  return {
    id: `requirement-detail-${detail.id}`,
    code: detail.requirement_version || `REQ-${detail.id}`,
    customer:
      ticket.customer_name ||
      (detail.target_object_type ? `需求包：${detail.target_object_type}` : "结构化需求包"),
    customerId: ticket.customer_id,
    contactPerson: ticket.applicant_name || "",
    contactPhone: "",
    method: "onsite",
    methodName: surveyMethods[0]?.name || "现场调研",
    status: detail.is_frozen ? "completed" : "in_progress",
    scheduledDate: detail.updated_at || detail.created_at || ticket.apply_time || "",
    completedDate: detail.frozen_at || null,
    location: detail.customer_factory_location || ticket.description || "",
    engineer: ticket.assignee_name || ticket.owner_name || "",
    salesPerson: ticket.applicant_name || "",
    opportunity: ticket.opportunity_name || "",
    opportunityId: ticket.opportunity_id,
    leadId,
    requirementDetailPath: leadId ? `/sales/leads/${leadId}/requirement` : "",
    summary: buildRequirementSummary(detail, ticket),
    productInfo: detail.target_object_type
      ? {
        name: detail.target_object_type,
        model: detail.application_scenario || "待确认",
        size: detail.delivery_mode || "待确认",
        material: detail.acceptance_method || "待确认",
      }
      : null,
    testRequirements,
    capacityRequirements:
      detail.cycle_time_seconds || detail.workstation_count
        ? {
          annual: 0,
          daily: detail.workstation_count || 0,
          uph: detail.cycle_time_seconds
            ? Math.round((3600 / Number(detail.cycle_time_seconds)) * (detail.workstation_count || 1))
            : 0,
        }
        : null,
    siteConditions: detail.customer_factory_location
      ? {
        area: detail.customer_factory_location,
        power: "待确认",
        airPressure: "待确认",
        environment: "待确认",
      }
      : null,
    budget: "",
    timeline: detail.expected_delivery_date || ticket.deadline || "",
    competitors: [],
    pendingQuestions,
    attachments: buildDocumentAttachments(detail),
    comments: pendingQuestions.length,
  };
}

export default function RequirementSurvey({ embedded = false }) {
  const [searchParams] = useSearchParams();
  const contextLeadId = searchParams.get("lead_id") || "";
  const contextTicketId = searchParams.get("ticket_id") || "";
  const contextOpportunityId = searchParams.get("opportunity_id") || "";
  const contextProjectId = searchParams.get("project_id") || "";
  const contextLeadIdNumber = parseContextId(contextLeadId);
  const contextTicketIdNumber = parseContextId(contextTicketId);
  const contextOpportunityIdNumber = parseContextId(contextOpportunityId);
  const contextProjectIdNumber = parseContextId(contextProjectId);
  const contextSourceType = contextLeadIdNumber
    ? "lead"
    : contextOpportunityIdNumber
      ? "opportunity"
      : "";
  const contextSourceId = contextLeadIdNumber || contextOpportunityIdNumber;
  const hasBusinessContext =
    Boolean(contextLeadIdNumber) ||
    Boolean(contextOpportunityIdNumber) ||
    Boolean(contextProjectIdNumber);
  const [selectedStatus, setSelectedStatus] = useState("all");
  const [selectedMethod, setSelectedMethod] = useState("all");
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedSurvey, setSelectedSurvey] = useState(null);
  const [surveys, setSurveys] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createForm, setCreateForm] = useState(INITIAL_SURVEY_FORM);
  const [isCreating, setIsCreating] = useState(false);

  // Load surveys from API
  const loadSurveys = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const params = {
        page: 1,
        page_size: 100,
        ticket_type: "REQUIREMENT_RESEARCH,TECHNICAL_EXCHANGE,SITE_VISIT",
      };

      if (selectedStatus !== "all") {
        const statusMap = {
          scheduled: "PENDING,ACCEPTED",
          in_progress: "IN_PROGRESS",
          completed: "COMPLETED",
          cancelled: "CANCELLED",
        };
        params.status = statusMap[selectedStatus] || selectedStatus;
      }

      if (searchTerm) {
        params.keyword = searchTerm;
      }
      if (contextLeadIdNumber) {
        params.lead_id = contextLeadId;
      }
      if (contextOpportunityIdNumber) {
        params.opportunity_id = contextOpportunityId;
      }
      if (contextTicketIdNumber && !hasBusinessContext) {
        params.ticket_id = contextTicketId;
      }
      if (contextProjectIdNumber) {
        params.project_id = contextProjectId;
      }

      let contextSurvey = null;
      if (contextSourceType && contextSourceId) {
        try {
          const contextParams = {
            sourceType: contextSourceType,
            sourceId: contextSourceId,
          };
          if (contextTicketIdNumber) {
            contextParams.presaleTicketId = contextTicketIdNumber;
          }
          const context = await presaleWorkbenchApi.loadContext(contextParams);
          contextSurvey = buildRequirementPackageSurvey(context);
        } catch (contextError) {
          console.warn("加载售前需求聚合上下文失败:", contextError);
        }
      }

      const response = await presaleApi.tickets.list(params);
      const ticketsData = getTicketItems(response);

      // Transform tickets to surveys
      const transformedSurveys = [
        contextSurvey,
        ...(ticketsData || []).map(mapTicketToSurvey),
      ].filter(Boolean);

      setSurveys(transformedSurveys);
    } catch (err) {
      console.error("Failed to load surveys:", err);
      setError(err.response?.data?.detail || err.message || "加载调研记录失败");
      setSurveys([]);
    } finally {
      setLoading(false);
    }
  }, [
    contextLeadId,
    contextLeadIdNumber,
    contextOpportunityId,
    contextOpportunityIdNumber,
    contextProjectId,
    contextProjectIdNumber,
    contextSourceId,
    contextSourceType,
    contextTicketId,
    contextTicketIdNumber,
    hasBusinessContext,
    selectedStatus,
    searchTerm,
  ]);

  useEffect(() => {
    loadSurveys();
  }, [loadSurveys]);

  const updateCreateForm = (field, value) => {
    setCreateForm((prev) => ({ ...prev, [field]: value }));
  };

  const resetCreateForm = () => {
    setCreateForm(INITIAL_SURVEY_FORM);
  };

  const handleCreateSurvey = async (event) => {
    event?.preventDefault();

    const title = createForm.title.trim();
    if (!title) {
      alert("请输入调研标题");
      return;
    }

    const payload = {
      title,
      ticket_type: createForm.ticket_type,
      urgency: createForm.urgency,
    };

    const optionalFields = ["customer_name", "expected_date", "description"];
    optionalFields.forEach((field) => {
      const value = (createForm[field] || "").trim();
      if (value) {
        payload[field] = value;
      }
    });

    if (contextLeadIdNumber) {
      payload.lead_id = contextLeadIdNumber;
    }
    if (contextOpportunityIdNumber) {
      payload.opportunity_id = contextOpportunityIdNumber;
    }
    if (contextProjectIdNumber) {
      payload.project_id = contextProjectIdNumber;
    }

    try {
      setIsCreating(true);
      await presaleApi.tickets.create(payload);
      setShowCreateDialog(false);
      resetCreateForm();
      await loadSurveys();
      alert("调研工单已创建");
    } catch (err) {
      console.error("Failed to create requirement survey:", err);
      const message = err.response?.data?.detail || err.message || "未知错误";
      alert(`创建调研失败：${message}`);
    } finally {
      setIsCreating(false);
    }
  };

  // 筛选调研记录
  const filteredSurveys = (surveys || []).filter((survey) => {
    const matchesStatus =
      selectedStatus === "all" || survey.status === selectedStatus;
    const matchesMethod =
      selectedMethod === "all" || survey.method === selectedMethod;
    const searchLower = searchTerm.toLowerCase();
    const matchesSearch =
      (survey.customer || "").toLowerCase().includes(searchLower) ||
      (survey.opportunity || "").toLowerCase().includes(searchLower) ||
      (survey.code || "").toLowerCase().includes(searchLower);
    return matchesStatus && matchesMethod && matchesSearch;
  });

  // 统计数据
  const stats = {
    total: surveys.length,
    scheduled: (surveys || []).filter((s) => s.status === "scheduled").length,
    completed: (surveys || []).filter((s) => s.status === "completed").length,
    pendingQuestions: (surveys || []).reduce(
      (acc, s) => acc + s.pendingQuestions?.length,
      0,
    ),
  };

  const createSurveyButton = (
    <Button
      className="flex items-center gap-2"
      onClick={() => setShowCreateDialog(true)}
    >
      <Plus className="w-4 h-4" />
      新建调研
    </Button>
  );

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {!embedded && (
        <PageHeader
          title="需求调研"
          description="管理客户需求调研记录、现场勘察、问题跟踪"
          actions={
            <motion.div variants={fadeIn} className="flex gap-2">
              {createSurveyButton}
            </motion.div>
          }
        />
      )}

      {embedded && (
        <motion.div variants={fadeIn} className="flex justify-end">
          {createSurveyButton}
        </motion.div>
      )}

      {/* 统计卡片 */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 sm:grid-cols-4 gap-4"
      >
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-slate-500/10 flex items-center justify-center">
                <ClipboardList className="w-5 h-5 text-slate-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">全部调研</p>
                <p className="text-2xl font-bold text-white">{stats.total}</p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-blue-500/10 flex items-center justify-center">
                <Calendar className="w-5 h-5 text-blue-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">已排期</p>
                <p className="text-2xl font-bold text-blue-400">
                  {stats.scheduled}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-emerald-500/10 flex items-center justify-center">
                <CheckCircle className="w-5 h-5 text-emerald-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">已完成</p>
                <p className="text-2xl font-bold text-emerald-400">
                  {stats.completed}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
        <Card className="bg-surface-100/50 backdrop-blur-lg border border-white/5">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="w-10 h-10 rounded-lg bg-amber-500/10 flex items-center justify-center">
                <AlertTriangle className="w-5 h-5 text-amber-400" />
              </div>
              <div>
                <p className="text-xs text-slate-500">待确认问题</p>
                <p className="text-2xl font-bold text-amber-400">
                  {stats.pendingQuestions}
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* 工具栏 */}
      <motion.div
        variants={fadeIn}
        className="bg-surface-100/50 backdrop-blur-lg rounded-xl border border-white/5 shadow-lg p-4"
      >
        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          {/* 搜索 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              type="text"
              placeholder="搜索客户、商机、调研编号..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-full"
            />
          </div>

          {/* 筛选 */}
          <div className="flex items-center gap-3 flex-wrap">
            <select
              value={selectedStatus}
              onChange={(e) => setSelectedStatus(e.target.value)}
              className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {(surveyStatuses || []).map((status) => (
                <option key={status.id} value={status.id}>
                  {status.name}
                </option>
              ))}
            </select>
            <select
              value={selectedMethod}
              onChange={(e) => setSelectedMethod(e.target.value)}
              className="bg-surface-50 border border-white/10 rounded-md px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              <option value="all">全部方式</option>
              {(surveyMethods || []).map((method) => (
                <option key={method.id} value={method.id}>
                  {method.name}
                </option>
              ))}
            </select>
          </div>
        </div>
      </motion.div>

      {/* 加载状态 */}
      {loading && (
        <div className="text-center py-16 text-slate-400">
          <ClipboardList className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
          <p className="text-lg font-medium">加载中...</p>
        </div>
      )}

      {/* 错误提示 */}
      {error && !loading && (
        <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
        </div>
      )}

      {/* 调研列表 */}
      {!loading && !error && (
        <motion.div
          variants={fadeIn}
          className="grid grid-cols-1 md:grid-cols-2 xl:grid-cols-3 gap-4"
        >
          {filteredSurveys.length > 0 ? (
            (filteredSurveys || []).map((survey) => (
              <SurveyCard
                key={survey.id}
                survey={survey}
                onClick={setSelectedSurvey}
              />
            ))
          ) : (
            <div className="col-span-full text-center py-16 text-slate-400">
              <ClipboardList className="w-12 h-12 mx-auto mb-4 text-slate-600" />
              <p className="text-lg font-medium">暂无调研记录</p>
              <p className="text-sm">请调整筛选条件或创建新调研</p>
            </div>
          )}
        </motion.div>
      )}

      {/* 调研详情面板 */}
      {selectedSurvey && (
        <SurveyDetailPanel
          survey={selectedSurvey}
          onClose={() => setSelectedSurvey(null)}
        />
      )}

      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-xl">
          <form onSubmit={handleCreateSurvey}>
            <DialogHeader>
              <DialogTitle>新建调研</DialogTitle>
              <DialogDescription>
                从当前售前上下文创建需求调研工单
              </DialogDescription>
            </DialogHeader>

            <div className="px-6 py-4 space-y-4">
              <div className="space-y-2">
                <Label htmlFor="requirement-survey-title">调研标题</Label>
                <Input
                  id="requirement-survey-title"
                  value={createForm.title}
                  onChange={(event) =>
                    updateCreateForm("title", event.target.value)
                  }
                  placeholder="请输入调研标题"
                />
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="requirement-survey-type">调研类型</Label>
                  <select
                    id="requirement-survey-type"
                    value={createForm.ticket_type}
                    onChange={(event) =>
                      updateCreateForm("ticket_type", event.target.value)
                    }
                    className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                  >
                    {surveyTaskTypes.map((type) => (
                      <option key={type.value} value={type.value}>
                        {type.label}
                      </option>
                    ))}
                  </select>
                </div>

                <div className="space-y-2">
                  <Label htmlFor="requirement-survey-urgency">紧急程度</Label>
                  <select
                    id="requirement-survey-urgency"
                    value={createForm.urgency}
                    onChange={(event) =>
                      updateCreateForm("urgency", event.target.value)
                    }
                    className="w-full rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-white focus:outline-none focus:border-primary/50 focus:ring-2 focus:ring-primary/20"
                  >
                    <option value="NORMAL">普通</option>
                    <option value="URGENT">紧急</option>
                    <option value="VERY_URGENT">非常紧急</option>
                  </select>
                </div>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="requirement-survey-customer">客户名称</Label>
                  <Input
                    id="requirement-survey-customer"
                    value={createForm.customer_name}
                    onChange={(event) =>
                      updateCreateForm("customer_name", event.target.value)
                    }
                    placeholder="可选"
                  />
                </div>

                <div className="space-y-2">
                  <Label htmlFor="requirement-survey-expected-date">
                    期望调研日期
                  </Label>
                  <Input
                    id="requirement-survey-expected-date"
                    type="date"
                    value={createForm.expected_date}
                    onChange={(event) =>
                      updateCreateForm("expected_date", event.target.value)
                    }
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label htmlFor="requirement-survey-description">调研说明</Label>
                <Textarea
                  id="requirement-survey-description"
                  rows={4}
                  value={createForm.description}
                  onChange={(event) =>
                    updateCreateForm("description", event.target.value)
                  }
                  placeholder="补充调研背景、现场条件或待确认问题"
                />
              </div>
            </div>

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
                disabled={isCreating}
              >
                取消
              </Button>
              <Button type="submit" disabled={isCreating}>
                {isCreating ? "创建中..." : "创建调研"}
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </motion.div>
  );
}
