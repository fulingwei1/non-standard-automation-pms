/**
 * 投标中心
 * 管理投标项目、技术标书、竞争分析
 */
import { useState, useEffect, useCallback } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Target,
  Search,
  Plus,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
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
import { biddingStages, mapTenderStatus } from "./constants";
import { StatsCards } from "./StatsCards";
import { BiddingKanban } from "./BiddingKanban";
import { BiddingDetailPanel } from "./BiddingDetailPanel";

function parseContextId(value) {
  if (!value) {
    return null;
  }

  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function appendContextParam(params, key, value) {
  if (value !== undefined && value !== null && value !== "") {
    params.set(key, String(value));
  }
}

function buildCostSupportUrl(bidding, contextType, fallbackContext = {}) {
  const params = new URLSearchParams();
  params.set("tab", "cost");
  const ticketId = bidding?.ticketId || fallbackContext.ticketId;
  const leadId = bidding?.leadId || fallbackContext.leadId;
  const opportunityId = bidding?.opportunityId || fallbackContext.opportunityId;
  const projectId = bidding?.projectId || fallbackContext.projectId;
  const amount = Number(bidding?.amount);
  if (
    contextType ||
    ticketId ||
    leadId ||
    opportunityId ||
    projectId
  ) {
    params.set("type", contextType || "support");
  }
  appendContextParam(params, "tender_id", bidding?.id);
  appendContextParam(params, "ticket_id", ticketId);
  appendContextParam(params, "lead_id", leadId);
  appendContextParam(params, "opportunity_id", opportunityId);
  appendContextParam(params, "project_id", projectId);
  appendContextParam(params, "solution_id", bidding?.solutionId);
  if (Number.isFinite(amount) && amount > 0) {
    appendContextParam(params, "amount", amount);
  }
  appendContextParam(params, "name", bidding?.name);

  return `/presales/technical-solutions?${params.toString()}`;
}

const INITIAL_TENDER_FORM = {
  tender_name: "",
  customer_name: "",
};

function extractTenderItems(response) {
  const payload = response?.formatted ?? response?.data?.data ?? response?.data ?? response;
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  return [];
}

function extractContextTenders(context) {
  return extractTenderItems(context?.tenders);
}

function mapTenderToBidding(tender) {
  const deadlineValue = tender.submission_deadline || tender.deadline;
  const deadline = deadlineValue ? new Date(deadlineValue) : null;
  const budgetAmount = Number(
    tender.budget ??
    tender.budget_amount ??
    tender.our_bid_amount ??
    tender.bid_amount ??
    0,
  );
  const now = new Date();
  const daysLeft = deadline ?
    Math.ceil((deadline - now) / (1000 * 60 * 60 * 24)) :
    0;

  return {
    id: tender.id,
    ticketId: tender.ticket_id,
    leadId: tender.lead_id,
    opportunityId: tender.opportunity_id,
    projectId: tender.project_id,
    solutionId: tender.solution_id,
    code: tender.tender_no || `BID-${tender.id}`,
    name: tender.tender_name || tender.project_name || "",
    customer: tender.customer_name || "",
    customerId: tender.customer_id,
    stage: mapTenderStatus(tender.status || tender.result),
    deadline: deadline ? deadline.toISOString().split("T")[0] : "",
    daysLeft: daysLeft > 0 ? daysLeft : 0,
    amount: Number.isFinite(budgetAmount) ? budgetAmount / 10000 : 0,
    engineer: tender.responsible_name || "",
    salesPerson: tender.sales_person_name || "",
    progress: tender.progress || 0,
    solution: tender.solution_id ? `SOL-${tender.solution_id}` : null,
    solutionName: tender.solution_name || null,
    techRequirements:
    tender.tech_requirements || tender.technical_requirements || tender.description || "",
    competitors: [],
    documents: [],
    timeline: [],
    notes: tender.notes || "",
    costSupport: {
      status: "none",
      requestedAt: null,
      requestedBy: null,
      estimatedCost: null,
      submittedAt: null,
      submittedBy: null
    }
  };
}

export default function BiddingCenter({ embedded = false } = {}) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const contextType = searchParams.get("type") || "";
  const contextLeadId = searchParams.get("lead_id") || "";
  const contextTicketId = searchParams.get("ticket_id") || "";
  const contextOpportunityId = searchParams.get("opportunity_id") || "";
  const contextProjectId = searchParams.get("project_id") || "";
  const contextLeadIdNumber = parseContextId(contextLeadId);
  const contextTicketIdNumber = parseContextId(contextTicketId);
  const contextOpportunityIdNumber = parseContextId(contextOpportunityId);
  const contextProjectIdNumber = parseContextId(contextProjectId);
  const contextSourceType = contextOpportunityIdNumber
    ? "opportunity"
    : contextLeadIdNumber
      ? "lead"
      : "";
  const contextSourceId = contextOpportunityIdNumber || contextLeadIdNumber;
  const [searchTerm, setSearchTerm] = useState("");
  const [selectedBidding, setSelectedBidding] = useState(null);
  const [biddings, setBiddings] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [showCreateDialog, setShowCreateDialog] = useState(false);
  const [createForm, setCreateForm] = useState(INITIAL_TENDER_FORM);
  const [createError, setCreateError] = useState("");
  const [creating, setCreating] = useState(false);

  // Load tenders from API
  const loadTenders = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

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
          const contextTenders = extractContextTenders(context);
          if (contextTenders.length > 0) {
            setBiddings(contextTenders.map(mapTenderToBidding));
            return;
          }
        } catch (contextError) {
          console.warn("加载售前投标聚合上下文失败:", contextError);
        }
      }

      const params = {
        page: 1,
        page_size: 100
      };

      if (searchTerm) {
        params.keyword = searchTerm;
      }
      if (contextLeadIdNumber) {
        params.lead_id = contextLeadId;
      }
      if (contextOpportunityIdNumber) {
        params.opportunity_id = contextOpportunityId;
      }
      if (contextTicketIdNumber) {
        params.ticket_id = contextTicketId;
      }
      if (contextProjectIdNumber) {
        params.project_id = contextProjectId;
      }

      const response = await presaleApi.tenders.list(params);
      const tendersData = extractTenderItems(response);
      const transformedTenders = (tendersData || []).map(mapTenderToBidding);

      setBiddings(transformedTenders);
    } catch (err) {
      console.error("Failed to load tenders:", err);
      setError(err.response?.data?.detail || err.message || "加载投标项目失败");
      setBiddings([]);
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
    searchTerm,
  ]);

  useEffect(() => {
    loadTenders();
  }, [loadTenders]);

  const updateCreateForm = (field, value) => {
    setCreateForm((previous) => ({ ...previous, [field]: value }));
  };

  const handleOpenCreate = () => {
    setCreateForm(INITIAL_TENDER_FORM);
    setCreateError("");
    setShowCreateDialog(true);
  };

  const handleCreateTender = async (event) => {
    event?.preventDefault();

    const tenderName = createForm.tender_name.trim();
    if (!tenderName) {
      setCreateError("请填写投标项目名称");
      return;
    }

    const payload = {
      tender_name: tenderName,
    };
    const customerName = createForm.customer_name.trim();
    if (customerName) {
      payload.customer_name = customerName;
    }
    if (contextLeadIdNumber) {
      payload.lead_id = contextLeadIdNumber;
    }
    if (contextOpportunityIdNumber) {
      payload.opportunity_id = contextOpportunityIdNumber;
    }
    if (contextTicketIdNumber) {
      payload.ticket_id = contextTicketIdNumber;
    }
    if (contextProjectIdNumber) {
      payload.project_id = contextProjectIdNumber;
    }

    try {
      setCreating(true);
      setCreateError("");
      await presaleApi.tenders.create(payload);
      setShowCreateDialog(false);
      setCreateForm(INITIAL_TENDER_FORM);
      await loadTenders();
      alert("投标记录已创建");
    } catch (err) {
      console.error("创建投标记录失败:", err);
      setCreateError(err.response?.data?.detail || err.message || "创建投标记录失败");
    } finally {
      setCreating(false);
    }
  };

  const handleRequestCostSupport = useCallback(
    (bidding) => {
      navigate(buildCostSupportUrl(bidding, contextType, {
        ticketId: contextTicketIdNumber,
        leadId: contextLeadIdNumber,
        opportunityId: contextOpportunityIdNumber,
        projectId: contextProjectIdNumber,
      }));
    },
    [
      contextLeadIdNumber,
      contextOpportunityIdNumber,
      contextProjectIdNumber,
      contextTicketIdNumber,
      contextType,
      navigate,
    ],
  );

  // 筛选投标
  const filteredBiddings = (biddings || []).filter((bidding) => {
    const searchLower = searchTerm.toLowerCase();
    const name = (bidding.name || "").toLowerCase();
    const customer = (bidding.customer || "").toLowerCase();
    const code = (bidding.code || "").toLowerCase();

    return (
      name.includes(searchLower) ||
      customer.includes(searchLower) ||
      code.includes(searchLower));

  });

  // 按阶段分组（看板视图）
  const biddingsByStage = (biddingStages || []).map((stage) => ({
    ...stage,
    biddings: (filteredBiddings || []).filter((b) => b.stage === stage.id)
  }));

  // 统计数据
  const stats = {
    total: biddings.length,
    active: (biddings || []).filter((b) => !["won", "lost"].includes(b.stage)).length,
    won: (biddings || []).filter((b) => b.stage === "won").length,
    totalAmount: biddings.
    filter((b) => b.stage === "won").
    reduce((acc, b) => acc + b.amount, 0)
  };

  const createTenderButton = (
    <Button className="flex items-center gap-2" onClick={handleOpenCreate}>
      <Plus className="w-4 h-4" />
      新建投标
    </Button>
  );

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* 页面头部 */}
      {!embedded && (
        <PageHeader
          title="投标中心"
          description="管理投标项目、技术标书、竞争分析"
          actions={
            <motion.div variants={fadeIn} className="flex gap-2">
              {createTenderButton}
            </motion.div>
          }
        />
      )}

      {embedded && (
        <motion.div variants={fadeIn} className="flex justify-end">
          {createTenderButton}
        </motion.div>
      )}

      {/* 统计卡片 */}
      <StatsCards stats={stats} />

      {/* 工具栏 */}
      <motion.div
        variants={fadeIn}
        className="bg-surface-100/50 backdrop-blur-lg rounded-xl border border-white/5 shadow-lg p-4">

        <div className="flex flex-col lg:flex-row justify-between items-start lg:items-center gap-4">
          {/* 搜索 */}
          <div className="relative flex-1 max-w-md">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              type="text"
              placeholder="搜索项目名称、客户、编号..."
              value={searchTerm || "unknown"}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 w-full" />

          </div>
        </div>
      </motion.div>

      {/* 加载状态 */}
      {loading &&
      <div className="text-center py-16 text-slate-400">
          <Target className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
          <p className="text-lg font-medium">加载中...</p>
      </div>
      }

      {/* 错误提示 */}
      {error && !loading &&
      <div className="bg-red-500/10 border border-red-500/30 rounded-lg p-4 text-red-400 text-sm">
          {error}
      </div>
      }

      {/* 看板视图 */}
      {!loading && !error &&
      <BiddingKanban
        biddingsByStage={biddingsByStage}
        onSelectBidding={setSelectedBidding} />

      }

      {/* 投标详情面板 */}
      {selectedBidding &&
      <BiddingDetailPanel
        bidding={selectedBidding}
        onRequestCostSupport={handleRequestCostSupport}
        onClose={() => setSelectedBidding(null)} />

      }
      <Dialog open={showCreateDialog} onOpenChange={setShowCreateDialog}>
        <DialogContent className="max-w-lg">
          <form onSubmit={handleCreateTender} className="space-y-4">
            <DialogHeader>
              <DialogTitle>新建投标</DialogTitle>
              <DialogDescription>从当前售前上下文创建投标记录</DialogDescription>
            </DialogHeader>

            <div className="space-y-2">
              <label htmlFor="tender_name" className="text-sm text-slate-300">
                投标项目名称
              </label>
              <Input
                id="tender_name"
                value={createForm.tender_name}
                onChange={(event) => updateCreateForm("tender_name", event.target.value)}
                placeholder="填写投标项目名称"
              />
            </div>

            <div className="space-y-2">
              <label htmlFor="customer_name" className="text-sm text-slate-300">
                招标单位
              </label>
              <Input
                id="customer_name"
                value={createForm.customer_name}
                onChange={(event) => updateCreateForm("customer_name", event.target.value)}
                placeholder="填写客户或招标单位"
              />
            </div>

            {createError && (
              <div className="rounded-lg border border-red-500/30 bg-red-500/10 px-3 py-2 text-sm text-red-200">
                {createError}
              </div>
            )}

            <DialogFooter>
              <Button
                type="button"
                variant="outline"
                onClick={() => setShowCreateDialog(false)}
                disabled={creating}
              >
                取消
              </Button>
              <Button type="submit" disabled={creating}>
                创建投标
              </Button>
            </DialogFooter>
          </form>
        </DialogContent>
      </Dialog>
    </motion.div>);

}
