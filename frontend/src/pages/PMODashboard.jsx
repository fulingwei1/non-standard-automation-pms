import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { pmoApi } from "../services/api";
import { formatCurrency } from "../lib/utils";
import { PageHeader } from "../components/layout/PageHeader";
import {
  Card,
  CardContent,
  DashboardStatCard,
  Progress,
  Badge,
  SkeletonCard,
  ApiIntegrationError,
} from "../components/ui";
import {
  Briefcase,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock,
  DollarSign,
  Users,
  Target,
  Activity,
} from "lucide-react";
import { CrossDepartmentProgress } from "../components/pmo/CrossDepartmentProgress";

const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
};

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

const getRiskLevelColor = (level) => {
  const colors = {
    CRITICAL: "bg-red-500/20 text-red-400 border-red-500/30",
    HIGH: "bg-orange-500/20 text-orange-400 border-orange-500/30",
    MEDIUM: "bg-yellow-500/20 text-yellow-400 border-yellow-500/30",
    LOW: "bg-blue-500/20 text-blue-400 border-blue-500/30",
  };
  return colors[level] || colors.LOW;
};

const getRiskLevelName = (level) => {
  const names = {
    CRITICAL: "严重",
    HIGH: "高",
    MEDIUM: "中",
    LOW: "低",
  };
  return names[level] || "未知";
};

// Mock data removed - using real API only

