/**
 * 客服工作台 - 现场任务（服务记录 + 安装调试派工）
 */

import { ClipboardList, Wrench } from "lucide-react";



import { formatDate, formatPercent } from "../../../lib/utils";
import {
  getOrderStatusLabel,
  getRecordStatusLabel,
  getStatusBadgeVariant,
} from "../constants";

export function FieldTaskTables({ records, orders }) {
  return (
    <div className="space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>服务记录</CardTitle>
          <CardDescription>售后上门、维修、维护等现场服务记录</CardDescription>
        </CardHeader>
        <CardContent>
          {records.length === 0 ? (
            <EmptyState
              icon={Wrench}
              title="暂无服务记录"
              message="当前范围内没有现场服务记录。"
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>记录</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>服务类型</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>服务日期</TableHead>
                  <TableHead>问题摘要</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {records.map((record) => (
                  <TableRow key={record.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-white">{record.record_no}</div>
                        <div className="text-xs text-slate-400">
                          工程师: {record.service_engineer_name || "未指定"}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{record.project_name}</TableCell>
                    <TableCell>{record.service_type}</TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(record.status)}>
                        {getRecordStatusLabel(record.status)}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(record.service_date) || "-"}</TableCell>
                    <TableCell className="max-w-[340px] truncate">
                      {record.issues_found || record.service_content}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardTitle>安装调试派工</CardTitle>
          <CardDescription>安装、调试和现场支持任务跟进</CardDescription>
        </CardHeader>
        <CardContent>
          {orders.length === 0 ? (
            <EmptyState
              icon={ClipboardList}
              title="暂无派工任务"
              message="当前范围内没有安装调试派工任务。"
            />
          ) : (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>派工单</TableHead>
                  <TableHead>项目</TableHead>
                  <TableHead>任务</TableHead>
                  <TableHead>状态</TableHead>
                  <TableHead>计划日期</TableHead>
                  <TableHead>进度</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {orders.map((order) => (
                  <TableRow key={order.id}>
                    <TableCell>
                      <div className="space-y-1">
                        <div className="font-medium text-white">{order.order_no}</div>
                        <div className="text-xs text-slate-400">
                          工程师: {order.assigned_to_name || "未派工"}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell>{order.project_name}</TableCell>
                    <TableCell>
                      <div className="space-y-1">
                        <div>{order.task_title}</div>
                        <div className="text-xs text-slate-400">{order.task_type}</div>
                      </div>
                    </TableCell>
                    <TableCell>
                      <Badge variant={getStatusBadgeVariant(order.status)}>
                        {getOrderStatusLabel(order.status)}
                      </Badge>
                    </TableCell>
                    <TableCell>{formatDate(order.scheduled_date) || "-"}</TableCell>
                    <TableCell>{formatPercent(order.progress || 0, 0)}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
