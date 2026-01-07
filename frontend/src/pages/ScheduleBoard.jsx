import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  Calendar,
  Clock,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Filter,
  Users,
  Package,
  Wrench,
  Zap,
  MoreHorizontal,
  ExternalLink,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from '../components/ui/card'
import { Button } from '../components/ui/button'
import { Badge } from '../components/ui/badge'
import { Progress } from '../components/ui/progress'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { projectApi, milestoneApi, progressApi } from '../services/api'

// Mock schedule data
const mockProjects = [
  {
    id: 'PJ250108001',
    name: 'BMS老化测试设备',
    customer: '宁德时代',
    stage: 'S5',
    stageName: '装配调试',
    progress: 65,
    health: 'H2',
    planStart: '2026-01-02',
    planEnd: '2026-01-20',
    daysRemaining: 16,
    milestones: [
      { name: '物料齐套', date: '2026-01-08', status: 'completed' },
      { name: '机械装配', date: '2026-01-12', status: 'in_progress' },
      { name: '电气调试', date: '2026-01-16', status: 'pending' },
      { name: '整机联调', date: '2026-01-20', status: 'pending' },
    ],
    resources: [
      { name: '张工', role: 'ME', load: 100 },
      { name: '李工', role: 'EE', load: 80 },
    ],
  },
  {
    id: 'PJ250105002',
    name: 'EOL功能测试设备',
    customer: '比亚迪',
    stage: 'S4',
    stageName: '加工制造',
    progress: 45,
    health: 'H1',
    planStart: '2025-12-20',
    planEnd: '2026-01-25',
    daysRemaining: 21,
    milestones: [
      { name: '设计评审', date: '2025-12-25', status: 'completed' },
      { name: '采购下单', date: '2026-01-02', status: 'completed' },
      { name: '物料到货', date: '2026-01-15', status: 'in_progress' },
      { name: '开始装配', date: '2026-01-18', status: 'pending' },
    ],
    resources: [
      { name: '王工', role: 'ME', load: 60 },
      { name: '赵工', role: 'SW', load: 40 },
    ],
  },
  {
    id: 'PJ250106003',
    name: 'ICT测试设备',
    customer: '华为',
    stage: 'S3',
    stageName: '采购备料',
    progress: 30,
    health: 'H3',
    planStart: '2025-12-28',
    planEnd: '2026-01-30',
    daysRemaining: 26,
    milestones: [
      { name: 'BOM发布', date: '2025-12-28', status: 'completed' },
      { name: '长周期物料下单', date: '2026-01-02', status: 'delayed' },
      { name: '物料齐套', date: '2026-01-20', status: 'at_risk' },
      { name: '开始装配', date: '2026-01-25', status: 'pending' },
    ],
    resources: [
      { name: '陈工', role: 'ME', load: 80 },
      { name: '刘工', role: 'EE', load: 100 },
    ],
    alerts: ['3件关键物料延期', '需要紧急协调'],
  },
]

const stageColors = {
  S1: 'bg-slate-500',
  S2: 'bg-blue-500',
  S3: 'bg-cyan-500',
  S4: 'bg-purple-500',
  S5: 'bg-amber-500',
  S6: 'bg-emerald-500',
  S7: 'bg-green-500',
  S8: 'bg-teal-500',
  S9: 'bg-slate-400',
}

const healthColors = {
  H1: { bg: 'bg-emerald-500/20', text: 'text-emerald-400', label: '正常' },
  H2: { bg: 'bg-amber-500/20', text: 'text-amber-400', label: '风险' },
  H3: { bg: 'bg-red-500/20', text: 'text-red-400', label: '阻塞' },
  H4: { bg: 'bg-slate-500/20', text: 'text-slate-400', label: '完结' },
}

const milestoneStatusColors = {
  completed: 'bg-emerald-500',
  in_progress: 'bg-blue-500',
  pending: 'bg-slate-500',
  delayed: 'bg-red-500',
  at_risk: 'bg-amber-500',
}

