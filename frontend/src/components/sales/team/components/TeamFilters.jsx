/**
 * TeamFilters - 团队筛选器组件
 * 提供部门、区域、日期范围等筛选功能
 */

import { motion } from "framer-motion";
import { Filter, RefreshCw } from "lucide-react";
import { Card, CardContent, Button, Input } from "../../../ui";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../../ui/select";
import { cn } from "../../../../lib/utils";
import { QUICK_RANGE_PRESETS, formatAutoRefreshTime } from "@/lib/constants/salesTeam";

export default function TeamFilters({
  filters,
  departmentOptions,
  regionOptions,
  dateError,
  onFilterChange,
  onQuickRange,
  onReset,
  activeQuickRange,
  lastAutoRefreshAt,
  highlightAutoRefresh,
}) {
  return (
    <motion.div variants={{ hidden: { opacity: 0, y: -10 }, visible: { opacity: 1, y: 0 } }}>
      <Card>
        <CardContent className="p-4 space-y-4">
          {/* 筛选器标题 */}
          <div className="flex items-center justify-between text-sm text-slate-300">
            <div className="flex items-center gap-2">
              <Filter className="w-4 h-4" />
              <span>筛选条件</span>
            </div>
            {dateError && (
              <span className="text-xs text-red-400">{dateError}</span>
            )}
          </div>

          {/* 筛选条件输入 */}
          <div className="grid gap-4 md:grid-cols-4">
            {/* 部门选择 */}
            <div>
              <p className="text-xs text-slate-400 mb-1">部门</p>
              <Select
                value={filters.departmentId}
                onValueChange={(value) => onFilterChange("departmentId", value)}
              >
                <SelectTrigger>
                  <SelectValue placeholder="全部部门" />
                </SelectTrigger>
                <SelectContent>
                  {(departmentOptions || []).map((dept) => (
                    <SelectItem key={dept.value} value={dept.value}>
                      {dept.label}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* 区域输入 */}
            <div>
              <p className="text-xs text-slate-400 mb-1">区域</p>
              <Input
                placeholder="输入区域（如华东、华南）"
                value={filters.region}
                onChange={(e) => onFilterChange("region", e.target.value)}
                list={regionOptions.length ? "region-suggestions" : undefined}
              />
              {regionOptions.length > 0 && (
                <datalist id="region-suggestions">
                  {(regionOptions || []).map((option) => (
                    <option key={option} value={option} />
                  ))}
                </datalist>
              )}
            </div>

            {/* 开始日期 */}
            <div>
              <p className="text-xs text-slate-400 mb-1">开始日期</p>
              <Input
                type="date"
                value={filters.startDate}
                onChange={(e) =>
                  onFilterChange("startDate", e.target.value)
                }
              />
            </div>

            {/* 结束日期 */}
            <div>
              <p className="text-xs text-slate-400 mb-1">结束日期</p>
              <Input
                type="date"
                value={filters.endDate}
                onChange={(e) =>
                  onFilterChange("endDate", e.target.value)
                }
              />
            </div>
          </div>

          {/* 快捷时间段 */}
          <div className="flex flex-wrap items-center gap-2 text-xs text-slate-400">
            <span className="text-slate-500">快捷时间段</span>
            {QUICK_RANGE_PRESETS.map((preset) => (
              <Button
                key={preset.key}
                size="sm"
                variant={
                  activeQuickRange === preset.key ? "default" : "outline"
                }
                onClick={() => onQuickRange(preset.key)}
                className={cn(
                  "h-7 px-3",
                  activeQuickRange === preset.key
                    ? "bg-primary text-white"
                    : "bg-slate-800/40 border-slate-700 text-slate-300",
                )}
              >
                {preset.label}
              </Button>
            ))}
            <span className="text-slate-500">
              快速切换日/周/月，洞察销售工程师创建的商机与拜访数据
            </span>
          </div>

          {/* 操作按钮 */}
          <div className="flex flex-wrap items-center gap-3 text-xs text-slate-400">
            <Button variant="ghost" size="sm" onClick={onReset}>
              重置筛选
            </Button>
            <div
              className={cn(
                "flex items-center gap-1 transition-colors",
                highlightAutoRefresh ? "text-emerald-400" : "text-slate-400",
              )}
            >
              <RefreshCw
                className={cn(
                  "w-3 h-3",
                  highlightAutoRefresh && "animate-spin",
                )}
              />
              {lastAutoRefreshAt ? (
                <>
                  <span>已自动刷新</span>
                  <span className="text-slate-500">
                    ({formatAutoRefreshTime(lastAutoRefreshAt)})
                  </span>
                </>
              ) : (
                <span>筛选更新后自动刷新数据</span>
              )}
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
