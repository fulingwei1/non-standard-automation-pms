import { useState, useCallback, useEffect, useMemo } from 'react';
import { supplierApi } from '../../../services/api';

/**
 * 供应商管理数据 Hook
 */
export function useSupplierManagement() {
    const [suppliers, setSuppliers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ level: '', category: '', keyword: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadSuppliers = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.level && filters.level !== 'all') params.level = filters.level;
            if (filters.category && filters.category !== 'all') params.category = filters.category;
            if (filters.keyword) params.keyword = filters.keyword;

            const response = await supplierApi.list(params);
            const data = response.data || response;
            setSuppliers(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    const createSupplier = useCallback(async (data) => {
        try {
            await supplierApi.create(data);
            await loadSuppliers();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadSuppliers]);

    const updateSupplier = useCallback(async (id, data) => {
        try {
            await supplierApi.update(id, data);
            await loadSuppliers();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadSuppliers]);

    const stats = useMemo(() => ({
        total: suppliers.length,
        byLevel: suppliers.reduce((acc, s) => {
            acc[s.level] = (acc[s.level] || 0) + 1;
            return acc;
        }, {}),
    }), [suppliers]);

    useEffect(() => { loadSuppliers(); }, [loadSuppliers]);

    return { suppliers, loading, error, filters, setFilters, pagination, setPagination, stats, loadSuppliers, createSupplier, updateSupplier };
}
