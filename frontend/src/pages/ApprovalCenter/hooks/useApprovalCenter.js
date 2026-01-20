import { useState, useCallback, useEffect, useMemo } from 'react';
import { approvalApi } from '../../../services/api';

/**
 * 审批中心数据 Hook
 */
export function useApprovalCenter() {
    const [approvals, setApprovals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', type: '' });
    const [tab, setTab] = useState('pending'); // pending, processed, initiated

    const loadApprovals = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50, tab };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;

            const response = await approvalApi.list(params);
            setApprovals(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [tab, filters]);

    const approve = useCallback(async (id, comment) => {
        try {
            await approvalApi.approve(id, { comment });
            await loadApprovals();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadApprovals]);

    const reject = useCallback(async (id, reason) => {
        try {
            await approvalApi.reject(id, { reason });
            await loadApprovals();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadApprovals]);

    const stats = useMemo(() => ({
        pending: approvals.filter(a => a.status === 'pending').length,
        approved: approvals.filter(a => a.status === 'approved').length,
        rejected: approvals.filter(a => a.status === 'rejected').length,
    }), [approvals]);

    useEffect(() => { loadApprovals(); }, [loadApprovals]);

    return { approvals, loading, error, filters, setFilters, tab, setTab, stats, loadApprovals, approve, reject };
}
