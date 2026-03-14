import { useState, useCallback, useEffect } from 'react';
import { workerApi } from '../../../services/api';
import { getItemsCompat } from '../../../utils/apiResponse';

export function useWorkerManagement() {
  const [workers, setWorkers] = useState([]);
  const [loading, setLoading] = useState(true);

  const loadWorkers = useCallback(async () => {
    try {
      setLoading(true);
      const response = await workerApi.list({ page_size: 100 });
      setWorkers(getItemsCompat(response));
    } catch (err) {
      console.error(err);
      setWorkers([]);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadWorkers();
  }, [loadWorkers]);

  return { workers, loading, loadWorkers };
}
