import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Calculator, FileText, Lightbulb } from "lucide-react";

import { PageHeader } from "../components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { toast } from "../components/ui/toast";
import CostEstimateForm from "../components/presales/CostEstimateForm";
import { presaleApi, presaleWorkbenchApi } from "../services/api";

function parseAmount(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount) || amount < 0) {
    return 0;
  }
  return amount;
}

function parseContextId(value) {
  if (!value) {
    return null;
  }

  const parsed = Number(value);
  return Number.isInteger(parsed) && parsed > 0 ? parsed : null;
}

function extractFirstItem(response) {
  const payload = response?.data ?? response;
  if (Array.isArray(payload)) {
    return payload[0] || null;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items[0] || null;
  }
  if (Array.isArray(payload?.data?.items)) {
    return payload.data.items[0] || null;
  }
  return null;
}

function extractSolutionDetail(response) {
  const payload = response?.data ?? response;
  if (!payload) {
    return null;
  }
  if (
    typeof payload === "object" &&
    "data" in payload &&
    ("code" in payload || "success" in payload)
  ) {
    return payload.data || null;
  }
  return payload;
}

function extractContextSolution(context) {
  const baseline = context?.costing?.baseline;
  if (!baseline?.solution_id) {
    return null;
  }

  const solution = (context?.solutions?.items || []).find(
    (item) => Number(item?.id) === Number(baseline.solution_id),
  ) || {};

  return {
    ...solution,
    id: baseline.solution_id,
    name: baseline.solution_name || solution.name || solution.solution_name,
    solution_no: baseline.solution_no || solution.solution_no,
    estimated_cost: baseline.estimated_cost ?? solution.estimated_cost,
    suggested_price: baseline.suggested_price ?? solution.suggested_price,
    cost_breakdown: baseline.cost_breakdown ?? solution.cost_breakdown,
  };
}

function toWan(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount) || amount <= 0) {
    return 0;
  }
  return amount / 10000;
}

function buildTechnicalSolutionsPath(tab, searchParams) {
  const nextParams = new URLSearchParams(searchParams);
  nextParams.set("tab", tab);
  const query = nextParams.toString();
  return `/presales/technical-solutions${query ? `?${query}` : ""}`;
}

function buildSalesQuoteCreatePath(context) {
  const params = new URLSearchParams();
  [
    ["opportunity_id", context.opportunityId],
    ["customer_id", context.customerId],
    ["solution_id", context.solutionId],
    ["ticket_id", context.ticketId],
    ["project_id", context.projectId],
    ["lead_id", context.leadId],
  ].forEach(([key, value]) => {
    if (value) {
      params.set(key, String(value));
    }
  });

  return `/sales/quotes/create${params.toString() ? `?${params.toString()}` : ""}`;
}

