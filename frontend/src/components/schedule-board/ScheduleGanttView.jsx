import { useState, useEffect, useMemo } from "react";
import { motion } from "framer-motion";
import { Calendar, ZoomIn, ZoomOut } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "../../components/ui/card";
import { Button } from "../../components/ui/button";
import { cn } from "../../lib/utils";
import { workloadApi } from "../../services/api";

export default function ScheduleGanttView({ projects: _projects, onProjectClick }) {
  const [ganttData, setGanttData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [zoom, setZoom] = useState("week");
  const [_scrollLeft, _setScrollLeft] = useState(0);

  const ZOOM_LEVELS = {
    day: { dayWidth: 60 },
    week: { dayWidth: 30 },
    month: { dayWidth: 12 }
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
          end_date: endDate.toISOString().split("T")[0]
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
        end: new Date(today.getFullYear(), today.getMonth() + 1, 0)
      };
    }

    let minDate = null;
    let maxDate = null;

    (ganttData || []).forEach((resource) => {
      resource.tasks?.forEach((task) => {
        const start = new Date(task.start_date);
        const end = new Date(task.end_date);
        if (!minDate || start < minDate) {minDate = start;}
        if (!maxDate || end > maxDate) {maxDate = end;}
      });
    });

    return {
      start: minDate || new Date(),
      end: maxDate || new Date()
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
  const _totalWidth = totalDays * dayWidth;

  // Generate date headers
  const dateHeaders = useMemo(() => {
    const headers = [];
    let currentDate = new Date(dateRange.start);

    while (currentDate <= dateRange.end) {
      headers.push({
        date: new Date(currentDate),
        label: currentDate.getDate(),
        isToday: currentDate.toDateString() === new Date().toDateString(),
        isWeekend: currentDate.getDay() === 0 || currentDate.getDay() === 6
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
    if (today < dateRange.start || today > dateRange.end) {return null;}
    return getDaysBetween(dateRange.start, today) * dayWidth;
  }, [dateRange, dayWidth]);

  const handleZoomIn = () => {
    if (zoom === "month") {setZoom("week");}
    else if (zoom === "week") {setZoom("day");}
  };

  const handleZoomOut = () => {
    if (zoom === "day") {setZoom("week");}
    else if (zoom === "week") {setZoom("month");}
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
              {(dateHeaders || []).map((header, index) => (
                <div
                  key={index}
                  className={cn(
                    "flex-shrink-0 text-center py-2 border-r border-border/30",
                    header.isToday && "bg-primary/10",
                    header.isWeekend && "bg-slate-800/30"
                  )}
                  style={{ width: `${dayWidth}px` }}
                >
                  <span
                    className={cn(
                      "text-xs",
                      header.isToday
                        ? "text-primary font-bold"
                        : "text-slate-400"
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
                {(ganttData || []).map((resource) => (
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
                  {(dateHeaders || []).map((header, index) => (
                    <div
                      key={index}
                      className={cn(
                        "flex-shrink-0 border-r border-border/20",
                        header.isWeekend && "bg-slate-800/20"
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
                {(ganttData || []).map((resource, _resourceIndex) => (
                  <div
                    key={resource.user_id}
                    className="relative h-12 border-b border-border/50"
                  >
                    {resource.tasks?.map((task) => {
                      const { startOffset, width } = getTaskPosition(task);
                      const statusColors = {
                        PENDING: {
                          bg: "bg-slate-600",
                          progress: "bg-slate-400"
                        },
                        IN_PROGRESS: {
                          bg: "bg-blue-900/50",
                          progress: "bg-blue-500"
                        },
                        BLOCKED: {
                          bg: "bg-red-900/50",
                          progress: "bg-red-500"
                        },
                        COMPLETED: {
                          bg: "bg-emerald-900/50",
                          progress: "bg-emerald-500"
                        }
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
                            "border-blue-500/50"
                          )}
                          style={{
                            left: `${startOffset}px`,
                            width: `${Math.max(width, dayWidth)}px`,
                            top: "50%",
                            transform: "translateY(-50%)"
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
