/**
 * Finance Statistics Card Component
 * 财务统计卡片组件
 * 用于展示关键财务指标的卡片
 */

import { motion } from "framer-motion";
import {
  DollarSign,
  TrendingUp,
  TrendingDown,
  ArrowUpRight,
  ArrowDownRight,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Target
} from "lucide-react";
import { Card, CardContent } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { cn } from "../../lib/utils";
import {
  formatCurrency,
  formatPercentage,
  getHealthLevel,
  getBudgetStatus
} from "./financeDashboardConstants";

// 统计卡片组件
const StatCard = ({
  title,
  value,
  subtitle,
  trend,
  icon: Icon,
  color,
  bg,
  loading = false,
  target = null,
  targetProgress = null,
  showBadge = false,
  badgeText = "",
  badgeColor = ""
}) => {
  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="w-8 h-8 bg-slate-700 rounded"></div>
            <div className="h-6 bg-slate-700 rounded w-3/4"></div>
            <div className="h-4 bg-slate-700 rounded w-1/2"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      transition={{ type: "spring", stiffness: 300 }}
    >
      <Card className="bg-surface-50 border-white/10 hover:bg-surface-100 transition-colors">
        <CardContent className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className={cn("w-12 h-12 rounded-lg flex items-center justify-center", bg)}>
              <Icon className={cn("w-6 h-6", color)} />
            </div>
            {showBadge && (
              <Badge variant="outline" className={cn("text-xs", badgeColor)}>
                {badgeText}
              </Badge>
            )}
          </div>

          <div className="space-y-2">
            <div className="flex items-center justify-between">
              <div className="text-2xl font-bold text-white">{value}</div>
              {trend !== undefined && (
                <div className={cn(
                  "flex items-center gap-1 text-sm font-medium",
                  trend >= 0 ? "text-green-400" : "text-red-400"
                )}>
                  {trend >= 0 ? (
                    <ArrowUpRight className="w-4 h-4" />
                  ) : (
                    <ArrowDownRight className="w-4 h-4" />
                  )}
                  {Math.abs(trend)}%
                </div>
              )}
            </div>

            <div className="text-sm text-slate-400">{title}</div>
            {subtitle && (
              <div className="text-xs text-slate-500">{subtitle}</div>
            )}

            {target !== null && targetProgress !== null && (
              <div className="mt-3">
                <div className="flex items-center justify-between text-xs text-slate-500 mb-1">
                  <span>目标完成度</span>
                  <span>{formatPercentage(targetProgress)}</span>
                </div>
                <Progress
                  value={Math.min(targetProgress, 100)}
                  className="h-1.5"
                />
              </div>
            )}
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
};

// 指标状态指示器
const MetricStatusIndicator = ({ status, size = "sm" }) => {
  const getStatusConfig = (status) => {
    switch (status) {
      case "excellent":
        return { color: "text-green-400", bg: "bg-green-500/10", icon: CheckCircle2 };
      case "good":
        return { color: "text-emerald-400", bg: "bg-emerald-500/10", icon: CheckCircle2 };
      case "fair":
        return { color: "text-amber-400", bg: "bg-amber-500/10", icon: Clock };
      case "poor":
        return { color: "text-orange-400", bg: "bg-orange-500/10", icon: AlertTriangle };
      case "critical":
        return { color: "text-red-400", bg: "bg-red-500/10", icon: AlertTriangle };
      default:
        return { color: "text-slate-400", bg: "bg-slate-500/10", icon: Clock };
    }
  };

  const config = getStatusConfig(status);
  const Icon = config.icon;

  return (
    <div className={cn(
      "flex items-center gap-2",
      size === "sm" ? "text-xs" : "text-sm"
    )}>
      <div className={cn("p-1 rounded", config.bg)}>
        <Icon className={cn("w-3 h-3", config.color)} />
      </div>
      <span className={config.color}>
        {status === "excellent" && "优秀"}
        {status === "good" && "良好"}
        {status === "fair" && "一般"}
        {status === "poor" && "较差"}
        {status === "critical" && "危险"}
      </span>
    </div>
  );
};

// 关键指标行组件
const KeyMetricsRow = ({ metrics, loading }) => {
  const keyMetrics = [
    {
      title: "营业收入",
      value: loading ? "-" : formatCurrency(metrics?.totalRevenue || 0),
      trend: metrics?.revenueGrowth,
      icon: DollarSign,
      color: "text-green-400",
      bg: "bg-green-500/10",
      target: metrics?.revenueTarget,
      targetProgress: metrics?.revenueAchievement,
      status: metrics?.revenueStatus
    },
    {
      title: "净利润",
      value: loading ? "-" : formatCurrency(metrics?.totalProfit || 0),
      trend: metrics?.profitGrowth,
      icon: TrendingUp,
      color: "text-emerald-400",
      bg: "bg-emerald-500/10",
      target: metrics?.profitTarget,
      targetProgress: metrics?.profitAchievement,
      status: metrics?.profitStatus
    },
    {
      title: "毛利率",
      value: loading ? "-" : formatPercentage(metrics?.grossMargin || 0),
      trend: metrics?.marginGrowth,
      icon: Target,
      color: "text-blue-400",
      bg: "bg-blue-500/10",
      target: metrics?.marginTarget,
      targetProgress: metrics?.marginAchievement,
      status: metrics?.marginStatus
    },
    {
      title: "现金流",
      value: loading ? "-" : formatCurrency(metrics?.cashFlow || 0),
      trend: metrics?.cashFlowGrowth,
      icon: ArrowUpRight,
      color: "text-purple-400",
      bg: "bg-purple-500/10",
      target: metrics?.cashFlowTarget,
      targetProgress: metrics?.cashFlowAchievement,
      status: metrics?.cashFlowStatus
    }
  ];

  return (
    <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      {keyMetrics.map((metric, index) => (
        <StatCard
          key={index}
          title={metric.title}
          value={metric.value}
          trend={metric.trend}
          icon={metric.icon}
          color={metric.color}
          bg={metric.bg}
          target={metric.target}
          targetProgress={metric.targetProgress}
          showBadge={metric.status}
          badgeText={metric.status === "excellent" && "优秀"}
          badgeColor="border-green-400 text-green-400"
          loading={loading}
        />
      ))}
    </div>
  );
};

