import { useState, useCallback, useEffect, useMemo } from 'react';
import { shortageAlertApi } from '../../../services/api';

export function useShortageAlert() {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ level: '', status: '' });

    const loadAlerts = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.level && filters.level !== 'all') params.level = filters.level;
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            const response = await shortageAlertApi.list(params);
            setAlerts(response.data?.items || response.data || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [filters]);

    const acknowledge = useCallback(async (id) => {
        try { await shortageAlertApi.acknowledge(id); await loadAlerts(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadAlerts]);

    const stats = useMemo(() => ({
        total: alerts.length,
        critical: alerts.filter(a => a.level === 'critical').length,
        unresolved: alerts.filter(a => a.status !== 'resolved').length,
    }), [alerts]);

    useEffect(() => { loadAlerts(); }, [loadAlerts]);
    return { alerts, loading, error, filters, setFilters, stats, loadAlerts, acknowledge };
}
