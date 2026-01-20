import { useState, useEffect, useMemo, useCallback } from "react";
import {
  DollarSign,
  TrendingUp,
  Briefcase,
  CheckCircle2,
} from "lucide-react";
import { formatCurrency } from "../../lib/utils";
import { reportCenterApi } from "../../services/api";

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
      setTrendData(
        Object.keys(monthly).map((month) => ({
          month,
          revenue: monthly[month].revenue || monthly[month].contract_amount || 0,
          profit: monthly[month].profit || 0,
          amount: monthly[month].amount || monthly[month].contract_amount || 0,
          count: monthly[month].count || monthly[month].new_contracts || 0,
        }))
      );
    }
  }, []);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const dashboardRes = await reportCenterApi.getExecutiveDashboard();

        if (dashboardRes.data) {
          setDashboardData(dashboardRes.data);
          processHealthData(dashboardRes.data);
        }

        try {
          const deliveryRes = await reportCenterApi.getDeliveryRate({
            time_range: timeRange,
          });
          if (deliveryRes.data) {
            setDeliveryData(
              Array.isArray(deliveryRes.data) ? deliveryRes.data : []
            );
          }
        } catch (err) {
          console.error("Failed to load delivery rate data:", err);
        }

        try {
          const utilRes = await reportCenterApi.getUtilization({
            time_range: timeRange,
          });
          if (utilRes.data) {
            setUtilizationData(Array.isArray(utilRes.data) ? utilRes.data : []);
          }
        } catch (err) {
          console.error("Failed to load utilization data:", err);
        }

        try {
          await reportCenterApi.getHealthDistribution();
        } catch (err) {
          console.error("Failed to load health distribution:", err);
        }
      } catch (err) {
        console.error("Failed to load executive dashboard:", err);
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange, processHealthData]);

  const kpiCards = useMemo(() => {
    const summary = dashboardData.summary || {};
    return [
      {
        title: "总营收",
        value: formatCurrency(summary.total_revenue || 0),
        change: `${summary.revenue_growth || 0}%`,
        changeType: (summary.revenue_growth || 0) >= 0 ? "up" : "down",
        subText: "较上月",
        icon: DollarSign,
        color: "blue",
      },
      {
        title: "净利润",
        value: formatCurrency(summary.total_profit || 0),
        change: `${summary.profit_growth || 0}%`,
        changeType: (summary.profit_growth || 0) >= 0 ? "up" : "down",
        subText: "较上月",
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
        value: `${summary.on_time_delivery_rate || 0}%`,
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

      if (dashboardRes.data) {
        setDashboardData(dashboardRes.data);
        processHealthData(dashboardRes.data);
      }

      if (deliveryRes.data) {
        setDeliveryData(
          Array.isArray(deliveryRes.data) ? deliveryRes.data : []
        );
      }

      if (utilRes.data) {
        setUtilizationData(Array.isArray(utilRes.data) ? utilRes.data : []);
      }
    } catch (err) {
      console.error("Failed to refresh:", err);
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
    } catch (err) {
      console.error("Failed to export:", err);
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
