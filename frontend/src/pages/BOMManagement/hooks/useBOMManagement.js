import { useState, useCallback, useEffect } from 'react';
import { bomApi } from '../../../services/api';

/**
 * BOM管理数据 Hook
 */
export function useBOMManagement() {
    const [boms, setBoms] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ type: '', status: '', keyword: '' });

    const loadBoms = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.keyword) params.keyword = filters.keyword;

            const response = await bomApi.list(params);
            setBoms(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const createBom = useCallback(async (data) => {
        try {
            await bomApi.create(data);
            await loadBoms();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadBoms]);

    const releaseBom = useCallback(async (id) => {
        try {
            await bomApi.release(id);
            await loadBoms();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadBoms]);

    useEffect(() => { loadBoms(); }, [loadBoms]);

    return { boms, loading, error, filters, setFilters, loadBoms, createBom, releaseBom };
}
