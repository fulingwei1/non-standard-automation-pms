import { useState, useCallback, useEffect, useMemo } from 'react';
import { salesTargetApi } from '../../../services/api';

/**
 * 销售目标数据 Hook
 */
export function useSalesTarget() {
    const [targets, setTargets] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [year, setYear] = useState(new Date().getFullYear());

    const loadTargets = useCallback(async () => {
        try {
            setLoading(true);
            const response = await salesTargetApi.list({ year });
            setTargets(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [year]);

    const updateTarget = useCallback(async (id, data) => {
        try {
            await salesTargetApi.update(id, data);
            await loadTargets();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTargets]);

    const stats = useMemo(() => ({
        totalTarget: targets.reduce((sum, t) => sum + (t.target_amount || 0), 0),
        totalActual: targets.reduce((sum, t) => sum + (t.actual_amount || 0), 0),
        completionRate: targets.length > 0 ?
            (targets.reduce((sum, t) => sum + (t.actual_amount || 0), 0) /
                targets.reduce((sum, t) => sum + (t.target_amount || 0), 0) * 100).toFixed(1) : 0,
    }), [targets]);

    useEffect(() => { loadTargets(); }, [loadTargets]);

    return { targets, loading, error, year, setYear, stats, loadTargets, updateTarget };
}
