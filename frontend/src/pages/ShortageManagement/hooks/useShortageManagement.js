import { useState, useCallback, useEffect } from 'react';
import { shortageApi } from '../../../services/api';

export function useShortageManagement() {
    const [shortages, setShortages] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', priority: '' });

    const loadShortages = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.priority && filters.priority !== 'all') params.priority = filters.priority;
            const response = await shortageApi.list(params);
            setShortages(response.data?.items || response.data || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [filters]);

    const resolveShortage = useCallback(async (id, resolution) => {
        try { await shortageApi.resolve(id, resolution); await loadShortages(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadShortages]);

    useEffect(() => { loadShortages(); }, [loadShortages]);
    return { shortages, loading, error, filters, setFilters, loadShortages, resolveShortage };
}
