import { useState, useCallback, useEffect } from 'react';
import { permissionApi } from '../../../services/api';

export function usePermissionManagement() {
    const [permissions, setPermissions] = useState([]);
    const [roles, setRoles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadData = useCallback(async () => {
        try {
            setLoading(true);
            const [permRes, roleRes] = await Promise.all([permissionApi.list(), permissionApi.listRoles()]);
            setPermissions(permRes.data || permRes || []);
            setRoles(roleRes.data || roleRes || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, []);

    const assignPermission = useCallback(async (roleId, permissionIds) => {
        try { await permissionApi.assignToRole(roleId, { permission_ids: permissionIds }); await loadData(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadData]);

    useEffect(() => { loadData(); }, [loadData]);
    return { permissions, roles, loading, error, loadData, assignPermission };
}
