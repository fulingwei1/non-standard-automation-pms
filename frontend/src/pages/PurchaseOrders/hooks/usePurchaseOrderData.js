import { useState, useCallback, useEffect } from 'react';
import { purchaseOrderApi } from '../../../services/api';

/**
 * 采购订单数据管理 Hook
 */
export function usePurchaseOrderData() {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [pagination, setPagination] = useState({
        page: 1,
        pageSize: 20,
        total: 0,
    });
    const [filters, setFilters] = useState({
        keyword: '',
        status: '',
        supplier_id: '',
    });

    // 加载订单列表
    const loadOrders = useCallback(async () => {
        try {
            setLoading(true);
            const params = {
                page: pagination.page,
                page_size: pagination.pageSize,
            };

            if (filters.keyword) params.keyword = filters.keyword;
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.supplier_id) params.supplier_id = filters.supplier_id;

            const response = await purchaseOrderApi.list(params);
            const data = response.data || response;

            setOrders(data.items || data || []);
            if (data.total !== undefined) {
                setPagination(prev => ({ ...prev, total: data.total }));
            }
        } catch (err) {
            console.error('Failed to load purchase orders:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    // 创建订单
    const createOrder = useCallback(async (data) => {
        try {
            await purchaseOrderApi.create(data);
            await loadOrders();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadOrders]);

    // 更新订单
    const updateOrder = useCallback(async (id, data) => {
        try {
            await purchaseOrderApi.update(id, data);
            await loadOrders();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadOrders]);

    // 提交订单
    const submitOrder = useCallback(async (id) => {
        try {
            await purchaseOrderApi.submit(id);
            await loadOrders();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadOrders]);

    // 取消订单
    const cancelOrder = useCallback(async (id) => {
        try {
            await purchaseOrderApi.cancel(id);
            await loadOrders();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadOrders]);

    useEffect(() => {
        loadOrders();
    }, [loadOrders]);

    return {
        orders,
        loading,
        error,
        pagination,
        setPagination,
        filters,
        setFilters,
        loadOrders,
        createOrder,
        updateOrder,
        submitOrder,
        cancelOrder,
    };
}
