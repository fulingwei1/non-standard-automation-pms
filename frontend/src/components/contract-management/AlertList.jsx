/**
 * Contract Alert List Component
 * 合同预警列表组件
 */

import { useState } from "react";
import { Badge } from "../../components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter } from
"../../components/ui/dialog";
import {
  Tabs,
  TabsContent,
  TabsList,
  TabsTrigger } from
"../../components/ui/tabs";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../../components/ui/select";
import {
  AlertTriangle,
  Clock,
  CheckCircle2,
  XCircle,
  Bell,
  Calendar,
  DollarSign,
  FileText,
  User,
  Eye,
  Search,
  Filter,
  MoreHorizontal,
  RefreshCw } from
"lucide-react";
import {
  reminderTypeConfigs,
  statusConfigs as _statusConfigs,
  formatStatus as _formatStatus,
  getRiskLevelConfig as _getRiskLevelConfig } from
"@/lib/constants/contractManagement";
import { cn, formatDate, formatCurrency } from "../../lib/utils";

export function AlertList({
  alerts,
  onMarkAsRead,
  onMarkAllAsRead,
  onResolveAlert,
  onEditAlert,
  onViewContract,
  refreshAlerts,
  isRefreshing,
  className
}) {
  const [selectedAlert, setSelectedAlert] = useState(null);
  const [showDetailDialog, setShowDetailDialog] = useState(false);
  const [filterStatus, setFilterStatus] = useState('all');
  const [filterType, setFilterType] = useState('all');
  const [searchTerm, setSearchTerm] = useState('');

  // 合同风险评估
  const riskAssessmentAlerts = (alerts || []).filter((alert) =>
  alert.type === 'RISK_ASSESSMENT' || alert.severity === 'HIGH' || alert.severity === 'CRITICAL'
  );

  // 合同到期提醒
  const dueDateAlerts = (alerts || []).filter((alert) =>
  alert.type === 'DUE_DATE_REMINDER' || alert.type === 'PAYMENT_REMINDER'
  );

  // 合同状态变更
  const statusChangeAlerts = (alerts || []).filter((alert) =>
  alert.type === 'STATUS_CHANGE'
  );

  // 其他类型
  const otherAlerts = (alerts || []).filter((alert) =>
  !riskAssessmentAlerts.includes(alert) &&
  !dueDateAlerts.includes(alert) &&
  !statusChangeAlerts.includes(alert)
  );

  // 根据筛选条件过滤
  const filteredAlerts = (alerts || []).filter((alert) => {
    const matchesStatus = filterStatus === 'all' || alert.status === filterStatus;
    const matchesType = filterType === 'all' || alert.type === filterType;
    const matchesSearch = alert.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    alert.description.toLowerCase().includes(searchTerm.toLowerCase());

    return matchesStatus && matchesType && matchesSearch;
  });

  // 获取严重程度颜色
  const getSeverityColor = (severity) => {
    switch (severity) {
      case 'CRITICAL':
        return 'bg-red-500 text-white border-red-500';
      case 'HIGH':
        return 'bg-orange-500 text-white border-orange-500';
      case 'MEDIUM':
        return 'bg-yellow-500 text-white border-yellow-500';
      case 'LOW':
        return 'bg-blue-500 text-white border-blue-500';
      default:
        return 'bg-slate-500 text-white border-slate-500';
    }
  };

  // 获取状态图标
  const getStatusIcon = (status) => {
    switch (status) {
      case 'READ':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'RESOLVED':
        return <CheckCircle2 className="h-4 w-4 text-green-500" />;
      case 'PENDING':
        return <Clock className="h-4 w-4 text-yellow-500" />;
      case 'EXPIRED':
        return <XCircle className="h-4 w-4 text-red-500" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-slate-400" />;
    }
  };

  // 获取类型图标
  const getTypeIcon = (type) => {
    const _config = reminderTypeConfigs[type] || {};
    switch (type) {
      case 'DUE_DATE_REMINDER':
      case 'PAYMENT_REMINDER':
        return <DollarSign className="h-4 w-4 text-yellow-500" />;
      case 'SIGNATURE_REMINDER':
        return <FileText className="h-4 w-4 text-blue-500" />;
      case 'RENEWAL_REMINDER':
        return <RefreshCw className="h-4 w-4 text-green-500" />;
      case 'INSPECTION_REMINDER':
        return <Eye className="h-4 w-4 text-purple-500" />;
      case 'RISK_ASSESSMENT':
        return <AlertTriangle className="h-4 w-4 text-red-500" />;
      default:
        return <Bell className="h-4 w-4 text-slate-500" />;
    }
  };

  // 处理预警点击
  const handleAlertClick = (alert) => {
    setSelectedAlert(alert);
    setShowDetailDialog(true);
    if (!alert.read_at) {
      onMarkAsRead(alert.id);
    }
  };

  // 处理解决预警
  const handleResolveAlert = (alert) => {
    onResolveAlert(alert.id);
    setShowDetailDialog(false);
  };

  // 格式化到期倒计时
  const formatDaysUntilDue = (dueDate) => {
    const today = new Date();
    const due = new Date(dueDate);
    const diffTime = due - today;
    const diffDays = Math.ceil(diffTime / (1000 * 60 * 60 * 24));

    if (diffDays < 0) {
      return `已逾期 ${Math.abs(diffDays)} 天`;
    } else if (diffDays === 0) {
      return '今天到期';
    } else if (diffDays <= 7) {
      return `${diffDays} 天后到期`;
    } else if (diffDays <= 30) {
      return `${diffDays} 天后到期`;
    } else {
      return formatDate(dueDate);
    }
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium flex items-center gap-2">
            <AlertTriangle className="h-5 w-5" />
            合同预警中心
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={onMarkAllAsRead}
              disabled={(alerts || []).filter((a) => !a.read_at).length === 0}>

              <CheckCircle2 className="h-4 w-4 mr-2" />
              全部已读
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={refreshAlerts}
              disabled={isRefreshing}>

              <RefreshCw className={cn("h-4 w-4 mr-2", isRefreshing && "animate-spin")} />
              刷新
            </Button>
          </div>
        </div>

        {/* 筛选和搜索 */}
        <div className="flex flex-wrap gap-4 items-center">
          <div className="flex items-center gap-2">
            <Search className="h-4 w-4 text-muted-foreground" />
            <input
              type="text"
              placeholder="搜索预警..."
              className="px-3 py-1.5 text-sm border border-slate-200 rounded-md w-48"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)} />

          </div>

          <div className="flex items-center gap-2">
            <Filter className="h-4 w-4 text-muted-foreground" />
            <Select value={filterStatus} onValueChange={setFilterStatus}>
              <SelectTrigger className="w-32">
                <SelectValue placeholder="状态筛选" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部状态</SelectItem>
                <SelectItem value="PENDING">待处理</SelectItem>
                <SelectItem value="READ">已读</SelectItem>
                <SelectItem value="RESOLVED">已解决</SelectItem>
                <SelectItem value="EXPIRED">已过期</SelectItem>
              </SelectContent>
            </Select>

            <Select value={filterType} onValueChange={setFilterType}>
              <SelectTrigger className="w-40">
                <SelectValue placeholder="类型筛选" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">全部类型</SelectItem>
                <SelectItem value="RISK_ASSESSMENT">风险评估</SelectItem>
                <SelectItem value="DUE_DATE_REMINDER">到期提醒</SelectItem>
                <SelectItem value="PAYMENT_REMINDER">付款提醒</SelectItem>
                <SelectItem value="STATUS_CHANGE">状态变更</SelectItem>
              </SelectContent>
            </Select>
          </div>
        </div>
      </CardHeader>

      <CardContent>
        {/* 预警统计 */}
        <div className="grid grid-cols-4 gap-4 mb-6">
          <div className="text-center">
            <div className="text-2xl font-bold text-red-600">
              {riskAssessmentAlerts.length}
            </div>
            <div className="text-xs text-muted-foreground">风险预警</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-orange-600">
              {dueDateAlerts.length}
            </div>
            <div className="text-xs text-muted-foreground">到期提醒</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-blue-600">
              {statusChangeAlerts.length}
            </div>
            <div className="text-xs text-muted-foreground">状态变更</div>
          </div>
          <div className="text-center">
            <div className="text-2xl font-bold text-slate-600">
              {otherAlerts.length}
            </div>
            <div className="text-xs text-muted-foreground">其他预警</div>
          </div>
        </div>

        {/* 预警列表 */}
        <div className="space-y-3">
          {filteredAlerts.length === 0 ?
          <div className="text-center py-8 text-muted-foreground">
              <Bell className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>暂无符合条件的预警</p>
          </div> :

          (filteredAlerts || []).map((alert) => {
            const config = reminderTypeConfigs[alert.type] || {};
            const isUnread = !alert.read_at;
            const isOverdue = alert.due_date && new Date(alert.due_date) < new Date();

            return (
              <Card
                key={alert.id}
                className={cn(
                  "cursor-pointer transition-all duration-200 hover:shadow-md",
                  isUnread && "bg-blue-50 border-blue-200",
                  isOverdue && "border-orange-300"
                )}
                onClick={() => handleAlertClick(alert)}>

                  <CardContent className="p-4">
                    <div className="flex items-start justify-between">
                      <div className="flex-1 space-y-2">
                        {/* 预警类型和状态 */}
                        <div className="flex items-center gap-2">
                          <div className={cn("p-1 rounded-full", getSeverityColor(alert.severity))}>
                            {getTypeIcon(alert.type)}
                          </div>
                          <Badge variant="secondary" className={config.color}>
                            {config.label || alert.type}
                          </Badge>
                          {isUnread &&
                        <Badge variant="default" className="bg-blue-500">
                              未读
                        </Badge>
                        }
                          {isOverdue &&
                        <Badge variant="destructive">
                              已逾期
                        </Badge>
                        }
                        </div>

                        {/* 预警标题 */}
                        <h4 className={cn(
                        "font-medium",
                        isUnread && "text-blue-900"
                      )}>
                          {alert.title}
                        </h4>

                        {/* 预警描述 */}
                        <p className="text-sm text-muted-foreground line-clamp-2">
                          {alert.description}
                        </p>

                        {/* 相关信息 */}
                        <div className="flex flex-wrap gap-4 text-xs text-muted-foreground">
                          <div className="flex items-center gap-1">
                            <Calendar className="h-3 w-3" />
                            <span>创建时间: {formatDate(alert.created_at)}</span>
                          </div>
                          {alert.contract_name &&
                        <div className="flex items-center gap-1">
                              <FileText className="h-3 w-3" />
                              <span className="truncate max-w-32">
                                {alert.contract_name}
                              </span>
                        </div>
                        }
                          {alert.counterparty &&
                        <div className="flex items-center gap-1">
                              <User className="h-3 w-3" />
                              <span className="truncate max-w-32">
                                {alert.counterparty}
                              </span>
                        </div>
                        }
                          {alert.due_date &&
                        <div className={cn(
                          "flex items-center gap-1 font-medium",
                          isOverdue ? "text-red-600" : "text-green-600"
                        )}>
                              <Clock className="h-3 w-3" />
                              <span>{formatDaysUntilDue(alert.due_date)}</span>
                        </div>
                        }
                          {alert.amount &&
                        <div className="flex items-center gap-1">
                              <DollarSign className="h-3 w-3" />
                              <span>金额: {formatCurrency(alert.amount)}</span>
                        </div>
                        }
                        </div>

                        {/* 操作按钮 */}
                        <div className="flex items-center justify-between pt-2">
                          <div className="flex items-center gap-1 text-xs text-muted-foreground">
                            {getStatusIcon(alert.status)}
                            <span>{alert.status}</span>
                          </div>
                          <div className="flex items-center gap-2">
                            <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2"
                            onClick={(e) => {
                              e.stopPropagation();
                              onViewContract(alert.contract_id);
                            }}>

                              查看合同
                            </Button>
                            {alert.status !== 'RESOLVED' &&
                          <Button
                            variant="ghost"
                            size="sm"
                            className="h-6 px-2"
                            onClick={(e) => {
                              e.stopPropagation();
                              handleResolveAlert(alert);
                            }}>

                                标记已解决
                          </Button>
                          }
                          </div>
                        </div>
                      </div>
                    </div>
                  </CardContent>
              </Card>);

          })
          }
        </div>

        {/* 预警详情对话框 */}
        <Dialog open={showDetailDialog} onOpenChange={setShowDetailDialog}>
          <DialogContent className="max-w-2xl">
            {selectedAlert &&
            <>
                <DialogHeader>
                  <DialogTitle className="flex items-center gap-2">
                    <div className={cn("p-1 rounded-full", getSeverityColor(selectedAlert.severity))}>
                      {getTypeIcon(selectedAlert.type)}
                    </div>
                    {selectedAlert.title}
                  </DialogTitle>
                  <DialogDescription>
                    {selectedAlert.description}
                  </DialogDescription>
                </DialogHeader>

                <div className="space-y-4">
                  {/* 预警详情 */}
                  <div className="grid grid-cols-2 gap-4 text-sm">
                    <div>
                      <label className="text-muted-foreground">预警类型</label>
                      <p>{selectedAlert.type}</p>
                    </div>
                    <div>
                      <label className="text-muted-foreground">严重程度</label>
                      <p>{selectedAlert.severity}</p>
                    </div>
                    <div>
                      <label className="text-muted-foreground">创建时间</label>
                      <p>{formatDate(selectedAlert.created_at)}</p>
                    </div>
                    <div>
                      <label className="text-muted-foreground">状态</label>
                      <p>{selectedAlert.status}</p>
                    </div>
                    {selectedAlert.contract_name &&
                  <div>
                        <label className="text-muted-foreground">相关合同</label>
                        <p className="font-medium">{selectedAlert.contract_name}</p>
                  </div>
                  }
                    {selectedAlert.due_date &&
                  <div>
                        <label className="text-muted-foreground">到期时间</label>
                        <p className={cn(
                      "font-medium",
                      new Date(selectedAlert.due_date) < new Date() ? "text-red-600" : "text-green-600"
                    )}>
                          {formatDate(selectedAlert.due_date)}
                        </p>
                  </div>
                  }
                  </div>

                  {/* 解决方案建议 */}
                  <div>
                    <h4 className="font-medium mb-2">解决方案</h4>
                    <p className="text-sm text-muted-foreground">
                      {selectedAlert.suggestion || '请根据实际情况处理此预警'}
                    </p>
                  </div>

                  {/* 操作按钮 */}
                  <DialogFooter className="flex gap-2">
                    <Button variant="outline" onClick={() => setShowDetailDialog(false)}>
                      关闭
                    </Button>
                    {selectedAlert.status !== 'RESOLVED' &&
                  <Button onClick={() => handleResolveAlert(selectedAlert)}>
                        标记已解决
                  </Button>
                  }
                    <Button variant="outline" onClick={() => onEditAlert(selectedAlert)}>
                      编辑预警
                    </Button>
                  </DialogFooter>
                </div>
            </>
            }
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>);

}