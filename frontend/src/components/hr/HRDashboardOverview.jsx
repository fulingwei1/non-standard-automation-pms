/**
 * HR仪表盘概览组件
 * 用途：展示HR核心统计数据和概览信息
 */
import { motion } from 'framer-motion';
import { Users, UserPlus, Award, Building2 } from 'lucide-react';
import { staggerContainer } from '../../lib/animations';
import StatCard from '../common/StatCard';

export const HRDashboardOverview = ({ statistics }) => {
  const stats = [
    {
      title: '在职员工',
      value: statistics?.totalEmployees || 0,
      subtitle: `本月新增 ${statistics?.newEmployees || 0} 人`,
      trend: statistics?.employeeTrend,
      icon: Users,
      color: 'text-blue-400',
      bg: 'bg-blue-500',
    },
    {
      title: '招聘中职位',
      value: statistics?.activeRecruitments || 0,
      subtitle: `本月完成 ${statistics?.completedRecruitments || 0} 个`,
      trend: statistics?.recruitmentTrend,
      icon: UserPlus,
      color: 'text-emerald-400',
      bg: 'bg-emerald-500',
    },
    {
      title: '绩效评审',
      value: `${statistics?.performanceCompletionRate || 0}%`,
      subtitle: `待评审 ${statistics?.pendingReviews || 0} 人`,
      trend: statistics?.performanceTrend,
      icon: Award,
      color: 'text-purple-400',
      bg: 'bg-purple-500',
    },
    {
      title: '部门数量',
      value: statistics?.totalDepartments || 0,
      subtitle: statistics?.departmentInfo || '正常运营',
      icon: Building2,
      color: 'text-amber-400',
      bg: 'bg-amber-500',
    },
  ];

  return (
    <motion.div
      variants={staggerContainer}
      initial="initial"
      animate="animate"
      className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4"
    >
      {stats.map((stat, index) => (
        <StatCard key={index} {...stat} />
      ))}
    </motion.div>
  );
};

export default HRDashboardOverview;
