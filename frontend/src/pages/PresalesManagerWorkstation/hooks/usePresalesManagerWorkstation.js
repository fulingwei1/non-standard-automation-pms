import { useState, useCallback, useEffect, useMemo } from 'react';
import { presaleApi, taskApi } from '../../../services/api';

/**
 * 售前经理工作台数据 Hook
 */
export function usePresalesManagerWorkstation() {
    const [opportunities, setOpportunities] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [teamMembers, setTeamMembers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadDashboardData = useCallback(async () => {
        try {
            setLoading(true);
            const [oppsRes, tasksRes, teamRes] = await Promise.all([
                presaleApi.listOpportunities({ page_size: 50 }),
                taskApi.getTeamTasks({ page_size: 50 }),
                presaleApi.getTeamMembers(),
            ]);

            setOpportunities(oppsRes.data?.items || oppsRes.data?.items || oppsRes.data || []);
            setTasks(tasksRes.data?.items || tasksRes.data?.items || tasksRes.data || []);
            setTeamMembers(teamRes.data || teamRes || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const assignTask = useCallback(async (taskId, userId) => {
        try {
            await taskApi.assign(taskId, { user_id: userId });
            await loadDashboardData();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadDashboardData]);

    const stats = useMemo(() => ({
        totalOpportunities: opportunities.length,
        pendingTasks: tasks.filter(t => t.status === 'pending').length,
        teamSize: teamMembers.length,
        totalValue: opportunities.reduce((sum, o) => sum + (o.expected_revenue || 0), 0),
    }), [opportunities, tasks, teamMembers]);

    useEffect(() => { loadDashboardData(); }, [loadDashboardData]);

    return { opportunities, tasks, teamMembers, loading, error, stats, loadDashboardData, assignTask };
}
