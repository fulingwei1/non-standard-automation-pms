import { useState, useCallback, useEffect } from 'react';
import { presaleApi as solutionApi } from '../../../services/api';

export function useSolutionList() {
    const [solutions, setSolutions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', keyword: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadSolutions = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.keyword) params.keyword = filters.keyword;
            const response = await solutionApi.list(params);
            const data = response.data || response;
            setSolutions(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [pagination.page, pagination.pageSize, filters]);

    useEffect(() => { loadSolutions(); }, [loadSolutions]);
    return { solutions, loading, error, filters, setFilters, pagination, setPagination, loadSolutions };
}
