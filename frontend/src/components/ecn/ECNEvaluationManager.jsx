/**
 * ECN Evaluation Manager Component
 * ECN 评估管理组件
 */

import { useState } from "react";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Textarea } from "../../components/ui/textarea";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../../components/ui/dialog";
import {
  Plus,
  TrendingUp,
  DollarSign,
  Clock,
  AlertTriangle,
  CheckCircle2,
  XCircle } from
"lucide-react";
import {
  evaluationStatusConfigs,
  impactTypeConfigs,
  formatStatus } from
"@/lib/constants/ecn";
import { cn, formatDate } from "../../lib/utils";import { toast } from "sonner";

export function ECNEvaluationManager({
  ecn,
  evaluations,
  evaluationSummary,
  onCreateEvaluation,
  loading: _loading
}) {
  const [showEvaluationDialog, setShowEvaluationDialog] = useState(false);
  const [evaluationForm, setEvaluationForm] = useState({
    department: "",
    impact_type: "",
    impact_description: "",
    cost_impact: "",
    schedule_impact: "",
    quality_impact: "",
    risk_level: "",
    recommendation: "",
    evaluated_by: ""
  });

  const getRiskLevelConfig = (level) => {
    const configs = {
      LOW: { label: "低风险", color: "bg-green-500", textColor: "text-green-50" },
      MEDIUM: { label: "中等风险", color: "bg-yellow-500", textColor: "text-yellow-50" },
      HIGH: { label: "高风险", color: "bg-red-500", textColor: "text-red-50" },
      CRITICAL: { label: "关键风险", color: "bg-purple-500", textColor: "text-purple-50" }
    };
    return configs[level] || configs.LOW;
  };

  const handleCreateEvaluation = () => {
    if (!evaluationForm.department || !evaluationForm.impact_type || !evaluationForm.recommendation) {
      toast.warning("请填写必填字段");
      return;
    }

    onCreateEvaluation({
      ...evaluationForm,
      ecn_id: ecn.id,
      evaluation_date: new Date().toISOString()
    });

    setEvaluationForm({
      department: "",
      impact_type: "",
      impact_description: "",
      cost_impact: "",
      schedule_impact: "",
      quality_impact: "",
      risk_level: "",
      recommendation: "",
      evaluated_by: ""
    });
    setShowEvaluationDialog(false);
  };

  return (
    <>
      {/* 评估汇总 */}
      {evaluationSummary &&
      <Card>
          <CardHeader>
            <CardTitle className="text-base flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              评估汇总
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-4 gap-4 mb-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">
                  {evaluationSummary.total_evaluations || 0}
                </div>
                <div className="text-sm text-slate-500">总评估数</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {evaluationSummary.completed_evaluations || 0}
                </div>
                <div className="text-sm text-slate-500">已完成</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  ¥{(evaluationSummary.total_cost_impact || 0).toLocaleString()}
                </div>
                <div className="text-sm text-slate-500">总成本影响</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-orange-600">
                  {evaluationSummary.max_schedule_impact || 0}天
                </div>
                <div className="text-sm text-slate-500">最大进度影响</div>
              </div>
            </div>
            
            {evaluationSummary.average_risk_level &&
          <div className="flex items-center gap-2">
                <span className="text-sm text-slate-500">平均风险等级:</span>
                <Badge className={cn(
              getRiskLevelConfig(evaluationSummary.average_risk_level).color,
              getRiskLevelConfig(evaluationSummary.average_risk_level).textColor
            )}>
                  {getRiskLevelConfig(evaluationSummary.average_risk_level).label}
                </Badge>
          </div>
          }
          </CardContent>
      </Card>
      }

      {/* 部门评估 */}
      <div className="flex justify-between items-center mb-4">
        <h3 className="text-lg font-semibold">部门评估</h3>
        {(ecn.status === "EVALUATING" || ecn.status === "SUBMITTED") &&
        <Button onClick={() => setShowEvaluationDialog(true)}>
            <Plus className="w-4 h-4 mr-2" />
            创建评估
        </Button>
        }
      </div>

      {evaluations.length === 0 ?
      <Card>
          <CardContent className="py-8 text-center text-slate-400">
            暂无评估记录
          </CardContent>
      </Card> :

      <div className="space-y-4">
          {(evaluations || []).map((evaluation) =>
        <Card key={evaluation.id} className="border-l-4 border-l-blue-500">
              <CardHeader>
                <div className="flex justify-between items-start">
                  <div>
                    <CardTitle className="text-base flex items-center gap-2">
                      {evaluation.department}
                      <Badge className={cn(
                    evaluationStatusConfigs[evaluation.status]?.color,
                    evaluationStatusConfigs[evaluation.status]?.textColor,
                    "text-xs"
                  )}>
                        {formatStatus(evaluation.status)}
                      </Badge>
                    </CardTitle>
                    <CardDescription className="mt-1">
                      评估人: {evaluation.evaluated_by} | 
                      评估日期: {formatDate(evaluation.evaluation_date)}
                    </CardDescription>
                  </div>
                  <div className="flex items-center gap-2">
                    {evaluation.impact_type &&
                <Badge variant="outline" className="text-xs">
                        {impactTypeConfigs[evaluation.impact_type]?.label || evaluation.impact_type}
                </Badge>
                }
                    {evaluation.risk_level &&
                <Badge className={cn(
                  getRiskLevelConfig(evaluation.risk_level).color,
                  getRiskLevelConfig(evaluation.risk_level).textColor,
                  "text-xs"
                )}>
                        {getRiskLevelConfig(evaluation.risk_level).label}
                </Badge>
                }
                  </div>
                </div>
              </CardHeader>
              <CardContent className="space-y-3">
                <div>
                  <div className="text-sm text-slate-500 mb-1">影响描述</div>
                  <div className="text-white bg-slate-800/50 p-3 rounded-lg text-sm">
                    {evaluation.impact_description}
                  </div>
                </div>

                <div className="grid grid-cols-3 gap-4">
                  <div>
                    <div className="text-sm text-slate-500 mb-1 flex items-center gap-1">
                      <DollarSign className="w-3 h-3" />
                      成本影响
                    </div>
                    <div className="text-white">
                      {evaluation.cost_impact ? `¥${evaluation.cost_impact.toLocaleString()}` : "无影响"}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1 flex items-center gap-1">
                      <Clock className="w-3 h-3" />
                      进度影响
                    </div>
                    <div className="text-white">
                      {evaluation.schedule_impact ? `${evaluation.schedule_impact}天` : "无影响"}
                    </div>
                  </div>
                  <div>
                    <div className="text-sm text-slate-500 mb-1 flex items-center gap-1">
                      <AlertTriangle className="w-3 h-3" />
                      质量影响
                    </div>
                    <div className="text-white">
                      {evaluation.quality_impact || "无影响"}
                    </div>
                  </div>
                </div>

                <div>
                  <div className="text-sm text-slate-500 mb-1">建议</div>
                  <div className="text-white bg-slate-800/50 p-3 rounded-lg text-sm">
                    {evaluation.recommendation}
                  </div>
                </div>
              </CardContent>
        </Card>
        )}
      </div>
      }

      {/* 创建评估对话框 */}
      <Dialog open={showEvaluationDialog} onOpenChange={setShowEvaluationDialog}>
        <DialogContent className="max-w-2xl">
          <DialogHeader>
            <DialogTitle>创建评估</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div className="grid grid-cols-2 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">评估部门 *</label>
                <Select
                  value={evaluationForm.department}
                  onValueChange={(value) =>
                  setEvaluationForm({ ...evaluationForm, department: value })
                  }>

                  <SelectTrigger>
                    <SelectValue placeholder="选择部门" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="工程部">工程部</SelectItem>
                    <SelectItem value="质量部">质量部</SelectItem>
                    <SelectItem value="生产部">生产部</SelectItem>
                    <SelectItem value="采购部">采购部</SelectItem>
                    <SelectItem value="销售部">销售部</SelectItem>
                    <SelectItem value="财务部">财务部</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">影响类型 *</label>
                <Select
                  value={evaluationForm.impact_type}
                  onValueChange={(value) =>
                  setEvaluationForm({ ...evaluationForm, impact_type: value })
                  }>

                  <SelectTrigger>
                    <SelectValue placeholder="选择影响类型" />
                  </SelectTrigger>
                  <SelectContent>
                    {Object.entries(impactTypeConfigs).map(([key, config]) =>
                    <SelectItem key={key} value={key || "unknown"}>
                        {config.icon} {config.label}
                    </SelectItem>
                    )}
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">影响描述</label>
              <Textarea
                value={evaluationForm.impact_description}
                onChange={(e) =>
                setEvaluationForm({ ...evaluationForm, impact_description: e.target.value })
                }
                placeholder="详细描述变更带来的影响..."
                rows={3} />

            </div>

            <div className="grid grid-cols-3 gap-4">
              <div>
                <label className="text-sm font-medium mb-2 block">成本影响</label>
                <input
                  type="number"
                  value={evaluationForm.cost_impact}
                  onChange={(e) =>
                  setEvaluationForm({ ...evaluationForm, cost_impact: e.target.value })
                  }
                  placeholder="0"
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white" />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">进度影响(天)</label>
                <input
                  type="number"
                  value={evaluationForm.schedule_impact}
                  onChange={(e) =>
                  setEvaluationForm({ ...evaluationForm, schedule_impact: e.target.value })
                  }
                  placeholder="0"
                  className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white" />

              </div>
              <div>
                <label className="text-sm font-medium mb-2 block">风险等级</label>
                <Select
                  value={evaluationForm.risk_level}
                  onValueChange={(value) =>
                  setEvaluationForm({ ...evaluationForm, risk_level: value })
                  }>

                  <SelectTrigger>
                    <SelectValue placeholder="选择风险等级" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="LOW">低风险</SelectItem>
                    <SelectItem value="MEDIUM">中等风险</SelectItem>
                    <SelectItem value="HIGH">高风险</SelectItem>
                    <SelectItem value="CRITICAL">关键风险</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <div>
              <label className="text-sm font-medium mb-2 block">建议 *</label>
              <Textarea
                value={evaluationForm.recommendation}
                onChange={(e) =>
                setEvaluationForm({ ...evaluationForm, recommendation: e.target.value })
                }
                placeholder="基于评估结果提出建议..."
                rows={3} />

            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowEvaluationDialog(false)}>

              取消
            </Button>
            <Button onClick={handleCreateEvaluation}>创建评估</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>);

}