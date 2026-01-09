import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { managementRhythmApi } from '../services/api'
import { PageHeader } from '../components/layout/PageHeader'
import { Card, CardContent, Badge, Button, Dialog, DialogContent, DialogHeader, DialogTitle } from '../components/ui'
import {
  Plus,
  FileText,
  Calendar,
  TrendingUp,
  TrendingDown,
  Minus,
  Download,
  Eye,
} from 'lucide-react'

const reportTypeConfig = {
  ANNUAL: { label: '年度报告', color: 'bg-blue-500' },
  MONTHLY: { label: '月度报告', color: 'bg-green-500' },
}

const statusConfig = {
  GENERATED: { label: '已生成', color: 'bg-gray-500' },
  PUBLISHED: { label: '已发布', color: 'bg-green-500' },
  ARCHIVED: { label: '已归档', color: 'bg-gray-400' },
}

export default function MeetingReports() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [reports, setReports] = useState([])
  const [total, setTotal] = useState(0)
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [filters, setFilters] = useState({
    report_type: '',
    period_year: new Date().getFullYear(),
    rhythm_level: '',
  })
  const [generateDialogOpen, setGenerateDialogOpen] = useState(false)
  const [generateForm, setGenerateForm] = useState({
    report_type: 'MONTHLY',
    period_year: new Date().getFullYear(),
    period_month: new Date().getMonth() + 1,
    rhythm_level: '',
  })

  useEffect(() => {
    fetchReports()
  }, [page, filters])

  const fetchReports = async () => {
    try {
      setLoading(true)
      const params = {
        page,
        page_size: pageSize,
        ...filters,
      }
      const res = await managementRhythmApi.reports.list(params)
      const data = res.data || res
      setReports(data.items || [])
      setTotal(data.total || 0)
    } catch (err) {
    } finally {
      setLoading(false)
    }
  }

  const handleGenerate = async () => {
    try {
      await managementRhythmApi.reports.generate(generateForm)
      setGenerateDialogOpen(false)
      fetchReports()
      alert('报告生成成功')
    } catch (err) {
      alert('报告生成失败: ' + (err.response?.data?.detail || err.message))
    }
  }

  const formatDate = (dateStr) => {
    if (!dateStr) return '-'
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN')
  }

  const renderComparison = (comparison) => {
    if (!comparison) return null

    const change = comparison.change || 0
    const changeRate = comparison.change_rate || '0%'
    const isPositive = change > 0
    const isNegative = change < 0

    return (
      <div className="flex items-center gap-2 text-sm">
        {isPositive && <TrendingUp className="w-4 h-4 text-green-600" />}
        {isNegative && <TrendingDown className="w-4 h-4 text-red-600" />}
        {!isPositive && !isNegative && <Minus className="w-4 h-4 text-gray-400" />}
        <span className={isPositive ? 'text-green-600' : isNegative ? 'text-red-600' : 'text-gray-500'}>
          {change > 0 ? '+' : ''}{change} ({changeRate})
        </span>
      </div>
    )
  }

  return (
    <div className="space-y-6">
      <PageHeader
        title="会议报告"
        description="自动生成年度和月度会议报告，月度报告包含与上月对比"
        action={
          <Button onClick={() => setGenerateDialogOpen(true)}>
            <Plus className="w-4 h-4 mr-2" />
            生成报告
          </Button>
        }
      />

      {/* 筛选器 */}
      <Card>
        <CardContent className="p-4">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <div>
              <label className="block text-sm font-medium mb-1">报告类型</label>
              <select
                value={filters.report_type}
                onChange={(e) => setFilters({ ...filters, report_type: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">全部</option>
                <option value="ANNUAL">年度报告</option>
                <option value="MONTHLY">月度报告</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">年份</label>
              <input
                type="number"
                value={filters.period_year}
                onChange={(e) => setFilters({ ...filters, period_year: parseInt(e.target.value) || new Date().getFullYear() })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">节律层级</label>
              <select
                value={filters.rhythm_level}
                onChange={(e) => setFilters({ ...filters, rhythm_level: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">全部</option>
                <option value="STRATEGIC">战略层</option>
                <option value="OPERATIONAL">经营层</option>
                <option value="OPERATION">运营层</option>
                <option value="TASK">任务层</option>
              </select>
            </div>
            <div className="flex items-end">
              <Button onClick={fetchReports} className="w-full">
                查询
              </Button>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 报告列表 */}
      <div className="space-y-4">
        {loading ? (
          <div className="text-center py-12">
            <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
            <p className="text-gray-600">加载中...</p>
          </div>
        ) : reports.length === 0 ? (
          <Card>
            <CardContent className="p-12 text-center">
              <FileText className="w-16 h-16 text-gray-400 mx-auto mb-4" />
              <p className="text-gray-500">暂无报告</p>
            </CardContent>
          </Card>
        ) : (
          reports.map((report) => (
            <Card key={report.id} className="hover:shadow-md transition-shadow">
              <CardContent className="p-6">
                <div className="flex items-start justify-between">
                  <div className="flex-1">
                    <div className="flex items-center gap-3 mb-2">
                      <Badge className={reportTypeConfig[report.report_type]?.color}>
                        {reportTypeConfig[report.report_type]?.label}
                      </Badge>
                      <h3 className="text-lg font-semibold">{report.report_title}</h3>
                      <Badge>{report.status}</Badge>
                    </div>
                    <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mt-4 text-sm text-gray-600">
                      <div>
                        <div className="font-medium">报告编号</div>
                        <div>{report.report_no}</div>
                      </div>
                      <div>
                        <div className="font-medium">周期</div>
                        <div>
                          {formatDate(report.period_start)} ~ {formatDate(report.period_end)}
                        </div>
                      </div>
                      <div>
                        <div className="font-medium">节律层级</div>
                        <div>{report.rhythm_level}</div>
                      </div>
                      <div>
                        <div className="font-medium">生成时间</div>
                        <div>{formatDate(report.generated_at)}</div>
                      </div>
                    </div>
                    {report.report_data?.summary && (
                      <div className="mt-4 grid grid-cols-2 md:grid-cols-4 gap-4">
                        <div>
                          <div className="text-sm text-gray-500">会议总数</div>
                          <div className="text-lg font-semibold">{report.report_data.summary.total_meetings}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-500">已完成会议</div>
                          <div className="text-lg font-semibold">{report.report_data.summary.completed_meetings}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-500">行动项总数</div>
                          <div className="text-lg font-semibold">{report.report_data.summary.total_action_items}</div>
                        </div>
                        <div>
                          <div className="text-sm text-gray-500">完成率</div>
                          <div className="text-lg font-semibold">{report.report_data.summary.action_completion_rate}</div>
                        </div>
                      </div>
                    )}
                    {report.comparison_data && (
                      <div className="mt-4 p-4 bg-blue-50 rounded-lg">
                        <div className="font-medium mb-2">与上月对比 ({report.comparison_data.previous_period})</div>
                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 text-sm">
                          <div>
                            <div className="text-gray-600">会议数</div>
                            {renderComparison(report.comparison_data.meetings_comparison)}
                          </div>
                          <div>
                            <div className="text-gray-600">已完成会议</div>
                            {renderComparison(report.comparison_data.completed_meetings_comparison)}
                          </div>
                          <div>
                            <div className="text-gray-600">行动项</div>
                            {renderComparison(report.comparison_data.action_items_comparison)}
                          </div>
                          <div>
                            <div className="text-gray-600">完成率</div>
                            <div className="text-sm">
                              {report.comparison_data.completion_rate_comparison?.current} → {report.comparison_data.completion_rate_comparison?.previous}
                              <span className={report.comparison_data.completion_rate_comparison?.change_value > 0 ? 'text-green-600' : 'text-red-600'}>
                                {' '}{report.comparison_data.completion_rate_comparison?.change}
                              </span>
                            </div>
                          </div>
                        </div>
                      </div>
                    )}
                  </div>
                  <div className="flex gap-2 ml-4">
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={() => navigate(`/meeting-reports/${report.id}`)}
                    >
                      <Eye className="w-4 h-4 mr-1" />
                      查看
                    </Button>
                    <Button
                      variant="outline"
                      size="sm"
                      onClick={async () => {
                        try {
                          const blob = await managementRhythmApi.reports.exportDocx(report.id)
                          const url = window.URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = `${report.report_no}.docx`
                          document.body.appendChild(a)
                          a.click()
                          window.URL.revokeObjectURL(url)
                          document.body.removeChild(a)
                        } catch (err) {
                          alert('导出失败: ' + (err.response?.data?.detail || err.message))
                        }
                      }}
                    >
                      <Download className="w-4 h-4 mr-1" />
                      导出Word
                    </Button>
                  </div>
                </div>
              </CardContent>
            </Card>
          ))
        )}
      </div>

      {/* 分页 */}
      {total > pageSize && (
        <div className="flex items-center justify-between">
          <div className="text-sm text-gray-600">
            共 {total} 条记录，第 {page} / {Math.ceil(total / pageSize)} 页
          </div>
          <div className="flex gap-2">
            <Button
              variant="outline"
              disabled={page === 1}
              onClick={() => setPage(page - 1)}
            >
              上一页
            </Button>
            <Button
              variant="outline"
              disabled={page >= Math.ceil(total / pageSize)}
              onClick={() => setPage(page + 1)}
            >
              下一页
            </Button>
          </div>
        </div>
      )}

      {/* 生成报告对话框 */}
      <Dialog open={generateDialogOpen} onOpenChange={setGenerateDialogOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>生成会议报告</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <div>
              <label className="block text-sm font-medium mb-1">报告类型</label>
              <select
                value={generateForm.report_type}
                onChange={(e) => setGenerateForm({ ...generateForm, report_type: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="ANNUAL">年度报告</option>
                <option value="MONTHLY">月度报告</option>
              </select>
            </div>
            <div>
              <label className="block text-sm font-medium mb-1">年份</label>
              <input
                type="number"
                value={generateForm.period_year}
                onChange={(e) => setGenerateForm({ ...generateForm, period_year: parseInt(e.target.value) || new Date().getFullYear() })}
                className="w-full px-3 py-2 border rounded-lg"
              />
            </div>
            {generateForm.report_type === 'MONTHLY' && (
              <div>
                <label className="block text-sm font-medium mb-1">月份</label>
                <select
                  value={generateForm.period_month}
                  onChange={(e) => setGenerateForm({ ...generateForm, period_month: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border rounded-lg"
                >
                  {Array.from({ length: 12 }, (_, i) => i + 1).map((m) => (
                    <option key={m} value={m}>
                      {m}月
                    </option>
                  ))}
                </select>
              </div>
            )}
            <div>
              <label className="block text-sm font-medium mb-1">节律层级（可选）</label>
              <select
                value={generateForm.rhythm_level}
                onChange={(e) => setGenerateForm({ ...generateForm, rhythm_level: e.target.value })}
                className="w-full px-3 py-2 border rounded-lg"
              >
                <option value="">全部层级</option>
                <option value="STRATEGIC">战略层</option>
                <option value="OPERATIONAL">经营层</option>
                <option value="OPERATION">运营层</option>
                <option value="TASK">任务层</option>
              </select>
            </div>
            <div className="flex gap-2 justify-end">
              <Button variant="outline" onClick={() => setGenerateDialogOpen(false)}>
                取消
              </Button>
              <Button onClick={handleGenerate}>生成报告</Button>
            </div>
          </div>
        </DialogContent>
      </Dialog>
    </div>
  )
}
