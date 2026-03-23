import { useState, useCallback, useEffect, useMemo } from 'react';
import { materialApi as materialReadinessApi } from '../../../services/api';

export function useMaterialReadiness() {
    const [materials, setMaterials] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ project_id: '', status: '' });

    const loadMaterials = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.project_id) params.project_id = filters.project_id;
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            const response = await materialReadinessApi.list(params);
            setMaterials(response.data?.items || response.data?.items || response.data || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [filters]);

    const stats = useMemo(() => ({
        total: materials.length,
        ready: materials.filter(m => m.readiness >= 100).length,
        partial: materials.filter(m => m.readiness >= 50 && m.readiness < 100).length,
        shortage: materials.filter(m => m.readiness < 50).length,
    }), [materials]);

    useEffect(() => { loadMaterials(); }, [loadMaterials]);
    return { materials, loading, error, filters, setFilters, stats, loadMaterials };
}
