/**
 * 阶段详情对话框
 */



import { formatDate } from "../../lib/utils";
import { getStatusBadge, getReviewResultBadge } from "./phaseUtils";
import { Badge, Button, Dialog, DialogBody, DialogContent, DialogFooter, DialogHeader, DialogTitle } from "../ui";

export default function PhaseDetailDialog({ open, onOpenChange, phase }) {
  if (!phase) {return null;}

  const statusBadge = getStatusBadge(phase.status);
  const reviewBadge = phase.review_result
    ? getReviewResultBadge(phase.review_result)
    : null;

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>阶段详情 - {phase.phase_name}</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-slate-400">阶段编码</span>
                <p className="text-white font-medium">{phase.phase_code}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">阶段顺序</span>
                <p className="text-white font-medium">{phase.phase_order}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">状态</span>
                <p className="mt-1">
                  <Badge variant={statusBadge.variant}>
                    {statusBadge.label}
                  </Badge>
                </p>
              </div>
              <div>
                <span className="text-sm text-slate-400">进度</span>
                <p className="text-white font-medium">{phase.progress || 0}%</p>
              </div>
            </div>

            {/* Timeline */}
            <div>
              <h4 className="text-sm font-medium text-white mb-3">时间计划</h4>
              <div className="grid grid-cols-2 gap-4 p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <div>
                  <span className="text-xs text-slate-400">计划开始</span>
                  <p className="text-white">
                    {phase.plan_start_date
                      ? formatDate(phase.plan_start_date)
                      : "未设置"}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">计划结束</span>
                  <p className="text-white">
                    {phase.plan_end_date
                      ? formatDate(phase.plan_end_date)
                      : "未设置"}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">实际开始</span>
                  <p className="text-white">
                    {phase.actual_start_date
                      ? formatDate(phase.actual_start_date)
                      : "未开始"}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">实际结束</span>
                  <p className="text-white">
                    {phase.actual_end_date
                      ? formatDate(phase.actual_end_date)
                      : "未结束"}
                  </p>
                </div>
              </div>
            </div>

            {/* Criteria */}
            {(phase.entry_criteria || phase.exit_criteria) && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">
                  门控条件
                </h4>
                <div className="space-y-3">
                  {phase.entry_criteria && (
                    <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <span className="text-xs text-slate-400">入口条件</span>
                      <p className="text-white mt-1">{phase.entry_criteria}</p>
                    </div>
                  )}
                  {phase.exit_criteria && (
                    <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <span className="text-xs text-slate-400">出口条件</span>
                      <p className="text-white mt-1">{phase.exit_criteria}</p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Check Results */}
            {(phase.entry_check_result || phase.exit_check_result) && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">
                  检查结果
                </h4>
                <div className="space-y-3">
                  {phase.entry_check_result && (
                    <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <span className="text-xs text-slate-400">
                        入口检查结果
                      </span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {phase.entry_check_result}
                      </p>
                    </div>
                  )}
                  {phase.exit_check_result && (
                    <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <span className="text-xs text-slate-400">
                        出口检查结果
                      </span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {phase.exit_check_result}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Review */}
            {phase.review_required && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">
                  评审信息
                </h4>
                <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5 space-y-2">
                  {reviewBadge && (
                    <div>
                      <span className="text-xs text-slate-400">评审结果</span>
                      <p className="mt-1">
                        <Badge variant={reviewBadge.variant}>
                          {reviewBadge.label}
                        </Badge>
                      </p>
                    </div>
                  )}
                  {phase.review_date && (
                    <div>
                      <span className="text-xs text-slate-400">评审日期</span>
                      <p className="text-white">
                        {formatDate(phase.review_date)}
                      </p>
                    </div>
                  )}
                  {phase.review_notes && (
                    <div>
                      <span className="text-xs text-slate-400">评审记录</span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {phase.review_notes}
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
