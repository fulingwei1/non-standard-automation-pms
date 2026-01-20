import { useState, useCallback, useEffect, useMemo } from 'react';
import { schedulerApi } from '../../../services/api';

export function useSchedulerMonitoringDashboard() {
    const [jobs, setJobs] = useState([]);
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            const [jobsRes, logsRes] = await Promise.all([
                schedulerApi.listJobs(),
                schedulerApi.getRecentLogs(),
            ]);
            setJobs(jobsRes.data || jobsRes || []);
            setLogs(logsRes.data || logsRes || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, []);

    const stats = useMemo(() => ({
        total: jobs.length,
        running: jobs.filter(j => j.status === 'running').length,
        failed: logs.filter(l => l.status === 'failed').length,
    }), [jobs, logs]);

    useEffect(() => { loadData(); }, [loadData]);
    return { jobs, logs, loading, error, stats, loadData };
}
