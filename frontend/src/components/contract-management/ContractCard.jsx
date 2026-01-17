/**
 * Contract Card Component
 * 合同卡片显示组件
 */

import { useState } from "react";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
  DropdownMenuSeparator } from
"../../components/ui/dropdown-menu";
import {
  MoreHorizontal,
  Eye,
  Edit,
  Trash2,
  FileText,
  Calendar,
  DollarSign,
  User,
  AlertTriangle,
  CheckCircle2,
  Clock } from
"lucide-react";
import {
  getStatusConfig,
  getTypeConfig,
  getAmountRangeConfig,
  riskLevelConfigs,
  fulfillmentStatusConfigs,
  formatStatus as _formatStatus,
  formatType } from
"./contractManagementConstants";
import { cn, formatDate, formatCurrency } from "../../lib/utils";

export function ContractCard({
  contract,
  onView,
  onEdit,
  onDelete,
  onTransition,
  transitionLoading,
  currentUser: _currentUser,
  className
}) {
  const [showTransitionMenu, setShowTransitionMenu] = useState(false);
  const [_transitionAction, setTransitionAction] = useState(null);

  const statusConfig = getStatusConfig(contract.status);
  const typeConfig = getTypeConfig(contract.type);
  const _amountRangeConfig = getAmountRangeConfig(contract.contract_amount);
  const riskConfig = contract.risk_level ?
  riskLevelConfigs[contract.risk_level] : riskLevelConfigs.MEDIUM;
  const fulfillmentConfig = contract.fulfillment_status ?
  fulfillmentStatusConfigs[contract.fulfillment_status] :
  fulfillmentStatusConfigs.NOT_STARTED;

  const getProgressColor = (status) => {
    switch (status) {
      case 'DRAFT':
        return 'bg-slate-500';
      case 'PENDING_SIGNATURE':
        return 'bg-blue-500';
      case 'UNDER_REVIEW':
        return 'bg-amber-500';
      case 'AWAITING_APPROVAL':
        return 'bg-purple-500';
      case 'APPROVED':
        return 'bg-emerald-500';
      case 'SIGNED':
        return 'bg-green-500';
      case 'ACTIVE':
        return 'bg-violet-500';
      case 'COMPLETED':
        return 'bg-slate-600';
      case 'TERMINATED':
      case 'CANCELLED':
      case 'REJECTED':
        return 'bg-gray-500';
      default:
        return 'bg-slate-500';
    }
  };

  const getProgressPercentage = (status) => {
    switch (status) {
      case 'DRAFT':
        return 10;
      case 'PENDING_SIGNATURE':
        return 20;
      case 'UNDER_REVIEW':
        return 30;
      case 'AWAITING_APPROVAL':
        return 40;
      case 'APPROVED':
        return 50;
      case 'SIGNED':
        return 70;
      case 'ACTIVE':
        return 85;
      case 'COMPLETED':
        return 100;
      case 'TERMINATED':
      case 'CANCELLED':
      case 'REJECTED':
        return 0;
      default:
        return 10;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'ACTIVE':
        return 'text-green-600';
      case 'COMPLETED':
        return 'text-slate-600';
      case 'TERMINATED':
      case 'CANCELLED':
        return 'text-red-600';
      case 'REJECTED':
        return 'text-red-600';
      default:
        return 'text-slate-600';
    }
  };

  const isOverdue = contract.due_date && new Date(contract.due_date) < new Date();
  const isDueSoon = contract.due_date && {
    days: Math.ceil((new Date(contract.due_date) - new Date()) / (1000 * 60 * 60 * 24)),
    isSoon: Math.ceil((new Date(contract.due_date) - new Date()) / (1000 * 60 * 60 * 24)) <= 30
  };

  const handleTransition = (newStatus) => {
    setTransitionAction(newStatus);
    onTransition(contract.id, newStatus);
    setShowTransitionMenu(false);
  };

  const transitionMenuItem = (status, label, icon) =>
  <DropdownMenuItem
    onClick={() => handleTransition(status)}
    disabled={transitionLoading}
    className="flex items-center gap-2">

      {icon}
      {label}
  </DropdownMenuItem>;


  return (
    <Card className={cn("h-full hover:shadow-md transition-shadow duration-200", className)}>
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="space-y-1">
            <CardTitle className="text-lg font-medium line-clamp-2">
              {contract.contract_no || `合同-${contract.id}`}
            </CardTitle>
            <div className="flex items-center gap-2">
              <Badge variant="secondary" className={cn("text-xs", typeConfig.color)}>
                {typeConfig.icon} {formatType(contract.type)}
              </Badge>
              <Badge
                variant="secondary"
                className={cn("text-xs", fulfillmentConfig.color)}>

                {fulfillmentConfig.label}
              </Badge>
            </div>
          </div>

          <DropdownMenu open={showTransitionMenu} onOpenChange={setShowTransitionMenu}>
            <DropdownMenuTrigger asChild>
              <Button variant="ghost" size="sm" className="h-8 w-8 p-0">
                <MoreHorizontal className="h-4 w-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={() => onView(contract)}>
                <Eye className="mr-2 h-4 w-4" />
                查看详情
              </DropdownMenuItem>
              <DropdownMenuItem onClick={() => onEdit(contract)}>
                <Edit className="mr-2 h-4 w-4" />
                编辑合同
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              {contract.status === 'DRAFT' && transitionMenuItem('PENDING_SIGNATURE', '提交签署', <FileText className="h-4 w-4" />)}
              {contract.status === 'PENDING_SIGNATURE' && transitionMenuItem('UNDER_REVIEW', '提交审核', <FileText className="h-4 w-4" />)}
              {contract.status === 'UNDER_REVIEW' && transitionMenuItem('AWAITING_APPROVAL', '提交审批', <FileText className="h-4 w-4" />)}
              {contract.status === 'AWAITING_APPROVAL' && transitionMenuItem('APPROVED', '批准', <CheckCircle2 className="h-4 w-4" />)}
              {contract.status === 'AWAITING_APPROVAL' && transitionMenuItem('REJECTED', '驳回', <AlertTriangle className="h-4 w-4" />)}
              {contract.status === 'APPROVED' && transitionMenuItem('SIGNED', '签署完成', <CheckCircle2 className="h-4 w-4" />)}
              {contract.status === 'SIGNED' && transitionMenuItem('ACTIVE', '激活合同', <CheckCircle2 className="h-4 w-4" />)}
              {contract.status === 'ACTIVE' && transitionMenuItem('COMPLETED', '完成合同', <CheckCircle2 className="h-4 w-4" />)}
              {(contract.status === 'ACTIVE' || contract.status === 'SIGNED') && transitionMenuItem('TERMINATED', '终止合同', <AlertTriangle className="h-4 w-4" />)}
              {contract.status === 'ACTIVE' && transitionMenuItem('AMENDED', '修订合同', <Edit className="h-4 w-4" />)}
              {(contract.status === 'DRAFT' || contract.status === 'PENDING_SIGNATURE' || contract.status === 'UNDER_REVIEW') && transitionMenuItem('CANCELLED', '取消合同', <Trash2 className="h-4 w-4" />)}
              <DropdownMenuItem
                onClick={() => onDelete(contract)}
                className="text-red-600 focus:text-red-600">

                <Trash2 className="mr-2 h-4 w-4" />
                删除合同
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* 合同基本信息 */}
        <div className="space-y-2">
          <div className="flex justify-between items-start">
            <span className="text-sm text-muted-foreground">合同名称</span>
            <span className="text-sm font-medium line-clamp-2">
              {contract.contract_name}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <DollarSign className="h-4 w-4" />
              <span>金额</span>
            </div>
            <span className="text-sm font-medium text-green-600">
              {formatCurrency(contract.contract_amount)}
            </span>
          </div>

          <div className="flex justify-between items-center">
            <div className="flex items-center gap-1 text-sm text-muted-foreground">
              <User className="h-4 w-4" />
              <span>签约方</span>
            </div>
            <span className="text-sm font-medium line-clamp-1">
              {contract.counterparty}
            </span>
          </div>
        </div>

        {/* 进度条 */}
        <div className="space-y-2">
          <div className="flex justify-between text-xs text-muted-foreground">
            <span>合同进度</span>
            <span>{getProgressPercentage(contract.status)}%</span>
          </div>
          <div className="w-full bg-slate-200 rounded-full h-2">
            <div
              className={cn(
                "h-2 rounded-full transition-all duration-300",
                getProgressColor(contract.status)
              )}
              style={{ width: `${getProgressPercentage(contract.status)}%` }} />

          </div>
        </div>

        {/* 状态和风险 */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">状态</span>
              <Badge
                variant="secondary"
                className={cn("text-xs", statusConfig.color)}>

                {statusConfig.label}
              </Badge>
            </div>
            <span className={cn("text-xs", getStatusColor(contract.status))}>
              {getStatusColor(contract.status).includes('text-green') && <CheckCircle2 className="inline w-3 h-3 mr-1" />}
              {getStatusColor(contract.status).includes('text-red') && <AlertTriangle className="inline w-3 h-3 mr-1" />}
              {getStatusColor(contract.status).includes('text-slate') && <Clock className="inline w-3 h-3 mr-1" />}
              {statusConfig.label}
            </span>
          </div>

          <div className="space-y-1">
            <div className="flex items-center justify-between">
              <span className="text-xs text-muted-foreground">风险等级</span>
              <Badge
                variant="secondary"
                className={cn("text-xs", riskConfig.color)}>

                {riskConfig.label}
              </Badge>
            </div>
            <span className="text-xs text-muted-foreground">
              风险评分: {riskConfig.score}
            </span>
          </div>
        </div>

        {/* 日期信息 */}
        <div className="grid grid-cols-2 gap-3">
          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              <span>签署日期</span>
            </div>
            <span className="text-xs">
              {contract.sign_date ? formatDate(contract.sign_date) : '-'}
            </span>
          </div>

          <div className="space-y-1">
            <div className="flex items-center gap-1 text-xs text-muted-foreground">
              <Calendar className="h-3 w-3" />
              <span>到期日期</span>
            </div>
            <div className={cn(
              "text-xs font-medium",
              isOverdue && "text-red-600",
              !isOverdue && isDueSoon?.isSoon && "text-orange-600",
              !isOverdue && !isDueSoon?.isSoon && "text-green-600"
            )}>
              {contract.due_date ? formatDate(contract.due_date) : '-'}
              {isOverdue && <span className="ml-1 text-red-500">(已逾期)</span>}
              {isDueSoon?.isSoon && !isOverdue &&
              <span className="ml-1 text-orange-500">({isDueSoon.days}天后到期)</span>
              }
            </div>
          </div>
        </div>

        {/* 附件数量 */}
        {contract.document_count > 0 &&
        <div className="flex items-center justify-between pt-2 border-t">
            <span className="text-xs text-muted-foreground">
              <FileText className="inline h-3 w-3 mr-1" />
              附件 ({contract.document_count})
            </span>
            <Button
            variant="ghost"
            size="sm"
            className="h-6 px-2 text-xs"
            onClick={() => onView(contract)}>

              查看详情
            </Button>
        </div>
        }
      </CardContent>
    </Card>);

}