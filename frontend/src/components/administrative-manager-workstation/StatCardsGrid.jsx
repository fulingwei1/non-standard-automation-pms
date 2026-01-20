import { motion } from "framer-motion";
import {
  ClipboardCheck,
  AlertTriangle,
  Calendar,
  Car,
  UserCheck,
  Building2
} from "lucide-react";
import { staggerContainer } from "../../lib/animations";
import StatCard from "./StatCard";
import { formatCurrency } from "./utils";

const StatCardsGrid = ({ stats }) => {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">

      <StatCard
        title="待审批事项"
        value={stats.pendingApprovals}
        subtitle={`紧急: ${stats.urgentApprovals} 项`}
        icon={ClipboardCheck}
        color="text-red-400"
        bg="bg-red-500/10"
        onClick={() => window.location.href = "/approval-center"} />

      <StatCard
        title="低库存物品"
        value={stats.officeSuppliesLowStock}
        subtitle="需要补货"
        icon={AlertTriangle}
        color="text-amber-400"
        bg="bg-amber-500/10" />

      <StatCard
        title="今日会议"
        value={stats.meetingsToday}
        subtitle={`本周: ${stats.meetingsThisWeek} 场`}
        icon={Calendar}
        color="text-blue-400"
        bg="bg-blue-500/10" />

      <StatCard
        title="在用车辆"
        value={stats.vehiclesInUse}
        subtitle={`总计: ${stats.totalVehicles} 辆`}
        icon={Car}
        color="text-cyan-400"
        bg="bg-cyan-500/10" />

      <StatCard
        title="员工出勤率"
        value={`${stats.attendanceRate}%`}
        subtitle="本月平均"
        icon={UserCheck}
        color="text-emerald-400"
        bg="bg-emerald-500/10" />

      <StatCard
        title="固定资产"
        value={stats.fixedAssetsTotal || 0}
        subtitle={`总值: ${formatCurrency(stats.fixedAssetsValue || 0)}`}
        icon={Building2}
        color="text-purple-400"
        bg="bg-purple-500/10" />

    </motion.div>
  );
};

export default StatCardsGrid;
