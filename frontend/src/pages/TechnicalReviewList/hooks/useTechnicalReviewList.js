import { useState, useEffect, useCallback } from 'react';
import { technicalReviewApi, projectApi } from '../../../services/api';

export function useTechnicalReviewList() {
    const [loading, setLoading] = useState(true);
    const [reviews, setReviews] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(20);

    // 筛选条件
    const [searchKeyword, setSearchKeyword] = useState("");
    const [projectId, setProjectId] = useState(null);
    const [status, setStatus] = useState(null);
    const [reviewType, setReviewType] = useState(null);

    // 项目列表（用于筛选）
    const [projectList, setProjectList] = useState([]);

    // 对话框
    const [deleteDialog, setDeleteDialog] = useState({
        open: false,
        review: null,
    });

    const fetchProjectList = useCallback(async () => {
        try {
            const response = await projectApi.list({ page: 1, page_size: 100 });
            const projects = response.data?.items || response.items || [];
            setProjectList(projects);
        } catch (error) {
            console.error("Failed to fetch projects:", error);
        }
    }, []);

    const fetchReviews = useCallback(async () => {
        try {
            setLoading(true);
            const params = {
                page,
                page_size: pageSize,
            };
            if (searchKeyword) params.keyword = searchKeyword;
            if (projectId) params.project_id = projectId;
            if (status) params.status = status;
            if (reviewType) params.review_type = reviewType;

            const response = await technicalReviewApi.list(params);
            const data = response.data || response;
            setReviews(data.items || []);
            setTotal(data.total || 0);
        } catch (error) {
            console.error("Failed to fetch reviews:", error);
            setReviews([]);
        } finally {
            setLoading(false);
        }
    }, [page, pageSize, searchKeyword, projectId, status, reviewType]);

    useEffect(() => {
        fetchReviews();
        fetchProjectList();
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [page, projectId, status, reviewType]); // Keep original dependencies behavior

    const handleDelete = async () => {
        if (!deleteDialog.review) return;
        try {
            await technicalReviewApi.delete(deleteDialog.review.id);
            setDeleteDialog({ open: false, review: null });
            fetchReviews();
        } catch (error) {
            console.error("Failed to delete review:", error);
            alert("删除失败：" + (error.response?.data?.detail || error.message));
        }
    };

    const handleSearch = () => {
        setPage(1);
        fetchReviews();
    };

    const handleReset = () => {
        setSearchKeyword("");
        setProjectId(null);
        setStatus(null);
        setReviewType(null);
        setPage(1);
        // setTimeout not ideal, but we rely on useEffect deps or manual refetch
        // In React 18 auto-batching, this might update everything then trigger effect once
    };

    return {
        loading,
        reviews,
        total,
        page,
        setPage,
        pageSize,
        searchKeyword, setSearchKeyword,
        projectId, setProjectId,
        status, setStatus,
        reviewType, setReviewType,
        projectList,
        deleteDialog, setDeleteDialog,
        handleDelete,
        handleSearch,
        handleReset
    };
}
