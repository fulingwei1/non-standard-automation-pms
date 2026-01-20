import { useEffect as _useEffect, useState as _useState } from "react";
import { Link } from "react-router-dom";
import { motion } from "framer-motion";
import { cn } from "../lib/utils";
import { projectApi, machineApi } from "../services/api";
import { formatCurrency as _formatCurrency, getHealthColor as _getHealthColor, getStageName as _getStageName } from "../lib/utils";
import {
  DashboardLayout,
  DashboardStatCard,
  useDashboardData,
  VirtualizedProjectList } from
"../components/dashboard";
import {
  Card,
  CardContent,
  Progress,
  Badge,
  HealthBadge,
  SkeletonCard } from
"../components/ui";
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
  Hammer } from
"lucide-react";

// Stagger animation variants
const _staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 }
  }
};

const _staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 }
};

// Note: Role-based redirect mapping is now handled in App.jsx at the route level
// This Dashboard component will only render for users without a specific dashboard

export default function Dashboard() {
  // 使用统一的数据获取Hook
  const { data: projectsData, loading: projectsLoading } = useDashboardData({
    fetchFn: () => projectApi.list(),
    cacheKey: "dashboard_projects",
    cacheTime: 5 * 60 * 1000 // 5分钟缓存
  });

  const { data: machinesData, loading: machinesLoading } = useDashboardData({
    fetchFn: () => machineApi.list({}),
    cacheKey: "dashboard_machines",
    cacheTime: 5 * 60 * 1000
  });

  const loading = projectsLoading || machinesLoading;

  // 处理不同API响应格式
  const projects = (() => {
    if (!projectsData) {return [];}
    if (Array.isArray(projectsData)) {return projectsData;}
    if (Array.isArray(projectsData.items)) {return projectsData.items;}
    if (Array.isArray(projectsData.data)) {return projectsData.data;}
    return [];
  })();

  const machines = (() => {
    if (!machinesData) {return [];}
    if (Array.isArray(machinesData)) {return machinesData;}
    if (Array.isArray(machinesData.items)) {return machinesData.items;}
    if (Array.isArray(machinesData.data)) {return machinesData.data;}
    return [];
  })();

  const stats = {
    totalProjects: projects.length,
    activeProjects: projects.filter((p) => p.health !== "H4").length,
    totalMachines: machines.length,
    atRiskProjects: projects.filter((p) => ["H2", "H3"].includes(p.health)).
    length
  };

  const recentProjects = projects.slice(0, 5);

  const statCards = [
  {
    icon: Briefcase,
    label: "总项目数",
    value: stats.totalProjects,
    change: "+12%",
    trend: "up"
  },
  {
    icon: BarChart3,
    label: "进行中项目",
    value: stats.activeProjects,
    change: "+3",
    trend: "up"
  },
  {
    icon: Box,
    label: "设备总数",
    value: stats.totalMachines,
    change: "+8%",
    trend: "up"
  },
  {
    icon: AlertTriangle,
    label: "风险项目",
    value: stats.atRiskProjects,
    change: "-2",
    trend: "down"
  }];


  return (
    <DashboardLayout
      title="仪表盘"
      description="项目全局概览与关键指标">

      {/* Stats Grid */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
        {statCards.map((stat, i) =>
        <DashboardStatCard
          key={i}
          {...stat}
          loading={loading} />

        )}
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
                  className="flex items-center gap-1 text-sm text-primary hover:text-primary-light transition-colors">

                  查看全部 <ArrowRight className="h-4 w-4" />
                </Link>
              </div>

              {loading ?
              <div className="p-5 space-y-4">
                  {Array(3).
                fill(null).
                map((_, i) =>
                <SkeletonCard key={i} />
                )}
              </div> :
              recentProjects.length > 0 ?
              // 使用虚拟滚动优化长列表性能
              recentProjects.length > 10 ?
              <VirtualizedProjectList
                projects={recentProjects}
                itemHeight={80} /> :


              <div className="divide-y divide-white/5">
                    {recentProjects.map((project) =>
                <Link
                  key={project.id}
                  to={`/projects/${project.id}`}
                  className="flex items-center gap-4 p-5 hover:bg-white/[0.02] transition-colors group">

                        {/* Icon */}
                        <div
                    className={cn(
                      "p-3 rounded-xl",
                      "bg-gradient-to-br from-primary/20 to-indigo-500/10",
                      "ring-1 ring-primary/20",
                      "group-hover:scale-105 transition-transform"
                    )}>

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
                )}
              </div> :


              <div className="p-12 text-center text-slate-500">
                  暂无项目数据
              </div>
              }
            </CardContent>
          </Card>
        </div>

        {/* Schedule Overview */}
        <div>
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
    </DashboardLayout>);

}