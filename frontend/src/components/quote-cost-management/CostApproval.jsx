import { Send } from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent
} from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Badge } from "../../components/ui/badge";
import { formatDate } from "../../lib/utils";

export function CostApproval({ approvalHistory, onSubmitApproval }) {
  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>成本审批流程</CardTitle>
            <CardDescription>
              提交成本审批，确保毛利率符合要求
            </CardDescription>
          </div>
          <Button onClick={onSubmitApproval}>
            <Send className="h-4 w-4 mr-2" />
            提交审批
          </Button>
        </div>
      </CardHeader>
      <CardContent>
        {approvalHistory.length > 0 ? (
          <div className="space-y-4">
            {approvalHistory.map((approval) => (
              <div
                key={approval.id}
                className="border border-slate-700 rounded-lg p-4"
              >
                <div className="flex items-center justify-between mb-2">
                  <div className="flex items-center gap-2">
                    <Badge
                      className={
                        approval.approval_status === "APPROVED"
                          ? "bg-green-500"
                          : approval.approval_status === "REJECTED"
                          ? "bg-red-500"
                          : "bg-amber-500"
                      }
                    >
                      {approval.approval_status === "APPROVED"
                        ? "已通过"
                        : approval.approval_status === "REJECTED"
                        ? "已驳回"
                        : "待审批"}
                    </Badge>
                    <span className="text-sm text-slate-400">
                      审批层级:{" "}
                      {approval.approval_level === 1
                        ? "销售经理"
                        : approval.approval_level === 2
                        ? "销售总监"
                        : "财务"}
                    </span>
                  </div>
                  <span className="text-sm text-slate-400">
                    {formatDate(approval.created_at)}
                  </span>
                </div>
                <div className="text-sm text-slate-300 space-y-1">
                  <div>毛利率: {approval.gross_margin?.toFixed(2)}%</div>
                  {approval.approval_comment && (
                    <div>审批意见: {approval.approval_comment}</div>
                  )}
                  {approval.rejected_reason && (
                    <div className="text-red-400">
                      驳回原因: {approval.rejected_reason}
                    </div>
                  )}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="text-center py-8 text-slate-400">暂无审批记录</div>
        )}
      </CardContent>
    </Card>
  );
}
