/**
 * HR Statistics Overview Component
 * HR 统计概览组件
 */

import { motion } from "framer-motion";
import {
  Users,
  UserPlus,
  Award,
  CheckCircle2,
  Heart,
  Target,
  UserMinus,
  GraduationCap,
  Clock } from
"lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import StatCard from "../common/StatCard";
import { cn } from "../../lib/utils";

const STAT_CARD_PROPS = {
  valueColor: "text-white",
  layout: "compact",
  trendShowSign: false,
  trendLabel: "",
  showDecoration: false,
  hoverScale: 1.02,
  cardClassName: "bg-surface-50 border-white/10 hover:bg-surface-100 hover:border-white/20 bg-none hover:shadow-none p-6",
  iconWrapperClassName: "w-12 h-12 p-0 flex items-center justify-center",
  iconClassName: "w-6 h-6"
};

const StatCardSkeleton = () => (
  <Card className="bg-surface-50 border-white/10">
    <CardContent className="p-6">
      <div className="animate-pulse space-y-3">
        <div className="w-8 h-8 bg-slate-700 rounded" />
        <div className="h-6 bg-slate-700 rounded w-3/4" />
        <div className="h-4 bg-slate-700 rounded w-1/2" />
      </div>
    </CardContent>
  </Card>
);

// 快速统计行组件
const QuickStatsRow = ({ stats, loading }) => {
  const quickStats = [
  {
    title: "本月入职",
    value: loading ? "-" : stats?.monthlyNewHires || 0,
    icon: UserPlus,
    color: "text-green-400",
    bg: "bg-green-500/10",
    trend: stats?.monthlyNewHiresTrend
  },
  {
    title: "本月离职",
    value: loading ? "-" : stats?.monthlyResignations || 0,
    icon: UserMinus,
    color: "text-red-400",
    bg: "bg-red-500/10",
    trend: stats?.monthlyResignationsTrend
  },
  {
    title: "培训完成率",
    value: loading ? "-" : `${stats?.trainingCompletionRate || 0}%`,
    icon: GraduationCap,
    color: "text-purple-400",
    bg: "bg-purple-500/10",
    trend: stats?.trainingCompletionTrend
  },
  {
    title: "招聘周期",
    value: loading ? "-" : `${stats?.avgRecruitmentCycle || 0}天`,
    icon: Clock,
    color: "text-blue-400",
    bg: "bg-blue-500/10",
    trend: stats?.recruitmentCycleTrend
  }];


  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {(quickStats || []).map((stat, index) =>
      loading ? (
        <StatCardSkeleton key={index} />
      ) : (
        <StatCard
          key={index}
          title={stat.title}
          value={stat.value}
          icon={stat.icon}
          color={stat.color}
          bg={stat.bg}
          trend={stat.trend}
          {...STAT_CARD_PROPS}
        />
      ))}
    </div>);

};

// 部门分布组件
const DepartmentDistribution = ({ departments, loading }) => {
  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/3" />
            {[...Array(5)].map((_, i) =>
            <div key={i} className="flex items-center justify-between">
                <div className="h-3 bg-slate-700 rounded w-1/4" />
                <div className="h-3 bg-slate-700 rounded w-1/6" />
            </div>
            )}
          </div>
        </CardContent>
      </Card>);

  }

  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">部门分布</h3>
        <div className="space-y-3">
          {departments?.slice(0, 6).map((dept, index) =>
          <div key={index} className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <div className="w-2 h-2 bg-blue-400 rounded-full" />
                <span className="text-sm text-slate-300">{dept.name}</span>
              </div>
              <div className="flex items-center gap-3">
                <span className="text-sm font-medium text-white">{dept.count}人</span>
                <div className="w-16 bg-slate-700 rounded-full h-2">
                  <div
                  className="bg-blue-400 h-2 rounded-full"
                  style={{ width: `${dept.percentage}%` }} />
                </div>
              </div>
          </div>
          )}
        </div>
      </CardContent>
    </Card>);

};

