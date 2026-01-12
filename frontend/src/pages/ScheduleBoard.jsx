import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import {
  Calendar,
  Clock,
  AlertTriangle,
  ChevronLeft,
  ChevronRight,
  Filter,
  Users,
  Package,
  Zap,
  ExternalLink,
  ZoomIn,
  ZoomOut,
} from "lucide-react";
import { PageHeader } from "../components/layout";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "../components/ui/card";
import { Button } from "../components/ui/button";
import { Badge } from "../components/ui/badge";
import { Progress } from "../components/ui/progress";
import { cn } from "../lib/utils";
import { fadeIn, staggerContainer } from "../lib/animations";
import {
  projectApi,
  milestoneApi,
  progressApi,
  productionApi,
  workloadApi,
} from "../services/api";

// Mock schedule data
// Mock data - 已移除，使用真实API
const stageColors = {
  S1: "bg-slate-500",
  S2: "bg-blue-500",
  S3: "bg-cyan-500",
  S4: "bg-purple-500",
  S5: "bg-amber-500",
  S6: "bg-emerald-500",
  S7: "bg-green-500",
  S8: "bg-teal-500",
  S9: "bg-slate-400",
};

const healthColors = {
  H1: { bg: "bg-emerald-500/20", text: "text-emerald-400", label: "正常" },
  H2: { bg: "bg-amber-500/20", text: "text-amber-400", label: "风险" },
  H3: { bg: "bg-red-500/20", text: "text-red-400", label: "阻塞" },
  H4: { bg: "bg-slate-500/20", text: "text-slate-400", label: "完结" },
};

const milestoneStatusColors = {
  completed: "bg-emerald-500",
  in_progress: "bg-blue-500",
  pending: "bg-slate-500",
  delayed: "bg-red-500",
  at_risk: "bg-amber-500",
};

