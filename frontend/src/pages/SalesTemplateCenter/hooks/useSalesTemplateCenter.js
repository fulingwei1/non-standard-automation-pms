import { useState, useCallback, useEffect } from 'react';
import { salesTemplateApi } from '../../../services/api';

/**
 * 销售模板中心数据 Hook
 */
export function useSalesTemplateCenter() {
    const [templates, setTemplates] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ category: '', keyword: '' });

    const loadTemplates = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 100 };
            if (filters.category && filters.category !== 'all') params.category = filters.category;
            if (filters.keyword) params.keyword = filters.keyword;

            const response = await salesTemplateApi.list(params);
            setTemplates(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const loadCategories = useCallback(async () => {
        try {
            const response = await salesTemplateApi.getCategories();
            setCategories(response.data || response || []);
        } catch (err) {
            console.error('Failed to load categories:', err);
        }
    }, []);

    const createTemplate = useCallback(async (data) => {
        try {
            await salesTemplateApi.create(data);
            await loadTemplates();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTemplates]);

    const duplicateTemplate = useCallback(async (id) => {
        try {
            await salesTemplateApi.duplicate(id);
            await loadTemplates();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadTemplates]);

    useEffect(() => { loadCategories(); loadTemplates(); }, [loadCategories, loadTemplates]);

    return { templates, categories, loading, error, filters, setFilters, loadTemplates, createTemplate, duplicateTemplate };
}
