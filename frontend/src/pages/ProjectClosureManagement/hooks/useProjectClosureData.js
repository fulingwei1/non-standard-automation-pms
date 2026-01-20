import { useState, useCallback, useEffect } from 'react';
import { projectApi } from '../../../services/api';

/**
 * 项目结项数据管理 Hook
 */
export function useProjectClosureData() {
    const [projects, setProjects] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedProject, setSelectedProject] = useState(null);
    const [closureData, setClosureData] = useState(null);

    // 加载可结项项目列表
    const loadProjects = useCallback(async () => {
        try {
            setLoading(true);
            const response = await projectApi.list({
                status: 'completed',
                page_size: 100,
            });
            const data = response.data || response;
            setProjects(data.items || data || []);
        } catch (err) {
            console.error('Failed to load projects:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    // 加载项目结项详情
    const loadClosureData = useCallback(async (projectId) => {
        try {
            const response = await projectApi.getClosureData(projectId);
            setClosureData(response.data || response);
            return response.data || response;
        } catch (err) {
            console.error('Failed to load closure data:', err);
            throw err;
        }
    }, []);

    // 提交结项申请
    const submitClosure = useCallback(async (projectId, data) => {
        try {
            await projectApi.submitClosure(projectId, data);
            await loadProjects();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadProjects]);

    // 批准结项
    const approveClosure = useCallback(async (projectId, comments) => {
        try {
            await projectApi.approveClosure(projectId, { comments });
            await loadProjects();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadProjects]);

    // 驳回结项
    const rejectClosure = useCallback(async (projectId, reason) => {
        try {
            await projectApi.rejectClosure(projectId, { reason });
            await loadProjects();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadProjects]);

    useEffect(() => {
        loadProjects();
    }, [loadProjects]);

    return {
        projects,
        loading,
        error,
        selectedProject,
        setSelectedProject,
        closureData,
        loadProjects,
        loadClosureData,
        submitClosure,
        approveClosure,
        rejectClosure,
    };
}
