import { useState, useCallback, useEffect } from 'react';
import { projectReviewApi } from '../../../services/api';

/**
 * 项目评审详情数据 Hook
 */
export function useProjectReviewDetail(reviewId) {
    const [review, setReview] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [comments, setComments] = useState([]);

    const loadReview = useCallback(async () => {
        if (!reviewId) return;
        try {
            setLoading(true);
            const response = await projectReviewApi.get(reviewId);
            setReview(response.data || response);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [reviewId]);

    const loadComments = useCallback(async () => {
        if (!reviewId) return;
        try {
            const response = await projectReviewApi.getComments(reviewId);
            setComments(response.data || response || []);
        } catch (err) {
            console.error('Failed to load comments:', err);
        }
    }, [reviewId]);

    const addComment = useCallback(async (content) => {
        try {
            await projectReviewApi.addComment(reviewId, { content });
            await loadComments();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [reviewId, loadComments]);

    const submitDecision = useCallback(async (decision, comment) => {
        try {
            await projectReviewApi.submitDecision(reviewId, { decision, comment });
            await loadReview();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [reviewId, loadReview]);

    useEffect(() => { loadReview(); loadComments(); }, [loadReview, loadComments]);

    return { review, loading, error, comments, loadReview, addComment, submitDecision };
}
