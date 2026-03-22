/**
 * DatePickerWithRange 日期范围选择器组件
 * 使用原生 date input + Popover 实现
 * 提供 from/to 日期范围选择功能
 */

import * as React from "react";
import { Calendar } from "lucide-react";
import * as Popover from "@radix-ui/react-popover";
import { cn } from "../../lib/utils";
import { Button } from "./button";
import { format } from "date-fns";

/**
 * DatePickerWithRange 日期范围选择器
 * @param {{ from?: Date; to?: Date }} value - 当前日期范围
 * @param {Function} onChange - 日期范围变更回调，参数为 { from?: Date, to?: Date }
 * @param {string} className - 自定义样式
 */
function DatePickerWithRange({ value, onChange, className }) {
  const formatDisplay = () => {
    if (!value?.from && !value?.to) return "选择日期范围";
    if (value?.from && value?.to) {
      return `${format(value.from, "yyyy-MM-dd")} ~ ${format(value.to, "yyyy-MM-dd")}`;
    }
    if (value?.from) return `${format(value.from, "yyyy-MM-dd")} ~`;
    return `~ ${format(value.to, "yyyy-MM-dd")}`;
  };

  // 处理日期输入变更，创建新对象而非修改原对象
  const handleFromChange = (e) => {
    const dateStr = e.target.value;
    const newFrom = dateStr ? new Date(dateStr) : undefined;
    onChange({ ...value, from: newFrom });
  };

  const handleToChange = (e) => {
    const dateStr = e.target.value;
    const newTo = dateStr ? new Date(dateStr) : undefined;
    onChange({ ...value, to: newTo });
  };

  const handleClear = () => {
    onChange({ from: undefined, to: undefined });
  };

  return (
    <Popover.Root>
      <Popover.Trigger asChild>
        <Button
          variant="outline"
          className={cn(
            "justify-start text-left font-normal min-w-[240px]",
            !value?.from && !value?.to && "text-slate-400",
            className,
          )}
        >
          <Calendar className="mr-2 h-4 w-4" />
          {formatDisplay()}
        </Button>
      </Popover.Trigger>
      <Popover.Portal>
        <Popover.Content
          className="z-50 rounded-xl border border-white/10 bg-surface-100 p-4 shadow-xl"
          align="start"
          sideOffset={4}
        >
          <div className="space-y-3">
            <div className="flex flex-col gap-2">
              <label className="text-xs text-slate-400">开始日期</label>
              <input
                type="date"
                className="rounded-lg border border-white/10 bg-surface-50 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={value?.from ? format(value.from, "yyyy-MM-dd") : ""}
                onChange={handleFromChange}
              />
            </div>
            <div className="flex flex-col gap-2">
              <label className="text-xs text-slate-400">结束日期</label>
              <input
                type="date"
                className="rounded-lg border border-white/10 bg-surface-50 px-3 py-2 text-sm text-white focus:outline-none focus:ring-2 focus:ring-primary/50"
                value={value?.to ? format(value.to, "yyyy-MM-dd") : ""}
                onChange={handleToChange}
              />
            </div>
            <Button variant="ghost" size="sm" className="w-full" onClick={handleClear}>
              清除
            </Button>
          </div>
        </Popover.Content>
      </Popover.Portal>
    </Popover.Root>
  );
}

export { DatePickerWithRange };
