/**
 * Cost Trend Chart Component - 成本趋势图表组件
 * 用于展示报价多个版本的成本变化趋势（总价、总成本、毛利率）
 */

import { useMemo } from "react";
import { formatCurrency } from "../../lib/utils";

export function CostTrendChart({
  data,
  height = 300,
  showGrid = true,
  showPoints = true,
}) {
  // data格式: [{ version_no: 'V1', created_at: '2025-01-01', total_price: 200000, total_cost: 160000, gross_margin: 20 }, ...]

  const sortedData = useMemo(() => {
    if (!data || !Array.isArray(data)) {return [];}
    return [...data].sort((a, b) => {
      const dateA = new Date(a.created_at || 0);
      const dateB = new Date(b.created_at || 0);
      return dateA - dateB;
    });
  }, [data]);

  // Calculate value ranges for each metric
  const priceValues = useMemo(
    () => (sortedData || []).map((d) => d.total_price || 0),
    [sortedData],
  );
  const costValues = useMemo(
    () => (sortedData || []).map((d) => d.total_cost || 0),
    [sortedData],
  );
  const marginValues = useMemo(
    () => (sortedData || []).map((d) => d.gross_margin || 0),
    [sortedData],
  );

  const maxPrice = useMemo(() => Math.max(...priceValues, 1), [priceValues]);
  const maxCost = useMemo(() => Math.max(...costValues, 1), [costValues]);
  const maxMargin = useMemo(
    () => Math.max(...marginValues, 100),
    [marginValues],
  );
  const minMargin = useMemo(() => Math.min(...marginValues, 0), [marginValues]);

  const padding = useMemo(
    () => ({ top: 20, right: 40, bottom: 60, left: 60 }),
    [],
  );
  const chartWidth = useMemo(() => height * 1.5, [height]); // Make chart wider for better visibility
  const chartHeight = height;

  // Calculate points for each line
  const pricePoints = useMemo(() => {
    if (sortedData.length === 0) {return [];}
    return (sortedData || []).map((item, index) => {
      const x =
        padding.left +
        (index / (sortedData.length - 1 || 1)) *
          (chartWidth - padding.left - padding.right);
      const y =
        padding.top +
        (1 - (item.total_price || 0) / maxPrice) *
          (chartHeight - padding.top - padding.bottom);
      return {
        x,
        y,
        value: item.total_price || 0,
        version: item.version_no,
        date: item.created_at,
      };
    });
  }, [sortedData, maxPrice, padding, chartWidth, chartHeight]);

  const costPoints = useMemo(() => {
    if (sortedData.length === 0) {return [];}
    return (sortedData || []).map((item, index) => {
      const x =
        padding.left +
        (index / (sortedData.length - 1 || 1)) *
          (chartWidth - padding.left - padding.right);
      const y =
        padding.top +
        (1 - (item.total_cost || 0) / maxCost) *
          (chartHeight - padding.top - padding.bottom);
      return {
        x,
        y,
        value: item.total_cost || 0,
        version: item.version_no,
        date: item.created_at,
      };
    });
  }, [sortedData, maxCost, padding, chartWidth, chartHeight]);

  const marginPoints = useMemo(() => {
    if (sortedData.length === 0) {return [];}
    const marginRange = maxMargin - minMargin || 100;
    return (sortedData || []).map((item, index) => {
      const x =
        padding.left +
        (index / (sortedData.length - 1 || 1)) *
          (chartWidth - padding.left - padding.right);
      const y =
        padding.top +
        (1 - ((item.gross_margin || 0) - minMargin) / marginRange) *
          (chartHeight - padding.top - padding.bottom);
      return {
        x,
        y,
        value: item.gross_margin || 0,
        version: item.version_no,
        date: item.created_at,
      };
    });
  }, [sortedData, maxMargin, minMargin, padding, chartWidth, chartHeight]);

  // Generate path data
  const pricePath = useMemo(() => {
    if (pricePoints.length === 0) {return "";}
    return pricePoints
      .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
      .join(" ");
  }, [pricePoints]);

  const costPath = useMemo(() => {
    if (costPoints.length === 0) {return "";}
    return costPoints
      .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
      .join(" ");
  }, [costPoints]);

  const marginPath = useMemo(() => {
    if (marginPoints.length === 0) {return "";}
    return marginPoints
      .map((p, i) => `${i === 0 ? "M" : "L"} ${p.x} ${p.y}`)
      .join(" ");
  }, [marginPoints]);

  // Early return after all hooks
  if (sortedData.length === 0) {
    return (
      <div className="flex items-center justify-center h-full text-slate-400">
        暂无数据
      </div>
    );
  }

  // Format Y-axis labels for price/cost
  const formatPriceLabel = (value) => {
    if (value >= 1000000) {return `${(value / 1000000).toFixed(1)}M`;}
    if (value >= 1000) {return `${(value / 1000).toFixed(0)}K`;}
    return value.toFixed(0);
  };

  return (
    <div
      className="relative"
      style={{ height: `${height}px`, width: "100%", overflowX: "auto" }}
    >
      <svg width={chartWidth} height={chartHeight} className="overflow-visible">
        {/* Grid lines */}
        {showGrid && (
          <g opacity="0.1" className="text-slate-500">
            {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
              const y =
                padding.top +
                (1 - ratio) * (chartHeight - padding.top - padding.bottom);
              return (
                <line
                  key={ratio}
                  x1={padding.left}
                  y1={y}
                  x2={chartWidth - padding.right}
                  y2={y}
                  stroke="currentColor"
                  strokeWidth="1"
                  strokeDasharray="4 4"
                />
              );
            })}
          </g>
        )}

        {/* Y-axis labels for price/cost (left) */}
        <g className="text-xs fill-slate-400">
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const value = maxPrice * ratio;
            const y =
              padding.top +
              (1 - ratio) * (chartHeight - padding.top - padding.bottom);
            return (
              <text
                key={`price-${ratio}`}
                x={padding.left - 10}
                y={y + 4}
                textAnchor="end"
              >
                {formatPriceLabel(value)}
              </text>
            );
          })}
        </g>

        {/* Y-axis labels for margin (right) */}
        <g className="text-xs fill-slate-400">
          {[0, 0.25, 0.5, 0.75, 1].map((ratio) => {
            const value = minMargin + (maxMargin - minMargin) * ratio;
            const y =
              padding.top +
              (1 - ratio) * (chartHeight - padding.top - padding.bottom);
            return (
              <text
                key={`margin-${ratio}`}
                x={chartWidth - padding.right + 10}
                y={y + 4}
                textAnchor="start"
              >
                {value.toFixed(0)}%
              </text>
            );
          })}
        </g>

        {/* Price line (green) */}
        {pricePoints.length > 1 && (
          <g>
            <path
              d={pricePath}
              fill="none"
              stroke="rgb(34, 197, 94)"
              strokeWidth="2"
              className="transition-all"
            />
            {showPoints &&
              (pricePoints || []).map((point, index) => (
                <g key={`price-${index}`}>
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r="4"
                    fill="rgb(34, 197, 94)"
                    className="transition-all hover:r-6"
                  />
                  <title>{`总价: ${formatCurrency(point.value)}\n版本: ${point.version}`}</title>
                </g>
              ))}
          </g>
        )}

        {/* Cost line (red) */}
        {costPoints.length > 1 && (
          <g>
            <path
              d={costPath}
              fill="none"
              stroke="rgb(239, 68, 68)"
              strokeWidth="2"
              className="transition-all"
            />
            {showPoints &&
              (costPoints || []).map((point, index) => (
                <g key={`cost-${index}`}>
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r="4"
                    fill="rgb(239, 68, 68)"
                    className="transition-all hover:r-6"
                  />
                  <title>{`总成本: ${formatCurrency(point.value)}\n版本: ${point.version}`}</title>
                </g>
              ))}
          </g>
        )}

        {/* Margin line (blue) - scaled to right axis */}
        {marginPoints.length > 1 && (
          <g>
            <path
              d={marginPath}
              fill="none"
              stroke="rgb(59, 130, 246)"
              strokeWidth="2"
              strokeDasharray="4 4"
              className="transition-all"
            />
            {showPoints &&
              (marginPoints || []).map((point, index) => (
                <g key={`margin-${index}`}>
                  <circle
                    cx={point.x}
                    cy={point.y}
                    r="4"
                    fill="rgb(59, 130, 246)"
                    className="transition-all hover:r-6"
                  />
                  <title>{`毛利率: ${point.value.toFixed(2)}%\n版本: ${point.version}`}</title>
                </g>
              ))}
          </g>
        )}

        {/* X-axis labels */}
        <g className="text-xs fill-slate-400">
          {(sortedData || []).map((item, index) => {
            const x =
              padding.left +
              (index / (sortedData.length - 1 || 1)) *
                (chartWidth - padding.left - padding.right);
            return (
              <text
                key={index}
                x={x}
                y={chartHeight - padding.bottom + 20}
                textAnchor="middle"
              >
                {item.version_no}
              </text>
            );
          })}
        </g>
      </svg>

      {/* Legend */}
      <div className="absolute top-0 right-0 flex gap-4 text-xs">
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-green-500" />
          <span className="text-slate-400">总价</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-red-500" />
          <span className="text-slate-400">总成本</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-3 h-0.5 bg-blue-500 border-dashed border-t-2 border-blue-500" />
          <span className="text-slate-400">毛利率</span>
        </div>
      </div>
    </div>
  );
}
