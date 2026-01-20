import { useState, useCallback, useEffect } from 'react';
import { projectApi } from '../../../services/api';

/**
 * 项目阶段管理数据 Hook
 */
export function useProjectPhaseData(projectId) {
    const [phases, setPhases] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [currentPhase, setCurrentPhase] = useState(null);

    const loadPhases = useCallback(async () => {
        if (!projectId) return;
        try {
            setLoading(true);
            const response = await projectApi.getPhases(projectId);
            setPhases(response.data || response || []);
            const current = (response.data || response || []).find(p => p.status === 'active');
            setCurrentPhase(current);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, [projectId]);

    const updatePhase = useCallback(async (phaseId, data) => {
        try {
            await projectApi.updatePhase(projectId, phaseId, data);
            await loadPhases();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [projectId, loadPhases]);

    const completePhase = useCallback(async (phaseId) => {
        try {
            await projectApi.completePhase(projectId, phaseId);
            await loadPhases();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [projectId, loadPhases]);

    useEffect(() => { loadPhases(); }, [loadPhases]);

    return { phases, loading, error, currentPhase, loadPhases, updatePhase, completePhase };
}
