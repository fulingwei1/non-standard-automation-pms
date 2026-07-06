import { useEffect, useState, useRef } from "react";
import { Card, CardContent, Badge, LoadingSpinner, EmptyState } from "../ui";
import { TrendingUp, AlertCircle } from "lucide-react";
import { cn } from "../../lib/utils";

/**
 * 通用趋势图组件（纯 CSS 绘制，不依赖图表库）
 * 支持两种模式：
 * 1. severity 趋势：每天一个色块（CRITICAL 红/HIGH 橙/MEDIUM 黄/LOW 绿/null 灰）
 * 2. 数值趋势：折线图（如毛利率%）
 */

const sevColor = {
  CRITICAL: "bg-red-500",
  HIGH: "bg-orange-500",
  MEDIUM: "bg-yellow-400",
  LOW: "bg-green-500",
  healthy: "bg-green-500",
  warning: "bg-yellow-400",
  critical: "bg-red-500",
};

const sevShort = {
  CRITICAL: "C", HIGH: "H", MEDIUM: "M", LOW: "L",
  healthy: "✓", warning: "!", critical: "✗",
};

export function SeverityTrendChart({ dates, severity, title = "风险等级趋势" }) {
  if (!dates || dates.length === 0) {
    return (
      <Card>
        <CardContent className="p-4">
          <EmptyState title="暂无趋势数据" description="需要先跑快照" />
        </CardContent>
      </Card>
    );
  }

  // 每 N 天显示一个日期标签
  const labelInterval = Math.max(1, Math.floor(dates.length / 8));

  return (
    <Card>
      <CardContent className="p-4">
        <h3 className="text-sm font-semibold mb-3 flex items-center gap-1">
          <TrendingUp className="w-4 h-4 text-gray-400" />
          {title}
          <span className="text-xs text-gray-400 ml-2">（{dates.length} 天）</span>
        </h3>

        {/* 色块条 */}
        <div className="flex gap-px flex-wrap">
          {severity.map((sev, idx) => (
            <div
              key={idx}
              title={`${dates[idx]}: ${sev || "无数据"}`}
              className={cn(
                "w-4 h-6 rounded-sm cursor-help flex items-center justify-center text-[8px] text-white font-bold",
                sev ? sevColor[sev] || "bg-gray-300" : "bg-gray-100"
              )}
            >
              {sev ? sevShort[sev] || "?" : ""}
            </div>
          ))}
        </div>

        {/* 日期标签 */}
        <div className="flex justify-between mt-1 text-[10px] text-gray-400">
          <span>{dates[0]?.slice(5)}</span>
          <span>{dates[Math.floor(dates.length / 2)]?.slice(5)}</span>
          <span>{dates[dates.length - 1]?.slice(5)}</span>
        </div>

        {/* 图例 */}
        <div className="flex gap-3 mt-3 text-xs text-gray-500">
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-red-500 rounded-sm" /> CRITICAL
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-orange-500 rounded-sm" /> HIGH
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-yellow-400 rounded-sm" /> MEDIUM
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-green-500 rounded-sm" /> LOW
          </span>
          <span className="flex items-center gap-1">
            <span className="w-3 h-3 bg-gray-100 border rounded-sm" /> 无数据
          </span>
        </div>
      </CardContent>
    </Card>
  );
}

export function NumericTrendChart({
  dates,
  values,
  title = "数值趋势",
  unit = "",
  color = "bg-blue-500",
  targetLine,
}) {
  const canvasRef = useRef(null);

  useEffect(() => {
    if (!values || values.length === 0 || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext("2d");
    const w = canvas.width;
    const h = canvas.height;
    ctx.clearRect(0, 0, w, h);

    // 过滤有效值
    const valid = values.map((v, i) => ({ v, i })).filter((d) => d.v != null);
    if (valid.length === 0) return;

    const vals = valid.map((d) => d.v);
    let min = Math.min(...vals);
    let max = Math.max(...vals);
    if (targetLine != null) {
      min = Math.min(min, targetLine);
      max = Math.max(max, targetLine);
    }
    const range = max - min || 1;
    const pad = range * 0.15;
    min -= pad;
    max += pad;

    const padX = 30;
    const padY = 15;
    const plotW = w - padX * 2;
    const plotH = h - padY * 2;

    // 目标线
    if (targetLine != null) {
      const y = padY + plotH - ((targetLine - min) / (max - min)) * plotH;
      ctx.strokeStyle = "#ef4444";
      ctx.lineWidth = 1;
      ctx.setLineDash([4, 3]);
      ctx.beginPath();
      ctx.moveTo(padX, y);
      ctx.lineTo(w - padX, y);
      ctx.stroke();
      ctx.setLineDash([]);
      ctx.fillStyle = "#ef4444";
      ctx.font = "10px sans-serif";
      ctx.fillText(`目标 ${targetLine}${unit}`, w - padX - 50, y - 3);
    }

    // 折线
    ctx.strokeStyle = "#3b82f6";
    ctx.lineWidth = 2;
    ctx.beginPath();
    valid.forEach((d, idx) => {
      const x = padX + (d.i / (values.length - 1)) * plotW;
      const y = padY + plotH - ((d.v - min) / (max - min)) * plotH;
      if (idx === 0) ctx.moveTo(x, y);
      else ctx.lineTo(x, y);
    });
    ctx.stroke();

    // 填充
    ctx.lineTo(padX + ((valid[valid.length - 1].i / (values.length - 1)) * plotW), h - padY);
    ctx.lineTo(padX + ((valid[0].i / (values.length - 1)) * plotW), h - padY);
    ctx.closePath();
    ctx.fillStyle = "rgba(59, 130, 246, 0.1)";
    ctx.fill();

    // 点
    ctx.fillStyle = "#3b82f6";
    valid.forEach((d) => {
      const x = padX + (d.i / (values.length - 1)) * plotW;
      const y = padY + plotH - ((d.v - min) / (max - min)) * plotH;
      ctx.beginPath();
      ctx.arc(x, y, 2, 0, Math.PI * 2);
      ctx.fill();
    });
  }, [values, targetLine, unit]);

  if (!dates || dates.length === 0 || !values?.some((v) => v != null)) {
    return (
      <Card>
        <CardContent className="p-4">
          <EmptyState title="暂无趋势数据" />
        </CardContent>
      </Card>
    );
  }

  return (
    <Card>
      <CardContent className="p-4">
        <div className="flex items-center justify-between mb-2">
          <h3 className="text-sm font-semibold flex items-center gap-1">
            <TrendingUp className="w-4 h-4 text-gray-400" />
            {title}
          </h3>
          <span className="text-xs text-gray-400">{dates.length} 天</span>
        </div>
        <canvas ref={canvasRef} width={600} height={150} className="w-full" />
        <div className="flex justify-between mt-1 text-[10px] text-gray-400">
          <span>{dates[0]?.slice(5)}</span>
          <span>{dates[dates.length - 1]?.slice(5)}</span>
        </div>
      </CardContent>
    </Card>
  );
}

/**
 * 通用趋势数据加载 hook
 */
export function useTrendData(fetchFn, deps = []) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    fetchFn()
      .then((resp) => {
        if (mounted) setData(resp.data?.data || resp.data);
      })
      .catch(() => {})
      .finally(() => mounted && setLoading(false));
    return () => {
      mounted = false;
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, deps);

  return { data, loading };
}
