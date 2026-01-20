import { useState, useCallback, useEffect } from 'react';
import { purchaseOrderApi } from '../../../services/api';

/**
 * 采购订单详情数据 Hook
 */
export function usePurchaseOrderDetail(orderId) {
    const [order, setOrder] = useState(null);
    const [items, setItems] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadOrder = useCallback(async () => {
        if (!orderId) return;
        try {
            setLoading(true);
            const response = await purchaseOrderApi.get(orderId);
            const data = response.data || response;
            setOrder(data);
            setItems(data.items || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [orderId]);

    const updateOrder = useCallback(async (data) => {
        try {
            await purchaseOrderApi.update(orderId, data);
            await loadOrder();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [orderId, loadOrder]);

    const addItem = useCallback(async (itemData) => {
        try {
            await purchaseOrderApi.addItem(orderId, itemData);
            await loadOrder();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [orderId, loadOrder]);

    const submitOrder = useCallback(async () => {
        try {
            await purchaseOrderApi.submit(orderId);
            await loadOrder();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [orderId, loadOrder]);

    useEffect(() => { loadOrder(); }, [loadOrder]);

    return { order, items, loading, error, loadOrder, updateOrder, addItem, submitOrder };
}
