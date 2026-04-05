import { useState, useCallback, useEffect } from 'react';
import { presaleApi } from '../../../services/api';

function extractItems(response) {
    return response?.data?.items || response?.data?.data?.items || response?.data || [];
}

function resolveActualHours(payload) {
    if (typeof payload === 'number') {
        return payload;
    }

    if (payload && typeof payload === 'object') {
        return payload.actual_hours ?? payload.actualHours ?? null;
    }

    return null;
}

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
            setError(null);

            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.ticket_type = filters.type;

            const response = await presaleApi.tickets.list(params);
            setTasks(extractItems(response));
        } catch (err) {
            setError(err.response?.data?.detail || err.message);
            setTasks([]);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const updateTaskStatus = useCallback(async (id, status, options = {}) => {
        try {
            if (status === 'ACCEPTED') {
                await presaleApi.tickets.accept(id, options.acceptPayload || {});
            } else if (status === 'IN_PROGRESS') {
                await presaleApi.tickets.updateProgress(id, {
                    progress_note: options.progressNote || '任务开始处理',
                    progress_percent: options.progressPercent ?? 50,
                });
            } else if (status === 'COMPLETED') {
                await presaleApi.tickets.complete(id, {
                    actual_hours: resolveActualHours(options),
                });
            } else {
                throw new Error(`暂不支持更新到状态: ${status}`);
            }

            await loadTasks();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTasks]);

    const completeTask = useCallback(async (id, payload) => {
        try {
            await presaleApi.tickets.complete(id, {
                actual_hours: resolveActualHours(payload),
            });
            await loadTasks();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTasks]);

    useEffect(() => {
        loadTasks();
    }, [loadTasks]);

    return { tasks, loading, error, filters, setFilters, loadTasks, updateTaskStatus, completeTask };
}
