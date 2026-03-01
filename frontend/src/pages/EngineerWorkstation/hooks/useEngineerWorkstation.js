import { useState, useCallback, useEffect, useMemo } from 'react';
import { taskCenterApi as taskApi, projectApi } from '../../../services/api';

/**
 * 工程师工作台数据 Hook
 */
export function useEngineerWorkstation() {
    const [tasks, setTasks] = useState([]);
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [viewMode, setViewMode] = useState('list'); // list, kanban, calendar

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            const [tasksRes, projectsRes] = await Promise.all([
                taskApi.getMyTasks({ page_size: 100 }),
                projectApi.getMyProjects({ page_size: 50 }),
            ]);

            setTasks(tasksRes.data?.items || tasksRes.data?.items || tasksRes.data || []);
            setProjects(projectsRes.data?.items || projectsRes.data?.items || projectsRes.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const updateTaskStatus = useCallback(async (taskId, status) => {
        try {
            await taskApi.updateStatus(taskId, { status });
            await loadData();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadData]);

    const stats = useMemo(() => ({
        totalTasks: tasks.length,
        pending: tasks.filter(t => t.status === 'pending').length,
        inProgress: tasks.filter(t => t.status === 'in_progress').length,
        completed: tasks.filter(t => t.status === 'completed').length,
        overdue: tasks.filter(t => new Date(t.due_date) < new Date() && t.status !== 'completed').length,
    }), [tasks]);

    useEffect(() => { loadData(); }, [loadData]);

    return { tasks, projects, loading, error, viewMode, setViewMode, stats, loadData, updateTaskStatus };
}
