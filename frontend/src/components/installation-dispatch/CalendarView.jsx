/**
 * CalendarView Component - Calendar-based task visualization for installation dispatch
 * 日历视图组件 - 基于日历的安装任务可视化
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
  Flag,
  MapPin,
  Users,
  Clock,
  Plus,
  Filter } from
"lucide-react";
import { Button, Badge } from "../../components/ui";
import { cn } from "../../lib/utils";
import {
  taskStatusConfigs as _taskStatusConfigs,
  priorityConfigs as _priorityConfigs,
  installationTypeConfigs as _installationTypeConfigs,
  formatDate as _formatDate,
  isTaskOverdue } from
"@/lib/constants/installationDispatch";

// View modes
const VIEW_MODES = {
  month: { id: "month", label: "月" },
  week: { id: "week", label: "周" },
  day: { id: "day", label: "日" }
};

// Days of week
const DAYS_OF_WEEK = ["日", "一", "二", "三", "四", "五", "六"];

// Status configuration
const statusConfig = {
  SCHEDULED: { icon: Circle, color: "text-blue-400", bg: "bg-blue-500/20" },
  IN_PROGRESS: { icon: PlayCircle, color: "text-green-400", bg: "bg-green-500/20" },
  ON_HOLD: { icon: PauseCircle, color: "text-yellow-400", bg: "bg-yellow-500/20" },
  COMPLETED: { icon: CheckCircle2, color: "text-emerald-400", bg: "bg-emerald-500/20" },
  CANCELLED: { icon: Circle, color: "text-slate-400", bg: "bg-slate-500/20" },
  DELAYED: { icon: AlertTriangle, color: "text-orange-400", bg: "bg-orange-500/20" }
};

// Priority colors
const priorityColors = {
  URGENT: "border-l-red-400 bg-red-500/20",
  HIGH: "border-l-amber-400 bg-amber-500/20",
  MEDIUM: "border-l-blue-400 bg-blue-500/20",
  LOW: "border-l-green-400 bg-green-500/20",
  NORMAL: "border-l-slate-400 bg-slate-500/20"
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
    date1.getDate() === date2.getDate());

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
  const priorityClass = priorityColors[task.priority] || priorityColors.NORMAL;
  const isOverdue = isTaskOverdue(task.status, task.planned_end_date);

  const _displayTitle = compact ?
  task.title :
  `${task.project_name || "无项目"} · ${task.machine_name || "无设备"}`;

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
          priorityClass,
          isSelected && "ring-1 ring-primary",
          isOverdue && "ring-1 ring-red-500"
        )}>

        <span className={cn("truncate", status.color)}>{task.title}</span>
      </div>);

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
        priorityClass,
        isSelected && "ring-2 ring-primary",
        isOverdue && "ring-1 ring-red-500"
      )}>

      <div className="flex items-center gap-1.5 mb-1">
        <StatusIcon className={cn("w-3 h-3", status.color)} />
        <span className="text-xs text-white font-medium truncate">
          {task.title}
        </span>
      </div>

      <div className="text-[10px] text-slate-400 space-y-1">
        <div className="flex items-center gap-1">
          <MapPin className="w-2.5 h-2.5" />
          <span className="truncate">{task.location || "无地点"}</span>
        </div>
        <div className="flex items-center gap-1">
          <Users className="w-2.5 h-2.5" />
          <span className="truncate">{task.assigned_engineer_name || "未分配"}</span>
        </div>
        {task.estimated_duration &&
        <div className="flex items-center gap-1">
            <Clock className="w-2.5 h-2.5" />
            <span>{task.estimated_duration}小时</span>
        </div>
        }
      </div>

      {isOverdue &&
      <div className="flex items-center gap-1 mt-1 text-[10px] text-red-400">
          <AlertTriangle className="w-2.5 h-2.5" />
          已逾期
      </div>
      }
    </motion.div>);

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
  onDateClick
}) {
  const dayTasks = tasks.filter((task) => {
    const start = parseDate(task.start_date || task.scheduled_date);
    const end = parseDate(task.end_date || task.scheduled_date);
    return isDateInRange(date, start, end);
  });

  // Tasks that start on this day
  const startingTasks = dayTasks.filter((task) => {
    const start = parseDate(task.start_date || task.scheduled_date);
    return isSameDay(start, date);
  });

  // Tasks that are due on this day
  const dueTasks = dayTasks.filter(
    (task) => {
      const end = parseDate(task.end_date || task.scheduled_date);
      return isSameDay(end, date) && task.status !== "COMPLETED";
    }
  );

  // Tasks with installation engineers available
  const assignedTasks = dayTasks.filter((task) => task.assigned_engineer_name);

  const isWeekend = date.getDay() === 0 || date.getDay() === 6;

  return (
    <div
      className={cn(
        "min-h-[120px] border border-border/30 p-1 transition-colors relative",
        !isCurrentMonth && "bg-slate-800/20",
        isToday && "bg-primary/5 border-primary/30",
        isWeekend && isCurrentMonth && "bg-slate-800/20",
        viewMode === "day" && "min-h-[400px]"
      )}
      onClick={() => onDateClick && onDateClick(date)}>

      {/* Date Header */}
      <div className="flex items-center justify-between mb-1">
        <span
          className={cn(
            "text-sm font-medium px-1.5 py-0.5 rounded cursor-pointer",
            isToday && "bg-primary text-white",
            !isCurrentMonth && "text-slate-600",
            isCurrentMonth && !isToday && "text-slate-300"
          )}>

          {date.getDate()}
        </span>

        <div className="flex gap-1">
          {dueTasks.length > 0 &&
          <Badge
            variant="outline"
            className="text-[10px] text-red-400 border-red-500/30 bg-red-500/10">

              {dueTasks.length}
          </Badge>
          }
          {assignedTasks.length > 0 && startingTasks.length > 0 &&
          <Badge
            variant="outline"
            className="text-[10px] text-green-400 border-green-500/30 bg-green-500/10">

              {assignedTasks.length}
          </Badge>
          }
        </div>
      </div>

      {/* Tasks */}
      <div className="space-y-1">
        {viewMode === "month" ?
        // Compact view for month
        <>
            {startingTasks.slice(0, 3).map((task) =>
          <TaskBlock
            key={task.id}
            task={task}
            onClick={onTaskClick}
            isSelected={selectedTaskId === task.id}
            compact />

          )}
            {startingTasks.length > 3 &&
          <div className="text-[10px] text-slate-500 text-center">
                +{startingTasks.length - 3} 更多
          </div>
          }
        </> :
        viewMode === "week" ?
        // Compact view for week
        <>
            {dayTasks.slice(0, 4).map((task) =>
          <TaskBlock
            key={task.id}
            task={task}
            onClick={onTaskClick}
            isSelected={selectedTaskId === task.id}
            compact />

          )}
            {dayTasks.length > 4 &&
          <div className="text-[10px] text-slate-500 text-center">
                +{dayTasks.length - 4} 更多
          </div>
          }
        </> :

        // Detailed view for day
        dayTasks.
        slice(0, 5).
        map((task) =>
        <TaskBlock
          key={task.id}
          task={task}
          onClick={onTaskClick}
          isSelected={selectedTaskId === task.id} />

        )
        }
        {viewMode === "week" && dayTasks.length > 4 &&
        <div className="text-[10px] text-slate-500 text-center">
            +{dayTasks.length - 4} 更多
        </div>
        }
        {viewMode === "day" && dayTasks.length > 5 &&
        <div className="text-[10px] text-slate-500 text-center">
            +{dayTasks.length - 5} 更多
        </div>
        }
      </div>
    </div>);

}

