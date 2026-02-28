import { useState, useCallback, useEffect, useMemo } from 'react';
import { materialApi } from '../../../services/api';

/**
 * 物料跟踪数据 Hook
 */
export function useMaterialTracking() {
    const [materials, setMaterials] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', category: '', keyword: '' });

    const loadMaterials = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.category && filters.category !== 'all') params.category = filters.category;
            if (filters.keyword) params.keyword = filters.keyword;

            const response = await materialApi.listTracking(params);
            setMaterials(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const updateStatus = useCallback(async (id, status, notes) => {
        try {
            await materialApi.updateTrackingStatus(id, { status, notes });
            await loadMaterials();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadMaterials]);

    const stats = useMemo(() => ({
        total: materials.length,
        ordered: materials.filter(m => m.status === 'ordered').length,
        shipped: materials.filter(m => m.status === 'shipped').length,
        received: materials.filter(m => m.status === 'received').length,
        delayed: materials.filter(m => m.is_delayed).length,
    }), [materials]);

    useEffect(() => { loadMaterials(); }, [loadMaterials]);

    return { materials, loading, error, filters, setFilters, stats, loadMaterials, updateStatus };
}
