/**
 * Rating Chart Component
 * 评分图表组件 - 可视化展示客户满意度评分数据
 */

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  BarChart3,
  PieChart,
  TrendingUp,
  Calendar,
  Users,
  Star,
  StarHalf,
  StarOff,
  ArrowUpRight,
  ArrowDownRight,
  Minus,
  RefreshCw } from
"lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger } from
"../../components/ui/tooltip";
import { cn } from "../../lib/utils";
import { Progress } from "../ui";
import {
  getSatisfactionScoreConfig,
  getSatisfactionColor as _getSatisfactionColor,
  satisfactionConstants
} from "@/lib/constants/customer";

// 模拟图表数据 - 实际项目中应该来自 props
const generateChartData = () => {
  return {
    ratings: [5, 4, 3, 2, 1].map((rating) => ({
      rating,
      count: Math.floor(Math.random() * 50) + 10,
      percentage: 0
    })),
    monthly: [
    { month: "1月", score: 4.2 },
    { month: "2月", score: 4.3 },
    { month: "3月", score: 4.1 },
    { month: "4月", score: 4.4 },
    { month: "5月", score: 4.5 },
    { month: "6月", score: 4.3 }],

    types: Object.keys(satisfactionConstants.feedbackTypeConfig).map((type) => ({
      type,
      averageScore: (Math.random() * 2 + 3).toFixed(1),
      count: Math.floor(Math.random() * 30) + 10
    })),
    departments: [
    { department: "研发部", score: 4.5, count: 45 },
    { department: "销售部", score: 4.2, count: 38 },
    { department: "客服部", score: 4.0, count: 52 },
    { department: "生产部", score: 4.3, count: 29 }]

  };
};

