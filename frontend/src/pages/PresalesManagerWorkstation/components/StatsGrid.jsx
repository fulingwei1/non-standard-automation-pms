import {
  Users,
  FileText,
  Target,
  DollarSign,
  Award,
} from "lucide-react";
import { staggerContainer } from "../../../lib/animations";
import { formatCurrencyCompact as formatCurrency } from "../../../lib/formatters";

export default function StatsGrid({ overallStats }) {
  return (
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
  );
}