function ProjectCard({ project }) {
  const health = healthColors[project.health]

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="bg-surface-1 rounded-xl border border-border overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 border-b border-border/50">
        <div className="flex items-start justify-between mb-2">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-accent">{project.id}</span>
              <Badge className={cn('text-[10px]', stageColors[project.stage])}>
                {project.stageName}
              </Badge>
            </div>
            <h3 className="font-semibold text-white">{project.name}</h3>
            <p className="text-sm text-slate-400">{project.customer}</p>
          </div>
          <div className={cn('px-2 py-1 rounded-lg text-xs font-medium', health.bg, health.text)}>
            {health.label}
          </div>
        </div>

        {/* Progress */}
        <div className="mt-3">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-slate-400">整体进度</span>
            <span className="text-white font-medium">{project.progress}%</span>
          </div>
          <Progress value={project.progress} className="h-2" />
        </div>

        {/* Time Info */}
        <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {project.planEnd}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            剩余 {project.daysRemaining} 天
          </span>
        </div>
      </div>

      {/* Milestones Timeline */}
      <div className="p-4 bg-surface-0/50">
        <div className="text-xs font-medium text-slate-400 mb-3">关键里程碑</div>
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[5px] top-2 bottom-2 w-0.5 bg-border" />
          
          <div className="space-y-3">
            {project.milestones.map((milestone, index) => (
              <div key={index} className="flex items-start gap-3 relative">
                <div
                  className={cn(
                    'w-3 h-3 rounded-full mt-0.5 z-10',
                    milestoneStatusColors[milestone.status]
                  )}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white truncate">
                      {milestone.name}
                    </span>
                    <span className="text-xs text-slate-500">{milestone.date}</span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alerts */}
      {project.alerts && project.alerts.length > 0 && (
        <div className="p-3 bg-red-500/10 border-t border-red-500/20">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div className="text-xs text-red-300">
              {project.alerts.map((alert, i) => (
                <div key={i}>{alert}</div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Resources */}
      <div className="p-3 border-t border-border/50">
        <div className="flex items-center justify-between">
          <div className="flex -space-x-2">
            {project.resources.map((resource, index) => (
              <div
                key={index}
                className="w-7 h-7 rounded-full bg-gradient-to-br from-accent to-purple-500 flex items-center justify-center text-[10px] font-medium text-white border-2 border-surface-1"
                title={`${resource.name} (${resource.role}) - 负荷${resource.load}%`}
              >
                {resource.name[0]}
              </div>
            ))}
          </div>
          <Button variant="ghost" size="sm" className="h-7 text-xs">
            <ExternalLink className="w-3 h-3 mr-1" />
            详情
          </Button>
        </div>
      </div>
    </motion.div>
  )
}

function StageColumn({ stage, stageName, projects }) {
  const stageProjects = projects.filter((p) => p.stage === stage)
  const stageColor = stageColors[stage]

  return (
    <div className="min-w-[320px] max-w-[320px]">
      {/* Column Header */}
      <div className="flex items-center gap-2 mb-4 px-2">
        <div className={cn('w-3 h-3 rounded-full', stageColor)} />
        <h3 className="font-semibold text-white">{stageName}</h3>
        <Badge variant="secondary" className="ml-auto">
          {stageProjects.length}
        </Badge>
      </div>

      {/* Projects */}
      <div className="space-y-4">
        {stageProjects.length > 0 ? (
          stageProjects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))
        ) : (
          <div className="p-8 text-center text-slate-500 border border-dashed border-border rounded-xl">
            暂无项目
          </div>
        )}
      </div>
    </div>
  )
}

export default function ScheduleBoard() {
  const [viewMode, setViewMode] = useState('kanban') // kanban | gantt | calendar
  const [projects, setProjects] = useState([])
  const [loading, setLoading] = useState(true)

  const stages = [
    { stage: 'S3', name: '采购备料' },
    { stage: 'S4', name: '加工制造' },
    { stage: 'S5', name: '装配调试' },
    { stage: 'S6', name: 'FAT验收' },
  ]

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoading(true)
        const response = await projectApi.list({ page_size: 100 })
        // Handle PaginatedResponse format
        const data = response.data || response
        const projectList = data.items || data || []
        
        // Transform backend project format to frontend format and load milestones/resources
        const transformedProjects = await Promise.all(
          projectList.map(async (p) => {
            const projectId = p.id || p.project_code
            
            // Load milestones for this project
            let milestones = []
            try {
              const milestonesRes = await milestoneApi.list(projectId)
              const milestonesData = milestonesRes.data || milestonesRes || []
              milestones = milestonesData.map(m => ({
                name: m.milestone_name || m.name || '',
                date: m.plan_date || m.planned_date || '',
                status: m.status === 'COMPLETED' ? 'completed' : 
                        m.status === 'IN_PROGRESS' ? 'in_progress' : 'pending',
              }))
            } catch (err) {
              console.error(`Failed to load milestones for project ${projectId}:`, err)
            }
            
            // Load resources/workload for this project
            let resources = []
            try {
              // Try to get project progress summary which may include resource info
              const progressRes = await progressApi.reports.getSummary(projectId).catch(() => null)
              if (progressRes?.data) {
                // Extract resource info if available
                // This is a placeholder - adjust based on actual API response structure
                resources = []
              }
            } catch (err) {
              console.error(`Failed to load resources for project ${projectId}:`, err)
            }
            
            return {
              id: p.project_code || p.id,
              name: p.project_name,
              customer: p.customer_name || '未知客户',
              stage: p.stage || 'S1',
              stageName: getStageName(p.stage),
              progress: p.progress_pct || 0,
              health: p.health || 'H1',
              planStart: p.planned_start_date || '',
              planEnd: p.planned_end_date || '',
              daysRemaining: p.planned_end_date 
                ? Math.ceil((new Date(p.planned_end_date) - new Date()) / (1000 * 60 * 60 * 24))
                : 0,
              milestones,
              resources,
            }
          })
        )
        
        setProjects(transformedProjects)
      } catch (err) {
        console.error('Failed to fetch projects:', err)
        // 如果是演示账号，使用 mock 数据
        const isDemoAccount = localStorage.getItem('token')?.startsWith('demo_token_')
        if (isDemoAccount) {
          setProjects(mockProjects)
        } else {
          setProjects([])
        }
      } finally {
        setLoading(false)
      }
    }
    fetchProjects()
  }, [])

  const getStageName = (stage) => {
    const stageNames = {
      'S1': '需求进入',
      'S2': '方案设计',
      'S3': '采购备料',
      'S4': '加工制造',
      'S5': '装配调试',
      'S6': 'FAT验收',
      'S7': '包装发运',
      'S8': 'SAT验收',
      'S9': '质保结项',
    }
    return stageNames[stage] || stage
  }

  const totalProjects = projects.length
  const atRiskProjects = projects.filter((p) => p.health === 'H2').length
  const blockedProjects = projects.filter((p) => p.health === 'H3').length

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <PageHeader
        title="排期看板"
        description="PMC视角的项目进度与资源协调中心"
      />

      {/* Summary Stats */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {[
          {
            label: '在制项目',
            value: totalProjects,
            icon: Package,
            color: 'text-blue-400',
          },
          {
            label: '风险项目',
            value: atRiskProjects,
            icon: AlertTriangle,
            color: 'text-amber-400',
          },
          {
            label: '阻塞项目',
            value: blockedProjects,
            icon: Zap,
            color: 'text-red-400',
          },
          {
            label: '资源占用',
            value: '85%',
            icon: Users,
            color: 'text-emerald-400',
          },
        ].map((stat, index) => (
          <Card key={index} className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <stat.icon className={cn('w-8 h-8', stat.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* View Controls */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              {/* View Mode Toggle */}
              <div className="flex items-center gap-2">
                {[
                  { id: 'kanban', label: '看板' },
                  { id: 'gantt', label: '甘特图' },
                  { id: 'calendar', label: '日历' },
                ].map((mode) => (
                  <Button
                    key={mode.id}
                    variant={viewMode === mode.id ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode(mode.id)}
                  >
                    {mode.label}
                  </Button>
                ))}
              </div>

              {/* Filters */}
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-1" />
                  筛选
                </Button>
                <Button variant="outline" size="sm">
                  <Users className="w-4 h-4 mr-1" />
                  资源
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Kanban Board */}
      {viewMode === 'kanban' && (
        <motion.div variants={fadeIn} className="overflow-x-auto pb-4">
          <div className="flex gap-6 min-w-max">
            {stages.map(({ stage, name }) => (
              <StageColumn
                key={stage}
                stage={stage}
                stageName={name}
                projects={projects}
              />
            ))}
          </div>
        </motion.div>
      )}

      {/* Gantt View Placeholder */}
      {viewMode === 'gantt' && (
        <motion.div variants={fadeIn}>
          <Card className="bg-surface-1/50">
            <CardContent className="p-12 text-center">
              <Calendar className="w-16 h-16 mx-auto text-slate-600 mb-4" />
              <h3 className="text-lg font-medium text-slate-400">甘特图视图</h3>
              <p className="text-sm text-slate-500 mt-1">即将推出</p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Calendar View Placeholder */}
      {viewMode === 'calendar' && (
        <motion.div variants={fadeIn}>
          <Card className="bg-surface-1/50">
            <CardContent className="p-12 text-center">
              <Calendar className="w-16 h-16 mx-auto text-slate-600 mb-4" />
              <h3 className="text-lg font-medium text-slate-400">日历视图</h3>
              <p className="text-sm text-slate-500 mt-1">即将推出</p>
            </CardContent>
          </Card>
        </motion.div>
      )}

      {/* Resource Heat Map */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              资源负荷热力图
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-7 gap-2 mb-4">
              {['周一', '周二', '周三', '周四', '周五', '周六', '周日'].map((day) => (
                <div key={day} className="text-center text-xs text-slate-500">
                  {day}
                </div>
              ))}
            </div>
            <div className="space-y-2">
              {[
                { name: '张工 (ME)', loads: [100, 100, 80, 100, 60, 0, 0] },
                { name: '李工 (EE)', loads: [80, 100, 100, 80, 80, 40, 0] },
                { name: '王工 (SW)', loads: [60, 60, 80, 100, 100, 0, 0] },
                { name: '陈工 (TE)', loads: [40, 60, 80, 100, 80, 60, 0] },
              ].map((engineer, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div className="w-24 text-sm text-slate-400 truncate">
                    {engineer.name}
                  </div>
                  <div className="flex-1 grid grid-cols-7 gap-1">
                    {engineer.loads.map((load, i) => (
                      <div
                        key={i}
                        className={cn(
                          'h-8 rounded flex items-center justify-center text-xs font-medium',
                          load === 0
                            ? 'bg-slate-800 text-slate-500'
                            : load <= 60
                            ? 'bg-emerald-500/30 text-emerald-400'
                            : load <= 80
                            ? 'bg-amber-500/30 text-amber-400'
                            : 'bg-red-500/30 text-red-400'
                        )}
                      >
                        {load > 0 ? `${load}%` : '-'}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  )
}

