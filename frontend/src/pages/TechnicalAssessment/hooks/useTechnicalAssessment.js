import { useState, useCallback, useEffect } from 'react';
import { assessmentApi } from '../../../services/api';

/**
 * 技术评估数据 Hook
 */
export function useTechnicalAssessment() {
    const [assessments, setAssessments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', type: '' });

    const loadAssessments = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.type && filters.type !== 'all') params.type = filters.type;

            const response = await assessmentApi.list(params);
            setAssessments(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const createAssessment = useCallback(async (data) => {
        try {
            await assessmentApi.create(data);
            await loadAssessments();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadAssessments]);

    const submitAssessment = useCallback(async (id, result) => {
        try {
            await assessmentApi.submit(id, result);
            await loadAssessments();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadAssessments]);

    useEffect(() => { loadAssessments(); }, [loadAssessments]);

    return { assessments, loading, error, filters, setFilters, loadAssessments, createAssessment, submitAssessment };
}
