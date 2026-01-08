import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  BarChart3,
  TrendingUp,
  TrendingDown,
  Users,
  Package,
  DollarSign,
  Clock,
  AlertTriangle,
  CheckCircle2,
  Calendar,
  Target,
  Activity,
  Zap,
  ArrowUpRight,
  ArrowDownRight,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Progress } from '../components/ui/progress'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Mock dashboard data
const dashboardData = {
  kpis: [
    {
      label: '在制项目',
      value: 12,
      change: 2,
      changePercent: '+20%',
      trend: 'up',
      icon: Package,
      color: 'text-blue-400',
      bgColor: 'bg-blue-500/10',
    },
    {
      label: '本月产值',
      value: '¥2,680万',
      change: 180,
      changePercent: '+7.2%',
      trend: 'up',
      icon: DollarSign,
      color: 'text-emerald-400',
      bgColor: 'bg-emerald-500/10',
    },
    {
      label: '交付准时率',
      value: '87%',
      change: -3,
      changePercent: '-3%',
      trend: 'down',
      icon: Clock,
      color: 'text-amber-400',
      bgColor: 'bg-amber-500/10',
    },
    {
      label: '工程师利用率',
      value: '85%',
      change: 5,
      changePercent: '+5%',
      trend: 'up',
      icon: Users,
      color: 'text-purple-400',
      bgColor: 'bg-purple-500/10',
    },
  ],
  projectHealth: {
    healthy: 7,
    atRisk: 3,
    blocked: 2,
    total: 12,
  },
  monthlyTrend: [
    { month: '8月', revenue: 2100, projects: 8 },
    { month: '9月', revenue: 2350, projects: 10 },
    { month: '10月', revenue: 2200, projects: 9 },
    { month: '11月', revenue: 2500, projects: 11 },
    { month: '12月', revenue: 2450, projects: 10 },
    { month: '1月', revenue: 2680, projects: 12 },
  ],
  departmentPerformance: [
    { name: '机械设计部', utilization: 92, projects: 8, onTime: 85 },
    { name: '电气设计部', utilization: 88, projects: 6, onTime: 90 },
    { name: '软件开发部', utilization: 78, projects: 4, onTime: 95 },
    { name: '测试调试部', utilization: 85, projects: 5, onTime: 80 },
  ],
  alerts: [
    { type: 'urgent', message: 'ICT测试设备(PJ250106003)关键物料延期', time: '10分钟前' },
    { type: 'warning', message: 'BMS老化设备(PJ250108001)进度落后3天', time: '1小时前' },
    { type: 'info', message: 'EOL测试设备(PJ250105002)设计评审通过', time: '2小时前' },
  ],
  topProjects: [
    { id: 'PJ250108001', name: 'BMS老化测试设备', customer: '宁德时代', value: 580, progress: 65, health: 'H2' },
    { id: 'PJ250105002', name: 'EOL功能测试设备', customer: '比亚迪', value: 420, progress: 45, health: 'H1' },
    { id: 'PJ250106003', name: 'ICT测试设备', customer: '华为', value: 380, progress: 30, health: 'H3' },
  ],
}

function KpiCard({ kpi }) {
  return (
    <Card className="bg-surface-1/50 hover:bg-surface-1/70 transition-colors">
      <CardContent className="p-5">
        <div className="flex items-start justify-between">
          <div className={cn('p-3 rounded-xl', kpi.bgColor)}>
            <kpi.icon className={cn('w-6 h-6', kpi.color)} />
          </div>
          <div
            className={cn(
              'flex items-center gap-1 text-xs font-medium',
              kpi.trend === 'up' ? 'text-emerald-400' : 'text-red-400'
            )}
          >
            {kpi.trend === 'up' ? (
              <ArrowUpRight className="w-4 h-4" />
            ) : (
              <ArrowDownRight className="w-4 h-4" />
            )}
            {kpi.changePercent}
          </div>
        </div>
        <div className="mt-4">
          <p className="text-sm text-slate-400">{kpi.label}</p>
          <p className="text-3xl font-bold text-white mt-1">{kpi.value}</p>
        </div>
      </CardContent>
    </Card>
  )
}

