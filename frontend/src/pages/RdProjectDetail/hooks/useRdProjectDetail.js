import { useState, useCallback, useEffect } from 'react';
import { rdProjectApi } from '../../../services/api';

/**
 * 研发项目详情数据 Hook
 */
export function useRdProjectDetail(projectId) {
    const [project, setProject] = useState(null);
    const [tasks, setTasks] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadProject = useCallback(async () => {
        if (!projectId) return;
        try {
            setLoading(true);
            const response = await rdProjectApi.get(projectId);
            setProject(response.data || response);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [projectId]);

    const loadTasks = useCallback(async () => {
        if (!projectId) return;
        try {
            const response = await rdProjectApi.getTasks(projectId);
            setTasks(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            console.error('Failed to load tasks:', err);
        }
    }, [projectId]);

    const updateProject = useCallback(async (data) => {
        try {
            await rdProjectApi.update(projectId, data);
            await loadProject();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [projectId, loadProject]);

    const addTask = useCallback(async (taskData) => {
        try {
            await rdProjectApi.addTask(projectId, taskData);
            await loadTasks();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [projectId, loadTasks]);

    useEffect(() => { loadProject(); loadTasks(); }, [loadProject, loadTasks]);

    return { project, tasks, loading, error, loadProject, loadTasks, updateProject, addTask };
}
