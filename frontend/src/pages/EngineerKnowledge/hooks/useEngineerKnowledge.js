import { useState, useCallback, useEffect } from 'react';
import { lessonsApi as engineerKnowledgeApi } from '../../../services/api';

export function useEngineerKnowledge() {
    const [articles, setArticles] = useState([]);
    const [loading, setLoading] = useState(true);
    const [filters, setFilters] = useState({ category: '', tag: '' });

    const loadArticles = useCallback(async () => {
        try {
            setLoading(true);
            const params = { page_size: 50 };
            if (filters.category) params.category = filters.category;
            if (filters.tag) params.tag = filters.tag;
            const response = await engineerKnowledgeApi.list(params);
            setArticles(response.data?.items || response.data?.items || response.data || []);
        } catch (err) { console.error(err); }
        finally { setLoading(false); }
    }, [filters]);

    useEffect(() => { loadArticles(); }, [loadArticles]);
    return { articles, loading, filters, setFilters, loadArticles };
}
