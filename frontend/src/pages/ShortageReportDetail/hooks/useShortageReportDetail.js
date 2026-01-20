import { useState, useCallback, useEffect } from 'react';
import { shortageReportApi } from '../../../services/api';

export function useShortageReportDetail(reportId) {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadReport = useCallback(async () => {
        if (!reportId) return;
        try {
            setLoading(true);
            const response = await shortageReportApi.get(reportId);
            setReport(response.data || response);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [reportId]);

    const updateReport = useCallback(async (data) => {
        try { await shortageReportApi.update(reportId, data); await loadReport(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [reportId, loadReport]);

    useEffect(() => { loadReport(); }, [loadReport]);
    return { report, loading, error, loadReport, updateReport };
}