// 财务健康度卡片
const FinancialHealthCard = ({ healthScore, loading }) => {
  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/3"></div>
            <div className="h-8 bg-slate-700 rounded w-1/2"></div>
            <div className="h-4 bg-slate-700 rounded w-2/3"></div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const healthLevel = getHealthLevel(healthScore);

  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">财务健康度</h3>
        <div className="flex items-center justify-between mb-4">
          <div>
            <div className="text-3xl font-bold text-white mb-1">{healthScore}</div>
            <div className="text-sm text-slate-400">健康度评分</div>
          </div>
          <MetricStatusIndicator status={healthLevel.label.toLowerCase()} />
        </div>

        <div className="space-y-3">
          <div className="flex justify-between text-sm">
            <span className="text-slate-400">评分分布</span>
            <span className="text-slate-400">100分</span>
          </div>
          <Progress
            value={healthScore}
            className="h-2"
            style={{
              background: `linear-gradient(to right, #4ade80 0%, #4ade80 ${healthScore}%, rgba(71, 85, 105, 0.3) ${healthScore}%)`
            }}
          />
          <div className="flex justify-between text-xs text-slate-500">
            <span>0</span>
            <span>50</span>
            <span>100</span>
          </div>
        </div>

        <div className="mt-4 p-3 bg-slate-800/50 rounded-lg border border-slate-700">
          <div className="text-xs text-slate-400 mb-1">评估说明</div>
          <div className="text-sm text-slate-300">{healthLevel.description}</div>
        </div>
      </CardContent>
    </Card>
  );
};

// 预算执行卡片
const BudgetExecutionCard = ({ budgetData, loading }) => {
  if (loading) {
    return (
      <Card className="bg-surface-50 border-white/10">
        <CardContent className="p-6">
          <div className="animate-pulse space-y-3">
            <div className="h-4 bg-slate-700 rounded w-1/4"></div>
            <div className="space-y-2">
              {[...Array(3)].map((_, i) => (
                <div key={i} className="h-3 bg-slate-700 rounded w-full"></div>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>
    );
  }

  const overallStatus = getBudgetStatus(
    budgetData?.totalActual || 0,
    budgetData?.totalBudget || 0
  );

  return (
    <Card className="bg-surface-50 border-white/10">
      <CardContent className="p-6">
        <h3 className="text-lg font-semibold text-white mb-4">预算执行情况</h3>

        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <div>
              <div className="text-sm text-slate-400">总体进度</div>
              <div className="text-2xl font-bold text-white">
                {formatPercentage(budgetData?.overallProgress || 0)}
              </div>
            </div>
            <Badge variant="outline" className={cn(
              "px-3 py-1",
              overallStatus.borderColor.replace("border-", "text-")
            )}>
              {overallStatus.label}
            </Badge>
          </div>

          <div className="space-y-2">
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">预算总额</span>
              <span className="text-slate-300">{formatCurrency(budgetData?.totalBudget || 0)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">已执行</span>
              <span className="text-white">{formatCurrency(budgetData?.totalActual || 0)}</span>
            </div>
            <div className="flex justify-between text-sm">
              <span className="text-slate-400">剩余预算</span>
              <span className="text-emerald-400">
                {formatCurrency((budgetData?.totalBudget || 0) - (budgetData?.totalActual || 0))}
              </span>
            </div>
          </div>

          {budgetData?.departments?.slice(0, 3).map((dept, index) => {
            const deptStatus = getBudgetStatus(dept.actual, dept.budget);
            return (
              <div key={index} className="pt-3 border-t border-slate-700">
                <div className="flex items-center justify-between mb-2">
                  <span className="text-sm font-medium text-white">{dept.name}</span>
                  <Badge variant="outline" className={cn(
                    "text-xs",
                    deptStatus.borderColor.replace("border-", "text-")
                  )}>
                    {deptStatus.label}
                  </Badge>
                </div>
                <Progress
                  value={(dept.actual / dept.budget) * 100}
                  className="h-1.5"
                />
                <div className="flex justify-between text-xs text-slate-500 mt-1">
                  <span>{formatCurrency(dept.actual)}</span>
                  <span>{formatCurrency(dept.budget)}</span>
                </div>
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
};

export function FinanceStatsCard({
  financeData,
  loading = false
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="space-y-6"
    >
      {/* 关键财务指标 */}
      <KeyMetricsRow
        metrics={financeData?.overview}
        loading={loading}
      />

      {/* 详细信息网格 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 财务健康度 */}
        <div className="lg:col-span-1">
          <FinancialHealthCard
            healthScore={financeData?.overview?.healthScore || 0}
            loading={loading}
          />
        </div>

        {/* 预算执行情况 */}
        <div className="lg:col-span-2">
          <BudgetExecutionCard
            budgetData={financeData?.budget}
            loading={loading}
          />
        </div>
      </div>
    </motion.div>
  );
}

export default FinanceStatsCard;