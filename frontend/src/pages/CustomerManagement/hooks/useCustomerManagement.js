import { useState, useEffect, useCallback } from "react";
import { customerApi } from "../../../services/api";

import { confirmAction } from "@/lib/confirmAction";
export function useCustomerManagement() {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(false);
    const [total, setTotal] = useState(0);
    const [page, setPage] = useState(1);
    const [pageSize] = useState(20);

    // Filters
    const [searchKeyword, setSearchKeyword] = useState("");
    const [filterIndustry, setFilterIndustry] = useState("all");
    const [filterStatus, setFilterStatus] = useState("all");
    const [industries, setIndustries] = useState([]);

    // Dialogs
    const [showCreateDialog, setShowCreateDialog] = useState(false);
    const [showEditDialog, setShowEditDialog] = useState(false);
    const [showDetailDialog, setShowDetailDialog] = useState(false);
    const [show360Dialog, setShow360Dialog] = useState(false);

    // Selected Items
    const [selectedCustomer, setSelectedCustomer] = useState(null);
    const [editCustomer, setEditCustomer] = useState(null);
    const [customer360, setCustomer360] = useState(null);
    const [loading360, setLoading360] = useState(false);

    const loadCustomers = useCallback(async () => {
        setLoading(true);
        try {
            const params = {
                page,
                page_size: pageSize
            };
            if (searchKeyword) params.keyword = searchKeyword;
            if (filterIndustry !== "all") params.industry = filterIndustry;
            if (filterStatus !== "all") params.is_active = filterStatus === "active";

            const response = await customerApi.list(params);
            const data = response.data || response;
            setCustomers(data.items || []);
            setTotal(data.total || 0);

            // Extract industries
            const industrySet = new Set();
            (data.items || []).forEach((customer) => {
                if (customer.industry) {
                    industrySet.add(customer.industry);
                }
            });
            setIndustries(Array.from(industrySet).sort());
        } catch (error) {
            console.error("加载客户列表失败:", error);
            alert("加载客户列表失败: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading(false);
        }
    }, [page, pageSize, searchKeyword, filterIndustry, filterStatus]);

    useEffect(() => {
        loadCustomers();
    }, [loadCustomers]);

    const handleCreate = async (data) => {
        try {
            await customerApi.create(data);
            setShowCreateDialog(false);
            loadCustomers();
        } catch (error) {
            alert("创建客户失败: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleUpdate = async (id, data) => {
        try {
            await customerApi.update(id, data);
            setShowEditDialog(false);
            setEditCustomer(null);
            loadCustomers();
        } catch (error) {
            alert("更新客户失败: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleDelete = async (id) => {
        if (!await confirmAction("确定要删除此客户吗？")) return;
        try {
            await customerApi.delete(id);
            loadCustomers();
        } catch (error) {
            alert("删除客户失败: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleViewDetail = async (id) => {
        try {
            const response = await customerApi.get(id);
            setSelectedCustomer(response.data || response);
            setShowDetailDialog(true);
        } catch (error) {
            alert("获取客户详情失败: " + (error.response?.data?.detail || error.message));
        }
    };

    const handleView360 = async (id) => {
        try {
            setLoading360(true);
            const response = await customerApi.get360(id);
            setCustomer360(response.data || response);
            setShow360Dialog(true);
        } catch (error) {
            console.error("加载客户360失败", error);
            alert("加载客户360失败: " + (error.response?.data?.detail || error.message));
        } finally {
            setLoading360(false);
        }
    };

    const prepareEdit = async (id) => {
        try {
            const response = await customerApi.get(id);
            setEditCustomer(response.data || response);
            setShowEditDialog(true);
        } catch (error) {
            alert("获取客户信息失败: " + (error.response?.data?.detail || error.message));
        }
    };

    return {
        customers,
        loading,
        total,
        page, setPage,
        pageSize,
        industries,

        // Filters
        searchKeyword, setSearchKeyword,
        filterIndustry, setFilterIndustry,
        filterStatus, setFilterStatus,

        // Dialog States
        showCreateDialog, setShowCreateDialog,
        showEditDialog, setShowEditDialog,
        showDetailDialog, setShowDetailDialog,
        show360Dialog, setShow360Dialog,

        // Data
        selectedCustomer, setSelectedCustomer,
        editCustomer, setEditCustomer,
        customer360, setCustomer360,
        loading360,

        // Handlers
        handleCreate,
        handleUpdate,
        handleDelete,
        handleViewDetail,
        handleView360,
        prepareEdit,
        refresh: loadCustomers
    };
}