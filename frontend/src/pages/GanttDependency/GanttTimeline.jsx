import { fadeIn } from "../../lib/animations";
import { formatDate } from "../../lib/utils";
import { STATUS_META, ROW_HEIGHT } from "./constants";

export default function GanttTimeline({
  sortedTasks,
  timelineMarkers,
  taskPlacementMap,
  dependencyLines,
  criticalTaskSet,
  blockingMode,
  highlightedTaskId,
  isTaskHighlighted,
  getTaskBlockingRole,
  handleTaskClick,
}) {
  return (
    <motion.section
      variants={fadeIn}
      className="rounded-2xl border border-slate-800 bg-slate-950/70"
    >
      <div className="border-b border-slate-800 px-5 py-4">
        <h2 className="text-sm font-semibold text-slate-100">任务时间线与依赖箭头</h2>
      </div>

      {sortedTasks.length === 0 ? (
        <div className="px-5 py-16 text-center text-sm text-slate-500">
          当前项目暂无任务数据，请先创建任务后再配置依赖。
        </div>
      ) : (
        <div className="overflow-x-auto">
          <div className="min-w-[920px]">
            <div className="grid grid-cols-[280px,1fr] border-b border-slate-800 bg-slate-900/70">
              <div className="px-4 py-3 text-xs uppercase tracking-wide text-slate-400">任务</div>
              <div className="relative px-3 py-3 text-xs text-slate-400">
                <div className="relative h-6">
                  {timelineMarkers.map((marker, index) => (
                    <div
                      key={`${marker.date.toISOString()}-${index}`}
                      className="absolute -translate-x-1/2"
                      style={{ left: `${marker.leftPct}%` }}
                    >
                      <div className="h-2 w-px bg-slate-700" />
                      <div className="mt-1 whitespace-nowrap text-[10px] text-slate-500">
                        {formatDate(marker.date)}
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            </div>

            <div className="grid grid-cols-[280px,1fr]">
              <div>
                {sortedTasks.map((task) => {
                  const statusMeta = STATUS_META[task.status] || STATUS_META.TODO;
                  const isCritical = criticalTaskSet.has(task.id);
                  const blockingRole = getTaskBlockingRole(task.id);
                  const isHighlighted = isTaskHighlighted(task.id);
                  const shouldDim = blockingMode && highlightedTaskId && !isHighlighted;

                  const getBlockingBgClass = () => {
                    if (!blockingMode) return isCritical ? "bg-orange-500/10" : "bg-transparent";
                    if (blockingRole === "center") return "bg-cyan-500/20";
                    if (blockingRole === "upstream") return "bg-red-500/15";
                    if (blockingRole === "downstream") return "bg-amber-500/15";
                    return shouldDim ? "bg-transparent opacity-30" : "bg-transparent";
                  };

                  return (
                    <div
                      key={`task-info-${task.id}`}
                      className={`flex h-14 flex-col justify-center border-b border-slate-800 px-4 transition-all cursor-pointer ${getBlockingBgClass()}`}
                      onClick={() => handleTaskClick(task.id)}
                    >
                      <div className="flex items-center gap-2">
                        <div className="truncate text-sm font-medium text-slate-100">{task.task_name}</div>
                        {blockingRole === "upstream" && (
                          <span className="text-[10px] px-1 py-0.5 rounded bg-red-500/30 text-red-300">阻塞源</span>
                        )}
                        {blockingRole === "downstream" && (
                          <span className="text-[10px] px-1 py-0.5 rounded bg-amber-500/30 text-amber-300">被阻塞</span>
                        )}
                        {blockingRole === "center" && (
                          <span className="text-[10px] px-1 py-0.5 rounded bg-cyan-500/30 text-cyan-300">当前</span>
                        )}
                      </div>
                      <div className="mt-1 flex items-center gap-2 text-[11px] text-slate-400">
                        <span
                          className={`rounded border px-1.5 py-0.5 ${statusMeta.badgeClass}`}
                        >
                          {statusMeta.label}
                        </span>
                        <span>{task.stage || "-"}</span>
                        <span>{task.progress_percent || 0}%</span>
                      </div>
                    </div>
                  );
                })}
              </div>

              <div className="relative bg-slate-900/40">
                <div
                  className="relative"
                  style={{ height: `${sortedTasks.length * ROW_HEIGHT}px` }}
                >
                  {sortedTasks.map((task, index) => {
                    const placement = taskPlacementMap[task.id];
                    const statusMeta = STATUS_META[task.status] || STATUS_META.TODO;
                    const isCritical = criticalTaskSet.has(task.id);
                    const blockingRole = getTaskBlockingRole(task.id);
                    const isHighlighted = isTaskHighlighted(task.id);
                    const shouldDim = blockingMode && highlightedTaskId && !isHighlighted;

                    const getBlockingRingClass = () => {
                      if (!blockingMode) return isCritical ? "ring-2 ring-orange-300/70" : "";
                      if (blockingRole === "center") return "ring-2 ring-cyan-400";
                      if (blockingRole === "upstream") return "ring-2 ring-red-400/70";
                      if (blockingRole === "downstream") return "ring-2 ring-amber-400/70";
                      return "";
                    };

                    return (
                      <div
                        key={`task-bar-${task.id}`}
                        className={`transition-opacity ${shouldDim ? "opacity-30" : ""}`}
                      >
                        <div
                          className="absolute left-0 right-0 border-b border-slate-800/80"
                          style={{ top: `${(index + 1) * ROW_HEIGHT}px` }}
                        />
                        <div
                          className={`absolute top-2 h-9 rounded-md px-2 text-xs font-medium text-white shadow-lg cursor-pointer ${
                            statusMeta.barClass
                          } ${getBlockingRingClass()}`}
                          style={{
                            left: `${placement.leftPct}%`,
                            width: `${placement.widthPct}%`,
                          }}
                          title={`${task.task_name}: ${formatDate(task.plan_start)} - ${formatDate(task.plan_end)}`}
                          onClick={() => handleTaskClick(task.id)}
                        >
                          <div className="truncate leading-9">{task.task_name}</div>
                        </div>
                      </div>
                    );
                  })}

                  <div className="pointer-events-none absolute inset-0">
                    {dependencyLines.map((line) => (
                      <div key={`line-${line.id}`} className="absolute inset-0">
                        <div
                          className={`absolute h-px ${
                            line.inCriticalPath ? "bg-orange-300" : "bg-cyan-300/80"
                          }`}
                          style={{
                            left: `${line.x1}%`,
                            top: `${line.y1}px`,
                            width: `${Math.max(line.turnX - line.x1, 0.2)}%`,
                          }}
                        />
                        <div
                          className={`absolute w-px ${
                            line.inCriticalPath ? "bg-orange-300" : "bg-cyan-300/80"
                          }`}
                          style={{
                            left: `${line.turnX}%`,
                            top: `${Math.min(line.y1, line.y2)}px`,
                            height: `${Math.max(Math.abs(line.y2 - line.y1), 1)}px`,
                          }}
                        />
                        <div
                          className={`absolute h-px ${
                            line.inCriticalPath ? "bg-orange-300" : "bg-cyan-300/80"
                          }`}
                          style={{
                            left: `${line.horizontal2Left}%`,
                            top: `${line.y2}px`,
                            width: `${Math.max(line.horizontal2Width, 0.2)}%`,
                          }}
                        />
                        <div
                          className={`absolute h-0 w-0 border-y-[4px] border-y-transparent ${
                            line.inCriticalPath
                              ? "border-l-[6px] border-l-orange-300"
                              : "border-l-[6px] border-l-cyan-300"
                          }`}
                          style={{
                            left: `${line.x2}%`,
                            top: `${line.y2 - 4}px`,
                            transform:
                              line.direction === "left"
                                ? "translateX(-100%) rotate(180deg)"
                                : "translateX(-5%)",
                          }}
                        />
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </motion.section>
  );
}
