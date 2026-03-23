import { useState, useCallback, useEffect } from 'react';
import { bomApi } from '../../../services/api';

/**
 * BOM装配属性数据 Hook
 */
export function useBomAssemblyAttrs() {
    const [boms, setBoms] = useState([]);
    const [attributes, setAttributes] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [selectedBom, setSelectedBom] = useState(null);

    const loadBoms = useCallback(async () => {
        try {
            setLoading(true);
            const response = await bomApi.list({ page_size: 100 });
            // 防御性处理：确保 boms 始终为数组
            setBoms(Array.isArray(response.data?.items) ? response.data.items : Array.isArray(response.data) ? response.data : []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadAttributes = useCallback(async (bomId) => {
        if (!bomId) return;
        try {
            const response = await bomApi.getAttributes(bomId);
            setAttributes(response.data || response || []);
        } catch (_err) {
          // 非关键操作失败时静默降级
        }
    }, []);

    const updateAttribute = useCallback(async (bomId, attrId, data) => {
        try {
            await bomApi.updateAttribute(bomId, attrId, data);
            await loadAttributes(bomId);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadAttributes]);

    const addAttribute = useCallback(async (bomId, data) => {
        try {
            await bomApi.addAttribute(bomId, data);
            await loadAttributes(bomId);
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadAttributes]);

    useEffect(() => { loadBoms(); }, [loadBoms]);
    useEffect(() => { if (selectedBom) loadAttributes(selectedBom.id); }, [selectedBom, loadAttributes]);

    return { boms, attributes, loading, error, selectedBom, setSelectedBom, loadBoms, loadAttributes, updateAttribute, addAttribute };
}
