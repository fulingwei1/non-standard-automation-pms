import { formatDate } from "../../lib/utils";

export default function CriticalPathPanel({ criticalPathTaskIds, sortedTasks }) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
      <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-100">
        <Route className="h-4 w-4 text-orange-300" />
        关键路径
      </h2>
      {criticalPathTaskIds.length === 0 ? (
        <div className="text-xs text-slate-500">暂无关键路径数据。</div>
      ) : (
        <div className="space-y-2 text-xs text-slate-300">
          {criticalPathTaskIds.map((taskId, index) => {
            const task = sortedTasks.find((item) => item.id === taskId);
            return (
              <div
                key={`critical-task-${taskId}`}
                className="rounded-lg border border-orange-400/30 bg-orange-500/10 px-3 py-2"
              >
                <div className="font-medium text-orange-200">
                  {index + 1}. {task?.task_name || `任务 #${taskId}`}
                </div>
                <div className="mt-1 text-[11px] text-orange-100/80">
                  {formatDate(task?.plan_start)} - {formatDate(task?.plan_end)}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
