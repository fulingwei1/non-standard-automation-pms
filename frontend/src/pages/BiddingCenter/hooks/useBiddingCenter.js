import { useState, useCallback, useEffect } from 'react';
import { presaleApi as biddingApi } from '../../../services/api';

/**
 * 招投标中心数据 Hook
 */
export function useBiddingCenter() {
    const [bids, setBids] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', type: '', keyword: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadBids = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.keyword) params.keyword = filters.keyword;

            const response = await biddingApi.list(params);
            const data = response.data || response;
            setBids(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    const createBid = useCallback(async (data) => {
        try {
            await biddingApi.create(data);
            await loadBids();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadBids]);

    const submitBid = useCallback(async (id) => {
        try {
            await biddingApi.submit(id);
            await loadBids();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadBids]);

    useEffect(() => { loadBids(); }, [loadBids]);

    return { bids, loading, error, filters, setFilters, pagination, setPagination, loadBids, createBid, submitBid };
}