function HealthDonut({ data }) {
  const total = data.total
  const healthyPercent = (data.healthy / total) * 100
  const atRiskPercent = (data.atRisk / total) * 100
  const blockedPercent = (data.blocked / total) * 100

  return (
    <div className="flex items-center gap-6">
      {/* Donut Chart */}
      <div className="relative w-32 h-32">
        <svg className="w-full h-full transform -rotate-90" viewBox="0 0 36 36">
          {/* Background */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            className="text-surface-2"
          />
          {/* Healthy */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={`${healthyPercent} ${100 - healthyPercent}`}
            strokeDashoffset="0"
            className="text-emerald-500"
          />
          {/* At Risk */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={`${atRiskPercent} ${100 - atRiskPercent}`}
            strokeDashoffset={`${-healthyPercent}`}
            className="text-amber-500"
          />
          {/* Blocked */}
          <circle
            cx="18"
            cy="18"
            r="15.9"
            fill="none"
            stroke="currentColor"
            strokeWidth="3"
            strokeDasharray={`${blockedPercent} ${100 - blockedPercent}`}
            strokeDashoffset={`${-(healthyPercent + atRiskPercent)}`}
            className="text-red-500"
          />
        </svg>
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <span className="text-2xl font-bold text-white">{total}</span>
          <span className="text-xs text-slate-400">项目</span>
        </div>
      </div>

      {/* Legend */}
      <div className="space-y-3">
        {[
          { label: '正常', value: data.healthy, color: 'bg-emerald-500' },
          { label: '风险', value: data.atRisk, color: 'bg-amber-500' },
          { label: '阻塞', value: data.blocked, color: 'bg-red-500' },
        ].map((item) => (
          <div key={item.label} className="flex items-center gap-2">
            <div className={cn('w-3 h-3 rounded-full', item.color)} />
            <span className="text-sm text-slate-400">{item.label}</span>
            <span className="text-sm font-medium text-white ml-auto">{item.value}</span>
          </div>
        ))}
      </div>
    </div>
  )
}

function MiniBarChart({ data }) {
  const maxValue = Math.max(...data.map((d) => d.revenue))

  return (
    <div className="flex items-end gap-2 h-32">
      {data.map((item, index) => (
        <div key={index} className="flex-1 flex flex-col items-center gap-1">
          <div className="w-full flex flex-col items-center gap-1">
            <span className="text-xs text-slate-400">{(item.revenue / 100).toFixed(0)}K</span>
            <div
              className="w-full bg-gradient-to-t from-accent/50 to-accent rounded-t-sm transition-all hover:from-accent/70"
              style={{ height: `${(item.revenue / maxValue) * 80}px` }}
            />
          </div>
          <span className="text-xs text-slate-500">{item.month}</span>
        </div>
      ))}
    </div>
  )
}

export default function OperationDashboard() {
  const [timeRange, setTimeRange] = useState('month')

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="运营大屏"
        description="实时监控公司运营状况，辅助管理决策"
        actions={
          <div className="flex items-center gap-2">
            {['week', 'month', 'quarter'].map((range) => (
              <Button
                key={range}
                variant={timeRange === range ? 'default' : 'outline'}
                size="sm"
                onClick={() => setTimeRange(range)}
              >
                {range === 'week' ? '本周' : range === 'month' ? '本月' : '本季度'}
              </Button>
            ))}
          </div>
        }
      />

      {/* KPI Cards */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {dashboardData.kpis.map((kpi, index) => (
          <KpiCard key={index} kpi={kpi} />
        ))}
      </motion.div>

      {/* Main Content Grid */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Project Health */}
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="w-5 h-5" />
              项目健康度
            </CardTitle>
          </CardHeader>
          <CardContent>
            <HealthDonut data={dashboardData.projectHealth} />
          </CardContent>
        </Card>

        {/* Revenue Trend */}
        <Card className="bg-surface-1/50 lg:col-span-2">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <BarChart3 className="w-5 h-5" />
              产值趋势
            </CardTitle>
            <CardDescription>近6个月产值（万元）</CardDescription>
          </CardHeader>
          <CardContent>
            <MiniBarChart data={dashboardData.monthlyTrend} />
          </CardContent>
        </Card>
      </motion.div>

      {/* Department Performance & Alerts */}
      <motion.div variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Department Performance */}
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              部门绩效
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {dashboardData.departmentPerformance.map((dept, index) => (
              <div key={index} className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm text-white">{dept.name}</span>
                  <div className="flex items-center gap-4 text-xs">
                    <span className="text-slate-400">
                      {dept.projects} 项目
                    </span>
                    <span
                      className={cn(
                        dept.onTime >= 90
                          ? 'text-emerald-400'
                          : dept.onTime >= 80
                          ? 'text-amber-400'
                          : 'text-red-400'
                      )}
                    >
                      准时率 {dept.onTime}%
                    </span>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Progress value={dept.utilization} className="h-2 flex-1" />
                  <span
                    className={cn(
                      'text-xs font-medium w-10 text-right',
                      dept.utilization >= 90
                        ? 'text-amber-400'
                        : 'text-emerald-400'
                    )}
                  >
                    {dept.utilization}%
                  </span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Alerts */}
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5" />
              实时预警
            </CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {dashboardData.alerts.map((alert, index) => (
              <div
                key={index}
                className={cn(
                  'p-3 rounded-lg flex items-start gap-3',
                  alert.type === 'urgent'
                    ? 'bg-red-500/10'
                    : alert.type === 'warning'
                    ? 'bg-amber-500/10'
                    : 'bg-blue-500/10'
                )}
              >
                {alert.type === 'urgent' ? (
                  <Zap className="w-4 h-4 text-red-400 mt-0.5" />
                ) : alert.type === 'warning' ? (
                  <AlertTriangle className="w-4 h-4 text-amber-400 mt-0.5" />
                ) : (
                  <CheckCircle2 className="w-4 h-4 text-blue-400 mt-0.5" />
                )}
                <div className="flex-1 min-w-0">
                  <p
                    className={cn(
                      'text-sm',
                      alert.type === 'urgent'
                        ? 'text-red-300'
                        : alert.type === 'warning'
                        ? 'text-amber-300'
                        : 'text-blue-300'
                    )}
                  >
                    {alert.message}
                  </p>
                  <p className="text-xs text-slate-500 mt-1">{alert.time}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </motion.div>

      {/* Top Projects */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Target className="w-5 h-5" />
              重点项目
            </CardTitle>
            <CardDescription>当前在制的高价值项目</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-3 text-slate-400 font-medium">项目编号</th>
                    <th className="text-left p-3 text-slate-400 font-medium">项目名称</th>
                    <th className="text-left p-3 text-slate-400 font-medium">客户</th>
                    <th className="text-right p-3 text-slate-400 font-medium">合同金额</th>
                    <th className="text-center p-3 text-slate-400 font-medium">进度</th>
                    <th className="text-center p-3 text-slate-400 font-medium">状态</th>
                  </tr>
                </thead>
                <tbody>
                  {dashboardData.topProjects.map((project) => (
                    <tr key={project.id} className="border-b border-border/50 hover:bg-surface-2/30">
                      <td className="p-3">
                        <span className="font-mono text-accent">{project.id}</span>
                      </td>
                      <td className="p-3 text-white">{project.name}</td>
                      <td className="p-3 text-slate-400">{project.customer}</td>
                      <td className="p-3 text-right text-white font-medium">
                        ¥{project.value}万
                      </td>
                      <td className="p-3">
                        <div className="flex items-center gap-2">
                          <Progress value={project.progress} className="h-1.5 w-20" />
                          <span className="text-xs text-slate-400">{project.progress}%</span>
                        </div>
                      </td>
                      <td className="p-3 text-center">
                        <Badge
                          className={cn(
                            project.health === 'H1'
                              ? 'bg-emerald-500/20 text-emerald-400'
                              : project.health === 'H2'
                              ? 'bg-amber-500/20 text-amber-400'
                              : 'bg-red-500/20 text-red-400'
                          )}
                        >
                          {project.health === 'H1'
                            ? '正常'
                            : project.health === 'H2'
                            ? '风险'
                            : '阻塞'}
                        </Badge>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

