import { useState, useCallback, useEffect, useMemo } from 'react';
import { itrApi as customerServiceApi } from '../../../services/api';

export function useCustomerServiceDashboard() {
    const [data, setData] = useState({ tickets: [], stats: {} });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            const response = await customerServiceApi.getDashboard();
            setData(response.data || response || {});
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, []);

    const stats = useMemo(() => ({
        total: data.tickets?.length || 0,
        open: data.tickets?.filter(t => t.status === 'open').length || 0,
        satisfaction: data.stats?.satisfaction || 0,
    }), [data]);

    useEffect(() => { loadData(); }, [loadData]);
    return { data, loading, error, stats, loadData };
}
