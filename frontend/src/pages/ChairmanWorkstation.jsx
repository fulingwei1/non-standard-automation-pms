/**
 * Chairman Workstation - Executive dashboard for chairman
 * Features: Strategic overview, Financial metrics, Company performance, Key decisions
 * Core Functions: Strategic decision-making, Major approvals, Overall monitoring
 */

import { useState, useEffect, useMemo } from 'react'
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
import { pmoApi, salesStatisticsApi, projectApi, reportCenterApi } from '../services/api'
import CultureWallCarousel from '../components/culture/CultureWallCarousel'
import { ApiIntegrationError } from '../components/ui'

// Mock data for chairman dashboard - 已移除，使用真实API
// const mockCompanyStats = {
//   // Financial metrics
//   totalRevenue: 125000000,
//   yearTarget: 150000000,
//   yearProgress: 83.3,
//   monthlyRevenue: 12500000,
//   monthlyTarget: 12500000,
//   monthlyProgress: 100,
//   profit: 25000000,
//   profitMargin: 20,
//   totalCost: 100000000,
//   
//   // Sales metrics
//   totalContracts: 156,
//   activeContracts: 42,
//   pendingContracts: 8,
//   totalCustomers: 245,
//   newCustomersThisMonth: 18,
//   salesTeamSize: 28,
//   
//   // Project metrics
//   totalProjects: 68,
//   activeProjects: 42,
//   completedProjects: 26,
//   onTimeDeliveryRate: 88.5,
//   projectHealthGood: 32,
//   projectHealthWarning: 8,
//   projectHealthCritical: 2,
//   
//   // Operations metrics
//   totalEmployees: 186,
//   activeEmployees: 178,
//   departments: 8,
//   productionCapacity: 85,
//   qualityPassRate: 96.2,
//   
//   // Financial health
//   accountsReceivable: 28500000,
//   overdueReceivable: 3500000,
//   collectionRate: 87.7,
//   cashFlow: 18500000,
//   
//   // Growth metrics
//   revenueGrowth: 18.5,
//   customerGrowth: 12.3,
//   projectGrowth: 15.8,
// }

