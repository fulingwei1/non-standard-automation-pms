import { useState, useEffect, useCallback } from "react";
import {
    salesStatisticsApi,
    opportunityApi,
    customerApi,
    contractApi,
    invoiceApi,
    projectApi,
    quoteApi,
    taskCenterApi
} from "../../../services/api";
import { DEFAULT_STATS } from "../constants";
import {
    transformOpportunity,
    transformCustomer,
    transformInvoiceToPayment,
    transformProject,
    transformTaskToTodo,
    isCurrentMonth
} from "../utils/transforms";

export function useSalesWorkstation() {
    const [todos, setTodos] = useState([]);
    const [stats, setStats] = useState({ ...DEFAULT_STATS });
    const [customers, setCustomers] = useState([]);
    const [projects, setProjects] = useState([]);
    const [payments, setPayments] = useState([]);
    const [opportunities, setOpportunities] = useState([]);
    const [funnelData, setFunnelData] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState(null);

    const loadStatistics = useCallback(async () => {
        try {
            setLoading(true);
            setError(null);

            const now = new Date();
            const startDate = new Date(now.getFullYear(), now.getMonth(), 1).toISOString().split("T")[0];
            const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0).toISOString().split("T")[0];
            const params = { start_date: startDate, end_date: endDate };

            const results = await Promise.allSettled([
                salesStatisticsApi.summary(params),
                salesStatisticsApi.funnel(params),
                opportunityApi.list({ page: 1, page_size: 100 }),
                customerApi.list({ page: 1, page_size: 10 }),
                contractApi.list({ page: 1, page_size: 10, status: "SIGNED" }).catch(() => ({ data: { items: [] } })),
                invoiceApi.list({ page: 1, page_size: 10 }).catch(() => ({ data: { items: [] } }))
            ]);

            const getValue = (result, fallback = {}) => result.status === "fulfilled" ? result.value : fallback;

            const summaryResponse = getValue(results[0], { data: {} });
            const funnelResponse = getValue(results[1], { data: {} });
            const opportunitiesResponse = getValue(results[2], { data: { items: [] } });
            const customersResponse = getValue(results[3], { data: { items: [] } });
            const contractsResponse = getValue(results[4], { data: { items: [] } });
            const invoicesResponse = getValue(results[5], { data: { items: [] } });

            if (results[0].status === "rejected" && results[1].status === "rejected") {
                throw new Error("无法加载销售统计数据");
            }

            const summaryData = summaryResponse.data?.data || summaryResponse.data || summaryResponse;
            const funnelPayload = funnelResponse.data?.data || funnelResponse.data || {};
            const oppsData = opportunitiesResponse.data?.items || opportunitiesResponse.data || [];
            const customersData = customersResponse.data?.items || customersResponse.data || [];
            const contractsData = contractsResponse.data?.items || contractsResponse.data || [];
            const invoicesData = invoicesResponse.data?.items || invoicesResponse.data || [];

            const normalizedOpportunities = oppsData.map(transformOpportunity);
            setOpportunities(normalizedOpportunities.slice(0, 5));
            const hotOpportunities = normalizedOpportunities.filter((opp) => opp.isHot).length;

            const normalizedCustomers = customersData.slice(0, 3).map(transformCustomer);
            setCustomers(normalizedCustomers);
            const newCustomerCount = normalizedCustomers.filter((c) => isCurrentMonth(c.createdAt)).length;
            const totalCustomers = customersResponse.data?.total ?? customersData.length;

            const paymentEntries = invoicesData.map(transformInvoiceToPayment);
            setPayments(paymentEntries);
            const pendingPayment = paymentEntries.filter((p) => p.status === "pending" || p.status === "invoiced").reduce((sum, p) => sum + (p.amount || 0), 0);
            const overduePayment = paymentEntries.filter((p) => {
                if (p.status === "overdue") return true;
                if (p.status !== "paid" && p.dueDate) return new Date(p.dueDate) < new Date();
                return false;
            }).reduce((sum, p) => sum + (p.amount || 0), 0);

            const projectIds = contractsData.map((c) => c.project_id).filter(Boolean).slice(0, 3);
            const projectDetails = await Promise.all(
                projectIds.map(async (projectId) => {
                    try {
                        const projectResponse = await projectApi.get(projectId);
                        const projectData = projectResponse.data || projectResponse;
                        return transformProject(projectData);
                    } catch (err) {
                        console.error(`Failed to load project ${projectId}:`, err);
                        return null;
                    }
                })
            );
            setProjects(projectDetails.filter(Boolean));

            const funnelCounts = {
                lead: funnelPayload.leads || 0,
                contact: funnelPayload.opportunities || 0,
                quote: funnelPayload.quotes || 0,
                negotiate: Math.max((funnelPayload.contracts || 0) - (summaryData?.won_opportunities || 0), 0),
                won: summaryData?.won_opportunities || funnelPayload.contracts || 0
            };
            setFunnelData(funnelCounts);

            setStats({
                monthlyTarget: summaryData?.monthly_target || DEFAULT_STATS.monthlyTarget,
                monthlyAchieved: summaryData?.total_contract_amount || 0,
                opportunityCount: summaryData?.total_opportunities || normalizedOpportunities.length,
                hotOpportunities,
                pendingPayment,
                overduePayment,
                customerCount: totalCustomers || summaryData?.total_leads || 0,
                newCustomers: newCustomerCount
            });
        } catch (err) {
            console.error("Failed to load sales statistics:", err);
            setError(err.response?.data?.detail || err.message || "加载销售数据失败");
            setStats({ ...DEFAULT_STATS });
            setFunnelData(null);
            setOpportunities([]);
            setCustomers([]);
            setProjects([]);
            setPayments([]);
        } finally {
            setLoading(false);
        }
    }, []);

    const loadTodos = useCallback(async () => {
        try {
            const results = await Promise.allSettled([
                taskCenterApi.myTasks({ page: 1, page_size: 10, status: "IN_PROGRESS" }),
                quoteApi.list({ status: "SUBMITTED", page_size: 5 })
            ]);

            const tasksResponse = results[0].status === "fulfilled" ? results[0].value : { data: { items: [] } };
            const quotesResponse = results[1].status === "fulfilled" ? results[1].value : { data: { items: [] } };

            const taskItems = tasksResponse.data?.items || tasksResponse.data || [];
            const taskTodos = taskItems.map(transformTaskToTodo);

            const quotes = quotesResponse.data?.items || quotesResponse.data || [];
            const approvalTodos = [];
            await Promise.all(
                quotes.slice(0, 3).map(async (quote) => {
                    try {
                        const statusResponse = await quoteApi.getApprovalStatus(quote.id);
                        const statusData = statusResponse.data?.data || statusResponse.data || statusResponse;
                        if ((statusData.status || statusData.approval_status) === "PENDING") {
                            approvalTodos.push({
                                id: `approval-quote-${quote.id}`,
                                type: "approval",
                                title: `报价审批 - ${quote.quote_code || quote.code}`,
                                target: quote.customer?.customer_name || quote.customer_name || "",
                                time: "待审批",
                                priority: "high",
                                done: false
                            });
                        }
                    } catch (err) {
                        console.error("Failed to load quote approval status:", err);
                    }
                })
            );

            setTodos([...taskTodos, ...approvalTodos]);
        } catch (err) {
            console.error("Failed to load todos:", err);
            setTodos([]);
        }
    }, []);

    useEffect(() => {
        loadStatistics();
        loadTodos();
    }, [loadStatistics, loadTodos]);

    const achievementRate = stats.monthlyTarget > 0 ? (stats.monthlyAchieved / stats.monthlyTarget * 100).toFixed(1) : "0";

    const toggleTodo = (id) => {
        setTodos((prev) => prev.map((t) => t.id === id ? { ...t, done: !t.done } : t));
    };

    return {
        todos,
        stats,
        customers,
        projects,
        payments,
        opportunities,
        funnelData,
        loading,
        error,
        achievementRate,
        toggleTodo,
        refresh: loadStatistics
    };
}
