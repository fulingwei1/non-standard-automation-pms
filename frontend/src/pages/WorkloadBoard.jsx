/**
 * Workload Board Page - 资源负荷看板页面
 * Features: 团队负荷统计、负荷热力图、可用资源查询
 */
import { useState, useEffect } from 'react'
import {
  Users,
  AlertTriangle,
  CheckCircle2,
  RefreshCw,
  BarChart3,
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
import { cn } from '../lib/utils'
import { workloadApi } from '../services/api'
export default function WorkloadBoard() {
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState(null)
  const [teamWorkload, setTeamWorkload] = useState([])
  const [selectedDept, setSelectedDept] = useState('')
  const [dateRange, setDateRange] = useState({
    start: new Date(new Date().getFullYear(), new Date().getMonth(), 1).toISOString().split('T')[0],
    end: new Date(new Date().getFullYear(), new Date().getMonth() + 1, 0).toISOString().split('T')[0],
  })
  useEffect(() => {
    fetchDashboardData()
    fetchTeamWorkload()
  }, [selectedDept, dateRange])
  const fetchDashboardData = async () => {
    try {
      const params = {}
      if (selectedDept) params.dept_id = selectedDept
      if (dateRange.start) params.start_date = dateRange.start
      if (dateRange.end) params.end_date = dateRange.end
      const res = await workloadApi.dashboard(params)
      setDashboardData(res.data || res)
    } catch (error) {
      console.error('Failed to fetch dashboard data:', error)
    }
  }
  const fetchTeamWorkload = async () => {
    try {
      setLoading(true)
      const params = {}
      if (selectedDept) params.dept_id = selectedDept
      if (dateRange.start) params.start_date = dateRange.start
      if (dateRange.end) params.end_date = dateRange.end
      const res = await workloadApi.team(params)
      const teamList = res.data?.items || res.data || []
      setTeamWorkload(teamList)
    } catch (error) {
      console.error('Failed to fetch team workload:', error)
    } finally {
      setLoading(false)
    }
  }
  const getLoadStatus = (rate) => {
    if (rate >= 120) return { label: '超负荷', color: 'bg-red-500', textColor: 'text-red-600' }
    if (rate >= 100) return { label: '满负荷', color: 'bg-orange-500', textColor: 'text-orange-600' }
    if (rate >= 80) return { label: '正常', color: 'bg-emerald-500', textColor: 'text-emerald-600' }
    return { label: '空闲', color: 'bg-blue-500', textColor: 'text-blue-600' }
  }
  if (loading) {
    return (
      <div className="space-y-6 p-6">
        <div className="text-center py-8 text-slate-400">加载中...</div>
      </div>
    )
  }
  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="资源负荷看板"
          description="团队负荷统计、负荷热力图、可用资源查询"
        />
        <Button variant="outline" onClick={() => {
          fetchDashboardData()
          fetchTeamWorkload()
        }}>
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>
      {/* Filters */}
      <Card>
        <CardContent className="pt-6">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">开始日期</label>
              <input
                type="date"
                value={dateRange.start}
                onChange={(e) => setDateRange({ ...dateRange, start: e.target.value })}
                className="w-full p-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">结束日期</label>
              <input
                type="date"
                value={dateRange.end}
                onChange={(e) => setDateRange({ ...dateRange, end: e.target.value })}
                className="w-full p-2 border rounded-lg"
              />
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">部门</label>
              <Select value={selectedDept} onValueChange={setSelectedDept}>
                <SelectTrigger>
                  <SelectValue placeholder="全部部门" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="">全部部门</SelectItem>
                  {/* 这里可以从API获取部门列表 */}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardContent>
      </Card>
      {/* Summary Statistics */}
      {dashboardData && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">总人数</div>
                  <div className="text-2xl font-bold">{dashboardData.summary?.total_users || teamWorkload.length}</div>
                </div>
                <Users className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">平均分配率</div>
                  <div className="text-2xl font-bold">
                    {dashboardData.summary?.avg_allocation_rate?.toFixed(1) || 0}%
                  </div>
                </div>
                <BarChart3 className="w-8 h-8 text-purple-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">超负荷人数</div>
                  <div className="text-2xl font-bold text-red-600">
                    {dashboardData.summary?.overload_count || teamWorkload.filter(u => u.allocation_rate >= 120).length}
                  </div>
                </div>
                <AlertTriangle className="w-8 h-8 text-red-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">空闲人数</div>
                  <div className="text-2xl font-bold text-emerald-600">
                    {dashboardData.summary?.idle_count || teamWorkload.filter(u => u.allocation_rate < 80).length}
                  </div>
                </div>
                <CheckCircle2 className="w-8 h-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      {/* Team Workload Table */}
      <Card>
        <CardHeader>
          <CardTitle>团队负荷统计</CardTitle>
        </CardHeader>
        <CardContent>
          {teamWorkload.length === 0 ? (
            <div className="text-center py-8 text-slate-400">暂无数据</div>
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>姓名</TableHead>
                  <TableHead>部门</TableHead>
                  <TableHead>角色</TableHead>
                  <TableHead>分配工时</TableHead>
                  <TableHead>标准工时</TableHead>
                  <TableHead>分配率</TableHead>
                  <TableHead>任务数</TableHead>
                  <TableHead>逾期任务</TableHead>
                  <TableHead>状态</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {teamWorkload.map((user) => {
                  const status = getLoadStatus(user.allocation_rate)
                  return (
                    <TableRow key={user.user_id}>
                      <TableCell className="font-medium">{user.user_name}</TableCell>
                      <TableCell>{user.dept_name || '-'}</TableCell>
                      <TableCell>{user.role || '-'}</TableCell>
                      <TableCell>{user.assigned_hours?.toFixed(1) || 0}h</TableCell>
                      <TableCell>{user.standard_hours?.toFixed(1) || 0}h</TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className="flex items-center justify-between text-xs">
                            <span className={status.textColor}>{user.allocation_rate?.toFixed(1) || 0}%</span>
                            <Badge className={status.color}>{status.label}</Badge>
                          </div>
                          <Progress
                            value={Math.min(user.allocation_rate || 0, 150)}
                            className={cn(
                              "h-1.5",
                              user.allocation_rate >= 120 && "bg-red-500",
                              user.allocation_rate >= 100 && user.allocation_rate < 120 && "bg-orange-500",
                              user.allocation_rate >= 80 && user.allocation_rate < 100 && "bg-emerald-500",
                              user.allocation_rate < 80 && "bg-blue-500"
                            )}
                          />
                        </div>
                      </TableCell>
                      <TableCell>{user.task_count || 0}</TableCell>
                      <TableCell>
                        {user.overdue_count > 0 ? (
                          <Badge variant="destructive">{user.overdue_count}</Badge>
                        ) : (
                          <span className="text-slate-400">0</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge className={status.color}>{status.label}</Badge>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  )
}
