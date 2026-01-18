/**
 * 项目卡片组件
 */





import { cn } from "../../lib/utils";
import { stageColors, healthColors, milestoneStatusColors } from "./scheduleConfig";

export default function ProjectCard({ project }) {
  const health = healthColors[project.health];

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="bg-surface-1 rounded-xl border border-border overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 border-b border-border/50">
        <div className="flex items-start justify-between mb-2">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-accent">
                {project.id}
              </span>
              <Badge className={cn("text-[10px]", stageColors[project.stage])}>
                {project.stageName}
              </Badge>
            </div>
            <h3 className="font-semibold text-white">{project.name}</h3>
            <p className="text-sm text-slate-400">{project.customer}</p>
          </div>
          <div
            className={cn(
              "px-2 py-1 rounded-lg text-xs font-medium",
              health.bg,
              health.text
            )}
          >
            {health.label}
          </div>
        </div>

        {/* Progress */}
        <div className="mt-3">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-slate-400">整体进度</span>
            <span className="text-white font-medium">{project.progress}%</span>
          </div>
          <Progress value={project.progress} className="h-2" />
        </div>

        {/* Time Info */}
        <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {project.planEnd}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            剩余 {project.daysRemaining} 天
          </span>
        </div>
      </div>

      {/* Milestones Timeline */}
      <div className="p-4 bg-surface-0/50">
        <div className="text-xs font-medium text-slate-400 mb-3">
          关键里程碑
        </div>
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[5px] top-2 bottom-2 w-0.5 bg-border" />

          <div className="space-y-3">
            {project.milestones.map((milestone, index) => (
              <div key={index} className="flex items-start gap-3 relative">
                <div
                  className={cn(
                    "w-3 h-3 rounded-full mt-0.5 z-10",
                    milestoneStatusColors[milestone.status]
                  )}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white truncate">
                      {milestone.name}
                    </span>
                    <span className="text-xs text-slate-500">
                      {milestone.date}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alerts */}
      {project.alerts && project.alerts.length > 0 && (
        <div className="p-3 bg-red-500/10 border-t border-red-500/20">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div className="text-xs text-red-300">
              {project.alerts.map((alert, i) => (
                <div key={i}>{alert}</div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Resources */}
      <div className="p-3 border-t border-border/50">
        <div className="flex items-center justify-between">
          <div className="flex -space-x-2">
            {project.resources.map((resource, index) => (
              <div
                key={index}
                className="w-7 h-7 rounded-full bg-gradient-to-br from-accent to-purple-500 flex items-center justify-center text-[10px] font-medium text-white border-2 border-surface-1"
                title={`${resource.name} (${resource.role}) - 负荷${resource.load}%`}
              >
                {resource.name[0]}
              </div>
            ))}
          </div>
          <Button variant="ghost" size="sm" className="h-7 text-xs">
            <ExternalLink className="w-3 h-3 mr-1" />
            详情
          </Button>
        </div>
      </div>
    </motion.div>
  );
}
