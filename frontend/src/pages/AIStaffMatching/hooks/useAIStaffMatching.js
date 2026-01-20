import { useState, useCallback, useEffect, useMemo } from 'react';
import { staffApi, projectApi } from '../../../services/api';

/**
 * AI人员匹配数据 Hook
 */
export function useAIStaffMatching() {
    const [projects, setProjects] = useState([]);
    const [staff, setStaff] = useState([]);
    const [matchResults, setMatchResults] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedProject, setSelectedProject] = useState(null);

    const loadProjects = useCallback(async () => {
        try {
            const response = await projectApi.list({ status: 'active', page_size: 50 });
            setProjects(response.data?.items || response.data || []);
        } catch (err) {
            console.error('Failed to load projects:', err);
        }
    }, []);

    const loadStaff = useCallback(async () => {
        try {
            const response = await staffApi.list({ page_size: 100, available: true });
            setStaff(response.data?.items || response.data || []);
        } catch (err) {
            console.error('Failed to load staff:', err);
        }
    }, []);

    const runMatching = useCallback(async (projectId, requirements) => {
        try {
            setLoading(true);
            const response = await staffApi.aiMatch({ project_id: projectId, requirements });
            setMatchResults(response.data || response || []);
            return { success: true, data: response.data || response };
        } catch (err) {
            setError(err.message);
            return { success: false, error: err.response?.data?.detail || err.message };
        } finally {
            setLoading(false);
        }
    }, []);

    const assignStaff = useCallback(async (projectId, staffId, role) => {
        try {
            await staffApi.assign(projectId, { staff_id: staffId, role });
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, []);

    useEffect(() => {
        const init = async () => {
            setLoading(true);
            await Promise.all([loadProjects(), loadStaff()]);
            setLoading(false);
        };
        init();
    }, [loadProjects, loadStaff]);

    return { projects, staff, matchResults, loading, error, selectedProject, setSelectedProject, runMatching, assignStaff };
}
