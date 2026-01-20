import { useState, useCallback, useEffect } from 'react';
import { contractApi } from '../../../services/api';

export function useContractList() {
    const [contracts, setContracts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', type: '', keyword: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadContracts = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.keyword) params.keyword = filters.keyword;
            const response = await contractApi.list(params);
            const data = response.data || response;
            setContracts(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [pagination.page, pagination.pageSize, filters]);

    useEffect(() => { loadContracts(); }, [loadContracts]);
    return { contracts, loading, error, filters, setFilters, pagination, setPagination, loadContracts };
}
