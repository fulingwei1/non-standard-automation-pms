/**
 * ECN审批流程标签页组件
 * 用途：展示和管理ECN的审批流程（时间线视图）
 */
import React from 'react';
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from '../ui/card';
import { Button } from '../ui/button';
import { Badge } from '../ui/badge';
import { CheckCircle2, XCircle } from 'lucide-react';

/**
 * 获取审批节点样式配置
 */
const getApprovalNodeStyle = (approval) => {
  const _isCompleted = approval.status === 'COMPLETED';
  const isApproved = approval.approval_result === 'APPROVED';
  const isRejected = approval.approval_result === 'REJECTED';
  const isPending = approval.status === 'PENDING';

  if (isApproved) {return { color: 'bg-green-500', icon: 'approved' };}
  if (isRejected) {return { color: 'bg-red-500', icon: 'rejected' };}
  if (isPending) {return { color: 'bg-blue-500', icon: 'pending' };}
  return { color: 'bg-slate-300', icon: 'default' };
};

/**
 * 获取审批状态Badge样式
 */
const getApprovalStatusBadge = (approval) => {
  const isApproved = approval.approval_result === 'APPROVED';
  const isRejected = approval.approval_result === 'REJECTED';
  const isPending = approval.status === 'PENDING';

  if (isApproved) {return { className: 'bg-green-500', label: '已通过' };}
  if (isRejected) {return { className: 'bg-red-500', label: '已驳回' };}
  if (isPending) {return { className: 'bg-blue-500', label: '待审批' };}
  return { className: 'bg-slate-500', label: approval.status };
};

/**
 * 时间线节点组件
 */
const TimelineNode = ({ approval, index }) => {
  const { color, icon: _icon } = getApprovalNodeStyle(approval);
  const isCompleted = approval.status === 'COMPLETED';
  const isApproved = approval.approval_result === 'APPROVED';
  const isRejected = approval.approval_result === 'REJECTED';

  return (
    <div className="relative z-10">
      <div
        className={`w-10 h-10 rounded-full flex items-center justify-center ${color} text-white font-bold shadow-lg`}>

        {isCompleted ?
        isApproved ?
        <CheckCircle2 className="w-5 h-5" /> :
        isRejected ?
        <XCircle className="w-5 h-5" /> :

        index + 1 :


        index + 1
        }
      </div>
    </div>);

};

/**
 * 审批卡片组件
 */
const ApprovalCard = ({ approval, onApprove, onReject, formatDate }) => {
  const statusBadge = getApprovalStatusBadge(approval);
  const isPending = approval.status === 'PENDING';

  const handleApprove = () => {
    const comment = prompt('请输入审批意见（可选）：') || '';
    onApprove(approval.id, comment);
  };

  const handleReject = () => {
    const reason = prompt('请输入驳回原因：');
    if (reason) {
      onReject(approval.id, reason);
    }
  };

  return (
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
            <Badge className={statusBadge.className}>
              {statusBadge.label}
            </Badge>
            {approval.is_overdue &&
            <Badge className="bg-red-500">超期</Badge>
            }
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-3">
        {/* 审批人信息 */}
        <div className="text-sm">
          <span className="text-slate-500">审批人:</span>{' '}
          {approval.approver_name || '待分配'}
        </div>

        {/* 审批时间 */}
        {approval.approved_at &&
        <div className="text-sm">
            <span className="text-slate-500">审批时间:</span>{' '}
            {formatDate(approval.approved_at)}
        </div>
        }

        {/* 审批期限 */}
        {approval.due_date &&
        <div className="text-sm">
            <span className="text-slate-500">审批期限:</span>{' '}
            {formatDate(approval.due_date)}
            {approval.is_overdue &&
          <span className="text-red-500 ml-2">（已超期）</span>
          }
        </div>
        }

        {/* 审批意见 */}
        {approval.approval_opinion &&
        <div>
            <div className="text-sm text-slate-500 mb-1">审批意见:</div>
            <div className="p-2 bg-slate-50 rounded text-sm">
              {approval.approval_opinion}
            </div>
        </div>
        }

        {/* 审批操作按钮（仅待审批状态显示） */}
        {isPending &&
        <div className="flex justify-end gap-2 pt-2">
            <Button
            size="sm"
            variant="outline"
            onClick={handleReject}>

              驳回
            </Button>
            <Button size="sm" onClick={handleApprove}>
              通过
            </Button>
        </div>
        }
      </CardContent>
    </Card>);

};

/**
 * ECN审批流程标签页主组件
 */
export const ECNApprovalsTab = ({
  approvals = [],
  onApprove,
  onReject,
  formatDate
}) => {
  // 空状态
  if (approvals.length === 0) {
    return (
      <Card>
        <CardContent className="py-8 text-center text-slate-400">
          暂无审批记录
        </CardContent>
      </Card>);

  }

  return (
    <div className="relative">
      {/* 时间线背景线 */}
      <div className="absolute left-5 top-0 bottom-0 w-0.5 bg-slate-200" />

      {/* 审批节点列表 */}
      <div className="space-y-6">
        {approvals.map((approval, index) =>
        <div
          key={approval.id}
          className="relative flex items-start gap-4">

            {/* 时间线节点 */}
            <TimelineNode approval={approval} index={index} />

            {/* 审批卡片 */}
            <ApprovalCard
            approval={approval}
            onApprove={onApprove}
            onReject={onReject}
            formatDate={formatDate} />

        </div>
        )}
      </div>
    </div>);

};

export default ECNApprovalsTab;