import { useState, useEffect, useMemo, useCallback } from "react";
import {
  DollarSign,
  TrendingUp,
  Briefcase,
  CheckCircle2,
} from "lucide-react";
import { formatCurrency } from "../../lib/utils";
import { reportCenterApi, salesStatisticsApi } from "../../services/api";

const REVENUE_TARGET = 160000000;
const PROFIT_TARGET = 15000000;

const toFiniteNumber = (value, fallback = 0) => {
  const number = Number(value);
  return Number.isFinite(number) ? number : fallback;
};

const firstFiniteNumber = (...values) => {
  for (const value of values) {
    const number = Number(value);
    if (Number.isFinite(number)) {
      return number;
    }
  }
  return null;
};

const normalizeDeliveryPoint = (item, fallbackMonth = "当前区间") => ({
  ...item,
  month: item?.month || item?.date || fallbackMonth,
  rate: firstFiniteNumber(item?.rate, item?.value, item?.on_time_rate) ?? 0,
  on_time_projects: firstFiniteNumber(item?.on_time_projects, item?.onTimeProjects),
  total_projects: firstFiniteNumber(item?.total_projects, item?.totalProjects, item?.total),
});

const normalizeDeliveryPayload = (payload) => {
  if (Array.isArray(payload)) {
    return payload.map((item, index) => normalizeDeliveryPoint(item, `阶段${index + 1}`));
  }
  if (payload && typeof payload === "object") {
    return [normalizeDeliveryPoint(payload)];
  }
  return [];
};

const unwrapApiPayload = (response) =>
  response?.formatted || response?.data?.data || response?.data || {};

const buildCostData = (summary = {}) => {
  const actualCost = toFiniteNumber(summary.total_actual_cost);
  const totalBudget = toFiniteNumber(summary.total_budget);
  const rows = [];

  if (actualCost > 0) {
    rows.push({ category: "已用预算", amount: actualCost });
  }

  if (totalBudget > actualCost) {
    rows.push({ category: "剩余预算", amount: totalBudget - actualCost });
  } else if (totalBudget > 0 && actualCost > totalBudget) {
    rows.push({ category: "超预算", amount: actualCost - totalBudget });
  }

  return rows;
};

