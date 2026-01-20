import { useState, useCallback, useEffect } from 'react';
import { costApi } from '../../../services/api';

export function useCostAccounting() {
    const [costs, setCosts] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ project_id: '', range: 'month' });

    const loadCosts = useCallback(async () => {
        try {
            setLoading(true);
            const params = { ...filters };
            const response = await costApi.list(params);
            setCosts(response.data?.items || response.data || []);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, [filters]);

    useEffect(() => { loadCosts(); }, [loadCosts]);
    return { costs, loading, filters, setFilters, loadCosts };
}
