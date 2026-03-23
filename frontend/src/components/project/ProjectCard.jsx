/**
 * ProjectCard - 项目卡片组件
 * 从 ProjectList 提取，用于多处复用
 */
import { cn } from "../../lib/utils";
import { formatDate } from "../../lib/utils";





const staggerChild = {
  hidden: { opacity: 0, y: 20 },
  visible: { opacity: 1, y: 0 },
};

export default function ProjectCard({ project, onClick }) {
  return (
    <motion.div variants={staggerChild}>
      <Card className="group cursor-pointer overflow-hidden" onClick={onClick}>
        {/* 顶部健康度色条 */}
        <div
          className={cn("h-1", {
            "bg-emerald-500": project.health === "H1",
            "bg-amber-500": project.health === "H2",
            "bg-red-500": project.health === "H3",
            "bg-slate-500": project.health === "H4",
          })}
        />

        <CardContent className="p-5">
          {/* 头部 */}
          <div className="flex items-start justify-between mb-4">
            <div className="flex items-center gap-3">
              <div
                className={cn(
                  "p-2.5 rounded-xl",
                  "bg-gradient-to-br from-primary/20 to-indigo-500/10",
                  "ring-1 ring-primary/20",
                  "group-hover:scale-105 transition-transform",
                )}
              >
                <Briefcase className="h-5 w-5 text-primary" />
              </div>
              <div>
                <h3 className="font-semibold text-white line-clamp-1 group-hover:text-primary transition-colors">
                  {project.project_name || project.name}
                </h3>
                <p className="text-xs text-slate-500">{project.project_code}</p>
              </div>
            </div>
            <HealthBadge health={project.health || "H1"} />
          </div>

          {/* 元信息 */}
          <div className="grid grid-cols-2 gap-3 mb-4 text-sm">
            <div className="flex items-center gap-2 text-slate-400">
              <Users className="h-4 w-4" />
              <span className="truncate">{project.customer_name || "-"}</span>
            </div>
            <div className="flex items-center gap-2 text-slate-400">
              <Calendar className="h-4 w-4" />
              <span>
                {project.planned_end_date
                  ? formatDate(project.planned_end_date)
                  : "未设置"}
              </span>
            </div>
          </div>

          {/* 进度条 */}
          <div className="mb-4">
            <div className="flex justify-between text-xs mb-2">
              <span className="text-slate-400">整体进度</span>
              <span className="text-white font-medium">
                {project.progress_pct || project.progress || 0}%
              </span>
            </div>
            <Progress
              value={project.progress_pct || project.progress || 0}
              color={
                project.health === "H3"
                  ? "danger"
                  : project.health === "H2"
                    ? "warning"
                    : "primary"
              }
            />
          </div>

          {/* 底部 */}
          <div className="flex items-center justify-between pt-3 border-t border-white/5">
            <Badge variant="secondary">{project.stage || "S1"}</Badge>
            <div className="flex items-center gap-1 text-sm text-slate-500 group-hover:text-primary transition-colors">
              查看详情
              <ArrowRight className="h-4 w-4 group-hover:translate-x-1 transition-transform" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
