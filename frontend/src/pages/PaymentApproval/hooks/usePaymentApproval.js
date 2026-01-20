import { useState, useCallback, useEffect } from 'react';
import { paymentApprovalApi } from '../../../services/api';

export function usePaymentApproval() {
    const [approvals, setApprovals] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [tab, setTab] = useState('pending');

    const loadApprovals = useCallback(async () => {
        try {
            setLoading(true);
            const response = await paymentApprovalApi.list({ tab, page_size: 50 });
            setApprovals(response.data?.items || response.data || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [tab]);

    const approve = useCallback(async (id, comment) => {
        try { await paymentApprovalApi.approve(id, { comment }); await loadApprovals(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadApprovals]);

    const reject = useCallback(async (id, reason) => {
        try { await paymentApprovalApi.reject(id, { reason }); await loadApprovals(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadApprovals]);

    useEffect(() => { loadApprovals(); }, [loadApprovals]);
    return { approvals, loading, error, tab, setTab, loadApprovals, approve, reject };
}
