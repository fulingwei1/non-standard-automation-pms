import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  Button,
  Badge
} from "../../components/ui";
import { cn } from "../../lib/utils";
import { formatCurrency } from "./utils";

const ApprovalDetailDialog = ({
  open,
  onOpenChange,
  selectedApproval
}) => {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-2xl">
        <DialogHeader>
          <DialogTitle>审批详情</DialogTitle>
          <DialogDescription>
            {selectedApproval?.department} · {selectedApproval?.applicant}
          </DialogDescription>
        </DialogHeader>
        <DialogBody>
          {selectedApproval &&
          <div className="space-y-4">
              <div className="flex items-center gap-2">
                <Badge
                variant="outline"
                className={cn(
                  selectedApproval.type === "office_supplies" &&
                  "bg-blue-500/20 text-blue-400 border-blue-500/30",
                  selectedApproval.type === "vehicle" &&
                  "bg-cyan-500/20 text-cyan-400 border-cyan-500/30",
                  selectedApproval.type === "asset" &&
                  "bg-purple-500/20 text-purple-400 border-purple-500/30",
                  selectedApproval.type === "meeting" &&
                  "bg-green-500/20 text-green-400 border-green-500/30",
                  selectedApproval.type === "leave" &&
                  "bg-pink-500/20 text-pink-400 border-pink-500/30"
                )}>
                  {selectedApproval.type === "office_supplies" ?
                "办公用品" :
                selectedApproval.type === "vehicle" ?
                "车辆" :
                selectedApproval.type === "asset" ?
                "资产" :
                selectedApproval.type === "meeting" ?
                "会议" :
                "请假"}
                </Badge>
                {selectedApproval.priority === "high" &&
              <Badge className="text-xs bg-red-500/20 text-red-400 border-red-500/30">
                    紧急
              </Badge>
              }
              </div>
              <div>
                <h3 className="text-lg font-semibold text-white mb-2">
                  {selectedApproval.title}
                </h3>
                {selectedApproval.items &&
              <div className="mb-2">
                    <p className="text-sm text-slate-400 mb-1">物品清单:</p>
                    <div className="flex flex-wrap gap-2">
                      {selectedApproval.items.map((item, idx) =>
                  <Badge key={idx} variant="outline">
                          {item}
                  </Badge>
                  )}
                    </div>
              </div>
              }
                {selectedApproval.amount &&
              <div className="mb-2">
                    <p className="text-sm text-slate-400">申请金额:</p>
                    <p className="text-lg font-bold text-amber-400">
                      {formatCurrency(selectedApproval.amount)}
                    </p>
              </div>
              }
                {selectedApproval.purpose &&
              <div className="mb-2">
                    <p className="text-sm text-slate-400">用途:</p>
                    <p className="text-white">{selectedApproval.purpose}</p>
              </div>
              }
                {selectedApproval.room &&
              <div className="mb-2">
                    <p className="text-sm text-slate-400">会议室:</p>
                    <p className="text-white">
                      {selectedApproval.room} · {selectedApproval.date}{" "}
                      {selectedApproval.time}
                    </p>
              </div>
              }
                {selectedApproval.days &&
              <div className="mb-2">
                    <p className="text-sm text-slate-400">请假天数:</p>
                    <p className="text-white">{selectedApproval.days} 天</p>
              </div>
              }
                <div className="mt-4 pt-4 border-t border-slate-700/50">
                  <p className="text-xs text-slate-500">
                    提交时间: {selectedApproval.submitTime}
                  </p>
                </div>
              </div>
              <div className="flex gap-2 pt-4">
                <Button className="flex-1">批准</Button>
                <Button variant="outline" className="flex-1">
                  拒绝
                </Button>
              </div>
          </div>
          }
        </DialogBody>
      </DialogContent>
    </Dialog>
  );
};

export default ApprovalDetailDialog;
