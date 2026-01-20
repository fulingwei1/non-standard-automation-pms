import { useState, useCallback, useEffect } from 'react';
import { knowledgeApi } from '../../../services/api';

/**
 * 服务知识库数据 Hook
 */
export function useKnowledgeBase() {
    const [articles, setArticles] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ keyword: '', category: '' });

    const loadArticles = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.keyword) params.keyword = filters.keyword;
            if (filters.category && filters.category !== 'all') params.category = filters.category;

            const response = await knowledgeApi.list(params);
            setArticles(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [filters]);

    const loadCategories = useCallback(async () => {
        try {
            const response = await knowledgeApi.getCategories();
            setCategories(response.data || response || []);
        } catch (err) {
            console.error('Failed to load categories:', err);
        }
    }, []);

    const createArticle = useCallback(async (data) => {
        try {
            await knowledgeApi.create(data);
            await loadArticles();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadArticles]);

    useEffect(() => { loadCategories(); loadArticles(); }, [loadCategories, loadArticles]);

    return { articles, categories, loading, error, filters, setFilters, loadArticles, createArticle };
}
