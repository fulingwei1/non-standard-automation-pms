/**
 * Issue Statistics Snapshot Page - 问题统计快照查看页面
 * Features: 快照列表、历史趋势对比、快照详情、数据导出
 */
import { useState, useEffect, useMemo } from 'react'
import {
  Calendar,
  Download,
  TrendingUp,
  TrendingDown,
  BarChart3,
  FileText,
  Eye,
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
  DialogFooter,
} from '../components/ui/dialog'
import { formatDate } from '../lib/utils'
import { issueApi } from '../services/api'
import { SimpleLineChart, SimpleBarChart, SimplePieChart } from '../components/administrative/StatisticsCharts'
import { cn } from '../lib/utils'

export default function IssueStatisticsSnapshot() {
  const [loading, setLoading] = useState(true)
  const [snapshots, setSnapshots] = useState([])
  const [selectedSnapshot, setSelectedSnapshot] = useState(null)
  const [showDetailDialog, setShowDetailDialog] = useState(false)
  
  // Filters
  const [startDate, setStartDate] = useState(new Date(Date.now() - 30 * 24 * 60 * 60 * 1000).toISOString().split('T')[0])
  const [endDate, setEndDate] = useState(new Date().toISOString().split('T')[0])
  const [page, setPage] = useState(1)
  const [pageSize] = useState(20)
  const [total, setTotal] = useState(0)

  useEffect(() => {
    loadSnapshots()
  }, [startDate, endDate, page])

  const loadSnapshots = async () => {
    try {
      setLoading(true)
      const params = {
        page,
        page_size: pageSize,
        start_date: startDate,
        end_date: endDate,
      }
      const res = await issueApi.getSnapshots(params)
      const data = res.data?.data || res.data || res
      if (data && typeof data === 'object' && 'items' in data) {
        setSnapshots(data.items || [])
        setTotal(data.total || 0)
      } else if (Array.isArray(data)) {
        setSnapshots(data)
        setTotal(data.length)
      } else {
        setSnapshots([])
        setTotal(0)
      }
    } catch (error) {
      setSnapshots([])
    } finally {
      setLoading(false)
    }
  }

  const handleViewDetail = async (snapshotId) => {
    try {
      const res = await issueApi.getSnapshot(snapshotId)
      setSelectedSnapshot(res.data || res)
      setShowDetailDialog(true)
    } catch (error) {
      console.error('操作失败:', error)
    }
  }

  const handleExport = () => {
    // 导出快照数据为CSV
    const headers = ['日期', '总问题数', '待处理', '处理中', '已解决', '已关闭', '阻塞问题', '逾期问题']
    const rows = snapshots.map(s => [
      s.snapshot_date,
      s.total_issues,
      s.open_issues,
      s.processing_issues,
      s.resolved_issues,
      s.closed_issues,
      s.blocking_issues,
      s.overdue_issues,
    ])
    
    const csv = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')
    
    const blob = new Blob(['\ufeff' + csv], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `问题统计快照_${startDate}_${endDate}.csv`
    link.click()
  }

  // 计算趋势数据
  const trendData = useMemo(() => {
    if (snapshots.length < 2) return null
    
    const sorted = [...snapshots].sort((a, b) => 
      new Date(a.snapshot_date) - new Date(b.snapshot_date)
    )
    
    return {
      total: sorted.map(s => ({ date: s.snapshot_date, value: s.total_issues })),
      open: sorted.map(s => ({ date: s.snapshot_date, value: s.open_issues })),
      resolved: sorted.map(s => ({ date: s.snapshot_date, value: s.resolved_issues })),
      blocking: sorted.map(s => ({ date: s.snapshot_date, value: s.blocking_issues })),
    }
  }, [snapshots])

  // 计算对比数据（最新 vs 最早）
  const comparison = useMemo(() => {
    if (snapshots.length < 2) return null
    
    const sorted = [...snapshots].sort((a, b) => 
      new Date(a.snapshot_date) - new Date(b.snapshot_date)
    )
    const latest = sorted[sorted.length - 1]
    const earliest = sorted[0]
    
    return {
      total: { current: latest.total_issues, previous: earliest.total_issues },
      open: { current: latest.open_issues, previous: earliest.open_issues },
      resolved: { current: latest.resolved_issues, previous: earliest.resolved_issues },
      blocking: { current: latest.blocking_issues, previous: earliest.blocking_issues },
    }
  }, [snapshots])

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-900 via-slate-800 to-slate-900">
      <PageHeader
        title="问题统计快照"
        description="查看历史问题统计数据，分析趋势变化"
      />

      <div className="container mx-auto px-4 py-6 space-y-6">
        {/* Filters */}
        <Card className="bg-surface-50 border-white/5">
          <CardContent className="pt-6">
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <label className="text-sm text-slate-400 mb-1 block">开始日期</label>
                <Input
                  type="date"
                  value={startDate}
                  onChange={(e) => setStartDate(e.target.value)}
                  className="bg-surface-100 border-white/10 text-white"
                />
              </div>
              <div>
                <label className="text-sm text-slate-400 mb-1 block">结束日期</label>
                <Input
                  type="date"
                  value={endDate}
                  onChange={(e) => setEndDate(e.target.value)}
                  className="bg-surface-100 border-white/10 text-white"
                />
              </div>
              <div className="flex items-end">
                <Button
                  onClick={loadSnapshots}
                  className="bg-primary hover:bg-primary/90 w-full"
                >
                  查询
                </Button>
              </div>
              <div className="flex items-end">
                <Button
                  onClick={handleExport}
                  variant="outline"
                  className="border-white/10 text-slate-300 w-full"
                >
                  <Download className="w-4 h-4 mr-2" />
                  导出
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 趋势对比卡片 */}
        {comparison && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card className="bg-surface-50 border-white/5">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">总问题数</div>
                <div className="flex items-center justify-between">
                  <div className="text-2xl font-bold text-white">{comparison.total.current}</div>
                  {comparison.total.previous && (
                    <div className={cn(
                      "text-sm flex items-center gap-1",
                      comparison.total.current > comparison.total.previous ? "text-red-400" : "text-green-400"
                    )}>
                      {comparison.total.current > comparison.total.previous ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      {Math.abs(((comparison.total.current - comparison.total.previous) / comparison.total.previous * 100)).toFixed(1)}%
                    </div>
                  )}
                </div>
                {comparison.total.previous && (
                  <div className="text-xs text-slate-500 mt-1">
                    期初: {comparison.total.previous}
                  </div>
                )}
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/5">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">待处理</div>
                <div className="flex items-center justify-between">
                  <div className="text-2xl font-bold text-blue-400">{comparison.open.current}</div>
                  {comparison.open.previous && (
                    <div className={cn(
                      "text-sm flex items-center gap-1",
                      comparison.open.current > comparison.open.previous ? "text-red-400" : "text-green-400"
                    )}>
                      {comparison.open.current > comparison.open.previous ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      {Math.abs(((comparison.open.current - comparison.open.previous) / comparison.open.previous * 100)).toFixed(1)}%
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/5">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">已解决</div>
                <div className="flex items-center justify-between">
                  <div className="text-2xl font-bold text-green-400">{comparison.resolved.current}</div>
                  {comparison.resolved.previous && (
                    <div className={cn(
                      "text-sm flex items-center gap-1",
                      comparison.resolved.current > comparison.resolved.previous ? "text-green-400" : "text-red-400"
                    )}>
                      {comparison.resolved.current > comparison.resolved.previous ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      {Math.abs(((comparison.resolved.current - comparison.resolved.previous) / comparison.resolved.previous * 100)).toFixed(1)}%
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/5">
              <CardContent className="p-4">
                <div className="text-sm text-slate-400 mb-1">阻塞问题</div>
                <div className="flex items-center justify-between">
                  <div className="text-2xl font-bold text-red-400">{comparison.blocking.current}</div>
                  {comparison.blocking.previous && (
                    <div className={cn(
                      "text-sm flex items-center gap-1",
                      comparison.blocking.current > comparison.blocking.previous ? "text-red-400" : "text-green-400"
                    )}>
                      {comparison.blocking.current > comparison.blocking.previous ? <TrendingUp className="w-4 h-4" /> : <TrendingDown className="w-4 h-4" />}
                      {Math.abs(((comparison.blocking.current - comparison.blocking.previous) / comparison.blocking.previous * 100)).toFixed(1)}%
                    </div>
                  )}
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* 趋势图表 */}
        {trendData && (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Card className="bg-surface-50 border-white/5">
              <CardHeader>
                <CardTitle>问题总数趋势</CardTitle>
              </CardHeader>
              <CardContent>
                <SimpleLineChart
                  data={trendData.total.map(item => ({
                    label: item.date,
                    value: item.value,
                  }))}
                  height={200}
                  color="text-blue-400"
                />
              </CardContent>
            </Card>
            <Card className="bg-surface-50 border-white/5">
              <CardHeader>
                <CardTitle>待处理 vs 已解决</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-4">
                  <div>
                    <div className="text-xs text-blue-400 mb-1">待处理</div>
                    <SimpleLineChart
                      data={trendData.open.map(item => ({
                        label: item.date,
                        value: item.value,
                      }))}
                      height={100}
                      color="text-blue-400"
                    />
                  </div>
                  <div>
                    <div className="text-xs text-green-400 mb-1">已解决</div>
                    <SimpleLineChart
                      data={trendData.resolved.map(item => ({
                        label: item.date,
                        value: item.value,
                      }))}
                      height={100}
                      color="text-green-400"
                    />
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        )}

        {/* 快照列表 */}
        <Card className="bg-surface-50 border-white/5">
          <CardHeader>
            <CardTitle className="text-white">快照列表</CardTitle>
            <CardDescription className="text-slate-400">
              共 {total} 条记录
            </CardDescription>
          </CardHeader>
          <CardContent>
            {loading ? (
              <div className="text-center py-8 text-slate-400">加载中...</div>
            ) : snapshots.length === 0 ? (
              <div className="text-center py-8 text-slate-400">暂无快照数据</div>
            ) : (
              <>
                <Table>
                  <TableHeader>
                    <TableRow className="border-white/10">
                      <TableHead className="text-slate-300">快照日期</TableHead>
                      <TableHead className="text-slate-300">总问题数</TableHead>
                      <TableHead className="text-slate-300">待处理</TableHead>
                      <TableHead className="text-slate-300">处理中</TableHead>
                      <TableHead className="text-slate-300">已解决</TableHead>
                      <TableHead className="text-slate-300">已关闭</TableHead>
                      <TableHead className="text-slate-300">阻塞问题</TableHead>
                      <TableHead className="text-slate-300">逾期问题</TableHead>
                      <TableHead className="text-slate-300">今日新增</TableHead>
                      <TableHead className="text-slate-300">今日解决</TableHead>
                      <TableHead className="text-right text-slate-300">操作</TableHead>
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {snapshots.map((snapshot) => (
                      <TableRow key={snapshot.id} className="border-white/10 hover:bg-surface-100/50">
                        <TableCell className="text-white font-medium">
                          {snapshot.snapshot_date ? formatDate(snapshot.snapshot_date) : '-'}
                        </TableCell>
                        <TableCell className="text-slate-300">{snapshot.total_issues || 0}</TableCell>
                        <TableCell className="text-blue-400">{snapshot.open_issues || 0}</TableCell>
                        <TableCell className="text-yellow-400">{snapshot.processing_issues || 0}</TableCell>
                        <TableCell className="text-green-400">{snapshot.resolved_issues || 0}</TableCell>
                        <TableCell className="text-slate-300">{snapshot.closed_issues || 0}</TableCell>
                        <TableCell className="text-red-400">{snapshot.blocking_issues || 0}</TableCell>
                        <TableCell className="text-orange-400">{snapshot.overdue_issues || 0}</TableCell>
                        <TableCell className="text-slate-300">{snapshot.new_issues_today || 0}</TableCell>
                        <TableCell className="text-slate-300">{snapshot.resolved_today || 0}</TableCell>
                        <TableCell className="text-right">
                          <Button
                            variant="ghost"
                            size="sm"
                            onClick={() => handleViewDetail(snapshot.id)}
                            className="text-slate-300 hover:text-white"
                          >
                            <Eye className="w-4 h-4" />
                          </Button>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
                
                {/* 分页 */}
                {total > pageSize && (
                  <div className="flex items-center justify-between mt-4">
                    <div className="text-sm text-slate-400">
                      第 {page} 页，共 {Math.ceil(total / pageSize)} 页
                    </div>
                    <div className="flex gap-2">
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.max(1, p - 1))}
                        disabled={page === 1}
                        className="border-white/10 text-slate-300"
                      >
                        上一页
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setPage(p => Math.min(Math.ceil(total / pageSize), p + 1))}
                        disabled={page >= Math.ceil(total / pageSize)}
                        className="border-white/10 text-slate-300"
                      >
                        下一页
                      </Button>
                    </div>
                  </div>
                )}
              </>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 快照详情对话框 */}
      <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
        <DialogContent className="bg-surface-50 border-white/10 max-w-4xl max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="text-white">快照详情</DialogTitle>
          </DialogHeader>
          {selectedSnapshot && (
            <div className="space-y-6">
              {/* 基本信息 */}
              <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div>
                  <div className="text-sm text-slate-400 mb-1">快照日期</div>
                  <div className="text-white">{selectedSnapshot.snapshot_date ? formatDate(selectedSnapshot.snapshot_date) : '-'}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">总问题数</div>
                  <div className="text-2xl font-bold text-white">{selectedSnapshot.total_issues || 0}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">阻塞问题</div>
                  <div className="text-2xl font-bold text-red-400">{selectedSnapshot.blocking_issues || 0}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-400 mb-1">逾期问题</div>
                  <div className="text-2xl font-bold text-orange-400">{selectedSnapshot.overdue_issues || 0}</div>
                </div>
              </div>

              {/* 状态分布 */}
              {selectedSnapshot.status_distribution && (
                <Card className="bg-surface-100 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">状态分布</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <SimplePieChart
                      data={Object.entries(selectedSnapshot.status_distribution).map(([key, value], idx) => ({
                        label: key,
                        value: value,
                        color: `hsl(${idx * 60}, 70%, 50%)`,
                      }))}
                      size={250}
                    />
                  </CardContent>
                </Card>
              )}

              {/* 严重程度分布 */}
              {selectedSnapshot.severity_distribution && (
                <Card className="bg-surface-100 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">严重程度分布</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <SimpleBarChart
                      data={Object.entries(selectedSnapshot.severity_distribution).map(([key, value]) => ({
                        label: key,
                        value: value,
                      }))}
                      height={200}
                      color="bg-red-500"
                    />
                  </CardContent>
                </Card>
              )}

              {/* 详细统计表格 */}
              <Card className="bg-surface-100 border-white/10">
                <CardHeader>
                  <CardTitle className="text-white text-lg">详细统计</CardTitle>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
                    <div>
                      <div className="text-sm text-slate-400">待处理</div>
                      <div className="text-xl font-bold text-blue-400">{selectedSnapshot.open_issues || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400">处理中</div>
                      <div className="text-xl font-bold text-yellow-400">{selectedSnapshot.processing_issues || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400">已解决</div>
                      <div className="text-xl font-bold text-green-400">{selectedSnapshot.resolved_issues || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400">已关闭</div>
                      <div className="text-xl font-bold text-slate-300">{selectedSnapshot.closed_issues || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400">已取消</div>
                      <div className="text-xl font-bold text-slate-300">{selectedSnapshot.cancelled_issues || 0}</div>
                    </div>
                    <div>
                      <div className="text-sm text-slate-400">已延期</div>
                      <div className="text-xl font-bold text-slate-300">{selectedSnapshot.deferred_issues || 0}</div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 处理时间统计 */}
              {(selectedSnapshot.avg_resolve_time || selectedSnapshot.avg_response_time) && (
                <Card className="bg-surface-100 border-white/10">
                  <CardHeader>
                    <CardTitle className="text-white text-lg">处理时间统计</CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="grid grid-cols-3 gap-4">
                      {selectedSnapshot.avg_response_time && (
                        <div>
                          <div className="text-sm text-slate-400">平均响应时间</div>
                          <div className="text-xl font-bold text-white">
                            {selectedSnapshot.avg_response_time.toFixed(1)} 小时
                          </div>
                        </div>
                      )}
                      {selectedSnapshot.avg_resolve_time && (
                        <div>
                          <div className="text-sm text-slate-400">平均解决时间</div>
                          <div className="text-xl font-bold text-white">
                            {selectedSnapshot.avg_resolve_time.toFixed(1)} 小时
                          </div>
                        </div>
                      )}
                      {selectedSnapshot.avg_verify_time && (
                        <div>
                          <div className="text-sm text-slate-400">平均验证时间</div>
                          <div className="text-xl font-bold text-white">
                            {selectedSnapshot.avg_verify_time.toFixed(1)} 小时
                          </div>
                        </div>
                      )}
                    </div>
                  </CardContent>
                </Card>
              )}
            </div>
          )}
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDetailDialog(false)}
              className="border-white/10 text-slate-300"
            >
              关闭
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  )
}
