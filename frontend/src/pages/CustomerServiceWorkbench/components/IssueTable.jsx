/**
 * 客服工作台 - 项目问题列表
 */

import { AlertTriangle } from "lucide-react";



import {
  getIssueStatusLabel,
  getStatusBadgeVariant,
  isIssueResolved,
} from "../constants";

export function IssueTable({ issues }) {
  if (issues.length === 0) {
    return (
      <EmptyState
        icon={AlertTriangle}
        title="暂无项目问题"
        message="当前范围内没有问题数据，或当前账号暂无问题查看权限。"
      />
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>问题</TableHead>
          <TableHead>项目</TableHead>
          <TableHead>状态</TableHead>
          <TableHead>严重度</TableHead>
          <TableHead>责任人</TableHead>
          <TableHead>解决情况</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {issues.map((issue) => (
          <TableRow key={issue.id}>
            <TableCell>
              <div className="space-y-1">
                <div className="font-medium text-white">{issue.title}</div>
                <div className="text-xs text-slate-400">{issue.issue_no}</div>
              </div>
            </TableCell>
            <TableCell>{issue.project_name}</TableCell>
            <TableCell>
              <Badge variant={getStatusBadgeVariant(issue.status)}>
                {getIssueStatusLabel(issue.status)}
              </Badge>
            </TableCell>
            <TableCell>{issue.severity}</TableCell>
            <TableCell>
              {issue.responsible_engineer_name || issue.assignee_name || "未分配"}
            </TableCell>
            <TableCell>
              {isIssueResolved(issue.status) ? (
                <span className="inline-flex items-center gap-1 text-emerald-300">
                  <CheckCircle2 className="h-4 w-4" />
                  已解决
                </span>
              ) : (
                <span className="inline-flex items-center gap-1 text-amber-300">
                  <AlertTriangle className="h-4 w-4" />
                  待处理
                </span>
              )}
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
