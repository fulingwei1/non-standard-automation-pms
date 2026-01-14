import { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { projectApi, machineApi } from "../services/api";
import { formatCurrency, getHealthColor, getStageName } from "../lib/utils";
import {
  DashboardLayout,
  DashboardStatCard,
  useDashboardData,
  VirtualizedProjectList,
} from "../components/dashboard";
import {
  Card,
  CardContent,
  Progress,
  Badge,
  HealthBadge,
  SkeletonCard,
} from "../components/ui";
import {
  Briefcase,
  Box,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock,
  Crown,
  Zap,
  GitBranch,
  ShoppingCart,
  Hammer,
} from "lucide-react";

// Stagger animation variants
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

// Note: Role-based redirect mapping is now handled in App.jsx at the route level
// This Dashboard component will only render for users without a specific dashboard

export default function Dashboard() {
  // 使用统一的数据获取Hook
  const { data: projectsData, loading: projectsLoading } = useDashboardData({
    fetchFn: () => projectApi.list(),
    cacheKey: "dashboard_projects",
    cacheTime: 5 * 60 * 1000, // 5分钟缓存
  });

  const { data: machinesData, loading: machinesLoading } = useDashboardData({
    fetchFn: () => machineApi.list({}),
    cacheKey: "dashboard_machines",
    cacheTime: 5 * 60 * 1000,
  });

  const loading = projectsLoading || machinesLoading;

  // 处理不同API响应格式
  const projects = (() => {
    if (!projectsData) return [];
    if (Array.isArray(projectsData)) return projectsData;
    if (Array.isArray(projectsData.items)) return projectsData.items;
    if (Array.isArray(projectsData.data)) return projectsData.data;
    return [];
  })();

  const machines = (() => {
    if (!machinesData) return [];
    if (Array.isArray(machinesData)) return machinesData;
    if (Array.isArray(machinesData.items)) return machinesData.items;
    if (Array.isArray(machinesData.data)) return machinesData.data;
    return [];
  })();

  const stats = {
    totalProjects: projects.length,
    activeProjects: projects.filter((p) => p.health !== "H4").length,
    totalMachines: machines.length,
    atRiskProjects: projects.filter((p) => ["H2", "H3"].includes(p.health))
      .length,
  };

  const recentProjects = projects.slice(0, 5);

  const statCards = [
    {
      icon: Briefcase,
      label: "总项目数",
      value: stats.totalProjects,
      change: "+12%",
      trend: "up",
    },
    {
      icon: BarChart3,
      label: "进行中项目",
      value: stats.activeProjects,
      change: "+3",
      trend: "up",
    },
    {
      icon: Box,
      label: "设备总数",
      value: stats.totalMachines,
      change: "+8%",
      trend: "up",
    },
    {
      icon: AlertTriangle,
      label: "风险项目",
      value: stats.atRiskProjects,
      change: "-2",
      trend: "down",
    },
  ];

  // 角色卡片配置
  const roleCards = [
    {
      title: "董事长",
      icon: Crown,
      path: "/chairman-dashboard",
      color: "from-purple-500/20 to-purple-600/10",
      iconColor: "text-purple-400",
      ringColor: "ring-purple-500/20",
      hoverColor: "hover:bg-purple-500/10",
      description: "董事长决策分析",
    },
    {
      title: "总经理",
      icon: Zap,
      path: "/gm-dashboard",
      color: "from-orange-500/20 to-orange-600/10",
      iconColor: "text-orange-400",
      ringColor: "ring-orange-500/20",
      hoverColor: "hover:bg-orange-500/10",
      description: "经营管理概览",
    },
    {
      title: "项目经理",
      icon: GitBranch,
      path: "/pmo/dashboard",
      color: "from-blue-500/20 to-blue-600/10",
      iconColor: "text-blue-400",
      ringColor: "ring-blue-500/20",
      hoverColor: "hover:bg-blue-500/10",
      description: "项目管理办公室",
    },
    {
      title: "销售总监",
      icon: TrendingUp,
      path: "/sales-director-dashboard",
      color: "from-rose-500/20 to-rose-600/10",
      iconColor: "text-rose-400",
      ringColor: "ring-rose-500/20",
      hoverColor: "hover:bg-rose-500/10",
      description: "销售管理概览",
    },
    {
      title: "销售经理",
      icon: Briefcase,
      path: "/sales-manager-dashboard",
      color: "from-pink-500/20 to-pink-600/10",
      iconColor: "text-pink-400",
      ringColor: "ring-pink-500/20",
      hoverColor: "hover:bg-pink-500/10",
      description: "销售执行与跟踪",
    },
    {
      title: "P&C (采购控制)",
      icon: ShoppingCart,
      path: "/procurement-manager-dashboard",
      color: "from-green-500/20 to-green-600/10",
      iconColor: "text-green-400",
      ringColor: "ring-green-500/20",
      hoverColor: "hover:bg-green-500/10",
      description: "采购与物料管理",
    },
    {
      title: "机械部经理",
      icon: Hammer,
      path: "/mech-manager-dashboard",
      color: "from-orange-500/20 to-orange-600/10",
      iconColor: "text-orange-400",
      ringColor: "ring-orange-500/20",
      hoverColor: "hover:bg-orange-500/10",
      description: "机械部门管理",
    },
  ];

  return (
    <DashboardLayout
      title="仪表盘"
      description="项目全局概览与关键指标"
    >
      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat, i) => (
          <DashboardStatCard
            key={i}
            {...stat}
            loading={loading}
          />
        ))}
      </div>

      {/* Role Selection Grid */}
      <div className="mb-8">
        <h3 className="text-lg font-semibold text-white mb-4">快速导航</h3>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {roleCards.map((role, index) => {
            const RoleIcon = role.icon;
            return (
              <motion.div
                key={index}
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.98 }}
              >
                <Link to={role.path}>
                  <Card
                    hover={true}
                    className={cn(
                      "h-full",
                      "bg-gradient-to-br",
                      role.color,
                      "border-white/5 group",
                    )}
                  >
                    <CardContent className="flex flex-col items-center justify-center p-6 text-center">
                      <div
                        className={cn(
                          "p-3 rounded-xl mb-3",
                          "bg-gradient-to-br",
                          role.color,
                          "ring-1",
                          role.ringColor,
                          "group-hover:scale-110 transition-transform",
                        )}
                      >
                        <RoleIcon
                          className={cn("h-6 w-6", role.iconColor)}
                        />
                      </div>
                      <h4 className="text-base font-semibold text-white mb-1">
                        {role.title}
                      </h4>
                      <p className="text-xs text-slate-400">
                        {role.description}
                      </p>
                      <div className="mt-3 flex items-center justify-center">
                        <ArrowRight className="h-4 w-4 text-slate-500 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </div>
                    </CardContent>
                  </Card>
                </Link>
              </motion.div>
            );
          })}
        </div>
      </div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Projects */}
        <div className="lg:col-span-2">
          <Card hover={false}>
            <CardContent className="p-0">
              <div className="flex items-center justify-between p-5 border-b border-white/5">
                <h3 className="text-lg font-semibold text-white">最近项目</h3>
                <Link
                  to="/projects"
                  className="flex items-center gap-1 text-sm text-primary hover:text-primary-light transition-colors"
                >
                  查看全部 <ArrowRight className="h-4 w-4" />
                </Link>
              </div>

              {loading ? (
                <div className="p-5 space-y-4">
                  {Array(3)
                    .fill(null)
                    .map((_, i) => (
                      <SkeletonCard key={i} />
                    ))}
                </div>
              ) : recentProjects.length > 0 ? (
                // 使用虚拟滚动优化长列表性能
                recentProjects.length > 10 ? (
                  <VirtualizedProjectList
                    projects={recentProjects}
                    itemHeight={80}
                  />
                ) : (
                  <div className="divide-y divide-white/5">
                    {recentProjects.map((project) => (
                      <Link
                        key={project.id}
                        to={`/projects/${project.id}`}
                        className="flex items-center gap-4 p-5 hover:bg-white/[0.02] transition-colors group"
                      >
                        {/* Icon */}
                        <div
                          className={cn(
                            "p-3 rounded-xl",
                            "bg-gradient-to-br from-primary/20 to-indigo-500/10",
                            "ring-1 ring-primary/20",
                            "group-hover:scale-105 transition-transform",
                          )}
                        >
                          <Briefcase className="h-5 w-5 text-primary" />
                        </div>

                        {/* Info */}
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center gap-3 mb-1">
                            <h4 className="font-medium text-white truncate">
                              {project.project_name}
                            </h4>
                            <HealthBadge health={project.health || "H1"} />
                          </div>
                          <div className="flex items-center gap-4 text-sm text-slate-500">
                            <span>{project.project_code}</span>
                            <span>•</span>
                            <span>{project.customer_name}</span>
                          </div>
                        </div>

                        {/* Progress */}
                        <div className="w-32 hidden sm:block">
                          <div className="flex justify-between text-xs mb-1">
                            <span className="text-slate-400">进度</span>
                            <span className="text-white">
                              {project.progress_pct || 0}%
                            </span>
                          </div>
                          <Progress value={project.progress_pct || 0} size="sm" />
                        </div>

                        {/* Arrow */}
                        <ArrowRight className="h-5 w-5 text-slate-600 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                      </Link>
                    ))}
                  </div>
                )
              ) : (
                <div className="p-12 text-center text-slate-500">
                  暂无项目数据
                </div>
              )}
            </CardContent>
          </Card>
        </div>

        {/* Quick Actions */}
        <div>
          <Card hover={false}>
            <CardContent>
              <h3 className="text-lg font-semibold text-white mb-4">
                快捷操作
              </h3>
              <div className="space-y-3">
                <Link
                  to="/projects"
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
                  <span className="text-sm font-medium">新建项目</span>
                </Link>

                <Link
                  to="/machines"
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-xl",
                    "bg-white/[0.03] border border-white/5",
                    "text-white hover:bg-white/[0.06] hover:border-white/10",
                    "transition-all duration-200",
                  )}
                >
                  <div className="p-2 rounded-lg bg-emerald-500/20">
                    <Box className="h-4 w-4 text-emerald-400" />
                  </div>
                  <span className="text-sm font-medium">添加设备</span>
                </Link>

                <Link
                  to="/alerts"
                  className={cn(
                    "flex items-center gap-3 p-3 rounded-xl",
                    "bg-white/[0.03] border border-white/5",
                    "text-white hover:bg-white/[0.06] hover:border-white/10",
                    "transition-all duration-200",
                  )}
                >
                  <div className="p-2 rounded-lg bg-amber-500/20">
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                  </div>
                  <span className="text-sm font-medium">查看预警</span>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Schedule Overview */}
          <Card hover={false} className="mt-6">
            <CardContent>
              <h3 className="text-lg font-semibold text-white mb-4">
                今日待办
              </h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02]">
                  <div className="mt-0.5">
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-sm text-white">项目评审会议</p>
                    <p className="text-xs text-slate-500">10:00 - 11:00</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02]">
                  <div className="mt-0.5">
                    <Clock className="h-5 w-5 text-amber-500" />
                  </div>
                  <div>
                    <p className="text-sm text-white">设备出厂验收</p>
                    <p className="text-xs text-slate-500">14:00 - 16:00</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02]">
                  <div className="mt-0.5">
                    <Clock className="h-5 w-5 text-slate-500" />
                  </div>
                  <div>
                    <p className="text-sm text-white">周进度汇报</p>
                    <p className="text-xs text-slate-500">17:00 - 18:00</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    </DashboardLayout>
  );
}
