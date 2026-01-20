import { useState, useCallback, useEffect, useMemo } from 'react';
import { assemblyApi } from '../../../services/api';

/**
 * 齐套分析看板数据 Hook
 */
export function useAssemblyKitBoard() {
    const [kits, setKits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ project_id: '', status: '' });

    const loadKits = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.project_id) params.project_id = filters.project_id;
            if (filters.status && filters.status !== 'all') params.status = filters.status;

            const response = await assemblyApi.listKits(params);
            setKits(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const analyzeKit = useCallback(async (machineId) => {
        try {
            const response = await assemblyApi.analyzeKit(machineId);
            return { success: true, data: response.data || response };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, []);

    const stats = useMemo(() => ({
        total: kits.length,
        ready: kits.filter(k => k.readiness >= 100).length,
        partial: kits.filter(k => k.readiness >= 50 && k.readiness < 100).length,
        notReady: kits.filter(k => k.readiness < 50).length,
        avgReadiness: kits.length > 0
            ? (kits.reduce((sum, k) => sum + k.readiness, 0) / kits.length).toFixed(1)
            : 0,
    }), [kits]);

    useEffect(() => { loadKits(); }, [loadKits]);

    return { kits, loading, error, filters, setFilters, stats, loadKits, analyzeKit };
}
