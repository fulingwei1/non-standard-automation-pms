import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { presaleApi } from "../../../services/api";

const defaultTechSpecs = {
    productInfo: {},
    capacity: { uph: 0, cycleTime: 0, dailyOutput: 0, channels: 0 },
    testItems: [],
    testStandards: [],
    environment: {},
    rawText: "",
};

const unwrapResponse = (response) => {
    if (response?.formatted !== undefined) {
        return response.formatted;
    }

    const data = response?.data;
    if (
        data &&
        typeof data === "object" &&
        "data" in data &&
        ("code" in data || "success" in data)
    ) {
        return data.data;
    }

    return data ?? response;
};

const safeNumber = (value) => {
    const number = Number(value);
    return Number.isFinite(number) ? number : 0;
};

const parseObject = (value) => {
    if (!value) {
        return null;
    }

    if (typeof value === "object" && !Array.isArray(value)) {
        return value;
    }

    if (typeof value === "string") {
        try {
            const parsed = JSON.parse(value);
            return parsed && typeof parsed === "object" && !Array.isArray(parsed)
                ? parsed
                : null;
        } catch {
            return null;
        }
    }

    return null;
};

const unwrapListResponse = (response) => {
    const data = unwrapResponse(response);

    if (Array.isArray(data)) {
        return data;
    }

    if (Array.isArray(data?.items)) {
        return data.items;
    }

    if (Array.isArray(data?.data)) {
        return data.data;
    }

    return [];
};

const normalizeTechSpecs = (solutionData) => {
    const source =
        parseObject(solutionData.tech_specs) ||
        parseObject(solutionData.technical_specs) ||
        parseObject(solutionData.technical_spec) ||
        {};

    return {
        productInfo: source.productInfo || source.product_info || {},
        capacity: {
            ...defaultTechSpecs.capacity,
            ...(source.capacity || {}),
        },
        testItems: source.testItems || source.test_items || [],
        testStandards: source.testStandards || source.test_standards || [],
        environment: source.environment || {},
        rawText:
            source.rawText ||
            source.raw_text ||
            (typeof solutionData.technical_spec === "string"
                ? solutionData.technical_spec
                : ""),
    };
};

const normalizeVersionHistory = (versions, currentSolutionId) =>
    versions.map((version) => ({
        id: version.id,
        version: version.version || version.solution_no || "",
        date: version.updated_at || version.created_at || version.review_time || "",
        author: version.author_name || version.creator_name || version.reviewer_name || "",
        changes:
            version.review_comment ||
            version.solution_overview ||
            version.requirement_summary ||
            version.description ||
            "",
        status: (version.status || version.review_status || "").toLowerCase(),
        current: Number(version.id) === Number(currentSolutionId),
    }));

export function useSolutionDetail() {
    const { id } = useParams();
    const [activeTab, setActiveTab] = useState("overview");
    const [solution, setSolution] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [costEstimate, setCostEstimate] = useState(null);
    const [submittingReview, setSubmittingReview] = useState(false);
    const [reviewError, setReviewError] = useState(null);

    const loadSolution = useCallback(async () => {
        if (!id) return;

        try {
            setLoading(true);
            setError(null);

            // Load solution detail
            const solutionResponse = await presaleApi.solutions.get(id);
            const solutionData = unwrapResponse(solutionResponse) || {};

            // Load cost estimate if available
            let costData = null;
            try {
                const costResponse = await presaleApi.solutions.getCost(id);
                costData = unwrapResponse(costResponse);
            } catch (_err) {
                // Cost estimate may not exist, ignore error
            }

            let versions = [];
            try {
                const versionsResponse = await presaleApi.solutions.getVersions(id);
                versions = unwrapListResponse(versionsResponse);
            } catch (_err) {
                // Version history may not be available, ignore error
            }

            const amountSource =
                solutionData.suggested_price != null
                    ? solutionData.suggested_price
                    : solutionData.estimated_cost;

            // Transform solution data
            const transformedSolution = {
                id: solutionData.id,
                code: solutionData.solution_no || `SOL-${solutionData.id}`,
                name: solutionData.name || "",
                customer: solutionData.customer_name || "",
                customerId: solutionData.customer_id,
                version: solutionData.version || "V1.0",
                status: (solutionData.status || solutionData.review_status)?.toLowerCase() || "draft",
                deviceType: solutionData.solution_type?.toLowerCase() || "",
                deviceTypeName: solutionData.solution_type || "",
                progress: solutionData.progress || 0,
                amount: safeNumber(amountSource) / 10000,
                deadline: solutionData.deadline || "",
                createdAt: solutionData.created_at || "",
                updatedAt: solutionData.updated_at || solutionData.created_at || "",
                creator: solutionData.creator_name || solutionData.author_name || "",
                opportunity: solutionData.opportunity_name || "",
                opportunityId: solutionData.opportunity_id,
                ticketId: solutionData.ticket_id,
                leadId: solutionData.lead_id,
                projectId: solutionData.project_id,
                salesPerson: solutionData.sales_person_name || "",
                tags: solutionData.tags || [],
                description:
                    solutionData.description ||
                    solutionData.solution_overview ||
                    solutionData.requirement_summary ||
                    "",
                requirementSummary: solutionData.requirement_summary || "",
                solutionOverview: solutionData.solution_overview || "",
                technicalSpec: solutionData.technical_spec || "",
                reviewStatus: solutionData.review_status || "",
                reviewComment: solutionData.review_comment || "",
                techSpecs: normalizeTechSpecs(solutionData),
                equipment: solutionData.equipment || {},
                deliverables: solutionData.deliverables || [],
                versionHistory: normalizeVersionHistory(versions, solutionData.id),
                reviews: [],
                collaborators: []
            };

            setSolution(transformedSolution);
            setCostEstimate(costData);
        } catch (err) {
            console.error("Failed to load solution:", err);
            setError(err.response?.data?.detail || err.message || "加载方案详情失败");
        } finally {
            setLoading(false);
        }
    }, [id]);

    const submitForReview = useCallback(async (comment = "提交评审") => {
        if (!id || submittingReview) {
            return;
        }

        try {
            setSubmittingReview(true);
            setReviewError(null);
            await presaleApi.solutions.review(id, {
                review_status: "REVIEW",
                review_comment: comment,
            });
            await loadSolution();
        } catch (err) {
            console.error("Failed to submit solution review:", err);
            const message = err.response?.data?.detail || err.message || "提交评审失败";
            setReviewError(message);
            throw err;
        } finally {
            setSubmittingReview(false);
        }
    }, [id, loadSolution, submittingReview]);

    useEffect(() => {
        loadSolution();
    }, [loadSolution]);

    return {
        id,
        activeTab, setActiveTab,
        solution,
        loading,
        error,
        costEstimate,
        submittingReview,
        reviewError,
        loadSolution,
        submitForReview
    };
}
