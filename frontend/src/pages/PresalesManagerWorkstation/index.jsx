/**
 * 售前工作台
 * 核心功能：团队管理、方案审核、投标支持、团队绩效监控
 */
import { motion } from "framer-motion";
import { Users, BarChart3 } from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Button } from "../../components/ui/button";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { formatCurrencyCompact as formatCurrency } from "../../lib/formatters";
import { useDashboardData } from "./hooks/useDashboardData";
import StatsGrid from "./components/StatsGrid";
import TeamPerformanceCard from "./components/TeamPerformanceCard";
import OngoingSolutionsCard from "./components/OngoingSolutionsCard";
import PendingReviewsCard from "./components/PendingReviewsCard";
import BiddingProjectsCard from "./components/BiddingProjectsCard";
import MonthlyTargetCard from "./components/MonthlyTargetCard";

export default function PresalesManagerWorkstation() {
  const {
    loading,
    error,
    overallStats,
    teamPerformance,
    pendingReviews,
    ongoingSolutions,
    biddingProjects,
  } = useDashboardData();

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader title="售前工作台" description="加载中..." />
        <div className="text-center py-16 text-slate-400">加载中...</div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="space-y-6">
        <PageHeader title="售前工作台" description="加载失败" />
        <div className="text-center py-16 text-red-400">
          <div className="text-lg font-medium">加载失败</div>
          <div className="text-sm mt-2">{error}</div>
        </div>
      </div>
    );
  }

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6">

      {/* 页面头部 */}
      <PageHeader
        title="售前工作台"
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
      <StatsGrid overallStats={overallStats} />

      {/* 主内容区域 */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* 左侧 - 团队绩效和进行中方案 */}
        <div className="lg:col-span-2 space-y-6">
          <TeamPerformanceCard teamPerformance={teamPerformance} />
          <OngoingSolutionsCard ongoingSolutions={ongoingSolutions} />
        </div>

        {/* 右侧 - 待审核方案和投标项目 */}
        <div className="space-y-6">
          <PendingReviewsCard pendingReviews={pendingReviews} />
          <BiddingProjectsCard biddingProjects={biddingProjects} />
        </div>
      </div>

      {/* 月度目标进度 */}
      <MonthlyTargetCard overallStats={overallStats} />
    </motion.div>
  );
}
