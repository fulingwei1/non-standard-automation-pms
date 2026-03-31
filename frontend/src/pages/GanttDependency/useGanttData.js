import { useCallback, useEffect, useMemo, useState } from "react";
import { ganttDependencyApi, projectApi } from "../../services/api";
import { ROW_HEIGHT } from "./constants";
import { extractPayload, normalizeProjects, parseDate, diffDays, getTaskBarPlacement } from "./utils";

export default function useGanttData() {
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

  return {
    projects,
    selectedProjectId,
    setSelectedProjectId,
    selectedProject,
    sortedTasks,
    dependencies,
    criticalPathTaskIds,
    criticalPathDuration,
    criticalTaskSet,
    loading,
    submitting,
    error,
    notice,
    form,
    setForm,
    timelineRange,
    timelineMarkers,
    taskPlacementMap,
    dependencyLines,
    handleRefresh,
    handleCreateDependency,
    handleDeleteDependency,
  };
}
