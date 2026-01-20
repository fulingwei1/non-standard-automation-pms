import { useState, useCallback, useEffect, useMemo } from 'react';
import { salesApi } from '../../../services/api';

/**
 * 商机管理数据 Hook
 */
export function useOpportunityManagement() {
    const [opportunities, setOpportunities] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ stage: '', owner: '', keyword: '' });
    const [pagination, setPagination] = useState({ page: 1, pageSize: 20, total: 0 });

    const loadOpportunities = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page: pagination.page, page_size: pagination.pageSize };
            if (filters.stage && filters.stage !== 'all') params.stage = filters.stage;
            if (filters.owner) params.owner_id = filters.owner;
            if (filters.keyword) params.keyword = filters.keyword;

            const response = await salesApi.listOpportunities(params);
            const data = response.data || response;
            setOpportunities(data.items || data || []);
            if (data.total) setPagination(prev => ({ ...prev, total: data.total }));
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [pagination.page, pagination.pageSize, filters]);

    const createOpportunity = useCallback(async (data) => {
        try {
            await salesApi.createOpportunity(data);
            await loadOpportunities();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadOpportunities]);

    const updateOpportunity = useCallback(async (id, data) => {
        try {
            await salesApi.updateOpportunity(id, data);
            await loadOpportunities();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadOpportunities]);

    const stats = useMemo(() => ({
        total: opportunities.length,
        totalValue: opportunities.reduce((sum, o) => sum + (o.expected_revenue || 0), 0),
        byStage: opportunities.reduce((acc, o) => {
            acc[o.stage] = (acc[o.stage] || 0) + 1;
            return acc;
        }, {}),
    }), [opportunities]);

    useEffect(() => { loadOpportunities(); }, [loadOpportunities]);

    return { opportunities, loading, error, filters, setFilters, pagination, setPagination, stats, loadOpportunities, createOpportunity, updateOpportunity };
}
