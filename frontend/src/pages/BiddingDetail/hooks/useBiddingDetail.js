import { useState, useCallback, useEffect } from 'react';
import { biddingApi } from '../../../services/api';

export function useBiddingDetail(biddingId) {
    const [bidding, setBidding] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadBidding = useCallback(async () => {
        if (!biddingId) return;
        try {
            setLoading(true);
            const response = await biddingApi.get(biddingId);
            setBidding(response.data || response);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [biddingId]);

    const submitBid = useCallback(async (data) => {
        try { await biddingApi.submitBid(biddingId, data); await loadBidding(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [biddingId, loadBidding]);

    useEffect(() => { loadBidding(); }, [loadBidding]);
    return { bidding, loading, error, loadBidding, submitBid };
}
