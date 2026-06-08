import { useState, useEffect, useCallback } from "react";
import { pmoApi } from "../../../services/api";
import { logger } from "../../../utils/logger";

export function useInitiationManagement(detailId = null) {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [initiations, setInitiations] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(20);
    const [keyword, setKeyword] = useState("");
    const [statusFilter, setStatusFilter] = useState("");
    const [createDialogOpen, setCreateDialogOpen] = useState(false);
    const [reviewDialogOpen, setReviewDialogOpen] = useState(false);
    const [reviewMode, setReviewMode] = useState("approve");
    const [reviewTargetId, setReviewTargetId] = useState(null);
    const [reviewLoading, setReviewLoading] = useState(false);
    const [projectManagers, setProjectManagers] = useState([]);

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
            if (detailId) {
                const res = await pmoApi.initiations.get(detailId);
                const item = res?.data;
                setInitiations(item ? [item] : []);
                setTotal(item ? 1 : 0);
                return;
            }

            const params = {
                page,
                page_size: pageSize,
                keyword: keyword || undefined,
                status: statusFilter || undefined
            };
            const res = await pmoApi.initiations.list(params);
            const data = res.data;

            // Handle PaginatedResponse format
            if (data && typeof data === "object" && "items" in data) {
                const itemsArray = Array.isArray(data.items) ? data.items : [];
                setInitiations(itemsArray);
                setTotal(data.total || 0);
            } else if (Array.isArray(data)) {
                setInitiations(data);
                setTotal(data.length);
            } else {
                logger.warn("无法识别数据格式:", data);
                setInitiations([]);
                setTotal(0);
            }
        } catch (err) {
            logger.error("获取数据失败:", err);
            setError(err.response?.data?.detail || err.message || "加载数据失败");
            setInitiations([]);
            setTotal(0);
        } finally {
            setLoading(false);
        }
    }, [detailId, page, pageSize, keyword, statusFilter]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleCreate = async (formData) => {
        try {
            const response = await pmoApi.initiations.create(formData);
            const created = response?.data?.data ?? response?.data ?? response;
            setCreateDialogOpen(false);
            fetchData();
            return created || true;
        } catch (err) {
            console.error("Failed to create initiation:", err);
            alert("创建失败: " + (err.response?.data?.detail || err.message));
            return false;
        }
    };

    const handleSubmit = async (id) => {
        try {
            await pmoApi.initiations.submit(id);
            fetchData();
            return true;
        } catch (err) {
            console.error("Failed to submit initiation:", err);
            alert("提交失败: " + (err.response?.data?.detail || err.message));
            return false;
        }
    };

    const loadProjectManagers = useCallback(async () => {
        try {
            const res = await pmoApi.initiations.projectManagers();
            const data = res?.data || res || [];
            setProjectManagers(Array.isArray(data) ? data : []);
        } catch (err) {
            logger.warn("获取项目经理候选失败:", err);
            setProjectManagers([]);
        }
    }, []);

    const openApproveDialog = async (id) => {
        setReviewMode("approve");
        setReviewTargetId(id);
        await loadProjectManagers();
        setReviewDialogOpen(true);
    };

    const openRejectDialog = (id) => {
        setReviewMode("reject");
        setReviewTargetId(id);
        setReviewDialogOpen(true);
    };

    const handleReview = async (payload) => {
        if (!reviewTargetId) {
            return false;
        }

        try {
            setReviewLoading(true);
            if (reviewMode === "approve") {
                await pmoApi.initiations.approve(reviewTargetId, payload);
            } else {
                await pmoApi.initiations.reject(reviewTargetId, {
                    review_result: payload.review_result,
                });
            }
            setReviewDialogOpen(false);
            setReviewTargetId(null);
            fetchData();
            return true;
        } catch (err) {
            console.error("Failed to review initiation:", err);
            alert("评审失败: " + (err.response?.data?.detail || err.message));
            return false;
        } finally {
            setReviewLoading(false);
        }
    };

    return {
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
    };
}
