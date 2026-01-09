/**
 * Mobile Progress Report - 移动端进度上报
 * 功能：上报工单进度和工时
 */
import { useState, useEffect } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import {
  ArrowLeft,
  TrendingUp,
  CheckCircle2,
  AlertCircle,
} from 'lucide-react'
import { Button } from '../../components/ui/button'
import { Input } from '../../components/ui/input'
import { Card, CardContent } from '../../components/ui/card'
import { Badge } from '../../components/ui/badge'
import { cn } from '../../lib/utils'
import { productionApi } from '../../services/api'

export default function MobileProgressReport() {
  const navigate = useNavigate()
  const [searchParams] = useSearchParams()
  const workOrderId = searchParams.get('workOrderId')
  
  const [loading, setLoading] = useState(false)
  const [workOrder, setWorkOrder] = useState(null)
  const [error, setError] = useState('')
  const [success, setSuccess] = useState(false)
  const [formData, setFormData] = useState({
    progress_percent: 0,
    work_hours: 0,
    report_note: '',
  })

  useEffect(() => {
    if (workOrderId) {
      fetchWorkOrder()
    }
  }, [workOrderId])

  const fetchWorkOrder = async () => {
    try {
      const res = await productionApi.workOrders.get(workOrderId)
      const order = res.data
      setWorkOrder(order)
      
      // 自动填充当前进度和工时
      const autoProgress = order.progress || 0
      const autoHours = order.actual_start_time 
        ? calculateWorkHours(order.actual_start_time)
        : 0
      
      setFormData({
        progress_percent: autoProgress,
        work_hours: autoHours,
        report_note: '',
      })
    } catch (error) {
      setError('获取工单信息失败')
    }
  }

  const calculateWorkHours = (startTime) => {
    if (!startTime) return 0
    const start = new Date(startTime)
    const now = new Date()
    const diffMs = now - start
    const diffHours = diffMs / (1000 * 60 * 60)
    return Math.round(diffHours * 10) / 10
  }

  const handleSubmit = async () => {
    if (!formData.progress_percent && !formData.work_hours) {
      setError('请填写进度或工时')
      return
    }
    
    try {
      setLoading(true)
      setError('')
      await productionApi.workReports.progress({
        work_order_id: workOrderId,
        progress_percent: formData.progress_percent,
        work_hours: formData.work_hours,
        report_note: formData.report_note,
      })
      setSuccess(true)
      setTimeout(() => {
        navigate('/mobile/tasks')
      }, 1500)
    } catch (error) {
      setError('进度上报失败: ' + (error.response?.data?.detail || error.message))
    } finally {
      setLoading(false)
    }
  }

  if (!workOrder) {
    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center">
        <div className="text-slate-400">加载中...</div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-slate-50">
      {/* 顶部导航栏 */}
      <div className="sticky top-0 z-10 bg-white border-b border-slate-200 shadow-sm">
        <div className="flex items-center justify-between px-4 py-3">
          <div className="flex items-center gap-3">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => navigate(-1)}
              className="p-2"
            >
              <ArrowLeft className="w-5 h-5" />
            </Button>
            <h1 className="text-lg font-semibold">进度上报</h1>
          </div>
        </div>
      </div>

      <div className="p-4 space-y-4">
        {/* 工单信息 */}
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-3">
              <div>
                <div className="text-sm text-slate-500 mb-1">工单号</div>
                <div className="font-mono text-base">{workOrder.work_order_no}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">任务名称</div>
                <div className="font-medium text-base">{workOrder.task_name}</div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">计划数量</div>
                <div className="font-medium text-base">{workOrder.plan_qty || 0}</div>
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 错误提示 */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 flex items-start gap-3">
            <AlertCircle className="w-5 h-5 text-red-500 flex-shrink-0 mt-0.5" />
            <div className="flex-1">
              <div className="text-sm font-medium text-red-800">{error}</div>
            </div>
          </div>
        )}

        {/* 成功提示 */}
        {success && (
          <div className="bg-emerald-50 border border-emerald-200 rounded-lg p-4 flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-emerald-500" />
            <div className="flex-1">
              <div className="text-sm font-medium text-emerald-800">进度上报成功！</div>
            </div>
          </div>
        )}

        {/* 表单 */}
        <Card>
          <CardContent className="pt-6">
            <div className="space-y-6">
              {/* 进度 */}
              <div>
                <label className="text-sm font-medium mb-2 block">进度 (%)</label>
                <Input
                  type="number"
                  min="0"
                  max="100"
                  value={formData.progress_percent}
                  onChange={(e) => setFormData({ ...formData, progress_percent: parseInt(e.target.value) || 0 })}
                  placeholder="0-100"
                  className="text-lg mb-3"
                />
                <div className="flex gap-2">
                  {[0, 25, 50, 75, 100].map((val) => (
                    <Button
                      key={val}
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setFormData({ ...formData, progress_percent: val })}
                      className={cn(
                        "flex-1",
                        formData.progress_percent === val && "bg-blue-50 border-blue-500"
                      )}
                    >
                      {val}%
                    </Button>
                  ))}
                </div>
              </div>

              {/* 工时 */}
              <div>
                <label className="text-sm font-medium mb-2 block">
                  工时 (小时)
                  {workOrder.actual_start_time && (
                    <span className="text-xs text-slate-500 ml-2">
                      已用: {calculateWorkHours(workOrder.actual_start_time)}h
                    </span>
                  )}
                </label>
                <Input
                  type="number"
                  min="0"
                  step="0.5"
                  value={formData.work_hours}
                  onChange={(e) => setFormData({ ...formData, work_hours: parseFloat(e.target.value) || 0 })}
                  placeholder="0"
                  className="text-lg"
                />
              </div>

              {/* 说明 */}
              <div>
                <label className="text-sm font-medium mb-2 block">进度说明（可选）</label>
                <textarea
                  className="w-full min-h-[100px] p-3 border rounded-lg resize-none focus:outline-none focus:ring-2 focus:ring-blue-500"
                  value={formData.report_note}
                  onChange={(e) => setFormData({ ...formData, report_note: e.target.value })}
                  placeholder="填写进度说明..."
                />
              </div>
            </div>
          </CardContent>
        </Card>

        {/* 提交按钮 */}
        <Button
          onClick={handleSubmit}
          disabled={loading}
          className="w-full bg-blue-500 hover:bg-blue-600 h-12 text-base"
        >
          <TrendingUp className="w-5 h-5 mr-2" />
          {loading ? '提交中...' : '提交进度'}
        </Button>
      </div>
    </div>
  )
}

