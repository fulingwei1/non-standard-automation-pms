/**
 * CalendarView Component - Calendar-based task visualization
 * Features: Month/Week view, task blocks, due date indicators
 */

import { useState, useMemo } from "react";
import { motion, AnimatePresence } from "framer-motion";
import {
  ChevronLeft,
  ChevronRight,
  Calendar,
  Circle,
  CheckCircle2,
  PlayCircle,
  PauseCircle,
  AlertTriangle,
} from "lucide-react";
import { Button, Badge } from "../ui";
import { cn } from "../../lib/utils";

// View modes
const VIEW_MODES = {
  month: { id: "month", label: "月" },
  week: { id: "week", label: "周" },
};

// Days of week
const DAYS_OF_WEEK = ["日", "一", "二", "三", "四", "五", "六"];

// Status icons and colors
const statusConfig = {
  pending: { icon: Circle, color: "text-slate-400", bg: "bg-slate-500/20" },
  in_progress: {
    icon: PlayCircle,
    color: "text-blue-400",
    bg: "bg-blue-500/20",
  },
  blocked: { icon: PauseCircle, color: "text-red-400", bg: "bg-red-500/20" },
  completed: {
    icon: CheckCircle2,
    color: "text-emerald-400",
    bg: "bg-emerald-500/20",
  },
};

// Priority colors
const priorityColors = {
  low: "border-l-slate-400",
  medium: "border-l-blue-400",
  high: "border-l-amber-400",
  critical: "border-l-red-400",
};

// Helper: Get days in month
const getDaysInMonth = (year, month) => {
  return new Date(year, month + 1, 0).getDate();
};

// Helper: Get first day of month (0 = Sunday)
const getFirstDayOfMonth = (year, month) => {
  return new Date(year, month, 1).getDay();
};

// Helper: Format date key
const formatDateKey = (date) => {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
};

// Helper: Parse date string
const parseDate = (dateStr) => {
  if (!dateStr) {return null;}
  return new Date(dateStr);
};

// Helper: Check if two dates are the same day
const isSameDay = (date1, date2) => {
  return (
    date1.getFullYear() === date2.getFullYear() &&
    date1.getMonth() === date2.getMonth() &&
    date1.getDate() === date2.getDate()
  );
};

// Helper: Check if date is in range
const isDateInRange = (date, start, end) => {
  const d = new Date(date);
  d.setHours(0, 0, 0, 0);
  const s = new Date(start);
  s.setHours(0, 0, 0, 0);
  const e = new Date(end);
  e.setHours(0, 0, 0, 0);
  return d >= s && d <= e;
};

// Task Block Component
function TaskBlock({ task, onClick, isSelected, compact = false }) {
  const status = statusConfig[task.status];
  const StatusIcon = status.icon;
  const isOverdue =
    task.status !== "completed" && new Date(task.plannedEnd) < new Date();

  if (compact) {
    return (
      <div
        onClick={(e) => {
          e.stopPropagation();
          onClick(task);
        }}
        className={cn(
          "px-1.5 py-0.5 rounded text-xs truncate cursor-pointer transition-all border-l-2",
          status.bg,
          priorityColors[task.priority],
          isSelected && "ring-1 ring-primary",
          isOverdue && "ring-1 ring-red-500",
        )}
      >
        <span className={cn("truncate", status.color)}>{task.titleCn}</span>
      </div>
    );
  }

  return (
    <motion.div
      whileHover={{ scale: 1.02 }}
      onClick={(e) => {
        e.stopPropagation();
        onClick(task);
      }}
      className={cn(
        "p-2 rounded-lg cursor-pointer transition-all border-l-2",
        status.bg,
        priorityColors[task.priority],
        isSelected && "ring-2 ring-primary",
        isOverdue && "ring-1 ring-red-500",
      )}
    >
      <div className="flex items-center gap-1.5 mb-1">
        <StatusIcon className={cn("w-3 h-3", status.color)} />
        <span className="text-xs text-white font-medium truncate">
          {task.titleCn}
        </span>
      </div>
      <div className="text-[10px] text-slate-400 truncate">
        {task.projectName} · {task.machineNo}
      </div>
      {isOverdue && (
        <div className="flex items-center gap-1 mt-1 text-[10px] text-red-400">
          <AlertTriangle className="w-2.5 h-2.5" />
          已逾期
        </div>
      )}
    </motion.div>
  );
}

