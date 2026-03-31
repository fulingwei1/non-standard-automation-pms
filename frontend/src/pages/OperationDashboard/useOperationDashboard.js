import { useEffect, useState } from "react";
import {
  Clock,
  DollarSign,
  Package,
  Users,
} from "lucide-react";
import api, { alertApi, projectApi } from "../../services/api";
import { DEFAULT_DASHBOARD_DATA } from "./constants";
import {
  buildDateRange,
  buildMonthlyTrend,
  formatAmountInWan,
  formatTimeAgo,
} from "./utils";

export function useOperationDashboard(timeRange) {
  const [dashboardData, setDashboardData] = useState(DEFAULT_DASHBOARD_DATA);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;

    const loadDashboard = async () => {
      setLoading(true);
      setError(null);

      const rangeParams = buildDateRange(timeRange);
      const results = await Promise.allSettled([
        api.get("/report-center/bi/dashboard/executive"),
        api.get("/report-center/bi/delivery-rate", { params: rangeParams }),
        api.get("/report-center/bi/utilization", { params: rangeParams }),
        alertApi.list({ page: 1, page_size: 5, status: "PENDING" }),
        projectApi.getBoard(),
      ]);

      const errors = [];
      const unwrap = (response) => response?.data?.data ?? response?.data ?? response;
      const errorMessage = (err) => {
        const status = err?.response?.status;
        const detail = err?.response?.data?.detail;
        const message = err?.response?.data?.message;
        const fallback = err?.message || "请求失败";
        const apiMessage =
          typeof detail === "string"
            ? detail
            : detail?.message || message || fallback;
        return status ? `(${status}) ${apiMessage}` : apiMessage;
      };

      let executiveData = {};
      let deliveryData = {};
      let utilizationData = {};
      let alertData = {};
      let projectBoardData = {};

      if (results[0].status === "fulfilled") {
        executiveData = unwrap(results[0].value);
      } else {
        errors.push(`决策数据：${errorMessage(results[0].reason)}`);
      }

      if (results[1].status === "fulfilled") {
        deliveryData = unwrap(results[1].value);
      } else {
        errors.push(`交付准时率：${errorMessage(results[1].reason)}`);
      }

      if (results[2].status === "fulfilled") {
        utilizationData = unwrap(results[2].value);
      } else {
        errors.push(`人员利用率：${errorMessage(results[2].reason)}`);
      }

      if (results[3].status === "fulfilled") {
        alertData = results[3].value?.data || {};
      } else {
        errors.push(`预警列表：${errorMessage(results[3].reason)}`);
      }

      if (results[4].status === "fulfilled") {
        projectBoardData = unwrap(results[4].value);
      } else {
        errors.push(`项目看板：${errorMessage(results[4].reason)}`);
      }

      const summary = executiveData?.summary || {};
      const monthly = executiveData?.monthly || {};
      const deliveryRate = Number(deliveryData?.on_time_rate || 0);
      const utilizationRate = Number(utilizationData?.avg_utilization_rate || 0);

      const boardProjects = projectBoardData?.board
        ? Object.values(projectBoardData.board).flatMap(
          (stage) => stage?.projects || []
        )
        : [];

      const healthSource = boardProjects.length
        ? (boardProjects || []).reduce((acc, project) => {
          const health = project?.health || "H1";
          acc[health] = (acc[health] || 0) + 1;
          return acc;
        }, {})
        : executiveData?.health_distribution || {};

      const healthyCount = Number(healthSource?.H1 || 0) + Number(healthSource?.H4 || 0);
      const atRiskCount = Number(healthSource?.H2 || 0);
      const blockedCount = Number(healthSource?.H3 || 0);

      const kpis = [
        {
          label: "在制项目",
          value: Number(summary.active_projects || 0),
          change: 0,
          changePercent: "0%",
          trend: "up",
          icon: Package,
          color: "text-blue-400",
          bgColor: "bg-blue-500/10",
        },
        {
          label: "本月产值",
          value: formatAmountInWan(monthly.contract_amount || 0),
          change: 0,
          changePercent: "0%",
          trend: "up",
          icon: DollarSign,
          color: "text-emerald-400",
          bgColor: "bg-emerald-500/10",
        },
        {
          label: "交付准时率",
          value: `${deliveryRate.toFixed(0)}%`,
          change: 0,
          changePercent: "0%",
          trend: deliveryRate >= 0 ? "up" : "down",
          icon: Clock,
          color: "text-amber-400",
          bgColor: "bg-amber-500/10",
        },
        {
          label: "工程师利用率",
          value: `${utilizationRate.toFixed(0)}%`,
          change: 0,
          changePercent: "0%",
          trend: utilizationRate >= 0 ? "up" : "down",
          icon: Users,
          color: "text-purple-400",
          bgColor: "bg-purple-500/10",
        },
      ];

      const topProjects = [...boardProjects]
        .sort((a, b) => Number(b.contract_amount || 0) - Number(a.contract_amount || 0))
        .slice(0, 5)
        .map((project) => ({
          id: project.project_code || project.id,
          name: project.project_name || "-",
          customer: project.customer_name || "-",
          value: Math.round(Number(project.contract_amount || 0) / 10000),
          progress: Math.round(Number(project.progress_pct || 0)),
          health: project.health || "H1",
        }));

      const alerts = (alertData.items || [])
        .slice(0, 3)
        .map((alert) => {
          const level = (alert.alert_level || "").toUpperCase();
          const type =
            level === "CRITICAL" || level === "HIGH"
              ? "urgent"
              : level === "MAJOR" || level === "MEDIUM"
                ? "warning"
                : "info";
          return {
            type,
            message: alert.alert_title || alert.alert_content || "预警触发",
            time: formatTimeAgo(alert.triggered_at),
          };
        });

      const utilizationList = utilizationData?.utilization_list || [];
      const deptUtilization = {};
      (utilizationList || []).forEach((entry) => {
        const dept = entry.department || "未分配";
        if (!deptUtilization[dept]) {
          deptUtilization[dept] = { total: 0, count: 0 };
        }
        deptUtilization[dept].total += Number(entry.utilization_rate || 0);
        deptUtilization[dept].count += 1;
      });

      const userDeptMap = new Map(
        (utilizationList || []).map((entry) => [entry.user_id, entry.department || "未分配"])
      );
      const deptProjectCounts = {};
      (boardProjects || []).forEach((project) => {
        const dept = userDeptMap.get(project.pm_id) || "未分配";
        deptProjectCounts[dept] = (deptProjectCounts[dept] || 0) + 1;
      });

      const departmentNames = new Set([
        ...Object.keys(deptUtilization),
        ...Object.keys(deptProjectCounts),
      ]);
      const departmentPerformance = Array.from(departmentNames).map((name) => {
        const util = deptUtilization[name];
        const avgUtilization = util ? util.total / util.count : 0;
        return {
          name,
          utilization: Math.round(avgUtilization),
          projects: deptProjectCounts[name] || 0,
          onTime: null,
        };
      });

      const monthlyTrend = buildMonthlyTrend(boardProjects, 6);

      if (!cancelled) {
        setDashboardData({
          kpis,
          projectHealth: {
            healthy: healthyCount,
            atRisk: atRiskCount,
            blocked: blockedCount,
            total: healthyCount + atRiskCount + blockedCount,
          },
          monthlyTrend,
          departmentPerformance,
          alerts,
          topProjects,
        });
        setError(errors.length ? errors.join("；") : null);
        setLoading(false);
      }
    };

    loadDashboard();

    return () => {
      cancelled = true;
    };
  }, [timeRange]);

  return { dashboardData, loading, error };
}
