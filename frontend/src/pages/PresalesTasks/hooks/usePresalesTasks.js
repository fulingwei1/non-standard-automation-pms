import { useState, useCallback, useEffect } from 'react';
import { presaleApi } from '../../../services/api';

/**
 * 售前任务数据 Hook
 */
export function usePresalesTasks() {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', type: '' });

    const loadTasks = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;

            const response = await presaleApi.getMyTasks(params);
            setTasks(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const updateTaskStatus = useCallback(async (id, status) => {
        try {
            await presaleApi.updateTaskStatus(id, { status });
            await loadTasks();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTasks]);

    const completeTask = useCallback(async (id, deliverables) => {
        try {
            await presaleApi.completeTask(id, { deliverables });
            await loadTasks();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTasks]);

    useEffect(() => { loadTasks(); }, [loadTasks]);

    return { tasks, loading, error, filters, setFilters, loadTasks, updateTaskStatus, completeTask };
}
