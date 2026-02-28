import { useState, useCallback, useEffect, useMemo } from 'react';
import { inventoryApi } from '../../../services/api';

/**
 * 库存分析数据 Hook
 */
export function useInventoryAnalysis() {
    const [inventory, setInventory] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ category: '', status: '', warehouse: '' });

    const loadInventory = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.category && filters.category !== 'all') params.category = filters.category;
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.warehouse && filters.warehouse !== 'all') params.warehouse = filters.warehouse;

            const response = await inventoryApi.list(params);
            setInventory(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const stats = useMemo(() => ({
        totalItems: inventory.length,
        totalValue: inventory.reduce((sum, i) => sum + (i.quantity * i.unit_price || 0), 0),
        lowStock: inventory.filter(i => i.quantity < i.min_stock).length,
        overStock: inventory.filter(i => i.quantity > i.max_stock).length,
        outOfStock: inventory.filter(i => i.quantity === 0).length,
    }), [inventory]);

    const categoryStats = useMemo(() => {
        return inventory.reduce((acc, item) => {
            const cat = item.category || 'other';
            if (!acc[cat]) acc[cat] = { count: 0, value: 0 };
            acc[cat].count++;
            acc[cat].value += item.quantity * item.unit_price || 0;
            return acc;
        }, {});
    }, [inventory]);

    useEffect(() => { loadInventory(); }, [loadInventory]);

    return { inventory, loading, error, filters, setFilters, stats, categoryStats, loadInventory };
}
