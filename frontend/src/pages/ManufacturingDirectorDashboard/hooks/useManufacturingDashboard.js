import { useState, useCallback, useEffect, useMemo } from 'react';
import { projectApi, productionApi } from '../../../services/api';

/**
 * 制造总监仪表板数据 Hook
 */
export function useManufacturingDashboard() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [projects, setProjects] = useState([]);
    const [productionStats, setProductionStats] = useState(null);
    const [alerts, setAlerts] = useState([]);

    const loadDashboardData = useCallback(async () => {
        try {
            setLoading(true);
            const [projectsRes, statsRes, alertsRes] = await Promise.all([
                projectApi.list({ status: 'active', page_size: 50 }),
                productionApi.getStats(),
                productionApi.getAlerts(),
            ]);

            setProjects(projectsRes.data?.items || projectsRes.data || []);
            setProductionStats(statsRes.data || statsRes);
            setAlerts(alertsRes.data?.items || alertsRes.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const stats = useMemo(() => ({
        totalProjects: projects.length,
        inProduction: projects.filter(p => p.status === 'producing').length,
        delayed: projects.filter(p => p.is_delayed).length,
        completedThisMonth: projects.filter(p => p.status === 'completed').length,
    }), [projects]);

    useEffect(() => { loadDashboardData(); }, [loadDashboardData]);

    return { loading, error, projects, productionStats, alerts, stats, loadDashboardData };
}
