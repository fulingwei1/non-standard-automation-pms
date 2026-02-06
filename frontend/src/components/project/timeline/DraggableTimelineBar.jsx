import { useState } from "react";
import { addDays, differenceInCalendarDays, format } from "date-fns";
import { cn } from "@/lib/utils";

/**
 * 可拖拽的时间轴条形组件
 *
 * 支持三种拖拽操作：
 * - 拖拽左边缘：修改开始日期
 * - 拖拽右边缘：修改结束日期
 * - 拖拽中间：整体移动（保持工期不变）
 */
export function DraggableTimelineBar({
  item,
  variant = "project", // "project" | "stage" | "milestone"
  viewStartDate,
  cellWidth,
  onUpdateStart,
  onUpdateDuration,
  onDoubleClick,
  disabled = false,
}) {
  const durationDays = differenceInCalendarDays(item.endDate, item.startDate) + 1;
  const offsetDays = differenceInCalendarDays(item.startDate, viewStartDate);
  const left = offsetDays * cellWidth;
  const width = durationDays * cellWidth;

  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState(0);
  const [dragType, setDragType] = useState(null); // "move" | "resize-left" | "resize-right"

  const handlePointerDown = (e) => {
    if (disabled) return;

    e.preventDefault();
    e.stopPropagation();
    setIsDragging(true);

    const rect = e.currentTarget.getBoundingClientRect();
    const offsetX = e.clientX - rect.left;

    // 根据点击位置决定拖拽类型
    const dragKind = offsetX < 10
      ? "resize-left"
      : offsetX > rect.width - 10
        ? "resize-right"
        : "move";

    setDragType(dragKind);
    document.body.style.cursor = dragKind === "move" ? "grabbing" : "col-resize";

    const startX = e.clientX;

    const handlePointerMove = (moveEvent) => {
      setDragOffset(moveEvent.clientX - startX);
    };

    const handlePointerUp = (upEvent) => {
      const deltaX = upEvent.clientX - startX;
      const daysMoved = Math.round(deltaX / cellWidth);

      if (daysMoved !== 0) {
        if (dragKind === "move") {
          // 整体移动
          const newStartDate = addDays(item.startDate, daysMoved);
          const newEndDate = addDays(item.endDate, daysMoved);
          if (onUpdateDuration) {
            onUpdateDuration(item.id, newStartDate, newEndDate);
          } else if (onUpdateStart) {
            onUpdateStart(item.id, newStartDate);
          }
        } else if (dragKind === "resize-left" && onUpdateDuration) {
          // 调整开始日期
          const newStartDate = addDays(item.startDate, daysMoved);
          if (newStartDate < item.endDate) {
            onUpdateDuration(item.id, newStartDate, item.endDate);
          }
        } else if (dragKind === "resize-right" && onUpdateDuration) {
          // 调整结束日期
          const newEndDate = addDays(item.endDate, daysMoved);
          if (newEndDate > item.startDate) {
            onUpdateDuration(item.id, item.startDate, newEndDate);
          }
        }
      }

      // 清理状态
      setIsDragging(false);
      setDragOffset(0);
      setDragType(null);
      document.body.style.cursor = "";
      window.removeEventListener("pointermove", handlePointerMove);
      window.removeEventListener("pointerup", handlePointerUp);
    };

    window.addEventListener("pointermove", handlePointerMove);
    window.addEventListener("pointerup", handlePointerUp);
  };

  // 计算视觉位置（拖拽时实时更新）
  let visualLeft = left;
  let visualWidth = width;

  if (isDragging && dragType) {
    if (dragType === "move") {
      visualLeft = left + dragOffset;
    } else if (dragType === "resize-right") {
      visualWidth = Math.max(cellWidth, width + dragOffset);
    } else if (dragType === "resize-left") {
      visualLeft = left + dragOffset;
      visualWidth = Math.max(cellWidth, width - dragOffset);
    }
  }

  // 日期标签
  const dateLabel = `${format(item.startDate, "MM/dd")} - ${format(item.endDate, "MM/dd")}`;

  // 根据变体和状态决定样式
  const getVariantStyles = () => {
    if (variant === "project") {
      return "bg-blue-500/15 border-blue-500/40 text-blue-700";
    }
    if (variant === "milestone") {
      return "bg-amber-500/15 border-amber-500/40 text-amber-700";
    }
    // stage 样式根据状态
    switch (item.status) {
      case "completed":
        return "bg-emerald-500/15 border-emerald-500/40 text-emerald-700";
      case "in_progress":
        return "bg-blue-500/15 border-blue-500/40 text-blue-700";
      case "delayed":
        return "bg-red-500/15 border-red-500/40 text-red-700";
      default:
        return "bg-slate-500/10 border-slate-500/30 text-slate-600";
    }
  };

  return (
    <div
      onPointerDown={handlePointerDown}
      onDoubleClick={onDoubleClick}
      className={cn(
        "absolute h-[28px] top-[6px] rounded-md border flex items-center px-2 gap-1.5 select-none overflow-hidden group",
        disabled ? "cursor-default opacity-60" : "cursor-grab active:cursor-grabbing",
        getVariantStyles(),
        isDragging && "shadow-lg z-30 opacity-90"
      )}
      style={{
        left: `${visualLeft}px`,
        width: `${Math.max(visualWidth, 60)}px`,
        transition: isDragging ? "none" : "left 0.2s ease-out, width 0.2s ease-out",
      }}
    >
      {/* 左侧拖拽手柄 */}
      {!disabled && (
        <div className="absolute left-0 top-0 bottom-0 w-2.5 cursor-col-resize opacity-0 group-hover:opacity-100 bg-current/10 rounded-l-md" />
      )}

      {/* 右侧拖拽手柄 */}
      {!disabled && (
        <div className="absolute right-0 top-0 bottom-0 w-2.5 cursor-col-resize opacity-0 group-hover:opacity-100 bg-current/10 rounded-r-md" />
      )}

      {/* 内容 */}
      <span className="text-xs font-medium whitespace-nowrap overflow-hidden text-ellipsis flex-1 min-w-0">
        {item.name}
      </span>

      {/* 进度显示 */}
      {item.progress !== undefined && (
        <span className="text-[10px] font-medium opacity-70 shrink-0">
          {item.progress}%
        </span>
      )}
    </div>
  );
}

export default DraggableTimelineBar;
