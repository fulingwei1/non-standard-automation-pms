import { useState, useCallback, useEffect } from 'react';
import { exceptionApi as productionExceptionApi } from '../../../services/api';

/**
 * 生产异常列表数据 Hook
 */
export function useProductionExceptionList() {
    const [exceptions, setExceptions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', type: '', project_id: '' });

    const loadExceptions = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.project_id) params.project_id = filters.project_id;

            const response = await productionExceptionApi.list(params);
            setExceptions(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const createException = useCallback(async (data) => {
        try {
            await productionExceptionApi.create(data);
            await loadExceptions();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadExceptions]);

    const resolveException = useCallback(async (id, resolution) => {
        try {
            await productionExceptionApi.resolve(id, resolution);
            await loadExceptions();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadExceptions]);

    useEffect(() => { loadExceptions(); }, [loadExceptions]);

    return { exceptions, loading, error, filters, setFilters, loadExceptions, createException, resolveException };
}
