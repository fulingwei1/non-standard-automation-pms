/**
 * Production Dashboard Page - 生产驾驶舱页面
 * Features: 生产经理总览看板，包含统计、异常、关键项目、设备状态
 */
import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import {
  Factory,
  TrendingUp,
  TrendingDown,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Users,
  Wrench,
  Package,
  BarChart3,
  RefreshCw,
  Eye,
  ArrowRight,
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
import { ApiIntegrationError } from '../components/ui'
import { cn, formatDate } from '../lib/utils'
import { productionApi } from '../services/api'
export default function ProductionDashboard() {
  const navigate = useNavigate()
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState(null)
  const [dashboardData, setDashboardData] = useState(null)
  const fetchDashboardData = async () => {
    try {
      setLoading(true)
      setError(null)
      const res = await productionApi.dashboard()
      // Handle different response formats
      const data = res.data?.data || res.data || res
      setDashboardData(data)
    } catch (error) {
      console.error('生产驾驶舱 API 调用失败:', error)
      setError(error)
      setDashboardData(null) // 清空数据
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    fetchDashboardData()
  }, [])
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6">
          <PageHeader
            title="生产驾驶舱"
            description="生产管理总览看板，实时监控生产状态"
          />
          <div className="text-center py-16 text-slate-400">加载中...</div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6 space-y-6">
          <PageHeader
            title="生产驾驶舱"
            description="生产管理总览看板，实时监控生产状态"
          />
          <ApiIntegrationError
            error={error}
            apiEndpoint="/api/v1/production/dashboard"
            onRetry={fetchDashboardData}
          />
        </div>
      </div>
    )
  }

  if (!dashboardData) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
        <div className="container mx-auto px-4 py-6 space-y-6">
          <PageHeader
            title="生产驾驶舱"
            description="生产管理总览看板，实时监控生产状态"
          />
          <Card>
            <CardContent className="p-12 text-center">
              <Factory className="w-16 h-16 mx-auto text-slate-600 mb-4" />
              <h3 className="text-lg font-medium text-slate-400">暂无数据</h3>
              <p className="text-sm text-slate-500 mt-1">请稍后重试或联系管理员</p>
              <Button
                variant="outline"
                className="mt-4"
                onClick={fetchDashboardData}
              >
                <RefreshCw className="w-4 h-4 mr-2" />
                刷新
              </Button>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }
  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-slate-950">
      <div className="container mx-auto px-4 py-6 space-y-6">
      <div className="flex items-center justify-between">
        <PageHeader
          title="生产驾驶舱"
          description="生产管理总览看板，实时监控生产状态"
        />
        <Button variant="outline" onClick={fetchDashboardData}>
          <RefreshCw className="w-4 h-4 mr-2" />
          刷新
        </Button>
      </div>
      {/* Overview Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">车间总数</div>
                <div className="text-2xl font-bold">{dashboardData.total_workshops || 0}</div>
              </div>
              <Factory className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">工位总数</div>
                <div className="text-2xl font-bold">{dashboardData.total_workstations || 0}</div>
              </div>
              <Wrench className="w-8 h-8 text-purple-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">在岗工人</div>
                <div className="text-2xl font-bold text-emerald-600">
                  {dashboardData.active_workers || 0} / {dashboardData.total_workers || 0}
                </div>
              </div>
              <Users className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">设备总数</div>
                <div className="text-2xl font-bold">{dashboardData.total_equipment || 0}</div>
              </div>
              <Package className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Work Order Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">总工单数</div>
                <div className="text-2xl font-bold">{dashboardData.total_work_orders || 0}</div>
              </div>
              <BarChart3 className="w-8 h-8 text-slate-400" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">待派工</div>
                <div className="text-2xl font-bold text-blue-600">
                  {dashboardData.pending_orders || 0}
                </div>
              </div>
              <Clock className="w-8 h-8 text-blue-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">进行中</div>
                <div className="text-2xl font-bold text-amber-600">
                  {dashboardData.in_progress_orders || 0}
                </div>
              </div>
              <TrendingUp className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">已完成</div>
                <div className="text-2xl font-bold text-emerald-600">
                  {dashboardData.completed_orders || 0}
                </div>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Today Statistics */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">今日计划</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.today_plan_qty || 0}</div>
            <div className="text-xs text-slate-500 mt-1">计划数量</div>
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">今日完成</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-emerald-600">
              {dashboardData.today_completed_qty || 0}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              完成率: {dashboardData.today_completion_rate?.toFixed(1) || 0}%
            </div>
            <Progress 
              value={dashboardData.today_completion_rate || 0} 
              className="h-2 mt-2" 
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">今日合格</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold text-blue-600">
              {dashboardData.today_qualified_qty || 0}
            </div>
            <div className="text-xs text-slate-500 mt-1">
              合格率: {dashboardData.today_pass_rate?.toFixed(1) || 0}%
            </div>
            <Progress 
              value={dashboardData.today_pass_rate || 0} 
              className="h-2 mt-2" 
            />
          </CardContent>
        </Card>
        <Card>
          <CardHeader>
            <CardTitle className="text-sm">今日工时</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{dashboardData.today_actual_hours?.toFixed(1) || 0}</div>
            <div className="text-xs text-slate-500 mt-1">实际工时（小时）</div>
          </CardContent>
        </Card>
      </div>
      {/* Equipment Status */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">运行中</div>
                <div className="text-2xl font-bold text-emerald-600">
                  {dashboardData.running_equipment || 0}
                </div>
              </div>
              <CheckCircle2 className="w-8 h-8 text-emerald-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">保养中</div>
                <div className="text-2xl font-bold text-amber-600">
                  {dashboardData.maintenance_equipment || 0}
                </div>
              </div>
              <Wrench className="w-8 h-8 text-amber-500" />
            </div>
          </CardContent>
        </Card>
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center justify-between">
              <div>
                <div className="text-sm text-slate-500 mb-1">故障</div>
                <div className="text-2xl font-bold text-red-600">
                  {dashboardData.fault_equipment || 0}
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
                <div className="text-sm text-slate-500 mb-1">异常总数</div>
                <div className="text-2xl font-bold text-red-600">
                  {dashboardData.open_exceptions || 0}
                </div>
                <div className="text-xs text-slate-500 mt-1">
                  严重: {dashboardData.critical_exceptions || 0}
                </div>
              </div>
              <AlertTriangle className="w-8 h-8 text-red-500" />
            </div>
          </CardContent>
        </Card>
      </div>
      {/* Quick Actions */}
      <Card>
        <CardHeader>
          <CardTitle>快速操作</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate('/work-orders')}
            >
              <Package className="w-6 h-6 mb-2" />
              <span>工单管理</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate('/production-plans')}
            >
              <BarChart3 className="w-6 h-6 mb-2" />
              <span>生产计划</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate('/work-reports')}
            >
              <CheckCircle2 className="w-6 h-6 mb-2" />
              <span>报工管理</span>
            </Button>
            <Button
              variant="outline"
              className="h-auto py-4 flex-col"
              onClick={() => navigate('/material-requisitions')}
            >
              <Package className="w-6 h-6 mb-2" />
              <span>领料管理</span>
            </Button>
          </div>
        </CardContent>
      </Card>
      </div>
    </div>
  )
}

