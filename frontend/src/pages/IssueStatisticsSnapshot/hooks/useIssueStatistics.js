import { useState, useCallback, useEffect, useMemo } from 'react';
import { issueApi } from '../../../services/api';

/**
 * 问题统计快照数据 Hook
 */
export function useIssueStatistics() {
    const [issues, setIssues] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [dateRange, setDateRange] = useState({ start: null, end: null });

    const loadIssues = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 200 };
            if (dateRange.start) params.start_date = dateRange.start;
            if (dateRange.end) params.end_date = dateRange.end;

            const response = await issueApi.list(params);
            setIssues(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [dateRange]);

    const stats = useMemo(() => ({
        total: issues.length,
        open: issues.filter(i => i.status === 'open').length,
        resolved: issues.filter(i => i.status === 'resolved').length,
        byType: issues.reduce((acc, i) => { acc[i.type] = (acc[i.type] || 0) + 1; return acc; }, {}),
        bySeverity: issues.reduce((acc, i) => { acc[i.severity] = (acc[i.severity] || 0) + 1; return acc; }, {}),
    }), [issues]);

    useEffect(() => { loadIssues(); }, [loadIssues]);

    return { issues, loading, error, dateRange, setDateRange, stats, loadIssues };
}
