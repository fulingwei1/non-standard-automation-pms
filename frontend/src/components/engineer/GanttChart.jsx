/**
 * GanttChart Component - Timeline visualization for engineer tasks
 * Features: Zoom controls, project grouping, progress bars, milestones, today line
 */

import { useState, useMemo, useRef, useEffect } from "react";
import { motion } from "framer-motion";
import {
  ZoomIn,
  ZoomOut,
  Calendar,
  Flag,
  Diamond,
  AlertTriangle,
} from "lucide-react";
import { Button } from "../ui";
import { cn } from "../../lib/utils";

// Zoom levels configuration
const ZOOM_LEVELS = {
  day: { unit: "day", dayWidth: 60, format: "dd", headerFormat: "yyyy年MM月" },
  week: {
    unit: "week",
    dayWidth: 30,
    format: "dd",
    headerFormat: "yyyy年MM月",
  },
  month: {
    unit: "month",
    dayWidth: 12,
    format: "dd",
    headerFormat: "yyyy年MM月",
  },
};

// Helper: Format date
const formatDate = (date, format) => {
  if (!date) {return "";}
  const d = new Date(date);
  const year = d.getFullYear();
  const month = String(d.getMonth() + 1).padStart(2, "0");
  const day = String(d.getDate()).padStart(2, "0");

  switch (format) {
    case "yyyy年MM月":
      return `${year}年${month}月`;
    case "MM-dd":
      return `${month}-${day}`;
    case "dd":
      return day;
    default:
      return `${year}-${month}-${day}`;
  }
};

// Helper: Get days between two dates
const getDaysBetween = (start, end) => {
  const startDate = new Date(start);
  const endDate = new Date(end);
  return Math.ceil((endDate - startDate) / (1000 * 60 * 60 * 24));
};

// Helper: Add days to date
const addDays = (date, days) => {
  const result = new Date(date);
  result.setDate(result.getDate() + days);
  return result;
};

// Helper: Get date range for tasks
const getDateRange = (tasks) => {
  if (tasks.length === 0) {
    const today = new Date();
    return {
      start: addDays(today, -7),
      end: addDays(today, 30),
    };
  }

  let minDate = new Date(tasks[0].plannedStart);
  let maxDate = new Date(tasks[0].plannedEnd);

  tasks.forEach((task) => {
    const start = new Date(task.plannedStart);
    const end = new Date(task.plannedEnd);
    if (start < minDate) {minDate = start;}
    if (end > maxDate) {maxDate = end;}
  });

  // Add padding
  return {
    start: addDays(minDate, -3),
    end: addDays(maxDate, 7),
  };
};

// Status colors for task bars
const statusColors = {
  pending: {
    bg: "bg-slate-600",
    progress: "bg-slate-400",
    border: "border-slate-500",
  },
  in_progress: {
    bg: "bg-blue-900/50",
    progress: "bg-gradient-to-r from-blue-500 to-blue-400",
    border: "border-blue-500/50",
  },
  blocked: {
    bg: "bg-red-900/50",
    progress: "bg-gradient-to-r from-red-500 to-red-400",
    border: "border-red-500/50",
  },
  completed: {
    bg: "bg-emerald-900/50",
    progress: "bg-gradient-to-r from-emerald-500 to-emerald-400",
    border: "border-emerald-500/50",
  },
};

// Priority colors
const priorityColors = {
  low: "text-slate-400",
  medium: "text-blue-400",
  high: "text-amber-400",
  critical: "text-red-400",
};

