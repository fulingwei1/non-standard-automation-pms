/**
 * Engineer Workstation - Timeline-focused work interface for mechanical engineers
 * Features: Gantt chart, Calendar view, Task list with design deliverables
 */

import { useState, useEffect, useMemo, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Calendar,
  Clock,
  CheckCircle2,
  Circle,
  PlayCircle,
  PauseCircle,
  AlertTriangle,
  Filter,
  Search,
  ChevronRight,
  ChevronLeft,
  Flag,
  Folder,
  Timer,
  BarChart3,
  CalendarDays,
  List,
  ZoomIn,
  ZoomOut,
  FileText,
  Upload,
  Send,
  ClipboardCheck,
  Box,
  Layers,
  Target,
  TrendingUp,
} from 'lucide-react'
import { PageHeader } from '../components/layout'
import {
  Card,
  CardContent,
  Button,
  Input,
  Badge,
  Progress,
} from '../components/ui'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { taskCenterApi, progressApi, projectApi } from '../services/api'

// Import engineer components
import GanttChart from '../components/engineer/GanttChart'
import CalendarView from '../components/engineer/CalendarView'
import TaskDetailPanel from '../components/engineer/TaskDetailPanel'

// Mock task data for mechanical engineer
const mockEngineerTasks = [
  {
    id: 'T001',
    title: 'Main frame 3D modeling',
    titleCn: '主框架3D建模',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineNo: '1号机',
    type: 'design',
    status: 'in_progress',
    priority: 'high',
    progress: 65,
    plannedStart: '2026-01-02',
    plannedEnd: '2026-01-08',
    actualStart: '2026-01-02',
    estimatedHours: 24,
    actualHours: 16,
    assignee: '张工',
    reviewer: '王组长',
    milestone: '设计评审',
    milestoneDate: '2026-01-10',
    dependencies: [],
    deliverables: [
      { id: 'D001', name: '主框架.stp', type: '3D模型', status: 'completed', size: '15.2MB' },
      { id: 'D002', name: '主框架装配图.dwg', type: '装配图', status: 'in_progress', size: '8.5MB' },
    ],
    bomItems: 12,
    reviewStatus: 'pending',
    notes: 'Focus on assembly interference check',
  },
  {
    id: 'T002',
    title: 'Transmission mechanism design',
    titleCn: '传动机构设计',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineNo: '1号机',
    type: 'design',
    status: 'pending',
    priority: 'high',
    progress: 0,
    plannedStart: '2026-01-08',
    plannedEnd: '2026-01-12',
    actualStart: null,
    estimatedHours: 20,
    actualHours: 0,
    assignee: '张工',
    reviewer: '王组长',
    milestone: '设计评审',
    milestoneDate: '2026-01-10',
    dependencies: ['T001'],
    deliverables: [],
    bomItems: 8,
    reviewStatus: 'pending',
    notes: 'Wait for main frame completion',
  },
  {
    id: 'T003',
    title: 'Fixture detail drawing',
    titleCn: '治具详图出图',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineNo: '1号机',
    type: 'drawing',
    status: 'completed',
    priority: 'medium',
    progress: 100,
    plannedStart: '2025-12-28',
    plannedEnd: '2026-01-02',
    actualStart: '2025-12-28',
    actualEnd: '2026-01-01',
    estimatedHours: 16,
    actualHours: 14,
    assignee: '张工',
    reviewer: '王组长',
    milestone: null,
    milestoneDate: null,
    dependencies: [],
    deliverables: [
      { id: 'D003', name: '治具A.dwg', type: '零件图', status: 'completed', size: '2.1MB' },
      { id: 'D004', name: '治具B.dwg', type: '零件图', status: 'completed', size: '1.8MB' },
    ],
    bomItems: 4,
    reviewStatus: 'approved',
    notes: '',
  },
  {
    id: 'T004',
    title: 'EOL test bench frame design',
    titleCn: 'EOL测试台架框架设计',
    projectId: 'PJ250105002',
    projectName: 'EOL功能测试设备',
    machineNo: '2号机',
    type: 'design',
    status: 'in_progress',
    priority: 'medium',
    progress: 40,
    plannedStart: '2026-01-03',
    plannedEnd: '2026-01-10',
    actualStart: '2026-01-03',
    estimatedHours: 32,
    actualHours: 12,
    assignee: '张工',
    reviewer: '王组长',
    milestone: '方案评审',
    milestoneDate: '2026-01-12',
    dependencies: [],
    deliverables: [
      { id: 'D005', name: 'EOL台架.stp', type: '3D模型', status: 'in_progress', size: '22.4MB' },
    ],
    bomItems: 18,
    reviewStatus: 'pending',
    notes: 'Customer confirmed new requirements',
  },
  {
    id: 'T005',
    title: 'BOM confirmation and review',
    titleCn: 'BOM确认与评审',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineNo: '1号机',
    type: 'bom',
    status: 'blocked',
    priority: 'high',
    progress: 30,
    plannedStart: '2026-01-05',
    plannedEnd: '2026-01-07',
    actualStart: '2026-01-05',
    estimatedHours: 8,
    actualHours: 2,
    assignee: '张工',
    reviewer: '王组长',
    milestone: '物料齐套',
    milestoneDate: '2026-01-15',
    dependencies: ['T001'],
    deliverables: [
      { id: 'D006', name: 'BOM清单_v1.xlsx', type: 'BOM', status: 'in_progress', size: '156KB' },
    ],
    bomItems: 45,
    reviewStatus: 'pending',
    blockedReason: 'Waiting for supplier quotation on custom parts',
    notes: '3 custom parts need supplier confirmation',
  },
  {
    id: 'T006',
    title: 'ICT fixture mechanism design',
    titleCn: 'ICT治具机构设计',
    projectId: 'PJ250106003',
    projectName: 'ICT测试设备',
    machineNo: '3号机',
    type: 'design',
    status: 'pending',
    priority: 'low',
    progress: 0,
    plannedStart: '2026-01-10',
    plannedEnd: '2026-01-15',
    actualStart: null,
    estimatedHours: 24,
    actualHours: 0,
    assignee: '张工',
    reviewer: '王组长',
    milestone: '设计评审',
    milestoneDate: '2026-01-18',
    dependencies: [],
    deliverables: [],
    bomItems: 0,
    reviewStatus: 'pending',
    notes: 'Low priority, can be delayed if needed',
  },
  {
    id: 'T007',
    title: 'Design review preparation',
    titleCn: '设计评审准备',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machineNo: '1号机',
    type: 'review',
    status: 'pending',
    priority: 'high',
    progress: 0,
    plannedStart: '2026-01-09',
    plannedEnd: '2026-01-10',
    actualStart: null,
    estimatedHours: 4,
    actualHours: 0,
    assignee: '张工',
    reviewer: '王组长',
    milestone: '设计评审',
    milestoneDate: '2026-01-10',
    dependencies: ['T001', 'T002'],
    deliverables: [],
    bomItems: 0,
    reviewStatus: 'pending',
    notes: 'Prepare presentation materials',
  },
]

