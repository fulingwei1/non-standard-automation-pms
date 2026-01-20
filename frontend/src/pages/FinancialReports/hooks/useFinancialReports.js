import { useState, useCallback, useEffect } from 'react';
import { reportApi } from '../../../services/api';

/**
 * 财务报表数据 Hook
 */
export function useFinancialReports() {
    const [reports, setReports] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ type: '', period: '', year: new Date().getFullYear() });

    const loadReports = useCallback(async () => {
        try {
            setLoading(true);
            const params = { year: filters.year };
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.period && filters.period !== 'all') params.period = filters.period;

            const response = await reportApi.listFinancial(params);
            setReports(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const generateReport = useCallback(async (type, params) => {
        try {
            const response = await reportApi.generateFinancial(type, params);
            await loadReports();
            return { success: true, data: response.data || response };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadReports]);

    const exportReport = useCallback(async (id, format) => {
        try {
            const response = await reportApi.exportFinancial(id, format);
            return { success: true, data: response.data };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, []);

    useEffect(() => { loadReports(); }, [loadReports]);

    return { reports, loading, error, filters, setFilters, loadReports, generateReport, exportReport };
}
