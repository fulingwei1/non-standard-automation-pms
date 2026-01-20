import { useState, useCallback, useEffect } from 'react';
import { exceptionApi } from '../../../services/api';

/**
 * 异常管理数据 Hook
 */
export function useExceptionManagement() {
    const [exceptions, setExceptions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', type: '', severity: '' });

    const loadExceptions = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.severity && filters.severity !== 'all') params.severity = filters.severity;

            const response = await exceptionApi.list(params);
            setExceptions(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const reportException = useCallback(async (data) => {
        try {
            await exceptionApi.create(data);
            await loadExceptions();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadExceptions]);

    const resolveException = useCallback(async (id, resolution) => {
        try {
            await exceptionApi.resolve(id, { resolution });
            await loadExceptions();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadExceptions]);

    useEffect(() => { loadExceptions(); }, [loadExceptions]);

    return { exceptions, loading, error, filters, setFilters, loadExceptions, reportException, resolveException };
}
