/**
 * PurchaseOrderFilters - 采购订单筛选器组件
 * 提供搜索、状态筛选、排序功能
 */

import { Search, Filter, ArrowUpDown } from "lucide-react";
import { Card, CardContent, Button } from "../../../ui";
import { Input } from "../../../ui/input";
import { ORDER_FILTER_OPTIONS } from "./purchaseOrderConstants";

export default function PurchaseOrderFilters({
  searchQuery = "",
  onSearchChange,
  statusFilter = "all",
  onStatusFilterChange,
  sortBy = "expected_date",
  onSortChange,
  sortOrder = "asc",
  onSortOrderChange,
}) {
  return (
    <Card className="bg-slate-800/50 border border-slate-700/50">
      <CardContent className="p-4">
        <div className="flex flex-col md:flex-row gap-4">
          {/* 搜索框 */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索订单号、供应商、项目..."
                value={searchQuery}
                onChange={(e) => onSearchChange?.(e.target.value)}
                className="pl-10 bg-slate-900 border-slate-700 text-white placeholder-slate-400"
              />
            </div>
          </div>

          {/* 状态筛选 */}
          <div className="flex items-center gap-2">
            <Filter className="text-slate-400 w-4 h-4" />
            <select
              value={statusFilter}
              onChange={(e) => onStatusFilterChange?.(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              {ORDER_FILTER_OPTIONS.status.map((option) => (
                <option key={option.value} value={option.value}>
                  {option.label}
                </option>
              ))}
            </select>
          </div>

          {/* 排序 */}
          <div className="flex items-center gap-2">
            <ArrowUpDown className="text-slate-400 w-4 h-4" />
            <select
              value={sortBy}
              onChange={(e) => onSortChange?.(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="expected_date">按预计到货日期</option>
              <option value="created_date">按创建日期</option>
              <option value="total_amount">按订单金额</option>
            </select>
            <Button
              variant="ghost"
              size="sm"
              onClick={() => onSortOrderChange?.(sortOrder === "asc" ? "desc" : "asc")}
              className="px-2"
              title={sortOrder === "asc" ? "升序" : "降序"}
            >
              {sortOrder === "asc" ? "↑" : "↓"}
            </Button>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
