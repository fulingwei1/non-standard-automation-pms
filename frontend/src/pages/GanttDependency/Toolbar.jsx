import { fadeIn } from "../../lib/animations";

export default function Toolbar({
  projects,
  selectedProjectId,
  setSelectedProjectId,
  selectedProject,
  criticalPathDuration,
  blockingMode,
  toggleBlockingMode,
  handleRefresh,
}) {
  return (
    <motion.section
      variants={fadeIn}
      className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 p-5"
    >
      <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
        <div className="flex items-center gap-3">
          <GitBranch className="h-5 w-5 text-cyan-300" />
          <span className="text-sm text-slate-300">项目选择</span>
          <select
            value={selectedProjectId || "unknown"}
            onChange={(event) => setSelectedProjectId(event.target.value)}
            className="min-w-56 rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none"
          >
            {projects.length === 0 && <option value="">暂无项目</option>}
            {projects.map((project) => (
              <option key={project.id} value={project.id}>
                {project.project_name || project.name || `项目 #${project.id}`}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-wrap items-center gap-3">
          <div className="rounded-lg border border-orange-500/30 bg-orange-500/10 px-3 py-2 text-xs text-orange-200">
            关键路径工期: {criticalPathDuration || 0} 天
          </div>
          <Button
            variant={blockingMode ? "default" : "outline"}
            className={blockingMode
              ? "bg-amber-600 text-white hover:bg-amber-500"
              : "border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800"
            }
            onClick={toggleBlockingMode}
          >
            {blockingMode ? (
              <>
                <EyeOff className="mr-2 h-4 w-4" />
                关闭阻塞高亮
              </>
            ) : (
              <>
                <AlertTriangle className="mr-2 h-4 w-4" />
                阻塞高亮模式
              </>
            )}
          </Button>
          <Button
            variant="outline"
            className="border-slate-700 bg-slate-900 text-slate-100 hover:bg-slate-800"
            onClick={handleRefresh}
          >
            <RefreshCw className="mr-2 h-4 w-4" />
            刷新
          </Button>
        </div>
      </div>
      <p className="mt-3 text-xs text-slate-400">
        当前项目: {selectedProject?.project_name || selectedProject?.name || "-"}
        {blockingMode
          ? "，阻塞高亮模式已启用，点击任务查看上下游依赖链。"
          : "，关键路径任务将以橙色高亮。"
        }
      </p>
    </motion.section>
  );
}
