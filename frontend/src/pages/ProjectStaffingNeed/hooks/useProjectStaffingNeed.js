import { useState, useCallback, useEffect } from 'react';
import { staffingApi } from '../../../services/api';

export function useProjectStaffingNeed() {
    const [needs, setNeeds] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', project_id: '' });

    const loadNeeds = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.project_id) params.project_id = filters.project_id;
            const response = await staffingApi.listNeeds(params);
            setNeeds(response.data?.items || response.data?.items || response.data || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [filters]);

    const assignStaff = useCallback(async (needId, staffId) => {
        try { await staffingApi.assign(needId, { staff_id: staffId }); await loadNeeds(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadNeeds]);

    useEffect(() => { loadNeeds(); }, [loadNeeds]);
    return { needs, loading, error, filters, setFilters, loadNeeds, assignStaff };
}
