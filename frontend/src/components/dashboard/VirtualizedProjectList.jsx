/**
 * VirtualizedProjectList - 虚拟滚动的项目列表组件
 * 用于优化长项目列表的渲染性能
 */
import { useMemo } from "react";
import { Link } from "react-router-dom";
import { VirtualizedList } from "./VirtualizedList";
import { Progress, HealthBadge } from "../ui";
import { Briefcase, ArrowRight } from "lucide-react";
import { cn } from "../../lib/utils";

export function VirtualizedProjectList({ projects, itemHeight = 80 }) {
  const renderItem = (project, index) => (
    <Link
      key={project.id}
      to={`/projects/${project.id}`}
      className={cn(
        "flex items-center gap-4 p-5 hover:bg-white/[0.02] transition-colors group",
        "border-b border-white/5"
      )}
    >
      {/* Icon */}
      <div
        className={cn(
          "p-3 rounded-xl",
          "bg-gradient-to-br from-primary/20 to-indigo-500/10",
          "ring-1 ring-primary/20",
          "group-hover:scale-105 transition-transform",
        )}
      >
        <Briefcase className="h-5 w-5 text-primary" />
      </div>

      {/* Info */}
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-3 mb-1">
          <h4 className="font-medium text-white truncate">
            {project.project_name}
          </h4>
          <HealthBadge health={project.health || "H1"} />
        </div>
        <div className="flex items-center gap-4 text-sm text-slate-500">
          <span>{project.project_code}</span>
          <span>•</span>
          <span>{project.customer_name}</span>
        </div>
      </div>

      {/* Progress */}
      <div className="w-32 hidden sm:block">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-slate-400">进度</span>
          <span className="text-white">
            {project.progress_pct || 0}%
          </span>
        </div>
        <Progress value={project.progress_pct || 0} size="sm" />
      </div>

      {/* Arrow */}
      <ArrowRight className="h-5 w-5 text-slate-600 group-hover:text-primary group-hover:translate-x-1 transition-all" />
    </Link>
  );

  return (
    <VirtualizedList
      items={projects}
      itemHeight={itemHeight}
      containerHeight={600}
      renderItem={renderItem}
      overscan={5}
    />
  );
}

export default VirtualizedProjectList;
