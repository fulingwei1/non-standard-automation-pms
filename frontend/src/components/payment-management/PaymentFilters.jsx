/**
 * 支付管理筛选组件
 * 提供搜索和多维度筛选功能
 */
import { Search, List, LayoutGrid } from 'lucide-react';
import { Card, CardContent, Input, Button } from '../ui';
import { PAYMENT_TYPES, PAYMENT_STATUS } from '@/lib/constants/finance';

/**
 * 支付筛选组件
 * @param {object} props
 * @param {string} props.searchTerm - 搜索关键词
 * @param {function} props.onSearchChange - 搜索改变回调
 * @param {string} props.selectedType - 选中的类型
 * @param {function} props.onTypeChange - 类型改变回调
 * @param {string} props.selectedStatus - 选中的状态
 * @param {function} props.onStatusChange - 状态改变回调
 * @param {string} props.viewMode - 当前视图模式
 * @param {function} props.onViewModeChange - 视图模式改变回调
 */
export default function PaymentFilters({
  searchTerm,
  onSearchChange,
  selectedType,
  onTypeChange,
  selectedStatus,
  onStatusChange,
  viewMode,
  onViewModeChange,
}) {
  return (
    <Card className="bg-slate-800/50 border-slate-700/50">
      <CardContent className="p-6">
        <div className="flex flex-col md:flex-row gap-4">
          <div className="flex-1">
            <div className="relative">
              <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 text-slate-400 w-4 h-4" />
              <Input
                placeholder="搜索客户、项目或合同..."
                value={searchTerm}
                onChange={(e) => onSearchChange && onSearchChange(e.target.value)}
                className="pl-10 bg-slate-900 border-slate-700 text-white"
              />
            </div>
          </div>
          <div className="flex items-center gap-2">
            <select
              value={selectedType}
              onChange={(e) => onTypeChange && onTypeChange(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2"
            >
              <option value="all">全部类型</option>
              {Object.values(PAYMENT_TYPES).map((type) => (
                <option key={type.key} value={type.key}>
                  {type.label}
                </option>
              ))}
            </select>
            <select
              value={selectedStatus}
              onChange={(e) => onStatusChange && onStatusChange(e.target.value)}
              className="bg-slate-900 border border-slate-700 text-white rounded-lg px-3 py-2"
            >
              <option value="all">全部状态</option>
              {Object.values(PAYMENT_STATUS).map((status) => (
                <option key={status.key} value={status.key}>
                  {status.label}
                </option>
              ))}
            </select>
            {onViewModeChange && (
              <div className="flex items-center gap-1">
                <Button
                  variant={viewMode === 'list' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => onViewModeChange('list')}
                >
                  <List className="w-4 h-4" />
                </Button>
                <Button
                  variant={viewMode === 'grid' ? 'default' : 'ghost'}
                  size="sm"
                  onClick={() => onViewModeChange('grid')}
                >
                  <LayoutGrid className="w-4 h-4" />
                </Button>
              </div>
            )}
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
