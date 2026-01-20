import { useState, useCallback, useEffect } from 'react';
import { roleTypeApi } from '../../../services/api';

/**
 * 项目角色类型管理数据 Hook
 */
export function useProjectRoleTypes() {
    const [roleTypes, setRoleTypes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadRoleTypes = useCallback(async () => {
        try {
            setLoading(true);
            const response = await roleTypeApi.list({ page_size: 100 });
            setRoleTypes(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const createRoleType = useCallback(async (data) => {
        try {
            await roleTypeApi.create(data);
            await loadRoleTypes();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadRoleTypes]);

    const updateRoleType = useCallback(async (id, data) => {
        try {
            await roleTypeApi.update(id, data);
            await loadRoleTypes();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadRoleTypes]);

    const deleteRoleType = useCallback(async (id) => {
        try {
            await roleTypeApi.delete(id);
            await loadRoleTypes();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadRoleTypes]);

    useEffect(() => { loadRoleTypes(); }, [loadRoleTypes]);

    return { roleTypes, loading, error, loadRoleTypes, createRoleType, updateRoleType, deleteRoleType };
}
