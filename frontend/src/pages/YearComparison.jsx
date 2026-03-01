/**
 * 战略同比分析页面
 * 当年 vs 去年健康度对比、BSC 维度雷达图、KPI 完成率对比
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  TrendingUp,
  TrendingDown,
  Minus,
  Target,
  Award,
  Briefcase,
  Lightbulb,
  AlertTriangle,
  CheckCircle,
  RefreshCw,
} from "lucide-react";
import { PageHeader } from "@/components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  Skeleton,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui";
import { fadeIn, staggerContainer } from "@/lib/animations";
import { comparisonApi } from "@/services/api/strategy";

// BSC 维度配置
const BSC_DIMENSIONS = {
  financial: {
    name: "财务",
    color: "#22c55e",
    icon: TrendingUp,
  },
  customer: {
    name: "客户",
    color: "#3b82f6",
    icon: Target,
  },
  internal: {
    name: "内部流程",
    color: "#f59e0b",
    icon: Briefcase,
  },
  learning: {
    name: "学习成长",
    color: "#a855f7",
    icon: Award,
  },
};

export default function YearComparison() {
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [currentYear, setCurrentYear] = useState(new Date().getFullYear());
  const [previousYear, setPreviousYear] = useState(new Date().getFullYear() - 1);
  const [yoyReport, setYoyReport] = useState(null);
  const [kpiAchievement, setKpiAchievement] = useState(null);

  // 获取同比报告
  useEffect(() => {
    fetchComparisonData();
  }, [currentYear, previousYear]);

  const fetchComparisonData = async () => {
    setLoading(true);
    try {
      const [reportRes, kpiRes] = await Promise.all([
        comparisonApi.getYoYReport(currentYear, previousYear),
        comparisonApi.getKpiAchievement(currentYear, previousYear),
      ]);

      setYoyReport(reportRes.data);
      setKpiAchievement(kpiRes.data);
    } catch (error) {
      console.error("获取对比数据失败:", error);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    await fetchComparisonData();
    setRefreshing(false);
  };

  const getTrendIcon = (change) => {
    if (change > 0) return <TrendingUp className="w-4 h-4 text-emerald-400" />;
    if (change < 0) return <TrendingDown className="w-4 h-4 text-red-400" />;
    return <Minus className="w-4 h-4 text-slate-400" />;
  };

  const getTrendColor = (change) => {
    if (change > 0) return "text-emerald-400";
    if (change < 0) return "text-red-400";
    return "text-slate-400";
  };

  const getTrendBg = (change) => {
    if (change > 0) return "bg-emerald-500/20";
    if (change < 0) return "bg-red-500/20";
    return "bg-slate-500/20";
  };

  if (loading) {
    return (
      <div className="space-y-6">
        <Skeleton className="h-12 w-full" />
        <div className="grid grid-cols-2 gap-4">
          <Skeleton className="h-32" />
          <Skeleton className="h-32" />
        </div>
        <Skeleton className="h-64" />
      </div>
    );
  }

  const healthScore = yoyReport?.current_health_score || 0;
  const previousHealthScore = yoyReport?.previous_health_score || 0;
  const healthChange = healthScore - previousHealthScore;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* 页面头部 */}
      <PageHeader
        title="战略同比分析"
        description={`${previousYear}年 vs ${currentYear}年 战略执行对比分析`}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Select
              value={previousYear.toString()}
              onValueChange={(val) => setPreviousYear(parseInt(val))}
            >
              <SelectTrigger className="w-[120px] bg-slate-900/50 border-slate-700">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[2022, 2023, 2024, 2025].map((y) => (
                  <SelectItem key={y} value={y.toString()}>
                    {y}年
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <span className="flex items-center text-slate-400">→</span>
            <Select
              value={currentYear.toString()}
              onValueChange={(val) => setCurrentYear(parseInt(val))}
            >
              <SelectTrigger className="w-[120px] bg-slate-900/50 border-slate-700">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {[2023, 2024, 2025, 2026].map((y) => (
                  <SelectItem key={y} value={y.toString()}>
                    {y}年
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Button variant="outline" onClick={handleRefresh} disabled={refreshing}>
              <RefreshCw className={`w-4 h-4 mr-2 ${refreshing ? "animate-spin" : ""}`} />
              刷新
            </Button>
          </motion.div>
        }
      />

      {/* 健康度对比卡 */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="w-5 h-5 text-primary" />
              战略健康度对比
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="flex items-center justify-between">
              <div className="text-center">
                <p className="text-sm text-slate-400 mb-2">{previousYear}年</p>
                <p className="text-4xl font-bold text-white">
                  {previousHealthScore?.toFixed(1) || 0}
                </p>
                <p className="text-xs text-slate-500 mt-1">健康度评分</p>
              </div>
              <div className="flex flex-col items-center">
                <div className={`p-3 rounded-full ${getTrendBg(healthChange)}`}>
                  {getTrendIcon(healthChange)}
                </div>
                <p className={`text-lg font-bold mt-2 ${getTrendColor(healthChange)}`}>
                  {healthChange > 0 ? "+" : ""}{healthChange?.toFixed(1) || 0}
                </p>
                <p className="text-xs text-slate-500">变化</p>
              </div>
              <div className="text-center">
                <p className="text-sm text-slate-400 mb-2">{currentYear}年</p>
                <p className="text-4xl font-bold text-white">
                  {healthScore?.toFixed(1) || 0}
                </p>
                <p className="text-xs text-slate-500 mt-1">健康度评分</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Award className="w-5 h-5 text-amber-400" />
              关键指标对比
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 text-center">
              <div>
                <p className="text-2xl font-bold text-white">
                  {yoyReport?.csf_growth_rate?.toFixed(1) || 0}%
                </p>
                <p className="text-xs text-slate-400 mt-1">CSF 增长率</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {yoyReport?.kpi_growth_rate?.toFixed(1) || 0}%
                </p>
                <p className="text-xs text-slate-400 mt-1">KPI 增长率</p>
              </div>
              <div>
                <p className="text-2xl font-bold text-white">
                  {yoyReport?.completion_rate_change?.toFixed(1) || 0}%
                </p>
                <p className="text-xs text-slate-400 mt-1">完成率变化</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* BSC 四维度对比 */}
      <motion.div variants={staggerContainer}>
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Target className="w-5 h-5 text-primary" />
              BSC 四维度对比
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
              {Object.entries(BSC_DIMENSIONS).map(([key, config]) => {
                const Icon = config.icon;
                const currentDim = yoyReport?.current_dimensions?.find(
                  (d) => d.dimension === key
                );
                const previousDim = yoyReport?.previous_dimensions?.find(
                  (d) => d.dimension === key
                );
                const currentScore = currentDim?.score || 0;
                const previousScore = previousDim?.score || 0;
                const change = currentScore - previousScore;

                return (
                  <motion.div key={key} variants={fadeIn}>
                    <div className="p-4 rounded-lg bg-slate-800/50 border border-slate-700/50">
                      <div className="flex items-center gap-2 mb-3">
                        <div
                          className="p-2 rounded"
                          style={{ backgroundColor: `${config.color}20` }}
                        >
                          <Icon className="w-4 h-4" style={{ color: config.color }} />
                        </div>
                        <span className="font-medium text-white">{config.name}</span>
                      </div>

                      {/* 柱状对比 */}
                      <div className="space-y-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-400 w-10">{previousYear}</span>
                          <div className="flex-1 h-4 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className="h-full transition-all"
                              style={{
                                width: `${previousScore}%`,
                                backgroundColor: config.color,
                                opacity: 0.6,
                              }}
                            />
                          </div>
                          <span className="text-xs text-slate-400 w-10 text-right">
                            {previousScore.toFixed(0)}
                          </span>
                        </div>
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-slate-400 w-10">{currentYear}</span>
                          <div className="flex-1 h-4 bg-slate-700 rounded-full overflow-hidden">
                            <div
                              className="h-full transition-all"
                              style={{
                                width: `${currentScore}%`,
                                backgroundColor: config.color,
                              }}
                            />
                          </div>
                          <span className="text-xs text-white w-10 text-right font-medium">
                            {currentScore.toFixed(0)}
                          </span>
                        </div>
                      </div>

                      {/* 变化指示 */}
                      <div className="flex items-center justify-between mt-3 pt-3 border-t border-slate-700/50">
                        <span className="text-xs text-slate-500">变化</span>
                        <div className={`flex items-center gap-1 ${getTrendColor(change)}`}>
                          {getTrendIcon(change)}
                          <span className="text-sm font-medium">
                            {change > 0 ? "+" : ""}{change.toFixed(1)}
                          </span>
                        </div>
                      </div>
                    </div>
                  </motion.div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* KPI 完成率对比表 */}
      <motion.div variants={staggerContainer}>
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Award className="w-5 h-5 text-amber-400" />
              KPI 完成率对比
            </CardTitle>
          </CardHeader>
          <CardContent>
            <Table>
              <TableHeader>
                <TableRow className="border-slate-700/50">
                  <TableHead className="text-slate-400">KPI 名称</TableHead>
                  <TableHead className="text-slate-400 text-right">{previousYear}年</TableHead>
                  <TableHead className="text-slate-400 text-right">{currentYear}年</TableHead>
                  <TableHead className="text-slate-400 text-right">变化</TableHead>
                  <TableHead className="text-slate-400">状态</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {(kpiAchievement?.kpis || []).map((kpi) => {
                  const change = kpi.current_rate - kpi.previous_rate;

                  return (
                    <TableRow key={kpi.id} className="border-slate-700/50">
                      <TableCell className="font-medium text-white">{kpi.name}</TableCell>
                      <TableCell className="text-right text-slate-300">
                        {kpi.previous_rate?.toFixed(1)}%
                      </TableCell>
                      <TableCell className="text-right text-white font-medium">
                        {kpi.current_rate?.toFixed(1)}%
                      </TableCell>
                      <TableCell className={`text-right ${getTrendColor(change)}`}>
                        {change > 0 ? "+" : ""}{change?.toFixed(1)}%
                      </TableCell>
                      <TableCell>
                        <Badge
                          variant="outline"
                          className={
                            kpi.current_rate >= 100
                              ? "bg-emerald-500/20 text-emerald-400 border-emerald-500/30"
                              : kpi.current_rate >= 80
                              ? "bg-blue-500/20 text-blue-400 border-blue-500/30"
                              : kpi.current_rate >= 60
                              ? "bg-amber-500/20 text-amber-400 border-amber-500/30"
                              : "bg-red-500/20 text-red-400 border-red-500/30"
                          }
                        >
                          {kpi.current_rate >= 100
                            ? "超额完成"
                            : kpi.current_rate >= 80
                            ? "良好"
                            : kpi.current_rate >= 60
                            ? "达标"
                            : "待改进"}
                        </Badge>
                      </TableCell>
                    </TableRow>
                  );
                })}

                {(kpiAchievement?.kpis || []).length === 0 && (
                  <TableRow>
                    <TableCell colSpan={5} className="text-center py-8 text-slate-500">
                      暂无 KPI 对比数据
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </motion.div>

      {/* 重点工作完成率对比 */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Briefcase className="w-5 h-5 text-blue-400" />
              重点工作完成率
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <span className="text-slate-400">{previousYear}年</span>
                <div className="flex items-center gap-3">
                  <div className="w-48 h-3 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-amber-500 transition-all"
                      style={{ width: `${yoyReport?.previous_work_completion || 0}%` }}
                    />
                  </div>
                  <span className="text-white font-medium w-12 text-right">
                    {yoyReport?.previous_work_completion?.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-slate-400">{currentYear}年</span>
                <div className="flex items-center gap-3">
                  <div className="w-48 h-3 bg-slate-700 rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${yoyReport?.current_work_completion || 0}%` }}
                    />
                  </div>
                  <span className="text-white font-medium w-12 text-right">
                    {yoyReport?.current_work_completion?.toFixed(1)}%
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="bg-slate-800/40 border-slate-700/50">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Lightbulb className="w-5 h-5 text-purple-400" />
              关键发现
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {yoyReport?.key_findings?.length > 0 ? (
              yoyReport.key_findings.map((finding, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <div className="w-1.5 h-1.5 rounded-full bg-purple-400 mt-1.5" />
                  <span className="text-sm text-slate-300">{finding}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500">暂无关键发现</p>
            )}
          </CardContent>
        </Card>
      </motion.div>

      {/* 亮点与改进建议 */}
      <motion.div variants={staggerContainer} className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Card className="bg-gradient-to-br from-emerald-900/20 to-slate-900/50 border-emerald-500/20">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <CheckCircle className="w-5 h-5 text-emerald-400" />
              亮点与优势
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {yoyReport?.highlights?.length > 0 ? (
              yoyReport.highlights.map((highlight, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <CheckCircle className="w-4 h-4 text-emerald-400 mt-0.5" />
                  <span className="text-sm text-slate-300">{highlight}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500">暂无亮点记录</p>
            )}
          </CardContent>
        </Card>

        <Card className="bg-gradient-to-br from-amber-900/20 to-slate-900/50 border-amber-500/20">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-amber-400" />
              改进建议
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {yoyReport?.recommendations?.length > 0 ? (
              yoyReport.recommendations.map((rec, idx) => (
                <div key={idx} className="flex items-start gap-2">
                  <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5" />
                  <span className="text-sm text-slate-300">{rec}</span>
                </div>
              ))
            ) : (
              <p className="text-sm text-slate-500">暂无改进建议</p>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
