import { useState, useCallback, useEffect, useMemo } from 'react';
import { salesApi } from '../../../services/api';

/**
 * 商机看板数据 Hook
 */
export function useOpportunityBoard() {
    const [opportunities, setOpportunities] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);
    const [viewMode, setViewMode] = useState('kanban'); // kanban, list, funnel

    const loadOpportunities = useCallback(async () => {
        try {
            setLoading(true);
            const response = await salesApi.listOpportunities({ page_size: 100 });
            setOpportunities(response.data?.items || response.data || []);
        } catch (err) {
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    const updateStage = useCallback(async (id, stage) => {
        try {
            await salesApi.updateOpportunity(id, { stage });
            await loadOpportunities();
            return { success: true };
        } catch (err) {
            return { success: false, error: err.response?.data?.detail || err.message };
        }
    }, [loadOpportunities]);

    const pipelineData = useMemo(() => {
        const stages = ['initial', 'qualified', 'proposal', 'negotiation', 'closed_won', 'closed_lost'];
        return stages.map(stage => ({
            stage,
            items: opportunities.filter(o => o.stage === stage),
            total: opportunities.filter(o => o.stage === stage).reduce((sum, o) => sum + (o.expected_revenue || 0), 0),
        }));
    }, [opportunities]);

    const stats = useMemo(() => ({
        total: opportunities.length,
        totalValue: opportunities.reduce((sum, o) => sum + (o.expected_revenue || 0), 0),
        avgValue: opportunities.length > 0
            ? opportunities.reduce((sum, o) => sum + (o.expected_revenue || 0), 0) / opportunities.length
            : 0,
        winRate: opportunities.length > 0
            ? (opportunities.filter(o => o.stage === 'closed_won').length / opportunities.length * 100).toFixed(1)
            : 0,
    }), [opportunities]);

    useEffect(() => { loadOpportunities(); }, [loadOpportunities]);

    return { opportunities, loading, error, viewMode, setViewMode, pipelineData, stats, loadOpportunities, updateStage };
}
