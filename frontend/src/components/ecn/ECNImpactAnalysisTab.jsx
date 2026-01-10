/**
 * ECNImpactAnalysisTab Component
 * ECN 影响分析 Tab 组件
 */
import { Card, CardContent, CardHeader, CardTitle } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Plus, Edit2, XCircle, GitBranch, AlertTriangle, Users, FileText } from 'lucide-react'
import { useECNImpact } from './hooks/useECNImpact'
import MaterialDialog from './dialogs/MaterialDialog'
import OrderDialog from './dialogs/OrderDialog'
import ResponsibilityDialog from './dialogs/ResponsibilityDialog'
import RcaDialog from './dialogs/RcaDialog'

export default function ECNImpactAnalysisTab({
  ecnId,
  ecn,
  affectedMaterials,
  affectedOrders,
  refetch,
}) {
  const {
    analyzingBom,
    bomImpactSummary,
    obsoleteAlerts,
    responsibilitySummary,
    rcaAnalysis,
    showResponsibilityDialog,
    setShowResponsibilityDialog,
    responsibilityForm,
    setResponsibilityForm,
    handleCreateResponsibility,
    showRcaDialog,
    setShowRcaDialog,
    rcaForm,
    setRcaForm,
    handleSaveRcaAnalysis,
    showMaterialDialog,
    setShowMaterialDialog,
    showOrderDialog,
    setShowOrderDialog,
    materialForm,
    setMaterialForm,
    orderForm,
    setOrderForm,
    editingMaterial,
    editingOrder,
    handleAnalyzeBomImpact,
    handleCheckObsoleteRisk,
    handleAddMaterial,
    handleEditMaterial,
    handleSaveMaterial,
    handleDeleteMaterial,
    handleAddOrder,
    handleEditOrder,
    handleSaveOrder,
    handleDeleteOrder,
  } = useECNImpact(ecnId, refetch)

  // 处理 BOM 分析
  const handleBomAnalysis = async () => {
    const result = await handleAnalyzeBomImpact()
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 处理呆滞料检查
  const handleObsoleteCheck = async () => {
    const result = await handleCheckObsoleteRisk()
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 处理删除物料
  const handleMaterialDelete = async (materialId) => {
    if (!confirm('确定要删除这个受影响物料吗？')) return
    const result = await handleDeleteMaterial(materialId)
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 处理删除订单
  const handleOrderDelete = async (orderId) => {
    if (!confirm('确定要删除这个受影响订单吗？')) return
    const result = await handleDeleteOrder(orderId)
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 判断是否可以编辑
  const canEdit =
    ecn?.status === 'DRAFT' ||
    ecn?.status === 'SUBMITTED' ||
    ecn?.status === 'EVALUATING'

  // 计算总成本影响
  const totalMaterialCost = affectedMaterials.reduce(
    (sum, m) => sum + (parseFloat(m.cost_impact) || 0),
    0
  )

  return (
    <div className="space-y-4">
      {/* 操作工具栏 */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={handleBomAnalysis}
              disabled={analyzingBom || !ecn?.machine_id}
            >
              <GitBranch className="w-4 h-4 mr-2" />
              {analyzingBom ? '分析中...' : 'BOM影响分析'}
            </Button>
            <Button
              variant="outline"
              onClick={handleObsoleteCheck}
              disabled={analyzingBom}
            >
              <AlertTriangle className="w-4 h-4 mr-2" />
              检查呆滞料风险
            </Button>
            <Button
              variant="outline"
              onClick={() => setShowResponsibilityDialog(true)}
            >
              <Users className="w-4 h-4 mr-2" />
              责任分摊
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                if (rcaAnalysis) {
                  setRcaForm({
                    root_cause: rcaAnalysis.root_cause || '',
                    root_cause_analysis: rcaAnalysis.root_cause_analysis || '',
                    root_cause_category: rcaAnalysis.root_cause_category || '',
                  })
                } else {
                  setRcaForm({
                    root_cause: '',
                    root_cause_analysis: '',
                    root_cause_category: '',
                  })
                }
                setShowRcaDialog(true)
              }}
            >
              <FileText className="w-4 h-4 mr-2" />
              RCA分析
            </Button>
          </div>
        </CardContent>
      </Card>

      {/* BOM影响分析结果 */}
      {bomImpactSummary && bomImpactSummary.has_impact && (
        <Card className="border-blue-200 bg-blue-50/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <GitBranch className="w-5 h-5 text-blue-600" />
              BOM影响分析结果
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-3 gap-4 mb-4">
              <div>
                <div className="text-sm text-slate-500 mb-1">总成本影响</div>
                <div className="text-xl font-bold text-red-600">
                  ¥{bomImpactSummary.total_cost_impact?.toLocaleString() || 0}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">受影响物料项</div>
                <div className="text-xl font-bold">
                  {bomImpactSummary.total_affected_items || 0} 项
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">最大交期影响</div>
                <div className="text-xl font-bold text-orange-600">
                  {bomImpactSummary.max_schedule_impact_days || 0} 天
                </div>
              </div>
            </div>
            {bomImpactSummary.bom_impacts &&
              bomImpactSummary.bom_impacts.length > 0 && (
                <div className="space-y-2">
                  <div className="text-sm font-medium">BOM影响明细：</div>
                  {bomImpactSummary.bom_impacts.map((impact, idx) => (
                    <div key={idx} className="p-2 bg-white rounded text-sm">
                      BOM #{impact.bom_id}: {impact.affected_item_count}项受影响,
                      成本影响¥{impact.cost_impact?.toLocaleString()},
                      交期影响{impact.schedule_impact_days}天
                    </div>
                  ))}
                </div>
              )}
          </CardContent>
        </Card>
      )}

      {/* 呆滞料预警 */}
      {obsoleteAlerts.length > 0 && (
        <Card className="border-red-200 bg-red-50/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <AlertTriangle className="w-5 h-5 text-red-600" />
              呆滞料预警
              <Badge className="bg-red-500">{obsoleteAlerts.length}</Badge>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {obsoleteAlerts.map((alert, idx) => (
                <Card key={idx} className="p-3">
                  <div className="flex justify-between items-start mb-2">
                    <div>
                      <div className="font-semibold">{alert.material_name}</div>
                      <div className="text-sm text-slate-500 font-mono">
                        {alert.material_code}
                      </div>
                    </div>
                    <Badge
                      className={
                        alert.risk_level === 'CRITICAL'
                          ? 'bg-red-600'
                          : alert.risk_level === 'HIGH'
                          ? 'bg-red-500'
                          : alert.risk_level === 'MEDIUM'
                          ? 'bg-orange-500'
                          : 'bg-yellow-500'
                      }
                    >
                      {alert.risk_level === 'CRITICAL'
                        ? '严重'
                        : alert.risk_level === 'HIGH'
                        ? '高'
                        : alert.risk_level === 'MEDIUM'
                        ? '中'
                        : '低'}
                    </Badge>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-sm">
                    <div>
                      <span className="text-slate-500">呆滞数量:</span>{' '}
                      {alert.obsolete_quantity}
                    </div>
                    <div>
                      <span className="text-slate-500">呆滞成本:</span>
                      <span className="font-semibold text-red-600 ml-1">
                        ¥{alert.obsolete_cost?.toLocaleString()}
                      </span>
                    </div>
                  </div>
                  {alert.analysis && (
                    <div className="mt-2 p-2 bg-slate-50 rounded text-sm">
                      {alert.analysis}
                    </div>
                  )}
                </Card>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* 责任分摊汇总 */}
      {responsibilitySummary && responsibilitySummary.has_responsibility && (
        <Card className="border-green-200 bg-green-50/30">
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <Users className="w-5 h-5 text-green-600" />
              责任分摊
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {responsibilitySummary.responsibilities?.map((resp, idx) => (
                <div
                  key={idx}
                  className="flex justify-between items-center p-3 bg-white rounded"
                >
                  <div>
                    <div className="font-semibold">{resp.dept}</div>
                    <div className="text-sm text-slate-500">
                      {resp.responsibility_type === 'PRIMARY'
                        ? '主要责任'
                        : resp.responsibility_type === 'SECONDARY'
                        ? '次要责任'
                        : '支持责任'}
                    </div>
                  </div>
                  <div className="text-right">
                    <div className="font-semibold">{resp.responsibility_ratio}%</div>
                    <div className="text-sm text-slate-500">
                      ¥{resp.cost_allocation?.toLocaleString()}
                    </div>
                  </div>
                </div>
              ))}
              <div className="pt-2 border-t">
                <div className="flex justify-between items-center">
                  <span className="font-semibold">总成本分摊</span>
                  <span className="text-xl font-bold text-green-600">
                    ¥{responsibilitySummary.total_cost_allocation?.toLocaleString()}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* RCA分析 */}
      {rcaAnalysis &&
        (rcaAnalysis.root_cause || rcaAnalysis.root_cause_analysis) && (
          <Card className="border-purple-200 bg-purple-50/30">
            <CardHeader>
              <CardTitle className="text-base flex items-center gap-2">
                <FileText className="w-5 h-5 text-purple-600" />
                RCA分析（根本原因分析）
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-3">
                {rcaAnalysis.root_cause && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">根本原因类型</div>
                    <div className="font-semibold">{rcaAnalysis.root_cause}</div>
                  </div>
                )}
                {rcaAnalysis.root_cause_category && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">原因分类</div>
                    <div>{rcaAnalysis.root_cause_category}</div>
                  </div>
                )}
                {rcaAnalysis.root_cause_analysis && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">分析内容</div>
                    <div className="p-3 bg-white rounded whitespace-pre-wrap">
                      {rcaAnalysis.root_cause_analysis}
                    </div>
                  </div>
                )}
              </div>
            </CardContent>
          </Card>
        )}

      {/* 成本影响汇总 */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">成本影响汇总</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-3 gap-4">
            <div className="text-center p-4 bg-slate-50 rounded-lg">
              <div className="text-sm text-slate-500 mb-1">物料成本影响</div>
              <div className="text-2xl font-bold text-red-600">
                ¥{totalMaterialCost.toFixed(2)}
              </div>
            </div>
            <div className="text-center p-4 bg-slate-50 rounded-lg">
              <div className="text-sm text-slate-500 mb-1">受影响物料数</div>
              <div className="text-2xl font-bold">{affectedMaterials.length}</div>
            </div>
            <div className="text-center p-4 bg-slate-50 rounded-lg">
              <div className="text-sm text-slate-500 mb-1">受影响订单数</div>
              <div className="text-2xl font-bold">{affectedOrders.length}</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* 受影响物料和订单 */}
      <div className="grid grid-cols-2 gap-4">
        {/* 受影响物料 */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-base">受影响物料</CardTitle>
              <div className="flex items-center gap-2">
                <Badge>{affectedMaterials.length}</Badge>
                {canEdit && (
                  <Button size="sm" onClick={handleAddMaterial}>
                    <Plus className="w-4 h-4 mr-2" />
                    添加物料
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {affectedMaterials.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-sm">
                暂无受影响物料
              </div>
            ) : (
              <div className="space-y-4">
                {affectedMaterials.map((mat) => (
                  <Card key={mat.id} className="p-4">
                    <div className="space-y-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold">{mat.material_name}</div>
                          <div className="text-sm text-slate-500 font-mono">
                            {mat.material_code}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge className="bg-blue-500">{mat.change_type}</Badge>
                          {canEdit && (
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditMaterial(mat)}
                              >
                                <Edit2 className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleMaterialDelete(mat.id)}
                              >
                                <XCircle className="w-4 h-4" />
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>

                      {/* 变更前后对比 */}
                      {(mat.old_quantity ||
                        mat.old_specification ||
                        mat.new_quantity ||
                        mat.new_specification) && (
                        <div className="grid grid-cols-2 gap-3 p-3 bg-slate-50 rounded-lg">
                          <div>
                            <div className="text-xs text-slate-500 mb-1">变更前</div>
                            {mat.old_quantity && (
                              <div className="text-sm">数量: {mat.old_quantity}</div>
                            )}
                            {mat.old_specification && (
                              <div className="text-sm">规格: {mat.old_specification}</div>
                            )}
                          </div>
                          <div>
                            <div className="text-xs text-slate-500 mb-1">变更后</div>
                            {mat.new_quantity && (
                              <div className="text-sm">数量: {mat.new_quantity}</div>
                            )}
                            {mat.new_specification && (
                              <div className="text-sm">规格: {mat.new_specification}</div>
                            )}
                          </div>
                        </div>
                      )}

                      <div className="flex justify-between items-center pt-2 border-t">
                        <div className="text-sm text-slate-500">成本影响</div>
                        <div
                          className={`text-lg font-semibold ${
                            parseFloat(mat.cost_impact) > 0
                              ? 'text-red-600'
                              : parseFloat(mat.cost_impact) < 0
                              ? 'text-green-600'
                              : 'text-slate-600'
                          }`}
                        >
                          {parseFloat(mat.cost_impact) > 0 ? '+' : ''}¥
                          {mat.cost_impact || 0}
                        </div>
                      </div>
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>

        {/* 受影响订单 */}
        <Card>
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="text-base">受影响订单</CardTitle>
              <div className="flex items-center gap-2">
                <Badge>{affectedOrders.length}</Badge>
                {canEdit && (
                  <Button size="sm" onClick={handleAddOrder}>
                    <Plus className="w-4 h-4 mr-2" />
                    添加订单
                  </Button>
                )}
              </div>
            </div>
          </CardHeader>
          <CardContent>
            {affectedOrders.length === 0 ? (
              <div className="text-center py-8 text-slate-400 text-sm">
                暂无受影响订单
              </div>
            ) : (
              <div className="space-y-3">
                {affectedOrders.map((order) => (
                  <Card key={order.id} className="p-4">
                    <div className="space-y-2">
                      <div className="flex justify-between items-start">
                        <div>
                          <div className="font-semibold">
                            {order.order_type === 'PURCHASE'
                              ? '采购订单'
                              : '外协订单'}
                          </div>
                          <div className="text-sm text-slate-500 font-mono">
                            {order.order_no}
                          </div>
                        </div>
                        <div className="flex items-center gap-2">
                          <Badge
                            className={
                              order.status === 'PROCESSED'
                                ? 'bg-green-500'
                                : 'bg-amber-500'
                            }
                          >
                            {order.status === 'PROCESSED' ? '已处理' : '待处理'}
                          </Badge>
                          {canEdit && (
                            <div className="flex gap-1">
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleEditOrder(order)}
                              >
                                <Edit2 className="w-4 h-4" />
                              </Button>
                              <Button
                                variant="ghost"
                                size="sm"
                                onClick={() => handleOrderDelete(order.id)}
                              >
                                <XCircle className="w-4 h-4" />
                              </Button>
                            </div>
                          )}
                        </div>
                      </div>
                      {order.impact_description && (
                        <div className="text-sm text-slate-600 p-2 bg-slate-50 rounded">
                          {order.impact_description}
                        </div>
                      )}
                      {order.action_type && (
                        <div className="text-sm">
                          <span className="text-slate-500">处理方式:</span>{' '}
                          {order.action_type}
                        </div>
                      )}
                    </div>
                  </Card>
                ))}
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* 对话框组件 */}
      <MaterialDialog
        open={showMaterialDialog}
        onOpenChange={setShowMaterialDialog}
        form={materialForm}
        setForm={setMaterialForm}
        onSubmit={async () => {
          const result = await handleSaveMaterial()
          if (result.success) {
            alert(result.message)
          } else {
            alert(result.message)
          }
        }}
        editingMaterial={editingMaterial}
      />

      <OrderDialog
        open={showOrderDialog}
        onOpenChange={setShowOrderDialog}
        form={orderForm}
        setForm={setOrderForm}
        onSubmit={async () => {
          const result = await handleSaveOrder()
          if (result.success) {
            alert(result.message)
          } else {
            alert(result.message)
          }
        }}
        editingOrder={editingOrder}
      />

      <ResponsibilityDialog
        open={showResponsibilityDialog}
        onOpenChange={setShowResponsibilityDialog}
        form={responsibilityForm}
        setForm={setResponsibilityForm}
        onSubmit={async () => {
          const result = await handleCreateResponsibility()
          if (result.success) {
            alert(result.message)
          } else {
            alert(result.message)
          }
        }}
      />

      <RcaDialog
        open={showRcaDialog}
        onOpenChange={setShowRcaDialog}
        form={rcaForm}
        setForm={setRcaForm}
        onSubmit={async () => {
          const result = await handleSaveRcaAnalysis()
          if (result.success) {
            alert(result.message)
          } else {
            alert(result.message)
          }
        }}
      />
    </div>
  )
}