// Week View Component
function WeekView({ currentDate, tasks, onTaskClick, selectedTaskId: _selectedTaskId, onDateClick }) {
  const startOfWeek = new Date(currentDate);
  startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());

  const weekDays = Array.from({ length: 7 }, (_, i) => {
    const date = new Date(startOfWeek);
    date.setDate(startOfWeek.getDate() + i);
    return date;
  });

  const getTasksForDate = (date) => {
    return tasks.filter((task) => {
      const start = parseDate(task.start_date || task.scheduled_date);
      const end = parseDate(task.end_date || task.scheduled_date);
      return isDateInRange(date, start, end);
    });
  };

  return (
    <div className="space-y-3">
      {/* Day Headers */}
      <div className="grid grid-cols-7 gap-2">
        {weekDays.map((date) =>
        <div
          key={formatDateKey(date)}
          className="text-center p-2 bg-slate-800/50 rounded-lg">

            <div className="text-sm font-medium text-slate-400">
              {date.getMonth() + 1}/{date.getDate()}
            </div>
            <div className={`text-xs ${date.getDay() === 0 || date.getDay() === 6 ? "text-slate-500" : "text-slate-400"}`}>
              {DAYS_OF_WEEK[date.getDay()]}
            </div>
        </div>
        )}
      </div>

      {/* Time Slots */}
      <div className="space-y-2">
        {Array.from({ length: 9 }, (_, hour) => {
          const timeSlot = hour + 9; // 9 AM to 5 PM
          return (
            <div key={hour} className="grid grid-cols-7 gap-2">
              {weekDays.map((date) => {
                const hourTasks = getTasksForDate(date).filter((task) => {
                  if (!task.scheduled_date) {return false;}
                  const taskDate = parseDate(task.scheduled_date);
                  return (
                    isSameDay(taskDate, date) &&
                    task.scheduled_time === `${timeSlot}:00`);

                });

                return (
                  <div
                    key={`${formatDateKey(date)}-${timeSlot}`}
                    className="h-20 bg-slate-800/20 rounded border border-slate-700/30 relative"
                    onClick={() => onDateClick && onDateClick(date)}>

                    {hourTasks.slice(0, 1).map((task) =>
                    <div
                      key={task.id}
                      className="p-1 text-xs bg-blue-500/50 rounded cursor-pointer"
                      onClick={(e) => {
                        e.stopPropagation();
                        onTaskClick(task);
                      }}>

                        {task.title}
                    </div>
                    )}
                    {hourTasks.length > 1 &&
                    <div className="absolute bottom-1 right-1 text-[10px] text-slate-500">
                        +{hourTasks.length - 1}
                    </div>
                    }
                  </div>);

              })}
            </div>);

        })}
      </div>
    </div>);

}

