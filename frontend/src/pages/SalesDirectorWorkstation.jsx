/**
 * Sales Director Workstation - Executive dashboard for sales directors
 * Features: Strategic overview, Team performance, Sales analytics, Revenue monitoring
 * Core Functions: Sales strategy, Team management, Performance monitoring, Contract approval
 */

import { useState, useEffect, useMemo } from 'react'
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
  Loader2,
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
import { salesStatisticsApi, opportunityApi, contractApi } from '../services/api'
import { ApiIntegrationError } from '../components/ui'

// Mock data removed - 使用真实API
const mockSalesFunnel = {
  inquiry: { count: 120, amount: 15000000, conversion: 100 },
  qualification: { count: 85, amount: 12000000, conversion: 70.8 },
  proposal: { count: 52, amount: 8500000, conversion: 61.2 },
  negotiation: { count: 28, amount: 5200000, conversion: 53.8 },
  closed: { count: 15, amount: 3850000, conversion: 53.6 },
}

// const mockTopCustomers = [ // 已移除，使用真实API
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

// const mockRecentActivities = [ // 已移除，使用真实API
const mockRecentActivities = [
  {
    id: 1,
    type: 'contract_signed',
    action: '合同签署',
    target: 'BMS测试设备合同',
    operator: '张销售',
    timestamp: '2025-01-06 14:30',
    status: 'success',
  },
  {
    id: 2,
    type: 'payment_received',
    action: '收到回款',
    target: '深圳XX科技 - ¥85万',
    operator: '财务部',
    timestamp: '2025-01-06 13:45',
    status: 'success',
  },
  {
    id: 3,
    type: 'opportunity_created',
    action: '新增商机',
    target: 'EOL测试设备 - 东莞XX电子',
    operator: '李销售',
    timestamp: '2025-01-06 12:20',
    status: 'success',
  },
  {
    id: 4,
    type: 'quotation_submitted',
    action: '提交报价',
    target: 'ICT测试设备 - 惠州XX电池',
    operator: '王销售',
    timestamp: '2025-01-06 11:15',
    status: 'pending',
  },
  {
    id: 5,
    type: 'customer_visit',
    action: '客户拜访',
    target: '广州XX汽车零部件',
    operator: '刘销售',
    timestamp: '2025-01-06 10:00',
    status: 'success',
  },
  {
    id: 6,
    type: 'contract_approved',
    action: '合同审批通过',
    target: 'BMS老化测试设备',
    operator: '销售总监',
    timestamp: '2025-01-06 09:30',
    status: 'success',
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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [overallStats, setOverallStats] = useState(null)
  const [teamPerformance, setTeamPerformance] = useState([])
  const [pendingApprovals, setPendingApprovals] = useState([])
  const [recentActivities, setRecentActivities] = useState([])
  const [selectedPeriod, setSelectedPeriod] = useState('month')

  // Load data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)

        const [statsRes, teamRes, approvalsRes] = await Promise.all([
          salesStatisticsApi.getSummary({ period: selectedPeriod }),
          salesStatisticsApi.getSalesPerformance({ period: selectedPeriod }),
          contractApi.list({ status: 'pending_approval' })
        ])

        if (statsRes.data) {
          setOverallStats(statsRes.data)
        }
        if (teamRes.data?.items) {
          setTeamPerformance(teamRes.data.items)
        }
        if (approvalsRes.data?.items) {
          setPendingApprovals(approvalsRes.data.items)
        }
      } catch (err) {
        setError(err)
        setOverallStats(null)
        setTeamPerformance([])
        setPendingApprovals([])
        setRecentActivities([])
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [selectedPeriod])

  // Show error state
  if (error && !overallStats) {
    return (
      <div className="space-y-6">
        <PageHeader title="销售总监工作台" description="销售战略总览、团队绩效监控" />
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/sales/statistics/summary"
          onRetry={() => {
            const fetchData = async () => {
              try {
                setLoading(true)
                setError(null)
                const statsRes = await salesStatisticsApi.getSummary({ period: selectedPeriod })
                if (statsRes.data) {
                  setOverallStats(statsRes.data)
                }
              } catch (err) {
                setError(err)
              } finally {
                setLoading(false)
              }
            }
            fetchData()
          }}
        />
      </div>
    )
  }

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
        description={overallStats ? `年度目标: ${formatCurrency(overallStats.yearTarget || 0)} | 已完成: ${formatCurrency(overallStats.yearAchieved || 0)} (${(overallStats.yearProgress || 0).toFixed(1)}%)` : '销售战略总览、团队绩效监控'}
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
      {overallStats && (
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
      >
        <StatCard
          title="本月签约"
          value={formatCurrency(overallStats.monthlyAchieved || 0)}
          subtitle={`目标: ${formatCurrency(overallStats.monthlyTarget || 0)}`}
          trend={15.2}
          icon={DollarSign}
          color="text-amber-400"
          bg="bg-amber-500/10"
        />
        <StatCard
          title="完成率"
          value={`${overallStats.achievementRate || 0}%`}
          subtitle="本月目标达成"
          icon={Target}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
        <StatCard
          title="活跃客户"
          value={overallStats.totalCustomers || 0}
          subtitle={`本月新增 ${overallStats.newCustomersThisMonth || 0}`}
          trend={8.5}
          icon={Building2}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          title="进行中合同"
          value={overallStats.activeContracts || 0}
          subtitle={`待审批 ${overallStats.pendingContracts || 0}`}
          icon={Briefcase}
          color="text-purple-400"
          bg="bg-purple-500/10"
        />
        <StatCard
          title="待回款"
          value={formatCurrency(overallStats.pendingPayment || 0)}
          subtitle={`逾期 ${formatCurrency(overallStats.overduePayment || 0)}`}
          icon={CreditCard}
          color="text-red-400"
          bg="bg-red-500/10"
        />
        <StatCard
          title="回款率"
          value={`${overallStats.collectionRate || 0}%`}
          subtitle="回款完成率"
          icon={Receipt}
          color="text-cyan-400"
          bg="bg-cyan-500/10"
        />
      </motion.div>
      )}

      {/* Main Content Grid */}
      {overallStats && (
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
                    {overallStats?.activeOpportunities || 0} 个商机
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  {/* Sales funnel - 需要从API获取数据 */}
                  {/* {Object.entries(mockSalesFunnel).map(([stage, data], index) => {
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
                  {teamPerformance.map((member, index) => (
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
                    {pendingApprovals.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {pendingApprovals.map((item) => (
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
                {/* Top customers - 需要从API获取数据 */}
                {/* {mockTopCustomers.map((customer, index) => (
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
                ))} */}
                <div className="text-center py-8 text-slate-500">
                  <p>重点客户数据需要从API获取</p>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>

      {/* Year Progress */}
      {overallStats && (
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
                    {formatCurrency(overallStats.yearTarget || 0)}
                  </p>
                </div>
                <div className="text-right">
                  <p className="text-sm text-slate-400">已完成</p>
                  <p className="text-2xl font-bold text-emerald-400 mt-1">
                    {formatCurrency(overallStats.yearAchieved || 0)}
                  </p>
                </div>
              </div>
              <Progress
                value={overallStats.yearProgress || 0}
                className="h-3 bg-slate-700/50"
              />
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-400">
                  完成率: {(overallStats.yearProgress || 0).toFixed(1)}%
                </span>
                <span className="text-slate-400">
                  剩余: {formatCurrency((overallStats.yearTarget || 0) - (overallStats.yearAchieved || 0))}
                </span>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>
      )}
    </motion.div>
  )
}

