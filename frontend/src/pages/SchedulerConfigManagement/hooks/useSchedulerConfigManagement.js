import { useState, useCallback, useEffect } from 'react';
import { schedulerConfigApi } from '../../../services/api';

export function useSchedulerConfigManagement() {
    const [configs, setConfigs] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadConfigs = useCallback(async () => {
        try {
            setLoading(true);
            const response = await schedulerConfigApi.list();
            setConfigs(response.data || response || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, []);

    const updateConfig = useCallback(async (id, data) => {
        try { await schedulerConfigApi.update(id, data); await loadConfigs(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadConfigs]);

    const toggleJob = useCallback(async (id, enabled) => {
        try { await schedulerConfigApi.toggle(id, { enabled }); await loadConfigs(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadConfigs]);

    useEffect(() => { loadConfigs(); }, [loadConfigs]);
    return { configs, loading, error, loadConfigs, updateConfig, toggleJob };
}
