import { useState, useCallback, useEffect } from 'react';
import { serviceApi } from '../../../services/api';

/**
 * 服务记录数据 Hook
 */
export function useServiceRecord() {
    const [records, setRecords] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ type: '', status: '', customer_id: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadRecords = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.customer_id) params.customer_id = filters.customer_id;

            const response = await serviceApi.listRecords(params);
            const data = response.data || response;
            setRecords(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    const createRecord = useCallback(async (data) => {
        try {
            await serviceApi.createRecord(data);
            await loadRecords();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadRecords]);

    const updateRecord = useCallback(async (id, data) => {
        try {
            await serviceApi.updateRecord(id, data);
            await loadRecords();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadRecords]);

    const closeRecord = useCallback(async (id, resolution) => {
        try {
            await serviceApi.closeRecord(id, { resolution });
            await loadRecords();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadRecords]);

    useEffect(() => { loadRecords(); }, [loadRecords]);

    return { records, loading, error, filters, setFilters, pagination, setPagination, loadRecords, createRecord, updateRecord, closeRecord };
}
