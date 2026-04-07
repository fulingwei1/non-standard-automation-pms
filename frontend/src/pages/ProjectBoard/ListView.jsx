import { cn } from "../../lib/utils";
import { PROJECT_STAGES, HEALTH_CONFIG } from "../../lib/constants";

export default function ListView({ projects, onProjectClick, isProjectRelevant }) {
  return (
    <div className="space-y-2">
      {(projects || []).map((project, index) =>
      <motion.div
        key={project.id}
        initial={{ opacity: 0, y: 10 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ delay: index * 0.02 }}>

          <Card
          className={cn(
            "hover:bg-surface-2/50 cursor-pointer transition-colors",
            isProjectRelevant(project.id) && "ring-1 ring-primary/30"
          )}
          onClick={() => onProjectClick(project)}>

            <div className="p-4 flex items-center gap-4">
              {/* 健康度指示 */}
              <div
              className={cn(
                "w-1 h-12 rounded-full",
                HEALTH_CONFIG[project.health || "H1"].dotClass
              )} />


              {/* 项目信息 */}
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2 mb-1">
                  <span className="text-xs font-mono text-slate-400">
                    {project.project_code}
                  </span>
                  <span
                  className={cn(
                    "text-xs px-2 py-0.5 rounded",
                    HEALTH_CONFIG[project.health || "H1"].bgClass,
                    HEALTH_CONFIG[project.health || "H1"].textClass
                  )}>

                    {HEALTH_CONFIG[project.health || "H1"].label}
                  </span>
                </div>
                <h4 className="text-white font-medium truncate">
                  {project.name}
                </h4>
              </div>

              {/* 阶段 */}
              <div className="text-center px-4">
                <div className="text-xs text-slate-500">阶段</div>
                <div className="text-sm text-white">
                  {PROJECT_STAGES.find(
                  (s) =>
                  (s.key || s.code) === (
                  project.stage || project.current_stage)
                )?.shortName || "-"}
                </div>
              </div>

              {/* 客户 */}
              <div className="text-center px-4 min-w-[100px]">
                <div className="text-xs text-slate-500">客户</div>
                <div className="text-sm text-white truncate">
                  {project.customer_name || "-"}
                </div>
              </div>

              {/* 负责人 */}
              <div className="text-center px-4">
                <div className="text-xs text-slate-500">负责人</div>
                <div className="text-sm text-white">
                  {project.pm_name || "-"}
                </div>
              </div>

              {/* 进度 */}
              <div className="text-center px-4 min-w-[80px]">
                <div className="text-xs text-slate-500">进度</div>
                <div className="text-sm text-white">
                  {project.progress || 0}%
                </div>
              </div>

              {/* 截止日期 */}
              <div className="text-center px-4">
                <div className="text-xs text-slate-500">截止</div>
                <div className="text-sm text-white">
                  {project.planned_end_date || "-"}
                </div>
              </div>
            </div>
          </Card>
      </motion.div>
      )}
    </div>);

}