// Day Cell Component
function DayCell({
  date,
  tasks,
  isCurrentMonth,
  isToday,
  onTaskClick,
  selectedTaskId,
  viewMode,
}) {
  const dayTasks = tasks.filter((task) => {
    const start = parseDate(task.plannedStart);
    const end = parseDate(task.plannedEnd);
    return isDateInRange(date, start, end);
  });

  // Tasks that start on this day
  const startingTasks = dayTasks.filter((task) =>
    isSameDay(parseDate(task.plannedStart), date),
  );

  // Tasks that are due on this day
  const dueTasks = dayTasks.filter(
    (task) =>
      isSameDay(parseDate(task.plannedEnd), date) &&
      task.status !== "completed",
  );

  const isWeekend = date.getDay() === 0 || date.getDay() === 6;

  return (
    <div
      className={cn(
        "min-h-[100px] border border-border/30 p-1 transition-colors",
        !isCurrentMonth && "bg-surface-2/30",
        isToday && "bg-primary/5 border-primary/30",
        isWeekend && isCurrentMonth && "bg-slate-800/30",
      )}
    >
      {/* Date Header */}
      <div className="flex items-center justify-between mb-1">
        <span
          className={cn(
            "text-sm font-medium px-1.5 py-0.5 rounded",
            isToday && "bg-primary text-white",
            !isCurrentMonth && "text-slate-600",
            isCurrentMonth && !isToday && "text-slate-300",
          )}
        >
          {date.getDate()}
        </span>
        {dueTasks.length > 0 && (
          <Badge
            variant="outline"
            className="text-[10px] text-amber-400 border-amber-500/30 bg-amber-500/10"
          >
            {dueTasks.length} 到期
          </Badge>
        )}
      </div>

      {/* Tasks */}
      <div className="space-y-1">
        {viewMode === "month" ? (
          // Compact view for month
          <>
            {startingTasks.slice(0, 2).map((task) => (
              <TaskBlock
                key={task.id}
                task={task}
                onClick={onTaskClick}
                isSelected={selectedTaskId === task.id}
                compact
              />
            ))}
            {startingTasks.length > 2 && (
              <div className="text-[10px] text-slate-500 text-center">
                +{startingTasks.length - 2} 更多
              </div>
            )}
          </>
        ) : (
          // Detailed view for week
          dayTasks
            .slice(0, 3)
            .map((task) => (
              <TaskBlock
                key={task.id}
                task={task}
                onClick={onTaskClick}
                isSelected={selectedTaskId === task.id}
              />
            ))
        )}
        {viewMode === "week" && dayTasks.length > 3 && (
          <div className="text-[10px] text-slate-500 text-center">
            +{dayTasks.length - 3} 更多
          </div>
        )}
      </div>
    </div>
  );
}

