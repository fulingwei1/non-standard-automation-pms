import { useState, useMemo, useEffect, useCallback } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import {
  ListTodo,
  Calendar,
  Clock,
  CheckCircle2,
  Circle,
  PlayCircle,
  PauseCircle,
  AlertTriangle,
  Filter,
  Search,
  Plus,
  ChevronRight,
  Flag,
  User,
  Folder,
  Timer,
  MoreHorizontal,
  ArrowRight,
  Zap,
  Wrench,
  Package,
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
import { Input } from '../components/ui/input'
import { Badge } from '../components/ui/badge'
import { Progress } from '../components/ui/progress'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'
import { getRoleInfo, isEngineerRole } from '../lib/roleConfig'
import { progressApi, projectApi, taskCenterApi } from '../services/api'

// Mock task data for engineers/managers
const mockTasks = [
  {
    id: 'T001',
    title: 'BMS老化设备 - 机械结构设计',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    status: 'in_progress',
    priority: 'high',
    progress: 65,
    assignee: '张工',
    dueDate: '2026-01-08',
    estimatedHours: 40,
    actualHours: 26,
    tags: ['机械设计', '3D建模'],
    subTasks: [
      { id: 'ST001', title: '框架结构设计', completed: true },
      { id: 'ST002', title: '传动机构设计', completed: true },
      { id: 'ST003', title: '工装夹具设计', completed: false },
      { id: 'ST004', title: '工程图纸输出', completed: false },
    ],
    blockedBy: null,
  },
  {
    id: 'T002',
    title: 'BMS老化设备 - BOM整理发布',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    status: 'pending',
    priority: 'high',
    progress: 0,
    assignee: '张工',
    dueDate: '2026-01-10',
    estimatedHours: 8,
    actualHours: 0,
    tags: ['BOM'],
    subTasks: [],
    blockedBy: 'T001',
  },
  {
    id: 'T003',
    title: 'EOL测试设备 - 电气原理图',
    projectId: 'PJ250105002',
    projectName: 'EOL功能测试设备',
    status: 'in_progress',
    priority: 'medium',
    progress: 80,
    assignee: '李工',
    dueDate: '2026-01-06',
    estimatedHours: 24,
    actualHours: 19,
    tags: ['电气设计'],
    subTasks: [],
    blockedBy: null,
  },
  {
    id: 'T004',
    title: 'ICT测试设备 - PLC程序框架',
    projectId: 'PJ250106003',
    projectName: 'ICT测试设备',
    status: 'blocked',
    priority: 'high',
    progress: 30,
    assignee: '王工',
    dueDate: '2026-01-12',
    estimatedHours: 32,
    actualHours: 10,
    tags: ['PLC编程', '软件'],
    subTasks: [],
    blockedBy: null,
    blockReason: '等待硬件选型确认',
  },
  {
    id: 'T005',
    title: 'BMS老化设备 - 设计评审',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    status: 'completed',
    priority: 'medium',
    progress: 100,
    assignee: '张工',
    dueDate: '2026-01-03',
    completedDate: '2026-01-03',
    estimatedHours: 4,
    actualHours: 3,
    tags: ['评审'],
    subTasks: [],
    blockedBy: null,
  },
]

// Mock assembly tasks for workers (装配技工专用任务)
const mockAssemblyTasks = [
  {
    id: 'AT001',
    title: '框架底座装配',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machine: '1号机',
    status: 'in_progress',
    priority: 'high',
    progress: 70,
    dueDate: '2026-01-05',
    estimatedHours: 8,
    actualHours: 5.5,
    location: 'A区-工位3',
    parts: [
      { name: '铝型材框架 40x40', qty: 12, ready: true },
      { name: '角码连接件', qty: 24, ready: true },
      { name: '脚轮组件', qty: 4, ready: true },
      { name: '调平脚', qty: 4, ready: false },
    ],
    tools: ['内六角扳手套装', '气动螺丝刀', '水平仪'],
    instructions: [
      { step: 1, desc: '检查物料清单，确认零件齐全', done: true },
      { step: 2, desc: '按图纸搭建框架底座', done: true },
      { step: 3, desc: '安装脚轮和调平脚', done: false },
      { step: 4, desc: '调整水平，锁紧螺栓', done: false },
    ],
    notes: '注意框架方正度，误差控制在±1mm',
  },
  {
    id: 'AT002',
    title: '传动机构安装',
    projectId: 'PJ250108001',
    projectName: 'BMS老化测试设备',
    machine: '1号机',
    status: 'pending',
    priority: 'high',
    progress: 0,
    dueDate: '2026-01-06',
    estimatedHours: 6,
    actualHours: 0,
    location: 'A区-工位3',
    parts: [
      { name: '滚珠丝杆 1605', qty: 2, ready: true },
      { name: '直线导轨 HGH20', qty: 4, ready: true },
      { name: '联轴器', qty: 2, ready: true },
    ],
    tools: ['扭力扳手', '百分表', '塞尺'],
    instructions: [
      { step: 1, desc: '安装直线导轨，检查平行度', done: false },
      { step: 2, desc: '安装丝杆支撑座', done: false },
      { step: 3, desc: '装配丝杆和滑块', done: false },
      { step: 4, desc: '测试运动顺畅度', done: false },
    ],
    blockedBy: 'AT001',
    notes: '丝杆安装需确保同心度',
  },
  {
    id: 'AT003',
    title: '电气接线',
    projectId: 'PJ250105002',
    projectName: 'EOL功能测试设备',
    machine: '2号机',
    status: 'in_progress',
    priority: 'medium',
    progress: 40,
    dueDate: '2026-01-05',
    estimatedHours: 4,
    actualHours: 1.5,
    location: 'B区-工位1',
    parts: [
      { name: '控制柜 800x600', qty: 1, ready: true },
      { name: '线缆套装', qty: 1, ready: true },
      { name: '端子排', qty: 10, ready: true },
    ],
    tools: ['剥线钳', '压线钳', '万用表'],
    instructions: [
      { step: 1, desc: '安装控制柜', done: true },
      { step: 2, desc: '布线走线槽', done: true },
      { step: 3, desc: '接线端子', done: false },
      { step: 4, desc: '线号标识', done: false },
    ],
    notes: '注意接线顺序，参照电气图纸',
  },
  {
    id: 'AT004',
    title: '气路安装调试',
    projectId: 'PJ250106003',
    projectName: 'ICT测试设备',
    machine: '3号机',
    status: 'blocked',
    priority: 'medium',
    progress: 0,
    dueDate: '2026-01-08',
    estimatedHours: 3,
    actualHours: 0,
    location: 'C区-工位2',
    parts: [
      { name: '气缸 SC50x100', qty: 4, ready: false },
      { name: 'PU气管 8mm', qty: 20, ready: true },
    ],
    tools: ['切管器', '气动快插接头'],
    instructions: [],
    blockReason: '气缸未到货，预计1月7日到',
    notes: '',
  },
  {
    id: 'AT005',
    title: '设备清洁打标',
    projectId: 'PJ241220001',
    projectName: '烧录测试设备',
    machine: '4号机',
    status: 'completed',
    priority: 'low',
    progress: 100,
    dueDate: '2026-01-03',
    completedDate: '2026-01-03',
    estimatedHours: 2,
    actualHours: 1.5,
    location: 'D区-工位4',
    parts: [],
    tools: ['清洁剂', '标签打印机'],
    instructions: [],
    notes: '设备已出货',
  },
]

const statusConfigs = {
  pending: {
    label: '待开始',
    icon: Circle,
    color: 'text-slate-400',
    bgColor: 'bg-slate-500/10',
  },
  in_progress: {
    label: '进行中',
    icon: PlayCircle,
    color: 'text-blue-400',
    bgColor: 'bg-blue-500/10',
  },
  blocked: {
    label: '阻塞',
    icon: PauseCircle,
    color: 'text-red-400',
    bgColor: 'bg-red-500/10',
  },
  completed: {
    label: '已完成',
    icon: CheckCircle2,
    color: 'text-emerald-400',
    bgColor: 'bg-emerald-500/10',
  },
}

const priorityConfigs = {
  low: { label: '低', color: 'text-slate-400', flagColor: 'text-slate-400' },
  medium: { label: '中', color: 'text-blue-400', flagColor: 'text-blue-400' },
  high: { label: '高', color: 'text-amber-400', flagColor: 'text-amber-400' },
  critical: { label: '紧急', color: 'text-red-400', flagColor: 'text-red-400' },
}

// Assembly task card for workers (装配技工专用任务卡片)
function AssemblyTaskCard({ task, onStatusChange, onStepToggle }) {
  const [expanded, setExpanded] = useState(true)
  const status = statusConfigs[task.status]
  const priority = priorityConfigs[task.priority]
  const StatusIcon = status.icon

  const isOverdue =
    task.status !== 'completed' && new Date(task.dueDate) < new Date()

  const partsReady = task.parts?.filter(p => p.ready).length || 0
  const partsTotal = task.parts?.length || 0
  const stepsCompleted = task.instructions?.filter(s => s.done).length || 0
  const stepsTotal = task.instructions?.length || 0

  return (
    <motion.div
      layout
      className={cn(
        'rounded-2xl border overflow-hidden',
        task.status === 'blocked'
          ? 'bg-red-500/5 border-red-500/30'
          : isOverdue
          ? 'bg-amber-500/5 border-amber-500/30'
          : task.status === 'in_progress'
          ? 'bg-blue-500/5 border-blue-500/30'
          : 'bg-surface-1 border-border'
      )}
    >
      {/* Header - larger touch target for workers */}
      <div className="p-5 pb-3">
        <div className="flex items-start gap-4">
          <button
            onClick={() => {
              if (task.status === 'pending') onStatusChange(task.id, 'in_progress')
              else if (task.status === 'in_progress' && stepsCompleted === stepsTotal) 
                onStatusChange(task.id, 'completed')
            }}
            className={cn(
              'p-3 rounded-xl transition-colors',
              status.bgColor,
              task.status !== 'blocked' && 'hover:bg-accent/20 active:scale-95'
            )}
          >
            <StatusIcon className={cn('w-8 h-8', status.color)} />
          </button>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Badge 
                variant="outline" 
                className={cn('text-xs', priority.color, 'border-current')}
              >
                {priority.label}优先级
              </Badge>
              <Badge variant="secondary" className="text-xs">
                {task.machine}
              </Badge>
            </div>
            <h2 className="text-xl font-bold text-white mb-1">{task.title}</h2>
            <p className="text-sm text-slate-400">
              {task.projectName} · {task.location}
            </p>
          </div>
        </div>

        {/* Block Reason */}
        {task.blockReason && (
          <div className="mt-4 p-4 rounded-xl bg-red-500/10 text-sm text-red-300 flex items-center gap-3">
            <AlertTriangle className="w-5 h-5 flex-shrink-0" />
            <span>{task.blockReason}</span>
          </div>
        )}

        {/* Progress */}
        {task.status === 'in_progress' && (
          <div className="mt-4">
            <div className="flex items-center justify-between text-sm mb-2">
              <span className="text-slate-400">进度</span>
              <span className="text-white font-medium">{stepsCompleted}/{stepsTotal} 步骤</span>
            </div>
            <Progress value={(stepsCompleted / stepsTotal) * 100 || 0} className="h-2" />
          </div>
        )}

        {/* Time info */}
        <div className="flex items-center gap-6 mt-4 text-sm">
          <span
            className={cn(
              'flex items-center gap-2',
              isOverdue ? 'text-red-400' : 'text-slate-400'
            )}
          >
            <Calendar className="w-4 h-4" />
            截止: {task.dueDate}
          </span>
          <span className="flex items-center gap-2 text-slate-400">
            <Timer className="w-4 h-4" />
            {task.actualHours}/{task.estimatedHours}h
          </span>
        </div>
      </div>

      {/* Parts checklist */}
      {task.parts && task.parts.length > 0 && (
        <div className="px-5 py-4 border-t border-border/50">
          <button
            onClick={() => setExpanded(!expanded)}
            className="w-full flex items-center justify-between text-sm font-medium text-white"
          >
            <span className="flex items-center gap-2">
              <Package className="w-4 h-4 text-blue-400" />
              物料准备 ({partsReady}/{partsTotal})
            </span>
            <motion.span animate={{ rotate: expanded ? 180 : 0 }}>
              <ChevronRight className="w-5 h-5 rotate-90" />
            </motion.span>
          </button>

          <AnimatePresence>
            {expanded && (
              <motion.div
                initial={{ height: 0, opacity: 0 }}
                animate={{ height: 'auto', opacity: 1 }}
                exit={{ height: 0, opacity: 0 }}
                className="overflow-hidden"
              >
                <div className="grid grid-cols-2 gap-2 mt-3">
                  {task.parts.map((part, idx) => (
                    <div
                      key={idx}
                      className={cn(
                        'flex items-center gap-2 p-2 rounded-lg text-sm',
                        part.ready ? 'bg-emerald-500/10' : 'bg-amber-500/10'
                      )}
                    >
                      <div
                        className={cn(
                          'w-5 h-5 rounded-full flex items-center justify-center',
                          part.ready ? 'bg-emerald-500' : 'bg-amber-500'
                        )}
                      >
                        {part.ready ? (
                          <CheckCircle2 className="w-3 h-3 text-white" />
                        ) : (
                          <Clock className="w-3 h-3 text-white" />
                        )}
                      </div>
                      <span className={part.ready ? 'text-emerald-300' : 'text-amber-300'}>
                        {part.name} x{part.qty}
                      </span>
                    </div>
                  ))}
                </div>
              </motion.div>
            )}
          </AnimatePresence>
        </div>
      )}

      {/* Work instructions */}
      {task.instructions && task.instructions.length > 0 && (
        <div className="px-5 py-4 border-t border-border/50">
          <h4 className="flex items-center gap-2 text-sm font-medium text-white mb-3">
            <Wrench className="w-4 h-4 text-violet-400" />
            作业步骤
          </h4>
          <div className="space-y-2">
            {task.instructions.map((step) => (
              <button
                key={step.step}
                onClick={() => onStepToggle(task.id, step.step)}
                className={cn(
                  'w-full flex items-center gap-3 p-3 rounded-xl text-left transition-colors',
                  step.done
                    ? 'bg-emerald-500/10'
                    : 'bg-surface-2/50 hover:bg-surface-2'
                )}
              >
                <div
                  className={cn(
                    'w-7 h-7 rounded-full border-2 flex items-center justify-center flex-shrink-0',
                    step.done
                      ? 'bg-emerald-500 border-emerald-500'
                      : 'border-slate-500'
                  )}
                >
                  {step.done ? (
                    <CheckCircle2 className="w-4 h-4 text-white" />
                  ) : (
                    <span className="text-xs text-slate-400">{step.step}</span>
                  )}
                </div>
                <span
                  className={cn(
                    'text-sm',
                    step.done
                      ? 'text-emerald-300 line-through'
                      : 'text-white'
                  )}
                >
                  {step.desc}
                </span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Notes */}
      {task.notes && (
        <div className="px-5 py-3 bg-amber-500/5 border-t border-amber-500/20">
          <p className="text-sm text-amber-300 flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 flex-shrink-0 mt-0.5" />
            {task.notes}
          </p>
        </div>
      )}

      {/* Tools needed */}
      {task.tools && task.tools.length > 0 && (
        <div className="px-5 py-3 bg-surface-2/30 border-t border-border/30">
          <p className="text-xs text-slate-400">
            <span className="font-medium">所需工具：</span>
            {task.tools.join('、')}
          </p>
        </div>
      )}
    </motion.div>
  )
}

function TaskCard({ task, onStatusChange }) {
  const [expanded, setExpanded] = useState(false)
  const status = statusConfigs[task.status]
  const priority = priorityConfigs[task.priority]
  const StatusIcon = status.icon

  const isOverdue =
    task.status !== 'completed' && new Date(task.dueDate) < new Date()

  const daysUntilDue = Math.ceil(
    (new Date(task.dueDate) - new Date()) / (1000 * 60 * 60 * 24)
  )

  return (
    <motion.div
      layout
      whileHover={{ scale: 1.005 }}
      className={cn(
        'rounded-xl border overflow-hidden transition-colors',
        task.status === 'blocked'
          ? 'bg-red-500/5 border-red-500/30'
          : isOverdue
          ? 'bg-amber-500/5 border-amber-500/30'
          : 'bg-surface-1 border-border'
      )}
    >
      <div className="p-4">
        {/* Header */}
        <div className="flex items-start gap-3">
          <button
            onClick={() => {
              if (task.status === 'pending') onStatusChange(task.id, 'in_progress')
              else if (task.status === 'in_progress') onStatusChange(task.id, 'completed')
            }}
            className={cn(
              'mt-0.5 p-1 rounded-lg transition-colors',
              status.bgColor,
              task.status !== 'blocked' && 'hover:bg-accent/20'
            )}
          >
            <StatusIcon className={cn('w-5 h-5', status.color)} />
          </button>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <Flag className={cn('w-3.5 h-3.5', priority.flagColor)} />
              <span className="font-mono text-xs text-slate-500">{task.id}</span>
            </div>
            <h3 className="font-medium text-white mb-1">{task.title}</h3>
            <div className="flex items-center gap-2 text-xs text-slate-400">
              <Folder className="w-3 h-3" />
              <span className="text-accent">{task.projectId}</span>
              <span>·</span>
              <span className="truncate">{task.projectName}</span>
            </div>
          </div>

          <Button variant="ghost" size="sm" className="h-7 w-7 p-0">
            <MoreHorizontal className="w-4 h-4" />
          </Button>
        </div>

        {/* Block Reason */}
        {task.blockReason && (
          <div className="mt-3 p-2 rounded-lg bg-red-500/10 text-xs text-red-300 flex items-center gap-2">
            <AlertTriangle className="w-3 h-3" />
            {task.blockReason}
          </div>
        )}

        {/* Progress */}
        {task.status === 'in_progress' && (
          <div className="mt-3">
            <div className="flex items-center justify-between text-xs mb-1">
              <span className="text-slate-400">进度</span>
              <span className="text-white">{task.progress}%</span>
            </div>
            <Progress value={task.progress} className="h-1.5" />
          </div>
        )}

        {/* Meta Info */}
        <div className="flex items-center gap-4 mt-3 text-xs">
          <span
            className={cn(
              'flex items-center gap-1',
              isOverdue ? 'text-red-400' : 'text-slate-400'
            )}
          >
            <Calendar className="w-3 h-3" />
            {isOverdue ? (
              <>已逾期 {Math.abs(daysUntilDue)} 天</>
            ) : daysUntilDue <= 3 ? (
              <span className="text-amber-400">剩余 {daysUntilDue} 天</span>
            ) : (
              task.dueDate
            )}
          </span>
          <span className="flex items-center gap-1 text-slate-400">
            <Timer className="w-3 h-3" />
            {task.actualHours}/{task.estimatedHours}h
          </span>
        </div>

        {/* Tags */}
        {task.tags.length > 0 && (
          <div className="flex flex-wrap gap-1 mt-3">
            {task.tags.map((tag) => (
              <Badge key={tag} variant="secondary" className="text-[10px] px-1.5">
                {tag}
              </Badge>
            ))}
          </div>
        )}

        {/* Subtasks */}
        {task.subTasks.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border/50">
            <button
              onClick={() => setExpanded(!expanded)}
              className="w-full flex items-center justify-between text-xs text-slate-400 hover:text-white transition-colors"
            >
              <span>子任务 ({task.subTasks.filter((st) => st.completed).length}/{task.subTasks.length})</span>
              <motion.span animate={{ rotate: expanded ? 90 : 0 }}>
                <ChevronRight className="w-4 h-4" />
              </motion.span>
            </button>

            <AnimatePresence>
              {expanded && (
                <motion.div
                  initial={{ height: 0, opacity: 0 }}
                  animate={{ height: 'auto', opacity: 1 }}
                  exit={{ height: 0, opacity: 0 }}
                  className="overflow-hidden"
                >
                  <div className="space-y-1 mt-2">
                    {task.subTasks.map((subTask) => (
                      <div
                        key={subTask.id}
                        className="flex items-center gap-2 text-xs"
                      >
                        <div
                          className={cn(
                            'w-3.5 h-3.5 rounded-full border flex items-center justify-center',
                            subTask.completed
                              ? 'bg-emerald-500 border-emerald-500'
                              : 'border-slate-500'
                          )}
                        >
                          {subTask.completed && (
                            <CheckCircle2 className="w-2.5 h-2.5 text-white" />
                          )}
                        </div>
                        <span
                          className={cn(
                            subTask.completed
                              ? 'text-slate-500 line-through'
                              : 'text-slate-300'
                          )}
                        >
                          {subTask.title}
                        </span>
                      </div>
                    ))}
                  </div>
                </motion.div>
              )}
            </AnimatePresence>
          </div>
        )}

        {/* Blocked By */}
        {task.blockedBy && (
          <div className="mt-3 p-2 rounded-lg bg-surface-2/50 text-xs flex items-center gap-2 text-slate-400">
            <ArrowRight className="w-3 h-3" />
            依赖任务：<span className="text-accent">{task.blockedBy}</span>
          </div>
        )}
      </div>
    </motion.div>
  )
}

export default function TaskCenter() {
  // Get current user role
  const currentUser = JSON.parse(localStorage.getItem('user') || '{}')
  const role = currentUser?.role || 'admin'
  const userId = currentUser?.id
  const isWorker = isEngineerRole(role) || role === 'assembler'
  const roleInfo = getRoleInfo(role)

  // State management
  const [tasks, setTasks] = useState([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [viewMode, setViewMode] = useState('list') // list | kanban
  const [statusFilter, setStatusFilter] = useState('all')
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedProject, setSelectedProject] = useState(null)
  const [projects, setProjects] = useState([])

  // Load projects for filtering
  useEffect(() => {
    const loadProjects = async () => {
      try {
        const response = await projectApi.list({ page_size: 100 })
        // Handle PaginatedResponse format
        const data = response.data || response
        setProjects(data.items || data || [])
      } catch (err) {
        console.error('Failed to load projects:', err)
        setProjects([])
      }
    }
    loadProjects()
  }, [])

  // Load tasks from API
  const loadTasks = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)

      // Use task-center API to get unified tasks
      const params = {
        page: 1,
        page_size: 100,
      }

      // Filter by project if selected
      if (selectedProject) {
        params.project_id = selectedProject
      }

      // Filter by status
      if (statusFilter !== 'all') {
        // Map frontend status to backend status
        const statusMap = {
          'pending': 'PENDING',
          'in_progress': 'IN_PROGRESS',
          'blocked': 'BLOCKED',
          'completed': 'COMPLETED',
        }
        params.status = statusMap[statusFilter] || statusFilter
      }

      // Search keyword
      if (searchQuery) {
        params.keyword = searchQuery
      }

      // Fetch tasks from task-center API (aggregates all task sources)
      const response = await taskCenterApi.getMyTasks(params)
      // Handle PaginatedResponse format
      const data = response.data || response
      const tasksData = data.items || data || []
      
      // Transform backend task format to frontend format
      const transformedTasks = tasksData.map(task => {
        const statusMap = {
          'PENDING': 'pending',
          'ACCEPTED': 'pending',
          'IN_PROGRESS': 'in_progress',
          'BLOCKED': 'blocked',
          'COMPLETED': 'completed',
          'CLOSED': 'completed',
        }
        return {
          id: task.id?.toString() || task.task_code,
          title: task.title || '',
          projectId: task.project_id?.toString(),
          projectName: task.project_name || '',
          status: statusMap[task.status] || task.status?.toLowerCase() || 'pending',
          priority: task.priority?.toLowerCase() || 'medium',
          progress: task.progress || 0,
          assignee: task.assignee_name || '',
          dueDate: task.deadline || task.plan_end_date || '',
          estimatedHours: task.estimated_hours || 0,
          actualHours: task.actual_hours || 0,
          tags: task.tags || [],
          subTasks: [],
          blockedBy: null,
          sourceType: task.source_type,
          sourceName: task.source_name,
        }
      })
      
      setTasks(transformedTasks)
    } catch (err) {
      console.error('Failed to load tasks:', err)
      setError(err.response?.data?.detail || err.message || '加载任务失败')
      setTasks([]) // 不再使用mock数据，显示空列表
    } finally {
      setLoading(false)
    }
  }, [statusFilter, searchQuery, selectedProject, isWorker, userId])

  // Load tasks when filters change
  useEffect(() => {
    loadTasks()
  }, [loadTasks])

  // Helper function to map backend status to frontend status
  const mapBackendStatusToFrontend = (backendStatus) => {
    const statusMap = {
      'PENDING': 'pending',
      'ACCEPTED': 'pending',
      'IN_PROGRESS': 'in_progress',
      'BLOCKED': 'blocked',
      'COMPLETED': 'completed',
      'CLOSED': 'completed',
    }
    return statusMap[backendStatus] || backendStatus?.toLowerCase() || 'pending'
  }

  // Helper function to map frontend status to backend status
  const mapFrontendStatusToBackend = (frontendStatus) => {
    const statusMap = {
      'pending': 'PENDING',
      'in_progress': 'IN_PROGRESS',
      'blocked': 'BLOCKED',
      'completed': 'COMPLETED',
    }
    return statusMap[frontendStatus] || frontendStatus?.toUpperCase()
  }

  const filteredTasks = tasks.filter((task) => {
    if (statusFilter !== 'all' && task.status !== statusFilter) return false
    if (searchQuery && !task.title.toLowerCase().includes(searchQuery.toLowerCase())) {
      return false
    }
    return true
  })

  const handleStatusChange = async (taskId, newStatus) => {
    try {
      const taskIdNum = parseInt(taskId)
      const backendStatus = mapFrontendStatusToBackend(newStatus)
      
      // Update task status via task-center API
      if (newStatus === 'completed') {
        await taskCenterApi.completeTask(taskIdNum)
      } else {
        await taskCenterApi.updateTask(taskIdNum, {
          status: backendStatus,
          progress: newStatus === 'completed' ? 100 : undefined,
        })
      }

      // Refresh tasks list
      await loadTasks()
    } catch (err) {
      console.error('Failed to update task status:', err)
      alert('更新任务状态失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const handleStepToggle = async (taskId, stepNumber) => {
    try {
      const task = tasks.find(t => t.id === taskId)
      if (!task) return

      const newInstructions = task.instructions.map((step) =>
        step.step === stepNumber ? { ...step, done: !step.done } : step
      )
      const stepsCompleted = newInstructions.filter((s) => s.done).length
      const progress = task.instructions.length > 0 
        ? Math.round((stepsCompleted / task.instructions.length) * 100)
        : task.progress

      // Update task progress via API
      const taskIdNum = parseInt(taskId.replace('T', ''))
      await progressApi.tasks.updateProgress(taskIdNum, {
        progress_percent: progress,
        update_note: `更新步骤 ${stepNumber} 的状态`,
      })

      // Update local state
      setTasks((prev) =>
        prev.map((t) => {
          if (t.id !== taskId) return t
          return { ...t, instructions: newInstructions, progress }
        })
      )
    } catch (err) {
      console.error('Failed to update task step:', err)
      alert('更新任务步骤失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  // Stats
  const stats = {
    total: tasks.length,
    inProgress: tasks.filter((t) => t.status === 'in_progress').length,
    blocked: tasks.filter((t) => t.status === 'blocked').length,
    completed: tasks.filter((t) => t.status === 'completed').length,
    overdue: tasks.filter(
      (t) => t.status !== 'completed' && new Date(t.dueDate) < new Date()
    ).length,
  }

  // Worker-specific view (装配技工专用界面)
  if (role === 'assembler') {
    return (
      <motion.div
        variants={staggerContainer}
        initial="hidden"
        animate="show"
        className="space-y-6"
      >
        <PageHeader
          title="我的装配任务"
          description={`今日待完成 ${stats.inProgress} 项，共 ${stats.total} 项任务`}
        />

        {/* Quick stats for workers */}
        <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
          {[
            { label: '进行中', value: stats.inProgress, icon: PlayCircle, color: 'text-blue-400', bg: 'bg-blue-500/10' },
            { label: '待开始', value: tasks.filter(t => t.status === 'pending').length, icon: Circle, color: 'text-slate-400', bg: 'bg-slate-500/10' },
            { label: '已阻塞', value: stats.blocked, icon: AlertTriangle, color: 'text-red-400', bg: 'bg-red-500/10' },
            { label: '已完成', value: stats.completed, icon: CheckCircle2, color: 'text-emerald-400', bg: 'bg-emerald-500/10' },
          ].map((stat, index) => (
            <Card key={index} className={cn('bg-surface-1/50', stat.bg)}>
              <CardContent className="p-4">
                <div className="flex items-center justify-between">
                  <div>
                    <p className="text-sm text-slate-400">{stat.label}</p>
                    <p className="text-3xl font-bold text-white mt-1">{stat.value}</p>
                  </div>
                  <stat.icon className={cn('w-8 h-8', stat.color)} />
                </div>
              </CardContent>
            </Card>
          ))}
        </motion.div>

        {/* Status tabs */}
        <motion.div variants={fadeIn}>
          <div className="flex gap-2 overflow-x-auto pb-2">
            {[
              { value: 'all', label: '全部任务' },
              { value: 'in_progress', label: '进行中' },
              { value: 'pending', label: '待开始' },
              { value: 'blocked', label: '已阻塞' },
              { value: 'completed', label: '已完成' },
            ].map((filter) => (
              <Button
                key={filter.value}
                variant={statusFilter === filter.value ? 'default' : 'secondary'}
                size="lg"
                onClick={() => setStatusFilter(filter.value)}
                className="whitespace-nowrap"
              >
                {filter.label}
              </Button>
            ))}
          </div>
        </motion.div>

        {/* Assembly tasks list */}
        <motion.div variants={fadeIn} className="space-y-4">
          {filteredTasks.map((task) => (
            <AssemblyTaskCard
              key={task.id}
              task={task}
              onStatusChange={handleStatusChange}
              onStepToggle={handleStepToggle}
            />
          ))}
        </motion.div>

        {/* Empty state */}
        {filteredTasks.length === 0 && (
          <motion.div variants={fadeIn} className="text-center py-16">
            <Wrench className="w-16 h-16 mx-auto text-slate-600 mb-4" />
            <h3 className="text-lg font-medium text-slate-400">暂无任务</h3>
            <p className="text-sm text-slate-500 mt-1">
              {statusFilter !== 'all' ? '没有符合条件的任务' : '今日没有分配的装配任务'}
            </p>
          </motion.div>
        )}
      </motion.div>
    )
  }

  // Regular view for managers and engineers
  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <PageHeader
        title="任务中心"
        description={isWorker ? '查看和更新您的任务进度' : '管理团队任务，跟踪进度'}
        actions={
          !isWorker && (
            <Button>
              <Plus className="w-4 h-4 mr-1" />
              新建任务
            </Button>
          )
        }
      />

      {/* Stats */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-5 gap-4">
        {[
          { label: '全部任务', value: stats.total, icon: ListTodo, color: 'text-blue-400' },
          { label: '进行中', value: stats.inProgress, icon: PlayCircle, color: 'text-blue-400' },
          { label: '阻塞', value: stats.blocked, icon: PauseCircle, color: 'text-red-400' },
          { label: '已完成', value: stats.completed, icon: CheckCircle2, color: 'text-emerald-400' },
          { label: '已逾期', value: stats.overdue, icon: AlertTriangle, color: 'text-amber-400' },
        ].map((stat, index) => (
          <Card key={index} className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                </div>
                <stat.icon className={cn('w-6 h-6', stat.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Filters */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex flex-col md:flex-row gap-4 items-start md:items-center justify-between">
              <div className="flex items-center gap-2 flex-wrap">
                {[
                  { value: 'all', label: '全部' },
                  { value: 'in_progress', label: '进行中' },
                  { value: 'pending', label: '待开始' },
                  { value: 'blocked', label: '阻塞' },
                  { value: 'completed', label: '已完成' },
                ].map((filter) => (
                  <Button
                    key={filter.value}
                    variant={statusFilter === filter.value ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setStatusFilter(filter.value)}
                  >
                    {filter.label}
                  </Button>
                ))}
              </div>
              <div className="flex items-center gap-2 w-full md:w-auto">
                <div className="relative flex-1 md:w-64">
                  <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
                  <Input
                    placeholder="搜索任务..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="pl-9"
                  />
                </div>
                <div className="flex border border-border rounded-lg overflow-hidden">
                  <Button
                    variant={viewMode === 'list' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('list')}
                    className="rounded-none"
                  >
                    列表
                  </Button>
                  <Button
                    variant={viewMode === 'kanban' ? 'default' : 'ghost'}
                    size="sm"
                    onClick={() => setViewMode('kanban')}
                    className="rounded-none"
                  >
                    看板
                  </Button>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Task List */}
      {viewMode === 'list' && (
        <motion.div variants={fadeIn} className="grid grid-cols-1 lg:grid-cols-2 gap-4">
          {filteredTasks.map((task) => (
            <TaskCard
              key={task.id}
              task={task}
              onStatusChange={handleStatusChange}
            />
          ))}
        </motion.div>
      )}

      {/* Kanban View */}
      {viewMode === 'kanban' && (
        <motion.div variants={fadeIn} className="overflow-x-auto pb-4">
          <div className="flex gap-4 min-w-max">
            {['pending', 'in_progress', 'blocked', 'completed'].map((status) => {
              const config = statusConfigs[status]
              const statusTasks = filteredTasks.filter((t) => t.status === status)

              return (
                <div key={status} className="w-80">
                  <div className="flex items-center gap-2 mb-4 px-2">
                    <config.icon className={cn('w-4 h-4', config.color)} />
                    <h3 className="font-medium text-white">{config.label}</h3>
                    <Badge variant="secondary" className="ml-auto">
                      {statusTasks.length}
                    </Badge>
                  </div>
                  <div className="space-y-3">
                    {statusTasks.map((task) => (
                      <TaskCard
                        key={task.id}
                        task={task}
                        onStatusChange={handleStatusChange}
                      />
                    ))}
                    {statusTasks.length === 0 && (
                      <div className="p-8 text-center text-slate-500 border border-dashed border-border rounded-xl">
                        暂无任务
                      </div>
                    )}
                  </div>
                </div>
              )
            })}
          </div>
        </motion.div>
      )}

      {/* Empty State */}
      {filteredTasks.length === 0 && viewMode === 'list' && (
        <motion.div variants={fadeIn} className="text-center py-16">
          <ListTodo className="w-16 h-16 mx-auto text-slate-600 mb-4" />
          <h3 className="text-lg font-medium text-slate-400">暂无任务</h3>
          <p className="text-sm text-slate-500 mt-1">
            {searchQuery || statusFilter !== 'all'
              ? '没有符合条件的任务'
              : '点击"新建任务"开始工作'}
          </p>
        </motion.div>
      )}
    </motion.div>
  )
}

