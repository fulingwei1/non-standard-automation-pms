import { useState } from 'react'
import { motion } from 'framer-motion'
import {
  Clock,
  Calendar,
  Plus,
  ChevronLeft,
  ChevronRight,
  Save,
  Send,
  Edit3,
  Trash2,
  AlertCircle,
  CheckCircle2,
  XCircle,
  Timer,
  Briefcase,
  Coffee,
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
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

// Current week dates helper
const getWeekDates = (offset = 0) => {
  const today = new Date()
  const currentDay = today.getDay()
  const monday = new Date(today)
  monday.setDate(today.getDate() - currentDay + 1 + offset * 7)

  const dates = []
  for (let i = 0; i < 7; i++) {
    const date = new Date(monday)
    date.setDate(monday.getDate() + i)
    dates.push(date)
  }
  return dates
}

const formatDate = (date) => {
  return `${date.getMonth() + 1}/${date.getDate()}`
}

const formatFullDate = (date) => {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`
}

const dayNames = ['周一', '周二', '周三', '周四', '周五', '周六', '周日']

// Mock timesheet data
const mockTimesheetData = {
  entries: [
    {
      id: 1,
      projectId: 'PJ250108001',
      projectName: 'BMS老化测试设备',
      taskId: 'T001',
      taskName: '机械结构设计',
      hours: {
        '2026-01-06': 4,
        '2026-01-07': 6,
        '2026-01-08': 5,
        '2026-01-09': 3,
        '2026-01-10': 0,
      },
      status: 'draft',
    },
    {
      id: 2,
      projectId: 'PJ250108001',
      projectName: 'BMS老化测试设备',
      taskId: 'T002',
      taskName: '3D建模',
      hours: {
        '2026-01-06': 4,
        '2026-01-07': 2,
        '2026-01-08': 3,
        '2026-01-09': 5,
        '2026-01-10': 8,
      },
      status: 'submitted',
    },
    {
      id: 3,
      projectId: 'PJ250105002',
      projectName: 'EOL功能测试设备',
      taskId: 'T003',
      taskName: '设计评审',
      hours: {
        '2026-01-08': 2,
        '2026-01-09': 0,
        '2026-01-10': 0,
      },
      status: 'approved',
    },
  ],
  summary: {
    totalHours: 42,
    weeklyTarget: 40,
    overtimeHours: 2,
    projectCount: 2,
    taskCount: 3,
  },
}

// Available projects for new entry
const availableProjects = [
  {
    id: 'PJ250108001',
    name: 'BMS老化测试设备',
    tasks: [
      { id: 'T001', name: '机械结构设计' },
      { id: 'T002', name: '3D建模' },
      { id: 'T003', name: '图纸输出' },
    ],
  },
  {
    id: 'PJ250105002',
    name: 'EOL功能测试设备',
    tasks: [
      { id: 'T004', name: '方案设计' },
      { id: 'T005', name: '设计评审' },
    ],
  },
  {
    id: 'PJ250106003',
    name: 'ICT测试设备',
    tasks: [
      { id: 'T006', name: '电气设计' },
      { id: 'T007', name: 'PLC编程' },
    ],
  },
]

const getStatusBadge = (status) => {
  const configs = {
    draft: { label: '草稿', variant: 'secondary', icon: Edit3 },
    submitted: { label: '已提交', variant: 'default', icon: AlertCircle },
    approved: { label: '已审批', variant: 'success', icon: CheckCircle2 },
    rejected: { label: '已退回', variant: 'destructive', icon: XCircle },
  }
  const config = configs[status] || configs.draft
  return (
    <Badge variant={config.variant} className="gap-1">
      <config.icon className="w-3 h-3" />
      {config.label}
    </Badge>
  )
}

function AddEntryDialog({ open, onOpenChange, onAdd, weekDates }) {
  const [selectedProject, setSelectedProject] = useState('')
  const [selectedTask, setSelectedTask] = useState('')
  const [hours, setHours] = useState({})

  const project = availableProjects.find((p) => p.id === selectedProject)

  const handleAdd = () => {
    if (selectedProject && selectedTask) {
      const projectInfo = availableProjects.find((p) => p.id === selectedProject)
      const taskInfo = projectInfo?.tasks.find((t) => t.id === selectedTask)
      onAdd({
        projectId: selectedProject,
        projectName: projectInfo?.name,
        taskId: selectedTask,
        taskName: taskInfo?.name,
        hours,
      })
      setSelectedProject('')
      setSelectedTask('')
      setHours({})
      onOpenChange(false)
    }
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="sm:max-w-[600px]">
        <DialogHeader>
          <DialogTitle>添加工时记录</DialogTitle>
        </DialogHeader>
        <div className="space-y-4 py-4">
          {/* Project Select */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">项目</label>
            <select
              value={selectedProject}
              onChange={(e) => {
                setSelectedProject(e.target.value)
                setSelectedTask('')
              }}
              className="w-full h-10 px-3 rounded-lg bg-surface-2 border border-border text-white focus:border-accent focus:outline-none"
            >
              <option value="">选择项目</option>
              {availableProjects.map((project) => (
                <option key={project.id} value={project.id}>
                  {project.id} - {project.name}
                </option>
              ))}
            </select>
          </div>

          {/* Task Select */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">任务</label>
            <select
              value={selectedTask}
              onChange={(e) => setSelectedTask(e.target.value)}
              disabled={!selectedProject}
              className="w-full h-10 px-3 rounded-lg bg-surface-2 border border-border text-white focus:border-accent focus:outline-none disabled:opacity-50"
            >
              <option value="">选择任务</option>
              {project?.tasks.map((task) => (
                <option key={task.id} value={task.id}>
                  {task.name}
                </option>
              ))}
            </select>
          </div>

          {/* Hours Input */}
          <div className="space-y-2">
            <label className="text-sm font-medium text-slate-300">工时</label>
            <div className="grid grid-cols-7 gap-2">
              {weekDates.map((date, index) => (
                <div key={index} className="text-center">
                  <div className="text-xs text-slate-500 mb-1">
                    {dayNames[index]}
                  </div>
                  <div className="text-xs text-slate-400 mb-1">
                    {formatDate(date)}
                  </div>
                  <Input
                    type="number"
                    min="0"
                    max="24"
                    step="0.5"
                    placeholder="0"
                    value={hours[formatFullDate(date)] || ''}
                    onChange={(e) =>
                      setHours({
                        ...hours,
                        [formatFullDate(date)]: parseFloat(e.target.value) || 0,
                      })
                    }
                    className="text-center h-9"
                  />
                </div>
              ))}
            </div>
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            取消
          </Button>
          <Button onClick={handleAdd} disabled={!selectedProject || !selectedTask}>
            添加
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  )
}

export default function Timesheet() {
  const [weekOffset, setWeekOffset] = useState(0)
  const [entries, setEntries] = useState(mockTimesheetData.entries)
  const [showAddDialog, setShowAddDialog] = useState(false)

  const weekDates = getWeekDates(weekOffset)
  const isCurrentWeek = weekOffset === 0

  // Calculate totals
  const dailyTotals = weekDates.reduce((acc, date) => {
    const dateStr = formatFullDate(date)
    acc[dateStr] = entries.reduce((sum, entry) => sum + (entry.hours[dateStr] || 0), 0)
    return acc
  }, {})

  const weeklyTotal = Object.values(dailyTotals).reduce((a, b) => a + b, 0)

  const handleAddEntry = (newEntry) => {
    setEntries([
      ...entries,
      {
        id: Date.now(),
        ...newEntry,
        status: 'draft',
      },
    ])
  }

  const handleHoursChange = (entryId, dateStr, value) => {
    setEntries(
      entries.map((entry) =>
        entry.id === entryId
          ? { ...entry, hours: { ...entry.hours, [dateStr]: parseFloat(value) || 0 } }
          : entry
      )
    )
  }

  const handleDeleteEntry = (entryId) => {
    setEntries(entries.filter((e) => e.id !== entryId))
  }

  const handleSubmit = () => {
    setEntries(
      entries.map((entry) =>
        entry.status === 'draft' ? { ...entry, status: 'submitted' } : entry
      )
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6">
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="show"
      className="space-y-6"
    >
      <PageHeader
        title="工时填报"
        description="记录您的工作时间，便于项目成本核算与绩效统计"
      />

      {/* Week Summary */}
      <motion.div variants={fadeIn} className="grid grid-cols-2 md:grid-cols-4 gap-4">
        {[
          {
            label: '本周工时',
            value: `${weeklyTotal}h`,
            icon: Clock,
            color: 'text-blue-400',
            desc: `目标 40h`,
          },
          {
            label: '加班工时',
            value: `${Math.max(0, weeklyTotal - 40)}h`,
            icon: Timer,
            color: weeklyTotal > 40 ? 'text-amber-400' : 'text-slate-400',
            desc: '超出标准工时',
          },
          {
            label: '参与项目',
            value: new Set(entries.map((e) => e.projectId)).size,
            icon: Briefcase,
            color: 'text-emerald-400',
            desc: '个项目',
          },
          {
            label: '休息时间',
            value: `${Math.max(0, 168 - weeklyTotal - 56)}h`,
            icon: Coffee,
            color: 'text-purple-400',
            desc: '本周剩余',
          },
        ].map((stat, index) => (
          <Card key={index} className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">{stat.value}</p>
                  <p className="text-xs text-slate-500 mt-0.5">{stat.desc}</p>
                </div>
                <stat.icon className={cn('w-8 h-8', stat.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* Week Navigation */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-3">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setWeekOffset(weekOffset - 1)}
                >
                  <ChevronLeft className="w-4 h-4" />
                </Button>
                <div className="flex items-center gap-2">
                  <Calendar className="w-5 h-5 text-accent" />
                  <span className="font-medium text-white">
                    {formatFullDate(weekDates[0])} ~ {formatFullDate(weekDates[6])}
                  </span>
                  {isCurrentWeek && (
                    <Badge variant="secondary" className="ml-2">
                      本周
                    </Badge>
                  )}
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => setWeekOffset(weekOffset + 1)}
                  disabled={weekOffset >= 0}
                >
                  <ChevronRight className="w-4 h-4" />
                </Button>
              </div>
              <div className="flex items-center gap-2">
                <Button variant="outline" onClick={() => setShowAddDialog(true)}>
                  <Plus className="w-4 h-4 mr-1" />
                  添加记录
                </Button>
                <Button variant="outline">
                  <Save className="w-4 h-4 mr-1" />
                  保存草稿
                </Button>
                <Button onClick={handleSubmit}>
                  <Send className="w-4 h-4 mr-1" />
                  提交审批
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Timesheet Table */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50 overflow-hidden">
          <CardHeader className="pb-0">
            <CardTitle className="text-lg">工时明细</CardTitle>
            <CardDescription>填写每天在各项目任务上投入的工时</CardDescription>
          </CardHeader>
          <CardContent className="p-0">
            <div className="overflow-x-auto">
              <table className="w-full">
                <thead>
                  <tr className="border-b border-border">
                    <th className="text-left p-4 text-sm font-medium text-slate-400 min-w-[200px]">
                      项目 / 任务
                    </th>
                    {weekDates.map((date, index) => {
                      const isToday =
                        formatFullDate(date) === formatFullDate(new Date())
                      const isWeekend = index >= 5
                      return (
                        <th
                          key={index}
                          className={cn(
                            'text-center p-4 text-sm font-medium min-w-[80px]',
                            isWeekend ? 'text-slate-500' : 'text-slate-400',
                            isToday && 'bg-accent/10'
                          )}
                        >
                          <div>{dayNames[index]}</div>
                          <div className="text-xs mt-0.5">{formatDate(date)}</div>
                        </th>
                      )
                    })}
                    <th className="text-center p-4 text-sm font-medium text-slate-400 min-w-[80px]">
                      小计
                    </th>
                    <th className="text-center p-4 text-sm font-medium text-slate-400 min-w-[100px]">
                      状态
                    </th>
                    <th className="text-center p-4 text-sm font-medium text-slate-400 w-[60px]">
                      操作
                    </th>
                  </tr>
                </thead>
                <tbody>
                  {entries.map((entry) => {
                    const entryTotal = Object.values(entry.hours).reduce(
                      (a, b) => a + b,
                      0
                    )
                    const isEditable = entry.status === 'draft'

                    return (
                      <tr
                        key={entry.id}
                        className="border-b border-border/50 hover:bg-surface-2/30"
                      >
                        <td className="p-4">
                          <div>
                            <div className="font-medium text-white text-sm">
                              {entry.projectName}
                            </div>
                            <div className="text-xs text-slate-400">
                              {entry.projectId} · {entry.taskName}
                            </div>
                          </div>
                        </td>
                        {weekDates.map((date, index) => {
                          const dateStr = formatFullDate(date)
                          const hours = entry.hours[dateStr] || 0
                          const isToday = dateStr === formatFullDate(new Date())
                          const isWeekend = index >= 5

                          return (
                            <td
                              key={index}
                              className={cn(
                                'p-2 text-center',
                                isToday && 'bg-accent/10',
                                isWeekend && 'bg-surface-0/30'
                              )}
                            >
                              {isEditable ? (
                                <Input
                                  type="number"
                                  min="0"
                                  max="24"
                                  step="0.5"
                                  value={hours || ''}
                                  onChange={(e) =>
                                    handleHoursChange(entry.id, dateStr, e.target.value)
                                  }
                                  className="w-16 h-8 text-center mx-auto"
                                  placeholder="0"
                                />
                              ) : (
                                <span
                                  className={cn(
                                    'text-sm',
                                    hours > 0 ? 'text-white' : 'text-slate-500'
                                  )}
                                >
                                  {hours || '-'}
                                </span>
                              )}
                            </td>
                          )
                        })}
                        <td className="p-4 text-center">
                          <span className="font-medium text-white">
                            {entryTotal}h
                          </span>
                        </td>
                        <td className="p-4 text-center">
                          {getStatusBadge(entry.status)}
                        </td>
                        <td className="p-4 text-center">
                          {isEditable && (
                            <Button
                              variant="ghost"
                              size="sm"
                              onClick={() => handleDeleteEntry(entry.id)}
                              className="h-8 w-8 p-0 text-slate-400 hover:text-red-400"
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          )}
                        </td>
                      </tr>
                    )
                  })}

                  {/* Daily Totals Row */}
                  <tr className="bg-surface-2/50 border-t-2 border-border">
                    <td className="p-4 font-medium text-white">每日合计</td>
                    {weekDates.map((date, index) => {
                      const dateStr = formatFullDate(date)
                      const total = dailyTotals[dateStr] || 0
                      const isToday = dateStr === formatFullDate(new Date())
                      const isOvertime = total > 8

                      return (
                        <td
                          key={index}
                          className={cn(
                            'p-4 text-center font-medium',
                            isToday && 'bg-accent/10',
                            isOvertime ? 'text-amber-400' : 'text-white'
                          )}
                        >
                          {total}h
                        </td>
                      )
                    })}
                    <td className="p-4 text-center">
                      <span
                        className={cn(
                          'font-bold text-lg',
                          weeklyTotal > 40 ? 'text-amber-400' : 'text-emerald-400'
                        )}
                      >
                        {weeklyTotal}h
                      </span>
                    </td>
                    <td colSpan={2}></td>
                  </tr>
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Add Entry Dialog */}
      <AddEntryDialog
        open={showAddDialog}
        onOpenChange={setShowAddDialog}
        onAdd={handleAddEntry}
        weekDates={weekDates}
      />
    </motion.div>
      </div>
    </div>
  )
}

