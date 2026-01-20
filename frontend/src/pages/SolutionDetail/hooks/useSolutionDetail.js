import { useState, useEffect, useCallback } from "react";
import { useParams } from "react-router-dom";
import { presaleApi } from "../../../services/api";

export function useSolutionDetail() {
    const { id } = useParams();
    const [activeTab, setActiveTab] = useState("overview");
    const [solution, setSolution] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [costEstimate, setCostEstimate] = useState(null);

    const loadSolution = useCallback(async () => {
        if (!id) return;

        try {
            setLoading(true);
            setError(null);

            // Load solution detail
            const solutionResponse = await presaleApi.solutions.get(id);
            const solutionData = solutionResponse.data;

            // Load cost estimate if available
            let costData = null;
            try {
                const costResponse = await presaleApi.solutions.getCost(id);
                costData = costResponse.data;
            } catch (_err) {
                // Cost estimate may not exist, ignore error
            }

            // Transform solution data
            const transformedSolution = {
                id: solutionData.id,
                code: solutionData.solution_no || `SOL-${solutionData.id}`,
                name: solutionData.name || "",
                customer: solutionData.customer_name || "",
                customerId: solutionData.customer_id,
                version: solutionData.version || "V1.0",
                status: solutionData.status?.toLowerCase() || "draft",
                deviceType: solutionData.solution_type?.toLowerCase() || "",
                deviceTypeName: solutionData.solution_type || "",
                progress: solutionData.progress || 0,
                amount: solutionData.estimated_cost
                    ? solutionData.estimated_cost / 10000
                    : solutionData.suggested_price
                        ? solutionData.suggested_price / 10000
                        : 0,
                deadline: solutionData.deadline || "",
                createdAt: solutionData.created_at || "",
                updatedAt: solutionData.updated_at || solutionData.created_at || "",
                creator: solutionData.creator_name || "",
                opportunity: solutionData.opportunity_name || "",
                opportunityId: solutionData.opportunity_id,
                salesPerson: solutionData.sales_person_name || "",
                tags: solutionData.tags || [],
                description: solutionData.description || "",
                techSpecs: solutionData.tech_specs || {},
                equipment: solutionData.equipment || {},
                deliverables: solutionData.deliverables || [],
                versionHistory: [], // These seem to be placeholders or missing from API transformation in original
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
        loadSolution
    };
}
