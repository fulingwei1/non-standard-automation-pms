import { useState, useCallback, useEffect } from 'react';
import { projectSettlementApi } from '../../../services/api';

export function useProjectSettlement() {
    const [settlements, setSettlements] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', project_id: '' });

    const loadSettlements = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.project_id) params.project_id = filters.project_id;
            const response = await projectSettlementApi.list(params);
            setSettlements(response.data?.items || response.data?.items || response.data || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [filters]);

    const submitSettlement = useCallback(async (data) => {
        try { await projectSettlementApi.submit(data); await loadSettlements(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadSettlements]);

    useEffect(() => { loadSettlements(); }, [loadSettlements]);
    return { settlements, loading, error, filters, setFilters, loadSettlements, submitSettlement };
}
