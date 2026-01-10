/**
 * ECNApprovalsTab Component
 * ECN 审批流程 Tab 组件（时间线视图）
 */
import { useState } from "react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
  CardDescription,
} from "../ui/card";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { CheckCircle2, XCircle } from "lucide-react";
import { formatDate } from "../../lib/utils";
import { ecnApi } from "../../services/api";

export default function ECNApprovalsTab({ approvals, refetch }) {
  const [processing, setProcessing] = useState(null);

  // 处理审批通过
  const handleApprove = async (approvalId) => {
    const comment = prompt("请输入审批意见（可选）：") || "";
    if (comment === null) return; // 用户取消

    setProcessing(approvalId);
    try {
      await ecnApi.approve(approvalId, comment);
      await refetch();
      alert("审批通过");
    } catch (error) {
      alert("审批失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setProcessing(null);
    }
  };

  // 处理审批驳回
  const handleReject = async (approvalId) => {
    const reason = prompt("请输入驳回原因：");
    if (!reason) return; // 用户取消或未输入

    setProcessing(approvalId);
    try {
      await ecnApi.reject(approvalId, reason);
      await refetch();
      alert("已驳回");
    } catch (error) {
      alert("驳回失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setProcessing(null);
    }
  };

  if (approvals.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-slate-400">
          暂无审批记录
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="relative">
        {/* 时间线 */}
        <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-slate-200" />

        <div className="space-y-6">
          {approvals.map((approval, index) => {
            const isCompleted = approval.status === "COMPLETED";
            const isApproved = approval.approval_result === "APPROVED";
            const isRejected = approval.approval_result === "REJECTED";
            const isPending = approval.status === "PENDING";
            const isProcessing = processing === approval.id;

            return (
              <div
                key={approval.id}
                className="relative flex items-start gap-4"
              >
                {/* 时间线节点 */}
                <div className="relative z-10">
                  <div
                    className={`w-10 h-10 rounded-full flex items-center justify-center ${
                      isApproved
                        ? "bg-green-500"
                        : isRejected
                          ? "bg-red-500"
                          : isPending
                            ? "bg-blue-500"
                            : "bg-slate-300"
                    } text-white font-bold shadow-lg`}
                  >
                    {isCompleted ? (
                      isApproved ? (
                        <CheckCircle2 className="w-5 h-5" />
                      ) : isRejected ? (
                        <XCircle className="w-5 h-5" />
                      ) : (
                        index + 1
                      )
                    ) : (
                      index + 1
                    )}
                  </div>
                </div>

                {/* 审批卡片 */}
                <Card className="flex-1 shadow-sm">
                  <CardHeader>
                    <div className="flex justify-between items-center">
                      <div>
                        <CardTitle className="text-base">
                          第{approval.approval_level}级审批
                        </CardTitle>
                        <CardDescription className="mt-1">
                          {approval.approval_role}
                        </CardDescription>
                      </div>
                      <div className="flex items-center gap-2">
                        <Badge
                          className={
                            isApproved
                              ? "bg-green-500"
                              : isRejected
                                ? "bg-red-500"
                                : isPending
                                  ? "bg-blue-500"
                                  : "bg-slate-500"
                          }
                        >
                          {isApproved
                            ? "已通过"
                            : isRejected
                              ? "已驳回"
                              : isPending
                                ? "待审批"
                                : approval.status}
                        </Badge>
                        {approval.is_overdue && (
                          <Badge className="bg-red-500">超期</Badge>
                        )}
                      </div>
                    </div>
                  </CardHeader>
                  <CardContent className="space-y-3">
                    <div className="text-sm">
                      <span className="text-slate-500">审批人:</span>{" "}
                      {approval.approver_name || "待分配"}
                    </div>
                    {approval.approved_at && (
                      <div className="text-sm">
                        <span className="text-slate-500">审批时间:</span>{" "}
                        {formatDate(approval.approved_at)}
                      </div>
                    )}
                    {approval.due_date && (
                      <div className="text-sm">
                        <span className="text-slate-500">审批期限:</span>{" "}
                        {formatDate(approval.due_date)}
                      </div>
                    )}
                    {approval.approval_opinion && (
                      <div>
                        <div className="text-sm text-slate-500 mb-1">
                          审批意见:
                        </div>
                        <div className="p-2 bg-slate-50 rounded text-sm">
                          {approval.approval_opinion}
                        </div>
                      </div>
                    )}
                    {isPending && (
                      <div className="flex justify-end gap-2 pt-2">
                        <Button
                          size="sm"
                          variant="outline"
                          onClick={() => handleReject(approval.id)}
                          disabled={isProcessing}
                        >
                          驳回
                        </Button>
                        <Button
                          size="sm"
                          onClick={() => handleApprove(approval.id)}
                          disabled={isProcessing}
                        >
                          {isProcessing ? "处理中..." : "通过"}
                        </Button>
                      </div>
                    )}
                  </CardContent>
                </Card>
              </div>
            );
          })}
        </div>
      </div>
    </div>
  );
}
