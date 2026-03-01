import { useState, useCallback, useEffect } from 'react';
import { progressApi as dependencyApi } from '../../../services/api';

export function useDependencyCheck() {
    const [dependencies, setDependencies] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ project_id: '', status: '' });

    const loadDependencies = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.project_id) params.project_id = filters.project_id;
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            const response = await dependencyApi.list(params);
            setDependencies(response.data?.items || response.data?.items || response.data || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [filters]);

    const runCheck = useCallback(async (projectId) => {
        try {
            const response = await dependencyApi.check(projectId);
            await loadDependencies();
            return { success: true, data: response.data };
        }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadDependencies]);

    useEffect(() => { loadDependencies(); }, [loadDependencies]);
    return { dependencies, loading, error, filters, setFilters, loadDependencies, runCheck };
}
