/**
 * Sales Director Workstation - Executive dashboard for sales directors
 * Features: Strategic overview, Team performance, Sales analytics, Revenue monitoring
 * Core Functions: Sales strategy, Team management, Performance monitoring, Contract approval
 */

import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Target,
  Briefcase,
  BarChart3,
  PieChart,
  Calendar,
  AlertTriangle,
  CheckCircle2,
  Clock,
  ArrowUpRight,
  ArrowDownRight,
  Building2,
  FileText,
  CreditCard,
  Receipt,
  Award,
  Activity,
  Zap,
  ChevronRight,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Badge,
  Progress,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Mock data for sales director dashboard
const mockOverallStats = {
  monthlyTarget: 5000000,
  monthlyAchieved: 3850000,
  achievementRate: 77,
  yearTarget: 60000000,
  yearAchieved: 42500000,
  yearProgress: 70.8,
  activeContracts: 28,
  pendingContracts: 5,
  totalCustomers: 156,
  newCustomersThisMonth: 12,
  teamSize: 18,
  activeOpportunities: 45,
  hotOpportunities: 18,
  totalRevenue: 42500000,
  pendingPayment: 2850000,
  overduePayment: 350000,
  collectionRate: 92.5,
}


const mockTeamPerformance = [
  {
    id: 1,
    name: '张销售',
    role: '销售工程师',
    monthlyTarget: 300000,
    monthlyAchieved: 285000,
    achievementRate: 95,
    activeProjects: 5,
    newCustomers: 2,
    status: 'excellent',
  },
  {
    id: 2,
    name: '李销售',
    role: '销售工程师',
    monthlyTarget: 300000,
    monthlyAchieved: 245000,
    achievementRate: 81.7,
    activeProjects: 4,
    newCustomers: 1,
    status: 'good',
  },
  {
    id: 3,
    name: '王销售',
    role: '销售工程师',
    monthlyTarget: 300000,
    monthlyAchieved: 198000,
    achievementRate: 66,
    activeProjects: 3,
    newCustomers: 0,
    status: 'warning',
  },
  {
    id: 4,
    name: '刘销售',
    role: '销售经理',
    monthlyTarget: 800000,
    monthlyAchieved: 720000,
    achievementRate: 90,
    activeProjects: 8,
    newCustomers: 3,
    status: 'excellent',
  },
]

const mockSalesFunnel = {
  inquiry: { count: 120, amount: 15000000, conversion: 100 },
  qualification: { count: 85, amount: 12000000, conversion: 70.8 },
  proposal: { count: 52, amount: 8500000, conversion: 61.2 },
  negotiation: { count: 28, amount: 5200000, conversion: 53.8 },
  closed: { count: 15, amount: 3850000, conversion: 53.6 },
}

const mockTopCustomers = [
  {
    id: 1,
    name: '深圳XX科技有限公司',
    totalAmount: 8500000,
    thisYear: 3200000,
    projectCount: 8,
    status: 'active',
    lastOrder: '2025-01-05',
  },
  {
    id: 2,
    name: '东莞XX电子有限公司',
    totalAmount: 6200000,
    thisYear: 1850000,
    projectCount: 6,
    status: 'active',
    lastOrder: '2024-12-20',
  },
  {
    id: 3,
    name: '广州XX汽车零部件',
    totalAmount: 5200000,
    thisYear: 2100000,
    projectCount: 5,
    status: 'active',
    lastOrder: '2025-01-08',
  },
  {
    id: 4,
    name: '惠州XX电池科技',
    totalAmount: 4500000,
    thisYear: 1200000,
    projectCount: 4,
    status: 'active',
    lastOrder: '2024-12-15',
  },
]

const mockPendingApprovals = [
  {
    id: 1,
    type: 'contract',
    title: 'BMS测试设备合同',
    customer: '深圳XX科技',
    amount: 850000,
    submitter: '张销售',
    submitTime: '2025-01-06 10:30',
    priority: 'high',
  },
  {
    id: 2,
    type: 'quotation',
    title: 'EOL设备报价单',
    customer: '东莞XX电子',
    amount: 620000,
    submitter: '李销售',
    submitTime: '2025-01-06 14:20',
    priority: 'medium',
  },
  {
    id: 3,
    type: 'discount',
    title: '价格优惠申请',
    customer: '惠州XX电池',
    amount: 450000,
    discount: 5,
    submitter: '王销售',
    submitTime: '2025-01-06 16:45',
    priority: 'high',
  },
]

