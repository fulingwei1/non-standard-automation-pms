/**
 * Service Ticket List Header Component
 * 服务工单列表头部组件
 */
import { useState } from "react";
import { Plus, Search, Filter, RefreshCw, Download, Calendar } from "lucide-react";
import { Button } from "../ui/button";
import { Input } from "../ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue } from
"../ui/select";
import { filterOptions, sortOptions } from "./serviceTicketConstants";

export function ServiceTicketListHeader({
  searchQuery,
  onSearchChange,
  statusFilter,
  onStatusChange,
  urgencyFilter,
  onUrgencyChange,
  problemTypeFilter,
  onProblemTypeChange,
  sortBy,
  onSortChange,
  sortOrder,
  onSortOrderChange,
  dateRange,
  onDateRangeChange,
  onCreateTicket,
  onRefresh,
  exporting,
  onExport
}) {
  const [showFilters, setShowFilters] = useState(false);
  const [showDateRange, setShowDateRange] = useState(false);

  return (
    <div className="space-y-4">
      {/* 搜索和操作栏 */}
      <div className="flex flex-col lg:flex-row gap-4 items-start lg:items-center justify-between">
        <div className="flex flex-col lg:flex-row gap-3 flex-1 w-full lg:w-auto">
          {/* 搜索框 */}
          <div className="relative flex-1 lg:flex-initial">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400" />
            <Input
              placeholder="搜索工单编号、客户、设备、问题描述..."
              value={searchQuery}
              onChange={(e) => onSearchChange(e.target.value)}
              className="pl-10 w-full lg:w-96" />

          </div>

          {/* 排序选择 */}
          <div className="flex items-center gap-2">
            <span className="text-sm text-slate-500 whitespace-nowrap">排序:</span>
            <Select
              value={sortBy}
              onValueChange={onSortChange}>

              <SelectTrigger className="w-32">
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {sortOptions.map((option) =>
                <SelectItem key={option.value} value={option.value}>
                    <div className="flex items-center gap-2">
                      {option.icon && <option.icon className="w-4 h-4" />}
                      {option.label}
                    </div>
                  </SelectItem>
                )}
              </SelectContent>
            </Select>
            
            <Button
              variant="outline"
              size="sm"
              onClick={() => onSortOrderChange(sortOrder === "asc" ? "desc" : "asc")}
              className="px-2">

              {sortOrder === "asc" ? "↑" : "↓"}
            </Button>
          </div>

          {/* 筛选和日期范围按钮 */}
          <div className="flex gap-2">
            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowFilters(!showFilters)}
              className="flex items-center gap-2">

              <Filter className="w-4 h-4" />
              筛选
              {(statusFilter !== "ALL" || urgencyFilter !== "ALL" || problemTypeFilter !== "ALL") &&
              <span className="w-2 h-2 bg-blue-500 rounded-full" />
              }
            </Button>

            <Button
              variant="outline"
              size="sm"
              onClick={() => setShowDateRange(!showDateRange)}
              className="flex items-center gap-2">

              <Calendar className="w-4 h-4" />
              日期
              {(dateRange.start || dateRange.end) &&
              <span className="w-2 h-2 bg-blue-500 rounded-full" />
              }
            </Button>
          </div>
        </div>

        {/* 操作按钮 */}
        <div className="flex gap-2 w-full lg:w-auto">
          <Button
            variant="outline"
            size="sm"
            onClick={onRefresh}
            disabled={exporting}
            className="flex items-center gap-2">

            <RefreshCw className="w-4 h-4" />
            刷新
          </Button>

          <Button
            variant="outline"
            size="sm"
            onClick={onExport}
            disabled={exporting}
            className="flex items-center gap-2">

            <Download className="w-4 h-4" />
            {exporting ? "导出中..." : "导出"}
          </Button>

          <Button
            size="sm"
            onClick={onCreateTicket}
            className="flex items-center gap-2">

            <Plus className="w-4 h-4" />
            创建工单
          </Button>
        </div>
      </div>

      {/* 筛选条件 */}
      {showFilters &&
      <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg border">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
            {/* 状态筛选 */}
            <div>
              <label className="text-sm font-medium mb-2 block">工单状态</label>
              <Select
              value={statusFilter}
              onValueChange={onStatusChange}>

                <SelectTrigger>
                  <SelectValue placeholder="选择状态" />
                </SelectTrigger>
                <SelectContent>
                  {filterOptions.statuses.map((status) =>
                <SelectItem key={status.value} value={status.value}>
                      {status.label}
                    </SelectItem>
                )}
                </SelectContent>
              </Select>
            </div>

            {/* 紧急程度筛选 */}
            <div>
              <label className="text-sm font-medium mb-2 block">紧急程度</label>
              <Select
              value={urgencyFilter}
              onValueChange={onUrgencyChange}>

                <SelectTrigger>
                  <SelectValue placeholder="选择紧急程度" />
                </SelectTrigger>
                <SelectContent>
                  {filterOptions.urgencies.map((urgency) =>
                <SelectItem key={urgency.value} value={urgency.value}>
                      {urgency.label}
                    </SelectItem>
                )}
                </SelectContent>
              </Select>
            </div>

            {/* 问题类型筛选 */}
            <div>
              <label className="text-sm font-medium mb-2 block">问题类型</label>
              <Select
              value={problemTypeFilter}
              onValueChange={onProblemTypeChange}>

                <SelectTrigger>
                  <SelectValue placeholder="选择问题类型" />
                </SelectTrigger>
                <SelectContent>
                  {filterOptions.problemTypes.map((type) =>
                <SelectItem key={type.value} value={type.value}>
                      <div className="flex items-center gap-2">
                        {type.icon && <span>{type.icon}</span>}
                        {type.label}
                      </div>
                    </SelectItem>
                )}
                </SelectContent>
              </Select>
            </div>

            {/* 快速筛选组合 */}
            <div>
              <label className="text-sm font-medium mb-2 block">快速筛选</label>
              <div className="flex flex-wrap gap-1">
                <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  onStatusChange("PENDING");
                  onUrgencyChange("URGENT");
                }}
                className="text-xs">

                  待处理紧急
                </Button>
                <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  onStatusChange("PENDING_VERIFY");
                  onUrgencyChange("ALL");
                }}
                className="text-xs">

                  待验证
                </Button>
                <Button
                variant="outline"
                size="sm"
                onClick={() => {
                  onStatusChange("ASSIGNED");
                  onUrgencyChange("HIGH");
                }}
                className="text-xs">

                  高优先级处理中
                </Button>
              </div>
            </div>
          </div>

          {/* 清除筛选 */}
          <div className="mt-4 flex justify-end">
            <Button
            variant="outline"
            size="sm"
            onClick={() => {
              onStatusChange("ALL");
              onUrgencyChange("ALL");
              onProblemTypeChange("ALL");
              onDateRangeChange({ start: "", end: "" });
            }}>

              清除所有筛选
            </Button>
          </div>
        </div>
      }

      {/* 日期范围筛选 */}
      {showDateRange &&
      <div className="bg-slate-50 dark:bg-slate-800 p-4 rounded-lg border">
          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <div>
              <label className="text-sm font-medium mb-2 block">开始日期</label>
              <Input
              type="date"
              value={dateRange.start}
              onChange={(e) => onDateRangeChange({ ...dateRange, start: e.target.value })} />

            </div>
            <div>
              <label className="text-sm font-medium mb-2 block">结束日期</label>
              <Input
              type="date"
              value={dateRange.end}
              onChange={(e) => onDateRangeChange({ ...dateRange, end: e.target.value })} />

            </div>
            <div className="flex items-end">
              <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // 设置为最近7天
                const end = new Date();
                const start = new Date();
                start.setDate(start.getDate() - 7);
                onDateRangeChange({
                  start: start.toISOString().split('T')[0],
                  end: end.toISOString().split('T')[0]
                });
              }}
              className="mr-2">

                最近7天
              </Button>
              <Button
              variant="outline"
              size="sm"
              onClick={() => {
                // 设置为最近30天
                const end = new Date();
                const start = new Date();
                start.setDate(start.getDate() - 30);
                onDateRangeChange({
                  start: start.toISOString().split('T')[0],
                  end: end.toISOString().split('T')[0]
                });
              }}
              className="mr-2">

                最近30天
              </Button>
              <Button
              variant="outline"
              size="sm"
              onClick={() => {
                onDateRangeChange({ start: "", end: "" });
              }}>

                清除
              </Button>
            </div>
          </div>
        </div>
      }
    </div>);

}
