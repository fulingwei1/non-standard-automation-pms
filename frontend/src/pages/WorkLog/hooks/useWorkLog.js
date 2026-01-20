import { useState, useCallback, useEffect } from 'react';
import { workLogApi } from '../../../services/api';

/**
 * 工作日志数据 Hook
 */
export function useWorkLog() {
    const [logs, setLogs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ date: new Date().toISOString().split('T')[0], project_id: '' });

    const loadLogs = useCallback(async () => {
        try {
            setLoading(true);
            const params = { date: filters.date };
            if (filters.project_id) params.project_id = filters.project_id;

            const response = await workLogApi.list(params);
            setLogs(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const createLog = useCallback(async (data) => {
        try {
            await workLogApi.create(data);
            await loadLogs();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadLogs]);

    const updateLog = useCallback(async (id, data) => {
        try {
            await workLogApi.update(id, data);
            await loadLogs();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadLogs]);

    const deleteLog = useCallback(async (id) => {
        try {
            await workLogApi.delete(id);
            await loadLogs();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadLogs]);

    useEffect(() => { loadLogs(); }, [loadLogs]);

    return { logs, loading, error, filters, setFilters, loadLogs, createLog, updateLog, deleteLog };
}
