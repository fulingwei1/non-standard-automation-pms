/**
 * 物料分析筛选器组件
 * 提供搜索和多维度筛选功能
 */
import { Search, Filter, Package, AlertTriangle } from 'lucide-react';
import { Button } from '../ui/button';
import { Input } from '../ui/input';
import { Badge } from '../ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '../ui/select';
import { MATERIAL_STATUS } from '@/lib/constants/materialAnalysis';

/**
 * 物料筛选器组件
 * @param {object} props
 * @param {string} props.searchTerm - 搜索关键词
 * @param {function} props.onSearchChange - 搜索改变回调
 * @param {string} props.statusFilter - 状态筛选
 * @param {function} props.onStatusChange - 状态改变回调
 * @param {string} props.categoryFilter - 分类筛选
 * @param {function} props.onCategoryChange - 分类改变回调
 * @param {array} props.categories - 分类列表
 * @param {function} props.onReset - 重置筛选
 */
export default function MaterialFilters({
  searchTerm,
  onSearchChange,
  statusFilter,
  onStatusChange,
  categoryFilter,
  onCategoryChange,
  categories = [],
  onReset,
}) {
  return (
    <div className="flex flex-col lg:flex-row gap-4 p-4 bg-slate-800/50 border border-slate-700/50 rounded-lg">
      {/* 搜索框 */}
      <div className="flex-1">
        <div className="relative">
          <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
          <Input
            placeholder="搜索物料编码、名称、规格..."
            value={searchTerm}
            onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
            className="pl-10 bg-slate-900 border-slate-700 text-white"
          />
        </div>
      </div>

      {/* 筛选条件 */}
      <div className="flex items-center gap-3 flex-wrap">
        {/* 状态筛选 */}
        <Select value={statusFilter || 'all'} onValueChange={onStatusChange}>
          <SelectTrigger className="w-[140px] bg-slate-900 border-slate-700 text-white">
            <SelectValue placeholder="物料状态" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">全部状态</SelectItem>
            {Object.values(MATERIAL_STATUS).map((status) => (
              <SelectItem key={status.key} value={status.key}>
                <div className="flex items-center gap-2">
                  <status.icon className="w-4 h-4" />
                  {status.label}
                </div>
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        {/* 分类筛选 */}
        {categories?.length > 0 && (
          <Select value={categoryFilter || 'all'} onValueChange={onCategoryChange}>
            <SelectTrigger className="w-[160px] bg-slate-900 border-slate-700 text-white">
              <SelectValue placeholder="物料分类" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部分类</SelectItem>
              {(categories || []).map((category) => (
                <SelectItem key={category.id} value={category.id}>
                  {category.name}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        )}

        {/* 快捷筛选按钮 */}
        <div className="flex items-center gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={() => onStatusChange && onStatusChange('delayed')}
            className={statusFilter === 'delayed' ? 'bg-red-500/20 border-red-500' : 'bg-slate-900 border-slate-700 text-white'}
          >
            <AlertTriangle className="w-4 h-4 mr-1" />
            延期物料
          </Button>
          <Button
            variant="outline"
            size="sm"
            onClick={() => onStatusChange && onStatusChange('not_ordered')}
            className={statusFilter === 'not_ordered' ? 'bg-amber-500/20 border-amber-500' : 'bg-slate-900 border-slate-700 text-white'}
          >
            <Package className="w-4 h-4 mr-1" />
            未采购
          </Button>
        </div>

        {/* 重置按钮 */}
        {onReset && (statusFilter !== 'all' || categoryFilter !== 'all' || searchTerm) && (
          <Button
            variant="ghost"
            size="sm"
            onClick={onReset}
            className="text-slate-400 hover:text-white"
          >
            <Filter className="w-4 h-4 mr-2" />
            重置
          </Button>
        )}
      </div>
    </div>
  );
}
