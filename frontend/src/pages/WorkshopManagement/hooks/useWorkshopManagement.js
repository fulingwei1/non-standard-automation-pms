import { useState, useCallback, useEffect } from 'react';
import { workshopApi } from '../../../services/api';

export function useWorkshopManagement() {
    const [workshops, setWorkshops] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', type: '' });

    const loadWorkshops = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            const response = await workshopApi.list(params);
            setWorkshops(response.data?.items || response.data?.items || response.data || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [filters]);

    const createWorkshop = useCallback(async (data) => {
        try { await workshopApi.create(data); await loadWorkshops(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadWorkshops]);

    useEffect(() => { loadWorkshops(); }, [loadWorkshops]);
    return { workshops, loading, error, filters, setFilters, loadWorkshops, createWorkshop };
}
