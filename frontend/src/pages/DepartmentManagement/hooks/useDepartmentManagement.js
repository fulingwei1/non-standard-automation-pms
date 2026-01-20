import { useState, useCallback, useEffect } from 'react';
import { departmentApi } from '../../../services/api';

export function useDepartmentManagement() {
    const [departments, setDepartments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadDepartments = useCallback(async () => {
        try {
            setLoading(true);
            const response = await departmentApi.list();
            setDepartments(response.data || response || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, []);

    const createDepartment = useCallback(async (data) => {
        try { await departmentApi.create(data); await loadDepartments(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadDepartments]);

    const updateDepartment = useCallback(async (id, data) => {
        try { await departmentApi.update(id, data); await loadDepartments(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadDepartments]);

    useEffect(() => { loadDepartments(); }, [loadDepartments]);
    return { departments, loading, error, loadDepartments, createDepartment, updateDepartment };
}
