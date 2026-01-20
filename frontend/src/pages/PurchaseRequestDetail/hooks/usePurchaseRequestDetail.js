import { useState, useCallback, useEffect } from 'react';
import { purchaseRequestApi } from '../../../services/api';

export function usePurchaseRequestDetail(requestId) {
    const [request, setRequest] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadRequest = useCallback(async () => {
        if (!requestId) return;
        try {
            setLoading(true);
            const response = await purchaseRequestApi.get(requestId);
            setRequest(response.data || response);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [requestId]);

    const updateRequest = useCallback(async (data) => {
        try { await purchaseRequestApi.update(requestId, data); await loadRequest(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [requestId, loadRequest]);

    const submitRequest = useCallback(async () => {
        try { await purchaseRequestApi.submit(requestId); await loadRequest(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [requestId, loadRequest]);

    useEffect(() => { loadRequest(); }, [loadRequest]);
    return { request, loading, error, loadRequest, updateRequest, submitRequest };
}
