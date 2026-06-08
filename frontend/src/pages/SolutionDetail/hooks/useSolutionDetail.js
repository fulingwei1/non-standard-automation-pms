import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { presaleApi } from "../../../services/api";

const defaultTechSpecs = {
    productInfo: {},
    capacity: { uph: 0, cycleTime: 0, dailyOutput: 0, channels: 0 },
    testItems: [],
    testStandards: [],
    environment: {},
    technicalParameters: [],
    rawText: "",
};

const technicalParameterLabels = {
    test_station_count: "测试工位数",
    cycle_time: "节拍时间",
    accuracy: "测试精度",
    fixture_qty: "夹具数量",
    channels: "测试通道",
    uph: "UPH",
    daily_output: "日产能",
    air_pressure: "气源压力",
    power_supply: "电源要求",
    communication: "通讯协议",
};

const technicalParameterUnits = {
    test_station_count: "个",
    cycle_time: "秒",
    fixture_qty: "套",
    channels: "通道",
    uph: "pcs/h",
    daily_output: "pcs",
    air_pressure: "MPa",
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

const avatarText = (name) => (name || "").trim().charAt(0);

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

const humanizeParameterKey = (key) =>
    String(key)
        .replace(/([a-z])([A-Z])/g, "$1 $2")
        .replace(/[_-]+/g, " ")
        .trim();

const normalizeTechnicalParameters = (parameters) => {
    const source = parseObject(parameters);
    if (!source) {
        return [];
    }

    return Object.entries(source)
        .map(([key, item]) => {
            const isObject = item && typeof item === "object" && !Array.isArray(item);
            const value = isObject
                ? item.value ?? item.default_value ?? item.default ?? item.amount
                : item;

            if (value === undefined || value === null || value === "") {
                return null;
            }

            const displayValue = Array.isArray(value) ? value.join("、") : String(value);

            return {
                key,
                label: isObject
                    ? item.label || technicalParameterLabels[key] || humanizeParameterKey(key)
                    : technicalParameterLabels[key] || humanizeParameterKey(key),
                value: displayValue,
                unit: isObject ? item.unit || technicalParameterUnits[key] || "" : technicalParameterUnits[key] || "",
            };
        })
        .filter(Boolean);
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
        technicalParameters: normalizeTechnicalParameters(solutionData.template_parameters),
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

const normalizeReviewStatus = (status) => {
    const normalized = (status || "").toLowerCase();

    if (["approved", "pass", "passed"].includes(normalized)) {
        return "approved";
    }

    if (["review", "pending", "submitted"].includes(normalized)) {
        return "pending";
    }

    if (["rejected", "reject"].includes(normalized)) {
        return "rejected";
    }

    return normalized || "pending";
};

const normalizeSolutionStatus = (solutionData) => {
    const status = (solutionData.status || "").toLowerCase();
    const rawReviewStatus = (solutionData.review_status || "").toLowerCase();
    const reviewStatus = normalizeReviewStatus(solutionData.review_status);

    if (["published", "archived"].includes(status)) {
        return status;
    }

    if (["approved", "rejected"].includes(reviewStatus)) {
        return reviewStatus;
    }

    if (["review", "pending", "submitted"].includes(rawReviewStatus)) {
        return "review";
    }

    return status || "draft";
};

const buildReviews = (solutionData) => {
    const hasReview =
        solutionData.review_status ||
        solutionData.review_comment ||
        solutionData.review_time ||
        solutionData.reviewer_name ||
        solutionData.reviewer_id;

    if (!hasReview) {
        return [];
    }

    const reviewer =
        solutionData.reviewer_name ||
        (solutionData.reviewer_id ? `评审人${solutionData.reviewer_id}` : "待评审");

    return [
        {
            id: `${solutionData.id}-review`,
            reviewer,
            avatar: avatarText(reviewer),
            date: solutionData.review_time || "",
            status: normalizeReviewStatus(solutionData.review_status || solutionData.status),
            comments: solutionData.review_comment || "",
        },
    ];
};

const addCollaborator = (collaborators, name, role) => {
    if (!name) {
        return;
    }

    const existing = collaborators.find((person) => person.name === name);
    if (existing) {
        if (!existing.role.split(" / ").includes(role)) {
            existing.role = `${existing.role} / ${role}`;
        }
        return;
    }

    collaborators.push({
        name,
        role,
        avatar: avatarText(name),
    });
};

const buildCollaborators = (solutionData) => {
    const collaborators = [];

    addCollaborator(collaborators, solutionData.author_name || solutionData.creator_name, "方案编制");
    addCollaborator(collaborators, solutionData.sales_person_name, "销售负责人");
    addCollaborator(collaborators, solutionData.reviewer_name, "方案评审");

    return collaborators;
};

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
                status: normalizeSolutionStatus(solutionData),
                deviceType: solutionData.solution_type?.toLowerCase() || "",
                deviceTypeName: solutionData.solution_type || "",
                progress: solutionData.progress || 0,
                amount: safeNumber(amountSource) / 10000,
                estimatedAmount: safeNumber(amountSource),
                estimatedCost: safeNumber(solutionData.estimated_cost),
                suggestedPrice: safeNumber(solutionData.suggested_price),
                estimatedHours: safeNumber(solutionData.estimated_hours),
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
                reviews: buildReviews(solutionData),
                collaborators: buildCollaborators(solutionData)
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
