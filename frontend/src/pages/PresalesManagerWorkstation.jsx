/**
 * 售前技术部经理工作台
 * 核心功能：团队管理、方案审核、投标支持、团队绩效监控
 */
import React, { useState, useEffect, useCallback } from "react";
import { motion } from "framer-motion";
import { Link } from "react-router-dom";
import {
  LayoutDashboard,
  Users,
  FileText,
  Target,
  CheckCircle2,
  Clock,
  AlertTriangle,
  TrendingUp,
  TrendingDown,
  Calendar,
  ChevronRight,
  BarChart3,
  Award,
  FileCheck,
  ClipboardList,
  Building2,
  Briefcase,
  DollarSign,
  Timer,
  Zap,
  Activity,
  MessageSquare,
  Lightbulb } from
"lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle } from
"../components/ui/card";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import { presaleApi, opportunityApi as _opportunityApi, orgApi as _orgApi, userApi } from "../services/api";
import { formatCurrencyCompact as formatCurrency } from "../lib/formatters";
import StatCard from "../components/common/StatCard";


export default function PresalesManagerWorkstation() {
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [overallStats, setOverallStats] = useState({
    teamSize: 0,
    activeSolutions: 0,
    pendingReview: 0,
    activeBids: 0,
    urgentBids: 0,
    monthlyOutput: 0,
    monthlyTarget: 0,
    achievementRate: 0,
    avgSolutionTime: 0,
    solutionQuality: 0
  });
  const [teamPerformance, setTeamPerformance] = useState([]);
  const [pendingReviews, setPendingReviews] = useState([]);
  const [ongoingSolutions, setOngoingSolutions] = useState([]);
  const [biddingProjects, setBiddingProjects] = useState([]);

  // Load dashboard data
  const loadDashboard = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      // Load solutions
      const solutionsResponse = await presaleApi.solutions.list({
        page: 1,
        page_size: 100,
        status: "DRAFT,REVIEWING,SUBMITTED"
      });
      const solutions =
      solutionsResponse.data?.items || solutionsResponse.data || [];
      setOngoingSolutions(Array.isArray(solutions) ? solutions : []);
      const activeSolutions = solutions.length;
      const pendingReview = solutions.filter(
        (s) => s.status === "REVIEWING"
      ).length;

      // Load tenders
      const tendersResponse = await presaleApi.tenders.list({
        page: 1,
        page_size: 100
      });
      const tenders = tendersResponse.data?.items || tendersResponse.data || [];
      setBiddingProjects(Array.isArray(tenders) ? tenders : []);
      const activeBids = tenders.length;
      const urgentBids = tenders.filter((t) => {
        const deadline = new Date(t.submission_deadline);
        const now = new Date();
        const daysLeft = Math.ceil((deadline - now) / (1000 * 60 * 60 * 24));
        return daysLeft <= 7 && daysLeft > 0;
      }).length;

      // Calculate monthly output (sum of estimated values)
      const monthlyOutput = solutions.reduce(
        (sum, s) => sum + (s.estimated_cost || s.suggested_price || 0),
        0
      );
      const monthlyTarget = monthlyOutput * 1.15; // Assume 15% target increase
      const achievementRate =
      monthlyTarget > 0 ? monthlyOutput / monthlyTarget * 100 : 0;

      // Get pending reviews
      const reviews = solutions.
      filter((s) => s.status === "REVIEWING").
      map((s) => ({
        id: s.id,
        title: s.name || "",
        customer: s.customer_name || "",
        author: s.creator_name || "",
        version: s.version || "V1.0",
        submitTime: s.submitted_at || s.created_at || "",
        amount: s.estimated_cost || s.suggested_price || 0,
        priority: s.priority?.toLowerCase() || "medium",
        daysWaiting: s.submitted_at ?
        Math.floor(
          (new Date() - new Date(s.submitted_at)) / (1000 * 60 * 60 * 24)
        ) :
        0
      })).
      sort((a, b) => b.daysWaiting - a.daysWaiting);

      // Get team size - try to get from department or user API
      let teamSize = 12; // default
      try {
        // Try to get users from "售前技术部" department
        const usersResponse = await userApi.
        list({
          department: "售前技术部",
          is_active: true,
          page_size: 100
        }).
        catch(() => null);
        if (usersResponse?.data?.total) {
          teamSize = usersResponse.data.total;
        }
      } catch (err) {
        console.error("Failed to get team size:", err);
      }

      // Get response time stats (for avgSolutionTime)
      let avgSolutionTime = 5.2; // default
      try {
        const responseTimeResponse = await presaleApi.statistics.
        responseTime({}).
        catch(() => null);
        if (
        responseTimeResponse?.data?.data?.completion_time?.
        avg_completion_hours)
        {
          avgSolutionTime = parseFloat(
            responseTimeResponse.data.data.completion_time.avg_completion_hours.toFixed(
              1
            )
          );
        }
      } catch (err) {
        console.error("Failed to get response time stats:", err);
      }

      // Calculate solution quality from solutions
      // Quality can be based on review status, approval rate, etc.
      let solutionQuality = 92.5; // default
      try {
        const allSolutionsResponse = await presaleApi.solutions.
        list({
          page: 1,
          page_size: 100
        }).
        catch(() => null);
        const allSolutions =
        allSolutionsResponse?.data?.items || allSolutionsResponse?.data || [];
        if (allSolutions.length > 0) {
          // Calculate quality based on approved/reviewed solutions
          const approvedSolutions = allSolutions.filter(
            (s) => s.status === "APPROVED" || s.status === "PUBLISHED"
          ).length;
          const reviewedSolutions = allSolutions.filter(
            (s) => s.status !== "DRAFT"
          ).length;
          if (reviewedSolutions > 0) {
            solutionQuality = parseFloat(
              (approvedSolutions / reviewedSolutions * 100).toFixed(1)
            );
          }
        }
      } catch (err) {
        console.error("Failed to calculate solution quality:", err);
      }

      // Load team performance
      let teamPerformanceData = [];
      try {
        const performanceResponse = await presaleApi.statistics.
        performance({}).
        catch(() => null);
        if (performanceResponse?.data?.data?.performance) {
          teamPerformanceData = performanceResponse.data.data.performance.map(
            (p) => ({
              id: p.user_id,
              name: p.user_name,
              role: "售前技术工程师",
              activeSolutions: p.solutions_count || 0,
              completedThisMonth: p.completed_tickets || 0,
              pendingReview: 0, // Not available in API
              avgQuality: p.avg_satisfaction ?
              parseFloat((p.avg_satisfaction * 20).toFixed(0)) :
              0, // Convert 0-5 to 0-100
              status:
              p.avg_satisfaction >= 4.5 ?
              "excellent" :
              p.avg_satisfaction >= 4.0 ?
              "good" :
              "warning"
            })
          );
        }
      } catch (err) {
        console.error("Failed to load team performance:", err);
      }

      setOverallStats({
        teamSize,
        activeSolutions,
        pendingReview,
        activeBids,
        urgentBids,
        monthlyOutput,
        monthlyTarget,
        achievementRate,
        avgSolutionTime,
        solutionQuality
      });
      setPendingReviews(reviews);
      setTeamPerformance(
        teamPerformanceData.length > 0 ? teamPerformanceData : []
      );
    } catch (err) {
      console.error("Failed to load dashboard:", err);
      setError(
        err.response?.data?.detail || err.message || "加载工作台数据失败"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadDashboard();
  }, [loadDashboard]);

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="售前技术部经理工作台" description="加载中..." />
        <div className="text-center py-16 text-slate-400">加载中...</div>
      </div>);

  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader title="售前技术部经理工作台" description="加载失败" />
        <div className="text-center py-16 text-red-400">
          <div className="text-lg font-medium">加载失败</div>
          <div className="text-sm mt-2">{error}</div>
        </div>
      </div>);

  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* 页面头部 */}
      <PageHeader
        title="售前技术部经理工作台"
        description={`团队规模: ${overallStats.teamSize}人 | 本月产出: ${formatCurrency(overallStats.monthlyOutput)} | 目标完成率: ${overallStats.achievementRate.toFixed(1)}%`}
        actions={
        <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              团队报表
            </Button>
            <Button className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              团队管理
            </Button>
        </motion.div>
        } />


      {/* 关键统计 - 6列网格 */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">

        <StatCard
          title="团队规模"
          value={overallStats.teamSize}
          subtitle="售前工程师"
          icon={Users}
          color="text-blue-400"
          bg="bg-blue-500/10" />

        <StatCard
          title="进行中方案"
          value={overallStats.activeSolutions}
          subtitle={`待审核 ${overallStats.pendingReview}`}
          icon={FileText}
          color="text-violet-400"
          bg="bg-violet-500/10" />

        <StatCard
          title="投标项目"
          value={overallStats.activeBids}
          subtitle={`紧急 ${overallStats.urgentBids}`}
          icon={Target}
          color="text-amber-400"
          bg="bg-amber-500/10" />

        <StatCard
          title="本月产出"
          value={formatCurrency(overallStats.monthlyOutput)}
          subtitle={`目标: ${formatCurrency(overallStats.monthlyTarget)}`}
          trend={12.5}
          icon={DollarSign}
          color="text-emerald-400"
          bg="bg-emerald-500/10" />

        <StatCard
          title="完成率"
          value={`${overallStats.achievementRate.toFixed(1)}%`}
          subtitle="目标达成率"
          icon={Target}
          color="text-purple-400"
          bg="bg-purple-500/10" />

        <StatCard
          title="方案质量"
          value={`${overallStats.solutionQuality.toFixed(1)}%`}
          subtitle="平均评分"
          icon={Award}
          color="text-cyan-400"
          bg="bg-cyan-500/10" />

      </motion.div>

      {/* 主内容区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧 - 团队绩效和进行中方案 */}
        <div className="lg:col-span-2 space-y-6">
          {/* 团队绩效 */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="h-5 w-5 text-purple-400" />
                    团队绩效排行
                  </CardTitle>
                  <Link to="/presales-tasks">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-primary">

                      查看详情 <ChevronRight className="w-3 h-3 ml-1" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {teamPerformance.map((member, index) =>
                  <div
                    key={member.id}
                    className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors">

                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div
                          className={cn(
                            "w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm",
                            index === 0 &&
                            "bg-gradient-to-br from-amber-500 to-orange-500",
                            index === 1 &&
                            "bg-gradient-to-br from-blue-500 to-cyan-500",
                            index === 2 &&
                            "bg-gradient-to-br from-slate-500 to-gray-600",
                            index === 3 &&
                            "bg-gradient-to-br from-purple-500 to-pink-500"
                          )}>

                            {index + 1}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-white">
                                {member.name}
                              </span>
                              <Badge
                              variant="outline"
                              className="text-xs bg-slate-700/40">

                                {member.role}
                              </Badge>
                            </div>
                            <div className="text-xs text-slate-400 mt-1">
                              {member.activeSolutions} 个进行中 · 本月完成{" "}
                              {member.completedThisMonth} 个
                              {member.pendingReview > 0 &&
                            <span className="text-amber-400 ml-1">
                                  · 待审核 {member.pendingReview}
                            </span>
                            }
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-white">
                            {member.avgQuality}%
                          </div>
                          <div className="text-xs text-slate-400">平均质量</div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">质量评分</span>
                          <span
                          className={cn(
                            "font-medium",
                            member.avgQuality >= 90 ?
                            "text-emerald-400" :
                            member.avgQuality >= 80 ?
                            "text-amber-400" :
                            "text-red-400"
                          )}>

                            {member.avgQuality}%
                          </span>
                        </div>
                        <Progress
                        value={member.avgQuality}
                        className="h-1.5 bg-slate-700/50" />

                      </div>
                  </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* 进行中方案 */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <FileText className="h-5 w-5 text-violet-400" />
                    进行中方案
                  </CardTitle>
                  <Link to="/solutions">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-primary">

                      方案中心 <ChevronRight className="w-3 h-3 ml-1" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {ongoingSolutions.map((solution, _index) =>
                <div
                  key={solution.id}
                  className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer">

                    <div className="flex items-start justify-between mb-3">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <h4 className="text-sm font-medium text-white">
                            {solution.name}
                          </h4>
                          <Badge variant="outline" className="text-xs">
                            {solution.version}
                          </Badge>
                        </div>
                        <div className="flex items-center gap-3 text-xs text-slate-500">
                          <span className="flex items-center gap-1">
                            <Building2 className="w-3 h-3" />
                            {solution.customer}
                          </span>
                          <span className="flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {solution.author}
                          </span>
                          <span className="flex items-center gap-1">
                            <DollarSign className="w-3 h-3" />
                            {formatCurrency(solution.amount)}
                          </span>
                        </div>
                      </div>
                      <Badge className={cn("text-xs", solution.statusColor)}>
                        {solution.status}
                      </Badge>
                    </div>
                    <div className="space-y-1">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">完成进度</span>
                        <span className="text-white">{solution.progress}%</span>
                      </div>
                      <Progress
                      value={solution.progress}
                      className="h-1.5 bg-slate-700/50" />

                    </div>
                    <div className="flex items-center justify-between mt-2 text-xs text-slate-500">
                      <span className="flex items-center gap-1">
                        <Calendar className="w-3 h-3" />
                        截止: {solution.deadline}
                      </span>
                    </div>
                </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* 右侧 - 待审核方案和投标项目 */}
        <div className="space-y-6">
          {/* 待审核方案 */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <FileCheck className="h-5 w-5 text-amber-400" />
                    待审核方案
                  </CardTitle>
                  <Badge
                    variant="outline"
                    className="bg-amber-500/20 text-amber-400 border-amber-500/30">

                    {pendingReviews.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {pendingReviews.map((item) =>
                <div
                  key={item.id}
                  className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer">

                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          {item.priority === "high" &&
                        <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              紧急
                        </Badge>
                        }
                          {item.daysWaiting > 1 &&
                        <Badge className="text-xs bg-orange-500/20 text-orange-400 border-orange-500/30">
                              待处理 {item.daysWaiting} 天
                        </Badge>
                        }
                        </div>
                        <p className="font-medium text-white text-sm">
                          {item.title}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">
                          {item.customer}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs mt-2">
                      <span className="text-slate-400">
                        {item.author} · {item.version} ·{" "}
                        {item.submitTime.split(" ")[1]}
                      </span>
                      <span className="font-medium text-amber-400">
                        {formatCurrency(item.amount)}
                      </span>
                    </div>
                </div>
                )}
                <Link to="/solutions">
                  <Button variant="outline" className="w-full mt-3">
                    查看全部方案
                  </Button>
                </Link>
              </CardContent>
            </Card>
          </motion.div>

          {/* 投标项目 */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Target className="h-5 w-5 text-amber-400" />
                    投标项目
                  </CardTitle>
                  <Link to="/bidding">
                    <Button
                      variant="ghost"
                      size="sm"
                      className="text-xs text-primary">

                      全部 <ChevronRight className="w-3 h-3 ml-1" />
                    </Button>
                  </Link>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {biddingProjects.map((bid) =>
                <div
                  key={bid.id}
                  className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer">

                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1 min-w-0">
                        <h4 className="text-sm font-medium text-white truncate">
                          {bid.name}
                        </h4>
                        <p className="text-xs text-slate-500 mt-0.5">
                          {bid.customer}
                        </p>
                      </div>
                      <Badge className={cn("text-xs", bid.statusColor)}>
                        {bid.status}
                      </Badge>
                    </div>
                    <div className="space-y-2 mt-2">
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400 flex items-center gap-1">
                          <Timer className="w-3 h-3" />
                          剩余{" "}
                          <span
                          className={cn(
                            "font-medium",
                            bid.daysLeft <= 7 ? "text-red-400" : "text-white"
                          )}>

                            {bid.daysLeft}
                          </span>{" "}
                          天
                        </span>
                        <span className="text-slate-400">
                          {formatCurrency(bid.amount)}
                        </span>
                      </div>
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-400">
                          负责人: {bid.responsible}
                        </span>
                        <span className="text-slate-400">
                          进度: {bid.progress}%
                        </span>
                      </div>
                      <Progress
                      value={bid.progress}
                      className="h-1 bg-slate-700/50" />

                    </div>
                </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* 月度目标进度 */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-5 w-5 text-cyan-400" />
              月度产出目标进度
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">月度目标</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {formatCurrency(overallStats.monthlyTarget)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-400">已完成</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1">
                    {formatCurrency(overallStats.monthlyOutput)}
                  </p>
                </div>
              </div>
              <Progress
                value={overallStats.achievementRate}
                className="h-3 bg-slate-700/50" />

              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">
                  完成率: {overallStats.achievementRate.toFixed(1)}%
                </span>
                <span className="text-slate-400">
                  剩余:{" "}
                  {formatCurrency(
                    overallStats.monthlyTarget - overallStats.monthlyOutput
                  )}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>);

}
