import { useState, useCallback, useEffect } from 'react';
import { acceptanceApi } from '../../../services/api';

/**
 * 验收执行数据 Hook
 */
export function useAcceptanceExecution() {
    const [acceptances, setAcceptances] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', type: '' });

    const loadAcceptances = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;

            const response = await acceptanceApi.listExecutions(params);
            setAcceptances(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const startExecution = useCallback(async (id) => {
        try {
            await acceptanceApi.startExecution(id);
            await loadAcceptances();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadAcceptances]);

    const submitResult = useCallback(async (id, result) => {
        try {
            await acceptanceApi.submitResult(id, result);
            await loadAcceptances();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadAcceptances]);

    useEffect(() => { loadAcceptances(); }, [loadAcceptances]);

    return { acceptances, loading, error, filters, setFilters, loadAcceptances, startExecution, submitResult };
}
