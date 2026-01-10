import { useState, useEffect } from 'react'
import { motion } from 'framer-motion'
import {
  CheckSquare,
  Download,
  RefreshCw,
  X,
  CheckCircle2,
  AlertCircle,
  Clock,
  FileSpreadsheet,
  Mail,
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
import { Checkbox } from '../components/ui/checkbox'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '../components/ui/dialog'
import { timesheetApi } from '../services/api'
import { cn } from '../lib/utils'
import { fadeIn, staggerContainer } from '../lib/animations'

export default function TimesheetBatchOperations() {
  const [loading, setLoading] = useState(false)
  const [timesheets, setTimesheets] = useState([])
  const [selectedIds, setSelectedIds] = useState(new Set())
  const [showApproveDialog, setShowApproveDialog] = useState(false)
  const [showExportDialog, setShowExportDialog] = useState(false)
  const [showSyncDialog, setShowSyncDialog] = useState(false)
  const [approveComment, setApproveComment] = useState('')
  const [filterStatus, setFilterStatus] = useState('PENDING')
  const [filterDate, setFilterDate] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1)
      .toISOString()
      .split('T')[0],
    end: new Date().toISOString().split('T')[0],
  })

  useEffect(() => {
    loadTimesheets()
  }, [filterStatus, filterDate])

  const loadTimesheets = async () => {
    setLoading(true)
    try {
      const response = await timesheetApi.list({
        status: filterStatus,
        start_date: filterDate.start,
        end_date: filterDate.end,
        page_size: 100,
      })
      setTimesheets(response.data?.items || response.data?.data?.items || [])
    } catch (error) {
      console.error('加载工时记录失败:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleSelectAll = (checked) => {
    if (checked) {
      setSelectedIds(new Set(timesheets.map((t) => t.id)))
    } else {
      setSelectedIds(new Set())
    }
  }

  const handleSelectOne = (id, checked) => {
    const newSelected = new Set(selectedIds)
    if (checked) {
      newSelected.add(id)
    } else {
      newSelected.delete(id)
    }
    setSelectedIds(newSelected)
  }

  const handleBatchApprove = async () => {
    if (selectedIds.size === 0) {
      alert('请选择要审批的记录')
      return
    }

    setLoading(true)
    try {
      await timesheetApi.batchApprove({
        timesheet_ids: Array.from(selectedIds),
        comment: approveComment || undefined,
      })
      alert(`成功审批 ${selectedIds.size} 条记录`)
      setShowApproveDialog(false)
      setApproveComment('')
      setSelectedIds(new Set())
      loadTimesheets()
    } catch (error) {
      console.error('批量审批失败:', error)
      alert('批量审批失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleBatchExport = async (format = 'excel') => {
    if (selectedIds.size === 0) {
      alert('请选择要导出的记录')
      return
    }

    setLoading(true)
    try {
      // 获取选中的记录数据
      const selectedTimesheets = timesheets.filter((t) =>
        selectedIds.has(t.id)
      )

      // 按项目分组导出
      const projectGroups = {}
      selectedTimesheets.forEach((ts) => {
        const projectId = ts.project_id || 'other'
        if (!projectGroups[projectId]) {
          projectGroups[projectId] = []
        }
        projectGroups[projectId].push(ts)
      })

      // 导出每个项目的报表
      for (const [projectId, projectTimesheets] of Object.entries(
        projectGroups
      )) {
        if (projectId === 'other') continue

        const firstTs = projectTimesheets[0]
        const workDate = new Date(firstTs.work_date)
        const year = workDate.getFullYear()
        const month = workDate.getMonth() + 1

        try {
          const response = await timesheetApi.getProjectReport({
            project_id: projectId,
            format: format,
            start_date: filterDate.start,
            end_date: filterDate.end,
          })

          if (format === 'excel') {
            const blob = new Blob([response.data], {
              type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            })
            const url = window.URL.createObjectURL(blob)
            const link = document.createElement('a')
            link.href = url
            link.download = `项目工时报表_${projectId}_${year}${String(month).padStart(2, '0')}.xlsx`
            document.body.appendChild(link)
            link.click()
            document.body.removeChild(link)
            window.URL.revokeObjectURL(url)
          }
        } catch (error) {
          console.error(`导出项目${projectId}报表失败:`, error)
        }
      }

      alert(`成功导出 ${selectedIds.size} 条记录`)
      setShowExportDialog(false)
    } catch (error) {
      console.error('批量导出失败:', error)
      alert('批量导出失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const handleBatchSync = async (syncTarget = 'all') => {
    if (selectedIds.size === 0) {
      alert('请选择要同步的记录')
      return
    }

    setLoading(true)
    try {
      // 获取选中记录的项目和日期信息
      const selectedTimesheets = timesheets.filter((t) =>
        selectedIds.has(t.id)
      )

      // 按项目分组同步
      const projectGroups = {}
      selectedTimesheets.forEach((ts) => {
        const projectId = ts.project_id
        if (projectId) {
          if (!projectGroups[projectId]) {
            projectGroups[projectId] = []
          }
          projectGroups[projectId].push(ts)
        }
      })

      let successCount = 0
      let failCount = 0

      for (const [projectId, projectTimesheets] of Object.entries(
        projectGroups
      )) {
        const firstTs = projectTimesheets[0]
        const workDate = new Date(firstTs.work_date)
        const year = workDate.getFullYear()
        const month = workDate.getMonth() + 1

        try {
          await timesheetApi.sync({
            project_id: projectId,
            year: year,
            month: month,
            sync_target: syncTarget,
          })
          successCount += projectTimesheets.length
        } catch (error) {
          console.error(`同步项目${projectId}失败:`, error)
          failCount += projectTimesheets.length
        }
      }

      alert(
        `同步完成：成功 ${successCount} 条，失败 ${failCount} 条`
      )
      setShowSyncDialog(false)
      loadTimesheets()
    } catch (error) {
      console.error('批量同步失败:', error)
      alert('批量同步失败，请稍后重试')
    } finally {
      setLoading(false)
    }
  }

  const getStatusBadge = (status) => {
    const statusMap = {
      DRAFT: { label: '草稿', variant: 'outline', color: 'text-slate-400' },
      PENDING: {
        label: '待审批',
        variant: 'default',
        color: 'text-yellow-500',
      },
      APPROVED: {
        label: '已通过',
        variant: 'default',
        color: 'text-green-500',
      },
      REJECTED: {
        label: '已驳回',
        variant: 'destructive',
        color: 'text-red-500',
      },
    }

    const config = statusMap[status] || statusMap.DRAFT
    return (
      <Badge variant={config.variant} className={config.color}>
        {config.label}
      </Badge>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <PageHeader
        title="批量工时操作"
        description="批量审批、导出、同步工时记录"
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* 筛选栏 */}
        <motion.div
          initial="hidden"
          animate="visible"
          variants={fadeIn}
          className="bg-slate-800/50 rounded-lg p-4 space-y-4"
        >
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="text-sm text-slate-300 mb-2 block">
                状态筛选
              </label>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
                className="w-full bg-slate-700 text-white px-3 py-2 rounded border border-slate-600"
              >
                <option value="">全部</option>
                <option value="DRAFT">草稿</option>
                <option value="PENDING">待审批</option>
                <option value="APPROVED">已通过</option>
                <option value="REJECTED">已驳回</option>
              </select>
            </div>
            <div>
              <label className="text-sm text-slate-300 mb-2 block">
                开始日期
              </label>
              <input
                type="date"
                value={filterDate.start}
                onChange={(e) =>
                  setFilterDate({ ...filterDate, start: e.target.value })
                }
                className="w-full bg-slate-700 text-white px-3 py-2 rounded border border-slate-600"
              />
            </div>
            <div>
              <label className="text-sm text-slate-300 mb-2 block">
                结束日期
              </label>
              <input
                type="date"
                value={filterDate.end}
                onChange={(e) =>
                  setFilterDate({ ...filterDate, end: e.target.value })
                }
                className="w-full bg-slate-700 text-white px-3 py-2 rounded border border-slate-600"
              />
            </div>
            <div className="flex items-end">
              <Button
                onClick={loadTimesheets}
                className="w-full bg-blue-600 hover:bg-blue-700"
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                刷新
              </Button>
            </div>
          </div>
        </motion.div>

        {/* 批量操作栏 */}
        {selectedIds.size > 0 && (
          <motion.div
            initial={{ opacity: 0, y: -20 }}
            animate={{ opacity: 1, y: 0 }}
            className="bg-blue-900/30 border border-blue-500/30 rounded-lg p-4"
          >
            <div className="flex items-center justify-between">
              <div className="flex items-center gap-2">
                <CheckSquare className="w-5 h-5 text-blue-400" />
                <span className="text-white font-medium">
                  已选择 {selectedIds.size} 条记录
                </span>
              </div>
              <div className="flex items-center gap-2">
                {filterStatus === 'PENDING' && (
                  <Button
                    onClick={() => setShowApproveDialog(true)}
                    className="bg-green-600 hover:bg-green-700"
                  >
                    <CheckCircle2 className="w-4 h-4 mr-2" />
                    批量审批
                  </Button>
                )}
                <Button
                  onClick={() => setShowExportDialog(true)}
                  variant="outline"
                  className="bg-slate-700 hover:bg-slate-600 text-white border-slate-600"
                >
                  <Download className="w-4 h-4 mr-2" />
                  批量导出
                </Button>
                <Button
                  onClick={() => setShowSyncDialog(true)}
                  variant="outline"
                  className="bg-slate-700 hover:bg-slate-600 text-white border-slate-600"
                >
                  <RefreshCw className="w-4 h-4 mr-2" />
                  批量同步
                </Button>
                <Button
                  onClick={() => setSelectedIds(new Set())}
                  variant="ghost"
                  className="text-slate-400 hover:text-white"
                >
                  <X className="w-4 h-4" />
                </Button>
              </div>
            </div>
          </motion.div>
        )}

        {/* 工时记录列表 */}
        <Card className="bg-slate-800/50 border-slate-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-white">工时记录列表</CardTitle>
                <CardDescription className="text-slate-400">
                  共 {timesheets.length} 条记录
                </CardDescription>
              </div>
              <div className="flex items-center gap-2">
                <Checkbox
                  checked={
                    selectedIds.size > 0 &&
                    selectedIds.size === timesheets.length
                  }
                  onCheckedChange={handleSelectAll}
                />
                <span className="text-sm text-slate-400">全选</span>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8">
                <Clock className="w-8 h-8 animate-spin text-blue-500 mx-auto mb-2" />
                <p className="text-slate-400">加载中...</p>
              </div>
            ) : timesheets.length === 0 ? (
              <div className="text-center py-8">
                <AlertCircle className="w-12 h-12 text-slate-500 mx-auto mb-2" />
                <p className="text-slate-400">暂无数据</p>
              </div>
            ) : (
              <div className="space-y-2">
                {timesheets.map((timesheet) => (
                  <div
                    key={timesheet.id}
                    className={cn(
                      'flex items-center gap-4 p-3 rounded bg-slate-700/50 hover:bg-slate-700/70 transition-colors',
                      selectedIds.has(timesheet.id) &&
                        'bg-blue-900/30 border border-blue-500/30'
                    )}
                  >
                    <Checkbox
                      checked={selectedIds.has(timesheet.id)}
                      onCheckedChange={(checked) =>
                        handleSelectOne(timesheet.id, checked)
                      }
                    />
                    <div className="flex-1 grid grid-cols-5 gap-4">
                      <div>
                        <p className="text-white font-medium">
                          {timesheet.user_name}
                        </p>
                        <p className="text-xs text-slate-400">
                          {timesheet.work_date}
                        </p>
                      </div>
                      <div>
                        <p className="text-white">{timesheet.project_name}</p>
                        <p className="text-xs text-slate-400">
                          {timesheet.project_code}
                        </p>
                      </div>
                      <div>
                        <p className="text-white">
                          {timesheet.work_hours || 0}h
                        </p>
                        <p className="text-xs text-slate-400">
                          {timesheet.work_type || 'NORMAL'}
                        </p>
                      </div>
                      <div>{getStatusBadge(timesheet.status)}</div>
                      <div className="text-right">
                        <p className="text-xs text-slate-400">
                          {timesheet.created_at
                            ? new Date(timesheet.created_at).toLocaleDateString()
                            : '-'}
                        </p>
                      </div>
                    </div>
                  </div>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 批量审批对话框 */}
      <Dialog open={showApproveDialog} onOpenChange={setShowApproveDialog}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">
              批量审批 ({selectedIds.size} 条)
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="text-sm text-slate-300 mb-2 block">
                审批意见（可选）
              </label>
              <textarea
                value={approveComment}
                onChange={(e) => setApproveComment(e.target.value)}
                className="w-full bg-slate-700 text-white px-3 py-2 rounded border border-slate-600 min-h-[100px]"
                placeholder="请输入审批意见..."
              />
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowApproveDialog(false)}
              className="border-slate-600 text-slate-300"
            >
              取消
            </Button>
            <Button
              onClick={handleBatchApprove}
              className="bg-green-600 hover:bg-green-700"
              disabled={loading}
            >
              {loading ? '审批中...' : '确认审批'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 批量导出对话框 */}
      <Dialog open={showExportDialog} onOpenChange={setShowExportDialog}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">
              批量导出 ({selectedIds.size} 条)
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-slate-300">
              将导出选中记录的工时报表，按项目分组生成Excel文件
            </p>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowExportDialog(false)}
              className="border-slate-600 text-slate-300"
            >
              取消
            </Button>
            <Button
              onClick={() => handleBatchExport('excel')}
              className="bg-blue-600 hover:bg-blue-700"
              disabled={loading}
            >
              <FileSpreadsheet className="w-4 h-4 mr-2" />
              {loading ? '导出中...' : '导出Excel'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 批量同步对话框 */}
      <Dialog open={showSyncDialog} onOpenChange={setShowSyncDialog}>
        <DialogContent className="bg-slate-800 border-slate-700">
          <DialogHeader>
            <DialogTitle className="text-white">
              批量同步 ({selectedIds.size} 条)
            </DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <p className="text-slate-300">选择同步目标：</p>
            <div className="space-y-2">
              {[
                { value: 'all', label: '全部系统' },
                { value: 'finance', label: '财务系统' },
                { value: 'rd', label: '研发系统' },
                { value: 'project', label: '项目系统' },
                { value: 'hr', label: 'HR系统' },
              ].map((option) => (
                <label
                  key={option.value}
                  className="flex items-center gap-2 text-slate-300 cursor-pointer"
                >
                  <input
                    type="radio"
                    name="syncTarget"
                    value={option.value}
                    defaultChecked={option.value === 'all'}
                    className="text-blue-500"
                  />
                  {option.label}
                </label>
              ))}
            </div>
          </div>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowSyncDialog(false)}
              className="border-slate-600 text-slate-300"
            >
              取消
            </Button>
            <Button
              onClick={() => {
                const target = document.querySelector(
                  'input[name="syncTarget"]:checked'
                )?.value || 'all'
                handleBatchSync(target)
              }}
              className="bg-blue-600 hover:bg-blue-700"
              disabled={loading}
            >
              <RefreshCw className="w-4 h-4 mr-2" />
              {loading ? '同步中...' : '开始同步'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
