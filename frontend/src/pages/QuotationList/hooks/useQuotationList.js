import { useState, useCallback, useEffect } from 'react';
import { quotationApi } from '../../../services/api';

/**
 * 报价单列表数据 Hook
 */
export function useQuotationList() {
    const [quotations, setQuotations] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', customer_id: '', keyword: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadQuotations = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.customer_id) params.customer_id = filters.customer_id;
            if (filters.keyword) params.keyword = filters.keyword;

            const response = await quotationApi.list(params);
            const data = response.data || response;
            setQuotations(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    const createQuotation = useCallback(async (data) => {
        try {
            await quotationApi.create(data);
            await loadQuotations();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadQuotations]);

    const duplicateQuotation = useCallback(async (id) => {
        try {
            await quotationApi.duplicate(id);
            await loadQuotations();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadQuotations]);

    useEffect(() => { loadQuotations(); }, [loadQuotations]);

    return { quotations, loading, error, filters, setFilters, pagination, setPagination, loadQuotations, createQuotation, duplicateQuotation };
}
