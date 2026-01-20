import { useState, useCallback, useEffect, useMemo } from 'react';
import { workerApi, taskApi } from '../../../services/api';

/**
 * 工人工作台数据 Hook
 */
export function useWorkerWorkstation() {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentTask, setCurrentTask] = useState(null);

    const loadTasks = useCallback(async () => {
        try {
            setLoading(true);
            const response = await workerApi.getMyTasks({ page_size: 50 });
            setTasks(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const startTask = useCallback(async (taskId) => {
        try {
            await workerApi.startTask(taskId);
            await loadTasks();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTasks]);

    const completeTask = useCallback(async (taskId, result) => {
        try {
            await workerApi.completeTask(taskId, result);
            await loadTasks();
            setCurrentTask(null);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTasks]);

    const reportIssue = useCallback(async (taskId, issue) => {
        try {
            await workerApi.reportIssue(taskId, issue);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, []);

    const stats = useMemo(() => ({
        total: tasks.length,
        pending: tasks.filter(t => t.status === 'pending').length,
        inProgress: tasks.filter(t => t.status === 'in_progress').length,
        completed: tasks.filter(t => t.status === 'completed').length,
    }), [tasks]);

    useEffect(() => { loadTasks(); }, [loadTasks]);

    return { tasks, loading, error, currentTask, setCurrentTask, stats, loadTasks, startTask, completeTask, reportIssue };
}
