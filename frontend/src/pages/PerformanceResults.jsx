/**
 * Performance Results - 绩效结果查看
 * Features: 个人绩效详情、历史记录、各项指标得分、趋势分析
 */
import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import {
  Award,
  TrendingUp,
  TrendingDown,
  Calendar,
  User,
  Building2,
  Target,
  BarChart3,
  Download,
  Eye,
  MessageSquare,
  ChevronRight,
  CheckCircle,
  AlertCircle,
  Loader2 } from
"lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../components/ui/tabs";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { performanceApi } from "../services/api";

// Mock data
// Mock data - 已移除，使用真实API
// Mock data - 已移除，使用真实API
const getLevelColor = (level) => {
  const colors = {
    EXCELLENT: "emerald",
    GOOD: "blue",
    QUALIFIED: "amber",
    NEEDS_IMPROVEMENT: "red"
  };
  return colors[level] || "slate";
};

const getScoreColor = (actual, target) => {
  const ratio = actual / target;
  if (ratio >= 1.0) return "text-emerald-400";
  if (ratio >= 0.9) return "text-blue-400";
  if (ratio >= 0.8) return "text-amber-400";
  return "text-red-400";
};

// 空的默认结果数据
const emptyCurrentResult = {
  period: "",
  level: "B",
  totalScore: 0,
  indicators: [],
  feedback: ""
};

