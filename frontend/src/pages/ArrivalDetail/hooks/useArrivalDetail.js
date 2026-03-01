import { useState, useCallback, useEffect } from 'react';
import { shortageApi as arrivalApi } from '../../../services/api';

export function useArrivalDetail(arrivalId) {
    const [arrival, setArrival] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadArrival = useCallback(async () => {
        if (!arrivalId) return;
        try {
            setLoading(true);
            const response = await arrivalApi.get(arrivalId);
            setArrival(response.data || response);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, [arrivalId]);

    const updateStatus = useCallback(async (status) => {
        try { await arrivalApi.updateStatus(arrivalId, status); await loadArrival(); return { success: true }; }
        catch (err) { return { success: false, error: err.message }; }
    }, [arrivalId, loadArrival]);

    useEffect(() => { loadArrival(); }, [loadArrival]);
    return { arrival, loading, loadArrival, updateStatus };
}
