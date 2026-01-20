import { useState, useCallback, useEffect } from 'react';
import { technicalReviewApi } from '../../../services/api';

export function useTechnicalReviewDetail(reviewId) {
    const [review, setReview] = useState(null);
    const [comments, setComments] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    const loadReview = useCallback(async () => {
        if (!reviewId) return;
        try {
            setLoading(true);
            const response = await technicalReviewApi.get(reviewId);
            setReview(response.data || response);
        } catch (err) { setError(err.message); }
        finally { setLoading(false); }
    }, [reviewId]);

    const loadComments = useCallback(async () => {
        if (!reviewId) return;
        try {
            const response = await technicalReviewApi.getComments(reviewId);
            setComments(response.data || response || []);
        } catch (err) { console.error(err); }
    }, [reviewId]);

    const submitDecision = useCallback(async (decision, comment) => {
        try { await technicalReviewApi.submitDecision(reviewId, { decision, comment }); await loadReview(); return { success: true }; }
        catch (err) { return { success: false, error: err.response?.data?.detail || err.message }; }
    }, [reviewId, loadReview]);

    useEffect(() => { loadReview(); loadComments(); }, [loadReview, loadComments]);
    return { review, comments, loading, error, loadReview, loadComments, submitDecision };
}
