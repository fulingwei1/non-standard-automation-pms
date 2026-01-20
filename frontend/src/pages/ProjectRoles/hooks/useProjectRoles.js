import { useState, useCallback, useEffect } from 'react';
import { projectRolesApi } from '../../../services/api';

export function useProjectRoles(projectId) {
    const [roles, setRoles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadRoles = useCallback(async () => {
        if (!projectId) return;
        try {
            setLoading(true);
            const response = await projectRolesApi.list(projectId);
            setRoles(response.data || response || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [projectId]);

    const assignRole = useCallback(async (roleData) => {
        try { await projectRolesApi.assign(projectId, roleData); await loadRoles(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [projectId, loadRoles]);

    useEffect(() => { loadRoles(); }, [loadRoles]);
    return { roles, loading, error, loadRoles, assignRole };
}
