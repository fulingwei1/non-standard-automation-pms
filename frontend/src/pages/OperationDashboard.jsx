import { useEffect, useState } from "react";
import { motion } from "framer-motion";
import {
  BarChart3,
  Users,
  Package,
  DollarSign,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Target,
  Activity,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import api, { alertApi, projectApi } from "../services/api";

const DEFAULT_DASHBOARD_DATA = {
  kpis: [],
  projectHealth: {
    healthy: 0,
    atRisk: 0,
    blocked: 0,
    total: 0,
  },
  monthlyTrend: [],
  departmentPerformance: [],
  alerts: [],
  topProjects: [],
};

const formatTimeAgo = (value) => {
  if (!value) {return "";}
  const target = new Date(value);
  if (Number.isNaN(target.getTime())) {return value;}
  const diff = Date.now() - target.getTime();
  const minute = 60 * 1000;
  const hour = 60 * minute;
  const day = 24 * hour;
  if (diff < minute) {return "刚刚";}
  if (diff < hour) {return `${Math.max(1, Math.floor(diff / minute))}分钟前`;}
  if (diff < day) {return `${Math.floor(diff / hour)}小时前`;}
  if (diff < 30 * day) {return `${Math.floor(diff / day)}天前`;}
  return target.toLocaleDateString("zh-CN");
};

const formatAmountInWan = (value) => {
  const amount = Number(value || 0);
  if (amount <= 0) {return "¥0";}
  const wan = amount / 10000;
  if (wan >= 1) {
    return `¥${wan.toFixed(wan >= 100 ? 0 : 1)}万`;
  }
  return `¥${amount.toFixed(2)}`;
};

const buildDateRange = (range) => {
  const end = new Date();
  const start = new Date(end);
  const days = range === "week" ? 7 : range === "quarter" ? 90 : 30;
  start.setDate(end.getDate() - days + 1);
  const toISODate = (date) => date.toISOString().slice(0, 10);
  return { start_date: toISODate(start), end_date: toISODate(end) };
};

const buildMonthlyTrend = (projects, months = 6) => {
  const now = new Date();
  const buckets = [];
  for (let i = months - 1; i >= 0; i -= 1) {
    const date = new Date(now.getFullYear(), now.getMonth() - i, 1);
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    buckets.push({ key, label: `${date.getMonth() + 1}月`, amount: 0 });
  }
  const bucketMap = new Map((buckets || []).map((bucket) => [bucket.key, bucket]));
  (projects || []).forEach((project) => {
    const dateValue = project.planned_end_date || project.contract_date;
    if (!dateValue) {return;}
    const date = new Date(dateValue);
    if (Number.isNaN(date.getTime())) {return;}
    const key = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}`;
    const bucket = bucketMap.get(key);
    if (bucket) {
      bucket.amount += Number(project.contract_amount || 0);
    }
  });
  return (buckets || []).map((bucket) => ({
    month: bucket.label,
    revenue: Math.round(bucket.amount / 10000),
  }));
};

function KpiCard({ kpi }) {
  return (
    <Card className="bg-surface-1/50 hover:bg-surface-1/70 transition-colors">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className={cn("p-3 rounded-xl", kpi.bgColor)}>
            <kpi.icon className={cn("w-6 h-6", kpi.color)}  />
          </div>
          <div
            className={cn(
              "flex items-center gap-1 text-xs font-medium",
              kpi.trend === "up" ? "text-emerald-400" : "text-red-400",
            )}
          >
            {kpi.trend === "up" ? (
              <ArrowUpRight className="w-4 h-4" />
            ) : (
              <ArrowDownRight className="w-4 h-4" />
            )}
            {kpi.changePercent}
          </div>
        </div>
        <div className="mt-4">
          <p className="text-sm text-slate-400">{kpi.label}</p>
          <p className="text-3xl font-bold text-white mt-1">{kpi.value}</p>
        </div>
      </CardContent>
    </Card>
  );
}

function HealthDonut({ data }) {
  const total = data.total;
  const safeTotal = total > 0 ? total : 1;
  const healthyPercent = total > 0 ? (data.healthy / safeTotal) * 100 : 0;
  const atRiskPercent = total > 0 ? (data.atRisk / safeTotal) * 100 : 0;
  const blockedPercent = total > 0 ? (data.blocked / safeTotal) * 100 : 0;

  return (
    <div className="flex items-center gap-6">
      {/* Donut Chart */}
      <div className="relative w-32 h-32">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
          {/* Background */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            className="text-surface-2"
          />
          {/* Healthy */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={`${healthyPercent} ${100 - healthyPercent}`}
            strokeDashoffset="0"
            className="text-emerald-500"
          />
          {/* At Risk */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={`${atRiskPercent} ${100 - atRiskPercent}`}
            strokeDashoffset={`${-healthyPercent}`}
            className="text-amber-500"
          />
          {/* Blocked */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={`${blockedPercent} ${100 - blockedPercent}`}
            strokeDashoffset={`${-(healthyPercent + atRiskPercent)}`}
            className="text-red-500"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-white">{total}</span>
          <span className="text-xs text-slate-400">项目</span>
        </div>
      </div>

      {/* Legend */}
      <div className="space-y-3">
        {[
          { label: "正常", value: data.healthy, color: "bg-emerald-500" },
          { label: "风险", value: data.atRisk, color: "bg-amber-500" },
          { label: "阻塞", value: data.blocked, color: "bg-red-500" },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <div className={cn("w-3 h-3 rounded-full", item.color)} />
            <span className="text-sm text-slate-400">{item.label}</span>
            <span className="text-sm font-medium text-white ml-auto">
              {item.value}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}

function MiniBarChart({ data }) {
  if (!data || data?.length === 0) {
    return <div className="text-sm text-slate-400">暂无产值数据</div>;
  }
  const maxValue = Math.max(...(data || []).map((d) => d.revenue), 0);
  if (maxValue === 0) {
    return <div className="text-sm text-slate-400">暂无产值数据</div>;
  }
  const safeMax = maxValue;

  return (
    <div className="flex items-end gap-2 h-32">
      {(data || []).map((item, index) => (
        <div key={index} className="flex-1 flex flex-col items-center gap-1">
          <div className="w-full flex flex-col items-center gap-1">
            <span className="text-xs text-slate-400">
              {(item.revenue / 100).toFixed(0)}K
            </span>
            <div
              className="w-full bg-gradient-to-t from-accent/50 to-accent rounded-t-sm transition-all hover:from-accent/70"
              style={{ height: `${(item.revenue / safeMax) * 80}px` }}
            />
          </div>
          <span className="text-xs text-slate-500">{item.month}</span>
        </div>
      ))}
    </div>
  );
}

export default function OperationDashboard() {
  const [timeRange, setTimeRange] = useState("month");
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

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="运营大屏"
        description="实时监控公司运营状况，辅助管理决策"
        actions={
          <div className="flex items-center gap-2">
            {["week", "month", "quarter"].map((range) => (
              <Button
                key={range}
                variant={timeRange === range ? "default" : "outline"}
                size="sm"
                onClick={() => setTimeRange(range)}
              >
                {range === "week"
                  ? "本周"
                  : range === "month"
                    ? "本月"
                    : "本季度"}
              </Button>
            ))}
          </div>
        }
      />

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-200">
          运营大屏数据加载失败：{error}
        </div>
      )}
      {loading && (
        <div className="text-sm text-slate-400">数据加载中...</div>
      )}

      {/* KPI Cards */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
      >
        {(dashboardData.kpis || []).map((kpi, index) => (
          <KpiCard key={index} kpi={kpi} />
        ))}
      </motion.div>

      {/* Main Content Grid */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 lg:grid-cols-3 gap-6"
      >
        {/* Project Health */}
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              项目健康度
            </CardTitle>
          </CardHeader>
          <CardContent>
            <HealthDonut data={dashboardData.projectHealth} />
          </CardContent>
        </Card>

        {/* Revenue Trend */}
        <Card className="bg-surface-1/50 lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              产值趋势
            </CardTitle>
            <CardDescription>近6个月产值（万元）</CardDescription>
          </CardHeader>
          <CardContent>
            <MiniBarChart data={dashboardData.monthlyTrend} />
          </CardContent>
        </Card>
      </motion.div>

      {/* Department Performance & Alerts */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-1 lg:grid-cols-2 gap-6"
      >
        {/* Department Performance */}
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              部门绩效
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {dashboardData.departmentPerformance?.length === 0 ? (
              <div className="text-sm text-slate-400">暂无部门绩效数据</div>
            ) : (
              (dashboardData.departmentPerformance || []).map((dept, index) => {
                const onTimeValue = Number.isFinite(dept.onTime) ? dept.onTime : null;
                return (
                  <div key={index} className="space-y-2">
                    <div className="flex items-center justify-between">
                      <span className="text-sm text-white">{dept.name}</span>
                      <div className="flex items-center gap-4 text-xs">
                        <span className="text-slate-400">{dept.projects} 项目</span>
                        <span
                          className={cn(
                            onTimeValue === null
                              ? "text-slate-400"
                              : onTimeValue >= 90
                                ? "text-emerald-400"
                                : onTimeValue >= 80
                                  ? "text-amber-400"
                                  : "text-red-400",
                          )}
                        >
                          准时率 {onTimeValue === null ? "--" : `${onTimeValue}%`}
                        </span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Progress value={dept.utilization} className="h-2 flex-1" />
                      <span
                        className={cn(
                          "text-xs font-medium w-10 text-right",
                          dept.utilization >= 90
                            ? "text-amber-400"
                            : "text-emerald-400",
                        )}
                      >
                        {dept.utilization}%
                      </span>
                    </div>
                  </div>
                );
              })
            )}
          </CardContent>
        </Card>

        {/* Alerts */}
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              实时预警
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {dashboardData.alerts?.length === 0 ? (
              <div className="text-sm text-slate-400">暂无预警数据</div>
            ) : (
              (dashboardData.alerts || []).map((alert, index) => (
                <div
                  key={index}
                  className={cn(
                    "p-3 rounded-lg flex items-start gap-3",
                    alert.type === "urgent"
                      ? "bg-red-500/10"
                      : alert.type === "warning"
                        ? "bg-amber-500/10"
                        : "bg-blue-500/10",
                  )}
                >
                  {alert.type === "urgent" ? (
                    <Zap className="w-4 h-4 text-red-400 mt-0.5" />
                  ) : alert.type === "warning" ? (
                    <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5" />
                  ) : (
                    <CheckCircle2 className="w-4 h-4 text-blue-400 mt-0.5" />
                  )}
                  <div className="flex-1 min-w-0">
                    <p
                      className={cn(
                        "text-sm",
                        alert.type === "urgent"
                          ? "text-red-300"
                          : alert.type === "warning"
                            ? "text-amber-300"
                            : "text-blue-300",
                      )}
                    >
                      {alert.message}
                    </p>
                    <p className="text-xs text-slate-500 mt-1">{alert.time}</p>
                  </div>
                </div>
              ))
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* Top Projects */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5" />
              重点项目
            </CardTitle>
            <CardDescription>当前在制的高价值项目</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              {dashboardData.topProjects?.length === 0 ? (
                <div className="text-sm text-slate-400 py-6 text-center">暂无重点项目</div>
              ) : (
                <table className="w-full text-sm">
                  <thead>
                    <tr className="border-b border-border">
                      <th className="text-left p-3 text-slate-400 font-medium">
                        项目编号
                      </th>
                      <th className="text-left p-3 text-slate-400 font-medium">
                        项目名称
                      </th>
                      <th className="text-left p-3 text-slate-400 font-medium">
                        客户
                      </th>
                      <th className="text-right p-3 text-slate-400 font-medium">
                        合同金额
                      </th>
                      <th className="text-center p-3 text-slate-400 font-medium">
                        进度
                      </th>
                      <th className="text-center p-3 text-slate-400 font-medium">
                        状态
                      </th>
                    </tr>
                  </thead>
                  <tbody>
                    {(dashboardData.topProjects || []).map((project) => (
                      <tr
                        key={project.id}
                        className="border-b border-border/50 hover:bg-surface-2/30"
                      >
                        <td className="p-3">
                          <span className="font-mono text-accent">
                            {project.id}
                          </span>
                        </td>
                        <td className="p-3 text-white">{project.name}</td>
                        <td className="p-3 text-slate-400">{project.customer}</td>
                        <td className="p-3 text-right text-white font-medium">
                          ¥{project.value}万
                        </td>
                        <td className="p-3">
                          <div className="flex items-center gap-2">
                            <Progress
                              value={project.progress}
                              className="h-1.5 w-20"
                            />
                            <span className="text-xs text-slate-400">
                              {project.progress}%
                            </span>
                          </div>
                        </td>
                        <td className="p-3 text-center">
                          <Badge
                            className={cn(
                              project.health === "H1"
                                ? "bg-emerald-500/20 text-emerald-400"
                                : project.health === "H2"
                                  ? "bg-amber-500/20 text-amber-400"
                                  : "bg-red-500/20 text-red-400",
                            )}
                          >
                            {project.health === "H1"
                              ? "正常"
                              : project.health === "H2"
                                ? "风险"
                                : "阻塞"}
                          </Badge>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              )}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
