/**
 * 客服工作台 - 项目列表
 */

import { Link } from "react-router-dom";
import { Briefcase } from "lucide-react";

import {
  Badge,
  Button,
  EmptyState,
  HealthBadge,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "../../../components/ui";
import { formatPercent, getStageName } from "../../../lib/utils";

export function ProjectTable({ projects }) {
  if (projects.length === 0) {
    return (
      <EmptyState
        icon={Briefcase}
        title="暂无项目数据"
        message="当前范围内还没有关联的售后项目。"
      />
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>项目</TableHead>
          <TableHead>阶段</TableHead>
          <TableHead>健康度</TableHead>
          <TableHead>进度</TableHead>
          <TableHead>服务工单</TableHead>
          <TableHead>未解决问题</TableHead>
          <TableHead className="text-right">操作</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {projects.map((project) => (
          <TableRow key={project.id}>
            <TableCell>
              <div className="space-y-1">
                <div className="font-medium text-white">{project.project_name}</div>
                <div className="text-xs text-slate-400">
                  {project.project_code} · 客户 {project.customer_name || "-"}
                </div>
              </div>
            </TableCell>
            <TableCell>{getStageName(project.stage || "-")}</TableCell>
            <TableCell>
              {project.health ? <HealthBadge health={project.health} /> : <span>-</span>}
            </TableCell>
            <TableCell>{formatPercent(project.progress_pct || 0, 0)}</TableCell>
            <TableCell>{project.ticketCount || 0}</TableCell>
            <TableCell>
              <Badge variant={project.unresolvedIssues > 0 ? "danger" : "success"}>
                {project.unresolvedIssues || 0}
              </Badge>
            </TableCell>
            <TableCell className="text-right">
              <Button asChild size="sm" variant="outline">
                <Link to={`/projects/${project.id}/workspace`}>查看项目</Link>
              </Button>
            </TableCell>
          </TableRow>
        ))}
      </TableBody>
    </Table>
  );
}
