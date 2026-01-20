import { useState, useCallback, useEffect } from 'react';
import { supplierApi } from '../../../services/api';

/**
 * 供应商管理数据 Hook
 */
export function useSupplierManagementPage() {
    const [suppliers, setSuppliers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ level: '', category: '', status: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadSuppliers = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.level && filters.level !== 'all') params.level = filters.level;
            if (filters.category && filters.category !== 'all') params.category = filters.category;
            if (filters.status && filters.status !== 'all') params.status = filters.status;

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

    const evaluateSupplier = useCallback(async (id, evaluation) => {
        try {
            await supplierApi.evaluate(id, evaluation);
            await loadSuppliers();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadSuppliers]);

    useEffect(() => { loadSuppliers(); }, [loadSuppliers]);

    return { suppliers, loading, error, filters, setFilters, pagination, setPagination, loadSuppliers, createSupplier, evaluateSupplier };
}
