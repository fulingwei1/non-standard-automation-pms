import { useState, useCallback, useEffect } from 'react';
import { kitApi } from '../../../services/api';

export function useKitCheck() {
    const [kits, setKits] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ project_id: '', status: '' });

    const loadKits = useCallback(async () => {
        try {
            setLoading(true);
            const response = await kitApi.list(filters);
            setKits(response.data?.items || response.data?.items || response.data || []);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, [filters]);

    useEffect(() => { loadKits(); }, [loadKits]);
    return { kits, loading, filters, setFilters, loadKits };
}
