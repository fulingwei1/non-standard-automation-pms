import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { cn } from '../lib/utils'
import { projectApi, machineApi } from '../services/api'
import { formatCurrency, getHealthColor, getStageName } from '../lib/utils'
import { PageHeader } from '../components/layout/PageHeader'
import {
  Card,
  CardContent,
  StatCard,
  Progress,
  Badge,
  HealthBadge,
  SkeletonCard,
} from '../components/ui'
import {
  Briefcase,
  Box,
  TrendingUp,
  AlertTriangle,
  ArrowRight,
  BarChart3,
  CheckCircle2,
  Clock,
} from 'lucide-react'

// Stagger animation variants
const staggerContainer = {
  hidden: { opacity: 0 },
  visible: {
    opacity: 1,
    transition: { staggerChildren: 0.05, delayChildren: 0.1 },
  },
}

const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
}

// Note: Role-based redirect mapping is now handled in App.jsx at the route level
// This Dashboard component will only render for users without a specific dashboard

export default function Dashboard() {
  const [loading, setLoading] = useState(true)
  const [stats, setStats] = useState({
    totalProjects: 0,
    activeProjects: 0,
    totalMachines: 0,
    atRiskProjects: 0,
  })
  const [recentProjects, setRecentProjects] = useState([])

  // Note: Role-based redirect is now handled at the route level in App.jsx
  // This component will only render for users without a specific dashboard

  useEffect(() => {
    const fetchData = async () => {
      try {
        setLoading(true)
        const [projectsRes, machinesRes] = await Promise.all([
          projectApi.list(),
          machineApi.list({}),
        ])

        // Handle different API response formats (array, {items: []}, {data: []})
        let projects = []
        let machines = []

        if (projectsRes.data) {
          if (Array.isArray(projectsRes.data)) {
            projects = projectsRes.data
          } else if (Array.isArray(projectsRes.data.items)) {
            projects = projectsRes.data.items
          } else if (Array.isArray(projectsRes.data.data)) {
            projects = projectsRes.data.data
          }
        }

        if (machinesRes.data) {
          if (Array.isArray(machinesRes.data)) {
            machines = machinesRes.data
          } else if (Array.isArray(machinesRes.data.items)) {
            machines = machinesRes.data.items
          } else if (Array.isArray(machinesRes.data.data)) {
            machines = machinesRes.data.data
          }
        }

        setStats({
          totalProjects: projects.length,
          activeProjects: projects.filter((p) => p.health !== 'H4').length,
          totalMachines: machines.length,
          atRiskProjects: projects.filter((p) =>
            ['H2', 'H3'].includes(p.health)
          ).length,
        })

        setRecentProjects(projects.slice(0, 5))
      } catch (err) {
        // Use empty arrays on error - don't crash the UI
        setStats({
          totalProjects: 0,
          activeProjects: 0,
          totalMachines: 0,
          atRiskProjects: 0,
        })
        setRecentProjects([])
      } finally {
        setLoading(false)
      }
    }

    fetchData()
  }, [])

  const statCards = [
    {
      icon: Briefcase,
      label: '总项目数',
      value: stats.totalProjects,
      change: '+12%',
      trend: 'up',
    },
    {
      icon: BarChart3,
      label: '进行中项目',
      value: stats.activeProjects,
      change: '+3',
      trend: 'up',
    },
    {
      icon: Box,
      label: '设备总数',
      value: stats.totalMachines,
      change: '+8%',
      trend: 'up',
    },
    {
      icon: AlertTriangle,
      label: '风险项目',
      value: stats.atRiskProjects,
      change: '-2',
      trend: 'down',
    },
  ]

  return (
    <motion.div
      initial="hidden"
      animate="visible"
      variants={staggerContainer}
    >
      <motion.div variants={staggerChild}>
        <PageHeader
          title="仪表盘"
          description="项目全局概览与关键指标"
        />
      </motion.div>

      {/* Stats Grid */}
      <motion.div
        variants={staggerChild}
        className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"
      >
        {loading
          ? Array(4)
              .fill(null)
              .map((_, i) => (
                <Card key={i} className="p-5">
                  <div className="animate-pulse">
                    <div className="h-10 w-10 rounded-xl bg-white/10 mb-4" />
                    <div className="h-3 w-20 rounded bg-white/10 mb-3" />
                    <div className="h-6 w-16 rounded bg-white/10" />
                  </div>
                </Card>
              ))
          : statCards.map((stat, i) => (
              <StatCard key={i} {...stat} />
            ))}
      </motion.div>

      {/* Main Content Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Recent Projects */}
        <motion.div variants={staggerChild} className="lg:col-span-2">
          <Card hover={false}>
            <CardContent className="p-0">
              <div className="flex items-center justify-between p-5 border-b border-white/5">
                <h3 className="text-lg font-semibold text-white">最近项目</h3>
                <Link
                  to="/projects"
                  className="flex items-center gap-1 text-sm text-primary hover:text-primary-light transition-colors"
                >
                  查看全部 <ArrowRight className="h-4 w-4" />
                </Link>
              </div>

              {loading ? (
                <div className="p-5 space-y-4">
                  {Array(3)
                    .fill(null)
                    .map((_, i) => (
                      <SkeletonCard key={i} />
                    ))}
                </div>
              ) : recentProjects.length > 0 ? (
                <div className="divide-y divide-white/5">
                  {recentProjects.map((project) => (
                    <Link
                      key={project.id}
                      to={`/projects/${project.id}`}
                      className="flex items-center gap-4 p-5 hover:bg-white/[0.02] transition-colors group"
                    >
                      {/* Icon */}
                      <div
                        className={cn(
                          'p-3 rounded-xl',
                          'bg-gradient-to-br from-primary/20 to-indigo-500/10',
                          'ring-1 ring-primary/20',
                          'group-hover:scale-105 transition-transform'
                        )}
                      >
                        <Briefcase className="h-5 w-5 text-primary" />
                      </div>

                      {/* Info */}
                      <div className="flex-1 min-w-0">
                        <div className="flex items-center gap-3 mb-1">
                          <h4 className="font-medium text-white truncate">
                            {project.project_name}
                          </h4>
                          <HealthBadge health={project.health || 'H1'} />
                        </div>
                        <div className="flex items-center gap-4 text-sm text-slate-500">
                          <span>{project.project_code}</span>
                          <span>•</span>
                          <span>{project.customer_name}</span>
                        </div>
                      </div>

                      {/* Progress */}
                      <div className="w-32 hidden sm:block">
                        <div className="flex justify-between text-xs mb-1">
                          <span className="text-slate-400">进度</span>
                          <span className="text-white">
                            {project.progress_pct || 0}%
                          </span>
                        </div>
                        <Progress
                          value={project.progress_pct || 0}
                          size="sm"
                        />
                      </div>

                      {/* Arrow */}
                      <ArrowRight className="h-5 w-5 text-slate-600 group-hover:text-primary group-hover:translate-x-1 transition-all" />
                    </Link>
                  ))}
                </div>
              ) : (
                <div className="p-12 text-center text-slate-500">
                  暂无项目数据
                </div>
              )}
            </CardContent>
          </Card>
        </motion.div>

        {/* Quick Actions */}
        <motion.div variants={staggerChild}>
          <Card hover={false}>
            <CardContent>
              <h3 className="text-lg font-semibold text-white mb-4">
                快捷操作
              </h3>
              <div className="space-y-3">
                <Link
                  to="/projects"
                  className={cn(
                    'flex items-center gap-3 p-3 rounded-xl',
                    'bg-white/[0.03] border border-white/5',
                    'text-white hover:bg-white/[0.06] hover:border-white/10',
                    'transition-all duration-200'
                  )}
                >
                  <div className="p-2 rounded-lg bg-primary/20">
                    <Briefcase className="h-4 w-4 text-primary" />
                  </div>
                  <span className="text-sm font-medium">新建项目</span>
                </Link>

                <Link
                  to="/machines"
                  className={cn(
                    'flex items-center gap-3 p-3 rounded-xl',
                    'bg-white/[0.03] border border-white/5',
                    'text-white hover:bg-white/[0.06] hover:border-white/10',
                    'transition-all duration-200'
                  )}
                >
                  <div className="p-2 rounded-lg bg-emerald-500/20">
                    <Box className="h-4 w-4 text-emerald-400" />
                  </div>
                  <span className="text-sm font-medium">添加设备</span>
                </Link>

                <Link
                  to="/alerts"
                  className={cn(
                    'flex items-center gap-3 p-3 rounded-xl',
                    'bg-white/[0.03] border border-white/5',
                    'text-white hover:bg-white/[0.06] hover:border-white/10',
                    'transition-all duration-200'
                  )}
                >
                  <div className="p-2 rounded-lg bg-amber-500/20">
                    <AlertTriangle className="h-4 w-4 text-amber-400" />
                  </div>
                  <span className="text-sm font-medium">查看预警</span>
                </Link>
              </div>
            </CardContent>
          </Card>

          {/* Schedule Overview */}
          <Card hover={false} className="mt-6">
            <CardContent>
              <h3 className="text-lg font-semibold text-white mb-4">
                今日待办
              </h3>
              <div className="space-y-3">
                <div className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02]">
                  <div className="mt-0.5">
                    <CheckCircle2 className="h-5 w-5 text-emerald-500" />
                  </div>
                  <div>
                    <p className="text-sm text-white">项目评审会议</p>
                    <p className="text-xs text-slate-500">10:00 - 11:00</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02]">
                  <div className="mt-0.5">
                    <Clock className="h-5 w-5 text-amber-500" />
                  </div>
                  <div>
                    <p className="text-sm text-white">设备出厂验收</p>
                    <p className="text-xs text-slate-500">14:00 - 16:00</p>
                  </div>
                </div>
                <div className="flex items-start gap-3 p-3 rounded-xl bg-white/[0.02]">
                  <div className="mt-0.5">
                    <Clock className="h-5 w-5 text-slate-500" />
                  </div>
                  <div>
                    <p className="text-sm text-white">周进度汇报</p>
                    <p className="text-xs text-slate-500">17:00 - 18:00</p>
                  </div>
                </div>
              </div>
            </CardContent>
          </Card>
        </motion.div>
      </div>
    </motion.div>
  )
}

