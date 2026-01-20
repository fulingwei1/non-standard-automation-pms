import { useState, useCallback, useEffect } from 'react';
import { taskApi } from '../../../services/api';

export function useProjectTaskList() {
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ project_id: '', status: '' });

    const loadTasks = useCallback(async () => {
        try {
            setLoading(true);
            const response = await taskApi.list(filters);
            setTasks(response.data?.items || response.data || []);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, [filters]);

    useEffect(() => { loadTasks(); }, [loadTasks]);
    return { tasks, loading, filters, setFilters, loadTasks };
}
