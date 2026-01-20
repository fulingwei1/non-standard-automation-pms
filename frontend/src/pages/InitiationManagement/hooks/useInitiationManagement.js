import { useState, useEffect, useCallback } from "react";
import { pmoApi } from "../../../services/api";
import { logger } from "../../../utils/logger";

export function useInitiationManagement() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [initiations, setInitiations] = useState([]);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(20);
    const [keyword, setKeyword] = useState("");
    const [statusFilter, setStatusFilter] = useState("");
    const [createDialogOpen, setCreateDialogOpen] = useState(false);

    const fetchData = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);
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
    }, [page, pageSize, keyword, statusFilter]);

    useEffect(() => {
        fetchData();
    }, [fetchData]);

    const handleCreate = async (formData) => {
        try {
            await pmoApi.initiations.create(formData);
            setCreateDialogOpen(false);
            fetchData();
            return true;
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
        handleCreate,
        handleSubmit,
        fetchData
    };
}