// 待办事项组件
const PendingItems = ({ items, loading }) => {
  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/3" />
            {[...Array(3)].map((_, i) =>
            <div key={i} className="p-3 bg-slate-800 rounded">
                <div className="h-3 bg-slate-700 rounded w-3/4 mb-2" />
                <div className="h-3 bg-slate-700 rounded w-1/2" />
            </div>
            )}
          </div>
        </CardContent>
      </Card>);

  }

  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">待处理事项</h3>
        <div className="space-y-3">
          {items?.slice(0, 4).map((item, index) =>
          <div key={index} className="p-3 bg-slate-800/50 rounded-lg border border-slate-700">
              <div className="flex justify-between items-start">
                <div>
                  <div className="text-sm font-medium text-white">{item.title}</div>
                  <div className="text-xs text-slate-400 mt-1">{item.description}</div>
                </div>
                <span className={cn(
                "text-xs px-2 py-1 rounded-full",
                item.urgent ? "bg-red-500/20 text-red-400" : "bg-yellow-500/20 text-yellow-400"
              )}>
                  {item.urgent ? "紧急" : "普通"}
                </span>
              </div>
              <div className="text-xs text-slate-500 mt-2">
                {item.time} • {item.department}
              </div>
          </div>
          )}
        </div>
      </CardContent>
    </Card>);

};

export function HRStatsOverview({
  hrStats,
  loading = false,
  departments,
  pendingRecruitments,
  pendingPerformanceReviews
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6">

      {/* 关键统计指标 */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">
        {[{
          title: "在职员工",
          value: loading ? "-" : hrStats?.activeEmployees || 0,
          subtitle: `总计 ${hrStats?.totalEmployees || 0} 人`,
          trend: hrStats?.employeeTrend,
          icon: Users,
          color: "text-blue-400",
          bg: "bg-blue-500/10"
        },
        {
          title: "待审批招聘",
          value: loading ? "-" : hrStats?.pendingRecruitments || 0,
          subtitle: "需要处理",
          icon: UserPlus,
          color: "text-amber-400",
          bg: "bg-amber-500/10"
        },
        {
          title: "待绩效评审",
          value: loading ? "-" : hrStats?.pendingPerformanceReviews || 0,
          subtitle: "待完成",
          icon: Award,
          color: "text-purple-400",
          bg: "bg-purple-500/10"
        },
        {
          title: "今日出勤率",
          value: loading ? "-" : `${hrStats?.todayAttendanceRate || 0}%`,
          subtitle: "考勤统计",
          icon: CheckCircle2,
          color: "text-emerald-400",
          bg: "bg-emerald-500/10"
        },
        {
          title: "员工满意度",
          value: loading ? "-" : `${hrStats?.employeeSatisfaction || 0}%`,
          subtitle: "关系管理",
          icon: Heart,
          color: "text-pink-400",
          bg: "bg-pink-500/10"
        },
        {
          title: "平均绩效分",
          value: loading ? "-" : hrStats?.avgPerformanceScore || 0,
          subtitle: "绩效指标",
          icon: Target,
          color: "text-cyan-400",
          bg: "bg-cyan-500/10"
        }].map((stat, index) => (
          loading ? (
            <StatCardSkeleton key={index} />
          ) : (
            <StatCard
              key={index}
              title={stat.title}
              value={stat.value}
              subtitle={stat.subtitle}
              trend={stat.trend}
              icon={stat.icon}
              color={stat.color}
              bg={stat.bg}
              {...STAT_CARD_PROPS}
            />
          )
        ))}
      </div>

      {/* 快速统计 */}
      <QuickStatsRow stats={hrStats} loading={loading} />

      {/* 详细信息网格 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 部门分布 */}
        <div className="lg:col-span-1">
          <DepartmentDistribution departments={departments} loading={loading} />
        </div>

        {/* 待处理招聘 */}
        <div className="lg:col-span-1">
          <PendingItems
            items={pendingRecruitments?.map((recruit) => ({
              title: recruit.position,
              description: `招聘 ${recruit.department}`,
              urgent: recruit.priority === "HIGH",
              time: recruit.posted_time,
              department: recruit.department
            }))}
            loading={loading} />

        </div>

        {/* 待处理绩效评审 */}
        <div className="lg:col-span-1">
          <PendingItems
            items={pendingPerformanceReviews?.map((review) => ({
              title: review.employee_name,
              description: `${review.department} • 绩效评审`,
              urgent: review.overdue,
              time: review.due_date,
              department: review.department
            }))}
            loading={loading} />

        </div>
      </div>
    </motion.div>);

}