const formatCurrency = (value) => {
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`
  }
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
  }).format(value)
}

const StatCard = ({ title, value, subtitle, trend, icon: Icon, color, bg }) => {
  return (
    <motion.div
      variants={fadeIn}
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={cn('text-2xl font-bold mb-1', color)}>{value}</p>
          {subtitle && (
            <p className="text-xs text-slate-500">{subtitle}</p>
          )}
          {trend && (
            <div className="flex items-center gap-1 mt-2">
              {trend > 0 ? (
                <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+{trend}%</span>
                </>
              ) : (
                <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{trend}%</span>
                </>
              )}
              <span className="text-xs text-slate-500 ml-1">vs 上月</span>
            </div>
          )}
        </div>
        <div className={cn('rounded-lg p-3 bg-opacity-20', bg)}>
          <Icon className={cn('h-6 w-6', color)} />
        </div>
      </div>
      <div className="absolute right-0 bottom-0 h-20 w-20 rounded-full bg-gradient-to-br from-purple-500/10 to-transparent blur-2xl opacity-30" />
    </motion.div>
  )
}

export default function SalesDirectorWorkstation() {
  const [selectedPeriod, setSelectedPeriod] = useState('month')

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="销售总监工作台"
        description={`年度目标: ${formatCurrency(mockOverallStats.yearTarget)} | 已完成: ${formatCurrency(mockOverallStats.yearAchieved)} (${mockOverallStats.yearProgress.toFixed(1)}%)`}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              销售报表
            </Button>
            <Button className="flex items-center gap-2">
              <Users className="w-4 h-4" />
              团队管理
            </Button>
          </motion.div>
        }
      />

      {/* Key Statistics - 6 column grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
      >
        <StatCard
          title="本月签约"
          value={formatCurrency(mockOverallStats.monthlyAchieved)}
          subtitle={`目标: ${formatCurrency(mockOverallStats.monthlyTarget)}`}
          trend={15.2}
          icon={DollarSign}
          color="text-amber-400"
          bg="bg-amber-500/10"
        />
        <StatCard
          title="完成率"
          value={`${mockOverallStats.achievementRate}%`}
          subtitle="本月目标达成"
          icon={Target}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
        <StatCard
          title="活跃客户"
          value={mockOverallStats.totalCustomers}
          subtitle={`本月新增 ${mockOverallStats.newCustomersThisMonth}`}
          trend={8.5}
          icon={Building2}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          title="进行中合同"
          value={mockOverallStats.activeContracts}
          subtitle={`待审批 ${mockOverallStats.pendingContracts}`}
          icon={Briefcase}
          color="text-purple-400"
          bg="bg-purple-500/10"
        />
        <StatCard
          title="待回款"
          value={formatCurrency(mockOverallStats.pendingPayment)}
          subtitle={`逾期 ${formatCurrency(mockOverallStats.overduePayment)}`}
          icon={CreditCard}
          color="text-red-400"
          bg="bg-red-500/10"
        />
        <StatCard
          title="回款率"
          value={`${mockOverallStats.collectionRate}%`}
          subtitle="回款完成率"
          icon={Receipt}
          color="text-cyan-400"
          bg="bg-cyan-500/10"
        />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Sales Funnel & Team Performance */}
        <div className="lg:col-span-2 space-y-6">
          {/* Sales Funnel */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <BarChart3 className="h-5 w-5 text-blue-400" />
                    销售漏斗分析
                  </CardTitle>
                  <Badge variant="outline" className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                    {mockOverallStats.activeOpportunities} 个商机
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {Object.entries(mockSalesFunnel).map(([stage, data], index) => {
                    const stageNames = {
                      inquiry: '询价阶段',
                      qualification: '需求确认',
                      proposal: '方案报价',
                      negotiation: '商务谈判',
                      closed: '签约成交',
                    }
                    return (
                      <div key={stage} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <div className="flex items-center gap-2">
                            <div className={cn(
                              'w-2 h-2 rounded-full',
                              index === 0 && 'bg-blue-500',
                              index === 1 && 'bg-cyan-500',
                              index === 2 && 'bg-amber-500',
                              index === 3 && 'bg-orange-500',
                              index === 4 && 'bg-emerald-500'
                            )} />
                            <span className="text-slate-300">{stageNames[stage]}</span>
                            <Badge variant="outline" className="text-xs bg-slate-700/40">
                              {data.count} 个
                            </Badge>
                          </div>
                          <div className="flex items-center gap-3">
                            <span className="text-slate-400 text-xs">
                              转化率: {data.conversion}%
                            </span>
                            <span className="text-white font-medium">
                              {formatCurrency(data.amount)}
                            </span>
                          </div>
                        </div>
                        <Progress
                          value={data.conversion}
                          className="h-2 bg-slate-700/50"
                        />
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Team Performance */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="h-5 w-5 text-purple-400" />
                    团队业绩排行
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    查看详情 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockTeamPerformance.map((member, index) => (
                    <div
                      key={member.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            'w-8 h-8 rounded-lg flex items-center justify-center text-white font-bold text-sm',
                            index === 0 && 'bg-gradient-to-br from-amber-500 to-orange-500',
                            index === 1 && 'bg-gradient-to-br from-blue-500 to-cyan-500',
                            index === 2 && 'bg-gradient-to-br from-slate-500 to-gray-600',
                            index === 3 && 'bg-gradient-to-br from-purple-500 to-pink-500',
                          )}>
                            {index + 1}
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-white">{member.name}</span>
                              <Badge variant="outline" className="text-xs bg-slate-700/40">
                                {member.role}
                              </Badge>
                            </div>
                            <div className="text-xs text-slate-400 mt-1">
                              {member.activeProjects} 个项目 · {member.newCustomers} 个新客户
                            </div>
                          </div>
                        </div>
                        <div className="text-right">
                          <div className="text-lg font-bold text-white">
                            {formatCurrency(member.monthlyAchieved)}
                          </div>
                          <div className="text-xs text-slate-400">
                            目标: {formatCurrency(member.monthlyTarget)}
                          </div>
                        </div>
                      </div>
                      <div className="space-y-2">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">完成率</span>
                          <span className={cn(
                            'font-medium',
                            member.achievementRate >= 90 ? 'text-emerald-400' :
                            member.achievementRate >= 70 ? 'text-amber-400' :
                            'text-red-400'
                          )}>
                            {member.achievementRate}%
                          </span>
                        </div>
                        <Progress
                          value={member.achievementRate}
                          className="h-1.5 bg-slate-700/50"
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Right Column - Pending Approvals & Top Customers */}
        <div className="space-y-6">
          {/* Pending Approvals */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <AlertTriangle className="h-5 w-5 text-amber-400" />
                    待审批事项
                  </CardTitle>
                  <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                    {mockPendingApprovals.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockPendingApprovals.map((item) => (
                  <div
                    key={item.id}
                    className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              item.type === 'contract' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                              item.type === 'quotation' && 'bg-purple-500/20 text-purple-400 border-purple-500/30',
                              item.type === 'discount' && 'bg-red-500/20 text-red-400 border-red-500/30'
                            )}
                          >
                            {item.type === 'contract' ? '合同' : item.type === 'quotation' ? '报价' : '优惠'}
                          </Badge>
                          {item.priority === 'high' && (
                            <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              紧急
                            </Badge>
                          )}
                        </div>
                        <p className="font-medium text-white text-sm">{item.title}</p>
                        <p className="text-xs text-slate-400 mt-1">{item.customer}</p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs mt-2">
                      <span className="text-slate-400">
                        {item.submitter} · {item.submitTime.split(' ')[1]}
                      </span>
                      <span className="font-medium text-amber-400">
                        {formatCurrency(item.amount)}
                      </span>
                    </div>
                  </div>
                ))}
                <Button variant="outline" className="w-full mt-3">
                  查看全部审批
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Top Customers */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Award className="h-5 w-5 text-amber-400" />
                    重点客户
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    全部 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockTopCustomers.map((customer, index) => (
                  <div
                    key={customer.id}
                    className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex items-center gap-2">
                        <div className={cn(
                          'w-6 h-6 rounded flex items-center justify-center text-xs font-bold text-white',
                          index === 0 && 'bg-gradient-to-br from-amber-500 to-orange-500',
                          index === 1 && 'bg-gradient-to-br from-blue-500 to-cyan-500',
                          index === 2 && 'bg-gradient-to-br from-purple-500 to-pink-500',
                          index === 3 && 'bg-gradient-to-br from-slate-500 to-gray-600',
                        )}>
                          {index + 1}
                        </div>
                        <div>
                          <p className="font-medium text-white text-sm">{customer.name}</p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            {customer.projectCount} 个项目
                          </p>
                        </div>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs">
                      <span className="text-slate-400">
                        累计: {formatCurrency(customer.totalAmount)}
                      </span>
                      <span className="text-emerald-400 font-medium">
                        本年: {formatCurrency(customer.thisYear)}
                      </span>
                    </div>
                  </div>
                ))}
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Year Progress */}
      <motion.div variants={fadeIn}>
        <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-base">
              <Activity className="h-5 w-5 text-cyan-400" />
              年度销售目标进度
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">年度目标</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {formatCurrency(mockOverallStats.yearTarget)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-400">已完成</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1">
                    {formatCurrency(mockOverallStats.yearAchieved)}
                  </p>
                </div>
              </div>
              <Progress
                value={mockOverallStats.yearProgress}
                className="h-3 bg-slate-700/50"
              />
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">
                  完成率: {mockOverallStats.yearProgress.toFixed(1)}%
                </span>
                <span className="text-slate-400">
                  剩余: {formatCurrency(mockOverallStats.yearTarget - mockOverallStats.yearAchieved)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

