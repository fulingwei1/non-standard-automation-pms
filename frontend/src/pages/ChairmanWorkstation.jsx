/**
 * Chairman Workstation - Executive dashboard for chairman
 * Features: Strategic overview, Financial metrics, Company performance, Key decisions
 * Core Functions: Strategic decision-making, Major approvals, Overall monitoring
 */

import { useState, useMemo } from 'react'
import { motion } from 'framer-motion'
import { Link } from 'react-router-dom'
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
  Crown,
  Globe,
  Factory,
  ShoppingCart,
  Package,
  Shield,
  Eye,
  ArrowRight,
  ClipboardCheck,
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

// Mock data for chairman dashboard
const mockCompanyStats = {
  // Financial metrics
  totalRevenue: 125000000,
  yearTarget: 150000000,
  yearProgress: 83.3,
  monthlyRevenue: 12500000,
  monthlyTarget: 12500000,
  monthlyProgress: 100,
  profit: 25000000,
  profitMargin: 20,
  totalCost: 100000000,
  
  // Sales metrics
  totalContracts: 156,
  activeContracts: 42,
  pendingContracts: 8,
  totalCustomers: 245,
  newCustomersThisMonth: 18,
  salesTeamSize: 28,
  
  // Project metrics
  totalProjects: 68,
  activeProjects: 42,
  completedProjects: 26,
  onTimeDeliveryRate: 88.5,
  projectHealthGood: 32,
  projectHealthWarning: 8,
  projectHealthCritical: 2,
  
  // Operations metrics
  totalEmployees: 186,
  activeEmployees: 178,
  departments: 8,
  productionCapacity: 85,
  qualityPassRate: 96.2,
  
  // Financial health
  accountsReceivable: 28500000,
  overdueReceivable: 3500000,
  collectionRate: 87.7,
  cashFlow: 18500000,
  
  // Growth metrics
  revenueGrowth: 18.5,
  customerGrowth: 12.3,
  projectGrowth: 15.8,
}

const mockDepartmentPerformance = [
  {
    id: 1,
    name: '销售部',
    manager: '刘总监',
    revenue: 125000000,
    target: 150000000,
    achievement: 83.3,
    projects: 42,
    employees: 28,
    status: 'good',
  },
  {
    id: 2,
    name: '项目部',
    manager: '孙经理',
    revenue: 0,
    target: 0,
    achievement: 0,
    projects: 42,
    onTimeRate: 88.5,
    employees: 35,
    status: 'good',
  },
  {
    id: 3,
    name: '技术开发部',
    manager: '周经理',
    revenue: 0,
    target: 0,
    achievement: 0,
    projects: 38,
    innovation: 12,
    employees: 45,
    status: 'excellent',
  },
  {
    id: 4,
    name: '生产部',
    manager: '王经理',
    revenue: 0,
    target: 0,
    achievement: 0,
    projects: 35,
    output: 28,
    employees: 52,
    status: 'good',
  },
  {
    id: 5,
    name: '采购部',
    manager: '陈经理',
    revenue: 0,
    target: 0,
    achievement: 0,
    orders: 156,
    costSavings: 850000,
    employees: 8,
    status: 'good',
  },
  {
    id: 6,
    name: '质量部',
    manager: '李经理',
    revenue: 0,
    target: 0,
    achievement: 0,
    inspections: 156,
    passRate: 96.2,
    employees: 12,
    status: 'excellent',
  },
]

const mockKeyDecisions = [
  {
    id: 1,
    type: 'investment',
    title: '新生产基地投资决策',
    amount: 50000000,
    department: '制造中心',
    submitter: '制造总监',
    submitTime: '2025-01-05',
    priority: 'high',
    status: 'pending',
  },
  {
    id: 2,
    type: 'contract',
    title: '重大合同审批',
    customer: '某大型汽车集团',
    amount: 8500000,
    department: '销售部',
    submitter: '销售总监',
    submitTime: '2025-01-06',
    priority: 'high',
    status: 'pending',
  },
  {
    id: 3,
    type: 'strategy',
    title: '2025年度战略规划',
    department: '总经理办公室',
    submitter: '总经理',
    submitTime: '2025-01-03',
    priority: 'high',
    status: 'reviewing',
  },
  {
    id: 4,
    type: 'personnel',
    title: '高级人才招聘',
    position: '技术总监',
    department: '技术开发部',
    submitter: 'HR部门',
    submitTime: '2025-01-04',
    priority: 'medium',
    status: 'pending',
  },
]

