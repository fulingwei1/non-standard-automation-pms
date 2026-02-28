/**
 * Performance Management - 绩效管理主页面
 * Features: 绩效概览、周期管理、待办事项、绩效统计
 */
import { useState, useEffect } from "react";
import { useNavigate } from "react-router-dom";
import { motion } from "framer-motion";
import {
  Award,
  TrendingUp,
  TrendingDown,
  Calendar,
  Users,
  Target,
  BarChart3,
  Clock,
  AlertCircle,
  CheckCircle2,
  Plus,
  Filter,
  Download,
  Eye,
  Edit,
  ArrowRight,
  Loader2 } from
"lucide-react";
import { PageHeader } from "../components/layout";
import StatCard from "../components/common/StatCard";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription } from
"../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../components/ui/select";
import { cn, formatDate } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { performanceApi, pmoApi } from "../services/api";

// Fallback mock data (used when API fails)
const getLevelColor = (level) => {
  const colors = {
    EXCELLENT: "text-emerald-400 bg-emerald-500/20 border-emerald-500/30",
    GOOD: "text-blue-400 bg-blue-500/20 border-blue-500/30",
    QUALIFIED: "text-amber-400 bg-amber-500/20 border-amber-500/30",
    NEEDS_IMPROVEMENT: "text-red-400 bg-red-500/20 border-red-500/30"
  };
  return colors[level] || colors.QUALIFIED;
};

const getLevelText = (level) => {
  const texts = {
    EXCELLENT: "优秀",
    GOOD: "良好",
    QUALIFIED: "合格",
    NEEDS_IMPROVEMENT: "待改进"
  };
  return texts[level] || level;
};

