import { useState, useCallback, useEffect } from 'react';
import { workOrderApi } from '../../../services/api';

/**
 * 工单管理数据 Hook
 */
export function useWorkOrderManagement() {
    const [workOrders, setWorkOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', type: '', priority: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadWorkOrders = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.priority && filters.priority !== 'all') params.priority = filters.priority;

            const response = await workOrderApi.list(params);
            const data = response.data || response;
            setWorkOrders(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    const createWorkOrder = useCallback(async (data) => {
        try {
            await workOrderApi.create(data);
            await loadWorkOrders();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadWorkOrders]);

    const updateWorkOrderStatus = useCallback(async (id, status) => {
        try {
            await workOrderApi.updateStatus(id, { status });
            await loadWorkOrders();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadWorkOrders]);

    useEffect(() => { loadWorkOrders(); }, [loadWorkOrders]);

    return { workOrders, loading, error, filters, setFilters, pagination, setPagination, loadWorkOrders, createWorkOrder, updateWorkOrderStatus };
}
