/**
 * ECNIntegrationTab Component
 * ECN 模块集成 Tab 组件
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card'
import { Button } from '../ui/button'
import { GitBranch, TrendingUp, DollarSign, Layers } from 'lucide-react'
import { ecnApi } from '../../services/api'

export default function ECNIntegrationTab({
  ecnId,
  ecn,
  affectedMaterials,
  affectedOrders,
  refetch,
}) {
  // 同步到BOM
  const handleSyncBom = async () => {
    try {
      const result = await ecnApi.syncToBOM(ecnId)
      const message = result.data?.message || result.message || '已同步到BOM'
      alert(message)
      await refetch()
    } catch (error) {
      alert('同步失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 同步到项目
  const handleSyncProject = async () => {
    try {
      const result = await ecnApi.syncToProject(ecnId)
      const message = result.data?.message || result.message || '已同步到项目'
      alert(message)
      await refetch()
    } catch (error) {
      alert('同步失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 同步到采购
  const handleSyncPurchase = async () => {
    try {
      const result = await ecnApi.syncToPurchase(ecnId)
      const message = result.data?.message || result.message || '已同步到采购'
      alert(message)
      await refetch()
    } catch (error) {
      alert('同步失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 批量同步
  const handleBatchSync = async () => {
    if (!confirm('确认要同步到所有相关模块吗？')) return

    try {
      const results = []

      // 同步到BOM
      if (affectedMaterials.length > 0) {
        try {
          await ecnApi.syncToBOM(ecnId)
          results.push('BOM同步成功')
        } catch (e) {
          results.push('BOM同步失败: ' + (e.response?.data?.detail || e.message))
        }
      }

      // 同步到项目
      if (ecn?.project_id) {
        try {
          await ecnApi.syncToProject(ecnId)
          results.push('项目同步成功')
        } catch (e) {
          results.push('项目同步失败: ' + (e.response?.data?.detail || e.message))
        }
      }

      // 同步到采购
      const purchaseOrders = affectedOrders.filter(
        (o) => o.order_type === 'PURCHASE'
      )
      if (purchaseOrders.length > 0) {
        try {
          await ecnApi.syncToPurchase(ecnId)
          results.push('采购同步成功')
        } catch (e) {
          results.push('采购同步失败: ' + (e.response?.data?.detail || e.message))
        }
      }

      alert(results.join('\n'))
      await refetch()
    } catch (error) {
      alert('批量同步失败: ' + (error.response?.data?.detail || error.message))
    }
  }

  // 判断是否可以同步
  const canSync =
    ecn?.status === 'APPROVED' || ecn?.status === 'EXECUTING'

  return (
    <div className="space-y-4">
      <Card>
        <CardHeader>
          <CardTitle className="text-base">模块集成操作</CardTitle>
          <CardDescription>将ECN变更同步到相关模块</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4">
          {/* BOM同步 */}
          <Card className="border-2">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <GitBranch className="w-5 h-5 text-blue-600" />
                  </div>
                  <div>
                    <div className="font-semibold">同步到BOM</div>
                    <div className="text-sm text-slate-500">
                      将物料变更同步到BOM清单
                    </div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  onClick={handleSyncBom}
                  disabled={!canSync}
                >
                  执行同步
                </Button>
              </div>
              {affectedMaterials.length > 0 && (
                <div className="text-sm text-slate-500">
                  将同步 {affectedMaterials.length} 个物料变更
                </div>
              )}
            </CardContent>
          </Card>

          {/* 项目同步 */}
          <Card className="border-2">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-green-100 flex items-center justify-center">
                    <TrendingUp className="w-5 h-5 text-green-600" />
                  </div>
                  <div>
                    <div className="font-semibold">同步到项目</div>
                    <div className="text-sm text-slate-500">更新项目成本和工期</div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  onClick={handleSyncProject}
                  disabled={!ecn?.project_id || !canSync}
                >
                  执行同步
                </Button>
              </div>
              {ecn?.cost_impact > 0 && (
                <div className="text-sm text-slate-500">
                  将更新项目成本: +¥{ecn.cost_impact}
                </div>
              )}
              {ecn?.schedule_impact_days > 0 && (
                <div className="text-sm text-slate-500">
                  将更新项目工期: +{ecn.schedule_impact_days} 天
                </div>
              )}
            </CardContent>
          </Card>

          {/* 采购同步 */}
          <Card className="border-2">
            <CardContent className="pt-4">
              <div className="flex items-center justify-between mb-3">
                <div className="flex items-center gap-3">
                  <div className="w-10 h-10 rounded-full bg-orange-100 flex items-center justify-center">
                    <DollarSign className="w-5 h-5 text-orange-600" />
                  </div>
                  <div>
                    <div className="font-semibold">同步到采购</div>
                    <div className="text-sm text-slate-500">调整受影响的采购订单</div>
                  </div>
                </div>
                <Button
                  variant="outline"
                  onClick={handleSyncPurchase}
                  disabled={!canSync}
                >
                  执行同步
                </Button>
              </div>
              {affectedOrders.filter((o) => o.order_type === 'PURCHASE').length >
                0 && (
                <div className="text-sm text-slate-500">
                  将处理{' '}
                  {affectedOrders.filter((o) => o.order_type === 'PURCHASE')
                    .length}{' '}
                  个采购订单
                </div>
              )}
            </CardContent>
          </Card>

          {/* 批量同步 */}
          <Card>
            <CardHeader>
              <CardTitle className="text-base">批量同步</CardTitle>
              <CardDescription>一次性同步到所有相关模块</CardDescription>
            </CardHeader>
            <CardContent>
              <Button
                className="w-full"
                onClick={handleBatchSync}
                disabled={!canSync}
              >
                <Layers className="w-4 h-4 mr-2" />
                批量同步所有模块
              </Button>
            </CardContent>
          </Card>
        </CardContent>
      </Card>
    </div>
  )
}
