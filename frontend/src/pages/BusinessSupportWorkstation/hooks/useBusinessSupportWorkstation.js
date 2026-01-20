import { useState, useCallback, useEffect, useMemo } from 'react';
import { supportApi, ticketApi } from '../../../services/api';

/**
 * 商务支持工作台数据 Hook
 */
export function useBusinessSupportWorkstation() {
    const [tickets, setTickets] = useState([]);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadTickets = useCallback(async () => {
        try {
            setLoading(true);
            const response = await ticketApi.getMyTickets({ page_size: 50 });
            setTickets(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadTasks = useCallback(async () => {
        try {
            const response = await supportApi.getMyTasks({ page_size: 50 });
            setTasks(response.data?.items || response.data || []);
        } catch (err) {
            console.error('Failed to load tasks:', err);
        }
    }, []);

    const updateTicketStatus = useCallback(async (id, status) => {
        try {
            await ticketApi.updateStatus(id, { status });
            await loadTickets();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTickets]);

    const stats = useMemo(() => ({
        totalTickets: tickets.length,
        pendingTickets: tickets.filter(t => t.status === 'pending').length,
        totalTasks: tasks.length,
        overdueTasks: tasks.filter(t => new Date(t.due_date) < new Date() && t.status !== 'completed').length,
    }), [tickets, tasks]);

    useEffect(() => { loadTickets(); loadTasks(); }, [loadTickets, loadTasks]);

    return { tickets, tasks, loading, error, stats, loadTickets, loadTasks, updateTicketStatus };
}
