import { useState, useCallback, useEffect } from 'react';
import { purchaseOrderApi } from '../../../services/api';

export function usePurchaseOrderFromBOM() {
    const [boms, setBoms] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadBoms = useCallback(async () => {
        try {
            setLoading(true);
            const response = await purchaseOrderApi.getBomsForOrder();
            setBoms(response.data || response || []);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, []);

    const createOrder = useCallback(async (data) => {
        try { await purchaseOrderApi.createFromBOM(data); return { success: true }; }
        catch (err) { return { success: false, error: err.message }; }
    }, []);

    useEffect(() => { loadBoms(); }, [loadBoms]);
    return { boms, loading, loadBoms, createOrder };
}
