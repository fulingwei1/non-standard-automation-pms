import { useState, useCallback, useEffect, useMemo } from 'react';
import { ecnApi } from '../../../services/api';

export function useECNOverdueAlerts() {
    const [alerts, setAlerts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadAlerts = useCallback(async () => {
        try {
            setLoading(true);
            const response = await ecnApi.getOverdueAlerts();
            setAlerts(response.data || response || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, []);

    const stats = useMemo(() => ({
        total: alerts.length,
        critical: alerts.filter(a => a.days_overdue > 30).length,
        warning: alerts.filter(a => a.days_overdue <= 30 && a.days_overdue > 7).length,
    }), [alerts]);

    useEffect(() => { loadAlerts(); }, [loadAlerts]);
    return { alerts, loading, error, stats, loadAlerts };
}