// Main CalendarView Component
export default function CalendarView({
  tasks,
  onTaskSelect,
  selectedTaskId,
  onDateSelect,
  selectedDate: _selectedDate,
  onViewModeChange,
  initialViewMode = "month"
}) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [viewMode, setViewMode] = useState(initialViewMode);

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
          isCurrentMonth: false
        });
      }

      // Current month days
      for (let i = 1; i <= daysInMonth; i++) {
        days.push({
          date: new Date(year, month, i),
          isCurrentMonth: true
        });
      }

      // Next month days
      const remainingDays = 42 - days.length; // 6 weeks
      for (let i = 1; i <= remainingDays; i++) {
        days.push({
          date: new Date(year, month + 1, i),
          isCurrentMonth: false
        });
      }

      return days;
    } else if (viewMode === "week") {
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());

      return Array.from({ length: 7 }, (_, i) => {
        const date = new Date(startOfWeek);
        date.setDate(startOfWeek.getDate() + i);
        return {
          date,
          isCurrentMonth: date.getMonth() === month
        };
      });
    } else {
      // Day view
      return [
      {
        date: currentDate,
        isCurrentMonth: true
      }];

    }
  }, [year, month, currentDate, viewMode]);

  // Navigation handlers
  const goToPrevious = () => {
    if (viewMode === "month") {
      setCurrentDate(new Date(year, month - 1, 1));
    } else if (viewMode === "week") {
      const newDate = new Date(currentDate);
      newDate.setDate(currentDate.getDate() - 7);
      setCurrentDate(newDate);
    } else {
      const newDate = new Date(currentDate);
      newDate.setDate(currentDate.getDate() - 1);
      setCurrentDate(newDate);
    }
  };

  const goToNext = () => {
    if (viewMode === "month") {
      setCurrentDate(new Date(year, month + 1, 1));
    } else if (viewMode === "week") {
      const newDate = new Date(currentDate);
      newDate.setDate(currentDate.getDate() + 7);
      setCurrentDate(newDate);
    } else {
      const newDate = new Date(currentDate);
      newDate.setDate(currentDate.getDate() + 1);
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
    } else if (viewMode === "week") {
      const startOfWeek = new Date(currentDate);
      startOfWeek.setDate(currentDate.getDate() - currentDate.getDay());
      const endOfWeek = new Date(startOfWeek);
      endOfWeek.setDate(startOfWeek.getDate() + 6);

      return `${startOfWeek.getMonth() + 1}月${startOfWeek.getDate()}日 - ${endOfWeek.getMonth() + 1}月${endOfWeek.getDate()}日`;
    } else {
      return `${year}年${month + 1}月${currentDate.getDate()}日`;
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
            {Object.values(VIEW_MODES).map((mode) =>
            <Button
              key={mode.id}
              variant={viewMode === mode.id ? "default" : "ghost"}
              size="sm"
              onClick={() => {
                setViewMode(mode.id);
                if (onViewModeChange) {
                  onViewModeChange(mode.id);
                }
              }}>

                {mode.label}
            </Button>
            )}
          </div>

          {/* Navigation */}
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={goToPrevious}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-lg font-medium text-white min-w-[180px] text-center">
              {headerTitle}
            </span>
            <Button variant="ghost" size="sm" onClick={goToNext}>
              <ChevronRight className="w-4 h-4" />
            </Button>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Button variant="outline" size="sm" onClick={goToToday}>
            <Calendar className="w-4 h-4 mr-1" />
            今天
          </Button>
          {viewMode !== "month" &&
          <Button size="sm" onClick={() => setViewMode("month")}>
              <Plus className="w-4 h-4 mr-1" />
              新建任务
          </Button>
          }
        </div>
      </div>

      {/* Days of Week Header (Month/Week view) */}
      {viewMode !== "day" &&
      <div className="grid grid-cols-7 bg-surface-2/30">
          {DAYS_OF_WEEK.map((day, index) =>
        <div
          key={day}
          className={cn(
            "text-center py-2 text-sm font-medium border-b border-border/30",
            index === 0 || index === 6 ? "text-slate-500" : "text-slate-400"
          )}>

              {day}
        </div>
        )}
      </div>
      }

      {/* Calendar Grid */}
      {viewMode === "week" ?
      <WeekView
        currentDate={currentDate}
        tasks={tasks}
        onTaskClick={onTaskSelect}
        selectedTaskId={selectedTaskId}
        onDateClick={onDateSelect} /> :


      <div
        className={cn(
          "grid grid-cols-7",
          viewMode === "day" ? "min-h-[400px]" : ""
        )}>

          <AnimatePresence mode="wait">
            {calendarDays.map((day) =>
          <motion.div
            key={formatDateKey(day.date)}
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.1 }}>

                <DayCell
              date={day.date}
              tasks={tasks}
              isCurrentMonth={day.isCurrentMonth}
              isToday={isSameDay(day.date, today)}
              onTaskClick={onTaskSelect}
              selectedTaskId={selectedTaskId}
              viewMode={viewMode}
              onDateClick={onDateSelect} />

          </motion.div>
          )}
          </AnimatePresence>
      </div>
      }

      {/* Legend */}
      <div className="flex items-center gap-6 p-3 border-t border-border bg-surface-2/30 text-xs text-slate-400">
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-blue-500/20 border-l-2 border-l-blue-400" />
          <span>已安排</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-green-500/20 border-l-2 border-l-green-400" />
          <span>进行中</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-yellow-500/20 border-l-2 border-l-yellow-400" />
          <span>暂停</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-3 rounded bg-emerald-500/20 border-l-2 border-l-emerald-400" />
          <span>已完成</span>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="text-[10px] text-red-400 border-red-500/30 bg-red-500/10">

            逾期
          </Badge>
          <span>逾期任务</span>
        </div>
        <div className="flex items-center gap-2">
          <Badge
            variant="outline"
            className="text-[10px] text-green-400 border-green-500/30 bg-green-500/10">

            已分配
          </Badge>
          <span>有工程师</span>
        </div>
      </div>
    </div>);

}