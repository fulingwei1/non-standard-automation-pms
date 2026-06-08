import { useEffect, useMemo, useState } from "react";
import { useLocation, useNavigate, useParams } from "react-router-dom";
import { Plus } from "lucide-react";
import { PageHeader } from "../../components/layout/PageHeader";
import { Button } from "../../components/ui";
import { useInitiationManagement } from "./hooks";
import { presaleWorkbenchApi } from "../../services/api";
import {
    CreateInitiationDialog,
    InitiationFilter,
    InitiationList,
    ReviewInitiationDialog,
} from "./components";

function readNumberParam(searchParams, key) {
    const value = searchParams.get(key);
    if (!value) {
        return "";
    }
    const parsed = Number(value);
    return Number.isFinite(parsed) && parsed > 0 ? parsed : "";
}

function firstNonEmpty(...values) {
    return values.find((value) => value !== undefined && value !== null && value !== "") || "";
}

function getSourceFromSearch(searchParams) {
    const opportunityId = readNumberParam(searchParams, "opportunity_id");
    const leadId = readNumberParam(searchParams, "lead_id");
    if (opportunityId) {
        return { sourceType: "opportunity", sourceId: opportunityId };
    }
    if (leadId) {
        return { sourceType: "lead", sourceId: leadId };
    }
    return { sourceType: "", sourceId: "" };
}

function buildFallbackHandoffData(searchParams) {
    if (searchParams.get("handoff") !== "presale") {
        return null;
    }

    return {
        project_name: firstNonEmpty(
            searchParams.get("project_name"),
            searchParams.get("opportunity_name"),
        ),
        project_type: "NEW",
        customer_name: searchParams.get("customer_name") || "",
        contract_no: searchParams.get("contract_no") || "",
        contract_amount: firstNonEmpty(
            searchParams.get("contract_amount"),
            searchParams.get("estimated_amount"),
        ),
        technical_solution_id: readNumberParam(searchParams, "solution_id"),
        requirement_summary: searchParams.get("requirement_summary") || "",
        estimated_hours: readNumberParam(searchParams, "estimated_hours"),
    };
}

function pickPrimarySolution(context, fallbackSolutionId) {
    const baselineSolutionId = context?.costing?.baseline?.solution_id;
    const targetSolutionId = fallbackSolutionId || baselineSolutionId;
    const solutions = context?.solutions?.items || [];
    if (targetSolutionId) {
        const matchedSolution = solutions.find(
            (item) => Number(item?.id) === Number(targetSolutionId),
        );
        if (matchedSolution) {
            return matchedSolution;
        }
    }
    return solutions[0] || null;
}

function buildContextHandoffData(context, fallbackData) {
    const baseline = context?.costing?.baseline || {};
    const solution = pickPrimarySolution(context, fallbackData?.technical_solution_id);
    const ticket = context?.ticket || {};
    const requirementDetail = context?.assessment?.requirementDetail || {};
    const technicalRisks = context?.assessment?.risks?.items || [];
    const primaryRisk = technicalRisks[0] || {};

    return {
        ...fallbackData,
        project_name: firstNonEmpty(
            solution?.project_name,
            solution?.name,
            solution?.solution_name,
            ticket?.opportunity_name,
            ticket?.title,
            fallbackData?.project_name,
        ),
        customer_name: firstNonEmpty(
            solution?.customer_name,
            ticket?.customer_name,
            fallbackData?.customer_name,
        ),
        contract_amount: firstNonEmpty(
            baseline.suggested_price,
            baseline.estimated_cost,
            solution?.suggested_price,
            solution?.estimated_cost,
            ticket?.estimated_amount,
            ticket?.estimated_value,
            fallbackData?.contract_amount,
        ),
        technical_solution_id: firstNonEmpty(
            baseline.solution_id,
            solution?.id,
            fallbackData?.technical_solution_id,
        ),
        requirement_summary: firstNonEmpty(
            requirementDetail.requirement_summary,
            requirementDetail.requirement_description,
            solution?.requirement_summary,
            ticket?.description,
            fallbackData?.requirement_summary,
        ),
        estimated_hours: firstNonEmpty(
            solution?.estimated_hours,
            ticket?.estimated_hours,
            fallbackData?.estimated_hours,
        ),
        risk_assessment: firstNonEmpty(
            primaryRisk.risk_title,
            primaryRisk.risk_description,
            fallbackData?.risk_assessment,
        ),
    };
}

