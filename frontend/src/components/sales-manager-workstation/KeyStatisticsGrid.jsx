import { motion } from "framer-motion";
import {
  DollarSign,
  Target,
  Users,
  Building2,
  CreditCard,
  AlertTriangle
} from "lucide-react";
import { staggerContainer } from "../../lib/animations";
import { formatCurrency } from "../../lib/utils";
import { StatCard } from "./StatCard";

export function KeyStatisticsGrid({ deptStats }) {
  if (!deptStats) return null;

  return (
    <motion.div
      variants={staggerContainer}
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
    >
      <StatCard
        title="本月签约"
        value={formatCurrency(deptStats.monthlyAchieved || 0)}
        subtitle={`目标: ${formatCurrency(deptStats.monthlyTarget || 0)}`}
        trend={12.5}
        icon={DollarSign}
        color="text-amber-400"
        bg="bg-amber-500/10"
      />

      <StatCard
        title="完成率"
        value={`${deptStats.achievementRate || 0}%`}
        subtitle="本月目标达成"
        icon={Target}
        color="text-emerald-400"
        bg="bg-emerald-500/10"
      />

      <StatCard
        title="团队规模"
        value={deptStats?.teamSize || 0}
        subtitle={`活跃成员 ${deptStats?.teamSize || 0}`}
        icon={Users}
        color="text-blue-400"
        bg="bg-blue-500/10"
      />

      <StatCard
        title="活跃客户"
        value={deptStats?.totalCustomers || 0}
        subtitle={`本月新增 ${deptStats?.newCustomersThisMonth || 0}`}
        trend={6.2}
        icon={Building2}
        color="text-purple-400"
        bg="bg-purple-500/10"
      />

      <StatCard
        title="待回款"
        value={formatCurrency(deptStats?.pendingPayment || 0)}
        subtitle={`逾期 ${formatCurrency(deptStats?.overduePayment || 0)}`}
        icon={CreditCard}
        color="text-red-400"
        bg="bg-red-500/10"
      />

      <StatCard
        title="待审批"
        value={deptStats?.pendingApprovals || 0}
        subtitle="项待处理"
        icon={AlertTriangle}
        color="text-amber-400"
        bg="bg-amber-500/10"
      />
    </motion.div>
  );
}
