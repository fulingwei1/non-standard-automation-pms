import { useState, useCallback, useEffect } from 'react';
import { paymentApi } from '../../../services/api';

/**
 * 付款管理数据 Hook
 */
export function usePaymentData() {
    const [payments, setPayments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });
    const [filters, setFilters] = useState({ keyword: '', status: '', type: '' });

    const loadPayments = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.keyword) params.keyword = filters.keyword;
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;

            const response = await paymentApi.list(params);
            const data = response.data || response;
            setPayments(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    const createPayment = useCallback(async (data) => {
        try {
            await paymentApi.create(data);
            await loadPayments();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadPayments]);

    const approvePayment = useCallback(async (id) => {
        try {
            await paymentApi.approve(id);
            await loadPayments();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadPayments]);

    useEffect(() => { loadPayments(); }, [loadPayments]);

    return { payments, loading, error, pagination, setPagination, filters, setFilters, loadPayments, createPayment, approvePayment };
}
