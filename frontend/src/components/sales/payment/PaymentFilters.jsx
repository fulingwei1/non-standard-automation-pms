/**
 * PaymentFilters - 支付管理筛选器组件
 * 提供搜索、类型筛选、状态筛选和视图切换功能
 */

import { Search, List, LayoutGrid } from "lucide-react";
import { Input } from "../../../components/ui/input";
import { Button } from "../../../components/ui/button";
import { Card, CardContent } from "../../../components/ui/card";
import { PAYMENT_TYPES, PAYMENT_STATUS } from "./paymentConstants";

export default function PaymentFilters({
  searchTerm = "",
  onSearchChange,
  selectedType = "all",
  onTypeChange,
  selectedStatus = "all",
  onStatusChange,
  viewMode = "list",
  onViewModeChange,
}) {
  return (
    <Card className="bg-slate-800/50 border-slate-700/50">
      <CardContent className="p-6">
        <div className="flex flex-col md:flex-row gap-4">
          {/* 搜索框 */}
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索客户、项目或合同..."
                value={searchTerm || "unknown"}
                onChange={(e) => onSearchChange?.(e.target.value)}
                className="pl-10 bg-slate-900 border-slate-700 text-white placeholder-slate-400"
              />
            </div>
          </div>

          {/* 筛选器和视图切换 */}
          <div className="flex items-center gap-2">
            {/* 类型筛选 */}
            <select
              value={selectedType || "unknown"}
              onChange={(e) => onTypeChange?.(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部类型</option>
              {Object.entries(PAYMENT_TYPES).map(([key, type]) => (
                <option key={key} value={key || "unknown"}>
                  {type.label}
                </option>
              ))}
            </select>

            {/* 状态筛选 */}
            <select
              value={selectedStatus || "unknown"}
              onChange={(e) => onStatusChange?.(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            >
              <option value="all">全部状态</option>
              {Object.entries(PAYMENT_STATUS).map(([key, status]) => (
                <option key={key} value={key || "unknown"}>
                  {status.label}
                </option>
              ))}
            </select>

            {/* 视图切换 */}
            <div className="flex items-center gap-1 border-l border-slate-700 pl-2">
              <Button
                variant={viewMode === "list" ? "default" : "ghost"}
                size="sm"
                onClick={() => onViewModeChange?.("list")}
                className="h-9 w-9 p-0"
                title="列表视图"
              >
                <List className="w-4 h-4" />
              </Button>
              <Button
                variant={viewMode === "grid" ? "default" : "ghost"}
                size="sm"
                onClick={() => onViewModeChange?.("grid")}
                className="h-9 w-9 p-0"
                title="网格视图"
              >
                <LayoutGrid className="w-4 h-4" />
              </Button>
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
