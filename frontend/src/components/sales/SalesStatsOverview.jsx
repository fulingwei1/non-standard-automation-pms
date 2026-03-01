/**
 * Sales Statistics Overview Component
 * 销售统计概览组件 - 展示销售团队关键指标
 */

import { useState as _useState, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Users,
  Target,
  TrendingUp,
  DollarSign,
  Activity,
  Award,
  Clock,
  RefreshCw } from
"lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { Button } from "../../components/ui/button";
import { cn } from "../../lib/utils";
import {
  DEFAULT_SALES_TEAM_STATS,
  calculateSalesCompletionRate as _calculateSalesCompletionRate,
  getPerformanceLevel,
  getSalesPerformanceLevelConfig,
  formatCurrency,
  formatAutoRefreshTime } from
"@/lib/constants/sales";

export const SalesStatsOverview = ({
  teamStats = DEFAULT_SALES_TEAM_STATS,
  autoRefreshInterval = 0,
  lastAutoRefreshAt = null,
  highlightAutoRefresh = false,
  onRefresh = null,
  onAutoRefreshChange = null,
  loading = false,
  className = ""
}) => {
  // 计算完成率对应的绩效等级
  const performanceLevel = useMemo(() => {
    return getPerformanceLevel(teamStats.avgAchievementRate);
  }, [teamStats.avgAchievementRate]);

  const performanceConfig = getSalesPerformanceLevelConfig(performanceLevel);

  // 统计卡片配置
  const statsCards = [
  {
    title: "团队成员",
    value: teamStats.totalMembers,
    subtitle: `活跃 ${teamStats.activeMembers}`,
    icon: Users,
    color: "from-blue-500/10 to-cyan-500/5 border-blue-500/20",
    iconBg: "bg-blue-500/20",
    iconColor: "text-blue-400"
  },
  {
    title: "团队目标",
    value: formatCurrency(teamStats.totalTarget),
    subtitle: performanceConfig.label,
    icon: Target,
    color: "from-indigo-500/10 to-purple-500/5 border-indigo-500/20",
    iconBg: "bg-indigo-500/20",
    iconColor: "text-indigo-400"
  },
  {
    title: "团队完成",
    value: formatCurrency(teamStats.totalAchieved),
    subtitle: `${teamStats.avgAchievementRate}% 完成率`,
    icon: DollarSign,
    color: "from-emerald-500/10 to-green-500/5 border-emerald-500/20",
    iconBg: "bg-emerald-500/20",
    iconColor: "text-emerald-400"
  },
  {
    title: "进行中项目",
    value: teamStats.totalProjects,
    subtitle: "团队项目总数",
    icon: Activity,
    color: "from-purple-500/10 to-pink-500/5 border-purple-500/20",
    iconBg: "bg-purple-500/20",
    iconColor: "text-purple-400"
  },
  {
    title: "客户总数",
    value: teamStats.totalCustomers,
    subtitle: `本月新增 ${teamStats.newCustomersThisMonth}`,
    icon: Users,
    color: "from-amber-500/10 to-orange-500/5 border-amber-500/20",
    iconBg: "bg-amber-500/20",
    iconColor: "text-amber-400"
  },
  {
    title: "绩效等级",
    value: performanceConfig.label,
    subtitle: `${teamStats.avgAchievementRate}% 平均完成率`,
    icon: Award,
    color: "from-rose-500/10 to-pink-500/5 border-rose-500/20",
    iconBg: "bg-rose-500/20",
    iconColor: "text-rose-400"
  }];


  return (
    <div className={cn("space-y-4", className)}>
      {/* 自动刷新控制 */}
      {(onRefresh || onAutoRefreshChange) &&
      <motion.div
        initial={{ opacity: 0, y: -10 }}
        animate={{ opacity: 1, y: 0 }}
        className="flex items-center justify-between mb-4">

          <div className="flex items-center gap-3">
            {lastAutoRefreshAt &&
          <div className={cn(
            "flex items-center gap-2 text-xs px-3 py-1.5 rounded-lg transition-colors",
            highlightAutoRefresh ?
            "bg-emerald-500/20 text-emerald-400 border border-emerald-500/40" :
            "bg-slate-800/60 text-slate-400 border border-slate-700/40"
          )}>
                <Clock className="w-3 h-3" />
                <span>最后更新: {formatAutoRefreshTime(lastAutoRefreshAt)}</span>
          </div>
          }
          </div>

          <div className="flex items-center gap-3">
            {onAutoRefreshChange &&
          <select
            value={autoRefreshInterval || "unknown"}
            onChange={(e) => onAutoRefreshChange(Number(e.target.value))}
            className="px-3 py-1.5 bg-slate-800 border border-slate-700 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-blue-500">

                <option value={0 || "unknown"}>关闭自动刷新</option>
                <option value={30 || "unknown"}>30秒</option>
                <option value={60 || "unknown"}>1分钟</option>
                <option value={300 || "unknown"}>5分钟</option>
                <option value={600 || "unknown"}>10分钟</option>
                <option value={1800 || "unknown"}>30分钟</option>
          </select>
          }
            
            {onRefresh &&
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={loading}
            className="text-xs">

                <RefreshCw className={cn("w-3 h-3 mr-1", loading && "animate-spin")} />
                刷新
          </Button>
          }
          </div>
      </motion.div>
      }

      {/* 统计卡片网格 */}
      <motion.div
        variants={{
          hidden: { opacity: 0 },
          show: {
            opacity: 1,
            transition: {
              staggerChildren: 0.1
            }
          }
        }}
        initial="hidden"
        animate="show"
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6 gap-4">

        {(statsCards || []).map((card, index) => {
          const Icon = card.icon;
          return (
            <motion.div
              key={card.title}
              variants={{
                hidden: { opacity: 0, y: 20 },
                show: { opacity: 1, y: 0 }
              }}
              transition={{ delay: index * 0.05 }}>

              <Card className={cn(
                "border transition-all duration-200 hover:shadow-lg hover:-translate-y-1",
                card.color
              )}>
                <CardContent className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-sm text-slate-400">{card.title}</p>
                      <p className="text-xl font-bold text-white mt-1 line-clamp-1">
                        {card.value}
                      </p>
                      <div className="flex items-center gap-1 mt-1">
                        <div className="w-2 h-2 rounded-full bg-current opacity-60" />
                        <p className="text-xs text-slate-500">{card.subtitle}</p>
                      </div>
                    </div>
                    <div className={cn("p-2 rounded-lg", card.iconBg)}>
                      <Icon className={cn("w-5 h-5", card.iconColor)} />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>);

        })}
      </motion.div>

      {/* 团队完成率进度条 */}
      <motion.div
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: 0.3 }}>

        <Card className="bg-gradient-to-r from-slate-900/80 to-slate-800/80 border-slate-700/60">
          <CardContent className="p-4">
            <div className="flex items-center justify-between mb-3">
              <div className="flex items-center gap-3">
                <div className="flex items-center justify-center w-8 h-8 rounded-lg bg-blue-500/10 border border-blue-500/40">
                  <Target className="w-4 h-4 text-blue-400" />
                </div>
                <div>
                  <p className="text-sm font-medium text-white">团队完成进度</p>
                  <p className="text-xs text-slate-500">
                    目标 {formatCurrency(teamStats.totalTarget)} / 已完成 {formatCurrency(teamStats.totalAchieved)}
                  </p>
                </div>
              </div>
              <Badge
                variant="outline"
                className={cn(
                  "text-xs px-2 py-1",
                  performanceConfig.color.replace("text-", "border-").replace("bg-", "text-")
                )}>

                {teamStats.avgAchievementRate}%
              </Badge>
            </div>
            
            <div className="space-y-2">
              <Progress
                value={Math.min(teamStats.avgAchievementRate, 100)}
                className={cn(
                  "h-2 transition-all duration-500",
                  teamStats.avgAchievementRate >= 100 ? "opacity-100" : "opacity-80"
                )}
                style={{
                  background: `linear-gradient(to right, ${performanceConfig.progress.replace('bg-', '#')} 0%, ${performanceConfig.progress.replace('bg-', '#')} ${Math.min(teamStats.avgAchievementRate, 100)}%, rgba(71, 85, 105, 0.3) ${Math.min(teamStats.avgAchievementRate, 100)}%)`
                }} />

              
              {/* 里程碑标记 */}
              <div className="flex justify-between text-xs text-slate-500">
                <span>0%</span>
                <span>50%</span>
                <span>100%</span>
                <span>150%</span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </div>);

};

export default SalesStatsOverview;