import { useState, useCallback, useEffect, useMemo } from 'react';
import { receivableApi } from '../../../services/api';

/**
 * 应收账款管理数据 Hook
 */
export function useReceivableManagement() {
    const [receivables, setReceivables] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', customer_id: '', overdue: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadReceivables = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.customer_id) params.customer_id = filters.customer_id;
            if (filters.overdue === 'true') params.overdue = true;

            const response = await receivableApi.list(params);
            const data = response.data || response;
            setReceivables(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    const recordPayment = useCallback(async (id, paymentData) => {
        try {
            await receivableApi.recordPayment(id, paymentData);
            await loadReceivables();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadReceivables]);

    const stats = useMemo(() => ({
        total: receivables.reduce((sum, r) => sum + (r.amount || 0), 0),
        received: receivables.reduce((sum, r) => sum + (r.received_amount || 0), 0),
        pending: receivables.reduce((sum, r) => sum + ((r.amount || 0) - (r.received_amount || 0)), 0),
        overdue: receivables.filter(r => r.is_overdue).reduce((sum, r) => sum + ((r.amount || 0) - (r.received_amount || 0)), 0),
    }), [receivables]);

    useEffect(() => { loadReceivables(); }, [loadReceivables]);

    return { receivables, loading, error, filters, setFilters, pagination, setPagination, stats, loadReceivables, recordPayment };
}
