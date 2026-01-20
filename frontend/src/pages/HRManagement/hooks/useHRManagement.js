import { useState, useCallback, useEffect } from 'react';
import { hrApi } from '../../../services/api';

export function useHRManagement() {
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ department: '', status: '', keyword: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadEmployees = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.department && filters.department !== 'all') params.department = filters.department;
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.keyword) params.keyword = filters.keyword;
            const response = await hrApi.listEmployees(params);
            const data = response.data || response;
            setEmployees(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [pagination.page, pagination.pageSize, filters]);

    useEffect(() => { loadEmployees(); }, [loadEmployees]);
    return { employees, loading, error, filters, setFilters, pagination, setPagination, loadEmployees };
}
