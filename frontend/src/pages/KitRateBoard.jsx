/**
 * Kit Rate Board Page - 齐套看板页面
 * Features: 齐套率分布、缺料预警汇总
 */
import { useState, useEffect } from 'react'
import {
  Package,
  AlertTriangle,
  CheckCircle2,
  TrendingUp,
  TrendingDown,
  RefreshCw,
  Filter,
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
import { cn, formatCurrency } from '../lib/utils'
import { purchaseApi, projectApi } from '../services/api'
export default function KitRateBoard() {
  const [loading, setLoading] = useState(true)
  const [dashboardData, setDashboardData] = useState(null)
  const [projects, setProjects] = useState([])
  const [filterProject, setFilterProject] = useState('')
  useEffect(() => {
    fetchProjects()
    fetchDashboardData()
  }, [filterProject])
  const fetchProjects = async () => {
    try {
      const res = await projectApi.list({ page_size: 1000 })
      setProjects(res.data?.items || res.data || [])
    } catch (error) {
      console.error('操作失败:', error)
    }
  }
  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      const params = {}
      if (filterProject) params.project_id = filterProject
      const res = await purchaseApi.kitRate.dashboard(params)
      setDashboardData(res.data || res || null)
    } catch (error) {
      setDashboardData(null) // 不再使用mock数据，显示空状态
    } finally {
      setLoading(false)
    }
  }
  const getKitRateColor = (rate) => {
    if (rate >= 90) return 'text-emerald-600'
    if (rate >= 70) return 'text-amber-600'
    return 'text-red-600'
  }
  const getKitRateBadge = (rate) => {
    if (rate >= 90) return { label: '良好', color: 'bg-emerald-500' }
    if (rate >= 70) return { label: '一般', color: 'bg-amber-500' }
    return { label: '不足', color: 'bg-red-500' }
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
          title="齐套看板"
          description="齐套率分布、缺料预警汇总、物料保障情况"
        />
        <div className="flex items-center gap-4">
          <Select value={filterProject} onValueChange={setFilterProject}>
            <SelectTrigger className="w-[200px]">
              <SelectValue placeholder="选择项目" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部项目</SelectItem>
              {projects.map((proj) => (
                <SelectItem key={proj.id} value={proj.id.toString()}>
                  {proj.project_name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          <Button variant="outline" onClick={fetchDashboardData}>
            <RefreshCw className="w-4 h-4 mr-2" />
            刷新
          </Button>
        </div>
      </div>
      {/* Statistics Cards */}
      {dashboardData?.summary && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">平均齐套率</div>
                  <div className={cn("text-2xl font-bold", getKitRateColor(dashboardData.summary.avg_kit_rate || 0))}>
                    {dashboardData.summary.avg_kit_rate || 0}%
                  </div>
                </div>
                <BarChart3 className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">缺料预警</div>
                  <div className="text-2xl font-bold text-red-600">
                    {dashboardData.summary.shortage_alerts || 0}
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
                  <div className="text-sm text-slate-500 mb-1">在途物料</div>
                  <div className="text-2xl font-bold text-blue-600">
                    {dashboardData.summary.in_transit_materials || 0}
                  </div>
                </div>
                <Package className="w-8 h-8 text-blue-500" />
              </div>
            </CardContent>
          </Card>
          <Card>
            <CardContent className="pt-6">
              <div className="flex items-center justify-between">
                <div>
                  <div className="text-sm text-slate-500 mb-1">已齐套项目</div>
                  <div className="text-2xl font-bold text-emerald-600">
                    {dashboardData.summary.ready_projects || 0}
                  </div>
                </div>
                <CheckCircle2 className="w-8 h-8 text-emerald-500" />
              </div>
            </CardContent>
          </Card>
        </div>
      )}
      {/* Kit Rate Distribution */}
      <Card>
        <CardHeader>
          <CardTitle>齐套率分布</CardTitle>
        </CardHeader>
        <CardContent>
          {dashboardData?.projects && dashboardData.projects.length > 0 ? (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>项目名称</TableHead>
                  <TableHead>机台</TableHead>
                  <TableHead>齐套率</TableHead>
                  <TableHead>缺料项</TableHead>
                  <TableHead>在途物料</TableHead>
                  <TableHead>状态</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {dashboardData.projects.map((item) => {
                  const badge = getKitRateBadge(item.kit_rate || 0)
                  return (
                    <TableRow key={item.id}>
                      <TableCell className="font-medium">{item.project_name}</TableCell>
                      <TableCell>{item.machine_name || '-'}</TableCell>
                      <TableCell>
                        <div className="space-y-1">
                          <div className={cn("font-bold", getKitRateColor(item.kit_rate || 0))}>
                            {item.kit_rate || 0}%
                          </div>
                          <Progress value={item.kit_rate || 0} className="h-1.5" />
                        </div>
                      </TableCell>
                      <TableCell>
                        {item.shortage_count > 0 ? (
                          <Badge className="bg-red-500">{item.shortage_count} 项</Badge>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        {item.in_transit_count > 0 ? (
                          <Badge variant="outline">{item.in_transit_count} 项</Badge>
                        ) : (
                          <span className="text-slate-400">-</span>
                        )}
                      </TableCell>
                      <TableCell>
                        <Badge className={badge.color}>{badge.label}</Badge>
                      </TableCell>
                    </TableRow>
                  )
                })}
              </TableBody>
            </Table>
          ) : (
            <div className="text-center py-8 text-slate-400">暂无数据</div>
          )}
        </CardContent>
      </Card>
      {/* Shortage Alerts */}
      {dashboardData?.alerts && dashboardData.alerts.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-500" />
              缺料预警
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {dashboardData.alerts.map((alert) => (
                <div
                  key={alert.id}
                  className="border-l-4 border-red-500 bg-red-50 p-4 rounded-r-lg"
                >
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-medium">{alert.project_name}</h3>
                        <Badge className="bg-red-500">{alert.level}</Badge>
                      </div>
                      <div className="text-sm text-slate-600 mb-1">
                        {alert.material_name} - 缺料 {alert.shortage_qty} {alert.unit}
                      </div>
                      <div className="text-xs text-slate-500">
                        需求日期: {alert.required_date}
                      </div>
                    </div>
                    <div className="text-right">
                      <div className="text-sm font-medium text-red-600">
                        {alert.urgency}
                      </div>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}
