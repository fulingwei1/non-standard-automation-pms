/**
 * Statistics Charts Components for Administrative Management
 * Reusable chart components for administrative statistics
 */

import { useMemo } from "react";
import { cn, formatCurrency } from "../../lib/utils";

/**
 * Simple Bar Chart Component
 */
export function SimpleBarChart({ data, height = 200, color = "bg-blue-500" }) {
  const maxValue = useMemo(() => {
    return Math.max(...data.map((d) => d.value), 1);
  }, [data]);

  return (
    <div className="flex items-end gap-2" style={{ height: `${height}px` }}>
      {data.map((item, index) => (
        <div key={index} className="flex-1 flex flex-col items-center gap-1">
          <div className="w-full flex flex-col items-center gap-1">
            <span className="text-xs text-slate-400">{item.value}</span>
            <div
              className={cn(
                "w-full rounded-t transition-all hover:opacity-80",
                color,
              )}
              style={{ height: `${(item.value / maxValue) * (height - 40)}px` }}
            />
          </div>
          <span className="text-xs text-slate-500 truncate w-full text-center">
            {item.label}
          </span>
        </div>
      ))}
    </div>
  );
}

/**
 * Line Chart Component
 */
export function SimpleLineChart({
  data,
  height = 200,
  color = "text-blue-400",
}) {
  const maxValue = useMemo(() => {
    return Math.max(...data.map((d) => d.value), 1);
  }, [data]);

  const points = data.map((item, index) => ({
    x: (index / (data.length - 1 || 1)) * 100,
    y: 100 - (item.value / maxValue) * 80,
    value: item.value,
    label: item.label,
  }));

  return (
    <div className="relative" style={{ height: `${height}px` }}>
      <svg
        className="w-full h-full"
        viewBox="0 0 100 100"
        preserveAspectRatio="none"
      >
        <polyline
          points={points.map((p) => `${p.x},${p.y}`).join(" ")}
          fill="none"
          stroke="currentColor"
          strokeWidth="0.5"
          className={color}
        />
        {points.map((point, index) => (
          <circle
            key={index}
            cx={point.x}
            cy={point.y}
            r="1"
            fill="currentColor"
            className={color}
          />
        ))}
      </svg>
      <div className="absolute bottom-0 left-0 right-0 flex justify-between text-xs text-slate-500">
        {data.map((item, index) => (
          <span
            key={index}
            className="truncate"
            style={{ width: `${100 / data.length}%` }}
          >
            {item.label}
          </span>
        ))}
      </div>
    </div>
  );
}

/**
 * Pie Chart Component (Donut Chart)
 */
