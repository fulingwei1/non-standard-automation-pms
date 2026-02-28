import { useState, useCallback, useEffect } from 'react';
import { knowledgeBaseApi } from '../../../services/api';

export function useKnowledgeBase() {
    const [articles, setArticles] = useState([]);
    const [categories, setCategories] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [filters, setFilters] = useState({ category: '', keyword: '' });

    const loadArticles = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.category && filters.category !== 'all') params.category = filters.category;
            if (filters.keyword) params.keyword = filters.keyword;
            const response = await knowledgeBaseApi.listArticles(params);
            setArticles(response.data?.items || response.data?.items || response.data || []);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [filters]);

    const loadCategories = useCallback(async () => {
        try {
            const response = await knowledgeBaseApi.getCategories();
            setCategories(response.data || response || []);
        } catch (err) { console.error(err); }
    }, []);

    useEffect(() => { loadCategories(); loadArticles(); }, [loadCategories, loadArticles]);
    return { articles, categories, loading, error, filters, setFilters, loadArticles };
}
