import { useCallback, useEffect, useMemo, useState } from "react";
import { useNavigate, useSearchParams } from "react-router-dom";
import { Calculator, Lightbulb } from "lucide-react";

import { PageHeader } from "../components/layout";
import { Card, CardContent, CardHeader, CardTitle } from "../components/ui/card";
import { Button } from "../components/ui/button";
import { toast } from "../components/ui/toast";
import CostEstimateForm from "../components/presales/CostEstimateForm";
import { presaleApi } from "../services/api";

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

function toWan(value) {
  const amount = Number(value);
  if (!Number.isFinite(amount) || amount <= 0) {
    return 0;
  }
  return amount / 10000;
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
  const contextOpportunityId = searchParams.get("opportunity_id") || "";
  const contextProjectId = searchParams.get("project_id") || "";
  const contextTicketIdNumber = parseContextId(contextTicketId);
  const contextOpportunityIdNumber = parseContextId(contextOpportunityId);
  const contextProjectIdNumber = parseContextId(contextProjectId);

  const loadLinkedSolution = useCallback(async () => {
    if (
      explicitSolutionId ||
      (!contextTicketIdNumber && !contextOpportunityIdNumber && !contextProjectIdNumber)
    ) {
      setLinkedSolution(null);
      return;
    }

    const params = { page: 1, page_size: 1 };
    if (contextOpportunityIdNumber) {
      params.opportunity_id = contextOpportunityId;
    }
    if (contextTicketIdNumber) {
      params.ticket_id = contextTicketId;
    }
    if (contextProjectIdNumber) {
      params.project_id = contextProjectId;
    }

    setSolutionLoading(true);
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
        ticketId: contextTicketIdNumber || undefined,
        opportunityId: contextOpportunityIdNumber || undefined,
        projectId: contextProjectIdNumber || undefined,
        name: searchParams.get("name") || linkedSolution?.name || "售前技术方案",
        amount: queryAmount > 0 ? queryAmount : solutionAmount,
      };
    },
    [
      contextOpportunityIdNumber,
      contextProjectIdNumber,
      contextTicketIdNumber,
      explicitSolutionId,
      linkedSolution,
      searchParams,
    ],
  );

  const handleSave = async (result) => {
    try {
      if (bidding.id && result?.costData) {
        await presaleApi.solutions.update(Number(bidding.id), result.costData);
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
    navigate(embedded ? "/presales/technical-solutions?tab=cost" : "/presales/workbench");
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
              to: "/presales/technical-solutions",
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
          <div className="rounded-xl border border-white/5 bg-surface-100/60 px-4 py-3 text-sm text-slate-300">
            {solutionLoading
              ? "正在加载关联技术方案..."
              : bidding.amount > 0
                ? `当前预算参考：¥${bidding.amount}万`
                : "可直接填写成本项，系统会自动计算建议报价。"}
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