export default function InitiationManagement() {
    const navigate = useNavigate();
    const location = useLocation();
    const { id: initiationId } = useParams();
    const searchParams = useMemo(() => new URLSearchParams(location.search), [location.search]);
    const fallbackHandoffData = useMemo(
        () => buildFallbackHandoffData(searchParams),
        [searchParams],
    );
    const [handoffInitialData, setHandoffInitialData] = useState(fallbackHandoffData);
    const {
        loading,
        error,
        initiations,
        total,
        page, setPage,
        pageSize,
        keyword, setKeyword,
        statusFilter, setStatusFilter,
        createDialogOpen, setCreateDialogOpen,
        reviewDialogOpen, setReviewDialogOpen,
        reviewMode,
        reviewLoading,
        projectManagers,
        handleCreate,
        handleSubmit,
        openApproveDialog,
        openRejectDialog,
        handleReview,
        fetchData
    } = useInitiationManagement(initiationId);

    useEffect(() => {
        if (initiationId || !fallbackHandoffData) {
            setHandoffInitialData(null);
            return;
        }

        let cancelled = false;
        setHandoffInitialData(fallbackHandoffData);
        setCreateDialogOpen(true);

        const { sourceType, sourceId } = getSourceFromSearch(searchParams);
        if (!sourceType || !sourceId) {
            return () => {
                cancelled = true;
            };
        }

        presaleWorkbenchApi.loadContext({
            sourceType,
            sourceId,
            presaleTicketId: readNumberParam(searchParams, "ticket_id") || undefined,
        }).then((context) => {
            if (!cancelled) {
                setHandoffInitialData(buildContextHandoffData(context, fallbackHandoffData));
            }
        }).catch((err) => {
            console.warn("加载售前交接上下文失败:", err);
        });

        return () => {
            cancelled = true;
        };
    }, [fallbackHandoffData, initiationId, searchParams, setCreateDialogOpen]);

    const handleCreateInitiation = async (formData) => {
        const created = await handleCreate(formData);
        const createdId = created?.id || created?.data?.id;
        if (createdId && handoffInitialData) {
            navigate(`/pmo/initiations/${createdId}`);
        }
        return created;
    };

    return (
        <div>
            <PageHeader
                title="立项管理"
                description={initiationId ? "立项申请详情与评审管理" : "项目立项申请与评审管理"}
                action={
                    <Button onClick={() => setCreateDialogOpen(true)} className="gap-2">
                        <Plus className="h-4 w-4" />
                        新建申请
                    </Button>
                }
            />

            <InitiationFilter
                keyword={keyword}
                setKeyword={setKeyword}
                statusFilter={statusFilter}
                setStatusFilter={setStatusFilter}
            />

            <InitiationList
                loading={loading}
                error={error}
                initiations={initiations}
                total={total}
                page={page}
                pageSize={pageSize}
                setPage={setPage}
                onRetry={fetchData}
                onViewDetail={(id) => navigate(`/pmo/initiations/${id}`)}
                onViewProject={(id) => navigate(`/projects/${id}`)}
                onSubmitReview={handleSubmit}
                onApprove={openApproveDialog}
                onReject={openRejectDialog}
            />

            <CreateInitiationDialog
                open={createDialogOpen}
                onOpenChange={setCreateDialogOpen}
                onSubmit={handleCreateInitiation}
                initialData={handoffInitialData}
            />

            <ReviewInitiationDialog
                open={reviewDialogOpen}
                mode={reviewMode}
                projectManagers={projectManagers}
                loading={reviewLoading}
                onOpenChange={setReviewDialogOpen}
                onSubmit={handleReview}
            />
        </div>
    );
}
