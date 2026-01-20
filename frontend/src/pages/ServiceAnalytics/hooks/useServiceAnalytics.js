import { useState, useCallback, useEffect, useMemo } from 'react';
import { serviceAnalyticsApi } from '../../../services/api';

export function useServiceAnalytics() {
    const [data, setData] = useState({ tickets: [], satisfaction: [], performance: [] });
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [dateRange, setDateRange] = useState({ start: null, end: null });

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            const params = {};
            if (dateRange.start) params.start_date = dateRange.start;
            if (dateRange.end) params.end_date = dateRange.end;
            const response = await serviceAnalyticsApi.getData(params);
            setData(response.data || response || {});
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [dateRange]);

    const stats = useMemo(() => ({
        totalTickets: data.tickets?.length || 0,
        avgSatisfaction: data.satisfaction?.length > 0 ? (data.satisfaction.reduce((s, i) => s + i.score, 0) / data.satisfaction.length).toFixed(1) : 0,
        avgResponseTime: data.performance?.avgResponseTime || 0,
    }), [data]);

    useEffect(() => { loadData(); }, [loadData]);
    return { data, loading, error, dateRange, setDateRange, stats, loadData };
}
