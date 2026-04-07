
export default function DependencyList({
  dependencies,
  sortedTasks,
  criticalTaskSet,
  handleDeleteDependency,
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
      <h2 className="mb-4 text-sm font-semibold text-slate-100">依赖关系列表</h2>
      {dependencies.length === 0 ? (
        <div className="text-xs text-slate-500">暂无依赖关系。</div>
      ) : (
        <div className="space-y-2">
          {dependencies.map((dependency) => {
            const task = sortedTasks.find((item) => item.id === dependency.task_id);
            const dependsOnTask = sortedTasks.find(
              (item) => item.id === dependency.depends_on_task_id,
            );
            const isCritical =
              criticalTaskSet.has(dependency.task_id) &&
              criticalTaskSet.has(dependency.depends_on_task_id);

            return (
              <div
                key={`dependency-${dependency.id}`}
                className={`rounded-lg border px-3 py-2 ${
                  isCritical
                    ? "border-orange-400/30 bg-orange-500/10"
                    : "border-slate-700 bg-slate-900/70"
                }`}
              >
                <div className="flex items-start justify-between gap-3">
                  <div className="min-w-0 text-xs text-slate-300">
                    <div className="truncate">
                      {dependsOnTask?.task_name || `任务 #${dependency.depends_on_task_id}`}{" "}
                      <span className="text-slate-500">→</span>{" "}
                      {task?.task_name || `任务 #${dependency.task_id}`}
                    </div>
                    <div className="mt-1 text-[11px] text-slate-500">
                      类型: {dependency.dependency_type || "FS"} | 滞后:{" "}
                      {dependency.lag_days || 0} 天
                    </div>
                  </div>
                  <button
                    type="button"
                    onClick={() => handleDeleteDependency(dependency.id)}
                    className="rounded-md border border-red-500/30 bg-red-500/10 p-1.5 text-red-300 transition hover:bg-red-500/20"
                  >
                    <Trash2 className="h-3.5 w-3.5" />
                  </button>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
