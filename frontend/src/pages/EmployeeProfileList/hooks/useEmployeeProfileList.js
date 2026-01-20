import { useState, useCallback, useEffect } from 'react';
import { employeeApi } from '../../../services/api';

export function useEmployeeProfileList() {
    const [employees, setEmployees] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ dept: '', status: '' });

    const loadEmployees = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.dept && filters.dept !== 'all') params.dept = filters.dept;
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            const response = await employeeApi.list(params);
            setEmployees(response.data?.items || response.data || []);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, [filters]);

    useEffect(() => { loadEmployees(); }, [loadEmployees]);
    return { employees, loading, filters, setFilters, loadEmployees };
}