const mockStrategicMetrics = [
  {
    label: '市场占有率',
    value: 12.5,
    unit: '%',
    trend: 2.3,
    target: 15,
    color: 'text-blue-400',
  },
  {
    label: '客户满意度',
    value: 92.8,
    unit: '%',
    trend: 1.2,
    target: 95,
    color: 'text-emerald-400',
  },
  {
    label: '员工满意度',
    value: 88.5,
    unit: '%',
    trend: -0.5,
    target: 90,
    color: 'text-amber-400',
  },
  {
    label: '研发投入占比',
    value: 8.5,
    unit: '%',
    trend: 0.8,
    target: 10,
    color: 'text-purple-400',
  },
]

// 月度营收趋势数据
const mockMonthlyRevenue = [
  { month: '7月', revenue: 9800000, target: 10000000 },
  { month: '8月', revenue: 10500000, target: 11000000 },
  { month: '9月', revenue: 11200000, target: 11500000 },
  { month: '10月', revenue: 10800000, target: 12000000 },
  { month: '11月', revenue: 11800000, target: 12500000 },
  { month: '12月', revenue: 12500000, target: 12500000 },
]

// 项目健康度分布
const mockProjectHealthDistribution = [
  { health: 'H1', label: '正常', count: 32, color: 'emerald', percentage: 76.2 },
  { health: 'H2', label: '关注', count: 8, color: 'amber', percentage: 19.0 },
  { health: 'H3', label: '预警', count: 2, color: 'red', percentage: 4.8 },
]

// 风险预警项目
const mockRiskProjects = [
  {
    id: 1,
    projectCode: 'P2025-001',
    projectName: 'BMS测试设备项目',
    customer: '深圳XX科技',
    health: 'H3',
    issue: '物料延期，影响交付',
    delayDays: 15,
    riskLevel: 'high',
  },
  {
    id: 2,
    projectCode: 'P2024-089',
    projectName: 'EOL自动化线体',
    customer: '东莞XX电子',
    health: 'H2',
    issue: '技术难点未解决',
    delayDays: 8,
    riskLevel: 'medium',
  },
  {
    id: 3,
    projectCode: 'P2025-012',
    projectName: 'ICT测试设备',
    customer: '惠州XX电池',
    health: 'H2',
    issue: '客户需求变更',
    delayDays: 5,
    riskLevel: 'medium',
  },
]

// 待审批事项
const mockPendingApprovals = [
  {
    id: 1,
    type: 'contract',
    title: '重大合同审批',
    customer: '某大型汽车集团',
    amount: 8500000,
    department: '销售部',
    submitter: '销售总监',
    submitTime: '2025-01-06 10:30',
    priority: 'high',
  },
  {
    id: 2,
    type: 'investment',
    title: '新生产基地投资',
    amount: 50000000,
    department: '制造中心',
    submitter: '制造总监',
    submitTime: '2025-01-05 14:20',
    priority: 'high',
  },
  {
    id: 3,
    type: 'budget',
    title: '年度预算调整',
    amount: 12000000,
    department: '财务部',
    submitter: '财务总监',
    submitTime: '2025-01-04 16:45',
    priority: 'medium',
  },
]