// Mock data removed - 使用真实API

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
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [companyStats, setCompanyStats] = useState(null)
  const [pendingApprovals, setPendingApprovals] = useState([])
  const [keyProjects, setKeyProjects] = useState([])
  const [departmentPerformance, setDepartmentPerformance] = useState([])
  const [monthlyRevenue, setMonthlyRevenue] = useState([])
  const [riskProjects, setRiskProjects] = useState([])
  const [projectHealthDistribution, setProjectHealthDistribution] = useState([])

  // Load data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)

        // 获取基础仪表板数据
        const [dashboardRes, projectsRes] = await Promise.all([
          pmoApi.dashboard(),
          projectApi.list({ page: 1, page_size: 10 })
        ])

        if (dashboardRes.data) {
          setCompanyStats(dashboardRes.data)
        }
        if (projectsRes.data?.items) {
          setKeyProjects(projectsRes.data.items.slice(0, 5))
          
          // 筛选风险项目（健康度为 H2 或 H3）
          const riskProjectsData = projectsRes.data.items.filter(
            p => p.health === 'H2' || p.health === 'H3'
          )
          setRiskProjects(riskProjectsData)
        }

        // 获取项目健康度分布
        try {
          const healthRes = await reportCenterApi.getHealthDistribution()
          if (healthRes.data) {
            setProjectHealthDistribution(healthRes.data)
          }
        } catch (err) {
          console.error('Failed to load health distribution:', err)
        }

        // 获取风险墙数据
        try {
          const riskWallRes = await pmoApi.riskWall()
          if (riskWallRes.data?.projects) {
            setRiskProjects(riskWallRes.data.projects)
          }
        } catch (err) {
          console.error('Failed to load risk wall:', err)
        }

        // 获取月度营收数据（从销售统计 API）
        try {
          const now = new Date()
          const startDate = new Date(now.getFullYear(), now.getMonth() - 5, 1)
          const endDate = new Date(now.getFullYear(), now.getMonth() + 1, 0)
          const salesRes = await salesStatisticsApi.performance({
            start_date: startDate.toISOString().split('T')[0],
            end_date: endDate.toISOString().split('T')[0],
          })
          if (salesRes.data?.monthly_data) {
            setMonthlyRevenue(salesRes.data.monthly_data)
          }
        } catch (err) {
          console.error('Failed to load monthly revenue:', err)
        }

        // 获取部门绩效数据（从 PMO dashboard）
        if (dashboardRes.data?.departments) {
          setDepartmentPerformance(dashboardRes.data.departments)
        }
      } catch (err) {
        console.error('Failed to load chairman dashboard:', err)
        setError(err)
        setCompanyStats(null)
        setKeyProjects([])
        setPendingApprovals([])
        setDepartmentPerformance([])
        setMonthlyRevenue([])
        setRiskProjects([])
        setProjectHealthDistribution([])
      } finally {
        setLoading(false)
      }
    }
    fetchData()
  }, [])

  // Show error state
  if (error && !companyStats) {
    return (
      <div className="space-y-6">
        <PageHeader title="董事长工作台" description="企业战略总览、经营决策支持" />
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/pmo/dashboard"
          onRetry={() => {
            const fetchData = async () => {
              try {
                setLoading(true)
                setError(null)
                const dashboardRes = await pmoApi.dashboard()
                if (dashboardRes.data) {
                  setCompanyStats(dashboardRes.data)
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
        title="董事长工作台"
        description={companyStats ? `年度营收目标: ${formatCurrency(companyStats.yearTarget || 0)} | 已完成: ${formatCurrency(companyStats.totalRevenue || 0)} (${(companyStats.yearProgress || 0).toFixed(1)}%)` : '企业战略总览、经营决策支持'}
        actions={
          <motion.div variants={fadeIn}>
            <Button className="flex items-center gap-2">
              <Eye className="w-4 h-4" />
              战略分析
            </Button>
          </motion.div>
        }
      />

      {/* 文化墙滚动播放 */}
      <motion.div variants={fadeIn}>
        <CultureWallCarousel
          autoPlay={true}
          interval={5000}
          showControls={true}
          showIndicators={true}
          height="400px"
          onItemClick={(item) => {
            if (item.category === 'GOAL') {
              window.location.href = '/personal-goals'
            } else {
              window.location.href = `/culture-wall?item=${item.id}`
            }
          }}
        />
      </motion.div>

      {/* Key Financial Metrics - 6 column grid */}
      {companyStats && (
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="visible"
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 md:grid-cols-3 lg:grid-cols-6"
      >
        <StatCard
          title="年度营收"
          value={formatCurrency(companyStats.totalRevenue || 0)}
          subtitle={`目标: ${formatCurrency(companyStats.yearTarget || 0)}`}
          trend={companyStats.revenueGrowth || 0}
          icon={DollarSign}
          color="text-amber-400"
          bg="bg-amber-500/10"
          size="large"
        />
        <StatCard
          title="净利润"
          value={formatCurrency(companyStats.profit || 0)}
          subtitle={`利润率: ${companyStats.profitMargin || 0}%`}
          trend={15.2}
          icon={TrendingUp}
          color="text-emerald-400"
          bg="bg-emerald-500/10"
        />
        <StatCard
          title="活跃项目"
          value={companyStats.activeProjects || 0}
          subtitle={`总计 ${companyStats.totalProjects || 0} 个`}
          trend={companyStats.projectGrowth || 0}
          icon={Briefcase}
          color="text-blue-400"
          bg="bg-blue-500/10"
        />
        <StatCard
          title="客户总数"
          value={companyStats.totalCustomers || 0}
          subtitle={`本月新增 ${companyStats.newCustomersThisMonth || 0}`}
          trend={companyStats.customerGrowth || 0}
          icon={Building2}
          color="text-purple-400"
          bg="bg-purple-500/10"
        />
        <StatCard
          title="应收账款"
          value={formatCurrency(companyStats.accountsReceivable || 0)}
          subtitle={`逾期 ${formatCurrency(companyStats.overdueReceivable || 0)}`}
          icon={CreditCard}
          color="text-red-400"
          bg="bg-red-500/10"
        />
        <StatCard
          title="回款率"
          value={`${companyStats.collectionRate || 0}%`}
          subtitle="回款完成率"
          icon={Receipt}
          color="text-cyan-400"
          bg="bg-cyan-500/10"
        />
      </motion.div>
      )}

      {/* Main Content Grid */}
      {companyStats && (
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Strategic Target & Operating Target */}
        <div className="lg:col-span-2 space-y-6">
          {/* Strategic Target */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Target className="h-5 w-5 text-purple-400" />
                  战略目标
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 gap-4">
                  {/* Strategic metrics - 需要从API获取数据 */}
                  {}
                  <div className="text-center py-8 text-slate-500">
                    <p>战略目标数据需要从API获取</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          {/* Operating Target */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="flex items-center gap-2 text-base">
                  <Activity className="h-5 w-5 text-cyan-400" />
                  经营目标
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div className="flex items-center justify-between">
                    <div>
                      <p className="text-sm text-slate-400">年度营收目标</p>
                      <p className="text-3xl font-bold text-white mt-1">
                        {formatCurrency(companyStats.yearTarget || 0)}
                      </p>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-slate-400">已完成</p>
                      <p className="text-3xl font-bold text-emerald-400 mt-1">
                        {formatCurrency(companyStats.totalRevenue || 0)}
                      </p>
                    </div>
                  </div>
                  <Progress
                    value={companyStats.yearProgress || 0}
                    className="h-4 bg-slate-700/50"
                  />
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">
                      完成率: {(companyStats.yearProgress || 0).toFixed(1)}%
                    </span>
                    <span className="text-slate-400">
                      剩余: {formatCurrency((companyStats.yearTarget || 0) - (companyStats.totalRevenue || 0))}
                    </span>
                  </div>
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
                  {monthlyRevenue.length > 0 ? (
                    monthlyRevenue.map((item, index) => {
                      const revenue = item.revenue || item.amount || 0
                      const target = item.target || item.target_amount || 0
                      const month = item.month || item.period || `第${index + 1}月`
                      const achievement = target > 0 ? (revenue / target) * 100 : 0
                      return (
                        <div key={index} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <span className="text-slate-400">{month}</span>
                            <div className="flex items-center gap-3">
                              {target > 0 && (
                                <span className="text-slate-400 text-xs">
                                  目标: {formatCurrency(target)}
                                </span>
                              )}
                              <span className="font-semibold text-white">
                                {formatCurrency(revenue)}
                              </span>
                              {target > 0 && (
                                <span className={cn(
                                  'text-xs font-medium',
                                  achievement >= 100 ? 'text-emerald-400' :
                                  achievement >= 90 ? 'text-amber-400' : 'text-red-400'
                                )}>
                                  {achievement.toFixed(1)}%
                                </span>
                              )}
                            </div>
                          </div>
                          {target > 0 && (
                            <Progress
                              value={Math.min(achievement, 100)}
                              className={cn(
                                "h-2 bg-slate-700/50",
                                achievement >= 100 && "bg-emerald-500/20",
                                achievement >= 90 && achievement < 100 && "bg-amber-500/20",
                                achievement < 90 && "bg-red-500/20"
                              )}
                            />
                          )}
                        </div>
                      )
                    })
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <TrendingUp className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
                      <p className="text-sm">月度营收数据需要从API获取</p>
                    </div>
                  )}
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
                  {projectHealthDistribution.length > 0 ? (
                    projectHealthDistribution.map((item) => {
                      const health = item.health || item.health_status || 'H1'
                      const label = item.label || (health === 'H1' ? '正常' : health === 'H2' ? '关注' : '预警')
                      const count = item.count || item.project_count || 0
                      const percentage = item.percentage || item.percentage || 0
                      const color = item.color || (health === 'H1' ? 'emerald' : health === 'H2' ? 'amber' : 'red')
                      return (
                        <div key={health} className="space-y-2">
                          <div className="flex items-center justify-between text-sm">
                            <div className="flex items-center gap-2">
                              <div className={cn(
                                'w-3 h-3 rounded-full',
                                color === 'emerald' && 'bg-emerald-500',
                                color === 'amber' && 'bg-amber-500',
                                color === 'red' && 'bg-red-500'
                              )} />
                              <span className="text-slate-300">{label}</span>
                            </div>
                            <div className="flex items-center gap-3">
                              <span className="text-slate-400 text-xs">
                                {count} 个项目
                              </span>
                              <span className={cn(
                                'font-semibold',
                                color === 'emerald' && 'text-emerald-400',
                                color === 'amber' && 'text-amber-400',
                                color === 'red' && 'text-red-400'
                              )}>
                                {percentage.toFixed(1)}%
                              </span>
                            </div>
                          </div>
                          <Progress
                            value={percentage}
                            className={cn(
                              "h-2 bg-slate-700/50",
                              color === 'emerald' && "bg-emerald-500/20",
                              color === 'amber' && "bg-amber-500/20",
                              color === 'red' && "bg-red-500/20"
                            )}
                          />
                        </div>
                      )
                    })
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <PieChart className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
                      <p className="text-sm">项目健康度数据需要从API获取</p>
                    </div>
                  )}
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
                    {riskProjects.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {riskProjects.length > 0 ? (
                    riskProjects.map((project) => {
                      const projectCode = project.project_code || project.projectCode || project.id
                      const projectName = project.project_name || project.projectName || project.name
                      const customer = project.customer_name || project.customer || ''
                      const health = project.health || 'H2'
                      const issue = project.issue || project.risk_description || '需要关注'
                      const delayDays = project.delay_days || project.delayDays || 0
                      return (
                        <Link
                          key={project.id}
                          to={`/projects/${project.id}`}
                          className="block p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-red-500/50 transition-colors cursor-pointer group"
                        >
                          <div className="flex items-start justify-between mb-2">
                            <div className="flex-1">
                              <div className="flex items-center gap-2 mb-1">
                                <span className="text-xs font-mono text-slate-400">
                                  {projectCode}
                                </span>
                                <Badge
                                  variant="outline"
                                  className={cn(
                                    'text-xs',
                                    health === 'H3' && 'bg-red-500/20 text-red-400 border-red-500/30',
                                    health === 'H2' && 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                                  )}
                                >
                                  {health === 'H3' ? '预警' : '关注'}
                                </Badge>
                              </div>
                              <p className="font-medium text-white text-sm group-hover:text-red-400 transition-colors">
                                {projectName}
                              </p>
                              {customer && (
                                <p className="text-xs text-slate-400 mt-1">{customer}</p>
                              )}
                            </div>
                          </div>
                          {issue && (
                            <div className="flex items-center justify-between text-xs mt-2">
                              <span className="text-slate-400">{issue}</span>
                              {delayDays > 0 && (
                                <span className="font-medium text-red-400">
                                  延期 {delayDays} 天
                                </span>
                              )}
                            </div>
                          )}
                        </Link>
                      )
                    })
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <CheckCircle2 className="h-12 w-12 mx-auto mb-3 text-emerald-500/50" />
                      <p className="text-sm">暂无风险预警项目</p>
                    </div>
                  )}
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
                  {departmentPerformance.length > 0 ? (
                    departmentPerformance.map((dept) => {
                      const deptName = dept.name || dept.department_name || ''
                      const manager = dept.manager || dept.manager_name || ''
                      const employees = dept.employees || dept.employee_count || 0
                      const projects = dept.projects || dept.project_count || dept.orders || dept.inspections || 0
                      const revenue = dept.revenue || dept.total_revenue || 0
                      const achievement = dept.achievement || dept.achievement_rate || 0
                      const status = dept.status || (achievement >= 90 ? 'excellent' : achievement >= 70 ? 'good' : 'warning')
                      return (
                        <div
                          key={dept.id || dept.department_id}
                          className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-slate-600/80 transition-colors"
                        >
                          <div className="flex items-start justify-between mb-3">
                            <div className="flex items-center gap-3">
                              <div className={cn(
                                'w-10 h-10 rounded-lg flex items-center justify-center',
                                status === 'excellent' && 'bg-gradient-to-br from-emerald-500/20 to-emerald-600/10',
                                status === 'good' && 'bg-gradient-to-br from-blue-500/20 to-blue-600/10',
                                status === 'warning' && 'bg-gradient-to-br from-amber-500/20 to-amber-600/10',
                              )}>
                                <Building2 className={cn(
                                  'h-5 w-5',
                                  status === 'excellent' && 'text-emerald-400',
                                  status === 'good' && 'text-blue-400',
                                  status === 'warning' && 'text-amber-400',
                                )} />
                              </div>
                              <div>
                                <div className="flex items-center gap-2">
                                  <span className="font-medium text-white">{deptName}</span>
                                  {manager && (
                                    <Badge variant="outline" className="text-xs bg-slate-700/40">
                                      {manager}
                                    </Badge>
                                  )}
                                </div>
                                <div className="text-xs text-slate-400 mt-1">
                                  {employees} 人 · {projects} 项工作
                                </div>
                              </div>
                            </div>
                            {revenue > 0 && (
                              <div className="text-right">
                                <div className="text-lg font-bold text-white">
                                  {formatCurrency(revenue)}
                                </div>
                                {achievement > 0 && (
                                  <div className="text-xs text-slate-400">
                                    完成率: {achievement.toFixed(1)}%
                                  </div>
                                )}
                              </div>
                            )}
                          </div>
                          {achievement > 0 && (
                            <Progress
                              value={achievement}
                              className="h-1.5 bg-slate-700/50"
                            />
                          )}
                        </div>
                      )
                    })
                  ) : (
                    <div className="text-center py-8 text-slate-500">
                      <Users className="h-12 w-12 mx-auto mb-3 text-slate-500/50" />
                      <p className="text-sm">部门绩效数据需要从API获取</p>
                    </div>
                  )}
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
                    {/* Key decisions count - 需要从API获取 */}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {/* Key decisions - 需要从API获取数据 */}
                <div className="text-center py-8 text-slate-500">
                  <p>暂无重大决策事项</p>
                </div>
              </CardContent>
            </Card>
          </motion.div>

          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <div className="flex items-center justify-between">
                  <CardTitle className="flex items-center gap-2 text-base">
                    <ClipboardCheck className="h-5 w-5 text-blue-400" />
                    待审批事项
                  </CardTitle>
                  <Badge variant="outline" className="bg-blue-500/20 text-blue-400 border-blue-500/30">
                    {pendingApprovals.length}
                  </Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                {pendingApprovals.map((item) => (
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
                  {keyProjects.length > 0 ? keyProjects.map((project) => (
                    <Link
                      key={project.id}
                      to={`/projects/${project.id}`}
                      className="block p-3 bg-slate-800/40 rounded-lg border border-slate-700/50 hover:border-cyan-500/50 transition-colors cursor-pointer group"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <div className="flex items-center gap-2 mb-1">
                            <span className="text-xs font-mono text-slate-400">
                              {project.project_code || project.projectCode || project.id}
                            </span>
                            <Badge
                              variant="outline"
                              className={cn(
                                'text-xs',
                                (project.health === 'H1' || project.health_status === 'H1') && 'bg-emerald-500/20 text-emerald-400 border-emerald-500/30',
                                (project.health === 'H2' || project.health_status === 'H2') && 'bg-amber-500/20 text-amber-400 border-amber-500/30'
                              )}
                            >
                              {(project.health === 'H1' || project.health_status === 'H1') ? '正常' : '关注'}
                            </Badge>
                          </div>
                          <p className="font-medium text-white text-sm group-hover:text-cyan-400 transition-colors">
                            {project.project_name || project.projectName || project.name}
                          </p>
                          <p className="text-xs text-slate-400 mt-1">{project.customer_name || project.customer || ''}</p>
                        </div>
                      </div>
                      <div className="space-y-2 mt-3">
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">进度</span>
                          <span className="text-white font-medium">{project.progress || 0}%</span>
                        </div>
                        <Progress
                          value={project.progress || 0}
                          className="h-1.5 bg-slate-700/50"
                        />
                        <div className="flex items-center justify-between text-xs">
                          <span className="text-slate-400">阶段: {project.current_stage || project.stage || ''}</span>
                          <span className="text-slate-400">
                            {project.planned_end_date || project.plannedEndDate || ''}
                          </span>
                        </div>
                      </div>
                    </Link>
                  )) : (
                    <div className="text-center py-8 text-slate-500">
                      <p>暂无项目数据</p>
                    </div>
                  )}
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
                      {companyStats.onTimeDeliveryRate || 0}%
                    </span>
                  </div>
                  <Progress
                    value={companyStats.onTimeDeliveryRate || 0}
                    className="h-2 bg-slate-700/50"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">质量合格率</span>
                    <span className="font-semibold text-emerald-400">
                      {companyStats.qualityPassRate || 0}%
                    </span>
                  </div>
                  <Progress
                    value={companyStats.qualityPassRate || 0}
                    className="h-2 bg-slate-700/50"
                  />
                </div>
                <div className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span className="text-slate-400">产能利用率</span>
                    <span className="font-semibold text-blue-400">
                      {companyStats.productionCapacity}%
                    </span>
                  </div>
                  <Progress
                    value={companyStats.productionCapacity}
                    className="h-2 bg-slate-700/50"
                  />
                </div>
                <div className="pt-3 border-t border-slate-700/50">
                  <div className="grid grid-cols-2 gap-3 text-center">
                    <div>
                      <div className="text-2xl font-bold text-white">
                        {companyStats.totalEmployees}
                      </div>
                      <div className="text-xs text-slate-400 mt-1">员工总数</div>
                    </div>
                    <div>
                      <div className="text-2xl font-bold text-white">
                        {companyStats.departments}
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
      )}
    </motion.div>
  )
}

