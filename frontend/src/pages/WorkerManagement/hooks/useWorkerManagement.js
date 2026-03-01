import { useState, useCallback, useEffect } from 'react';
import { productionApi as workerApi } from '../../../services/api';

export function useWorkerManagement() {
    const [workers, setWorkers] = useState([]);
    const [loading, setLoading] = useState(true);

    const loadWorkers = useCallback(async () => {
        try {
            setLoading(true);
            const response = await workerApi.list();
            setWorkers(response.data || response || []);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, []);

    useEffect(() => { loadWorkers(); }, [loadWorkers]);
    return { workers, loading, loadWorkers };
}
