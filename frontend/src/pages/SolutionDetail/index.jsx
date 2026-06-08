import { motion } from "framer-motion";
import { useLocation, useNavigate } from "react-router-dom";
import { FileText } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { staggerContainer, fadeIn } from "../../lib/animations";
import { useSolutionDetail } from "./hooks";
import {
    SolutionHeader,
    SolutionStatsCards,
    SolutionTabs,
    SolutionOverviewTab,
    SolutionSpecsTab,
    SolutionEquipmentTab,
    SolutionCostTab,
    SolutionDeliverablesTab,
    SolutionHistoryTab,
} from "./components";

function appendContextParam(params, key, value) {
    if (value !== undefined && value !== null && value !== "") {
        params.set(key, String(value));
    }
}

function getContextParam(params, snakeKey, camelKey) {
    return params.get(snakeKey) || params.get(camelKey) || "";
}

function buildFallbackSolutionListUrl(search) {
    const currentParams = new URLSearchParams(search);
    const ticketId = getContextParam(currentParams, "ticket_id", "ticketId");
    const leadId = getContextParam(currentParams, "lead_id", "leadId");
    const opportunityId = getContextParam(currentParams, "opportunity_id", "opportunityId");
    const projectId = getContextParam(currentParams, "project_id", "projectId");

    const params = new URLSearchParams();
    params.set("tab", "solutions");
    if (ticketId || leadId || opportunityId || projectId) {
        params.set("type", "support");
    }
    appendContextParam(params, "ticket_id", ticketId);
    appendContextParam(params, "lead_id", leadId);
    appendContextParam(params, "opportunity_id", opportunityId);
    appendContextParam(params, "project_id", projectId);

    return `/presales/technical-solutions?${params.toString()}`;
}

function getContextValue(solutionValue, currentParams, snakeKey, camelKey) {
    return solutionValue || getContextParam(currentParams, snakeKey, camelKey);
}

function buildCostEstimateUrl(solution, search = "") {
    const currentParams = new URLSearchParams(search);
    const params = new URLSearchParams();
    params.set("tab", "cost");
    appendContextParam(params, "solution_id", solution?.id);
    appendContextParam(
        params,
        "ticket_id",
        getContextValue(solution?.ticketId, currentParams, "ticket_id", "ticketId"),
    );
    appendContextParam(
        params,
        "lead_id",
        getContextValue(solution?.leadId, currentParams, "lead_id", "leadId"),
    );
    appendContextParam(
        params,
        "opportunity_id",
        getContextValue(solution?.opportunityId, currentParams, "opportunity_id", "opportunityId"),
    );
    appendContextParam(
        params,
        "project_id",
        getContextValue(solution?.projectId, currentParams, "project_id", "projectId"),
    );
    return `/presales/technical-solutions?${params.toString()}`;
}

function buildInitiationHandoffUrl(solution, search = "") {
    const currentParams = new URLSearchParams(search);
    const params = new URLSearchParams();
    params.set("handoff", "presale");

    appendContextParam(params, "solution_id", solution?.id);
    appendContextParam(
        params,
        "ticket_id",
        getContextValue(solution?.ticketId, currentParams, "ticket_id", "ticketId"),
    );
    appendContextParam(
        params,
        "lead_id",
        getContextValue(solution?.leadId, currentParams, "lead_id", "leadId"),
    );
    appendContextParam(
        params,
        "opportunity_id",
        getContextValue(solution?.opportunityId, currentParams, "opportunity_id", "opportunityId"),
    );
    appendContextParam(
        params,
        "project_id",
        getContextValue(solution?.projectId, currentParams, "project_id", "projectId"),
    );
    appendContextParam(params, "project_name", solution?.name);
    appendContextParam(params, "opportunity_name", solution?.opportunity);
    appendContextParam(params, "customer_name", solution?.customer);
    appendContextParam(
        params,
        "estimated_amount",
        solution?.suggestedPrice || solution?.estimatedAmount || solution?.estimatedCost,
    );
    appendContextParam(
        params,
        "requirement_summary",
        solution?.requirementSummary || solution?.description || solution?.solutionOverview,
    );
    appendContextParam(params, "estimated_hours", solution?.estimatedHours);

    return `/pmo/initiations?${params.toString()}`;
}

export default function SolutionDetail() {
    const navigate = useNavigate();
    const location = useLocation();
    const {
        activeTab,
        setActiveTab,
        solution,
        loading,
        error,
        costEstimate,
        submittingReview,
        reviewError,
        submitForReview,
    } = useSolutionDetail();

    if (loading) {
        return (
            <div className="space-y-6">
                <PageHeader title="方案详情" description="加载中..." />
                <div className="text-center py-16 text-slate-400">
                    <FileText className="w-12 h-12 mx-auto mb-4 text-slate-600 animate-pulse" />
                    <p className="text-lg font-medium">加载中...</p>
                </div>
            </div>
        );
    }

    if (error || !solution) {
        return (
            <div className="space-y-6">
                <PageHeader title="方案详情" description="加载失败" />
                <div className="text-center py-16 text-red-400">
                    <div className="text-lg font-medium">加载失败</div>
                    <div className="text-sm mt-2">{error || "方案不存在"}</div>
                    <Button className="mt-4" onClick={() => navigate(buildFallbackSolutionListUrl(location.search))}>
                        返回方案列表
                    </Button>
                </div>
            </div>
        );
    }

    return (
        <motion.div
            variants={staggerContainer}
            initial="hidden"
            animate="visible"
            className="space-y-6"
        >
            <SolutionHeader
                solution={solution}
                navigate={navigate}
                onSubmitReview={submitForReview}
                submittingReview={submittingReview}
                contextSearch={location.search}
                onCreateInitiation={(targetSolution) =>
                    navigate(buildInitiationHandoffUrl(targetSolution, location.search))
                }
            />

            {reviewError && (
                <div className="rounded-lg border border-red-500/20 bg-red-500/10 px-4 py-3 text-sm text-red-300">
                    {reviewError}
                </div>
            )}

            <SolutionStatsCards solution={solution} />

            <SolutionTabs activeTab={activeTab} setActiveTab={setActiveTab} />

            <motion.div variants={fadeIn}>
                {activeTab === "overview" && <SolutionOverviewTab solution={solution} />}
                {activeTab === "specs" && <SolutionSpecsTab solution={solution} />}
                {activeTab === "equipment" && <SolutionEquipmentTab solution={solution} />}
                {activeTab === "deliverables" && <SolutionDeliverablesTab solution={solution} />}
                {activeTab === "cost" && (
                    <SolutionCostTab
                        costEstimate={costEstimate}
                        solution={solution}
                        onCreateEstimate={(targetSolution) =>
                            navigate(buildCostEstimateUrl(targetSolution, location.search))
                        }
                    />
                )}
                {activeTab === "history" && <SolutionHistoryTab solution={solution} />}
            </motion.div>
        </motion.div>
    );
}