// Task type configs
const taskTypeConfigs = {
  design: { label: '结构设计', color: 'text-blue-400', bgColor: 'bg-blue-500/10', icon: Box },
  drawing: { label: '出图', color: 'text-emerald-400', bgColor: 'bg-emerald-500/10', icon: FileText },
  bom: { label: 'BOM', color: 'text-amber-400', bgColor: 'bg-amber-500/10', icon: Layers },
  review: { label: '评审', color: 'text-purple-400', bgColor: 'bg-purple-500/10', icon: ClipboardCheck },
}

// Status configs
const statusConfigs = {
  pending: { label: '待开始', icon: Circle, color: 'text-slate-400', bgColor: 'bg-slate-500/10' },
  in_progress: { label: '进行中', icon: PlayCircle, color: 'text-blue-400', bgColor: 'bg-blue-500/10' },
  blocked: { label: '已阻塞', icon: PauseCircle, color: 'text-red-400', bgColor: 'bg-red-500/10' },
  completed: { label: '已完成', icon: CheckCircle2, color: 'text-emerald-400', bgColor: 'bg-emerald-500/10' },
}

// Priority configs
const priorityConfigs = {
  low: { label: '低', color: 'text-slate-400', flagColor: 'text-slate-400' },
  medium: { label: '中', color: 'text-blue-400', flagColor: 'text-blue-400' },
  high: { label: '高', color: 'text-amber-400', flagColor: 'text-amber-400' },
  critical: { label: '紧急', color: 'text-red-400', flagColor: 'text-red-400' },
}

