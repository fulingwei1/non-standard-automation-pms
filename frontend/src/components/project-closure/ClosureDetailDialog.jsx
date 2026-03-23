/**
 * 结项详情对话框
 */



import { formatDate } from "../../lib/utils";
import { getStatusBadge } from "./closureUtils";

export default function ClosureDetailDialog({ open, onOpenChange, closure }) {
  if (!closure) {return null;}

  const statusBadge = getStatusBadge(closure.status);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>结项详情 - {closure.closure_no || "结项申请"}</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Status */}
            <div>
              <span className="text-sm text-slate-400">状态</span>
              <p className="mt-1">
                <Badge variant={statusBadge.variant}>
                  {statusBadge.label}
                </Badge>
              </p>
            </div>

            {/* Acceptance */}
            {closure.acceptance_date && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">验收信息</h4>
                <div className="grid grid-cols-2 gap-4">
                  <div>
                    <span className="text-xs text-slate-400">验收日期</span>
                    <p className="text-white mt-1">
                      {formatDate(closure.acceptance_date)}
                    </p>
                  </div>
                  <div>
                    <span className="text-xs text-slate-400">验收结果</span>
                    <p className="text-white mt-1">
                      {closure.acceptance_result || "未设置"}
                    </p>
                  </div>
                  {closure.acceptance_notes && (
                    <div className="col-span-2">
                      <span className="text-xs text-slate-400">验收说明</span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {closure.acceptance_notes}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Summary */}
            {closure.project_summary && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">项目总结</h4>
                <p className="text-white whitespace-pre-wrap">
                  {closure.project_summary}
                </p>
              </div>
            )}

            {/* Achievement */}
            {closure.achievement && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">项目成果</h4>
                <p className="text-white whitespace-pre-wrap">
                  {closure.achievement}
                </p>
              </div>
            )}

            {/* Lessons */}
            {closure.lessons_learned && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">经验教训</h4>
                <p className="text-white whitespace-pre-wrap">
                  {closure.lessons_learned}
                </p>
              </div>
            )}

            {/* Improvement */}
            {closure.improvement_suggestions && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">改进建议</h4>
                <p className="text-white whitespace-pre-wrap">
                  {closure.improvement_suggestions}
                </p>
              </div>
            )}

            {/* Scores */}
            <div className="grid grid-cols-2 gap-4">
              {closure.quality_score !== null && closure.quality_score !== undefined && (
                <div>
                  <span className="text-sm text-slate-400">质量评分</span>
                  <p className="text-white font-medium text-2xl mt-1">
                    {closure.quality_score}
                  </p>
                </div>
              )}
              {closure.customer_satisfaction !== null && closure.customer_satisfaction !== undefined && (
                <div>
                  <span className="text-sm text-slate-400">客户满意度</span>
                  <p className="text-white font-medium text-2xl mt-1">
                    {closure.customer_satisfaction}
                  </p>
                </div>
              )}
            </div>

            {/* Review Info */}
            {closure.status === "REVIEWED" && closure.review_result && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">评审信息</h4>
                <div className="space-y-2">
                  <div>
                    <span className="text-xs text-slate-400">评审结果</span>
                    <p className="text-white mt-1">{closure.review_result}</p>
                  </div>
                  {closure.review_notes && (
                    <div>
                      <span className="text-xs text-slate-400">评审记录</span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {closure.review_notes}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}
          </div>
        </DialogBody>
        <DialogFooter>
          <Button onClick={() => onOpenChange(false)}>关闭</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
