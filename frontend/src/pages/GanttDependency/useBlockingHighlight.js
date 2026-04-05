import { useCallback, useMemo, useState } from "react";

export default function useBlockingHighlight(dependencies) {
  const [blockingMode, setBlockingMode] = useState(false);
  const [highlightedTaskId, setHighlightedTaskId] = useState(null);

  const highlightedChain = useMemo(() => {
    if (!blockingMode || !highlightedTaskId) {
      return { upstream: new Set(), downstream: new Set(), center: null };
    }

    const upstream = new Set();
    const downstream = new Set();

    const findUpstream = (taskId, visited = new Set()) => {
      if (visited.has(taskId)) return;
      visited.add(taskId);

      dependencies.forEach((dep) => {
        if (dep.task_id === taskId) {
          upstream.add(dep.depends_on_task_id);
          findUpstream(dep.depends_on_task_id, visited);
        }
      });
    };

    const findDownstream = (taskId, visited = new Set()) => {
      if (visited.has(taskId)) return;
      visited.add(taskId);

      dependencies.forEach((dep) => {
        if (dep.depends_on_task_id === taskId) {
          downstream.add(dep.task_id);
          findDownstream(dep.task_id, visited);
        }
      });
    };

    findUpstream(highlightedTaskId);
    findDownstream(highlightedTaskId);

    return { upstream, downstream, center: highlightedTaskId };
  }, [blockingMode, highlightedTaskId, dependencies]);

  const isTaskHighlighted = useCallback((taskId) => {
    if (!blockingMode) return false;
    if (!highlightedTaskId) return false;
    return (
      taskId === highlightedTaskId ||
      highlightedChain.upstream.has(taskId) ||
      highlightedChain.downstream.has(taskId)
    );
  }, [blockingMode, highlightedTaskId, highlightedChain]);

  const getTaskBlockingRole = useCallback((taskId) => {
    if (!blockingMode || !highlightedTaskId) return null;
    if (taskId === highlightedTaskId) return "center";
    if (highlightedChain.upstream.has(taskId)) return "upstream";
    if (highlightedChain.downstream.has(taskId)) return "downstream";
    return null;
  }, [blockingMode, highlightedTaskId, highlightedChain]);

  const handleTaskClick = useCallback((taskId) => {
    if (blockingMode) {
      setHighlightedTaskId(highlightedTaskId === taskId ? null : taskId);
    }
  }, [blockingMode, highlightedTaskId]);

  const toggleBlockingMode = useCallback(() => {
    setBlockingMode((prev) => {
      if (prev) {
        setHighlightedTaskId(null);
      }
      return !prev;
    });
  }, []);

  return {
    blockingMode,
    highlightedTaskId,
    isTaskHighlighted,
    getTaskBlockingRole,
    handleTaskClick,
    toggleBlockingMode,
  };
}
