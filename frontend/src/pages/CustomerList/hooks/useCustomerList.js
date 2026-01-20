import { useState, useCallback, useEffect } from 'react';
import { customerApi } from '../../../services/api';

/**
 * 客户列表数据 Hook
 */
export function useCustomerList() {
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ level: '', industry: '', keyword: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadCustomers = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.level && filters.level !== 'all') params.level = filters.level;
            if (filters.industry && filters.industry !== 'all') params.industry = filters.industry;
            if (filters.keyword) params.keyword = filters.keyword;

            const response = await customerApi.list(params);
            const data = response.data || response;
            setCustomers(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    const deleteCustomer = useCallback(async (id) => {
        try {
            await customerApi.delete(id);
            await loadCustomers();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadCustomers]);

    useEffect(() => { loadCustomers(); }, [loadCustomers]);

    return { customers, loading, error, filters, setFilters, pagination, setPagination, loadCustomers, deleteCustomer };
}
