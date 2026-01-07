/**
 * Work Report List Page - 报工列表页面
 * Features: 报工记录列表、审批、统计
 */
import { useState, useEffect, useMemo } from 'react'
import {
  Search,
  Eye,
  CheckCircle2,
  User,
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
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '../components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '../components/ui/table'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from '../components/ui/dialog'
import { formatDate } from '../lib/utils'
import { productionApi } from '../services/api'
const statusConfigs = {
  PENDING: { label: '待审批', color: 'bg-blue-500' },
  APPROVED: { label: '已审批', color: 'bg-emerald-500' },
  REJECTED: { label: '已驳回', color: 'bg-red-500' },
}
const reportTypeConfigs = {
  START: { label: '开工', color: 'bg-blue-500' },
  PROGRESS: { label: '进度', color: 'bg-amber-500' },
  COMPLETE: { label: '完工', color: 'bg-emerald-500' },
}
export default function WorkReportList() {
  const [loading, setLoading] = useState(true)
  const [reports, setReports] = useState([])
  // Filters
  const [searchKeyword, setSearchKeyword] = useState('')
  const [filterStatus, setFilterStatus] = useState('')
  const [filterType, setFilterType] = useState('')
  // Dialogs
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  const [selectedReport, setSelectedReport] = useState(null)
  useEffect(() => {
    fetchReports()
  }, [filterStatus, filterType, searchKeyword])
  const fetchReports = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filterStatus) params.status = filterStatus
      if (filterType) params.report_type = filterType
      if (searchKeyword) params.search = searchKeyword
      const res = await productionApi.workReports.list(params)
      const reportList = res.data?.items || res.data || []
      setReports(reportList)
    } catch (error) {
      console.error('Failed to fetch reports:', error)
    } finally {
      setLoading(false)
    }
  }
  const handleViewDetail = async (reportId) => {
    try {
      const res = await productionApi.workReports.get(reportId)
      setSelectedReport(res.data || res)
      setShowDetailDialog(true)
    } catch (error) {
      console.error('Failed to fetch report detail:', error)
    }
  }
  const handleApprove = async (reportId) => {
    if (!confirm('确认审批通过此报工记录？')) return
    try {
      await productionApi.workReports.approve(reportId)
      fetchReports()
      if (showDetailDialog) {
        handleViewDetail(reportId)
      }
    } catch (error) {
      console.error('Failed to approve report:', error)
      alert('审批失败: ' + (error.response?.data?.detail || error.message))
    }
  }
  const filteredReports = useMemo(() => {
    return reports.filter(report => {
      if (searchKeyword) {
        const keyword = searchKeyword.toLowerCase()
        return (
          report.report_no?.toLowerCase().includes(keyword) ||
          report.work_order_no?.toLowerCase().includes(keyword) ||
          report.worker_name?.toLowerCase().includes(keyword)
        )
      }
      return true
    })
  }, [reports, searchKeyword])
  return (
    <div className="space-y-6 p-6">
      <PageHeader
        title="报工管理"
        description="报工记录列表、审批、统计"
      />
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索报工单号、工单号..."
                value={searchKeyword}
                onChange={(e) => setSearchKeyword(e.target.value)}
                className="pl-10"
              />
            </div>
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger>
                <SelectValue placeholder="选择状态" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部状态</SelectItem>
                {Object.entries(statusConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger>
                <SelectValue placeholder="选择类型" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="">全部类型</SelectItem>
                {Object.entries(reportTypeConfigs).map(([key, config]) => (
                  <SelectItem key={key} value={key}>
                    {config.label}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </CardContent>
      </Card>
      {/* Report List */}
      <Card>
        <CardHeader>
          <CardTitle>报工记录列表</CardTitle>
          <CardDescription>
            共 {filteredReports.length} 条报工记录
          </CardDescription>
        </CardHeader>
        <CardContent>
          {loading ? (
            <div className="text-center py-8 text-slate-400">加载中...</div>
          ) : filteredReports.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无报工记录</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>报工单号</TableHead>
                  <TableHead>工单号</TableHead>
                  <TableHead>工人</TableHead>
                  <TableHead>报工类型</TableHead>
                  <TableHead>报工时间</TableHead>
                  <TableHead>完成数量</TableHead>
                  <TableHead>合格数量</TableHead>
                  <TableHead>工时</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead className="text-right">操作</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {filteredReports.map((report) => (
                  <TableRow key={report.id}>
                    <TableCell className="font-mono text-sm">
                      {report.report_no}
                    </TableCell>
                    <TableCell className="font-mono text-sm">
                      {report.work_order_no || '-'}
                    </TableCell>
                    <TableCell>
                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-slate-400" />
                        <span>{report.worker_name || '-'}</span>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge className={reportTypeConfigs[report.report_type]?.color || 'bg-slate-500'}>
                        {reportTypeConfigs[report.report_type]?.label || report.report_type}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-slate-500 text-sm">
                      {report.report_time ? formatDate(report.report_time) : '-'}
                    </TableCell>
                    <TableCell className="font-medium">
                      {report.completed_qty || 0}
                    </TableCell>
                    <TableCell className="text-emerald-600 font-medium">
                      {report.qualified_qty || 0}
                    </TableCell>
                    <TableCell>
                      {report.work_hours ? `${report.work_hours.toFixed(1)}h` : '-'}
                    </TableCell>
                    <TableCell>
                      <Badge className={statusConfigs[report.status]?.color || 'bg-slate-500'}>
                        {statusConfigs[report.status]?.label || report.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <div className="flex items-center justify-end gap-2">
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleViewDetail(report.id)}
                        >
                          <Eye className="w-4 h-4" />
                        </Button>
                        {report.status === 'PENDING' && (
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleApprove(report.id)}
                          >
                            <CheckCircle2 className="w-4 h-4" />
                          </Button>
                        )}
                      </div>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
      {/* Report Detail Dialog */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="max-w-4xl">
          <DialogHeader>
            <DialogTitle>
              {selectedReport?.report_no} - 报工详情
            </DialogTitle>
          </DialogHeader>
          <DialogBody>
            {selectedReport && (
              <div className="space-y-4">
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1">报工单号</div>
                    <div className="font-mono">{selectedReport.report_no}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">状态</div>
                    <Badge className={statusConfigs[selectedReport.status]?.color}>
                      {statusConfigs[selectedReport.status]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">工单号</div>
                    <div className="font-mono">{selectedReport.work_order_no || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">工人</div>
                    <div>{selectedReport.worker_name || '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">报工类型</div>
                    <Badge className={reportTypeConfigs[selectedReport.report_type]?.color}>
                      {reportTypeConfigs[selectedReport.report_type]?.label}
                    </Badge>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">报工时间</div>
                    <div>{selectedReport.report_time ? formatDate(selectedReport.report_time) : '-'}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">完成数量</div>
                    <div className="font-medium">{selectedReport.completed_qty || 0}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">合格数量</div>
                    <div className="font-medium text-emerald-600">{selectedReport.qualified_qty || 0}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">不良数量</div>
                    <div className="font-medium text-red-600">{selectedReport.defect_qty || 0}</div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1">工时</div>
                    <div>{selectedReport.work_hours ? `${selectedReport.work_hours.toFixed(1)} 小时` : '-'}</div>
                  </div>
                  {selectedReport.progress_percent !== undefined && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">进度</div>
                      <div className="font-medium">{selectedReport.progress_percent}%</div>
                    </div>
                  )}
                  {selectedReport.approved_at && (
                    <div>
                      <div className="text-sm text-slate-500 mb-1">审批时间</div>
                      <div>{formatDate(selectedReport.approved_at)}</div>
                    </div>
                  )}
                </div>
                {selectedReport.report_note && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">报工说明</div>
                    <div>{selectedReport.report_note}</div>
                  </div>
                )}
              </div>
            )}
          </DialogBody>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
              关闭
            </Button>
            {selectedReport && selectedReport.status === 'PENDING' && (
              <Button onClick={() => handleApprove(selectedReport.id)}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                审批通过
              </Button>
            )}
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}

