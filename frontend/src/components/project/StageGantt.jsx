import React from "react";
import { cn } from "../../lib/utils";
import { formatDate } from "../../lib/utils";
import { CheckCircle2, Circle } from "lucide-react";

export default function StageGantt({ stages }) {
  if (!stages || stages.length === 0) {
    return <div className="text-center py-8 text-slate-500">暂无阶段数据</div>;
  }

  // 计算整个项目的时间范围
  const allDates = stages.
  flatMap((s) => [
  new Date(s.planned_start_date),
  new Date(s.planned_end_date)]
  ).
  filter((d) => !isNaN(d));

  const minDate = new Date(Math.min(...allDates));
  const maxDate = new Date(Math.max(...allDates));
  const totalDays = Math.ceil((maxDate - minDate) / (1000 * 60 * 60 * 24)) + 1;

  // 计算日期相对位置函数
  const getPositionPercent = (date) => {
    const daysFromStart =
    (new Date(date) - minDate) / (1000 * 60 * 60 * 24);
    return daysFromStart / totalDays * 100;
  };

  const getWidthPercent = (startDate, endDate) => {
    const start = new Date(startDate);
    const end = new Date(endDate);
    const days = Math.ceil((end - start) / (1000 * 60 * 60 * 24)) + 1;
    return days / totalDays * 100;
  };

  // 状态颜色映射
  const statusColors = {
    COMPLETED: "bg-emerald-500",
    IN_PROGRESS: "bg-blue-500",
    PENDING: "bg-slate-600"
  };

  const _statusBgColors = {
    COMPLETED: "bg-emerald-500/10",
    IN_PROGRESS: "bg-blue-500/10",
    PENDING: "bg-slate-600/10"
  };

  const _statusBorderColors = {
    COMPLETED: "border-emerald-500/30",
    IN_PROGRESS: "border-blue-500/30",
    PENDING: "border-slate-600/30"
  };

  return (
    <div className="space-y-6">
      {/* 时间刻度 */}
      <div className="relative pl-32">
        <div className="flex justify-between text-xs text-slate-400 mb-2">
          <span>{formatDate(minDate)}</span>
          <span>{formatDate(maxDate)}</span>
        </div>
        <div className="absolute top-0 left-0 right-0 h-16 bg-gradient-to-r from-slate-900/50 to-slate-900/50 rounded-lg p-3">
          {/* Gantt chart background grid */}
          <div className="relative h-full">
            <div className="absolute inset-0 flex">
              {Array.from({ length: Math.min(totalDays, 50) }).map((_, i) =>
              <div
                key={i}
                className="flex-1 border-r border-white/5"
                style={{ flex: `${100 / Math.min(totalDays, 50)}%` }} />

              )}
            </div>
          </div>
        </div>
      </div>

      {/* 阶段条形图 */}
      <div className="space-y-3">
        {stages.map((stage) => {
          const startPercent = getPositionPercent(stage.planned_start_date);
          const widthPercent = getWidthPercent(
            stage.planned_start_date,
            stage.planned_end_date
          );

          return (
            <div key={stage.id} className="group">
              <div className="flex items-center gap-4">
                {/* 阶段代码和名称 */}
                <div className="w-28 flex-shrink-0">
                  <div className="flex items-center gap-2">
                    {stage.status === "COMPLETED" ?
                    <CheckCircle2 className="w-4 h-4 text-emerald-500" /> :
                    stage.status === "IN_PROGRESS" ?
                    <Circle className="w-4 h-4 text-blue-500 animate-pulse" /> :

                    <Circle className="w-4 h-4 text-slate-600" />
                    }
                    <div className="min-w-0">
                      <p className="font-semibold text-sm text-white truncate">
                        {stage.stage_code}
                      </p>
                      <p className="text-xs text-slate-400 truncate">
                        {stage.stage_name}
                      </p>
                    </div>
                  </div>
                </div>

                {/* 甘特条形图 */}
                <div className="flex-1 relative h-10 bg-white/5 rounded-lg border border-white/10 overflow-hidden">
                  {/* 条形背景 */}
                  <div
                    className={cn(
                      "absolute h-full rounded transition-all",
                      statusColors[stage.status] || "bg-slate-600"
                    )}
                    style={{
                      left: `${startPercent}%`,
                      width: `${widthPercent}%`,
                      opacity: stage.status === "COMPLETED" ? 0.8 : 0.6
                    }} />


                  {/* 进度条（如果有进度） */}
                  {stage.progress_pct > 0 && stage.status !== "COMPLETED" &&
                  <div
                    className="absolute h-full bg-gradient-to-r from-blue-400 to-blue-500 opacity-40"
                    style={{
                      left: `${startPercent}%`,
                      width: `${widthPercent * stage.progress_pct / 100}%`
                    }} />

                  }

                  {/* 文字标签 */}
                  <div
                    className="absolute h-full flex items-center justify-center px-2 text-xs font-medium text-white"
                    style={{
                      left: `${startPercent}%`,
                      width: `${widthPercent}%`
                    }}>

                    <span className="truncate">
                      {stage.progress_pct > 0 && stage.status !== "COMPLETED" ?
                      `${stage.progress_pct}%` :
                      stage.status === "COMPLETED" ?
                      "✓ 完成" :
                      ""}
                    </span>
                  </div>
                </div>

                {/* 日期和进度 */}
                <div className="w-40 flex-shrink-0 text-right">
                  <div className="text-xs text-slate-400 truncate">
                    {formatDate(stage.planned_start_date)} ~{" "}
                    {formatDate(stage.planned_end_date)}
                  </div>
                  <div className="text-sm font-semibold text-white">
                    {stage.progress_pct || 0}% | {stage.status === "COMPLETED" ? "已完成" : stage.status === "IN_PROGRESS" ? "进行中" : "未开始"}
                  </div>
                </div>
              </div>

              {/* 描述信息 */}
              {stage.description &&
              <p className="text-xs text-slate-400 ml-28 mt-1">
                  {stage.description}
              </p>
              }
            </div>);

        })}
      </div>

      {/* 图例 */}
      <div className="flex gap-6 text-xs text-slate-400 pt-4 border-t border-white/10">
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-emerald-500 rounded" />
          <span>已完成</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-blue-500 rounded animate-pulse" />
          <span>进行中</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-4 h-4 bg-slate-600 rounded" />
          <span>未开始</span>
        </div>
      </div>
    </div>);

}