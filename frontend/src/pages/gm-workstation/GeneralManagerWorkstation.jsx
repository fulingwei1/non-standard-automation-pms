import { motion } from "framer-motion";
import {
  DollarSign,
  TrendingUp,
  Briefcase,
  ClipboardCheck,
  CheckCircle2,
  Award,
  BarChart3
} from "lucide-react";
import { PageHeader } from "../../components/layout";
import { Card, CardContent, Button } from "../../components/ui";
import { fadeIn, staggerContainer } from "../../lib/animations";
import { ApiIntegrationError } from "../../components/ui";
import CultureWallCarousel from "../../components/culture/CultureWallCarousel";

import StatCard from "./StatCard";
import YearProgressCard from "./YearProgressCard";
import KeyMetricsCard from "./KeyMetricsCard";
import ProjectHealthCard from "./ProjectHealthCard";
import PendingApprovalsCard from "./PendingApprovalsCard";
import DepartmentStatusCard from "./DepartmentStatusCard";
import { formatCurrency } from "./formatCurrency";
import useGMDashboard from "./useGMDashboard";

export default function GeneralManagerWorkstation() {
  const {
    loading,
    error,
    businessStats,
    pendingApprovals,
    projectHealth,
    departmentStatus,
    keyMetrics,
    loadDashboard
  } = useGMDashboard();

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="总经理工作台"
        description={
          loading
            ? "加载中..."
            : businessStats
              ? `年度营收目标: ${formatCurrency(businessStats.yearTarget || 0)} | 已完成: ${formatCurrency(businessStats.yearRevenue || 0)} (${(businessStats.yearProgress || 0).toFixed(1)}%)`
              : "企业经营总览、战略决策支持"
        }
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              经营报表
            </Button>
            <Button className="flex items-center gap-2">
              <ClipboardCheck className="w-4 h-4" />
              审批中心
            </Button>
          </motion.div>
        }
      />

      <motion.div variants={fadeIn}>
        <CultureWallCarousel
          autoPlay
          interval={5000}
          showControls
          showIndicators
          height="400px"
          onItemClick={(item) => {
            if (item.category === "GOAL") {
              window.location.href = "/personal-goals";
            } else {
              window.location.href = `/culture-wall?item=${item.id}`;
            }
          }}
        />
      </motion.div>

      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
      >
        {loading ? (
          [1, 2, 3, 4, 5, 6].map((i) => (
            <Card key={i} className="bg-surface-1/50 animate-pulse">
              <CardContent className="p-5">
                <div className="h-20 bg-slate-700/50 rounded" />
              </CardContent>
            </Card>
          ))
        ) : error ? (
          <div className="col-span-6">
            <ApiIntegrationError
              error={error}
              apiEndpoint="/api/v1/dashboard/general-manager"
              onRetry={loadDashboard}
            />
          </div>
        ) : businessStats ? (
          <>
            <StatCard
              title="本月营收"
              value={formatCurrency(businessStats.monthlyRevenue || 0)}
              subtitle={`目标: ${formatCurrency(businessStats.monthlyTarget || 0)}`}
              trend={businessStats.revenueGrowth || 0}
              icon={DollarSign}
              color="text-amber-400"
              bg="bg-amber-500/10"
            />
            <StatCard
              title="净利润"
              value={formatCurrency(businessStats.profit || 0)}
              subtitle={`利润率: ${businessStats.profitMargin || 0}%`}
              trend={15.2}
              icon={TrendingUp}
              color="text-emerald-400"
              bg="bg-emerald-500/10"
            />
            <StatCard
              title="进行中项目"
              value={businessStats.activeProjects || 0}
              subtitle={`总计 ${businessStats.totalProjects || 0} 个`}
              trend={businessStats.projectGrowth || 0}
              icon={Briefcase}
              color="text-blue-400"
              bg="bg-blue-500/10"
            />
            <StatCard
              title="待审批事项"
              value={businessStats.pendingApproval || 0}
              subtitle="需要处理"
              icon={ClipboardCheck}
              color="text-red-400"
              bg="bg-red-500/10"
            />
            <StatCard
              title="按时交付率"
              value={`${businessStats.onTimeDeliveryRate || 0}%`}
              subtitle="项目交付"
              icon={CheckCircle2}
              color="text-emerald-400"
              bg="bg-emerald-500/10"
            />
            <StatCard
              title="质量合格率"
              value={`${businessStats.qualityPassRate || 0}%`}
              subtitle="质量指标"
              icon={Award}
              color="text-cyan-400"
              bg="bg-cyan-500/10"
            />
          </>
        ) : null}
      </motion.div>

      {businessStats ? (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          <div className="lg:col-span-2 space-y-6">
            <YearProgressCard businessStats={businessStats} />
            <KeyMetricsCard keyMetrics={keyMetrics} />
            <ProjectHealthCard projectHealth={projectHealth} />
          </div>
          <div className="space-y-6">
            <PendingApprovalsCard pendingApprovals={pendingApprovals} />
            <DepartmentStatusCard departmentStatus={departmentStatus} />
          </div>
        </div>
      ) : null}
    </motion.div>
  );
}