const normalizeSalesFunnelPayload = (payload = {}) => {
  if (Array.isArray(payload)) {
    return payload.map((item, index) => ({
      stage: item.stage || item.name || item.label || `阶段${index + 1}`,
      value: firstFiniteNumber(item.value, item.count, item.total) ?? 0,
    }));
  }

  const source = payload.funnel || payload.summary || payload;
  return [
    { stage: "线索", value: firstFiniteNumber(source.leads, source.leads_count) ?? 0 },
    {
      stage: "商机",
      value: firstFiniteNumber(source.opportunities, source.opportunities_count) ?? 0,
    },
    { stage: "报价", value: firstFiniteNumber(source.quotes, source.quotes_count) ?? 0 },
    {
      stage: "合同",
      value: firstFiniteNumber(source.contracts, source.contracts_count) ?? 0,
    },
  ];
};

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
  const [costData, setCostData] = useState([]);
  const [trendData, setTrendData] = useState([]);
  const [milestoneData, setMilestoneData] = useState({
    completionRate: 0,
    healthIndex: 0,
  });
  const [salesFunnelData, setSalesFunnelData] = useState([]);
  const [error, setError] = useState(null);
  const [exporting, setExporting] = useState(false);
  const [exportFormat, setExportFormat] = useState("");

  const applyHealthDistribution = useCallback((distribution) => {
    if (distribution && typeof distribution === "object") {
      setHealthData(distribution);

      const total = Object.values(distribution).reduce(
        (sum, val) => sum + val,
        0
      );
      if (total > 0) {
        const h1Count = distribution.H1 || 0;
        const h2Count = distribution.H2 || 0;
        const h3Count = distribution.H3 || 0;
        const healthIndex = Math.round(
          (h1Count * 100 + h2Count * 70 + h3Count * 30) / total
        );
        setMilestoneData((prev) => ({ ...prev, healthIndex }));
      }
    }
  }, []);

  const processHealthData = useCallback((data) => {
    if (data.health_distribution) {
      applyHealthDistribution(data.health_distribution);
    }

    setCostData(buildCostData(data.summary || {}));

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
  }, [applyHealthDistribution]);

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true);
        setError(null);

        const dashboardRes = await reportCenterApi.getExecutiveDashboard();
        const dashboardPayload = unwrapApiPayload(dashboardRes);

        if (dashboardPayload) {
          setDashboardData(dashboardPayload);
          processHealthData(dashboardPayload);
        }

        try {
          const deliveryRes = await reportCenterApi.getDeliveryRate({
            time_range: timeRange,
          });
          const deliveryPayload = unwrapApiPayload(deliveryRes);
          setDeliveryData(normalizeDeliveryPayload(deliveryPayload));
        } catch (err) {
          console.error("Failed to load delivery rate data:", err);
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
        } catch (err) {
          console.error("Failed to load utilization data:", err);
        }

        try {
          const healthRes = await reportCenterApi.getHealthDistribution();
          applyHealthDistribution(unwrapApiPayload(healthRes));
        } catch (err) {
          console.error("Failed to load health distribution:", err);
        }

        try {
          const funnelRes = await salesStatisticsApi.funnel();
          setSalesFunnelData(normalizeSalesFunnelPayload(unwrapApiPayload(funnelRes)));
        } catch (err) {
          console.error("Failed to load sales funnel data:", err);
        }
      } catch (err) {
        console.error("Failed to load executive dashboard:", err);
        setError(err);
      } finally {
        setLoading(false);
      }
    };

    fetchData();
  }, [timeRange, processHealthData, applyHealthDistribution]);

  const kpiCards = useMemo(() => {
    const summary = dashboardData.summary || {};
    const revenue = toFiniteNumber(summary.total_contract_amount);
    const actualCost = toFiniteNumber(summary.total_actual_cost);
    const explicitGrossProfit =
      summary.gross_profit ?? summary.total_gross_profit ?? summary.profit;
    const grossProfit =
      explicitGrossProfit !== undefined && explicitGrossProfit !== null
        ? toFiniteNumber(explicitGrossProfit)
        : revenue - actualCost;
    const revenueRate = REVENUE_TARGET > 0 ? (revenue / REVENUE_TARGET) * 100 : 0;
    const profitRate = PROFIT_TARGET > 0 ? (grossProfit / PROFIT_TARGET) * 100 : 0;
    const activeProjects = toFiniteNumber(summary.active_projects);
    const totalProjects = toFiniteNumber(summary.total_projects);
    const projectGrowth = firstFiniteNumber(summary.project_growth);
    const latestDelivery =
      deliveryData.length > 0 ? deliveryData[deliveryData.length - 1] : null;
    const previousDelivery =
      deliveryData.length > 1 ? deliveryData[deliveryData.length - 2] : null;
    const deliveryRate = firstFiniteNumber(
      summary.on_time_delivery_rate,
      dashboardData?.monthly?.on_time_rate,
      latestDelivery?.rate,
      latestDelivery?.value,
      latestDelivery?.on_time_rate
    );
    const deliveryRateChange = firstFiniteNumber(summary.delivery_rate_change);
    const previousDeliveryRate = firstFiniteNumber(
      previousDelivery?.rate,
      previousDelivery?.value,
      previousDelivery?.on_time_rate
    );
    const onTimeProjects = firstFiniteNumber(latestDelivery?.on_time_projects);
    const totalDeliveryProjects = firstFiniteNumber(latestDelivery?.total_projects);
    const deliveryDelta =
      deliveryRate !== null && previousDeliveryRate !== null
        ? deliveryRate - previousDeliveryRate
        : null;

    let deliveryChange = "暂无趋势";
    let deliveryChangeType = "up";
    let deliverySubText = "交付数据";
    if (deliveryRateChange !== null) {
      deliveryChange = `${deliveryRateChange}%`;
      deliveryChangeType = deliveryRateChange >= 0 ? "up" : "down";
      deliverySubText = "较上月";
    } else if (deliveryDelta !== null) {
      deliveryChange = `${deliveryDelta.toFixed(1)}%`;
      deliveryChangeType = deliveryDelta >= 0 ? "up" : "down";
      deliverySubText = "较上一期";
    } else if (onTimeProjects !== null && totalDeliveryProjects > 0) {
      deliveryChange = `${onTimeProjects}/${totalDeliveryProjects}`;
      deliveryChangeType = deliveryRate === null || deliveryRate >= 80 ? "up" : "down";
      deliverySubText = "按期/总数";
    }

    return [
      {
        title: "总营收",
        value: formatCurrency(revenue),
        change: `目标${formatCurrency(REVENUE_TARGET)} · 达成${revenueRate.toFixed(1)}%`,
        changeType: revenueRate >= 100 ? "up" : "down",
        subText: "2026目标对比",
        icon: DollarSign,
        color: "blue",
      },
      {
        title: "项目毛利",
        value: formatCurrency(grossProfit),
        change: `目标${formatCurrency(PROFIT_TARGET)} · 达成${profitRate.toFixed(1)}%`,
        changeType: profitRate >= 100 ? "up" : "down",
        subText: "合同额减实际成本",
        icon: TrendingUp,
        color: "green",
      },
      {
        title: "活跃项目",
        value: activeProjects,
        change: projectGrowth !== null ? `${projectGrowth}%` : `${totalProjects}`,
        changeType: projectGrowth === null || projectGrowth >= 0 ? "up" : "down",
        subText: projectGrowth !== null ? "较上月" : "项目总数",
        icon: Briefcase,
        color: "orange",
      },
      {
        title: "交付准时率",
        value: deliveryRate === null ? "暂无数据" : `${deliveryRate}%`,
        change: deliveryChange,
        changeType: deliveryChangeType,
        subText: deliverySubText,
        icon: CheckCircle2,
        color: "purple",
      },
    ];
  }, [dashboardData, deliveryData]);

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

      const dashboardPayload = unwrapApiPayload(dashboardRes);
      if (dashboardPayload) {
        setDashboardData(dashboardPayload);
        processHealthData(dashboardPayload);
      }

      const deliveryPayload = unwrapApiPayload(deliveryRes);
      setDeliveryData(normalizeDeliveryPayload(deliveryPayload));

      const utilPayload = unwrapApiPayload(utilRes);
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

      const funnelRes = await salesStatisticsApi.funnel();
      setSalesFunnelData(normalizeSalesFunnelPayload(unwrapApiPayload(funnelRes)));
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
