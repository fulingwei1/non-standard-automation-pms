import { useCallback, useEffect, useMemo, useState } from "react";
import { motion } from "framer-motion";
import { GitBranch, RefreshCw, Trash2, Link2, Route } from "lucide-react";
import { PageHeader } from "../components/layout";
import { Button } from "../components/ui/button";
import { fadeIn, staggerContainer } from "../lib/animations";
import { formatDate } from "../lib/utils";
import { ganttDependencyApi, projectApi } from "../services/api";

const STATUS_META = {
  DONE: {
    label: "已完成",
    barClass: "bg-emerald-500/80",
    badgeClass: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  },
  COMPLETED: {
    label: "已完成",
    barClass: "bg-emerald-500/80",
    badgeClass: "bg-emerald-500/15 text-emerald-300 border-emerald-500/30",
  },
  IN_PROGRESS: {
    label: "进行中",
    barClass: "bg-blue-500/80",
    badgeClass: "bg-blue-500/15 text-blue-300 border-blue-500/30",
  },
  TODO: {
    label: "待开始",
    barClass: "bg-slate-500/80",
    badgeClass: "bg-slate-500/20 text-slate-300 border-slate-500/30",
  },
  PENDING: {
    label: "待开始",
    barClass: "bg-slate-500/80",
    badgeClass: "bg-slate-500/20 text-slate-300 border-slate-500/30",
  },
  BLOCKED: {
    label: "阻塞",
    barClass: "bg-red-500/80",
    badgeClass: "bg-red-500/15 text-red-300 border-red-500/30",
  },
};

const ROW_HEIGHT = 56;

function extractPayload(response) {
  return response?.formatted ?? response?.data?.data ?? response?.data ?? response;
}

function normalizeProjects(payload) {
  if (Array.isArray(payload)) {
    return payload;
  }
  if (Array.isArray(payload?.items)) {
    return payload.items;
  }
  if (Array.isArray(payload?.list)) {
    return payload.list;
  }
  if (Array.isArray(payload?.data?.items)) {
    return payload.data.items;
  }
  return [];
}

function parseDate(value) {
  if (!value) {
    return null;
  }
  const parsed = new Date(value);
  if (Number.isNaN(parsed.getTime())) {
    return null;
  }
  return parsed;
}

function diffDays(start, end) {
  const ms = end.getTime() - start.getTime();
  return Math.round(ms / (1000 * 60 * 60 * 24));
}

function getTaskBarPlacement(task, timelineRange) {
  const start = parseDate(task.plan_start) || timelineRange.startDate;
  const rawEnd = parseDate(task.plan_end) || start;
  const end = rawEnd < start ? start : rawEnd;
  const startOffset = Math.max(0, diffDays(timelineRange.startDate, start));
  const duration = Math.max(1, diffDays(start, end) + 1);
  const leftPct = (startOffset / timelineRange.totalDays) * 100;
  const widthPct = Math.max((duration / timelineRange.totalDays) * 100, 1.5);
  return {
    leftPct,
    widthPct,
    endPct: Math.min(leftPct + widthPct, 100),
  };
}

