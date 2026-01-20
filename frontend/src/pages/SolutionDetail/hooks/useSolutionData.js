import { useState, useCallback, useEffect } from 'react';
import { presaleApi } from '../../../services/api';

/**
 * 方案详情数据管理 Hook
 */
export function useSolutionData(solutionId) {
    const [solution, setSolution] = useState(null);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [activeTab, setActiveTab] = useState('overview');

    // 加载方案详情
    const loadSolution = useCallback(async () => {
        if (!solutionId) return;

        try {
            setLoading(true);
            setError(null);
            const response = await presaleApi.getSolution(solutionId);
            setSolution(response.data || response);
        } catch (err) {
            console.error('Failed to load solution:', err);
            setError(err.response?.data?.detail || err.message);
        } finally {
            setLoading(false);
        }
    }, [solutionId]);

    // 更新方案
    const updateSolution = useCallback(async (data) => {
        try {
            const response = await presaleApi.updateSolution(solutionId, data);
            setSolution(response.data || response);
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [solutionId]);

    // 提交审批
    const submitForApproval = useCallback(async () => {
        try {
            await presaleApi.submitSolutionForApproval(solutionId);
            await loadSolution();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [solutionId, loadSolution]);

    useEffect(() => {
        loadSolution();
    }, [loadSolution]);

    return {
        solution,
        loading,
        error,
        activeTab,
        setActiveTab,
        loadSolution,
        updateSolution,
        submitForApproval,
    };
}