// 最近项目
const mockRecentProjects = [
  {
    id: 1,
    projectCode: 'P2025-015',
    projectName: 'BMS测试设备项目',
    customer: '深圳XX科技',
    health: 'H1',
    progress: 65,
    stage: 'S4',
    plannedEndDate: '2025-03-15',
  },
  {
    id: 2,
    projectCode: 'P2025-014',
    projectName: 'EOL自动化线体',
    customer: '东莞XX电子',
    health: 'H2',
    progress: 45,
    stage: 'S3',
    plannedEndDate: '2025-04-20',
  },
  {
    id: 3,
    projectCode: 'P2025-013',
    projectName: 'ICT测试设备',
    customer: '惠州XX电池',
    health: 'H1',
    progress: 78,
    stage: 'S5',
    plannedEndDate: '2025-02-28',
  },
]

const formatCurrency = (value) => {
  if (value >= 100000000) {
    return `¥${(value / 100000000).toFixed(2)}亿`
  }
  if (value >= 10000) {
    return `¥${(value / 10000).toFixed(1)}万`
  }
  return new Intl.NumberFormat('zh-CN', {
    style: 'currency',
    currency: 'CNY',
    minimumFractionDigits: 0,
  }).format(value)
}

const StatCard = ({ title, value, subtitle, trend, icon: Icon, color, bg, size = 'normal' }) => {
  const textSize = size === 'large' ? 'text-3xl' : 'text-2xl'
  return (
    <motion.div
      variants={fadeIn}
      className="relative overflow-hidden rounded-lg border border-slate-700/50 bg-gradient-to-br from-slate-800/50 to-slate-900/50 p-5 backdrop-blur transition-all hover:border-slate-600/80 hover:shadow-lg"
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <p className="text-sm text-slate-400 mb-2">{title}</p>
          <p className={cn('font-bold mb-1', textSize, color)}>{value}</p>
          {subtitle && (
            <p className="text-xs text-slate-500">{subtitle}</p>
          )}
          {trend !== undefined && (
            <div className="flex items-center gap-1 mt-2">
              {trend > 0 ? (
                <>
                  <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                  <span className="text-xs text-emerald-400">+{trend}%</span>
                </>
              ) : trend < 0 ? (
                <>
                  <ArrowDownRight className="w-3 h-3 text-red-400" />
                  <span className="text-xs text-red-400">{trend}%</span>
                </>
              ) : null}
              {trend !== 0 && (
                <span className="text-xs text-slate-500 ml-1">vs 上月</span>
              )}
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

export default function ChairmanWorkstation() {
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      {/* Page Header */}
      <PageHeader
        title="董事长工作台"
        description={`年度营收目标: ${formatCurrency(mockCompanyStats.yearTarget)} | 已完成: ${formatCurrency(mockCompanyStats.totalRevenue)} (${mockCompanyStats.yearProgress.toFixed(1)}%)`}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <Button variant="outline" className="flex items-center gap-2">
              <BarChart3 className="w-4 h-4" />
              经营报表
            </Button>
            <Button className="flex items-center gap-2">
              <Eye className="w-4 h-4" />
              战略分析
            </Button>
          </motion.div>
        }
      />

      {/* Key Financial Metrics - 6 column grid */}
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
      >
        <StatCard
          title="年度营收"
          value={formatCurrency(mockCompanyStats.totalRevenue)}
          subtitle={`目标: ${formatCurrency(mockCompanyStats.yearTarget)}`}
          trend={mockCompanyStats.revenueGrowth}
          icon={DollarSign}
          color="text-amber-400"
          bg="bg-amber-500/10"
          size="large"
        />
        <StatCard
          title="净利润"
          value={formatCurrency(mockCompanyStats.profit)}
          subtitle={`利润率: ${mockCompanyStats.profitMargin}%`}
          trend={15.2}
          icon={TrendingUp}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
        <StatCard
          title="活跃项目"
          value={mockCompanyStats.activeProjects}
          subtitle={`总计 ${mockCompanyStats.totalProjects} 个`}
          trend={mockCompanyStats.projectGrowth}
          icon={Briefcase}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          title="客户总数"
          value={mockCompanyStats.totalCustomers}
          subtitle={`本月新增 ${mockCompanyStats.newCustomersThisMonth}`}
          trend={mockCompanyStats.customerGrowth}
          icon={Building2}
          color="text-purple-400"
          bg="bg-purple-500/10"
        />
        <StatCard
          title="应收账款"
          value={formatCurrency(mockCompanyStats.accountsReceivable)}
          subtitle={`逾期 ${formatCurrency(mockCompanyStats.overdueReceivable)}`}
          icon={CreditCard}
          color="text-red-400"
          bg="bg-red-500/10"
        />
        <StatCard
          title="回款率"
          value={`${mockCompanyStats.collectionRate}%`}
          subtitle="回款完成率"
          icon={Receipt}
          color="text-cyan-400"
          bg="bg-cyan-500/10"
        />
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Year Progress & Strategic Metrics */}
        <div className="lg:col-span-2 space-y-6">
          {/* Year Progress */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="h-5 w-5 text-cyan-400" />
                  年度经营目标进度
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">年度营收目标</p>
                      <p className="text-3xl font-bold text-white mt-1">
                        {formatCurrency(mockCompanyStats.yearTarget)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-slate-400">已完成</p>
                      <p className="text-3xl font-bold text-emerald-400 mt-1">
                        {formatCurrency(mockCompanyStats.totalRevenue)}
                      </p>
                    </div>
                  </div>
                  <Progress
                    value={mockCompanyStats.yearProgress}
                    className="h-4 bg-slate-700/50"
                  />
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">
                      完成率: {mockCompanyStats.yearProgress.toFixed(1)}%
                    </span>
                    <span className="text-slate-400">
                      剩余: {formatCurrency(mockCompanyStats.yearTarget - mockCompanyStats.totalRevenue)}
                    </span>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Strategic Metrics */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Target className="h-5 w-5 text-purple-400" />
                  战略指标
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {mockStrategicMetrics.map((metric, index) => (
                    <div key={index} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-slate-400">{metric.label}</span>
                        <div className="flex items-center gap-2">
                          {metric.trend > 0 ? (
                            <ArrowUpRight className="w-3 h-3 text-emerald-400" />
                          ) : metric.trend < 0 ? (
                            <ArrowDownRight className="w-3 h-3 text-red-400" />
                          ) : null}
                          <span className={cn('font-semibold', metric.color)}>
                            {metric.value}{metric.unit}
                          </span>
                        </div>
                      </div>
                      <Progress
                        value={(metric.value / metric.target) * 100}
                        className="h-2 bg-slate-700/50"
                      />
                      <div className="flex items-center justify-between text-xs">
                        <span className="text-slate-500">目标: {metric.target}{metric.unit}</span>
                        <span className="text-slate-500">
                          {metric.trend > 0 ? '+' : ''}{metric.trend}%
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Revenue Trend */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <TrendingUp className="h-5 w-5 text-emerald-400" />
                    月度营收趋势
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary" asChild>
                    <Link to="/business-reports">
                      查看报表 <ChevronRight className="w-3 h-3 ml-1" />
                    </Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockMonthlyRevenue.map((item, index) => {
                    const achievement = (item.revenue / item.target) * 100
                    return (
                      <div key={index} className="space-y-2">
                        <div className="flex items-center justify-between text-sm">
                          <span className="text-slate-400">{item.month}</span>
                          <div className="flex items-center gap-3">
                            <span className="text-slate-400 text-xs">
                              目标: {formatCurrency(item.target)}
                            </span>
                            <span className="font-semibold text-white">
                              {formatCurrency(item.revenue)}
                            </span>
                            <span className={cn(
                              'text-xs font-medium',
                              achievement >= 100 ? 'text-emerald-400' :
                              achievement >= 90 ? 'text-amber-400' : 'text-red-400'
                            )}>
                              {achievement.toFixed(1)}%
                            </span>
                          </div>
                        </div>
                        <Progress
                          value={Math.min(achievement, 100)}
                          className={cn(
                            "h-2 bg-slate-700/50",
                            achievement >= 100 && "bg-emerald-500/20",
                            achievement >= 90 && achievement < 100 && "bg-amber-500/20",
                            achievement < 90 && "bg-red-500/20"
                          )}
                        />
                      </div>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Project Health Overview */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <PieChart className="h-5 w-5 text-purple-400" />
                    项目健康度分布
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary" asChild>
                    <Link to="/board">
                      项目看板 <ChevronRight className="w-3 h-3 ml-1" />
                    </Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockProjectHealthDistribution.map((item) => (
                    <div key={item.health} className="space-y-2">
                      <div className="flex items-center justify-between text-sm">
                        <div className="flex items-center gap-2">
                          <div className={cn(
                            'w-3 h-3 rounded-full',
                            item.color === 'emerald' && 'bg-emerald-500',
                            item.color === 'amber' && 'bg-amber-500',
                            item.color === 'red' && 'bg-red-500'
                          )} />
                          <span className="text-slate-300">{item.label}</span>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className="text-slate-400 text-xs">
                            {item.count} 个项目
                          </span>
                          <span className={cn(
                            'font-semibold',
                            item.color === 'emerald' && 'text-emerald-400',
                            item.color === 'amber' && 'text-amber-400',
                            item.color === 'red' && 'text-red-400'
                          )}>
                            {item.percentage}%
                          </span>
                        </div>
                      </div>
                      <Progress
                        value={item.percentage}
                        className={cn(
                          "h-2 bg-slate-700/50",
                          item.color === 'emerald' && "bg-emerald-500/20",
                          item.color === 'amber' && "bg-amber-500/20",
                          item.color === 'red' && "bg-red-500/20"
                        )}
                      />
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Risk Projects */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <AlertTriangle className="h-5 w-5 text-red-400" />
                    风险预警项目
                  </CardTitle>
                  <Badge variant="outline" className="bg-red-500/20 text-red-400 border-red-500/30">
                    {mockRiskProjects.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockRiskProjects.map((project) => (
                    <Link
                      key={project.id}
                      to={`/projects/${project.id}`}
                      className="block p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-red-500/50 transition-colors cursor-pointer group"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-mono text-slate-400">
                              {project.projectCode}
                            </span>
                            <Badge
                              variant="outline"
                              className={cn(
                                'text-xs',
                                project.health === 'H3' && 'bg-red-500/20 text-red-400 border-red-500/30',
                                project.health === 'H2' && 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                              )}
                            >
                              {project.health === 'H3' ? '预警' : '关注'}
                            </Badge>
                            {project.riskLevel === 'high' && (
                              <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                                高风险
                              </Badge>
                            )}
                          </div>
                          <p className="font-medium text-white text-sm group-hover:text-red-400 transition-colors">
                            {project.projectName}
                          </p>
                          <p className="text-xs text-slate-400 mt-1">{project.customer}</p>
                        </div>
                      </div>
                      <div className="flex items-center justify-between text-xs mt-2">
                        <span className="text-slate-400">{project.issue}</span>
                        <span className="font-medium text-red-400">
                          延期 {project.delayDays} 天
                        </span>
                      </div>
                    </Link>
                  ))}
                  <Button variant="outline" className="w-full mt-3" asChild>
                    <Link to="/alerts">
                      查看全部预警 <ArrowRight className="w-3 h-3 ml-2" />
                    </Link>
                  </Button>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Department Performance */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Users className="h-5 w-5 text-blue-400" />
                    部门绩效总览
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary" asChild>
                    <Link to="/departments">
                      部门管理 <ChevronRight className="w-3 h-3 ml-1" />
                    </Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockDepartmentPerformance.map((dept) => (
                    <div
                      key={dept.id}
                      className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                    >
                      <div className="flex items-start justify-between mb-3">
                        <div className="flex items-center gap-3">
                          <div className={cn(
                            'w-10 h-10 rounded-lg flex items-center justify-center',
                            dept.status === 'excellent' && 'bg-gradient-to-br from-emerald-500/20 to-emerald-600/10',
                            dept.status === 'good' && 'bg-gradient-to-br from-blue-500/20 to-blue-600/10',
                            dept.status === 'warning' && 'bg-gradient-to-br from-amber-500/20 to-amber-600/10',
                          )}>
                            <Building2 className={cn(
                              'h-5 w-5',
                              dept.status === 'excellent' && 'text-emerald-400',
                              dept.status === 'good' && 'text-blue-400',
                              dept.status === 'warning' && 'text-amber-400',
                            )} />
                          </div>
                          <div>
                            <div className="flex items-center gap-2">
                              <span className="font-medium text-white">{dept.name}</span>
                              <Badge variant="outline" className="text-xs bg-slate-700/40">
                                {dept.manager}
                              </Badge>
                            </div>
                            <div className="text-xs text-slate-400 mt-1">
                              {dept.employees} 人 · {dept.projects || dept.orders || dept.inspections} 项工作
                            </div>
                          </div>
                        </div>
                        {dept.revenue > 0 && (
                          <div className="text-right">
                            <div className="text-lg font-bold text-white">
                              {formatCurrency(dept.revenue)}
                            </div>
                            <div className="text-xs text-slate-400">
                              完成率: {dept.achievement.toFixed(1)}%
                            </div>
                          </div>
                        )}
                      </div>
                      {dept.achievement > 0 && (
                        <Progress
                          value={dept.achievement}
                          className="h-1.5 bg-slate-700/50"
                        />
                      )}
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>

        {/* Right Column - Key Decisions, Approvals & Recent Projects */}
        <div className="space-y-6">
          {/* Key Decisions */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Crown className="h-5 w-5 text-amber-400" />
                    重大决策事项
                  </CardTitle>
                  <Badge variant="outline" className="bg-amber-500/20 text-amber-400 border-amber-500/30">
                    {mockKeyDecisions.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockKeyDecisions.map((item) => (
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
                              item.type === 'investment' && 'bg-red-500/20 text-red-400 border-red-500/30',
                              item.type === 'contract' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                              item.type === 'strategy' && 'bg-purple-500/20 text-purple-400 border-purple-500/30',
                              item.type === 'personnel' && 'bg-cyan-500/20 text-cyan-400 border-cyan-500/30'
                            )}
                          >
                            {item.type === 'investment' ? '投资' : 
                             item.type === 'contract' ? '合同' :
                             item.type === 'strategy' ? '战略' : '人事'}
                          </Badge>
                          {item.priority === 'high' && (
                            <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              紧急
                            </Badge>
                          )}
                        </div>
                        <p className="font-medium text-white text-sm">{item.title}</p>
                        <p className="text-xs text-slate-400 mt-1">
                          {item.department} · {item.submitter}
                        </p>
                      </div>
                    </div>
                    {item.amount && (
                      <div className="flex items-center justify-between text-xs mt-2">
                        <span className="text-slate-400">{item.submitTime}</span>
                        <span className="font-medium text-amber-400">
                          {formatCurrency(item.amount)}
                        </span>
                      </div>
                    )}
                  </div>
                ))}
                <Button variant="outline" className="w-full mt-3" asChild>
                  <Link to="/key-decisions">
                    查看全部事项 <ArrowRight className="w-3 h-3 ml-2" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Pending Approvals */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <ClipboardCheck className="h-5 w-5 text-blue-400" />
                    待审批事项
                  </CardTitle>
                  <Badge variant="outline" className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                    {mockPendingApprovals.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {mockPendingApprovals.map((item) => (
                  <Link
                    key={item.id}
                    to="/approvals"
                    className="block p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-blue-500/50 transition-colors cursor-pointer group"
                  >
                    <div className="flex items-start justify-between mb-2">
                      <div className="flex-1">
                        <div className="flex items-center gap-2 mb-1">
                          <Badge
                            variant="outline"
                            className={cn(
                              'text-xs',
                              item.type === 'contract' && 'bg-blue-500/20 text-blue-400 border-blue-500/30',
                              item.type === 'investment' && 'bg-red-500/20 text-red-400 border-red-500/30',
                              item.type === 'budget' && 'bg-purple-500/20 text-purple-400 border-purple-500/30'
                            )}
                          >
                            {item.type === 'contract' ? '合同' : 
                             item.type === 'investment' ? '投资' : '预算'}
                          </Badge>
                          {item.priority === 'high' && (
                            <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                              紧急
                            </Badge>
                          )}
                        </div>
                        <p className="font-medium text-white text-sm group-hover:text-blue-400 transition-colors">
                          {item.title}
                        </p>
                        <p className="text-xs text-slate-400 mt-1">
                          {item.department} · {item.submitter}
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center justify-between text-xs mt-2">
                      <span className="text-slate-400">{item.submitTime.split(' ')[1]}</span>
                      <span className="font-medium text-amber-400">
                        {formatCurrency(item.amount)}
                      </span>
                    </div>
                  </Link>
                ))}
                <Button variant="outline" className="w-full mt-3" asChild>
                  <Link to="/approvals">
                    审批中心 <ArrowRight className="w-3 h-3 ml-2" />
                  </Link>
                </Button>
              </CardContent>
            </Card>
          </motion.div>

          {/* Recent Projects */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <Briefcase className="h-5 w-5 text-cyan-400" />
                    最近项目
                  </CardTitle>
                  <Button variant="ghost" size="sm" className="text-xs text-primary" asChild>
                    <Link to="/projects">
                      项目列表 <ChevronRight className="w-3 h-3 ml-1" />
                    </Link>
                  </Button>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {mockRecentProjects.map((project) => (
                    <Link
                      key={project.id}
                      to={`/projects/${project.id}`}
                      className="block p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-cyan-500/50 transition-colors cursor-pointer group"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-mono text-slate-400">
                              {project.projectCode}
                            </span>
                            <Badge
                              variant="outline"
                              className={cn(
                                'text-xs',
                                project.health === 'H1' && 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
                                project.health === 'H2' && 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                              )}
                            >
                              {project.health === 'H1' ? '正常' : '关注'}
                            </Badge>
                          </div>
                          <p className="font-medium text-white text-sm group-hover:text-cyan-400 transition-colors">
                            {project.projectName}
                          </p>
                          <p className="text-xs text-slate-400 mt-1">{project.customer}</p>
                        </div>
                      </div>
                      <div className="space-y-2 mt-3">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">进度</span>
                          <span className="text-white font-medium">{project.progress}%</span>
                        </div>
                        <Progress
                          value={project.progress}
                          className="h-1.5 bg-slate-700/50"
                        />
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">阶段: {project.stage}</span>
                          <span className="text-slate-400">
                            {project.plannedEndDate}
                          </span>
                        </div>
                      </div>
                    </Link>
                  ))}
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Quick Stats */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <BarChart3 className="h-5 w-5 text-cyan-400" />
                  运营概览
                </CardTitle>
              </CardHeader>
              <CardContent className="space-y-4">
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">项目按时交付率</span>
                    <span className="font-semibold text-emerald-400">
                      {mockCompanyStats.onTimeDeliveryRate}%
                    </span>
                  </div>
                  <Progress
                    value={mockCompanyStats.onTimeDeliveryRate}
                    className="h-2 bg-slate-700/50"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">质量合格率</span>
                    <span className="font-semibold text-emerald-400">
                      {mockCompanyStats.qualityPassRate}%
                    </span>
                  </div>
                  <Progress
                    value={mockCompanyStats.qualityPassRate}
                    className="h-2 bg-slate-700/50"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">产能利用率</span>
                    <span className="font-semibold text-blue-400">
                      {mockCompanyStats.productionCapacity}%
                    </span>
                  </div>
                  <Progress
                    value={mockCompanyStats.productionCapacity}
                    className="h-2 bg-slate-700/50"
                  />
                </div>
                <div className="pt-3 border-t border-slate-700/50">
                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div>
                      <div className="text-2xl font-bold text-white">
                        {mockCompanyStats.totalEmployees}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">员工总数</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-white">
                        {mockCompanyStats.departments}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">部门数量</div>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>
        </div>
      </div>
    </motion.div>
  )
}

