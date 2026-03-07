/**
 * Contract Timeline Component
 * 合同时间线组件
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
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger } from
"../../components/ui/tooltip";
import {
  Calendar,
  CheckCircle2,
  XCircle,
  AlertTriangle,
  Clock,
  FileText,
  User,
  MessageSquare,
  Plus,
  Eye,
  Edit } from
"lucide-react";
import {
  statusChangeTypeConfigs,
  getStatusConfig,
  formatStatus } from
"@/lib/constants/contractManagement";
import { cn, formatDate } from "../../lib/utils";

export function ContractTimeline({
  contract,
  onAddEvent,
  onEditEvent,
  onAddReminder,
  currentUser,
  className
}) {
  const [showAddEventDialog, setShowAddEventDialog] = useState(false);
  const [showAddReminderDialog, setShowAddReminderDialog] = useState(false);
  const [_selectedEvent, setSelectedEvent] = useState(null);
  const [newEvent, setNewEvent] = useState({
    title: '',
    description: '',
    event_date: new Date().toISOString().split('T')[0],
    type: 'CUSTOM',
    status: 'PENDING'
  });

  // 示例时间线事件数据
  const timelineEvents = [
  {
    id: 1,
    type: 'CREATED',
    title: '合同创建',
    description: '创建合同草稿',
    event_date: '2024-01-15',
    user: '张三',
    status: 'COMPLETED',
    document_id: null
  },
  {
    id: 2,
    type: 'REVIEWED',
    title: '法务审核',
    description: '法务部门完成审核',
    event_date: '2024-01-18',
    user: '李四',
    status: 'COMPLETED',
    document_id: 101
  },
  {
    id: 3,
    type: 'APPROVED',
    title: '管理层批准',
    description: '总经理批准合同',
    event_date: '2024-01-20',
    user: '王五',
    status: 'COMPLETED',
    document_id: 102
  },
  {
    id: 4,
    type: 'SIGNED',
    title: '合同签署',
    description: '双方正式签署合同',
    event_date: '2024-01-25',
    user: '张三',
    status: 'COMPLETED',
    document_id: 103
  },
  {
    id: 5,
    type: 'ACTIVATED',
    title: '合同生效',
    description: '合同正式生效开始执行',
    event_date: '2024-01-26',
    user: '李四',
    status: 'COMPLETED',
    document_id: null
  },
  {
    id: 6,
    type: 'REMINDER',
    title: '付款提醒',
    description: '提醒对方支付第一期款项',
    event_date: '2024-02-15',
    user: '王五',
    status: 'PENDING',
    due_date: '2024-02-20',
    document_id: null
  },
  {
    id: 7,
    type: 'COMPLETION_REMINDER',
    title: '验收提醒',
    description: '项目即将到期，准备验收',
    event_date: '2024-03-10',
    user: '张三',
    status: 'IN_PROGRESS',
    due_date: '2024-03-15',
    document_id: 104
  }];


  const getEventConfig = (type) => {
    return statusChangeTypeConfigs[type] || {
      label: '自定义事件',
      color: 'bg-slate-500',
      textColor: 'text-slate-50',
      icon: '📋'
    };
  };

  const getEventIcon = (type, status) => {
    const _eventConfig = getEventConfig(type);
    const iconClass = "w-5 h-5";

    if (status === 'COMPLETED') {
      return <CheckCircle2 className={cn(iconClass, "text-green-500")} />;
    } else if (status === 'FAILED' || status === 'REJECTED') {
      return <XCircle className={cn(iconClass, "text-red-500")} />;
    } else if (status === 'PENDING') {
      return <Clock className={cn(iconClass, "text-yellow-500")} />;
    } else if (status === 'IN_PROGRESS') {
      return <Clock className={cn(iconClass, "text-blue-500 animate-pulse")} />;
    } else {
      return <AlertTriangle className={cn(iconClass, "text-slate-400")} />;
    }
  };

  const getStatusColor = (status) => {
    switch (status) {
      case 'COMPLETED':
        return 'text-green-600 bg-green-50 border-green-200';
      case 'FAILED':
      case 'REJECTED':
        return 'text-red-600 bg-red-50 border-red-200';
      case 'PENDING':
        return 'text-yellow-600 bg-yellow-50 border-yellow-200';
      case 'IN_PROGRESS':
        return 'text-blue-600 bg-blue-50 border-blue-200';
      default:
        return 'text-slate-600 bg-slate-50 border-slate-200';
    }
  };

  const groupedEvents = (timelineEvents || []).reduce((acc, event) => {
    const month = new Date(event.event_date).toLocaleDateString('zh-CN', { year: 'numeric', month: 'long' });
    if (!acc[month]) {
      acc[month] = [];
    }
    acc[month].push(event);
    return acc;
  }, {});

  const months = Object.keys(groupedEvents).sort((a, b) => {
    const dateA = new Date(a);
    const dateB = new Date(b);
    return dateB - dateA;
  });

  const handleAddEvent = () => {
    onAddEvent({
      ...newEvent,
      contract_id: contract.id,
      user: currentUser.name
    });
    setNewEvent({
      title: '',
      description: '',
      event_date: new Date().toISOString().split('T')[0],
      type: 'CUSTOM',
      status: 'PENDING'
    });
    setShowAddEventDialog(false);
  };

  const handleEditEvent = (event) => {
    setSelectedEvent(event);
    onEditEvent(event);
  };

  return (
    <Card className={cn("w-full", className)}>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-lg font-medium flex items-center gap-2">
            <Calendar className="h-5 w-5" />
            合同时间线
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAddReminderDialog(true)}>

              <Plus className="h-4 w-4 mr-2" />
              添加提醒
            </Button>
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowAddEventDialog(true)}>

              <Plus className="h-4 w-4 mr-2" />
              添加事件
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-6">
        {/* 当前状态展示 */}
        <div className="flex items-center justify-between p-4 bg-slate-50 rounded-lg">
          <div>
            <h3 className="font-medium">当前状态</h3>
            <p className="text-sm text-muted-foreground">
              {formatStatus(contract.status)} - {contract.status_desc || ''}
            </p>
          </div>
          <Badge className={getStatusConfig(contract.status).color}>
            {getStatusConfig(contract.status).label}
          </Badge>
        </div>

        {/* 时间线主体 */}
        <div className="relative">
          {/* 垂直时间线 */}
          <div className="absolute left-4 top-0 bottom-0 w-0.5 bg-slate-200" />

          {(months || []).map((month, _monthIndex) =>
          <div key={month} className="relative">
              <div className="sticky top-0 z-10 bg-white p-2 border-b">
                <h3 className="text-sm font-medium text-slate-600">{month}</h3>
              </div>

              <div className="ml-8 space-y-4 pb-4">
                {groupedEvents[month].map((event, eventIndex) => {
                const isLast = eventIndex === groupedEvents[month].length - 1;
                const eventConfig = getEventConfig(event.type);

                return (
                  <div key={event.id} className="relative">
                      {/* 时间线节点 */}
                      <div className={cn(
                      "absolute left-[-16px] w-8 h-8 rounded-full flex items-center justify-center border-2 border-white",
                      eventConfig.color
                    )}>
                        {getEventIcon(event.type, event.status)}
                      </div>

                      {/* 事件卡片 */}
                      <Card className={cn(
                      "hover:shadow-md transition-shadow duration-200",
                      getStatusColor(event.status)
                    )}>
                        <CardContent className="p-4">
                          <div className="flex items-start justify-between">
                            <div className="flex-1 space-y-2">
                              <div className="flex items-center gap-2">
                                <Badge
                                variant="secondary"
                                className={cn("text-xs", eventConfig.color)}>

                                  {eventConfig.icon} {eventConfig.label}
                                </Badge>
                                <span className="text-xs text-muted-foreground">
                                  {formatDate(event.event_date)}
                                </span>
                                {event.due_date &&
                              <span className="text-xs text-orange-600">
                                    截止: {formatDate(event.due_date)}
                              </span>
                              }
                              </div>

                              <h4 className="font-medium">{event.title}</h4>
                              <p className="text-sm">{event.description}</p>

                              <div className="flex items-center gap-4 text-xs text-muted-foreground">
                                <div className="flex items-center gap-1">
                                  <User className="h-3 w-3" />
                                  <span>{event.user}</span>
                                </div>
                                {event.document_id &&
                              <div className="flex items-center gap-1">
                                    <FileText className="h-3 w-3" />
                                    <span>文档 #{event.document_id}</span>
                              </div>
                              }
                              </div>

                              {/* 操作按钮 */}
                              <div className="flex items-center gap-2 pt-2">
                                <TooltipProvider>
                                  <Tooltip>
                                    <TooltipTrigger asChild>
                                      <Button
                                      variant="ghost"
                                      size="sm"
                                      className="h-6 px-2"
                                      onClick={() => handleEditEvent(event)}>

                                        <Eye className="h-3 w-3" />
                                      </Button>
                                    </TooltipTrigger>
                                    <TooltipContent>
                                      <p>查看详情</p>
                                    </TooltipContent>
                                  </Tooltip>
                                </TooltipProvider>

                                {event.type !== 'CREATED' && event.type !== 'SIGNED' &&
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 px-2">

                                    <Edit className="h-3 w-3" />
                              </Button>
                              }

                                {event.type === 'REMINDER' &&
                              <Button
                                variant="ghost"
                                size="sm"
                                className="h-6 px-2 text-blue-600">

                                    <MessageSquare className="h-3 w-3" />
                              </Button>
                              }
                              </div>
                            </div>
                          </div>
                        </CardContent>
                      </Card>

                      {!isLast &&
                    <div className="absolute left-[-16px] top-full w-0.5 h-4 bg-slate-200" />
                    }
                  </div>);

              })}
              </div>
          </div>
          )}

          {/* 如果没有事件 */}
          {months.length === 0 &&
          <div className="text-center py-8 text-muted-foreground">
              <Calendar className="h-12 w-12 mx-auto mb-2 opacity-50" />
              <p>暂无时间线事件</p>
              <p className="text-sm">点击"添加事件"开始记录</p>
          </div>
          }
        </div>

        {/* 添加事件对话框 */}
        <Dialog open={showAddEventDialog} onOpenChange={setShowAddEventDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>添加时间线事件</DialogTitle>
              <DialogDescription>
                为合同添加一个新的事件记录
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">事件标题</label>
                <input
                  type="text"
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-md text-sm"
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                  placeholder="输入事件标题" />

              </div>
              <div>
                <label className="text-sm font-medium">事件描述</label>
                <textarea
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-md text-sm"
                  value={newEvent.description}
                  onChange={(e) => setNewEvent({ ...newEvent, description: e.target.value })}
                  placeholder="输入事件描述"
                  rows={3} />

              </div>
              <div>
                <label className="text-sm font-medium">事件日期</label>
                <input
                  type="date"
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-md text-sm"
                  value={newEvent.event_date}
                  onChange={(e) => setNewEvent({ ...newEvent, event_date: e.target.value })} />

              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddEventDialog(false)}>
                取消
              </Button>
              <Button onClick={handleAddEvent}>
                添加事件
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>

        {/* 添加提醒对话框 */}
        <Dialog open={showAddReminderDialog} onOpenChange={setShowAddReminderDialog}>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>添加提醒</DialogTitle>
              <DialogDescription>
                为合同设置一个提醒事项
              </DialogDescription>
            </DialogHeader>
            <div className="space-y-4">
              <div>
                <label className="text-sm font-medium">提醒类型</label>
                <select
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-md text-sm"
                  value={newEvent.type}
                  onChange={(e) => setNewEvent({ ...newEvent, type: e.target.value })}>

                  <option value="PAYMENT_REMINDER">付款提醒</option>
                  <option value="RENEWAL_REMINDER">续签提醒</option>
                  <option value="INSPECTION_REMINDER">验收提醒</option>
                  <option value="COMPLETION_REMINDER">完成提醒</option>
                  <option value="OTHER_REMINDER">其他提醒</option>
                </select>
              </div>
              <div>
                <label className="text-sm font-medium">提醒标题</label>
                <input
                  type="text"
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-md text-sm"
                  value={newEvent.title}
                  onChange={(e) => setNewEvent({ ...newEvent, title: e.target.value })}
                  placeholder="输入提醒标题" />

              </div>
              <div>
                <label className="text-sm font-medium">提醒日期</label>
                <input
                  type="date"
                  className="w-full mt-1 px-3 py-2 border border-slate-200 rounded-md text-sm"
                  value={newEvent.event_date}
                  onChange={(e) => setNewEvent({ ...newEvent, event_date: e.target.value })} />

              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setShowAddReminderDialog(false)}>
                取消
              </Button>
              <Button onClick={() => {
                onAddReminder({
                  ...newEvent,
                  contract_id: contract.id,
                  user: currentUser.name
                });
                setShowAddReminderDialog(false);
              }}>
                添加提醒
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>);

}