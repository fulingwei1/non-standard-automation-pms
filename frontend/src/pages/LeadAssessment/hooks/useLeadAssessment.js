import { useState, useCallback, useEffect } from 'react';
import { leadAssessmentApi } from '../../../services/api';

export function useLeadAssessment() {
    const [assessments, setAssessments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', result: '' });

    const loadAssessments = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.result && filters.result !== 'all') params.result = filters.result;
            const response = await leadAssessmentApi.list(params);
            setAssessments(response.data?.items || response.data || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [filters]);

    const submitAssessment = useCallback(async (id, data) => {
        try { await leadAssessmentApi.submit(id, data); await loadAssessments(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [loadAssessments]);

    useEffect(() => { loadAssessments(); }, [loadAssessments]);
    return { assessments, loading, error, filters, setFilters, loadAssessments, submitAssessment };
}
