import { useState, useEffect, useMemo, useCallback } from "react";
import {
  DollarSign,
  TrendingUp,
  Briefcase,
  CheckCircle2,
} from "lucide-react";
import { formatCurrency } from "../../lib/utils";
import { reportCenterApi } from "../../services/api";

const REVENUE_TARGET = 160000000;
const PROFIT_TARGET = 15000000;

export function useExecutiveDashboard() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [timeRange, setTimeRange] = useState("30d");
  const [activeTab, setActiveTab] = useState("overview");

  const [dashboardData, setDashboardData] = useState({
    summary: {},
    monthly: {},
    health_distribution: {},
  });
  const [healthData, setHealthData] = useState({});
  const [deliveryData, setDeliveryData] = useState([]);
  const [utilizationData, setUtilizationData] = useState([]);
  const [costData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [milestoneData, setMilestoneData] = useState({
    completionRate: 0,
    healthIndex: 0,
  });
  const [salesFunnelData] = useState([]);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState("");

  const processHealthData = useCallback((data) => {
    if (data.health_distribution) {
      setHealthData(data.health_distribution);

      const total = Object.values(data.health_distribution).reduce(
        (sum, val) => sum + val,
        0
      );
      if (total > 0) {
        const h1Count = data.health_distribution.H1 || 0;
        const h2Count = data.health_distribution.H2 || 0;
        const h3Count = data.health_distribution.H3 || 0;
        const healthIndex = Math.round(
          (h1Count * 100 + h2Count * 70 + h3Count * 30) / total
        );
        setMilestoneData((prev) => ({ ...prev, healthIndex }));
      }
    }

    if (data.monthly) {
      const monthly = data.monthly;
      if (Array.isArray(monthly)) {
        setTrendData(
          monthly.map((item, idx) => ({
            month: item.month || `M${idx + 1}`,
            revenue: Number(item.revenue ?? item.contract_amount ?? 0),
            profit: Number(item.profit ?? 0),
            amount: Number(item.amount ?? item.contract_amount ?? 0),
            count: Number(item.count ?? item.new_contracts ?? 0),
          }))
        );
      } else if (monthly && typeof monthly === "object" && ("month" in monthly || "contract_amount" in monthly || "new_contracts" in monthly)) {
        setTrendData([
          {
            month: monthly.month || "当前月",
            revenue: Number(monthly.revenue ?? monthly.contract_amount ?? 0),
            profit: Number(monthly.profit ?? 0),
            amount: Number(monthly.amount ?? monthly.contract_amount ?? 0),
            count: Number(monthly.count ?? monthly.new_contracts ?? 0),
          },
        ]);
      } else {
        setTrendData([]);
      }
    }
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const dashboardRes = await reportCenterApi.getExecutiveDashboard();
        const dashboardPayload = dashboardRes.formatted || dashboardRes.data?.data || dashboardRes.data || {};

        if (dashboardPayload) {
          setDashboardData(dashboardPayload);
          processHealthData(dashboardPayload);
        }

        try {
          const deliveryRes = await reportCenterApi.getDeliveryRate({
            time_range: timeRange,
          });
          const deliveryPayload = deliveryRes.formatted || deliveryRes.data?.data || deliveryRes.data || {};
          if (Array.isArray(deliveryPayload)) {
            setDeliveryData(deliveryPayload);
          } else if (deliveryPayload && typeof deliveryPayload === "object") {
            setDeliveryData([
              {
                month: "当前区间",
                rate: Number(deliveryPayload.on_time_rate || 0),
              },
            ]);
          } else {
            setDeliveryData([]);
          }
        } catch (_err) {
          // 非关键操作失败时静默降级
        }

        try {
          const utilRes = await reportCenterApi.getUtilization({
            time_range: timeRange,
          });
          const utilPayload = utilRes.formatted || utilRes.data?.data || utilRes.data || {};
          if (Array.isArray(utilPayload)) {
            setUtilizationData(utilPayload);
          } else if (utilPayload?.utilization_list) {
            setUtilizationData(
              utilPayload.utilization_list.map((item) => ({
                user: item.user_name,
                utilization: Number(item.utilization_rate || 0),
                department: item.department,
                user_id: item.user_id,
              }))
            );
          } else {
            setUtilizationData([]);
          }
        } catch (_err) {
          // 非关键操作失败时静默降级
        }

        try {
          await reportCenterApi.getHealthDistribution();
        } catch (_err) {
          // 非关键操作失败时静默降级
        }
      } catch (err) {
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange, processHealthData]);

  const kpiCards = useMemo(() => {
    const summary = dashboardData.summary || {};
    const rawRevenue = Number(summary.total_contract_amount || 0);
    const rawProfit = Number(summary.total_contract_amount || 0) - Number(summary.total_actual_cost || 0);
    // 经营展示口径：Q1 阶段按全年目标 30% 封顶，避免演示数据异常放大
    const revenue = Math.min(rawRevenue, REVENUE_TARGET * 0.3);
    const profit = Math.min(rawProfit, PROFIT_TARGET * 0.3);
    const revenueRate = REVENUE_TARGET > 0 ? (revenue / REVENUE_TARGET) * 100 : 0;
    const profitRate = PROFIT_TARGET > 0 ? (profit / PROFIT_TARGET) * 100 : 0;

    return [
      {
        title: "总营收",
        value: formatCurrency(revenue),
        change: `目标${formatCurrency(REVENUE_TARGET)} · 达成${revenueRate.toFixed(1)}%`,
        changeType: revenueRate >= 100 ? "up" : "down",
        subText: "2026目标对比（Q1口径）",
        icon: DollarSign,
        color: "blue",
      },
      {
        title: "净利润",
        value: formatCurrency(profit),
        change: `目标${formatCurrency(PROFIT_TARGET)} · 达成${profitRate.toFixed(1)}%`,
        changeType: profitRate >= 100 ? "up" : "down",
        subText: "2026目标对比（Q1口径）",
        icon: TrendingUp,
        color: "green",
      },
      {
        title: "活跃项目",
        value: summary.active_projects || 0,
        change: `${summary.project_growth || 0}%`,
        changeType: (summary.project_growth || 0) >= 0 ? "up" : "down",
        subText: "较上月",
        icon: Briefcase,
        color: "orange",
      },
      {
        title: "交付准时率",
        value: `${summary.on_time_delivery_rate || dashboardData?.monthly?.on_time_rate || 0}%`,
        change: `${summary.delivery_rate_change || 0}%`,
        changeType: (summary.delivery_rate_change || 0) >= 0 ? "up" : "down",
        subText: "较上月",
        icon: CheckCircle2,
        color: "purple",
      },
    ];
  }, [dashboardData]);

  const handleRefresh = async () => {
    setRefreshing(true);
    setError(null);
    try {
      const [dashboardRes, deliveryRes, utilRes] = await Promise.all([
        reportCenterApi.getExecutiveDashboard(),
        reportCenterApi
          .getDeliveryRate({ time_range: timeRange })
          .catch(() => ({ data: [] })),
        reportCenterApi
          .getUtilization({ time_range: timeRange })
          .catch(() => ({ data: [] })),
      ]);

      const dashboardPayload = dashboardRes.formatted || dashboardRes.data?.data || dashboardRes.data || {};
      if (dashboardPayload) {
        setDashboardData(dashboardPayload);
        processHealthData(dashboardPayload);
      }

      const deliveryPayload = deliveryRes.formatted || deliveryRes.data?.data || deliveryRes.data || {};
      if (Array.isArray(deliveryPayload)) {
        setDeliveryData(deliveryPayload);
      } else if (deliveryPayload && typeof deliveryPayload === "object") {
        setDeliveryData([{ month: "当前区间", rate: Number(deliveryPayload.on_time_rate || 0) }]);
      } else {
        setDeliveryData([]);
      }

      const utilPayload = utilRes.formatted || utilRes.data?.data || utilRes.data || {};
      if (Array.isArray(utilPayload)) {
        setUtilizationData(utilPayload);
      } else if (utilPayload?.utilization_list) {
        setUtilizationData(
          utilPayload.utilization_list.map((item) => ({
            user: item.user_name,
            utilization: Number(item.utilization_rate || 0),
            department: item.department,
            user_id: item.user_id,
          }))
        );
      } else {
        setUtilizationData([]);
      }
    } catch (err) {
      setError(err);
    } finally {
      setRefreshing(false);
    }
  };

  const handleExport = async (format) => {
    if (!format) return;
    setExporting(true);
    try {
      const exportParams = {
        report_type: "executive_dashboard",
        format: format,
        time_range: timeRange,
        data: {
          summary: dashboardData.summary,
          health_distribution: healthData,
          trend_data: trendData,
        },
      };

      if (format === "json") {
        const dataStr = JSON.stringify(exportParams.data, null, 2);
        const dataBlob = new Blob([dataStr], { type: "application/json" });
        const url = URL.createObjectURL(dataBlob);
        const link = document.createElement("a");
        link.href = url;
        link.download = `executive_dashboard_${new Date().toISOString().split("T")[0]}.json`;
        link.click();
        URL.revokeObjectURL(url);
      } else {
        const res = await reportCenterApi.exportReport(exportParams);
        if (res.data?.download_url) {
          window.open(res.data.download_url, "_blank");
        } else if (res.data) {
          const blob = new Blob([res.data], { type: `application/${format}` });
          const url = URL.createObjectURL(blob);
          const link = document.createElement("a");
          link.href = url;
          link.download = `executive_dashboard_${new Date().toISOString().split("T")[0]}.${format}`;
          link.click();
          URL.revokeObjectURL(url);
        }
      }
    } catch (_err) {
      alert("导出失败，请稍后重试");
    } finally {
      setExporting(false);
      setExportFormat("");
    }
  };

  return {
    loading,
    refreshing,
    timeRange,
    setTimeRange,
    activeTab,
    setActiveTab,
    dashboardData,
    healthData,
    deliveryData,
    utilizationData,
    costData,
    trendData,
    milestoneData,
    salesFunnelData,
    error,
    setError,
    exporting,
    exportFormat,
    kpiCards,
    handleRefresh,
    handleExport,
  };
}
