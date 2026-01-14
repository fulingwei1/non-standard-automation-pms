/**
 * ECN Detail Header Component
 * ECN 详情页头部 - 显示基本信息和操作按钮
 */
import { ArrowLeft, RefreshCw, Edit2, CheckCircle2, XCircle } from "lucide-react";
import { PageHeader } from "../layout";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { getStatusBadge, getTypeBadge, getPriorityBadge } from "./ecnConstants";

export default function ECNDetailHeader({
  ecn,
  loading,
  onBack,
  onRefresh,
  onEdit,
  onSubmit,
  onWithdraw,
  onStartEval,
  onApprove,
  onReject,
  onExecute,
  onVerify,
  onClose,
  canEdit,
  canSubmit,
  canWithdraw,
  canStartEval,
  canApprove,
  canExecute,
  canVerify,
  canClose,
}) {
  if (loading || !ecn) {
    return (
      <PageHeader
        title="加载中..."
        description="正在加载ECN详情"
        leftAction={<Button onClick={onBack} variant="ghost" size="sm"><ArrowLeft className="w-4 h-4" /></Button>}
      />
    );
  }

  const statusBadge = getStatusBadge(ecn.status);
  const typeBadge = getTypeBadge(ecn.change_type);
  const priorityBadge = getPriorityBadge(ecn.priority);

  const renderActions = () => {
    const actions = [];

    if (canEdit) {
      actions.push(
        <Button key="edit" onClick={onEdit} variant="outline" size="sm">
          <Edit2 className="w-4 h-4 mr-2" />
          编辑
        </Button>
      );
    }

    if (canSubmit) {
      actions.push(
        <Button key="submit" onClick={onSubmit} className="bg-blue-600 hover:bg-blue-700">
          提交评估
        </Button>
      );
    }

    if (canWithdraw) {
      actions.push(
        <Button key="withdraw" onClick={onWithdraw} variant="outline">
          撤回
        </Button>
      );
    }

    if (canStartEval) {
      actions.push(
        <Button key="startEval" onClick={onStartEval} className="bg-amber-600 hover:bg-amber-700">
          开始评估
        </Button>
      );
    }

    if (canApprove) {
      actions.push(
        <Button key="approve" onClick={onApprove} className="bg-emerald-600 hover:bg-emerald-700">
          <CheckCircle2 className="w-4 h-4 mr-2" />
          批准
        </Button>,
        <Button key="reject" onClick={onReject} variant="destructive">
          <XCircle className="w-4 h-4 mr-2" />
          驳回
        </Button>
      );
    }

    if (canExecute) {
      actions.push(
        <Button key="execute" onClick={onExecute} className="bg-violet-600 hover:bg-violet-700">
          开始执行
        </Button>
      );
    }

    if (canVerify) {
      actions.push(
        <Button key="verify" onClick={onVerify} className="bg-indigo-600 hover:bg-indigo-700">
          验证完成
        </Button>
      );
    }

    if (canClose) {
      actions.push(
        <Button key="close" onClick={onClose} variant="outline">
          关闭ECN
        </Button>
      );
    }

    return actions;
  };

  return (
    <PageHeader
      title={
        <div className="flex items-center gap-4">
          <span>{ecn.code}</span>
          <Badge className={statusBadge.color}>
            {statusBadge.text}
          </Badge>
          <Badge className={typeBadge.color} variant="outline">
            {typeBadge.text}
          </Badge>
          <Badge className={priorityBadge.color} variant="outline">
            {priorityBadge.text}
          </Badge>
        </div>
      }
      description={ecn.title}
      leftAction={
        <Button onClick={onBack} variant="ghost" size="sm">
          <ArrowLeft className="w-4 h-4" />
        </Button>
      }
      rightAction={
        <div className="flex items-center gap-2">
          <Button onClick={onRefresh} variant="ghost" size="sm">
            <RefreshCw className="w-4 h-4" />
          </Button>
          {renderActions()}
        </div>
      }
    />
  );
}
