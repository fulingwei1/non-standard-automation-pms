import { useState, useRef, useEffect, useMemo, useCallback } from "react";
import {
  differenceInCalendarDays,
  addDays,
  addWeeks,
  subWeeks,
  startOfWeek,
  startOfMonth,
  endOfMonth,
  format,
  isSameDay,
  isWeekend,
  isToday,
  eachDayOfInterval,
} from "date-fns";
import { zhCN } from "date-fns/locale";
import {
  ChevronLeft,
  ChevronRight,
  ZoomIn,
  ZoomOut,
  Calendar,
  ChevronDown,
  ChevronUp,
  GripVertical,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { Button } from "@/components/ui/button";
import {
  Tooltip,
  TooltipContent,
  TooltipProvider,
  TooltipTrigger,
} from "@/components/ui/tooltip";
import { DraggableTimelineBar } from "./DraggableTimelineBar";

/**
 * 项目时间轴组件
 *
 * 用于可视化展示项目、阶段、里程碑的时间安排
 * 支持拖拽调整日期
 */
export function ProjectTimeline({
  projects = [],
  onProjectUpdate,
  onStageUpdate,
  onMilestoneUpdate,
  onItemDoubleClick,
  showStages = true,
  showMilestones = true,
  readOnly = false,
  className,
}) {
  // 视图状态
  const [viewMode, setViewMode] = useState("week"); // "day" | "week" | "month"
  const [zoom, setZoom] = useState(1);
  const [expandedProjects, setExpandedProjects] = useState(
    () => projects.map((p) => p.id)
  );

  // 时间轴起始日期（默认从当前周开始往前一周）
  const [viewStartDate, setViewStartDate] = useState(() =>
    startOfWeek(subWeeks(new Date(), 1), { weekStartsOn: 1 })
  );

  // DOM 引用
  const scrollContainerRef = useRef(null);
  const shouldAutoScrollRef = useRef(true);

  // 计算日期范围
  const dates = useMemo(() => {
    const daysToRender =
      viewMode === "day" ? 30 : viewMode === "week" ? 60 : 90;
    return eachDayOfInterval({
      start: viewStartDate,
      end: addDays(viewStartDate, daysToRender - 1),
    });
  }, [viewMode, viewStartDate]);

  // 单元格宽度（根据视图模式和缩放级别）
  const baseCellWidth = viewMode === "day" ? 80 : viewMode === "week" ? 40 : 20;
  const cellWidth = Math.max(16, Math.round(baseCellWidth * zoom));
  const timelineWidth = dates.length * cellWidth;

  // 侧边栏宽度
  const sidebarWidth = 260;

  // 今日位置
  const todayOffset = useMemo(() => {
    const today = new Date();
    const offset = differenceInCalendarDays(today, dates[0]);
    if (offset < 0 || offset >= dates.length) return null;
    return offset;
  }, [dates]);

  // 自动滚动到今天
  useEffect(() => {
    if (!shouldAutoScrollRef.current || todayOffset === null) return;

    const el = scrollContainerRef.current;
    if (!el) return;

    const viewportWidth = el.clientWidth - sidebarWidth;
    const todayX = todayOffset * cellWidth;
    const target = Math.max(0, todayX - viewportWidth / 2 + cellWidth / 2);

    el.scrollTo({ left: target, behavior: "smooth" });
    shouldAutoScrollRef.current = false;
  }, [todayOffset, cellWidth, sidebarWidth]);

  // 重置缩放
  useEffect(() => {
    setZoom(1);
  }, [viewMode]);

  // 导航函数
  const navigateTime = useCallback(
    (direction) => {
      const step = direction === "next" ? 1 : -1;
      const weeksStep = viewMode === "month" ? 4 : viewMode === "week" ? 2 : 1;
      setViewStartDate((d) =>
        step === 1 ? addWeeks(d, weeksStep) : subWeeks(d, weeksStep)
      );
    },
    [viewMode]
  );

  const goToToday = useCallback(() => {
    shouldAutoScrollRef.current = true;
    setViewStartDate(startOfWeek(subWeeks(new Date(), 1), { weekStartsOn: 1 }));
  }, []);

  // 切换项目展开/折叠
  const toggleProject = useCallback((projectId) => {
    setExpandedProjects((prev) =>
      prev.includes(projectId)
        ? prev.filter((id) => id !== projectId)
        : [...prev, projectId]
    );
  }, []);

  // 处理项目日期更新
  const handleProjectDurationUpdate = useCallback(
    (projectId, newStart, newEnd) => {
      if (readOnly || !onProjectUpdate) return;
      onProjectUpdate(projectId, { start_date: newStart, end_date: newEnd });
    },
    [readOnly, onProjectUpdate]
  );

  // 处理阶段日期更新
  const handleStageDurationUpdate = useCallback(
    (projectId, stageId, newStart, newEnd) => {
      if (readOnly || !onStageUpdate) return;
      onStageUpdate(projectId, stageId, {
        start_date: newStart,
        end_date: newEnd,
      });
    },
    [readOnly, onStageUpdate]
  );

  // 渲染日期头部
  const renderDateHeader = () => {
    // 按月份分组
    const months = [];
    let currentMonth = null;
    let monthStart = 0;

    dates.forEach((date, index) => {
      const monthKey = format(date, "yyyy-MM");
      if (monthKey !== currentMonth) {
        if (currentMonth !== null) {
          months.push({
            key: currentMonth,
            label: format(dates[monthStart], "yyyy年M月", { locale: zhCN }),
            start: monthStart,
            width: index - monthStart,
          });
        }
        currentMonth = monthKey;
        monthStart = index;
      }
    });
    // 最后一个月
    months.push({
      key: currentMonth,
      label: format(dates[monthStart], "yyyy年M月", { locale: zhCN }),
      start: monthStart,
      width: dates.length - monthStart,
    });

    return (
      <div className="sticky top-0 z-20 bg-white border-b">
        {/* 月份行 */}
        <div className="flex h-8 border-b">
          <div
            className="shrink-0 bg-slate-50 border-r flex items-center px-3"
            style={{ width: sidebarWidth }}
          >
            <span className="text-xs font-medium text-slate-500">项目名称</span>
          </div>
          <div className="flex">
            {months.map((month) => (
              <div
                key={month.key}
                className="flex items-center justify-center border-r bg-slate-50 text-xs font-medium text-slate-600"
                style={{ width: month.width * cellWidth }}
              >
                {month.label}
              </div>
            ))}
          </div>
        </div>

        {/* 日期行 */}
        <div className="flex h-8">
          <div
            className="shrink-0 bg-white border-r"
            style={{ width: sidebarWidth }}
          />
          <div className="flex">
            {dates.map((date, index) => {
              const isWeekendDay = isWeekend(date);
              const isTodayDate = isToday(date);

              return (
                <div
                  key={index}
                  className={cn(
                    "flex flex-col items-center justify-center border-r text-[10px]",
                    isWeekendDay && "bg-slate-50",
                    isTodayDate && "bg-blue-50 font-bold text-blue-600"
                  )}
                  style={{ width: cellWidth }}
                >
                  <span>{format(date, "d")}</span>
                  {viewMode !== "month" && (
                    <span className="text-slate-400">
                      {format(date, "EEE", { locale: zhCN })}
                    </span>
                  )}
                </div>
              );
            })}
          </div>
        </div>
      </div>
    );
  };

  // 渲染项目行
  const renderProjectRow = (project) => {
    const isExpanded = expandedProjects.includes(project.id);
    const hasChildren =
      (showStages && project.stages?.length > 0) ||
      (showMilestones && project.milestones?.length > 0);

    const projectItem = {
      id: project.id,
      name: project.name || project.project_name,
      startDate: new Date(project.start_date || project.planned_start_date),
      endDate: new Date(project.end_date || project.planned_end_date),
      progress: project.progress,
      status: project.status,
    };

    return (
      <div key={project.id} className="border-b">
        {/* 项目主行 */}
        <div className="flex h-10 hover:bg-slate-50/50 group">
          {/* 项目名称 */}
          <div
            className="shrink-0 flex items-center gap-2 px-3 border-r bg-white"
            style={{ width: sidebarWidth }}
          >
            {hasChildren ? (
              <button
                onClick={() => toggleProject(project.id)}
                className="p-0.5 rounded hover:bg-slate-100"
              >
                {isExpanded ? (
                  <ChevronDown className="w-4 h-4 text-slate-400" />
                ) : (
                  <ChevronRight className="w-4 h-4 text-slate-400" />
                )}
              </button>
            ) : (
              <span className="w-5" />
            )}
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <span className="text-sm font-medium text-slate-700 truncate flex-1">
                    {projectItem.name}
                  </span>
                </TooltipTrigger>
                <TooltipContent>
                  <p>{projectItem.name}</p>
                  <p className="text-xs text-slate-400">
                    {format(projectItem.startDate, "yyyy-MM-dd")} ~{" "}
                    {format(projectItem.endDate, "yyyy-MM-dd")}
                  </p>
                </TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>

          {/* 时间轴区域 */}
          <div
            className="relative flex-1"
            style={{ width: timelineWidth }}
          >
            {/* 网格背景 */}
            <div className="absolute inset-0 flex">
              {dates.map((date, index) => (
                <div
                  key={index}
                  className={cn(
                    "border-r h-full",
                    isWeekend(date) && "bg-slate-50/50",
                    isToday(date) && "bg-blue-50/30"
                  )}
                  style={{ width: cellWidth }}
                />
              ))}
            </div>

            {/* 今日线 */}
            {todayOffset !== null && (
              <div
                className="absolute top-0 bottom-0 w-0.5 bg-blue-500 z-10"
                style={{ left: todayOffset * cellWidth + cellWidth / 2 }}
              />
            )}

            {/* 项目条 */}
            <DraggableTimelineBar
              item={projectItem}
              variant="project"
              viewStartDate={dates[0]}
              cellWidth={cellWidth}
              onUpdateDuration={(id, newStart, newEnd) =>
                handleProjectDurationUpdate(id, newStart, newEnd)
              }
              onDoubleClick={() => onItemDoubleClick?.("project", project)}
              disabled={readOnly}
            />
          </div>
        </div>

        {/* 展开的阶段/里程碑 */}
        {isExpanded && hasChildren && (
          <div className="bg-slate-50/30">
            {/* 阶段 */}
            {showStages &&
              project.stages?.map((stage) => {
                const stageItem = {
                  id: stage.id,
                  name: stage.name || stage.stage_name,
                  startDate: new Date(stage.start_date || stage.planned_start_date),
                  endDate: new Date(stage.end_date || stage.planned_end_date),
                  progress: stage.progress,
                  status: stage.status,
                };

                return (
                  <div
                    key={stage.id}
                    className="flex h-9 hover:bg-slate-100/50"
                  >
                    <div
                      className="shrink-0 flex items-center gap-2 px-3 pl-10 border-r"
                      style={{ width: sidebarWidth }}
                    >
                      <span className="w-1.5 h-1.5 rounded-full bg-slate-400" />
                      <span className="text-xs text-slate-600 truncate">
                        {stageItem.name}
                      </span>
                    </div>
                    <div
                      className="relative flex-1"
                      style={{ width: timelineWidth }}
                    >
                      {/* 网格背景 */}
                      <div className="absolute inset-0 flex">
                        {dates.map((date, index) => (
                          <div
                            key={index}
                            className={cn(
                              "border-r h-full",
                              isWeekend(date) && "bg-slate-50/50"
                            )}
                            style={{ width: cellWidth }}
                          />
                        ))}
                      </div>

                      <DraggableTimelineBar
                        item={stageItem}
                        variant="stage"
                        viewStartDate={dates[0]}
                        cellWidth={cellWidth}
                        onUpdateDuration={(id, newStart, newEnd) =>
                          handleStageDurationUpdate(project.id, id, newStart, newEnd)
                        }
                        onDoubleClick={() =>
                          onItemDoubleClick?.("stage", stage, project)
                        }
                        disabled={readOnly}
                      />
                    </div>
                  </div>
                );
              })}

            {/* 里程碑 */}
            {showMilestones &&
              project.milestones?.map((milestone) => {
                const milestoneDate = new Date(
                  milestone.due_date || milestone.planned_date
                );

                return (
                  <div
                    key={milestone.id}
                    className="flex h-9 hover:bg-slate-100/50"
                  >
                    <div
                      className="shrink-0 flex items-center gap-2 px-3 pl-10 border-r"
                      style={{ width: sidebarWidth }}
                    >
                      <span className="w-0 h-0 border-l-[5px] border-l-transparent border-r-[5px] border-r-transparent border-b-[8px] border-b-amber-500" />
                      <span className="text-xs text-slate-600 truncate">
                        {milestone.name}
                      </span>
                    </div>
                    <div
                      className="relative flex-1"
                      style={{ width: timelineWidth }}
                    >
                      {/* 里程碑标记 */}
                      {(() => {
                        const offset = differenceInCalendarDays(
                          milestoneDate,
                          dates[0]
                        );
                        if (offset < 0 || offset >= dates.length) return null;

                        return (
                          <TooltipProvider>
                            <Tooltip>
                              <TooltipTrigger asChild>
                                <div
                                  className="absolute top-1/2 -translate-y-1/2 w-4 h-4 bg-amber-500 rotate-45 cursor-pointer hover:scale-110 transition-transform"
                                  style={{
                                    left: offset * cellWidth + cellWidth / 2 - 8,
                                  }}
                                  onClick={() =>
                                    onItemDoubleClick?.("milestone", milestone, project)
                                  }
                                />
                              </TooltipTrigger>
                              <TooltipContent>
                                <p>{milestone.name}</p>
                                <p className="text-xs text-slate-400">
                                  {format(milestoneDate, "yyyy-MM-dd")}
                                </p>
                              </TooltipContent>
                            </Tooltip>
                          </TooltipProvider>
                        );
                      })()}
                    </div>
                  </div>
                );
              })}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={cn("flex flex-col h-full bg-white rounded-lg border", className)}>
      {/* 工具栏 */}
      <div className="flex items-center justify-between px-4 py-2 border-b bg-slate-50">
        <div className="flex items-center gap-2">
          {/* 导航按钮 */}
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigateTime("prev")}
          >
            <ChevronLeft className="w-4 h-4" />
          </Button>
          <Button variant="outline" size="sm" onClick={goToToday}>
            <Calendar className="w-4 h-4 mr-1" />
            今天
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => navigateTime("next")}
          >
            <ChevronRight className="w-4 h-4" />
          </Button>
        </div>

        <div className="flex items-center gap-4">
          {/* 视图模式切换 */}
          <div className="flex items-center gap-1 bg-white rounded-md border p-0.5">
            {["day", "week", "month"].map((mode) => (
              <button
                key={mode}
                onClick={() => setViewMode(mode)}
                className={cn(
                  "px-3 py-1 text-xs font-medium rounded transition-colors",
                  viewMode === mode
                    ? "bg-blue-500 text-white"
                    : "text-slate-600 hover:bg-slate-100"
                )}
              >
                {mode === "day" ? "日" : mode === "week" ? "周" : "月"}
              </button>
            ))}
          </div>

          {/* 缩放控制 */}
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setZoom((z) => Math.max(0.5, z - 0.25))}
              disabled={zoom <= 0.5}
            >
              <ZoomOut className="w-4 h-4" />
            </Button>
            <span className="text-xs text-slate-500 w-12 text-center">
              {Math.round(zoom * 100)}%
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => setZoom((z) => Math.min(2, z + 0.25))}
              disabled={zoom >= 2}
            >
              <ZoomIn className="w-4 h-4" />
            </Button>
          </div>
        </div>
      </div>

      {/* 时间轴主体 */}
      <div
        ref={scrollContainerRef}
        className="flex-1 overflow-auto"
      >
        <div style={{ minWidth: sidebarWidth + timelineWidth }}>
          {/* 日期头部 */}
          {renderDateHeader()}

          {/* 项目列表 */}
          <div>
            {projects.length === 0 ? (
              <div className="flex items-center justify-center h-40 text-slate-400">
                暂无项目数据
              </div>
            ) : (
              projects.map((project) => renderProjectRow(project))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

export default ProjectTimeline;
