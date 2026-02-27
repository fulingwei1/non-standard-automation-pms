import { useState, useCallback, useEffect } from 'react';
import { shortageApi } from '../../../services/api';

export function useShortageReportDetail(reportId) {
    const [report, setReport] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadReport = useCallback(async () => {
        if (!reportId) return;
        try {
            setLoading(true);
            const response = await shortageApi.reports.get(reportId);
            setReport(response.data || response);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [reportId]);

    const confirmReport = useCallback(async () => {
        try { await shortageApi.reports.confirm(reportId); await loadReport(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [reportId, loadReport]);

    const handleReport = useCallback(async (data) => {
        try { await shortageApi.reports.handle(reportId, data); await loadReport(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [reportId, loadReport]);

    const resolveReport = useCallback(async () => {
        try { await shortageApi.reports.resolve(reportId); await loadReport(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [reportId, loadReport]);

    const rejectReport = useCallback(async (reason) => {
        try { await shortageApi.reports.reject(reportId, reason); await loadReport(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [reportId, loadReport]);

    useEffect(() => { loadReport(); }, [loadReport]);
    return { report, loading, error, loadReport, confirmReport, handleReport, resolveReport, rejectReport };
}
