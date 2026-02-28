/**
 * 方案卡片组件
 * 用于在列表和网格视图中展示技术方案摘要
 */
import React from "react";
import { motion } from "framer-motion";
import {
  FileText,
  Calendar,
  Users,
  Building2,
  Briefcase,
  DollarSign,
  Eye,
  Edit,
  Copy,
  Archive,
  Trash2,
  MoreHorizontal,
} from "lucide-react";
import { Button } from "../ui/button";
import { Badge } from "../ui/badge";
import { Progress } from "../ui/progress";
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "../ui/dropdown-menu";
import { cn } from "../../lib/utils";
import { fadeIn } from "../../lib/animations";

// 方案状态配置
const solutionStatuses = {
  draft: { name: "草稿", color: "bg-slate-500" },
  in_progress: { name: "编写中", color: "bg-blue-500" },
  reviewing: { name: "评审中", color: "bg-amber-500" },
  published: { name: "已发布", color: "bg-emerald-500" },
  archived: { name: "已归档", color: "bg-slate-600" },
};

export function SolutionCard({
  solution,
  onView,
  onEdit,
  onCopy,
  onArchive,
  onDelete,
}) {
  const statusConfig =
    solutionStatuses[solution.status] || solutionStatuses.draft;

  return (
    <motion.div
      variants={fadeIn}
      className="p-4 rounded-xl bg-surface-100/50 backdrop-blur-lg border border-white/5 hover:bg-white/[0.03] cursor-pointer transition-all group"
      onClick={() => onView?.(solution)}
    >
      <div className="flex items-start justify-between mb-3">
        <div className="flex-1 min-w-0">
          <div className="flex items-center gap-2 mb-1.5 flex-wrap">
            <Badge className={cn("text-xs", statusConfig.color)}>
              {statusConfig.name}
            </Badge>
            <Badge variant="outline" className="text-xs">
              {solution.version}
            </Badge>
            <span className="text-xs text-slate-500">{solution.code}</span>
          </div>
          <h4 className="text-sm font-medium text-white group-hover:text-primary transition-colors line-clamp-2">
            {solution.name}
          </h4>
        </div>
        <DropdownMenu>
          <DropdownMenuTrigger asChild>
            <Button
              variant="ghost"
              size="icon"
              className="opacity-0 group-hover:opacity-100 transition-opacity"
              onClick={(e) => e.stopPropagation()}
            >
              <MoreHorizontal className="w-4 h-4 text-slate-400" />
            </Button>
          </DropdownMenuTrigger>
          <DropdownMenuContent align="end">
            <DropdownMenuItem onClick={() => onView?.(solution)}>
              <Eye className="w-4 h-4 mr-2" />
              查看详情
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onEdit?.(solution)}>
              <Edit className="w-4 h-4 mr-2" />
              编辑
            </DropdownMenuItem>
            <DropdownMenuItem onClick={() => onCopy?.(solution)}>
              <Copy className="w-4 h-4 mr-2" />
              复制
            </DropdownMenuItem>
            <DropdownMenuSeparator />
            <DropdownMenuItem onClick={() => onArchive?.(solution)}>
              <Archive className="w-4 h-4 mr-2" />
              归档
            </DropdownMenuItem>
            <DropdownMenuItem
              className="text-red-400"
              onClick={() => onDelete?.(solution)}
            >
              <Trash2 className="w-4 h-4 mr-2" />
              删除
            </DropdownMenuItem>
          </DropdownMenuContent>
        </DropdownMenu>
      </div>

      {solution.description && (
        <p className="text-xs text-slate-500 line-clamp-2 mb-3">
          {solution.description}
        </p>
      )}

      {solution.tags && solution.tags?.length > 0 && (
        <div className="flex items-center gap-2 flex-wrap mb-3">
          {solution.tags.slice(0, 3).map((tag, index) => (
            <span
              key={index}
              className="text-xs px-2 py-0.5 bg-primary/10 text-primary rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
      )}

      <div className="flex items-center gap-3 text-xs text-slate-500 mb-3">
        <span className="flex items-center gap-1">
          <Building2 className="w-3 h-3" />
          {solution.customer}
        </span>
        {solution.deviceTypeName && (
          <span className="flex items-center gap-1">
            <Briefcase className="w-3 h-3" />
            {solution.deviceTypeName}
          </span>
        )}
      </div>

      {solution.status !== "published" &&
        solution.status !== "archived" &&
        solution.progress !== undefined && (
          <div className="space-y-1 mb-3">
            <div className="flex items-center justify-between text-xs">
              <span className="text-slate-400">进度</span>
              <span className="text-white">{solution.progress}%</span>
            </div>
            <Progress value={solution.progress} className="h-1.5" />
          </div>
        )}

      <div className="flex items-center justify-between text-xs pt-3 border-t border-white/5">
        <div className="flex items-center gap-3 text-slate-500">
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {solution.updatedAt}
          </span>
          <span className="flex items-center gap-1">
            <Users className="w-3 h-3" />
            {solution.creator}
          </span>
        </div>
        {solution.amount && (
          <span className="text-emerald-400 font-medium">
            ¥{solution.amount}万
          </span>
        )}
      </div>
    </motion.div>
  );
}

export default SolutionCard;
