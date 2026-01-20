import { useState, useCallback, useEffect } from 'react';
import { salesProjectApi } from '../../../services/api';

/**
 * 销售项目跟踪数据 Hook
 */
export function useSalesProjectTrack() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ stage: '', owner: '' });

    const loadProjects = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.stage && filters.stage !== 'all') params.stage = filters.stage;
            if (filters.owner) params.owner_id = filters.owner;

            const response = await salesProjectApi.list(params);
            setProjects(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const updateStage = useCallback(async (id, stage) => {
        try {
            await salesProjectApi.updateStage(id, { stage });
            await loadProjects();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadProjects]);

    const addFollowUp = useCallback(async (id, content) => {
        try {
            await salesProjectApi.addFollowUp(id, { content });
            await loadProjects();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadProjects]);

    useEffect(() => { loadProjects(); }, [loadProjects]);

    return { projects, loading, error, filters, setFilters, loadProjects, updateStage, addFollowUp };
}
