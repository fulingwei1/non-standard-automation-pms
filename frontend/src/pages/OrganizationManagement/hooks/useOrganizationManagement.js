import { useState, useCallback, useEffect } from 'react';
import { orgApi } from '../../../services/api';

/**
 * 组织管理数据 Hook
 */
export function useOrganizationManagement() {
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadDepartments = useCallback(async () => {
        try {
            setLoading(true);
            const response = await orgApi.listDepartments();
            setDepartments(response.data || response || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const createDepartment = useCallback(async (data) => {
        try {
            await orgApi.createDepartment(data);
            await loadDepartments();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadDepartments]);

    const updateDepartment = useCallback(async (id, data) => {
        try {
            await orgApi.updateDepartment(id, data);
            await loadDepartments();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadDepartments]);

    const deleteDepartment = useCallback(async (id) => {
        try {
            await orgApi.deleteDepartment(id);
            await loadDepartments();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadDepartments]);

    useEffect(() => { loadDepartments(); }, [loadDepartments]);

    return { departments, loading, error, loadDepartments, createDepartment, updateDepartment, deleteDepartment };
}
