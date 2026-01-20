import { useState, useCallback, useEffect } from 'react';
import { quoteApi } from '../../../services/api';

export function useQuoteCostAnalysis(quoteId) {
    const [analysis, setAnalysis] = useState(null);
    const [loading, setLoading] = useState(true);

    const loadAnalysis = useCallback(async () => {
        if (!quoteId) return;
        try {
            setLoading(true);
            const response = await quoteApi.getCostAnalysis(quoteId);
            setAnalysis(response.data || response);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, [quoteId]);

    useEffect(() => { loadAnalysis(); }, [loadAnalysis]);
    return { analysis, loading, loadAnalysis };
}
