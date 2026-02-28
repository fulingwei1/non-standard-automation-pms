import { useState, useEffect, useCallback } from "react";
import {
  Download,
  RefreshCw
} from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import { LoadingCard, ErrorMessage } from "../components/common";
import { toast } from "../components/ui/toast";
import { serviceApi } from "../services/api";
import { ServiceOverview } from "../components/service-analytics/ServiceOverview";
import { ServiceCharts } from "../components/service-analytics/ServiceCharts";
import { ServicePerformance } from "../components/service-analytics/ServicePerformance";
import { ServiceTrends } from "../components/service-analytics/ServiceTrends";

// Empty fallback data (no mock)
const emptyFallback = {
  ticketTrends: [],
  serviceTypeDistribution: [],
  problemTypeDistribution: [],
  satisfactionTrends: [],
  responseTimeDistribution: [],
  topCustomers: [],
  engineerPerformance: []
};

export default function ServiceAnalytics() {
  const [analytics, setAnalytics] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [period, setPeriod] = useState("MONTHLY"); // DAILY, WEEKLY, MONTHLY, YEARLY

  useEffect(() => {
    loadAnalytics();
  }, [period]);

  const loadAnalytics = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load statistics from multiple APIs
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

      const tickets = ticketsList.data?.items || ticketsList.data?.items || ticketsList.data || [];
      const records = recordsList.data?.items || recordsList.data?.items || recordsList.data || [];
      const communications =
        communicationsList.data?.items || communicationsList.data?.items || communicationsList.data || [];
      const satisfactions =
        satisfactionList.data?.items || satisfactionList.data?.items || satisfactionList.data || [];
      const ticketsStatsData = ticketsStats.data || {};
      const satisfactionStatsData = {
        ...(satisfactionStats.data || {}),
        items: satisfactions
      };

      // Calculate overview
      const totalTickets = ticketsStatsData.total || tickets.length;
      const totalRecords = records?.length;
      const totalCommunications = communications.length;
      const totalSurveys = satisfactionStatsData.total || 0;

      // Calculate average response time (from tickets)
      const ticketsWithResponseTime = (tickets || []).filter((t) => t.response_time);
      const avgResponseTime =
        ticketsWithResponseTime.length > 0
          ? (ticketsWithResponseTime || []).reduce((sum, t) => {
              const responseTime =
                new Date(t.response_time) -
                new Date(t.reported_time || t.created_at);
              return sum + responseTime / (1000 * 60 * 60); // Convert to hours
            }, 0) / ticketsWithResponseTime.length
          : 2.5;

      // Calculate average resolution time (from tickets)
      const resolvedTickets = (tickets || []).filter(
        (t) => t.resolved_time && t.reported_time
      );
      const avgResolutionTime =
        resolvedTickets.length > 0
          ? (resolvedTickets || []).reduce((sum, t) => {
              const resolutionTime =
                new Date(t.resolved_time) -
                new Date(t.reported_time || t.created_at);
              return sum + resolutionTime / (1000 * 60 * 60); // Convert to hours
            }, 0) / resolvedTickets.length
          : 8.5;

      // Calculate average satisfaction
      const avgSatisfaction = satisfactionStatsData.average_score || 4.3;

      // Calculate completion rate
      const completedTickets = (tickets || []).filter(
        (t) => t.status === "CLOSED" || t.status === "已关闭"
      ).length;
      const completionRate =
        totalTickets > 0 ? (completedTickets / totalTickets) * 100 : 0;

      // Calculate service type distribution (from records)
      const serviceTypeCounts = {};
      (records || []).forEach((r) => {
        const type = r.service_type || "其他";
        serviceTypeCounts[type] = (serviceTypeCounts[type] || 0) + 1;
      });
      const totalRecordsCount = records?.length;
      const serviceTypeDistribution = Object.entries(serviceTypeCounts).map(
        ([type, count]) => ({
          type,
          count,
          percentage:
            totalRecordsCount > 0
              ? ((count / totalRecordsCount) * 100).toFixed(1)
              : 0
        })
      );

      // Calculate problem type distribution (from tickets)
      const problemTypeCounts = {};
      (tickets || []).forEach((t) => {
        const type = t.problem_type || "其他";
        problemTypeCounts[type] = (problemTypeCounts[type] || 0) + 1;
      });
      const totalTicketsCount = tickets.length;
      const problemTypeDistribution = Object.entries(problemTypeCounts).map(
        ([type, count]) => ({
          type,
          count,
          percentage:
            totalTicketsCount > 0
              ? ((count / totalTicketsCount) * 100).toFixed(1)
              : 0
        })
      );

      // Calculate response time distribution
      const responseTimeRanges = {
        "0-2小时": 0,
        "2-4小时": 0,
        "4-8小时": 0,
        "8-24小时": 0,
        ">24小时": 0
      };
      (ticketsWithResponseTime || []).forEach((t) => {
        const hours =
          (new Date(t.response_time) -
            new Date(t.reported_time || t.created_at)) /
          (1000 * 60 * 60);
        if (hours <= 2) {
          responseTimeRanges["0-2小时"]++;
        } else if (hours <= 4) {
          responseTimeRanges["2-4小时"]++;
        } else if (hours <= 8) {
          responseTimeRanges["4-8小时"]++;
        } else if (hours <= 24) {
          responseTimeRanges["8-24小时"]++;
        } else {
          responseTimeRanges[">24小时"]++;
        }
      });
      const totalWithResponseTime = ticketsWithResponseTime.length;
      const responseTimeDistribution = Object.entries(responseTimeRanges).map(
        ([range, count]) => ({
          range,
          count,
          percentage:
            totalWithResponseTime > 0
              ? ((count / totalWithResponseTime) * 100).toFixed(1)
              : 0
        })
      );

      // Group tickets by month for trends
      const ticketTrends = {};
      (tickets || []).forEach((t) => {
        const date = new Date(t.reported_time || t.created_at);
        const month = `${date.getFullYear()}-${String(
          date.getMonth() + 1
        ).padStart(2, "0")}`;
        if (!ticketTrends[month]) {
          ticketTrends[month] = { count: 0, resolved: 0 };
        }
        ticketTrends[month].count++;
        if (t.status === "CLOSED" || t.status === "已关闭") {
          ticketTrends[month].resolved++;
        }
      });
      const ticketTrendsArray = Object.entries(ticketTrends)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .slice(-4)
        .map(([month, data]) => ({ month, ...data }));

      // Calculate satisfaction trends from satisfaction data
      const satisfactionTrendsData = {};
      if (satisfactionStatsData.items) {
        (satisfactionStatsData.items || []).forEach((s) => {
          const date = new Date(s.created_at || s.survey_date);
          const month = `${date.getFullYear()}-${String(
            date.getMonth() + 1
          ).padStart(2, "0")}`;
          if (!satisfactionTrendsData[month]) {
            satisfactionTrendsData[month] = { total: 0, sum: 0 };
          }
          satisfactionTrendsData[month].total++;
          satisfactionTrendsData[month].sum += parseFloat(
            s.overall_score || s.score || 0
          );
        });
      }
      const satisfactionTrendsArray = Object.entries(satisfactionTrendsData)
        .sort((a, b) => a[0].localeCompare(b[0]))
        .slice(-4)
        .map(([month, data]) => ({
          month,
          score:
            data.total > 0
              ? parseFloat((data.sum / data.total).toFixed(1))
              : 0
        }));

      // Calculate top customers from tickets
      const customerTicketCounts = {};
      const customerSatisfaction = {};
      (tickets || []).forEach((t) => {
        const customerName = t.customer_name || t.customer || "未知客户";
        customerTicketCounts[customerName] =
          (customerTicketCounts[customerName] || 0) + 1;
      });
      // Get satisfaction scores for customers
      if (satisfactionStatsData.items) {
        (satisfactionStatsData.items || []).forEach((s) => {
          const customerName = s.customer_name || "未知客户";
          if (!customerSatisfaction[customerName]) {
            customerSatisfaction[customerName] = { total: 0, sum: 0 };
          }
          customerSatisfaction[customerName].total++;
          customerSatisfaction[customerName].sum += parseFloat(
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

      // Calculate engineer performance from tickets
      const engineerStats = {};
      (tickets || []).forEach((t) => {
        const engineerName =
          t.engineer_name || t.assignee_name || t.assignee || "未知工程师";
        if (!engineerStats[engineerName]) {
          engineerStats[engineerName] = {
            tickets: 0,
            totalTime: 0,
            satisfactionSum: 0,
            satisfactionCount: 0
          };
        }
        engineerStats[engineerName].tickets++;
        if (t.resolved_time && t.reported_time) {
          const time =
            (new Date(t.resolved_time) - new Date(t.reported_time)) /
            (1000 * 60 * 60);
          engineerStats[engineerName].totalTime += time;
        }
      });
      // Get satisfaction for engineers
      if (satisfactionStatsData.items) {
        (satisfactionStatsData.items || []).forEach((s) => {
          const engineerName = s.engineer_name || "未知工程师";
          if (engineerStats[engineerName]) {
            engineerStats[engineerName].satisfactionCount++;
            engineerStats[engineerName].satisfactionSum += parseFloat(
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
                  (stats.satisfactionSum / stats.satisfactionCount).toFixed(1)
                )
              : 0
        }))
        .sort((a, b) => b.tickets - a.tickets)
        .slice(0, 4);

      // Build analytics object
      const analyticsData = {
        overview: {
          totalTickets,
          totalRecords,
          totalCommunications,
          totalSurveys,
          averageResponseTime: parseFloat(avgResponseTime.toFixed(1)),
          averageResolutionTime: parseFloat(avgResolutionTime.toFixed(1)),
          averageSatisfaction: parseFloat(avgSatisfaction.toFixed(1)),
          completionRate: parseFloat(completionRate.toFixed(1))
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
      };

      setAnalytics(analyticsData);
    } catch (err) {
      console.error("Failed to load analytics:", err);
      setError(err.response?.data?.detail || err.message || "加载分析数据失败");
    } finally {
      setLoading(false);
    }
  }, [period]);

  const handleExport = (format = "csv") => {
    if (!analytics) {
      toast.error("暂无数据可导出");
      return;
    }

    try {
      // 准备导出数据
      const exportData = {
        统计周期:
          period === "DAILY"
            ? "今日"
            : period === "WEEKLY"
            ? "本周"
            : period === "MONTHLY"
            ? "本月"
            : "本年",
        导出日期: new Date().toLocaleDateString("zh-CN"),
        概览: {
          工单总数: analytics.overview.totalTickets,
          服务记录数: analytics.overview.totalRecords,
          沟通记录数: analytics.overview.totalCommunications,
          满意度调查数: analytics.overview.totalSurveys,
          平均响应时间: `${analytics.overview.averageResponseTime}小时`,
          平均解决时间: `${analytics.overview.averageResolutionTime}小时`,
          平均满意度: analytics.overview.averageSatisfaction,
          完成率: `${analytics.overview.completionRate}%`
        },
        工单趋势: (analytics.ticketTrends || []).map((t) => ({
          月份: t.month,
          工单数: t.count,
          已解决: t.resolved
        })),
        服务类型分布: (analytics.serviceTypeDistribution || []).map((d) => ({
          类型: d.type,
          数量: d.count,
          占比: `${d.percentage}%`
        })),
        问题类型分布: (analytics.problemTypeDistribution || []).map((d) => ({
          类型: d.type,
          数量: d.count,
          占比: `${d.percentage}%`
        })),
        响应时间分布: (analytics.responseTimeDistribution || []).map((d) => ({
          时间范围: d.range,
          数量: d.count,
          占比: `${d.percentage}%`
        }))
      };

      if (format === "excel") {
        // Excel格式导出（使用HTML table方式）
        const htmlContent = generateExcelHTML(exportData);
        const blob = new Blob([htmlContent], {
          type: "application/vnd.ms-excel"
        });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute(
          "download",
          `服务数据分析报表_${period}_${new Date().toISOString().split("T")[0]}.xls`
        );
        link.style.visibility = "hidden";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);
        toast.success("Excel报表导出成功");
      } else {
        // CSV格式导出
        const csvRows = [];

        // 概览数据
        csvRows.push("=== 概览数据 ===");
        csvRows.push("项目,数值");
        Object.entries(exportData.概览).forEach(([key, value]) => {
          csvRows.push(`"${key}","${value}"`);
        });
        csvRows.push("");

        // 工单趋势
        if (exportData.工单趋势?.length > 0) {
          csvRows.push("=== 工单趋势 ===");
          csvRows.push("月份,工单数,已解决");
          (exportData.工单趋势 || []).forEach((t) => {
            csvRows.push(`"${t.月份}",${t.工单数},${t.已解决}`);
          });
          csvRows.push("");
        }

        // 服务类型分布
        if (exportData.服务类型分布?.length > 0) {
          csvRows.push("=== 服务类型分布 ===");
          csvRows.push("类型,数量,占比");
          (exportData.服务类型分布 || []).forEach((d) => {
            csvRows.push(`"${d.类型}",${d.数量},"${d.占比}"`);
          });
          csvRows.push("");
        }

        // 问题类型分布
        if (exportData.问题类型分布?.length > 0) {
          csvRows.push("=== 问题类型分布 ===");
          csvRows.push("类型,数量,占比");
          (exportData.问题类型分布 || []).forEach((d) => {
            csvRows.push(`"${d.类型}",${d.数量},"${d.占比}"`);
          });
          csvRows.push("");
        }

        // 响应时间分布
        if (exportData.响应时间分布?.length > 0) {
          csvRows.push("=== 响应时间分布 ===");
          csvRows.push("时间范围,数量,占比");
          (exportData.响应时间分布 || []).forEach((d) => {
            csvRows.push(`"${d.时间范围}",${d.数量},"${d.占比}"`);
          });
        }

        const csvContent = csvRows.join("\n");

        // 添加BOM以支持中文
        const BOM = "\uFEFF";
        const blob = new Blob([BOM + csvContent], {
          type: "text/csv;charset=utf-8;"
        });
        const link = document.createElement("a");
        const url = URL.createObjectURL(blob);
        link.setAttribute("href", url);
        link.setAttribute(
          "download",
          `服务数据分析报表_${period}_${new Date().toISOString().split("T")[0]}.csv`
        );
        link.style.visibility = "hidden";
        document.body.appendChild(link);
        link.click();
        document.body.removeChild(link);
        URL.revokeObjectURL(url);

        toast.success("CSV报表导出成功");
      }
    } catch (error) {
      console.error("导出失败:", error);
      toast.error("导出失败: " + (error.message || "未知错误"));
    }
  };

  // 生成Excel HTML格式
  const generateExcelHTML = (data) => {
    let html = `
      <html xmlns:o="urn:schemas-microsoft-com:office:office" xmlns:x="urn:schemas-microsoft-com:office:excel" xmlns="http://www.w3.org/TR/REC-html40">
      <head>
        <meta charset="utf-8">
        <style>
          table { border-collapse: collapse; width: 100%; }
          th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
          th { background-color: #4f46e5; color: white; font-weight: bold; }
          .section-title { background-color: #e5e7eb; font-weight: bold; }
        </style>
      </head>
      <body>
        <h2>服务数据分析报表</h2>
        <p>统计周期: ${data.统计周期}</p>
        <p>导出日期: ${data.导出日期}</p>
        <br>
    `;

    // 概览数据
    html += '<table><tr class="section-title"><th colspan="2">概览数据</th></tr><tr><th>项目</th><th>数值</th></tr>';
    Object.entries(data.概览).forEach(([key, value]) => {
      html += `<tr><td>${key}</td><td>${value}</td></tr>`;
    });
    html += "</table><br>";

    // 工单趋势
    if (data.工单趋势?.length > 0) {
      html += '<table><tr class="section-title"><th colspan="3">工单趋势</th></tr><tr><th>月份</th><th>工单数</th><th>已解决</th></tr>';
      (data.工单趋势 || []).forEach((t) => {
        html += `<tr><td>${t.月份}</td><td>${t.工单数}</td><td>${t.已解决}</td></tr>`;
      });
      html += "</table><br>";
    }

    // 服务类型分布
    if (data.服务类型分布?.length > 0) {
      html += '<table><tr class="section-title"><th colspan="3">服务类型分布</th></tr><tr><th>类型</th><th>数量</th><th>占比</th></tr>';
      (data.服务类型分布 || []).forEach((d) => {
        html += `<tr><td>${d.类型}</td><td>${d.数量}</td><td>${d.占比}</td></tr>`;
      });
      html += "</table><br>";
    }

    // 问题类型分布
    if (data.问题类型分布?.length > 0) {
      html += '<table><tr class="section-title"><th colspan="3">问题类型分布</th></tr><tr><th>类型</th><th>数量</th><th>占比</th></tr>';
      (data.问题类型分布 || []).forEach((d) => {
        html += `<tr><td>${d.类型}</td><td>${d.数量}</td><td>${d.占比}</td></tr>`;
      });
      html += "</table><br>";
    }

    // 响应时间分布
    if (data.响应时间分布?.length > 0) {
      html += '<table><tr class="section-title"><th colspan="3">响应时间分布</th></tr><tr><th>时间范围</th><th>数量</th><th>占比</th></tr>';
      (data.响应时间分布 || []).forEach((d) => {
        html += `<tr><td>${d.时间范围}</td><td>${d.数量}</td><td>${d.占比}</td></tr>`;
      });
      html += "</table>";
    }

    html += "</body></html>";
    return html;
  };

  if (loading && !analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="服务数据分析" />
        <div className="container mx-auto px-4 py-6">
          <LoadingCard rows={5} />
        </div>
      </div>
    );
  }

  if (error && !analytics) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <PageHeader title="服务数据分析" />
        <div className="container mx-auto px-4 py-6">
          <ErrorMessage error={error} onRetry={loadAnalytics} />
        </div>
      </div>
    );
  }

  if (!analytics) return null;

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="服务数据分析"
        description="分析服务数据，了解服务质量和效率"
        actions={
          <div className="flex gap-2">
            <div className="flex gap-1 bg-slate-800/50 rounded-lg p-1">
              {["DAILY", "WEEKLY", "MONTHLY", "YEARLY"].map((p) => (
                <Button
                  key={p}
                  variant={period === p ? "default" : "ghost"}
                  size="sm"
                  onClick={() => setPeriod(p)}
                >
                  {p === "DAILY"
                    ? "今日"
                    : p === "WEEKLY"
                    ? "本周"
                    : p === "MONTHLY"
                    ? "本月"
                    : "本年"}
                </Button>
              ))}
            </div>
            <Button
              variant="outline"
              size="sm"
              className="gap-2"
              onClick={() => {
                loadAnalytics();
                toast.success("数据已刷新");
              }}
              disabled={loading}
            >
              <RefreshCw
                className={`w-4 h-4 ${loading ? "animate-spin" : ""}`}
              />
              刷新
            </Button>
            <div className="flex gap-2">
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => handleExport("csv")}
              >
                <Download className="w-4 h-4" />
                导出CSV
              </Button>
              <Button
                variant="outline"
                size="sm"
                className="gap-2"
                onClick={() => handleExport("excel")}
              >
                <Download className="w-4 h-4" />
                导出Excel
              </Button>
            </div>
          </div>
        }
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        <ServiceOverview analytics={analytics} />
        <ServiceCharts analytics={analytics} />
        <ServicePerformance analytics={analytics} />
        <ServiceTrends analytics={analytics} />
      </div>
    </div>
  );
}
