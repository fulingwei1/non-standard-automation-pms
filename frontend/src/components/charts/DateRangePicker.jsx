/**
 * 日期范围选择器组件
 * 支持预设范围和自定义日期选择
 */

import { useState, useMemo } from "react";
import {
  format,
  subDays,
  subMonths,
  startOfMonth,
  endOfMonth,
  startOfYear,
} from "date-fns";
import { Calendar, ChevronDown, Check } from "lucide-react";
import { cn } from "../../lib/utils";

const presetRanges = [
  {
    key: "7d",
    label: "近7天",
    getRange: () => ({ start: subDays(new Date(), 7), end: new Date() }),
  },
  {
    key: "30d",
    label: "近30天",
    getRange: () => ({ start: subDays(new Date(), 30), end: new Date() }),
  },
  {
    key: "90d",
    label: "近90天",
    getRange: () => ({ start: subDays(new Date(), 90), end: new Date() }),
  },
  {
    key: "thisMonth",
    label: "本月",
    getRange: () => ({ start: startOfMonth(new Date()), end: new Date() }),
  },
  {
    key: "lastMonth",
    label: "上月",
    getRange: () => {
      const lastMonth = subMonths(new Date(), 1);
      return { start: startOfMonth(lastMonth), end: endOfMonth(lastMonth) };
    },
  },
  {
    key: "ytd",
    label: "年初至今",
    getRange: () => ({ start: startOfYear(new Date()), end: new Date() }),
  },
  { key: "custom", label: "自定义", getRange: () => null },
];

/**
 * DateRangePicker - 日期范围选择器
 * @param {object} value - 当前值 { start: Date, end: Date }
 * @param {function} onChange - 值变更回调
 * @param {string} presetKey - 预设范围key
 * @param {function} onPresetChange - 预设变更回调
 * @param {string} className - 自定义类名
 */
export default function DateRangePicker({
  value,
  onChange,
  presetKey = "30d",
  onPresetChange,
  className,
}) {
  const [isOpen, setIsOpen] = useState(false);
  const [selectedPreset, setSelectedPreset] = useState(presetKey);
  const [customStart, setCustomStart] = useState("");
  const [customEnd, setCustomEnd] = useState("");

  const displayText = useMemo(() => {
    if (value?.start && value?.end) {
      return `${format(value.start, "yyyy-MM-dd")} ~ ${format(value.end, "yyyy-MM-dd")}`;
    }
    const preset = (presetRanges || []).find((p) => p.key === selectedPreset);
    return preset?.label || "选择日期";
  }, [value, selectedPreset]);

  const handlePresetSelect = (preset) => {
    setSelectedPreset(preset.key);
    if (preset.key !== "custom") {
      const range = preset.getRange();
      onChange?.(range);
      onPresetChange?.(preset.key);
      setIsOpen(false);
    }
  };

  const handleCustomApply = () => {
    if (customStart && customEnd) {
      onChange?.({
        start: new Date(customStart),
        end: new Date(customEnd),
      });
      onPresetChange?.("custom");
      setIsOpen(false);
    }
  };

  return (
    <div className={cn("relative", className)}>
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="flex items-center gap-2 px-3 py-2 bg-surface-100 border border-white/10 rounded-lg text-sm text-white hover:bg-surface-200 transition-colors"
      >
        <Calendar className="w-4 h-4 text-slate-400" />
        <span>{displayText}</span>
        <ChevronDown
          className={cn(
            "w-4 h-4 text-slate-400 transition-transform",
            isOpen && "rotate-180",
          )}
        />
      </button>

      {isOpen && (
        <div className="absolute top-full mt-2 right-0 z-50 w-72 bg-slate-800 border border-slate-700 rounded-lg shadow-xl">
          {/* 预设选项 */}
          <div className="p-2 border-b border-slate-700">
            <div className="text-xs text-slate-400 px-2 py-1 mb-1">
              快捷选择
            </div>
            <div className="grid grid-cols-2 gap-1">
              {presetRanges
                .filter((p) => p.key !== "custom")
                .map((preset) => (
                  <button
                    key={preset.key}
                    onClick={() => handlePresetSelect(preset)}
                    className={cn(
                      "flex items-center justify-between px-3 py-2 rounded-md text-sm transition-colors",
                      selectedPreset === preset.key
                        ? "bg-primary text-white"
                        : "text-slate-300 hover:bg-slate-700",
                    )}
                  >
                    <span>{preset.label}</span>
                    {selectedPreset === preset.key && (
                      <Check className="w-4 h-4" />
                    )}
                  </button>
                ))}
            </div>
          </div>

          {/* 自定义日期 */}
          <div className="p-3">
            <div className="text-xs text-slate-400 mb-2">自定义日期范围</div>
            <div className="flex gap-2 mb-3">
              <input
                type="date"
                value={customStart ?? ""}
                onChange={(e) => setCustomStart(e.target.value)}
                className="flex-1 px-2 py-1.5 bg-slate-700 border border-slate-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary"
              />
              <span className="text-slate-400 self-center">~</span>
              <input
                type="date"
                value={customEnd ?? ""}
                onChange={(e) => setCustomEnd(e.target.value)}
                className="flex-1 px-2 py-1.5 bg-slate-700 border border-slate-600 rounded text-sm text-white focus:outline-none focus:ring-1 focus:ring-primary"
              />
            </div>
            <button
              onClick={handleCustomApply}
              disabled={!customStart || !customEnd}
              className="w-full py-2 bg-primary text-white rounded-md text-sm font-medium hover:bg-primary/90 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
            >
              应用
            </button>
          </div>
        </div>
      )}

      {/* 点击外部关闭 */}
      {isOpen && (
        <div className="fixed inset-0 z-40" onClick={() => setIsOpen(false)} />
      )}
    </div>
  );
}
