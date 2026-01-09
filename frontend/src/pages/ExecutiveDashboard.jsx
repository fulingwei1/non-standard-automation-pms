/**
 * Executive Dashboard - 决策驾驶舱
 * 高管级数据可视化仪表盘，集成专业图表库
 */

import { useState, useEffect, useMemo } from 'react'
import { motion } from 'framer-motion'
import {
  LayoutDashboard,
  RefreshCw,
  Download,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Briefcase,
  CheckCircle2,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  Button,
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger,
} from '../components/ui'
import {
  LineChart,
  BarChart,
  PieChart,
  AreaChart,
  GaugeChart,
  DualAxesChart,
  FunnelChart,
} from '../components/charts'
import {
  ProjectHealthChart,
  CostAnalysisChart,
  DeliveryRateChart,
  UtilizationChart,
} from '../components/charts'
import { cn, formatCurrency } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { reportCenterApi } from '../services/api'
import { ApiIntegrationError } from '../components/ui'

// 时间范围选项
const timeRangeOptions = [
  { value: '7d', label: '近7天' },
  { value: '30d', label: '近30天' },
  { value: '90d', label: '近90天' },
  { value: 'ytd', label: '年初至今' },
  { value: 'custom', label: '自定义' },
]

export default function ExecutiveDashboard() {
  const [loading, setLoading] = useState(true)
  const [refreshing, setRefreshing] = useState(false)
  const [timeRange, setTimeRange] = useState('30d')
  const [activeTab, setActiveTab] = useState('overview')

  // 数据状态
  const [dashboardData, setDashboardData] = useState({
    summary: {},
    monthly: {},
    health_distribution: {},
  })
  const [healthData, setHealthData] = useState({})
  const [deliveryData, setDeliveryData] = useState([])
  const [utilizationData, setUtilizationData] = useState([])
  const [costData, setCostData] = useState([])
  const [trendData, setTrendData] = useState([])
  const [projectStageData, setProjectStageData] = useState([])
  const [milestoneData, setMilestoneData] = useState({ completionRate: 0, healthIndex: 0 })
  const [projectProgressData, setProjectProgressData] = useState([])
  const [budgetData, setBudgetData] = useState([])
  const [paymentData, setPaymentData] = useState([])
  const [profitData, setProfitData] = useState([])
  const [salesFunnelData, setSalesFunnelData] = useState([])
  const [customerDistributionData, setCustomerDistributionData] = useState([])
  const [error, setError] = useState(null)
  const [exporting, setExporting] = useState(false)
  const [exportFormat, setExportFormat] = useState('')

  // 颜色映射
  const colorMap = {
    blue: 'from-blue-500/20 to-blue-600/30 border-blue-500/30',
    green: 'from-emerald-500/20 to-emerald-600/30 border-emerald-500/30',
    orange: 'from-orange-500/20 to-orange-600/30 border-orange-500/30',
    purple: 'from-purple-500/20 to-purple-600/30 border-purple-500/30',
    red: 'from-red-500/20 to-red-600/30 border-red-500/30',
  }

  const iconColorMap = {
    blue: 'bg-blue-500/20 text-blue-400',
    green: 'bg-emerald-500/20 text-emerald-400',
    orange: 'bg-orange-500/20 text-orange-400',
    purple: 'bg-purple-500/20 text-purple-400',
    red: 'bg-red-500/20 text-red-400',
  }

  // 加载数据
  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        setError(null)

        // 获取仪表板数据
        const dashboardRes = await reportCenterApi.getExecutiveDashboard()

        if (dashboardRes.data) {
          setDashboardData(dashboardRes.data)
          
          // 设置健康度数据
          if (dashboardRes.data.health_distribution) {
            setHealthData(dashboardRes.data.health_distribution)
            
            // 计算健康指数
            const total = Object.values(dashboardRes.data.health_distribution).reduce((sum, val) => sum + val, 0)
            if (total > 0) {
              const h1Count = dashboardRes.data.health_distribution.H1 || 0
              const h2Count = dashboardRes.data.health_distribution.H2 || 0
              const h3Count = dashboardRes.data.health_distribution.H3 || 0
              const healthIndex = Math.round(((h1Count * 100 + h2Count * 70 + h3Count * 30) / total))
              setMilestoneData(prev => ({ ...prev, healthIndex }))
            }
          }
          
          // 设置趋势数据
          if (dashboardRes.data.monthly) {
            const monthly = dashboardRes.data.monthly
            setTrendData(
              Object.keys(monthly).map(month => ({
                month,
                revenue: monthly[month].revenue || monthly[month].contract_amount || 0,
                profit: monthly[month].profit || 0,
                amount: monthly[month].amount || monthly[month].contract_amount || 0,
                count: monthly[month].count || monthly[month].new_contracts || 0,
              }))
            )
          }
        }

        // 获取交付准时率数据
        try {
          const deliveryRes = await reportCenterApi.getDeliveryRate({ time_range: timeRange })
          if (deliveryRes.data) {
            setDeliveryData(Array.isArray(deliveryRes.data) ? deliveryRes.data : [])
          }
        } catch (err) {
          console.error('Failed to load delivery rate data:', err)
        }

        // 获取利用率数据
        try {
          const utilRes = await reportCenterApi.getUtilization({ time_range: timeRange })
          if (utilRes.data) {
            setUtilizationData(Array.isArray(utilRes.data) ? utilRes.data : [])
          }
        } catch (err) {
          console.error('Failed to load utilization data:', err)
        }

        // 获取健康度分布（用于项目阶段分布等）
        try {
          const healthRes = await reportCenterApi.getHealthDistribution()
          if (healthRes.data) {
            // 可以用于计算项目阶段分布等
          }
        } catch (err) {
          console.error('Failed to load health distribution:', err)
        }
      } catch (err) {
        console.error('Failed to load executive dashboard:', err)
        setError(err)
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [timeRange])

  // KPI 卡片数据
  const kpiCards = useMemo(() => {
    const summary = dashboardData.summary || {}
    return [
      {
        title: '总营收',
        value: formatCurrency(summary.total_revenue || 0),
        change: `${summary.revenue_growth || 0}%`,
        changeType: (summary.revenue_growth || 0) >= 0 ? 'up' : 'down',
        subText: '较上月',
        icon: DollarSign,
        color: 'blue',
      },
      {
        title: '净利润',
        value: formatCurrency(summary.total_profit || 0),
        change: `${summary.profit_growth || 0}%`,
        changeType: (summary.profit_growth || 0) >= 0 ? 'up' : 'down',
        subText: '较上月',
        icon: TrendingUp,
        color: 'green',
      },
      {
        title: '活跃项目',
        value: summary.active_projects || 0,
        change: `${summary.project_growth || 0}%`,
        changeType: (summary.project_growth || 0) >= 0 ? 'up' : 'down',
        subText: '较上月',
        icon: Briefcase,
        color: 'orange',
      },
      {
        title: '交付准时率',
        value: `${summary.on_time_delivery_rate || 0}%`,
        change: `${summary.delivery_rate_change || 0}%`,
        changeType: (summary.delivery_rate_change || 0) >= 0 ? 'up' : 'down',
        subText: '较上月',
        icon: CheckCircle2,
        color: 'purple',
      },
    ]
  }, [dashboardData])

  // 刷新数据
  const handleRefresh = async () => {
    setRefreshing(true)
    setError(null)
    try {
      // 重新加载所有数据
      const [dashboardRes, deliveryRes, utilRes] = await Promise.all([
        reportCenterApi.getExecutiveDashboard(),
        reportCenterApi.getDeliveryRate({ time_range: timeRange }).catch(() => ({ data: [] })),
        reportCenterApi.getUtilization({ time_range: timeRange }).catch(() => ({ data: [] })),
      ])

      if (dashboardRes.data) {
        setDashboardData(dashboardRes.data)
        if (dashboardRes.data.health_distribution) {
          setHealthData(dashboardRes.data.health_distribution)
          
          // 重新计算健康指数
          const total = Object.values(dashboardRes.data.health_distribution).reduce((sum, val) => sum + val, 0)
          if (total > 0) {
            const h1Count = dashboardRes.data.health_distribution.H1 || 0
            const h2Count = dashboardRes.data.health_distribution.H2 || 0
            const h3Count = dashboardRes.data.health_distribution.H3 || 0
            const healthIndex = Math.round(((h1Count * 100 + h2Count * 70 + h3Count * 30) / total))
            setMilestoneData(prev => ({ ...prev, healthIndex }))
          }
        }
        if (dashboardRes.data.monthly) {
          const monthly = dashboardRes.data.monthly
          setTrendData(
            Object.keys(monthly).map(month => ({
              month,
              revenue: monthly[month].revenue || monthly[month].contract_amount || 0,
              profit: monthly[month].profit || 0,
              amount: monthly[month].amount || monthly[month].contract_amount || 0,
              count: monthly[month].count || monthly[month].new_contracts || 0,
            }))
          )
        }
      }

      if (deliveryRes.data) {
        setDeliveryData(Array.isArray(deliveryRes.data) ? deliveryRes.data : [])
      }

      if (utilRes.data) {
        setUtilizationData(Array.isArray(utilRes.data) ? utilRes.data : [])
      }
    } catch (err) {
      console.error('Failed to refresh:', err)
      setError(err)
    } finally {
      setRefreshing(false)
    }
  }

  // 导出数据
  const handleExport = async (format) => {
    if (!format) return
    setExporting(true)
    try {
      const exportParams = {
        report_type: 'executive_dashboard',
        format: format,
        time_range: timeRange,
        data: {
          summary: dashboardData.summary,
          health_distribution: healthData,
          trend_data: trendData,
        },
      }

      if (format === 'json') {
        // JSON 格式直接下载
        const dataStr = JSON.stringify(exportParams.data, null, 2)
        const dataBlob = new Blob([dataStr], { type: 'application/json' })
        const url = URL.createObjectURL(dataBlob)
        const link = document.createElement('a')
        link.href = url
        link.download = `executive_dashboard_${new Date().toISOString().split('T')[0]}.json`
        link.click()
        URL.revokeObjectURL(url)
      } else {
        // 其他格式调用 API
        const res = await reportCenterApi.exportReport(exportParams)
        if (res.data?.download_url) {
          window.open(res.data.download_url, '_blank')
        } else if (res.data) {
          // 如果返回的是 blob，直接下载
          const blob = new Blob([res.data], { type: `application/${format}` })
          const url = URL.createObjectURL(blob)
          const link = document.createElement('a')
          link.href = url
          link.download = `executive_dashboard_${new Date().toISOString().split('T')[0]}.${format}`
          link.click()
          URL.revokeObjectURL(url)
        }
      }
    } catch (err) {
      console.error('Failed to export:', err)
      alert('导出失败，请稍后重试')
    } finally {
      setExporting(false)
      setExportFormat('')
    }
  }

  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <PageHeader title="决策驾驶舱" description="企业运营数据全景视图" icon={LayoutDashboard} />
        <div className="text-center py-16 text-slate-400">加载中...</div>
      </div>
    )
  }

  if (error && !dashboardData.summary) {
    return (
      <div className="space-y-6 p-6">
        <PageHeader title="决策驾驶舱" description="企业运营数据全景视图" icon={LayoutDashboard} />
        <ApiIntegrationError
          error={error}
          apiEndpoint="/api/v1/report-center/executive-dashboard"
          onRetry={() => {
            setError(null)
            setLoading(true)
          }}
        />
      </div>
    )
  }

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
      className="space-y-6 p-6"
    >
      <PageHeader
        title="决策驾驶舱"
        description="企业运营数据全景视图"
        icon={LayoutDashboard}
        actions={
          <motion.div variants={fadeIn} className="flex gap-2">
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value)}
              className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary"
            >
              {timeRangeOptions.map((opt) => (
                <option key={opt.value} value={opt.value}>
                  {opt.label}
                </option>
              ))}
            </select>
            <Button
              variant="outline"
              size="sm"
              onClick={handleRefresh}
              disabled={refreshing}
              className="flex items-center gap-2"
            >
              <RefreshCw className={cn('w-4 h-4', refreshing && 'animate-spin')} />
              刷新
            </Button>
            <div className="relative inline-block">
              <select
                value={exportFormat}
                onChange={(e) => handleExport(e.target.value)}
                disabled={exporting}
                className="px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary appearance-none pr-8 cursor-pointer disabled:opacity-50"
              >
                <option value="" disabled>导出格式</option>
                <option value="xlsx">导出 Excel</option>
                <option value="pdf">导出 PDF</option>
                <option value="csv">导出 CSV</option>
                <option value="json">导出 JSON</option>
              </select>
              <Download className={cn('w-4 h-4 absolute right-2 top-1/2 -translate-y-1/2 pointer-events-none text-slate-400', exporting && 'animate-pulse')} />
            </div>
          </motion.div>
        }
      />

      {/* KPI Cards */}
      <motion.div
        variants={staggerContainer}
        className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4"
      >
        {kpiCards.map((kpi, index) => {
          const Icon = kpi.icon
          return (
            <motion.div key={index} variants={fadeIn}>
              <Card className={cn(
                'bg-gradient-to-br border',
                colorMap[kpi.color]
              )}>
                <CardContent className="p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <p className="text-sm text-slate-400 mb-1">{kpi.title}</p>
                      <p className="text-2xl font-bold text-white">{kpi.value}</p>
                      <div className="flex items-center gap-2 mt-2">
                        <span className={cn(
                          'text-xs flex items-center gap-1',
                          kpi.changeType === 'up' ? 'text-emerald-400' : 'text-red-400'
                        )}>
                          {kpi.changeType === 'up' ? (
                            <TrendingUp className="w-3 h-3" />
                          ) : (
                            <TrendingDown className="w-3 h-3" />
                          )}
                          {kpi.change}
                        </span>
                        <span className="text-xs text-slate-500">{kpi.subText}</span>
                      </div>
                    </div>
                    <div className={cn('p-3 rounded-xl', iconColorMap[kpi.color])}>
                      <Icon className="w-6 h-6" />
                    </div>
                  </div>
                </CardContent>
              </Card>
            </motion.div>
          )
        })}
      </motion.div>

      {/* Main Charts */}
      <Tabs value={activeTab} onValueChange={setActiveTab}>
        <TabsList className="grid w-full grid-cols-5 mb-4">
          <TabsTrigger value="overview">总览</TabsTrigger>
          <TabsTrigger value="projects">项目</TabsTrigger>
          <TabsTrigger value="finance">财务</TabsTrigger>
          <TabsTrigger value="resources">资源</TabsTrigger>
          <TabsTrigger value="sales">销售</TabsTrigger>
        </TabsList>

        {/* Overview Tab */}
        <TabsContent value="overview" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 项目健康度分布 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">项目健康度分布</CardTitle>
                </CardHeader>
                <CardContent>
                  <ProjectHealthChart
                    data={Object.keys(healthData).length > 0 ? healthData : { H1: 12, H2: 8, H3: 3, H4: 5 }}
                    chartType="donut"
                    height={280}
                    title=""
                    onHealthClick={(health) => console.log('Health clicked:', health)}
                  />
                </CardContent>
              </Card>
            </motion.div>

            {/* 交付准时率趋势 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">交付准时率趋势</CardTitle>
                </CardHeader>
                <CardContent>
                  {deliveryData.length > 0 ? (
                    <DeliveryRateChart
                      data={deliveryData}
                      chartType="trend"
                      height={280}
                      title=""
                    />
                  ) : (
                    <DeliveryRateChart
                      data={[
                        { month: '7月', rate: 82 },
                        { month: '8月', rate: 85 },
                        { month: '9月', rate: 78 },
                        { month: '10月', rate: 88 },
                        { month: '11月', rate: 92 },
                        { month: '12月', rate: 85 },
                      ]}
                      chartType="trend"
                      height={280}
                      title=""
                    />
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* 营收趋势 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">营收与利润趋势</CardTitle>
                </CardHeader>
                <CardContent>
                  {trendData.length > 0 ? (
                    <DualAxesChart
                      data={trendData}
                      xField="month"
                      yField={['revenue', 'profit']}
                      height={280}
                      leftFormatter={(v) => formatCurrency(v)}
                      rightFormatter={(v) => formatCurrency(v)}
                      title=""
                    />
                  ) : (
                    <div className="text-center py-16 text-slate-500">
                      <p>暂无趋势数据</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* 成本构成 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">成本构成分析</CardTitle>
                </CardHeader>
                <CardContent>
                  {costData.length > 0 ? (
                    <CostAnalysisChart
                      data={costData}
                      chartType="structure"
                      height={280}
                      title=""
                      onCategoryClick={(cat) => console.log('Category clicked:', cat)}
                    />
                  ) : (
                    <div className="text-center py-16 text-slate-500">
                      <p>暂无成本数据</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>
          </div>
        </TabsContent>

        {/* Projects Tab */}
        <TabsContent value="projects" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
            {/* 项目阶段分布 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">项目阶段分布</CardTitle>
                </CardHeader>
                <CardContent>
                  <BarChart
                    data={[
                      { stage: 'S1-需求', count: 3 },
                      { stage: 'S2-设计', count: 5 },
                      { stage: 'S3-采购', count: 4 },
                      { stage: 'S4-制造', count: 6 },
                      { stage: 'S5-装配', count: 4 },
                      { stage: 'S6-FAT', count: 2 },
                      { stage: 'S7-发运', count: 1 },
                      { stage: 'S8-SAT', count: 2 },
                      { stage: 'S9-质保', count: 1 },
                    ]}
                    xField="stage"
                    yField="count"
                    height={250}
                    colors={['#3b82f6']}
                    showLabel
                  />
                </CardContent>
              </Card>
            </motion.div>

            {/* 健康度仪表盘 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">项目健康指数</CardTitle>
                </CardHeader>
                <CardContent>
                  <GaugeChart
                    value={milestoneData.healthIndex || 0}
                    height={250}
                    title="整体健康度"
                    unit="%"
                  />
                </CardContent>
              </Card>
            </motion.div>

            {/* 里程碑完成率 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">里程碑完成率</CardTitle>
                </CardHeader>
                <CardContent>
                  <GaugeChart
                    value={milestoneData.completionRate || 0}
                    height={250}
                    title="本月里程碑"
                    unit="%"
                    thresholds={[
                      { value: 0.5, color: '#ef4444' },
                      { value: 0.75, color: '#eab308' },
                      { value: 1, color: '#22c55e' },
                    ]}
                  />
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* 项目进度看板 */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-lg text-white">项目进度趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <AreaChart
                  data={[
                    { week: 'W1', completed: 12, inProgress: 8, delayed: 2 },
                    { week: 'W2', completed: 15, inProgress: 10, delayed: 3 },
                    { week: 'W3', completed: 18, inProgress: 12, delayed: 2 },
                    { week: 'W4', completed: 22, inProgress: 9, delayed: 1 },
                  ].flatMap(d => [
                    { week: d.week, type: '已完成', value: d.completed },
                    { week: d.week, type: '进行中', value: d.inProgress },
                    { week: d.week, type: '延期', value: d.delayed },
                  ])}
                  xField="week"
                  yField="value"
                  seriesField="type"
                  isStack
                  height={300}
                  colors={['#22c55e', '#3b82f6', '#ef4444']}
                />
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        {/* Finance Tab */}
        <TabsContent value="finance" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 预算执行 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">预算执行分析</CardTitle>
                </CardHeader>
                <CardContent>
                  <CostAnalysisChart
                    data={[
                      { category: '材料成本', budget: 50000000, actual: 47500000 },
                      { category: '人工成本', budget: 30000000, actual: 28500000 },
                      { category: '外协费用', budget: 15000000, actual: 14500000 },
                      { category: '管理费用', budget: 10000000, actual: 10500000 },
                    ]}
                    chartType="budget"
                    height={300}
                  />
                </CardContent>
              </Card>
            </motion.div>

            {/* 回款进度 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">回款进度</CardTitle>
                </CardHeader>
                <CardContent>
                  <LineChart
                    data={[
                      { month: '7月', plan: 15000000, actual: 14200000 },
                      { month: '8月', plan: 18000000, actual: 17500000 },
                      { month: '9月', plan: 20000000, actual: 19800000 },
                      { month: '10月', plan: 22000000, actual: 21000000 },
                      { month: '11月', plan: 25000000, actual: 24500000 },
                      { month: '12月', plan: 28000000, actual: 26000000 },
                    ].flatMap(d => [
                      { month: d.month, type: '计划', value: d.plan },
                      { month: d.month, type: '实际', value: d.actual },
                    ])}
                    xField="month"
                    yField="value"
                    seriesField="type"
                    height={300}
                    formatter={(v) => formatCurrency(v)}
                    colors={['#64748b', '#22c55e']}
                  />
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* 利润分析 */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-lg text-white">项目利润分析</CardTitle>
              </CardHeader>
              <CardContent>
                <BarChart
                  data={[
                    { project: 'BMS老化测试', revenue: 850000, cost: 420000, profit: 430000 },
                    { project: 'EOL功能测试', revenue: 620000, cost: 498000, profit: 122000 },
                    { project: 'ICT在线测试', revenue: 450000, cost: 234500, profit: 215500 },
                    { project: 'AOI视觉检测', revenue: 380000, cost: 320000, profit: 60000 },
                    { project: '自动组装线', revenue: 1200000, cost: 850000, profit: 350000 },
                  ].flatMap(d => [
                    { project: d.project, type: '营收', value: d.revenue },
                    { project: d.project, type: '成本', value: d.cost },
                    { project: d.project, type: '利润', value: d.profit },
                  ])}
                  xField="project"
                  yField="value"
                  seriesField="type"
                  isGroup
                  height={350}
                  formatter={(v) => formatCurrency(v)}
                  colors={['#3b82f6', '#ef4444', '#22c55e']}
                />
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        {/* Resources Tab */}
        <TabsContent value="resources" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 人员利用率排名 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">人员利用率排名</CardTitle>
                </CardHeader>
                <CardContent>
                  {utilizationData.length > 0 ? (
                    <UtilizationChart
                      data={utilizationData}
                      chartType="bar"
                      height={350}
                      onPersonClick={(person) => console.log('Person clicked:', person)}
                    />
                  ) : (
                    <div className="text-center py-16 text-slate-500">
                      <p>暂无利用率数据</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* 部门负荷 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">部门负荷对比</CardTitle>
                </CardHeader>
                <CardContent>
                  <UtilizationChart
                    data={[
                      { department: '机械部', rate: 85 },
                      { department: '电气部', rate: 78 },
                      { department: '软件部', rate: 72 },
                      { department: '项目部', rate: 90 },
                      { department: '采购部', rate: 65 },
                      { department: '质量部', rate: 70 },
                    ]}
                    chartType="radar"
                    height={350}
                  />
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* 工时分布热力图 */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-lg text-white">资源分配趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <AreaChart
                  data={[
                    { week: 'W1', 机械部: 320, 电气部: 280, 软件部: 240 },
                    { week: 'W2', 机械部: 350, 电气部: 300, 软件部: 260 },
                    { week: 'W3', 机械部: 380, 电气部: 320, 软件部: 280 },
                    { week: 'W4', 机械部: 360, 电气部: 340, 软件部: 300 },
                  ].flatMap(d => [
                    { week: d.week, department: '机械部', hours: d.机械部 },
                    { week: d.week, department: '电气部', hours: d.电气部 },
                    { week: d.week, department: '软件部', hours: d.软件部 },
                  ])}
                  xField="week"
                  yField="hours"
                  seriesField="department"
                  isStack
                  height={300}
                  formatter={(v) => `${v}h`}
                />
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>

        {/* Sales Tab */}
        <TabsContent value="sales" className="space-y-6">
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            {/* 销售漏斗 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">销售漏斗</CardTitle>
                </CardHeader>
                <CardContent>
                  {salesFunnelData.length > 0 ? (
                    <FunnelChart
                      data={salesFunnelData}
                      xField="stage"
                      yField="value"
                      height={350}
                    />
                  ) : (
                    <div className="text-center py-16 text-slate-500">
                      <p>暂无销售漏斗数据</p>
                    </div>
                  )}
                </CardContent>
              </Card>
            </motion.div>

            {/* 客户分布 */}
            <motion.div variants={fadeIn}>
              <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
                <CardHeader>
                  <CardTitle className="text-lg text-white">客户行业分布</CardTitle>
                </CardHeader>
                <CardContent>
                  <PieChart
                    data={[
                      { type: '新能源', value: 35 },
                      { type: '消费电子', value: 28 },
                      { type: '汽车电子', value: 20 },
                      { type: '医疗器械', value: 12 },
                      { type: '其他', value: 5 },
                    ]}
                    donut
                    height={350}
                    statistic={{
                      title: '客户总数',
                      content: '156',
                    }}
                  />
                </CardContent>
              </Card>
            </motion.div>
          </div>

          {/* 销售趋势 */}
          <motion.div variants={fadeIn}>
            <Card className="bg-gradient-to-br from-slate-800/50 to-slate-900/50 border-slate-700/50">
              <CardHeader>
                <CardTitle className="text-lg text-white">销售业绩趋势</CardTitle>
              </CardHeader>
              <CardContent>
                {trendData.length > 0 ? (
                  <DualAxesChart
                    data={trendData}
                    xField="month"
                    yField={['amount', 'count']}
                    height={300}
                    leftFormatter={(v) => formatCurrency(v)}
                    rightFormatter={(v) => `${v}个`}
                    geometryOptions={[
                      { geometry: 'column', columnWidthRatio: 0.4, color: '#3b82f6' },
                      { geometry: 'line', smooth: true, color: '#22c55e', point: { size: 4 } },
                    ]}
                  />
                ) : (
                  <div className="text-center py-16 text-slate-500">
                    <p>销售业绩趋势数据需要从API获取</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}
