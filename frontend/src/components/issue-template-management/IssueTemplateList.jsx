import React from "react";
import { Eye, Edit, Copy, Trash2 } from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../ui/table";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "../ui/card";

export default function IssueTemplateList({
  loading,
  templates,
  categoryConfigs,
  issueTypeConfigs,
  priorityConfigs,
  onViewDetail,
  onEdit,
  onCreateIssue,
  onDelete,
  formatDate,
}) {
  return (
    <Card className="bg-surface-50 border-white/5">
      <CardHeader>
        <CardTitle className="text-white">问题模板列表</CardTitle>
        <CardDescription className="text-slate-400">
          共 {templates.length} 个模板
        </CardDescription>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="text-center py-8 text-slate-400">加载中...</div>
        ) : templates.length === 0 ? (
          <div className="text-center py-8 text-slate-400">暂无模板</div>
        ) : (
          <Table>
            <TableHeader>
              <TableRow className="border-white/10">
                <TableHead className="text-slate-300">模板名称</TableHead>
                <TableHead className="text-slate-300">模板编码</TableHead>
                <TableHead className="text-slate-300">分类</TableHead>
                <TableHead className="text-slate-300">问题类型</TableHead>
                <TableHead className="text-slate-300">默认优先级</TableHead>
                <TableHead className="text-slate-300">使用次数</TableHead>
                <TableHead className="text-slate-300">状态</TableHead>
                <TableHead className="text-slate-300">创建时间</TableHead>
                <TableHead className="text-right text-slate-300">
                  操作
                </TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {templates.map((template) => (
                <TableRow
                  key={template.id}
                  className="border-white/10 hover:bg-surface-100/50"
                >
                  <TableCell className="font-medium text-white">
                    {template.template_name}
                  </TableCell>
                  <TableCell className="text-slate-300">
                    {template.template_code}
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        categoryConfigs[template.category]?.color ||
                        "bg-slate-500"
                      }
                    >
                      {categoryConfigs[template.category]?.label ||
                        template.category}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        issueTypeConfigs[template.issue_type]?.color ||
                        "bg-slate-500"
                      }
                    >
                      {issueTypeConfigs[template.issue_type]?.label ||
                        template.issue_type}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Badge
                      className={
                        priorityConfigs[template.default_priority]?.color ||
                        "bg-slate-500"
                      }
                    >
                      {priorityConfigs[template.default_priority]?.label ||
                        template.default_priority}
                    </Badge>
                  </TableCell>
                  <TableCell className="text-slate-300">
                    {template.usage_count || 0}
                  </TableCell>
                  <TableCell>
                    {template.is_active ? (
                      <Badge className="bg-green-500">启用</Badge>
                    ) : (
                      <Badge className="bg-gray-500">禁用</Badge>
                    )}
                  </TableCell>
                  <TableCell className="text-slate-400 text-sm">
                    {template.created_at
                      ? formatDate(template.created_at)
                      : "-"}
                  </TableCell>
                  <TableCell className="text-right">
                    <div className="flex items-center justify-end gap-2">
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onViewDetail(template.id)}
                        className="text-slate-300 hover:text-white"
                      >
                        <Eye className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onEdit(template)}
                        className="text-slate-300 hover:text-white"
                      >
                        <Edit className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onCreateIssue(template)}
                        className="text-slate-300 hover:text-white"
                      >
                        <Copy className="w-4 h-4" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="sm"
                        onClick={() => onDelete(template)}
                        className="text-red-400 hover:text-red-300"
                      >
                        <Trash2 className="w-4 h-4" />
                      </Button>
                    </div>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        )}
      </CardContent>
    </Card>
  );
}