// View modes
const VIEW_MODES = {
  gantt: { id: 'gantt', label: '甘特图', icon: BarChart3 },
  calendar: { id: 'calendar', label: '日历', icon: CalendarDays },
  list: { id: 'list', label: '列表', icon: List },
}

// Stats Card Component
function StatsCard({ label, value, icon: Icon, color, onClick, active }) {
  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      whileTap={{ scale: 0.98 }}
      onClick={onClick}
      className={cn(
        'cursor-pointer rounded-xl border p-4 transition-all',
        active
          ? 'bg-primary/10 border-primary/30'
          : 'bg-surface-1/50 border-border hover:border-border/80'
      )}
    >
      <div className="flex items-center justify-between">
        <div>
          <p className="text-sm text-slate-400">{label}</p>
          <p className="text-2xl font-bold text-white mt-1">{value}</p>
        </div>
        <Icon className={cn('w-6 h-6', color)} />
      </div>
    </motion.div>
  )
}

// Task List Item Component (for list view)
function TaskListItem({ task, onClick, isSelected }) {
  const status = statusConfigs[task.status]
  const priority = priorityConfigs[task.priority]
  const taskType = taskTypeConfigs[task.type]
  const StatusIcon = status.icon
  const TypeIcon = taskType.icon

  const isOverdue = task.status !== 'completed' && new Date(task.plannedEnd) < new Date()
  const daysUntilDue = Math.ceil((new Date(task.plannedEnd) - new Date()) / (1000 * 60 * 60 * 24))

  return (
    <motion.div
      layout
      whileHover={{ scale: 1.005 }}
      onClick={() => onClick(task)}
      className={cn(
        'rounded-xl border p-4 cursor-pointer transition-all',
        isSelected
          ? 'bg-primary/10 border-primary/30'
          : task.status === 'blocked'
          ? 'bg-red-500/5 border-red-500/30 hover:border-red-500/50'
          : isOverdue
          ? 'bg-amber-500/5 border-amber-500/30 hover:border-amber-500/50'
          : 'bg-surface-1/50 border-border hover:border-border/80'
      )}
    >
      <div className="flex items-start gap-4">
        {/* Status Icon */}
        <div className={cn('mt-0.5 p-2 rounded-lg', status.bgColor)}>
          <StatusIcon className={cn('w-5 h-5', status.color)} />
        </div>

        {/* Content */}
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1">
            <Badge variant="outline" className={cn('text-xs', taskType.color, taskType.bgColor)}>
              <TypeIcon className="w-3 h-3 mr-1" />
              {taskType.label}
            </Badge>
            <Flag className={cn('w-3.5 h-3.5', priority.flagColor)} />
            <span className="text-xs text-slate-500">{task.machineNo}</span>
          </div>

          <h3 className="font-medium text-white mb-1">{task.titleCn}</h3>
          
          <div className="flex items-center gap-2 text-xs text-slate-400 mb-2">
            <Folder className="w-3 h-3" />
            <span className="text-accent truncate">{task.projectName}</span>
          </div>

          {/* Progress bar */}
          <div className="mb-2">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">进度</span>
              <span className="text-white">{task.progress}%</span>
            </div>
            <Progress value={task.progress} className="h-1.5" />
          </div>

          {/* Meta info */}
          <div className="flex items-center gap-4 text-xs text-slate-400">
            <span className={cn(
              'flex items-center gap-1',
              isOverdue ? 'text-red-400' : daysUntilDue <= 3 ? 'text-amber-400' : ''
            )}>
              <Calendar className="w-3 h-3" />
              {isOverdue ? (
                `逾期 ${Math.abs(daysUntilDue)} 天`
              ) : daysUntilDue <= 3 && daysUntilDue >= 0 ? (
                `剩余 ${daysUntilDue} 天`
              ) : (
                task.plannedEnd
              )}
            </span>
            <span className="flex items-center gap-1">
              <Timer className="w-3 h-3" />
              {task.actualHours}/{task.estimatedHours}h
            </span>
            {task.deliverables.length > 0 && (
              <span className="flex items-center gap-1">
                <FileText className="w-3 h-3" />
                {task.deliverables.length} 文件
              </span>
            )}
          </div>

          {/* Blocked reason */}
          {task.blockedReason && (
            <div className="mt-2 p-2 rounded-lg bg-red-500/10 text-xs text-red-300 flex items-center gap-2">
              <AlertTriangle className="w-3 h-3" />
              {task.blockedReason}
            </div>
          )}
        </div>

        {/* Arrow */}
        <ChevronRight className="w-5 h-5 text-slate-500" />
      </div>
    </motion.div>
  )
}