// Gantt Task Bar Component
function GanttTaskBar({
  task,
  startOffset,
  width,
  dayWidth,
  onClick,
  isSelected,
}) {
  const colors = statusColors[task.status];
  const isOverdue =
    task.status !== "completed" && new Date(task.plannedEnd) < new Date();

  return (
    <motion.div
      initial={{ opacity: 0, scaleX: 0 }}
      animate={{ opacity: 1, scaleX: 1 }}
      whileHover={{ scale: 1.02 }}
      onClick={() => onClick(task)}
      className={cn(
        "absolute h-8 rounded-md cursor-pointer transition-all border",
        colors.bg,
        colors.border,
        isSelected && "ring-2 ring-primary ring-offset-2 ring-offset-surface-0",
        isOverdue && "ring-1 ring-red-500",
      )}
      style={{
        left: `${startOffset}px`,
        width: `${Math.max(width, dayWidth)}px`,
        top: "50%",
        transform: "translateY(-50%)",
        transformOrigin: "left center",
      }}
    >
      {/* Progress fill */}
      <div
        className={cn("h-full rounded-md", colors.progress)}
        style={{ width: `${task.progress}%` }}
      />

      {/* Task label */}
      <div className="absolute inset-0 flex items-center px-2 overflow-hidden">
        <span className="text-xs font-medium text-white truncate drop-shadow-sm">
          {task.titleCn}
        </span>
      </div>

      {/* Progress percentage */}
      <div className="absolute right-2 top-1/2 -translate-y-1/2">
        <span className="text-[10px] font-medium text-white/80">
          {task.progress}%
        </span>
      </div>

      {/* Overdue indicator */}
      {isOverdue && (
        <div className="absolute -top-1 -right-1 w-4 h-4 bg-red-500 rounded-full flex items-center justify-center">
          <AlertTriangle className="w-2.5 h-2.5 text-white" />
        </div>
      )}
    </motion.div>
  );
}

// Milestone marker component
function MilestoneMarker({ label, offset }) {
  return (
    <div
      className="absolute flex flex-col items-center"
      style={{
        left: `${offset}px`,
        top: "50%",
        transform: "translate(-50%, -50%)",
      }}
    >
      <Diamond className="w-4 h-4 text-purple-400 fill-purple-400" />
      <span className="text-[10px] text-purple-400 mt-1 whitespace-nowrap">
        {label}
      </span>
    </div>
  );
}

