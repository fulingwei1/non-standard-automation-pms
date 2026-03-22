import { useState, useCallback, useEffect } from 'react';
import { productionApi } from '../../../services/api';
import { getItemsCompat } from '../../../utils/apiResponse';

export function useProductionPlanList() {
  const [plans, setPlans] = useState([]);
  const [loading, setLoading] = useState(true);
  const [filters, setFilters] = useState({ status: '' });

  const loadPlans = useCallback(async () => {
    try {
      setLoading(true);
      const params = { ...filters };
      if (!params.status || params.status === 'all') {
        delete params.status;
      }
      const response = await productionApi.productionPlans.list(params);
      setPlans(getItemsCompat(response));
    } catch (err) {
      setPlans([]);
    } finally {
      setLoading(false);
    }
  }, [filters]);

  useEffect(() => {
    loadPlans();
  }, [loadPlans]);

  return { plans, loading, filters, setFilters, loadPlans };
}
