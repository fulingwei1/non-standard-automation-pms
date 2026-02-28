import { useState, useCallback, useEffect, useMemo } from 'react';
import { alertApi } from '../../../services/api';

/**
 * 告警中心数据 Hook
 */
export function useAlertCenter() {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ level: '', type: '', status: '' });

    const loadAlerts = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.level && filters.level !== 'all') params.level = filters.level;
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.status && filters.status !== 'all') params.status = filters.status;

            const response = await alertApi.list(params);
            setAlerts(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const acknowledgeAlert = useCallback(async (id) => {
        try {
            await alertApi.acknowledge(id);
            await loadAlerts();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadAlerts]);

    const resolveAlert = useCallback(async (id, resolution) => {
        try {
            await alertApi.resolve(id, { resolution });
            await loadAlerts();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadAlerts]);

    const stats = useMemo(() => ({
        total: alerts.length,
        critical: alerts.filter(a => a.level === 'critical').length,
        warning: alerts.filter(a => a.level === 'warning').length,
        unresolved: alerts.filter(a => a.status !== 'resolved').length,
    }), [alerts]);

    useEffect(() => { loadAlerts(); }, [loadAlerts]);

    return { alerts, loading, error, filters, setFilters, stats, loadAlerts, acknowledgeAlert, resolveAlert };
}
