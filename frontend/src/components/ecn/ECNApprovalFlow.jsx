/**
 * ECN Approval Flow Component - Updated with Unified Approval System
 * ECN 审批流程可视化组件 - 已更新为统一审批系统
 */

import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { Textarea } from "../../components/ui/textarea";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogBody,
  DialogFooter } from
"../../components/ui/dialog";
import {
  CheckCircle2,
  XCircle,
  Clock,
  AlertTriangle,
  User,
  Calendar,
  MessageSquare,
  UserPlus } from
"lucide-react";
import {
  approvalStatusConfigs,
  getStatusConfig as _getStatusConfig,
  formatStatus } from
"./ecnConstants";
import { cn, formatDate } from "../../lib/utils";
import { useState } from "react";
import { toast } from "sonner";
import {
  approveApproval,
  rejectApproval,
  delegateApproval,
  APPROVAL_STATUS,
  getStatusConfig
} from "../../services/api/approval.js";

export function ECNApprovalFlow({
  approvals,
  ecn,
  onApprove,
  onReject,
  currentUser,
  loading: _loading,
  approvalInstance = null,
  onRefreshApprovals = () => {}
}) {
  const [showApprovalDialog, setShowApprovalDialog] = useState(false);
  const [showDelegateDialog, setShowDelegateDialog] = useState(false);
  const [approvalForm, setApprovalForm] = useState({
    action: "", // "approve", "reject", or "delegate"
    comment: ""
  });
  const [delegateForm, setDelegateForm] = useState({
    delegate_to_id: null,
    comment: ""
  });
  const [submitting, setSubmitting] = useState(false);

  const statusOrder = [
  "SUBMITTED",
  "EVALUATING",
  "EVALUATED",
  "PENDING_APPROVAL",
  "APPROVED",
  "REJECTED"];


  const _getCurrentApprovalStep = () => {
    const currentIndex = statusOrder.indexOf(ecn.status);
    return currentIndex >= 0 ? currentIndex : 0;
  };

  const getApprovalIcon = (status) => {
    const _statusConfig = approvalStatusConfigs[status];
    switch (status) {
      case "APPROVED":
        return <CheckCircle2 className="w-5 h-5 text-green-500" />;
      case "REJECTED":
        return <XCircle className="w-5 h-5 text-red-500" />;
      case "PENDING":
        return <Clock className="w-5 h-5 text-yellow-500" />;
      default:
        return <AlertTriangle className="w-5 h-5 text-slate-400" />;
    }
  };

  const handleApproval = async () => {
    if (!approvalForm.action || !approvalForm.comment.trim()) {
      toast.warning("请填写审批意见");
      return;
    }

    try {
      setSubmitting(true);

      if (approvalInstance) {
        if (approvalForm.action === "approve") {
          await approveApproval(approvalInstance.id, approvalForm.comment);
          toast.success("审批已批准");
        } else if (approvalForm.action === "reject") {
          await rejectApproval(approvalInstance.id, approvalForm.comment);
          toast.success("审批已驳回");
        }
      } else {
        if (onApprove && approvalForm.action === "approve") {
          await onApprove({
            ecn_id: ecn.id,
            comment: approvalForm.comment,
            approved_by: currentUser.name,
            approved_time: new Date().toISOString()
          });
        } else if (onReject && approvalForm.action === "reject") {
          await onReject({
            ecn_id: ecn.id,
            comment: approvalForm.comment,
            rejected_by: currentUser.name,
            rejected_time: new Date().toISOString()
          });
        }
      }

      await onRefreshApprovals();
    } catch (error) {
      console.error("Approval failed:", error);
      toast.error("审批失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setSubmitting(false);
      setApprovalForm({ action: "", comment: "" });
      setShowApprovalDialog(false);
    }
  };

  const canApprove = () => {
    if (approvalInstance) {
      return approvalInstance.status === APPROVAL_STATUS.PENDING &&
             currentUser && (
               currentUser.role === "MANAGER" || currentUser.role === "DIRECTOR");
    }
    return ecn.status === "PENDING_APPROVAL" &&
           currentUser && (
             currentUser.role === "MANAGER" || currentUser.role === "DIRECTOR");
  };

  const handleDelegate = async () => {
    if (!delegateForm.delegate_to_id || !delegateForm.comment.trim()) {
      toast.warning("请选择被委托人并填写委托说明");
      return;
    }

    try {
      setSubmitting(true);

      if (approvalInstance) {
        await delegateApproval(
          approvalInstance.id,
          delegateForm.delegate_to_id,
          delegateForm.comment
        );
        toast.success("审批已委托");
      }

      await onRefreshApprovals();
    } catch (error) {
      console.error("Delegate failed:", error);
      toast.error("委托失败: " + (error.response?.data?.detail || error.message));
    } finally {
      setSubmitting(false);
      setDelegateForm({ delegate_to_id: null, comment: "" });
      setShowDelegateDialog(false);
    }
  };

  return (
    <>
      {approvals.length === 0 ?
      <Card>
          <CardContent className="py-8 text-center text-slate-400">
            暂无审批记录
          </CardContent>
      </Card> :

      <div className="relative">
          {/* 时间线背景线 */}
          <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-slate-600" />
          
          <div className="space-y-6">
            {approvals.map((approval, _index) =>
          <div key={approval.id} className="relative flex items-start gap-4">
                {/* 状态图标 */}
                <div className="relative z-10">
                  <div className={cn(
                "w-16 h-16 rounded-full flex items-center justify-center bg-slate-800 border-2",
                approval.status === "APPROVED" && "border-green-500 bg-green-500/10",
                approval.status === "REJECTED" && "border-red-500 bg-red-500/10",
                approval.status === "PENDING" && "border-yellow-500 bg-yellow-500/10"
              )}>
                    {getApprovalIcon(approval.status)}
                  </div>
                </div>

                {/* 审批内容 */}
                <div className="flex-1 min-w-0">
                  <Card className="border-l-4 border-l-slate-600">
                    <CardHeader className="pb-3">
                      <div className="flex justify-between items-start">
                        <div>
                          <CardTitle className="text-base flex items-center gap-2">
                            {approval.approval_type || "审批"}
                            <Badge className={cn(
                          approvalStatusConfigs[approval.status]?.color,
                          approvalStatusConfigs[approval.status]?.textColor,
                          "text-xs"
                        )}>
                              {formatStatus(approval.status)}
                            </Badge>
                          </CardTitle>
                          <div className="flex items-center gap-4 mt-1 text-sm text-slate-500">
                            <div className="flex items-center gap-1">
                              <User className="w-3 h-3" />
                              {approval.approver_name || approval.approver}
                            </div>
                            <div className="flex items-center gap-1">
                              <Calendar className="w-3 h-3" />
                              {formatDate(approval.approval_time || approval.created_time)}
                            </div>
                            {approval.department &&
                        <span>{approval.department}</span>
                        }
                          </div>
                        </div>
                      </div>
                    </CardHeader>
                    <CardContent>
                      <div className="space-y-3">
                        {approval.comment &&
                    <div>
                            <div className="text-sm text-slate-500 mb-1 flex items-center gap-1">
                              <MessageSquare className="w-3 h-3" />
                              审批意见
                            </div>
                            <div className="text-white bg-slate-800/50 p-3 rounded-lg text-sm">
                              {approval.comment}
                            </div>
                    </div>
                    }

                        {approval.conditions && approval.conditions.length > 0 &&
                    <div>
                            <div className="text-sm text-slate-500 mb-1">审批条件</div>
                            <ul className="text-white text-sm space-y-1">
                              {approval.conditions.map((condition, idx) =>
                        <li key={idx} className="flex items-center gap-2">
                                  <span className="w-1.5 h-1.5 bg-blue-400 rounded-full" />
                                  {condition}
                        </li>
                        )}
                            </ul>
                    </div>
                    }

                        {approval.attachments && approval.attachments.length > 0 &&
                    <div>
                            <div className="text-sm text-slate-500 mb-1">附件</div>
                            <div className="flex flex-wrap gap-2">
                              {approval.attachments.map((attachment, idx) =>
                        <Badge key={idx} variant="outline" className="text-xs">
                                  {attachment.name}
                        </Badge>
                        )}
                            </div>
                    </div>
                    }
                      </div>
                    </CardContent>
                  </Card>
                </div>
          </div>
          )}

            {/* 当前待审批状态 */}
            {canApprove() &&
          <div className="relative flex items-start gap-4">
                <div className="relative z-10">
                  <div className="w-16 h-16 rounded-full flex items-center justify-center bg-blue-500/20 border-2 border-blue-500 animate-pulse">
                    <Clock className="w-6 h-6 text-blue-500" />
                  </div>
                </div>
                <div className="flex-1">
                  <Card className="border-l-4 border-l-blue-500 bg-blue-500/5">
                    <CardContent className="pt-6">
                      <div className="flex justify-between items-center">
                        <div>
                          <h4 className="text-base font-semibold text-white">待审批</h4>
                          <p className="text-sm text-slate-400 mt-1">
                            此ECN等待您的审批
                          </p>
                        </div>
                        <div className="flex gap-2">
                          <Button
                        variant="outline"
                        size="sm"
                        onClick={() => {
                          setApprovalForm({ action: "reject", comment: "" });
                          setShowApprovalDialog(true);
                        }}
                        className="border-red-500 text-red-400 hover:bg-red-500 hover:text-white">
 
                            驳回
                          </Button>
                          <Button
                        variant="outline"
                        size="sm"
                        onClick={() => setShowDelegateDialog(true)}
                        className="border-blue-500 text-blue-400 hover:bg-blue-500 hover:text-white">
 
                            委托
                          </Button>
                          <Button
                        size="sm"
                        onClick={() => {
                          setApprovalForm({ action: "approve", comment: "" });
                          setShowApprovalDialog(true);
                        }}
                        className="bg-green-600 hover:bg-green-700">
 
                            批准
                          </Button>
                        </div>
                      </div>
                    </CardContent>
                  </Card>
                </div>
          </div>
          }
          </div>
      </div>
      }

      {/* 审批对话框 */}
      <Dialog open={showApprovalDialog} onOpenChange={setShowApprovalDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>
              {approvalForm.action === "approve" ? "批准ECN" : "驳回ECN"}
            </DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">审批意见 *</label>
              <Textarea
                value={approvalForm.comment}
                onChange={(e) =>
                  setApprovalForm({ ...approvalForm, comment: e.target.value })
                }
                placeholder={approvalForm.action === "approve" ?
                "请输入批准理由..." :
                "请输入驳回理由..."
                }
                rows={4} />
 
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowApprovalDialog(false)}
              disabled={submitting}>
 
              取消
            </Button>
            <Button
              onClick={handleApproval}
              disabled={submitting}
              className={approvalForm.action === "approve" ?
              "bg-green-600 hover:bg-green-700" :
              "bg-red-600 hover:bg-red-700"
              }>
 
              {submitting ? "提交中..." : (approvalForm.action === "approve" ? "批准" : "驳回")}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* 委托审批对话框 */}
      <Dialog open={showDelegateDialog} onOpenChange={setShowDelegateDialog}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>委托审批</DialogTitle>
          </DialogHeader>
          <DialogBody className="space-y-4">
            <div>
              <label className="text-sm font-medium mb-2 block">被委托人 *</label>
              <select
                value={delegateForm.delegate_to_id || ""}
                onChange={(e) =>
                  setDelegateForm({ ...delegateForm, delegate_to_id: Number(e.target.value) })
                }
                className="w-full px-3 py-2 border border-slate-600 rounded-lg bg-slate-800 text-white focus:outline-none focus:ring-2 focus:ring-blue-500">
                <option value="">请选择被委托人...</option>
                <option value="8">王经理</option>
                <option value="9">李总监</option>
                <option value="10">张经理</option>
              </select>
            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">委托说明 *</label>
              <Textarea
                value={delegateForm.comment}
                onChange={(e) =>
                  setDelegateForm({ ...delegateForm, comment: e.target.value })
                }
                placeholder="请输入委托说明..."
                rows={3} />
            </div>
          </DialogBody>
          <DialogFooter>
            <Button
              variant="outline"
              onClick={() => setShowDelegateDialog(false)}
              disabled={submitting}>
              取消
            </Button>
            <Button
              onClick={handleDelegate}
              disabled={submitting}
              className="bg-blue-600 hover:bg-blue-700">
              {submitting ? "提交中..." : "委托"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </>);

}