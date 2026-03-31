import { useState, useEffect, useCallback } from "react";
import { serviceApi } from "../../../services/api";
import { emptyFallback, RESPONSE_TIME_RANGES } from "../constants";

/**
 * Fetches and computes all analytics data for the ServiceAnalytics page.
 *
 * Returns:
 *   analytics  – computed analytics object (or null while loading for the first time)
 *   loading    – true while a fetch is in-flight
 *   error      – error message string (or null)
 *   period     – active period string ("DAILY" | "WEEKLY" | "MONTHLY" | "YEARLY")
 *   setPeriod  – setter for period
 *   reload     – manually re-trigger the fetch
 */
export function useServiceAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading]     = useState(false);
  const [error, setError]         = useState(null);
  const [period, setPeriod]       = useState("MONTHLY");

  const reload = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const [
        ticketsStats,
        satisfactionStats,
        satisfactionList,
        ticketsList,
        recordsList,
        communicationsList
      ] = await Promise.all([
        serviceApi.tickets.getStatistics().catch(() => ({ data: {} })),
        serviceApi.satisfaction.statistics().catch(() => ({ data: {} })),
        serviceApi.satisfaction
          .list({ page: 1, page_size: 1000 })
          .catch(() => ({ data: { items: [] } })),
        serviceApi.tickets
          .list({ page: 1, page_size: 1000 })
          .catch(() => ({ data: { items: [] } })),
        serviceApi.records
          .list({ page: 1, page_size: 1000 })
          .catch(() => ({ data: { items: [] } })),
        serviceApi.communications
          .list({ page: 1, page_size: 1000 })
          .catch(() => ({ data: { items: [] } }))
      ]);

      const tickets       = ticketsList.data?.items       || ticketsList.data       || [];
      const records       = recordsList.data?.items       || recordsList.data       || [];
      const communications = communicationsList.data?.items || communicationsList.data || [];
      const satisfactions = satisfactionList.data?.items  || satisfactionList.data  || [];

      const ticketsStatsData     = ticketsStats.data || {};
      const satisfactionStatsData = {
        ...(satisfactionStats.data || {}),
        items: satisfactions
      };

      // ── Overview metrics ──────────────────────────────────────────────────
      const totalTickets        = ticketsStatsData.total || tickets.length;
      const totalRecords        = records.length;
      const totalCommunications = communications.length;
      const totalSurveys        = satisfactionStatsData.total || 0;

      const ticketsWithResponseTime = tickets.filter((t) => t.response_time);
      const avgResponseTime =
        ticketsWithResponseTime.length > 0
          ? ticketsWithResponseTime.reduce((sum, t) => {
              return (
                sum +
                (new Date(t.response_time) -
                  new Date(t.reported_time || t.created_at)) /
                  (1000 * 60 * 60)
              );
            }, 0) / ticketsWithResponseTime.length
          : 2.5;

      const resolvedTickets = tickets.filter(
        (t) => t.resolved_time && t.reported_time
      );
      const avgResolutionTime =
        resolvedTickets.length > 0
          ? resolvedTickets.reduce((sum, t) => {
              return (
                sum +
                (new Date(t.resolved_time) -
                  new Date(t.reported_time || t.created_at)) /
                  (1000 * 60 * 60)
              );
            }, 0) / resolvedTickets.length
          : 8.5;

      const avgSatisfaction = satisfactionStatsData.average_score || 4.3;

      const completedTickets = tickets.filter(
        (t) => t.status === "CLOSED" || t.status === "已关闭"
      ).length;
      const completionRate =
        totalTickets > 0 ? (completedTickets / totalTickets) * 100 : 0;

      // ── Service type distribution (from records) ──────────────────────────
      const serviceTypeCounts = {};
      records.forEach((r) => {
        const type = r.service_type || "其他";
        serviceTypeCounts[type] = (serviceTypeCounts[type] || 0) + 1;
      });
      const serviceTypeDistribution = Object.entries(serviceTypeCounts).map(
        ([type, count]) => ({
          type,
          count,
          percentage:
            totalRecords > 0
              ? ((count / totalRecords) * 100).toFixed(1)
              : 0
        })
      );

      // ── Problem type distribution (from tickets) ──────────────────────────
      const problemTypeCounts = {};
      tickets.forEach((t) => {
        const type = t.problem_type || "其他";
        problemTypeCounts[type] = (problemTypeCounts[type] || 0) + 1;
      });
      const problemTypeDistribution = Object.entries(problemTypeCounts).map(
        ([type, count]) => ({
          type,
          count,
          percentage:
            tickets.length > 0
              ? ((count / tickets.length) * 100).toFixed(1)
              : 0
        })
      );

      // ── Response time distribution ────────────────────────────────────────
      const responseTimeRangeCounts = Object.fromEntries(
        RESPONSE_TIME_RANGES.map(({ key }) => [key, 0])
      );
      ticketsWithResponseTime.forEach((t) => {
        const hours =
          (new Date(t.response_time) -
            new Date(t.reported_time || t.created_at)) /
          (1000 * 60 * 60);
        const bucket = RESPONSE_TIME_RANGES.find(({ max }) => hours <= max);
        if (bucket) responseTimeRangeCounts[bucket.key]++;
      });
      const totalWithResponseTime = ticketsWithResponseTime.length;
      const responseTimeDistribution = Object.entries(responseTimeRangeCounts).map(
        ([range, count]) => ({
          range,
          count,
          percentage:
            totalWithResponseTime > 0
              ? ((count / totalWithResponseTime) * 100).toFixed(1)
              : 0
        })
      );

      // ── Ticket trends (last 4 months) ─────────────────────────────────────
      const ticketTrendsMap = {};
      tickets.forEach((t) => {
        const date  = new Date(t.reported_time || t.created_at);
        const month = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
        if (!ticketTrendsMap[month]) ticketTrendsMap[month] = { count: 0, resolved: 0 };
        ticketTrendsMap[month].count++;
        if (t.status === "CLOSED" || t.status === "已关闭") {
          ticketTrendsMap[month].resolved++;
        }
      });
      const ticketTrendsArray = Object.entries(ticketTrendsMap)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .slice(-4)
        .map(([month, data]) => ({ month, ...data }));

      // ── Satisfaction trends (last 4 months) ───────────────────────────────
      const satisfactionTrendsMap = {};
      if (satisfactionStatsData.items) {
        satisfactionStatsData.items.forEach((s) => {
          const date  = new Date(s.created_at || s.survey_date);
          const month = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
          if (!satisfactionTrendsMap[month])
            satisfactionTrendsMap[month] = { total: 0, sum: 0 };
          satisfactionTrendsMap[month].total++;
          satisfactionTrendsMap[month].sum += parseFloat(
            s.overall_score || s.score || 0
          );
        });
      }
      const satisfactionTrendsArray = Object.entries(satisfactionTrendsMap)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .slice(-4)
        .map(([month, data]) => ({
          month,
          score:
            data.total > 0
              ? parseFloat((data.sum / data.total).toFixed(1))
              : 0
        }));

      // ── Top customers (top 4 by ticket count) ────────────────────────────
      const customerTicketCounts  = {};
      const customerSatisfaction  = {};
      tickets.forEach((t) => {
        const name = t.customer_name || t.customer || "未知客户";
        customerTicketCounts[name] = (customerTicketCounts[name] || 0) + 1;
      });
      if (satisfactionStatsData.items) {
        satisfactionStatsData.items.forEach((s) => {
          const name = s.customer_name || "未知客户";
          if (!customerSatisfaction[name])
            customerSatisfaction[name] = { total: 0, sum: 0 };
          customerSatisfaction[name].total++;
          customerSatisfaction[name].sum += parseFloat(
            s.overall_score || s.score || 0
          );
        });
      }
      const topCustomersArray = Object.entries(customerTicketCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 4)
        .map(([customer, ticketCount]) => ({
          customer,
          tickets: ticketCount,
          satisfaction: customerSatisfaction[customer]
            ? parseFloat(
                (
                  customerSatisfaction[customer].sum /
                  customerSatisfaction[customer].total
                ).toFixed(1)
              )
            : 0
        }));

      // ── Engineer performance (top 4 by ticket count) ─────────────────────
      const engineerStats = {};
      tickets.forEach((t) => {
        const name =
          t.engineer_name || t.assignee_name || t.assignee || "未知工程师";
        if (!engineerStats[name]) {
          engineerStats[name] = {
            tickets: 0,
            totalTime: 0,
            satisfactionSum: 0,
            satisfactionCount: 0
          };
        }
        engineerStats[name].tickets++;
        if (t.resolved_time && t.reported_time) {
          engineerStats[name].totalTime +=
            (new Date(t.resolved_time) - new Date(t.reported_time)) /
            (1000 * 60 * 60);
        }
      });
      if (satisfactionStatsData.items) {
        satisfactionStatsData.items.forEach((s) => {
          const name = s.engineer_name || "未知工程师";
          if (engineerStats[name]) {
            engineerStats[name].satisfactionCount++;
            engineerStats[name].satisfactionSum += parseFloat(
              s.overall_score || s.score || 0
            );
          }
        });
      }
      const engineerPerformanceArray = Object.entries(engineerStats)
        .map(([engineer, stats]) => ({
          engineer,
          tickets: stats.tickets,
          avgTime:
            stats.tickets > 0
              ? parseFloat((stats.totalTime / stats.tickets).toFixed(1))
              : 0,
          satisfaction:
            stats.satisfactionCount > 0
              ? parseFloat(
                  (
                    stats.satisfactionSum / stats.satisfactionCount
                  ).toFixed(1)
                )
              : 0
        }))
        .sort((a, b) => b.tickets - a.tickets)
        .slice(0, 4);

      // ── Assemble final object ─────────────────────────────────────────────
      setAnalytics({
        overview: {
          totalTickets,
          totalRecords,
          totalCommunications,
          totalSurveys,
          averageResponseTime:  parseFloat(avgResponseTime.toFixed(1)),
          averageResolutionTime: parseFloat(avgResolutionTime.toFixed(1)),
          averageSatisfaction:  parseFloat(avgSatisfaction.toFixed(1)),
          completionRate:       parseFloat(completionRate.toFixed(1))
        },
        ticketTrends:
          ticketTrendsArray.length > 0
            ? ticketTrendsArray
            : emptyFallback.ticketTrends,
        serviceTypeDistribution:
          serviceTypeDistribution.length > 0
            ? serviceTypeDistribution
            : emptyFallback.serviceTypeDistribution,
        problemTypeDistribution:
          problemTypeDistribution.length > 0
            ? problemTypeDistribution
            : emptyFallback.problemTypeDistribution,
        satisfactionTrends:
          satisfactionTrendsArray.length > 0
            ? satisfactionTrendsArray
            : emptyFallback.satisfactionTrends,
        responseTimeDistribution:
          responseTimeDistribution.length > 0
            ? responseTimeDistribution
            : emptyFallback.responseTimeDistribution,
        topCustomers:
          topCustomersArray.length > 0
            ? topCustomersArray
            : emptyFallback.topCustomers,
        engineerPerformance:
          engineerPerformanceArray.length > 0
            ? engineerPerformanceArray
            : emptyFallback.engineerPerformance
      });
    } catch (err) {
      console.error("Failed to load analytics:", err);
      setError(err.response?.data?.detail || err.message || "加载分析数据失败");
    } finally {
      setLoading(false);
    }
  }, [period]);

  useEffect(() => {
    reload();
  }, [reload]);

  return { analytics, loading, error, period, setPeriod, reload };
}