// Main GanttChart Component
export default function GanttChart({ tasks, onTaskSelect, selectedTaskId }) {
  const [zoom, setZoom] = useState("week");
  const [scrollLeft, setScrollLeft] = useState(0);
  const chartRef = useRef(null);
  const headerRef = useRef(null);

  const zoomConfig = ZOOM_LEVELS[zoom];
  const { dayWidth } = zoomConfig;

  // Calculate date range
  const dateRange = useMemo(() => getDateRange(tasks), [tasks]);
  const totalDays = getDaysBetween(dateRange.start, dateRange.end);
  const totalWidth = totalDays * dayWidth;

  // Generate date headers
  const dateHeaders = useMemo(() => {
    const headers = [];
    let currentDate = new Date(dateRange.start);
    let currentMonth = null;

    while (currentDate <= dateRange.end) {
      const monthKey = `${currentDate.getFullYear()}-${currentDate.getMonth()}`;

      if (monthKey !== currentMonth) {
        headers.push({
          type: "month",
          date: new Date(currentDate),
          label: formatDate(currentDate, "yyyy年MM月"),
        });
        currentMonth = monthKey;
      }

      headers.push({
        type: "day",
        date: new Date(currentDate),
        label: formatDate(currentDate, "dd"),
        isToday: currentDate.toDateString() === new Date().toDateString(),
        isWeekend: currentDate.getDay() === 0 || currentDate.getDay() === 6,
      });

      currentDate = addDays(currentDate, 1);
    }

    return headers;
  }, [dateRange, zoom]);

  // Group tasks by project
  const groupedTasks = useMemo(() => {
    const groups = {};
    tasks.forEach((task) => {
      if (!groups[task.projectId]) {
        groups[task.projectId] = {
          projectId: task.projectId,
          projectName: task.projectName,
          tasks: [],
        };
      }
      groups[task.projectId].tasks.push(task);
    });
    return Object.values(groups);
  }, [tasks]);

  // Calculate task position
  const getTaskPosition = (task) => {
    const startDate = new Date(task.plannedStart);
    const endDate = new Date(task.plannedEnd);
    const startOffset = getDaysBetween(dateRange.start, startDate) * dayWidth;
    const duration = getDaysBetween(startDate, endDate) + 1;
    const width = duration * dayWidth;

    return { startOffset, width };
  };

  // Get today line position
  const todayOffset = useMemo(() => {
    const today = new Date();
    if (today < dateRange.start || today > dateRange.end) {return null;}
    return getDaysBetween(dateRange.start, today) * dayWidth;
  }, [dateRange, dayWidth]);

  // Sync scroll between header and chart
  const handleScroll = (e) => {
    const left = e.target.scrollLeft;
    setScrollLeft(left);
    if (headerRef.current) {
      headerRef.current.scrollLeft = left;
    }
  };

  // Zoom controls
  const handleZoomIn = () => {
    if (zoom === "month") {setZoom("week");}
    else if (zoom === "week") {setZoom("day");}
  };

  const handleZoomOut = () => {
    if (zoom === "day") {setZoom("week");}
    else if (zoom === "week") {setZoom("month");}
  };

  // Scroll to today
  const scrollToToday = () => {
    if (todayOffset && chartRef.current) {
      const containerWidth = chartRef.current.clientWidth;
      chartRef.current.scrollLeft = todayOffset - containerWidth / 2;
    }
  };

  // Initial scroll to today
  useEffect(() => {
    scrollToToday();
  }, [zoom]);

  return (
    <div className="bg-surface-1 rounded-xl border border-border overflow-hidden">
      {/* Toolbar */}
      <div className="flex items-center justify-between p-3 border-b border-border bg-surface-2/50">
        <div className="flex items-center gap-2">
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomOut}
            disabled={zoom === "month"}
          >
            <ZoomOut className="w-4 h-4" />
          </Button>
          <span className="text-sm text-slate-400 min-w-16 text-center">
            {zoom === "day" ? "日视图" : zoom === "week" ? "周视图" : "月视图"}
          </span>
          <Button
            variant="ghost"
            size="sm"
            onClick={handleZoomIn}
            disabled={zoom === "day"}
          >
            <ZoomIn className="w-4 h-4" />
          </Button>
        </div>

        <Button variant="outline" size="sm" onClick={scrollToToday}>
          <Calendar className="w-4 h-4 mr-1" />
          今天
        </Button>
      </div>

      {/* Date Headers */}
      <div
        ref={headerRef}
        className="overflow-hidden border-b border-border bg-surface-2/30"
        style={{ marginLeft: "200px" }}
      >
        <div
          className="flex"
          style={{
            width: `${totalWidth}px`,
            transform: `translateX(-${scrollLeft}px)`,
          }}
        >
          {dateHeaders
            .filter((h) => h.type === "day")
            .map((header, index) => (
              <div
                key={index}
                className={cn(
                  "flex-shrink-0 text-center py-2 border-r border-border/30",
                  header.isToday && "bg-primary/10",
                  header.isWeekend && "bg-slate-800/30",
                )}
                style={{ width: `${dayWidth}px` }}
              >
                <span
                  className={cn(
                    "text-xs",
                    header.isToday
                      ? "text-primary font-bold"
                      : "text-slate-400",
                  )}
                >
                  {header.label}
                </span>
              </div>
            ))}
        </div>
      </div>

      {/* Chart Body */}
      <div className="flex">
        {/* Task Names Column */}
        <div className="w-[200px] flex-shrink-0 border-r border-border bg-surface-2/20">
          {groupedTasks.map((group) => (
            <div key={group.projectId}>
              {/* Project Header */}
              <div className="px-3 py-2 bg-surface-2/50 border-b border-border">
                <span className="text-xs font-medium text-accent truncate">
                  {group.projectName}
                </span>
              </div>

              {/* Tasks */}
              {group.tasks.map((task) => (
                <div
                  key={task.id}
                  onClick={() => onTaskSelect(task)}
                  className={cn(
                    "h-12 px-3 flex items-center border-b border-border/50 cursor-pointer transition-colors",
                    selectedTaskId === task.id
                      ? "bg-primary/10"
                      : "hover:bg-surface-2/50",
                  )}
                >
                  <Flag
                    className={cn(
                      "w-3 h-3 mr-2",
                      priorityColors[task.priority],
                    )}
                  />
                  <span className="text-sm text-white truncate">
                    {task.titleCn}
                  </span>
                </div>
              ))}
            </div>
          ))}

          {groupedTasks.length === 0 && (
            <div className="h-32 flex items-center justify-center">
              <span className="text-sm text-slate-500">暂无任务</span>
            </div>
          )}
        </div>

        {/* Timeline Area */}
        <div
          ref={chartRef}
          className="flex-1 overflow-x-auto"
          onScroll={handleScroll}
        >
          <div style={{ width: `${totalWidth}px`, minHeight: "200px" }}>
            {/* Grid Background */}
            <div
              className="absolute inset-0 flex pointer-events-none"
              style={{ width: `${totalWidth}px` }}
            >
              {dateHeaders
                .filter((h) => h.type === "day")
                .map((header, index) => (
                  <div
                    key={index}
                    className={cn(
                      "flex-shrink-0 border-r border-border/20",
                      header.isWeekend && "bg-slate-800/20",
                    )}
                    style={{ width: `${dayWidth}px`, height: "100%" }}
                  />
                ))}
            </div>

            {/* Today Line */}
            {todayOffset && (
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-red-500 z-10"
                style={{ left: `${todayOffset}px` }}
              >
                <div className="absolute -top-1 left-1/2 -translate-x-1/2 px-1.5 py-0.5 bg-red-500 rounded text-[10px] text-white font-medium">
                  今天
                </div>
              </div>
            )}

            {/* Task Rows */}
            {groupedTasks.map((group) => (
              <div key={group.projectId}>
                {/* Project spacer */}
                <div className="h-[33px] border-b border-border" />

                {/* Task bars */}
                {group.tasks.map((task) => {
                  const { startOffset, width } = getTaskPosition(task);
                  return (
                    <div
                      key={task.id}
                      className="h-12 relative border-b border-border/50"
                    >
                      <GanttTaskBar
                        task={task}
                        startOffset={startOffset}
                        width={width}
                        dayWidth={dayWidth}
                        onClick={onTaskSelect}
                        isSelected={selectedTaskId === task.id}
                      />

                      {/* Milestone marker */}
                      {task.milestone && task.milestoneDate && (
                        <MilestoneMarker
                          date={task.milestoneDate}
                          label={task.milestone}
                          offset={
                            getDaysBetween(
                              dateRange.start,
                              new Date(task.milestoneDate),
                            ) * dayWidth
                          }
                        />
                      )}
                    </div>
                  );
                })}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 p-3 border-t border-border bg-surface-2/30 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <div className="w-4 h-2 rounded bg-gradient-to-r from-blue-500 to-blue-400" />
          <span>进行中</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-2 rounded bg-slate-600" />
          <span>待开始</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-2 rounded bg-gradient-to-r from-emerald-500 to-emerald-400" />
          <span>已完成</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-2 rounded bg-gradient-to-r from-red-500 to-red-400" />
          <span>已阻塞</span>
        </div>
        <div className="flex items-center gap-2">
          <Diamond className="w-3 h-3 text-purple-400 fill-purple-400" />
          <span>里程碑</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-0.5 h-3 bg-red-500" />
          <span>今天</span>
        </div>
      </div>
    </div>
  );
}
