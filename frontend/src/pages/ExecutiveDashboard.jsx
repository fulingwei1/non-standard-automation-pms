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
  Calendar,
  TrendingUp,
  TrendingDown,
  DollarSign,
  Users,
  Briefcase,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Target,
  Activity,
  FileText,
  Building2,
  Truck,
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
  const [deliveryData, setDeliveryData] = useState({})
  const [utilizationData, setUtilizationData] = useState([])
  const [costData, setCostData] = useState([])
  const [trendData, setTrendData] = useState([])

  // Mock 数据
  const mockTrendData = [
    { month: '2024-07', revenue: 9800000, cost: 7500000, profit: 2300000 },
    { month: '2024-08', revenue: 10500000, cost: 8000000, profit: 2500000 },
    { month: '2024-09', revenue: 11200000, cost: 8500000, profit: 2700000 },
    { month: '2024-10', revenue: 11800000, cost: 9000000, profit: 2800000 },
    { month: '2024-11', revenue: 12200000, cost: 9200000, profit: 3000000 },
    { month: '2024-12', revenue: 12500000, cost: 9500000, profit: 3000000 },
  ]

  const mockCostData = [
    { category: '材料成本', amount: 47500000 },
    { category: '人工成本', amount: 28500000 },
    { category: '外协费用', amount: 14500000 },
    { category: '管理费用', amount: 10500000 },
    { category: '销售费用', amount: 8500000 },
    { category: '研发费用', amount: 6800000 },
  ]

  const mockUtilizationData = [
    { name: '张三', rate: 95, department: '机械部' },
    { name: '李四', rate: 88, department: '电气部' },
    { name: '王五', rate: 82, department: '软件部' },
    { name: '赵六', rate: 78, department: '机械部' },
    { name: '钱七', rate: 72, department: '项目部' },
    { name: '孙八', rate: 68, department: '电气部' },
    { name: '周九', rate: 55, department: '软件部' },
  ]

  const mockSalesFunnel = [
    { stage: '线索', value: 100 },
    { stage: '商机', value: 65 },
    { stage: '报价', value: 45 },
    { stage: '签约', value: 25 },
    { stage: '回款', value: 18 },
  ]

  // 获取数据
  useEffect(() => {
    const fetchData = async () => {
      setLoading(true)
      try {
        const [dashboardRes, healthRes, deliveryRes, utilizationRes] = await Promise.allSettled([
          reportCenterApi.getExecutiveDashboard(),
          reportCenterApi.getHealthDistribution(),
          reportCenterApi.getDeliveryRate(),
          reportCenterApi.getUtilization(),
        ])

        if (dashboardRes.status === 'fulfilled' && dashboardRes.value?.data) {
          setDashboardData(dashboardRes.value.data)
        }
        if (healthRes.status === 'fulfilled' && healthRes.value?.data) {
          setHealthData(healthRes.value.data.distribution || {})
        }
        if (deliveryRes.status === 'fulfilled' && deliveryRes.value?.data) {
          setDeliveryData(deliveryRes.value.data)
        }
        if (utilizationRes.status === 'fulfilled' && utilizationRes.value?.data?.utilization_list) {
          setUtilizationData(utilizationRes.value.data.utilization_list)
        } else {
          setUtilizationData(mockUtilizationData)
        }

        setTrendData(mockTrendData)
        setCostData(mockCostData)
      } catch (err) {
        console.log('Dashboard API unavailable, using mock data')
        setTrendData(mockTrendData)
        setCostData(mockCostData)
        setUtilizationData(mockUtilizationData)
      }
      setLoading(false)
    }
    fetchData()
  }, [timeRange])

  // 刷新数据
  const handleRefresh = async () => {
    setRefreshing(true)
    try {
      const [dashboardRes, healthRes, deliveryRes, utilizationRes] = await Promise.allSettled([
        reportCenterApi.getExecutiveDashboard(),
        reportCenterApi.getHealthDistribution(),
        reportCenterApi.getDeliveryRate(),
        reportCenterApi.getUtilization(),
      ])

      if (dashboardRes.status === 'fulfilled' && dashboardRes.value?.data) {
        setDashboardData(dashboardRes.value.data)
      }
      if (healthRes.status === 'fulfilled' && healthRes.value?.data) {
        setHealthData(healthRes.value.data.distribution || {})
      }
      if (deliveryRes.status === 'fulfilled' && deliveryRes.value?.data) {
        setDeliveryData(deliveryRes.value.data)
      }
      if (utilizationRes.status === 'fulfilled' && utilizationRes.value?.data?.utilization_list) {
        setUtilizationData(utilizationRes.value.data.utilization_list)
      }
    } catch (err) {
      console.error('刷新数据失败:', err)
    } finally {
      setRefreshing(false)
    }
  }

  // 导出报表
  const [exporting, setExporting] = useState(false)
  const [exportFormat, setExportFormat] = useState('xlsx')

  const handleExport = async (format = 'xlsx') => {
    setExporting(true)
    try {
      const response = await reportCenterApi.exportDirect({
        report_type: 'EXECUTIVE_DASHBOARD',
        format: format,
        time_range: timeRange
      })

      if (response?.data?.export_path || response?.data?.report_id) {
        // 如果返回了 report_id，调用下载接口
        const reportId = response.data.report_id
        if (reportId) {
          const downloadRes = await reportCenterApi.download(reportId)
          // 创建下载链接
          const url = window.URL.createObjectURL(new Blob([downloadRes.data]))
          const link = document.createElement('a')
          link.href = url
          link.setAttribute('download', `决策驾驶舱_${new Date().toISOString().slice(0,10)}.${format}`)
          document.body.appendChild(link)
          link.click()
          link.remove()
          window.URL.revokeObjectURL(url)
        }
      }
    } catch (err) {
      console.error('导出报表失败:', err)
      // 回退到客户端导出
      handleClientExport(format)
    } finally {
      setExporting(false)
    }
  }

  // 客户端导出（备用方案）
  const handleClientExport = (format) => {
    const data = {
      summary: dashboardData.summary,
      monthly: dashboardData.monthly,
      health_distribution: dashboardData.health_distribution,
      exported_at: new Date().toISOString()
    }

    if (format === 'json') {
      const blob = new Blob([JSON.stringify(data, null, 2)], { type: 'application/json' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `决策驾驶舱_${new Date().toISOString().slice(0,10)}.json`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    } else if (format === 'csv') {
      // 简单 CSV 导出
      const rows = [
        ['指标', '值'],
        ['总项目数', dashboardData.summary?.total_projects || 0],
        ['进行中项目', dashboardData.summary?.active_projects || 0],
        ['合同总额', dashboardData.summary?.total_contract_amount || 0],
        ['已回款金额', dashboardData.summary?.total_received || 0],
        ['人员总数', dashboardData.summary?.total_users || 0],
      ]
      const csv = rows.map(row => row.join(',')).join('\n')
      const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8' })
      const url = window.URL.createObjectURL(blob)
      const link = document.createElement('a')
      link.href = url
      link.setAttribute('download', `决策驾驶舱_${new Date().toISOString().slice(0,10)}.csv`)
      document.body.appendChild(link)
      link.click()
      link.remove()
    }
  }

  // 计算指标
  const summary = dashboardData.summary || {}
  const monthly = dashboardData.monthly || {}

  // KPI 卡片数据
  const kpiCards = [
    {
      title: '总项目数',
      value: summary.total_projects || 28,
      change: '+3',
      changeType: 'up',
      icon: Briefcase,
      color: 'blue',
      subText: `进行中 ${summary.active_projects || 15}`,
    },
    {
      title: '合同总额',
      value: formatCurrency(summary.total_contract_amount || 125800000),
      change: '+18.5%',
      changeType: 'up',
      icon: DollarSign,
      color: 'amber',
      subText: `已回款 ${formatCurrency(summary.total_received || 89600000)}`,
    },
    {
      title: '交付准时率',
      value: `${(deliveryData.on_time_rate || 85.2).toFixed(1)}%`,
      change: '+2.3%',
      changeType: 'up',
      icon: Target,
      color: 'emerald',
      subText: `延期 ${deliveryData.delayed_projects || 3} 个`,
    },
    {
      title: '人员总数',
      value: summary.total_users || 86,
      change: '+5',
      changeType: 'up',
      icon: Users,
      color: 'purple',
      subText: `平均利用率 78.5%`,
    },
  ]

  const colorMap = {
    blue: 'from-blue-500/20 to-blue-600/10 border-blue-500/30',
    amber: 'from-amber-500/20 to-amber-600/10 border-amber-500/30',
    emerald: 'from-emerald-500/20 to-emerald-600/10 border-emerald-500/30',
    purple: 'from-purple-500/20 to-purple-600/10 border-purple-500/30',
  }

  const iconColorMap = {
    blue: 'text-blue-400 bg-blue-500/20',
    amber: 'text-amber-400 bg-amber-500/20',
    emerald: 'text-emerald-400 bg-emerald-500/20',
    purple: 'text-purple-400 bg-purple-500/20',
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
                  <DualAxesChart
                    data={trendData}
                    xField="month"
                    yField={['revenue', 'profit']}
                    height={280}
                    leftFormatter={(v) => formatCurrency(v)}
                    rightFormatter={(v) => formatCurrency(v)}
                    title=""
                  />
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
                  <CostAnalysisChart
                    data={costData}
                    chartType="structure"
                    height={280}
                    title=""
                    onCategoryClick={(cat) => console.log('Category clicked:', cat)}
                  />
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
                    value={78}
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
                    value={85}
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
                  <UtilizationChart
                    data={utilizationData.length > 0 ? utilizationData : mockUtilizationData}
                    chartType="bar"
                    height={350}
                    onPersonClick={(person) => console.log('Person clicked:', person)}
                  />
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
                  <FunnelChart
                    data={mockSalesFunnel}
                    xField="stage"
                    yField="value"
                    height={350}
                  />
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
                <DualAxesChart
                  data={[
                    { month: '7月', amount: 9800000, count: 5 },
                    { month: '8月', amount: 12500000, count: 7 },
                    { month: '9月', amount: 11200000, count: 6 },
                    { month: '10月', amount: 15800000, count: 9 },
                    { month: '11月', amount: 18200000, count: 11 },
                    { month: '12月', amount: 22500000, count: 13 },
                  ]}
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
              </CardContent>
            </Card>
          </motion.div>
        </TabsContent>
      </Tabs>
    </motion.div>
  )
}
