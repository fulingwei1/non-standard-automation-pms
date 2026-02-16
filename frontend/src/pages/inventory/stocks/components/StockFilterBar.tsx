/**
 * 库存筛选栏组件
 * 提供物料分类、仓库位置、批次号、库存状态等筛选功能
 */

import React from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import { Search, RefreshCw, Download } from 'lucide-react';
import { StockStatus } from '@/types/inventory';

interface StockFilterBarProps {
  filters: {
    material_code?: string;
    location?: string;
    batch_number?: string;
    status?: StockStatus;
  };
  onFilterChange: (filters: any) => void;
  onSearch: () => void;
  onReset: () => void;
  onExport?: () => void;
  loading?: boolean;
}

const StockFilterBar: React.FC<StockFilterBarProps> = ({
  filters,
  onFilterChange,
  onSearch,
  onReset,
  onExport,
  loading,
}) => {
  const handleInputChange = (key: string, value: string) => {
    onFilterChange({ ...filters, [key]: value });
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow space-y-4">
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {/* 物料编码 */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-1 block">
            物料编码
          </label>
          <Input
            placeholder="输入物料编码"
            value={filters.material_code || ''}
            onChange={(e) => handleInputChange('material_code', e.target.value)}
            disabled={loading}
          />
        </div>

        {/* 仓库位置 */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-1 block">
            仓库位置
          </label>
          <Input
            placeholder="输入仓库位置"
            value={filters.location || ''}
            onChange={(e) => handleInputChange('location', e.target.value)}
            disabled={loading}
          />
        </div>

        {/* 批次号 */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-1 block">
            批次号
          </label>
          <Input
            placeholder="输入批次号"
            value={filters.batch_number || ''}
            onChange={(e) => handleInputChange('batch_number', e.target.value)}
            disabled={loading}
          />
        </div>

        {/* 库存状态 */}
        <div>
          <label className="text-sm font-medium text-gray-700 mb-1 block">
            库存状态
          </label>
          <Select
            value={filters.status || 'all'}
            onValueChange={(value) =>
              handleInputChange('status', value === 'all' ? '' : value)
            }
            disabled={loading}
          >
            <SelectTrigger>
              <SelectValue placeholder="选择状态" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="all">全部</SelectItem>
              <SelectItem value={StockStatus.NORMAL}>正常</SelectItem>
              <SelectItem value={StockStatus.LOW}>低库存</SelectItem>
              <SelectItem value={StockStatus.EXPIRED}>已过期</SelectItem>
              <SelectItem value={StockStatus.RESERVED}>已预留</SelectItem>
            </SelectContent>
          </Select>
        </div>
      </div>

      {/* 操作按钮 */}
      <div className="flex gap-2">
        <Button
          onClick={onSearch}
          disabled={loading}
          className="bg-blue-500 hover:bg-blue-600"
        >
          <Search className="h-4 w-4 mr-2" />
          查询
        </Button>
        <Button onClick={onReset} disabled={loading} variant="outline">
          <RefreshCw className="h-4 w-4 mr-2" />
          重置
        </Button>
        {onExport && (
          <Button onClick={onExport} disabled={loading} variant="outline">
            <Download className="h-4 w-4 mr-2" />
            导出
          </Button>
        )}
      </div>
    </div>
  );
};

export default StockFilterBar;
