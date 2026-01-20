import { useState, useCallback, useEffect } from 'react';
import { quoteApi, customerApi } from '../../../services/api';

export function useQuoteCreateEdit(quoteId) {
    const [quote, setQuote] = useState(null);
    const [customers, setCustomers] = useState([]);
    const [loading, setLoading] = useState(true);
    const [saving, setSaving] = useState(false);

    const loadQuote = useCallback(async () => {
        if (!quoteId) { setLoading(false); return; }
        try {
            setLoading(true);
            const response = await quoteApi.get(quoteId);
            setQuote(response.data || response);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, [quoteId]);

    const loadCustomers = useCallback(async () => {
        try {
            const response = await customerApi.list({ page_size: 100 });
            setCustomers(response.data?.items || response.data || []);
        } catch (err) { console.error(err); }
    }, []);

    const saveQuote = useCallback(async (data) => {
        try {
            setSaving(true);
            if (quoteId) { await quoteApi.update(quoteId, data); }
            else { await quoteApi.create(data); }
            return { success: true };
        } catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
        finally { setSaving(false); }
    }, [quoteId]);

    useEffect(() => { loadCustomers(); loadQuote(); }, [loadCustomers, loadQuote]);
    return { quote, customers, loading, saving, loadQuote, saveQuote };
}
