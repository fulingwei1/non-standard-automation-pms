import { useState, useCallback, useEffect } from 'react';
import { alertSubscriptionApi } from '../../../services/api';

export function useAlertSubscriptionSettings() {
    const [subscriptions, setSubscriptions] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadSubscriptions = useCallback(async () => {
        try {
            setLoading(true);
            const response = await alertSubscriptionApi.list();
            setSubscriptions(response.data || response || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, []);

    const updateSubscription = useCallback(async (id, data) => {
        try { await alertSubscriptionApi.update(id, data); await loadSubscriptions(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadSubscriptions]);

    useEffect(() => { loadSubscriptions(); }, [loadSubscriptions]);
    return { subscriptions, loading, error, loadSubscriptions, updateSubscription };
}