export default function PerformanceResults() {
  const [_selectedPeriod, _setSelectedPeriod] = useState("current");
  const [loading, setLoading] = useState(true);
  const [_error, setError] = useState(null);
  const [currentResult, setCurrentResult] = useState(emptyCurrentResult);
  const [historyResults, setHistoryResults] = useState([]);

  // Fetch performance results
  useEffect(() => {
    const fetchResults = async () => {
      setLoading(true);
      setError(null);
      try {
        const myPerfRes = await performanceApi.getMyPerformance();
        if (myPerfRes.data) {
          const perfData = myPerfRes.data;
          // Map API response to component data structure
          if (perfData.current_result) {
            setCurrentResult({
              ...emptyCurrentResult,
              ...perfData.current_result
            });
          }
          if (perfData.history?.length > 0) {
            setHistoryResults(perfData.history);
          }
        }
      } catch (err) {
        console.error("Failed to load performance results:", err);
        setError("加载绩效结果失败");
      } finally {
        setLoading(false);
      }
    };
    fetchResults();
  }, []);

  const levelColor = getLevelColor(currentResult.level);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      <PageHeader
        title="绩效结果查看"
        description="查看个人绩效详情和历史记录"
        actions={
        <div className="flex items-center gap-3">
            <Button variant="outline" className="flex items-center gap-2">
              <Download className="w-4 h-4" />
              导出报告
            </Button>
            <Button variant="outline" className="flex items-center gap-2">
              <MessageSquare className="w-4 h-4" />
              申诉
            </Button>
          </div>
        } />


      {/* Current Result Summary */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardContent className="pt-6">
            {loading ?
            <div className="flex items-center justify-center py-12">
                <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
              </div> :

            <div className="flex items-start justify-between gap-6">
                <div className="flex items-start gap-4">
                  <div
                  className={cn(
                    "w-16 h-16 rounded-full flex items-center justify-center text-2xl font-bold",
                    `bg-${levelColor}-500/20 text-${levelColor}-400 border-2 border-${levelColor}-500/50`
                  )}>

                    {currentResult.level === "EXCELLENT" ?
                  "A" :
                  currentResult.level === "GOOD" ?
                  "B" :
                  currentResult.level === "QUALIFIED" ?
                  "C" :
                  "D"}
                  </div>
                  <div>
                    <h2 className="text-2xl font-bold text-white mb-2">
                      {currentResult.periodName}绩效结果
                    </h2>
                    <div className="flex items-center gap-4 text-sm text-slate-400">
                      <div className="flex items-center gap-1">
                        <User className="w-4 h-4" />
                        <span>{currentResult.employeeName}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Building2 className="w-4 h-4" />
                        <span>{currentResult.department}</span>
                      </div>
                      <div className="flex items-center gap-1">
                        <Calendar className="w-4 h-4" />
                        <span>评价时间: {currentResult.evaluateDate}</span>
                      </div>
                    </div>
                  </div>
                </div>

                <div className="flex gap-6">
                  <div className="text-center">
                    <p className="text-sm text-slate-400 mb-1">综合得分</p>
                    <p
                    className={cn(
                      "text-4xl font-bold",
                      `text-${levelColor}-400`
                    )}>

                      {currentResult.totalScore}
                    </p>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-slate-400 mb-1">绩效等级</p>
                    <Badge
                    className={cn(
                      "text-base px-3 py-1",
                      `bg-${levelColor}-500/20 text-${levelColor}-400 border-${levelColor}-500/50`
                    )}>

                      {currentResult.levelName}
                    </Badge>
                  </div>
                  <div className="text-center">
                    <p className="text-sm text-slate-400 mb-1">排名</p>
                    <p className="text-2xl font-bold text-white">
                      {currentResult.rank}
                      <span className="text-sm text-slate-400">
                        /{currentResult.totalEmployees}
                      </span>
                    </p>
                    <p className="text-xs text-slate-500 mt-1">
                      超越 {currentResult.percentile}% 员工
                    </p>
                  </div>
                </div>
              </div>
            }
          </CardContent>
        </Card>
      </motion.div>

      {/* Tabs */}
      <Tabs defaultValue="indicators" className="w-full">
        <TabsList className="grid w-full max-w-lg grid-cols-3">
          <TabsTrigger value="indicators">
            <Target className="w-4 h-4 mr-2" />
            指标得分
          </TabsTrigger>
          <TabsTrigger value="history">
            <BarChart3 className="w-4 h-4 mr-2" />
            历史记录
          </TabsTrigger>
          <TabsTrigger value="comments">
            <MessageSquare className="w-4 h-4 mr-2" />
            评价反馈
          </TabsTrigger>
        </TabsList>

        {/* Indicators Tab */}
        <TabsContent value="indicators" className="space-y-4 mt-6">
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Target className="h-5 w-5 text-purple-400" />
                各项指标得分
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ?
              <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                </div> :

              <div className="space-y-4">
                  {currentResult.indicators.map((indicator, index) =>
                <motion.div
                  key={index}
                  variants={fadeIn}
                  className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">

                      <div className="flex items-start justify-between gap-4 mb-3">
                        <div className="flex-1">
                          <div className="flex items-center gap-3 mb-2">
                            <h4 className="font-semibold text-white">
                              {indicator.name}
                            </h4>
                            {indicator.trend === "up" &&
                        <TrendingUp className="w-4 h-4 text-emerald-400" />
                        }
                            {indicator.trend === "down" &&
                        <TrendingDown className="w-4 h-4 text-red-400" />
                        }
                          </div>
                          <div className="flex items-center gap-6 text-sm">
                            <div>
                              <span className="text-slate-400">目标值: </span>
                              <span className="text-white font-semibold">
                                {indicator.target}
                                {indicator.unit}
                              </span>
                            </div>
                            <div>
                              <span className="text-slate-400">实际值: </span>
                              <span
                            className={cn(
                              "font-semibold",
                              getScoreColor(
                                indicator.actual,
                                indicator.target
                              )
                            )}>

                                {indicator.actual}
                                {indicator.unit}
                              </span>
                            </div>
                            <div>
                              <span className="text-slate-400">完成率: </span>
                              <span
                            className={cn(
                              "font-semibold",
                              getScoreColor(
                                indicator.actual,
                                indicator.target
                              )
                            )}>

                                {(
                            indicator.actual / indicator.target *
                            100).
                            toFixed(1)}
                                %
                              </span>
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <p className="text-sm text-slate-400 mb-1">得分</p>
                          <p className="text-2xl font-bold text-white">
                            {indicator.score}
                            <span className="text-sm text-slate-400 ml-1">
                              /{indicator.weight}
                            </span>
                          </p>
                        </div>
                      </div>
                      <Progress
                    value={indicator.score / indicator.weight * 100}
                    className="h-2 bg-slate-700/50" />

                    </motion.div>
                )}
                </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* History Tab */}
        <TabsContent value="history" className="space-y-4 mt-6">
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <BarChart3 className="h-5 w-5 text-blue-400" />
                历史绩效记录
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ?
              <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                </div> :

              <div className="space-y-3">
                  {historyResults.map((result, index) =>
                <motion.div
                  key={index}
                  variants={fadeIn}
                  className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50 hover:border-slate-600/80 transition-all cursor-pointer">

                      <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                          <div
                        className={cn(
                          "w-12 h-12 rounded-lg flex items-center justify-center text-lg font-bold",
                          `bg-${getLevelColor(result.level)}-500/20 text-${getLevelColor(result.level)}-400 border border-${getLevelColor(result.level)}-500/50`
                        )}>

                            {result.level === "EXCELLENT" ?
                        "A" :
                        result.level === "GOOD" ?
                        "B" :
                        result.level === "QUALIFIED" ?
                        "C" :
                        "D"}
                          </div>
                          <div>
                            <h4 className="font-semibold text-white mb-1">
                              {result.periodName}
                            </h4>
                            <div className="flex items-center gap-3 text-sm text-slate-400">
                              <span>得分: {result.score}</span>
                              <span>•</span>
                              <span>等级: {result.levelName}</span>
                              <span>•</span>
                              <span>排名: {result.rank}</span>
                            </div>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          {result.change !== 0 &&
                      <div
                        className={cn(
                          "flex items-center gap-1 text-sm",
                          result.change > 0 ?
                          "text-emerald-400" :
                          "text-red-400"
                        )}>

                              {result.change > 0 ?
                        <TrendingUp className="w-4 h-4" /> :

                        <TrendingDown className="w-4 h-4" />
                        }
                              <span>{Math.abs(result.change)}</span>
                            </div>
                      }
                          <ChevronRight className="w-5 h-5 text-slate-400" />
                        </div>
                      </div>
                    </motion.div>
                )}
                </div>
              }
            </CardContent>
          </Card>
        </TabsContent>

        {/* Comments Tab */}
        <TabsContent value="comments" className="space-y-4 mt-6">
          <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <MessageSquare className="h-5 w-5 text-cyan-400" />
                评价与反馈
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ?
              <div className="flex items-center justify-center py-12">
                  <Loader2 className="h-8 w-8 animate-spin text-slate-400" />
                </div> :

              <div className="space-y-4">
                  {currentResult.comments.map((comment, index) =>
                <motion.div
                  key={index}
                  variants={fadeIn}
                  className="p-4 rounded-lg bg-slate-800/40 border border-slate-700/50">

                      <div className="flex items-start gap-3 mb-3">
                        <CheckCircle className="w-5 h-5 text-emerald-400 mt-0.5" />
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-2">
                            <span className="font-semibold text-white">
                              {comment.from}
                            </span>
                            <span className="text-xs text-slate-500">
                              {comment.date}
                            </span>
                          </div>
                          <p className="text-slate-300 leading-relaxed">
                            {comment.content}
                          </p>
                        </div>
                      </div>
                    </motion.div>
                )}
                </div>
              }
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </motion.div>);

}