import { useState, useCallback, useEffect, useMemo } from 'react';
import { salesApi, projectApi, customerApi } from '../../../services/api';

/**
 * 销售工作台数据管理 Hook
 */
export function useSalesWorkstationData() {
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState(null);

    // 数据状态
    const [leads, setLeads] = useState([]);
    const [opportunities, setOpportunities] = useState([]);
    const [projects, setProjects] = useState([]);
    const [customers, setCustomers] = useState([]);

    // 统计数据
    const [stats, setStats] = useState({
        totalLeads: 0,
        newLeadsThisMonth: 0,
        conversionRate: 0,
        totalRevenue: 0,
    });

    // 加载仪表板数据
    const loadDashboardData = useCallback(async () => {
        try {
            setLoading(true);

            // 并行加载各项数据
            const [leadsRes, oppsRes, projectsRes, customersRes] = await Promise.all([
                salesApi.listLeads({ page_size: 20 }),
                salesApi.listOpportunities({ page_size: 20 }),
                projectApi.list({ page_size: 20, status: 'active' }),
                customerApi.list({ page_size: 50 }),
            ]);

            setLeads(leadsRes.data?.items || leadsRes.data || []);
            setOpportunities(oppsRes.data?.items || oppsRes.data || []);
            setProjects(projectsRes.data?.items || projectsRes.data || []);
            setCustomers(customersRes.data?.items || customersRes.data || []);

            // 计算统计数据
            const leadsData = leadsRes.data?.items || leadsRes.data || [];
            const oppsData = oppsRes.data?.items || oppsRes.data || [];

            setStats({
                totalLeads: leadsData.length,
                newLeadsThisMonth: leadsData.filter(l => {
                    const created = new Date(l.created_at);
                    const now = new Date();
                    return created.getMonth() === now.getMonth() &&
                        created.getFullYear() === now.getFullYear();
                }).length,
                conversionRate: leadsData.length > 0
                    ? Math.round((oppsData.length / leadsData.length) * 100)
                    : 0,
                totalRevenue: oppsData.reduce((sum, o) => sum + (o.expected_revenue || 0), 0),
            });

        } catch (err) {
            console.error('Failed to load dashboard data:', err);
            setError(err.message);
        } finally {
            setLoading(false);
        }
    }, []);

    // 创建线索
    const createLead = useCallback(async (data) => {
        try {
            await salesApi.createLead(data);
            await loadDashboardData();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadDashboardData]);

    // 转换为商机
    const convertToOpportunity = useCallback(async (leadId, data) => {
        try {
            await salesApi.convertLead(leadId, data);
            await loadDashboardData();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadDashboardData]);

    // 更新商机阶段
    const updateOpportunityStage = useCallback(async (id, stage) => {
        try {
            await salesApi.updateOpportunity(id, { stage });
            await loadDashboardData();
            return { success: true };
        } catch (err) {
            return {
                success: false,
                error: err.response?.data?.detail || err.message
            };
        }
    }, [loadDashboardData]);

    // 管道视图数据
    const pipelineData = useMemo(() => {
        const stages = ['initial', 'qualified', 'proposal', 'negotiation', 'closed'];
        return stages.map(stage => ({
            stage,
            opportunities: opportunities.filter(o => o.stage === stage),
            total: opportunities.filter(o => o.stage === stage)
                .reduce((sum, o) => sum + (o.expected_revenue || 0), 0),
        }));
    }, [opportunities]);

    useEffect(() => {
        loadDashboardData();
    }, [loadDashboardData]);

    return {
        loading,
        error,
        leads,
        opportunities,
        projects,
        customers,
        stats,
        pipelineData,
        loadDashboardData,
        createLead,
        convertToOpportunity,
        updateOpportunityStage,
    };
}
