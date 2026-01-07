/**
 * Sales Manager Workstation - Department-level sales management dashboard
 * Features: Team performance, Department metrics, Approval workflow, Customer management
 * Core Functions: Team management, Performance monitoring, Contract approval, Customer relationship
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
  ChevronRight,
  Phone,
  Mail,
  Flame,
  Zap,
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
import { SalesFunnel, CustomerCard, PaymentTimeline } from '../components/sales'

// Mock data for sales manager dashboard (department level)
const mockDeptStats = {
  monthlyTarget: 2000000,
  monthlyAchieved: 1680000,
  achievementRate: 84,
  yearTarget: 24000000,
  yearAchieved: 16800000,
  yearProgress: 70,
  teamSize: 8,
  activeContracts: 12,
  pendingApprovals: 3,
  totalCustomers: 68,
  newCustomersThisMonth: 5,
  activeOpportunities: 18,
  hotOpportunities: 7,
  pendingPayment: 850000,
  overduePayment: 120000,
  collectionRate: 88.5,
}

const mockTeamMembers = [
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
    name: '陈销售',
    role: '销售工程师',
    monthlyTarget: 300000,
    monthlyAchieved: 320000,
    achievementRate: 106.7,
    activeProjects: 6,
    newCustomers: 2,
    status: 'excellent',
  },
]

const mockSalesFunnel = {
  inquiry: { count: 45, amount: 5600000, conversion: 100 },
  qualification: { count: 32, amount: 4200000, conversion: 71.1 },
  proposal: { count: 20, amount: 3200000, conversion: 62.5 },
  negotiation: { count: 12, amount: 2100000, conversion: 60 },
  closed: { count: 7, amount: 1680000, conversion: 58.3 },
}

const mockPendingApprovals = [
  {
    id: 1,
    type: 'contract',
    title: 'BMS测试设备合同',
    customer: '深圳XX科技',
    amount: 850000,
    submitter: '张销售',
    submitTime: '2026-01-06 10:30',
    priority: 'high',
  },
  {
    id: 2,
    type: 'quotation',
    title: 'EOL设备报价单',
    customer: '东莞XX电子',
    amount: 620000,
    submitter: '李销售',
    submitTime: '2026-01-06 14:20',
    priority: 'medium',
  },
  {
    id: 3,
    type: 'discount',
    title: '价格优惠申请',
    customer: '惠州XX电池',
    amount: 450000,
    submitter: '王销售',
    submitTime: '2026-01-06 16:45',
    priority: 'high',
  },
]

const mockTopCustomers = [
  {
    id: 1,
    name: '深圳XX科技有限公司',
    shortName: '深圳XX科技',
    grade: 'A',
    status: 'active',
    industry: '新能源电池',
    location: '深圳',
    lastContact: '2天前',
    opportunityCount: 3,
    totalAmount: 2500000,
  },
  {
    id: 2,
    name: '东莞XX电子有限公司',
    shortName: '东莞XX电子',
    grade: 'B',
    status: 'active',
    industry: '消费电子',
    location: '东莞',
    lastContact: '1周前',
    opportunityCount: 1,
    totalAmount: 1200000,
  },
  {
    id: 3,
    name: '惠州XX电池科技',
    shortName: '惠州XX电池',
    grade: 'B',
    status: 'potential',
    industry: '储能系统',
    location: '惠州',
    lastContact: '3天前',
    opportunityCount: 2,
    totalAmount: 800000,
  },
]

const mockPayments = [
  { id: 1, type: 'progress', projectName: 'EOL项目进度款', amount: 150000, dueDate: '2026-01-08', status: 'pending' },
  { id: 2, type: 'deposit', projectName: 'BMS项目签约款', amount: 200000, dueDate: '2026-01-15', paidDate: '2026-01-05', status: 'paid' },
  { id: 3, type: 'acceptance', projectName: 'ICT项目验收款', amount: 180000, dueDate: '2026-01-20', status: 'pending' },
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
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-4 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg"
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
        <div className={cn('rounded-lg p-2 bg-opacity-20', bg)}>
          <Icon className={cn('h-5 w-5', color)} />
        </div>
      </div>
    </motion.div>
  )
}

const typeConfig = {
  contract: { label: '合同', color: 'bg-blue-500', textColor: 'text-blue-400' },
  quotation: { label: '报价', color: 'bg-purple-500', textColor: 'text-purple-400' },
  discount: { label: '优惠', color: 'bg-red-500', textColor: 'text-red-400' },
}

const priorityConfig = {
  high: { label: '紧急', color: 'bg-red-500', textColor: 'text-red-400' },
  medium: { label: '普通', color: 'bg-amber-500', textColor: 'text-amber-400' },
  low: { label: '低', color: 'bg-slate-500', textColor: 'text-slate-400' },
}

export default function SalesManagerWorkstation() {
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
        title="销售经理工作台"
        description={`部门目标: ${formatCurrency(mockDeptStats.monthlyTarget)} | 已完成: ${formatCurrency(mockDeptStats.monthlyAchieved)} (${mockDeptStats.achievementRate}%)`}
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
        }
      />

      {/* Key Statistics */}
      <motion.div
        variants={staggerContainer}
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
      >
        <StatCard
          title="本月签约"
          value={formatCurrency(mockDeptStats.monthlyAchieved)}
          subtitle={`目标: ${formatCurrency(mockDeptStats.monthlyTarget)}`}
          trend={12.5}
          icon={DollarSign}
          color="text-amber-400"
          bg="bg-amber-500/10"
        />
        <StatCard
          title="完成率"
          value={`${mockDeptStats.achievementRate}%`}
          subtitle="本月目标达成"
          icon={Target}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
        <StatCard
          title="团队规模"
          value={mockDeptStats.teamSize}
          subtitle={`活跃成员 ${mockDeptStats.teamSize}`}
          icon={Users}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          title="活跃客户"
          value={mockDeptStats.totalCustomers}
          subtitle={`本月新增 ${mockDeptStats.newCustomersThisMonth}`}
          trend={6.2}
          icon={Building2}
          color="text-purple-400"
          bg="bg-purple-500/10"
        />
        <StatCard
          title="待回款"
          value={formatCurrency(mockDeptStats.pendingPayment)}
          subtitle={`逾期 ${formatCurrency(mockDeptStats.overduePayment)}`}
          icon={CreditCard}
          color="text-red-400"
          bg="bg-red-500/10"
        />
        <StatCard
          title="待审批"
          value={mockDeptStats.pendingApprovals}
          subtitle="项待处理"
          icon={AlertTriangle}
          color="text-amber-400"
          bg="bg-amber-500/10"
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
                    {mockDeptStats.activeOpportunities} 个商机
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
                    团队成员业绩
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    查看详情 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {mockTeamMembers.map((member, index) => (
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
                {mockPendingApprovals.map((item) => {
                  const typeInfo = typeConfig[item.type]
                  const priorityInfo = priorityConfig[item.priority]
                  return (
                    <div
                      key={item.id}
                      className="p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors cursor-pointer"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <Badge
                              variant="outline"
                              className={cn('text-xs', typeInfo.textColor)}
                            >
                              {typeInfo.label}
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
                  )
                })}
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
                {mockTopCustomers.map((customer) => (
                  <CustomerCard
                    key={customer.id}
                    customer={customer}
                    compact
                    onClick={(c) => {
                      // Handle customer click if needed
                    }}
                  />
                ))}
              </CardContent>
            </Card>
          </motion.div>

          {/* Payment Schedule */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Receipt className="h-5 w-5 text-emerald-400" />
                    近期回款计划
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary">
                    全部回款 <ChevronRight className="w-3 h-3 ml-1" />
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <PaymentTimeline payments={mockPayments} compact />
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
                    {formatCurrency(mockDeptStats.yearTarget)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-400">已完成</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1">
                    {formatCurrency(mockDeptStats.yearAchieved)}
                  </p>
                </div>
              </div>
              <Progress
                value={mockDeptStats.yearProgress}
                className="h-3 bg-slate-700/50"
              />
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">
                  完成率: {mockDeptStats.yearProgress}%
                </span>
                <span className="text-slate-400">
                  剩余: {formatCurrency(mockDeptStats.yearTarget - mockDeptStats.yearAchieved)}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