export default function PresalesCostEstimation({ embedded = false } = {}) {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [linkedSolution, setLinkedSolution] = useState(null);
  const [solutionLoading, setSolutionLoading] = useState(false);

  const explicitSolutionId = parseContextId(
    searchParams.get("solution_id") || searchParams.get("id"),
  );
  const contextTicketId = searchParams.get("ticket_id") || "";
  const contextTenderId = searchParams.get("tender_id") || "";
  const contextLeadId = searchParams.get("lead_id") || "";
  const contextOpportunityId = searchParams.get("opportunity_id") || "";
  const contextProjectId = searchParams.get("project_id") || "";
  const contextTicketIdNumber = parseContextId(contextTicketId);
  const contextTenderIdNumber = parseContextId(contextTenderId);
  const contextLeadIdNumber = parseContextId(contextLeadId);
  const contextOpportunityIdNumber = parseContextId(contextOpportunityId);
  const contextProjectIdNumber = parseContextId(contextProjectId);

  const loadLinkedSolution = useCallback(async () => {
    if (explicitSolutionId) {
      setSolutionLoading(true);
      try {
        const response = await presaleApi.solutions.get(explicitSolutionId);
        setLinkedSolution(extractSolutionDetail(response));
      } catch (error) {
        console.error("加载关联方案失败:", error);
        setLinkedSolution(null);
        toast.error(error?.response?.data?.detail || "关联方案加载失败");
      } finally {
        setSolutionLoading(false);
      }
      return;
    }

    const sourceType = contextOpportunityIdNumber ? "opportunity" : "lead";
    const sourceId = contextOpportunityIdNumber || contextLeadIdNumber;
    const hasLookupContext = Boolean(
      contextTicketIdNumber ||
      contextLeadIdNumber ||
      contextOpportunityIdNumber ||
      contextProjectIdNumber,
    );

    if (!hasLookupContext) {
      setLinkedSolution(null);
      return;
    }

    setSolutionLoading(true);

    if (sourceId) {
      try {
        const context = await presaleWorkbenchApi.loadContext({
          sourceType,
          sourceId,
          presaleTicketId: contextTicketIdNumber || undefined,
        });
        const contextSolution = extractContextSolution(context);
        if (contextSolution) {
          setLinkedSolution(contextSolution);
          setSolutionLoading(false);
          return;
        }
      } catch (error) {
        console.error("加载售前聚合上下文失败:", error);
      }
    }

    const params = { page: 1, page_size: 1 };
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

    try {
      const response = await presaleApi.solutions.list(params);
      setLinkedSolution(extractFirstItem(response));
    } catch (error) {
      console.error("加载关联方案失败:", error);
      setLinkedSolution(null);
      toast.error(error?.response?.data?.detail || "关联方案加载失败");
    } finally {
      setSolutionLoading(false);
    }
  }, [
    contextLeadId,
    contextLeadIdNumber,
    contextOpportunityId,
    contextOpportunityIdNumber,
    contextProjectId,
    contextProjectIdNumber,
    contextTicketId,
    contextTicketIdNumber,
    explicitSolutionId,
  ]);

  useEffect(() => {
    loadLinkedSolution();
  }, [loadLinkedSolution]);

  const bidding = useMemo(
    () => {
      const queryAmount = parseAmount(searchParams.get("amount"));
      const solutionAmount = toWan(
        linkedSolution?.suggested_price || linkedSolution?.estimated_cost,
      );

      return {
        id: explicitSolutionId || linkedSolution?.id || undefined,
        tenderId: contextTenderIdNumber || undefined,
        ticketId: contextTicketIdNumber || undefined,
        leadId: contextLeadIdNumber || undefined,
        opportunityId: contextOpportunityIdNumber || undefined,
        projectId: contextProjectIdNumber || undefined,
        name: searchParams.get("name") || linkedSolution?.name || "售前技术方案",
        amount: queryAmount > 0 ? queryAmount : solutionAmount,
      };
    },
    [
      contextLeadIdNumber,
      contextOpportunityIdNumber,
      contextProjectIdNumber,
      contextTenderIdNumber,
      contextTicketIdNumber,
      explicitSolutionId,
      linkedSolution,
      searchParams,
    ],
  );

  const quoteContext = useMemo(() => {
    const solutionId = explicitSolutionId || parseContextId(linkedSolution?.id);
    const opportunityId =
      contextOpportunityIdNumber ||
      parseContextId(linkedSolution?.opportunity_id);
    const customerId =
      parseContextId(searchParams.get("customer_id")) ||
      parseContextId(linkedSolution?.customer_id);
    const ticketId =
      contextTicketIdNumber || parseContextId(linkedSolution?.ticket_id);

    return {
      solutionId,
      opportunityId,
      customerId,
      ticketId,
      projectId:
        contextProjectIdNumber || parseContextId(linkedSolution?.project_id),
      leadId: contextLeadIdNumber || parseContextId(linkedSolution?.lead_id),
    };
  }, [
    contextLeadIdNumber,
    contextOpportunityIdNumber,
    contextProjectIdNumber,
    contextTicketIdNumber,
    explicitSolutionId,
    linkedSolution,
    searchParams,
  ]);

  const quoteCreatePath = useMemo(
    () => buildSalesQuoteCreatePath(quoteContext),
    [quoteContext],
  );

  const handleCreateSalesQuote = () => {
    if (!quoteContext.solutionId) {
      toast.error("请先保存或选择技术方案后再生成销售报价");
      return;
    }
    if (!quoteContext.opportunityId) {
      toast.error("缺少商机，无法生成销售报价");
      return;
    }
    navigate(quoteCreatePath);
  };

  const appendSolutionContext = (payload) => {
    const nextPayload = { ...payload };

    if (bidding.leadId) {
      nextPayload.lead_id = bidding.leadId;
    }
    if (bidding.opportunityId) {
      nextPayload.opportunity_id = bidding.opportunityId;
    }
    if (bidding.ticketId) {
      nextPayload.ticket_id = bidding.ticketId;
    }
    if (bidding.projectId) {
      nextPayload.project_id = bidding.projectId;
    }

    return nextPayload;
  };

  const buildSolutionPayload = (costData) => {
    const payload = {
      name: bidding.name,
      solution_type: "CUSTOM",
      ...costData,
    };

    return appendSolutionContext(payload);
  };

  const buildSolutionUpdatePayload = (costData) => appendSolutionContext({ ...costData });

  const enrichCostDataWithContext = (costData = {}) => {
    if (!bidding.tenderId) {
      return costData;
    }

    return {
      ...costData,
      cost_breakdown: {
        ...(costData.cost_breakdown || {}),
        presale_context: {
          tender_id: bidding.tenderId,
          ticket_id: bidding.ticketId || null,
          lead_id: bidding.leadId || null,
          opportunity_id: bidding.opportunityId || null,
          project_id: bidding.projectId || null,
        },
      },
    };
  };

  const handleSave = async (result) => {
    try {
      const costData = result?.costData ? enrichCostDataWithContext(result.costData) : null;

      if (bidding.id && result?.costData) {
        await presaleApi.solutions.update(Number(bidding.id), buildSolutionUpdatePayload(costData));
      } else if (costData) {
        const response = await presaleApi.solutions.create(buildSolutionPayload(costData));
        setLinkedSolution(extractSolutionDetail(response));
      }

      if (result?.status === "submitted") {
        toast.success("成本估算已提交");
        return;
      }

      toast.success("成本估算草稿已保存");
    } catch (error) {
      console.error("保存成本估算失败:", error);
      toast.error(error?.response?.data?.detail || error?.message || "成本估算保存失败");
    }
  };

  const handleCancel = () => {
    navigate(embedded ? buildTechnicalSolutionsPath("cost", searchParams) : "/presales/workbench");
  };

  return (
    <div className="space-y-6">
      {!embedded && (
        <PageHeader
          title="成本估算"
          description="按技术方案拆分成本结构，输出建议报价与毛利参考。"
          actions={[
            {
              label: "查看技术方案",
              icon: Lightbulb,
              to: buildTechnicalSolutionsPath("solutions", searchParams),
              variant: "outline",
            },
          ]}
        />
      )}

      <Card className="bg-surface-1/50 border border-white/5">
        <CardHeader>
          <CardTitle className="flex items-center gap-2 text-white">
            <Calculator className="h-5 w-5 text-amber-300" />
            {bidding.name}
          </CardTitle>
        </CardHeader>
        <CardContent className="space-y-4">
          <div className="rounded-xl border border-white/5 bg-surface-100/60 px-4 py-3">
            <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
              <div className="text-sm text-slate-300">
                {solutionLoading
                  ? "正在加载关联技术方案..."
                  : bidding.amount > 0
                    ? `当前预算参考：¥${bidding.amount}万`
                    : "可直接填写成本项，系统会自动计算建议报价。"}
              </div>
              <Button
                type="button"
                size="sm"
                onClick={handleCreateSalesQuote}
                disabled={solutionLoading}
                className="w-full sm:w-auto"
              >
                <FileText className="h-4 w-4" />
                生成销售报价
              </Button>
            </div>
          </div>

          <CostEstimateForm
            bidding={bidding}
            onSave={handleSave}
            onCancel={handleCancel}
          />

          {!embedded && (
            <div className="flex justify-end">
              <Button variant="ghost" onClick={() => navigate("/presales/workbench")}>
                返回售前工作台
              </Button>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
