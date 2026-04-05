import { Link2 } from "lucide-react";
import { Button } from "../../components/ui/button";

export default function DependencyForm({
  form,
  setForm,
  sortedTasks,
  submitting,
  selectedProjectId,
  handleCreateDependency,
}) {
  return (
    <div className="rounded-2xl border border-slate-800 bg-slate-950/70 p-5">
      <h2 className="mb-4 flex items-center gap-2 text-sm font-semibold text-slate-100">
        <Link2 className="h-4 w-4 text-cyan-300" />
        新增依赖关系
      </h2>
      <form onSubmit={handleCreateDependency} className="space-y-3">
        <div>
          <label className="mb-1 block text-xs text-slate-400">任务</label>
          <select
            value={form.task_id}
            onChange={(event) => setForm((prev) => ({ ...prev, task_id: event.target.value }))}
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none"
          >
            <option value="">请选择任务</option>
            {sortedTasks.map((task) => (
              <option key={`task-option-${task.id}`} value={task.id}>
                {task.task_name}
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="mb-1 block text-xs text-slate-400">前置任务</label>
          <select
            value={form.depends_on_task_id}
            onChange={(event) =>
              setForm((prev) => ({ ...prev, depends_on_task_id: event.target.value }))
            }
            className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none"
          >
            <option value="">请选择前置任务</option>
            {sortedTasks
              .filter((task) => String(task.id) !== String(form.task_id))
              .map((task) => (
                <option key={`depends-task-option-${task.id}`} value={task.id}>
                  {task.task_name}
                </option>
              ))}
          </select>
        </div>

        <div className="grid grid-cols-2 gap-3">
          <div>
            <label className="mb-1 block text-xs text-slate-400">依赖类型</label>
            <select
              value={form.dependency_type}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, dependency_type: event.target.value }))
              }
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none"
            >
              <option value="FS">FS</option>
              <option value="SS">SS</option>
              <option value="FF">FF</option>
              <option value="SF">SF</option>
            </select>
          </div>
          <div>
            <label className="mb-1 block text-xs text-slate-400">滞后天数</label>
            <input
              type="number"
              value={form.lag_days}
              onChange={(event) =>
                setForm((prev) => ({ ...prev, lag_days: event.target.value }))
              }
              className="w-full rounded-lg border border-slate-700 bg-slate-900 px-3 py-2 text-sm text-slate-100 focus:border-cyan-500 focus:outline-none"
            />
          </div>
        </div>

        <Button
          type="submit"
          disabled={submitting || !selectedProjectId}
          className="w-full bg-cyan-600 text-white hover:bg-cyan-500"
        >
          {submitting ? "创建中..." : "创建依赖"}
        </Button>
      </form>
    </div>
  );
}