function ProjectCard({ project }) {
  const health = healthColors[project.health];

  return (
    <motion.div
      whileHover={{ scale: 1.01 }}
      className="bg-surface-1 rounded-xl border border-border overflow-hidden"
    >
      {/* Header */}
      <div className="p-4 border-b border-border/50">
        <div className="flex items-start justify-between mb-2">
          <div>
            <div className="flex items-center gap-2 mb-1">
              <span className="font-mono text-xs text-accent">
                {project.id}
              </span>
              <Badge className={cn("text-[10px]", stageColors[project.stage])}>
                {project.stageName}
              </Badge>
            </div>
            <h3 className="font-semibold text-white">{project.name}</h3>
            <p className="text-sm text-slate-400">{project.customer}</p>
          </div>
          <div
            className={cn(
              "px-2 py-1 rounded-lg text-xs font-medium",
              health.bg,
              health.text,
            )}
          >
            {health.label}
          </div>
        </div>

        {/* Progress */}
        <div className="mt-3">
          <div className="flex items-center justify-between text-sm mb-1">
            <span className="text-slate-400">整体进度</span>
            <span className="text-white font-medium">{project.progress}%</span>
          </div>
          <Progress value={project.progress} className="h-2" />
        </div>

        {/* Time Info */}
        <div className="flex items-center gap-4 mt-3 text-xs text-slate-400">
          <span className="flex items-center gap-1">
            <Calendar className="w-3 h-3" />
            {project.planEnd}
          </span>
          <span className="flex items-center gap-1">
            <Clock className="w-3 h-3" />
            剩余 {project.daysRemaining} 天
          </span>
        </div>
      </div>

      {/* Milestones Timeline */}
      <div className="p-4 bg-surface-0/50">
        <div className="text-xs font-medium text-slate-400 mb-3">
          关键里程碑
        </div>
        <div className="relative">
          {/* Timeline line */}
          <div className="absolute left-[5px] top-2 bottom-2 w-0.5 bg-border" />

          <div className="space-y-3">
            {project.milestones.map((milestone, index) => (
              <div key={index} className="flex items-start gap-3 relative">
                <div
                  className={cn(
                    "w-3 h-3 rounded-full mt-0.5 z-10",
                    milestoneStatusColors[milestone.status],
                  )}
                />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center justify-between">
                    <span className="text-sm text-white truncate">
                      {milestone.name}
                    </span>
                    <span className="text-xs text-slate-500">
                      {milestone.date}
                    </span>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Alerts */}
      {project.alerts && project.alerts.length > 0 && (
        <div className="p-3 bg-red-500/10 border-t border-red-500/20">
          <div className="flex items-start gap-2">
            <AlertTriangle className="w-4 h-4 text-red-400 shrink-0 mt-0.5" />
            <div className="text-xs text-red-300">
              {project.alerts.map((alert, i) => (
                <div key={i}>{alert}</div>
              ))}
            </div>
          </div>
        </div>
      )}

      {/* Resources */}
      <div className="p-3 border-t border-border/50">
        <div className="flex items-center justify-between">
          <div className="flex -space-x-2">
            {project.resources.map((resource, index) => (
              <div
                key={index}
                className="w-7 h-7 rounded-full bg-gradient-to-br from-accent to-purple-500 flex items-center justify-center text-[10px] font-medium text-white border-2 border-surface-1"
                title={`${resource.name} (${resource.role}) - 负荷${resource.load}%`}
              >
                {resource.name[0]}
              </div>
            ))}
          </div>
          <Button variant="ghost" size="sm" className="h-7 text-xs">
            <ExternalLink className="w-3 h-3 mr-1" />
            详情
          </Button>
        </div>
      </div>
    </motion.div>
  );
}

function StageColumn({ stage, stageName, projects }) {
  const stageProjects = projects.filter((p) => p.stage === stage);
  const stageColor = stageColors[stage];

  return (
    <div className="min-w-[320px] max-w-[320px]">
      {/* Column Header */}
      <div className="flex items-center gap-2 mb-4 px-2">
        <div className={cn("w-3 h-3 rounded-full", stageColor)} />
        <h3 className="font-semibold text-white">{stageName}</h3>
        <Badge variant="secondary" className="ml-auto">
          {stageProjects.length}
        </Badge>
      </div>

      {/* Projects */}
      <div className="space-y-4">
        {stageProjects.length > 0 ? (
          stageProjects.map((project) => (
            <ProjectCard key={project.id} project={project} />
          ))
        ) : (
          <div className="p-8 text-center text-slate-500 border border-dashed border-border rounded-xl">
            暂无项目
          </div>
        )}
      </div>
    </div>
  );
}

// Calendar View Component
function ScheduleCalendarView({ projects, onProjectClick }) {
  const [currentDate, setCurrentDate] = useState(new Date());
  const [calendarData, setCalendarData] = useState([]);
  const [loading, setLoading] = useState(true);

  const year = currentDate.getFullYear();
  const month = currentDate.getMonth();

  // Fetch calendar data
  useEffect(() => {
    const fetchCalendarData = async () => {
      try {
        setLoading(true);
        const startDate = new Date(year, month, 1);
        const endDate = new Date(year, month + 1, 0);

        const response = await productionApi.productionPlans.calendar({
          start_date: startDate.toISOString().split("T")[0],
          end_date: endDate.toISOString().split("T")[0],
        });

        const data = response.data || response;
        setCalendarData(data.calendar || []);
      } catch (err) {
        console.error("Failed to fetch calendar data:", err);
        setCalendarData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchCalendarData();
  }, [year, month]);

  // Get days in month
  const getDaysInMonth = (year, month) => {
    return new Date(year, month + 1, 0).getDate();
  };

  const getFirstDayOfMonth = (year, month) => {
    return new Date(year, month, 1).getDay();
  };

  const formatDateKey = (date) => {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
  };

  const isSameDay = (date1, date2) => {
    if (!date1 || !date2) return false;
    return (
      date1.getFullYear() === date2.getFullYear() &&
      date1.getMonth() === date2.getMonth() &&
      date1.getDate() === date2.getDate()
    );
  };

  // Generate calendar days
  const calendarDays = useMemo(() => {
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
    const remainingDays = 42 - days.length;
    for (let i = 1; i <= remainingDays; i++) {
      days.push({
        date: new Date(year, month + 1, i),
        isCurrentMonth: false,
      });
    }

    return days;
  }, [year, month]);

  // Get events for a date
  const getEventsForDate = (date) => {
    const dateKey = formatDateKey(date);
    const dayData = calendarData.find((d) => d.date === dateKey);
    if (!dayData) return [];

    return [
      ...(dayData.plans || []).map((p) => ({ ...p, type: "plan" })),
      ...(dayData.work_orders || []).map((w) => ({ ...w, type: "work_order" })),
    ];
  };

  const goToPrevious = () => {
    setCurrentDate(new Date(year, month - 1, 1));
  };

  const goToNext = () => {
    setCurrentDate(new Date(year, month + 1, 1));
  };

  const goToToday = () => {
    setCurrentDate(new Date());
  };

  const today = new Date();

  return (
    <Card className="bg-surface-1/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            排产日历
          </CardTitle>
          <div className="flex items-center gap-2">
            <Button variant="ghost" size="sm" onClick={goToPrevious}>
              <ChevronLeft className="w-4 h-4" />
            </Button>
            <span className="text-lg font-medium text-white min-w-[150px] text-center">
              {year}年{month + 1}月
            </span>
            <Button variant="ghost" size="sm" onClick={goToNext}>
              <ChevronRight className="w-4 h-4" />
            </Button>
            <Button variant="outline" size="sm" onClick={goToToday}>
              今天
            </Button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-slate-400">加载中...</div>
          </div>
        ) : (
          <>
            {/* Days of Week Header */}
            <div className="grid grid-cols-7 bg-surface-2/30 border-b border-border">
              {["日", "一", "二", "三", "四", "五", "六"].map((day) => (
                <div
                  key={day}
                  className="text-center py-2 text-sm font-medium text-slate-400"
                >
                  {day}
                </div>
              ))}
            </div>

            {/* Calendar Grid */}
            <div className="grid grid-cols-7">
              {calendarDays.map((day) => {
                const events = getEventsForDate(day.date);
                const isToday = isSameDay(day.date, today);
                const isWeekend =
                  day.date.getDay() === 0 || day.date.getDay() === 6;

                return (
                  <div
                    key={formatDateKey(day.date)}
                    className={cn(
                      "min-h-[120px] border border-border/30 p-2 transition-colors",
                      !day.isCurrentMonth && "bg-surface-2/30",
                      isToday && "bg-primary/10 border-primary/30",
                      isWeekend && day.isCurrentMonth && "bg-slate-800/30",
                    )}
                  >
                    <div className="flex items-center justify-between mb-1">
                      <span
                        className={cn(
                          "text-sm font-medium px-1.5 py-0.5 rounded",
                          isToday && "bg-primary text-white",
                          !day.isCurrentMonth && "text-slate-600",
                          day.isCurrentMonth && !isToday && "text-slate-300",
                        )}
                      >
                        {day.date.getDate()}
                      </span>
                      {events.length > 0 && (
                        <Badge variant="outline" className="text-[10px]">
                          {events.length}
                        </Badge>
                      )}
                    </div>

                    <div className="space-y-1">
                      {events.slice(0, 3).map((event, idx) => (
                        <div
                          key={idx}
                          onClick={() =>
                            onProjectClick && onProjectClick(event)
                          }
                          className={cn(
                            "px-1.5 py-0.5 rounded text-xs truncate cursor-pointer transition-all",
                            event.type === "plan"
                              ? "bg-blue-500/20 text-blue-400 border-l-2 border-l-blue-400"
                              : "bg-purple-500/20 text-purple-400 border-l-2 border-l-purple-400",
                          )}
                          title={
                            event.plan_name || event.task_name || event.order_no
                          }
                        >
                          {event.plan_name || event.task_name || event.order_no}
                        </div>
                      ))}
                      {events.length > 3 && (
                        <div className="text-[10px] text-slate-500 text-center">
                          +{events.length - 3} 更多
                        </div>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          </>
        )}
      </CardContent>
    </Card>
  );
}

// Gantt View Component
function ScheduleGanttView({ projects, onProjectClick }) {
  const [ganttData, setGanttData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [zoom, setZoom] = useState("week");
  const [scrollLeft, setScrollLeft] = useState(0);

  const ZOOM_LEVELS = {
    day: { dayWidth: 60 },
    week: { dayWidth: 30 },
    month: { dayWidth: 12 },
  };

  const zoomConfig = ZOOM_LEVELS[zoom];
  const { dayWidth } = zoomConfig;

  // Fetch gantt data
  useEffect(() => {
    const fetchGanttData = async () => {
      try {
        setLoading(true);
        const today = new Date();
        const startDate = new Date(today.getFullYear(), today.getMonth(), 1);
        const endDate = new Date(today.getFullYear(), today.getMonth() + 1, 0);

        const response = await workloadApi.gantt({
          start_date: startDate.toISOString().split("T")[0],
          end_date: endDate.toISOString().split("T")[0],
        });

        const data = response.data || response;
        setGanttData(data.resources || []);
      } catch (err) {
        console.error("Failed to fetch gantt data:", err);
        setGanttData([]);
      } finally {
        setLoading(false);
      }
    };
    fetchGanttData();
  }, []);

  // Calculate date range
  const dateRange = useMemo(() => {
    if (ganttData.length === 0) {
      const today = new Date();
      return {
        start: new Date(today.getFullYear(), today.getMonth(), 1),
        end: new Date(today.getFullYear(), today.getMonth() + 1, 0),
      };
    }

    let minDate = null;
    let maxDate = null;

    ganttData.forEach((resource) => {
      resource.tasks?.forEach((task) => {
        const start = new Date(task.start_date);
        const end = new Date(task.end_date);
        if (!minDate || start < minDate) minDate = start;
        if (!maxDate || end > maxDate) maxDate = end;
      });
    });

    return {
      start: minDate || new Date(),
      end: maxDate || new Date(),
    };
  }, [ganttData]);

  const getDaysBetween = (start, end) => {
    return Math.ceil((end - start) / (1000 * 60 * 60 * 24));
  };

  const addDays = (date, days) => {
    const result = new Date(date);
    result.setDate(result.getDate() + days);
    return result;
  };

  const totalDays = getDaysBetween(dateRange.start, dateRange.end);
  const totalWidth = totalDays * dayWidth;

  // Generate date headers
  const dateHeaders = useMemo(() => {
    const headers = [];
    let currentDate = new Date(dateRange.start);

    while (currentDate <= dateRange.end) {
      headers.push({
        date: new Date(currentDate),
        label: currentDate.getDate(),
        isToday: currentDate.toDateString() === new Date().toDateString(),
        isWeekend: currentDate.getDay() === 0 || currentDate.getDay() === 6,
      });
      currentDate = addDays(currentDate, 1);
    }

    return headers;
  }, [dateRange]);

  const getTaskPosition = (task) => {
    const startDate = new Date(task.start_date);
    const endDate = new Date(task.end_date);
    const startOffset = getDaysBetween(dateRange.start, startDate) * dayWidth;
    const duration = getDaysBetween(startDate, endDate) + 1;
    const width = duration * dayWidth;

    return { startOffset, width };
  };

  const todayOffset = useMemo(() => {
    const today = new Date();
    if (today < dateRange.start || today > dateRange.end) return null;
    return getDaysBetween(dateRange.start, today) * dayWidth;
  }, [dateRange, dayWidth]);

  const handleZoomIn = () => {
    if (zoom === "month") setZoom("week");
    else if (zoom === "week") setZoom("day");
  };

  const handleZoomOut = () => {
    if (zoom === "day") setZoom("week");
    else if (zoom === "week") setZoom("month");
  };

  return (
    <Card className="bg-surface-1/50">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Calendar className="w-5 h-5" />
            排产甘特图
          </CardTitle>
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
              {zoom === "day"
                ? "日视图"
                : zoom === "week"
                  ? "周视图"
                  : "月视图"}
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
        </div>
      </CardHeader>
      <CardContent>
        {loading ? (
          <div className="flex items-center justify-center h-96">
            <div className="text-slate-400">加载中...</div>
          </div>
        ) : (
          <div className="overflow-x-auto">
            {/* Date Headers */}
            <div
              className="flex border-b border-border bg-surface-2/30"
              style={{ marginLeft: "200px" }}
            >
              {dateHeaders.map((header, index) => (
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

            {/* Chart Body */}
            <div className="flex">
              {/* Resource Names Column */}
              <div className="w-[200px] flex-shrink-0 border-r border-border bg-surface-2/20">
                {ganttData.map((resource) => (
                  <div
                    key={resource.user_id}
                    className="h-12 px-3 flex items-center border-b border-border/50"
                  >
                    <span className="text-sm text-white truncate">
                      {resource.user_name}
                    </span>
                    {resource.dept_name && (
                      <span className="text-xs text-slate-500 ml-2">
                        ({resource.dept_name})
                      </span>
                    )}
                  </div>
                ))}
                {ganttData.length === 0 && (
                  <div className="h-32 flex items-center justify-center">
                    <span className="text-sm text-slate-500">暂无数据</span>
                  </div>
                )}
              </div>

              {/* Timeline Area */}
              <div
                className="flex-1 relative"
                style={{ minHeight: `${ganttData.length * 48}px` }}
              >
                {/* Grid Background */}
                <div className="absolute inset-0 flex pointer-events-none">
                  {dateHeaders.map((header, index) => (
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

                {/* Task Bars */}
                {ganttData.map((resource, resourceIndex) => (
                  <div
                    key={resource.user_id}
                    className="relative h-12 border-b border-border/50"
                  >
                    {resource.tasks?.map((task) => {
                      const { startOffset, width } = getTaskPosition(task);
                      const statusColors = {
                        PENDING: {
                          bg: "bg-slate-600",
                          progress: "bg-slate-400",
                        },
                        IN_PROGRESS: {
                          bg: "bg-blue-900/50",
                          progress: "bg-blue-500",
                        },
                        BLOCKED: {
                          bg: "bg-red-900/50",
                          progress: "bg-red-500",
                        },
                        COMPLETED: {
                          bg: "bg-emerald-900/50",
                          progress: "bg-emerald-500",
                        },
                      };
                      const colors =
                        statusColors[task.status] || statusColors.PENDING;

                      return (
                        <motion.div
                          key={task.task_id}
                          initial={{ opacity: 0, scaleX: 0 }}
                          animate={{ opacity: 1, scaleX: 1 }}
                          onClick={() => onProjectClick && onProjectClick(task)}
                          className={cn(
                            "absolute h-8 rounded-md cursor-pointer transition-all border",
                            colors.bg,
                            "border-blue-500/50",
                          )}
                          style={{
                            left: `${startOffset}px`,
                            width: `${Math.max(width, dayWidth)}px`,
                            top: "50%",
                            transform: "translateY(-50%)",
                          }}
                        >
                          <div
                            className={cn("h-full rounded-md", colors.progress)}
                            style={{ width: `${task.progress || 0}%` }}
                          />
                          <div className="absolute inset-0 flex items-center px-2 overflow-hidden">
                            <span className="text-xs font-medium text-white truncate">
                              {task.task_name}
                            </span>
                          </div>
                        </motion.div>
                      );
                    })}
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export default function ScheduleBoard() {
  const [viewMode, setViewMode] = useState("kanban"); // kanban | gantt | calendar
  const [projects, setProjects] = useState([]);
  const [loading, setLoading] = useState(true);

  const stages = [
    { stage: "S3", name: "采购备料" },
    { stage: "S4", name: "加工制造" },
    { stage: "S5", name: "装配调试" },
    { stage: "S6", name: "FAT验收" },
  ];

  const getStageName = (stage) => {
    const stageNames = {
      S1: "需求进入",
      S2: "方案设计",
      S3: "采购备料",
      S4: "加工制造",
      S5: "装配调试",
      S6: "FAT验收",
      S7: "包装发运",
      S8: "SAT验收",
      S9: "质保结项",
    };
    return stageNames[stage] || stage;
  };

  useEffect(() => {
    const fetchProjects = async () => {
      try {
        setLoading(true);
        const response = await projectApi.list({ page_size: 100 });
        // Handle PaginatedResponse format
        const data = response.data || response;
        const projectList = data.items || data || [];

        // Transform backend project format to frontend format and load milestones/resources
        const transformedProjects = await Promise.all(
          projectList.map(async (p) => {
            const projectId = p.id || p.project_code;

            // Load milestones for this project
            let milestones = [];
            try {
              const milestonesRes = await milestoneApi.list(projectId);
              const milestonesData = milestonesRes.data || milestonesRes || [];
              milestones = milestonesData.map((m) => ({
                name: m.milestone_name || m.name || "",
                date: m.plan_date || m.planned_date || "",
                status:
                  m.status === "COMPLETED"
                    ? "completed"
                    : m.status === "IN_PROGRESS"
                      ? "in_progress"
                      : "pending",
              }));
            } catch (err) {
              console.error(
                `Failed to load milestones for project ${projectId}:`,
                err,
              );
            }

            // Load resources/workload for this project
            let resources = [];
            try {
              // Try to get project progress summary which may include resource info
              const progressRes = await progressApi.reports
                .getSummary(projectId)
                .catch(() => null);
              if (progressRes?.data) {
                // Extract resource info if available
                // This is a placeholder - adjust based on actual API response structure
                resources = [];
              }
            } catch (err) {
              console.error(
                `Failed to load resources for project ${projectId}:`,
                err,
              );
            }

            return {
              id: p.project_code || p.id,
              name: p.project_name,
              customer: p.customer_name || "未知客户",
              stage: p.stage || "S1",
              stageName: getStageName(p.stage),
              progress: p.progress_pct || 0,
              health: p.health || "H1",
              planStart: p.planned_start_date || "",
              planEnd: p.planned_end_date || "",
              daysRemaining: p.planned_end_date
                ? Math.ceil(
                    (new Date(p.planned_end_date) - new Date()) /
                      (1000 * 60 * 60 * 24),
                  )
                : 0,
              milestones,
              resources,
            };
          }),
        );

        setProjects(transformedProjects);
      } catch (err) {
        console.error("Failed to fetch projects:", err);
        setProjects([]);
      } finally {
        setLoading(false);
      }
    };
    fetchProjects();
  }, []);

  const totalProjects = projects.length;
  const atRiskProjects = projects.filter((p) => p.health === "H2").length;
  const blockedProjects = projects.filter((p) => p.health === "H3").length;

  return (
    <motion.div
      variants={staggerContainer}
      initial="hidden"
      animate="visible"
      className="space-y-6"
    >
      <PageHeader
        title="排期看板"
        description="PMC视角的项目进度与资源协调中心"
      />

      {/* Summary Stats */}
      <motion.div
        variants={fadeIn}
        className="grid grid-cols-2 md:grid-cols-4 gap-4"
      >
        {[
          {
            label: "在制项目",
            value: totalProjects,
            icon: Package,
            color: "text-blue-400",
          },
          {
            label: "风险项目",
            value: atRiskProjects,
            icon: AlertTriangle,
            color: "text-amber-400",
          },
          {
            label: "阻塞项目",
            value: blockedProjects,
            icon: Zap,
            color: "text-red-400",
          },
          {
            label: "资源占用",
            value: "85%",
            icon: Users,
            color: "text-emerald-400",
          },
        ].map((stat, index) => (
          <Card key={index} className="bg-surface-1/50">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-slate-400">{stat.label}</p>
                  <p className="text-2xl font-bold text-white mt-1">
                    {stat.value}
                  </p>
                </div>
                <stat.icon className={cn("w-8 h-8", stat.color)} />
              </div>
            </CardContent>
          </Card>
        ))}
      </motion.div>

      {/* View Controls */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardContent className="p-4">
            <div className="flex items-center justify-between">
              {/* View Mode Toggle */}
              <div className="flex items-center gap-2">
                {[
                  { id: "kanban", label: "看板" },
                  { id: "gantt", label: "甘特图" },
                  { id: "calendar", label: "日历" },
                ].map((mode) => (
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

              {/* Filters */}
              <div className="flex items-center gap-2">
                <Button variant="outline" size="sm">
                  <Filter className="w-4 h-4 mr-1" />
                  筛选
                </Button>
                <Button variant="outline" size="sm">
                  <Users className="w-4 h-4 mr-1" />
                  资源
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>
      </motion.div>

      {/* Kanban Board */}
      {viewMode === "kanban" && (
        <motion.div variants={fadeIn} className="overflow-x-auto pb-4">
          <div className="flex gap-6 min-w-max">
            {stages.map(({ stage, name }) => (
              <StageColumn
                key={stage}
                stage={stage}
                stageName={name}
                projects={projects}
              />
            ))}
          </div>
        </motion.div>
      )}

      {/* Gantt View */}
      {viewMode === "gantt" && (
        <motion.div variants={fadeIn}>
          <ScheduleGanttView
            projects={projects}
            onProjectClick={(task) => {
              if (task.project_id) {
                window.open(`/projects/${task.project_id}`, "_blank");
              }
            }}
          />
        </motion.div>
      )}

      {/* Calendar View */}
      {viewMode === "calendar" && (
        <motion.div variants={fadeIn}>
          <ScheduleCalendarView
            projects={projects}
            onProjectClick={(event) => {
              if (event.plan_id) {
                // Navigate to production plan or project
                console.log("Clicked plan:", event);
              }
            }}
          />
        </motion.div>
      )}

      {/* Resource Heat Map */}
      <motion.div variants={fadeIn}>
        <Card className="bg-surface-1/50">
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Users className="w-5 h-5" />
              资源负荷热力图
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-7 gap-2 mb-4">
              {["周一", "周二", "周三", "周四", "周五", "周六", "周日"].map(
                (day) => (
                  <div key={day} className="text-center text-xs text-slate-500">
                    {day}
                  </div>
                ),
              )}
            </div>
            <div className="space-y-2">
              {[
                { name: "张工 (ME)", loads: [100, 100, 80, 100, 60, 0, 0] },
                { name: "李工 (EE)", loads: [80, 100, 100, 80, 80, 40, 0] },
                { name: "王工 (SW)", loads: [60, 60, 80, 100, 100, 0, 0] },
                { name: "陈工 (TE)", loads: [40, 60, 80, 100, 80, 60, 0] },
              ].map((engineer, index) => (
                <div key={index} className="flex items-center gap-2">
                  <div className="w-24 text-sm text-slate-400 truncate">
                    {engineer.name}
                  </div>
                  <div className="flex-1 grid grid-cols-7 gap-1">
                    {engineer.loads.map((load, i) => (
                      <div
                        key={i}
                        className={cn(
                          "h-8 rounded flex items-center justify-center text-xs font-medium",
                          load === 0
                            ? "bg-slate-800 text-slate-500"
                            : load <= 60
                              ? "bg-emerald-500/30 text-emerald-400"
                              : load <= 80
                                ? "bg-amber-500/30 text-amber-400"
                                : "bg-red-500/30 text-red-400",
                        )}
                      >
                        {load > 0 ? `${load}%` : "-"}
                      </div>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </motion.div>
    </motion.div>
  );
}