export function SimplePieChart({ data, size = 200 }) {
  const total = useMemo(() => {
    return data.reduce((sum, item) => sum + item.value, 0);
  }, [data]);

  const radius = size / 2 - 10;
  const centerX = size / 2;
  const centerY = size / 2;

  const segments = useMemo(() => {
    // Calculate cumulative angles using reduce to avoid mutation
    const angles = data.reduce((acc, item, index) => {
      const prevAngle = index === 0 ? -90 : acc[index - 1].endAngle;
      const angle = (item.value / total) * 360;
      acc.push({
        startAngle: prevAngle,
        endAngle: prevAngle + angle,
        angle,
        item,
        index,
      });
      return acc;
    }, []);

    return angles.map(({ startAngle, endAngle, angle, item, index }) => {
      const percentage = (item.value / total) * 100;
      const startAngleRad = (startAngle * Math.PI) / 180;
      const endAngleRad = (endAngle * Math.PI) / 180;

      const x1 = centerX + radius * Math.cos(startAngleRad);
      const y1 = centerY + radius * Math.sin(startAngleRad);
      const x2 = centerX + radius * Math.cos(endAngleRad);
      const y2 = centerY + radius * Math.sin(endAngleRad);

      const largeArcFlag = angle > 180 ? 1 : 0;

      const pathData = [
        `M ${centerX} ${centerY}`,
        `L ${x1} ${y1}`,
        `A ${radius} ${radius} 0 ${largeArcFlag} 1 ${x2} ${y2}`,
        "Z",
      ].join(" ");

      return {
        pathData,
        percentage,
        color: item.color || `hsl(${index * 60}, 70%, 50%)`,
        label: item.label,
        value: item.value,
      };
    });
  }, [data, total, radius, centerX, centerY]);

  return (
    <div className="flex items-center gap-6">
      <div
        className="relative"
        style={{ width: `${size}px`, height: `${size}px` }}
      >
        <svg width={size} height={size} className="transform -rotate-90">
          {segments.map((segment, index) => (
            <path
              key={index}
              d={segment.pathData}
              fill={segment.color}
              stroke="rgb(15 23 42)"
              strokeWidth="2"
              className="transition-opacity hover:opacity-80"
            />
          ))}
        </svg>
        <div className="absolute inset-0 flex items-center justify-center">
          <div className="text-center">
            <div className="text-2xl font-bold text-white">{total}</div>
            <div className="text-xs text-slate-400">总计</div>
          </div>
        </div>
      </div>
      <div className="flex-1 space-y-2">
        {segments.map((segment, index) => (
          <div key={index} className="flex items-center gap-3">
            <div
              className="w-4 h-4 rounded"
              style={{ backgroundColor: segment.color }}
            />
            <div className="flex-1">
              <div className="flex items-center justify-between text-sm">
                <span className="text-slate-300">{segment.label}</span>
                <span className="text-white font-medium">{segment.value}</span>
              </div>
              <div className="text-xs text-slate-500">
                {segment.percentage.toFixed(1)}%
              </div>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

/**
 * Trend Comparison Card
 */
export function TrendComparisonCard({
  title,
  current,
  previous,
  unit = "",
  formatValue,
}) {
  const trend = useMemo(() => {
    if (!previous || previous === 0) {return 0;}
    return ((current - previous) / previous) * 100;
  }, [current, previous]);

  const format = formatValue || ((v) => `${v}${unit}`);

  return (
    <div className="p-4 bg-slate-800/40 rounded-lg border border-slate-700/50">
      <div className="text-sm text-slate-400 mb-2">{title}</div>
      <div className="flex items-end justify-between">
        <div>
          <div className="text-2xl font-bold text-white">{format(current)}</div>
          {previous && (
            <div className="text-xs text-slate-500 mt-1">
              上月: {format(previous)}
            </div>
          )}
        </div>
        {trend !== 0 && (
          <div
            className={cn(
              "flex items-center gap-1 text-sm font-medium",
              trend > 0 ? "text-emerald-400" : "text-red-400",
            )}
          >
            {trend > 0 ? "↑" : "↓"}
            {Math.abs(trend).toFixed(1)}%
          </div>
        )}
      </div>
    </div>
  );
}

/**
 * Category Breakdown Card
 */
export function CategoryBreakdownCard({ title, data, total, formatValue }) {
  const format = formatValue || formatCurrency;

  return (
    <div className="space-y-3">
      <div className="flex items-center justify-between">
        <h4 className="text-sm font-medium text-white">{title}</h4>
        <span className="text-sm text-slate-400">总计: {format(total)}</span>
      </div>
      <div className="space-y-2">
        {data.map((item, index) => {
          const percentage = total > 0 ? (item.value / total) * 100 : 0;
          return (
            <div key={index} className="space-y-1">
              <div className="flex items-center justify-between text-sm">
                <div className="flex items-center gap-2">
                  <div
                    className="w-3 h-3 rounded"
                    style={{
                      backgroundColor:
                        item.color || `hsl(${index * 60}, 70%, 50%)`,
                    }}
                  />
                  <span className="text-slate-300">{item.label}</span>
                </div>
                <div className="flex items-center gap-3">
                  <span className="text-white font-medium">
                    {format(item.value)}
                  </span>
                  <span className="text-slate-500 text-xs w-12 text-right">
                    {percentage.toFixed(1)}%
                  </span>
                </div>
              </div>
              <div className="h-1.5 bg-slate-700/50 rounded-full overflow-hidden">
                <div
                  className="h-full transition-all"
                  style={{
                    width: `${percentage}%`,
                    backgroundColor:
                      item.color || `hsl(${index * 60}, 70%, 50%)`,
                  }}
                />
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

/**
 * Monthly Trend Chart
 */
export function MonthlyTrendChart({
  data,
  valueKey = "value",
  labelKey = "month",
  height = 200,
}) {
  const maxValue = useMemo(() => {
    return Math.max(...data.map((d) => d[valueKey]), 1);
  }, [data, valueKey]);

  return (
    <div className="space-y-4">
      <div className="flex items-end gap-2" style={{ height: `${height}px` }}>
        {data.map((item, index) => (
          <div key={index} className="flex-1 flex flex-col items-center gap-1">
            <div className="w-full flex flex-col items-center gap-1">
              <span className="text-xs text-slate-400">
                {typeof item[valueKey] === "number"
                  ? item[valueKey] >= 10000
                    ? `${(item[valueKey] / 10000).toFixed(1)}万`
                    : item[valueKey]
                  : item[valueKey]}
              </span>
              <div
                className="w-full bg-gradient-to-t from-blue-500/50 to-blue-500 rounded-t transition-all hover:from-blue-500/70 hover:to-blue-400"
                style={{
                  height: `${(item[valueKey] / maxValue) * (height - 40)}px`,
                }}
              />
            </div>
            <span className="text-xs text-slate-500 truncate w-full text-center">
              {item[labelKey]?.slice(-2) || item[labelKey]}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
