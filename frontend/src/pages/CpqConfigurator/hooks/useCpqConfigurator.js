import { useState, useCallback, useEffect } from 'react';
import { quoteApi as cpqApi } from '../../../services/api';

export function useCpqConfigurator() {
    const [configuration, setConfiguration] = useState({});
    const [price, setPrice] = useState(null);
    const [loading, setLoading] = useState(false);
    const [rules, setRules] = useState([]);

    const loadRules = useCallback(async () => {
        try {
            const response = await cpqApi.getRules();
            setRules(response.data || response || []);
        } catch (err) { console.error(err); }
    }, []);

    const calculatePrice = useCallback(async (config) => {
        try {
            setLoading(true);
            const response = await cpqApi.calculatePrice(config);
            setPrice(response.data?.price || response.price || 0);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { loadRules(); }, [loadRules]);

    return { configuration, setConfiguration, price, loading, rules, calculatePrice };
}
