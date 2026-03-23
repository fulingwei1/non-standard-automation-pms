import { useState, useCallback, useEffect, useMemo } from 'react';
import { purchaseApi, materialApi } from '../../../services/api';

/**
 * 采购物料成本管理数据 Hook
 */
export function usePurchaseMaterialCost() {
    const [materials, setMaterials] = useState([]);
    const [suppliers, setSuppliers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ keyword: '', category: '', supplier_id: '' });

    const loadMaterials = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.keyword) params.keyword = filters.keyword;
            if (filters.category && filters.category !== 'all') params.category = filters.category;
            if (filters.supplier_id) params.supplier_id = filters.supplier_id;

            const response = await materialApi.listWithCost(params);
            // 防御性处理：API 响应可能是数组、对象或 {items: [...]}
            const data = response.data;
            setMaterials(Array.isArray(data?.items) ? data.items : Array.isArray(data) ? data : []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const loadSuppliers = useCallback(async () => {
        try {
            const response = await purchaseApi.listSuppliers({ page_size: 100 });
            const sData = response.data;
            setSuppliers(Array.isArray(sData?.items) ? sData.items : Array.isArray(sData) ? sData : []);
        } catch (_err) {
          // 非关键操作失败时静默降级
        }
    }, []);

    const updateMaterialPrice = useCallback(async (id, price) => {
        try {
            await materialApi.updatePrice(id, { price });
            await loadMaterials();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadMaterials]);

    const stats = useMemo(() => ({
        totalMaterials: materials.length,
        totalValue: materials.reduce((sum, m) => sum + (m.stock_qty * m.unit_price || 0), 0),
        lowStock: materials.filter(m => m.stock_qty < m.min_stock).length,
    }), [materials]);

    useEffect(() => { loadSuppliers(); loadMaterials(); }, [loadSuppliers, loadMaterials]);

    return { materials, suppliers, loading, error, filters, setFilters, stats, loadMaterials, updateMaterialPrice };
}
