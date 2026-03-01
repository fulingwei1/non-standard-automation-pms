/**
 * 工单筛选器组件
 * 提供搜索、状态筛选和排序功能
 */
import { Search, ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { Input } from '../ui/input';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { WORK_ORDER_STATUS } from '@/lib/constants/workerWorkstation';

/**
 * 工单筛选器组件
 * @param {object} props
 * @param {string} props.searchTerm - 搜索关键词
 * @param {function} props.onSearchChange - 搜索改变回调
 * @param {string} props.filterStatus - 筛选状态
 * @param {function} props.onStatusChange - 状态改变回调
 * @param {string} props.sortField - 排序字段
 * @param {string} props.sortDirection - 排序方向
 * @param {function} props.onSort - 排序回调
 */
export default function WorkOrderFilters({
  searchTerm,
  onSearchChange,
  filterStatus,
  onStatusChange,
  sortField,
  sortDirection,
  onSort,
}) {
  const handleSort = (field) => {
    if (onSort) {
      onSort(field);
    }
  };

  const getSortIcon = (field) => {
    if (sortField !== field) {
      return <ArrowUpDown className="w-4 h-4 text-slate-400" />;
    }
    return sortDirection === 'asc' ? (
      <ArrowUp className="w-4 h-4 text-blue-500" />
    ) : (
      <ArrowDown className="w-4 h-4 text-blue-500" />
    );
  };

  return (
    <div className="flex flex-col md:flex-row gap-4">
      {/* 搜索框 */}
      <div className="flex-1">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
          <Input
            placeholder="搜索工单号、项目名称..."
            value={searchTerm || "unknown"}
            onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
            className="pl-10 bg-slate-800/50 border-slate-700/50 text-white"
          />
        </div>
      </div>

      {/* 状态筛选 */}
      <Select value={filterStatus || "unknown"} onValueChange={onStatusChange}>
        <SelectTrigger className="w-[180px] bg-slate-800/50 border-slate-700/50 text-white">
          <SelectValue placeholder="筛选状态" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="all">全部状态</SelectItem>
          {Object.values(WORK_ORDER_STATUS).map((status) => (
            <SelectItem key={status.key} value={status.key}>
              {status.label}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>

      {/* 排序按钮 */}
      <div className="flex items-center gap-2">
        <button
          onClick={() => handleSort('created_time')}
          className="flex items-center gap-1 px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50 text-white hover:bg-slate-700/50 transition-colors"
        >
          创建时间
          {getSortIcon('created_time')}
        </button>
        <button
          onClick={() => handleSort('priority')}
          className="flex items-center gap-1 px-3 py-2 rounded-lg bg-slate-800/50 border border-slate-700/50 text-white hover:bg-slate-700/50 transition-colors"
        >
          优先级
          {getSortIcon('priority')}
        </button>
      </div>
    </div>
  );
}
