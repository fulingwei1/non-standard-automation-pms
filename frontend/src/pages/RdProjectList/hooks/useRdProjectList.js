import { useState, useCallback, useEffect } from 'react';
import { rdProjectApi } from '../../../services/api';

export function useRdProjectList() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', keyword: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadProjects = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.keyword) params.keyword = filters.keyword;
            const response = await rdProjectApi.list(params);
            const data = response.data || response;
            setProjects(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [pagination.page, pagination.pageSize, filters]);

    useEffect(() => { loadProjects(); }, [loadProjects]);
    return { projects, loading, error, filters, setFilters, pagination, setPagination, loadProjects };
}
