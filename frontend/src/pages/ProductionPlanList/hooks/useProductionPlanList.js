import { useState, useCallback, useEffect } from 'react';
import { productionApi } from '../../../services/api';

export function useProductionPlanList() {
    const [plans, setPlans] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ status: '' });

    const loadPlans = useCallback(async () => {
        try {
            setLoading(true);
            const params = { ...filters };
            const response = await productionApi.listPlans(params);
            setPlans(response.data?.items || response.data || []);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, [filters]);

    useEffect(() => { loadPlans(); }, [loadPlans]);
    return { plans, loading, filters, setFilters, loadPlans };
}
