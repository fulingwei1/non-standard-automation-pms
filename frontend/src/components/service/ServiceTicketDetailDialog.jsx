/**
 * Service Ticket Detail Dialog Component
 * 服务工单详情对话框组件
 */

import { useState } from "react";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogBody,
  DialogFooter,
} from "../../components/ui/dialog";
import { Badge } from "../../components/ui/badge";
import { Button } from "../../components/ui/button";
import { Textarea } from "../../components/ui/textarea";
import { toast } from "../../components/ui/toast";
import { Star, Phone, Calendar, User, CheckCircle2 } from "lucide-react";
import { statusConfigs, urgencyConfigs, problemTypeConfigs } from "@/lib/constants/service";
import { cn, formatDate } from "../../lib/utils";
import { ServiceTicketAssignDialog } from "./ServiceTicketAssignDialog";

export function ServiceTicketDetailDialog({ ticket, onClose, onAssign, onCloseTicket }) {
  const [showAssignDialog, setShowAssignDialog] = useState(false);
  const [showCloseDialog, setShowCloseDialog] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [closeData, setCloseData] = useState({
    solution: "",
    root_cause: "",
    preventive_action: "",
    satisfaction: "",
    feedback: "",
  });

  const resolveConfigByKeyOrLabel = (configs, value, fallbackKey) => {
    if (!configs) {return undefined;}
    if (!value) {return configs[fallbackKey] || Object.values(configs)[0];}
    return (
      configs[value] ||
      Object.values(configs).find((config) => config.label === value) ||
      configs[fallbackKey] ||
      Object.values(configs)[0]
    );
  };

  const status = resolveConfigByKeyOrLabel(statusConfigs, ticket.status, "PENDING");
  const urgency = resolveConfigByKeyOrLabel(urgencyConfigs, ticket.urgency, "NORMAL");
  const problemType = resolveConfigByKeyOrLabel(problemTypeConfigs, ticket.problem_type, "其他");

  const handleClose = async () => {
    if (!closeData.solution || !closeData.solution.trim()) {
      toast.warning("请填写解决方案");
      return;
    }
    if (!closeData.satisfaction) {
      toast.warning("请选择客户满意度评分");
      return;
    }

    if (submitting) {return;}

    try {
      setSubmitting(true);
      await onCloseTicket(ticket.id, closeData);
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <>
      <Dialog open onOpenChange={onClose}>
        <DialogContent className="max-w-4xl bg-slate-900 border-slate-700 max-h-[90vh] overflow-y-auto">
          <DialogHeader>
            <DialogTitle className="flex items-center gap-2">
              <span className="font-mono">{ticket.ticket_no}</span>
              <Badge className={cn(status.color, "text-xs")}>
                {status.label}
              </Badge>
              <Badge className={cn(urgency.bg, urgency.textColor, "text-xs")}>
                {urgency.label}
              </Badge>
            </DialogTitle>
            <DialogDescription>服务工单详情</DialogDescription>
          </DialogHeader>
          <DialogBody>
            <div className="space-y-6">
              {/* Basic Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400 mb-1">项目信息</p>
                  <p className="text-white">
                    {ticket.project_code} - {ticket.project_name}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">机台号</p>
                  <p className="text-white">{ticket.machine_no || "-"}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">客户名称</p>
                  <p className="text-white">{ticket.customer_name}</p>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">问题类型</p>
                  <p className="text-white">
                    {problemType.icon} {problemType.label}
                  </p>
                </div>
              </div>

              {/* Problem Description */}
              <div>
                <p className="text-sm text-slate-400 mb-1">问题描述</p>
                <p className="text-white bg-slate-800/50 p-3 rounded-lg">
                  {ticket.problem_desc}
                </p>
              </div>

              {/* Contact Info */}
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <p className="text-sm text-slate-400 mb-1">报告人</p>
                  <div className="flex items-center gap-2">
                    <User className="w-4 h-4 text-slate-400" />
                    <span className="text-white">{ticket.reported_by}</span>
                  </div>
                </div>
                <div>
                  <p className="text-sm text-slate-400 mb-1">联系电话</p>
                  <div className="flex items-center gap-2">
                    <Phone className="w-4 h-4 text-slate-400" />
                    <span className="text-white">{ticket.reported_phone || "-"}</span>
                  </div>
                </div>
              </div>

              {/* Timeline */}
              <div className="space-y-3">
                <p className="text-sm text-slate-400 mb-2">处理时间线</p>
                
                <div className="flex items-start gap-3">
                  <div className="w-2 h-2 bg-blue-400 rounded-full mt-2" />
                  <div className="flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm text-white">工单创建</span>
                      <Calendar className="w-3 h-3 text-slate-400" />
                    </div>
                    <span className="text-xs text-slate-500">
                      {formatDate(ticket.created_time)}
                    </span>
                  </div>
                </div>

                {ticket.assigned_time && (
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-yellow-400 rounded-full mt-2" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-white">工单分配</span>
                        <User className="w-3 h-3 text-slate-400" />
                      </div>
                      <span className="text-xs text-slate-500">
                        {formatDate(ticket.assigned_time)}
                      </span>
                      {ticket.assignee_name && (
                        <div className="mt-1">
                          <span className="text-xs text-slate-400">
                            负责人: {ticket.assignee_name}
                          </span>
                        </div>
                      )}
                    </div>
                  </div>
                )}

                {ticket.resolved_time && (
                  <div className="flex items-start gap-3">
                    <div className="w-2 h-2 bg-green-400 rounded-full mt-2" />
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <span className="text-sm text-white">工单解决</span>
                        <CheckCircle2 className="w-3 h-3 text-slate-400" />
                      </div>
                      <span className="text-xs text-slate-500">
                        {formatDate(ticket.resolved_time)}
                      </span>
                    </div>
                  </div>
                )}
              </div>

              {/* Solution */}
              {ticket.solution && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">解决方案</p>
                  <p className="text-white bg-slate-800/50 p-3 rounded-lg">
                    {ticket.solution}
                  </p>
                </div>
              )}

              {/* Satisfaction */}
              {ticket.satisfaction && (
                <div>
                  <p className="text-sm text-slate-400 mb-1">客户满意度</p>
                  <div className="flex items-center gap-2">
                    <div className="flex items-center gap-1">
                      {[1, 2, 3, 4, 5].map((i) => (
                        <Star
                          key={i}
                          className={cn(
                            "w-5 h-5",
                            i <= ticket.satisfaction
                              ? "fill-yellow-400 text-yellow-400"
                              : "text-slate-600",
                          )}
                        />
                      ))}
                    </div>
                    <span className="text-white">{ticket.satisfaction}/5</span>
                  </div>
                  {ticket.feedback && (
                    <p className="text-slate-400 text-sm mt-2 bg-slate-800/50 p-3 rounded-lg">
                      {ticket.feedback}
                    </p>
                  )}
                </div>
              )}

              {/* Action Buttons Info */}
              <div className="border-t border-slate-700 pt-4">
                <p className="text-sm text-slate-400 mb-2">操作提示</p>
                <div className="text-xs text-slate-500 space-y-1">
                  {ticket.status === "待分配" && (
                    <p>• 点击"分配工单"按钮，将此工单分配给负责的工程师</p>
                  )}
                  {ticket.status === "待验证" && (
                    <p>
                      • 点击"关闭工单"按钮，填写解决方案和客户反馈后关闭工单
                    </p>
                  )}
                  {ticket.status === "处理中" && (
                    <p>• 工单正在处理中，等待工程师完成处理</p>
                  )}
                  {ticket.status === "已关闭" && (
                    <p>• 工单已关闭，如需重新打开请联系管理员</p>
                  )}
                </div>
              </div>
            </div>
          </DialogBody>
          <DialogFooter>
            <div className="flex items-center justify-between w-full">
              <div className="text-xs text-slate-400">
                提示：按 ESC 键可关闭对话框
              </div>
              <div className="flex gap-2">
                {ticket.status === "待分配" && (
                  <Button
                    variant="outline"
                    onClick={() => setShowAssignDialog(true)}
                    disabled={submitting}
                  >
                    分配工单
                  </Button>
                )}
                {ticket.status === "待验证" && (
                  <Button
                    onClick={() => setShowCloseDialog(true)}
                    disabled={submitting}
                  >
                    关闭工单
                  </Button>
                )}
                <Button
                  variant="outline"
                  onClick={onClose}
                >
                  关闭
                </Button>
              </div>
            </div>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Assign Dialog */}
      {showAssignDialog && (
        <ServiceTicketAssignDialog
          ticketId={ticket.id}
          onClose={() => setShowAssignDialog(false)}
          onSubmit={(assignData) => onAssign(ticket.id, assignData)}
        />
      )}

      {/* Close Dialog */}
      {showCloseDialog && (
        <Dialog open onOpenChange={() => setShowCloseDialog(false)}>
          <DialogContent className="max-w-md bg-slate-900 border-slate-700">
            <DialogHeader>
              <DialogTitle>关闭工单</DialogTitle>
              <DialogDescription>
                请填写解决方案和客户反馈信息
              </DialogDescription>
            </DialogHeader>
            <DialogBody>
              <div className="space-y-4">
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">
                    解决方案 *
                  </label>
                  <Textarea
                    value={closeData.solution}
                    onChange={(e) =>
                      setCloseData({ ...closeData, solution: e.target.value })
                    }
                    placeholder="请详细描述解决方案..."
                    rows={3}
                    className="bg-slate-800/50 border-slate-700"
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">
                    根本原因分析
                  </label>
                  <Textarea
                    value={closeData.root_cause}
                    onChange={(e) =>
                      setCloseData({ ...closeData, root_cause: e.target.value })
                    }
                    placeholder="问题根本原因分析..."
                    rows={2}
                    className="bg-slate-800/50 border-slate-700"
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">
                    预防措施
                  </label>
                  <Textarea
                    value={closeData.preventive_action}
                    onChange={(e) =>
                      setCloseData({ ...closeData, preventive_action: e.target.value })
                    }
                    placeholder="预防类似问题的措施..."
                    rows={2}
                    className="bg-slate-800/50 border-slate-700"
                  />
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">
                    客户满意度 *
                  </label>
                  <select
                    value={closeData.satisfaction}
                    onChange={(e) =>
                      setCloseData({ ...closeData, satisfaction: e.target.value })
                    }
                    className="w-full px-3 py-2 bg-slate-800/50 border border-slate-700 rounded-lg text-white"
                  >
                    <option value="">请选择满意度</option>
                    <option value="5">非常满意 (5星)</option>
                    <option value="4">满意 (4星)</option>
                    <option value="3">一般 (3星)</option>
                    <option value="2">不满意 (2星)</option>
                    <option value="1">非常不满意 (1星)</option>
                  </select>
                </div>
                <div>
                  <label className="text-sm text-slate-400 mb-1 block">
                    客户反馈
                  </label>
                  <Textarea
                    value={closeData.feedback}
                    onChange={(e) =>
                      setCloseData({ ...closeData, feedback: e.target.value })
                    }
                    placeholder="客户反馈意见..."
                    rows={2}
                    className="bg-slate-800/50 border-slate-700"
                  />
                </div>
              </div>
            </DialogBody>
            <DialogFooter>
              <Button
                variant="outline"
                onClick={() => setShowCloseDialog(false)}
                disabled={submitting}
              >
                取消
              </Button>
              <Button onClick={handleClose} disabled={submitting}>
                {submitting ? "关闭中..." : "关闭工单"}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      )}
    </>
  );
}
