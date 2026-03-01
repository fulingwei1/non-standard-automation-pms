/**
 * 战略管理仪表板
 * BEM 战略解码主页面 - 展示战略健康度、BSC四维度、执行状态
 */
import { motion } from "framer-motion";
import {
  Target,
  RefreshCw,
  Settings,
  Calendar,
  BarChart3,
  Map,
  ChevronDown,
  TrendingUp,
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
} from "../../components/ui";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { useStrategyDashboard } from "./hooks/useStrategyDashboard";
import { HealthScoreCard } from "./components/HealthScoreCard";
import { DimensionCard } from "./components/DimensionCard";
import { QuickStatsPanel } from "./components/QuickStatsPanel";
import { ExecutionStatusPanel } from "./components/ExecutionStatusPanel";
import { MyStrategyPanel } from "./components/MyStrategyPanel";
import { MultiYearTrendChart } from "./components/MultiYearTrendChart";
import { BSC_DIMENSIONS, STRATEGY_STATUS } from "../../lib/constants/strategy";

export default function StrategyDashboard() {
  const {
    loading,
    refreshing,
    activeTab,
    setActiveTab,
    selectedStrategyId,
    activeStrategy,
    strategies,
    overview,
    healthStats,
    executionStats,
    myStrategy,
    quickStats,
    multiYearTrend,
    refresh,
    handleStrategyChange,
  } = useStrategyDashboard();

  // 渲染加载骨架屏
  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-full" />
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
          {[1, 2, 3, 4].map((i) => (
            <Skeleton key={i} className="h-40" />
          ))}
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const statusConfig = activeStrategy?.status
    ? STRATEGY_STATUS[activeStrategy.status]
    : null;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 页面头部 */}
      <PageHeader
        title="战略分析"
        description="BEM战略解码 | 战略健康度监控 | BSC四维度管理"
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            {/* 战略选择器 */}
            {strategies.length > 0 && (
              <Select
                value={selectedStrategyId?.toString()}
                onValueChange={(val) => handleStrategyChange(parseInt(val))}
              >
                <SelectTrigger className="w-[200px] bg-slate-900/50 border-slate-700">
                  <SelectValue placeholder="选择战略" />
                </SelectTrigger>
                <SelectContent>
                  {(strategies || []).map((s) => (
                    <SelectItem key={s.id} value={s.id.toString()}>
                      {s.name} ({s.year})
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
            <Button
              variant="outline"
              className="flex items-center gap-2"
              onClick={refresh}
              disabled={refreshing}
            >
              <RefreshCw
                className={`w-4 h-4 ${refreshing ? "animate-spin" : ""}`}
              />
              刷新
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <Map className="w-4 h-4" />
              战略地图
            </Button>
            <Button className="flex items-center gap-2">
              <Settings className="w-4 h-4" />
              战略设置
            </Button>
          </motion.div>
        }
      />

      {/* 当前战略信息 */}
      {activeStrategy && (
        <motion.div variants={fadeIn}>
          <Card className="bg-gradient-to-r from-slate-800/50 to-primary/10 border-primary/30">
            <CardContent className="py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-4">
                  <div className="p-3 rounded-lg bg-primary/20">
                    <Target className="w-6 h-6 text-primary" />
                  </div>
                  <div>
                    <h2 className="text-xl font-bold text-white">
                      {activeStrategy.name}
                    </h2>
                    <p className="text-sm text-slate-400">
                      {activeStrategy.year}年度战略 | {activeStrategy.vision}
                    </p>
                  </div>
                </div>
                <div className="flex items-center gap-4">
                  {statusConfig && (
                    <Badge
                      variant="outline"
                      className={`${
                        activeStrategy.status === "ACTIVE"
                          ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                          : "bg-slate-500/20 text-slate-400 border-slate-500/30"
                      }`}
                    >
                      {statusConfig.label}
                    </Badge>
                  )}
                  <div className="text-right">
                    <p className="text-sm text-slate-400">战略周期</p>
                    <p className="text-sm text-white">
                      {activeStrategy.start_date} ~ {activeStrategy.end_date}
                    </p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* 快速统计 */}
      {quickStats && (
        <motion.div variants={fadeIn}>
          <QuickStatsPanel stats={quickStats} />
        </motion.div>
      )}

      {/* 主内容区 - 标签页 */}
      <Tabs value={activeTab || "unknown"} onValueChange={setActiveTab} className="space-y-6">
        <TabsList className="bg-surface-50 border-white/10">
          <TabsTrigger value="overview">战略概览</TabsTrigger>
          <TabsTrigger value="dimensions">BSC维度</TabsTrigger>
          <TabsTrigger value="execution">执行追踪</TabsTrigger>
          <TabsTrigger value="my-strategy">我的战略</TabsTrigger>
          <TabsTrigger value="trends">趋势分析</TabsTrigger>
        </TabsList>

        {/* 战略概览标签页 */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 健康度评分卡 */}
            <div className="lg:col-span-1">
              <HealthScoreCard healthStats={healthStats} />
            </div>

            {/* 概览信息 */}
            <div className="lg:col-span-2">
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50 h-full">
                <CardHeader>
                  <CardTitle className="flex items-center gap-2 text-base">
                    <BarChart3 className="w-5 h-5 text-primary" />
                    战略概览
                  </CardTitle>
                </CardHeader>
                <CardContent>
                  {overview ? (
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                      <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50 text-center">
                        <p className="text-3xl font-bold text-white">
                          {overview.csf_count || 0}
                        </p>
                        <p className="text-sm text-slate-400 mt-1">关键成功因素</p>
                      </div>
                      <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50 text-center">
                        <p className="text-3xl font-bold text-white">
                          {overview.kpi_count || 0}
                        </p>
                        <p className="text-sm text-slate-400 mt-1">KPI指标</p>
                      </div>
                      <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50 text-center">
                        <p className="text-3xl font-bold text-white">
                          {overview.annual_work_count || 0}
                        </p>
                        <p className="text-sm text-slate-400 mt-1">重点工作</p>
                      </div>
                      <div className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50 text-center">
                        <p className="text-3xl font-bold text-emerald-400">
                          {overview.completion_rate?.toFixed(1) || 0}%
                        </p>
                        <p className="text-sm text-slate-400 mt-1">整体完成率</p>
                      </div>
                    </div>
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      暂无概览数据
                    </div>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>

          {/* BSC 四维度卡片 */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {Object.entries(BSC_DIMENSIONS).map(([key, config]) => {
              const dimensionData = healthStats?.dimensions?.find(
                (d) => d.dimension === key
              );
              return (
                <DimensionCard
                  key={key}
                  dimension={key}
                  config={config}
                  data={dimensionData}
                />
              );
            })}
          </div>
        </TabsContent>

        {/* BSC 维度详情标签页 */}
        <TabsContent value="dimensions" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {Object.entries(BSC_DIMENSIONS).map(([key, config]) => {
              const dimensionData = healthStats?.dimensions?.find(
                (d) => d.dimension === key
              );
              return (
                <Card
                  key={key}
                  className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50"
                >
                  <CardHeader>
                    <CardTitle className="flex items-center gap-2 text-base">
                      <config.icon
                        className="w-5 h-5"
                        style={{ color: config.color }}
                       />
                      {config.name}
                    </CardTitle>
                    <p className="text-sm text-slate-400">{config.description}</p>
                  </CardHeader>
                  <CardContent className="space-y-4">
                    {dimensionData ? (
                      <>
                        <div className="flex items-center justify-between">
                          <span className="text-slate-400">健康度评分</span>
                          <span
                            className="text-2xl font-bold"
                            style={{ color: config.color }}
                          >
                            {dimensionData.score?.toFixed(1) || 0}%
                          </span>
                        </div>
                        <div className="grid grid-cols-3 gap-4 text-center">
                          <div className="p-3 rounded-lg bg-slate-800/40">
                            <p className="text-lg font-semibold text-white">
                              {dimensionData.csfCount || 0}
                            </p>
                            <p className="text-xs text-slate-400">CSF</p>
                          </div>
                          <div className="p-3 rounded-lg bg-slate-800/40">
                            <p className="text-lg font-semibold text-white">
                              {dimensionData.kpiCount || 0}
                            </p>
                            <p className="text-xs text-slate-400">KPI</p>
                          </div>
                          <div className="p-3 rounded-lg bg-slate-800/40">
                            <p className="text-lg font-semibold text-emerald-400">
                              {dimensionData.kpiOnTrack || 0}
                            </p>
                            <p className="text-xs text-slate-400">达标</p>
                          </div>
                        </div>
                        <div className="flex items-center gap-2 text-sm">
                          <span className="px-2 py-1 rounded bg-emerald-500/20 text-emerald-400">
                            达标 {dimensionData.kpiOnTrack || 0}
                          </span>
                          <span className="px-2 py-1 rounded bg-amber-500/20 text-amber-400">
                            预警 {dimensionData.kpiAtRisk || 0}
                          </span>
                          <span className="px-2 py-1 rounded bg-red-500/20 text-red-400">
                            落后 {dimensionData.kpiOffTrack || 0}
                          </span>
                        </div>
                      </>
                    ) : (
                      <div className="text-center py-4 text-slate-500">
                        暂无数据
                      </div>
                    )}
                  </CardContent>
                </Card>
              );
            })}
          </div>
        </TabsContent>

        {/* 执行追踪标签页 */}
        <TabsContent value="execution" className="space-y-6">
          <ExecutionStatusPanel executionStats={executionStats} />
        </TabsContent>

        {/* 我的战略标签页 */}
        <TabsContent value="my-strategy" className="space-y-6">
          <MyStrategyPanel myStrategy={myStrategy} />
        </TabsContent>

        {/* 趋势分析标签页 */}
        <TabsContent value="trends" className="space-y-6">
          <MultiYearTrendChart trendData={multiYearTrend} />
        </TabsContent>
      </Tabs>
    </motion.div>
  );
}
