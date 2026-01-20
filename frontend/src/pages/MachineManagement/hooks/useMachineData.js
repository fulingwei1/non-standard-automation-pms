import { useState, useCallback, useEffect } from 'react';
import { machineApi, projectApi } from '../../../services/api';

/**
 * 机台数据管理 Hook
 * 负责机台和项目数据的加载、创建、更新
 */
export function useMachineData(projectId) {
    const [loading, setLoading] = useState(true);
    const [project, setProject] = useState(null);
    const [machines, setMachines] = useState([]);
    const [filters, setFilters] = useState({
        searchKeyword: '',
        filterStatus: '',
        filterHealth: '',
    });

    // 加载项目信息
    const fetchProject = useCallback(async () => {
        if (!projectId) return;
        try {
            const res = await projectApi.get(projectId);
            setProject(res.data || res);
        } catch (error) {
            console.error('Failed to fetch project:', error);
        }
    }, [projectId]);

    // 加载机台列表
    const fetchMachines = useCallback(async () => {
        if (!projectId) return;
        try {
            setLoading(true);
            const params = { project_id: projectId };
            if (filters.filterStatus && filters.filterStatus !== 'all') {
                params.status = filters.filterStatus;
            }
            if (filters.filterHealth && filters.filterHealth !== 'all') {
                params.health = filters.filterHealth;
            }
            if (filters.searchKeyword) {
                params.search = filters.searchKeyword;
            }
            const res = await machineApi.list(params);
            const machineList = res.data?.items || res.data || [];
            setMachines(machineList);
        } catch (error) {
            console.error('Failed to fetch machines:', error);
        } finally {
            setLoading(false);
        }
    }, [projectId, filters]);

    // 创建机台
    const createMachine = useCallback(async (machineData) => {
        try {
            await machineApi.create({
                ...machineData,
                project_id: parseInt(projectId),
            });
            await fetchMachines();
            return { success: true };
        } catch (error) {
            console.error('Failed to create machine:', error);
            return {
                success: false,
                error: error.response?.data?.detail || error.message
            };
        }
    }, [projectId, fetchMachines]);

    // 获取机台详情
    const getMachineDetail = useCallback(async (machineId) => {
        try {
            const res = await machineApi.get(machineId);
            return res.data || res;
        } catch (error) {
            console.error('Failed to fetch machine detail:', error);
            throw error;
        }
    }, []);

    // 初始加载
    useEffect(() => {
        if (projectId) {
            fetchProject();
            fetchMachines();
        }
    }, [projectId, fetchProject, fetchMachines]);

    return {
        loading,
        project,
        machines,
        filters,
        setFilters,
        fetchMachines,
        createMachine,
        getMachineDetail,
    };
}
