import { CheckCircle2, Send, XCircle } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { Progress } from "../../components/ui/progress";
import { formatDate } from "../../lib/utils";
import { statusConfigs, typeConfigs } from "./constants";

export default function PlanDetailDialog({
  open,
  onOpenChange,
  selectedPlan,
  onSubmitPlan,
  onApprovePlan,
  onPublish,
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl">
        <DialogHeader>
          <DialogTitle>
            {selectedPlan?.plan_name} - {selectedPlan?.plan_no}
          </DialogTitle>
          <DialogDescription>
            查看生产计划详情并按当前状态推进审批或发布。
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          {selectedPlan && (
            <div className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <div className="text-sm text-slate-500 mb-1">计划编号</div>
                  <div className="font-mono">{selectedPlan.plan_no}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">状态</div>
                  <Badge className={statusConfigs[selectedPlan.status]?.color}>
                    {statusConfigs[selectedPlan.status]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">计划类型</div>
                  <Badge className={typeConfigs[selectedPlan.plan_type]?.color}>
                    {typeConfigs[selectedPlan.plan_type]?.label}
                  </Badge>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">项目</div>
                  <div>{selectedPlan.project_name || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">车间</div>
                  <div>{selectedPlan.workshop_name || "-"}</div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">进度</div>
                  <div className="space-y-1">
                    <div className="text-lg font-bold">
                      {selectedPlan.progress || 0}%
                    </div>
                    <Progress value={selectedPlan.progress || 0} className="h-2" />
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">计划开始</div>
                  <div>
                    {selectedPlan.plan_start_date
                      ? formatDate(selectedPlan.plan_start_date)
                      : "-"}
                  </div>
                </div>
                <div>
                  <div className="text-sm text-slate-500 mb-1">计划结束</div>
                  <div>
                    {selectedPlan.plan_end_date
                      ? formatDate(selectedPlan.plan_end_date)
                      : "-"}
                  </div>
                </div>
              </div>
              {selectedPlan.description && (
                <div>
                  <div className="text-sm text-slate-500 mb-1">描述</div>
                  <div>{selectedPlan.description}</div>
                </div>
              )}
            </div>
          )}
        </DialogBody>
        <DialogFooter>
          <Button variant="outline" onClick={() => onOpenChange(false)}>
            关闭
          </Button>
          {selectedPlan && selectedPlan.status === "DRAFT" && (
            <Button onClick={() => onSubmitPlan(selectedPlan.id)}>
              <Send className="w-4 h-4 mr-2" />
              提交审批
            </Button>
          )}
          {selectedPlan && selectedPlan.status === "SUBMITTED" && (
            <>
              <Button onClick={() => onApprovePlan(selectedPlan.id, true)}>
                <CheckCircle2 className="w-4 h-4 mr-2" />
                审批通过
              </Button>
              <Button variant="outline" onClick={() => onApprovePlan(selectedPlan.id, false)}>
                <XCircle className="w-4 h-4 mr-2" />
                审批驳回
              </Button>
            </>
          )}
          {selectedPlan && selectedPlan.status === "APPROVED" && (
            <Button onClick={() => onPublish(selectedPlan.id)}>
              <CheckCircle2 className="w-4 h-4 mr-2" />
              发布计划
            </Button>
          )}
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}
