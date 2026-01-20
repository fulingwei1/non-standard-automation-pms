import { useState, useCallback, useEffect, useMemo } from 'react';
import { purchaseApi, supplierApi } from '../../../services/api';

/**
 * 采购工程师工作台数据 Hook
 */
export function useProcurementWorkstation() {
    const [orders, setOrders] = useState([]);
    const [suppliers, setSuppliers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadOrders = useCallback(async () => {
        try {
            setLoading(true);
            const response = await purchaseApi.getMyOrders({ page_size: 50 });
            setOrders(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadSuppliers = useCallback(async () => {
        try {
            const response = await supplierApi.list({ page_size: 100 });
            setSuppliers(response.data?.items || response.data || []);
        } catch (err) {
            console.error('Failed to load suppliers:', err);
        }
    }, []);

    const createOrder = useCallback(async (data) => {
        try {
            await purchaseApi.create(data);
            await loadOrders();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadOrders]);

    const stats = useMemo(() => ({
        total: orders.length,
        pending: orders.filter(o => o.status === 'pending').length,
        ordered: orders.filter(o => o.status === 'ordered').length,
        delayed: orders.filter(o => o.is_delayed).length,
        totalValue: orders.reduce((sum, o) => sum + (o.total_amount || 0), 0),
    }), [orders]);

    useEffect(() => { loadOrders(); loadSuppliers(); }, [loadOrders, loadSuppliers]);

    return { orders, suppliers, loading, error, stats, loadOrders, createOrder };
}