export default function PMODashboard() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [dashboardData, setDashboardData] = useState(null);
  const [selectedProjectId, setSelectedProjectId] = useState(null);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await pmoApi.dashboard();
      setDashboardData(res.data);
    } catch (err) {
      console.error("Failed to fetch PMO dashboard data:", err);
      setError(err);
      setDashboardData(null);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchData();
  }, []);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="PMO 驾驶舱" description="项目管理部全景视图" />
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {Array(8)
            .fill(null)
            .map((_, i) => (
              <Card key={i} className="p-5">
                <div className="animate-pulse">
                  <div className="h-10 w-10 rounded-xl bg-white/10 mb-4" />
                  <div className="h-3 w-20 rounded bg-white/10 mb-3" />
                  <div className="h-6 w-16 rounded bg-white/10" />
                </div>
              </Card>
            ))}
        </div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader title="PMO 驾驶舱" description="项目管理部全景视图" />
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/pmo/dashboard"
          onRetry={fetchData}
        />
      </div>
    );
  }

  if (!dashboardData) {
    return (
      <div className="space-y-6">
        <PageHeader title="PMO 驾驶舱" description="项目管理部全景视图" />
        <Card>
          <CardContent className="p-12 text-center text-slate-500">
            暂无数据
          </CardContent>
        </Card>
      </div>
    );
  }

  const { summary, projects_by_status, projects_by_stage, recent_risks } =
    dashboardData;

  const statCards = [
    {
      icon: Briefcase,
      label: "项目总数",
      value: summary?.total_projects || 0,
      change: `${summary?.active_projects || 0} 进行中`,
      trend: "up",
      color: "text-blue-400",
    },
    {
      icon: Activity,
      label: "活跃项目",
      value: summary?.active_projects || 0,
      change: `${summary?.completed_projects || 0} 已完成`,
      trend: "up",
      color: "text-emerald-400",
    },
    {
      icon: AlertTriangle,
      label: "延期项目",
      value: summary?.delayed_projects || 0,
      change: summary?.delayed_projects > 0 ? "需关注" : "正常",
      trend: summary?.delayed_projects > 0 ? "down" : "up",
      color: "text-red-400",
    },
    {
      icon: DollarSign,
      label: "总预算",
      value: formatCurrency(summary?.total_budget || 0),
      change: `成本: ${formatCurrency(summary?.total_cost || 0)}`,
      trend: "up",
      color: "text-violet-400",
    },
    {
      icon: Target,
      label: "风险总数",
      value: summary?.total_risks || 0,
      change: `${summary?.critical_risks || 0} 严重`,
      trend: summary?.critical_risks > 0 ? "down" : "up",
      color: "text-orange-400",
    },
    {
      icon: AlertTriangle,
      label: "高风险",
      value: summary?.high_risks || 0,
      change: `${summary?.critical_risks || 0} 严重`,
      trend: summary?.high_risks > 0 ? "down" : "up",
      color: "text-red-400",
    },
    {
      icon: Users,
      label: "已完成",
      value: summary?.completed_projects || 0,
      change: "项目",
      trend: "up",
      color: "text-green-400",
    },
    {
      icon: BarChart3,
      label: "成本执行率",
      value:
        summary?.total_budget > 0
          ? `${((summary?.total_cost / summary?.total_budget) * 100).toFixed(1)}%`
          : "0%",
      change: "预算执行",
      trend: "up",
      color: "text-indigo-400",
    },
  ];

  return (
    <motion.div initial="hidden" animate="visible" variants={staggerContainer}>
      <motion.div variants={staggerChild}>
        <PageHeader
          title="PMO 驾驶舱"
          description="项目管理部全景视图与关键指标监控"
        />
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        variants={staggerChild}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        {(statCards || []).map((stat, i) => (
          <DashboardStatCard key={i} {...stat} />
        ))}
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Project Status Distribution */}
        <motion.div variants={staggerChild} className="lg:col-span-2">
          <Card hover={false}>
            <CardContent className="p-0">
              <div className="flex items-center justify-between p-5 border-b border-white/5">
                <h3 className="text-lg font-semibold text-white">
                  项目状态分布
                </h3>
              </div>

              <div className="p-5 space-y-4">
                {/* By Status */}
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-3">
                    按状态
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {Object.entries(projects_by_status || {}).map(
                      ([status, count]) => (
                        <div
                          key={status}
                          className="p-3 rounded-xl bg-white/[0.02] border border-white/5"
                        >
                          <div className="text-2xl font-bold text-white mb-1">
                            {count}
                          </div>
                          <div className="text-xs text-slate-400">{status}</div>
                        </div>
                      ),
                    )}
                  </div>
                </div>

                {/* By Stage */}
                <div>
                  <h4 className="text-sm font-medium text-slate-400 mb-3">
                    按阶段
                  </h4>
                  <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                    {Object.entries(projects_by_stage || {}).map(
                      ([stage, count]) => (
                        <div
                          key={stage}
                          className="p-3 rounded-xl bg-white/[0.02] border border-white/5"
                        >
                          <div className="text-2xl font-bold text-white mb-1">
                            {count}
                          </div>
                          <div className="text-xs text-slate-400">{stage}</div>
                        </div>
                      ),
                    )}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Recent Risks */}
          <Card hover={false} className="mt-6">
            <CardContent className="p-0">
              <div className="flex items-center justify-between p-5 border-b border-white/5">
                <h3 className="text-lg font-semibold text-white">最近风险</h3>
                <Link
                  to="/pmo/risks"
                  className="flex items-center gap-1 text-sm text-primary hover:text-primary-light transition-colors"
                >
                  查看全部 <ArrowRight className="h-4 w-4" />
                </Link>
              </div>

              {recent_risks && recent_risks.length > 0 ? (
                <div className="divide-y divide-white/5">
                  {recent_risks.slice(0, 5).map((risk) => (
                    <div
                      key={risk.id}
                      className="p-5 hover:bg-white/[0.02] transition-colors"
                    >
                      <div className="flex items-start gap-4">
                        <div
                          className={cn(
                            "px-2 py-1 rounded text-xs font-medium border",
                            getRiskLevelColor(risk.risk_level),
                          )}
                        >
                          {getRiskLevelName(risk.risk_level)}
                        </div>
                        <div className="flex-1 min-w-0">
                          <h4 className="font-medium text-white mb-1">
                            {risk.risk_name}
                          </h4>
                          <p className="text-sm text-slate-400 line-clamp-2">
                            {risk.description}
                          </p>
                          <div className="flex items-center gap-4 mt-2 text-xs text-slate-500">
                            <span>{risk.risk_category}</span>
                            {risk.owner_name && (
                              <>
                                <span>•</span>
                                <span>负责人: {risk.owner_name}</span>
                              </>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              ) : (
                <div className="p-12 text-center text-slate-500">
                  暂无风险数据
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Quick Actions */}
        <motion.div variants={staggerChild}>
          <Card hover={false}>
            <CardContent>
              <h3 className="text-lg font-semibold text-white mb-4">
                快捷操作
              </h3>
              <div className="space-y-3">
                <Link
                  to="/pmo/initiations"
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-xl",
                    "bg-white/[0.03] border border-white/5",
                    "text-white hover:bg-white/[0.06] hover:border-white/10",
                    "transition-all duration-200",
                  )}
                >
                  <div className="p-2 rounded-lg bg-primary/20">
                    <Briefcase className="h-4 w-4 text-primary" />
                  </div>
                  <span className="text-sm font-medium">立项管理</span>
                </Link>

                <Link
                  to="/pmo/risks"
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-xl",
                    "bg-white/[0.03] border border-white/5",
                    "text-white hover:bg-white/[0.06] hover:border-white/10",
                    "transition-all duration-200",
                  )}
                >
                  <div className="p-2 rounded-lg bg-red-500/20">
                    <AlertTriangle className="h-4 w-4 text-red-400" />
                  </div>
                  <span className="text-sm font-medium">风险管理</span>
                </Link>

                <Link
                  to="/pmo/phases"
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-xl",
                    "bg-white/[0.03] border border-white/5",
                    "text-white hover:bg-white/[0.06] hover:border-white/10",
                    "transition-all duration-200",
                  )}
                >
                  <div className="p-2 rounded-lg bg-emerald-500/20">
                    <Target className="h-4 w-4 text-emerald-400" />
                  </div>
                  <span className="text-sm font-medium">阶段管理</span>
                </Link>

                <Link
                  to="/pmo/resource-overview"
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-xl",
                    "bg-white/[0.03] border border-white/5",
                    "text-white hover:bg-white/[0.06] hover:border-white/10",
                    "transition-all duration-200",
                  )}
                >
                  <div className="p-2 rounded-lg bg-violet-500/20">
                    <Users className="h-4 w-4 text-violet-400" />
                  </div>
                  <span className="text-sm font-medium">资源总览</span>
                </Link>

                <Link
                  to="/pmo/risk-wall"
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-xl",
                    "bg-white/[0.03] border border-white/5",
                    "text-white hover:bg-white/[0.06] hover:border-white/10",
                    "transition-all duration-200",
                  )}
                >
                  <div className="p-2 rounded-lg bg-red-500/20">
                    <AlertTriangle className="h-4 w-4 text-red-400" />
                  </div>
                  <span className="text-sm font-medium">风险预警墙</span>
                </Link>

                <Link
                  to="/pmo/weekly-report"
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-xl",
                    "bg-white/[0.03] border border-white/5",
                    "text-white hover:bg-white/[0.06] hover:border-white/10",
                    "transition-all duration-200",
                  )}
                >
                  <div className="p-2 rounded-lg bg-indigo-500/20">
                    <BarChart3 className="h-4 w-4 text-indigo-400" />
                  </div>
                  <span className="text-sm font-medium">项目周报</span>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Risk Summary */}
          <Card hover={false} className="mt-6">
            <CardContent>
              <h3 className="text-lg font-semibold text-white mb-4">
                风险概览
              </h3>
              <div className="space-y-3">
                <div className="flex items-center justify-between p-3 rounded-xl bg-red-500/10 border border-red-500/20">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-red-400" />
                    <div>
                      <p className="text-sm font-medium text-white">严重风险</p>
                      <p className="text-xs text-slate-400">
                        {summary?.critical_risks || 0} 个
                      </p>
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-red-400">
                    {summary?.critical_risks || 0}
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-orange-500/10 border border-orange-500/20">
                  <div className="flex items-center gap-3">
                    <AlertTriangle className="h-5 w-5 text-orange-400" />
                    <div>
                      <p className="text-sm font-medium text-white">高风险</p>
                      <p className="text-xs text-slate-400">
                        {summary?.high_risks || 0} 个
                      </p>
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-orange-400">
                    {summary?.high_risks || 0}
                  </div>
                </div>

                <div className="flex items-center justify-between p-3 rounded-xl bg-yellow-500/10 border border-yellow-500/20">
                  <div className="flex items-center gap-3">
                    <Target className="h-5 w-5 text-yellow-400" />
                    <div>
                      <p className="text-sm font-medium text-white">总风险</p>
                      <p className="text-xs text-slate-400">
                        {summary?.total_risks || 0} 个
                      </p>
                    </div>
                  </div>
                  <div className="text-2xl font-bold text-yellow-400">
                    {summary?.total_risks || 0}
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>

      {/* 跨部门进度视图 */}
      <motion.div variants={staggerChild} className="mt-8">
        <Card hover={false}>
          <CardContent className="p-6">
            <div className="mb-6">
              <h2 className="text-xl font-bold text-white mb-2">
                跨部门进度视图
              </h2>
              <p className="text-sm text-slate-400">
                选择项目查看各部门实时进度
              </p>
            </div>

            {/* 项目选择器 */}
            <div className="mb-6">
              <label className="block text-sm text-slate-400 mb-2">
                选择项目:
              </label>
              <select
                value={selectedProjectId || ""}
                onChange={(e) =>
                  setSelectedProjectId(
                    e.target.value ? parseInt(e.target.value) : null,
                  )
                }
                className="w-full md:w-96 px-4 py-2 rounded-lg bg-surface-2 border border-border text-white focus:outline-none focus:ring-2 focus:ring-primary/50 transition-all"
              >
                <option value="">-- 请选择项目 --</option>
                <option value="27">项目1 - BMS老化测试设备</option>
                <option value="28">项目2 - EOL功能测试设备</option>
                <option value="29">项目3 - ICT测试设备</option>
              </select>
            </div>

            {/* 跨部门进度组件 */}
            {selectedProjectId ? (
              <CrossDepartmentProgress projectId={selectedProjectId} />
            ) : (
              <div className="text-center py-12">
                <Users className="w-16 h-16 text-slate-600 mx-auto mb-4" />
                <p className="text-slate-400">请选择项目以查看跨部门进度</p>
              </div>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
