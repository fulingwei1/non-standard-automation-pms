/**
 * 客服工作台 - 服务工单列表
 */

import { Headphones } from "lucide-react";



import { formatDateTime } from "../../../lib/utils";
import {
  getStatusBadgeVariant,
  getTicketStatusLabel,
  getUrgencyBadgeVariant,
} from "../constants";

export function TicketTable({ tickets }) {
  if (tickets.length === 0) {
    return (
      <EmptyState
        icon={Headphones}
        title="暂无服务工单"
        message="当前范围内没有可展示的服务工单。"
      />
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>工单</TableHead>
          <TableHead>项目</TableHead>
          <TableHead>问题描述</TableHead>
          <TableHead>状态</TableHead>
          <TableHead>紧急度</TableHead>
          <TableHead>提报时间</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {tickets.map((ticket) => (
          <TableRow key={ticket.id}>
            <TableCell>
              <div className="space-y-1">
                <div className="font-medium text-white">{ticket.ticket_no}</div>
                <div className="text-xs text-slate-400">
                  负责人: {ticket.assigned_to_name || "未指派"}
                </div>
              </div>
            </TableCell>
            <TableCell>{ticket.project_name}</TableCell>
            <TableCell className="max-w-[340px] truncate">{ticket.problem_desc}</TableCell>
            <TableCell>
              <Badge variant={getStatusBadgeVariant(ticket.status)}>
                {getTicketStatusLabel(ticket.status)}
              </Badge>
            </TableCell>
            <TableCell>
              <Badge variant={getUrgencyBadgeVariant(ticket.urgency)}>{ticket.urgency}</Badge>
            </TableCell>
            <TableCell>{formatDateTime(ticket.reported_time) || "-"}</TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
