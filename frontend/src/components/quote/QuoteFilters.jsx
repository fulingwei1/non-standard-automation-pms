/**
 * 报价筛选器组件
 * 提供搜索和多维度筛选功能
 */
import { Search, SlidersHorizontal } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';

/**
 * 报价筛选器组件
 * @param {object} props
 * @param {string} props.searchTerm - 搜索关键词
 * @param {function} props.onSearchChange - 搜索改变回调
 * @param {object} props.filters - 筛选条件
 * @param {function} props.onFilterChange - 筛选改变回调
 * @param {function} props.onReset - 重置筛选
 */
export default function QuoteFilters({
  searchTerm,
  onSearchChange,
  filters,
  onFilterChange,
  onReset,
}) {
  return (
    <div className="flex flex-col md:flex-row gap-4 p-4 bg-slate-800/50 border border-slate-700/50 rounded-lg">
      {/* 搜索框 */}
      <div className="flex-1">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
          <Input
            placeholder="搜索报价单号、客户、项目..."
            value={searchTerm}
            onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
            className="pl-10 bg-slate-900 border-slate-700 text-white"
          />
        </div>
      </div>

      {/* 筛选条件 */}
      <div className="flex items-center gap-3">
        {/* 状态筛选 */}
        <Select
          value={filters.status || 'all'}
          onValueChange={(value) => onFilterChange && onFilterChange({ ...filters, status: value })}
        >
          <SelectTrigger className="w-[140px] bg-slate-900 border-slate-700 text-white">
            <SelectValue placeholder="状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            <SelectItem value="draft">草稿</SelectItem>
            <SelectItem value="submitted">已提交</SelectItem>
            <SelectItem value="approved">已批准</SelectItem>
            <SelectItem value="rejected">已拒绝</SelectItem>
            <SelectItem value="expired">已过期</SelectItem>
          </SelectContent>
        </Select>

        {/* 优先级筛选 */}
        <Select
          value={filters.priority || 'all'}
          onValueChange={(value) => onFilterChange && onFilterChange({ ...filters, priority: value })}
        >
          <SelectTrigger className="w-[120px] bg-slate-900 border-slate-700 text-white">
            <SelectValue placeholder="优先级" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部优先级</SelectItem>
            <SelectItem value="high">高</SelectItem>
            <SelectItem value="medium">中</SelectItem>
            <SelectItem value="low">低</SelectItem>
          </SelectContent>
        </Select>

        {/* 时间范围 */}
        <Select
          value={filters.timeRange || 'month'}
          onValueChange={(value) => onFilterChange && onFilterChange({ ...filters, timeRange: value })}
        >
          <SelectTrigger className="w-[120px] bg-slate-900 border-slate-700 text-white">
            <SelectValue placeholder="时间范围" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="week">最近1周</SelectItem>
            <SelectItem value="month">最近1月</SelectItem>
            <SelectItem value="quarter">最近3月</SelectItem>
            <SelectItem value="year">最近1年</SelectItem>
          </SelectContent>
        </Select>

        {/* 重置按钮 */}
        {onReset && (
          <Button
            variant="outline"
            size="sm"
            onClick={onReset}
            className="bg-slate-900 border-slate-700 text-white hover:bg-slate-800"
          >
            <SlidersHorizontal className="w-4 h-4 mr-2" />
            重置
          </Button>
        )}
      </div>
    </div>
  );
}
