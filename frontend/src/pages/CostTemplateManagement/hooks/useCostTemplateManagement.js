import { useState, useCallback, useEffect } from 'react';
import { salesTemplateApi as costTemplateApi } from '../../../services/api';

/**
 * 成本模板管理数据 Hook
 */
export function useCostTemplateManagement() {
    const [templates, setTemplates] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ type: '', status: '' });

    const loadTemplates = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.type && filters.type !== 'all') params.type = filters.type;
            if (filters.status && filters.status !== 'all') params.status = filters.status;

            const response = await costTemplateApi.list(params);
            setTemplates(response.data?.items || response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const createTemplate = useCallback(async (data) => {
        try {
            await costTemplateApi.create(data);
            await loadTemplates();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTemplates]);

    const updateTemplate = useCallback(async (id, data) => {
        try {
            await costTemplateApi.update(id, data);
            await loadTemplates();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTemplates]);

    const duplicateTemplate = useCallback(async (id) => {
        try {
            await costTemplateApi.duplicate(id);
            await loadTemplates();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTemplates]);

    useEffect(() => { loadTemplates(); }, [loadTemplates]);

    return { templates, loading, error, filters, setFilters, loadTemplates, createTemplate, updateTemplate, duplicateTemplate };
}