export const RatingChart = ({
  chartType: initialChartType = "trend",
  timeRange = "6month",
  className = "",
  loading = false,
  onTypeChange = null,
  data: _data = null
}) => {
  const [chartType, setChartType] = useState(initialChartType);
  const [selectedTimeRange, setSelectedTimeRange] = useState(timeRange);
  const [chartData, setChartData] = useState(generateChartData());

  // 计算评分分布百分比
  const ratingsWithPercentage = useMemo(() => {
    const total = (chartData.ratings || []).reduce((sum, item) => sum + item.count, 0);
    return (chartData.ratings || []).map((item) => ({
      ...item,
      percentage: (item.count / total * 100).toFixed(1)
    }));
  }, [chartData.ratings]);

  // 获取当前图表数据
  const getCurrentChartData = () => {
    switch (chartType) {
      case "trend":
        return chartData.monthly;
      case "distribution":
        return ratingsWithPercentage;
      case "type_analysis":
        return chartData.types;
      case "department":
        return chartData.departments;
      default:
        return [];
    }
  };

  // 渲染趋势图
  const renderTrendChart = () => {
    const data = getCurrentChartData();
    const maxScore = Math.max(...(data || []).map((item) => item.score));
    const minScore = Math.min(...(data || []).map((item) => item.score));

    return (
      <div className="space-y-4">
        {(data || []).map((item, index) => {
          const trend = index > 0 ? item.score - data[index - 1].score : 0;
          const config = getSatisfactionScoreConfig(item.score);

          return (
            <motion.div
              key={item.month}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-4">

              <div className="w-16 text-sm text-slate-600">
                {item.month}
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <div
                    className="h-4 rounded-full bg-gradient-to-r from-slate-200 to-slate-300 relative overflow-hidden"
                    style={{ width: "100%" }}>

                    <motion.div
                      className="h-full rounded-full"
                      style={{
                        width: `${(item.score - minScore) / (maxScore - minScore || 1) * 100}%`,
                        background: `linear-gradient(90deg, ${config.progress.replace("bg-", "from-")} ${config.progress.replace("bg-", "to-")})`
                      }} />

                  </div>
                  <span className="ml-3 text-sm font-medium text-slate-800 w-12">
                    {item.score}分
                  </span>
                </div>
                <div className="flex items-center gap-1">
                  <div className="flex">
                    {[1, 2, 3, 4, 5].map((star) =>
                    <Star
                      key={star}
                      className={cn(
                        "w-3 h-3",
                        star <= Math.floor(item.score) ?
                        "text-yellow-400 fill-current" :
                        star <= item.score ?
                        "text-yellow-400 fill-current opacity-50" :
                        "text-slate-300"
                      )} />

                    )}
                  </div>
                  {trend !== 0 &&
                  <motion.span
                    initial={{ scale: 0 }}
                    animate={{ scale: 1 }}
                    className={cn(
                      "text-xs font-medium",
                      trend > 0 ? "text-emerald-500" : "text-red-500"
                    )}>

                      {trend > 0 ? <ArrowUpRight className="w-3 h-3" /> : <ArrowDownRight className="w-3 h-3" />}
                      {Math.abs(trend).toFixed(1)}
                  </motion.span>
                  }
                </div>
              </div>
            </motion.div>);

        })}
      </div>);

  };

  // 渲染分布图
  const renderDistributionChart = () => {
    const data = getCurrentChartData();
    const maxCount = Math.max(...(data || []).map((item) => item.count));

    return (
      <div className="space-y-4">
        {(data || []).map((item, index) => {
          const config = getSatisfactionScoreConfig(item.rating);

          return (
            <motion.div
              key={item.rating}
              initial={{ opacity: 0, x: -20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: index * 0.1 }}
              className="flex items-center gap-4">

              <div className="flex items-center gap-2 w-20">
                <div className="flex">
                  {[1, 2, 3, 4, 5].map((star) =>
                  <Star
                    key={star}
                    className={cn(
                      "w-4 h-4",
                      star <= item.rating ?
                      config.color.replace("text-", "text-").replace("/400", "/500") :
                      "text-slate-300"
                    )} />

                  )}
                </div>
                <span className="text-sm text-slate-600">
                  {item.rating}分
                </span>
              </div>
              <div className="flex-1">
                <div className="flex items-center justify-between mb-1">
                  <div
                    className="h-6 rounded-lg bg-gradient-to-r from-slate-200 to-slate-300 relative overflow-hidden"
                    style={{ width: "100%" }}>

                    <motion.div
                      className="h-full rounded-lg flex items-center justify-end pr-2"
                      style={{
                        width: `${item.count / maxCount * 100}%`,
                        background: `linear-gradient(90deg, ${config.progress.replace("bg-", "from-")} ${config.progress.replace("bg-", "to-")})`
                      }}>

                      <span className="text-xs font-medium text-white">
                        {item.count}
                      </span>
                    </motion.div>
                  </div>
                </div>
                <div className="flex items-center justify-between">
                  <Progress value={parseFloat(item.percentage)} className="h-2 flex-1" />
                  <span className="text-sm text-slate-600 w-16 text-right">
                    {item.percentage}%
                  </span>
                </div>
              </div>
            </motion.div>);

        })}
      </div>);

  };

  // 渲染类型/部门分析图
  const renderAnalysisChart = () => {
    const data = getCurrentChartData();
    const _maxScore = Math.max(...(data || []).map((item) => parseFloat(item.averageScore || item.score)));

    return (
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {(data || []).map((item, index) => {
          const config = getSatisfactionScoreConfig(parseFloat(item.averageScore || item.score));
          const percentage = ((parseFloat(item.averageScore || item.score) - 1) / 4 * 100).toFixed(0);

          return (
            <motion.div
              key={item.type || item.department}
              initial={{ opacity: 0, scale: 0.9 }}
              animate={{ opacity: 1, scale: 1 }}
              transition={{ delay: index * 0.1 }}
              className="p-4 bg-slate-50 rounded-lg border border-slate-200">

              <div className="flex items-center justify-between mb-3">
                <h4 className="font-medium text-slate-800">
                  {item.type || item.department}
                </h4>
                <Badge
                  variant="outline"
                  className={cn("text-sm", config.color)}>

                  {parseFloat(item.averageScore || item.score).toFixed(1)}分
                </Badge>
              </div>
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <Progress value={percentage || "unknown"} className="h-3" />
                </div>
                <div className="text-sm text-slate-600 w-16 text-right">
                  {item.count || 0}条
                </div>
              </div>
            </motion.div>);

        })}
      </div>);

  };

  // 渲染当前图表
  const renderChart = () => {
    switch (chartType) {
      case "trend":
        return renderTrendChart();
      case "distribution":
        return renderDistributionChart();
      case "type_analysis":
      case "department":
        return renderAnalysisChart();
      default:
        return null;
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      className={cn("w-full", className)}>

      <Card className="border-slate-200 bg-white/80 backdrop-blur-sm">
        <CardHeader className="pb-4">
          <div className="flex items-center justify-between">
            <CardTitle className="text-lg font-semibold text-slate-800">
              评分分析图表
            </CardTitle>
            <div className="flex items-center gap-2">
              <Select value={selectedTimeRange || "unknown"} onValueChange={setSelectedTimeRange}>
                <SelectTrigger className="w-[120px]">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="1month">近1个月</SelectItem>
                  <SelectItem value="3month">近3个月</SelectItem>
                  <SelectItem value="6month">近6个月</SelectItem>
                  <SelectItem value="1year">近1年</SelectItem>
                </SelectContent>
              </Select>
              <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  setChartData(generateChartData());
                  if (onTypeChange) {onTypeChange();}
                }}
                disabled={loading}>

                <BarChart3 className="w-4 h-4" />
              </Button>
            </div>
          </div>

          {/* 图表类型选择 */}
          <div className="flex flex-wrap gap-2">
            {Object.entries(satisfactionConstants.CHART_TYPE_CONFIG).map(([key, config]) =>
            <Button
              key={key}
              variant={chartType === key ? "default" : "outline"}
              size="sm"
              onClick={() => setChartType(key)}
              className={cn(
                "h-8",
                chartType === key ?
                "bg-blue-500 text-white border-blue-500 hover:bg-blue-600" :
                "text-slate-600 border-slate-300 hover:bg-slate-50"
              )}>

                {config.label}
            </Button>
            )}
          </div>
        </CardHeader>

        <CardContent className="pt-0">
          <AnimatePresence mode="wait">
            {loading ?
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="h-64 flex items-center justify-center">

                <RefreshCw className="w-6 h-6 text-slate-400 animate-spin" />
            </motion.div> :

            <motion.div
              key={chartType}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              className="min-h-[300px]">

                {renderChart()}
            </motion.div>
            }
          </AnimatePresence>
        </CardContent>
      </Card>
    </motion.div>);

};