export default function PerformanceManagement() {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(true);
  const [_selectedPeriod, _setSelectedPeriod] = useState("current");

  // API data states with fallback to mock data
  const [currentPeriod, setCurrentPeriod] = useState({});
  const [stats, setStats] = useState({});
  const [pendingTasks, setPendingTasks] = useState([]);
  const [recentResults, setRecentResults] = useState([]);
  const [departmentPerformance, setDepartmentPerformance] = useState([]);

  // Fetch data from API
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true);
      try {
        // Fetch dashboard data (contains overview stats)
        const dashboardRes = await pmoApi.dashboard();
        if (dashboardRes.data) {
          // Extract performance stats if available
          const dashboard = dashboardRes.data;
          if (dashboard.performance_stats) {
            setStats((prev) => ({ ...prev, ...dashboard.performance_stats }));
          }
          if (dashboard.current_period) {
            setCurrentPeriod((prev) => ({
              ...prev,
              ...dashboard.current_period
            }));
          }
        }
      } catch (_err) {
        console.log("Dashboard API unavailable, using mock data");
      }

      try {
        // Fetch evaluation tasks for current user
        const tasksRes = await performanceApi.getEvaluationTasks({
          status: "PENDING"
        });
        if (tasksRes.data?.items?.length > 0) {
          const tasks = (tasksRes.data.items || []).map((task) => ({
            id: task.id,
            type: task.type || "evaluation",
            title: task.title || "评价下属绩效",
            count: task.count || 1,
            deadline: task.deadline,
            priority: task.priority || "medium"
          }));
          setPendingTasks(tasks);
        }
      } catch (_err) {
        console.log("Evaluation tasks API unavailable, using mock data");
      }

      try {
        // Fetch my performance for recent results
        const myPerfRes = await performanceApi.getMyPerformance();
        if (myPerfRes.data) {
          const perfData = myPerfRes.data;
          if (perfData.recent_results?.length > 0) {
            setRecentResults(perfData.recent_results);
          }
          if (perfData.department_ranking?.length > 0) {
            setDepartmentPerformance(perfData.department_ranking);
          }
        }
      } catch (_err) {
        console.log("My performance API unavailable, using mock data");
      }

      setLoading(false);
    };

    fetchData();
  }, []);

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* Page Header */}
      <PageHeader
        title="绩效管理"
        description="绩效考核、评价管理、统计分析"
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button
            variant="outline"
            className="flex items-center gap-2"
            onClick={() => navigate("/performance/indicators")}>

              <Target className="w-4 h-4" />
              指标配置
            </Button>
            <Button
            variant="outline"
            className="flex items-center gap-2"
            onClick={() => navigate("/performance/ranking")}>

              <Award className="w-4 h-4" />
              绩效排行
            </Button>
            <Button
            className="flex items-center gap-2"
            onClick={() => navigate("/performance/results")}>

              <BarChart3 className="w-4 h-4" />
              绩效结果
            </Button>
        </motion.div>
        } />


      {/* Current Period Card */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-violet-500/10 to-indigo-500/10 border-violet-500/30">
          <CardContent className="p-6">
            {loading ?
            <div className="flex items-center justify-center py-8">
                <Loader2 className="h-8 w-8 animate-spin text-violet-400" />
            </div> :

            <div className="flex items-start justify-between">
                <div className="flex-1">
                  <div className="flex items-center gap-3 mb-3">
                    <Calendar className="h-6 w-6 text-violet-400" />
                    <div>
                      <h3 className="text-xl font-bold text-white">
                        {currentPeriod.period_name}
                      </h3>
                      <p className="text-sm text-slate-400">
                        {formatDate(currentPeriod.start_date)} 至{" "}
                        {formatDate(currentPeriod.end_date)}
                      </p>
                    </div>
                  </div>
                  <div className="space-y-2">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-slate-400">考核进度</span>
                      <span className="text-white font-medium">
                        {currentPeriod.progress}%
                      </span>
                    </div>
                    <Progress
                    value={currentPeriod.progress}
                    className="h-2 bg-slate-700/50" />

                    <div className="flex items-center justify-between text-xs text-slate-500">
                      <span>剩余 {currentPeriod.days_remaining} 天</span>
                      <span>
                        已评价: {stats.evaluated} / {stats.total_employees}
                      </span>
                    </div>
                  </div>
                </div>
                <Badge className="bg-violet-500/20 text-violet-400 border-violet-500/30">
                  进行中
                </Badge>
            </div>
            }
          </CardContent>
        </Card>
      </motion.div>

      {/* Statistics */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-4">

        <StatCard
          title="平均分数"
          value={stats.avg_score}
          subtitle="全员平均绩效分数"
          icon={BarChart3}
          color="text-cyan-400"
          bg="bg-cyan-500/20"
          trend={2.3}
          trendLabel="vs 上期"
          size="large"
          showDecoration={false} />

        <StatCard
          title="优秀人数"
          value={stats.excellent}
          subtitle={`占比 ${(stats.excellent / stats.total_employees * 100).toFixed(1)}%`}
          icon={Award}
          color="text-emerald-400"
          bg="bg-emerald-500/20"
          trend={5}
          trendLabel="vs 上期"
          size="large"
          showDecoration={false} />

        <StatCard
          title="良好人数"
          value={stats.good}
          subtitle={`占比 ${(stats.good / stats.total_employees * 100).toFixed(1)}%`}
          icon={CheckCircle2}
          color="text-blue-400"
          bg="bg-blue-500/20"
          size="large"
          showDecoration={false} />

        <StatCard
          title="完成率"
          value={`${stats.completion_rate}%`}
          subtitle={`${stats.evaluated} / ${stats.total_employees} 人已评价`}
          icon={Target}
          color="text-purple-400"
          bg="bg-purple-500/20"
          size="large"
          showDecoration={false} />

      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Pending Tasks & Recent Results */}
        <div className="lg:col-span-2 space-y-6">
          {/* Pending Tasks */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Clock className="h-5 w-5 text-amber-400" />
                  待办事项
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {loading ?
                  <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
                  </div> :
                  pendingTasks.length === 0 ?
                  <div className="text-center py-8 text-slate-400">
                      暂无待办事项
                  </div> :

                  (pendingTasks || []).map((task) =>
                  <div
                    key={task.id}
                    className="flex items-center justify-between p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                    onClick={() => navigate("/performance/results")}>

                        <div className="flex items-center gap-3">
                          <div
                        className={cn(
                          "w-10 h-10 rounded-lg flex items-center justify-center",
                          task.priority === "high" && "bg-red-500/20",
                          task.priority === "medium" && "bg-amber-500/20"
                        )}>

                            <AlertCircle
                          className={cn(
                            "h-5 w-5",
                            task.priority === "high" && "text-red-400",
                            task.priority === "medium" && "text-amber-400"
                          )} />

                          </div>
                          <div>
                            <p className="font-medium text-white">
                              {task.title}
                            </p>
                            <p className="text-xs text-slate-400">
                              截止: {formatDate(task.deadline)}
                            </p>
                          </div>
                        </div>
                        <Badge variant="outline" className="bg-slate-700/40">
                          {task.count} 项
                        </Badge>
                  </div>
                  )
                  }
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Results */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="h-5 w-5 text-blue-400" />
                    最近绩效结果
                  </CardTitle>
                  <Button
                    variant="ghost"
                    size="sm"
                    className="text-xs text-primary"
                    onClick={() => navigate("/performance/results")}>

                    查看全部 <ArrowRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {loading ?
                  <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
                  </div> :
                  recentResults.length === 0 ?
                  <div className="text-center py-8 text-slate-400">
                      暂无绩效数据
                  </div> :

                  (recentResults || []).map((result) =>
                  <div
                    key={result.id}
                    className="flex items-center justify-between p-3 bg-slate-800/40 rounded-lg border border-slate-700/50">

                        <div className="flex items-center gap-3 flex-1">
                          <div className="flex flex-col">
                            <span className="font-medium text-white">
                              {result.employee_name}
                            </span>
                            <span className="text-xs text-slate-400">
                              {result.department}
                            </span>
                          </div>
                        </div>
                        <div className="flex items-center gap-3">
                          <div className="text-right">
                            <div className="text-lg font-bold text-white">
                              {result.score}
                            </div>
                            <div className="text-xs text-slate-400">
                              排名 #{result.rank}
                            </div>
                          </div>
                          <Badge
                        variant="outline"
                        className={getLevelColor(result.level)}>

                            {getLevelText(result.level)}
                          </Badge>
                          {result.trend === "up" &&
                      <TrendingUp className="w-4 h-4 text-emerald-400" />
                      }
                          {result.trend === "down" &&
                      <TrendingDown className="w-4 h-4 text-red-400" />
                      }
                        </div>
                  </div>
                  )
                  }
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Right Column - Department Performance */}
        <div className="space-y-6">
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <BarChart3 className="h-5 w-5 text-purple-400" />
                  部门绩效排行
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {loading ?
                  <div className="flex items-center justify-center py-8">
                      <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
                  </div> :
                  departmentPerformance.length === 0 ?
                  <div className="text-center py-8 text-slate-400">
                      暂无部门数据
                  </div> :

                  (departmentPerformance || []).map((dept, index) =>
                  <div
                    key={index}
                    className="flex items-center justify-between p-3 bg-slate-800/40 rounded-lg border border-slate-700/50">

                        <div className="flex items-center gap-3">
                          <div
                        className={cn(
                          "w-8 h-8 rounded-lg flex items-center justify-center font-bold",
                          index === 0 && "bg-amber-500/20 text-amber-400",
                          index === 1 && "bg-slate-500/20 text-slate-300",
                          index === 2 && "bg-orange-500/20 text-orange-400",
                          index > 2 && "bg-slate-700/40 text-slate-400"
                        )}>

                            {dept.rank}
                          </div>
                          <div>
                            <p className="font-medium text-white text-sm">
                              {dept.department}
                            </p>
                            <p className="text-xs text-slate-400">
                              平均: {dept.avg_score}
                            </p>
                          </div>
                        </div>
                        {dept.change !== 0 &&
                    <div className="flex items-center gap-1">
                            {dept.change > 0 ?
                      <>
                                <TrendingUp className="w-3 h-3 text-emerald-400" />
                                <span className="text-xs text-emerald-400">
                                  +{dept.change}
                                </span>
                      </> :

                      <>
                                <TrendingDown className="w-3 h-3 text-red-400" />
                                <span className="text-xs text-red-400">
                                  {dept.change}
                                </span>
                      </>
                      }
                    </div>
                    }
                  </div>
                  )
                  }
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Level Distribution */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Target className="h-5 w-5 text-cyan-400" />
                  绩效等级分布
                </CardTitle>
              </CardHeader>
              <CardContent>
                {loading ?
                <div className="flex items-center justify-center py-8">
                    <Loader2 className="h-6 w-6 animate-spin text-slate-400" />
                </div> :

                <div className="space-y-4">
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-emerald-400">优秀 (A)</span>
                        <span className="font-semibold text-white">
                          {stats.excellent} 人
                        </span>
                      </div>
                      <Progress
                      value={stats.excellent / stats.total_employees * 100}
                      className="h-2 bg-slate-700/50" />

                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-blue-400">良好 (B)</span>
                        <span className="font-semibold text-white">
                          {stats.good} 人
                        </span>
                      </div>
                      <Progress
                      value={stats.good / stats.total_employees * 100}
                      className="h-2 bg-slate-700/50" />

                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-amber-400">合格 (C)</span>
                        <span className="font-semibold text-white">
                          {stats.qualified} 人
                        </span>
                      </div>
                      <Progress
                      value={stats.qualified / stats.total_employees * 100}
                      className="h-2 bg-slate-700/50" />

                    </div>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-red-400">待改进 (D)</span>
                        <span className="font-semibold text-white">
                          {stats.needs_improvement} 人
                        </span>
                      </div>
                      <Progress
                      value={
                      stats.needs_improvement / stats.total_employees *
                      100
                      }
                      className="h-2 bg-slate-700/50" />

                    </div>
                </div>
                }
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </motion.div>);

}
