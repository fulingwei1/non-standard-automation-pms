/**
 * 风险详情对话框
 */



import { formatDate } from "../../lib/utils";
import { getRiskLevelBadge, getStatusBadge, getProbabilityLabel, getImpactLabel } from "./riskUtils";

export default function RiskDetailDialog({ open, onOpenChange, risk }) {
  if (!risk) {return null;}

  const levelBadge = getRiskLevelBadge(risk.risk_level);
  const statusBadge = getStatusBadge(risk.status);

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-3xl max-h-[90vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>风险详情 - {risk.risk_name}</DialogTitle>
        </DialogHeader>
        <DialogBody>
          <div className="space-y-4">
            {/* Basic Info */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-slate-400">风险编号</span>
                <p className="text-white font-medium">{risk.risk_no}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">风险类别</span>
                <p className="text-white font-medium">{risk.risk_category}</p>
              </div>
              <div>
                <span className="text-sm text-slate-400">风险等级</span>
                <p className="mt-1">
                  <Badge
                    variant={levelBadge.variant}
                    className={levelBadge.bgColor}
                  >
                    {levelBadge.label}
                  </Badge>
                </p>
              </div>
              <div>
                <span className="text-sm text-slate-400">状态</span>
                <p className="mt-1">
                  <Badge variant={statusBadge.variant}>
                    {statusBadge.label}
                  </Badge>
                </p>
              </div>
            </div>

            {/* Description */}
            {risk.description && (
              <div>
                <span className="text-sm text-slate-400">风险描述</span>
                <p className="text-white mt-1 whitespace-pre-wrap">
                  {risk.description}
                </p>
              </div>
            )}

            {/* Risk Matrix */}
            <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
              <h4 className="text-sm font-medium text-white mb-3">
                风险评估矩阵
              </h4>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <span className="text-xs text-slate-400">发生概率</span>
                  <p className="text-white font-medium">
                    {getProbabilityLabel(risk.probability)}
                  </p>
                </div>
                <div>
                  <span className="text-xs text-slate-400">影响程度</span>
                  <p className="text-white font-medium">
                    {getImpactLabel(risk.impact)}
                  </p>
                </div>
              </div>
            </div>

            {/* Response Plan */}
            {risk.response_strategy && (
              <div>
                <h4 className="text-sm font-medium text-white mb-3">
                  应对计划
                </h4>
                <div className="space-y-3">
                  <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                    <span className="text-xs text-slate-400">应对策略</span>
                    <p className="text-white mt-1">{risk.response_strategy}</p>
                  </div>
                  {risk.response_plan && (
                    <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                      <span className="text-xs text-slate-400">应对措施</span>
                      <p className="text-white mt-1 whitespace-pre-wrap">
                        {risk.response_plan}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            )}

            {/* Owner & Tracking */}
            <div className="grid grid-cols-2 gap-4">
              <div>
                <span className="text-sm text-slate-400">负责人</span>
                <p className="text-white font-medium">
                  {risk.owner_name || "未分配"}
                </p>
              </div>
              <div>
                <span className="text-sm text-slate-400">跟踪日期</span>
                <p className="text-white font-medium">
                  {risk.follow_up_date
                    ? formatDate(risk.follow_up_date)
                    : "未设置"}
                </p>
              </div>
              {risk.last_update && (
                <div className="col-span-2">
                  <span className="text-sm text-slate-400">最新进展</span>
                  <p className="text-white mt-1 whitespace-pre-wrap">
                    {risk.last_update}
                  </p>
                </div>
              )}
            </div>

            {/* Trigger Condition */}
            {risk.trigger_condition && (
              <div>
                <span className="text-sm text-slate-400">触发条件</span>
                <p className="text-white mt-1">{risk.trigger_condition}</p>
              </div>
            )}

            {/* Close Info */}
            {risk.status === "CLOSED" && (
              <div className="p-3 rounded-xl bg-white/[0.02] border border-white/5">
                <span className="text-xs text-slate-400">关闭信息</span>
                <div className="mt-2 space-y-1">
                  {risk.closed_date && (
                    <p className="text-white text-sm">
                      关闭日期: {formatDate(risk.closed_date)}
                    </p>
                  )}
                  {risk.closed_reason && (
                    <p className="text-white text-sm whitespace-pre-wrap">
                      关闭原因: {risk.closed_reason}
                    </p>
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