export default function GanttDependency() {
  const [projects, setProjects] = useState([]);
  const [selectedProjectId, setSelectedProjectId] = useState("");
  const [tasks, setTasks] = useState([]);
  const [dependencies, setDependencies] = useState([]);
  const [criticalPathTaskIds, setCriticalPathTaskIds] = useState([]);
  const [criticalPathDuration, setCriticalPathDuration] = useState(0);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState("");
  const [notice, setNotice] = useState("");
  const [form, setForm] = useState({
    task_id: "",
    depends_on_task_id: "",
    dependency_type: "FS",
    lag_days: 0,
  });

  const loadProjects = useCallback(async () => {
    try {
      const response = await projectApi.list({ page: 1, page_size: 200 });
      const payload = extractPayload(response);
      const list = normalizeProjects(payload);
      setProjects(list);

      if (!selectedProjectId && list.length > 0) {
        setSelectedProjectId(String(list[0].id));
      }
    } catch (err) {
      console.error("加载项目列表失败:", err);
      setError("加载项目列表失败，请稍后重试。");
    }
  }, [selectedProjectId]);

  const loadProjectData = useCallback(async (projectId) => {
    if (!projectId) {
      return;
    }

    try {
      setLoading(true);
      setError("");

      const [ganttRes, criticalRes] = await Promise.all([
        ganttDependencyApi.getGantt(projectId),
        ganttDependencyApi.getCriticalPath(projectId),
      ]);

      const ganttPayload = extractPayload(ganttRes);
      const criticalPayload = extractPayload(criticalRes);

      setTasks(ganttPayload?.tasks || []);
      setDependencies(ganttPayload?.dependencies || []);
      setCriticalPathTaskIds(criticalPayload?.critical_path_task_ids || []);
      setCriticalPathDuration(criticalPayload?.total_duration_days || 0);

      setForm((prev) => ({
        ...prev,
        task_id: prev.task_id || String(ganttPayload?.tasks?.[0]?.id || ""),
        depends_on_task_id: prev.depends_on_task_id || "",
      }));
    } catch (err) {
      console.error("加载甘特图数据失败:", err);
      setError("加载甘特图数据失败，请检查网络或稍后重试。");
      setTasks([]);
      setDependencies([]);
      setCriticalPathTaskIds([]);
      setCriticalPathDuration(0);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadProjects();
  }, [loadProjects]);

  useEffect(() => {
    if (selectedProjectId) {
      loadProjectData(selectedProjectId);
    }
  }, [loadProjectData, selectedProjectId]);

  const sortedTasks = useMemo(() => {
    return [...tasks].sort((a, b) => {
      const dateA = parseDate(a.plan_start) || parseDate(a.plan_end);
      const dateB = parseDate(b.plan_start) || parseDate(b.plan_end);
      if (!dateA && !dateB) {
        return a.id - b.id;
      }
      if (!dateA) {
        return 1;
      }
      if (!dateB) {
        return -1;
      }
      return dateA.getTime() - dateB.getTime();
    });
  }, [tasks]);

  const timelineRange = useMemo(() => {
    const dates = [];
    sortedTasks.forEach((task) => {
      const start = parseDate(task.plan_start);
      const end = parseDate(task.plan_end);
      if (start) {
        dates.push(start);
      }
      if (end) {
        dates.push(end);
      }
    });

    if (dates.length === 0) {
      const today = new Date();
      const end = new Date(today);
      end.setDate(today.getDate() + 14);
      return {
        startDate: today,
        endDate: end,
        totalDays: 15,
      };
    }

    const sortedDates = [...dates].sort((a, b) => a.getTime() - b.getTime());
    const startDate = sortedDates[0];
    let endDate = sortedDates[sortedDates.length - 1];
    if (endDate.getTime() === startDate.getTime()) {
      endDate = new Date(endDate);
      endDate.setDate(endDate.getDate() + 1);
    }

    return {
      startDate,
      endDate,
      totalDays: Math.max(diffDays(startDate, endDate) + 1, 2),
    };
  }, [sortedTasks]);

  const timelineMarkers = useMemo(() => {
    const markerCount = 6;
    const step = Math.max(1, Math.floor(timelineRange.totalDays / (markerCount - 1)));
    return Array.from({ length: markerCount }, (_, idx) => {
      const offset = Math.min(idx * step, timelineRange.totalDays - 1);
      const markerDate = new Date(timelineRange.startDate);
      markerDate.setDate(timelineRange.startDate.getDate() + offset);
      return {
        date: markerDate,
        leftPct: (offset / timelineRange.totalDays) * 100,
      };
    });
  }, [timelineRange]);

  const taskPlacementMap = useMemo(() => {
    const map = {};
    sortedTasks.forEach((task, index) => {
      map[task.id] = {
        rowIndex: index,
        ...getTaskBarPlacement(task, timelineRange),
      };
    });
    return map;
  }, [sortedTasks, timelineRange]);

  const criticalTaskSet = useMemo(() => new Set(criticalPathTaskIds), [criticalPathTaskIds]);

  const dependencyLines = useMemo(() => {
    return dependencies
      .map((dependency) => {
        const source = taskPlacementMap[dependency.depends_on_task_id];
        const target = taskPlacementMap[dependency.task_id];
        if (!source || !target) {
          return null;
        }

        const y1 = source.rowIndex * ROW_HEIGHT + ROW_HEIGHT / 2;
        const y2 = target.rowIndex * ROW_HEIGHT + ROW_HEIGHT / 2;
        const x1 = Math.max(1, Math.min(99, source.endPct));
        const x2 = Math.max(1, Math.min(99, target.leftPct));
        const turnX = Math.max(1, Math.min(99, x1 + 2.2));
        const horizontal2Left = Math.min(turnX, x2);
        const horizontal2Width = Math.abs(x2 - turnX);
        const direction = x2 >= turnX ? "right" : "left";
        const inCriticalPath =
          criticalTaskSet.has(dependency.task_id) &&
          criticalTaskSet.has(dependency.depends_on_task_id);

        return {
          id: dependency.id,
          y1,
          y2,
          x1,
          x2,
          turnX,
          horizontal2Left,
          horizontal2Width,
          direction,
          inCriticalPath,
        };
      })
      .filter(Boolean);
  }, [dependencies, taskPlacementMap, criticalTaskSet]);

  const selectedProject = useMemo(() => {
    return projects.find((project) => String(project.id) === String(selectedProjectId));
  }, [projects, selectedProjectId]);

  const handleRefresh = async () => {
    if (!selectedProjectId) {
      return;
    }
    await loadProjectData(selectedProjectId);
  };

  const handleCreateDependency = async (event) => {
    event.preventDefault();
    setNotice("");
    setError("");

    if (!form.task_id || !form.depends_on_task_id) {
      setError("请选择任务和前置任务。");
      return;
    }
    if (form.task_id === form.depends_on_task_id) {
      setError("任务不能依赖自身。");
      return;
    }

    try {
      setSubmitting(true);
      await ganttDependencyApi.createDependency(selectedProjectId, {
        task_id: Number(form.task_id),
        depends_on_task_id: Number(form.depends_on_task_id),
        dependency_type: form.dependency_type,
        lag_days: Number(form.lag_days) || 0,
      });
      setNotice("依赖关系创建成功。");
      await loadProjectData(selectedProjectId);
    } catch (err) {
      console.error("创建依赖失败:", err);
      setError(err?.response?.data?.detail || "创建依赖失败，请重试。");
    } finally {
      setSubmitting(false);
    }
  };

  const handleDeleteDependency = async (dependencyId) => {
    setNotice("");
    setError("");
    try {
      await ganttDependencyApi.deleteDependency(dependencyId);
      setNotice("依赖关系已删除。");
      await loadProjectData(selectedProjectId);
    } catch (err) {
      console.error("删除依赖失败:", err);
      setError(err?.response?.data?.detail || "删除依赖失败，请重试。");
    }
  };

  return (
    <div className="space-y-6">
      <PageHeader
        title="甘特图依赖关系"
        description="任务时间线、依赖关系与关键路径分析"
      />

      {error && (
        <div className="rounded-xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
          {error}
        </div>
      )}
      {notice && (
        <div className="rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-4 py-3 text-sm text-emerald-200">
          {notice}
        </div>
      )}

      {loading ? (
        <div className="rounded-2xl border border-slate-800 bg-slate-950/60 py-16 text-center text-slate-400">
          正在加载甘特图依赖数据...
        </div>
      ) : (
        <motion.div
          initial="hidden"
          animate="visible"
          variants={staggerContainer}
          className="space-y-6"
        >
          <motion.section
            variants={fadeIn}
            className="rounded-2xl border border-slate-800 bg-gradient-to-r from-slate-950 via-slate-900 to-slate-950 p-5"
          >
            <div className="flex flex-col gap-4 lg:flex-row lg:items-center lg:justify-between">
              <div className="flex items-center gap-3">
                <GitBranch className="h-5 w-5 text-cyan-300" />
                <span className="text-sm text-slate-300">项目选择</span>
                <select
                  value={selectedProjectId}
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
              当前项目: {selectedProject?.project_name || selectedProject?.name || "-"}，关键路径任务将以橙色高亮。
            </p>
          </motion.section>

          <div className="grid grid-cols-1 gap-6 xl:grid-cols-[2fr,1fr]">
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

                          return (
                            <div
                              key={`task-info-${task.id}`}
                              className={`flex h-14 flex-col justify-center border-b border-slate-800 px-4 ${
                                isCritical ? "bg-orange-500/10" : "bg-transparent"
                              }`}
                            >
                              <div className="truncate text-sm font-medium text-slate-100">{task.task_name}</div>
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

                            return (
                              <div key={`task-bar-${task.id}`}>
                                <div
                                  className="absolute left-0 right-0 border-b border-slate-800/80"
                                  style={{ top: `${(index + 1) * ROW_HEIGHT}px` }}
                                />
                                <div
                                  className={`absolute top-2 h-9 rounded-md px-2 text-xs font-medium text-white shadow-lg ${
                                    statusMeta.barClass
                                  } ${isCritical ? "ring-2 ring-orange-300/70" : ""}`}
                                  style={{
                                    left: `${placement.leftPct}%`,
                                    width: `${placement.widthPct}%`,
                                  }}
                                  title={`${task.task_name}: ${formatDate(task.plan_start)} - ${formatDate(task.plan_end)}`}
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

            <motion.section variants={fadeIn} className="space-y-6">
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
            </motion.section>
          </div>
        </motion.div>
      )}
    </div>
  );
}
