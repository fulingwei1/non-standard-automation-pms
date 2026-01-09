/**
 * ECNEvaluationsTab Component
 * ECN 评估管理 Tab 组件
 */
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '../ui/card'
import { Button } from '../ui/button'
import { Badge } from '../ui/badge'
import { Plus } from 'lucide-react'
import { formatDate } from '../../lib/utils'
import { useECNEvaluations } from './hooks/useECNEvaluations'
import EvaluationDialog from './dialogs/EvaluationDialog'

const evalResultConfigs = {
  APPROVED: { label: '通过', color: 'bg-green-500' },
  CONDITIONAL: { label: '有条件通过', color: 'bg-yellow-500' },
  REJECTED: { label: '不通过', color: 'bg-red-500' },
}

export default function ECNEvaluationsTab({ ecnId, ecn, evaluations, evaluationSummary, refetch }) {
  const {
    showEvaluationDialog,
    setShowEvaluationDialog,
    evaluationForm,
    setEvaluationForm,
    handleCreateEvaluation,
    handleSubmitEvaluation,
  } = useECNEvaluations(ecnId, refetch)

  // 处理创建评估
  const handleCreateClick = async () => {
    const result = await handleCreateEvaluation()
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 处理提交评估
  const handleSubmitClick = async (evaluationId) => {
    if (!confirm('确认提交此评估？提交后将无法修改。')) return

    const result = await handleSubmitEvaluation(evaluationId)
    if (result.success) {
      alert(result.message)
    } else {
      alert(result.message)
    }
  }

  // 判断是否可以创建评估
  const canCreateEvaluation =
    ecn?.status === 'SUBMITTED' || ecn?.status === 'EVALUATING'

  return (
    <div className="space-y-4">
      {/* 评估汇总 */}
      {evaluationSummary && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">评估汇总</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div>
                <div className="text-sm text-slate-500 mb-1">总成本影响</div>
                <div className="text-xl font-semibold text-red-600">
                  ¥{evaluationSummary.total_cost_impact || 0}
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">最大工期影响</div>
                <div className="text-xl font-semibold text-orange-600">
                  {evaluationSummary.max_schedule_impact || 0} 天
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">评估完成度</div>
                <div className="text-xl font-semibold">
                  {evaluationSummary.submitted_count || 0} /{' '}
                  {evaluationSummary.total_evaluations || 0}
                </div>
                <div className="mt-2">
                  <div className="w-full bg-slate-200 rounded-full h-2">
                    <div
                      className="bg-blue-500 h-2 rounded-full transition-all"
                      style={{
                        width: `${
                          evaluationSummary.total_evaluations > 0
                            ? (evaluationSummary.submitted_count /
                                evaluationSummary.total_evaluations) *
                              100
                            : 0
                        }%`,
                      }}
                    />
                  </div>
                </div>
              </div>
              <div>
                <div className="text-sm text-slate-500 mb-1">通过/驳回</div>
                <div className="text-xl font-semibold">
                  <span className="text-green-600">
                    {evaluationSummary.approved_count || 0}
                  </span>
                  {' / '}
                  <span className="text-red-600">
                    {evaluationSummary.rejected_count || 0}
                  </span>
                </div>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* 部门评估列表 */}
      <div className="flex justify-between items-center">
        <CardTitle className="text-lg">部门评估</CardTitle>
        {canCreateEvaluation && (
          <Button onClick={() => setShowEvaluationDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            创建评估
          </Button>
        )}
      </div>

      {evaluations.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-slate-400">
            暂无评估记录
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {evaluations.map((evaluation) => (
            <Card
              key={evaluation.id}
              className="hover:shadow-md transition-shadow"
            >
              <CardHeader>
                <div className="flex justify-between items-center">
                  <div>
                    <CardTitle className="text-base">
                      {evaluation.eval_dept}
                    </CardTitle>
                    {evaluation.evaluated_at && (
                      <CardDescription className="mt-1">
                        评估时间: {formatDate(evaluation.evaluated_at)}
                      </CardDescription>
                    )}
                  </div>
                  <div className="flex items-center gap-2">
                    <Badge
                      className={
                        evalResultConfigs[evaluation.eval_result]?.color ||
                        'bg-slate-500'
                      }
                    >
                      {evalResultConfigs[evaluation.eval_result]?.label ||
                        evaluation.eval_result}
                    </Badge>
                    <Badge
                      className={
                        evaluation.status === 'SUBMITTED'
                          ? 'bg-green-500'
                          : 'bg-amber-500'
                      }
                    >
                      {evaluation.status === 'SUBMITTED' ? '已提交' : '草稿'}
                    </Badge>
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div className="grid grid-cols-2 gap-3">
                  <div className="p-2 bg-slate-50 rounded">
                    <div className="text-xs text-slate-500 mb-1">成本估算</div>
                    <div className="font-semibold text-red-600">
                      {evaluation.cost_estimate > 0
                        ? `¥${evaluation.cost_estimate}`
                        : '-'}
                    </div>
                  </div>
                  <div className="p-2 bg-slate-50 rounded">
                    <div className="text-xs text-slate-500 mb-1">工期估算</div>
                    <div className="font-semibold text-orange-600">
                      {evaluation.schedule_estimate > 0
                        ? `${evaluation.schedule_estimate} 天`
                        : '-'}
                    </div>
                  </div>
                </div>
                <div className="text-sm">
                  <span className="text-slate-500">评估人:</span>{' '}
                  {evaluation.evaluator_name || '待分配'}
                </div>
                {evaluation.impact_analysis && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">影响分析:</div>
                    <div className="p-2 bg-slate-50 rounded text-sm line-clamp-3">
                      {evaluation.impact_analysis}
                    </div>
                  </div>
                )}
                {evaluation.risk_assessment && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">风险评估:</div>
                    <div className="p-2 bg-amber-50 rounded text-sm">
                      {evaluation.risk_assessment}
                    </div>
                  </div>
                )}
                {evaluation.eval_opinion && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">评估意见:</div>
                    <div className="p-2 bg-slate-50 rounded text-sm">
                      {evaluation.eval_opinion}
                    </div>
                  </div>
                )}
                {evaluation.conditions && (
                  <div>
                    <div className="text-sm text-slate-500 mb-1">附加条件:</div>
                    <div className="p-2 bg-blue-50 rounded text-sm">
                      {evaluation.conditions}
                    </div>
                  </div>
                )}
                {evaluation.status === 'DRAFT' && (
                  <Button
                    size="sm"
                    className="w-full"
                    onClick={() => handleSubmitClick(evaluation.id)}
                  >
                    提交评估
                  </Button>
                )}
              </CardContent>
            </Card>
          ))}
        </div>
      )}

      {/* 创建评估对话框 */}
      <EvaluationDialog
        open={showEvaluationDialog}
        onOpenChange={setShowEvaluationDialog}
        form={evaluationForm}
        setForm={setEvaluationForm}
        onSubmit={handleCreateClick}
      />
    </div>
  )
}
