/**
 * Service Ticket List Table Component
 * 服务工单列表表格组件
 */
import { useState } from "react";
import { Eye, Edit, Clock, CheckCircle2, AlertTriangle, User, Calendar } from "lucide-react";
import { Checkbox } from "../ui/checkbox";
import { Badge } from "../ui/badge";
import { Button } from "../ui/button";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow } from
"../ui/table";
import { Card, CardContent } from "../ui/card";
import { formatDate } from "../../lib/utils";
import {
  statusConfigs,
  urgencyConfigs,
  getStatusLabel,
  getUrgencyLabel,
  getProblemTypeIcon } from
"@/lib/constants/service";

export function ServiceTicketListTable({
  tickets = [],
  loading = false,
  selectedTicketIds = new Set(),
  onSelectionChange,
  onViewDetail,
  onEditTicket
}) {
  const [sortConfig, setSortConfig] = useState({
    key: "reported_time",
    direction: "desc"
  });

  // 排序函数
  const handleSort = (key) => {
    setSortConfig((prev) => ({
      key,
      direction: prev.key === key && prev.direction === "desc" ? "asc" : "desc"
    }));
  };

  // 排序数据
  const sortedTickets = [...tickets].sort((a, b) => {
    let aValue = a[sortConfig.key];
    let bValue = b[sortConfig.key];

    // 处理日期排序
    if (sortConfig.key.includes("_time") || sortConfig.key.includes("Date")) {
      aValue = new Date(aValue);
      bValue = new Date(bValue);
    }

    if (aValue < bValue) {return sortConfig.direction === "asc" ? -1 : 1;}
    if (aValue > bValue) {return sortConfig.direction === "asc" ? 1 : -1;}
    return 0;
  });

  // 处理单行选择
  const handleRowSelect = (ticketId, checked) => {
    const newSelection = new Set(selectedTicketIds);
    if (checked) {
      newSelection.add(ticketId);
    } else {
      newSelection.delete(ticketId);
    }
    onSelectionChange(newSelection);
  };

  // 处理全选
  const handleSelectAll = (checked) => {
    if (checked) {
      onSelectionChange(new Set(sortedTickets.map((ticket) => ticket.id)));
    } else {
      onSelectionChange(new Set());
    }
  };

  // 获取状态图标
  const getStatusIcon = (status) => {
    switch (status) {
      case "PENDING":
        return <Clock className="w-3 h-3 text-slate-500" />;
      case "ASSIGNED":
      case "IN_PROGRESS":
        return <Clock className="w-3 h-3 text-blue-500" />;
      case "PENDING_VERIFY":
        return <CheckCircle2 className="w-3 h-3 text-amber-500" />;
      case "CLOSED":
        return <CheckCircle2 className="w-3 h-3 text-emerald-500" />;
      default:
        return <Clock className="w-3 h-3 text-slate-400" />;
    }
  };

  // 获取紧急程度图标
  const getUrgencyIcon = (urgency) => {
    switch (urgency) {
      case "URGENT":
        return <AlertTriangle className="w-3 h-3 text-red-500" />;
      case "HIGH":
        return <AlertTriangle className="w-3 h-3 text-orange-500" />;
      default:
        return <Clock className="w-3 h-3 text-slate-400" />;
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center py-12">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-500" />
        <span className="ml-2 text-slate-600 dark:text-slate-400">加载中...</span>
      </div>);

  }

  if (sortedTickets.length === 0) {
    return (
      <div className="text-center py-12">
        <div className="text-slate-400 mb-2">
          <AlertTriangle className="w-12 h-12 mx-auto opacity-50" />
        </div>
        <p className="text-slate-500 dark:text-slate-400">暂无服务工单</p>
        <p className="text-sm text-slate-400 dark:text-slate-500 mt-1">
          请调整筛选条件或创建新的服务工单
        </p>
      </div>);

  }

  return (
    <Card>
      <CardContent className="p-0">
        <div className="rounded-lg border bg-white dark:bg-slate-950">
          <Table>
            <TableHeader>
              <TableRow className="bg-slate-50 dark:bg-slate-900/50">
                <TableHead className="w-12">
                  <Checkbox
                    checked={sortedTickets.length > 0 && selectedTicketIds.size === sortedTickets.length}
                    onCheckedChange={handleSelectAll} />

                </TableHead>
                
                {/* 可排序列头 */}
                <TableHead className="cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => handleSort("ticket_no")}>
                  <div className="flex items-center gap-1">
                    工单编号
                    {sortConfig.key === "ticket_no" &&
                    <span className="text-xs text-slate-400">
                        {sortConfig.direction === "asc" ? "↑" : "↓"}
                    </span>
                    }
                  </div>
                </TableHead>

                <TableHead>标题</TableHead>
                <TableHead>客户</TableHead>
                <TableHead>问题类型</TableHead>
                <TableHead>状态</TableHead>
                <TableHead>紧急程度</TableHead>
                <TableHead>工程师</TableHead>

                <TableHead className="cursor-pointer hover:bg-slate-100 dark:hover:bg-slate-800" onClick={() => handleSort("reported_time")}>
                  <div className="flex items-center gap-1">
                    报告时间
                    {sortConfig.key === "reported_time" &&
                    <span className="text-xs text-slate-400">
                        {sortConfig.direction === "asc" ? "↑" : "↓"}
                    </span>
                    }
                  </div>
                </TableHead>

                <TableHead className="text-right">操作</TableHead>
              </TableRow>
            </TableHeader>

            <TableBody>
              {sortedTickets.map((ticket) =>
              <TableRow
                key={ticket.id}
                className={`hover:bg-slate-50 dark:hover:bg-slate-800/50 ${
                selectedTicketIds.has(ticket.id) ? "bg-blue-50 dark:bg-blue-900/20" : ""}`
                }>

                  <TableCell>
                    <Checkbox
                    checked={selectedTicketIds.has(ticket.id)}
                    onCheckedChange={(checked) => handleRowSelect(ticket.id, checked)} />

                  </TableCell>

                  <TableCell className="font-mono text-sm">
                    #{ticket.ticket_no || `ST${String(ticket.id).padStart(6, '0')}`}
                  </TableCell>

                  <TableCell className="max-w-xs">
                    <div className="truncate font-medium" title={ticket.title}>
                      {ticket.title}
                    </div>
                  </TableCell>

                  <TableCell>
                    <div className="text-sm">
                      <div className="font-medium">{ticket.customer_name || "未知客户"}</div>
                      {ticket.contact_phone &&
                    <div className="text-xs text-slate-500">{ticket.contact_phone}</div>
                    }
                    </div>
                  </TableCell>

                  <TableCell>
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{getProblemTypeIcon(ticket.problem_type)}</span>
                      <span className="text-sm">{ticket.problem_type}</span>
                    </div>
                  </TableCell>

                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getStatusIcon(ticket.status)}
                      <Badge
                      variant="outline"
                      className={`${statusConfigs[ticket.status]?.borderColor} border-2 text-xs`}>

                        {getStatusLabel(ticket.status)}
                      </Badge>
                    </div>
                  </TableCell>

                  <TableCell>
                    <div className="flex items-center gap-2">
                      {getUrgencyIcon(ticket.urgency)}
                      <Badge
                      variant="secondary"
                      className={`${urgencyConfigs[ticket.urgency]?.bg} text-xs`}>

                        {getUrgencyLabel(ticket.urgency)}
                      </Badge>
                    </div>
                  </TableCell>

                  <TableCell>
                    <div className="text-sm">
                      {ticket.assigned_engineer ?
                    <div className="flex items-center gap-1">
                          <User className="w-3 h-3 text-slate-400" />
                          {ticket.assigned_engineer}
                    </div> :

                    <span className="text-slate-400">未分配</span>
                    }
                    </div>
                  </TableCell>

                  <TableCell className="text-sm text-slate-600 dark:text-slate-400">
                    <div className="flex items-center gap-1">
                      <Calendar className="w-3 h-3" />
                      {formatDate(ticket.reported_time)}
                    </div>
                  </TableCell>

                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-1">
                      <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onViewDetail(ticket)}
                      className="h-8 w-8 p-0">

                        <Eye className="w-4 h-4" />
                      </Button>
                      {ticket.status === "PENDING" &&
                    <Button
                      variant="ghost"
                      size="sm"
                      onClick={() => onEditTicket(ticket)}
                      className="h-8 w-8 p-0">

                          <Edit className="w-4 h-4" />
                    </Button>
                    }
                    </div>
                  </TableCell>
              </TableRow>
              )}
            </TableBody>
          </Table>
        </div>
      </CardContent>
    </Card>);

}