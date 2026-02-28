/**
 * ECN评估管理标签页组件
 * 用途：展示和管理ECN的部门评估信息
 */
import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { Plus } from 'lucide-react';
import { evalResultConfigs } from '@/lib/constants/ecn';

/**
 * 评估汇总卡片组件
 */
import { confirmAction } from "@/lib/confirmAction";
const EvaluationSummaryCard = ({ summary }) => {
  if (!summary) {return null;}

  const completionRate = summary.total_evaluations > 0
    ? (summary.submitted_count / summary.total_evaluations) * 100
    : 0;

  return (
    <Card>
      <CardHeader>
        <CardTitle className="text-base">评估汇总</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-4 gap-4 mb-4">
          <div>
            <div className="text-sm text-slate-500 mb-1">总成本影响</div>
            <div className="text-xl font-semibold text-red-600">
              ¥{summary.total_cost_impact || 0}
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-500 mb-1">最大工期影响</div>
            <div className="text-xl font-semibold text-orange-600">
              {summary.max_schedule_impact || 0} 天
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-500 mb-1">评估完成度</div>
            <div className="text-xl font-semibold">
              {summary.submitted_count || 0} / {summary.total_evaluations || 0}
            </div>
            <div className="mt-2">
              <div className="w-full bg-slate-200 rounded-full h-2">
                <div
                  className="bg-blue-500 h-2 rounded-full transition-all"
                  style={{ width: `${completionRate}%` }}
                />
              </div>
            </div>
          </div>
          <div>
            <div className="text-sm text-slate-500 mb-1">通过/驳回</div>
            <div className="text-xl font-semibold">
              <span className="text-green-600">
                {summary.approved_count || 0}
              </span>
              {' / '}
              <span className="text-red-600">
                {summary.rejected_count || 0}
              </span>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};

/**
 * 单个评估卡片组件
 */
const EvaluationCard = ({ evaluation, onSubmit, formatDate }) => {
  const handleSubmit = async () => {
    if (!await confirmAction('确认提交此评估？提交后将无法修改。')) {return;}
    await onSubmit(evaluation.id);
  };

  return (
    <Card className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex justify-between items-center">
          <div>
            <CardTitle className="text-base">{evaluation.eval_dept}</CardTitle>
            {evaluation.evaluated_at && (
              <CardDescription className="mt-1">
                评估时间: {formatDate(evaluation.evaluated_at)}
              </CardDescription>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Badge
              className={
                evalResultConfigs[evaluation.eval_result]?.color || 'bg-slate-500'
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
        {/* 成本和工期估算 */}
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

        {/* 评估人 */}
        <div className="text-sm">
          <span className="text-slate-500">评估人:</span>{' '}
          {evaluation.evaluator_name || '待分配'}
        </div>

        {/* 影响分析 */}
        {evaluation.impact_analysis && (
          <div>
            <div className="text-sm text-slate-500 mb-1">影响分析:</div>
            <div className="p-2 bg-slate-50 rounded text-sm line-clamp-3">
              {evaluation.impact_analysis}
            </div>
          </div>
        )}

        {/* 风险评估 */}
        {evaluation.risk_assessment && (
          <div>
            <div className="text-sm text-slate-500 mb-1">风险评估:</div>
            <div className="p-2 bg-amber-50 rounded text-sm">
              {evaluation.risk_assessment}
            </div>
          </div>
        )}

        {/* 评估意见 */}
        {evaluation.eval_opinion && (
          <div>
            <div className="text-sm text-slate-500 mb-1">评估意见:</div>
            <div className="p-2 bg-slate-50 rounded text-sm">
              {evaluation.eval_opinion}
            </div>
          </div>
        )}

        {/* 附加条件 */}
        {evaluation.conditions && (
          <div>
            <div className="text-sm text-slate-500 mb-1">附加条件:</div>
            <div className="p-2 bg-blue-50 rounded text-sm">
              {evaluation.conditions}
            </div>
          </div>
        )}

        {/* 提交按钮（仅草稿状态显示） */}
        {evaluation.status === 'DRAFT' && (
          <Button size="sm" className="w-full" onClick={handleSubmit}>
            提交评估
          </Button>
        )}
      </CardContent>
    </Card>
  );
};

/**
 * ECN评估管理标签页主组件
 */
export const ECNEvaluationsTab = ({
  ecnStatus,
  evaluationSummary,
  evaluations = [],
  onCreateEvaluation,
  onSubmitEvaluation,
  formatDate,
}) => {
  // 是否允许创建评估
  const canCreateEvaluation =
    ecnStatus === 'SUBMITTED' || ecnStatus === 'EVALUATING';

  return (
    <div className="space-y-4">
      {/* 评估汇总 */}
      <EvaluationSummaryCard summary={evaluationSummary} />

      {/* 标题和创建按钮 */}
      <div className="flex justify-between items-center">
        <CardTitle className="text-lg">部门评估</CardTitle>
        {canCreateEvaluation && (
          <Button onClick={onCreateEvaluation}>
            <Plus className="w-4 h-4 mr-2" />
            创建评估
          </Button>
        )}
      </div>

      {/* 评估列表 */}
      {evaluations.length === 0 ? (
        <Card>
          <CardContent className="py-8 text-center text-slate-400">
            暂无评估记录
          </CardContent>
        </Card>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {(evaluations || []).map((evaluation) => (
            <EvaluationCard
              key={evaluation.id}
              evaluation={evaluation}
              onSubmit={onSubmitEvaluation}
              formatDate={formatDate}
            />
          ))}
        </div>
      )}
    </div>
  );
};

export default ECNEvaluationsTab;
