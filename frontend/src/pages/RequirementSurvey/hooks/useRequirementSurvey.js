import { useState, useCallback, useEffect } from 'react';
import { surveyApi } from '../../../services/api/survey';

/**
 * 需求调研数据 Hook
 */
export function useRequirementSurvey() {
    const [surveys, setSurveys] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ status: '', customer_id: '' });

    const loadSurveys = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.status && filters.status !== 'all') params.status = filters.status;
            if (filters.customer_id) params.customer_id = filters.customer_id;

            const response = await surveyApi.list(params);
            setSurveys(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const createSurvey = useCallback(async (data) => {
        try {
            await surveyApi.create(data);
            await loadSurveys();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadSurveys]);

    const updateSurvey = useCallback(async (id, data) => {
        try {
            await surveyApi.update(id, data);
            await loadSurveys();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadSurveys]);

    const submitSurvey = useCallback(async (id) => {
        try {
            await surveyApi.submit(id);
            await loadSurveys();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadSurveys]);

    useEffect(() => { loadSurveys(); }, [loadSurveys]);

    return { surveys, loading, error, filters, setFilters, loadSurveys, createSurvey, updateSurvey, submitSurvey };
}
