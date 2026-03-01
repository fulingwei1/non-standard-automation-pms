import { useState, useCallback, useEffect } from 'react';
import { purchaseApi as goodsReceiptApi, purchaseApi as purchaseOrderApi } from '../../../services/api';

export function useGoodsReceiptNew() {
    const [orders, setOrders] = useState([]);
    const [loading, setLoading] = useState(true);
    const [submitting, setSubmitting] = useState(false);

    const loadOrders = useCallback(async () => {
        try {
            setLoading(true);
            const response = await purchaseOrderApi.getPending({ page_size: 100 });
            setOrders(response.data?.items || response.data?.items || response.data || []);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, []);

    const createReceipt = useCallback(async (data) => {
        try {
            setSubmitting(true);
            await goodsReceiptApi.create(data);
            return { success: true };
        } catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
        finally { setSubmitting(false); }
    }, []);

    useEffect(() => { loadOrders(); }, [loadOrders]);
    return { orders, loading, submitting, loadOrders, createReceipt };
}
