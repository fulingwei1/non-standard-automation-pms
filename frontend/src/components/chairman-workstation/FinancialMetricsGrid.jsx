import { motion } from "framer-motion";
import {
  DollarSign,
  TrendingUp,
  Briefcase,
  Building2,
  CreditCard,
  Receipt
} from "lucide-react";
import { staggerContainer } from "../../lib/animations";
import StatCard from "../common/StatCard";
import { formatCurrency } from "./utils";

export const FinancialMetricsGrid = ({ companyStats }) => {
  if (!companyStats) {return null;}

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6">

      <StatCard
        title="年度营收"
        value={formatCurrency(companyStats.totalRevenue || 0)}
        subtitle={`目标: ${formatCurrency(companyStats.yearTarget || 0)}`}
        trend={companyStats.revenueGrowth || 0}
        icon={DollarSign}
        color="text-amber-400"
        bg="bg-amber-500/10"
        size="large" />

      <StatCard
        title="净利润"
        value={formatCurrency(companyStats.profit || 0)}
        subtitle={`利润率: ${companyStats.profitMargin || 0}%`}
        trend={15.2}
        icon={TrendingUp}
        color="text-emerald-400"
        bg="bg-emerald-500/10" />

      <StatCard
        title="活跃项目"
        value={companyStats.activeProjects || 0}
        subtitle={`总计 ${companyStats.totalProjects || 0} 个`}
        trend={companyStats.projectGrowth || 0}
        icon={Briefcase}
        color="text-blue-400"
        bg="bg-blue-500/10" />

      <StatCard
        title="客户总数"
        value={companyStats.totalCustomers || 0}
        subtitle={`本月新增 ${companyStats.newCustomersThisMonth || 0}`}
        trend={companyStats.customerGrowth || 0}
        icon={Building2}
        color="text-purple-400"
        bg="bg-purple-500/10" />

      <StatCard
        title="应收账款"
        value={formatCurrency(companyStats.accountsReceivable || 0)}
        subtitle={`逾期 ${formatCurrency(companyStats.overdueReceivable || 0)}`}
        icon={CreditCard}
        color="text-red-400"
        bg="bg-red-500/10" />

      <StatCard
        title="回款率"
        value={`${companyStats.collectionRate || 0}%`}
        subtitle="回款完成率"
        icon={Receipt}
        color="text-cyan-400"
        bg="bg-cyan-500/10" />

    </motion.div>
  );
};

export default FinancialMetricsGrid;