// Main Component
export default function EngineerWorkstation() {
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [viewMode, setViewMode] = useState('gantt')
  const [statusFilter, setStatusFilter] = useState('all')
  const [projectFilter, setProjectFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedTask, setSelectedTask] = useState(null)
  const [detailPanelOpen, setDetailPanelOpen] = useState(false)

  // Map backend status to frontend status
  const mapBackendStatus = (backendStatus) => {
    const statusMap = {
      'PENDING': 'pending',
      'ACCEPTED': 'pending',
      'IN_PROGRESS': 'in_progress',
      'COMPLETED': 'completed',
      'DONE': 'completed',
      'BLOCKED': 'blocked',
      'CANCELLED': 'cancelled',
    }
    return statusMap[backendStatus] || backendStatus?.toLowerCase() || 'pending'
  }

  // Map frontend status to backend status
  const mapFrontendStatus = (frontendStatus) => {
    const statusMap = {
      'pending': 'PENDING',
      'in_progress': 'IN_PROGRESS',
      'completed': 'COMPLETED',
      'blocked': 'BLOCKED',
    }
    return statusMap[frontendStatus] || frontendStatus?.toUpperCase()
  }

  // Load engineer tasks
  const loadTasks = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      const params = {
        page: 1,
        page_size: 100,
      }

      if (statusFilter !== 'all') {
        params.status = mapFrontendStatus(statusFilter)
      }

      if (projectFilter !== 'all') {
        params.project_id = parseInt(projectFilter)
      }

      if (searchQuery) {
        params.keyword = searchQuery
      }

      const response = await taskCenterApi.myTasks(params)
      const tasksData = response.data?.items || response.data || []

      // Transform backend tasks to frontend format
      const transformedTasks = tasksData.map(task => ({
        id: task.id?.toString(),
        title: task.title || '',
        titleCn: task.title || task.description || '',
        projectId: task.project_id?.toString() || '',
        projectName: task.project_name || '',
        machineNo: task.source_name || '',
        type: task.task_type?.toLowerCase() || 'design',
        status: mapBackendStatus(task.status),
        priority: task.priority?.toLowerCase() || 'medium',
        progress: task.progress || 0,
        plannedStart: task.plan_start_date || task.plan_start || '',
        plannedEnd: task.plan_end_date || task.deadline || '',
        actualStart: task.actual_start_date || null,
        actualEnd: task.actual_end_date || null,
        estimatedHours: task.estimated_hours || 0,
        actualHours: parseFloat(task.actual_hours || 0),
        assignee: task.assignee_name || '',
        reviewer: task.assigner_name || '',
        milestone: null,
        milestoneDate: null,
        dependencies: [],
        deliverables: [],
        bomItems: 0,
        reviewStatus: 'pending',
        notes: task.description || '',
      }))

      setTasks(transformedTasks)
    } catch (err) {
      console.error('Failed to load engineer tasks:', err)
      setError(err.response?.data?.detail || err.message || '加载任务列表失败')
      setTasks([]) // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false)
    }
  }, [statusFilter, projectFilter, searchQuery])

  // Load tasks when component mounts or filters change
  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  // Get unique projects for filter
  const projects = useMemo(() => {
    const projectSet = new Set(tasks.map(t => t.projectId))
    return Array.from(projectSet).map(id => {
      const task = tasks.find(t => t.projectId === id)
      return { id, name: task.projectName }
    })
  }, [tasks])

  // Filter tasks
  const filteredTasks = useMemo(() => {
    return tasks.filter(task => {
      if (statusFilter !== 'all' && task.status !== statusFilter) return false
      if (projectFilter !== 'all' && task.projectId !== projectFilter) return false
      if (searchQuery) {
        const query = searchQuery.toLowerCase()
        return (
          task.titleCn.toLowerCase().includes(query) ||
          task.projectName.toLowerCase().includes(query)
        )
      }
      return true
    })
  }, [tasks, statusFilter, projectFilter, searchQuery])

  // Calculate stats
  const stats = useMemo(() => {
    const today = new Date()
    const weekEnd = new Date(today)
    weekEnd.setDate(weekEnd.getDate() + 7)

    return {
      inProgress: tasks.filter(t => t.status === 'in_progress').length,
      pending: tasks.filter(t => t.status === 'pending').length,
      completed: tasks.filter(t => t.status === 'completed').length,
      dueThisWeek: tasks.filter(t => {
        const dueDate = new Date(t.plannedEnd)
        return t.status !== 'completed' && dueDate >= today && dueDate <= weekEnd
      }).length,
      overdue: tasks.filter(t => {
        return t.status !== 'completed' && new Date(t.plannedEnd) < today
      }).length,
    }
  }, [tasks])

  // Handle task selection
  const handleTaskSelect = (task) => {
    setSelectedTask(task)
    setDetailPanelOpen(true)
  }

  // Handle task update
  const handleTaskUpdate = (taskId, updates) => {
    setTasks(prev => prev.map(t => 
      t.id === taskId ? { ...t, ...updates } : t
    ))
    if (selectedTask?.id === taskId) {
      setSelectedTask(prev => ({ ...prev, ...updates }))
    }
  }

  // Close detail panel
  const handleCloseDetail = () => {
    setDetailPanelOpen(false)
    setTimeout(() => setSelectedTask(null), 300)
  }

  if (loading) {
    return (
      <div className="space-y-6">
        <PageHeader
          title="我的工作台"
          description="机械设计任务管理 · 时间轴视图"
        />
        <div className="text-center py-16">
          <div className="text-slate-400">加载中...</div>
        </div>
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
        title="我的工作台"
        description="机械设计任务管理 · 时间轴视图"
        actions={
          <div className="flex gap-2">
            <Button variant="outline" size="sm">
              <Upload className="w-4 h-4 mr-1" />
              上传文件
            </Button>
            <Button size="sm">
              <Send className="w-4 h-4 mr-1" />
              申请评审
            </Button>
          </div>
        }
      />

      {/* Stats Cards */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-5 gap-4">
        <StatsCard
          label="进行中"
          value={stats.inProgress}
          icon={PlayCircle}
          color="text-blue-400"
          onClick={() => setStatusFilter(statusFilter === 'in_progress' ? 'all' : 'in_progress')}
          active={statusFilter === 'in_progress'}
        />
        <StatsCard
          label="待开始"
          value={stats.pending}
          icon={Circle}
          color="text-slate-400"
          onClick={() => setStatusFilter(statusFilter === 'pending' ? 'all' : 'pending')}
          active={statusFilter === 'pending'}
        />
        <StatsCard
          label="已完成"
          value={stats.completed}
          icon={CheckCircle2}
          color="text-emerald-400"
          onClick={() => setStatusFilter(statusFilter === 'completed' ? 'all' : 'completed')}
          active={statusFilter === 'completed'}
        />
        <StatsCard
          label="本周到期"
          value={stats.dueThisWeek}
          icon={Calendar}
          color="text-amber-400"
        />
        <StatsCard
          label="已逾期"
          value={stats.overdue}
          icon={AlertTriangle}
          color="text-red-400"
        />
      </motion.div>

      {/* View Toggle & Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              {/* View Mode Toggle */}
              <div className="flex items-center gap-1 p-1 bg-surface-2 rounded-lg">
                {Object.values(VIEW_MODES).map((mode) => (
                  <Button
                    key={mode.id}
                    variant={viewMode === mode.id ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode(mode.id)}
                    className="gap-2"
                  >
                    <mode.icon className="w-4 h-4" />
                    {mode.label}
                  </Button>
                ))}
              </div>

              {/* Filters */}
              <div className="flex items-center gap-3 flex-wrap">
                {/* Project Filter */}
                <select
                  value={projectFilter}
                  onChange={(e) => setProjectFilter(e.target.value)}
                  className="h-9 px-3 rounded-lg bg-surface-2 border border-border text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="all">全部项目</option>
                  {projects.map(p => (
                    <option key={p.id} value={p.id}>{p.name}</option>
                  ))}
                </select>

                {/* Status Filter */}
                <select
                  value={statusFilter}
                  onChange={(e) => setStatusFilter(e.target.value)}
                  className="h-9 px-3 rounded-lg bg-surface-2 border border-border text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
                >
                  <option value="all">全部状态</option>
                  <option value="in_progress">进行中</option>
                  <option value="pending">待开始</option>
                  <option value="blocked">已阻塞</option>
                  <option value="completed">已完成</option>
                </select>

                {/* Search */}
                <div className="relative">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索任务..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9 w-48"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Main Content Area */}
      <motion.div variants={fadeIn} className="relative">
        <div className={cn(
          'transition-all duration-300',
          detailPanelOpen ? 'mr-96' : ''
        )}>
          {/* Gantt View */}
          {viewMode === 'gantt' && (
            <GanttChart
              tasks={filteredTasks}
              onTaskSelect={handleTaskSelect}
              selectedTaskId={selectedTask?.id}
            />
          )}

          {/* Calendar View */}
          {viewMode === 'calendar' && (
            <CalendarView
              tasks={filteredTasks}
              onTaskSelect={handleTaskSelect}
              selectedTaskId={selectedTask?.id}
            />
          )}

          {/* List View */}
          {viewMode === 'list' && (
            <div className="space-y-3">
              {filteredTasks.map(task => (
                <TaskListItem
                  key={task.id}
                  task={task}
                  onClick={handleTaskSelect}
                  isSelected={selectedTask?.id === task.id}
                />
              ))}

              {filteredTasks.length === 0 && (
                <div className="text-center py-16">
                  <Box className="w-16 h-16 mx-auto text-slate-600 mb-4" />
                  <h3 className="text-lg font-medium text-slate-400">暂无任务</h3>
                  <p className="text-sm text-slate-500 mt-1">
                    {searchQuery || statusFilter !== 'all' || projectFilter !== 'all'
                      ? '没有符合条件的任务'
                      : '当前没有分配给您的设计任务'}
                  </p>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Task Detail Panel */}
        <AnimatePresence>
          {detailPanelOpen && selectedTask && (
            <TaskDetailPanel
              task={selectedTask}
              onClose={handleCloseDetail}
              onUpdate={handleTaskUpdate}
              statusConfigs={statusConfigs}
              priorityConfigs={priorityConfigs}
              taskTypeConfigs={taskTypeConfigs}
            />
          )}
        </AnimatePresence>
      </motion.div>
    </motion.div>
  )
}