// Main CalendarView Component
export default function CalendarView({ tasks, onTaskSelect, selectedTaskId }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState("month");

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Generate calendar days
  const calendarDays = useMemo(() => {
    if (viewMode === "month") {
      const daysInMonth = getDaysInMonth(year, month);
      const firstDay = getFirstDayOfMonth(year, month);
      const days = [];

      // Previous month days
      const prevMonthDays = getDaysInMonth(year, month - 1);
      for (let i = firstDay - 1; i >= 0; i--) {
        days.push({
          date: new Date(year, month - 1, prevMonthDays - i),
          isCurrentMonth: false,
        });
      }

      // Current month days
      for (let i = 1; i <= daysInMonth; i++) {
        days.push({
          date: new Date(year, month, i),
          isCurrentMonth: true,
        });
      }

      // Next month days
      const remainingDays = 42 - days.length; // 6 weeks
      for (let i = 1; i <= remainingDays; i++) {
        days.push({
          date: new Date(year, month + 1, i),
          isCurrentMonth: false,
        });
      }

      return days;
    } else {
      // Week view
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());

      return Array.from({ length: 7 }, (_, i) => {
        const date = new Date(startOfWeek);
        date.setDate(startOfWeek.getDate() + i);
        return {
          date,
          isCurrentMonth: date.getMonth() === month,
        };
      });
    }
  }, [year, month, currentDate, viewMode]);

  // Navigation handlers
  const goToPrevious = () => {
    if (viewMode === "month") {
      setCurrentDate(new Date(year, month - 1, 1));
    } else {
      const newDate = new Date(currentDate);
      newDate.setDate(currentDate.getDate() - 7);
      setCurrentDate(newDate);
    }
  };

  const goToNext = () => {
    if (viewMode === "month") {
      setCurrentDate(new Date(year, month + 1, 1));
    } else {
      const newDate = new Date(currentDate);
      newDate.setDate(currentDate.getDate() + 7);
      setCurrentDate(newDate);
    }
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  // Format header title
  const headerTitle = useMemo(() => {
    if (viewMode === "month") {
      return `${year}年${month + 1}月`;
    } else {
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);

      return `${startOfWeek.getMonth() + 1}月${startOfWeek.getDate()}日 - ${endOfWeek.getMonth() + 1}月${endOfWeek.getDate()}日`;
    }
  }, [year, month, currentDate, viewMode]);

  const today = new Date();

  return (
    <div className="bg-surface-1 rounded-xl border border-border overflow-hidden">
      {/* Header */}
      <div className="flex items-center justify-between p-4 border-b border-border bg-surface-2/50">
        <div className="flex items-center gap-4">
          {/* View Mode Toggle */}
          <div className="flex items-center gap-1 p-1 bg-surface-2 rounded-lg">
            {Object.values(VIEW_MODES).map((mode) => (
              <Button
                key={mode.id}
                variant={viewMode === mode.id ? "default" : "ghost"}
                size="sm"
                onClick={() => setViewMode(mode.id)}
              >
                {mode.label}
              </Button>
            ))}
          </div>

          {/* Navigation */}
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={goToPrevious}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-lg font-medium text-white min-w-[150px] text-center">
              {headerTitle}
            </span>
            <Button variant="ghost" size="sm" onClick={goToNext}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <Button variant="outline" size="sm" onClick={goToToday}>
          <Calendar className="w-4 h-4 mr-1" />
          今天
        </Button>
      </div>

      {/* Days of Week Header */}
      <div className="grid grid-cols-7 bg-surface-2/30">
        {DAYS_OF_WEEK.map((day, index) => (
          <div
            key={day}
            className={cn(
              "text-center py-2 text-sm font-medium border-b border-border/30",
              index === 0 || index === 6 ? "text-slate-500" : "text-slate-400",
            )}
          >
            {day}
          </div>
        ))}
      </div>

      {/* Calendar Grid */}
      <div
        className={cn(
          "grid grid-cols-7",
          viewMode === "week" ? "min-h-[400px]" : "",
        )}
      >
        <AnimatePresence mode="wait">
          {calendarDays.map((day) => (
            <motion.div
              key={formatDateKey(day.date)}
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.1 }}
            >
              <DayCell
                date={day.date}
                tasks={tasks}
                isCurrentMonth={day.isCurrentMonth}
                isToday={isSameDay(day.date, today)}
                onTaskClick={onTaskSelect}
                selectedTaskId={selectedTaskId}
                viewMode={viewMode}
              />
            </motion.div>
          ))}
        </AnimatePresence>
      </div>

      {/* Legend */}
      <div className="flex items-center gap-6 p-3 border-t border-border bg-surface-2/30 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-500/20 border-l-2 border-l-blue-400" />
          <span>进行中</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-slate-500/20 border-l-2 border-l-slate-400" />
          <span>待开始</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-emerald-500/20 border-l-2 border-l-emerald-400" />
          <span>已完成</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-red-500/20 border-l-2 border-l-red-400" />
          <span>已阻塞</span>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="text-[10px] text-amber-400 border-amber-500/30 bg-amber-500/10"
          >
            到期
          </Badge>
          <span>当日截止</span>
        </div>
      </div>
    </div>
  );
}
