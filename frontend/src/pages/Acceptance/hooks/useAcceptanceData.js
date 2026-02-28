import { useState, useCallback, useEffect } from 'react';
import { acceptanceApi } from '../../../services/api';

/**
 * 验收管理数据 Hook
 */
export function useAcceptanceData() {
    const [acceptances, setAcceptances] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', project_id: '' });

    const loadAcceptances = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.project_id) params.project_id = filters.project_id;

            const response = await acceptanceApi.list(params);
            setAcceptances(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const createAcceptance = useCallback(async (data) => {
        try {
            await acceptanceApi.create(data);
            await loadAcceptances();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadAcceptances]);

    const submitAcceptance = useCallback(async (id, result) => {
        try {
            await acceptanceApi.submit(id, result);
            await loadAcceptances();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadAcceptances]);

    useEffect(() => { loadAcceptances(); }, [loadAcceptances]);

    return { acceptances, loading, error, filters, setFilters, loadAcceptances, createAcceptance, submitAcceptance };
}
