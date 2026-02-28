import { memo } from "react";
import { cn } from "../../lib/utils";
import { Calendar, RotateCw, Search, X } from "lucide-react";
import { Input } from "../ui";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "../ui";
import { Button } from "../ui";
import {
  ORDER_STATUS_OPTIONS,
  ORDER_URGENCY_OPTIONS,
} from "@/lib/constants/procurement";

/**
 * 采购订单筛选器组件
 */
const PurchaseOrderFilters = memo(function PurchaseOrderFilters({
  // 搜索
  searchQuery = "",
  onSearchChange,
  // 状态筛选
  statusFilter = "all",
  onStatusFilterChange,
  // 紧急程度筛选
  urgencyFilter = "all",
  onUrgencyFilterChange,
  // 日期范围
  dateRange = null,
  onDateRangeChange,
}) {
  // 重置所有筛选
  const handleReset = () => {
    onSearchChange?.("");
    onStatusFilterChange?.("all");
    onUrgencyFilterChange?.("all");
    onDateRangeChange?.(null);
  };

  // 检查是否有激活的筛选
  const hasActiveFilters =
    searchQuery !== "" ||
    statusFilter !== "all" ||
    urgencyFilter !== "all" ||
    dateRange !== null;

  return (
    <div className="space-y-4">
      {/* 基础筛选行 */}
      <div className="flex flex-wrap items-center gap-4">
        {/* 搜索框 */}
        <div className="flex-1 min-w-[250px]">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索订单编号、供应商、项目..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10"
            />
            {searchQuery && (
              <button
                onClick={() => onSearchChange("")}
                className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-white"
              >
                <X className="w-4 h-4" />
              </button>
            )}
          </div>
        </div>

        {/* 状态筛选 */}
        <Select value={statusFilter} onValueChange={onStatusFilterChange}>
          <SelectTrigger className="w-[140px]">
            <SelectValue placeholder="状态" />
          </SelectTrigger>
          <SelectContent>
            {ORDER_STATUS_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* 紧急程度筛选 */}
        <Select value={urgencyFilter} onValueChange={onUrgencyFilterChange}>
          <SelectTrigger className="w-[130px]">
            <SelectValue placeholder="紧急程度" />
          </SelectTrigger>
          <SelectContent>
            {ORDER_URGENCY_OPTIONS.map((option) => (
              <SelectItem key={option.value} value={option.value}>
                {option.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* 日期范围筛选 */}
        <div className="flex items-center gap-2">
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              type="date"
              placeholder="开始日期"
              value={dateRange?.start ? new Date(dateRange.start).toISOString().split('T')[0] : ""}
              onChange={(e) => {
                const start = e.target.value ? new Date(e.target.value) : null;
                onDateRangeChange?.({ ...dateRange, start });
              }}
              className="pl-10 w-[140px]"
            />
          </div>
          <span className="text-slate-400">至</span>
          <div className="relative">
            <Calendar className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              type="date"
              placeholder="结束日期"
              value={dateRange?.end ? new Date(dateRange.end).toISOString().split('T')[0] : ""}
              onChange={(e) => {
                const end = e.target.value ? new Date(e.target.value) : null;
                onDateRangeChange?.({ ...dateRange, end });
              }}
              className="pl-10 w-[140px]"
            />
          </div>
        </div>

        {/* 重置按钮 */}
        <Button
          variant="ghost"
          size="sm"
          onClick={handleReset}
          disabled={!hasActiveFilters}
          className={cn(
            "text-slate-400 hover:text-white",
            !hasActiveFilters && "opacity-50 cursor-not-allowed"
          )}
        >
          <RotateCw className="w-4 h-4" />
          重置
        </Button>
      </div>
    </div>
  );
});

export default PurchaseOrderFilters;